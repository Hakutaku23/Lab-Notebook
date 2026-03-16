from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attachment import Attachment
from app.models.record import ExperimentRecord, RecordFieldValue
from app.models.version import RecordVersion


def get_record_for_snapshot(db: Session, record_id: UUID) -> ExperimentRecord:
    stmt = (
        select(ExperimentRecord)
        .where(ExperimentRecord.id == record_id)
        .options(
            selectinload(ExperimentRecord.values),
            selectinload(ExperimentRecord.attachments),
        )
    )
    record = db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    return record


def build_snapshot_payload(record: ExperimentRecord) -> dict:
    return {
        "record": {
            "id": record.id,
            "title": record.title,
            "status": record.status,
            "summary": record.summary,
            "project_id": record.project_id,
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
                "value_json": value.value_json,
                "note": value.note,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
            for value in record.values
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
            for item in record.attachments
        ],
    }


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