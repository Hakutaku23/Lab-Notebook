from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class RegisterIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    full_name: str | None = Field(default=None, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class CurrentUserOut(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUserOut
