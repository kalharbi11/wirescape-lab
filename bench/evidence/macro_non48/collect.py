#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""#226: source-pinned, device-free Macro non48 evidence (no product modifications).

The existing offline oscillator_metrics FFT pitch estimator is used verbatim.
An FFT peak around the requested note is NOT proof of a pitched fundamental in
a noise/inharmonic Plaits engine: applicability remains a reserved design question.
Final source pins are supplied at release by the lead only after the #212/B4
native/document compatibility handoff. No default or guessed HEAD is permitted.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
MODULE = "ports.macro_oscillator"
RATES = (44100, 48000, 96000)
TARGETS = (110, 440, 1760, 3520, 7040)
MODELS = tuple(range(24))
FRAMES, SECONDS, SEED = 128, 10, 37
D5_PATCH = "basics-07-macro-keys.json"
IR_LENGTHS = (12, 24)
PITCH_MAX_DELTA_CENTS = 2.0
IR_48_MAX_GROWTH_PERCENT = 3.0
PIN_FILES = ("bench/offline/metrics.py", "bench/golden/render.py",
             "bench/offline/run_all.py", "native/modules2/macro_oscillator/dsp.h",
             "native/modules2/macro_oscillator/CMakeLists.txt",
             "native/modules2/macro_oscillator/module.json",
             "native/document/qt_free_patch_coverage_tests.cpp")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
                    + "\n", encoding="utf-8")


def run(command, cwd=None, timeout=300, allow_fail=False):
    p = subprocess.run([str(x) for x in command], cwd=cwd,
                       stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, timeout=timeout, check=False)
    if p.returncode and not allow_fail:
        raise RuntimeError("%s failed exit=%d: %s" %
                           (Path(str(command[0])).name, p.returncode,
                            " ".join(p.stderr.split())[-850:]))
    return p


def verify_sha(text: str) -> str:
    if not SHA_PATTERN.fullmatch(text):
        raise ValueError("a full immutable 40-character source SHA is required")
    return text


def pinned(checkout: Path, expected: str) -> None:
    sha = run(["git", "rev-parse", "HEAD"], checkout).stdout.strip()
    if sha != verify_sha(expected):
        raise ValueError("source pin mismatch: expected %s; checkout %s" %
                         (expected, sha))


def binaries(checkout: Path, name: str) -> Path:
    base = checkout / "build/native"
    for p in (base / name, base / "Release" / name,
              base / (name + ".exe"), base / "Release" / (name + ".exe")):
        if p.is_file():
            return p
    raise FileNotFoundError("pinned Release binary unavailable: " + name)


def toolchain(checkout: Path) -> dict:
    cache = checkout / "build/native/CMakeCache.txt"
    rows = {}
    if cache.exists():
        for line in cache.read_text(errors="replace").splitlines():
            if line.startswith(("CMAKE_CXX_COMPILER:", "CMAKE_BUILD_TYPE:",
                                "CMAKE_CXX_FLAGS_RELEASE:")):
                k, _, v = line.partition("=")
                rows[k] = v
    return {"python": sys.version.split()[0], "system": platform.platform(),
            "architecture": platform.machine(), "cpu": platform.processor() or "unavailable",
            "cmake": rows, "date_et": datetime.now(ZoneInfo("America/New_York")).isoformat()}


def harness_sources(checkout: Path) -> dict:
    return {name: digest(checkout / name) for name in PIN_FILES}


def compiled_libraries(checkout: Path) -> dict:
    """Exact built library hashes; unavailable is a blocker, not a proxy."""
    build = checkout / "build/native"
    matches = sorted(p for p in build.rglob("*ws2_macro_oscillator*")
                     if p.is_file() and p.suffix.lower() in (".so", ".dylib", ".dll"))
    if not matches:
        return {"status": "unavailable", "reason": "built ws2_macro_oscillator shared module absent"}
    return {"status": "measured", "files": [
        {"path": p.relative_to(checkout).as_posix(), "sha256": digest(p),
         "bytes": p.stat().st_size} for p in matches]}


