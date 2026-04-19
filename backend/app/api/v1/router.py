"""
API v1 main router - Aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    content,
    locations,
    memory,
    pathways,
    prayer_times,
)

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(pathways.router, prefix="/pathways", tags=["Pathways"])
api_router.include_router(memory.router, prefix="/memories", tags=["Memories"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(prayer_times.router, prefix="/prayer-times", tags=["Prayer Times"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
