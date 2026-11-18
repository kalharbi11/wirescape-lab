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
HEAD = "32abedde03e37a8d85510244c61d782652ed32c8"
RATES = (44100, 48000, 96000)
DAMPINGS = (0.1, 0.4, 0.7, 0.9)
R2_METHOD = "first suffix-maximum abs(sample) <= peak * 1e-3"
TAIL_METHOD = "median of 5 (silent full-block median ns / active full-block median ns)"
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


def damping_key(damping: float) -> str:
    if damping not in DAMPINGS:
        raise ValueError("only contracted A13 damping settings supported")
    return "%.1f" % damping


def make_damping_probe(checkout: Path, temporary: Path, out: Path) -> tuple[Path, dict]:
    """Produce the original pinned production probe with ONE verified parameter insertion.

    The native module, Engine, harness at both source pins, test signal and both
    original render loops are untouched. The source copy is included in the artifact.
    Only the module's damping field is set before the original reset/render.
    """
    original = checkout / "bench/offline/r2_engine_probe.cpp"
    before = original.read_text(encoding="utf-8")
    marker = "    engine->reset(); // Start one full second of silence before the single impulse."
    if before.count(marker) != 1:
        raise ValueError("pinned R2 production probe reset seam changed; no substitution")
    injection = r"""
    // #193/A13 collector-only setting, outside all render/source timing loops.
    // Original default=0.4 uses the unchanged pinned probe (not this source).
    const char* setting = std::getenv("WS_R2_DAMPING");
    need(setting != nullptr, "missing A13 damping setting");
    char* end = nullptr;
    const float damping = std::strtof(setting, &end);
    need(end != setting && *end == '\0' && std::isfinite(damping) &&
         (damping == 0.1f || damping == 0.7f || damping == 0.9f),
         "unexpected A13 damping setting");
    bool found_damping = false;
    for(uint32_t i=0; i<c.desc->param_count; ++i) {
        if(std::strcmp(c.desc->params[i].id,"damping")==0) {
            need(engine->set_parameter(2,i,damping),
                 "cannot set A13 Reverb damping in production engine graph");
            found_damping = true;
        }
    }
    need(found_damping, "target module has no damping parameter");
"""
    derived = before.replace(marker, injection + marker)
    target = temporary / "bench/offline/r2_engine_probe.cpp"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Preserve pinned relative include ../../native without writing to the worktree.
    (temporary / "native").symlink_to((checkout / "native").resolve(), target_is_directory=True)
    target.write_text(derived, encoding="utf-8")
    retained = out / "harness/r2_engine_probe_a13.cpp"
    retained.parent.mkdir(parents=True, exist_ok=True)
    if retained.exists() and retained.read_bytes() != target.read_bytes():
        raise ValueError("before/head generated production probe differs")
    shutil.copyfile(target, retained)
    return target, {
        "source": "original pinned bench/offline/r2_engine_probe.cpp + one A13 pre-reset damping assignment",
        "original_source_sha256": digest(original),
        "effective_source_sha256": digest(retained),
        "retained_source": retained.relative_to(out).as_posix(),
        "source_changed_in_checkout": False,
        "modified_render_or_stimulus": False,
    }


def raw_suffix_r2(path: Path, rate: int) -> dict:
    """Independent detached replay of the EXACT original suffix-max R2 definition."""
    from array import array
    import math
    if path.stat().st_size != 2 * rate * 4:
        raise ValueError("R2 original PCM byte length mismatch")
    samples = array("f")
    samples.frombytes(path.read_bytes())
    if sys.byteorder != "little":
        samples.byteswap()
    if len(samples) != 2 * rate or any(not math.isfinite(x) for x in samples):
        raise ValueError("R2 raw float32 contains nonfinite or wrong frame count")
    absolute = [abs(float(x)) for x in samples]
    peak = max(absolute)
    if not peak:
        raise ValueError("R2 original PCM is silent")
    first_peak = absolute.index(peak)
    threshold = peak * 1e-3
    remaining = 0.0
    crossing = None
    for index in range(len(absolute) - 1, first_peak - 1, -1):
        remaining = max(remaining, absolute[index])
        if remaining <= threshold:
            crossing = index
    if crossing is None:
        raise ValueError("original R2 -60 dB suffix envelope not reached inside 2 s")
    return {"capture_frames": len(samples), "peak_fs": peak,
            "time_to_minus60_db_re_peak_ms": crossing / rate * 1000.0,
            "decay_status": "reached", "method": R2_METHOD,
            "nan_count": 0, "inf_count": 0, "nonfinite_samples": 0}


