"""
Plan schemas — request/response models for 7-day journey system.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlanCreateRequest(BaseModel):
    prescription_id: Optional[str] = Field(None, description="ID of the prescription if generated from chat", example="550e8400-e29b-41d4-a716-446655440000")
    journey_type: str = Field("anxiety_management", description="Type of spiritual journey (e.g., anxiety_management, grief_healing)", example="anxiety_management")
    user_input: Optional[str] = Field(None, description="Original user complaint for AI context customization", example="Çok stresliyim ve uyuyamıyorum.")

    class Config:
        json_schema_extra = {
            "example": {
                "journey_type": "anxiety_management",
                "user_input": "İçim daralıyor, huzur bulmak istiyorum."
            }
        }


class TaskResponse(BaseModel):
    id: str = Field(..., description="Unique task ID")
    day_number: int = Field(..., description="Day number of the plan (0-7)", example=1)
    task_type: str = Field(..., description="Type of task: morning, evening, journal, day0_verse, day0_dua, day0_esma, day0_routine", example="morning")
    title: str = Field(..., description="Task title", example="Sabah Zikri")
    description: Optional[str] = Field(None, description="Detailed instructions or content", example="Subhanallah (33 kere) çekelim.")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes", example=5)
    order_index: int = Field(..., description="Order of the task within the day")
    is_completed: bool = Field(False, description="Completion status")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when completed")
    task_metadata: Optional[dict] = Field(None, description="Additional data for Day 0 tasks (verse, dua, esma content)")


class DayGroup(BaseModel):
    day_number: int
    tasks: List[TaskResponse]
    is_complete: bool = False
    is_day0: bool = False
    is_skippable: bool = False


class PlanResponse(BaseModel):
    id: str = Field(..., description="Plan ID")
    journey_title: str = Field(..., description="Title of the 8-day journey", example="Huzur Yolculuğu")
    journey_type: str = Field(..., description="Internal journey type code")
    total_days: int = Field(8, description="Total duration of the plan")
    current_day: int = Field(0, description="Current active day (0-7)")
    status: str = Field("active", description="Plan status: active, completed, archived")
    started_at: Optional[datetime] = Field(None, description="Plan start timestamp")
    days: List[DayGroup] = Field([], description="Grouped tasks by day")
    topic_summary: Optional[str] = Field(None, description="AI summary of journey topic")
    day0_skipped: bool = Field(False, description="Whether Day 0 was skipped")


class DayCompleteRequest(BaseModel):
    reflection: Optional[str] = Field(None, description="User's reflection or journal entry for the day", example="Bugün kendimi çok daha iyi hissettim.")


class PrescriptionGenerateRequest(BaseModel):
    message: str = Field(..., description="User's message or context to generate prescription from", example="Kendimi çok yalnız hissediyorum.")


class JourneySummary(BaseModel):
    """Lightweight summary for the journey list view."""
    plan_id: str
    title: str
    journey_type: str
    topic_summary: Optional[str]
    current_day: int
    total_days: int
    status: str
    today_completed: int
    today_total: int
    started_at: Optional[str]


class PrescriptionResponse(BaseModel):
    id: str = Field(..., description="Prescription UUID")
    title: Optional[str] = Field(None, description="Title of the diagnosis/state", example="Yalnızlık ve Ünsiyet")
    description: Optional[str] = Field(None, description="General advice or summary", example="Allah'a yakınlaşmak en büyük dostluktur.")
    emotion_category: Optional[str] = Field(None, description="Detected emotion category", example="yalnızlık")
    prescription_data: Optional[dict] = Field(None, description="Full unstructured prescription data from AI")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True
