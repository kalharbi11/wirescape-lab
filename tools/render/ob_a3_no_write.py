# SPDX-License-Identifier: GPL-3.0-only
"""OB-a3 pin 7: real standalone renderer refuses v1 without touching it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def snapshot(folder: Path) -> tuple:
    return tuple((p.name, p.read_bytes(), hashlib.sha256(p.read_bytes()).hexdigest(),
                  p.stat().st_mtime_ns) for p in sorted(folder.iterdir()))


def main() -> None:
    render, old_source, case_source = map(Path, sys.argv[1:4])
    case = json.loads(case_source.read_bytes())
    assert json.loads(old_source.read_bytes())["version"] == 1
    assert case["patch"]["version"] == 2
    with tempfile.TemporaryDirectory(prefix="wirescape-ob-a3-render-") as folder:
        root = Path(folder)
        inputs = root / "inputs"
        output = root / "output"
        inputs.mkdir()
        output.mkdir()
        legacy = inputs / "legacy.json"
        modern = inputs / "modern.json"
        shutil.copy2(old_source, legacy)
        modern.write_text(json.dumps(case["patch"]) + "\n", encoding="utf-8")
        events = output / "events.json"
        events.write_text(json.dumps(case["events"]) + "\n", encoding="utf-8")
        before = snapshot(inputs)

        def invoke(patch: Path, wav: Path) -> subprocess.CompletedProcess:
            return subprocess.run([
                str(render), "--patch", str(patch), "--script", str(events),
                "--out", str(wav), "--rate", str(case["rate"]),
                "--block", str(case["block"]), "--seconds", str(case["seconds"]),
                "--seed", str(case["seed"])],
                capture_output=True, text=True, timeout=70, cwd=root)

        denied_wav = output / "denied.wav"
        denied = invoke(legacy, denied_wav)
        assert denied.returncode != 0, "renderer unexpectedly accepted a v1 document"
        assert "requires ABI2 patch v2" in denied.stderr, denied.stderr[-1000:]
        assert not denied_wav.exists(), "renderer created a WAV from refused v1"
        assert snapshot(inputs) == before, "renderer refusal changed input bytes, mtime or siblings"
        modern_wav = output / "control.wav"
        accepted = invoke(modern, modern_wav)
        assert accepted.returncode == 0, accepted.stderr[-1200:]
        assert modern_wav.read_bytes()[:12] == b"RIFF" + modern_wav.read_bytes()[4:8] + b"WAVE"
        assert "render_metrics " in accepted.stdout, accepted.stdout[-600:]
        assert snapshot(inputs) == before, "renderer v2 control mutated input bytes or siblings"
        assert not any(".bak-v1" in p.name or p.name.endswith(".v1.json")
                       for p in inputs.iterdir())
    print("OB-a3 renderer: v1 refused, v2 rendered, inputs unchanged")


if __name__ == "__main__":
    main()
