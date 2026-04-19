from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    if not settings.SERVICE_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service authentication is not configured",
        )
    if x_service_token != settings.SERVICE_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token",
        )
