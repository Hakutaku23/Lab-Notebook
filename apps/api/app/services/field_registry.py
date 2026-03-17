from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FieldTypeDefinition:
    key: str
    label: str
    category: str
    description: str
    accepts_structured_value: bool = False
    ui_hint: str | None = None


FIELD_TYPE_DEFINITIONS: dict[str, FieldTypeDefinition] = {
    "text": FieldTypeDefinition(
        key="text",
        label="单行文本",
        category="basic",
        description="适合标题、编号、名称等短文本输入。",
    ),
    "textarea": FieldTypeDefinition(
        key="textarea",
        label="多行文本",
        category="basic",
        description="适合实验目的、结论、现象记录等长文本输入。",
        ui_hint="textarea",
    ),
    "richtext": FieldTypeDefinition(
        key="richtext",
        label="富文本",
        category="basic",
        description="当前以前端多行文本方式编辑，后续可接入真正富文本编辑器。",
        ui_hint="textarea",
    ),
    "date": FieldTypeDefinition(
        key="date",
        label="日期",
        category="basic",
        description="记录实验日期、采样日期、校准日期等。",
        ui_hint="date",
    ),
    "number": FieldTypeDefinition(
        key="number",
        label="数字",
        category="basic",
        description="适合质量、体积、温度、时间、转速等数值输入。",
        ui_hint="number",
    ),
    "select": FieldTypeDefinition(
        key="select",
        label="下拉选择",
        category="basic",
        description="单选枚举值。",
        ui_hint="select",
    ),
    "checkbox": FieldTypeDefinition(
        key="checkbox",
        label="勾选项",
        category="basic",
        description="布尔值开关。",
        ui_hint="checkbox",
    ),
    "json": FieldTypeDefinition(
        key="json",
        label="JSON 数据",
        category="structured",
        description="以结构化 JSON 记录复杂对象。",
        accepts_structured_value=True,
        ui_hint="json",
    ),
    "table": FieldTypeDefinition(
        key="table",
        label="表格数据",
        category="structured",
        description="可填写 JSON、CSV 或 Markdown 表格内容。",
        accepts_structured_value=True,
        ui_hint="table",
    ),
    "file": FieldTypeDefinition(
        key="file",
        label="文件说明",
        category="structured",
        description="当前保存附件说明信息；真实文件上传仍在记录详情页完成。",
        accepts_structured_value=True,
        ui_hint="file",
    ),
    "chemical_equation": FieldTypeDefinition(
        key="chemical_equation",
        label="化学反应方程式",
        category="chemistry",
        description="用于记录化学反应方程式、条件与备注，为后续专业化学编辑器预留结构。",
        accepts_structured_value=True,
        ui_hint="chemical_equation",
    ),
    "reaction_process": FieldTypeDefinition(
        key="reaction_process",
        label="反应过程步骤",
        category="chemistry",
        description="以步骤列表记录简易或复杂反应流程、条件和现象。",
        accepts_structured_value=True,
        ui_hint="reaction_process",
    ),
}

ALLOWED_FIELD_TYPES = set(FIELD_TYPE_DEFINITIONS.keys())


def is_supported_field_type(field_type: str) -> bool:
    return field_type in FIELD_TYPE_DEFINITIONS


def list_field_type_definitions() -> list[dict[str, str | bool | None]]:
    return [
        asdict(FIELD_TYPE_DEFINITIONS[key])
        for key in sorted(FIELD_TYPE_DEFINITIONS.keys())
    ]
