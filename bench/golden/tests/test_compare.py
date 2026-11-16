# SPDX-License-Identifier: GPL-3.0-only
"""Golden comparison checks using deliberately altered, device-free PCM."""
import copy
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from compare import compare, first_float32_difference
from render import CENTERS_HZ, events_for_patch


def fixture():
    row={"sha256_float32_pcm":"a"*64,"frames":480000,"channels":2,
         "peak_fs":0.2,"rms_fs":0.1,"dc_fs":0,
         "third_octave_bands":[{"center_hz":round(c,6),"level_dbfs":-45.0}
                               for c in CENTERS_HZ]}
    return dict(machine="linux-x64",sample_rate_hz=48000,block_frames=128,
                seconds=10,seed=37,channels=2,patches={"bundled/fixture.json":row})


def wav(path,values):
    data=struct.pack("<"+"f"*len(values),*values)
    header=b"RIFF"+struct.pack("<I",36+len(data))+b"WAVEfmt "
    header+=struct.pack("<IHHIIHH",16,3,2,48000,48000*8,8,32)
    header+=b"data"+struct.pack("<I",len(data))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(header+data)


class GoldenCompareTests(unittest.TestCase):
    def test_identical_hash(self):
        before=fixture()
        rows=compare(before,copy.deepcopy(before))
        self.assertEqual(rows["bundled/fixture.json"]["status"],"identical")
        self.assertEqual(rows["bundled/fixture.json"]["largest_band_difference_db"],0)

    def test_altered_hash_and_band_is_different_default(self):
        before=fixture()
        after=copy.deepcopy(before)
        entry=after["patches"]["bundled/fixture.json"]
        entry["sha256_float32_pcm"]="b"*64
        entry["third_octave_bands"][7]["level_dbfs"]=-44.6
        rows=compare(before,after)
        record=rows["bundled/fixture.json"]
        self.assertEqual(record["status"],"different")
        self.assertAlmostEqual(record["largest_band_difference_db"],.4)
        self.assertIsNone(record["first_differing_sample_index"])
        self.assertEqual(compare(before,after,.5)["bundled/fixture.json"]["status"],
                         "within tolerance")

    def test_altered_wav_reports_exact_sample_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a.wav",Path(tmp)/"b.wav"
            wav(a,[0.,0.,0.,0.,0.,0.])
            wav(b,[0.,0.,0.,1.,0.,0.])
            self.assertEqual(first_float32_difference(a,b),3)

    def test_cli_exits_nonzero_for_different(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a.json",Path(tmp)/"b.json"
            before=fixture()
            after=copy.deepcopy(before)
            after["patches"]["bundled/fixture.json"]["sha256_float32_pcm"]="b"*64
            a.write_text(json.dumps(before))
            b.write_text(json.dumps(after))
            result=subprocess.run([sys.executable,str(HERE/"compare.py"),str(a),str(b)],
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertIn("different",result.stdout)
            self.assertIn("first differing sample index=unavailable",result.stdout)

    def test_note_script_mirrors_offline_bundled_fixture(self):
        patch={"modules":[{"id":4,"module":"host.keyboard"},
                          {"id":6,"module":"essentials.output"}]}
        self.assertEqual(events_for_patch(patch),[
            {"frame":0,"type":"noteOn","node":4,"key":60},
            {"frame":240000,"type":"noteOff","node":4,"key":60}])


    def test_missing_patch_is_different_and_cli_fails(self):
        before=fixture()
        after=copy.deepcopy(before)
        del after["patches"]["bundled/fixture.json"]
        self.assertEqual(compare(before,after)["bundled/fixture.json"]["status"],"different")
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/"a.json",Path(temp)/"b.json"
            a.write_text(json.dumps(before),encoding="utf-8")
            b.write_text(json.dumps(after),encoding="utf-8")
            p=subprocess.run([sys.executable,str(HERE/"compare.py"),str(a),str(b)],
                             capture_output=True,text=True)
            self.assertEqual(p.returncode,1,p.stderr)
            self.assertIn("patch missing",p.stdout)

    def test_within_tolerance_cli_exit_zero(self):
        before=fixture()
        after=copy.deepcopy(before)
        row=after["patches"]["bundled/fixture.json"]
        row["sha256_float32_pcm"]="b"*64
        row["third_octave_bands"][4]["level_dbfs"]=-44.995
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/"a.json",Path(temp)/"b.json"
            a.write_text(json.dumps(before),encoding="utf-8")
            b.write_text(json.dumps(after),encoding="utf-8")
            p=subprocess.run([sys.executable,str(HERE/"compare.py"),str(a),str(b),
                              "--tolerance-db","0.01"],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn("within tolerance",p.stdout)

    def test_named_and_all_declarations_with_required_reason(self):
        from compare import parse_sound_changes
        names={"bundled/fixture.json","owner/other.json"}
        self.assertEqual(parse_sound_changes("Sound-change: fixture.json — intended change",names),
                         {"bundled/fixture.json"})
        self.assertEqual(parse_sound_changes("Sound-change: all — change accepted",names),names)
        self.assertEqual(parse_sound_changes("No sound change",names),set())
        for bad in ("Sound-change: fixture.json", "Sound-change: unknown.json — no match",
                    "Sound-change: fixture.json — ", "Sound-change: , — empty name"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_sound_changes(bad,names)

    def test_undeclared_sample_difference_then_declaration_with_wav_artifacts(self):
        from compare import parse_sound_changes
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            before=fixture()
            after=copy.deepcopy(before)
            name="bundled/fixture.json"
            after["patches"][name]["sha256_float32_pcm"]="b"*64
            after["patches"][name]["third_octave_bands"][0]["level_dbfs"]=-44.2
            wa=root/"before"/"bundled/fixture.wav"
            wb=root/"after"/"bundled/fixture.wav"
            wav(wa,[0.0,0.0,0.0,0.0,0.0,0.0])
            wav(wb,[0.0,0.0,0.0,0.5,0.0,0.0])
            a,b=root/"a.json",root/"b.json"
            a.write_text(json.dumps(before),encoding="utf-8")
            b.write_text(json.dumps(after),encoding="utf-8")
            cmd=[sys.executable,str(HERE/"compare.py"),str(a),str(b),
                 "--before-wavs",str(root/"before"),"--after-wavs",str(root/"after"),
                 "--require-wavs","--difference-wavs",str(root/"diff"),
                 "--json-out",str(root/"report.json")]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            item=json.loads((root/"report.json").read_text())["patches"][name]
            self.assertEqual(item["status"],"different")
            self.assertEqual(item["first_differing_sample_index"],3)
            self.assertEqual(item["first_differing_frame_index"],1)
            self.assertAlmostEqual(item["first_differing_time_s"],1/48000)
            self.assertAlmostEqual(item["peak_sample_difference_fs"],.5)
            self.assertTrue((root/"diff"/"before"/"bundled/fixture.wav").is_file())
            self.assertTrue((root/"diff"/"after"/"bundled/fixture.wav").is_file())
            event=root/"event.json"
            event.write_text(json.dumps({"pull_request":{"body":
               "Sound-change: fixture.json — deliberate offline amplitude perturbation"}}),encoding="utf-8")
            declared=subprocess.run([*cmd,"--pr-event",str(event)],capture_output=True,text=True)
            self.assertEqual(declared.returncode,0,declared.stderr)
            self.assertIn("declared;",declared.stdout)
            self.assertEqual(json.loads((root/"report.json").read_text())["declared_count"],1)
            self.assertEqual(parse_sound_changes(event.read_text(),{name}),set())

    def test_missing_patch_is_unconditionally_different_even_when_declared(self):
        """Named or all declarations must never conceal removed or newly added patches."""
        from compare import parse_sound_changes
        name="bundled/fixture.json"
        for missing in ("before", "after"):
            for declaration in (
                    "Sound-change: fixture.json — intentional sound update",
                    "Sound-change: all — intentional global sound update"):
                with self.subTest(missing=missing,declaration=declaration):
                    before=fixture()
                    after=copy.deepcopy(before)
                    del (before if missing=="before" else after)["patches"][name]
                    declared=parse_sound_changes(declaration,{name})
                    row=compare(before,after,declared=declared)[name]
                    self.assertEqual(row["status"],"different")
                    self.assertEqual(row["reason"],"patch missing from one reference")
                    with tempfile.TemporaryDirectory() as temp:
                        root=Path(temp)
                        a,b,event,report=(root/"before.json",root/"after.json",
                                          root/"event.json",root/"result.json")
                        a.write_text(json.dumps(before),encoding="utf-8")
                        b.write_text(json.dumps(after),encoding="utf-8")
                        event.write_text(json.dumps({"pull_request":{"body":declaration}}),
                                         encoding="utf-8")
                        output=subprocess.run(
                            [sys.executable,str(HERE/"compare.py"),str(a),str(b),
                             "--pr-event",str(event),"--json-out",str(report)],
                            capture_output=True,text=True)
                        self.assertEqual(output.returncode,1,output.stderr)
                        self.assertIn(f"{name}: different;",output.stdout)
                        data=json.loads(report.read_text(encoding="utf-8"))
                        self.assertEqual(data["different_count"],1)
                        self.assertEqual(data["declared_count"],0)
                        self.assertEqual(data["patches"][name]["status"],"different")

    def test_wav_and_json_hashes_must_agree_in_both_directions_cli(self):
        """Known-answer bytes disallow both inconsistent hash/WAV combinations."""
        name="bundled/fixture.json"
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            wa=root/"before"/"bundled/fixture.wav"
            wb=root/"after"/"bundled/fixture.wav"
            a,b=root/"a.json",root/"b.json"
            for case in ("same_hash_different_wavs","different_hash_same_wavs"):
                with self.subTest(case=case):
                    before=fixture()
                    after=copy.deepcopy(before)
                    if case=="same_hash_different_wavs":
                        # Hashes claim identical, actual sample 2 disagrees.
                        wav(wa,[0.0,0.0,0.0,0.0])
                        wav(wb,[0.0,0.0,0.25,0.0])
                        expected="hashes are identical but WAVs differ"
                    else:
                        # Hashes claim changed, actual four samples are identical.
                        after["patches"][name]["sha256_float32_pcm"]="b"*64
                        wav(wa,[0.0,0.0,0.0,0.0])
                        wav(wb,[0.0,0.0,0.0,0.0])
                        expected="hashes differ but WAVs are identical"
                    a.write_text(json.dumps(before),encoding="utf-8")
                    b.write_text(json.dumps(after),encoding="utf-8")
                    with self.assertRaisesRegex(ValueError,expected):
                        compare(before,after,raw_before=root/"before",
                                raw_after=root/"after",require_wavs=True)
                    output=subprocess.run(
                        [sys.executable,str(HERE/"compare.py"),str(a),str(b),
                         "--before-wavs",str(root/"before"),
                         "--after-wavs",str(root/"after"),"--require-wavs"],
                        capture_output=True,text=True)
                    self.assertEqual(output.returncode,2,output.stdout+output.stderr)
                    self.assertIn(expected,output.stderr)

    def test_consistent_json_and_wav_equality_is_identical(self):
        before=fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for side in ("before","after"):
                wav(root/side/"bundled/fixture.wav",[0.0,0.0,0.25,0.0])
            row=compare(before,copy.deepcopy(before),
                        raw_before=root/"before",raw_after=root/"after",
                        require_wavs=True)["bundled/fixture.json"]
            self.assertEqual(row["status"],"identical")
            self.assertIsNone(row["first_differing_sample_index"])

    def test_require_wavs_rejects_missing_file(self):
        before=fixture()
        after=copy.deepcopy(before)
        after["patches"]["bundled/fixture.json"]["sha256_float32_pcm"]="b"*64
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaisesRegex(ValueError,"WAV missing"):
                compare(before,after,raw_before=root/"before",
                        raw_after=root/"after",require_wavs=True)


if __name__=="__main__":
    unittest.main()
