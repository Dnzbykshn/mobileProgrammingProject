"""
Memory repository — async database operations for user memories.
Implements hybrid search with semantic similarity + recency + importance scoring.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_
from typing import Optional, List
from datetime import datetime, timezone
import math
import uuid

from app.models.user_memory import UserMemory


async def create_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    memory_type: str,
    content: str,
    embedding: List[float],
    *,
    context: Optional[dict] = None,
    importance_score: int = 50,
    conversation_id: Optional[uuid.UUID] = None,
    pathway_id: Optional[uuid.UUID] = None,
    is_sensitive: bool = False,
    expires_at: Optional[datetime] = None,
) -> UserMemory:
    """Create a new memory entry with vector embedding."""
    memory = UserMemory(
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        context=context or {},
        embedding=embedding,
        importance_score=importance_score,
        conversation_id=conversation_id,
        pathway_id=pathway_id,
        is_sensitive=is_sensitive,
        expires_at=expires_at,
    )
    db.add(memory)
    await db.flush()
    return memory


async def get_memory_by_id(
    db: AsyncSession,
    memory_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[UserMemory]:
    """Get a specific memory by ID (authorization check: must belong to user)."""
    result = await db.execute(
        select(UserMemory).where(
            and_(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id,
                UserMemory.is_deleted == False,
            )
        )
    )
    return result.scalar_one_or_none()


async def list_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    memory_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[UserMemory]:
    """List user memories with optional filtering by type."""
    query = select(UserMemory).where(
        and_(
            UserMemory.user_id == user_id,
            UserMemory.is_deleted == False,
        )
    )

    if memory_type:
        query = query.where(UserMemory.memory_type == memory_type)

    query = query.order_by(
        UserMemory.importance_score.desc(),
        UserMemory.created_at.desc(),
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def soft_delete_memory(
    db: AsyncSession,
    memory_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Soft delete a memory (sets is_deleted=True). Returns True if deleted."""
    memory = await get_memory_by_id(db, memory_id, user_id)
    if not memory:
        return False

    memory.is_deleted = True
    await db.flush()
    return True


async def retrieve_relevant_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    query_embedding: List[float],
    limit: int = 4,
) -> List[UserMemory]:
    """
    Hybrid retrieval: semantic search + recency boost + importance weighting.

    Scoring formula:
    final_score = (importance / 100) × recency_decay × access_boost / (1 + semantic_distance)

    recency_decay = exp(-age_days / 30)  # Halves every ~21 days
    access_boost = min(1 + (access_count × 0.1), 2.0)  # +10% per access, max 2x
    semantic_distance = cosine distance from query embedding
    """
    # Convert embedding list to pgvector format
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    # Use direct string formatting for vector since bindparam doesn't work well with custom types
    sql_query = f"""
        WITH scored_memories AS (
            SELECT
                id,
                user_id,
                memory_type,
                content,
                context,
                importance_score,
                access_count,
                created_at,
                conversation_id,
                pathway_id,
                is_sensitive,
                -- Semantic distance (cosine distance, 0 = identical, 2 = opposite)
                (embedding <=> '{embedding_str}'::vector) as semantic_distance,
                -- Recency score (0-1, decays over 30 days)
                EXP(-EXTRACT(EPOCH FROM (NOW() - created_at)) / (30 * 86400.0)) as recency_score,
                -- Access boost (0.1 per access, max 2x)
                LEAST(1.0 + (access_count * 0.1), 2.0) as access_boost
            FROM user_memories
            WHERE user_id = :user_id
              AND is_deleted = FALSE
              AND (expires_at IS NULL OR expires_at > NOW())
        )
        SELECT
            id, user_id, memory_type, content, context,
            importance_score, access_count, created_at,
            conversation_id, pathway_id, is_sensitive,
            -- Combined hybrid score
            ((importance_score / 100.0) * recency_score * access_boost) / (1.0 + semantic_distance) as final_score
        FROM scored_memories
        ORDER BY final_score DESC
        LIMIT :lim
    """

    result = await db.execute(
        text(sql_query),
        {
            "user_id": str(user_id),
            "lim": limit,
        }
    )

    # Fetch memories and increment access count
    memory_ids = [row.id for row in result.fetchall()]
    if not memory_ids:
        return []

    # Get full memory objects
    memories_result = await db.execute(
        select(UserMemory).where(UserMemory.id.in_(memory_ids))
    )
    memories = list(memories_result.scalars().all())

    # Update access stats
    for memory in memories:
        memory.access_count += 1
        memory.last_accessed_at = datetime.now(timezone.utc)

    await db.flush()

    # Sort by original score order
    memories_dict = {str(m.id): m for m in memories}
    sorted_memories = [memories_dict[str(mid)] for mid in memory_ids if str(mid) in memories_dict]

    return sorted_memories


