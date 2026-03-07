"""
Search endpoint - Test/debug endpoint for search functionality.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.search_router import SearchRouter

router = APIRouter()

# Singleton search router (no DB state)
_search_router = None


def get_search_router():
    global _search_router
    if _search_router is None:
        _search_router = SearchRouter()
    return _search_router


class SearchRequest(BaseModel):
    query: str
    mode: Optional[str] = None  # SIMPLE, RULE, SMART, or None for AUTO


@router.post("/query")
async def search_query(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Test search endpoint. Supports forced mode selection."""
    sr = get_search_router()
    results = await sr.run(request.query, db=db, force_mode=request.mode)

    formatted = []
    for r in results:
        formatted.append(
            {
                "content_text": r.get("content_text", ""),
                "explanation": r.get("explanation", ""),
                "metadata": r.get("metadata", {}),
            }
        )

    return {"query": request.query, "mode": request.mode or "AUTO", "results": formatted}
