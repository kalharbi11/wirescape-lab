# SPDX-License-Identifier: GPL-3.0-only
"""CI-only, uncommitted one-line VCO perturbation proving the sound-change gate.

Only use in an ephemeral runner checkout after the normal base/head comparison.
The source file is restored in a finally block. No product changes are committed.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from compare import compare, parse_sound_changes
from render import binary, measure

PATCH = "bundled/basics-01-first-tone.json"
SOURCE = "modules/vco/dsp.h"
ORIGINAL = "out[i]=static_cast<float>(std::sin(phase[c]));"
ALTERED = "out[i]=static_cast<float>(0.875*std::sin(phase[c]));"


def run_experiment(root: Path, baseline_path: Path, baseline_wavs: Path,
                   changed_wavs: Path, report_path: Path):
    root = root.resolve()
    baseline_path = baseline_path.resolve()
    baseline_wavs = baseline_wavs.resolve()
    changed_wavs = changed_wavs.resolve()
    report_path = report_path.resolve()
    original_wav = baseline_wavs / "bundled/basics-01-first-tone.wav"
    source_path = root / SOURCE
    if not original_wav.is_file() or not source_path.is_file():
        raise RuntimeError("missing baseline WAV or VCO source for experiment")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if PATCH not in baseline["patches"]:
        raise RuntimeError("required first-tone patch absent from golden baseline")
    before = copy.deepcopy(baseline)
    before["patches"] = {PATCH: baseline["patches"][PATCH]}
    source_original = source_path.read_text(encoding="utf-8")
    if source_original.count(ORIGINAL) != 1:
        raise RuntimeError("expected exact one-line VCO mutation target once")
    source_path.write_text(source_original.replace(ORIGINAL, ALTERED), encoding="utf-8")
    try:
        # Headless incremental rebuild, with no devices, on this same runner.
        subprocess.run([sys.executable, "tools/dev.py", "build", "--headless",
                        "--config", "Release"], cwd=root, check=True)
        renderer = binary(root)
        if renderer is None:
            raise RuntimeError("offline render executable absent after mutation build")
        after_row = measure(renderer.resolve(),
                            root / "apps/studio/patches/basics-01-first-tone.json",
                            "bundled", root, changed_wavs / "after")
        after = copy.deepcopy(before)
        after["patches"] = {PATCH: after_row}
        # Same runner/patch; retention-only WAV copies are stored under "changed".
        source = original_wav
        target = changed_wavs / "before/bundled/basics-01-first-tone.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        raw_a, raw_b = changed_wavs / "before", changed_wavs / "after"
        detected = compare(before, after, tolerance_db=0,
                           raw_before=raw_a, raw_after=raw_b, require_wavs=True)
        row = detected[PATCH]
        if (row["status"] != "different" or row["first_differing_sample_index"] is None
                or not row["peak_sample_difference_fs"] > 0):
            raise AssertionError(f"uncommitted one-line DSP change was not detected: {row}")
        declaration = f"Sound-change: basics-01-first-tone.json — CI-only VCO amplitude experiment"
        permitted = parse_sound_changes(declaration, [PATCH])
        declared = compare(before, after, tolerance_db=0, raw_before=raw_a,
                           raw_after=raw_b, declared=permitted, require_wavs=True)
        if declared[PATCH]["status"] != "declared":
            raise AssertionError(f"Sound-change declaration not honored: {declared}")
        report = {
            "experiment": "one-line uncommitted native VCO amplitude change",
            "source_path": SOURCE,
            "original_line": ORIGINAL,
            "modified_line": ALTERED,
            "patch": PATCH,
            "primary_undeclared": row,
            "primary_declared": declared[PATCH],
            "declaration": declaration,
            "baseline_commit": baseline["commit"],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
        print("SOUND_EXPERIMENT " + json.dumps(report, separators=(",", ":")), flush=True)
    finally:
        # Protect the checkout even on failed builds/assertions.
        source_path.write_text(source_original, encoding="utf-8")
        subprocess.run(["git", "diff", "--exit-code", "--", SOURCE],
                       cwd=root, check=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--baseline-wavs", type=Path, required=True)
    p.add_argument("--changed-wavs", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    run_experiment(args.root, args.baseline, args.baseline_wavs,
                   args.changed_wavs, args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
