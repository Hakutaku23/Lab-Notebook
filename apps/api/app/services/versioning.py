from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.record import ExperimentRecord, RecordFieldValue
from app.models.template import ExperimentTemplate, TemplateSection
from app.models.version import RecordVersion
from app.services.record_field_values import normalize_record_field_value


def get_record_for_snapshot(db: Session, record_id: UUID) -> ExperimentRecord:
    stmt = (
        select(ExperimentRecord)
        .where(ExperimentRecord.id == record_id)
        .options(
            selectinload(ExperimentRecord.project),
            selectinload(ExperimentRecord.values),
            selectinload(ExperimentRecord.attachments),
        )
    )
    record = db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    return record


def get_template_for_restore(db: Session, template_id: UUID) -> ExperimentTemplate:
    stmt = (
        select(ExperimentTemplate)
        .where(ExperimentTemplate.id == template_id)
        .options(
            selectinload(ExperimentTemplate.sections).selectinload(TemplateSection.fields),
        )
    )
    template = db.scalar(stmt)
    if template is None:
        raise HTTPException(status_code=404, detail="实验模板不存在。")
    return template


def build_snapshot_payload(record: ExperimentRecord) -> dict:
    return {
        "record": {
            "id": record.id,
            "title": record.title,
            "status": record.status,
            "summary": record.summary,
            "project_id": record.project_id,
            "project_name": record.project.name if record.project else None,
            "template_id": record.template_id,
            "template_version": record.template_version,
            "created_by": record.created_by,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        },
        "values": [
            {
                "id": value.id,
                "field_id": value.field_id,
                "section_key_snapshot": value.section_key_snapshot,
                "field_key_snapshot": value.field_key_snapshot,
                "field_label_snapshot": value.field_label_snapshot,
                "field_type_snapshot": value.field_type_snapshot,
                "value_json": normalize_record_field_value(
                    value.field_type_snapshot,
                    value.value_json,
                ),
                "note": value.note,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
            for value in sorted(
                record.values,
                key=lambda item: (item.section_key_snapshot, item.field_key_snapshot),
            )
        ],
        "attachments": [
            {
                "id": item.id,
                "original_name": item.original_name,
                "stored_name": item.stored_name,
                "mime_type": item.mime_type,
                "size_bytes": item.size_bytes,
                "description": item.description,
                "storage_path": item.storage_path,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in sorted(
                record.attachments,
                key=lambda attachment: attachment.stored_name,
            )
        ],
    }


def restore_record_from_snapshot(
    db: Session,
    record: ExperimentRecord,
    source_version: RecordVersion,
) -> None:
    snapshot = source_version.snapshot_json or {}
    record_payload = snapshot.get("record") or {}
    value_payloads = snapshot.get("values") or []

    template = get_template_for_restore(db, record.template_id)
    field_map = {
        str(field.id): field
        for section in template.sections
        for field in section.fields
    }

    missing_fields: list[str] = []
    for item in value_payloads:
        field_id = str(item.get("field_id") or "")
        if field_id not in field_map:
            missing_fields.append(
                str(
                    item.get("field_label_snapshot")
                    or item.get("field_key_snapshot")
                    or field_id
                )
            )

    if missing_fields:
        raise HTTPException(
            status_code=409,
            detail=f"当前模板缺少历史字段，无法恢复：{', '.join(missing_fields)}",
        )

    record.title = record_payload.get("title") or record.title
    if record_payload.get("status"):
        record.status = str(record_payload["status"])
    record.summary = record_payload.get("summary")

    record.values.clear()
    db.flush()

    for item in value_payloads:
        field = field_map[str(item["field_id"])]
        record.values.append(
            RecordFieldValue(
                field_id=field.id,
                section_key_snapshot=item.get("section_key_snapshot") or field.section.key,
                field_key_snapshot=item.get("field_key_snapshot") or field.key,
                field_label_snapshot=item.get("field_label_snapshot") or field.label,
                field_type_snapshot=item.get("field_type_snapshot") or field.field_type,
                value_json=normalize_record_field_value(
                    field.field_type,
                    item.get("value_json"),
                ),
                note=item.get("note"),
            )
        )

    db.flush()


def create_record_snapshot(
    db: Session,
    record_id: UUID,
    comment: str | None = None,
    created_by: UUID | None = None,
) -> RecordVersion:
    record = get_record_for_snapshot(db, record_id)

    current_max_version = db.scalar(
        select(func.max(RecordVersion.version_no)).where(RecordVersion.record_id == record_id)
    )
    next_version_no = 1 if current_max_version is None else current_max_version + 1

    snapshot = RecordVersion(
        record_id=record_id,
        created_by=created_by,
        version_no=next_version_no,
        comment=comment,
        snapshot_json=jsonable_encoder(build_snapshot_payload(record)),
    )
    db.add(snapshot)
    db.flush()
    return snapshot
