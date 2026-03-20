from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attachment import Attachment
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User
from app.schemas.attachment import AttachmentOut
from app.services.audit import write_audit_log
from app.services.permissions import ensure_record_access, ensure_record_write_access
from app.services.record_workflow import ensure_record_editable
from app.services.serializers import serialize_attachment
from app.services.storage import save_record_file
from app.services.user_resolver import resolve_user_id
from app.services.versioning import create_record_snapshot

router = APIRouter()


@router.get("/records/{record_id}/attachments", response_model=list[AttachmentOut])
def list_record_attachments(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    stmt = select(Attachment).where(Attachment.record_id == record_id).order_by(Attachment.created_at.desc())
    items = db.scalars(stmt).all()
    return [serialize_attachment(item) for item in items]


@router.post("/records/{record_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    record_id: UUID,
    file: UploadFile = File(...),
    uploaded_by: UUID | None = Form(default=None),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    ensure_record_write_access(current_user, record, project=project)
    ensure_record_editable(record)
    actual_user_id = resolve_user_id(db, uploaded_by or current_user.id)
    stored = save_record_file(str(record_id), file)
    attachment = Attachment(
        record_id=record_id,
        uploaded_by=actual_user_id,
        original_name=stored["original_name"],
        stored_name=stored["stored_name"],
        mime_type=stored["mime_type"],
        size_bytes=stored["size_bytes"],
        storage_path=stored["storage_path"],
        description=description,
    )
    db.add(attachment)
    db.flush()
    create_record_snapshot(db, record_id=record_id, comment=f"上传附件：{attachment.original_name}", created_by=current_user.id)
    write_audit_log(
        db,
        actor=current_user,
        action="attachment.upload",
        resource_type="record",
        resource_id=record_id,
        summary=f"上传附件：{attachment.original_name}",
        detail={"attachment_id": str(attachment.id), "size_bytes": attachment.size_bytes, "actor_role": current_user.role},
    )
    db.commit()
    db.refresh(attachment)
    return serialize_attachment(attachment)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.get(Attachment, attachment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="附件不存在。")
    record = db.get(ExperimentRecord, item.record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    path = Path(item.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="附件文件不存在。")
    return FileResponse(path=str(path), media_type=item.mime_type or "application/octet-stream", filename=item.original_name)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.get(Attachment, attachment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="附件不存在。")
    record = db.get(ExperimentRecord, item.record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")
    project = db.get(Project, record.project_id)
    ensure_record_access(current_user, record, project=project)
    ensure_record_write_access(current_user, record, project=project)
    ensure_record_editable(record)
    record_id = item.record_id
    file_path = item.storage_path
    file_name = item.original_name
    db.delete(item)
    db.flush()
    create_record_snapshot(db, record_id=record_id, comment=f"删除附件：{file_name}", created_by=current_user.id)
    write_audit_log(
        db,
        actor=current_user,
        action="attachment.delete",
        resource_type="record",
        resource_id=record_id,
        summary=f"删除附件：{file_name}",
        detail={"actor_role": current_user.role},
    )
    db.commit()
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        pass
