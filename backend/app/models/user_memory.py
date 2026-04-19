"""
UserMemory — Long-term episodic memory for personalized AI interactions.
Stores timestamped user experiences with vector embeddings for semantic retrieval.

Memory Types:
- emotional_state: User's emotional patterns (e.g., "Kaygı yaşıyor, iş stresi nedeniyle")
- life_event: Significant life events (e.g., "5 Şubat'ta aile çatışması belirtti")
- spiritual_preference: Spiritual preferences (e.g., "Yasin suresini seviyor")
- goal: User goals (e.g., "5 kısa sure ezberlemek istiyor")
- progress_milestone: Achievements (e.g., "7 günlük kaygı yolculuğunu tamamladı")
- behavioral_pattern: Usage patterns (e.g., "Akşam 20:00'de aktif")
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.db.database import Base


class UserMemory(Base):
    __tablename__ = "user_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Memory content
    memory_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    context = Column(JSONB, default=dict)  # Additional structured metadata

    # Vector embedding for semantic search (768 dimensions for Gemini embeddings)
    embedding = Column(Vector(768))

    # Relevance scoring
    importance_score = Column(Integer, default=50)  # 0-100 scale
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Source tracking
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    pathway_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pathways.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Temporal
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Privacy controls
    is_deleted = Column(Boolean, default=False)  # Soft delete
    is_sensitive = Column(Boolean, default=False)  # Crisis/personal data flag
