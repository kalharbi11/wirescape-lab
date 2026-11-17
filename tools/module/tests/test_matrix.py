# SPDX-License-Identifier: GPL-3.0-only
"""MT2 hosted, compiled SDK-template quick/full matrix and diagnostic regressions."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys
import time
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
sys.path.insert(0, str(MODULE))
import matrix  # noqa: E402
import wsmod  # noqa: E402

TEMPLATE = ROOT / json.loads((MODULE / "layout.json").read_text(encoding="utf-8"))["paths"]["template"]
EXPECTED_QUICK = {f"T{i}" for i in range(1, 10)} | {"T11"}
EXPECTED_FULL = {f"T{i}" for i in range(1, 14)}


class MatrixTests(unittest.TestCase):
    def invoke(self, *options, folder=None):
        cmd = [sys.executable, str(MODULE / "wsmod.py"), "test", str(folder or TEMPLATE),
               "--json", *options]
        started = time.monotonic()
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=240)
        elapsed = time.monotonic() - started
        self.assertFalse(proc.stderr.strip().startswith("Traceback"), proc.stderr)
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc.returncode, json.loads(proc.stdout), elapsed

    def test_real_template_quick_and_deterministic(self):
        first_code, first, seconds = self.invoke()
        self.assertEqual(first_code, 0, first)
        self.assertEqual(first["schema"], "wsmod/1")
        self.assertEqual(first["mode"], "quick")
        self.assertEqual(first["module"]["id"], "example.gain2")
        self.assertTrue(EXPECTED_QUICK.issubset({r["test"] for r in first["results"]}))
        self.assertEqual(first["summary"]["fail"], 0, first)
        for entry in first["results"]:
            if entry["status"] in ("fail", "warn"):
                self.assertTrue(all(entry[k] for k in ("what", "where", "fix")), entry)
        second_code, second, _ = self.invoke()
        self.assertEqual(second_code, 0, second)
        self.assertEqual(first, second)
        print("MT2 actual quick wall seconds:", round(seconds, 3))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(first))

    def test_real_template_full_and_report_only(self):
        code, report, seconds = self.invoke("--full")
        self.assertEqual(code, 0, report)
        self.assertEqual(report["mode"], "full")
        seen = {r["test"] for r in report["results"]}
        self.assertTrue(EXPECTED_FULL.issubset(seen), report)
        self.assertEqual(report["summary"]["fail"], 0, report)
        for test in ("T10", "T13"):
            self.assertTrue(any(r["test"] == test for r in report["results"]))
        print("MT2 actual full wall seconds:", round(seconds, 3))

    def test_real_stepped_parameter_constant_and_per_sample_buffers(self):
        # Real compiled SDK mutation: set a step without naming an ABI symbol.
        # Quick retains min/max; full enumerates the five values in both modes.
        with tempfile.TemporaryDirectory(prefix="wsmod-mt2-step-") as tmp:
            folder = Path(tmp) / "module"
            shutil.copytree(TEMPLATE, folder)
            file = folder / "module.cpp"
            source = file.read_text(encoding="utf-8")
            original = 'ws::param("gain","Gain",0,2,1)'
            stepped = 'ws::param("gain","Gain",0,2,1,"",3,0,0,4,.5)'
            self.assertEqual(source.count(original), 1)
            file.write_text(source.replace(original, stepped), encoding="utf-8")
            code, report, _ = self.invoke("--full", folder=folder)
            self.assertEqual(code, 0, report)
            rows = [r for r in report["results"] if r["test"] == "T11"]
            self.assertEqual(len(rows), 10, report)
            details = [r["what"] for r in rows]
            for label in ("minimum", "maximum", "step"):
                self.assertTrue(any(label in d for d in details), details)
            self.assertEqual(sum("per-sample" in d for d in details), 5)
            self.assertEqual(sum("constant" in d for d in details), 5)
            self.assertNotIn(str(folder.resolve()), json.dumps(report))
            self.assertTrue(all(r["where"]["param"] == "gain" for r in rows))

    def test_strict_report_only_warnings_never_fail(self):
        args = type("Args", (), {"keep_build": None, "full": True, "strict": True})()
        report = {"module": {"id": None, "folder": "template"}, "results": []}
        records = [
            {"test": "T1", "status": "pass", "detail": "valid",
             "where": {"rate": 48000}, "metrics": {}},
            {"test": "T10", "status": "warn", "detail": "denormal samples",
             "where": {"rate": 48000}, "metrics": {"value": 2}},
            {"test": "T13", "status": "warn", "detail": "block size variation",
             "where": {"rate": 48000}, "metrics": {"value": .01}},
        ]
        records.extend({"test": f"T{i}", "status": "pass", "detail": "ok",
                        "where": {"rate": 48000}, "metrics": {}}
                       for i in (2, 3, 4, 5, 6, 7, 8, 9, 11, 12))
        output = "\n".join(json.dumps(r) for r in records)
        built = {"state": "ok", "runner": Path("runner")}
        desc = subprocess.CompletedProcess([], 0, '{"id":"example.gain2"}')
        done = subprocess.CompletedProcess([], 0, output)
        with mock.patch.object(matrix, "build", return_value=built), \
             mock.patch.object(matrix, "run_command", side_effect=(desc, done)):
            self.assertEqual(matrix.run(ROOT, TEMPLATE, {}, json.loads(
                (MODULE / "messages.json").read_text()), args, report), 0)
        self.assertTrue(all(r["fix"] and r["where"] and r["what"]
                            for r in report["results"] if r["status"] == "warn"))

    def test_compile_and_runtime_failure_are_structured(self):
        args = type("Args", (), {"keep_build": None, "full": False, "strict": False})()
        messages = json.loads((MODULE / "messages.json").read_text())
        for state, expected in (({"state": "environment", "detail": "no generator"}, 4),
                                ({"state": "build", "detail": "compiler error"}, 3)):
            report = {"module": {"id": None}, "results": []}
            with mock.patch.object(matrix, "build", return_value=state):
                code = matrix.run(ROOT, TEMPLATE, {}, messages, args, report)
            self.assertEqual(code, expected)
            self.assertEqual(report["results"][0]["status"], "fail")
            self.assertTrue(all(report["results"][0][k] for k in ("what", "where", "fix")))

    def test_test_tree_abi_and_repository_path_isolation(self):
        # Include all tests, not only top-level sources; adapter is the sole
        # ABI owner and layout.json the sole holder of repo-relative paths.
        adapter = MODULE / "runner" / "abi_ws2.h"
        for source in [*MODULE.rglob("*.py"), *MODULE.glob("runner/*.cpp"),
                       *MODULE.glob("runner/*.h")]:
            if source == adapter:
                continue
            content = source.read_text(encoding="utf-8")
            for marker in ("ws" + "2_", "WS" + "2_"):
                self.assertNotIn(marker, content, source)
            self.assertNotRegex(content, r"\bnative/(?:sdk|include|modules|tests|voice)\b")
        self.assertIn("class HostModule", adapter.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
