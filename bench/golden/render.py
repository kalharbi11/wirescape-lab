# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic, device-free golden rendering of all bundled and owner patches.

The renderer runs twice per patch in temporary directories; no WAV/PCM is
committed. The output JSON holds numeric facts and SHA-256 of raw float32 PCM.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / "apps/studio/patches"
OWNER = ROOT / "bench/patches/owner"
RATE = 48000
BLOCK = 128
SECONDS = 10
SEED = 37
CENTERS_HZ = [20.0 * 2**(i/3) for i in range(31)]
BAND_FLOOR_DBFS = -300.0


def binary(root=ROOT):
    name = "wirescape_render" + (".exe" if os.name == "nt" else "")
    for p in (root/"build/native"/name, root/"build/native/Release"/name,
              root/"build"/name, root/"build/Release"/name):
        if p.is_file():
            return p
    return None


def sources(root=ROOT, coverage_root=None):
    bundled = sorted((root / "apps/studio/patches").glob("*.json"))
    owner = sorted((root / "bench/patches/owner").glob("*.json"))
    if not bundled:
        raise RuntimeError("No bundled patch files found")
    result = [("bundled", p) for p in bundled] + [("owner", p) for p in owner]
    if coverage_root is not None:
        manifest = coverage_manifest()
        directory = coverage_root / "bench/patches/coverage"
        expected = {row["fixture"] for row in manifest["cases"]}
        existing = {p.name for p in directory.glob("*.json")}
        if expected != existing:
            raise RuntimeError(f"coverage fixture inventory mismatch: missing={sorted(expected-existing)}, "
                               f"extra={sorted(existing-expected)}")
        for row in manifest["cases"]:
            control = directory / row["control"]
            if not control.is_file():
                raise RuntimeError(f"missing coverage intervention control: {control}")
            result.append(("coverage", directory / row["fixture"]))
    return result


def coverage_manifest():
    manifest_path = ROOT / "bench/golden/coverage_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or not manifest.get("cases"):
        raise ValueError("invalid golden coverage manifest")
    names = [r["fixture"] for r in manifest["cases"]]
    if len(set(names)) != len(names):
        raise ValueError("duplicate coverage fixture")
    return manifest


