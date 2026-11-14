"""Conservative structural inference, including union and absence handling."""

from __future__ import annotations

from typing import Any

from .models import Json


def infer(value: Any) -> Json:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        items: Json = {}
        for item in value:
            items = merge(items, infer(item))
        return {"type": "array", "items": items}
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {k: infer(v) for k, v in value.items()},
            "required": sorted(value),
        }
    return {}


def merge(left: Json, right: Json) -> Json:
    if not left:
        return right
    if not right or left == right:
        return left
    if left.get("type") == right.get("type") == "object":
        a, b = left["properties"], right["properties"]
        return {
            "type": "object",
            "properties": {
                key: merge(a.get(key, {}), b.get(key, {})) for key in sorted(a.keys() | b.keys())
            },
            "required": sorted(set(left.get("required", [])) & set(right.get("required", []))),
        }
    if left.get("type") == right.get("type") == "array":
        return {"type": "array", "items": merge(left["items"], right["items"])}
    variants = left.get("anyOf", [left]) + right.get("anyOf", [right])
    unique = []
    for variant in variants:
        if variant not in unique:
            unique.append(variant)
    return {"anyOf": unique}
