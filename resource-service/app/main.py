from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.models.knowledge_unit import KnowledgeUnit  # noqa: F401
from app.services.graph_context_service import GraphContextService


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Resource service starting...")
    yield
    driver = GraphContextService._driver
    if driver is not None:
        driver.close()
        GraphContextService._driver = None
    print("👋 Resource service shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"❌ Resource service error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"status": "active", "service": settings.PROJECT_NAME}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "resource-service",
        "graph_context_enabled": settings.GRAPH_CONTEXT_ENABLED,
    }
