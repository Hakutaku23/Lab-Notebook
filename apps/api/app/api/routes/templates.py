from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.record import ExperimentRecord
from app.models.template import ExperimentTemplate, TemplateSection
from app.models.user import User
from app.schemas.template import (
    ExperimentTemplateCreate,
    ExperimentTemplateDetailOut,
    ExperimentTemplateSummaryOut,
    ExperimentTemplateUpdate,
    TemplateLineageOut,
    TemplateVersionCreate,
)
from app.services.audit import write_audit_log
from app.services.permissions import ensure_template_access
from app.services.serializers import serialize_template_detail, serialize_template_summary
from app.services.template_builder import (
    export_template_sections,
    replace_template_sections,
    validate_template_sections,
)
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
    count = db.scalar(select(func.count(ExperimentRecord.id)).where(ExperimentRecord.template_id == template_id))
    return bool(count and count > 0)


def can_read_template(user: User, template: ExperimentTemplate) -> bool:
    return user.role == "admin" or template.created_by in (None, user.id)


def collect_template_family(
    db: Session,
    source: ExperimentTemplate,
) -> tuple[ExperimentTemplate, list[ExperimentTemplate]]:
    stmt = select(ExperimentTemplate).order_by(ExperimentTemplate.created_at.asc())
    all_templates = db.scalars(stmt).all()

    family_ids = {source.id}
    root = source
    visited: set[UUID] = set()

    while root.parent_template_id and root.parent_template_id not in visited:
        visited.add(root.id)
        parent = db.get(ExperimentTemplate, root.parent_template_id)
        if parent is None:
            break
        family_ids.add(parent.id)
        root = parent

    changed = True
    while changed:
        changed = False
        for item in all_templates:
            if item.parent_template_id in family_ids and item.id not in family_ids:
                family_ids.add(item.id)
                changed = True

    family = [item for item in all_templates if item.id in family_ids]
    family.sort(key=lambda item: (item.version, item.created_at))
    return root, family


def compute_next_family_version(db: Session, source: ExperimentTemplate) -> int:
    _, family = collect_template_family(db, source)
    max_version = max(item.version for item in family)
    return max_version + 1


@router.get("", response_model=list[ExperimentTemplateSummaryOut])
def list_templates(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ExperimentTemplate).order_by(ExperimentTemplate.category.asc(), ExperimentTemplate.name.asc())
    if active_only:
        stmt = stmt.where(ExperimentTemplate.is_active.is_(True))

    templates = db.scalars(stmt).all()
    if current_user.role != "admin":
        templates = [item for item in templates if item.created_by in (None, current_user.id)]

    return [serialize_template_summary(item) for item in templates]


@router.get("/by-key/{template_key}", response_model=ExperimentTemplateDetailOut)
def get_template_by_key(
    template_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(ExperimentTemplate)
        .where(ExperimentTemplate.key == template_key)
        .options(selectinload(ExperimentTemplate.sections).selectinload(TemplateSection.fields))
    )
    template = db.scalar(stmt)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")

    if not can_read_template(current_user, template):
        raise HTTPException(status_code=403, detail="无权访问该模板。")

    return serialize_template_detail(template)


