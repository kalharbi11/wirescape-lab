# SPDX-License-Identifier: GPL-3.0-only
"""Offline MT1 mutation tests; no product edits, sockets or downloads."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
sys.path.insert(0, str(MODULE))
import check  # noqa: E402

LAYOUT = json.loads((MODULE / "layout.json").read_text(encoding="utf-8"))
MESSAGES = json.loads((MODULE / "messages.json").read_text(encoding="utf-8"))


class ModuleToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "module"
        template = ROOT / LAYOUT["paths"]["template"]
        if not template.is_dir():
            self.skipTest("actual SDK template not available; cannot assert native template green")
        shutil.copytree(template, self.folder)

    def check(self, folder=None, *extra):
        command = [sys.executable, str(MODULE / "wsmod.py"), "check", str(folder or self.folder),
                   "--json", *extra]
        response = subprocess.run(command, capture_output=True, text=True, check=False,
                                  timeout=240, stdin=subprocess.DEVNULL)
        self.assertTrue(response.stdout.strip(), response.stderr)
        return response.returncode, json.loads(response.stdout)

    def mutate(self, transform):
        source = self.folder / "module.cpp"
        previous = source.read_text(encoding="utf-8")
        changed = transform(previous)
        self.assertNotEqual(changed, previous)
        source.write_text(changed, encoding="utf-8")

    def assert_failure(self, code, expected=1):
        exit_code, report = self.check()
        self.assertEqual(exit_code, expected, report)
        matches = [r for r in report["results"] if r["test"] == code]
        self.assertTrue(any(r["status"] == "fail" for r in matches), report)
        for result in report["results"]:
            if result["status"] in ("fail", "warn"):
                self.assertTrue(result["what"] and result["where"] and result["fix"], result)
        return report

    def test_valid_template_static_and_actual_describe(self):
        code, report = self.check()
        self.assertEqual(code, 0, report)
        self.assertEqual(report["module"]["id"], "example.gain2")
        for number in ("C1", "C2", "C3", "C4", "C5"):
            self.assertTrue(any(x["test"] == number and x["status"] == "pass"
                                for x in report["results"]), report)
        self.assertEqual(report["summary"]["fail"], 0)

    def test_c1_module_cpp_missing_in_existing_folder(self):
        (self.folder / "module.cpp").unlink()
        self.assert_failure("C1")

    def test_c1_registration_missing(self):
        self.mutate(lambda s: re.sub(r"WS_REGISTER_MODULE\s*\([^\n]*\)", "", s))
        self.assert_failure("C1")

    def test_c1_duplicate_registration(self):
        self.mutate(lambda s: s + "\nWS_REGISTER_MODULE(Duplicate)\n")
        self.assert_failure("C1")

    def test_c2_missing_spdx(self):
        self.mutate(lambda s: re.sub(r"SPDX-License-Identifier:\s*[\w.-]+", "missing", s, count=1))
        self.assert_failure("C2")

    def test_c3_banned_include(self):
        self.mutate(lambda s: s.replace("\n", "\n#include <vector>\n", 1))
        self.assert_failure("C3")

    def test_c3_tests_cpp_exempt(self):
        (self.folder / "tests.cpp").write_text(
            "// SPDX-License-Identifier: MIT\n#include <vector>\n", encoding="utf-8")
        code, report = self.check()
        self.assertEqual(code, 0, report)
        self.assertFalse(any(x["test"] == "C3" and x["status"] == "fail"
                             for x in report["results"]))

    def test_c4_bad_descriptor_id(self):
        self.mutate(lambda s: s.replace('"example.gain2"', '"Invalid-ID"'))
        self.assert_failure("C4")

    def test_c4_param_initial_outside_range(self):
        # Both the current SDK template and the isolated ABI fixture use this
        # literal range; if it changes, fail rather than silently bypass C4.
        def broken(source):
            if '"gain","Gain",0,2,1' in source:
                return source.replace('"gain","Gain",0,2,1', '"gain","Gain",0,2,5')
            return source.replace('"gain","Gain","",0,2,1', '"gain","Gain","",0,2,5')
        self.mutate(broken)
        self.assert_failure("C4")

    def test_c5_port_id_mismatch(self):
        metadata = self.folder / "module.json"
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        payload["inputs"] = {"invalid_port": "signal"}
        metadata.write_text(json.dumps(payload), encoding="utf-8")
        report = self.assert_failure("C5")
        self.assertTrue(any("inputs ids" in r["what"] for r in report["results"]
                            if r["test"] == "C5"))

    def test_missing_folder_code_two_and_no_machine_paths(self):
        missing = self.folder.parent / "absent"
        proc = subprocess.run([sys.executable, str(MODULE / "wsmod.py"),
                               "check", str(missing), "--json"],
                              capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(proc.returncode, 2)
        report = json.loads(proc.stdout)
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["results"][0]["test"], "USAGE")
        self.assertNotIn(str(self.folder.parent), proc.stdout)
        self.assertTrue(all(report["results"][0][field] for field in ("what", "where", "fix")))

    def test_build_error_never_leaks_absolute_source_path(self):
        self.mutate(lambda source: '#include "mt1_missing_header_for_diagnostic.h"\n' + source)
        report = self.assert_failure("BUILD", expected=3)
        output = json.dumps(report)
        self.assertNotIn(str(self.folder.resolve()), output)
        self.assertNotIn(str(ROOT.resolve()), output)
        self.assertIn("mt1_missing_header_for_diagnostic.h", output)

    def test_c5_metadata_mismatch(self):
        metadata = self.folder / "module.json"
        value = json.loads(metadata.read_text(encoding="utf-8"))
        value["name"] = "Wrong name"
        metadata.write_text(json.dumps(value), encoding="utf-8")
        self.assert_failure("C5")

    def test_c5_malformed_json(self):
        (self.folder / "module.json").write_text("{bad", encoding="utf-8")
        self.assert_failure("C5")

    def test_build_failure_exit_three_with_fix(self):
        self.mutate(lambda s: s + "\n#error deliberate_module_error\n")
        self.assert_failure("BUILD", expected=3)

    def test_runner_counts_only_module_allocations(self):
        # The MT2 test writer cannot edit this ABI bridge. A synthetic fixture
        # proves host-side vector staging is outside the measured callback.
        if not shutil.which("c++"):
            self.skipTest("C++17 driver not installed")
        runner = MODULE / "runner" / "abi_ws2.h"
        counter = ROOT / LAYOUT["paths"]["allocation_counter"]
        if not counter.is_file():
            self.skipTest("reused allocation counter source unavailable")
        sample = Path(self.temp.name) / "measure.cpp"
        sample.write_text("""// SPDX-License-Identifier: GPL-3.0-only
