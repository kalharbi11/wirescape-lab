# SPDX-License-Identifier: GPL-3.0-only
"""OB-c A10 null-sink tests: panic drone, buffer restart, basics-04.

Run explicitly with a compiled native sidecar:
  WIRESCAPE_OB_C_SIDECAR=/.../wirescape_engine_sidecar python \
    native/tests2/ob_c_a10_capture_tests.py -v

NOT auto-discovered by Lab until lead authorizes additive CTest registration.
No xfails are guessed from absent hosted execution. Product-only failures name
the A10 oracle; setup, process, PCM parsing and missing dependencies fail normally.
"""
from __future__ import annotations

import copy
import math
import statistics
import tempfile
import unittest
from pathlib import Path

from ob_c_a10_capture import (CaptureClient, ROOT, RATE, channel,
                             drone, marker, read_marks, read_segments, sidecar_binary)

BASICS04 = ROOT / "apps/studio/patches/basics-04-sequencer-and-quantizer.json"


def load_json(path):
    import json
    return json.loads(path.read_text())


def nonzero(a: tuple[float, ...]) -> bool:
    return any(x != 0.0 for x in a)


class A10Capture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sidecar = sidecar_binary()  # Always an infrastructure error if absent.

    def _run(self, root: Path, name: str, patch: dict, events: list, *, pre=4, post=10):
        path = root / (name + ".f32")
        engine = CaptureClient(self.sidecar, path)
        engine.statuses(2)
        engine.call("loadGraph", patch=patch)
        engine.statuses(pre)
        for kind, payload, waits in events:
            engine.call(kind, **payload)
            engine.statuses(waits)
        engine.statuses(post)
        stderr = engine.close()
        seg = read_segments(path)
        marks = read_marks(path, seg)
        return seg, marks, stderr

    def test_panic_drone_bit_exact_and_contiguous_frames(self):
        """A10.1: no gate/note exists, so panic must leave VCO PCM bit-identical."""
        with tempfile.TemporaryDirectory(prefix="ob-c-panic-") as t:
            root = Path(t)
            graph = drone()
            # Identical-value param event is the no-panic timing/marks control.
            ref_segments, ref_marks, _ = self._run(root, "reference", graph,
                                                    [("setParam", {"moduleId": 1,
                                                                  "paramId": "frequency",
                                                                  "value": 220}, 7)])
            got_segments, got_marks, _ = self._run(root, "panic", graph,
                                                    [("panic", {}, 7)])
            self.assertEqual(len(ref_segments), 1, "INFRA: reference unexpectedly restarted")
            self.assertEqual(len(got_segments), 1, "PRODUCT_A10_PANIC: unexpected sink segment")
            control = channel(ref_segments[0])
            actual = channel(got_segments[0])
            self.assertTrue(nonzero(control) and nonzero(actual), "INFRA: drone not audible")
            # Anchor to the first active VCO sample, NOT a guessed wall-clock time.
            first_ref = next(i for i, v in enumerate(control) if v)
            first_actual = next(i for i, v in enumerate(actual) if v)
            before = 4096
            self.assertEqual(control[first_ref:first_ref + before],
                             actual[first_actual:first_actual + before],
                             "INFRA: the two before-panic deterministic drone traces differ")
            mark = marker(got_marks, "panic")
            # Capture file header+payload accounting proves every recorded block
            # is complete; bench summary separately demands overruns=0.
            start = max(0, mark["b1"] * got_segments[0]["block"] - first_actual)
            span = 4096
            self.assertGreater(len(actual) - first_actual - start, span)
            self.assertGreater(len(control) - first_ref - start, span)
            self.assertEqual(control[first_ref + start:first_ref + start + span],
                             actual[first_actual + start:first_actual + start + span],
                             "PRODUCT_A10_PANIC: panic changed gate-free drone PCM or frame continuity")
            self.assertEqual(len(ref_marks), 2)
            self.assertEqual(len(got_marks), 2)

    def test_buffer_new_segment_audible_past_reported_latency_and_five_repeat_facts(self):
        """A10.2: no owner 546-ms threshold; five measured block intervals only."""
        with tempfile.TemporaryDirectory(prefix="ob-c-buffer-") as t:
            root = Path(t)
            spans = []
            samples = []
            for k in range(5):
                # Fresh process and settings per repeat prevent persistent changes.
                segs, marks, _ = self._run(root, f"buffer-{k}", drone(),
                                            [("setBufferFrames", {"frames": 256}, 6)],
                                            pre=4, post=6)
                self.assertGreaterEqual(len(segs), 2, "PRODUCT_A10_BUFFER: no new sink segment")
                self.assertEqual(segs[0]["block"], 128)
                self.assertEqual(segs[-1]["block"], 256)
                m = marker(marks, "setBufferFrames")
                # Marks are counts of *appended blocks*, never wall-clock time.
                spans.append(m["b1"] - m["b0"])
                rows = channel(segs[-1])
                self.assertTrue(all(math.isfinite(v) for v in rows))
                # Production audio_status latencyMs is 2 * block / sample rate;
                # new segment must produce nonzero within that actual reported
                # latency, not an arbitrary hardware 546-ms budget.
                latency_frames = 2 * segs[-1]["block"]
                samples.append(next((i for i, v in enumerate(rows[:latency_frames]) if v != 0), None))
            facts = {"architecture": __import__("platform").machine(),
                     "rate": RATE, "new_block": 256, "repeats": 5,
                     "mark_interval_blocks": spans,
                     "median_blocks": statistics.median(spans),
                     "max_blocks": max(spans),
                     "wall_clock_stop_to_first_frame_ms": None,
                     "note": "R7 b0/b1 block counts cannot time a stopped sink; do not label block count as wall latency"}
            print("OB-C-A10-BUFFER-FACT " + __import__("json").dumps(facts, sort_keys=True))
            self.assertTrue(all(x is not None for x in samples),
                            "PRODUCT_A10_BUFFER: first new block remains silent past reported latency")
            self.assertEqual(len(samples), 5)

    def test_basics04_gate_step_peaks_60db_and_all_finite(self):
        """A10.3: exact bundled patch + attack 0.001/0.005 x original/max VCA."""
        source = load_json(BASICS04)
        seq = next(m for m in source["modules"] if m["id"] == 2)
        gates = [int(seq["parameters"][f"gate{i}"]) for i in range(1, 9)]
        self.assertEqual(gates, [1, 1, 1, 1, 1, 1, 1, 0])
        beat_hz = next(m for m in source["modules"] if m["id"] == 1)["parameters"]["bpm"] / 60
        ticks_per_beat = next(m for m in source["modules"] if m["id"] == 1)["parameters"]["ticks_per_beat"]
        step_frames = RATE / (beat_hz * ticks_per_beat)
        gain_values = [next(m for m in source["modules"] if m["id"] == 7)["parameters"]["gain"], 2.0]
        variants = [("bundled", None, None)] + [
            (f"attack{a}-gain{g}", a, g)
            for a in (0.001, 0.005) for g in gain_values]
        with tempfile.TemporaryDirectory(prefix="ob-c-basics-") as t:
            for name, attack, gain in variants:
                patch = copy.deepcopy(source)
                if attack is not None:
                    next(m for m in patch["modules"] if m["id"] == 8)["parameters"]["attack"] = attack
                    next(m for m in patch["modules"] if m["id"] == 7)["parameters"]["gain"] = gain
                segs, marks, _ = self._run(Path(t), name, patch, [],
                                             pre=18, post=10)
                self.assertEqual(len(segs), 1, "INFRA: bundled graph unexpectedly restarted")
                pcm = channel(segs[0])
                self.assertTrue(all(math.isfinite(v) for v in pcm),
                                f"PRODUCT_A10_BASICS04: nonfinite PCM in {name}")
                origin = marker(marks, "loadGraph")["b1"] * segs[0]["block"]
                # Skip first gate to avoid conflating loadGraph start/ramp with
                # an actual repeated sequencer gate; cover all later gate-on
                # steps over two complete 8-step cycles.
                step_peaks = []
                for step in range(1, 16):
                    if not gates[step % 8]:
                        continue
                    first = int(origin + (step + .1) * step_frames)
                    last = int(origin + (step + .9) * step_frames)
                    self.assertGreater(len(pcm), last, "INFRA: capture too short for all gate steps")
                    step_peaks.append(max(abs(v) for v in pcm[first:last]))
                self.assertGreater(len(step_peaks), 8)
                reference = statistics.median(step_peaks)
                self.assertGreater(reference, 0, f"PRODUCT_A10_BASICS04: silent median gate peak in {name}")
                self.assertTrue(all(peak >= reference * 10**(-60/20) for peak in step_peaks),
                                f"PRODUCT_A10_BASICS04: gate-on peak more than 60 dB below median in {name}: {step_peaks}")


if __name__ == "__main__":
    unittest.main()
