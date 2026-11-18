#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Pure regression tests for the #193 collector; no native/device execution."""
import hashlib
import math
from array import array
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
        self.assertEqual(collect.DAMPINGS, (0.1, 0.4, 0.7, 0.9))
        self.assertEqual(collect.HEAD, "32abedde03e37a8d85510244c61d782652ed32c8")

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

    @staticmethod
    def _pcm(rate, late=False):
        samples = array("f", [0.0]) * (2 * rate)
        samples[0] = 1.0
        # Deliberate late transient: suffix-maximum must not accept an
        # earlier zero crossing while the remainder contains this spike.
        samples[rate // (2 if late else 4)] = 0.02
        return samples.tobytes()

    def _fake_actual(self, out, include_d5=False):
        original_probe = "a" * 64
        source = {p: "f" * 64 for p in collect.SOURCE_FILES}
        source["bench/offline/r2_engine_probe.cpp"] = original_probe
        harness = out / "harness/r2_engine_probe_a13.cpp"
        harness.parent.mkdir(parents=True, exist_ok=True)
        harness.write_text("synthetic A13 source fixture only\n")
        adjusted_probe = collect.digest(harness)
        records = {}
        for label, sha in (("before", collect.BASE), ("head", collect.HEAD)):
            impulse, tails, measures = [], [], {}
            for damping in collect.DAMPINGS:
                key = collect.damping_key(damping)
                values = {}
                for rate in collect.RATES:
                    raw = out / ("raw/r2-%s-d%s-%d.f32le" %
                                 (label, key.replace(".", ""), rate))
                    raw.parent.mkdir(parents=True, exist_ok=True)
                    raw.write_bytes(self._pcm(rate))
                    metrics = collect.raw_suffix_r2(raw, rate)
                    actual_probe = original_probe if damping == 0.4 else adjusted_probe
                    attribution = {"probe_sha256": actual_probe}
                    kind = "original_pinned" if damping == 0.4 else "A13_collector_damping_only"
                    entry = row(rate, metrics["time_to_minus60_db_re_peak_ms"])
                    entry.update(metrics)
                    entry.update(damping=damping, input_mode="bench_source_engine_graph",
                                 module_library_sha256="c"*64,
                                 effective_probe_sha256=actual_probe,
                                 probe_source=attribution, probe_kind=kind,
                                 raw_capture={
                                     "path":raw.relative_to(out).as_posix(),
                                     "sha256_float32_pcm":collect.digest(raw),
                                     "bytes":raw.stat().st_size})
                    impulse.append(entry)
                    values[rate] = metrics["time_to_minus60_db_re_peak_ms"]
                    repeats = [{
                        "repeat": i, "faults": 0, "active_full_blocks": 100,
                        "silent_full_blocks": 500,
                        "active_median_ns": 100.0, "silent_median_ns": 103.0,
                        "silent_over_active": 1.03,
                        "subnormal_output_samples": 0,
                        "nonfinite_output_samples": 0,
                    } for i in range(5)]
                    tails.append({
                        "metric":"r2_tail", "module":collect.MODULE,
                        "sample_rate_hz":rate, "damping":damping,
                        "status":"measured",
                        "engine_process_mode":"production_Engine_render",
                        "active_frames":rate, "zero_frames":5*rate,
                        "zero_input_verified":True,
                        "production_ftz_mode":"engine_render_mxcsr_ftz_daz",
                        "probe_kind":kind, "effective_probe_sha256":actual_probe,
                        "probe_source":attribution,
                        "repeats":repeats, "repeat_count":5,
                        "median_silent_over_active_block_cost":1.03,
                        "individual_silent_over_active_ratios":[1.03]*5,
                        "subnormal_output_samples_all_repeats":0,
                        "nonfinite_output_samples_all_repeats":0,
                        "method":collect.TAIL_METHOD,
                    })
                measures[key] = {str(rate):values[rate] for rate in collect.RATES}
            default = {int(k):v for k,v in measures["0.4"].items()}
            record = {
                "schema":"wirescape/s7.1-evidence-193/2", "source_commit":sha,
                "label":label, "quick":False, "sample_rates_hz":list(collect.RATES),
                "dampings":list(collect.DAMPINGS),
                "source_harness_sha256":source,
                "damping_probe":{
                    "retained_source":harness.relative_to(out).as_posix(),
                    "original_source_sha256":original_probe,
                    "effective_source_sha256":adjusted_probe,
                }, "impulse":impulse, "tail":tails,
                "times_ms":{str(r):default[r] for r in collect.RATES},
                "spread_percent_of_48k":collect.spread_percent(default),
                "times_ms_by_damping":measures,
                "spread_percent_by_damping":{
                    k:collect.spread_percent({int(r):v for r,v in val.items()})
                    for k,val in measures.items()},
            }
            collect.write_json(out / ("r2-%s.json" % label),record)
            records[label]=record
        if include_d5:
            self._make_d5(out)
        return records

    @staticmethod
    def _make_d5(out):
        d5 = out / "d5"
        d5.mkdir(parents=True, exist_ok=True)
        pcm = array("f", [0.0]) * (48000 * 10 * 2)
        pcm[0] = .25
        renders = {}
        for label, sha in (("before", collect.BASE), ("head", collect.HEAD)):
            a = d5 / (label + ".f32le")
            b = d5 / (label + ".flac")
            a.write_bytes(pcm.tobytes())
            b.write_bytes(b"fLaCsynthetic-validated-hash-not-a-real-encoder")
            renders[label] = {
                "source_commit":sha, "source_patch_sha256":"b"*64,
                "renderer_sha256":"c"*64,
                "original_pcm":{"path":a.name,"bytes":a.stat().st_size,
                                "sha256":collect.digest(a),
                                "format":"interleaved stereo little-endian float32"},
                "flac":{"path":b.name,"bytes":b.stat().st_size,
                        "sha256":collect.digest(b),
                        "codec":{"codec_name":"flac","sample_rate":"48000",
                                 "channels":2,"bits_per_raw_sample":24}}
            }
        script=d5/"c4-events.json"
        script.write_text("[]\n",encoding="utf-8")
        collect.write_json(d5/"manifest.json",{
            "sources":{"before":collect.BASE,"head":collect.HEAD},
            "configuration":{"sample_rate_hz":48000,"block_frames":128,"seconds":10,
                             "seed":37,"channels":2},
            "patch":collect.PATCH,"patch_sha256":"b"*64,
            "rendered_separately":True,
            "script":script.name,"script_sha256":collect.digest(script),
            "renders":renders,"float32_pcm_identical":True})

    def test_detached_suffix_r2_is_not_zero_crossing_and_rejects_nonfinite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.f32le"
            rate=100
            p.write_bytes(self._pcm(rate))
            timing=collect.raw_suffix_r2(p,rate)["time_to_minus60_db_re_peak_ms"]
            self.assertEqual(timing,(rate//4+1)/rate*1000)
            original=bytearray(p.read_bytes())
            original[-4:]=array("f",[math.nan]).tobytes()
            p.write_bytes(original)
            with self.assertRaisesRegex(ValueError,"nonfinite"):
                collect.raw_suffix_r2(p,rate)
            p.write_bytes(b"\x00\x00\x00")
            with self.assertRaisesRegex(ValueError,"length"):
                collect.raw_suffix_r2(p,rate)

    def test_generated_probe_is_narrow_source_retained_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            checkout=root/"pinned"
            (checkout/"native").mkdir(parents=True)
            src=checkout/"bench/offline/r2_engine_probe.cpp"
            src.parent.mkdir(parents=True)
            src.write_text("original signal source\n"
                           "    engine->reset(); // Start one full second of silence before the single impulse.\n"
                           "original engine render\n")
            temporary=root/"generated"
            temporary.mkdir()
            target,record=collect.make_damping_probe(checkout,temporary,root/"archive")
            self.assertTrue(target.is_file())
            self.assertTrue((temporary/"native").is_symlink())
            self.assertEqual(record["original_source_sha256"],collect.digest(src))
            self.assertEqual(record["effective_source_sha256"],
                             collect.digest(root/"archive"/record["retained_source"]))
            self.assertEqual(target.read_text().count("WS_R2_DAMPING"),1)
            self.assertEqual(src.read_text().count("WS_R2_DAMPING"),0)
            src.write_text("mismatched original reset seam")
            with self.assertRaisesRegex(ValueError,"seam changed"):
                collect.make_damping_probe(checkout,root/"other",root/"archive")

    def test_summary_requires_before_head_production_and_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            self._fake_actual(out)
            with patch.object(collect.platform, "machine", return_value="x86_64"):
                with self.assertRaisesRegex(ValueError,"D5 pair required"):
                    collect.summarize(out)
            with patch.object(collect.platform, "machine", return_value="aarch64"):
                collect.summarize(out)
            result=json.loads((out/"summary.json").read_text())
            self.assertTrue(result["r2_target_met"])
            self.assertTrue(result["a13_no_damping_regressions"])
            self.assertTrue(result["r2_48k_original_pcm_identical"])
            self.assertFalse(result["d5_flac_pair_staged"])
            self.assertEqual(len(result["a13_damping_rows"]),4)
            raw=out/"raw/r2-head-d04-48000.f32le"
            raw.write_bytes(b"tampered")
            with patch.object(collect.platform, "machine", return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"byte length/SHA"):
                    collect.summarize(out)

    def test_summary_recomputes_raw_even_if_hash_and_claimed_time_are_mutated(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            self._fake_actual(out)
            record=out/"r2-head.json"
            j=json.loads(record.read_text())
            j["impulse"][0]["time_to_minus60_db_re_peak_ms"]+=2.0
            collect.write_json(record,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"timing/peak mismatch"):
                    collect.summarize(out)
            self._fake_actual(out)
            record=out/"r2-head.json"
            j=json.loads(record.read_text())
            item=j["impulse"][0]["raw_capture"]
            raw=out/item["path"]
            raw.write_bytes(array("f",[0.0]) * (2*j["impulse"][0]["sample_rate_hz"]))
            item["sha256_float32_pcm"]=collect.digest(raw)
            item["bytes"]=raw.stat().st_size
            collect.write_json(record,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"silent"):
                    collect.summarize(out)

    def test_tail_five_repeats_and_ratio_are_validated_not_trusted(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            self._fake_actual(out)
            path=out/"r2-head.json"
            j=json.loads(path.read_text())
            j["tail"][0]["repeats"][1]["silent_over_active"]=1.33
            collect.write_json(path,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"repeated timing ratio"):
                    collect.summarize(out)
            self._fake_actual(out)
            j=json.loads(path.read_text())
            j["tail"][0]["repeats"].pop()
            collect.write_json(path,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"five real full timing"):
                    collect.summarize(out)

    def test_missing_damping_and_mismatched_source_probe_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            self._fake_actual(out)
            path=out/"r2-head.json"
            j=json.loads(path.read_text())
            j["impulse"].pop()
            collect.write_json(path,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"damping.*rate matrix"):
                    collect.summarize(out)
            self._fake_actual(out)
            j=json.loads(path.read_text())
            j["impulse"][0]["effective_probe_sha256"]="0"*64
            collect.write_json(path,j)
            with patch.object(collect.platform,"machine",return_value="aarch64"):
                with self.assertRaisesRegex(ValueError,"source attribution"):
                    collect.summarize(out)

    def test_d5_present_missing_or_corrupt_flac_and_pcm_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            self._fake_actual(out, include_d5=True)
            with patch.object(collect.platform,"machine",return_value="x86_64"):
                collect.summarize(out)
                self.assertTrue(json.loads((out/"summary.json").read_text())[
                    "d5_flac_pair_staged"])
                flac=out/"d5/head.flac"
                flac.unlink()
                with self.assertRaisesRegex(ValueError,"missing/size/SHA"):
                    collect.summarize(out)
                self._make_d5(out)
                flac.write_bytes(b"fLaCtampered")
                with self.assertRaisesRegex(ValueError,"missing/size/SHA"):
                    collect.summarize(out)
                self._make_d5(out)
                pcm=out/"d5/head.f32le"
                pcm.write_bytes(pcm.read_bytes()[:-4])
                with self.assertRaisesRegex(ValueError,"missing/size/SHA"):
                    collect.summarize(out)
                self._make_d5(out)
                manifest=out/"d5/manifest.json"
                d5=json.loads(manifest.read_text())
                d5["float32_pcm_identical"]=False
                collect.write_json(manifest,d5)
                with self.assertRaisesRegex(ValueError,"identity failed"):
                    collect.summarize(out)



if __name__ == "__main__":
    unittest.main()
