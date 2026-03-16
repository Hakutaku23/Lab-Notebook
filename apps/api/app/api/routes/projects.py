from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.serializers import serialize_project
from app.services.user_resolver import resolve_user_id

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    owner_id = resolve_user_id(db, payload.owner_id)

    project = Project(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        owner_id=owner_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize_project(project)


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    stmt = select(Project).order_by(Project.created_at.desc())
    projects = db.scalars(stmt).all()
    return [serialize_project(item) for item in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_detail(project_id: UUID, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")
    return serialize_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")

    record_count = db.scalar(
        select(func.count(ExperimentRecord.id)).where(ExperimentRecord.project_id == project_id)
    )
    if record_count and record_count > 0:
        raise HTTPException(status_code=400, detail="该项目下已有实验记录，不能直接删除。")

    db.delete(project)
    db.commit()