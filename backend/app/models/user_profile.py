"""
UserProfile — persistent user knowledge accumulated across conversations.
Tracks personality, known topics, interaction count, and tone preference.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Display name the AI learns (e.g. "Efe abi")
    display_name = Column(String(100), nullable=True)
    # Topics the user has discussed: ["kaygı", "öfke", "aile"]
    known_topics = Column(JSONB, default=list)
    # Free-text notes the AI accumulates about the user
    personality_notes = Column(Text, nullable=True)
    # Total conversation turns across all conversations
    interaction_count = Column(Integer, default=0)
    # Last detected mood
    last_mood = Column(String(50), nullable=True)
    # Tone: "formal" → "samimi" (evolves automatically)
    preferred_tone = Column(String(20), default="formal")
    # Long-term preference/memory summary fields populated by memory services.
    spiritual_preferences = Column(JSONB, default=dict)
    behavioral_insights = Column(JSONB, default=dict)
    memory_summary = Column(Text, nullable=True)
    last_memory_summary_at = Column(DateTime(timezone=True), nullable=True)
    # Learned linguistic preferences for prompt adaptation.
    language_style = Column(JSONB, default=dict)
    # Relationship-aware tone used by conversation prompt shaping.
    conversational_tone = Column(String(50), default="polite_formal")
    relationship_start_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
