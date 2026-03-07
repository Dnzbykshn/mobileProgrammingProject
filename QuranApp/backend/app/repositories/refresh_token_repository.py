"""
Refresh token repository — token rotation and revocation persistence.
"""
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    user_id,
    device_id: str,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        device_id=device_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()
    return token


async def get_by_token_hash(db: AsyncSession, token_hash: str) -> Optional[RefreshToken]:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def get_active_by_token_hash(db: AsyncSession, token_hash: str) -> Optional[RefreshToken]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def list_active_for_user(
    db: AsyncSession,
    user_id,
    limit: int = 50,
) -> Sequence[RefreshToken]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def revoke_by_token_hash(
    db: AsyncSession,
    token_hash: str,
    replaced_by_token_hash: Optional[str] = None,
) -> int:
    result = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=datetime.now(timezone.utc),
            replaced_by_token_hash=replaced_by_token_hash,
        )
    )
    return result.rowcount or 0


async def revoke_all_for_user(db: AsyncSession, user_id) -> int:
    result = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    return result.rowcount or 0
