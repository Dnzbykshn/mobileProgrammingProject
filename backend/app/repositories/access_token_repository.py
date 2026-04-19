"""
Access token revocation persistence.
"""
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revoked_access_token import RevokedAccessToken


async def is_access_token_revoked(db: AsyncSession, token_hash: str) -> bool:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RevokedAccessToken.token_hash).where(
            RevokedAccessToken.token_hash == token_hash,
            RevokedAccessToken.expires_at > now,
        )
    )
    return result.scalar_one_or_none() is not None


async def revoke_access_token(
    db: AsyncSession,
    *,
    token_hash: str,
    user_id,
    expires_at: datetime,
) -> None:
    await db.execute(
        insert(RevokedAccessToken)
        .values(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
        )
        .on_conflict_do_nothing(index_elements=["token_hash"])
    )


async def delete_expired_revocations(db: AsyncSession) -> int:
    result = await db.execute(
        delete(RevokedAccessToken).where(
            RevokedAccessToken.expires_at <= datetime.now(timezone.utc)
        )
    )
    return result.rowcount or 0
