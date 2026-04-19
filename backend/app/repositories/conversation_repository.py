from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message


async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[str],
    user_id: Optional[str],
) -> Conversation:
    if conversation_id:
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except (ValueError, AttributeError):
            conv_uuid = None

        if conv_uuid:
            result = await db.execute(select(Conversation).where(Conversation.id == conv_uuid))
            conversation = result.scalar_one_or_none()
            if conversation:
                conv_user_id = str(conversation.user_id) if conversation.user_id else None
                is_authorized = (
                    (user_id is not None and conv_user_id == user_id)
                    or (user_id is None and conv_user_id is None)
                )
                if is_authorized:
                    return conversation

    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id) if user_id else None,
        phase="IDLE",
        gathering_context={},
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def list_messages(db: AsyncSession, conversation_id) -> list[dict]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return [{"sender": item.sender, "content": item.content} for item in result.scalars().all()]


async def save_message(
    db: AsyncSession,
    conversation_id,
    sender: str,
    content: str,
    metadata: dict | None = None,
):
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        metadata_=metadata,
    )
    db.add(message)
    await db.flush()
    return message


async def get_cross_conversation_history(
    db: AsyncSession,
    user_id,
    limit: int = 20,
) -> list[dict]:
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"sender": item.sender, "content": item.content} for item in messages]


def conversation_history_to_text(history: list[dict]) -> str:
    lines = []
    for item in history:
        role = "Kullanıcı" if item["sender"] == "user" else "Asistan"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)
