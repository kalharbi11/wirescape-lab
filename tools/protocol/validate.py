# SPDX-License-Identifier: GPL-3.0-only
"""Pure Python validation oracle for the restricted protocol-v0 schema subset."""
from __future__ import annotations

import json
import math
from pathlib import Path

from generate import PRINTABLE_ASCII_PATTERN, validate_schema_patterns

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "specs" / "protocol.schema.json"
SUPPORTED = {
    "$schema", "$id", "title", "description", "$defs", "$ref", "oneOf", "type",
    "required", "properties", "const", "enum", "minimum", "maximum",
    "minLength", "maxLength", "minItems", "maxItems", "items", "pattern",
}


def read_schema() -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validate_schema_patterns(schema)
    return schema


def check_schema_subset(node: object, *, map_keys: bool = False) -> None:
    if isinstance(node, list):
        for value in node:
            check_schema_subset(value)
    elif isinstance(node, dict):
        for key, value in node.items():
            if not map_keys and key not in SUPPORTED:
                raise ValueError(f"Unsupported schema keyword: {key}")
            check_schema_subset(value, map_keys=key in ("$defs", "properties"))



def json_equal(left: object, right: object) -> bool:
    """JSON Schema equality: booleans are not numbers; 1 and 1.0 are equal."""
    if left is None or right is None:
        return left is None and right is None
    if type(left) is bool or type(right) is bool:
        return type(left) is bool and type(right) is bool and left is right
    if type(left) in (int, float) or type(right) in (int, float):
        return (type(left) in (int, float) and type(right) in (int, float)
                and math.isfinite(left) and math.isfinite(right) and left == right)
    if type(left) is str or type(right) is str:
        return type(left) is str and type(right) is str and left == right
    if type(left) is list or type(right) is list:
        return (type(left) is list and type(right) is list
                and len(left) == len(right)
                and all(json_equal(a, b) for a, b in zip(left, right)))
    if type(left) is dict or type(right) is dict:
        return (type(left) is dict and type(right) is dict
                and left.keys() == right.keys()
                and all(json_equal(left[key], right[key]) for key in left))
    return False


def validate(value: object, schema: dict | None = None) -> bool:
    root = read_schema() if schema is None else schema

    def match(shape: dict, instance: object, depth: int) -> bool:
        if depth > 64 or not isinstance(shape, dict):
            return False
        if "$ref" in shape:
            name = shape["$ref"]
            if not isinstance(name, str) or not name.startswith("#/$defs/"):
                return False
            definition = root["$defs"].get(name.removeprefix("#/$defs/"))
            return isinstance(definition, dict) and match(definition, instance, depth + 1)
        if "oneOf" in shape:
            return sum(match(candidate, instance, depth + 1) for candidate in shape["oneOf"]) == 1

        def has_type(kind: str) -> bool:
            if kind == "object":
                return isinstance(instance, dict)
            if kind == "array":
                return isinstance(instance, list)
            if kind == "string":
                return isinstance(instance, str)
            if kind == "boolean":
                return isinstance(instance, bool)
            if kind == "null":
                return instance is None
            if kind == "integer":
                return type(instance) is int
            if kind == "number":
                return type(instance) in (int, float) and math.isfinite(instance)
            return False

        kinds = shape.get("type")
        if kinds is not None:
            if not any(has_type(k) for k in (kinds if isinstance(kinds, list) else [kinds])):
                return False
        if "const" in shape and not json_equal(instance, shape["const"]):
            return False
        if "enum" in shape and not any(json_equal(instance, item) for item in shape["enum"]):
            return False
        if type(instance) in (int, float):
            if not math.isfinite(instance):
                return False
            if "minimum" in shape and instance < shape["minimum"]:
                return False
            if "maximum" in shape and instance > shape["maximum"]:
                return False
        if isinstance(instance, str):
            if "minLength" in shape and len(instance) < shape["minLength"]:
                return False
            if "maxLength" in shape and len(instance) > shape["maxLength"]:
                return False
            if "pattern" in shape:
                if shape["pattern"] != PRINTABLE_ASCII_PATTERN:
                    return False
                # Q8: ASCII bytes 0x20..0x7E, no regex evaluation.
                if any(byte < 0x20 or byte > 0x7E for byte in instance.encode("utf-8")):
                    return False
        elif "pattern" in shape:
            return False
        if isinstance(instance, list):
            if "minItems" in shape and len(instance) < shape["minItems"]:
                return False
            if "maxItems" in shape and len(instance) > shape["maxItems"]:
                return False
            if "items" in shape and any(not match(shape["items"], item, depth + 1) for item in instance):
                return False
        if isinstance(instance, dict):
            if any(key not in instance for key in shape.get("required", [])):
                return False
            if any(key in instance and not match(child, instance[key], depth + 1)
                   for key, child in shape.get("properties", {}).items()):
                return False
            # Deliberate P2/Q3: unknown patch/document properties are allowed and untouched.
        return True

    return match(root, value, 0)


def parse_line(text: str, schema: dict | None = None) -> dict:
    if len(text.encode("utf-8")) > 2_097_152:
        raise ValueError("line exceeds protocol byte cap")

    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate wire key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant: {value}")

    message = json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
    if not isinstance(message, dict) or not validate(message, schema):
        raise ValueError("protocol v0 schema mismatch")
    return message
