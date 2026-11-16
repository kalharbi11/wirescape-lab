# SPDX-License-Identifier: GPL-3.0-only
"""Coverage fixture inventory and fail-closed comparison, no devices or renderer."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"bench/golden"))
from render import coverage_manifest, sources, CENTERS_HZ
from compare import compare, parse_sound_changes
from inventory import registry, render_inventory

CASES=("chord-notes.json","notes-to-cv.json","spectral-cross.json")


def fixture():
    row={"sha256_float32_pcm":"a"*64,"fixture_sha256":"b"*64,
         "control_sha256":"c"*64,
         "rms_fs":0.1,"peak_fs":0.2,"contribution_verified":True,
         "control_peak_difference_fs":0.1,
         "third_octave_bands":[{"center_hz":round(c,6),"level_dbfs":-30.0} for c in CENTERS_HZ]}
    return {"machine":"linux-x64","sample_rate_hz":48000,"block_frames":128,
            "seconds":10,"seed":37,"channels":2,
            "patches":{"coverage/chord-notes.json":row,
                       "bundled/basics-01-first-tone.json":copy.deepcopy(row)}}


class CoverageTests(unittest.TestCase):
    def test_current_fixture_manifest_and_native_v2_event_cables(self):
        manifest=coverage_manifest()
        self.assertEqual(sorted(r["fixture"] for r in manifest["cases"]),list(CASES))
        root=ROOT/"bench/patches/coverage"
        for row in manifest["cases"]:
            data=json.loads((root/row["fixture"]).read_text())
            control=json.loads((root/row["control"]).read_text())
            self.assertEqual(data["format"],"wirescape.native.patch")
            self.assertEqual(data["version"],2)
            self.assertEqual(data["outputs"],control["outputs"])
            for case in (data,control):
                self.assertEqual(len({m["id"] for m in case["modules"]}),len(case["modules"]))
                self.assertTrue(case["outputs"])
                ids={m["id"] for m in case["modules"]}
                for edge in case["connections"]:
                    self.assertIn(edge["from"]["module"],ids)
                    self.assertIn(edge["to"]["module"],ids)
                    self.assertIn(edge["kind"],("signal","event"))
            self.assertTrue(set(row["targets"]) <= {m["module"] for m in data["modules"]})
            self.assertNotEqual(data["connections"],control["connections"])

    def test_sources_fail_on_missing_or_extra_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            coverage=root/"bench/patches/coverage"
            coverage.mkdir(parents=True)
            for name in CASES:
                (coverage/name).write_text("{}",encoding="utf-8")
            for control in (r["control"] for r in coverage_manifest()["cases"]):
                target=coverage/control
                target.parent.mkdir(exist_ok=True)
                target.write_text("{}",encoding="utf-8")
            base=ROOT
            self.assertEqual(len([k for k,p in sources(base,root) if k=="coverage"]),3)
            (coverage/"chord-notes.json").unlink()
            with self.assertRaisesRegex(RuntimeError,"fixture inventory mismatch"):
                sources(base,root)
            (coverage/"chord-notes.json").write_text("{}",encoding="utf-8")
            (coverage/"rogue.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"fixture inventory mismatch"):
                sources(base,root)

    def test_registry_and_bundled_patch_inventory_is_all_34(self):
        from inventory import registry, render_inventory
        modules=registry(ROOT)
        self.assertEqual(len(modules),34)
        self.assertIn("osc.out",modules)
        self.assertIn("midi.in",modules)
        self.assertIn("monitor",modules)
        self.assertIn("sound.spectral",modules)
        render={"engine_source_commit":"test-engine-sha",
                "fixture_source_commit":"test-fixture-sha",
                "machine":"linux-x64","cpu":"synthetic-known-answer",
                "patches":{}}
        for path in (ROOT/"apps/studio/patches").glob("*.json"):
            render["patches"]["bundled/"+path.name]={"rms_fs":0.0}
        for case in coverage_manifest()["cases"]:
            folder=ROOT/"bench/patches/coverage"
            render["patches"]["coverage/"+case["fixture"]]={
                "fixture_sha256":hashlib.sha256((folder/case["fixture"]).read_bytes()).hexdigest(),
                "control_sha256":hashlib.sha256((folder/case["control"]).read_bytes()).hexdigest(),
                "rms_fs":0.2,"peak_fs":0.3,
                "control_peak_difference_fs":0.1,"contribution_verified":True}
        facts=render_inventory(ROOT,render,"https://example.test/known-answer")
        self.assertEqual(facts["source_commit"],"test-engine-sha")
        self.assertEqual(facts["fixture_source_commit"],"test-fixture-sha")
        self.assertEqual(len(facts["modules"]),34)
        self.assertEqual(facts["bundled_patch_count"],24)
        self.assertEqual(facts["coverage_fixture_count"],3)
        self.assertEqual(facts["modules"]["essentials.chord"]["contribution_status"],
                         "measured_audio_bypass_intervention")
        self.assertEqual(facts["modules"]["essentials.notes_to_cv"]["contribution_status"],
                         "measured_audio_bypass_intervention")
        self.assertEqual(facts["modules"]["sound.spectral"]["contribution_status"],
                         "measured_audio_bypass_intervention")
        self.assertEqual(facts["modules"]["midi.in"]["contribution_status"],
                         "not_exercised_offline")
        self.assertEqual(facts["modules"]["osc.out"]["contribution_status"],
                         "bundled_presence_unverified")

    def test_bundled_probe_inventory_and_only_target_cables_removed(self):
        from probe_bundled import CASES,disable_module_edges
        modules=registry(ROOT)
        self.assertEqual(len(CASES),25)
        self.assertEqual(set(CASES)-set(modules),set())
        self.assertFalse({"osc.out","monitor"}&set(CASES))
        for target,name in CASES.items():
            with self.subTest(target=target,name=name):
                doc=json.loads((ROOT/"apps/studio/patches"/name).read_text())
                new,intervention,removed=disable_module_edges(doc,target)
                self.assertGreater(removed,0)
                self.assertEqual(doc["modules"],new["modules"])
                self.assertEqual(doc["outputs"],new["outputs"])
                target_nodes={m["id"] for m in doc["modules"] if m["module"]==target}
                removed_edges=[c for c in doc["connections"] if c not in new["connections"]]
                self.assertEqual(len(removed_edges),removed)
                for edge in removed_edges:
                    if target=="essentials.output":
                        self.assertIn(edge["to"]["module"],target_nodes)
                        self.assertEqual(intervention,"disconnect_inputs_to_output")
                    else:
                        self.assertIn(edge["from"]["module"],target_nodes)
                        self.assertEqual(intervention,"disconnect_module_output_edges")

    def test_missing_bundled_and_coverage_remain_failures_with_all_declared(self):
        for key in ("bundled/basics-01-first-tone.json","coverage/chord-notes.json"):
            for side in ("before","after"):
                with self.subTest(key=key,side=side):
                    before=fixture()
                    after=copy.deepcopy(before)
                    del (before if side=="before" else after)["patches"][key]
                    names=set(before["patches"])|set(after["patches"])
                    declared=parse_sound_changes("Sound-change: all — intended DSP",names)
                    row=compare(before,after,declared=declared)[key]
                    self.assertEqual(row["status"],"different")
                    self.assertIn("patch missing",row["reason"])

    def test_same_fixture_and_control_bytes_are_required_independently_of_pcm_hash(self):
        before=fixture()
        for changed_key in ("fixture_sha256","control_sha256"):
            after=copy.deepcopy(before)
            after["patches"]["coverage/chord-notes.json"][changed_key]="d"*64
            with self.subTest(key=changed_key):
                with self.assertRaisesRegex(ValueError,"fixture or bypass-control bytes differ"):
                    compare(before,after)
        self.assertEqual(compare(before,copy.deepcopy(before))
                         ["coverage/chord-notes.json"]["status"],"identical")


if __name__=="__main__":
    unittest.main()
