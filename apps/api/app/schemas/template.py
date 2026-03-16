from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TemplateFieldIn(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    field_type: str = Field(min_length=1, max_length=50)
    required: bool = False
    order_index: int = 0
    placeholder: str | None = Field(default=None, max_length=255)
    help_text: str | None = None
    default_value: Any = None
    options: dict | None = None
    validation_rules: dict | None = None
    ui_props: dict | None = None


class TemplateSectionIn(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    order_index: int = 0
    is_repeatable: bool = False
    fields: list[TemplateFieldIn] = Field(default_factory=list)


class ExperimentTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    key: str = Field(min_length=1, max_length=100)
    description: str | None = None
    category: str = Field(default="generic", max_length=50)
    parent_template_id: UUID | None = None
    created_by: UUID | None = None
    is_active: bool = True
    sections: list[TemplateSectionIn] = Field(default_factory=list)


class ExperimentTemplateUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    key: str = Field(min_length=1, max_length=100)
    description: str | None = None
    category: str = Field(default="generic", max_length=50)
    parent_template_id: UUID | None = None
    is_active: bool = True
    sections: list[TemplateSectionIn] = Field(default_factory=list)


class TemplateFieldOut(BaseModel):
    id: UUID
    key: str
    label: str
    field_type: str
    required: bool
    order_index: int
    placeholder: str | None = None
    help_text: str | None = None
    default_value: Any = None
    options: dict | None = None
    validation_rules: dict | None = None
    ui_props: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class TemplateSectionOut(BaseModel):
    id: UUID
    key: str
    title: str
    description: str | None = None
    order_index: int
    is_repeatable: bool
    fields: list[TemplateFieldOut]

    model_config = ConfigDict(from_attributes=True)


class ExperimentTemplateSummaryOut(BaseModel):
    id: UUID
    name: str
    key: str
    description: str | None = None
    category: str
    version: int
    is_system: bool
    is_active: bool
    parent_template_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentTemplateDetailOut(ExperimentTemplateSummaryOut):
    sections: list[TemplateSectionOut]

class TemplateVersionCreate(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, max_length=50)
    created_by: UUID | None = None
    is_active: bool = True
    sections: list[TemplateSectionIn] | None = None

class TemplateLineageOut(BaseModel):
    root_template_id: UUID
    current_template_id: UUID
    items: list[ExperimentTemplateSummaryOut]