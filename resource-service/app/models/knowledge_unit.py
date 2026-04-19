from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class KnowledgeUnit(Base):
    __tablename__ = "knowledge_units"

    id = Column(Integer, primary_key=True)
    source_type = Column(String(50), nullable=False)
    content_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    unit_metadata = Column("metadata", JSONB, nullable=True)
    embedding = Column(Vector(768))
    created_at = Column(DateTime, server_default=func.current_timestamp())

    def __repr__(self) -> str:
        preview = (self.content_text or "")[:20]
        return f"<KnowledgeUnit(id={self.id}, content_text='{preview}...')>"
