"""
FastAPI Application Entry Point.
Async-first with lifespan context manager.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.rate_limit import limiter
from app.integrations.resource_service import ResourceServiceClient

# Import all models so SQLAlchemy knows about them
from app.models import user, conversation, pathway, pathway_definition, user_profile, refresh_token, revoked_access_token, user_memory  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle."""
    print("🚀 Server Starting...")

    yield

    await ResourceServiceClient.aclose()
    print("👋 Server shutting down")


app = FastAPI(
    title="QuranApp App Service",
    description="App-service backend for the QuranApp mobile product",
    version="3.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS_LIST,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Device-ID"],
)

# --- Exception Handlers ---
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def health_check():
    return {"status": "active", "service": "quranapp-app-service"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "app-service",
        "orchestration": "langgraph-ready",
    }
