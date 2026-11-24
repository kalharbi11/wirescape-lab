#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""T0.5 R2 device-free Engine::render impulse and silent-tail collector (Linux).

This file compiles only the bench-local probe source, linking the existing
Release engine2 library. It changes no native target or product file.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

import numpy as np

from metrics import r2_impulse_metrics, r2_tail_metrics

ROOT = Path(__file__).resolve().parents[2]
PROBE_SOURCE = Path(__file__).with_name("r2_engine_probe.cpp")
RATES = (44100, 48000, 96000)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def find_library(build, short):
    """Discover the *actual* built runtime library; never substitute a module."""
    matches = sorted(Path(build).rglob("libws2_" + short + ".so"))
    return matches[0] if len(matches) == 1 else None


def build_probe(build, destination):
    library = sorted(Path(build).rglob("libwirescape_engine2.a"))
    if len(library) != 1:
        raise RuntimeError("expected one Release libwirescape_engine2.a, found " +
                           str(len(library)))
    compiler = shutil.which(os.environ.get("CXX", "c++"))
    if not compiler:
        raise RuntimeError("host C++ compiler not available")
    binary = Path(destination) / "wirescape-r2-engine-probe"
    command = [
        compiler, "-std=c++17", "-O2", str(PROBE_SOURCE), str(library[0]),
        "-I" + str(ROOT / "sdk/include"),
        "-I" + str(ROOT / "sdk"),
        "-I" + str(ROOT / "engine"),
        "-pthread", "-ldl", "-o", str(binary),
    ]
    result = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, check=False,
                            timeout=120)
    if result.returncode != 0 or not binary.is_file():
        detail = " ".join(result.stderr.split())[-1500:]
        raise RuntimeError("R2 bench-only probe compile failed: " + detail)
    return binary, {
        "compiler": Path(compiler).name,
        "probe_sha256": sha256(PROBE_SOURCE),
        "engine2_archive_sha256": sha256(library[0]),
        "compile_flags": "-std=c++17 -O2 -pthread -ldl",
        "source": "bench/offline/r2_engine_probe.cpp",
    }


def invoke(binary, mode, ident, library, rate, output_path):
    command = [str(binary), mode, ident, str(library), str(rate),
               "128", str(output_path)]
    try:
        result = subprocess.run(
            command, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, cwd=ROOT, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "probe_execution_error", "reason": str(exc)[:500]}
    if result.returncode:
        return {"status": "probe_execution_error",
                "exit_code": result.returncode,
                "reason": " ".join(result.stderr.split())[-900:]}
    try:
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError("probe stdout must contain one JSON record")
        row = json.loads(lines[0])
        if row.get("module") != ident or row.get("rate_hz") != rate:
            raise ValueError("probe module/rate identity mismatch")
        if row.get("mode") != mode:
            raise ValueError("probe mode mismatch")
        if row.get("status") not in ("measured", "not_applicable"):
            raise ValueError("unexpected probe status")
        return row
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "probe_malformed_result", "reason": str(exc)[:400]}


def _port_present(descriptor, port):
    return any(p.get("type") == "WS2_AUDIO" for p in descriptor.get(port, ()))


def collect_r2(build, desc, quick, rates=RATES):
    """Return exact impulse rows and FTZ tail rows, every module and rate."""
    impulse, tails = [], []
    os_name = platform.system()
    eligible = sorted(desc)
    with tempfile.TemporaryDirectory(prefix="wirescape-r2-") as directory:
        binary = None
        source = None
        build_failure = None
        for ident in eligible:
            d = desc[ident]
            audio_in = _port_present(d, "inputs")
            audio_out = _port_present(d, "outputs")
            suffix = ident.rsplit(".", 1)[-1]
            library = find_library(build, suffix) if os_name == "Linux" else None
            for rate in rates:
                metadata = {
                    "module": ident, "sample_rate_hz": rate,
                    "block_frames": 128, "input_mode": "bench_source_engine_graph",
                    "engine_process_mode": "production_Engine_render",
                }
                if not audio_in:
                    result = {"status": "not_applicable",
                              "reason": "descriptor has no WS2_AUDIO input"}
                elif not audio_out:
                    result = {"status": "not_applicable",
                              "reason": "descriptor has no WS2_AUDIO output tap"}
                elif os_name != "Linux":
                    result = {"status": "runner_not_in_r2_measurement_scope",
                              "reason": "R2 measured facts are collected on hosted Linux x64/ARM64"}
                elif quick:
                    result = {"status": "not_run_quick_mode",
                              "reason": "full 1s + 2s impulse and 5x(1s + 5s) tail only in full mode"}
                elif library is None:
                    result = {"status": "not_built_runtime_module",
                              "reason": "expected unique libws2_" + suffix + ".so not found"}
                else:
                    result = None
                if result is not None:
                    impulse.append({**metadata, "metric": "r2_impulse", **result})
                    tails.append({**metadata, "metric": "r2_tail", **result})
                    continue
                if binary is None and build_failure is None:
                    try:
                        binary, source = build_probe(build, directory)
                    except (OSError, ValueError, RuntimeError,
                            subprocess.TimeoutExpired) as exc:
                        build_failure = str(exc)[:1500]
                if build_failure:
                    row = {"status": "probe_compile_error",
                           "reason": build_failure}
                    impulse.append({**metadata, "metric": "r2_impulse", **row})
                    tails.append({**metadata, "metric": "r2_tail", **row})
                    continue
                path = Path(directory) / "capture.f32le"
                record = invoke(binary, "impulse", ident, library, rate, path)
                if record.get("status") == "measured":
                    try:
                        if (record["input_nonzero_frames"] != 1 or
                                record["one_second_pre_silence_frames"] != rate or
                                record["capture_frames"] != 2 * rate or
                                record["faults"] != 0):
                            raise ValueError("impulse frame, source or engine-fault mismatch")
                        measured = np.fromfile(path, dtype="<f4")
                        record.update(r2_impulse_metrics(measured, rate))
                        record["status"] = "measured"
                    except (ValueError, KeyError, OSError, TypeError) as exc:
                        record = {"status": "probe_invalid_impulse",
                                  "reason": str(exc)[:450]}
                impulse.append({**metadata, "metric": "r2_impulse",
                                "module_library_sha256": sha256(library),
                                "probe_source": source, **record})
                tail = invoke(binary, "tail", ident, library, rate, path)
                if tail.get("status") == "measured":
                    try:
                        if (tail["active_frames"] != rate or
                                tail["zero_frames"] != 5 * rate or
                                tail["zero_input_verified"] is not True or
                                tail["production_ftz_mode"] not in
                                ("engine_render_mxcsr_ftz_daz",
                                 "engine_render_fpcr_fz")):
                            raise ValueError("tail source duration/FTZ verification mismatch")
                        tail.update(r2_tail_metrics(tail["repeats"]))
                        if any(x["faults"] != 0 for x in tail["repeats"]):
                            raise ValueError("engine reported nonzero tail faults")
                    except (ValueError, KeyError, TypeError) as exc:
                        tail = {"status": "probe_invalid_tail",
                                "reason": str(exc)[:450]}
                tails.append({**metadata, "metric": "r2_tail",
                              "module_library_sha256": sha256(library),
                              "probe_source": source, **tail})
    return impulse, tails
