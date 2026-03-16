from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def ensure_upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_record_file(record_id: str, upload_file: UploadFile) -> dict:
    root = ensure_upload_root()
    target_dir = root / "records" / record_id
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(upload_file.filename or "").suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    target_path = target_dir / stored_name

    upload_file.file.seek(0)
    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return {
        "original_name": upload_file.filename or stored_name,
        "stored_name": stored_name,
        "mime_type": upload_file.content_type,
        "size_bytes": target_path.stat().st_size,
        "storage_path": str(target_path),
    }