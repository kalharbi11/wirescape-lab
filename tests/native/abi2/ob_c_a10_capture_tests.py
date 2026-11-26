# SPDX-License-Identifier: GPL-3.0-only
"""OB-c A10 null-sink tests: panic drone, buffer restart, basics-04.

Run explicitly with a compiled native sidecar:
  WIRESCAPE_OB_C_SIDECAR=/.../wirescape_engine_sidecar python \
    tests/native/abi2/ob_c_a10_capture_tests.py -v

NOT auto-discovered by Lab until lead authorizes additive CTest registration.
No xfails are guessed from absent hosted execution. Product-only failures name
the A10 oracle; setup, process, PCM parsing and missing dependencies fail normally.
"""
from __future__ import annotations

import copy
import json
import math
import os
import re
from contextlib import nullcontext
import statistics
import struct
import tempfile
import unittest
from pathlib import Path

from ob_c_a10_capture import (CaptureClient, ROOT, RATE, CHANNELS, channel,
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

    def _run(self, root: Path, name: str, patch: dict, events: list, *, pre=4, post=10, retain_stderr=False, audio_status=None):
        path = root / (name + ".f32")
        engine = CaptureClient(self.sidecar, path)
        if audio_status is not None:
            audio_status.update(engine.hello["audio"])
        engine.statuses(2)
        engine.call("loadGraph", patch=patch)
        engine.statuses(pre)
        for kind, payload, waits in events:
            engine.call(kind, **payload)
            engine.statuses(waits)
        engine.statuses(post)
        stderr = engine.close()
        if retain_stderr:
            path.with_suffix('.stderr.txt').write_text(stderr, encoding='utf-8')
        seg = read_segments(path)
        marks = read_marks(path, seg)
        return seg, marks, stderr

    def test_panic_drone_gap_and_contiguous_frames(self):
        """OB r2.8a P1: allow the required phase reset, gate the audio gap."""
        # Keep the original captures in the hosted artifact even on a red oracle.
        evidence = os.environ.get("WIRESCAPE_OB_C_PANIC_EVIDENCE")
        if evidence:
            Path(evidence).mkdir(parents=True, exist_ok=False)
        with (nullcontext(evidence) if evidence else
              tempfile.TemporaryDirectory(prefix="ob-c-panic-")) as t:
            root = Path(t)
            graph = drone()
            # Identical-value param event is the no-panic timing/marks control.
            ref_segments, ref_marks, ref_stderr = self._run(root, "reference", graph,
                                                    [("setParam", {"moduleId": 1,
                                                                  "paramId": "frequency",
                                                                  "value": 220}, 7)], retain_stderr=True)
            audio = {}
            got_segments, got_marks, got_stderr = self._run(root, "panic", graph,
                                                    [("panic", {}, 7)], retain_stderr=True,
                                                    audio_status=audio)
            self.assertEqual(len(ref_segments), 1, "INFRA: reference unexpectedly restarted")
            self.assertEqual(len(got_segments), 1, "PRODUCT_A10_PANIC: unexpected sink segment")
            control = channel(ref_segments[0])
            actual = channel(got_segments[0])
            self.assertTrue(nonzero(control) and nonzero(actual), "INFRA: drone not audible")
            # Full aligned identity is retained as a diagnostic only (A45).
            first_ref = next(i for i, v in enumerate(control) if v)
            first_actual = next(i for i, v in enumerate(actual) if v)
            span = min(len(control) - first_ref, len(actual) - first_actual)
            self.assertGreater(span, RATE * 2,
                               "INFRA: insufficient full drone capture for a frame oracle")
            mark = marker(got_marks, "panic")
            before_mark = mark["b0"] * got_segments[0]["block"] - first_actual
            after_mark = mark["b1"] * got_segments[0]["block"] - first_actual
            self.assertTrue(0 < before_mark <= after_mark < span - RATE,
                            "INFRA: panic mark outside full active comparison window")
            # P1 identity diagnostics and the revised gap oracle.
            block = got_segments[0]["block"]
            lo, hi = mark["b0"] * block, (mark["b1"] + 1) * block
            mismatches = {}
            first_diff = None
            for d in range(span):
                if control[first_ref + d] != actual[first_actual + d]:
                    if first_diff is None:
                        first_diff = d
                    b = (first_actual + d) // block
                    mismatches[b] = mismatches.get(b, 0) + 1
            frame = None if first_diff is None else first_actual + first_diff
            location = ("identical" if frame is None else
                        "before" if frame < lo else "after" if frame >= hi else "inside")
            ref_bytes = ref_segments[0]["bytes"].cast("I")[
                first_ref * CHANNELS:(first_ref + span) * CHANNELS:CHANNELS].tobytes()
            got_bytes = got_segments[0]["bytes"].cast("I")[
                first_actual * CHANNELS:(first_actual + span) * CHANNELS:CHANNELS].tobytes()
            # Cross-check the sink's appended blocks with the separately
            # counted completed render timings and the exact file payload.
            def accounting(stderr, segment):
                capture = re.search(r"capture segments=(\d+) blocks=(\d+) failed=(\d+)", stderr)
                bench = re.search(r"bench blocks=(\d+).*?overruns=(\d+) faults=(\d+)", stderr)
                self.assertIsNotNone(capture, "INFRA: missing capture summary")
                self.assertIsNotNone(bench, "INFRA: missing render summary")
                segments, appended, failed = map(int, capture.groups())
                rendered, overruns, faults = map(int, bench.groups())
                return {"segments": segments, "appended_blocks": appended,
                        "rendered_blocks": rendered, "file_blocks": segment["blocks"],
                        "file_frames": segment["frames"], "capture_failed": failed,
                        "overruns": overruns, "faults": faults,
                        "counts_match": appended == rendered == segment["blocks"]}

            ref_accounting = accounting(ref_stderr, ref_segments[0])
            got_accounting = accounting(got_stderr, got_segments[0])
            self.assertEqual(audio["sampleRate"], RATE)
            self.assertEqual(audio["bufferFrames"], block)
            latency_ms = audio["latencyMs"]
            self.assertTrue(math.isfinite(latency_ms) and latency_ms >= 0)
            latency_frames = math.ceil(latency_ms * RATE / 1000)
            # The mark brackets the command by appended blocks; the reset can
            # occur at either endpoint. Use the latest possible boundary for
            # the deadline, not the first PCM difference (which is diagnostic).
            deadline = mark["b1"] * block + latency_frames
            first_required_block = (deadline + block - 1) // block
            silent_blocks = [b for b in range(first_required_block, got_segments[0]["blocks"])
                             if not nonzero(actual[b * block:(b + 1) * block])]
            # Preserve the existing pre-reset check. A52 replaces the
            # post-reset landmark comparison with exact sample identity.
            def landmarks(samples):
                return [(v > 0, v < 0, w > v, w < v)
                        for v, w in zip(samples, samples[1:])]

            pre = landmarks(actual[first_actual:lo])
            pre_ok = pre == landmarks(control[first_ref:first_ref + lo - first_actual])
            # The first nonzero sample follows the VCO's phase-zero sample.
            # Search only the contracted block-boundary reset origins and
            # compare from each candidate through the entire captured tail.
            # Do not trim a mismatch or select an origin from the PCM itself.
            reference_origin = first_ref - 1
            self.assertGreaterEqual(reference_origin, 0)
            self.assertEqual(control[reference_origin], 0.0,
                             "INFRA: reference has no phase-zero origin")
            matching_origins = []
            origin_reports = []
            for origin in range(lo, deadline + 1, block):
                count = len(actual) - origin
                self.assertGreater(count, 0, "INFRA: reset origin outside capture")
                self.assertLessEqual(reference_origin + count, len(control),
                                     "INFRA: reference too short for full post-reset comparison")
                mismatch = next((i for i in range(count)
                                 if actual[origin + i] != control[reference_origin + i]), None)
                origin_reports.append({
                    "origin_capture_frame": origin,
                    "reference_origin_frame": reference_origin,
                    "required_samples": count,
                    "first_mismatch_index": mismatch,
                    "first_mismatch_capture_frame": None if mismatch is None else origin + mismatch,
                    "first_mismatch_reference_frame": None if mismatch is None else reference_origin + mismatch,
                    "reference_value": None if mismatch is None else control[reference_origin + mismatch],
                    "panic_value": None if mismatch is None else actual[origin + mismatch],
                })
                if mismatch is None:
                    matching_origins.append(origin)
            # A52 strict-xfail cause diagnostic only: loadGraph uses a
            # 10 ms master fade (AppEngine::master_step and render_live),
            # while panic only resets processors at unity master gain.
            # Reproduce float32 addition/multiplication exactly and require
            # equality through the ENTIRE candidate tail. No corrected PCM
            # is used for the raw A52 assertion.
            def f32(value):
                return struct.unpack("<f", struct.pack("<f", value))[0]

            step = f32(1.0 / max(1, math.floor(RATE * 0.01)))
            fade_origins = []
            fade_reports = []
            for candidate in origin_reports:
                origin = candidate["origin_capture_frame"]
                count = candidate["required_samples"]
                gain = 0.0
                first_unexplained = None
                for i in range(count):
                    gain = min(1.0, f32(gain + step))
                    predicted = f32(actual[origin + i] * gain)
                    if predicted != control[reference_origin + i]:
                        first_unexplained = i
                        break
                fade_reports.append({
                    "origin_capture_frame": origin,
                    "first_unexplained_index": first_unexplained,
                    "required_samples": count,
                })
                if first_unexplained is None:
                    fade_origins.append(origin)
            # Independently check adjacent repeated complete audible blocks.
            # Capture format still does not expose absolute engine frame IDs.
            repeated_blocks = [b for b in range(first_required_block + 1, got_segments[0]["blocks"])
                               if actual[(b - 1) * block:b * block] == actual[b * block:(b + 1) * block]]
            report = {
                "aligned_first_reference_frame": first_ref,
                "aligned_first_panic_frame": first_actual,
                "compared_every_frame": span,
                "first_differing_relative_sample": first_diff,
                "first_differing_capture_frame": frame,
                "first_differing_capture_block": None if frame is None else frame // block,
                "first_reference_value": None if first_diff is None else control[first_ref + first_diff],
                "first_panic_value": None if first_diff is None else actual[frame],
                "panic_mark": mark,
                "panic_bracket_capture_frames_half_open": [lo, hi],
                "first_difference_vs_bracket": location,
                "reference_complete_blocks": ref_segments[0]["blocks"],
                "panic_complete_blocks": got_segments[0]["blocks"],
                "reference_block_frames": ref_segments[0]["block"],
                "panic_block_frames": block,
                "reference_frames": ref_segments[0]["frames"],
                "panic_frames": got_segments[0]["frames"],
                "reference_marks": ref_marks,
                "panic_marks": got_marks,
                "compared_capture_block_range_inclusive": [
                    first_actual // block, (first_actual + span - 1) // block],
                "mismatched_samples_by_panic_capture_block": mismatches,
                "numeric_equal_outside_listed_blocks": True,
                "numeric_equal_full_aligned_overlap": first_diff is None,
                "byte_equal_full_aligned_channel_zero": ref_bytes == got_bytes,
                "overruns": got_accounting["overruns"],
                "reference_accounting": ref_accounting,
                "panic_accounting": got_accounting,
                "reported_latency_ms": latency_ms,
                "reported_latency_frames": latency_frames,
                "first_required_audible_block": first_required_block,
                "silent_blocks_past_latency": silent_blocks,
                "repeated_adjacent_blocks_past_latency": repeated_blocks,
                "pre_reset_phase_landmarks_match": pre_ok,
                "post_reset_matching_phase_origins": matching_origins,
                "post_reset_sample_identity_by_origin": origin_reports,
                "startup_master_fade_cause_by_origin": fade_reports,
                "startup_master_fade_matching_origins": fade_origins,
                "independent_absolute_engine_frame_ids_available": False,
            }
            (root / "panic-report.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print("OB-C-A10-P1 " + json.dumps(report, sort_keys=True), flush=True)
            for counts in (ref_accounting, got_accounting):
                self.assertTrue(counts["counts_match"],
                                "PRODUCT_A10_PANIC: missing/repeated capture blocks versus render count")
                self.assertEqual(counts["segments"], 1)
                self.assertEqual(counts["capture_failed"], 0)
                self.assertEqual(counts["overruns"], 0, "PRODUCT_A10_PANIC: overrun")
                self.assertEqual(counts["faults"], 0, "PRODUCT_A10_PANIC: render fault")
            self.assertTrue(all(math.isfinite(v) for v in control + actual),
                            "PRODUCT_A10_PANIC: nonfinite drone PCM")
            self.assertLess(first_required_block, got_segments[0]["blocks"],
                            "INFRA: capture ends before reported latency")
            self.assertFalse(silent_blocks, "PRODUCT_A10_PANIC: silent block past reported latency")
            self.assertFalse(repeated_blocks, "PRODUCT_A10_PANIC: repeated audible block")
            self.assertTrue(pre_ok, "PRODUCT_A10_PANIC: discontinuous pre-reset drone phase progression")
            self.assertEqual(len(ref_marks), 2)
            self.assertEqual(len(got_marks), 2)
            # A52: only this exact raw-identity assertion is expected to
            # fail, and only with the independently demonstrated fade cause.
            # XPASS and an unexplained mismatch fail the suite; no setup,
            # other gap assertion or unrelated test can be swallowed.
            try:
                self.assertTrue(matching_origins,
                                "PRODUCT_A10_PANIC: no sample-identical block-boundary reset origin; "
                                + json.dumps(origin_reports, sort_keys=True))
            except AssertionError:
                if not fade_origins:
                    raise
                print("OB-C-A10-STRICT-XFAIL P1_STARTUP_MASTER_FADE_VS_UNITY_PANIC "
                      + json.dumps(origin_reports, sort_keys=True), flush=True)
            else:
                self.fail("STRICT_XPASS P1_STARTUP_MASTER_FADE_VS_UNITY_PANIC: remove expected failure")
            print("OB-C-A10-PANIC-FULL-FRAME-FACT " + json.dumps({
                "architecture": __import__("platform").machine(),
                "aligned_first_reference_frame": first_ref,
                "aligned_first_panic_frame": first_actual,
                "compared_every_frame": span,
                "panic_mark_blocks": [mark["b0"], mark["b1"]],
                "capture_complete_blocks_reference": ref_segments[0]["blocks"],
                "capture_complete_blocks_panic": got_segments[0]["blocks"],
                "pcm_bit_identical_full_aligned_overlap": ref_bytes == got_bytes,
                "overruns": got_accounting["overruns"],
                "unsupported_independent_absolute_frame_ids": True
            }, sort_keys=True))

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
                                             pre=48, post=24)
                self.assertEqual(len(segs), 1, "INFRA: bundled graph unexpectedly restarted")
                pcm = channel(segs[0])
                self.assertTrue(all(math.isfinite(v) for v in pcm),
                                f"PRODUCT_A10_BASICS04: nonfinite PCM in {name}")
                origin = marker(marks, "loadGraph")["b1"] * segs[0]["block"]
                # A10 explicitly requires EVERY enabled gate, including
                # startup step 0 and first step of the second cycle (step 8).
                # Never hide startup gates as a warm-up exemption.
                step_peaks = []
                step_indices = []
                for step in range(0, 16):
                    if not gates[step % 8]:
                        continue
                    first = int(origin + (step + .1) * step_frames)
                    last = int(origin + (step + .9) * step_frames)
                    self.assertGreater(len(pcm), last, "INFRA: capture too short for all gate steps")
                    step_peaks.append(max(abs(v) for v in pcm[first:last]))
                    step_indices.append(step)
                self.assertEqual(step_indices, [s for s in range(16) if gates[s % 8]],
                                 "INFRA: omitted a required startup/second-cycle gate")
                self.assertEqual(len(step_peaks), 14)
                reference = statistics.median(step_peaks)
                self.assertGreater(reference, 0, f"PRODUCT_A10_BASICS04: silent median gate peak in {name}")
                self.assertTrue(all(peak >= reference * 10**(-60/20) for peak in step_peaks),
                                f"PRODUCT_A10_BASICS04: gate-on peak more than 60 dB below median in {name}: {step_peaks}")
                print("OB-C-A10-BASICS04-EVERY-GATE-FACT " + __import__("json").dumps({
                    "variant": name, "enabled_steps": step_indices,
                    "all_14_gate_peaks": step_peaks,
                    "median_step_peak": reference, "nonfinite_samples": 0,
                    "minimum_allowed_peak": reference * 10**(-60/20),
                }, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
