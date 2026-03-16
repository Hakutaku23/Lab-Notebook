from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExperimentTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experiment_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str] = mapped_column(String(50), default="generic", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiment_templates.id", ondelete="SET NULL"),
        nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    extra_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creator = relationship("User", back_populates="created_templates")
    parent_template = relationship("ExperimentTemplate", remote_side="ExperimentTemplate.id", back_populates="child_templates")
    child_templates = relationship("ExperimentTemplate", back_populates="parent_template")
    sections = relationship(
        "TemplateSection",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateSection.order_index"
    )
    records = relationship("ExperimentRecord", back_populates="template")


class TemplateSection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "template_sections"
    __table_args__ = (
        UniqueConstraint("template_id", "key", name="uq_template_section_key"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiment_templates.id", ondelete="CASCADE"),
        nullable=False
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_repeatable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    template = relationship("ExperimentTemplate", back_populates="sections")
    fields = relationship(
        "TemplateField",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="TemplateField.order_index"
    )


class TemplateField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "template_fields"
    __table_args__ = (
        UniqueConstraint("section_id", "key", name="uq_section_field_key"),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_sections.id", ondelete="CASCADE"),
        nullable=False
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)

    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    default_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ui_props: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    section = relationship("TemplateSection", back_populates="fields")
    record_values = relationship("RecordFieldValue", back_populates="field")