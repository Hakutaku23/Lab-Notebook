from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.record import ExperimentRecord
from app.models.version import RecordVersion
from app.schemas.version import (
    RecordVersionDetailOut,
    RecordVersionSummaryOut,
    SnapshotCreateIn,
)
from app.services.serializers import serialize_version_detail, serialize_version_summary
from app.services.user_resolver import resolve_user_id
from app.services.versioning import create_record_snapshot

router = APIRouter()


@router.get("/records/{record_id}/versions", response_model=list[RecordVersionSummaryOut])
def list_record_versions(record_id: UUID, db: Session = Depends(get_db)):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")

    stmt = (
        select(RecordVersion)
        .where(RecordVersion.record_id == record_id)
        .order_by(RecordVersion.version_no.desc())
    )
    items = db.scalars(stmt).all()
    return [serialize_version_summary(item) for item in items]


@router.get("/records/{record_id}/versions/{version_id}", response_model=RecordVersionDetailOut)
def get_record_version_detail(record_id: UUID, version_id: UUID, db: Session = Depends(get_db)):
    item = db.get(RecordVersion, version_id)
    if item is None or item.record_id != record_id:
        raise HTTPException(status_code=404, detail="版本不存在。")
    return serialize_version_detail(item)


@router.post("/records/{record_id}/versions/snapshot", response_model=RecordVersionDetailOut, status_code=status.HTTP_201_CREATED)
def create_manual_snapshot(record_id: UUID, payload: SnapshotCreateIn, db: Session = Depends(get_db)):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")

    actual_user_id = None
    if payload.created_by is not None:
        actual_user_id = resolve_user_id(db, payload.created_by)

    item = create_record_snapshot(
        db,
        record_id=record_id,
        comment=payload.comment or "手动创建快照",
        created_by=actual_user_id,
    )
    db.commit()
    db.refresh(item)
    return serialize_version_detail(item)