#include "abi_ws2.h"
#include <cstdint>
int main(int argc, char**) {
    HostModule module;
    if (!module.describe().errors.empty() || module.create(48000.0, 17, 1) != 0) return 2;
    HostBlock block;
    block.frames = 17;
    block.channels = 1;
    std::uint64_t allocations = 999;
    if (module.process(block, &allocations) != 0) return 3;
    if (allocations != (argc > 1 ? 1u : 0u)) return 4;
    module.reset(&allocations);
    if (allocations != 0) return 5;
    return 0;
}
""", encoding="utf-8")
        executable = Path(self.temp.name) / "measure"
        command = [shutil.which("c++"), "-std=c++17", "-O0", "-I", str(runner.parent),
                   "-I", str(ROOT / LAYOUT["paths"]["abi"]),
                   "-I", str(ROOT / LAYOUT["paths"]["allocation_include"]),
                   str(sample), str(self.folder / "module.cpp"), str(counter),
                   "-o", str(executable)]
        native = subprocess.run(command, capture_output=True, text=True,
                                check=False, timeout=90)
        self.assertEqual(native.returncode, 0, native.stderr)
        self.assertEqual(subprocess.run([str(executable)], check=False,
                                        timeout=15).returncode, 0)

        # A volatile write prevents the compiler from eliminating new/delete.
        source = (self.folder / "module.cpp").read_text(encoding="utf-8")
        changed = re.sub(r"(static int process\([^)]*\)\s*\{)\s*return [A-Z0-9_]+;",
                         r"\1 static void* volatile sink = nullptr; sink = new char[16]; return 0;",
                         source, count=1)
        if changed == source:
            self.skipTest("synthetic ABI fixture lacks a directly mutable process body")
        (self.folder / "module.cpp").write_text(changed, encoding="utf-8")
        rebuilt = subprocess.run(command, capture_output=True, text=True,
                                 check=False, timeout=90)
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
        self.assertEqual(subprocess.run([str(executable), "expect-one"], check=False,
                                        timeout=15).returncode, 0)

    def test_c6_advisory_even_in_strict(self):
        # Exercises the decision function directly, independently of compiler presence.
        class Args:
            keep_build = Path(self.temp.name) / "c6"
            strict = True
        result = {"module": {"folder": "module"}, "results": []}
        with mock.patch.object(check, "portable_symbols", return_value={
            "native": "compiled", "cross": "unavailable",
            "symbols": {"heap_symbols": ["malloc"]}}):
            check.advisory_check(ROOT, self.folder, LAYOUT, MESSAGES, Args, result)
        self.assertEqual(result["results"][0]["test"], "C6")
        self.assertEqual(result["results"][0]["status"], "warn")
        self.assertTrue(all(result["results"][0][x] for x in ("what", "where", "fix")))

    def test_environment_missing_gives_code_four(self):
        class Args:
            keep_build = None
            strict = False
        result = {"module": {"folder": "module"}, "results": []}
        with mock.patch.object(check, "build", return_value={"state": "environment", "detail": "no cmake"}), \
             mock.patch.object(check, "portable_symbols", return_value={"native": "unavailable", "cross": "unavailable", "symbols": {}}):
            code = check.run(ROOT, self.folder, LAYOUT, MESSAGES, Args, result)
        self.assertEqual(code, 4)
        self.assertTrue(any(x["test"] == "ENV" and x["status"] == "fail" for x in result["results"]))

    def test_check_json_is_byte_identical_and_paths_not_exposed(self):
        code_a, first = self.check()
        code_b, second = self.check()
        self.assertEqual(code_a, 0)
        self.assertEqual(code_b, 0)
        self.assertEqual(first, second)
        self.assertNotIn(str(self.folder.resolve()), json.dumps(first))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(first))

    def test_mt2_and_mt3_stubs_do_not_fabricate_success(self):
        for stage in ("test", "render"):
            proc = subprocess.run([sys.executable, str(MODULE / "wsmod.py"),
                                   stage, str(self.folder), "--json"],
                                  capture_output=True, text=True, check=False, timeout=15)
            self.assertEqual(proc.returncode, 4)
            result = json.loads(proc.stdout)
            self.assertEqual(result["exit_code"], 4)
            self.assertEqual(result["results"][0]["status"], "skip")

    def test_abi_and_layout_source_isolation(self):
        abi = MODULE / "runner" / "abi_ws2.h"
        self.assertTrue(abi.exists())
        for source in [*MODULE.glob("*.py"), *MODULE.glob("runner/*.cpp"),
                       *MODULE.glob("runner/*.h")]:
            if source == abi:
                continue
            text = source.read_text(encoding="utf-8")
            for prefix in ("ws" + "2_", "WS" + "2_"):
                self.assertNotIn(prefix, text)
            self.assertNotIn('"wirescape/"' + '"module' + '2.h"', text)
            self.assertNotRegex(text, r"\bnative/(?:modules|sdk|include|tests)\b")


if __name__ == "__main__":
    unittest.main()
