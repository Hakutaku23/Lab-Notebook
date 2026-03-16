from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.audit import write_audit_log
from app.services.permissions import ensure_project_access
from app.services.serializers import serialize_project
from app.services.user_resolver import resolve_user_id

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_id = resolve_user_id(db, payload.owner_id or current_user.id)
    if current_user.role != "admin" and owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="不能为其他用户创建项目。")
    project = Project(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        owner_id=owner_id,
    )
    db.add(project)
    db.flush()
    write_audit_log(
        db,
        actor=current_user,
        action="project.create",
        resource_type="project",
        resource_id=project.id,
        summary=f"创建项目：{project.name}",
        detail={"code": project.code, "owner_id": str(project.owner_id)},
    )
    db.commit()
    db.refresh(project)
    return serialize_project(project)


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).order_by(Project.created_at.desc())
    if current_user.role != "admin":
        stmt = stmt.where(Project.owner_id == current_user.id)
    projects = db.scalars(stmt).all()
    return [serialize_project(item) for item in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_detail(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")
    ensure_project_access(current_user, project)
    return serialize_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")
    ensure_project_access(current_user, project)

    record_count = db.scalar(
        select(func.count(ExperimentRecord.id)).where(ExperimentRecord.project_id == project_id)
    )
    if record_count and record_count > 0:
        raise HTTPException(status_code=400, detail="该项目下已有实验记录，不能直接删除。")

    write_audit_log(
        db,
        actor=current_user,
        action="project.delete",
        resource_type="project",
        resource_id=project.id,
        summary=f"删除项目：{project.name}",
    )
    db.delete(project)
    db.commit()
