from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    id: UUID
    record_id: UUID
    uploaded_by: UUID | None = None
    original_name: str
    stored_name: str
    mime_type: str | None = None
    size_bytes: int
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    download_url: str

    model_config = ConfigDict(from_attributes=True)