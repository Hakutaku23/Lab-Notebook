from __future__ import annotations

from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.template import ExperimentTemplate
from app.models.user import User
from app.models.version import RecordVersion


def serialize_current_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def serialize_attachment(item: Attachment) -> dict:
    return {
        "id": item.id,
        "record_id": item.record_id,
        "uploaded_by": item.uploaded_by,
        "original_name": item.original_name,
        "stored_name": item.stored_name,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "description": item.description,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "download_url": f"/api/attachments/{item.id}/download",
    }


def serialize_template_summary(template: ExperimentTemplate) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "key": template.key,
        "description": template.description,
        "category": template.category,
        "version": template.version,
        "is_system": template.is_system,
        "is_active": template.is_active,
        "parent_template_id": template.parent_template_id,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def serialize_template_detail(template: ExperimentTemplate) -> dict:
    return {
        **serialize_template_summary(template),
        "sections": [
            {
                "id": section.id,
                "key": section.key,
                "title": section.title,
                "description": section.description,
                "order_index": section.order_index,
                "is_repeatable": section.is_repeatable,
                "fields": [
                    {
                        "id": field.id,
                        "key": field.key,
                        "label": field.label,
                        "field_type": field.field_type,
                        "required": field.required,
                        "order_index": field.order_index,
                        "placeholder": field.placeholder,
                        "help_text": field.help_text,
                        "default_value": field.default_value,
                        "options": field.options,
                        "validation_rules": field.validation_rules,
                        "ui_props": field.ui_props,
                    }
                    for field in section.fields
                ],
            }
            for section in template.sections
        ],
    }


def serialize_project(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "owner_id": project.owner_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def serialize_record_summary(
    record: ExperimentRecord,
    allowed_actions: list[str] | None = None,
) -> dict:
    return {
        "id": record.id,
        "title": record.title,
        "status": record.status,
        "summary": record.summary,
        "project_id": record.project_id,
        "project_name": record.project.name if record.project else None,
        "template_id": record.template_id,
        "template_name": record.template.name if record.template else None,
        "template_version": record.template_version,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "allowed_actions": allowed_actions or [],
    }


def serialize_record_detail(
    record: ExperimentRecord,
    allowed_actions: list[str] | None = None,
) -> dict:
    return {
        **serialize_record_summary(record, allowed_actions=allowed_actions),
        "values": [
            {
                "id": value.id,
                "field_id": value.field_id,
                "section_key_snapshot": value.section_key_snapshot,
                "field_key_snapshot": value.field_key_snapshot,
                "field_label_snapshot": value.field_label_snapshot,
                "field_type_snapshot": value.field_type_snapshot,
                "value_json": value.value_json,
                "note": value.note,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
            for value in record.values
        ],
        "attachments": [serialize_attachment(item) for item in record.attachments],
    }


def serialize_version_summary(item: RecordVersion) -> dict:
    return {
        "id": item.id,
        "record_id": item.record_id,
        "created_by": item.created_by,
        "version_no": item.version_no,
        "comment": item.comment,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def serialize_version_detail(item: RecordVersion) -> dict:
    return {
        **serialize_version_summary(item),
        "snapshot_json": item.snapshot_json,
    }

def serialize_audit_log(item: AuditLog) -> dict:
    return {
        "id": item.id,
        "actor_id": item.actor_id,
        "actor_username": item.actor_username,
        "action": item.action,
        "resource_type": item.resource_type,
        "resource_id": item.resource_id,
        "summary": item.summary,
        "detail_json": item.detail_json,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }