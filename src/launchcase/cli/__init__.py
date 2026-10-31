import argparse
import importlib.metadata
import json
import os
from pathlib import Path

from pydantic import ValidationError

from launchcase.application.services import CaseService
from launchcase.domain.common import DomainError, uid
from launchcase.domain.contracts import ProductBrief, SourceImport
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.store import read_import_file


def main():
    parser = argparse.ArgumentParser(prog="launchcase")
    parser.add_argument("--json", action="store_true", help="All commands emit JSON")
    parser.add_argument("--idempotency-key", default=None, help="Reuse for the same logical mutation")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("init-db")
    sub.add_parser("worker-once")
    demo_parser = sub.add_parser("demo")
    demo_parser.add_argument("--fixture", type=Path, required=True)
    demo_parser.add_argument("--out", type=Path, required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--case", dest="output_dir", type=Path, required=True)
    validate_parser.add_argument("--strict", action="store_true")
    back = sub.add_parser("backup")
    back.add_argument("--out", type=Path, required=True)
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("--source", type=Path, required=True)
    restore_parser.add_argument("--out", type=Path, required=True)
    retention_parser = sub.add_parser("retention")
    retention_parser.add_argument("--confirm-tenant")
    export_parser = sub.add_parser("export")
    export_parser.add_argument("pack_id")
    export_parser.add_argument("--format", choices=["json", "md", "zip"], default="json")
    export_parser.add_argument("--out", type=Path, required=True)
    auth = sub.add_parser("auth").add_subparsers(dest="operation", required=True).add_parser("create")
    auth.add_argument("--tenant", required=True)
    auth.add_argument("--name", required=True)
    auth.add_argument("--role", choices=["owner", "reviewer", "analyst", "agent", "viewer"], default="owner")
    auth.add_argument("--synthetic", action="store_true")
    case = sub.add_parser("case").add_subparsers(dest="operation", required=True)
    create = case.add_parser("create")
    create.add_argument("--brief", type=Path, required=True)
    status = case.add_parser("status")
    status.add_argument("case_id")
    case.add_parser("list")
    source = sub.add_parser("source").add_subparsers(dest="operation", required=True).add_parser("import")
    source.add_argument("--case", dest="case_id", required=True)
    source.add_argument("--file", type=Path, required=True)
    source.add_argument(
        "--type", required=True, choices=["review", "competitor", "quote", "spec", "sample", "rule"]
    )
    source.add_argument("--rights", required=True, choices=["synthetic_fixture", "authorized", "unknown"])
    source.add_argument("--synthetic", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("kind", choices=["research", "opportunities", "concepts", "feasibility", "launch_draft"])
    run.add_argument("--case", dest="case_id", required=True)
    gate = sub.add_parser("gate").add_subparsers(dest="operation", required=True).add_parser("decide")
    gate.add_argument("--case", dest="case_id", required=True)
    gate.add_argument("--gate", required=True)
    gate.add_argument("--file", type=Path, required=True)
    spec = sub.add_parser("spec").add_subparsers(dest="operation", required=True).add_parser("history")
    spec.add_argument("--case", dest="case_id", required=True)
    compare = sub.add_parser("concept").add_subparsers(dest="operation", required=True).add_parser("compare")
    compare.add_argument("--case", dest="case_id", required=True)
    visual = sub.add_parser("visual").add_subparsers(dest="operation", required=True)
    plan = visual.add_parser("plan")
    plan.add_argument("--case", dest="case_id", required=True)
    plan.add_argument("--file", type=Path, required=True)
    for name in ["status", "submit", "sync", "cancel", "approve-plan", "review-asset"]:
        item = visual.add_parser(name)
        item.add_argument("resource_id")
        if name in {"approve-plan", "review-asset"}:
            item.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    request_key = args.idempotency_key or uid()
    service = CaseService(Settings.from_env())
    try:
        if args.command == "doctor":
            result = {
                "status": "ok",
                "paid_enabled": False,
                "external_actions": False,
                "versions": {
                    p: importlib.metadata.version(p)
                    for p in ["launchcase", "fastapi", "pydantic", "sqlalchemy", "langgraph", "openai-agents"]
                },
            }
        elif args.command == "init-db":
            from launchcase.infrastructure.migrate import migrate

            migrate(service.settings)
            result = {"migrated": True}
        elif args.command == "demo":
            from launchcase.application.demo import demo

            result = demo(args.fixture, args.out)
        elif args.command == "validate":
            from launchcase.application.demo import validate

            result = validate(args.output_dir, args.strict)
        elif args.command == "backup":
            from launchcase.infrastructure.operations import backup

            result = backup(service.settings, args.out)
        elif args.command == "restore":
            from launchcase.infrastructure.operations import restore

            result = restore(args.source, args.out)
        elif args.command == "worker-once":
            from launchcase.workflow.worker import recover_once

            result = {"tasks": recover_once(service)}
        elif args.command == "auth":
            token, actor = service.provision(args.tenant, args.name, args.role, args.synthetic)
            result = {"token": token, "tenant_id": actor.tenant_id, "role": actor.role}
        else:
            actor = service.authenticate(os.getenv("LAUNCHCASE_TOKEN", ""))
            if args.command == "retention":
                from launchcase.infrastructure.operations import retention

                result = retention(service, actor, args.confirm_tenant)
            elif args.command == "export":
                from launchcase.application.launchpacks import LaunchPackService

                content = LaunchPackService(service).export(actor, args.pack_id, args.format)
                with args.out.open("xb") as target:
                    target.write(content)
                result = {"exported": str(args.out), "publishable": False}
            elif args.command == "run":
                from launchcase.workflow.graph import enqueue_run, execute_task

                task = enqueue_run(service, actor, args.case_id, args.kind, request_key)
                result = execute_task(service, actor, task["id"])
            elif args.command == "gate":
                from launchcase.application.products import ProductService
                from launchcase.domain.contracts import GateRequest

                result = ProductService(service).decide(
                    actor,
                    args.case_id,
                    args.gate,
                    GateRequest.model_validate_json(read_import_file(args.file)),
                    request_key,
                )
            elif args.command == "visual":
                from launchcase.application.visuals import VisualService
                from launchcase.domain.contracts import ReviewRequest, VisualRequest

                visual_service = VisualService(service)
                if args.operation == "plan":
                    result = visual_service.create(
                        actor,
                        args.case_id,
                        VisualRequest.model_validate_json(read_import_file(args.file)),
                        request_key,
                    )
                elif args.operation in {"approve-plan", "review-asset"}:
                    request = ReviewRequest.model_validate_json(read_import_file(args.file))
                    action = (
                        visual_service.approve if args.operation == "approve-plan" else visual_service.review
                    )
                    result = action(actor, args.resource_id, request, request_key)
                else:
                    action = getattr(visual_service, "get" if args.operation == "status" else args.operation)
                    result = action(actor, args.resource_id)
            elif args.command in {"spec", "concept"}:
                from launchcase.infrastructure.models import Artifact

                result = {
                    "items": service.list_scoped(
                        actor,
                        args.case_id,
                        Artifact,
                        kind="ProductSpec" if args.command == "spec" else "Concept",
                    )
                }
            elif args.command == "case" and args.operation == "create":
                result = service.create_case(
                    actor, ProductBrief.model_validate_json(read_import_file(args.brief)), request_key
                )
            elif args.command == "case" and args.operation == "status":
                result = service.get_case(actor, args.case_id)
            elif args.command == "case":
                result = {"items": service.list_cases(actor)}
            else:
                request = SourceImport(
                    filename=args.file.name,
                    content=read_import_file(args.file),
                    source_type=args.type,
                    rights_status=args.rights,
                    is_synthetic=args.synthetic,
                )
                result = service.import_source(actor, args.case_id, request, request_key)
        print(json.dumps(result, ensure_ascii=False))
    except DomainError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}))
        raise SystemExit(1) from exc
    except (ValidationError, OSError, ValueError) as exc:
        # Never echo source text, bearer secrets or raw validation inputs.
        print(json.dumps({"error": {"code": "INVALID_INPUT", "message": type(exc).__name__}}))
        raise SystemExit(1) from exc
