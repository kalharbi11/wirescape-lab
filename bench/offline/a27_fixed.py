#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Evidence-only M7 r1.4 (A27) fixed-window Delay capture.
The original T7.0 collector and its defaults are not changed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np
from scipy import signal

import run_all
from t7_0 import SWITCHES

RATE, FRAMES, SWITCH = 48000, 96000, 48000
WINDOWS = {"mode": (48000, 85201), "tone": (48000, 67200),
           "division_clocked": (48000, 49200)}
CASES = (*WINDOWS, "division_unclocked")
BEFORE_X64 = {"mode": 7.041270, "tone": 2.445507, "division_clocked": 3.080779}
COUNTERS = ("faults", "dropped_events", "late_events", "stale_events",
            "arena_full_events", "ring_full_events")


def require_pin(pin):
    if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("full lowercase 40-character source SHA required")
    return pin


def sha256(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path, doc):
    Path(path).write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n",
                          encoding="utf-8")


def dbfs(x):
    return 20 * math.log10(x) if x > 0 else "-inf"


def measure_pair(name, switched, control):
    if name not in CASES:
        raise ValueError("unknown fixed-window case")
    row = dict(case=name, sample_rate_hz=RATE, switch_frame=SWITCH,
               pair_render_frames=FRAMES, highpass_hz=2000,
               switch_click_peak_fs=None, no_switch_floor_fs=None,
               switch_click_peak_dbfs=None, no_switch_floor_dbfs=None,
               click_excess_db=None)
    if name in WINDOWS:
        row.update(window_start_frame=WINDOWS[name][0],
                   window_end_frame_exclusive=WINDOWS[name][1])
    if switched is None or control is None:
        return dict(row, status="unavailable", reason="missing render")
    a, b = np.asarray(switched, dtype=np.float64), np.asarray(control, dtype=np.float64)
    if (a.shape != (FRAMES, 2) or b.shape != a.shape or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        return dict(row, status="unavailable", reason="invalid PCM shape or nonfinite data")
    if not np.array_equal(a[:SWITCH], b[:SWITCH]):
        return dict(row, status="unavailable", reason="PCM differs before switch")
    different = np.flatnonzero(np.any(a[SWITCH:] != b[SWITCH:], axis=1))
    row["first_effect_frame"] = SWITCH + int(different[0]) if different.size else None
    if name == "division_unclocked":
        return dict(row, status="unexpected_effect" if different.size else "no_effect",
                    full_capture_equal=not bool(different.size))
    begin, end = WINDOWS[name]
    sos = signal.butter(2, 2000, btype="highpass", fs=RATE, output="sos")
    def peak(x):
        return float(np.max(np.abs(signal.sosfilt(sos, np.mean(x, axis=1))[begin:end])))
    switched_peak, floor_peak = peak(a), peak(b)
    excess = (0.0 if switched_peak == floor_peak == 0 else
              "inf" if floor_peak == 0 else
              "-inf" if switched_peak == 0 else
              20 * math.log10(switched_peak / floor_peak))
    return dict(row, status="measured", switch_click_peak_fs=switched_peak,
                no_switch_floor_fs=floor_peak, switch_click_peak_dbfs=dbfs(switched_peak),
                no_switch_floor_dbfs=dbfs(floor_peak), click_excess_db=excess)


def capture(source, build, out, pin):
    require_pin(pin)
    actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                     text=True).strip()
    if actual != pin:
        raise ValueError("checkout does not match requested pin")
    subprocess.run(["git", "-C", str(source), "diff", "--quiet", "HEAD", "--"], check=True)
    # Use the original fixture constructors/renderer invocation, but resolve
    # descriptors and native paths against this exact pinned source tree.
    run_all.ROOT = source
    meta = run_all.provenance(build)
    if meta["commit"] != pin or meta["machine"]["configuration"] != "Release":
        raise ValueError("not an exact-source Release build")
    renderer = run_all.executable(build, "wirescape_render")
    if renderer is None:
        raise ValueError("renderer unavailable")
    desc = run_all.descriptors()
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in CASES:
        param = "division" if name.startswith("division") else name
        module, _, old, new, extra = next(s for s in SWITCHES
                                         if s[0] == "fx.delay" and s[1] == param)
        identity = dict(module=module, parameter=param, before=old, after=new,
                        fixture="clocked" if name == "division_clocked" else "unclocked")
        try:
            d = desc[module]
            bounds = d["parameters"][param]
            if not bounds["min"] <= old <= bounds["max"] or not bounds["min"] <= new <= bounds["max"]:
                raise ValueError("parameter bounds mismatch")
            patch, reason = run_all.build_module_patch(module, d, {**extra, param: old})
            if patch is None:
                raise ValueError(reason or "no probe")
            if name == "division_clocked":
                clock = desc["essentials.clock"]
                if ("clock" not in {p["port"] for p in d["inputs"]} or
                        "clock" not in {p["port"] for p in clock["outputs"]}):
                    raise ValueError("clock port unavailable")
                node = max(int(item["id"]) for item in patch["modules"]) + 1
                patch["modules"].append({"id": node, "module": "essentials.clock",
                                         "version": clock["version"],
                                         "parameters": {"bpm": 120, "ticks_per_beat": 4, "run": 1}})
                patch["connections"].append({"kind": "signal",
                    "from": {"module": node, "port": "clock"},
                    "to": {"module": 1, "port": "clock"}})
                identity.update(clock_bpm=120, clock_ticks_per_beat=4)
        except (KeyError, ValueError) as exc:
            rows.append(dict(measure_pair(name, None, None), **identity, reason=str(exc)))
            continue
        captures, audio = {}, {}
        for side in ("switched", "control"):
            folder = out / name / side
            folder.mkdir(parents=True)
            events = ([{"frame": SWITCH, "type": "setParam", "node": 1,
                        "parameter": param, "value": new}] if side == "switched" else [])
            pcm, report = run_all.wav_run(renderer, patch, events, 2, 128, folder, seed=7, rate=RATE)
            audio[side] = pcm
            captures[side] = dict(report, files={
                str(p.relative_to(out)): sha256(p) for p in sorted(folder.iterdir()) if p.is_file()})
        row = dict(measure_pair(name, audio["switched"], audio["control"]),
                   **identity, captures=captures)
        # Preserve raw counter data. Nonzero or absent required counters cannot
        # be evidence of a valid device-off pair.
        for result in captures.values():
            counters = result.get("counters", {})
            if result["status"] != "measured" or any(counters.get(k) != 0 for k in COUNTERS):
                row.update(status="unavailable", reason="render failure or nonzero/missing counter")
                break
        rows.append(row)
    report = dict(source_commit=pin, provenance=meta, renderer_sha256=sha256(renderer),
                  method="M7 A27 fixed windows, full 2 s causal 2 kHz HP; seed 7, block 128",
                  rows=rows)
    write_json(out / "report.json", report)
    return report


