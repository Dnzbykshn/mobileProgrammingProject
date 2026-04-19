from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Pathway(Base):
    __tablename__ = "pathways"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    title = Column(String(255), nullable=True)
    pathway_type = Column(String(50), nullable=True)
    topic_summary = Column(Text, nullable=True)
    topic_keywords = Column(JSONB, nullable=True)
    total_days = Column(Integer, default=8)
    current_day = Column(Integer, default=0)
    day0_skipped = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PathwayTask(Base):
    __tablename__ = "pathway_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pathway_id = Column(UUID(as_uuid=True), ForeignKey("pathways.id", ondelete="CASCADE"))
    day_number = Column(Integer, nullable=False)
    task_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    task_metadata = Column("task_metadata", JSONB, nullable=True)