@router.get("/{template_id}/lineage", response_model=TemplateLineageOut)
def get_template_lineage(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = db.get(ExperimentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")

    if not can_read_template(current_user, template):
        raise HTTPException(status_code=403, detail="无权访问该模板。")

    root, family = collect_template_family(db, template)

    if current_user.role != "admin":
        family = [item for item in family if can_read_template(current_user, item)]

    if not family:
        raise HTTPException(status_code=404, detail="未找到可访问的模板谱系。")

    visible_root = family[0]

    return TemplateLineageOut(
        root_template_id=visible_root.id,
        current_template_id=template.id,
        items=[serialize_template_summary(item) for item in family],
    )


@router.get("/{template_id}", response_model=ExperimentTemplateDetailOut)
def get_template_detail(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = load_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")

    if not can_read_template(current_user, template):
        raise HTTPException(status_code=403, detail="无权访问该模板。")

    return serialize_template_detail(template)


@router.post("", response_model=ExperimentTemplateDetailOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: ExperimentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_template_sections(payload.sections)

    created_by = resolve_user_id(db, payload.created_by or current_user.id)
    if current_user.role != "admin" and created_by != current_user.id:
        raise HTTPException(status_code=403, detail="不能为其他用户创建模板。")

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
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="模板 key 重复或数据不合法。")

    write_audit_log(
        db,
        actor=current_user,
        action="template.create",
        resource_type="template",
        resource_id=template.id,
        summary=f"创建模板：{template.name}",
        detail={"key": template.key, "category": template.category},
    )

    db.commit()
    created = load_template(db, template.id)
    return serialize_template_detail(created)


@router.put("/{template_id}", response_model=ExperimentTemplateDetailOut)
def update_template(
    template_id: UUID,
    payload: ExperimentTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = load_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")

    if template.is_system and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="系统模板不可直接编辑。")

    ensure_template_access(current_user, template)

    if template_in_use(db, template_id):
        raise HTTPException(status_code=400, detail="已有记录使用该模板，不能直接修改。")

    validate_template_sections(payload.sections)

    before = {"name": template.name, "version": template.version, "key": template.key}

    template.name = payload.name
    template.key = payload.key
    template.description = payload.description
    template.category = payload.category
    template.parent_template_id = payload.parent_template_id
    template.is_active = payload.is_active
    template.version += 1

    # Flush orphan deletions first so unique section keys can be re-used safely.
    template.sections.clear()
    db.flush()
    replace_template_sections(template, payload.sections)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="模板 key 重复或数据不合法。")

    write_audit_log(
        db,
        actor=current_user,
        action="template.update",
        resource_type="template",
        resource_id=template.id,
        summary=f"更新模板：{template.name}",
        detail={
            "before": before,
            "after": {"name": template.name, "version": template.version, "key": template.key},
        },
    )

    db.commit()
    updated = load_template(db, template_id)
    return serialize_template_detail(updated)


@router.post(
    "/{template_id}/versions",
    response_model=ExperimentTemplateDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def create_template_version(
    template_id: UUID,
    payload: TemplateVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = load_template(db, template_id)
    if source is None:
        raise HTTPException(status_code=404, detail="源模板不存在。")

    if not can_read_template(current_user, source):
        raise HTTPException(status_code=403, detail="无权基于该模板创建新版本。")

    sections_payload = payload.sections or export_template_sections(source)
    validate_template_sections(sections_payload)

    created_by = current_user.id
    if payload.created_by is not None:
        created_by = resolve_user_id(db, payload.created_by)

    if current_user.role != "admin" and created_by != current_user.id:
        raise HTTPException(status_code=403, detail="不能为其他用户创建模板版本。")

    next_version = compute_next_family_version(db, source)

    template = ExperimentTemplate(
        name=payload.name or source.name,
        key=payload.key,
        description=payload.description if payload.description is not None else source.description,
        category=payload.category or source.category,
        parent_template_id=source.id,
        created_by=created_by,
        version=next_version,
        is_system=False,
        is_active=payload.is_active,
        extra_config=deepcopy(source.extra_config),
    )
    replace_template_sections(template, sections_payload)
    db.add(template)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="模板 key 重复或数据不合法。")

    write_audit_log(
        db,
        actor=current_user,
        action="template.version.create",
        resource_type="template",
        resource_id=template.id,
        summary=f"基于模板 {source.name} 创建新版本：{template.name}",
        detail={
            "source_template_id": str(source.id),
            "source_version": source.version,
            "new_version": template.version,
            "new_key": template.key,
        },
    )

    db.commit()
    created = load_template(db, template.id)
    return serialize_template_detail(created)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = db.get(ExperimentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在。")

    if template.is_system and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="系统模板不可删除。")

    ensure_template_access(current_user, template)

    if template_in_use(db, template_id):
        raise HTTPException(status_code=400, detail="已有记录使用该模板，不能删除。")

    write_audit_log(
        db,
        actor=current_user,
        action="template.delete",
        resource_type="template",
        resource_id=template.id,
        summary=f"删除模板：{template.name}",
    )

    db.delete(template)
    db.commit()