def verify_r2_row(out: Path, label: str, row: dict) -> float:
    import math
    rate, damping = row.get("sample_rate_hz"), row.get("damping")
    if type(rate) is not int or rate not in RATES or damping not in DAMPINGS:
        raise ValueError("missing R2 rate/damping identity")
    if (row.get("module") != MODULE or row.get("metric") != "r2_impulse" or
            row.get("engine_process_mode") != "production_Engine_render" or
            row.get("status") != "measured" or row.get("decay_status") != "reached" or
            row.get("input_nonzero_frames") != 1 or
            row.get("one_second_pre_silence_frames") != rate or
            row.get("capture_frames") != 2 * rate or row.get("faults") != 0 or
            row.get("method") != R2_METHOD):
        raise ValueError("original R2 production stimulus/method/identity mismatch")
    raw = row.get("raw_capture")
    expected_path = "raw/r2-%s-d%s-%d.f32le" % (
        label, damping_key(damping).replace(".", ""), rate)
    if not isinstance(raw, dict) or raw.get("path") != expected_path:
        raise ValueError("R2 capture path/label/damping mismatch")
    path = out / expected_path
    if path.stat().st_size != raw.get("bytes") or digest(path) != raw.get("sha256_float32_pcm"):
        raise ValueError("R2 raw PCM byte length/SHA mismatch")
    actual = raw_suffix_r2(path, rate)
    for key in ("capture_frames", "method", "decay_status",
                "nan_count", "inf_count", "nonfinite_samples"):
        if row.get(key) != actual[key]:
            raise ValueError("detached R2 original PCM field mismatch: " + key)
    for key in ("peak_fs", "time_to_minus60_db_re_peak_ms"):
        value = row.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or not math.isclose(
                value, actual[key], rel_tol=0, abs_tol=1e-9):
            raise ValueError("detached R2 original PCM timing/peak mismatch: " + key)
    return actual["time_to_minus60_db_re_peak_ms"]


def verify_tail_row(row: dict, rate: int, damping: float) -> None:
    """Recompute actual 5-repeat timing/counters; shared probe emits no tail PCM."""
    import math
    import statistics
    if (row.get("metric") != "r2_tail" or row.get("module") != MODULE or
            row.get("sample_rate_hz") != rate or row.get("damping") != damping or
            row.get("engine_process_mode") != "production_Engine_render" or
            row.get("status") != "measured" or row.get("active_frames") != rate or
            row.get("zero_frames") != 5 * rate or row.get("zero_input_verified") is not True or
            row.get("production_ftz_mode") not in
            ("engine_render_mxcsr_ftz_daz", "engine_render_fpcr_fz") or
            row.get("repeat_count") != 5 or row.get("method") != TAIL_METHOD):
        raise ValueError("R2 tail production mode/source identity mismatch")
    repeats = row.get("repeats")
    if not isinstance(repeats, list) or len(repeats) != 5:
        raise ValueError("R2 tail must contain five real full timing repeats")
    ratios = []
    for index, record in enumerate(repeats):
        if (record.get("repeat") != index or record.get("faults") != 0 or
                type(record.get("active_full_blocks")) is not int or
                record["active_full_blocks"] <= 0 or
                type(record.get("silent_full_blocks")) is not int or
                record["silent_full_blocks"] <= 0 or
                record.get("subnormal_output_samples") != 0 or
                record.get("nonfinite_output_samples") != 0):
            raise ValueError("R2 tail repeat count/fault/source mismatch")
        a, b, ratio = (record.get(k) for k in (
            "active_median_ns", "silent_median_ns", "silent_over_active"))
        if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0
               for x in (a, b, ratio)) or not math.isclose(
                ratio, b/a, rel_tol=2e-6, abs_tol=0):
            raise ValueError("R2 tail actual repeated timing ratio mismatch")
        ratios.append(float(ratio))
    expected = statistics.median(ratios)
    observed = row.get("median_silent_over_active_block_cost")
    published = row.get("individual_silent_over_active_ratios")
    if (type(observed) not in (int, float) or not math.isclose(
            observed, expected, rel_tol=0, abs_tol=1e-9) or
            not isinstance(published, list) or len(published) != 5 or
            any(type(x) not in (int, float) or not math.isclose(
                float(x), ratios[i], rel_tol=0, abs_tol=1e-9)
                for i, x in enumerate(published)) or
            row.get("subnormal_output_samples_all_repeats") != 0 or
            row.get("nonfinite_output_samples_all_repeats") != 0):
        raise ValueError("detached R2 tail aggregate contradicts original repeats")


