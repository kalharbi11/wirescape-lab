# SPDX-License-Identifier: GPL-3.0-only
"""OB-a3 pin 7: real device-off soak/golden CLI input no-write regressions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def snapshot(folder: Path) -> tuple:
    names = tuple(sorted(p.name for p in folder.iterdir()))
    return tuple((p.name, p.read_bytes(), hashlib.sha256(p.read_bytes()).hexdigest(),
                  p.stat().st_mtime_ns) for p in sorted(folder.iterdir())) + (names,)


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("soak", "golden"))
    parser.add_argument("binary", type=Path)
    parser.add_argument("legacy", type=Path)
    parser.add_argument("modern", type=Path)
    a = parser.parse_args()

    assert json.loads(a.legacy.read_bytes())["version"] == 1
    assert json.loads(a.modern.read_bytes())["version"] == 2
    with tempfile.TemporaryDirectory(prefix="wirescape-ob-a3-") as temp:
        root = Path(temp)
        sources = root / "inputs"
        sources.mkdir()
        old = sources / "native-v1.json"
        new = sources / "control-v2.json"
        shutil.copy2(a.legacy, old)
        shutil.copy2(a.modern, new)
        before = snapshot(sources)
        assert tuple(p.name for p in sources.iterdir()) == ("native-v1.json", "control-v2.json")
        if a.mode == "soak":
            for patch in (old, new):
                process = subprocess.run(
                    [str(a.binary), "--patch", str(patch), "--rate", "48000",
                     "--block", "128", "--seconds", "0.01"],
                    capture_output=True, text=True, timeout=45, cwd=root)
                assert process.returncode == 0, process.stderr[-1600:]
                result = json.loads(process.stdout)
                assert result["graph"] == "document", result
                assert result["faults"] == 0, result
                assert snapshot(sources) == before, "soak rewrote its input or siblings"
        else:
            process = subprocess.run([str(a.binary), str(sources)],
                                     capture_output=True, text=True, timeout=90, cwd=root)
            assert process.returncode == 0, process.stderr[-1600:]
            report = json.loads(process.stdout)
            cases = {case["name"] for case in report["cases"]}
            assert {"patch/native-v1.json", "patch/control-v2.json"} <= cases, cases
            assert snapshot(sources) == before, "Golden rewrote its input or siblings"
        assert not any(".bak-v1" in p.name or p.name.endswith(".v1.json")
                       for p in sources.iterdir())
    print(f"OB-a3 {a.mode}: real executable v1 and v2 sources unchanged")


if __name__ == "__main__":
    run()
