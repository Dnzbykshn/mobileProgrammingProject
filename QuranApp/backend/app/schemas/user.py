import re

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: str = Field(..., description="User's email address", example="ahmet@example.com")
    password: str = Field(..., min_length=8, description="Password (min 8 chars required)", example="GucluSifre123!")
    full_name: Optional[str] = Field(None, description="User's full display name", example="Ahmet Yılmaz")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "email": "ahmet@example.com",
                "password": "securePassword123",
                "full_name": "Ahmet Yılmaz"
            }
        }


class UserLogin(BaseModel):
    email: str = Field(..., description="Registered email", example="ahmet@example.com")
    password: str = Field(..., description="User password", example="GucluSifre123!")


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Optional refresh token to revoke")


class AuthSession(BaseModel):
    device_id: str = Field(..., description="Client-provided device identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Refresh token expiry timestamp")
    is_current_device: bool = Field(False, description="Whether this session belongs to current device")


class LogoutAllResponse(BaseModel):
    detail: str = Field(..., description="Operation status message")
    revoked_sessions: int = Field(..., description="Number of sessions revoked")


class UserResponse(BaseModel):
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="Display name")
    is_premium: bool = Field(False, description="Premium subscription status")
