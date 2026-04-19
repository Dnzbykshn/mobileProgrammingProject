"""
Memory Extraction Service — AI-powered memory extraction from conversations.

After a conversation reaches GENERATED phase (prescription created), this service
analyzes the conversation and extracts structured, timestamped memories with embeddings.

Memory extraction happens asynchronously to avoid blocking the chat response.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid
import json

from app.models.conversation import Conversation, Message
from app.services.ai_service import generate_content, get_embedding
from app.repositories.memory_repository import create_memory


# ──────────────────────────────────────────
# Pydantic schemas for AI structured output
# ──────────────────────────────────────────


class ExtractedMemory(BaseModel):
    """Single extracted memory from conversation."""
    memory_type: str  # emotional_state, life_event, spiritual_preference, goal, progress_milestone
    content: str  # 1-2 sentence summary
    importance: int  # 0-100
    context: Optional[str] = None  # Additional metadata as JSON string (Gemini rejects OBJECT with empty properties)


class MemoryExtractionResponse(BaseModel):
    """AI response containing multiple extracted memories."""
    memories: List[ExtractedMemory]


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _parse_context(context_str: Optional[str]) -> dict:
    """Parse context JSON string from AI into a dict. Returns empty dict on failure."""
    if not context_str:
        return {}
    try:
        parsed = json.loads(context_str)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# ──────────────────────────────────────────
# Memory extraction logic
# ──────────────────────────────────────────


async def extract_memories_from_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> List[uuid.UUID]:
    """
    Extract memories from a completed conversation.
    Returns list of created memory IDs.

    Called after conversation phase = GENERATED (prescription created).
    """
    # Get conversation and messages
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation or not conversation.user_id:
        return []  # Skip anonymous conversations

    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = list(messages_result.scalars().all())

    if len(messages) < 3:
        return []  # Too short for meaningful extraction

    # Format conversation for AI
    conversation_text = "\n".join([
        f"{'Kullanıcı' if m.sender == 'user' else 'Asistan'}: {m.content}"
        for m in messages
    ])

    # AI extraction prompt
    prompt = f"""
    Aşağıdaki manevi terapi konuşmasını analiz et ve önemli anıları çıkar.

    KONUŞMA:
    {conversation_text}

    GÖREV:
    Bu konuşmadan kullanıcı hakkında hatırlanması gereken önemli bilgileri çıkar.
    Her anı için:
    - memory_type: Aşağıdakilerden biri seç
      * emotional_state: Duygusal durum (örn: "Kullanıcı iş stresi nedeniyle kaygı yaşıyor")
      * life_event: Yaşam olayı (örn: "2 haftadır iş yükü artmış")
      * spiritual_preference: Manevi tercih (örn: "Sabah namazı kılmayı seviyor")
      * goal: Hedef (örn: "5 kısa sure ezberlemek istiyor")
      * progress_milestone: Başarı (örn: "7 günlük yolculuğu tamamladı")
    - content: 1-2 cümle özet (kullanıcı hakkında 3. şahıs olarak yaz)
    - importance: 0-100 arası önem skoru (kriz/önemli olaylar: 80-100, rutin: 30-50)
    - context: Ek detaylar JSON string olarak (örn: '{{"trigger": "iş", "duration": "2 hafta"}}'). Eğer yoksa boş string döndür.

    KURALLAR:
    - Sadece önemli ve hatırlanmaya değer bilgileri çıkar (max 5 anı)
    - Her anı benzersiz ve bilgilendirici olmalı
    - Kullanıcının özel hayatını ve duygularını doğru yansıt
    - Kriz belirtileri varsa (intihar, zarar verme) importance=95+ ve is_sensitive=true

    JSON array döndür.
    """

    try:
        response = await generate_content(prompt, response_schema=MemoryExtractionResponse)
        extraction = MemoryExtractionResponse(**response.parsed.model_dump())
    except Exception as e:
        print(f"❌ Memory extraction failed: {e}")
        return []

    # Create memories with embeddings
    created_ids = []
    for mem in extraction.memories:
        # Generate embedding for semantic search
        embedding = await get_embedding(mem.content)

        # Determine expiration based on type
        expires_at = None
        if mem.memory_type == "emotional_state":
            expires_at = datetime.now(timezone.utc) + timedelta(days=180)  # 6 months
        elif mem.memory_type == "life_event":
            expires_at = datetime.now(timezone.utc) + timedelta(days=365)  # 1 year
        elif mem.memory_type == "behavioral_pattern":
            expires_at = datetime.now(timezone.utc) + timedelta(days=90)  # 3 months
        # spiritual_preference, goal, progress_milestone: no expiration (permanent unless user deletes)

        # Detect sensitive content
        is_sensitive = mem.importance >= 90 or any(
            keyword in mem.content.lower()
            for keyword in ["intihar", "zarar", "ölmek", "kriz", "çaresiz"]
        )

        memory = await create_memory(
            db,
            user_id=conversation.user_id,
            memory_type=mem.memory_type,
            content=mem.content,
            embedding=embedding,
            context=_parse_context(mem.context),  # Parse JSON string to dict
            importance_score=min(mem.importance, 100),
            conversation_id=conversation_id,
            is_sensitive=is_sensitive,
            expires_at=expires_at,
        )
        created_ids.append(memory.id)

    await db.commit()

    print(f"✅ Extracted {len(created_ids)} memories from conversation {conversation_id}")
    return created_ids


async def extract_milestone_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    pathway_id: uuid.UUID,
    milestone_content: str,
) -> Optional[uuid.UUID]:
    """
    Extract a progress milestone memory when a user completes a pathway milestone.

    Called from the pathway flow when a 7-day pathway milestone is reached.
    """
    embedding = await get_embedding(milestone_content)

    memory = await create_memory(
        db,
        user_id=user_id,
        memory_type="progress_milestone",
        content=milestone_content,
        embedding=embedding,
        importance_score=85,  # Milestones are important
        pathway_id=pathway_id,
        is_sensitive=False,
        expires_at=None,  # Milestones are permanent
    )

    await db.commit()

    print(f"✅ Created milestone memory for pathway {pathway_id}")
    return memory.id
