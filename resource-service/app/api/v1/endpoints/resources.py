from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.service_auth import require_service_token
from app.domain.content.models import ContentSearchQuery, GraphContextRequest, GraphContextResponse
from app.domain.content.service import ContentService
from app.services.graph_context_service import GraphContextService

router = APIRouter(dependencies=[Depends(require_service_token)])


class ContentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(6, ge=1, le=20)
    source_types: list[str] = Field(default_factory=lambda: ["quran"])


@router.get("/sources")
async def list_content_sources(db: AsyncSession = Depends(get_db)):
    service = ContentService(db)
    sources = await service.list_source_types()
    return {"sources": sources}


@router.post("/search")
async def search_content(
    body: ContentSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    results = await service.search(
        ContentSearchQuery(
            query=body.query,
            limit=body.limit,
            source_types=body.source_types,
        )
    )
    return {"results": [item.model_dump() for item in results]}


@router.get("/items/{content_id}")
async def get_content_item(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    try:
        item = await service.get_content_item(content_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return item.model_dump()


@router.post("/contexts/graph", response_model=GraphContextResponse)
async def get_graph_context(body: GraphContextRequest):
    service = GraphContextService()
    context = await service.get_context(
        user_text=body.text,
        keywords=body.keywords,
        top_k=body.top_k,
    )
    return GraphContextResponse.model_validate(context)
