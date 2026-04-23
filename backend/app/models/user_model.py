"""Persistence model definitions for users."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserDocument(BaseModel):
    """MongoDB representation of a platform user."""

    id: str | None = Field(default=None, alias="_id")
    email: EmailStr
    full_name: str
    hashed_password: str
    role: Literal["admin", "auditor", "user"] = "user"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
