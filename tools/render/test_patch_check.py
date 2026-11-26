# SPDX-License-Identifier: GPL-3.0-only
"""OB-h6 integration contract. Run against the built native renderer; devices off."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "build/native/wirescape_render"
if sys.platform == "win32":
    RENDER = RENDER.with_suffix(".exe")
LIBRARY = ROOT / "tools/patch_library.py"
FIXTURE = ROOT / "tests/fixtures/patch_shapes/no-config.json"
RATE, BLOCK, SECONDS = 48000, 128, 1.25
FRAMES = 60000
COUNTERS = {"faults", "late_events", "dropped_events", "ring_full_events",
            "stale_events", "arena_full_events"}
TIMING = {"p50_us", "p99_us", "worst_us", "period_us", "overruns", "blocks"}
ROW_KEYS = {"patch", "load_ok", "reason", "nan_inf_samples", "peak", "rms",
            "silent", "timing"}


class PatchCheckTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(RENDER.is_file(), f"build actual renderer first: {RENDER}")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "patches"
        self.folder.mkdir()
        self.good = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.write("good.json", self.good)
        self.events = self.root / "events.json"
        self.events.write_text("[]", encoding="utf-8")

    def write(self, name, patch):
        (self.folder / name).write_text(json.dumps(patch), encoding="utf-8")

    def render(self, name, timing=False):
        wav = self.root / f"{name}.wav"
        args = [str(RENDER), "--patch", str(self.folder / "good.json"),
                "--script", str(self.events), "--out", str(wav),
                "--rate", str(RATE), "--block", str(BLOCK),
                "--seconds", str(SECONDS), "--seed", "42"]
        if timing:
            args += ["--timing"]
        run = subprocess.run(args, capture_output=True, timeout=90)
        self.assertEqual(run.returncode, 0, run.stderr.decode(errors="replace"))
        records = [line.removeprefix(b"render_metrics ") for line in run.stdout.splitlines()
                   if line.startswith(b"render_metrics ")]
        self.assertEqual(len(records), 1)
        return run.stdout, json.loads(records[0]), wav.read_bytes()

    def check(self):
        dest = self.root / "report.json"
        before = {p.name: p.read_bytes() for p in self.folder.glob("*.json")}
        run = subprocess.run([sys.executable, str(LIBRARY), "check", str(self.folder),
                              "--rate", str(RATE), "--block", str(BLOCK),
                              "--seconds", str(SECONDS), "--json", str(dest)],
                             capture_output=True, text=True, timeout=120)
        self.assertTrue(dest.is_file(), run.stdout + run.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.folder.glob("*.json")})
        doc = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(set(doc), {"schema_version", "rate", "block", "seconds", "patches"})
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual((doc["rate"], doc["block"], doc["seconds"]),
                         (RATE, BLOCK, SECONDS))
        for row in doc["patches"]:
            self.assertEqual(set(row), ROW_KEYS)
            self.assertIn(row["patch"], run.stdout)
        return run, {row["patch"]: row for row in doc["patches"]}

    def assert_timing(self, timing):
        self.assertTrue(TIMING.issubset(timing))
        self.assertEqual(timing["blocks"], math.ceil(FRAMES / BLOCK))
        self.assertAlmostEqual(timing["period_us"], BLOCK * 1e6 / RATE)
        self.assertLessEqual(0, timing["p50_us"])
        self.assertLessEqual(timing["p50_us"], timing["p99_us"])
        self.assertLessEqual(timing["p99_us"], timing["worst_us"])
        self.assertLessEqual(0, timing["overruns"])
        self.assertLessEqual(timing["overruns"], timing["blocks"])
        for key in ("p50_us", "p99_us", "worst_us", "period_us"):
            self.assertTrue(math.isfinite(timing[key]))

    def test_default_native_baseline_and_opt_in(self):
        out, metrics, wav = self.render("default")
        expected = {"faults": 0, "late_events": 0, "dropped_events": 0,
                    "ring_full_events": 0, "stale_events": 0, "arena_full_events": 0}
        self.assertEqual(metrics, expected)
        self.assertEqual(set(metrics), COUNTERS)
        self.assertEqual(len(wav), 44 + FRAMES * 8)
        self.assertEqual(wav[:4], b"RIFF")
        self.assertEqual(wav[36:40], b"data")
        self.assertEqual(self.render("repeat"), (out, metrics, wav))
        print("OB-h6 default stdout:", repr(out), flush=True)
        print("OB-h6 default WAV SHA256:", hashlib.sha256(wav).hexdigest(), flush=True)
        _, timed, timed_wav = self.render("timed", timing=True)
        self.assertEqual(set(timed), COUNTERS | {"timing"})
        self.assertEqual({k: timed[k] for k in COUNTERS}, metrics)
        self.assertEqual(timed_wav, wav)
        self.assert_timing(timed["timing"])

    def test_sounding_and_silent_exit_zero(self):
        silent = copy.deepcopy(self.good)
        silent["modules"] = [silent["modules"][0]]
        silent["connections"] = []
        self.write("silent.json", silent)
        run, rows = self.check()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(set(rows), {"good.json", "silent.json"})
        for row in rows.values():
            self.assertIs(row["load_ok"], True)
            self.assertIsNone(row["reason"])
            self.assertEqual(row["nan_inf_samples"], 0)
            self.assert_timing(row["timing"])
            for stat in ("p50", "p99", "worst"):
                self.assertAlmostEqual(row["timing"][stat + "_percent"],
                                       row["timing"][stat + "_us"] * 100 /
                                       row["timing"]["period_us"])
        self.assertIs(rows["good.json"]["silent"], False)
        self.assertGreater(rows["good.json"]["peak"], 0)
        self.assertGreater(rows["good.json"]["rms"], 0)
        self.assertIs(rows["silent.json"]["silent"], True)
        self.assertEqual(rows["silent.json"]["peak"], 0)
        self.assertEqual(rows["silent.json"]["rms"], 0)

    def test_refusal_does_not_stop_folder(self):
        bad = copy.deepcopy(self.good)
        bad["modules"][1]["module"] = "invalid.missing"
        self.write("bad.json", bad)
        run, rows = self.check()
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(set(rows), {"good.json", "bad.json"})
        self.assertIs(rows["good.json"]["load_ok"], True)
        self.assertIs(rows["bad.json"]["load_ok"], False)
        self.assertTrue(rows["bad.json"]["reason"])
        for key in ("nan_inf_samples", "peak", "rms", "silent", "timing"):
            self.assertIsNone(rows["bad.json"][key])

    def test_synthetic_pcm_nonfinite_accounting(self):
        # Synthetic PCM tests only the analyser, not a native NaN-producing patch.
        spec = importlib.util.spec_from_file_location("patch_library", LIBRARY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pcm = struct.pack("<8f", 0, 0, 0, 0, float("nan"), float("inf"), -1, 1)
        row = module.analyse_pcm(pcm, rate=2)
        self.assertEqual(row["nan_inf_samples"], 2)
        self.assertIs(row["silent"], False)
        self.assertEqual(row["peak"], 1)
        self.assertAlmostEqual(row["rms"], math.sqrt(2 / 6))


if __name__ == "__main__":
    unittest.main(verbosity=2)
