from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateFieldTypeDefinition:
    key: str
    label: str
    category: str = "generic"
    description: str = ""
    default_ui_props: dict | None = None


FIELD_TYPE_DEFINITIONS: dict[str, TemplateFieldTypeDefinition] = {
    "text": TemplateFieldTypeDefinition("text", "单行文本", description="适合简短说明、名称、编号等。"),
    "date": TemplateFieldTypeDefinition("date", "日期", description="用于记录实验日期、取样日期等。"),
    "textarea": TemplateFieldTypeDefinition("textarea", "多行文本", description="适合过程、现象、分析结论。"),
    "richtext": TemplateFieldTypeDefinition("richtext", "富文本", description="当前以前端多行文本方式录入，可后续接入富文本编辑器。"),
    "table": TemplateFieldTypeDefinition("table", "表格/结构化文本", description="可填写 JSON、CSV 或 Markdown 表格内容。"),
    "file": TemplateFieldTypeDefinition("file", "文件说明", description="用于填写附件说明；真实文件上传仍在记录详情页完成。"),
    "number": TemplateFieldTypeDefinition("number", "数值", description="适合质量、体积、温度、浓度等数值。"),
    "select": TemplateFieldTypeDefinition("select", "枚举选择", description="单选枚举字段，选项定义在 options 中。"),
    "checkbox": TemplateFieldTypeDefinition("checkbox", "布尔选项", description="勾选 / 不勾选。"),
    "json": TemplateFieldTypeDefinition("json", "JSON", description="直接填写结构化 JSON 内容。"),
    "chemical_equation": TemplateFieldTypeDefinition(
        "chemical_equation",
        "化学反应方程式",
        category="chemistry",
        description="支持结构化录入反应物、生成物、箭头和条件，也支持直接手写方程式。",
        default_ui_props={"arrow": "→", "mode": "structured"},
    ),
    "reaction_process": TemplateFieldTypeDefinition(
        "reaction_process",
        "化学反应过程",
        category="chemistry",
        description="按步骤记录操作、条件和现象，适合化学实验过程追踪。",
        default_ui_props={"stepLabel": "步骤"},
    ),
}


def get_supported_field_types() -> set[str]:
    return set(FIELD_TYPE_DEFINITIONS.keys())


def is_supported_field_type(field_type: str) -> bool:
    return field_type in FIELD_TYPE_DEFINITIONS
