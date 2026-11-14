# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic resource sampler, scaling logic and device-authorization tests."""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure import CpuSampler, ProcessStat, search_max_n, summary
from generate_scaling import scaling_patch

RUN = Path(__file__).resolve().parents[1] / "measure.py"


class SyntheticSamplerTests(unittest.TestCase):
    def test_cpu_and_memory_from_process_tree(self):
        s = CpuSampler()
        p = lambda pid, cpu, rss: ProcessStat(pid, 7., cpu, rss)
        first = s.observe([p(10, 1., 100), p(11, .5, 300)], 20.)
        second = s.observe([p(10, 1.2, 150), p(11, .6, 350)], 20.1)
        self.assertIsNone(first["cpu_percent"])
        self.assertAlmostEqual(second["cpu_percent"], 300.)
        self.assertEqual(second["rss_bytes"], 500)
        self.assertEqual(second["processes"], 2)
        self.assertAlmostEqual(summary([second])["cpu_max_percent"], 300.)

    def test_pid_reuse_does_not_count_old_cpu(self):
        s = CpuSampler()
        s.observe([ProcessStat(10, 1., 7., 8)], 5.)
        result = s.observe([ProcessStat(10, 2., 90., 10)], 5.1)
        self.assertEqual(result["cpu_percent"], 0.)

    def test_zero_or_backward_clock_is_not_divided(self):
        s = CpuSampler()
        s.observe([ProcessStat(1, 1., 1., 1)], 8.)
        self.assertIsNone(s.observe([ProcessStat(1, 1., 2., 2)], 8.)["cpu_percent"])

    def test_max_n_stops_at_first_xrun(self):
        probed = []
        got = search_max_n(lambda n: probed.append(n) or n < 8,
                           levels=(1, 2, 4, 8, 16, 32))
        self.assertEqual(got, 4)
        self.assertEqual(probed, [1, 2, 4, 8])

    def test_no_acceptable_level(self):
        self.assertIsNone(search_max_n(lambda n: False, levels=(1, 2, 4)))

    def test_midi_fixture_is_deterministic(self):
        from midi_fixture import fixture_bytes
        fixture = fixture_bytes()
        self.assertEqual(fixture[:4], b"MThd")
        self.assertEqual(fixture[14:18], b"MTrk")
        self.assertEqual(fixture.count(bytes((0x90, 48, 100))), 15)
        self.assertEqual(fixture.count(bytes((0x80, 48, 0))), 15)
        self.assertEqual(fixture, fixture_bytes())

    def test_wirescape_reference_patches_have_valid_endpoints(self):
        import json
        base = Path(__file__).resolve().parents[1] / "patches" / "wirescape"
        for name in ("mono", "poly8", "poly8-fx"):
            with self.subTest(name=name):
                patch = json.loads((base / (name + ".json")).read_text())
                self.assertEqual(patch["format"], "wirescape.native.patch")
                self.assertEqual(patch["version"], 2)
                ids = [m["id"] for m in patch["modules"]]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertLessEqual(len(ids), 64)
                for cable in patch["connections"]:
                    self.assertIn(cable["from"]["module"], ids)
                    self.assertIn(cable["to"]["module"], ids)
                for output in patch["outputs"]:
                    self.assertIn(output["module"], ids)
                if name != "mono":
                    voices = next(m for m in patch["modules"] if m["module"] == "midi.to_cv")
                    self.assertEqual(voices["parameters"]["voice_count"], 8)

    def test_scaling_graph_count_and_ports(self):
        for n in (1, 2, 4, 8):
            patch = scaling_patch(n)
            self.assertEqual(len(patch["modules"]), 6*n)
            self.assertEqual(len(patch["connections"]), 6*n - 1)
            self.assertEqual(len(set(m["id"] for m in patch["modules"])), 6*n)
            self.assertEqual(patch["outputs"][0]["bus_channel"], 0)
        with self.assertRaisesRegex(ValueError, "64-module"):
            scaling_patch(16)

    def test_live_requires_authorization_before_backend(self):
        proc = subprocess.run([sys.executable, str(RUN), "--pid", "1"],
                              text=True, capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--confirm-audio is required", proc.stderr)

    def test_engine_mode_rejects_device_authorization(self):
        proc = subprocess.run([sys.executable, str(RUN), "--engine",
                               str(RUN), "--confirm-audio"],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--engine is only supported", proc.stderr)

    def test_missing_engine_rejected_without_starting_process(self):
        proc = subprocess.run([sys.executable, str(RUN), "--dry-run",
                               "--engine", str(RUN.parent / "missing-binary")],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--engine must point to a built executable", proc.stderr)

    def test_dry_run_rejects_recording(self):
        proc = subprocess.run([sys.executable, str(RUN), "--dry-run",
                               "--record", "monitor"],
                              text=True, capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--dry-run prohibits", proc.stderr)


class SpectralTests(unittest.TestCase):
    def test_sine_thd_is_small(self):
        import numpy as np
        from analyse import tone_metrics
        rate = 48000
        t = np.arange(rate * 2) / rate
        x = .1 * np.sin(2 * np.pi * 440 * t)
        result = tone_metrics(x, rate, 440)
        self.assertLess(result["thd_percent"], .01)
        self.assertLess(result["nonharmonic_floor_db_relative"], -40.)

    def test_recorded_gate_edge(self):
        import numpy as np
        import soundfile as sf
        import tempfile
        from analyse import analyse_recording
        with tempfile.TemporaryDirectory() as directory:
            f = Path(directory) / "synthetic.wav"
            x = np.zeros(48000, dtype=np.float32)
            x[12000:] = .7
            sf.write(f, x, 48000)
            result = analyse_recording(f, gate_times=[.25])
            self.assertTrue(result["gate_edge_clicks"]["0.25"])

    def test_click_edge(self):
        import numpy as np
        from analyse import clicks
        x = np.zeros(24000)
        x[12000:] = .8
        self.assertTrue(any(abs(t - .25) < .001 for t in clicks(x, 48000)))


if __name__ == "__main__":
    unittest.main()
