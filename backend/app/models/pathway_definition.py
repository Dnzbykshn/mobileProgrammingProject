from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class PathwayDefinition(Base):
    __tablename__ = "pathway_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    pathway_type = Column(String(50), nullable=False)
    summary = Column(Text, nullable=True)
    total_days = Column(Integer, default=8, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PathwayDefinitionDay(Base):
    __tablename__ = "pathway_definition_days"
    __table_args__ = (
        UniqueConstraint("definition_id", "day_number", name="uq_pathway_definition_days_definition_day"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    definition_id = Column(UUID(as_uuid=True), ForeignKey("pathway_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_day0 = Column(Boolean, default=False, nullable=False)
    is_skippable = Column(Boolean, default=False, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)


class PathwayDefinitionTask(Base):
    __tablename__ = "pathway_definition_tasks"
    __table_args__ = (
        UniqueConstraint("definition_day_id", "order_index", name="uq_pathway_definition_tasks_day_order"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    definition_day_id = Column(UUID(as_uuid=True), ForeignKey("pathway_definition_days.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False)
    task_metadata = Column(JSONB, nullable=True)
