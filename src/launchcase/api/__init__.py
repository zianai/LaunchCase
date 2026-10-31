from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from launchcase.domain.common import DomainError


def create_app():
    app = FastAPI(title="LaunchCase", version="1.0.0", openapi_url="/api/v1/openapi.json")

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

    return app


app = create_app()
