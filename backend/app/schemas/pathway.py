"""Canonical pathway schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PathwayCreateRequest(BaseModel):
    pathway_type: Literal[
        "anxiety_management",
        "grief_healing",
        "anger_control",
        "spiritual_growth",
    ] = Field(
        "anxiety_management",
        description="Internal pathway type code.",
        example="anxiety_management",
    )
    user_input: Optional[str] = Field(
        None,
        description="Optional user context used to personalize the pathway.",
        example="İçim daralıyor, huzur bulmak istiyorum.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "pathway_type": "anxiety_management",
                "user_input": "İçim daralıyor, huzur bulmak istiyorum.",
            }
        }


class PathwayTaskResponse(BaseModel):
    id: str = Field(..., description="Unique task ID")
    day_number: int = Field(..., description="Day number of the pathway", example=1)
    task_type: str = Field(
        ...,
        description="Task type such as morning, evening, reflection, day0_verse, day0_routine.",
        example="morning",
    )
    title: str = Field(..., description="Task title", example="Sabah nefesi")
    description: Optional[str] = Field(None, description="Task guidance text")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    order_index: int = Field(..., description="Order of the task within the day")
    is_completed: bool = Field(False, description="Completion status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    task_metadata: Optional[dict] = Field(None, description="Additional structured metadata")


class PathwayDayGroup(BaseModel):
    day_number: int
    tasks: List[PathwayTaskResponse]
    is_complete: bool = False
    is_day0: bool = False
    is_skippable: bool = False


class PathwayResponse(BaseModel):
    id: str = Field(..., description="Pathway ID")
    title: str = Field(..., description="Pathway title", example="Sükûnet Yolu")
    pathway_type: str = Field(..., description="Internal pathway type code")
    total_days: int = Field(8, description="Total duration")
    current_day: int = Field(0, description="Current active day")
    status: str = Field("active", description="Pathway status")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    days: List[PathwayDayGroup] = Field(default_factory=list, description="Grouped tasks by day")
    topic_summary: Optional[str] = Field(None, description="Summary of the current pathway topic")
    day0_skipped: bool = Field(False, description="Whether the intro day was skipped")


class PathwayDayCompleteRequest(BaseModel):
    reflection: Optional[str] = Field(
        None,
        description="Optional reflection text for the day.",
        example="Bugün biraz daha sakin kaldım.",
    )


class PathwaySummary(BaseModel):
    pathway_id: str
    title: str
    pathway_type: str
    topic_summary: Optional[str]
    current_day: int
    total_days: int
    status: str
    today_completed: int
    today_total: int
    started_at: Optional[str]


class PathwayDefinitionTaskResponse(BaseModel):
    id: str
    task_type: str
    title: str
    description: Optional[str]
    duration_minutes: Optional[int]
    order_index: int
    task_metadata: Optional[dict]


class PathwayDefinitionDayResponse(BaseModel):
    day_number: int
    title: Optional[str]
    description: Optional[str]
    is_day0: bool
    is_skippable: bool
    tasks: List[PathwayDefinitionTaskResponse] = Field(default_factory=list)


class PathwayDefinitionSummary(BaseModel):
    id: str
    slug: str
    title: str
    pathway_type: str
    summary: Optional[str]
    total_days: int


class PathwayDefinitionResponse(PathwayDefinitionSummary):
    days: List[PathwayDefinitionDayResponse] = Field(default_factory=list)


class PathwayDefinitionStartRequest(BaseModel):
    conversation_id: Optional[str] = None
    topic_summary: Optional[str] = None
    topic_keywords: List[str] = Field(default_factory=list)


