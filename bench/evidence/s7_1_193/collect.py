#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""#193: device-off, source-pinned production R2 and D5 evidence only.

This collector intentionally imports the EXISTING R2 stimulus/analysis from each
pinned source checkout. Its invoke wrapper merely copies the original float32
impulse bytes before r2_probe's temporary directory is removed. It does not
alter Engine::render, stimuli, thresholds, native code or the Facts pipeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "518fe3f8d8a71d1485364bf9176bcf166f9602f3"
HEAD = "8823c78ad58992b39f7b8f696425d9751bdb7ac0"
RATES = (44100, 48000, 96000)
MODULE = "fx.reverb"
PATCH = "basics-03-echo-and-reverb.json"
BLOCK, SECONDS, SEED = 128, 10, 37
SOURCE_FILES = ("bench/offline/r2_probe.py", "bench/offline/r2_engine_probe.cpp",
                "bench/offline/metrics.py", "bench/golden/render.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
                    + "\n", encoding="utf-8")


def execute(argv: list[str], cwd: Path | None = None,
            timeout: int = 1200) -> subprocess.CompletedProcess:
    result = subprocess.run([str(x) for x in argv], cwd=cwd,
                            stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError("command failed (exit %s): %s: %s" %
                           (result.returncode, Path(str(argv[0])).name,
                            " ".join(result.stderr.split())[-1300:]))
    return result


def pinned(checkout: Path, label: str) -> str:
    expected = {"before": BASE, "head": HEAD}[label]
    current = execute(["git", "rev-parse", "HEAD"], checkout).stdout.strip()
    if current != expected:
        raise ValueError("%s source mismatch: expected %s; actual %s" %
                         (label, expected, current))
    return current


def source_hashes(checkout: Path) -> dict:
    return {path: digest(checkout / path) for path in SOURCE_FILES}


def compare_harness(base: Path, head: Path) -> None:
    if source_hashes(base) != source_hashes(head):
        raise ValueError("pinned base/head R2 or golden harness differs; no substitution allowed")


def validate_impulses(rows: list[dict]) -> dict:
    if len(rows) != 3 or {r.get("sample_rate_hz") for r in rows} != set(RATES):
        raise ValueError("R2 must contain exactly 44.1/48/96k rows")
    values = {}
    for row in rows:
        if (row.get("module") != MODULE or row.get("metric") != "r2_impulse"
                or row.get("engine_process_mode") != "production_Engine_render"
                or row.get("status") != "measured" or row.get("decay_status") != "reached"
                or row.get("input_nonzero_frames") != 1
                or row.get("one_second_pre_silence_frames") != row["sample_rate_hz"]
                or row.get("capture_frames") != 2 * row["sample_rate_hz"]
                or row.get("faults") != 0):
            raise ValueError("unmeasured or invalid production R2 row: %s" %
                             row.get("sample_rate_hz"))
        t = row.get("time_to_minus60_db_re_peak_ms")
        if not isinstance(t, (int, float)) or not (0 < t < 2000):
            raise ValueError("R2 decay value invalid")
        values[row["sample_rate_hz"]] = float(t)
    return values


def spread_percent(values: dict) -> float:
    if set(values) != set(RATES) or values[48000] <= 0:
        raise ValueError("missing positive 48k reference")
    return (max(values.values()) - min(values.values())) / values[48000] * 100


def capture_r2(checkout: Path, label: str, out: Path) -> None:
    source_commit = pinned(checkout, label)
    build = checkout / "build/native"
    if not (build / "CMakeCache.txt").is_file():
        raise FileNotFoundError("pinned Release native build missing: " + label)
    # Each side is run in its own Python process: no cached module/harness crossover.
    sys.path.insert(0, str(checkout / "bench/offline"))
    import r2_probe  # type: ignore
    import run_all  # type: ignore
    from metrics import r2_impulse_metrics  # type: ignore
    import numpy as np

    if r2_probe.ROOT.resolve() != checkout.resolve() or run_all.ROOT.resolve() != checkout.resolve():
        raise ValueError("collector loaded an unpinned R2 harness")
    desc = run_all.descriptors()
    if MODULE not in desc:
        raise ValueError("missing source descriptor for " + MODULE)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    originals = {}
    original_invoke = r2_probe.invoke

    def preserve_impulse(binary, mode, ident, library, rate, output_path):
        # Invoke the exact pre-existing executable and analysis; only snapshot
        # the bytestream AFTER it returns and BEFORE the next (tail) invocation.
        result = original_invoke(binary, mode, ident, library, rate, output_path)
        if mode == "impulse" and ident == MODULE and result.get("status") == "measured":
            raw = raw_dir / ("r2-%s-%d.f32le" % (label, rate))
            shutil.copyfile(output_path, raw)
            if raw.stat().st_size != 2 * rate * 4:
                raise ValueError("R2 raw capture size mismatch")
            originals[rate] = {"path": raw.relative_to(out).as_posix(),
                               "sha256_float32_pcm": digest(raw),
                               "bytes": raw.stat().st_size}
        return result

    r2_probe.invoke = preserve_impulse
    try:
        impulses, tails = r2_probe.collect_r2(build, {MODULE: desc[MODULE]},
                                              quick=False, rates=RATES)
    finally:
        r2_probe.invoke = original_invoke
    values = validate_impulses(impulses)
    if len(tails) != 3 or any(r.get("status") != "measured" for r in tails):
        raise ValueError("full production R2 tail evidence missing; no quick fallback")
    if set(originals) != set(RATES):
        raise ValueError("missing original R2 float32 captures")
    for row in impulses:
        rate = row["sample_rate_hz"]
        original = np.fromfile(out / originals[rate]["path"], dtype="<f4")
        independently = r2_impulse_metrics(original, rate)
        if independently["time_to_minus60_db_re_peak_ms"] != row["time_to_minus60_db_re_peak_ms"]:
            raise ValueError("raw float PCM and original R2 metric disagree")
        row["raw_capture"] = originals[rate]

    meta = run_all.provenance(build)
    if meta["commit"] != source_commit:
        raise ValueError("R2 provenance returned wrong source commit")
    write_json(out / ("r2-%s.json" % label), {
        "schema": "wirescape/s7.1-evidence-193/1",
        "label": label, "source_commit": source_commit,
        "source_harness_sha256": source_hashes(checkout),
        "scope": "production_Engine_render nonquick R2, fx.reverb only",
        "quick": False, "sample_rates_hz": list(RATES),
        "provenance": meta, "impulse": impulses, "tail": tails,
        "times_ms": {str(k): values[k] for k in RATES},
        "spread_percent_of_48k": spread_percent(values),
    })
    print("%s actual production R2 ms: %s; spread %.6f%%" %
          (label, [values[r] for r in RATES], spread_percent(values)), flush=True)


def binary(root: Path) -> Path:
    for path in (root / "build/native/wirescape_render",
                 root / "build/native/Release/wirescape_render"):
        if path.is_file():
            return path
    raise FileNotFoundError("pinned Release wirescape_render missing")


def encode_flac(wav: Path, destination: Path) -> dict:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg and ffprobe required for D5 FLAC; no substitute")
    # Source WAV is float32; FLAC's integer format is a 24-bit listening copy.
    # The *unmodified* source float32 PCM is preserved separately with SHA.
    execute(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-y", "-i", str(wav), "-map", "0:a:0", "-c:a", "flac",
             "-sample_fmt", "s32", "-bits_per_raw_sample", "24",
             str(destination)], timeout=240)
    result = execute(["ffprobe", "-v", "error", "-select_streams", "a:0",
                      "-show_entries",
                      "stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration",
                      "-of", "json", str(destination)])
    streams = json.loads(result.stdout).get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_name") != "flac" or (
            int(streams[0].get("sample_rate", 0)) != 48000 or
            int(streams[0].get("channels", 0)) != 2 or
            int(streams[0].get("bits_per_raw_sample", 0)) != 24):
        raise ValueError("D5 FLAC format unexpectedly changed")
    return {"path": destination.name, "sha256": digest(destination),
            "bytes": destination.stat().st_size, "codec": streams[0]}


