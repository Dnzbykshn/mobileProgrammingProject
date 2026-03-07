"""
FastAPI dependency injection providers.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import redis.asyncio as aioredis

from app.db.database import AsyncSessionLocal
from app.core.security import decode_access_token, token_fingerprint

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db():
    """Async database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session


def get_master_brain(request: Request):
    """Get Master Brain instance from app.state."""
    return request.app.state.brain


def get_redis(request: Request) -> Optional[aioredis.Redis]:
    """Get async Redis client from app.state."""
    return getattr(request.app.state, "redis", None)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client: Optional[aioredis.Redis] = Depends(get_redis),
):
    """
    Decode JWT token and return the User object.
    If no token is provided, returns None (for optional auth endpoints).
    """
    if token is None:
        return None

    # Optional logout token revocation (works when Redis is available).
    if redis_client is not None:
        try:
            blacklisted = await redis_client.exists(
                f"auth:blacklist:{token_fingerprint(token)}"
            )
            if blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception:
            # Fail-open to avoid auth outage when Redis is unavailable.
            pass

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    if payload.get("typ") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def require_current_user(
    user=Depends(get_current_user),
):
    """Strict version — raises 401 if no user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
