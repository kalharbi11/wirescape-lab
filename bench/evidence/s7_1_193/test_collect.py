#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Pure regression tests for the #193 collector; no native/device execution."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collect


def row(rate, ms):
    return {
        "module": "fx.reverb", "metric": "r2_impulse",
        "engine_process_mode": "production_Engine_render",
        "sample_rate_hz": rate, "status": "measured", "decay_status": "reached",
        "input_nonzero_frames": 1,
        "one_second_pre_silence_frames": rate,
        "capture_frames": 2 * rate, "faults": 0,
        "time_to_minus60_db_re_peak_ms": ms,
    }


class PinnedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row(44100, 250.), row(48000, 245.35417), row(96000, 248.)]

    def test_pins_are_full_immutable_sha_and_expected_d5_fixture(self):
        for commit in (collect.BASE, collect.HEAD):
            self.assertEqual(len(commit), 40)
            int(commit, 16)
        self.assertNotEqual(collect.BASE, collect.HEAD)
        self.assertEqual((collect.BLOCK, collect.SECONDS, collect.SEED),
                         (128, 10, 37))
        self.assertEqual(collect.PATCH, "basics-03-echo-and-reverb.json")
        self.assertEqual(collect.RATES, (44100, 48000, 96000))

    def test_exact_three_production_rows_and_unchanged_percent_denominator(self):
        values = collect.validate_impulses(self.rows)
        self.assertEqual(set(values), {44100, 48000, 96000})
        self.assertAlmostEqual(collect.spread_percent(values),
                               (250.-245.35417)/245.35417*100)
        self.assertLess(collect.spread_percent(values), 5.0)

    def test_missing_or_proxy_rate_refusal_fails_not_skips(self):
        for mutated in (
            self.rows[:-1],
            self.rows[:2] + [row(48000, 248.)],
            [dict(self.rows[0], engine_process_mode="module_unit_proxy"),
             *self.rows[1:]],
            [dict(self.rows[0], status="not_run_quick_mode"), *self.rows[1:]],
            [dict(self.rows[0], input_nonzero_frames=2), *self.rows[1:]],
            [dict(self.rows[0], faults=1), *self.rows[1:]],
            [dict(self.rows[0], decay_status="not_reached_within_2s"),
             *self.rows[1:]],
        ):
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    collect.validate_impulses(mutated)

    def test_bad_reference_and_explicit_threshold(self):
        with self.assertRaises(ValueError):
            collect.spread_percent({44100: 1., 48000: 0., 96000: 1.})
        with self.assertRaises(ValueError):
            collect.spread_percent({44100: 1., 48000: 1.})
        self.assertGreater(collect.spread_percent(
            {44100: 295.80499, 48000: 245.35417, 96000: 208.53125}), 5.)
        self.assertGreater(collect.spread_percent(
            {44100: 295.80499, 48000: 245.35417, 96000: 169.43750}), 5.)

    def test_source_identity_rejects_nonpinned_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(collect, "execute") as run:
                run.return_value.stdout = "f" * 40 + "\n"
                with self.assertRaisesRegex(ValueError, "source mismatch"):
                    collect.pinned(root, "before")

    def test_raw_hashes_are_over_actual_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "original.f32le"
            p.write_bytes(b"\x00\x00\x00\x00\x00\x00\x80?")
            self.assertEqual(collect.digest(p), hashlib.sha256(p.read_bytes()).hexdigest())
            p.write_bytes(p.read_bytes() + b"\x00")
            self.assertNotEqual(collect.digest(p),
                                hashlib.sha256(b"\x00\x00\x00\x00\x00\x00\x80?").hexdigest())

    def test_summary_requires_before_head_production_and_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for label, sha in (("before", collect.BASE), ("head", collect.HEAD)):
                rows = []
                for r in self.rows:
                    item = dict(r)
                    rel = "raw/r2-%s-%d.f32le" % (label, r["sample_rate_hz"])
                    path = out / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"real bytes, synthetic fixture only")
                    item["raw_capture"] = {
                        "path": rel, "sha256_float32_pcm": collect.digest(path)}
                    rows.append(item)
                collect.write_json(out / ("r2-%s.json" % label), {
                    "source_commit": sha,
                    "source_harness_sha256": {"r2_probe": "fixed"},
                    "impulse": rows,
                })
            # x64 requires an actual D5 manifest; the synthetic pure test may
            # omit it on arm64. The collector must refuse missing x64 evidence.
            with patch.object(collect.platform, "machine", return_value="x86_64"):
                with self.assertRaisesRegex(ValueError, "D5 pair required"):
                    collect.summarize(out)
            with patch.object(collect.platform, "machine", return_value="aarch64"):
                collect.summarize(out)
            result = json.loads((out / "summary.json").read_text())
            self.assertTrue(result["r2_target_met"])
            self.assertFalse(result["d5_flac_pair_staged"])
            # Corrupted original float PCM can never be treated as verified.
            (out / "raw/r2-head-48000.f32le").write_bytes(b"tampered")
            with patch.object(collect.platform, "machine", return_value="aarch64"):
                with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                    collect.summarize(out)


if __name__ == "__main__":
    unittest.main()
