"""
Application-level exception classes and handlers.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} not found", status_code=404)


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=409)


class AIServiceError(AppException):
    def __init__(self, detail: str = "AI service temporarily unavailable"):
        super().__init__(detail=detail, status_code=503)


async def app_exception_handler(request: Request, exc: AppException):
    """Handler for custom AppException errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
