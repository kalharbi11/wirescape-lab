# SPDX-License-Identifier: GPL-3.0-only
"""Unwired contract corpus and preservation tests; devices/network not opened here."""
from __future__ import annotations

import copy
import json
import re
import unittest

from validate import ROOT, check_schema_subset, parse_line, read_schema, validate


SPEC = ROOT / "docs" / "specs" / "ENGINE_PROTOCOL.md"
SIDECAR = ROOT / "native" / "sidecar" / "protocol_tests.py"


class ProtocolV0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read_schema()

    def test_schema_uses_restricted_keywords(self):
        check_schema_subset(self.schema)
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(self.schema["$defs"]["command"]["oneOf"]), 20)

    def test_every_normative_spec_section_10_wire_line(self):
        section = SPEC.read_text(encoding="utf-8").split(
            "## 10. Normative example exchanges", 1
        )[1]
        markers = re.findall(r"\*\*T(\d\d)\b", section)
        self.assertEqual(markers, [f"{n:02d}" for n in range(1, 17)])
        validated = []
        malformed = []
        for line_number, line in enumerate(section.splitlines(), 1):
            match = re.match(r"^([<>@])\s+(\{.*)$", line)
            if not match:
                continue
            marker, raw = match.groups()
            try:
                wire = parse_line(raw, self.schema)
            except (ValueError, json.JSONDecodeError):
                malformed.append((line_number, raw))
                self.assertEqual(marker, ">")
                self.assertIn("BROKEN", raw)
                continue
            validated.append((marker, wire))
        self.assertEqual(len(malformed), 1, malformed)
        self.assertGreaterEqual(len(validated), 35)
        self.assertTrue(any(m.get("type") == "hello" for _, m in validated))
        self.assertTrue(any(m.get("type") == "telemetry" for _, m in validated))
        self.assertTrue(any(m.get("type") == "app.engineExited" for _, m in validated))
        for _, message in validated:
            self.assertEqual(message["v"], 0)
            if "re" in message and "id" not in message:
                self.assertIn("gen", message)

        for request_id in ("r9b", "r10b"):
            found = [m for _, m in validated if m.get("id") == request_id]
            self.assertEqual(len(found), 1)
            self.assertNotEqual(found[0]["id"], found[0]["deviceId"])

    def test_unknown_document_fields_are_retained(self):
        original = {
            "v": 0, "id": "fixture", "type": "loadGraph",
            "patch": {
                "format": "wirescape.native.patch", "version": 2,
                "modules": [{"id": 1, "module": "essentials.output",
                             "config": {"novel": {"deep": [1, "opaque", None]}},
                             "future_module_key": "keep"}],
                "connections": [], "ui": {"other-ui-key": {"alpha": 10}},
                "future_root": {"exact": [True, None, {"unknown": 13}]},
            },
        }
        before = copy.deepcopy(original)
        self.assertTrue(validate(original, self.schema))
        self.assertEqual(original, before)
        self.assertEqual(original["patch"]["future_root"], before["patch"]["future_root"])
        # Payload must not be stripped, coerced or normalized by a validation call.
        self.assertEqual(json.dumps(original), json.dumps(before))

    def test_known_envelope_fields_are_enforced(self):
        good = {"v": 0, "id": "x", "type": "noteOn", "note": 60, "velocity": 0.8}
        self.assertTrue(validate(good, self.schema))
        for bad in [
            {**good, "v": 1}, {**good, "id": ""},
            {**good, "note": 128}, {**good, "velocity": -0.01},
            {**good, "note": 1.2}, {**good, "type": "notACommand"},
            {"v": 0, "re": "x", "ok": False, "gen": "0"},
        ]:
            self.assertFalse(validate(bad, self.schema), bad)

    def test_connection_identity_ignores_nested_amount_only_for_identity_operations(self):
        identity = {
            "kind": "modulation",
            "from": {"module": 10, "port": "control"},
            "to": {"module": 9, "port": "frequency"},
            "amount": "ignored",
        }
        for command_type, extra in [
            ("disconnect", {}),
            ("setModAmount", {"amount": -0.5}),
        ]:
            command = {"v": 0, "id": "x", "type": command_type,
                       "connection": identity, **extra}
            self.assertTrue(validate(command, self.schema), command)
        # A newly created connection does have a meaningful modulation amount.
        self.assertFalse(validate(
            {"v": 0, "id": "x", "type": "connect", "connection": identity},
            self.schema,
        ))

    def test_unknown_fields_do_not_disable_known_field_validation(self):
        command = {"v": 0, "id": "x", "type": "loadGraph",
                   "patch": {"format": "wirescape.native.patch", "version": 2,
                             "modules": [{"id": 3, "module": "essentials.output",
                                          "new_field": {"data": [1, 2]}}],
                             "connections": [], "next_version_data": [1, 2, 3]}}
        self.assertTrue(validate(command, self.schema))
        bad = copy.deepcopy(command)
        bad["patch"]["modules"][0]["id"] = 0
        self.assertFalse(validate(bad, self.schema))

    def test_strict_ndjson_duplicate_and_bounds(self):
        valid = '{"v":0,"id":"one","type":"panic"}'
        self.assertEqual(parse_line(valid, self.schema)["type"], "panic")
        for raw in [
            '{"v":0,"v":0,"id":"one","type":"panic"}',
            '{"v":0,"id":"one","type":"panic","payload":{"x":1,"x":2}}',
            '{"v":0,"id":"one","type":"panic","bad":NaN}',
            '{"v":0,"id":"one","type":"panic"}' + " " * 2_097_152,
        ]:
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_line(raw, self.schema)

    def test_sidecar_live_corpus_instrumentation_anchors(self):
        source = SIDECAR.read_text(encoding="utf-8")
        # validate_sidecar.py inserts readers in memory; no existing test is edited.
        self.assertEqual(source.count(
            "self.messages.put(json.loads(line, object_pairs_hook=strict_object))"), 1)
        self.assertEqual(source.count(
            "command = dict(v=0, id=request_id, type=method, **payload)"), 1)
        self.assertIn("self.process.stdout", source)
        self.assertIn("def call(self, method, expected=True, **payload):", source)


if __name__ == "__main__":
    unittest.main()
