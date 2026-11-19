# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("compare", Path(__file__).resolve().parents[2] / "bench/compare_bench.py")
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "benchmark.json"
        self.data = {"rows": [{"name": n, "mean_ns": 999,
                              "repetition_means_ns": [v, v * 100, v, v / 2, v]}
                             for n, v in zip(("abi2_mono", "abi2_poly8", "abi2_eight_mono",
                                              "abi2_modulated", "vcf_constant", "vcf_audio_rate_cutoff"),
                                             (105, 800, 800, 210, 100, 120))]}

    def run_cli(self, *args):
        self.path.write_text(json.dumps(self.data))
        with redirect_stdout(StringIO()) as output, redirect_stderr(StringIO()):
            result = compare.main(["--head", str(self.path), *args])
        return result, output.getvalue()

    def test_medians_ratios_and_delta(self):
        self.path.write_text(json.dumps(self.data))
        values = compare.load(self.path)
        self.assertEqual(values["abi2_mono"], 105)
        self.assertEqual(values["poly8_vs_eight_mono_ratio"], 1.0)
        self.assertNotIn("mono_ratio", values)
        self.assertIn("+0.00%", compare.table(values, values))
        self.assertEqual(self.run_cli("--base", str(self.path), "--gate")[0], 0)

    def test_each_gate_and_report_only(self):
        for index in (1,):
            original = self.data["rows"][index]["repetition_means_ns"]
            self.data["rows"][index]["repetition_means_ns"] = [10000] * 5
            self.assertEqual(self.run_cli("--gate")[0], 1)
            self.assertEqual(self.run_cli()[0], 0)
            self.data["rows"][index]["repetition_means_ns"] = original

    def test_historical_abi1_base_row_retired_and_head_rejects_it(self):
        legacy = {"name": "abi1_mono", "repetition_means_ns": [100] * 5}
        with tempfile.TemporaryDirectory() as tmp:
            historic = Path(tmp) / "historical.json"
            historic.write_text(json.dumps({"rows": self.data["rows"] + [legacy]}))
            current = self.path
            current.write_text(json.dumps(self.data))
            table = compare.table(compare.load(current), compare.load(historic, historical=True))
            self.assertNotIn("abi1", table)
            with self.assertRaisesRegex(ValueError, "exact six"):
                compare.load(historic)

    def test_bad_input(self):
        for invalid in ([1] * 4, [float("nan")] * 5, [0] * 5):
            self.data["rows"][0]["repetition_means_ns"] = invalid
            with self.assertRaises(SystemExit):
                self.run_cli()
        self.data["rows"] = []
        with self.assertRaises(SystemExit):
            self.run_cli()

    def test_mismatched_rows(self):
        with self.assertRaises(ValueError):
            compare.table({"x": 1}, {"y": 1})
