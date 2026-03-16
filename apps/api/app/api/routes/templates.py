from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.record import ExperimentRecord
from app.models.template import ExperimentTemplate, TemplateSection
from app.schemas.template import (
    ExperimentTemplateCreate,
    ExperimentTemplateDetailOut,
    ExperimentTemplateSummaryOut,
    ExperimentTemplateUpdate,
)
from app.services.serializers import serialize_template_detail, serialize_template_summary
from app.services.template_builder import replace_template_sections, validate_template_sections
from app.services.user_resolver import resolve_user_id

router = APIRouter()


def load_template(db: Session, template_id: UUID) -> ExperimentTemplate | None:
    stmt = (
        select(ExperimentTemplate)
        .where(ExperimentTemplate.id == template_id)
        .options(selectinload(ExperimentTemplate.sections).selectinload(TemplateSection.fields))
    )
    return db.scalar(stmt)


def template_in_use(db: Session, template_id: UUID) -> bool:
    count = db.scalar(
        select(func.count(ExperimentRecord.id)).where(ExperimentRecord.template_id == template_id)
    )
    return bool(count and count > 0)


@router.get("", response_model=list[ExperimentTemplateSummaryOut])
def list_templates(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    stmt = select(ExperimentTemplate).order_by(
        ExperimentTemplate.category.asc(),
        ExperimentTemplate.name.asc(),
    )
    if active_only:
        stmt = stmt.where(ExperimentTemplate.is_active.is_(True))

    templates = db.scalars(stmt).all()
    return [serialize_template_summary(item) for item in templates]


@router.get("/by-key/{template_key}", response_model=ExperimentTemplateDetailOut)
def get_template_by_key(template_key: str, db: Session = Depends(get_db)):
    stmt = (
        select(ExperimentTemplate)
        .where(ExperimentTemplate.key == template_key)
        .options(selectinload(ExperimentTemplate.sections).selectinload(TemplateSection.fields))
    )
    template = db.scalar(stmt)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")
    return serialize_template_detail(template)


@router.get("/{template_id}", response_model=ExperimentTemplateDetailOut)
def get_template_detail(template_id: UUID, db: Session = Depends(get_db)):
    template = load_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")
    return serialize_template_detail(template)


@router.post("", response_model=ExperimentTemplateDetailOut, status_code=status.HTTP_201_CREATED)
def create_template(payload: ExperimentTemplateCreate, db: Session = Depends(get_db)):
    validate_template_sections(payload.sections)
    created_by = resolve_user_id(db, payload.created_by)

    template = ExperimentTemplate(
        name=payload.name,
        key=payload.key,
        description=payload.description,
        category=payload.category,
        parent_template_id=payload.parent_template_id,
        created_by=created_by,
        version=1,
        is_system=False,
        is_active=payload.is_active,
    )
    replace_template_sections(template, payload.sections)

    db.add(template)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="模板 key 重复或数据不合法。")

    created = load_template(db, template.id)
    return serialize_template_detail(created)


@router.put("/{template_id}", response_model=ExperimentTemplateDetailOut)
def update_template(
    template_id: UUID,
    payload: ExperimentTemplateUpdate,
    db: Session = Depends(get_db),
):
    template = load_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统模板不可直接编辑。")
    if template_in_use(db, template_id):
        raise HTTPException(status_code=400, detail="已有记录使用该模板，不能直接修改。")

    validate_template_sections(payload.sections)

    template.name = payload.name
    template.key = payload.key
    template.description = payload.description
    template.category = payload.category
    template.parent_template_id = payload.parent_template_id
    template.is_active = payload.is_active
    template.version += 1

    replace_template_sections(template, payload.sections)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="模板 key 重复或数据不合法。")

    updated = load_template(db, template_id)
    return serialize_template_detail(updated)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: UUID, db: Session = Depends(get_db)):
    template = db.get(ExperimentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统模板不可删除。")
    if template_in_use(db, template_id):
        raise HTTPException(status_code=400, detail="已有记录使用该模板，不能删除。")

    db.delete(template)
    db.commit()