def capture_r2(checkout: Path, label: str, out: Path) -> None:
    source_commit = pinned(checkout, label)
    build = checkout / "build/native"
    if not (build / "CMakeCache.txt").is_file():
        raise FileNotFoundError("pinned Release native build missing: " + label)
    # Runs once per pinned checkout/process. No cached cross-source imports.
    sys.path.insert(0, str(checkout / "bench/offline"))
    import r2_probe  # type: ignore
    import run_all  # type: ignore
    from metrics import r2_impulse_metrics  # type: ignore
    import numpy as np

    if r2_probe.ROOT.resolve() != checkout.resolve() or run_all.ROOT.resolve() != checkout.resolve():
        raise ValueError("collector loaded an unpinned R2 production harness")
    desc = run_all.descriptors()
    if MODULE not in desc:
        raise ValueError("missing source descriptor for " + MODULE)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    impulses, tails = [], []
    values_by_damping = {}
    original_invoke = r2_probe.invoke
    original_probe = r2_probe.PROBE_SOURCE
    original_env = os.environ.get("WS_R2_DAMPING")
    with tempfile.TemporaryDirectory(prefix="mt193-a13-probe-") as td:
        generated_probe, generation = make_damping_probe(checkout, Path(td), out)
        try:
            for damping in DAMPINGS:
                key = damping_key(damping)
                original_bytes = {}

                def preserve_impulse(binary, mode, ident, library, rate, output_path):
                    record = original_invoke(binary, mode, ident, library, rate, output_path)
                    if mode == "impulse" and ident == MODULE and record.get("status") == "measured":
                        raw = out / "raw" / ("r2-%s-d%s-%d.f32le" %
                                            (label, key.replace(".", ""), rate))
                        shutil.copyfile(output_path, raw)
                        if raw.stat().st_size != 2 * rate * 4:
                            raise ValueError("actual R2 raw PCM size mismatch")
                        original_bytes[rate] = {
                            "path": raw.relative_to(out).as_posix(),
                            "sha256_float32_pcm": digest(raw), "bytes": raw.stat().st_size}
                    return record

                # Original default (0.4): build and run the byte-for-byte pinned
                # upstream probe. Other A13 settings: a one-seam, retained, hashed
                # source copy setting damping *before* the original engine reset.
                if damping == 0.4:
                    r2_probe.PROBE_SOURCE = original_probe
                    os.environ.pop("WS_R2_DAMPING", None)
                    probe_sha = digest(original_probe)
                else:
                    r2_probe.PROBE_SOURCE = generated_probe
                    os.environ["WS_R2_DAMPING"] = key
                    probe_sha = generation["effective_source_sha256"]
                r2_probe.invoke = preserve_impulse
                packet, tail_packet = r2_probe.collect_r2(
                    build, {MODULE: desc[MODULE]}, quick=False, rates=RATES)
                if len(packet) != 3 or len(tail_packet) != 3 or set(original_bytes) != set(RATES):
                    raise ValueError("incomplete real A13 production rate/PCM/tail rows")
                for row in packet:
                    rate = row["sample_rate_hz"]
                    if row.get("status") != "measured" or row.get("probe_source", {}).get(
                            "probe_sha256") != probe_sha:
                        raise ValueError("missing measured row or mismatched compiled production probe")
                    raw = original_bytes[rate]
                    measured = r2_impulse_metrics(np.fromfile(out / raw["path"], dtype="<f4"), rate)
                    if measured["time_to_minus60_db_re_peak_ms"] != row[
                            "time_to_minus60_db_re_peak_ms"]:
                        raise ValueError("original pinned R2 estimator contradicts original raw bytes")
                    row.update(damping=damping, raw_capture=raw,
                               effective_probe_sha256=probe_sha,
                               probe_kind="original_pinned" if damping == 0.4
                               else "A13_collector_damping_only")
                    verify_r2_row(out, label, row)
                    impulses.append(row)
                for row in tail_packet:
                    row.update(damping=damping, effective_probe_sha256=probe_sha,
                               probe_kind="original_pinned" if damping == 0.4
                               else "A13_collector_damping_only")
                    verify_tail_row(row, row["sample_rate_hz"], damping)
                    tails.append(row)
                values = validate_impulses(packet)
                values_by_damping[key] = {str(rate): values[rate] for rate in RATES}
                print("%s damping=%s production suffix R2 ms %s; spread %.6f%%" %
                      (label, key, [values[rate] for rate in RATES],
                       spread_percent(values)), flush=True)
        finally:
            r2_probe.invoke = original_invoke
            r2_probe.PROBE_SOURCE = original_probe
            if original_env is None:
                os.environ.pop("WS_R2_DAMPING", None)
            else:
                os.environ["WS_R2_DAMPING"] = original_env
    if len(impulses) != 12 or len(tails) != 12:
        raise ValueError("A13 requires all four damping × three production rates")
    meta = run_all.provenance(build)
    if meta["commit"] != source_commit:
        raise ValueError("R2 production provenance returned wrong source commit")
    default = {int(rate): ms for rate, ms in values_by_damping["0.4"].items()}
    write_json(out / ("r2-%s.json" % label), {
        "schema": "wirescape/s7.1-evidence-193/2",
        "label": label, "source_commit": source_commit,
        "source_harness_sha256": source_hashes(checkout),
        "scope": "production_Engine_render nonquick R2, fx.reverb; A13 four dampings",
        "quick": False, "sample_rates_hz": list(RATES), "dampings": list(DAMPINGS),
        "damping_probe": generation, "provenance": meta,
        "impulse": impulses, "tail": tails,
        "times_ms": {str(k): default[k] for k in RATES},
        "spread_percent_of_48k": spread_percent(default),
        "times_ms_by_damping": values_by_damping,
        "spread_percent_by_damping": {
            key: spread_percent({int(r): ms for r, ms in values.items()})
            for key, values in values_by_damping.items()},
    })



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