def provenance(checkout: Path, expected: str, label: str) -> dict:
    pinned(checkout, expected)
    return {"source_commit": expected, "label": label, "toolchain": toolchain(checkout),
            "collector_sha256": digest(Path(__file__)),
            "source_hashes": harness_sources(checkout),
            "compiled_macro_libraries": compiled_libraries(checkout)}


def matrix(label: str) -> list[tuple[int, int, int]]:
    if label not in ("before", "head"):
        raise ValueError("source label must be before/head")
    rates = (48000,) if label == "before" else RATES
    return [(model, rate, hz) for rate in rates for model in MODELS for hz in TARGETS]


def macro_patch(run_all, version: int, model: int, hz: int):
    """Byte-equivalent parameter/CV recipe from existing run_all.oscillator_sections."""
    import numpy as np
    note = 12 * math.log2(hz / 261.6255653005986)
    coarse = float(np.clip(note, -48, 48))
    patch = run_all.direct_source(MODULE, version,
                                  {"model": model, "coarse": coarse}, "main")
    residual = (note - coarse) / 12
    if abs(residual) > 1e-9:
        patch["modules"].append(run_all.mod(3, "essentials.scale_offset",
                                            parameters={"scale": 0, "offset": residual}))
        patch["connections"].append(run_all.edge(3, "control", 1, "pitch"))
    return patch


def import_original_harness(checkout: Path):
    """One source checkout per Python process; never cross-import cached code."""
    source = str(checkout / "bench/offline")
    if any(n in sys.modules for n in ("metrics", "run_all")):
        raise RuntimeError("cross-source harness import refused")
    sys.path.insert(0, source)
    import metrics  # type: ignore
    import run_all  # type: ignore
    if run_all.ROOT.resolve() != checkout.resolve():
        raise ValueError("original run_all imported from wrong source checkout")
    return run_all, metrics


def raw_pcm(wav: Path, rate: int, seconds: float) -> bytes:
    import struct
    data = wav.read_bytes()
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:16] != b"WAVEfmt ":
        raise ValueError("not original renderer float32 stereo WAV")
    fmt = struct.unpack_from("<IHHIIHH", data, 16)
    if fmt != (16, 3, 2, rate, rate * 8, 8, 32):
        raise ValueError("WAV encoding/rate differs from prescribed original float32")
    size = struct.unpack_from("<I", data, 40)[0]
    if size != len(data) - 44 or size != round(seconds * rate) * 8:
        raise ValueError("WAV PCM size mismatch")
    return data[44:]


