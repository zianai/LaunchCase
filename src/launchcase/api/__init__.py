from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from launchcase.application.services import CaseService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import BriefRevision, ProductBrief, RightsChange, SourceImport
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.models import Artifact, AuditEvent, BriefVersion, Evidence, SourceDocument


def create_app(settings=None):
    app = FastAPI(title="LaunchCase", version="1.0.0", openapi_url="/api/v1/openapi.json")
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
        return JSONResponse({"error": {"code": "INVALID_REQUEST", "message": "Request does not match the strict contract",
            "details": [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()]}}, status_code=422)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)

    @app.get("/health")
    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "schema_version": "1.0.0", "mode": "offline", "paid_enabled": False}

    @app.get("/api/v1/capabilities")
    def capabilities():
        return {"schema_version": "1.0.0", "mode": "differentiation", "marketplace": "amazon_us",
                "paid_models": False, "external_actions": False, "publication": "unavailable"}

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
        return Response(service.read_source(actor, source_id, True), media_type="text/plain", headers={"X-Content-Type-Options": "nosniff"})

    @app.patch("/api/v1/sources/{source_id}/rights")
    def rights(source_id: str, body: RightsChange, actor=Depends(identity), request_key=Depends(key)):
        return service.change_rights(actor, source_id, body, request_key)

    def listing(model, kind=None):
        def endpoint(case_id: str, actor=Depends(identity), limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0)):
            return {"items": service.list_scoped(actor, case_id, model, limit, offset, kind)}
        return endpoint

    for suffix, model in [("sources", SourceDocument), ("evidence", Evidence), ("activity", AuditEvent), ("brief-versions", BriefVersion)]:
        app.add_api_route(f"/api/v1/product-cases/{{case_id}}/{suffix}", listing(model), methods=["GET"])
    app.add_api_route("/api/v1/product-cases/{case_id}/market-snapshots", listing(Artifact, "MarketSnapshot"), methods=["GET"])

    return app


app = create_app()
