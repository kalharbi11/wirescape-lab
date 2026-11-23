# SPDX-License-Identifier: GPL-3.0-only
"""Device-free play regression, including clean interrupted teardown on POSIX."""
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import struct
import subprocess
import sys
import tempfile
import time

runner, patch = map(str, sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="play-", dir=Path.cwd()) as work:
    wav = Path(work) / "offline.wav"
    result = subprocess.run([runner, "play", patch, "--output", str(wav)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["offline"] and report["loader"] == "runtime_patch"
    assert report["frames"] == 480000 and report["peak"] > 0 and report["rms"] > 0
    data = wav.read_bytes()
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    assert struct.unpack_from("<HHIIHH", data, 20) == (1, 2, 48000, 192000, 4, 16)
    assert len(data) == 44 + 480000 * 4
    # OB-a3 pin 7: invoke the real offline CLI with a copied native v1
    # document, not merely the shared loader. Rendering may create an output
    # WAV only in a separate disposable directory; the source remains inert.
    legacy = Path(patch)
    assert json.loads(legacy.read_text())["version"] == 1, "CLI regression requires executable native v1"
    v1dir = Path(work) / "legacy-input"
    v1dir.mkdir()
    v1 = v1dir / "patch_v1.json"
    shutil.copy2(legacy, v1)
    def source_snapshot():
        raw = v1.read_bytes()
        return (raw, hashlib.sha256(raw).hexdigest(),
                v1.stat().st_mtime_ns, tuple(sorted(p.name for p in v1dir.iterdir())))
    before = source_snapshot()
    assert before[3] == ("patch_v1.json",)
    legacy_wav = Path(work) / "legacy-offline.wav"
    v1_result = subprocess.run(
        [runner, "play", str(v1), "--output", str(legacy_wav)],
        capture_output=True, text=True, timeout=30)
    assert v1_result.returncode == 0, v1_result.stderr
    legacy_report = json.loads(v1_result.stdout)
    assert legacy_report["offline"] and legacy_report["loader"] == "runtime_patch"
    assert legacy_wav.is_file() and legacy_wav.read_bytes()[:4] == b"RIFF"
    assert source_snapshot() == before, "v1 CLI execution mutated source bytes, hash, mtime or siblings"
    assert not any(p.name.startswith("patch_v1.json.bak-v1") or
                   p.name.endswith(".v1.json") for p in v1dir.iterdir())

    # Future service hooks fail before any endpoint is opened.
    refused = subprocess.run([runner, "play", patch, "--midi", "fake"], capture_output=True, timeout=10)
    assert refused.returncode != 0 and b"confirmation" in refused.stderr
    # Parsing and refusal happen before constructing the real MIDI backend.
    listed = subprocess.run([runner, "play", "--list-midi"], capture_output=True, timeout=10)
    assert listed.returncode != 0 and b"--confirm-midi" in listed.stderr
    assert b"Unknown play argument" not in listed.stderr
    if os.name != "nt":
        interrupted = Path(work) / "interrupted.wav"
        process = subprocess.Popen([runner, "play", patch, "--pace", "--output", str(interrupted)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while (not interrupted.exists() or interrupted.stat().st_size < 4096) and time.monotonic() < deadline:
                time.sleep(0.02)
            assert interrupted.exists(), "offline renderer did not start"
            process.send_signal(signal.SIGINT)
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stderr
            stopped = json.loads(stdout)
            assert 0 < stopped["frames"] < 480000
            assert interrupted.stat().st_size == 44 + stopped["frames"] * 4
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
print("offline play WAV, device flags and teardown pass")