def preserve_pcm(pcm: bytes, output: Path, root: Path) -> dict:
    """Persist every original float32 sample, compressed; hash both representations."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(output), mode="wb", compresslevel=6, mtime=0) as writer:
        writer.write(pcm)
    original_sha = hashlib.sha256(pcm).hexdigest()
    if gzip.decompress(output.read_bytes()) != pcm:
        raise ValueError("compressed original float PCM does not round-trip")
    return {"file": output.relative_to(root).as_posix(), "sha256_original_pcm": original_sha,
            "bytes_original_pcm": len(pcm), "sha256_gzip": digest(output),
            "bytes_gzip": output.stat().st_size, "format": "f32le stereo interleaved gzip"}


def pitch_status(result: dict) -> dict:
    """Never interpret an inharmonic/noise peak as a pitch pass."""
    observed = result.get("observed_hz")
    cents = result.get("pitch_cents")
    if (not isinstance(observed, (int, float)) or observed <= 0 or
            not math.isfinite(observed) or not isinstance(cents, (int, float)) or
            not math.isfinite(cents)):
        return {"status": "unmeasured", "reason":
                "existing FFT estimator yielded no finite positive tonal candidate"}
    return {"status": "unmeasured_pending_design_ruling", "reason":
            "inharmonic/noise models may have a near-target FFT peak without a meaningful fundamental; "
            "model applicability remains reserved for Architect, never zero/pass",
            "unmodified_estimator_pitch_cents_diagnostic": float(cents),
            "unmodified_estimator_observed_hz_diagnostic": float(observed)}


def capture_pitch(checkout: Path, label: str, expected: str, out: Path) -> None:
    meta = provenance(checkout, expected, label)
    renderer = binaries(checkout, "wirescape_render")
    run_all, metrics = import_original_harness(checkout)
    descriptor = run_all.descriptors().get(MODULE)
    if not descriptor:
        raise ValueError("Macro source descriptor missing")
    records = []
    with tempfile.TemporaryDirectory(prefix="ws-macro-226-") as td:
        temp = Path(td)
        for model, rate, hz in matrix(label):
            patch = macro_patch(run_all, descriptor["version"], model, hz)
            patch_path = temp / "patch.json"
            events_path = temp / "events.json"
            wav = temp / "raw.wav"
            patch_bytes = (json.dumps(patch, sort_keys=True) + "\n").encode()
            patch_path.write_bytes(patch_bytes)
            events_path.write_text("[]\n", encoding="utf-8")
            entry = {"module": MODULE, "model": model, "target_hz": hz,
                     "sample_rate_hz": rate, "render_seconds": 2,
                     "block_frames": 128, "seed": 7,
                     "patch_sha256": hashlib.sha256(patch_bytes).hexdigest(),
                     "events_sha256": digest(events_path)}
            result = run([renderer, "--patch", patch_path, "--script", events_path,
                          "--out", wav, "--rate", rate, "--block", 128,
                          "--seconds", 2, "--seed", 7], checkout,
                         timeout=180, allow_fail=True)
            if result.returncode:
                records.append({**entry, "status": "unmeasured_render_failed",
                                "reason": "actual renderer exit %d: %s" %
                                (result.returncode, " ".join(result.stderr.split())[-400:])})
                continue
            pcm = raw_pcm(wav, rate, 2)
            capture_path = out / "raw" / ("%s-m%02d-%d-%d.f32le.gz" %
                                           (label, model, hz, rate))
            raw = preserve_pcm(pcm, capture_path, out)
            audio = metrics.read_audio(wav, rate=rate)
            values = metrics.oscillator_metrics(audio, hz, rate)
            if values.get("nonfinite_samples", 0):
                records.append({**entry, "status": "unmeasured_nonfinite",
                                "reason": "original oscillator_metrics returned nonfinite output",
                                "pcm": raw, "estimator": values})
            else:
                records.append({**entry, "status": "measured_output",
                                "pcm": raw, "estimator": values,
                                "pitch": pitch_status(values)})
    save(out / ("pitch-" + label + ".json"),
         {"schema": "wirescape/macro-non48-226/1", "kind": "pitch",
          "source": meta, "renderer_sha256": digest(renderer),
          "original_fft_estimator": "bench/offline/metrics.py:oscillator_metrics unchanged; "
                                    "Hann, 80-120% target search, log-parabola peak",
          "expected": {"models": len(MODELS), "targets_hz": list(TARGETS),
                       "rates_hz": [48000] if label == "before" else list(RATES)},
          "rows": records})
    print("%s pitch records: %d; measured output %d; no tonal verdict inferred" %
          (label, len(records), sum(r["status"] == "measured_output" for r in records)),
          flush=True)


def capture_ir(checkout: Path, label: str, expected: str, out: Path) -> None:
    meta = provenance(checkout, expected, label)
    if platform.system() != "Linux":
        raise RuntimeError("Callgrind is Linux-only; no fabricated Windows Ir")
    valgrind = shutil.which("valgrind")
    if not valgrind:
        raise RuntimeError("valgrind unavailable; no instruction proxy")
    probe = binaries(checkout, "abi2_module_cpu_probe")
    sys.path.insert(0, str(checkout))
    from bench.gate.instructions import verify_module_probe  # type: ignore
    from tools.bench.abi2_cost import instructions as ir_summary  # type: ignore
    version = run([valgrind, "--version"], checkout).stdout.strip()
    rows = []
    for rate in ((48000,) if label == "before" else RATES):
        for voices in (1, 8):
            entry = {"module": MODULE, "sample_rate_hz": rate,
                     "voices": voices, "block_frames": FRAMES,
                     "mode": "callgrind-Ir-two-length-difference-v1",
                     "lengths_blocks": list(IR_LENGTHS)}
            totals, raw_files = [], []
            failure = None
            for n in IR_LENGTHS:
                output = out / "ir" / ("%s-%d-v%d-n%d.callgrind" %
                                       (label, rate, voices, n))
                output.parent.mkdir(parents=True, exist_ok=True)
                cmd = [probe, "--module", MODULE, "--rate", rate, "--block",
                       FRAMES, "--channels", voices, "--instances", 1,
                       "--seconds", n * FRAMES / rate]
                try:
                    result = run([valgrind, "--quiet", "--tool=callgrind",
                                  "--error-exitcode=77", "--callgrind-out-file=" + str(output),
                                  *cmd], checkout, timeout=240)
                    verify_module_probe(result.stdout, {
                        "module": MODULE, "channels": voices, "instances": 1,
                        "sample_rate": rate, "block": FRAMES, "blocks": n,
                        "seconds": n * FRAMES / rate})
                    total = ir_summary(output)
                    totals.append(total)
                    raw_files.append({"file": output.relative_to(out).as_posix(),
                                      "sha256": digest(output), "bytes": output.stat().st_size})
                except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as err:
                    failure = type(err).__name__ + ": " + str(err)[:400]
                    break
            if failure:
                rows.append({**entry, "status": "unmeasured", "reason": failure,
                             "callgrind": raw_files})
                continue
            delta = totals[1] - totals[0]
            if delta <= 0:
                rows.append({**entry, "status": "unmeasured",
                             "reason": "nonpositive actual Callgrind Ir delta",
                             "callgrind": raw_files, "totals": totals})
                continue
            rows.append({**entry, "status": "measured",
                         "ir_per_128_frame_block": delta / (IR_LENGTHS[1]-IR_LENGTHS[0]),
                         "totals": totals, "callgrind": raw_files})
    save(out / ("ir-" + label + ".json"),
         {"schema": "wirescape/macro-non48-226/1", "kind": "callgrind",
          "source": meta, "valgrind_version": version, "probe_sha256": digest(probe),
          "rate_48_rule": "<=+3% vs original source; 44.1/96 report-only, no baseline",
          "rows": rows})
    print("%s Callgrind rows: %d" % (label, len(rows)), flush=True)


def encode_flac(wav: Path, destination: Path) -> dict:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("D5 needs actual ffmpeg and ffprobe; no substitute")
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-i", wav, "-map", "0:a:0", "-c:a", "flac",
         "-sample_fmt", "s32", "-bits_per_raw_sample", "24", destination], timeout=180)
    probe = run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                 "-show_entries", "stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration",
                 "-of", "json", destination])
    streams = json.loads(probe.stdout).get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_name") != "flac" or (
            int(streams[0].get("sample_rate", 0)) != 48000 or
            int(streams[0].get("channels", 0)) != 2 or
            int(streams[0].get("bits_per_raw_sample", 0)) != 24):
        raise ValueError("D5 FLAC format mismatch (needs 48k/stereo/24-bit)")
    return {"file": destination.name, "sha256": digest(destination),
            "bytes": destination.stat().st_size, "codec": streams[0]}


def capture_d5(base: Path, head: Path, base_sha: str, head_sha: str, out: Path) -> None:
    pinned(base, base_sha)
    pinned(head, head_sha)
    before_path = base / "apps/studio/patches" / D5_PATCH
    after_path = head / "apps/studio/patches" / D5_PATCH
    if digest(before_path) != digest(after_path):
        raise ValueError("D5 source patch bytes differ between source checkouts")
    patch = json.loads(after_path.read_text(encoding="utf-8"))
    if MODULE not in [m.get("module") for m in patch["modules"]]:
        raise ValueError("prescribed D5 patch does not contain Macro")
    if digest(base / "bench/golden/render.py") != digest(head / "bench/golden/render.py"):
        raise ValueError("original 48k golden-script harness differs")
    sys.path.insert(0, str(head / "bench/golden"))
    import render as golden  # type: ignore
    if golden.ROOT.resolve() != head.resolve() or (
            golden.RATE, golden.BLOCK, golden.SECONDS, golden.SEED) != (
            48000, FRAMES, SECONDS, SEED):
        raise ValueError("golden renderer was changed or imported from wrong checkout")
    events = golden.events_for_patch(patch)
    if not events or any(x["frame"] >= SECONDS*48000 for x in events):
        raise ValueError("original D5 C4 script absent or out of bounds")
    dest = out / "d5"
    dest.mkdir(parents=True, exist_ok=True)
    script = dest / "c4-events.json"
    save(script, events)
    records = {}
    with tempfile.TemporaryDirectory(prefix="ws-macro-d5-") as tmp:
        for label, checkout, sha, patch_path in (
            ("before", base, base_sha, before_path),
            ("head", head, head_sha, after_path)):
            renderer = binaries(checkout, "wirescape_render")
            wav = Path(tmp) / (label + ".wav")
            run([renderer, "--patch", patch_path, "--script", script,
                 "--out", wav, "--rate", 48000, "--block", FRAMES,
                 "--seconds", SECONDS, "--seed", SEED], checkout, timeout=240)
            pcm = raw_pcm(wav, 48000, SECONDS)
            import numpy as np
            audio = np.frombuffer(pcm, dtype="<f4")
            if not np.isfinite(audio).all() or float(np.max(np.abs(audio))) <= 0:
                raise ValueError("D5 source render is silent or contains nonfinite output")
            raw = dest / (label + ".f32le")
            raw.write_bytes(pcm)
            records[label] = {"source_sha": sha, "renderer_sha256": digest(renderer),
                              "wav_sha256": digest(wav), "original_pcm": {
                                  "file": raw.name, "sha256": digest(raw),
                                  "bytes": len(pcm),
                                  "format": "interleaved stereo little-endian float32"},
                              "peak_fs": float(np.max(np.abs(audio))),
                              "rms_fs": float(np.sqrt(np.mean(audio.astype("float64")**2))),
                              "flac": encode_flac(wav, dest / (label + ".flac"))}
    save(dest / "manifest.json", {
        "schema": "wirescape/macro-non48-d5-226/1",
        "sources": {"before": base_sha, "head": head_sha},
        "source_harness_sha256": {
            "before": harness_sources(base), "head": harness_sources(head)},
        "compiled_macro_libraries": {
            "before": compiled_libraries(base), "head": compiled_libraries(head)},
        "patch_file": D5_PATCH, "patch_sha256": digest(after_path),
        "script_sha256": digest(script),
        "golden_harness_sha256": digest(head / "bench/golden/render.py"),
        "configuration": {"rate_hz": 48000, "block_frames": FRAMES,
                          "seconds": SECONDS, "seed": SEED, "channels": 2},
        "renders": records, "rendered_separately": True,
        "original_float_pcm_identical": records["before"]["original_pcm"]["sha256"] ==
                                        records["head"]["original_pcm"]["sha256"],
        "conversion_note": "FLAC is 24-bit listening copy; original float32 raw retained."})
    print("Actual separate 48k D5 PCM identical:",
          records["before"]["original_pcm"]["sha256"] ==
          records["head"]["original_pcm"]["sha256"], flush=True)


def require_raw(out: Path, item: dict) -> None:
    if item["bytes_original_pcm"] <= 0:
        raise ValueError("empty original PCM")
    path = out / item["file"]
    if digest(path) != item["sha256_gzip"]:
        raise ValueError("raw compressed SHA mismatch")
    data = gzip.decompress(path.read_bytes())
    if len(data) != item["bytes_original_pcm"] or (
            hashlib.sha256(data).hexdigest() != item["sha256_original_pcm"]):
        raise ValueError("raw original float PCM SHA/length mismatch")


def summarize(out: Path, base_sha: str, head_sha: str) -> dict:
    before = json.loads((out / "pitch-before.json").read_text())
    after = json.loads((out / "pitch-head.json").read_text())
    ir_before = json.loads((out / "ir-before.json").read_text())
    ir_after = json.loads((out / "ir-head.json").read_text())
    d5 = json.loads((out / "d5/manifest.json").read_text())
    for record, label in ((before, "before"), (after, "head"),
                          (ir_before, "before"), (ir_after, "head")):
        if record.get("source", {}).get("source_commit") != (
                base_sha if label == "before" else head_sha):
            raise ValueError("source pin mismatch in evidence record")
    for row in before["rows"] + after["rows"]:
        if row["status"] == "measured_output":
            require_raw(out, row["pcm"])
    b = {(r["model"], r["sample_rate_hz"], r["target_hz"]): r for r in before["rows"]}
    a = {(r["model"], r["sample_rate_hz"], r["target_hz"]): r for r in after["rows"]}
    if set(b) != set(matrix("before")) or set(a) != set(matrix("head")):
        raise ValueError("missing/duplicated 24 model x 5 pitch x 3 rate rows")
    pitch_rows, unchanged_48 = [], True
    for model in MODELS:
        for hz in TARGETS:
            base_row, ref = b[model,48000,hz], a[model,48000,hz]
            equal = (base_row["status"] == ref["status"] == "measured_output" and
                     base_row["pcm"]["sha256_original_pcm"] ==
                     ref["pcm"]["sha256_original_pcm"])
            unchanged_48 = unchanged_48 and equal
            for rate in (44100, 96000):
                r = a[model,rate,hz]
                measured = r["status"] == ref["status"] == "measured_output"
                f = r.get("estimator", {}).get("observed_hz")
                f48 = ref.get("estimator", {}).get("observed_hz")
                delta = (1200*math.log2(f/f48) if measured and
                         isinstance(f, (int,float)) and f>0 and
                         isinstance(f48, (int,float)) and f48>0 else None)
                pitch_rows.append({
                    "model": model, "target_hz": hz, "sample_rate_hz": rate,
                    "status": "unmeasured_pending_design_ruling" if delta is not None else "unmeasured",
                    "raw_estimator_delta_cents_vs48_diagnostic": delta,
                    "absolute_delta_within_two_cents_diagnostic": (
                        abs(delta) <= PITCH_MAX_DELTA_CENTS if delta is not None else None),
                    "reason": "fundamental meaningfulness/model applicability not yet ruled; "
                              "do not treat an inharmonic FFT peak as pitched/zero/pass",
                    "source_row_status": r["status"], "reference_48_status": ref["status"]})
    if d5.get("sources") != {"before": base_sha, "head": head_sha}:
        raise ValueError("D5 source pins mismatch")
    if d5["configuration"] != {"rate_hz":48000,"block_frames":128,
                                "seconds":10,"seed":37,"channels":2}:
        raise ValueError("D5 original golden configuration mismatch")
    for label in ("before","head"):
        for kind in ("original_pcm","flac"):
            record = d5["renders"][label][kind]
            if digest(out / "d5" / record["file"]) != record["sha256"]:
                raise ValueError("D5 PCM/FLAC SHA mismatch")
        codec = d5["renders"][label]["flac"].get("codec", {})
        if (codec.get("codec_name") != "flac" or
                int(codec.get("sample_rate", 0)) != 48000 or
                int(codec.get("channels", 0)) != 2 or
                int(codec.get("bits_per_raw_sample", 0)) != 24):
            raise ValueError("D5 FLAC media format provenance absent/invalid")
    d5_same = (d5["renders"]["before"]["original_pcm"]["sha256"] ==
               d5["renders"]["head"]["original_pcm"]["sha256"])
    if d5["original_float_pcm_identical"] != d5_same:
        raise ValueError("D5 claimed original PCM equality contradicts hashes")
    ir_b = {(r["sample_rate_hz"],r["voices"]):r for r in ir_before["rows"]}
    ir_a = {(r["sample_rate_hz"],r["voices"]):r for r in ir_after["rows"]}
    if set(ir_b)!={(48000,1),(48000,8)} or set(ir_a)!={(r,v) for r in RATES for v in (1,8)}:
        raise ValueError("instruction-rate/voice matrix incomplete")
    ir_summary=[]
    for rate in RATES:
        for voices in (1,8):
            row=ir_a[rate,voices]
            old=ir_b.get((rate,voices))
            ratio = (100*(row["ir_per_128_frame_block"] /
                          old["ir_per_128_frame_block"] - 1)
                     if old and row["status"]==old["status"]=="measured" else None)
            ir_summary.append({"rate_hz":rate,"voices":voices,"status":row["status"],
                               "after_ir_per_128":row.get("ir_per_128_frame_block"),
                               "before_ir_per_128":old.get("ir_per_128_frame_block") if old else None,
                               "growth_pct":ratio,
                               "rule":"<=3% only for 48000; non48 report only, no baseline"})
    for row in ir_before["rows"]+ir_after["rows"]:
        for original in row.get("callgrind",[]):
            path=out / original["file"]
            if digest(path)!=original["sha256"] or path.stat().st_size!=original["bytes"]:
                raise ValueError("original Callgrind file hash mismatch")
    result={"schema":"wirescape/macro-non48-226/1",
            "source":{"before":base_sha,"head":head_sha},
            "pitch_estimator":"original bench/offline/metrics.py::oscillator_metrics unchanged",
            "pitch_rule_max_abs_cents_vs48":PITCH_MAX_DELTA_CENTS,
            "pitch_status":"unmeasured_pending_architect_pitch_applicability_ruling",
            "pitch_reserved_question":"Which of the 24 Plaits models have a meaningful tonal "
                "fundamental for the unchanged FFT peak estimator? How should inharmonic/noise "
                "models be classified without interpreting their near-target peaks as pass?",
            "pitch_diagnostic_rows":pitch_rows,
            "head_non48_output_rows_measured":sum(
                r["status"]=="measured_output" for r in after["rows"]
                if r["sample_rate_hz"]!=48000),
            "head_non48_output_rows_required":24*len(TARGETS)*2,
            "48k_all_model_original_pcm_identical":unchanged_48,
            "ir_rows":ir_summary,
            "ir_48k_within_plus3":all(
                r["growth_pct"] is not None and r["growth_pct"]<=IR_48_MAX_GROWTH_PERCENT
                for r in ir_summary if r["rate_hz"]==48000),
            "d5_original_pcm_identical":d5_same,
            "d5_pair_exists":True,
            "full_acceptance":False,
            "reason":"pitch applicability reserved; B4 compatibility handoff, Architect and lead review still gate S7.4"}
    save(out / "summary.json", result)
    return result


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",required=True,
                   choices=("check","pitch","ir","d5","summary"))
    p.add_argument("--checkout",type=Path)
    p.add_argument("--label",choices=("before","head"))
    p.add_argument("--base",type=Path)
    p.add_argument("--head",type=Path)
    p.add_argument("--base-sha")
    p.add_argument("--head-sha")
    p.add_argument("--out",type=Path)
    args=p.parse_args(argv)
    if args.mode=="check":
        # Safe on main and PR heads; does not inspect native libraries,
        # choose #212 source pins or claim rate support.
        path=ROOT/"bench/offline/run_all.py"
        source=path.read_text()
        for banned in ("Macro Oscillator requires 48000 Hz",
                       "Macro Oscillator prepare() requires 48000 Hz",
                       "macro_models\": \"0..23 (48000 Hz only)"):
            if banned in source:raise ValueError("obsolete Macro off-rate guard still exists")
        if "oscillator_metrics(audio, hz, rate)" not in source:
            raise ValueError("existing pitch estimator call removed")
        print("Macro collector static preflight passed; no native capture/pin performed")
        return 0
    if args.out is None:
        p.error("evidence modes require --out")
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if not args.base_sha or not args.head_sha:
        p.error("source release missing: both --base-sha and --head-sha required")
    base_sha,head_sha=verify_sha(args.base_sha),verify_sha(args.head_sha)
    if base_sha==head_sha:
        p.error("before and head source commits must differ")
    if args.mode in ("pitch","ir"):
        if args.checkout is None or args.label is None:
            p.error("pitch/ir require a single source --checkout and --label")
        checkout=args.checkout.resolve()
        pin=base_sha if args.label=="before" else head_sha
        (capture_pitch if args.mode=="pitch" else capture_ir)(
            checkout,args.label,pin,out)
    elif args.mode=="d5":
        if args.base is None or args.head is None:
            p.error("d5 requires --base and --head checkout")
        capture_d5(args.base.resolve(),args.head.resolve(),base_sha,head_sha,out)
    else:
        result=summarize(out,base_sha,head_sha)
        print("Macro #226 pinned evidence summary; output rows %d; 48k identical=%s; "
              "pitch remains reserved=%s" % (
                result["head_non48_output_rows_measured"],
                result["48k_all_model_original_pcm_identical"],
                result["pitch_status"]),flush=True)
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        print("Macro #226 collector failure: %s" % e,file=sys.stderr)
        raise SystemExit(1)
