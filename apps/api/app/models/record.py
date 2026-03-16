from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExperimentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experiment_records"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiment_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    template_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project = relationship("Project", back_populates="records")
    template = relationship("ExperimentTemplate", back_populates="records")
    creator = relationship("User", back_populates="created_records")

    values = relationship(
        "RecordFieldValue",
        back_populates="record",
        cascade="all, delete-orphan",
    )
    attachments = relationship(
        "Attachment",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="Attachment.created_at.desc()",
    )
    versions = relationship(
        "RecordVersion",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="RecordVersion.version_no.desc()",
    )


class RecordFieldValue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "record_field_values"
    __table_args__ = (
        UniqueConstraint("record_id", "field_id", name="uq_record_field_value"),
    )

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiment_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_fields.id", ondelete="RESTRICT"),
        nullable=False,
    )

    section_key_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    field_key_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    field_label_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)

    value_json: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    record = relationship("ExperimentRecord", back_populates="values")
    field = relationship("TemplateField", back_populates="record_values")