def capture_d5(base: Path, head: Path, out: Path) -> None:
    pinned(base, "before")
    pinned(head, "head")
    compare_harness(base, head)
    before_patch = base / "apps/studio/patches" / PATCH
    after_patch = head / "apps/studio/patches" / PATCH
    if digest(before_patch) != digest(after_patch):
        raise ValueError("prescribed bundled D5 patch differs between source pins")
    document = json.loads(after_patch.read_text(encoding="utf-8"))
    if document.get("format") != "wirescape.native.patch" or document.get("version") != 2:
        raise ValueError("D5 patch schema mismatch")
    if MODULE not in [m.get("module") for m in document["modules"]]:
        raise ValueError("D5 patch does not contain the affected reverb")
    sys.path.insert(0, str(head / "bench/golden"))
    import render as golden  # type: ignore
    if golden.ROOT.resolve() != head.resolve() or (
            golden.RATE, golden.BLOCK, golden.SECONDS, golden.SEED) != (
            48000, 128, 10, 37):
        raise ValueError("D5 script is not the original golden configuration")
    events = golden.events_for_patch(document)
    if not events or any(e["frame"] >= SECONDS * 48000 for e in events):
        raise ValueError("D5 C4 scripted stimulus missing/invalid")
    destination = out / "d5"
    destination.mkdir(parents=True, exist_ok=True)
    script = destination / "c4-events.json"
    script.write_text(json.dumps(events, sort_keys=True) + "\n", encoding="utf-8")
    records = {}
    with tempfile.TemporaryDirectory(prefix="mt193-d5-") as tmp:
        for label, root, patch in (("before", base, before_patch),
                                   ("head", head, after_patch)):
            renderer = binary(root)
            wav = Path(tmp) / (label + ".wav")
            execute([str(renderer), "--patch", str(patch),
                     "--script", str(script), "--out", str(wav),
                     "--rate", "48000", "--block", "128",
                     "--seconds", "10", "--seed", "37"], cwd=root, timeout=240)
            pcm, audio = golden.read_pcm(wav)
            if not pcm or float(abs(audio).max()) <= 0:
                raise ValueError("D5 source patch produced silence")
            raw = destination / (label + ".f32le")
            raw.write_bytes(pcm)
            records[label] = {
                "source_commit": BASE if label == "before" else HEAD,
                "source_patch_sha256": digest(patch),
                "renderer_sha256": digest(renderer),
                "wav_sha256": digest(wav),
                "original_pcm": {"path": raw.name, "sha256": digest(raw),
                                 "bytes": len(pcm), "format": "interleaved stereo little-endian float32"},
                "peak_fs": float(abs(audio).max()),
                "rms_fs": float((audio.astype("float64") ** 2).mean() ** .5),
                "flac": encode_flac(wav, destination / (label + ".flac")),
            }
    write_json(destination / "manifest.json", {
        "schema": "wirescape/s7.1-d5-193/1",
        "sources": {"before": BASE, "head": HEAD}, "patch": PATCH,
        "patch_sha256": digest(after_patch),
        "golden_harness_sha256": digest(head / "bench/golden/render.py"),
        "script_sha256": digest(script), "script": script.name,
        "configuration": {"sample_rate_hz": 48000, "block_frames": BLOCK,
                          "seconds": SECONDS, "seed": SEED, "channels": 2},
        "conversion_note": "FLAC is 24-bit integer for listening; original float32 PCM bytes retained",
        "rendered_separately": True,
        "float32_pcm_identical": (records["before"]["original_pcm"]["sha256"] ==
                                  records["head"]["original_pcm"]["sha256"]),
        "renders": records,
    })
    print("D5 separately rendered before/head; original PCM hash identical: %s" %
          (records["before"]["original_pcm"]["sha256"] ==
           records["head"]["original_pcm"]["sha256"]), flush=True)