def validate_reports(before, after, base_pin, subject_pin):
    require_pin(base_pin)
    require_pin(subject_pin)
    if base_pin == subject_pin:
        raise ValueError("base and subject must be distinct pins")
    for report, pin in ((before, base_pin), (after, subject_pin)):
        if report.get("source_commit") != pin or report.get("provenance", {}).get("commit") != pin:
            raise ValueError("report source pin mismatch")
        if [row.get("case") for row in report.get("rows", [])] != list(CASES):
            raise ValueError("missing or duplicate row inventory")
        for row in report["rows"]:
            if row["case"] in WINDOWS and (row.get("window_start_frame"),
                    row.get("window_end_frame_exclusive")) != WINDOWS[row["case"]]:
                raise ValueError("fixed-window mismatch")
    if before["provenance"]["machine"]["architecture"] != after["provenance"]["machine"]["architecture"]:
        raise ValueError("paired report architecture mismatch")


def pair_reports(root, base_pin, subject_pin):
    before, after = (json.loads((root / role / "report.json").read_text(encoding="utf-8"))
                     for role in ("base", "subject"))
    validate_reports(before, after, base_pin, subject_pin)
    for role, doc in (("base", before), ("subject", after)):
        for row in doc["rows"]:
            for item in row.get("captures", {}).values():
                for name, digest in item["files"].items():
                    p = (root / role / name).resolve()
                    if not p.is_relative_to((root / role).resolve()) or sha256(p) != digest:
                        raise ValueError("raw artifact digest mismatch")
    arch = before["provenance"]["machine"]["architecture"]
    rows = []
    for a, b in zip(before["rows"], after["rows"]):
        row = dict(case=a["case"], before=a, after=b, before_excess_matches=None,
                   reduction_db=None)
        if a["case"] in WINDOWS:
            x, y = a["click_excess_db"], b["click_excess_db"]
            if a["status"] == b["status"] == "measured" and isinstance(x, (float, int)) and isinstance(y, (float, int)):
                row["reduction_db"] = x - y
                if arch == "x86_64":
                    row["before_excess_matches"] = abs(x - BEFORE_X64[a["case"]]) <= .1
        rows.append(row)
    write_json(root / "paired.json", dict(base_pin=base_pin, subject_pin=subject_pin,
                architecture=arch, base_report_sha256=sha256(root / "base/report.json"),
                subject_report_sha256=sha256(root / "subject/report.json"), rows=rows))
    # Evidence tool validity, not a sound acceptance gate.
    if any(r["before_excess_matches"] is False for r in rows):
        raise ValueError("x64 fixed-window baseline did not reproduce within A27 0.1 dB")
    if any(r["before"]["status"] not in ("measured", "no_effect") or
           r["after"]["status"] not in ("measured", "no_effect") for r in rows):
        raise ValueError("unavailable or unexpected-effect rows preserved in artifact")


