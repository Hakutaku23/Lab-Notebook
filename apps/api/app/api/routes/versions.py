from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User
from app.models.version import RecordVersion
from app.schemas.record import ExperimentRecordOut
from app.schemas.version import (
    RecordVersionCompareOut,
    RecordVersionDetailOut,
    RecordVersionSummaryOut,
    RestoreVersionIn,
    SnapshotCreateIn,
)
from app.services.audit import write_audit_log
from app.services.diffing import build_version_diff
from app.services.permissions import ensure_record_access
from app.services.serializers import (
    serialize_record_detail,
    serialize_version_detail,
    serialize_version_summary,
)
from app.services.user_resolver import resolve_user_id
from app.services.versioning import (
    create_record_snapshot,
    restore_record_from_snapshot,
)

router = APIRouter()


def ensure_record_permission(db: Session, current_user: User, record_id: UUID) -> ExperimentRecord:
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    return record


def get_record_detail_entity(db: Session, record_id: UUID) -> ExperimentRecord:
    stmt = (
        select(ExperimentRecord)
        .where(ExperimentRecord.id == record_id)
        .options(
            selectinload(ExperimentRecord.project),
            selectinload(ExperimentRecord.template),
            selectinload(ExperimentRecord.values),
            selectinload(ExperimentRecord.attachments),
        )
    )
    record = db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    return record


@router.get("/records/{record_id}/versions", response_model=list[RecordVersionSummaryOut])
def list_record_versions(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_record_permission(db, current_user, record_id)
    stmt = (
        select(RecordVersion)
        .where(RecordVersion.record_id == record_id)
        .order_by(RecordVersion.version_no.desc())
    )
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


@router.post(
    "/records/{record_id}/versions/snapshot",
    response_model=RecordVersionDetailOut,
    status_code=status.HTTP_201_CREATED,
)
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


@router.post(
    "/records/{record_id}/versions/{version_id}/restore",
    response_model=ExperimentRecordOut,
)
def restore_record_version(
    record_id: UUID,
    version_id: UUID,
    payload: RestoreVersionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = ensure_record_permission(db, current_user, record_id)
    source_version = db.get(RecordVersion, version_id)

    if source_version is None or source_version.record_id != record_id:
        raise HTTPException(status_code=404, detail="版本不存在。")

    restore_record_from_snapshot(db, record=record, source_version=source_version)

    new_snapshot = create_record_snapshot(
        db,
        record_id=record_id,
        comment=payload.comment or f"恢复到版本 v{source_version.version_no}",
        created_by=current_user.id,
    )

    write_audit_log(
        db,
        actor=current_user,
        action="record.version.restore",
        resource_type="record",
        resource_id=record_id,
        summary=f"恢复实验记录到历史版本：{record.title}",
        detail={
            "source_version_id": str(source_version.id),
            "source_version_no": source_version.version_no,
            "new_version_no": new_snapshot.version_no,
            "attachments_restored": False,
        },
    )

    db.commit()

    restored = get_record_detail_entity(db, record_id)
    return serialize_record_detail(restored)


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