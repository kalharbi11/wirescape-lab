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
from inventory import EXPERIMENTAL, allowed_ids, golden_ids, registry, render_inventory

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
    def test_measured_coverage_rejects_silence_and_unrelated_audio(self):
        from unittest.mock import patch
        import numpy as np
        import render
        path=ROOT/"bench/patches/coverage/spectral-cross.json"
        control=ROOT/"bench/patches/coverage/controls/spectral-cross-bypass.json"
        sound=np.array([[0.0,0.0],[0.25,0.25],[0.0,0.0]],dtype=np.float32)
        changed=np.array([[0.0,0.0],[0.1,0.1],[0.0,0.0]],dtype=np.float32)
        unchanged=[(b"one",sound),(b"one",sound),(b"control",sound)]
        with patch.object(render,"render_one",side_effect=unchanged), \
             patch.object(render,"levels",return_value={"rms_fs":0.1,"peak_fs":0.25}):
            with self.assertRaisesRegex(AssertionError,"no observable contribution"):
                render.measure(Path("/unused/renderer"),path,"coverage",ROOT,control_patch=control)
        with patch.object(render,"render_one",side_effect=[(b"one",sound),(b"one",sound)]), \
             patch.object(render,"levels",return_value={"rms_fs":0.0,"peak_fs":0.0}):
            with self.assertRaisesRegex(AssertionError,"covered path is silent"):
                render.measure(Path("/unused/renderer"),path,"coverage",ROOT,control_patch=control)
        with patch.object(render,"render_one",
                          side_effect=[(b"one",sound),(b"one",sound),(b"control",changed)]), \
             patch.object(render,"levels",return_value={"rms_fs":0.1,"peak_fs":0.25}):
            row=render.measure(Path("/unused/renderer"),path,"coverage",ROOT,control_patch=control)
            self.assertTrue(row["contribution_verified"])
            self.assertAlmostEqual(row["control_peak_difference_fs"],0.15,places=6)
            self.assertEqual(row["fixture_sha256"],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(row["control_sha256"],hashlib.sha256(control.read_bytes()).hexdigest())

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

    def test_manifest_cannot_remove_required_coverage_case(self):
        from unittest.mock import patch
        import render
        with tempfile.TemporaryDirectory() as temp:
            fake=Path(temp)
            folder=fake/"bench/golden"
            folder.mkdir(parents=True)
            original=coverage_manifest()
            broken=copy.deepcopy(original)
            broken["cases"]=[case for case in broken["cases"]
                             if case["fixture"]!="chord-notes.json"]
            (folder/"coverage_manifest.json").write_text(json.dumps(broken),encoding="utf-8")
            with patch.object(render,"ROOT",fake):
                with self.assertRaisesRegex(ValueError,"removes required fixtures"):
                    render.coverage_manifest()

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

    def test_base_without_new_fixtures_uses_exact_head_fixture_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)/"old-engine"
            head=Path(temp)/"new-fixtures"
            (base/"apps/studio/patches").mkdir(parents=True)
            (base/"apps/studio/patches/old.json").write_text("{}",encoding="utf-8")
            (head/"bench/patches/coverage/controls").mkdir(parents=True)
            for name in CASES:
                (head/"bench/patches/coverage"/name).write_bytes(
                    (ROOT/"bench/patches/coverage"/name).read_bytes())
            for case in coverage_manifest()["cases"]:
                (head/"bench/patches/coverage"/case["control"]).write_bytes(
                    (ROOT/"bench/patches/coverage"/case["control"]).read_bytes())
            entries=sources(base,head)
            self.assertEqual([scope for scope,_ in entries],
                             ["bundled","coverage","coverage","coverage"])
            self.assertEqual([path.name for scope,path in entries if scope=="coverage"],
                             [row["fixture"] for row in coverage_manifest()["cases"]])
            self.assertTrue(all(path.is_relative_to(head)
                                for scope,path in entries if scope=="coverage"))

    def test_exact_golden_and_experimental_inventory(self):
        from inventory import registry, render_inventory
        modules=registry(ROOT)
        self.assertEqual(set(modules), allowed_ids(ROOT))
        self.assertEqual(len(golden_ids(ROOT)), 34)
        self.assertEqual(EXPERIMENTAL, {"essentials.cv_to_notes", "essentials.gate_delay"})
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
        self.assertEqual(set(facts["modules"]), allowed_ids(ROOT))
        self.assertEqual(facts["modules"]["essentials.cv_to_notes"]["contribution_status"], "not_exercised_offline")
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

    def test_r3_event_path_citations_and_both_workflow_path_filters(self):
        # The six event/control side effects are NOT PCM golden coverage.
        evidence=json.loads((ROOT/"bench/golden/event_path_evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["contract"],"M0 r2 R3")
        expected={"midi.in","midi.to_cv","midi.cc_to_cv","osc.in","osc.out","monitor"}
        self.assertEqual({r["module_id"] for r in evidence["rows"]},expected)
        self.assertEqual(len(evidence["rows"]),6)
        table=(ROOT/"facts/dsp/coverage/README.md").read_text(encoding="utf-8")
        for row in evidence["rows"]:
            with self.subTest(module=row["module_id"]):
                self.assertEqual(row["classification"],"event-path")
                source=(ROOT/row["test_file"])
                self.assertTrue(source.is_file())
                lines=source.read_text(encoding="utf-8").splitlines()
                self.assertLessEqual(1,row["line_start"])
                self.assertLessEqual(row["line_start"],row["line_end"])
                self.assertLessEqual(row["line_end"],len(lines))
                observed="\n".join(lines[row["line_start"]-1:row["line_end"]])
                self.assertIn(row["assertion"],observed)
                self.assertIn(f"| {row['module_id']} |",table)
                matrix_row=next(line for line in table.splitlines()
                                if line.startswith(f"| {row['module_id']} |"))
                cells=[cell.strip() for cell in matrix_row.strip().strip("|").split("|")]
                self.assertEqual(cells[4],"event-path")
                self.assertIn(row["test_target"],cells[5])
                self.assertIn(evidence["test_source_commit"],cells[5])
        for machine in ("linux-x64","linux-arm64","windows-x64"):
            source=ROOT/f"facts/dsp/coverage/ci-{machine}-modules-2026-11-15.json"
            data=json.loads(source.read_text(encoding="utf-8"))
            self.assertEqual(data["source_commit"],evidence["test_source_commit"])
            self.assertEqual(len(data["modules"]),34)
            audio={key for key,record in data["modules"].items()
                   if record["contribution_status"].startswith("measured_")}
            self.assertEqual(len(audio),28)
            self.assertEqual(set(data["modules"])-audio,expected)
        workflow=(ROOT/".github/workflows/golden-renders.yml").read_text(encoding="utf-8")
        pr=workflow.index("  pull_request:")
        push=workflow.index("  push:")
        dispatch=workflow.index("  workflow_dispatch:")
        entry='      - "bench/patches/coverage/**"'
        self.assertIn(entry,workflow[pr:push])
        self.assertIn(entry,workflow[push:dispatch])
        self.assertEqual(workflow.count(entry),2)

    def test_missing_bundled_and_coverage_remain_failures_with_all_declared(self):
        for key in ("bundled/basics-01-first-tone.json",
                    "coverage/chord-notes.json","owner/owner-demo.json"):
            for side in ("before","after"):
                with self.subTest(key=key,side=side):
                    before=fixture()
                    before["patches"]["owner/owner-demo.json"] = copy.deepcopy(
                        before["patches"]["bundled/basics-01-first-tone.json"])
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
