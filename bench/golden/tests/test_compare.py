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


if __name__=="__main__":
    unittest.main()
