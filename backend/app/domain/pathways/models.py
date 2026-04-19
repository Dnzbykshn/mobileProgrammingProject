from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


PathwaySource = Literal["chat", "manual", "admin", "template"]


class PathwayTaskDraft(BaseModel):
    day_number: int
    task_type: str
    title: str
    description: str = ""
    duration_minutes: int = 5
    order_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class PathwayDayDraft(BaseModel):
    day_number: int
    tasks: list[PathwayTaskDraft] = Field(default_factory=list)


class PathwayBlueprint(BaseModel):
    title: str
    pathway_type: str
    topic_summary: str = ""
    topic_keywords: list[str] = Field(default_factory=list)
    source: PathwaySource = "template"
    total_days: int = 8
    days: list[PathwayDayDraft] = Field(default_factory=list)


class PathwaySummary(BaseModel):
    id: str
    title: str
    pathway_type: str
    topic_summary: str | None = None
    current_day: int
    total_days: int
    status: str
    started_at: datetime | None = None
