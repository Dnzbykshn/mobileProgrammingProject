from sqlalchemy import Column, Integer, Text, String
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.database import Base

class KnowledgeUnit(Base):
    __tablename__ = "knowledge_units"

    id = Column(Integer, primary_key=True, index=True)
    content_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    unit_metadata = Column("metadata", JSONB, nullable=True)  # Mapped to 'metadata' column in DB
    embedding = Column(Vector(768))  # Assuming 768 dim from config (Gemini)

    def __repr__(self):
        return f"<KnowledgeUnit(id={self.id}, content_text='{self.content_text[:20]}...')>"
