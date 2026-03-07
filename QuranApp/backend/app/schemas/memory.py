"""
Memory API schemas — Request/response models for memory endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class MemoryCreate(BaseModel):
    """Request schema for creating a new memory."""
    memory_type: str = Field(
        ...,
        description="Memory type",
        example="emotional_state",
        pattern="^(emotional_state|life_event|spiritual_preference|goal|progress_milestone|behavioral_pattern)$"
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Memory content (1-2 sentences)",
        example="Kullanıcı iş stresi nedeniyle kaygı yaşıyor"
    )
    context: Optional[dict] = Field(
        default={},
        description="Additional structured metadata",
        example={"trigger": "iş", "duration": "2 hafta"}
    )
    importance_score: Optional[int] = Field(
        default=50,
        ge=0,
        le=100,
        description="Importance score (0-100)",
        example=75
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Source conversation ID (if from conversation)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "memory_type": "emotional_state",
                "content": "Kullanıcı iş stresi nedeniyle kaygı yaşıyor",
                "context": {"trigger": "iş", "duration": "2 hafta"},
                "importance_score": 75,
            }
        }


class MemoryResponse(BaseModel):
    """Response schema for memory objects."""
    id: UUID = Field(..., description="Memory unique ID")
    user_id: UUID = Field(..., description="Owner user ID")
    memory_type: str = Field(..., description="Memory type", example="emotional_state")
    content: str = Field(..., description="Memory content")
    context: dict = Field(default={}, description="Additional metadata")
    importance_score: int = Field(..., description="Importance (0-100)", example=75)
    access_count: int = Field(..., description="How many times retrieved", example=3)
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp (null = permanent)")
    is_sensitive: bool = Field(..., description="Sensitive/crisis content flag")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "memory_type": "emotional_state",
                "content": "Kullanıcı iş stresi nedeniyle kaygı yaşıyor",
                "context": {"trigger": "iş", "duration": "2 hafta"},
                "importance_score": 75,
                "access_count": 3,
                "created_at": "2026-02-14T10:30:00Z",
                "expires_at": "2026-08-14T10:30:00Z",
                "is_sensitive": False,
            }
        }


class MemoryListResponse(BaseModel):
    """Response schema for list of memories."""
    memories: List[MemoryResponse] = Field(..., description="List of memories")
    total: int = Field(..., description="Total count (before pagination)")

    class Config:
        json_schema_extra = {
            "example": {
                "memories": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "memory_type": "emotional_state",
                        "content": "Kullanıcı iş stresi nedeniyle kaygı yaşıyor",
                        "context": {},
                        "importance_score": 75,
                        "access_count": 3,
                        "created_at": "2026-02-14T10:30:00Z",
                        "expires_at": "2026-08-14T10:30:00Z",
                        "is_sensitive": False,
                    }
                ],
                "total": 42,
            }
        }


class MemorySearchRequest(BaseModel):
    """Request schema for semantic memory search."""
    search_query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Search query (will be embedded for semantic search)",
        example="iş stresi kaygı"
    )
    limit: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Max results to return",
        example=5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search_query": "iş stresi kaygı",
                "limit": 5,
            }
        }


class PrivacyReportResponse(BaseModel):
    """Response schema for privacy dashboard."""
    total_memories: int = Field(..., description="Total memory count", example=42)
    by_type: dict = Field(
        ...,
        description="Breakdown by memory type",
        example={"emotional_state": 15, "life_event": 8, "spiritual_preference": 12}
    )
    oldest_memory: Optional[str] = Field(
        None,
        description="Oldest memory timestamp (ISO format)",
        example="2025-08-15T10:00:00Z"
    )
    storage_size_kb: float = Field(
        ...,
        description="Estimated storage size in KB",
        example=156.5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_memories": 42,
                "by_type": {
                    "emotional_state": 15,
                    "life_event": 8,
                    "spiritual_preference": 12,
                    "goal": 5,
                    "progress_milestone": 2,
                },
                "oldest_memory": "2025-08-15T10:00:00Z",
                "storage_size_kb": 156.5,
            }
        }


class MemoryDeleteResponse(BaseModel):
    """Response schema for memory deletion."""
    detail: str = Field(..., description="Operation status", example="Memory deleted successfully")
    deleted_id: UUID = Field(..., description="Deleted memory ID")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Memory deleted successfully",
                "deleted_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
