# SPDX-License-Identifier: GPL-3.0-only
"""Pure tests for device-free evidence classification and completeness."""
import json
import tempfile
import unittest
from pathlib import Path

from sidecar_probe import classify_reply
from verify_artifacts import validate


class ProtocolTests(unittest.TestCase):
    def test_ack_and_refusal(self):
        self.assertEqual(classify_reply({"ok": True, "gen": "1"}),
                         {"sidecar_result": "ack", "sidecar_generation": "1"})
        self.assertEqual(classify_reply({"ok": False, "gen": "0", "code": "refused",
                                         "message": "Cannot load patch"}),
                         {"sidecar_result": "refuse", "sidecar_generation": "0",
                          "sidecar_code": "refused", "sidecar_message": "Cannot load patch"})
        self.assertEqual(classify_reply({})["sidecar_result"], "unavailable")

    def test_verifier_requires_sidecar_reply(self):
        with tempfile.TemporaryDirectory() as folder:
            perf = Path(folder) / "perf"
            perf.mkdir()
            docs = {
                "module_cpu": [],
                "engine_cpu": [
                    {"block_frames": block, "status": "measured", "name": name}
                    for block in (64, 128, 256)
                    for name in ("abi2_mono", "abi2_poly8", "abi2_eight_mono",
                                 "abi2_modulated", "vcf_constant",
                                 "vcf_audio_rate_cutoff")],
                "probe_failures": [
                    {"module": "essentials.chord", "block_frames": 64, "channels": 1,
                     "sample_rate_hz": 48000, "instances": 1,
                     "input_mode": "normal", "stderr": "prepare failed"}],
                "soak_failures": [
                    {"patch": "sample.json", "block_frames": 64,
                     "error_text": "graph setup/render failed",
                     "sidecar_result": "refuse",
                     "sidecar_message": "Invalid graph"}],
                "denormal_spikes": [
                    {"block_frames": block, "status": "measured", "p99_ratio": 1.0}
                    for block in (64, 128, 256)],
            }
            for name, rows in docs.items():
                (perf / (name + ".json")).write_text(json.dumps({
                    "provenance": {"commit": "test-commit"}, "rows": rows}), encoding="utf-8")
                (perf / (name + ".md")).write_text("# " + name, encoding="utf-8")
            self.assertEqual(validate(folder)["measured_engine_benchmarks"], 18)
            # A seventh historic/unknown case must never be silently accepted.
            docs["engine_cpu"].append({"block_frames": 64, "status": "measured",
                                       "name": "abi1_mono"})
            (perf / "engine_cpu.json").write_text(json.dumps({
                "provenance": {"commit": "test-commit"},
                "rows": docs["engine_cpu"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact six"):
                validate(folder)
            docs["engine_cpu"].pop()
            (perf / "engine_cpu.json").write_text(json.dumps({
                "provenance": {"commit": "test-commit"},
                "rows": docs["engine_cpu"]}), encoding="utf-8")
            docs["soak_failures"][0]["sidecar_result"] = "unavailable"
            (perf / "soak_failures.json").write_text(
                json.dumps({"provenance": {"commit": "test-commit"},
                            "rows": docs["soak_failures"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "sidecar reply"):
                validate(folder)


if __name__ == "__main__":
    unittest.main()
