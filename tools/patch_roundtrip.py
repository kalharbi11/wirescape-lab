# SPDX-License-Identifier: GPL-3.0-only
"""OB-a1 real Studio codec + device-free native runtime load/save/load evidence.

The Node regression exercises product PatchDoc.from()/toJSON(). Every patch
before/after save is independently loaded and rendered by the actual compiled
wirescape_render (document::load_runtime_patch + AppEngine), never a mock.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "apps/studio"
BUNDLES = STUDIO / "patches"
SHAPES = ROOT / "tests/fixtures/patch_shapes"
SPEC = ROOT / "native/tests2/ob_patch_roundtrip.spec.cjs"
SHAPE_IDS = {"no-config", "chord-empty", "groove-v1", "groove-v2",
             "midi-in", "midi-cc-to-cv", "osc-in", "osc-out"}
METRICS = ("faults", "late_events", "dropped_events",
           "ring_full_events", "stale_events", "arena_full_events")
RATE, FRAMES, BLOCK = 48000, 48000, 128


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized(value) -> str:
    # Only JSON object key order is irrelevant. All values, UI and opaque keys
    # count, and arrays retain order; no migration or default healing.
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def read_patch(path: Path) -> tuple[bytes, dict]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError(f"missing, symlinked or oversized patch: {path}")
    raw = path.read_bytes()
    patch = json.loads(raw.decode("utf-8"),
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if (not isinstance(patch, dict) or patch.get("format") != "wirescape.native.patch"
            or patch.get("version") != 2):
        raise ValueError(f"unsupported native v2 patch (no migration authorized): {path}")
    normalized(patch)
    return raw, patch


def inventory() -> list[tuple[str, Path]]:
    bundled = sorted(BUNDLES.glob("*.json"))
    fixtures = sorted(SHAPES.glob("*.json"))
    found = {p.stem for p in fixtures}
    if not bundled:
        raise ValueError("zero bundled patches; coverage cannot pass")
    if found != SHAPE_IDS:
        raise ValueError(f"config-shape inventory mismatch; missing={sorted(SHAPE_IDS-found)} "
                         f"unexpected={sorted(found-SHAPE_IDS)}")
    cases = [("bundled/" + p.stem, p) for p in bundled]
    cases += [("config-shape/" + p.stem, p) for p in fixtures]
    for _, path in cases:
        read_patch(path)
    return cases


def studio_codec(manifest: Path, temporary: Path) -> None:
    if not (STUDIO / "node_modules/@playwright/test").is_dir():
        raise ValueError("Studio deps missing; run npm ci --prefix apps/studio")
    cli = STUDIO / "node_modules/playwright/cli.js"
    if not cli.is_file():
        raise ValueError("pinned Playwright CLI missing")
    config = temporary / "ob-playwright.config.cjs"
    config.write_text("module.exports = {testDir:" + json.dumps(str(SPEC.parent))
                      + ",testMatch:'ob_patch_roundtrip.spec.cjs',workers:1,"
                      + "fullyParallel:false,retries:0,reporter:'list',timeout:120000};\n",
                      encoding="utf-8")
    env = os.environ.copy()
    env["OB_PATCH_MANIFEST"] = str(manifest)
    env["NODE_PATH"] = str(STUDIO / "node_modules") + (
        os.pathsep + env["NODE_PATH"] if env.get("NODE_PATH") else "")
    proc = subprocess.run(["node", str(cli), "test", "--config", str(config)],
                          cwd=STUDIO, env=env, capture_output=True, text=True,
                          timeout=180, check=False)
    if proc.returncode:
        raise ValueError("product Studio codec test failed: "
                         + (proc.stdout + "\n" + proc.stderr)[-6000:])


def events(patch: dict) -> list[dict]:
    # Same documented keyboard stimulus as the existing real library smoke.
    ids = [m["id"] for m in patch["modules"] if m.get("module") == "host.keyboard"]
    return sorted([e for node in ids for e in (
        {"frame": 0, "type": "noteOn", "node": node, "key": 60},
        {"frame": RATE // 2, "type": "noteOff", "node": node, "key": 60})],
        key=lambda e: e["frame"])


def render(renderer: Path, source: Path, dest: Path) -> dict:
    _, patch = read_patch(source)
    seed = patch.get("settings", {}).get("seed", 42)
    if type(seed) is not int or not 0 <= seed <= 2**64-1:
        raise ValueError("invalid seed")
    script = dest.with_suffix(".events.json")
    wav = dest.with_suffix(".wav")
    script.write_text(json.dumps(events(patch)), encoding="utf-8")
    cmd = [str(renderer), "--patch", str(source), "--script", str(script),
           "--out", str(wav), "--rate", str(RATE), "--block", str(BLOCK),
           "--seconds", "1", "--seed", str(seed)]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if run.returncode:
        raise ValueError(f"native loader/render exit {run.returncode}: " + run.stderr[-1200:])
    records = [s[len("render_metrics "):] for s in run.stdout.splitlines()
               if s.startswith("render_metrics ")]
    if len(records) != 1:
        raise ValueError("missing actual native render metrics")
    metrics = json.loads(records[0])
    if any(type(metrics.get(k)) is not int or metrics[k] != 0 for k in METRICS):
        raise ValueError(f"native render fault: {metrics}")
    raw = wav.read_bytes()
    if (len(raw) != 44 + FRAMES * 8 or raw[:4] != b"RIFF"
            or raw[8:16] != b"WAVEfmt " or raw[36:40] != b"data"):
        raise ValueError("noncanonical native stereo-float WAV")
    if any(not math.isfinite(sample) for (sample,) in struct.iter_unpack("<f", raw[44:])):
        raise ValueError("native render produced non-finite sample")
    return {"sha256": sha(raw), "bytes": len(raw), "metrics": metrics}


def compare(original: dict, saved: dict, reopened: dict, a: dict, b: dict, c: dict) -> None:
    if normalized(original) != normalized(saved):
        raise ValueError("source vs product save: normalized document drift")
    if normalized(saved) != normalized(reopened):
        raise ValueError("saved vs product reloaded: normalized document drift")
    if not a["sha256"] == b["sha256"] == c["sha256"]:
        raise ValueError("native source/save/reload render SHA256 drift")


def negative(renderer: Path, work: Path) -> dict:
    _, source = read_patch(SHAPES / "no-config.json")
    altered = json.loads(json.dumps(source))
    next(m for m in altered["modules"]
         if m["module"] == "essentials.vco")["parameters"]["frequency"] = 880
    if normalized(source) == normalized(altered):
        raise ValueError("negative document sensitivity not detected")
    original_file, modified_file = work / "negative-original.json", work / "negative-modified.json"
    original_file.write_text(json.dumps(source), encoding="utf-8")
    modified_file.write_text(json.dumps(altered), encoding="utf-8")
    a = render(renderer, original_file, work / "negative-original")
    b = render(renderer, modified_file, work / "negative-modified")
    if a["sha256"] == b["sha256"]:
        raise ValueError("VCO frequency 220->880 did not alter native render hash")
    try:
        compare(source, altered, altered, a, b, b)
    except ValueError:
        pass
    else:
        raise ValueError("changed document/render incorrectly accepted")
    return {"document_difference_detected": True, "render_difference_detected": True,
            "original_render_sha256": a["sha256"], "changed_render_sha256": b["sha256"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--renderer", required=True, type=Path)
    p.add_argument("--report", type=Path, default=ROOT / "build_reports/ob/patch_roundtrip.json")
    p.add_argument("--source-sha", default="", help="full PR source head SHA for provenance")
    args = p.parse_args()
    if args.source_sha and not re.fullmatch("[a-f0-9]{40}", args.source_sha):
        p.error("--source-sha requires a full lowercase Git commit SHA")
    report = {"test": "OB-a1", "source_sha": args.source_sha or None,
              "checkout_sha": os.getenv("GITHUB_SHA"), "runner_event": os.getenv("GITHUB_EVENT_NAME"),
              "renderer_sha256": None, "rate": RATE, "frames": FRAMES, "block": BLOCK,
              "bundled": 0, "config_shapes": 0, "cases": [], "negative": None, "passed": False}
    try:
        renderer = args.renderer.resolve(strict=True)
        if not renderer.is_file():
            raise ValueError(f"renderer is not a file: {renderer}")
        report["renderer_sha256"] = sha(renderer.read_bytes())
        cases = inventory()
        report["bundled"] = sum(name.startswith("bundled/") for name, _ in cases)
        report["config_shapes"] = len(cases) - report["bundled"]
        with tempfile.TemporaryDirectory(prefix="wirescape-ob-a1-") as temp:
            work = Path(temp)
            manifest = [{"name": name, "source": str(path),
                         "saved": str(work / f"{i:03d}-saved.json"),
                         "reopened": str(work / f"{i:03d}-reopened.json")}
                        for i, (name, path) in enumerate(cases)]
            source = work / "manifest.json"
            source.write_text(json.dumps(manifest), encoding="utf-8")
            studio_codec(source, work)
            for i, case in enumerate(manifest):
                try:
                    values = [read_patch(Path(case[key])) for key in ("source", "saved", "reopened")]
                    hashes = [render(renderer, Path(case[key]), work / f"{i:03d}-{key}")
                              for key in ("source", "saved", "reopened")]
                    compare(*(j for _, j in values), *hashes)
                    report["cases"].append({"name": case["name"], "status": "pass",
                       "source_bytes_sha256": sha(values[0][0]),
                       "document_sha256": sha(normalized(values[0][1]).encode("utf-8")),
                       "render_sha256": hashes[0]["sha256"]})
                    print("PASS " + case["name"], flush=True)
                except (OSError, ValueError, KeyError, TypeError,
                        subprocess.TimeoutExpired) as exc:
                    report["cases"].append({"name": case["name"], "status": "fail", "reason": str(exc)})
                    print(f"FAIL {case['name']}: {exc}", file=sys.stderr, flush=True)
            try:
                report["negative"] = negative(renderer, work)
            except (OSError, ValueError, KeyError, TypeError,
                    subprocess.TimeoutExpired) as exc:
                report["negative"] = {"status": "fail", "reason": str(exc)}
                print(f"FAIL negative: {exc}", file=sys.stderr, flush=True)
        report["passed"] = (len(report["cases"]) == len(cases)
                            and all(c["status"] == "pass" for c in report["cases"])
                            and bool(report["negative"] and report["negative"].get("document_difference_detected")
                                     and report["negative"].get("render_difference_detected")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        report["setup_error"] = str(exc)
        print(f"FAIL OB-a1 setup: {exc}", file=sys.stderr, flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"OB-a1 {sum(c['status']=='pass' for c in report['cases'])}/"
          f"{report['bundled']+report['config_shapes']} cases; report={args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
