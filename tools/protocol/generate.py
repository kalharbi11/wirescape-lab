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


def render() -> dict[str, str]:
    source = json.loads(SCHEMA.read_text(encoding="utf-8"))
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
    }
    results = {}
    for name, template in [
        ("ts", HOME / "templates" / "protocol_v0.ts.in"),
        ("cpp", HOME / "templates" / "protocol_v0.hpp.in"),
    ]:
        result = template.read_text(encoding="utf-8")
        for needle, value in substitutions.items():
            result = result.replace(needle, value)
        if "__SCHEMA_JSON__" in result or "__COMMAND_TYPES__" in result or "__ERROR_CODES__" in result:
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