def verify_d5(out: Path) -> dict | None:
    """P2: never report an intact D5 pair from a manifest alone."""
    import math
    from array import array
    manifest = out / "d5/manifest.json"
    if not manifest.is_file():
        if platform.machine().lower() in ("x86_64", "amd64"):
            raise ValueError("D5 pair required on Linux x64")
        return None
    d5 = json.loads(manifest.read_text(encoding="utf-8"))
    if (d5.get("sources") != {"before": BASE, "head": HEAD} or
            d5.get("configuration") != {
                "sample_rate_hz": 48000, "block_frames": 128, "seconds": 10,
                "seed": 37, "channels": 2} or
            d5.get("patch") != PATCH or d5.get("rendered_separately") is not True or
            set(d5.get("renders", {})) != {"before", "head"}):
        raise ValueError("D5 source/configuration/independent-render manifest mismatch")
    pcm_hashes = []
    for label in ("before", "head"):
        entry = d5["renders"][label]
        if (entry.get("source_commit") != (BASE if label == "before" else HEAD) or
                entry.get("source_patch_sha256") != d5.get("patch_sha256") or
                type(entry.get("renderer_sha256")) is not str or
                len(entry["renderer_sha256"]) != 64):
            raise ValueError("D5 render source/hash pin mismatch")
        for kind, extension in (("original_pcm", "f32le"), ("flac", "flac")):
            item = entry.get(kind)
            required_name = "%s.%s" % (label, extension)
            if not isinstance(item, dict) or item.get("path") != required_name:
                raise ValueError("D5 %s %s path is absent/malformed" % (label, kind))
            path = out / "d5" / required_name
            if (not path.is_file() or type(item.get("bytes")) is not int or
                    path.stat().st_size != item["bytes"] or
                    digest(path) != item.get("sha256")):
                raise ValueError("D5 %s %s missing/size/SHA mismatch" % (label, kind))
            if kind == "original_pcm":
                if (item.get("format") != "interleaved stereo little-endian float32" or
                        item["bytes"] != 48000 * 10 * 2 * 4):
                    raise ValueError("D5 original float32 PCM format/length mismatch")
                audio = array("f")
                audio.frombytes(path.read_bytes())
                if sys.byteorder != "little":
                    audio.byteswap()
                if (not all(math.isfinite(x) for x in audio) or
                        not any(x != 0 for x in audio)):
                    raise ValueError("D5 source float PCM is silent/nonfinite")
                pcm_hashes.append(item["sha256"])
            else:
                if path.open("rb").read(4) != b"fLaC":
                    raise ValueError("D5 FLAC header missing/invalid")
                codec = item.get("codec", {})
                if (codec.get("codec_name") != "flac" or
                        int(codec.get("sample_rate", 0)) != 48000 or
                        int(codec.get("channels", 0)) != 2 or
                        int(codec.get("bits_per_raw_sample", 0)) != 24):
                    raise ValueError("D5 48k stereo 24-bit FLAC metadata mismatch")
    identical = pcm_hashes[0] == pcm_hashes[1]
    if d5.get("float32_pcm_identical") is not identical or not identical:
        raise ValueError("D5 original float PCM before/head identity failed")
    script = d5.get("script")
    if script != "c4-events.json" or digest(out / "d5/c4-events.json") != d5.get(
            "script_sha256"):
        raise ValueError("D5 scripted golden C4 source/hash mismatch")
    return d5


