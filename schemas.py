from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class MagicLinkRequest(BaseModel):
    """Request body for requesting a magic link"""
    email: EmailStr


class MagicLinkVerify(BaseModel):
    """Request body for verifying a magic link token"""
    token: str


class TokenResponse(BaseModel):
    """Response containing access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Response for successful authentication"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing an access token"""
    refresh_token: str


class UserResponse(BaseModel):
    """User data response"""
    id: int
    email: str
    google_id: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
