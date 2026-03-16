from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.template import ExperimentTemplate, TemplateSection
from app.models.user import User
from app.schemas.record import (
    ExperimentRecordCreate,
    ExperimentRecordOut,
    ExperimentRecordSummaryOut,
    ExperimentRecordUpdate,
)
from app.services.audit import write_audit_log
from app.services.permissions import ensure_project_access, ensure_record_access
from app.services.record_builder import build_record_values
from app.services.serializers import serialize_record_detail, serialize_record_summary
from app.services.user_resolver import resolve_user_id
from app.services.versioning import create_record_snapshot

router = APIRouter()


def get_template_with_fields(db: Session, template_id: UUID) -> ExperimentTemplate:
    stmt = (
        select(ExperimentTemplate)
        .where(ExperimentTemplate.id == template_id)
        .options(selectinload(ExperimentTemplate.sections).selectinload(TemplateSection.fields))
    )
    template = db.scalar(stmt)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板不可用。")
    return template


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


@router.post("", response_model=ExperimentRecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: ExperimentRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="所属项目不存在。")
    ensure_project_access(current_user, project)
    template = get_template_with_fields(db, payload.template_id)
    created_by = resolve_user_id(db, payload.created_by or current_user.id)
    if current_user.role != "admin" and created_by != current_user.id:
        raise HTTPException(status_code=403, detail="不能以其他用户身份创建记录。")

    record = ExperimentRecord(
        title=payload.title,
        status=payload.status,
        summary=payload.summary,
        project_id=payload.project_id,
        template_id=payload.template_id,
        created_by=created_by,
        template_version=template.version,
    )
    record.values = build_record_values(template, payload.values)
    db.add(record)
    db.flush()

    create_record_snapshot(db, record_id=record.id, comment="创建记录", created_by=created_by)
    write_audit_log(
        db,
        actor=current_user,
        action="record.create",
        resource_type="record",
        resource_id=record.id,
        summary=f"创建实验记录：{record.title}",
        detail={"project_id": str(record.project_id), "template_id": str(record.template_id)},
    )
    db.commit()

    created_record = get_record_detail_entity(db, record.id)
    return serialize_record_detail(created_record)


@router.get("", response_model=list[ExperimentRecordSummaryOut])
def list_records(
    project_id: UUID | None = Query(default=None),
    template_id: UUID | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(ExperimentRecord)
        .options(
            selectinload(ExperimentRecord.project),
            selectinload(ExperimentRecord.template),
        )
        .order_by(ExperimentRecord.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(ExperimentRecord.project_id == project_id)
    if template_id is not None:
        stmt = stmt.where(ExperimentRecord.template_id == template_id)
    if status_value:
        stmt = stmt.where(ExperimentRecord.status == status_value)
    if current_user.role != "admin":
        stmt = stmt.join(Project, ExperimentRecord.project_id == Project.id).where(
            (Project.owner_id == current_user.id) | (ExperimentRecord.created_by == current_user.id)
        )
    records = db.scalars(stmt).all()
    return [serialize_record_summary(item) for item in records]


@router.get("/{record_id}", response_model=ExperimentRecordOut)
def get_record_detail(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_record_detail_entity(db, record_id)
    ensure_record_access(current_user, record, project=record.project)
    return serialize_record_detail(record)


@router.put("/{record_id}", response_model=ExperimentRecordOut)
def update_record(
    record_id: UUID,
    payload: ExperimentRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_record_detail_entity(db, record_id)
    ensure_record_access(current_user, record, project=record.project)
    before = {"title": record.title, "status": record.status, "summary": record.summary}
    if payload.title is not None:
        record.title = payload.title
    if payload.status is not None:
        record.status = payload.status
    if payload.summary is not None:
        record.summary = payload.summary
    if payload.values is not None:
        template = get_template_with_fields(db, record.template_id)
        record.values.clear()
        db.flush()
        record.values.extend(build_record_values(template, payload.values))
        db.flush()
    create_record_snapshot(db, record_id=record_id, comment="更新记录", created_by=current_user.id)
    write_audit_log(
        db,
        actor=current_user,
        action="record.update",
        resource_type="record",
        resource_id=record.id,
        summary=f"更新实验记录：{record.title}",
        detail={"before": before, "after": {"title": record.title, "status": record.status, "summary": record.summary}},
    )
    db.commit()
    updated_record = get_record_detail_entity(db, record_id)
    return serialize_record_detail(updated_record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    write_audit_log(
        db,
        actor=current_user,
        action="record.delete",
        resource_type="record",
        resource_id=record.id,
        summary=f"删除实验记录：{record.title}",
    )
    db.delete(record)
    db.commit()
