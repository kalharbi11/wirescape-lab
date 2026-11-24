# SPDX-License-Identifier: GPL-3.0-only
"""Collect and compare the pinned Reverb S7.2 module outputs."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import sys
from unittest.mock import patch

MODULE = "fx.reverb"
RATE = 48000
SECONDS = 1.5
BLOCK = 128
SEED = 7


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def measure(source, pin, out):
    if Path.cwd() != source or platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("run from the pinned checkout on Linux x64")
    sys.path.insert(0, str(source / "bench/offline"))
    import run_all as collector

    build = source / "build/native"
    renderer = collector.executable(build, "wirescape_render")
    meta = collector.provenance(build)
    if (renderer is None or not renderer.is_relative_to(build)
            or meta["commit"] != pin or meta["machine"]["configuration"] != "Release"):
        raise ValueError("expected the pinned checkout's own Release wirescape_render")

    desc = collector.descriptors()
    meta["dsp_sample_rates_hz"] = [RATE]
    meta["benchmark_collector_sha256"] = sha256(Path(collector.__file__))
    meta["renderer"] = {
        "binary_sha256": sha256(renderer),
        "path": renderer.relative_to(source).as_posix(),
        "entrypoint_sha256": sha256(source / "native/tools/render/main.cpp"),
    }
    module_source = desc[MODULE]["source"]
    meta["module_source"] = {"path": module_source, "sha256": sha256(source / module_source)}
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "provenance.json", meta)

    original_call = collector.call

    def capture_first_render(command, **kwargs):
        # module_sections calls the baseline render before its parameter step.
        # Copy its exact inputs and output while run_wav still owns the temp files.
        if (out / "patch.json").exists():
            return original_call(command, **kwargs)
        flags = dict(zip(command[1::2], command[2::2], strict=True))
        settings = {"rate_hz": flags["--rate"], "block_frames": flags["--block"],
                    "seconds": flags["--seconds"], "seed": flags["--seed"]}
        shutil.copyfile(flags["--patch"], out / "patch.json")
        shutil.copyfile(flags["--script"], out / "script.json")
        result = original_call(command, **kwargs)
        write_json(out / "render.json", {"settings": settings, "result": result})
        if flags["--out"].is_file():
            shutil.copyfile(flags["--out"], out / "audio.wav")
        return result

    with patch.object(collector, "call", side_effect=capture_first_render):
        collector.module_sections(renderer, desc, [MODULE], meta, out, quick=False, rates=(RATE,))

    wav = out / "audio.wav"
    if wav.is_file():
        # This reader verifies the collector's RIFF layout and float32 stereo format.
        collector.read_audio(wav, rate=RATE)
        meta["raw_wav_sha256"] = sha256(wav)
        meta["raw_pcm_sha256"] = hashlib.sha256(wav.read_bytes()[44:]).hexdigest()
    meta["fixture"] = {
        "settings": json.loads((out / "render.json").read_text(encoding="utf-8"))["settings"],
        "patch_sha256": sha256(out / "patch.json"),
        "script_sha256": sha256(out / "script.json"),
    }
    write_json(out / "provenance.json", meta)


def compare(out, base, head):
    comparison = {}
    for label, pin in (("before", base), ("head", head)):
        folder = out / label
        report = json.loads((folder / "dsp/module_outputs.json").read_text(encoding="utf-8"))
        provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
        row, = report["rows"]
        if (provenance["commit"] != pin or report["provenance"]["commit"] != pin
                or row["module"] != MODULE or row["status"] != "measured"
                or row["sample_rate_hz"] != RATE or row.get("nonfinite_samples") != 0
                or row.get("finite_samples") != int(RATE * SECONDS * 2)
                or not all(math.isfinite(row[k]) for k in ("peak_fs", "rms_fs"))
                or provenance["fixture"]["settings"] != {
                    "rate_hz": RATE, "seconds": SECONDS, "block_frames": BLOCK, "seed": SEED}
                or json.loads((folder / "script.json").read_text(encoding="utf-8")) != []
                or not provenance["raw_pcm_sha256"]):
            raise ValueError(f"{label} did not produce the required full-mode measured row")
        comparison[label] = {"row": row, "provenance": provenance}

    before = comparison["before"]["provenance"]
    after = comparison["head"]["provenance"]
    if before["fixture"] != after["fixture"] or before["machine"] != after["machine"]:
        raise ValueError("fixture or runner provenance differs between measurements")
    comparison["renderer_entrypoint_matches"] = (
        before["renderer"]["entrypoint_sha256"] == after["renderer"]["entrypoint_sha256"])
    comparison["raw_pcm_matches"] = before["raw_pcm_sha256"] == after["raw_pcm_sha256"]
    passed = comparison["head"]["row"]["peak_fs"] <= 1.0
    comparison["head_peak_criterion"] = {"maximum_fs": 1.0, "passed": passed}
    write_json(out / "comparison.json", comparison)
    lines = ["### Reverb S7.2 full mode · 1.5 s · 48 kHz", "",
             "| Source | Commit | Peak FS | RMS FS |",
             "| --- | --- | ---: | ---: |"]
    for label, result in ((k, comparison[k]) for k in ("before", "head")):
        row = result["row"]
        lines.append(f"| {label} | `{result['provenance']['commit']}` | "
                     f"{row['peak_fs']!r} | {row['rms_fs']!r} |")
    lines += ["", f"Head peak ≤ 1.00 FS: {'pass' if passed else 'fail'}",
              "", "Signed: codex-lead, issue #267"]
    summary = "\n".join(lines) + "\n"
    print(summary, end="")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as handle:
            handle.write(summary)
    if not passed:
        raise SystemExit("head peak exceeds the existing 1.00 FS criterion")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    run = commands.add_parser("measure")
    run.add_argument("source", type=Path)
    run.add_argument("pin")
    run.add_argument("out", type=Path)
    summary = commands.add_parser("compare")
    summary.add_argument("out", type=Path)
    summary.add_argument("base")
    summary.add_argument("head")
    args = parser.parse_args()
    if args.mode == "measure":
        measure(args.source.resolve(), args.pin, args.out.resolve())
    else:
        compare(args.out, args.base, args.head)


if __name__ == "__main__":
    main()
