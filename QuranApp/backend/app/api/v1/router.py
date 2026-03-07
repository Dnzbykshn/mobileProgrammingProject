"""
API v1 main router - Aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import chat, auth, search, plan, prescriptions, memory, prayer_times, locations

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(plan.router, prefix="/plans", tags=["Plans"])
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["Prescriptions"])
api_router.include_router(memory.router, prefix="/memories", tags=["Memories"])
api_router.include_router(prayer_times.router, prefix="/prayer-times", tags=["Prayer Times"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