async def search_memories_semantic(
    db: AsyncSession,
    user_id: uuid.UUID,
    query_embedding: List[float],
    limit: int = 5,
) -> List[UserMemory]:
    """
    Pure semantic search (no recency/importance weighting).
    Used for user-initiated search in Memory Timeline UI.
    """
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    # Use direct string formatting for vector
    sql_query = f"""
        SELECT id, user_id, memory_type, content, context,
               importance_score, access_count, created_at,
               conversation_id, pathway_id, is_sensitive,
               (embedding <=> '{embedding_str}'::vector) as distance
        FROM user_memories
        WHERE user_id = :user_id
          AND is_deleted = FALSE
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT :lim
    """

    result = await db.execute(
        text(sql_query),
        {
            "user_id": str(user_id),
            "lim": limit,
        }
    )

    memory_ids = [row.id for row in result.fetchall()]
    if not memory_ids:
        return []

    memories_result = await db.execute(
        select(UserMemory).where(UserMemory.id.in_(memory_ids))
    )
    return list(memories_result.scalars().all())


async def get_privacy_report(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get privacy dashboard data: total count, breakdown by type, storage stats."""
    result = await db.execute(
        text("""
            SELECT
                memory_type,
                COUNT(*) as count,
                MIN(created_at) as oldest,
                SUM(LENGTH(content::text)) as total_chars
            FROM user_memories
            WHERE user_id = :user_id AND is_deleted = FALSE
            GROUP BY memory_type
        """),
        {"user_id": str(user_id)},
    )

    rows = result.fetchall()
    by_type = {row.memory_type: row.count for row in rows}
    total = sum(by_type.values())
    oldest = min((row.oldest for row in rows), default=None) if rows else None
    total_chars = sum((row.total_chars for row in rows), default=0)

    return {
        "total_memories": total,
        "by_type": by_type,
        "oldest_memory": oldest.isoformat() if oldest else None,
        "storage_size_kb": round(total_chars / 1024, 2),
    }


# ──────────────────────────────────────────
# Helper functions for AI prompt formatting
# ──────────────────────────────────────────


def memories_to_context_str(memories: List[UserMemory]) -> str:
    """
    Format memories for AI prompt injection.

    Example output:
    KULLANICI ANILARI:
    - [💭 Duygusal Durum] Kullanıcı iş stresi nedeniyle kaygı yaşıyor (3 gün önce)
    - [🏆 Başarı] 7 günlük kaygı yolculuğunu tamamladı (1 hafta önce)
    """
    if not memories:
        return "Henüz kayıtlı anı yok."

    type_icons = {
        "emotional_state": "💭 Duygusal Durum",
        "life_event": "📍 Yaşam Olayı",
        "spiritual_preference": "✨ Manevi Tercih",
        "goal": "🎯 Hedef",
        "progress_milestone": "🏆 Başarı",
        "behavioral_pattern": "⏰ Alışkanlık",
    }

    lines = []
    for memory in memories:
        type_label = type_icons.get(memory.memory_type, "📝 Anı")

        # Calculate time ago
        now = datetime.now(timezone.utc)
        age = now - memory.created_at
        days_ago = age.days

        if days_ago == 0:
            time_label = "Bugün"
        elif days_ago == 1:
            time_label = "Dün"
        elif days_ago < 7:
            time_label = f"{days_ago} gün önce"
        elif days_ago < 30:
            weeks = days_ago // 7
            time_label = f"{weeks} hafta önce"
        else:
            months = days_ago // 30
            time_label = f"{months} ay önce"

        lines.append(f"- [{type_label}] {memory.content} ({time_label})")

    return "\n".join(lines)


def spiritual_preferences_to_context_str(prefs: dict) -> str:
    """Format spiritual preferences JSONB for AI prompt."""
    if not prefs:
        return "Manevi tercihler belirlenmemiş."

    parts = []

    if prefs.get("favorite_surahs"):
        surahs = [s.get("name", s) if isinstance(s, dict) else s
                  for s in prefs["favorite_surahs"][:3]]
        parts.append(f"Sevdiği sureler: {', '.join(surahs)}")

    if prefs.get("favorite_duas"):
        duas = prefs["favorite_duas"][:3]
        parts.append(f"Sevdiği dualar: {', '.join(duas)}")

    if prefs.get("favorite_esmas"):
        esmas = prefs["favorite_esmas"][:3]
        parts.append(f"Sevdiği esma: {', '.join(esmas)}")

    if prefs.get("active_times"):
        times = ", ".join(prefs["active_times"])
        parts.append(f"Aktif saatler: {times}")

    return " | ".join(parts) if parts else "Manevi tercihler kısmen belirlenmiş."


def format_language_style(style: dict) -> str:
    """Format language_style JSONB for AI prompt."""
    if not style:
        return "Standart"

    formality = int(style.get("formality_level", 0.5) * 100)
    emoji_usage = style.get("emoji_usage", 0.0)
    address = style.get("address_style", "sen")
    vocab = style.get("vocabulary_preference", "standard")

    parts = []
    parts.append(f"{formality}% formel")

    if emoji_usage > 0.3:
        parts.append("emoji kullanır")

    parts.append(f"'{address}' ile hitap")

    if vocab == "religious":
        parts.append("dini kelime tercihi")
    elif vocab == "modern":
        parts.append("modern dil")

    return ", ".join(parts)