def summarize(out: Path) -> None:
    a = json.loads((out / "r2-before.json").read_text(encoding="utf-8"))
    b = json.loads((out / "r2-head.json").read_text(encoding="utf-8"))
    if a["source_commit"] != BASE or b["source_commit"] != HEAD or (
            a["source_harness_sha256"] != b["source_harness_sha256"]):
        raise ValueError("R2 source/harness provenance mismatch")
    before, after = validate_impulses(a["impulse"]), validate_impulses(b["impulse"])
    baseline, measured = spread_percent(before), spread_percent(after)
    initial_sha = next(r["raw_capture"]["sha256_float32_pcm"]
                       for r in a["impulse"] if r["sample_rate_hz"] == 48000)
    final_sha = next(r["raw_capture"]["sha256_float32_pcm"]
                     for r in b["impulse"] if r["sample_rate_hz"] == 48000)
    for report in (a, b):
        for row in report["impulse"]:
            raw = out / row["raw_capture"]["path"]
            if digest(raw) != row["raw_capture"]["sha256_float32_pcm"]:
                raise ValueError("R2 raw capture SHA mismatch")
    has_d5 = (out / "d5/manifest.json").is_file()
    if platform.machine().lower() in ("x86_64", "amd64") and not has_d5:
        raise ValueError("D5 pair required on Linux x64")
    d5 = json.loads((out / "d5/manifest.json").read_text()) if has_d5 else None
    if d5 and (d5["sources"] != {"before": BASE, "head": HEAD} or
               d5["configuration"] != {"sample_rate_hz": 48000, "block_frames": 128,
                                       "seconds": 10, "seed": 37, "channels": 2}):
        raise ValueError("D5 source or configuration mismatch")
    write_json(out / "summary.json", {
        "schema": "wirescape/s7.1-evidence-193/1",
        "sources": {"before": BASE, "head": HEAD},
        "rate_hz": list(RATES),
        "before_ms": {str(k): before[k] for k in RATES},
        "head_ms": {str(k): after[k] for k in RATES},
        "before_spread_percent": baseline,
        "head_spread_percent": measured,
        "r2_max_spread_percent": 5.0,
        "r2_target_met": measured <= 5.0,
        "r2_48k_original_pcm_identical": initial_sha == final_sha,
        "d5_flac_pair_staged": bool(d5),
        "d5_original_pcm_identical": d5["float32_pcm_identical"] if d5 else None,
        "runner": {"system": platform.system(), "machine": platform.machine()},
    })
    print("Production R2: before %.6f%%, head %.6f%%, 48k raw identical=%s" %
          (baseline, measured, initial_sha == final_sha), flush=True)
    if measured > 5 or initial_sha != final_sha or (
            d5 is not None and not d5["float32_pcm_identical"]):
        raise ValueError("actual measurement fails unchanged S7.1 numeric or 48k PCM rule")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", required=True, choices=("r2", "d5", "summary"))
    p.add_argument("--checkout", type=Path)
    p.add_argument("--label", choices=("before", "head"))
    p.add_argument("--base", type=Path)
    p.add_argument("--head", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == "r2":
        if args.checkout is None or args.label is None:
            p.error("r2 needs --checkout and --label")
        capture_r2(args.checkout.resolve(), args.label, args.out.resolve())
    elif args.mode == "d5":
        if args.base is None or args.head is None:
            p.error("d5 needs --base and --head")
        capture_d5(args.base.resolve(), args.head.resolve(), args.out.resolve())
    else:
        summarize(args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print("MT193 evidence failure: %s" % error, file=sys.stderr)
        raise SystemExit(1)
