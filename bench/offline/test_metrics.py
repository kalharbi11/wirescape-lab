# SPDX-License-Identifier: GPL-3.0-only
"""Pure DSP measurement tests; no hardware, network or built engine needed."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy import signal

from metrics import (basic, click_events, direct_envelope_metrics,
                     filter_impulse_evidence, filter_metrics,
                     folded_alias_frequencies, oscillator_metrics, patch_metrics,
                     read_audio, r2_impulse_metrics, r2_tail_metrics,
                     self_oscillation_metrics, step_metrics, sweep_residual_metrics,
                      switch_click_metrics)


class MetricsTests(unittest.TestCase):
    def test_r2_exact_impulse_60db_time_known_exponential(self):
        rate = 48000
        tau = .004
        t = np.arange(rate * 2) / rate
        response = np.exp(-t / tau)
        result = r2_impulse_metrics(response, rate)
        self.assertEqual(result["capture_frames"], rate * 2)
        self.assertEqual(result["decay_status"], "reached")
        self.assertEqual(result["nonfinite_samples"], 0)
        self.assertAlmostEqual(result["peak_fs"], 1.0)
        self.assertAlmostEqual(result["time_to_minus60_db_re_peak_ms"],
                               tau * math.log(1000) * 1000, delta=.04)

    def test_r2_60db_time_uses_suffix_peak_not_sine_zero_crossings(self):
        rate = 44100
        t = np.arange(rate * 2) / rate
        response = np.exp(-t / .03) * np.sin(2 * math.pi * 1000 * t)
        measured = r2_impulse_metrics(response, rate)
        self.assertEqual(measured["decay_status"], "reached")
        self.assertGreater(measured["time_to_minus60_db_re_peak_ms"], 150)
        self.assertLess(measured["time_to_minus60_db_re_peak_ms"], 300)
        silence = r2_impulse_metrics(np.zeros(rate * 2), rate)
        self.assertEqual(silence["decay_status"], "zero_response")
        self.assertIsNone(silence["time_to_minus60_db_re_peak_ms"])

    def test_r2_impulse_nan_and_inf_counts(self):
        rate = 48000
        samples = np.zeros(rate * 2)
        samples[3] = np.nan
        samples[4] = np.inf
        result = r2_impulse_metrics(samples, rate)
        self.assertEqual((result["nan_count"], result["inf_count"]), (1, 1))
        self.assertEqual(result["decay_status"], "nonfinite_response")
        with self.assertRaisesRegex(ValueError, "exactly two seconds"):
            r2_impulse_metrics(samples[:-1], rate)

    def test_r2_five_tail_ratios_and_malformed_counts(self):
        rows = [
            {"repeat": i, "active_median_ns": 100 + i * 10,
             "silent_median_ns": 150 + i * 15,
             "silent_over_active": 1.5,
             "active_full_blocks": 100, "silent_full_blocks": 300,
             "subnormal_output_samples": i,
             "nonfinite_output_samples": 0, "faults": 0}
            for i in range(5)
        ]
        result = r2_tail_metrics(rows)
        self.assertEqual(result["repeat_count"], 5)
        self.assertAlmostEqual(result["median_silent_over_active_block_cost"], 1.5)
        self.assertEqual(result["subnormal_output_samples_all_repeats"], 10)
        with self.assertRaisesRegex(ValueError, "exactly five"):
            r2_tail_metrics(rows[:4])
        with self.assertRaisesRegex(ValueError, "invalid block timing"):
            r2_tail_metrics([{**r, "silent_over_active": 0.8}
                             for r in rows])

    def test_float_wav_and_levels(self):
        rate = 48000
        t = np.arange(rate) / rate
        tone = (0.5 * np.sin(2 * math.pi * 440 * t)).astype("<f4")
        data = np.column_stack([tone, tone]).astype("<f4").tobytes()
        length = len(data)
        header = (b"RIFF" + struct.pack("<I", 36 + length) + b"WAVEfmt " +
                  struct.pack("<IHHIIHH", 16, 3, 2, rate, rate * 8, 8, 32) +
                  b"data" + struct.pack("<I", length))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tone.wav"
            path.write_bytes(header + data)
            audio = read_audio(path)
        levels = basic(audio)
        self.assertEqual(audio.shape, (rate, 2))
        self.assertEqual(levels["nonfinite_samples"], 0)
        self.assertAlmostEqual(levels["peak_fs"], .5, places=4)
        self.assertAlmostEqual(levels["rms_fs"], math.sqrt(.125), places=4)

    def test_pitch_and_thd(self):
        t = np.arange(48000) / 48000
        sine = np.sin(2 * math.pi * 440 * t)
        stereo = np.column_stack([sine, sine])
        result = oscillator_metrics(stereo, 440)
        self.assertLess(abs(result["pitch_cents"]), .1)
        self.assertLess(result["thd_db"], -60)
        self.assertTrue(math.isfinite(result["alias_floor_dbfs"]))

    def test_folded_aliases_only_at_expected_harmonics(self):
        rate, fundamental = 48000, 7040
        predicted = folded_alias_frequencies(fundamental, rate, max_harmonic=8)
        self.assertIn(12800., predicted)  # 5 * 7040 -> 12800
        self.assertIn(19840., predicted)  # 4 * 7040 -> 19840
        self.assertNotIn(7040., predicted)  # fundamental is not an alias
        t = np.arange(rate, dtype=float) / rate
        clean = .6 * np.sin(math.tau * fundamental * t)
        alias = clean + .2 * np.sin(math.tau * 12800 * t)
        metric = lambda x: oscillator_metrics(np.column_stack([x, x]), fundamental, rate)
        a, b = metric(clean), metric(alias)
        self.assertGreater(b["alias_floor_dbfs"], a["alias_floor_dbfs"] + 25)
        self.assertGreater(b["alias_expected_bin_count"], 0)
        self.assertGreater(b["nonharmonic_floor_dbfs"], a["nonharmonic_floor_dbfs"] + 25)

    def test_nonfinite(self):
        data = np.zeros((50, 2))
        data[8, 0] = np.nan
        self.assertEqual(basic(data)["nonfinite_samples"], 1)

    def test_click_and_silence(self):
        data = np.zeros((48000, 2))
        data[10000:20000] = .2
        metrics = patch_metrics(data)
        self.assertGreaterEqual(metrics["silence_segments"], 1)
        self.assertEqual(metrics["nonfinite_samples"], 0)

    def test_click_detector_known_answer_sine_and_saw(self):
        rate = 48000
        time = np.arange(rate * 2) / rate
        sine = .1 * np.sin(math.tau * 440 * time)
        saw = .1 * (2 * ((440 * time + .5) % 1) - 1)
        for label, clean in (("sine", sine), ("saw", saw)):
            with self.subTest(shape=label):
                self.assertEqual(click_events(clean, rate), [])
                shifted = clean.copy()
                shifted[int(rate * .31):] += .6
                shifted[int(rate * 1.13):] -= .6
                found = click_events(shifted, rate)
                self.assertEqual(len(found), 2, found)
                self.assertAlmostEqual(found[0]["time_s"], .31, delta=.003)
                self.assertAlmostEqual(found[1]["time_s"], 1.13, delta=.003)
                for event in found:
                    self.assertAlmostEqual(event["size_fs"], .6, delta=.1)
                    self.assertGreaterEqual(event["highpass_energy_ratio"], 3)
                stereo = np.column_stack([shifted, shifted])
                report = patch_metrics(stereo, rate)
                self.assertEqual(report["click_count"], 2)
                self.assertEqual(len(report["click_events"]), 2)
                self.assertNotIn("click_delta_outliers", report)

    def test_direct_envelope_timing(self):
        rate = 48000
        x = np.concatenate([np.linspace(0, 1, 2400), np.ones(21600),
                            np.linspace(1, 0, 4800), np.zeros(19200)])
        stereo = np.column_stack([x, x])
        record = direct_envelope_metrics(stereo, 0, 24000, .05, .1)
        self.assertAlmostEqual(record["rise_measured_s"], .05, delta=.001)
        self.assertAlmostEqual(record["fall_measured_s"], .1, delta=.002)

    def test_filter_cutoff_and_resonance_interpolation(self):
        rate = 48000
        rng = np.random.default_rng(17)
        dry = rng.normal(0, .1, rate * 3)
        # Third-order lowpass IIR has an analytic -3.01 dB corner at 1k.
        wet = signal.sosfilt(signal.butter(3, 1000, fs=rate, output="sos"), dry)
        stereo = lambda x: np.column_stack([x, x])
        record = filter_metrics(stereo(dry), stereo(wet), rate,
                                cutoff_hz=1000, resonance=0, output_tap="test.lowpass")
        self.assertEqual(record["output_tap"], "test.lowpass")
        self.assertAlmostEqual(record["cutoff_3db_hz"], 1000, delta=80)
        self.assertAlmostEqual(record["cutoff_error_hz"], 0, delta=80)
        f = np.arange(0, 4000, 100, dtype=float)
        response = -((f - 750) / 200) ** 2 + 2
        from metrics import parabolic_peak_hz
        self.assertAlmostEqual(parabolic_peak_hz(f, response, 7), 750, delta=1)

    def test_sweep_residual_ratio_known_answer(self):
        rate = 48000
        fast_time = np.arange(rate) / rate
        slow_time = np.arange(rate * 8) / rate
        fast = .1 * np.sin(math.tau * 440 * fast_time)
        fast += .08 * np.sin(math.tau * 8000 * fast_time)
        slow = .1 * np.sin(math.tau * 440 * slow_time)
        record = sweep_residual_metrics(fast, slow, rate)
        self.assertGreater(record["fast_to_slow_highpass_ratio"], 10)
        self.assertEqual(record["fast_duration_s"], 1)
        self.assertEqual(record["slow_duration_s"], 8)

    def test_impulse_gate_pulse_not_misreported(self):
        rate = 48000
        signal = np.zeros(rate * 3)
        signal[0:4] = 1
        too_wide = filter_impulse_evidence(signal, rate, 4)
        self.assertEqual(too_wide["status"], "not_exact_impulse")
        self.assertIn("4 samples", too_wide["reason"])
        self.assertNotIn("tail_rms_fs", too_wide)
        self.assertEqual(too_wide["gate_pulse_tail_rms_fs"], 0)
        exact = filter_impulse_evidence(signal, rate, 1)
        self.assertEqual(exact["status"], "measured")
        self.assertEqual(exact["excitation_shape"], "single_sample_impulse")
        self.assertIn("tail_rms_fs", exact)

    def test_post_impulse_tail_rms_known_answer(self):
        rate = 48000
        silent = np.zeros(rate * 3)
        silent[0] = 1
        measure = self_oscillation_metrics(silent, rate)
        self.assertEqual(measure["status"], "measured")
        self.assertEqual(measure["tail_rms_fs"], 0)
        sustained = silent.copy()
        sustained[rate * 2:] = .1
        active = self_oscillation_metrics(sustained, rate)
        self.assertAlmostEqual(active["tail_rms_fs"], .1, places=7)

    def test_t7_switch_click_step_and_crossfade_known_answers_three_rates(self):
        # Same deliberately constructed 0->0.8 DC step, once immediate and
        # once over 10 ms; both cases preserve the same final steady state.
        for rate in (44100, 48000, 96000):
            with self.subTest(rate=rate):
                switch = rate // 2
                abrupt = np.zeros(rate, dtype=float)
                abrupt[switch:] = .8
                fade = max(4, int(rate * .010))
                gentle = np.zeros(rate, dtype=float)
                gentle[switch:switch + fade] = .8 * np.linspace(0, 1, fade)
                gentle[switch + fade:] = .8
                immediate = switch_click_metrics(np.column_stack([abrupt, abrupt]), switch, rate)
                crossfade = switch_click_metrics(np.column_stack([gentle, gentle]), switch, rate)
                self.assertEqual(immediate["status"] if "status" in immediate else "measured",
                                 "measured")
                self.assertGreater(immediate["switch_click_peak_fs"],
                                   crossfade["switch_click_peak_fs"])
                self.assertGreater(immediate["switch_click_peak_dbfs"],
                                   crossfade["switch_click_peak_dbfs"] + 20)
                self.assertAlmostEqual(immediate["switch_click_peak_fs"],
                    step_metrics(np.column_stack([abrupt, abrupt]), switch, rate)["highpass_peak_fs"])
                self.assertAlmostEqual(immediate["switch_click_peak_dbfs"],
                    20 * math.log10(immediate["switch_click_peak_fs"]))
                self.assertEqual(immediate["highpass_hz"], 2000)
                self.assertAlmostEqual(immediate["window_ms"],
                    2000 * int(.025 * rate) / rate, places=12)

    def test_t7_switch_click_silence_and_short_capture_are_explicit(self):
        rate = 48000
        zero = switch_click_metrics(np.zeros((rate, 2)), rate // 2, rate)
        self.assertEqual(zero["switch_click_peak_fs"], 0.0)
        self.assertEqual(zero["switch_click_peak_dbfs"], "-inf")
        missing = switch_click_metrics(np.zeros((3, 2)), 1, rate)
        self.assertIsNone(missing["switch_click_peak_fs"])
        self.assertEqual(missing["status"], "unavailable")

    def test_t7_0b_excess_and_identical_pair(self):
        rate, switch = 48000, 48000
        t = np.arange(rate * 2) / rate
        floor = .04 * np.sin(2 * math.pi * 220 * t)
        switched = floor.copy()
        switched[switch:] += .4
        stereo = lambda mono: np.column_stack([mono, mono])
        result = switch_click_metrics(stereo(switched), switch, rate,
                                      no_switch_audio=stereo(floor))
        self.assertEqual(result["status"], "measured")
        self.assertGreater(result["click_excess_db"], 0)
        self.assertAlmostEqual(result["click_excess_db"],
            result["switch_click_peak_dbfs"] - result["no_switch_floor_dbfs"])
        self.assertEqual(result["window_before_ms"], 25)
        self.assertEqual(result["window_after_ms"], 25)
        same = switch_click_metrics(stereo(floor), switch, rate,
                                    no_switch_audio=stereo(floor))
        self.assertEqual(same["click_excess_db"], 0.0)

    def test_t7_0b_delay_repetition_window_and_refusal(self):
        rate, switch, seconds = 48000, 48000, .375
        floor = np.zeros(rate * 2)
        active = floor.copy()
        active[switch + int(seconds * rate)] = .5
        stereo = lambda mono: np.column_stack([mono, mono])
        early = switch_click_metrics(stereo(active), switch, rate)
        late = switch_click_metrics(stereo(active), switch, rate,
                                    no_switch_audio=stereo(floor),
                                    delay_time_s=seconds)
        self.assertEqual(early["switch_click_peak_fs"], 0.)
        self.assertGreater(late["switch_click_peak_fs"], .1)
        self.assertEqual(late["click_excess_db"], "inf")
        self.assertEqual(late["window_kind"], "delay_first_repeat")
        self.assertEqual(late["window_after_ms"], 400.)
        refused = switch_click_metrics(stereo(active[:switch + 8]), switch, rate,
                                       no_switch_audio=stereo(floor[:switch + 8]),
                                       delay_time_s=seconds)
        self.assertEqual(refused["status"], "unavailable")
        self.assertIsNone(refused["click_excess_db"])

    def test_t7_0b_window_captures_late_first_effect(self):
        rate, switch, first = 48000, 48000, 84001
        baseline = np.zeros((rate * 2, 2))
        switched = baseline.copy()
        switched[first] = .5
        early = switch_click_metrics(switched, switch, rate,
                                     no_switch_audio=baseline, delay_time_s=.375)
        corrected = switch_click_metrics(switched, switch, rate,
                                         no_switch_audio=baseline, delay_time_s=.375,
                                         first_effect_frame=first)
        self.assertEqual(early["switch_click_peak_fs"], 0.0)
        self.assertGreater(corrected["switch_click_peak_fs"], .1)
        self.assertEqual(corrected["window_kind"], "delay_first_observed_difference")
        self.assertEqual(corrected["window_end_frame_exclusive"], first + 1200)

    def test_response_and_step(self):
        t = np.arange(48000) / 48000
        dry = np.column_stack([np.sin(t * math.tau * 440)] * 2)
        wet = dry * .5
        response = filter_metrics(dry, wet)
        self.assertEqual(len(response["frequency_hz"]), 2049)
        index = int(np.argmin(abs(np.asarray(response["frequency_hz"]) - 440)))
        self.assertAlmostEqual(response["magnitude_db"][index], -6.0206, places=2)
        self.assertIsNotNone(step_metrics(wet, 24000)["highpass_peak_fs"])


if __name__ == "__main__":
    unittest.main()
