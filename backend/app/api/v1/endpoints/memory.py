"""
Memory API endpoints - CRUD operations and semantic search for user memories.

Provides:
- Memory creation (manual or AI-extracted)
- Memory listing with filtering by type
- Semantic search with vector similarity
- Soft delete with authorization check
- Privacy dashboard (storage stats, retention info)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemoryListResponse,
    MemorySearchRequest,
    PrivacyReportResponse,
    MemoryDeleteResponse,
)
from app.core.dependencies import get_db, get_current_user
from app.repositories import memory_repository
from app.services.ai_service import get_embedding
from app.models.user import User

router = APIRouter()


@router.post("/memories", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory_data: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new memory entry.

    Memory types:
    - emotional_state: Emotional/psychological state (expires in 6 months)
    - life_event: Significant life events (expires in 1 year)
    - spiritual_preference: Spiritual preferences (permanent)
    - goal: User goals (expires in 1 year)
    - progress_milestone: Achievements (permanent)
    - behavioral_pattern: Behavioral patterns (rolling 3 months)

    AI automatically extracts memories from conversations,
    but users can also manually create memories via this endpoint.
    """
    # Validate memory type
    valid_types = {
        "emotional_state",
        "life_event",
        "spiritual_preference",
        "goal",
        "progress_milestone",
        "behavioral_pattern",
    }
    if memory_data.memory_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory_type. Must be one of: {', '.join(valid_types)}",
        )

    # Generate embedding for semantic search
    try:
        embedding = await get_embedding(memory_data.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}",
        )

    # Determine expiration based on type
    from datetime import datetime, timedelta, timezone
    expires_at = None
    if memory_data.memory_type == "emotional_state":
        expires_at = datetime.now(timezone.utc) + timedelta(days=180)  # 6 months
    elif memory_data.memory_type == "life_event":
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)  # 1 year
    elif memory_data.memory_type == "behavioral_pattern":
        expires_at = datetime.now(timezone.utc) + timedelta(days=90)  # 3 months
    # spiritual_preference, goal, progress_milestone: permanent (None)

    # Detect sensitive content
    is_sensitive = memory_data.importance_score >= 90 or any(
        keyword in memory_data.content.lower()
        for keyword in ["intihar", "zarar", "ölmek", "kriz", "çaresiz"]
    )

    # Create memory
    memory = await memory_repository.create_memory(
        db,
        user_id=current_user.id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        embedding=embedding,
        context=memory_data.context or {},
        importance_score=memory_data.importance_score,
        conversation_id=memory_data.conversation_id,
        is_sensitive=is_sensitive,
        expires_at=expires_at,
    )

    await db.commit()
    await db.refresh(memory)

    return memory


@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List user's memories with optional filtering by type.

    Results are sorted by importance_score (desc) and created_at (desc).
    Expired and deleted memories are excluded.
    """
    memories = await memory_repository.list_memories(
        db,
        user_id=current_user.id,
        memory_type=memory_type,
        limit=limit,
        offset=offset,
    )

    # Get total count for pagination
    from sqlalchemy import select, func, and_
    from app.models.user_memory import UserMemory

    count_query = select(func.count()).select_from(UserMemory).where(
        and_(
            UserMemory.user_id == current_user.id,
            UserMemory.is_deleted == False,
        )
    )
    if memory_type:
        count_query = count_query.where(UserMemory.memory_type == memory_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    return MemoryListResponse(memories=memories, total=total)


@router.post("/memories/search", response_model=MemoryListResponse)
async def search_memories(
    search_request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search across user's memories using vector similarity.

    The search query is embedded and compared against all memory embeddings
    using cosine distance. Returns the most semantically similar memories.

    Example: "iş stresi kaygı" will find memories about work-related anxiety
    even if exact words don't match.
    """
    # Generate query embedding
    try:
        query_embedding = await get_embedding(search_request.search_query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate search embedding: {str(e)}",
        )

    # Semantic search
    memories = await memory_repository.search_memories_semantic(
        db,
        user_id=current_user.id,
        query_embedding=query_embedding,
        limit=search_request.limit,
    )

    return MemoryListResponse(memories=memories, total=len(memories))


@router.delete("/memories/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a memory.

    Sets is_deleted=True instead of permanently removing the record.
    Authorization check: memory must belong to the current user.

    Deleted memories are excluded from search, retrieval, and listing.
    """
    # Validate UUID
    try:
        mem_uuid = uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")

    # Soft delete
    deleted = await memory_repository.soft_delete_memory(
        db,
        memory_id=mem_uuid,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Memory not found or already deleted",
        )

    await db.commit()

    return MemoryDeleteResponse(
        detail="Memory deleted successfully",
        deleted_id=mem_uuid,
    )


@router.get("/memories/privacy-report", response_model=PrivacyReportResponse)
async def get_privacy_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Privacy dashboard: memory statistics and storage info.

    Returns:
    - Total memory count
    - Breakdown by memory type
    - Oldest memory timestamp
    - Estimated storage size in KB

    Used by mobile app's privacy control screen.
    """
    report = await memory_repository.get_privacy_report(db, current_user.id)
    return PrivacyReportResponse(**report)
