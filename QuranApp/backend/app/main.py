"""
FastAPI Application Entry Point.
Async-first with lifespan context manager.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.rate_limit import limiter
from app.services.master_brain import MasterBrain

# Import all models so SQLAlchemy knows about them
from app.models import user, conversation, prescription, user_profile, refresh_token, user_memory  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle."""
    # --- Startup ---
    print("🚀 Server Starting...")

    # Initialize Master Brain (sync — runs once)
    app.state.brain = MasterBrain()

    # Initialize async Redis
    try:
        app.state.redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            socket_connect_timeout=5,
            decode_responses=True,
        )
        await app.state.redis.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis unavailable: {e}")
        app.state.redis = None

    yield

    # --- Shutdown ---
    if app.state.redis:
        await app.state.redis.close()
    print("👋 Server shutting down")


app = FastAPI(
    title="Spiritual Therapy AI API",
    description="Backend for Islamic Mental Health App",
    version="2.0.0",
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
    return {"status": "active", "service": "Spiritual Therapy API"}


@app.get("/health")
async def health(request: Request):
    return {
        "status": "healthy",
        "redis": request.app.state.redis is not None,
        "brain": request.app.state.brain is not None,
    }
