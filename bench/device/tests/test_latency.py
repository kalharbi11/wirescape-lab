# SPDX-License-Identifier: GPL-3.0-only
"""Device-free synthetic signal, click detection and hardware authorization tests."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import latency
import latency_r1
from latency import (CLICK_PEAK, CLICKS, MIN_CLICKS, click_patch,
                     measure, synthetic_capture)


class LatencyTests(unittest.TestCase):
    def call(self, *flags):
        return subprocess.run([sys.executable, str(HERE / "latency.py"), *flags],
                              capture_output=True, text=True, timeout=90)

    def test_known_delay_plus_noise_within_one_sample(self):
        for rate, block in ((44100, 64), (48000, 128), (96000, 256)):
            with self.subTest(rate=rate, block=block):
                audio, first, delay = synthetic_capture(rate, block, noise=0.0015)
                result = measure(audio, rate, first, phase_known=True)
                self.assertEqual(result["clicks_found"], CLICKS)
                self.assertLessEqual(abs(result["frames"]["median"] - delay), 1)
                self.assertLessEqual(max(abs(a["delay_frames"] - delay)
                                         for a in result["arrivals"]), 1)

    def test_low_level_refused_even_if_a_tone_is_present(self):
        audio, first, _ = synthetic_capture(48000, 128, noise=0)
        with self.assertRaisesRegex(ValueError, "below -40 dBFS"):
            measure(audio * 0.0001, 48000, first)

    def test_too_few_clicks_refused(self):
        rate = 48000
        audio, first, _ = synthetic_capture(rate, 128, noise=0)
        audio[first + 18 * (rate // 2):, :] = 0
        with self.assertRaisesRegex(ValueError, "at least 30 required"):
            measure(audio, rate, first)

    def test_clock_patch_bounded_and_muted_until_armed(self):
        patch = click_patch(48000, 128)
        modules = {m["id"]: m for m in patch["modules"]}
        self.assertEqual(modules[1]["parameters"]["bpm"], 120)
        self.assertEqual(modules[1]["parameters"]["run"], 0)
        self.assertEqual(modules[4]["parameters"]["gain"], 0)
        self.assertLessEqual(CLICK_PEAK, 0.2)
        self.assertEqual(len(patch["outputs"]), 2)
        self.assertEqual(len(patch["connections"]), 4)
        self.assertAlmostEqual(20 * math.log10(CLICK_PEAK), -13.9794001, places=3)

    def test_authorization_rejected_before_creating_results(self):
        with tempfile.TemporaryDirectory() as root:
            proc = self.call("--results", root, "--machine", "gate")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--confirm-audio is required", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))
            proc = self.call("--dry-run", "--confirm-audio", "--results", root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--dry-run prohibits", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))
            proc = self.call("--confirm-audio", "--results", root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("requires both --device and --input-device", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))

    def test_no_authorization_no_external_process_or_output(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("subprocess.Popen", side_effect=AssertionError("spawn forbidden")):
                with self.assertRaises(SystemExit):
                    latency.main(["--machine", "gate", "--results", root])
                with self.assertRaises(SystemExit):
                    latency.main(["--dry-run", "--confirm-audio", "--results", root])
            self.assertFalse(list(Path(root).iterdir()))

    def test_direct_capture_helper_requires_authorization_before_backend(self):
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(dry_run=False, confirm_audio=False,
                                   device="output-id", input_device="input-id")
            with patch("subprocess.Popen", side_effect=AssertionError("spawn forbidden")):
                with self.assertRaisesRegex(PermissionError, "--confirm-audio"):
                    latency.physical_capture(args, 128, Path(root))
            self.assertFalse(list(Path(root).iterdir()))

    def test_live_shaped_fixture_is_not_reported_as_calibrated_latency(self):
        rate, block = 48000, 128
        audio, first, _ = synthetic_capture(rate, block, noise=0.001)
        metadata = {
            "rate_hz": rate, "buffer_frames": block,
            "expected_first_frame": first,
            "timing_model": {
                "measurement_quantity": "uncalibrated_host_command_midpoint_to_input_click_onset",
                "calibrated_dac_to_adc_round_trip": False,
                "request_ack_window_ms": 7.0,
                "absolute_error_bound_ms": None,
            },
        }
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(dry_run=False, results=Path(root),
                                   machine="fixture", rate=rate)
            with patch.object(latency, "physical_capture", return_value=(audio, metadata)):
                self.assertTrue(latency.run_one(args, block, "abcdef0123456", "2026-11-15"))
            evidence = list(Path(root).rglob("latency.json"))
            self.assertEqual(len(evidence), 1)
            values = json.loads(evidence[0].read_text(encoding="utf-8"))
            report = (evidence[0].parent / "report.md").read_text(encoding="utf-8")
            self.assertTrue(values["completed"])
            self.assertFalse(values["issue_54_calibrated_round_trip_requirement_met"])
            self.assertFalse(values["measurement"]["calibrated_round_trip"])
            self.assertFalse(values["uncalibrated_nominal_comparison"]["meaningful_device_overhead"])
            self.assertIsNone(values["timing_model"]["absolute_error_bound_ms"])
            self.assertNotIn("difference_from_2x_buffer_frames", values)
            self.assertIn("NOT calibrated DAC-to-ADC", report)
            self.assertIn("NOT an estimate of hardware/device overhead", report)
            self.assertIn("not an error bound", report)

    def test_dry_run_sweep_is_synthetic_and_has_reports(self):
        with tempfile.TemporaryDirectory() as root:
            proc = self.call("--dry-run", "--sweep", "--machine", "synthetic",
                             "--results", root)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            reports = sorted(Path(root).rglob("latency.json"))
            self.assertEqual(len(reports), 3)
            self.assertEqual({json.loads(p.read_text())["buffer_frames"]
                              for p in reports}, {64, 128, 256})
            for path in reports:
                result = json.loads(path.read_text())
                self.assertTrue(result["dry_run"])
                self.assertTrue(result["completed"])
                self.assertEqual(result["kind"], "M0-r2-three-quantity-latency")
                self.assertTrue(result["completed"])
                self.assertEqual(result["harness_loopback_ms"]["statistics"]["repeats"], CLICKS)
                self.assertEqual(result["command_to_capture_ms"]["statistics"]["repeats"], CLICKS)
                self.assertEqual(result["command_to_sound_ms"]["representation"], "range_only")
                self.assertEqual(set(result["command_to_sound_ms"]["range_ms"]), {"median", "p95"})
                self.assertFalse(result["owner_physical_measurement"])
                self.assertEqual(result["measurement"]["quantity"], "synthetic_known_sample_delay")
                self.assertFalse(result["measurement"]["calibrated_round_trip"])
                self.assertEqual(result["measurement"]["clicks_found"], CLICKS)
                self.assertLessEqual(abs(result["measurement"]["frames"]["median"]
                                         - result["synthetic_delay_frames"]), 1)
                self.assertFalse((path.parent / "capture.flac").exists())


class R1ContractTests(unittest.TestCase):
    def test_sample_index_only_duplex_loopback_without_wall_clock(self):
        rate = 48000
        outs = [rate // 4 + i * (rate // 2) for i in range(40)]
        captured = [i + 267 for i in outs]
        with patch.object(latency_r1.time, "monotonic",
                          side_effect=AssertionError("wall clock forbidden")):
            result = latency_r1.harness_loopback_ms(outs, captured, rate)
        self.assertEqual(result["quantity"], "harness_loopback_ms")
        self.assertEqual(result["statistics"]["repeats"], 40)
        self.assertAlmostEqual(result["statistics"]["median"], 267 * 1000 / rate)
        self.assertAlmostEqual(result["statistics"]["p95"], 267 * 1000 / rate)
        with self.assertRaisesRegex(ValueError, "precedes output"):
            latency_r1.harness_loopback_ms(outs, [i - 1 for i in outs], rate)

    def test_adc_timestamp_plus_index_rate_and_callback_fallback_uncertainty(self):
        rate, block = 48000, 128
        epoch = 10.0
        blocks = [{
            "start_frame": k * block, "frames": block,
            "adc_monotonic_s": epoch + k * block / rate,
            "callback_monotonic_s": epoch + (k + 1) * block / rate,
        } for k in range(40)]
        onsets = [k * block + 64 for k in range(40)]
        writes = [epoch + (index - 48) / rate for index in onsets]
        result = latency_r1.command_to_capture_ms(writes, onsets, blocks, rate)
        self.assertEqual(result["statistics"]["repeats"], 40)
        self.assertAlmostEqual(result["statistics"]["median"], 1.0, places=5)
        self.assertAlmostEqual(result["statistics"]["p95"], 1.0, places=5)
        self.assertEqual(result["timestamp_sources"], {"adc": 40, "callback_fallback": 0})
        self.assertEqual(result["additional_capture_buffer_uncertainty_ms"]["max"], 0)
        self.assertIsNone(result["absolute_clock_mapping_error_bound_ms"])
        fallback_blocks = [dict(b) for b in blocks]
        fallback_blocks[-1]["adc_monotonic_s"] = None
        fallback = latency_r1.command_to_capture_ms(writes, onsets, fallback_blocks, rate)
        self.assertEqual(fallback["timestamp_sources"], {"adc": 39, "callback_fallback": 1})
        self.assertAlmostEqual(
            fallback["additional_capture_buffer_uncertainty_ms"]["max"],
            block * 1000 / rate)
        self.assertAlmostEqual(fallback["statistics"]["p95"], 1.0, places=5)
        self.assertGreater(fallback["statistics"]["max"], result["statistics"]["max"])

    def test_range_arithmetic_never_single_sound_latency(self):
        captured = {
            "statistics": {"median": 9.0, "p95": 13.0}
        }
        harness = {
            "statistics": {"median": 3.0, "p95": 5.0}
        }
        result = latency_r1.command_to_sound_ms(captured, harness)
        self.assertEqual(set(result), {"quantity", "representation", "range_ms",
                                       "method", "caveat"})
        self.assertEqual(result["representation"], "range_only")
        self.assertEqual(result["range_ms"]["median"],
                         {"lower_ms": 6.0, "upper_ms": 9.0})
        self.assertEqual(result["range_ms"]["p95"],
                         {"lower_ms": 8.0, "upper_ms": 13.0})

    def test_command_onset_detector_synthetic_clicks_with_noise(self):
        rate, buffer = 8000, 128
        epoch = 20.0
        rng = np.random.default_rng(13)
        audio = rng.normal(0, .0001, (rate * 22, 2)).astype(np.float32)
        first = rate // 4
        expected_frames = [first + k * (rate // 2) for k in range(40)]
        for start in expected_frames:
            click = .18 * np.sin(np.arange(160) * 2*np.pi*1000/rate)
            audio[start:start+len(click), 0] += click
            audio[start:start+len(click), 1] += click
        writes = [epoch + (start-48)/rate for start in expected_frames]
        blocks = [{"start_frame":i, "frames":min(buffer,len(audio)-i),
                   "adc_monotonic_s":epoch+i/rate,
                   "callback_monotonic_s":epoch+(i+buffer)/rate}
                  for i in range(0,len(audio),buffer)]
        found = latency_r1.find_command_onsets(audio,rate,writes,blocks)
        self.assertEqual(len(found), 40)
        self.assertTrue(all(abs(a["start_frame"]-expected_frames[a["click"]]) <= 12
                            for a in found))
        # The old <=12-sample check permitted a double half-window shift.
        # For this known 1 kHz click, phase 0 starts at zero and the first
        # above-threshold captured sample must be at N+1, never before N.
        for observed in found:
            delta = observed["start_frame"] - expected_frames[observed["click"]]
            self.assertGreaterEqual(delta, 0)
            self.assertLessEqual(delta, 1)
        too_few = audio.copy()
        too_few[expected_frames[18]:] = 0
        with self.assertRaisesRegex(ValueError, "at least 30"):
            latency_r1.find_command_onsets(too_few, rate, writes, blocks)

    def test_command_onset_sample_oracle_at_44100_48000_96000_hz(self):
        # Regression oracle for the centered RMS lookahead: a clean pulse has
        # exact zeros before sample N. Reported onset must never precede N,
        # even though the coarse envelope already sees the upcoming pulse.
        # Three phases and a noise case exercise the raw-sample refinement.
        for rate in (44100, 48000, 96000):
            for phase, noise in ((0.0, 0.0), (math.pi / 2, 0.0),
                                 (0.37, 0.0002)):
                with self.subTest(rate=rate, phase=phase, noise=noise):
                    buffer = 128
                    epoch = 20.0
                    first = rate // 4
                    starts = [first + k * (rate // 2) for k in range(40)]
                    frames = starts[-1] + rate // 8
                    rng = np.random.default_rng(84 + rate)
                    audio = rng.normal(0.0, noise, (frames, 2)).astype(np.float32)
                    t = np.arange(round(rate * .016), dtype=np.float64) / rate
                    pulse = (.18 * np.sin(2 * np.pi * 1000 * t + phase)).astype(np.float32)
                    for start in starts:
                        audio[start:start + len(pulse), 0] += pulse
                        audio[start:start + len(pulse), 1] -= pulse * .8
                        if noise == 0:
                            self.assertFalse(np.any(audio[start - 128:start]))
                    writes = [epoch + start / rate - .001 for start in starts]
                    blocks = []
                    for index in range(0, frames, buffer):
                        count = min(buffer, frames - index)
                        blocks.append({
                            "start_frame": index, "frames": count,
                            "adc_monotonic_s": epoch + index / rate,
                            "callback_monotonic_s": epoch + (index + count) / rate,
                        })
                    arrivals = latency_r1.find_command_onsets(
                        audio, rate, writes, blocks)
                    self.assertEqual([row["click"] for row in arrivals],
                                     list(range(40)))
                    onsets = [row["start_frame"] for row in arrivals]
                    for start, onset in zip(starts, onsets):
                        self.assertGreaterEqual(onset, start,
                            "onset cannot be in the exact-zero pre-click region")
                        self.assertLessEqual(onset, start + 1,
                            "1 kHz known onset must resolve within one sample")
                    measured = latency_r1.command_to_capture_ms(
                        writes, onsets, blocks, rate)
                    self.assertEqual(measured["statistics"]["repeats"], 40)
                    self.assertEqual(measured["timestamp_sources"],
                                     {"adc": 40, "callback_fallback": 0})
                    for start, onset, elapsed in zip(
                            starts, onsets, measured["observations_ms"]):
                        self.assertAlmostEqual(
                            elapsed, 1.0 + (onset - start) * 1000 / rate,
                            places=6)
                        self.assertGreaterEqual(elapsed, 1.0 - 1e-8)
                        self.assertLessEqual(elapsed, 1.0 + 1000 / rate + 1e-8)
                    offset = round(.0004 * rate)
                    loopback = latency_r1.harness_loopback_ms(
                        starts, [start + offset for start in starts], rate)
                    sound = latency_r1.command_to_sound_ms(measured, loopback)
                    self.assertEqual(sound["representation"], "range_only")
                    self.assertNotIn("statistics", sound)
                    for quantile in ("median", "p95"):
                        self.assertAlmostEqual(
                            sound["range_ms"][quantile]["lower_ms"],
                            measured["statistics"][quantile] -
                            loopback["statistics"][quantile], places=8)
                        self.assertAlmostEqual(
                            sound["range_ms"][quantile]["upper_ms"],
                            measured["statistics"][quantile], places=8)

    def test_malformed_or_fewer_than_20_samples_refused(self):
        with self.assertRaisesRegex(ValueError, "at least 20"):
            latency_r1.summary([1.0]*19)
        with self.assertRaisesRegex(ValueError, "at least 20"):
            latency_r1.summary([1.0]*19 + [float("nan")])
        with self.assertRaisesRegex(ValueError, "counts differ"):
            latency_r1.command_to_capture_ms([1.0]*21, [5]*20, [], 48000)

    def test_physical_duplex_helper_requires_owner_gate_before_backend(self):
        with self.assertRaisesRegex(PermissionError, "--confirm-audio"):
            latency_r1.duplex_harness(SimpleNamespace(dry_run=True),48000,128,latency)


class RecorderCallbackStatusTests(unittest.TestCase):
    """No PortAudio device or FLAC encoder is touched in these callback tests."""

    def capture_once(self, root, status):
        import record

        class FakeSoundFile:
            def __init__(self, filename, **kwargs):
                self.path = Path(filename)
                self.blocks = []

            def write(self, frames):
                self.blocks.append(frames.copy())

            def close(self):
                # Recorder checks a nonempty finalized artifact, just as it
                # would after a real FLAC writer; bytes are mock data only.
                self.path.write_bytes(b"f" * 256)

        class FakeInputStream:
            def __init__(self, *, callback, **kwargs):
                self.callback = callback

            def start(self):
                timestamp = SimpleNamespace(
                    inputBufferAdcTime=9.9, currentTime=10.0)
                self.callback(
                    np.zeros((128, 2), dtype=np.float32),
                    128, timestamp, status)

            def stop(self):
                pass

            def close(self):
                pass

        with patch.dict(sys.modules, {
            "sounddevice": SimpleNamespace(InputStream=FakeInputStream),
            "soundfile": SimpleNamespace(SoundFile=FakeSoundFile),
        }):
            recorder = record.Recorder(
                "input", Path(root), rate=48000,
                input_device="mock-only", capture_buffer_frames=128)
            recorder.start()
            return recorder

    def test_record_input_overflow_refused_even_without_writer_queue_overflow(self):
        class InputOverflowStatus:
            input_overflow = True

            def __bool__(self):
                return True

            def __str__(self):
                return "input overflow"

        with tempfile.TemporaryDirectory() as root:
            recorder = self.capture_once(root, InputOverflowStatus())
            # This is the failure that previous code missed: all 128 frames
            # were submitted and queue.Full never occurred, but PortAudio
            # reports that samples were lost before invoking the callback.
            self.assertEqual(recorder.overruns, 0)
            self.assertEqual(recorder.captured_frame_count, 128)
            self.assertEqual(recorder.callback_status_count, 1)
            self.assertEqual(recorder.callback_statuses[0], {
                "start_frame": 0, "frames": 128, "flags": "input overflow"})
            with self.assertRaisesRegex(
                    RuntimeError,
                    r"input capture callback status/data loss: 1 flagged callback"
                    r".*capture frame 0, 128 frames: input overflow"):
                recorder.stop()

    def test_record_other_callback_loss_status_also_refused(self):
        with tempfile.TemporaryDirectory() as root:
            recorder = self.capture_once(root, "input underflow")
            self.assertEqual(recorder.overruns, 0)
            self.assertEqual(recorder.callback_status_count, 1)
            with self.assertRaisesRegex(RuntimeError, "input underflow"):
                recorder.stop()

    def test_record_clean_callback_control_preserves_success(self):
        with tempfile.TemporaryDirectory() as root:
            recorder = self.capture_once(root, "")
            self.assertEqual(recorder.callback_status_count, 0)
            self.assertEqual(recorder.callback_statuses, [])
            self.assertEqual(recorder.overruns, 0)
            self.assertEqual(recorder.captured_frame_count, 128)
            artifact = recorder.stop()
            self.assertEqual(artifact, Path(root) / "capture.flac")
            self.assertTrue(artifact.is_file())
            self.assertGreater(artifact.stat().st_size, 100)

    def test_r1_refused_report_preserves_status_and_no_numeric_latency(self):
        # The owner-only command path calls recorder.stop() before computing
        # onsets; an overflow must become a refused run, not a plausible value.
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(
                dry_run=False, results=Path(root), machine="mock-only",
                rate=48000, device_class="test-interface")
            failure = RuntimeError(
                "input capture callback status/data loss: 1 flagged callback(s); "
                "first at capture frame 0, 128 frames: input overflow")
            with (patch.object(latency_r1, "duplex_harness",
                               return_value={"quantity": "harness_loopback_ms"}),
                  patch.object(latency_r1, "physical_command_capture",
                               side_effect=failure)):
                self.assertFalse(latency_r1.run_one(
                    args, 128, "0123456789abcdef", "2026-11-16", latency))
            records = list(Path(root).rglob("latency.json"))
            self.assertEqual(len(records), 1)
            report = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertFalse(report["completed"])
            self.assertFalse(report["owner_physical_measurement"])
            self.assertIn("input overflow", report["error"])
            self.assertIn("capture frame 0", report["error"])
            for metric in ("harness_loopback_ms", "command_to_capture_ms",
                           "command_to_sound_ms"):
                self.assertNotIn(metric, report)
            summary = (records[0].parent / "report.md").read_text(encoding="utf-8")
            self.assertIn("REFUSED", summary)
            self.assertIn("input overflow", summary)


if __name__ == "__main__":
    unittest.main()