def verify_report(out: Path, report: dict, label: str) -> tuple[dict, dict]:
    if (report.get("schema") != "wirescape/s7.1-evidence-193/2" or
            report.get("source_commit") != (BASE if label == "before" else HEAD) or
            report.get("label") != label or report.get("quick") is not False or
            report.get("dampings") != list(DAMPINGS) or
            report.get("sample_rates_hz") != list(RATES)):
        raise ValueError("wrong source/nonquick A13 report or missing damping matrix")
    hashes = report.get("source_harness_sha256", {})
    if (not isinstance(hashes, dict) or set(hashes) != set(SOURCE_FILES) or
            any(type(x) is not str or len(x) != 64 for x in hashes.values())):
        raise ValueError("R2 original source harness hash evidence incomplete")
    probe = report.get("damping_probe", {})
    path = probe.get("retained_source")
    if (path != "harness/r2_engine_probe_a13.cpp" or
            probe.get("original_source_sha256") != hashes[
                "bench/offline/r2_engine_probe.cpp"] or
            digest(out / path) != probe.get("effective_source_sha256")):
        raise ValueError("A13 collector-only effective source mismatch")
    impulses, tails = report.get("impulse"), report.get("tail")
    if not isinstance(impulses, list) or not isinstance(tails, list):
        raise ValueError("missing production impulse/tail arrays")
    expected = {(d, r) for d in DAMPINGS for r in RATES}
    imap = {(row.get("damping"), row.get("sample_rate_hz")): row for row in impulses}
    tmap = {(row.get("damping"), row.get("sample_rate_hz")): row for row in tails}
    if len(impulses) != 12 or len(tails) != 12 or set(imap) != expected or set(tmap) != expected:
        raise ValueError("incomplete/duplicated A13 damping × rate matrix")
    measures = {}
    for damping in DAMPINGS:
        key = damping_key(damping)
        rows = {}
        for rate in RATES:
            row, tail = imap[damping, rate], tmap[damping, rate]
            expected_sha = (hashes["bench/offline/r2_engine_probe.cpp"]
                            if damping == 0.4 else probe["effective_source_sha256"])
            for item in (row, tail):
                if (item.get("effective_probe_sha256") != expected_sha or
                        item.get("probe_source", {}).get("probe_sha256") != expected_sha or
                        item.get("probe_kind") != (
                            "original_pinned" if damping == 0.4 else "A13_collector_damping_only")):
                    raise ValueError("A13 effective native probe source attribution mismatch")
            rows[rate] = verify_r2_row(out, label, row)
            verify_tail_row(tail, rate, damping)
        if report.get("times_ms_by_damping", {}).get(key) != {
                str(rate): rows[rate] for rate in RATES}:
            raise ValueError("original R2 damping timing summary contradicts raw PCM")
        spread = spread_percent(rows)
        if not isinstance(report.get("spread_percent_by_damping", {}).get(key), (int, float)) or abs(
                report["spread_percent_by_damping"][key] - spread) > 1e-9:
            raise ValueError("reported R2 damping spread contradicts raw PCM")
        measures[key] = rows
    default = measures["0.4"]
    if report.get("times_ms") != {str(r): default[r] for r in RATES} or abs(
            report.get("spread_percent_of_48k", -999) - spread_percent(default)) > 1e-9:
        raise ValueError("original default R2 summary altered")
    return measures, imap


