import json
from pathlib import Path

from launchcase.application.launchpacks import LaunchPackService
from launchcase.application.products import ProductService
from launchcase.application.services import Actor, CaseService
from launchcase.application.visuals import VisualService
from launchcase.domain.common import DomainError, digest, uid
from launchcase.domain.contracts import GateRequest, ProductBrief, ReviewRequest, SourceImport, VisualRequest
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.migrate import migrate
from launchcase.infrastructure.models import (
    Artifact,
    Evidence,
    GateDecision,
    SourceDocument,
    VisualAsset,
    VisualTask,
)
from launchcase.infrastructure.store import read_import_file
from launchcase.workflow.graph import enqueue_run, execute_task


def fixture_decision(service, actor, case_id, gate, subject_id, decision):
    if not actor.synthetic or not service.get_case(actor, case_id)["is_synthetic"]:
        raise DomainError("FIXTURE_ONLY", "Automated fixture approvals require a synthetic actor and Case")
    product = ProductService(service)
    subject = product.gate_subject(actor, case_id, gate, subject_id)
    return product.decide(
        actor,
        case_id,
        gate,
        GateRequest(
            decision=decision,
            subject_type={"G1": "opportunity", "G2": "concept", "G3": "feasibility"}[gate],
            subject_id=subject_id,
            expected_subject_hash=subject["subject_hash"],
            reason="SYNTHETIC TEST ACTOR: functional scenario only; not a real commercial approval",
        ),
        uid(),
    )


