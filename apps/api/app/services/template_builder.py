from __future__ import annotations

from copy import deepcopy

from fastapi import HTTPException

from app.models.template import ExperimentTemplate, TemplateField, TemplateSection
from app.schemas.template import TemplateFieldIn, TemplateSectionIn

ALLOWED_FIELD_TYPES = {
    "text",
    "date",
    "textarea",
    "richtext",
    "table",
    "file",
    "number",
    "select",
    "checkbox",
    "json",
}


def validate_template_sections(sections: list[TemplateSectionIn]) -> None:
    section_keys: set[str] = set()

    for section in sections:
        if section.key in section_keys:
            raise HTTPException(status_code=422, detail=f"重复的 section key: {section.key}")
        section_keys.add(section.key)

        field_keys: set[str] = set()
        for field in section.fields:
            if field.key in field_keys:
                raise HTTPException(
                    status_code=422,
                    detail=f"section={section.key} 下存在重复字段 key: {field.key}",
                )
            field_keys.add(field.key)

            if field.field_type not in ALLOWED_FIELD_TYPES:
                raise HTTPException(
                    status_code=422,
                    detail=f"字段 {field.key} 的 field_type 不受支持: {field.field_type}",
                )


def replace_template_sections(
    template: ExperimentTemplate,
    sections_payload: list[TemplateSectionIn],
) -> None:
    template.sections.clear()

    for section_in in sections_payload:
        section = TemplateSection(
            key=section_in.key,
            title=section_in.title,
            description=section_in.description,
            order_index=section_in.order_index,
            is_repeatable=section_in.is_repeatable,
        )

        for field_in in section_in.fields:
            field = TemplateField(
                key=field_in.key,
                label=field_in.label,
                field_type=field_in.field_type,
                required=field_in.required,
                order_index=field_in.order_index,
                placeholder=field_in.placeholder,
                help_text=field_in.help_text,
                default_value=field_in.default_value,
                options=field_in.options,
                validation_rules=field_in.validation_rules,
                ui_props=field_in.ui_props,
            )
            section.fields.append(field)

        template.sections.append(section)


def export_template_sections(template: ExperimentTemplate) -> list[TemplateSectionIn]:
    exported: list[TemplateSectionIn] = []

    for section in template.sections:
        exported.append(
            TemplateSectionIn(
                key=section.key,
                title=section.title,
                description=section.description,
                order_index=section.order_index,
                is_repeatable=section.is_repeatable,
                fields=[
                    TemplateFieldIn(
                        key=field.key,
                        label=field.label,
                        field_type=field.field_type,
                        required=field.required,
                        order_index=field.order_index,
                        placeholder=field.placeholder,
                        help_text=field.help_text,
                        default_value=deepcopy(field.default_value),
                        options=deepcopy(field.options),
                        validation_rules=deepcopy(field.validation_rules),
                        ui_props=deepcopy(field.ui_props),
                    )
                    for field in section.fields
                ],
            )
        )

    return exported