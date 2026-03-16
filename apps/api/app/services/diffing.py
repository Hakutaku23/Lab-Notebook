from __future__ import annotations

from typing import Any

from app.models.version import RecordVersion


RECORD_FIELD_LABELS = {
    "title": "标题",
    "status": "状态",
    "summary": "摘要",
    "template_version": "模板版本",
}


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        return sorted((_normalize(item) for item in value), key=lambda item: str(item))
    if isinstance(value, dict):
        return {key: _normalize(val) for key, val in sorted(value.items())}
    return value


def build_version_diff(from_version: RecordVersion, to_version: RecordVersion) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    from_record = from_version.snapshot_json.get("record", {})
    to_record = to_version.snapshot_json.get("record", {})
    for field_name, label in RECORD_FIELD_LABELS.items():
        before = from_record.get(field_name)
        after = to_record.get(field_name)
        if _normalize(before) != _normalize(after):
            items.append(
                {
                    "group": "record",
                    "key": field_name,
                    "label": label,
                    "change_type": "updated",
                    "before": before,
                    "after": after,
                }
            )

    from_values = {
        item["field_key_snapshot"]: item
        for item in from_version.snapshot_json.get("values", [])
    }
    to_values = {
        item["field_key_snapshot"]: item
        for item in to_version.snapshot_json.get("values", [])
    }
    value_keys = sorted(set(from_values) | set(to_values))
    for key in value_keys:
        before_item = from_values.get(key)
        after_item = to_values.get(key)
        label = (
            after_item or before_item or {}
        ).get("field_label_snapshot", key)
        section_key = (after_item or before_item or {}).get("section_key_snapshot", "unknown")
        if before_item is None:
            items.append(
                {
                    "group": "value",
                    "key": f"{section_key}.{key}",
                    "label": label,
                    "change_type": "added",
                    "before": None,
                    "after": after_item.get("value_json") if after_item else None,
                }
            )
            continue
        if after_item is None:
            items.append(
                {
                    "group": "value",
                    "key": f"{section_key}.{key}",
                    "label": label,
                    "change_type": "removed",
                    "before": before_item.get("value_json"),
                    "after": None,
                }
            )
            continue
        before = before_item.get("value_json")
        after = after_item.get("value_json")
        if _normalize(before) != _normalize(after):
            items.append(
                {
                    "group": "value",
                    "key": f"{section_key}.{key}",
                    "label": label,
                    "change_type": "updated",
                    "before": before,
                    "after": after,
                }
            )

    from_attachments = {
        item["stored_name"]: item
        for item in from_version.snapshot_json.get("attachments", [])
    }
    to_attachments = {
        item["stored_name"]: item
        for item in to_version.snapshot_json.get("attachments", [])
    }
    attachment_keys = sorted(set(from_attachments) | set(to_attachments))
    for key in attachment_keys:
        before_item = from_attachments.get(key)
        after_item = to_attachments.get(key)
        label = (after_item or before_item or {}).get("original_name", key)
        if before_item is None:
            items.append(
                {
                    "group": "attachment",
                    "key": key,
                    "label": label,
                    "change_type": "added",
                    "before": None,
                    "after": label,
                }
            )
        elif after_item is None:
            items.append(
                {
                    "group": "attachment",
                    "key": key,
                    "label": label,
                    "change_type": "removed",
                    "before": label,
                    "after": None,
                }
            )

    return items
