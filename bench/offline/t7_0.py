#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""M7 T7.0 device-off CHAOS alias and switch-click before-fact capture.

Runs the existing two-second offline oscillator probe at the exact requested
three rates, taking the same alias_floor_dbfs and RMS calculations. The second
probe records switch-centered high-pass peaks; it makes no DSP changes.
Never backfills an omitted case from historical aggregates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from metrics import switch_click_metrics
from run_all import (ROOT, descriptors, executable, build_module_patch,
                     oscillator_sections, provenance, run_wav)

RATES = (44100, 48000, 96000)
HERTZ = (110, 1760, 3520, 7040)
WAVES = ("saw", "square")
MODULE = "essentials.chaos_lite"
CASES = tuple((rate, wave, hz) for rate in RATES for wave in WAVES for hz in HERTZ)
SWITCHES = (
    ("essentials.quad_vca", "mode1", 0, 1, {"level1": 1}),
    ("fx.delay", "mode", 0, 1, {"mix": 1, "feedback": .4}),
    ("fx.delay", "division", 5, 6, {"mix": 1, "feedback": .4}),
    ("fx.delay", "tone", 0, 1, {"mix": 1, "feedback": .4}),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_chaos(document: dict, expected_head: str) -> list[dict]:
    """Exactly 24 observations or explicitly unavailable cases, never extrapolation."""
    if document.get("provenance", {}).get("commit") != expected_head:
        raise ValueError("oscillator artifact source commit does not match exact build head")
    if document.get("section") != "oscillators":
        raise ValueError("not an oscillator artifact")
    observed = {}
    for row in document.get("rows", []):
        if row.get("module") != MODULE or row.get("waveform") not in WAVES:
            continue
        key = (row.get("sample_rate_hz"), row.get("waveform"), row.get("target_hz"))
        if key not in CASES:
            continue
        if key in observed:
            raise ValueError("duplicate CHAOS alias case " + repr(key))
        observed[key] = row
    if set(observed) != set(CASES):
        raise ValueError("missing CHAOS alias case(s): " +
                         repr(sorted(set(CASES) - set(observed))))
    output = []
    for rate, waveform, hz in CASES:
        row = observed[(rate, waveform, hz)]
        item = dict(module=MODULE, oscillator="A", waveform=waveform,
                    sample_rate_hz=rate, target_hz=hz,
                    alias_floor_dbfs=None, rms_fs=None, alias_expected_bin_count=None)
        if row.get("status") != "measured":
            item.update(status="unavailable",
                        reason=row.get("reason") or row.get("status") or "render unavailable")
        elif row.get("nonfinite_samples") != 0:
            item.update(status="unavailable", reason="nonfinite rendered samples")
        elif not (isinstance(row.get("alias_expected_bin_count"), int) and
                  row["alias_expected_bin_count"] > 0):
            # -300 from the existing FFT floor is NOT evidence of zero alias
            # energy if no isolated alias-frequency bins are available.
            item.update(status="unavailable", reason="no isolated folded-alias FFT bins")
        else:
            alias, rms = row.get("alias_floor_dbfs"), row.get("rms_fs")
            if not (isinstance(alias, (float, int)) and math.isfinite(alias) and
                    isinstance(rms, (float, int)) and math.isfinite(rms)):
                item.update(status="unavailable", reason="missing finite alias/RMS measurement")
            else:
                item.update(status="measured", alias_floor_dbfs=float(alias),
                            rms_fs=float(rms),
                            alias_expected_bin_count=row["alias_expected_bin_count"])
        output.append(item)
    return output


def require_switch_descriptors(desc: dict) -> None:
    """Reject source-list identities that do not exist in native descriptors.

    A misspelled module ID must fail capture rather than be recorded as
    a legitimate runtime-unavailable switch measurement.
    """
    for module, param, _, _, _ in SWITCHES:
        if module not in desc:
            raise ValueError(f"missing native switch descriptor: {module}")
        if param not in desc[module].get("parameters", {}):
            raise ValueError(f"missing native switch parameter: {module}.{param}")


def capture_switches(renderer: Path, desc: dict) -> list[dict]:
    rate, seconds, switch_frame = 48000, 2, 48000
    output = []
    for module, param, old, new, extra in SWITCHES:
        identity = dict(module=module, parameter=param, before=old, after=new,
                        sample_rate_hz=rate, switch_frame=switch_frame)
        descriptor = desc.get(module)
        bounds = descriptor["parameters"].get(param) if descriptor else None
        # Source-pinned switch list is authoritative: the metadata extractor
        # cannot infer the kMode WS2_STEPPED alias in quad_vca/dsp.h.
        if not bounds or not (bounds["min"] <= old <= bounds["max"] and
                             bounds["min"] <= new <= bounds["max"]):
            output.append(dict(identity, status="unavailable",
                               reason="switch parameter or bounds unavailable"))
            continue
        patch, reason = build_module_patch(module, descriptor, {**extra, param: old})
        if patch is None:
            output.append(dict(identity, status="unavailable",
                               reason=reason or "no renderer probe"))
            continue
        audio, result = run_wav(renderer, patch, [
            {"frame": switch_frame, "type": "setParam", "node": 1,
             "parameter": param, "value": new}], seconds, rate=rate)
        if audio is None:
            output.append(dict(identity, status="unavailable",
                               reason=result.get("reason") or "renderer failed"))
        else:
            metric = switch_click_metrics(audio, switch_frame, rate)
            output.append(dict(identity, status=metric.get("status", "measured"),
                               **{k: v for k, v in metric.items() if k != "status"},
                               render_counters=result.get("counters")))
    return output


def capture(build_dir: Path, out_dir: Path, head: str) -> dict:
    if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
        raise ValueError("full lowercase 40-character source SHA required")
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout.strip()
    if head != actual:
        raise ValueError("requested source HEAD differs from checkout")
    renderer = executable(build_dir, "wirescape_render")
    if renderer is None:
        raise ValueError("exact-head Release wirescape_render unavailable")
    meta = provenance(build_dir)
    if meta["commit"] != head:
        raise ValueError("native measurement provenance disagrees with source HEAD")
    meta["dsp_sample_rates_hz"] = list(RATES)
    desc = descriptors()
    if MODULE not in desc:
        raise ValueError("CHAOS source descriptor unavailable")
    require_switch_descriptors(desc)
    out_dir.mkdir(parents=True, exist_ok=True)
    oscillator_sections(renderer, desc, meta, out_dir, False, RATES, t7_chaos_only=True)
    alias_json = out_dir / "dsp/oscillators.json"
    data = json.loads(alias_json.read_text(encoding="utf-8"))
    alias_rows = extract_chaos(data, head)
    switch_rows = capture_switches(renderer, desc)
    return {
        "SPDX-License-Identifier": "GPL-3.0-only",
        "task": "M7 T7.0",
        "status": "measured" if all(row["status"] == "measured"
                                      for row in alias_rows + switch_rows) else "partially_unavailable",
        "provenance": {
            "source_commit": head, "date_et": meta["date_et"],
            "machine_class": meta["machine"], "renderer_sha256": sha256(renderer),
            "oscillator_artifact_sha256": sha256(alias_json),
            "oscillator_artifact": "dsp/oscillators.json",
            "method": "bench/offline/run_all.py --t7-chaos-only (full 2s); "
                      "bench/offline/t7_0.py capture (switch rows, 2s, 48 kHz)",
        },
        "alias_method": data.get("method_details"),
        "alias_rows": alias_rows,
        "switch_method": ("step_metrics highpass_peak_fs; second-order Butterworth "
                          "2000 Hz; centered +/-25ms; dBFS=20log10(peak FS)"),
        "switch_rows": switch_rows,
        "observed_alias_below_minus80": [
            {"sample_rate_hz": row["sample_rate_hz"],
             "waveform": row["waveform"], "target_hz": row["target_hz"],
             "alias_floor_dbfs": row["alias_floor_dbfs"]}
            for row in alias_rows if row["status"] == "measured"
            and row["alias_floor_dbfs"] < -80
        ],
        "unmeasured_other_modules": ["example.ringmod2"],
        "constraints": {"devices": "off", "lan": "off", "sound_change": False,
                        "no_acceptance_gate": True},
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="artifact directory outside the repository")
    parser.add_argument("--head", required=True, help="exact full built source commit SHA")
    parser.add_argument("--summary", type=Path, required=True,
                        help="output summary JSON (do not overwrite historical facts)")
    args = parser.parse_args(argv)
    if args.summary.exists():
        parser.error("refusing to overwrite existing fact/summary")
    results = capture(args.build_dir, args.out_dir, args.head)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n",
                            encoding="utf-8")
    print("M7 T7.0: 24 CHAOS cases, 4 switch cases; see statuses and artifact hashes")


if __name__ == "__main__":
    main()
