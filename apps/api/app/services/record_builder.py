from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.models.record import RecordFieldValue
from app.models.template import ExperimentTemplate, TemplateField
from app.schemas.record import RecordFieldValueIn


def is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def collect_template_fields(template: ExperimentTemplate) -> dict:
    field_map: dict = {}
    for section in template.sections:
        for field in section.fields:
            field_map[field.id] = field
    return field_map


def build_record_values(
    template: ExperimentTemplate,
    payload_values: list[RecordFieldValueIn],
) -> list[RecordFieldValue]:
    field_map = collect_template_fields(template)

    submitted_ids = set()
    built_values: list[RecordFieldValue] = []

    for item in payload_values:
        if item.field_id in submitted_ids:
            raise HTTPException(status_code=422, detail="同一个字段被重复提交。")
        submitted_ids.add(item.field_id)

        field: TemplateField | None = field_map.get(item.field_id)
        if field is None:
            raise HTTPException(status_code=422, detail="提交了不属于该模板的字段。")

        if is_empty_value(item.value_json):
            continue

        built_values.append(
            RecordFieldValue(
                field_id=field.id,
                section_key_snapshot=field.section.key,
                field_key_snapshot=field.key,
                field_label_snapshot=field.label,
                field_type_snapshot=field.field_type,
                value_json=item.value_json,
                note=item.note,
            )
        )

    missing_required_fields: list[str] = []
    submitted_map = {item.field_id: item for item in payload_values}

    for section in template.sections:
        for field in section.fields:
            if not field.required:
                continue
            submitted = submitted_map.get(field.id)
            if submitted is None or is_empty_value(submitted.value_json):
                missing_required_fields.append(field.label)

    if missing_required_fields:
        raise HTTPException(
            status_code=422,
            detail=f"必填字段未填写：{', '.join(missing_required_fields)}"
        )

    return built_values