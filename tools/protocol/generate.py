# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic, first-party protocol v0 generators; deliberately not runtime-wired."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "tools" / "protocol"
SCHEMA = ROOT / "docs" / "specs" / "protocol.schema.json"
OUTPUTS = {
    "ts": ROOT / "apps" / "studio" / "src" / "engine" / "generated" / "protocol_v0.ts",
    "cpp": ROOT / "native" / "sidecar" / "generated" / "protocol_v0.hpp",
    "table": HOME / "generated" / "command_error_tables.md",
}



# Exact JSON Schema pattern approved by Fable, QUESTIONS Q8 / 0010 P1.
# Do not add a regex engine: generated Python/TS/C++ inspect UTF-8 bytes.
PRINTABLE_ASCII_PATTERN = r"^[\x20-\x7E]*$"


def validate_schema_patterns(node: object) -> None:
    """Fail generation on any pattern other than Q8's single literal."""
    if isinstance(node, list):
        for child in node:
            validate_schema_patterns(child)
    elif isinstance(node, dict):
        if "pattern" in node and (
            node["pattern"] != PRINTABLE_ASCII_PATTERN or node.get("type") != "string"
        ):
            raise ValueError(f"Unsupported protocol schema pattern: {node['pattern']!r}")
        for child in node.values():
            validate_schema_patterns(child)


def ts_alias(name: str) -> str:
    """Preserve existing schema names in stable exported TypeScript aliases."""
    return "Protocol" + name[0].upper() + name[1:]


def ts_type(shape: dict) -> str:
    """Emit the supported JSON Schema subset as structural TypeScript types.

    Bounds, integer-ness and UTF-8 transport rules remain runtime validation,
    not an invented compile-time constraint. Known required properties stay
    mandatory, and permissive Q3 document additions remain indexable.
    """
    if "$ref" in shape:
        prefix = "#/$defs/"
        ref = shape["$ref"]
        if not isinstance(ref, str) or not ref.startswith(prefix):
            raise ValueError(f"Unrepresentable schema reference: {ref!r}")
        return ts_alias(ref[len(prefix):])
    if "oneOf" in shape:
        return " | ".join("(" + ts_type(item) + ")" for item in shape["oneOf"])
    if "const" in shape:
        return json.dumps(shape["const"], ensure_ascii=False)
    if "enum" in shape:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in shape["enum"])
    kind = shape.get("type")
    if isinstance(kind, list):
        return " | ".join("(" + ts_type({**shape, "type": item}) + ")" for item in kind)
    if kind == "object":
        props = shape.get("properties", {})
        if not props:
            return "Record<string, unknown>"
        required = set(shape.get("required", []))
        fields = ["{"]  # Unknown document/push fields are intentionally permitted.
        for key, child in props.items():
            label = json.dumps(key, ensure_ascii=False)
            fields.append(f"  {label}{'' if key in required else '?'}: {ts_type(child)};")
        fields.append("  [key: string]: unknown;")
        fields.append("}")
        return "\n".join(fields)
    if kind == "array":
        item = shape.get("items")
        return "Array<" + (ts_type(item) if item is not None else "unknown") + ">"
    if kind in ("integer", "number"):
        return "number"
    if kind == "string":
        return "string"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    if kind is None:
        # Known shapes may specify only oneOf/const/enum/$ref above.
        raise ValueError(f"Cannot derive TS type from schema: {shape!r}")
    raise ValueError(f"Unsupported JSON Schema type: {kind!r}")


def ts_definitions(schema: dict) -> str:
    defs = schema["$defs"]
    output = [
        "// Generated from the schema, not hand-written payload approximations.",
        "// TypeScript cannot encode integer ranges, JSON physical line bytes, or",
        "// valid UTF-8 scalar sequences: the runtime validators enforce those.",
    ]
    for name, shape in defs.items():
        output.append(f"export type {ts_alias(name)} = {ts_type(shape)};")
    output.append("export type ProtocolV0 = ProtocolCommand | ProtocolReply | ProtocolPush;")
    return "\n\n".join(output)


def render() -> dict[str, str]:
    source = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validate_schema_patterns(source)
    expected_id = {"type": "string", "minLength": 1, "maxLength": 64,
                   "pattern": PRINTABLE_ASCII_PATTERN}
    if source["$defs"]["requestId"] != expected_id:
        raise ValueError("Q8 requestId must use exact ASCII pattern and 1..64 bounds")
    variants = source["$defs"]["command"]["oneOf"]
    command_types = [item["properties"]["type"]["const"] for item in variants]
    errors = source["$defs"]["reply"]["oneOf"][1]["properties"]["code"]["enum"]
    inline_schema = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    command_union = " | ".join(json.dumps(item, ensure_ascii=False) for item in command_types)
    error_union = " | ".join(json.dumps(item, ensure_ascii=False) for item in errors)
    substitutions = {
        "__SCHEMA_JSON__": inline_schema,
        "__COMMAND_TYPES__": command_union,
        "__ERROR_CODES__": error_union,
        "__SCHEMA_TYPES__": ts_definitions(source),
        "__PRINTABLE_ASCII_PATTERN__": json.dumps(PRINTABLE_ASCII_PATTERN),
    }
    results = {}
    for name, template in [
        ("ts", HOME / "templates" / "protocol_v0.ts.in"),
        ("cpp", HOME / "templates" / "protocol_v0.hpp.in"),
    ]:
        result = template.read_text(encoding="utf-8")
        for needle, value in substitutions.items():
            result = result.replace(needle, value)
        if any(key in result for key in substitutions):
            raise ValueError(f"Unresolved template substitution in {template}")
        results[name] = result
    table = [
        "<!-- SPDX-License-Identifier: GPL-3.0-only -->",
        "# Protocol v0 command and error inventory (generated; not runtime-wired)",
        "",
        "Source: `docs/specs/protocol.schema.json`; regenerate with `python tools/protocol/generate.py`.",
        "",
        "| Command type | Required payload fields |",
        "| --- | --- |",
    ]
    for item in variants:
        name = item["properties"]["type"]["const"]
        fields = [key for key in item["required"] if key not in ("v", "id", "type")]
        table.append(f"| `{name}` | {', '.join('`' + key + '`' for key in fields) if fields else '—'} |")
    table.extend(["", "| Refusal error code |", "| --- |"])
    table.extend(f"| `{name}` |" for name in errors)
    results["table"] = "\n".join(table) + "\n"
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when committed output drifts")
    options = parser.parse_args()
    outputs = render()
    errors = []
    for kind, result in outputs.items():
        target = OUTPUTS[kind]
        if options.check:
            if not target.exists() or target.read_text(encoding="utf-8") != result:
                errors.append(str(target.relative_to(ROOT)))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(result, encoding="utf-8")
            print("generated", target.relative_to(ROOT))
    if errors:
        for path in errors:
            print("DRIFT:", path)
        return 1
    if options.check:
        print("protocol v0 generated files: exact match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
