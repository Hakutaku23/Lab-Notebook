from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attachment import Attachment
from app.models.record import ExperimentRecord
from app.schemas.attachment import AttachmentOut
from app.services.serializers import serialize_attachment
from app.services.storage import save_record_file
from app.services.user_resolver import resolve_user_id
from app.services.versioning import create_record_snapshot

router = APIRouter()


@router.get("/records/{record_id}/attachments", response_model=list[AttachmentOut])
def list_record_attachments(record_id: UUID, db: Session = Depends(get_db)):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")

    stmt = (
        select(Attachment)
        .where(Attachment.record_id == record_id)
        .order_by(Attachment.created_at.desc())
    )
    items = db.scalars(stmt).all()
    return [serialize_attachment(item) for item in items]


@router.post("/records/{record_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    record_id: UUID,
    file: UploadFile = File(...),
    uploaded_by: UUID | None = Form(default=None),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    record = db.get(ExperimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="实验记录不存在。")

    actual_user_id = resolve_user_id(db, uploaded_by)
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

    create_record_snapshot(
        db,
        record_id=record_id,
        comment=f"上传附件：{attachment.original_name}",
        created_by=actual_user_id,
    )
    db.commit()
    db.refresh(attachment)

    return serialize_attachment(attachment)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Attachment, attachment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="附件不存在。")

    path = Path(item.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="附件文件不存在。")

    return FileResponse(
        path=str(path),
        media_type=item.mime_type or "application/octet-stream",
        filename=item.original_name,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(attachment_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Attachment, attachment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="附件不存在。")

    record_id = item.record_id
    file_path = item.storage_path
    file_name = item.original_name

    db.delete(item)
    db.flush()

    create_record_snapshot(
        db,
        record_id=record_id,
        comment=f"删除附件：{file_name}",
    )
    db.commit()

    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        pass