from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User
from app.models.version import RecordVersion
from app.schemas.version import (
    RecordVersionCompareOut,
    RecordVersionDetailOut,
    RecordVersionSummaryOut,
    SnapshotCreateIn,
)
from app.services.audit import write_audit_log
from app.services.diffing import build_version_diff
from app.services.permissions import ensure_record_access
from app.services.serializers import serialize_version_detail, serialize_version_summary
from app.services.user_resolver import resolve_user_id
from app.services.versioning import create_record_snapshot

router = APIRouter()


def ensure_record_permission(db: Session, current_user: User, record_id: UUID) -> ExperimentRecord:
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    return record


@router.get("/records/{record_id}/versions", response_model=list[RecordVersionSummaryOut])
def list_record_versions(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_record_permission(db, current_user, record_id)
    stmt = select(RecordVersion).where(RecordVersion.record_id == record_id).order_by(RecordVersion.version_no.desc())
    items = db.scalars(stmt).all()
    return [serialize_version_summary(item) for item in items]


@router.get("/records/{record_id}/versions/compare", response_model=RecordVersionCompareOut)
def compare_record_versions(
    record_id: UUID,
    from_version_id: UUID = Query(...),
    to_version_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_record_permission(db, current_user, record_id)
    from_version = db.get(RecordVersion, from_version_id)
    to_version = db.get(RecordVersion, to_version_id)
    if from_version is None or from_version.record_id != record_id:
        raise HTTPException(status_code=404, detail="起始版本不存在。")
    if to_version is None or to_version.record_id != record_id:
        raise HTTPException(status_code=404, detail="目标版本不存在。")
    items = build_version_diff(from_version, to_version)
    return {
        "from_version": serialize_version_summary(from_version),
        "to_version": serialize_version_summary(to_version),
        "change_count": len(items),
        "items": items,
    }


@router.post("/records/{record_id}/versions/snapshot", response_model=RecordVersionDetailOut, status_code=status.HTTP_201_CREATED)
def create_manual_snapshot(
    record_id: UUID,
    payload: SnapshotCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = ensure_record_permission(db, current_user, record_id)
    actual_user_id = resolve_user_id(db, payload.created_by or current_user.id)
    item = create_record_snapshot(
        db,
        record_id=record_id,
        comment=payload.comment or "手动创建快照",
        created_by=actual_user_id,
    )
    write_audit_log(
        db,
        actor=current_user,
        action="record.snapshot.create",
        resource_type="record",
        resource_id=record_id,
        summary=f"创建记录快照：{record.title}",
        detail={"version_no": item.version_no, "comment": item.comment},
    )
    db.commit()
    db.refresh(item)
    return serialize_version_detail(item)


@router.get("/records/{record_id}/versions/{version_id}", response_model=RecordVersionDetailOut)
def get_record_version_detail(
    record_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_record_permission(db, current_user, record_id)
    item = db.get(RecordVersion, version_id)
    if item is None or item.record_id != record_id:
        raise HTTPException(status_code=404, detail="版本不存在。")
    return serialize_version_detail(item)
