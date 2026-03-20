from __future__ import annotations

from typing import Any


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_plain_object(value: Any) -> bool:
    return isinstance(value, dict)


def normalize_chemical_equation_value(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    if isinstance(value, str):
        plain_text = value.strip()
        if not plain_text:
            return None
        return {
            "kind": "reaction" if plain_text.startswith("$RXN") else "molecule",
            "ket": "",
            "rxnfile": "",
            "molfile": "",
            "smiles": "",
            "svg": "",
            "plain_text": plain_text,
        }

    if not _is_plain_object(value):
        return None

    ket = _clean_string(value.get("ket"))
    rxnfile = _clean_string(value.get("rxnfile"))
    molfile = _clean_string(value.get("molfile"))
    smiles = _clean_string(value.get("smiles"))
    svg = _clean_string(value.get("svg"))
    plain_text_input = _clean_string(value.get("plain_text"))

    kind = "reaction" if value.get("kind") == "reaction" or rxnfile else "molecule"
    plain_text = plain_text_input or smiles or rxnfile or molfile or ket
    if not plain_text and not svg:
        return None

    return {
        "kind": kind,
        "ket": ket,
        "rxnfile": rxnfile,
        "molfile": molfile,
        "smiles": smiles,
        "svg": svg,
        "plain_text": plain_text,
    }


def normalize_reaction_process_value(value: Any) -> list[dict[str, str]]:
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return []
        if trimmed.startswith("["):
            try:
                import json

                return normalize_reaction_process_value(json.loads(trimmed))
            except Exception:
                pass
        return [
            {
                "title": line.strip(),
                "operation": "",
                "reagent": "",
                "condition": "",
                "observation": "",
                "note": "",
            }
            for line in trimmed.splitlines()
            if line.strip()
        ]

    if not isinstance(value, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in value:
        if not _is_plain_object(item):
            continue

        step = {
            "title": _clean_string(item.get("title")),
            "operation": _clean_string(item.get("operation")),
            "reagent": _clean_string(item.get("reagent")),
            "condition": _clean_string(item.get("condition")),
            "observation": _clean_string(item.get("observation")),
            "note": _clean_string(item.get("note")),
        }
        if any(step.values()):
            normalized.append(step)

    return normalized


def normalize_record_field_value(field_type: str, value: Any) -> Any:
    if field_type == "chemical_equation":
        return normalize_chemical_equation_value(value)
    if field_type == "reaction_process":
        return normalize_reaction_process_value(value)
    return value


def is_effectively_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return all(is_effectively_empty(item) for item in value.values())
    return False
