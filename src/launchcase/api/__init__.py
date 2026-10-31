from fastapi import BackgroundTasks, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from launchcase.api.limits import RequestLimit
from launchcase.application.feasibility import FeasibilityService
from launchcase.application.launchpacks import LaunchPackService
from launchcase.application.products import ProductService
from launchcase.application.services import CaseService
from launchcase.application.visuals import VisualService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import (
    BriefRevision,
    CostRequest,
    GateRequest,
    HandoffPreparation,
    ProductBrief,
    ReviewRequest,
    RightsChange,
    RuleAttestation,
    SampleAttestation,
    SourceImport,
    SpecRevision,
    VisualRequest,
)
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.models import (
    Artifact,
    AuditEvent,
    BriefVersion,
    Evidence,
    SourceDocument,
    VisualTask,
)
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run, execute_task


def create_app(settings=None):
    app = FastAPI(title="LaunchCase", version="1.0.0", openapi_url="/api/v1/openapi.json")
    app.add_middleware(RequestLimit, max_bytes=2 * 1024 * 1024)
    service = CaseService(settings or Settings.from_env())
    app.state.service = service

    def identity(authorization: str = Header(default="")):
        if not authorization.startswith("Bearer "):
            raise DomainError("UNAUTHORIZED", "Bearer identity required", 401)
        return service.authenticate(authorization[7:])

    def key(idempotency_key: str = Header(min_length=1, max_length=180)):
        return idempotency_key

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            {
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request does not match the strict contract",
                    "details": [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()],
                }
            },
            status_code=422,
        )

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)

    @app.get("/health")
    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "schema_version": "1.0.0", "mode": "offline", "paid_enabled": False}

    @app.get("/api/v1/capabilities")
    def capabilities():
        return {
            "schema_version": "1.0.0",
            "mode": "differentiation",
            "marketplace": "amazon_us",
            "paid_models": False,
            "external_actions": False,
            "publication": "unavailable",
        }

    @app.post("/api/v1/product-cases", status_code=201)
    def create_case(body: ProductBrief, actor=Depends(identity), request_key=Depends(key)):
        return service.create_case(actor, body, request_key)

    @app.get("/api/v1/product-cases")
    def cases(actor=Depends(identity), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
        return {"items": service.list_cases(actor, limit, offset), "limit": limit, "offset": offset}

    @app.get("/api/v1/product-cases/{case_id}")
    def case(case_id: str, actor=Depends(identity)):
        return service.get_case(actor, case_id)

    @app.patch("/api/v1/product-cases/{case_id}/brief")
    def revise(case_id: str, body: BriefRevision, actor=Depends(identity), request_key=Depends(key)):
        return service.revise_brief(actor, case_id, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/sources/import")
    def source_import(case_id: str, body: SourceImport, actor=Depends(identity), request_key=Depends(key)):
        return service.import_source(actor, case_id, body, request_key)

    @app.get("/api/v1/sources/{source_id}")
    def source(source_id: str, actor=Depends(identity)):
        return service.read_source(actor, source_id)

    @app.get("/api/v1/sources/{source_id}/content")
    def source_content(source_id: str, actor=Depends(identity)):
        return Response(
            service.read_source(actor, source_id, True),
            media_type="text/plain",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    @app.patch("/api/v1/sources/{source_id}/rights")
    def rights(source_id: str, body: RightsChange, actor=Depends(identity), request_key=Depends(key)):
        return service.change_rights(actor, source_id, body, request_key)

    def listing(model, kind=None):
        def endpoint(
            case_id: str,
            actor=Depends(identity),
            limit: int = Query(100, ge=1, le=5000),
            offset: int = Query(0, ge=0),
        ):
            return {"items": service.list_scoped(actor, case_id, model, limit, offset, kind)}

        return endpoint

    for suffix, model in [
        ("sources", SourceDocument),
        ("evidence", Evidence),
        ("activity", AuditEvent),
        ("brief-versions", BriefVersion),
    ]:
        app.add_api_route(f"/api/v1/product-cases/{{case_id}}/{suffix}", listing(model), methods=["GET"])
    app.add_api_route(
        "/api/v1/product-cases/{case_id}/market-snapshots",
        listing(Artifact, "MarketSnapshot"),
        methods=["GET"],
    )
    for suffix, kind in [
        ("insights", "Insight"),
        ("opportunities", "Opportunity"),
        ("research", "Research"),
        ("concepts", "Concept"),
        ("spec-versions", "ProductSpec"),
        ("feasibility", "Feasibility"),
        ("launch-packs", "LaunchPack"),
        ("truth", "ProductTruthSnapshot"),
        ("rules", "RuleSnapshot"),
        ("samples", "SampleValidation"),
        ("handoff-preparations", "HandoffPreparation"),
    ]:
        app.add_api_route(
            f"/api/v1/product-cases/{{case_id}}/{suffix}", listing(Artifact, kind), methods=["GET"]
        )

    @app.post("/api/v1/product-cases/{case_id}/runs/{kind}", status_code=202)
    def run(
        case_id: str,
        kind: str,
        background: BackgroundTasks,
        actor=Depends(identity),
        request_key=Depends(key),
    ):
        task = enqueue_run(service, actor, case_id, kind, request_key)
        background.add_task(execute_task, service, actor, task["id"])
        return task

    @app.get("/api/v1/tasks/{task_id}")
    def task(task_id: str, actor=Depends(identity)):
        return TaskManager(service).get(actor, task_id)

    @app.get("/api/v1/product-cases/{case_id}/gates")
    def gates(case_id: str, actor=Depends(identity)):
        return {"items": ProductService(service).decisions(actor, case_id)}

    @app.get("/api/v1/product-cases/{case_id}/gates/{gate}/subject/{subject_id}")
    def subject(case_id: str, gate: str, subject_id: str, actor=Depends(identity)):
        return ProductService(service).gate_subject(actor, case_id, gate, subject_id)

    @app.post("/api/v1/product-cases/{case_id}/gates/{gate}/decision")
    def decide(case_id: str, gate: str, body: GateRequest, actor=Depends(identity), request_key=Depends(key)):
        return ProductService(service).decide(actor, case_id, gate, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/concepts/{concept_id}/spec-versions")
    def spec_revision(
        case_id: str, concept_id: str, body: SpecRevision, actor=Depends(identity), request_key=Depends(key)
    ):
        return ProductService(service).revise_spec(actor, case_id, concept_id, body, request_key)

    @app.get("/api/v1/product-cases/{case_id}/spec-diff")
    def spec_diff(case_id: str, left: str, right: str, actor=Depends(identity)):
        return ProductService(service).spec_diff(actor, case_id, left, right)

    @app.get("/api/v1/product-cases/{case_id}/events")
    def events(
        case_id: str,
        after: int = Query(0, ge=0),
        last_event_id: int = Header(default=0),
        actor=Depends(identity),
    ):
        import json

        rows = service.replay_events(actor, case_id, max(after, last_event_id))
        body = "".join(f"id: {r['sequence']}\nevent: progress\ndata: {json.dumps(r)}\n\n" for r in rows)
        return Response(
            body + ": reconnect for new events\n\n",
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.post("/api/v1/product-cases/{case_id}/visual-tasks")
    def visual_create(case_id: str, body: VisualRequest, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).create(actor, case_id, body, request_key)

    @app.get("/api/v1/product-cases/{case_id}/visual-tasks")
    def visual_list(case_id: str, actor=Depends(identity)):
        visual = VisualService(service)
        return {
            "items": [visual.get(actor, x["id"]) for x in service.list_scoped(actor, case_id, VisualTask)]
        }

    @app.get("/api/v1/visual-tasks/{task_id}")
    def visual_get(task_id: str, actor=Depends(identity)):
        return VisualService(service).get(actor, task_id)

    @app.post("/api/v1/visual-tasks/{task_id}/approve-plan")
    def visual_approve(task_id: str, body: ReviewRequest, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).approve(actor, task_id, body, request_key)

    @app.post("/api/v1/visual-tasks/{task_id}/submit")
    def visual_submit(task_id: str, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).submit(actor, task_id)

    @app.post("/api/v1/visual-tasks/{task_id}/sync")
    def visual_sync(task_id: str, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).sync(actor, task_id)

    @app.post("/api/v1/visual-tasks/{task_id}/cancel")
    def visual_cancel(task_id: str, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).cancel(actor, task_id)

    @app.get("/api/v1/visual-assets/{asset_id}")
    def visual_asset(asset_id: str, actor=Depends(identity)):
        return VisualService(service).asset(actor, asset_id)

    @app.get("/api/v1/visual-assets/{asset_id}/content")
    def visual_content(asset_id: str, actor=Depends(identity)):
        return Response(
            VisualService(service).asset(actor, asset_id, True),
            media_type="image/png",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    @app.post("/api/v1/visual-assets/{asset_id}/review")
    def visual_review(asset_id: str, body: ReviewRequest, actor=Depends(identity), request_key=Depends(key)):
        return VisualService(service).review(actor, asset_id, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/feasibility")
    def cost(case_id: str, body: CostRequest, actor=Depends(identity), request_key=Depends(key)):
        return FeasibilityService(service).evaluate(actor, case_id, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/sample-attestations")
    def sample(case_id: str, body: SampleAttestation, actor=Depends(identity), request_key=Depends(key)):
        return FeasibilityService(service).sample(actor, case_id, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/rule-attestations")
    def rule(case_id: str, body: RuleAttestation, actor=Depends(identity), request_key=Depends(key)):
        return FeasibilityService(service).rule(actor, case_id, body, request_key)

    @app.post("/api/v1/product-cases/{case_id}/handoff-preparations")
    def prepare_handoff(
        case_id: str, body: HandoffPreparation, actor=Depends(identity), request_key=Depends(key)
    ):
        return LaunchPackService(service).prepare(actor, case_id, body, request_key)

    @app.get("/api/v1/launch-packs/{pack_id}/handoff-receipt")
    def handoff_receipt(pack_id: str, actor=Depends(identity)):
        return LaunchPackService(service).handoff_receipt(actor, pack_id)

    @app.get("/api/v1/launch-packs/{pack_id}/handoff-export")
    def handoff_export(pack_id: str, actor=Depends(identity)):
        return Response(
            LaunchPackService(service).export_handoff(actor, pack_id),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="internal-handoff.zip"'},
        )

    @app.post("/api/v1/product-cases/{case_id}/launch-packs")
    def pack_create(case_id: str, actor=Depends(identity), request_key=Depends(key)):
        return LaunchPackService(service).build(actor, case_id, request_key)

    @app.get("/api/v1/launch-packs/{pack_id}")
    def pack_read(pack_id: str, actor=Depends(identity)):
        return LaunchPackService(service).read(actor, pack_id)

    @app.get("/api/v1/launch-packs/{pack_id}/export")
    def pack_export(pack_id: str, format: str = "json", actor=Depends(identity)):
        data = LaunchPackService(service).export(actor, pack_id, format)
        mime = {"json": "application/json", "md": "text/markdown", "zip": "application/zip"}.get(
            format, "application/octet-stream"
        )
        return Response(
            data,
            media_type=mime,
            headers={
                "Content-Disposition": f'attachment; filename="internal-draft.{format}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    return app


app = create_app()