def summarize(out: Path) -> None:
    a = json.loads((out / "r2-before.json").read_text(encoding="utf-8"))
    b = json.loads((out / "r2-head.json").read_text(encoding="utf-8"))
    if a.get("source_harness_sha256") != b.get("source_harness_sha256"):
        raise ValueError("before/head original R2 or Golden source harness differs")
    before, b_rows = verify_report(out, a, "before")
    after, h_rows = verify_report(out, b, "head")
    compare = []
    unchanged = True
    regressions = []
    for damping in DAMPINGS:
        key = damping_key(damping)
        base, head = before[key], after[key]
        base_spread, head_spread = spread_percent(base), spread_percent(head)
        spread_ok = head_spread <= base_spread + 1e-9
        if not spread_ok:
            regressions.append("damping %s spread %.9f > baseline %.9f" %
                               (key, head_spread, base_spread))
        matched_rate_rows = []
        for rate in RATES:
            # "No row worse than matched base": evaluate absolute deviation
            # from its own 48k reference, never raw-decay duration.
            old_deviation = abs(base[rate] - base[48000]) / base[48000] * 100.0
            new_deviation = abs(head[rate] - head[48000]) / head[48000] * 100.0
            ok = new_deviation <= old_deviation + 1e-9
            if not ok:
                regressions.append("damping %s rate %d deviation %.9f > base %.9f" %
                                   (key, rate, new_deviation, old_deviation))
            matched_rate_rows.append({
                "rate_hz": rate, "before_ms": base[rate], "head_ms": head[rate],
                "before_deviation_percent_of_48k": old_deviation,
                "head_deviation_percent_of_48k": new_deviation,
                "no_worse_than_matched_base": ok})
        initial = b_rows[damping, 48000]["raw_capture"]["sha256_float32_pcm"]
        final = h_rows[damping, 48000]["raw_capture"]["sha256_float32_pcm"]
        same = initial == final
        unchanged = unchanged and same
        if not same:
            regressions.append("damping %s original 48k R2 float PCM differs" % key)
        compare.append({
            "damping": damping, "before_spread_percent": base_spread,
            "head_spread_percent": head_spread,
            "spread_no_worse_than_matched_base": spread_ok,
            "rate_rows": matched_rate_rows,
            "48k_original_float32_pcm_identical": same,
            "before_48k_raw_sha256": initial, "head_48k_raw_sha256": final,
        })
    d5 = verify_d5(out)
    default_spread = spread_percent(after["0.4"])
    default_ok = default_spread <= 5.0
    if not default_ok:
        regressions.append("default damping0.4 R2 spread %.9f > 5%%" % default_spread)
    if d5 is not None and not d5["float32_pcm_identical"]:
        regressions.append("original D5 48k PCM changed")
    success = not regressions
    record = {
        "schema": "wirescape/s7.1-evidence-193/2",
        "sources": {"before": BASE, "head": HEAD},
        "rate_hz": list(RATES), "dampings": list(DAMPINGS),
        "before_ms": {str(r): before["0.4"][r] for r in RATES},
        "head_ms": {str(r): after["0.4"][r] for r in RATES},
        "before_spread_percent": spread_percent(before["0.4"]),
        "head_spread_percent": default_spread,
        "r2_max_spread_percent": 5.0,
        "r2_target_met": default_ok,
        "r2_48k_original_pcm_identical": unchanged,
        "d5_flac_pair_staged": d5 is not None,
        "d5_original_pcm_identical": d5["float32_pcm_identical"] if d5 else None,
        "a13_damping_rows": compare,
        "a13_no_damping_regressions": all(
            x["spread_no_worse_than_matched_base"] and
            all(y["no_worse_than_matched_base"] for y in x["rate_rows"]) for x in compare),
        "recomputation": "detached suffix-max float32 PCM and five actual tail repeats per rate/damping",
        "criterion_met": success,
        "violations": regressions,
        "runner": {"system": platform.system(), "machine": platform.machine()},
    }
    write_json(out / "summary.json", record)
    print("A13 actual production suffix R2 damping comparisons:", compare, flush=True)
    print("Original 48k all dampings identical=%s; 0.4 spread %.9f%%; D5 pair=%s" %
          (unchanged, default_spread, d5 is not None), flush=True)
    if not success:
        raise ValueError("actual pinned S7.1 criterion failed: " + "; ".join(regressions))



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
