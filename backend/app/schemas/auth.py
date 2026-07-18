"""Authentication request / response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class RegisterResponse(BaseModel):
    user: UserRead
    access_token: str
    token_type: str = "bearer"
    expires_in: int
