#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Pure known-answer #226 tests. No native library, audio device, or GitHub checkout."""
from __future__ import annotations

import gzip
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collect


class MacroCollectorTests(unittest.TestCase):
    def test_immutable_source_pins_and_disallow_unreleased_capture(self):
        self.assertEqual(collect.RATES, (44100, 48000, 96000))
        self.assertEqual(len(collect.MODELS), 24)
        self.assertEqual(len(collect.TARGETS), 5)
        self.assertEqual(len(collect.matrix("before")), 120)
        self.assertEqual(len(collect.matrix("head")), 360)
        self.assertEqual(len(set(collect.matrix("head"))), 360)
        self.assertEqual(collect.PITCH_MAX_DELTA_CENTS, 2)
        self.assertEqual(collect.IR_48_MAX_GROWTH_PERCENT, 3)
        self.assertEqual(collect.D5_PATCH, "basics-07-macro-keys.json")
        for bad in ("", "a"*39, "g"*40, "deadbeef", "a"*41):
            with self.subTest(pin=bad):
                with self.assertRaises(ValueError):
                    collect.verify_sha(bad)
        self.assertEqual(collect.verify_sha("f"*40), "f"*40)
        with patch.object(collect, "run") as runner:
            runner.return_value.stdout = "a"*40+"\n"
            with self.assertRaisesRegex(ValueError, "pin mismatch"):
                collect.pinned(Path("/tmp/invalid-source"), "b"*40)

    def test_original_existing_estimator_cannot_certify_inharmonic_pitch(self):
        raw = {"observed_hz": 445.5, "pitch_cents": 21.51}
        p = collect.pitch_status(raw)
        self.assertEqual(p["status"], "unmeasured_pending_design_ruling")
        self.assertEqual(p["unmodified_estimator_pitch_cents_diagnostic"], 21.51)
        self.assertEqual(p["unmodified_estimator_observed_hz_diagnostic"], 445.5)
        self.assertIn("fundamental", p["reason"])
        for val in (None, 0, float("nan"), float("inf")):
            p = collect.pitch_status({"observed_hz": val, "pitch_cents": 0})
            self.assertEqual(p["status"], "unmeasured")
        self.assertEqual(collect.pitch_status({
            "observed_hz": 440.0, "pitch_cents": None})["status"], "unmeasured")
        self.assertFalse(any("passed" in key for key in
                             collect.pitch_status(raw)))

    def test_patch_recipe_inherits_existing_CV_and_model_identity(self):
        import numpy as np  # installed in host-independent test workflow
        class Existing:
            @staticmethod
            def direct_source(ident, version, params, port):
                return {"modules":[{"id":1,"module":ident,"parameters":params}],
                        "connections":[{"from":{"module":1,"port":port}}]}
            @staticmethod
            def mod(node, name, parameters):
                return {"id":node,"module":name,"parameters":parameters}
            @staticmethod
            def edge(fr, p, to, q):
                return {"from":(fr,p), "to":(to,q)}
        patch110=collect.macro_patch(Existing,1,23,110)
        self.assertEqual(patch110["modules"][0]["parameters"]["model"],23)
        self.assertEqual(patch110["modules"][0]["module"],collect.MODULE)
        self.assertEqual(patch110["connections"][0]["from"]["port"],"main")
        patch7040=collect.macro_patch(Existing,1,7,7040)
        self.assertEqual(patch7040["modules"][0]["parameters"]["model"],7)
        self.assertEqual(len(patch7040["modules"]),3 if
                         patch7040["modules"][0].get("module")=="unused" else 2)
        self.assertEqual(patch7040["modules"][1]["module"],"essentials.scale_offset")
        self.assertGreater(patch7040["modules"][1]["parameters"]["offset"],0)
        self.assertTrue(np.isfinite(patch7040["modules"][1]["parameters"]["offset"]))

    def test_raw_original_float32_stereo_pcm_is_strict(self):
        rate=48000
        frames=4
        pcm=struct.pack("<8f",*[0.125,-0.125]*frames)
        header=(b"RIFF"+struct.pack("<I",36+len(pcm))+b"WAVE"+
                b"fmt "+struct.pack("<IHHIIHH",16,3,2,rate,rate*8,8,32)+
                b"data"+struct.pack("<I",len(pcm)))
        self.assertEqual(len(header),44)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            wav=root/"audio.wav"
            wav.write_bytes(header+pcm)
            self.assertEqual(collect.raw_pcm(wav,rate,frames/rate),pcm)
            with self.assertRaisesRegex(ValueError,"encoding/rate"):
                collect.raw_pcm(wav,44100,frames/rate)
            with self.assertRaisesRegex(ValueError,"size mismatch"):
                collect.raw_pcm(wav,rate,frames/rate+1/rate)
            compressed=root/"raw"/"trial.f32le.gz"
            info=collect.preserve_pcm(pcm,compressed,root)
            self.assertEqual(info["sha256_original_pcm"],hashlib.sha256(pcm).hexdigest())
            self.assertEqual(gzip.decompress(compressed.read_bytes()),pcm)
            collect.require_raw(root,info)
            compressed.write_bytes(compressed.read_bytes()+b"garbage")
            with self.assertRaisesRegex(ValueError,"compressed SHA mismatch"):
                collect.require_raw(root,info)

    def test_sources_and_rounded_cost_verdict_are_evidence_not_guesses(self):
        self.assertEqual(tuple(collect.IR_LENGTHS),(12,24))
        self.assertEqual(collect.FRAMES,128)
        self.assertEqual(collect.SECONDS,10)
        self.assertEqual(collect.SEED,37)
        self.assertEqual(collect.RATES,(44100,48000,96000))
        self.assertEqual(collect.matrix("head")[-1],(23,96000,7040))
        self.assertEqual(collect.matrix("before")[0],(0,48000,110))
        with self.assertRaises(ValueError):
            collect.matrix("unknown")

    def _fake_complete(self, out, base_sha="a"*40, head_sha="b"*40):
        original_pcm=b"\x00\x00\x00\x00\x00\x00\x80\x3f"
        p=out/"raw"/"canonical.f32le.gz"
        raw=collect.preserve_pcm(original_pcm,p,out)
        # All actual row identities are represented, but values here are PURE
        # SYNTHETIC KNOWN-ANSWER DATA, not human-facing benchmark claims.
        def rows(label):
            return [dict(module=collect.MODULE,model=m, sample_rate_hz=r,
                         target_hz=hz,status="measured_output",pcm=raw,
                         estimator={"observed_hz":float(hz),
                                    "pitch_cents":0.0},
                         pitch={"status":"unmeasured_pending_design_ruling"})
                    for m,r,hz in collect.matrix(label)]
        for label,sha in (("before",base_sha),("head",head_sha)):
            collect.save(out/f"pitch-{label}.json", {
                "source":{"source_commit":sha},"rows":rows(label)})
            ir_rates=(48000,) if label=="before" else collect.RATES
            collect.save(out/f"ir-{label}.json",{
                "source":{"source_commit":sha},
                "rows":[{"sample_rate_hz":r,"voices":v,"status":"measured",
                         "ir_per_128_frame_block":100.0,"callgrind":[]}
                        for r in ir_rates for v in (1,8)]})
        d5=out/"d5"
        d5.mkdir(parents=True,exist_ok=True)
        renders={}
        for label in ("before","head"):
            original=d5/f"{label}.f32le";original.write_bytes(original_pcm)
            flac=d5/f"{label}.flac";flac.write_bytes(b"not real FLAC; synthetic test only")
            renders[label]={
                "original_pcm":{"file":original.name,"sha256":collect.digest(original)},
                "flac":{"file":flac.name,"sha256":collect.digest(flac),
                        "codec":{"codec_name":"flac","sample_rate":"48000",
                                 "channels":2,"bits_per_raw_sample":24}}}
        collect.save(d5/"manifest.json",{
            "sources":{"before":base_sha,"head":head_sha},
            "configuration":{"rate_hz":48000,"block_frames":128,"seconds":10,
                             "seed":37,"channels":2},
            "original_float_pcm_identical":True,"renders":renders})
        return base_sha,head_sha

    def test_full_known_answer_summary_never_promotes_raw_peak_to_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            base,head=self._fake_complete(out)
            result=collect.summarize(out,base,head)
            self.assertEqual(result["head_non48_output_rows_measured"],240)
            self.assertEqual(result["head_non48_output_rows_required"],240)
            self.assertTrue(result["48k_all_model_original_pcm_identical"])
            self.assertTrue(result["ir_48k_within_plus3"])
            self.assertTrue(result["d5_original_pcm_identical"])
            self.assertFalse(result["full_acceptance"])
            self.assertEqual(len(result["pitch_diagnostic_rows"]),240)
            self.assertTrue(all(r["status"]=="unmeasured_pending_design_ruling"
                                for r in result["pitch_diagnostic_rows"]))
            self.assertTrue(all(r["raw_estimator_delta_cents_vs48_diagnostic"]==0
                                for r in result["pitch_diagnostic_rows"]))
            self.assertIn("inharmonic",result["pitch_reserved_question"])

    def test_compiled_library_identity_and_d5_manifest_must_be_factual(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            self.assertEqual(collect.compiled_libraries(out)["status"],"unavailable")
            shared=out/"build/native/modules2/macro_oscillator/libws2_macro_oscillator.so"
            shared.parent.mkdir(parents=True,exist_ok=True)
            shared.write_bytes(b"synthetic library bytes, never a captured build")
            record=collect.compiled_libraries(out)
            self.assertEqual(record["status"],"measured")
            self.assertEqual(record["files"][0]["sha256"],collect.digest(shared))
            base,head=self._fake_complete(out)
            d5=out/"d5/manifest.json"
            stored=json.loads(d5.read_text())
            stored["original_float_pcm_identical"]=False
            collect.save(d5,stored)
            with self.assertRaisesRegex(ValueError,"contradicts hashes"):
                collect.summarize(out,base,head)
            stored["original_float_pcm_identical"]=True
            stored["renders"]["head"]["flac"]["codec"]["sample_rate"]="96000"
            collect.save(d5,stored)
            with self.assertRaisesRegex(ValueError,"media format provenance"):
                collect.summarize(out,base,head)

    def test_missing_rows_pcm_mutation_and_bad_pins_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            base,head=self._fake_complete(out)
            headfile=out/"pitch-head.json"
            obj=json.loads(headfile.read_text())
            obj["rows"].pop()
            collect.save(headfile,obj)
            with self.assertRaisesRegex(ValueError,"missing/duplicated"):
                collect.summarize(out,base,head)
            self._fake_complete(out,base,head)
            with self.assertRaisesRegex(ValueError,"source pin mismatch"):
                collect.summarize(out,base,"c"*40)
            path=out/"raw"/"canonical.f32le.gz"
            path.write_bytes(b"replaced evidence")
            with self.assertRaisesRegex(ValueError,"raw compressed SHA mismatch"):
                collect.summarize(out,base,head)


if __name__=="__main__":
    unittest.main()
