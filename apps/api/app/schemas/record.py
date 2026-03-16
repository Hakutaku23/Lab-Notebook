from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.attachment import AttachmentOut


class RecordFieldValueIn(BaseModel):
    field_id: UUID
    value_json: Any = None
    note: str | None = None


class ExperimentRecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="draft", max_length=50)
    summary: str | None = None
    project_id: UUID
    template_id: UUID
    created_by: UUID | None = None
    values: list[RecordFieldValueIn] = Field(default_factory=list)


class ExperimentRecordUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    summary: str | None = None
    values: list[RecordFieldValueIn] | None = None


class RecordFieldValueOut(BaseModel):
    id: UUID
    field_id: UUID
    section_key_snapshot: str
    field_key_snapshot: str
    field_label_snapshot: str
    field_type_snapshot: str
    value_json: Any = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentRecordSummaryOut(BaseModel):
    id: UUID
    title: str
    status: str
    summary: str | None = None
    project_id: UUID
    project_name: str | None = None
    template_id: UUID
    template_name: str | None = None
    template_version: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentRecordOut(ExperimentRecordSummaryOut):
    values: list[RecordFieldValueOut]
    attachments: list[AttachmentOut]