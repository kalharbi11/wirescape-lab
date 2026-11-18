# SPDX-License-Identifier: GPL-3.0-only
"""A10 OB-c actual click oracles on real native AppEngine PCM.

The native C++ fixture schedules scene07 panic at two EXACT sample frames and
replays actual Studio pointermove->setParam event timestamps. This script
imports bench/offline/metrics.click_events UNMODIFIED. Source only pending
lead-authorized CTest target and Studio trace artifact handoff.

Invocation after native build + trace:
  WIRESCAPE_OB_C_AUDIO_RUNNER=/.../ob_c_a10_audio_runner \
  WIRESCAPE_OB_C_STUDIO_TRACE=/.../ob-c-a10-studio-setparam-cadence.json \
  python native/tests2/ob_c_a10_click_tests.py -v

No xfail or pass result is guessed. A setup/compile/decoder/trace failure
must fail normally; only a proven detector inequality is a product defect.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bench" / "offline"))
from metrics import click_events  # noqa: E402 -- production detector unchanged
import numpy as np  # noqa: E402

RATE = 48000
SCENE = ROOT / "apps" / "studio" / "patches" / "scene-07-witching-hour.json"
MID_NOTE = 8192
BETWEEN_NOTES = 275200
ECHO_START = 96000


def required_binary() -> Path:
    value = os.environ.get("WIRESCAPE_OB_C_AUDIO_RUNNER")
    if not value or not Path(value).is_file():
        raise FileNotFoundError("INFRA_A10_CLICKS: real ob_c_a10_audio_runner target missing")
    return Path(value).resolve()


def run_fixture(which: str, source: Path, target: Path):
    proc = subprocess.run([str(required_binary()), which, str(source), str(target)],
                          capture_output=True, text=True, timeout=180, check=False)
    if proc.returncode:
        raise RuntimeError(f"INFRA_A10_CLICKS: native fixture failed: "
                           f"status={proc.returncode} stdout={proc.stdout} stderr={proc.stderr}")
    return proc.stdout


def pcm(path: Path) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(f"INFRA_A10_CLICKS: missing raw PCM {path}")
    raw = np.fromfile(path, dtype="<f4")
    if len(raw) % 2 or len(raw) < RATE:
        raise ValueError(f"INFRA_A10_CLICKS: wrong stereo PCM length {path}")
    data = raw.reshape(-1, 2)
    if not np.isfinite(data).all():
        raise ValueError(f"PRODUCT_A10_CLICKS: nonfinite samples in {path.name}")
    return data


def after_clicks(data: np.ndarray, start: int, duration_ms: int) -> list[dict]:
    """500ms/gesture window with detector's unchanged ±25-ms guard present."""
    guard = int(.05 * RATE)  # 50ms surrounding context, NOT an altered click oracle
    end = start + round(duration_ms * RATE / 1000)
    if start < guard or end + guard > len(data):
        raise RuntimeError("INFRA_A10_CLICKS: source capture too short for click window")
    excerpt = data[start - guard:end + guard]
    events = click_events(excerpt, RATE)
    lo, hi = guard / RATE, guard / RATE + duration_ms / 1000
    return [e for e in events if lo <= e["time_s"] < hi]


class A10Clicks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = required_binary()

    def test_scene07_two_exact_frame_panics_vs_no_panic_reference(self):
        """A10.4: original bundled scene07, exact mid-note/between-note frames."""
        with tempfile.TemporaryDirectory(prefix="ob-c-scene-") as td:
            dest = Path(td)
            detail = run_fixture("scene", SCENE, dest)
            self.assertIn(f"exact_panic_frames={MID_NOTE},{BETWEEN_NOTES}", detail,
                          "INFRA: no fixed-frame native panic evidence")
            reference = pcm(dest / "scene-reference.f32le")
            for name, start in (("mid-note", MID_NOTE), ("between-notes", BETWEEN_NOTES)):
                actual = pcm(dest / f"scene-{name}.f32le")
                self.assertEqual(reference.shape, actual.shape, "INFRA: reference frame count mismatch")
                self.assertTrue(np.array_equal(reference[:start], actual[:start]),
                                f"INFRA: {name} stimulus did not match before fixed panic frame")
                real = after_clicks(actual, start, 500)
                baseline = after_clicks(reference, start, 500)
                print("OB-C-A10-SCENE-CLICK-FACT " + json.dumps({
                    "phase": name, "panic_frame": start, "rate": RATE, "post_panic_ms": 500,
                    "click_events": len(real), "reference_click_events": len(baseline),
                    "detector": "unchanged bench/offline/metrics.py:38-89"}, sort_keys=True))
                self.assertLessEqual(len(real), len(baseline),
                                     f"PRODUCT_A10_SCENE07: {name} panic added clicks in 500ms")

    def test_echo_actual_studio_cadence_sweeps_vs_no_gesture(self):
        """A10.5: each knob 100ms and 1s, real Studio trace, unchanged detector."""
        trace = os.environ.get("WIRESCAPE_OB_C_STUDIO_TRACE")
        if not trace or not Path(trace).is_file():
            raise FileNotFoundError(
                "INFRA_A10_ECHO: actual Studio Playwright cadence JSON is required; "
                "a guessed 60Hz rate is forbidden")
        data = json.loads(Path(trace).read_text())
        if data.get("real_sidecar_or_audio") is not False or len(data.get("gestures", [])) != 8:
            raise ValueError("INFRA_A10_ECHO: invalid eight-gesture real Studio trace")
        with tempfile.TemporaryDirectory(prefix="ob-c-echo-") as td:
            dest = Path(td)
            detail = run_fixture("echo", Path(trace), dest)
            self.assertEqual(detail.count("OB-C-A10-ECHO knob="), 8)
            for g in data["gestures"]:
                knob = g["knob"]
                duration = g["duration_nominal_ms"]
                self.assertIn(knob, ("time", "feedback", "tone", "mix"))
                self.assertIn(duration, (100, 1000))
                tag = f"{knob}-{duration}"
                reference = pcm(dest / f"echo-reference-{tag}.f32le")
                actual = pcm(dest / f"echo-sweep-{tag}.f32le")
                self.assertEqual(reference.shape, actual.shape)
                self.assertTrue(np.array_equal(reference[:ECHO_START], actual[:ECHO_START]),
                                f"INFRA_A10_ECHO: baseline drift before {tag}")
                real = after_clicks(actual, ECHO_START, duration)
                baseline = after_clicks(reference, ECHO_START, duration)
                print("OB-C-A10-ECHO-CLICK-FACT " + json.dumps({
                    "knob": knob, "duration_ms": duration,
                    "actual_studio_setparam_events": len(g["events"]),
                    "click_events": len(real), "reference_click_events": len(baseline),
                    "detector": "unchanged bench/offline/metrics.py:38-89"}, sort_keys=True))
                self.assertLessEqual(len(real), len(baseline),
                                     f"PRODUCT_A10_ECHO: {tag} gesture added click_events")
            print("OB-C-A10-ECHO-RECORD-ONLY " + json.dumps(
                data["mode_division_record_only"], sort_keys=True))


if __name__ == "__main__":
    unittest.main()