def events_for_patch(patch):
    # Match bench/offline/run_all.py bundled_section: one identical C4 key-on
    # and half-window key-off for every host.keyboard node.
    keyboard = sorted(m["id"] for m in patch.get("modules", [])
                      if m.get("module") == "host.keyboard")
    return sorted([{"frame": frame, "type": typ, "node": node, "key": 60}
                   for node in keyboard
                   for frame, typ in ((0, "noteOn"), (RATE*SECONDS//2, "noteOff"))],
                  key=lambda e: (e["frame"], e["node"], e["type"]))


def read_pcm(path):
    raw = path.read_bytes()
    if (len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:16] != b"WAVEfmt "
            or raw[36:40] != b"data"):
        raise ValueError("expected 44-byte float32 WAV header")
    fmt = struct.unpack_from("<IHHIIHH", raw, 16)
    if fmt != (16, 3, 2, RATE, RATE*8, 8, 32):
        raise ValueError(f"unexpected WAV format {fmt}")
    size = struct.unpack_from("<I", raw, 40)[0]
    pcm = raw[44:]
    if size != len(pcm) or size != RATE*SECONDS*8:
        raise ValueError(f"unexpected PCM length: {len(pcm)}")
    audio = np.frombuffer(pcm, dtype="<f4").reshape(-1, 2)
    if not np.isfinite(audio).all():
        raise ValueError("nonfinite float32 output")
    return pcm, audio


def levels(audio):
    x = audio.astype(np.float64)
    # Welch one-sided density, averaged across two output channels; integrated
    # per 1/3-octave band into mean square FS.
    hz, psd = signal.welch(x, fs=RATE, nperseg=65536, axis=0,
                           detrend="constant", scaling="density")
    power = psd.mean(axis=1)
    bin_width = hz[1] - hz[0]
    table = []
    for center in CENTERS_HZ:
        lower, upper = center/2**(1/6), center*2**(1/6)
        energy = float(np.sum(power[(hz >= lower) & (hz < upper)]) * bin_width)
        table.append({"center_hz": round(center, 6),
                      "level_dbfs": round(10*np.log10(energy), 6) if energy>1e-30
                      else BAND_FLOOR_DBFS})
    return {
        "peak_fs": float(np.max(np.abs(x))),
        "rms_fs": float(np.sqrt(np.mean(x*x))),
        "dc_fs": float(np.mean(x)),
        "third_octave_bands": table,
    }


def render_one(exe, patch, script, wav, root=ROOT):
    cmd = [str(exe), "--patch", str(patch), "--script", str(script),
           "--out", str(wav), "--rate", str(RATE), "--block", str(BLOCK),
           "--seconds", str(SECONDS), "--seed", str(SEED)]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                            timeout=150, check=False)
    if result.returncode:
        raise RuntimeError(f"renderer exit {result.returncode} for {patch.name}: "
                           + result.stderr[-1500:])
    return read_pcm(wav)


def measure(exe, path, scope, root=ROOT, wav_folder=None, control_patch=None):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != "wirescape.native.patch" or data.get("version") != 2:
        raise ValueError(f"{path.name}: requires native patch v2")
    events = events_for_patch(data)
    with tempfile.TemporaryDirectory(prefix="ws-golden-") as tmp:
        work = Path(tmp)
        script = work/"events.json"
        script.write_text(json.dumps(events), encoding="utf-8")
        pcm1, a1 = render_one(exe, path, script, work/"render-a.wav", root)
        pcm2, _ = render_one(exe, path, script, work/"render-b.wav", root)
        if pcm1 != pcm2:
            # Determine exact first divergent frame for this repeated-run pair.
            idx = next(i for i in range(0, len(pcm1), 8) if pcm1[i:i+8] != pcm2[i:i+8])
            raise AssertionError(f"{scope}/{path.name}: two renders differ at frame {idx//8}")
        if wav_folder is not None:
            destination = wav_folder / scope / (path.stem + ".wav")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work/"render-a.wav", destination)
        out = {
            "sha256_float32_pcm": hashlib.sha256(pcm1).hexdigest(),
            "frames": int(a1.shape[0]), "channels": 2,
            "repeat_identical": True,
            "scripted_note_count": len(events),
            "script_note_key": 60 if events else None,
            "source": f"{scope}/{path.name}",
        }
        out.update(levels(a1))
        if control_patch is not None:
            if not out["rms_fs"] > 1e-8:
                raise AssertionError(f"{scope}/{path.name}: covered path is silent")
            _, control_audio = render_one(exe, control_patch, script, work/"control.wav", root)
            delta = float(np.max(np.abs(a1.astype(np.float64) - control_audio.astype(np.float64))))
            if not delta > 1e-8:
                raise AssertionError(f"{scope}/{path.name}: no observable contribution vs bypass control")
            out["fixture_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            out["control_sha256"] = hashlib.sha256(control_patch.read_bytes()).hexdigest()
            out["control_peak_difference_fs"] = delta
            out["contribution_verified"] = True
        return out


def cpu_model():
    """Record the actual runner CPU rather than architecture alone."""
    if platform.system() == "Linux":
        try:
            completed = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=5, check=False)
            for line in completed.stdout.splitlines():
                if line.startswith("Model name:"):
                    return line.split(":", 1)[1].strip()
        except OSError:
            pass
    return platform.processor() or platform.machine()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--renderer", type=Path)
    p.add_argument("--root", type=Path, default=ROOT, help="checkout whose patches and renderer are measured")
    p.add_argument("--keep-wavs", type=Path, help="job-local WAV tree for same-runner A/B; never commit")
    p.add_argument("--coverage-root", type=Path, help="fixture checkout; same exact bytes for base and head")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--machine", required=True, choices=("linux-x64","linux-arm64","windows-x64"))
    args = p.parse_args(argv)
    root = args.root.resolve()
    if not (root / "apps/studio/patches").is_dir():
        p.error("--root is not a lab checkout with bundled patches")
    exe = args.renderer or binary(root)
    if not exe or not exe.is_file():
        p.error("wirescape_render binary unavailable: build native headless first or pass --renderer")
    version = subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,
                             capture_output=True,check=True).stdout.strip()
    fixture_root = args.coverage_root.resolve() if args.coverage_root else None
    fixture_sha = None
    manifest = None
    if fixture_root is not None:
        manifest = coverage_manifest()
        fixture_sha = subprocess.run(["git","rev-parse","HEAD"],cwd=fixture_root,text=True,
                                     capture_output=True,check=True).stdout.strip()
    meta = {
        "schema": 1, "commit": version,
        "engine_source_commit": version,
        "fixture_source_commit": fixture_sha,
        "date_et": dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": args.machine,
        "architecture": platform.machine(),
        "os": platform.system(),
        "cpu": cpu_model(),
        "sample_rate_hz": RATE, "block_frames": BLOCK,
        "seconds": SECONDS, "seed": SEED, "channels": 2,
        "encoding": "little-endian IEEE754 float32 PCM; SHA-256 excludes 44-byte WAV header",
        "spectrum_method": "scipy.signal.welch nperseg=65536 one-sided density, average channel PSD, integrate per band",
        "band_floor_dbfs": BAND_FLOOR_DBFS,
        "notes": "C4 noteOn at frame 0 and noteOff at frame 240000 on every host.keyboard",
        "patches": {},
    }
    cases = {r["fixture"]: r for r in manifest["cases"]} if manifest is not None else {}
    for scope, path in sources(root, fixture_root):
        key = f"{scope}/{path.name}"
        control = (fixture_root / "bench/patches/coverage" / cases[path.name]["control"]
                   if scope == "coverage" else None)
        meta["patches"][key] = measure(exe.resolve(), path.resolve(), scope, root,
                                      args.keep_wavs.resolve() if args.keep_wavs else None, control)
        if scope == "coverage":
            meta["patches"][key]["target_ids"] = cases[path.name]["targets"]
        print(f"golden {key}: {meta['patches'][key]['sha256_float32_pcm'][:12]} "
              f"peak={meta['patches'][key]['peak_fs']:.6g} "
              f"rms={meta['patches'][key]['rms_fs']:.6g}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(meta, indent=2, allow_nan=False)+"\n",encoding="utf-8")
    print(f"golden summary: {len(meta['patches'])} patches, all repeated renders byte-identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
