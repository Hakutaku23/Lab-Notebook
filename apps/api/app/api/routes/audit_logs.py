from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.services.permissions import ensure_record_access
from app.services.serializers import serialize_audit_log

router = APIRouter()


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    resource_type: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)

    if current_user.role != "admin":
        if resource_type == "record" and resource_id is not None:
            record = db.get(ExperimentRecord, resource_id)
            if record is None:
                raise HTTPException(status_code=404, detail="实验记录不存在。")
            project = db.get(Project, record.project_id)
            ensure_record_access(current_user, record, project=project)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="非管理员只能查询自己有权限的单条资源审计日志。",
            )

    items = db.scalars(stmt.limit(limit)).all()
    return [serialize_audit_log(item) for item in items]
