from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContentSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=20)
    source_types: list[str] = Field(default_factory=list)


class ContentHit(BaseModel):
    id: int
    source_type: str
    content_text: str
    explanation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    score_hint: str = "semantic"


class GraphContextRequest(BaseModel):
    text: str = Field(default="")
    keywords: list[str] = Field(default_factory=list)
    top_k: int = Field(default=8, ge=1, le=20)


class GraphPassage(BaseModel):
    id: int | None = None
    translation: str = ""
    explanation: str = ""


class GraphContextResponse(BaseModel):
    graph_keywords: list[str] = Field(default_factory=list)
    graph_passages: list[GraphPassage] = Field(default_factory=list)
    graph_sub_categories: list[str] = Field(default_factory=list)
    graph_root_categories: list[str] = Field(default_factory=list)
    graph_summary: str = ""
    suggested_pathway_type: str | None = None
