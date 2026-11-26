# SPDX-License-Identifier: GPL-3.0-only
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_run  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_defaults(self):
        s = dev_run.parse_request("/dev-run test")
        self.assertEqual(s["profile"], "test")
        self.assertEqual(s["platforms"], ["linux-x64"])
        self.assertEqual((s["filter"], s["build"], s["timeout"], s["repeat"]), ("", "release", 60, 1))

    def test_only_first_line(self):
        s = dev_run.parse_request("/dev-run test filter=osc\nplease run this @someone")
        self.assertEqual(s["filter"], "osc")

    def test_both_platforms_and_asan(self):
        s = dev_run.parse_request("/dev-run asan platform=both filter=abi2_osc_(heavy|panic).* timeout=600")
        self.assertEqual(s["platforms"], ["linux-x64", "linux-arm64"])
        self.assertEqual(s["build"], "asan")
        self.assertEqual(s["timeout"], 600)

    def test_cmd(self):
        s = dev_run.parse_request('/dev-run cmd build=asan cmd="build/asan/abi2_osc_heavy_ingress_tests --cpu-wall"')
        self.assertEqual(s["cmd"], ["build/asan/abi2_osc_heavy_ingress_tests", "--cpu-wall"])
        s = dev_run.parse_request('/dev-run cmd cmd="valgrind --tool=callgrind build/native/wirescape_render x.json"')
        self.assertEqual(s["cmd"][0], "valgrind")

    def test_targets(self):
        s = dev_run.parse_request("/dev-run asan target=abi2_osc_heavy_ingress_tests filter=abi2_osc_heavy")
        self.assertEqual(s["targets"], ["abi2_osc_heavy_ingress_tests"])
        self.assertEqual(dev_run.parse_request("/dev-run test")["targets"], [])

    def test_refusals(self):
        bad = [
            "/dev-run", "/dev-run shell", "/dev-run test foo", "/dev-run test platform=windows-x64",
            "/dev-run test filter=a;rm", "/dev-run test build=asan", "/dev-run cmd",
            '/dev-run cmd cmd="bash -c x"', '/dev-run cmd cmd="build/native/../../x"',
            '/dev-run test cmd="build/native/x"', "/dev-run test timeout=0", "/dev-run test repeat=99",
            "/dev-run studio platform=linux-arm64", "/dev-run test filter=a filter=b", "/dev-run test target=a;b", "/dev-run studio target=x", '/dev-run cmd cmd="x',
        ]
        for text in bad:
            with self.subTest(text=text), self.assertRaises(dev_run.RequestError):
                dev_run.parse_request(text)


class DevRunUsabilityTests(unittest.TestCase):
    """Lead/Architect 2026-11-25: B5 lost a run to a misspelled target; B4 waited for a full
    native build to run a Python check. These keep both fixed."""

    LISTING = ("abi2_delay_tests: phony\nwirescape_engine_sidecar: phony\n"
               "engine2/abi2_delay_tests: CXX_EXECUTABLE_LINKER__abi2_delay_tests_Release\n"
               "cmake_object_order_depends_target_abi2_delay_tests: phony\nbuild.ninja: RERUN_CMAKE\nall: phony\n")

    def test_known_targets_from_ninja_listing(self):
        known = dev_run.known_targets(self.LISTING)
        self.assertIn("abi2_delay_tests", known)
        self.assertIn("wirescape_engine_sidecar", known)
        self.assertNotIn("build.ninja", known)
        self.assertFalse(any(k.startswith("cmake_") for k in known))

    def test_unknown_target_gets_close_match(self):
        hint = dev_run.target_hint(["wirescape_sidecar"], dev_run.known_targets(self.LISTING))
        self.assertIn("`wirescape_sidecar` is not a CMake target", hint)
        self.assertIn("wirescape_engine_sidecar", hint)
        self.assertEqual(dev_run.target_hint(["abi2_delay_tests"], dev_run.known_targets(self.LISTING)), "")

    def test_build_none_only_for_python_cmd(self):
        s = dev_run.parse_request('/dev-run cmd build=none cmd="python3 tools/foundation/tests/test_banned_includes.py"')
        self.assertEqual(s["build"], "none")
        for text in ["/dev-run test build=none", '/dev-run cmd build=none cmd="build/native/x"',
                     '/dev-run cmd build=none target=x cmd="python3 tools/x.py"']:
            with self.subTest(text=text), self.assertRaises(dev_run.RequestError):
                dev_run.parse_request(text)

    def test_first_causes_and_report_show_cause_first(self):
        lines = ["-- Configuring done", "ninja: error: unknown target 'wirescape_sidecar'", "x"]
        self.assertEqual(dev_run.first_causes(lines), ["ninja: error: unknown target 'wirescape_sidecar'"])
        spec = dev_run.parse_request("/dev-run test target=wirescape_sidecar")
        text = dev_run.build_report(spec, "c" * 40, "u", [{
            "platform": "linux-x64", "ok": False, "steps": [], "hint": "dev-run hint: did you mean y?",
            "causes": lines[1:2], "tail": lines}])
        self.assertLess(text.index("First error lines"), text.index("Last 3 log lines"))
        self.assertIn("did you mean y?", text)


class ReportTests(unittest.TestCase):
    def test_report_defuses_and_flags_missing(self):
        spec = dev_run.parse_request("/dev-run test platform=both")
        summaries = [{"platform": "linux-x64", "ok": False,
                      "steps": [{"name": "ctest", "exit": 8, "seconds": 3.2}],
                      "failed_tests": ["12 - x (Failed)"], "tail": ["```", "@owner hi"]}]
        text = dev_run.build_report(spec, "a" * 40, "https://example.invalid/run", summaries)
        self.assertIn("❌ fail", text)
        self.assertIn("linux-arm64 | ⚠️ no result", text)
        self.assertNotIn("\n```\n```", text)
        self.assertNotIn("@owner", text)
        self.assertIn("not contract evidence", text)

    def test_report_ignores_unrequested_platform(self):
        spec = dev_run.parse_request("/dev-run test")
        text = dev_run.build_report(spec, "b" * 40, "u", [{"platform": "linux-arm64", "ok": True}])
        self.assertIn("linux-x64 | ⚠️ no result", text)
        self.assertNotIn("linux-arm64 |", text)


if __name__ == "__main__":
    unittest.main()
