"""Content endpoints exposed by the app service.

These routes are intentionally thin. The app service owns the mobile-facing API,
while the resource service owns search, retrieval, graph context, and source
metadata. This module simply validates the public request shape and proxies it
through the resource boundary.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.integrations.resource_service import ResourceServiceClient

router = APIRouter()


class ContentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(6, ge=1, le=20)
    source_types: list[str] = Field(default_factory=lambda: ["quran"])


@router.get("/sources")
async def list_content_sources():
    client = ResourceServiceClient()
    return await client.list_sources()


@router.post("/search")
async def search_content(body: ContentSearchRequest):
    client = ResourceServiceClient()
    return await client.search_content(
        query=body.query,
        limit=body.limit,
        source_types=body.source_types,
    )


@router.get("/items/{content_id}")
async def get_content_item(content_id: int):
    client = ResourceServiceClient()
    return await client.get_content_item(content_id)
