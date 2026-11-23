# SPDX-License-Identifier: GPL-3.0-only
"""Unwired contract corpus and preservation tests; devices/network not opened here."""
from __future__ import annotations

import copy
import json
import re
import unittest

from generate import PRINTABLE_ASCII_PATTERN, validate_schema_patterns
from validate import ROOT, check_schema_subset, json_equal, parse_line, read_schema, validate


SPEC = ROOT / "docs" / "specs" / "ENGINE_PROTOCOL.md"
SIDECAR = ROOT / "host" / "sidecar" / "protocol_tests.py"


class ProtocolV0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read_schema()

    def test_schema_uses_restricted_keywords(self):
        check_schema_subset(self.schema)
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(self.schema["$defs"]["command"]["oneOf"]), 21)
        self.assertEqual(self.schema["$defs"]["requestId"], {
            "type": "string", "minLength": 1, "maxLength": 64,
            "pattern": PRINTABLE_ASCII_PATTERN,
        })
        validate_schema_patterns(self.schema)

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

    def test_q13_bus_channel_boundaries_and_applygraph_corpus(self):
        cases = json.loads((ROOT / "tools/protocol/bus_channel_cases.json").read_text(encoding="utf-8"))
        self.assertEqual([case["value"] for case in cases], [0, 15, 16, 63, -1, 1.5])
        self.assertEqual([case["valid"] for case in cases], [True, True, False, False, False, False])
        for case in cases:
            with self.subTest(case=case["name"]):
                patch = {"format": "wirescape.native.patch", "version": 2,
                         "modules": [{"id": 7, "module": "essentials.output"}],
                         "connections": [], "future": {"preserve": [1, None, True]},
                         "outputs": [{"module": 7, "port": "audio",
                                      "bus_channel": case["value"]}]}
                untouched = copy.deepcopy(patch)
                for method in ("loadGraph", "applyGraph"):
                    wire = {"v": 0, "id": "q13", "type": method, "patch": patch}
                    self.assertIs(validate(wire, self.schema), case["valid"])
                self.assertEqual(patch, untouched)

    def test_applygraph_reply_result_and_hello_capability(self):
        patch = {"format": "wirescape.native.patch", "version": 2,
                 "modules": [], "connections": [], "future": {"retained": True}}
        self.assertTrue(validate({"v": 0, "id": "apply", "type": "applyGraph",
                                  "patch": patch}, self.schema))
        self.assertFalse(validate({"v": 0, "id": "apply", "type": "applyGraph"}, self.schema))
        shape = {"$defs": self.schema["$defs"], "$ref": "#/$defs/applyGraphResult"}
        result = {"path": "live", "replaced": [], "unapplied": [], "future": {"kept": 1}}
        self.assertTrue(validate(result, shape))
        self.assertTrue(validate({"v": 0, "re": "apply", "ok": True, "gen": "1",
                                  "result": result}, self.schema))
        for bad in ({"path": "unknown", "replaced": [], "unapplied": []},
                    {"path": "live", "replaced": []},
                    {"path": "live", "replaced": ["7"], "unapplied": []},
                    {"path": "restart", "replaced": [], "unapplied": [{"moduleId": 7}]}):
            self.assertFalse(validate(bad, shape), bad)
        self.assertFalse(validate({"v": 0, "re": "apply", "ok": True, "gen": "1",
                                   "result": {"path": "unknown"}}, self.schema))
        self.assertIn("applyGraph", [variant["properties"]["type"]["const"]
                      for variant in self.schema["$defs"]["command"]["oneOf"]])
        self.assertTrue(validate({"v": 0, "type": "hello", "session": "s1", "protocol": 0,
                                  "engine": {"version": "1", "sha": "a"},
                                  "capabilities": ["applyGraph"],
                                  "catalogue": {"modules": []},
                                  "audio": {"state": "no-device", "sampleRate": 48000,
                                            "bufferFrames": 256, "latencyMs": 0,
                                            "cpuPercent": 0, "dropouts": 0,
                                            "deviceId": None, "deviceName": None},
                                  "midi": {"devices": [], "activity": {}}}, self.schema))

    def test_optional_scripted_midi_counters_and_generated_drift(self):
        # Default S0 MIDI remains valid with no new transport member.
        default = {"devices": [], "activity": {}}
        shape = {"$defs": self.schema["$defs"], "$ref": "#/$defs/midi"}
        self.assertTrue(validate(default, shape))
        counts = {"received": 50, "dropped": 0, "malformed": 0,
                  "oversize": 0, "ring_full": 0, "disconnects": 0,
                  "send_fail": 0, "ignored_rpn": 0, "release_panics": 2,
                  "ports": [{"name": "Scripted MIDI", "system_name": "scripted:midi-m8:0",
                             "received": 50, "online": True}]}
        self.assertTrue(validate({**default, "counters": counts}, shape))
        for invalid in (
            {**counts, "release_panics": -1},
            {**counts, "release_panics": True},
            {**counts, "ports": [{"name": "missing-required"}]},
            {k: v for k, v in counts.items() if k != "send_fail"},
        ):
            self.assertFalse(validate({**default, "counters": invalid}, shape))
        # SR17: source-schema and both generated validator/TS outputs must match.
        from generate import OUTPUTS, render
        for key, rendered in render().items():
            with self.subTest(generated=key):
                self.assertEqual(rendered, OUTPUTS[key].read_text(encoding="utf-8"))

    def test_json_semantic_equality_for_const_and_enum(self):
        # Python bool is a subclass of int; JSON does not equate them.
        self.assertFalse(json_equal(False, 0))
        self.assertFalse(json_equal(True, 1))
        self.assertFalse(json_equal({"nested": [1, False]}, {"nested": [1, 0]}))
        self.assertTrue(json_equal(1, 1.0))
        self.assertTrue(json_equal({"b": True, "a": [1.0]}, {"a": [1], "b": True}))
        self.assertFalse(validate({"v": False, "id": "x", "type": "panic"}, self.schema))
        self.assertFalse(validate({"v": 0, "re": "x", "ok": 1, "gen": "0"}, self.schema))
        self.assertTrue(validate({"v": 0, "re": "x", "ok": True, "gen": "0"}, self.schema))
        custom = {"$defs": {}, "enum": [0, 1]}
        self.assertFalse(validate(False, custom))
        self.assertFalse(validate(True, custom))
        self.assertTrue(validate(1.0, custom))

    def test_non_ascii_length_counts_codepoints_for_other_strings(self):
        generic_string = {"type": "string", "minLength": 1, "maxLength": 64}
        for scalar in ("é", "🙂"):
            self.assertTrue(validate(scalar * 33, generic_string))
            self.assertTrue(validate(scalar * 64, generic_string))
            self.assertFalse(validate(scalar * 65, generic_string))
        self.assertTrue(validate("a" * 64, generic_string))
        self.assertFalse(validate("a" * 65, generic_string))

    def test_q8_printable_ascii_request_id_corpus(self):
        cases = json.loads((ROOT / "tools/protocol/request_id_cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 10)
        for case in cases:
            with self.subTest(case=case["name"]):
                cmd = {"v": 0, "id": case["id"], "type": "panic"}
                self.assertIs(validate(cmd, self.schema), case["valid"])
                raw = json.dumps(cmd, ensure_ascii=False)
                if case["valid"]:
                    self.assertEqual(parse_line(raw, self.schema), cmd)
                else:
                    with self.assertRaises(ValueError):
                        parse_line(raw, self.schema)

    def test_generator_rejects_every_other_pattern_value(self):
        bad = copy.deepcopy(self.schema)
        bad["$defs"]["requestId"]["pattern"] = "^.*$"
        with self.assertRaisesRegex(ValueError, "Unsupported protocol schema pattern"):
            validate_schema_patterns(bad)
        bad = copy.deepcopy(self.schema)
        bad["$defs"]["requestId"]["pattern"] = PRINTABLE_ASCII_PATTERN + " "
        with self.assertRaisesRegex(ValueError, "Unsupported protocol schema pattern"):
            validate_schema_patterns(bad)
        bad = copy.deepcopy(self.schema)
        bad["$defs"]["requestId"]["type"] = "number"
        with self.assertRaisesRegex(ValueError, "Unsupported protocol schema pattern"):
            validate_schema_patterns(bad)

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
