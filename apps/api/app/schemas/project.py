from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    owner_id: UUID | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)