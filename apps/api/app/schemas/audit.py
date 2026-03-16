from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    actor_username: str | None = None
    action: str
    resource_type: str
    resource_id: UUID | None = None
    summary: str
    detail_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