def demo(fixture: Path, out: Path):
    if out.exists() or ".." in out.parts or any(p.is_symlink() for p in out.parents):
        raise DomainError(
            "OUTPUT_EXISTS", "Use a new non-symlink output directory; existing data is never overwritten"
        )
    out.mkdir(parents=True)
    settings = Settings(out.absolute(), f"sqlite:///{out.absolute()}/launchcase.db")
    migrate(settings)
    service = CaseService(settings)
    _, actor = service.provision("synthetic-demo", "Synthetic fixture operator", "owner", synthetic=True)
    brief = ProductBrief.model_validate_json(read_import_file(fixture / "synthetic-brief.json"))
    if not brief.data_policy.is_synthetic:
        raise DomainError("FIXTURE_ONLY", "Demo requires explicitly synthetic input")
    case = service.create_case(actor, brief, "demo-case")
    case_id = case["id"]
    for filename, kind in [
        ("synthetic-voc.csv", "review"),
        ("synthetic-competitors.csv", "competitor"),
        ("synthetic-quote.json", "quote"),
    ]:
        service.import_source(
            actor,
            case_id,
            SourceImport(
                filename=filename,
                content=read_import_file(fixture / filename),
                source_type=kind,
                rights_status="synthetic_fixture",
                is_synthetic=True,
            ),
            "demo-import-" + kind,
        )

    def run(kind):
        task = enqueue_run(service, actor, case_id, kind, "demo-" + kind)
        return execute_task(service, actor, task["id"])

    run("research")
    opportunities = service.list_scoped(actor, case_id, Artifact, kind="Opportunity")
    opportunity = next(x for x in opportunities if "assembly" in x["data"]["title"])
    fixture_decision(service, actor, case_id, "G1", opportunity["id"], "accept")
    run("concepts")
    concepts = service.list_scoped(actor, case_id, Artifact, kind="Concept")
    concept = concepts[0]
    fixture_decision(service, actor, case_id, "G2", concept["id"], "select")
    run("feasibility")
    feasibility = service.list_scoped(actor, case_id, Artifact, kind="Feasibility")[-1]
    fixture_decision(service, actor, case_id, "G3", feasibility["id"], "sample_validation")
    visual_service = VisualService(service)
    visual = visual_service.create(
        actor,
        case_id,
        VisualRequest(
            concept_id=concept["id"],
            requirements="SYNTHETIC internal concept fixture; no real product claims",
        ),
        "demo-visual",
    )
    visual_service.approve(
        actor,
        visual["id"],
        ReviewRequest(
            expected_subject_hash=visual["plan_hash"],
            decision="approved",
            reason="Synthetic test fixture zero-budget Mock plan",
        ),
        "demo-plan",
    )
    visual_service.submit(actor, visual["id"])
    visual_service.sync(actor, visual["id"])
    asset = visual_service.asset(actor, visual_service.get(actor, visual["id"])["assets"][0]["id"])
    visual_service.review(
        actor,
        asset["id"],
        ReviewRequest(
            expected_subject_hash=asset["subject_hash"],
            decision="approved",
            reason="Synthetic fixture asset review; internal-only Mock",
        ),
        "demo-asset",
    )
    final_task = run("launch_draft")
    pack_id = final_task["result"]["pack_id"]
    packs = LaunchPackService(service)
    files = {}
    for fmt in ["json", "md", "zip"]:
        content = packs.export(actor, pack_id, fmt)
        (out / f"internal-draft.{fmt}").write_bytes(content)
        files[f"internal-draft.{fmt}"] = digest(content)
    manifest = {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "pack_id": pack_id,
        "actor_id": actor.id,
        "tenant_id": actor.tenant_id,
        "is_synthetic": True,
        "scope": "tested_offline",
        "waiting_for": final_task["result"]["waiting_for"],
        "publishable": False,
        "files": files,
        "counts": {
            "sources": 3,
            "evidence": len(service.list_scoped(actor, case_id, Evidence)),
            "concepts": len(concepts),
            "opportunities": len(opportunities),
        },
        "paid_calls": 0,
        "paid_calls_basis": "only local deterministic SDK Model and protocol fake instantiated",
    }
    (out / "demo-manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def validate(out: Path, strict=True):
    manifest = json.loads((out / "demo-manifest.json").read_text())
    if (
        manifest.get("publishable") is not False
        or manifest.get("is_synthetic") is not True
        or manifest.get("scope") != "tested_offline"
        or manifest.get("waiting_for") != "G4"
    ):
        raise DomainError("FALSE_CLAIM", "Synthetic demo status/approval/scope was relabeled")
    service = CaseService(Settings(out.absolute(), f"sqlite:///{out.absolute()}/launchcase.db"))
    actor = Actor(manifest["actor_id"], manifest["tenant_id"], "owner", True)
    case_id = manifest["case_id"]
    case = service.get_case(actor, case_id)
    if not case["is_synthetic"]:
        raise DomainError("FALSE_CLAIM", "Synthetic Case lost its label")
    for name, sha in manifest["files"].items():
        if Path(name).name != name or (out / name).is_symlink() or digest((out / name).read_bytes()) != sha:
            raise DomainError("EXPORT_CORRUPT", "Export bytes differ from recorded manifest")
    pack = LaunchPackService(service).read(actor, manifest["pack_id"])
    if not pack["current"] or pack["data"]["publishable"] or not pack["data"]["is_synthetic"]:
        raise DomainError("INVALID_PACK", "Pack not current or incorrectly labeled")
    if digest((out / "internal-draft.json").read_bytes()) != digest(
        LaunchPackService(service).export(actor, manifest["pack_id"])
    ):
        raise DomainError("EXPORT_CORRUPT", "JSON export does not match current immutable pack")
    sources = {s["id"]: s for s in service.list_scoped(actor, case_id, SourceDocument, 5000)}
    for src in sources.values():
        service.read_source(actor, src["id"], True)
        if not src["is_synthetic"]:
            raise DomainError("FALSE_CLAIM", "Synthetic source lost its label")
    evidence = service.list_scoped(actor, case_id, Evidence, 5000)
    ids = {e["id"] for e in evidence}
    from launchcase.application.intake import parse_import

    originals = {}
    for source_id, src in sources.items():
        _, rows = parse_import(
            SourceImport(
                filename=src["filename"],
                content=service.read_source(actor, source_id, True).decode("utf-8"),
                source_type=src["source_type"],
                rights_status=src["rights_status"],
                is_synthetic=src["is_synthetic"],
                collected_at=src["metadata_json"].get("collected_at"),
            )
        )
        originals[source_id] = {f"{src['filename']}#row={row['row']}": row for row in rows}
    for item in evidence:
        if item["source_id"] not in sources or not item["source_locator"] or not item["is_synthetic"]:
            raise DomainError("INVALID_LINEAGE", "Evidence provenance/synthetic label invalid")
        original = originals[item["source_id"]].get(item["source_locator"])
        if (
            not original
            or original["quote"] != item["quote"]
            or original["fingerprint"] != item["fingerprint"]
        ):
            raise DomainError("INVALID_LINEAGE", "Evidence does not match its exact original row")
    artifacts = service.list_scoped(actor, case_id, Artifact, 5000)
    decisions = service.list_scoped(actor, case_id, GateDecision, 5000)
    visuals = service.list_scoped(actor, case_id, VisualTask, 5000)
    assets = service.list_scoped(actor, case_id, VisualAsset, 5000)
    artifact_ids = {item["id"] for item in artifacts}
    decision_ids = {item["id"] for item in decisions}
    foreign_keys = {
        "source_id": set(sources),
        "evidence_id": ids,
        "visual_task_id": {item["id"] for item in visuals},
        "asset_id": {item["id"] for item in assets},
        **{
            key: artifact_ids
            for key in [
                "concept_id",
                "opportunity_id",
                "insight_id",
                "spec_id",
                "parent_spec_id",
                "cost_input_id",
                "feasibility_id",
            ]
        },
        **{key: decision_ids for key in ["g1_id", "g2_id", "g3_id"]},
    }

    def check_references(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"raw", "rows"}:
                    continue  # External source fields are inert data, not internal foreign keys.
                if key in foreign_keys and child is not None and child not in foreign_keys[key]:
                    raise DomainError("INVALID_LINEAGE", "Unresolved immutable document reference")
                if key.endswith("evidence_refs") and not set(child) <= ids:
                    raise DomainError("INVALID_CITATION", "Unresolved document evidence citation")
                if key == "source_hashes" and any(
                    source not in sources or sources[source]["sha256"] != sha for source, sha in child.items()
                ):
                    raise DomainError("INVALID_LINEAGE", "Source digest reference mismatch")
                check_references(child)
        elif isinstance(value, list):
            for child in value:
                check_references(child)

    for artifact in artifacts:
        if digest(artifact["data"]) != artifact["sha256"]:
            raise DomainError("ARTIFACT_CORRUPT", "Immutable artifact data differs from its hash")
        check_references(artifact["data"])
    for decision in decisions:
        if decision["subject_id"] not in artifact_ids:
            raise DomainError("INVALID_LINEAGE", "Unresolved decision subject")
    for insight in service.list_scoped(actor, case_id, Artifact, 5000, kind="Insight"):
        if (
            not set(
                insight["data"]["supporting_evidence_refs"] + insight["data"]["contradicting_evidence_refs"]
            )
            <= ids
        ):
            raise DomainError("INVALID_CITATION", "Unresolved insight evidence")
    if any(not d["is_synthetic"] or d["gate"] in {"G4", "G5"} for d in decisions):
        raise DomainError("FALSE_APPROVAL", "Synthetic flow contains a false real/sample/launch approval")
    for asset in assets:
        if asset["identity"] != "mock":
            raise DomainError("FALSE_CLAIM", "Mock asset misrepresented")
        service.objects.get(asset["sha256"])
    return {
        "valid": True,
        "strict": strict,
        "case_id": case_id,
        "scope": "tested_offline",
        "waiting_for": "G4",
        "publishable": False,
    }