def endpoint_columns(old, target, switched):
    """M7 r1.8 diagnostic columns in FS; signed excess in dB."""
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0
           for x in (old, target, switched)):
        raise ValueError("invalid endpoint peak")
    floor = max(old, target)
    excess = (0.0 if switched == floor == 0 else "inf" if floor == 0 else
              "-inf" if switched == 0 else 20 * math.log10(switched / floor))
    return dict(old_floor=old, target_floor=target, endpoint_floor=floor,
                switched=switched, excess_over_endpoint_db=excess)


def target_patch(patch, parameter, old, target):
    """Copy the exact old-control graph; only the named Delay value changes."""
    result = copy.deepcopy(patch)
    nodes = [m for m in result["modules"] if m["id"] == 1 and m["module"] == "fx.delay"]
    if len(nodes) != 1 or nodes[0]["parameters"].get(parameter) != old:
        raise ValueError("old-control patch does not match target case")
    nodes[0]["parameters"][parameter] = target
    return result


def supplemental_target_controls(source, build, out, pin):
    """Diagnostic-only target-from-start cases; never enter paired acceptance rows."""
    require_pin(pin)
    if subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                               text=True).strip() != pin:
        raise ValueError("supplemental source mismatch")
    subprocess.run(["git", "-C", str(source), "diff", "--quiet", "HEAD", "--"], check=True)
    run_all.ROOT = source
    meta = run_all.provenance(build)
    if meta["commit"] != pin or meta["machine"]["configuration"] != "Release":
        raise ValueError("not exact-source Release")
    renderer = run_all.executable(build, "wirescape_render")
    if renderer is None:
        raise ValueError("renderer unavailable")
    # Exact old-control patch from the same subject capture: preserve every
    # clock connection, initial value, output and stimulus setting.
    subject_root = out.parent / "subject"
    subject_path = subject_root / "report.json"
    subject = json.loads(subject_path.read_text(encoding="utf-8"))
    if (subject["source_commit"] != pin or subject["provenance"]["commit"] != pin or
            subject["renderer_sha256"] != sha256(renderer) or
            subject["provenance"]["machine"]["architecture"] != meta["machine"]["architecture"]):
        raise ValueError("target control subject provenance mismatch")
    if [r["case"] for r in subject["rows"]] != list(CASES):
        raise ValueError("subject row inventory mismatch")
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in WINDOWS:
        subject_row = next(r for r in subject["rows"] if r["case"] == name)
        if (subject_row["status"] != "measured" or
                (subject_row["window_start_frame"], subject_row["window_end_frame_exclusive"]) != WINDOWS[name]):
            raise ValueError("invalid subject fixed-window row")
        param = subject_row["parameter"]
        old, new = subject_row["before"], subject_row["after"]
        for capture in subject_row["captures"].values():
            for relative, digest in capture["files"].items():
                p = (subject_root / relative).resolve()
                if not p.is_relative_to(subject_root.resolve()) or sha256(p) != digest:
                    raise ValueError("subject capture digest mismatch")
        control = subject_root / name / "control"
        if json.loads((control / "script.json").read_text(encoding="utf-8")) != []:
            raise ValueError("old control has events")
        patch = target_patch(json.loads((control / "patch.json").read_text(encoding="utf-8")),
                             param, old, new)
        folder = out / name
        folder.mkdir()
        pcm, result = run_all.wav_run(renderer, patch, [], 2, 128, folder, seed=7, rate=RATE)
        if result["status"] != "measured" or any(result.get("counters", {}).get(k) != 0 for k in COUNTERS):
            raise ValueError("target control render/counter failure")
        x = np.asarray(pcm, dtype=np.float64)
        if x.shape != (FRAMES, 2) or not np.isfinite(x).all():
            raise ValueError("target control PCM invalid")
        sos = signal.butter(2, 2000, btype="highpass", fs=RATE, output="sos")
        filtered = signal.sosfilt(sos, x, axis=0)
        mono = filtered.mean(axis=1)
        def summarize(begin, end):
            frame = begin + int(np.argmax(np.abs(mono[begin:end])))
            return dict(start_frame=begin, end_frame_exclusive=end, peak_frame=frame,
                        peak_fs=abs(float(mono[frame])), peak_dbfs=dbfs(abs(float(mono[frame]))),
                        signed_channel_fs=filtered[frame].tolist())
        fixed = summarize(*WINDOWS[name])
        endpoint = endpoint_columns(subject_row["no_switch_floor_fs"],
                                    fixed["peak_fs"], subject_row["switch_click_peak_fs"])
        rows.append(dict(case=name, parameter=param, old=old, target_from_start=new,
                         **endpoint, peak_units="FS",
                         events=[], status="measured", captures=result,
                         files={str(p.relative_to(out)): sha256(p)
                                for p in sorted(folder.iterdir()) if p.is_file()},
                         fixed_window=fixed,
                         full_capture=summarize(0, FRAMES),
                         post_switch_time=summarize(SWITCH, FRAMES)))
    write_json(out / "target-controls.json", dict(source_commit=pin, provenance=meta,
               renderer_sha256=sha256(renderer), sample_rate_hz=RATE, frames=FRAMES,
               diagnostic_only=True, method="M7 r1.8 endpoint floor over fixed r1.4 windows",
               subject_report_sha256=sha256(subject_path), rows=rows))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("capture")
    for arg in ("source", "build", "out"):
        c.add_argument("--" + arg, type=Path, required=True)
    c.add_argument("--pin", required=True)
    t = sub.add_parser("target-controls")
    for arg in ("source", "build", "out"):
        t.add_argument("--" + arg, type=Path, required=True)
    t.add_argument("--pin", required=True)
    q = sub.add_parser("pair")
    q.add_argument("--root", type=Path, required=True)
    q.add_argument("--base-pin", required=True)
    q.add_argument("--subject-pin", required=True)
    a = p.parse_args()
    if a.command == "capture":
        capture(a.source.resolve(), a.build.resolve(), a.out.resolve(), a.pin)
    elif a.command == "target-controls":
        supplemental_target_controls(a.source.resolve(), a.build.resolve(), a.out.resolve(), a.pin)
    else:
        pair_reports(a.root.resolve(), a.base_pin, a.subject_pin)


if __name__ == "__main__":
    main()
