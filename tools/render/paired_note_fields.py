# SPDX-License-Identifier: GPL-3.0-only
"""Opt-in #747 paired diagnostic. Build a pinned test-only checkout in isolation.

Usage: python3 tools/render/paired_note_fields.py HEAD_RENDER TEST_ONLY_SHA
The head renderer must already be built in Release mode. This is not a CTest:
it fetches and builds the test-only revision in a disposable worktree.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("renderer", type=Path)
    parser.add_argument("test_only_sha")
    args = parser.parse_args()
    head_renderer = args.renderer.resolve()
    root = Path(__file__).resolve().parents[2]
    test = Path(__file__).with_name("test_note_fields.py").resolve()
    sha = args.test_only_sha
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        parser.error("expected full test-only commit SHA")
    if not head_renderer.is_file():
        parser.error("build the head renderer first")

    def git(*words):
        return subprocess.check_output(["git", "-C", str(root), *words], text=True).strip()

    print("head:", git("rev-parse", "HEAD"), "test-only:", sha, flush=True)
    # Dev-run checks out a shallow head; fetch only the explicitly pinned
    # same-repository commit. No credentials or external devices are needed.
    subprocess.run(["git", "-C", str(root), "fetch", "--no-tags", "--depth=1",
                    "origin", sha], check=True, timeout=90)
    with tempfile.TemporaryDirectory(prefix="ws-note-pair-") as folder:
        checkout = Path(folder) / "base"
        build = Path(folder) / "build"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach",
                        str(checkout), sha], check=True)
        try:
            actual = subprocess.check_output(["git", "-C", str(checkout),
                                              "rev-parse", "HEAD"], text=True).strip()
            assert actual == sha, actual
            configure = ["cmake", "-S", str(checkout / "native"), "-B", str(build),
                         "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"]
            if shutil.which("ccache"):
                configure += ["-DCMAKE_C_COMPILER_LAUNCHER=ccache",
                              "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache"]
            subprocess.run(configure, check=True)
            subprocess.run(["cmake", "--build", str(build), "--target",
                            "wirescape_render"], check=True)
            base_renderer = build / head_renderer.name
            base_test = checkout / "tools/render/test_note_fields.py"
            red = subprocess.run([sys.executable, str(base_test), str(base_renderer)],
                                 capture_output=True, text=True, timeout=120)
            print(red.stdout, end="", flush=True)
            print(red.stderr, end="", flush=True)
            # Do not mistake an infrastructure error or unrelated assertion
            # for reproduction of the expected ignored-velocity defect.
            assert red.returncode != 0 and "AssertionError: (7, 1.0, 17)" in red.stderr, (
                "test-only head did not reproduce expected ignored velocity")
            print("expected red confirmed on", actual, flush=True)
            # The existing test compares complete WAV bytes for every case,
            # using both executables on the same runner, rate, block and seed.
            subprocess.run([sys.executable, str(test), str(head_renderer),
                            str(base_renderer)], check=True, timeout=120)
            print("paired full WAV bytes identical for every existing case", flush=True)
        finally:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force",
                            str(checkout)], check=True)


if __name__ == "__main__":
    main()
