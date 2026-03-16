from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SnapshotCreateIn(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
    created_by: UUID | None = None


class RecordVersionSummaryOut(BaseModel):
    id: UUID
    record_id: UUID
    created_by: UUID | None = None
    version_no: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecordVersionDetailOut(RecordVersionSummaryOut):
    snapshot_json: dict