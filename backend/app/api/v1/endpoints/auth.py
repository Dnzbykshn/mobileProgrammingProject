"""
Auth endpoints — Registration, Login, Profile.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    RefreshTokenRequest,
    LogoutRequest,
    AuthSession,
    LogoutAllResponse,
)
from app.core.dependencies import (
    get_db,
    require_current_user,
    oauth2_scheme,
)
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    token_fingerprint,
)
from app.repositories.user_repository import get_user_by_email, get_user_by_id, create_user
from app.repositories import access_token_repository, refresh_token_repository
from app.core.rate_limit import limiter

router = APIRouter()


def _expires_at_from_token(token: str) -> datetime:
    payload = decode_access_token(token)
    exp_ts = int(payload.get("exp")) if payload and payload.get("exp") else None
    if exp_ts is None:
        raise RuntimeError("Failed to parse token expiration")
    return datetime.fromtimestamp(exp_ts, tz=timezone.utc)


def _get_device_id(request: Request) -> str:
    raw_device_id = (request.headers.get("X-Device-ID") or "").strip()
    if not raw_device_id:
        return "unknown"
    return raw_device_id[:128]


async def _issue_token_pair(db: AsyncSession, user_id, device_id: str) -> Token:
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    refresh_hash = token_fingerprint(refresh_token)
    refresh_expires_at = _expires_at_from_token(refresh_token)
    await refresh_token_repository.create_refresh_token(
        db=db,
        user_id=user_id,
        device_id=device_id,
        token_hash=refresh_hash,
        expires_at=refresh_expires_at,
    )
    await db.commit()
    return Token(access_token=access_token, refresh_token=refresh_token)


async def _revoke_current_access_token(
    db: AsyncSession,
    token: str,
    user_id,
) -> None:
    payload = decode_access_token(token)
    exp_ts = int(payload.get("exp")) if payload and payload.get("exp") else None
    if not exp_ts:
        return

    await access_token_repository.delete_expired_revocations(db)
    await access_token_repository.revoke_access_token(
        db,
        token_hash=token_fingerprint(token),
        user_id=user_id,
        expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and return JWT."""
    normalized_email = user_data.email.strip().lower()
    device_id = _get_device_id(request)

    existing = await get_user_by_email(db, normalized_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(
        db,
        email=normalized_email,
        password=user_data.password,
        full_name=user_data.full_name,
    )

    return await _issue_token_pair(db, user.id, device_id)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return JWT."""
    normalized_email = credentials.email.strip().lower()
    device_id = _get_device_id(request)
    user = await get_user_by_email(db, normalized_email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return await _issue_token_pair(db, user.id, device_id)


@router.post("/refresh", response_model=Token)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue a new access token pair."""
    request_device_id = _get_device_id(request)
    decoded = decode_access_token(payload.refresh_token)
    if not decoded or decoded.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_hash = token_fingerprint(payload.refresh_token)
    stored = await refresh_token_repository.get_active_by_token_hash(db, token_hash)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        )
    if stored.device_id not in ("unknown", request_device_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    new_refresh_hash = token_fingerprint(new_refresh_token)

    await refresh_token_repository.revoke_by_token_hash(
        db,
        token_hash=token_hash,
        replaced_by_token_hash=new_refresh_hash,
    )
    await refresh_token_repository.create_refresh_token(
        db=db,
        user_id=user.id,
        device_id=stored.device_id if stored.device_id else request_device_id,
        token_hash=new_refresh_hash,
        expires_at=_expires_at_from_token(new_refresh_token),
    )
    await db.commit()

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(require_current_user)):
    """Return current authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_premium=current_user.is_premium,
    )


@router.get("/sessions", response_model=list[AuthSession])
@limiter.limit("30/minute")
async def list_sessions(
    request: Request,
    current_user=Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active refresh sessions for current user."""
    current_device_id = _get_device_id(request)
    sessions = await refresh_token_repository.list_active_for_user(db, current_user.id)

    return [
        AuthSession(
            device_id=s.device_id,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current_device=(s.device_id == current_device_id),
        )
        for s in sessions
    ]


@router.post("/logout")
@limiter.limit("30/minute")
async def logout(
    request: Request,
    payload: Optional[LogoutRequest] = None,
    current_user=Depends(require_current_user),
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Logout current session and revoke current access token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request_device_id = _get_device_id(request)
    await _revoke_current_access_token(db, token, current_user.id)

    refresh_token_value = payload.refresh_token if payload else None
    if refresh_token_value:
        refresh_payload = decode_access_token(refresh_token_value)
        if (
            not refresh_payload
            or refresh_payload.get("typ") != "refresh"
            or refresh_payload.get("sub") != str(current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        stored_refresh = await refresh_token_repository.get_by_token_hash(
            db,
            token_fingerprint(refresh_token_value),
        )
        if stored_refresh and stored_refresh.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        if stored_refresh and stored_refresh.device_id not in ("unknown", request_device_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        await refresh_token_repository.revoke_by_token_hash(
            db=db,
            token_hash=token_fingerprint(refresh_token_value),
        )
    else:
        await refresh_token_repository.revoke_all_for_user(db, current_user.id)
    await db.commit()

    return {"detail": "Logged out"}


@router.post("/logout-all", response_model=LogoutAllResponse)
@limiter.limit("10/minute")
async def logout_all(
    request: Request,
    current_user=Depends(require_current_user),
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all refresh sessions for current user and invalidate current access token."""
    if token:
        await _revoke_current_access_token(db, token, current_user.id)

    revoked_count = await refresh_token_repository.revoke_all_for_user(db, current_user.id)
    await db.commit()

    return LogoutAllResponse(
        detail="Logged out from all devices",
        revoked_sessions=revoked_count,
    )
