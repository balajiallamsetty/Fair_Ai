"""Pydantic schemas for users and authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Create-user request payload."""

    email: EmailStr
    full_name: str
    password: str
    role: Literal["admin", "auditor", "user"] = "user"


class UserLogin(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Public user response schema."""

    id: str
    email: EmailStr
    full_name: str
    role: Literal["admin", "auditor", "user"]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT login response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class TokenPayload(BaseModel):
    """Decoded JWT payload schema."""

    sub: str
    role: str
    exp: int
