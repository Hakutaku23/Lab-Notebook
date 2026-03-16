from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.template import ExperimentTemplate
from app.models.user import User


def ensure_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限。")


def can_manage_project(user: User, project: Project) -> bool:
    return user.role == "admin" or project.owner_id == user.id


def ensure_project_access(user: User, project: Project) -> None:
    if not can_manage_project(user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该项目。")


def can_manage_template(user: User, template: ExperimentTemplate) -> bool:
    return user.role == "admin" or template.created_by == user.id


def ensure_template_access(user: User, template: ExperimentTemplate) -> None:
    if not can_manage_template(user, template):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该模板。")


def can_view_record(user: User, record: ExperimentRecord, project: Project | None = None) -> bool:
    if user.role == "admin":
        return True
    if record.created_by == user.id:
        return True
    if project is not None and project.owner_id == user.id:
        return True
    if record.project is not None and record.project.owner_id == user.id:
        return True
    return False


def ensure_record_access(user: User, record: ExperimentRecord, project: Project | None = None) -> None:
    if not can_view_record(user, record, project=project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该实验记录。")
