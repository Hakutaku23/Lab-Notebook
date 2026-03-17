from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.template import ExperimentTemplate, TemplateSection, TemplateField


GENERIC_TEMPLATE_KEY = "generic-experiment-v1"


def build_generic_template():
    return {
        "name": "通用实验记录模板",
        "key": GENERIC_TEMPLATE_KEY,
        "description": "适用于大多数基础实验记录场景的通用模板",
        "category": "generic",
        "sections": [
            {
                "key": "basic_info",
                "title": "基本信息",
                "order_index": 1,
                "fields": [
                    {"key": "experiment_name", "label": "实验名称", "field_type": "text", "required": True, "order_index": 1},
                    {"key": "experiment_code", "label": "实验编号", "field_type": "text", "required": False, "order_index": 2},
                    {"key": "experiment_date", "label": "实验日期", "field_type": "date", "required": True, "order_index": 3},
                    {"key": "operator", "label": "实验人员", "field_type": "text", "required": True, "order_index": 4},
                    {"key": "location", "label": "实验地点", "field_type": "text", "required": False, "order_index": 5},
                ]
            },
            {
                "key": "objective",
                "title": "实验目的",
                "order_index": 2,
                "fields": [
                    {"key": "objective_text", "label": "实验目的", "field_type": "textarea", "required": True, "order_index": 1},
                    {"key": "background", "label": "实验背景", "field_type": "richtext", "required": False, "order_index": 2},
                ]
            },
            {
                "key": "materials",
                "title": "材料与设备",
                "order_index": 3,
                "fields": [
                    {"key": "materials_list", "label": "试剂/材料", "field_type": "table", "required": False, "order_index": 1},
                    {"key": "equipment_list", "label": "仪器设备", "field_type": "table", "required": False, "order_index": 2},
                ]
            },
            {
                "key": "procedure",
                "title": "实验步骤",
                "order_index": 4,
                "fields": [
                    {"key": "procedure_text", "label": "实验步骤", "field_type": "richtext", "required": True, "order_index": 1},
                    {"key": "safety_notes", "label": "安全注意事项", "field_type": "textarea", "required": False, "order_index": 2},
                ]
            },
            {
                "key": "observation",
                "title": "实验现象与原始数据",
                "order_index": 5,
                "fields": [
                    {"key": "observation_text", "label": "实验现象", "field_type": "richtext", "required": False, "order_index": 1},
                    {"key": "raw_data_table", "label": "原始数据", "field_type": "table", "required": False, "order_index": 2},
                    {"key": "attachments", "label": "附件", "field_type": "file", "required": False, "order_index": 3},
                ]
            },
            {
                "key": "analysis",
                "title": "数据处理与分析",
                "order_index": 6,
                "fields": [
                    {"key": "processing_method", "label": "处理方法", "field_type": "richtext", "required": False, "order_index": 1},
                    {"key": "analysis_result", "label": "分析结果", "field_type": "richtext", "required": False, "order_index": 2},
                ]
            },
            {
                "key": "conclusion",
                "title": "结论",
                "order_index": 7,
                "fields": [
                    {"key": "conclusion_text", "label": "实验结论", "field_type": "richtext", "required": True, "order_index": 1},
                    {"key": "follow_up", "label": "后续建议", "field_type": "textarea", "required": False, "order_index": 2},
                ]
            }
        ]
    }


def main():
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(ExperimentTemplate).where(ExperimentTemplate.key == GENERIC_TEMPLATE_KEY)
        )
        if existing:
            print("通用模板已存在，跳过初始化。")
            return

        tpl_data = build_generic_template()
        template = ExperimentTemplate(
            name=tpl_data["name"],
            key=tpl_data["key"],
            description=tpl_data["description"],
            category=tpl_data["category"],
            version=1,
            is_system=True,
            is_active=True,
        )
        db.add(template)
        db.flush()

        for section_data in tpl_data["sections"]:
            section = TemplateSection(
                template_id=template.id,
                key=section_data["key"],
                title=section_data["title"],
                order_index=section_data["order_index"],
            )
            db.add(section)
            db.flush()

            for field_data in section_data["fields"]:
                field = TemplateField(
                    section_id=section.id,
                    key=field_data["key"],
                    label=field_data["label"],
                    field_type=field_data["field_type"],
                    required=field_data.get("required", False),
                    order_index=field_data.get("order_index", 0),
                )
                db.add(field)

        db.commit()
        print("通用实验记录模板初始化完成。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
