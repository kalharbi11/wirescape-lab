# SPDX-License-Identifier: GPL-3.0-only
import argparse
import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import dev  # noqa: E402
from foundation.helpers import run_logged  # noqa: E402


class BuildFailureDiagnosticsTests(unittest.TestCase):
    def test_visual_studio_toolset_is_explicit_in_configure_argv(self):
        for generator, toolset, expected in (
            ("Visual Studio 18 2026", "v143,version=14.44", ["-T", "v143,version=14.44"]),
            ("Visual Studio 17 2022", "", []),
            ("Ninja", "v143,version=14.44", []),
        ):
            with self.subTest(generator=generator, toolset=toolset), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "native").mkdir()
                (root / "native/CMakeLists.txt").touch()
                calls = []

                def stop_after_configure(command, cwd, log):
                    calls.append(command)
                    return {"command": command, "exit_code": 7, "error": "synthetic failure"}

                with patch.object(dev, "ROOT", root), \
                     patch.object(dev, "BUILD_DIR", root / "build"), \
                     patch.object(dev, "REPORT_DIR", root / "reports"), \
                     patch.object(dev, "_base_record", return_value={"action": "build", "source": {}}), \
                     patch.object(dev, "_cmake_and_generator", return_value=("cmake", generator, "x64")), \
                     patch.object(dev, "run_logged", side_effect=stop_after_configure), \
                     patch.dict(os.environ, {"CMAKE_GENERATOR_TOOLSET": toolset}), \
                     redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = dev.command_build(argparse.Namespace(config="Release", headless=True, json=True))

                self.assertEqual(code, 7)
                self.assertEqual(len(calls), 1)
                command = calls[0]
                if expected:
                    self.assertEqual(command[command.index("-T"):command.index("-T") + 2], expected)
                else:
                    self.assertNotIn("-T", command)

    def test_failed_command_and_bounded_log_tail_visible_without_breaking_json(self):
        for stage in ("configure", "build"):
            for as_json in (False, True):
                with self.subTest(stage=stage, as_json=as_json), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    (root / "native").mkdir()
                    (root / "native/CMakeLists.txt").touch()
                    calls = []

                    def simulate(command, cwd, log):
                        calls.append(command)
                        failing = stage == "configure" or len(calls) == 2
                        script = (
                            "import sys; print('old-line-outside-tail'); "
                            "[print('build progress', i) for i in range(200)]; "
                            "print('synthetic compiler error C1234', file=sys.stderr, flush=True); "
                            "sys.exit(7)"
                            if failing else "print('configure ok')"
                        )
                        result = run_logged([sys.executable, "-u", "-c", script], cwd, log)
                        result["command"] = command
                        return result

                    stdout, stderr = io.StringIO(), io.StringIO()
                    with patch.object(dev, "ROOT", root), \
                         patch.object(dev, "BUILD_DIR", root / "build"), \
                         patch.object(dev, "REPORT_DIR", root / "reports"), \
                         patch.object(dev, "_base_record", return_value={"action": "build", "source": {}}), \
                         patch.object(dev, "_cmake_and_generator", return_value=("cmake with space", "Ninja", "x64")), \
                         patch.object(dev, "run_logged", side_effect=simulate), \
                         redirect_stdout(stdout), redirect_stderr(stderr):
                        code = dev.command_build(argparse.Namespace(config="Release", headless=True, json=as_json))

                    self.assertEqual(code, 7)
                    self.assertEqual(len(calls), 1 if stage == "configure" else 2)
                    diagnostics = stderr.getvalue()
                    self.assertIn(stage, diagnostics)
                    self.assertIn(json.dumps(calls[-1]), diagnostics)
                    self.assertIn("synthetic compiler error C1234", diagnostics)
                    self.assertIn("build progress 199", diagnostics)
                    self.assertNotIn("old-line-outside-tail", diagnostics)
                    if as_json:
                        report = json.loads(stdout.getvalue())
                        self.assertEqual(report["status"], "failed")
                        self.assertEqual(report["command_result"]["exit_code"], 7)
                    else:
                        self.assertIn("build: FAILED", stdout.getvalue())
                    log = next((root / "reports").glob("build-" + ("configure" if stage == "configure" else "compile") + "-*.log"))
                    self.assertIn("old-line-outside-tail", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
