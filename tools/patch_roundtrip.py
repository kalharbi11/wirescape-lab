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
SPEC = ROOT / "tests/native/abi2/ob_patch_roundtrip.spec.cjs"
SHAPE_IDS = {"no-config", "chord-empty", "groove-v1", "groove-v2",
             "midi-in", "midi-cc-to-cv", "osc-in", "osc-out"}
METRICS = ("faults", "late_events", "dropped_events",
           "ring_full_events", "stale_events", "arena_full_events")
RATE, FRAMES, BLOCK = 48000, 48000, 128
OWNER_REPORTS = ROOT / "bench/results"
OWNER_REPORT = OWNER_REPORTS / "patch_roundtrip_owner.json"


def prepare_owner_report(path: Path, folder: Path) -> None:
    """Never emit owner data to a non-ignored location or input directory."""
    root = OWNER_REPORTS.resolve()
    dest = path.resolve()
    marker = root / ".gitignore"
    if dest == marker.resolve():
        raise ValueError("owner report destination is reserved bench/results/.gitignore")
    if dest == root or not dest.is_relative_to(root):
        raise ValueError("--dir report must stay under bench/results/")
    if root.is_relative_to(folder.resolve()):
        raise ValueError("report directory is inside the supplied input folder")
    if dest.is_relative_to(folder.resolve()):
        raise ValueError("report output is inside the supplied input folder")
    root.mkdir(parents=True, exist_ok=True)
    if marker.is_symlink() or (marker.exists() and not marker.is_file()):
        raise ValueError("unsafe bench/results/.gitignore")
    if not marker.exists():
        marker.write_text("*\n", encoding="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    ignored = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-q", "--", str(dest)],
        capture_output=True, text=True, check=False)
    if ignored.returncode != 0:
        raise ValueError("owner report is not gitignored by bench/results rules")


def write_owner_report_atomic(path: Path, content: str) -> None:
    """Never truncate a pre-existing report inode (possibly hard-linked to input)."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            # Check the actual temporary pathname before putting owner data in it.
            ignored = subprocess.run(
                ["git", "-C", str(ROOT), "check-ignore", "-q", "--", str(temporary)],
                capture_output=True, text=True, check=False)
            if ignored.returncode != 0:
                raise ValueError("owner report temporary file is not gitignored")
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def owner_inventory(folder: Path):
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"missing input folder: {folder}")
    folder = folder.resolve(strict=True)
    for path in folder.rglob("*"):
        if path.is_symlink() and path.is_dir():
            raise ValueError(f"symlinked input subdirectory: {path}")
    paths = tuple(sorted(folder.rglob("*.json")))
    if not paths:
        raise ValueError("empty input folder: no JSON patches")
    valid, invalid, snapshots, located = [], [], {}, {}
    for path in paths:
        name = "owner/" + path.relative_to(folder).as_posix()
        located[name] = path
        try:
            if path.is_file() and not path.is_symlink():
                snapshots[name] = sha(path.read_bytes())
            read_patch(path)
            valid.append((name, path))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            invalid.append({"name": name, "status": "fail", "reason": str(exc)})
    return valid, invalid, snapshots, located, paths


def verify_owner_inputs(report: dict, snapshots: dict, located: dict,
                        original_paths: tuple, folder: Path) -> None:
    for item in report["cases"]:
        name, path = item["name"], located[item["name"]]
        before = snapshots.get(name)
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError("source is missing or symlinked after run")
            after = sha(path.read_bytes())
        except (OSError, ValueError):
            after = None
        item.update(input_sha256_before=before, input_sha256_after=after,
                    input_unchanged=(before is not None and before == after))
        if not item["input_unchanged"]:
            item["status"] = "fail"
            item["reason"] = (item.get("reason", "")
                              + "; source input changed or became unreadable").strip("; ")
    report["input_inventory_unchanged"] = (
        tuple(sorted(folder.rglob("*.json"))) == original_paths)
    if not report["input_inventory_unchanged"]:
        report["setup_error"] = "JSON file inventory changed during run"



def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized(value) -> str:
    # JSON has a single numeric type: JavaScript JSON.stringify writes 1.0 as
    # 1, and -0.0 as 0. Compare numeric values, not Python's float/int spelling.
    # Keep every field, array order, non-integral value and boolean distinct.
    def semantic(v):
        if isinstance(v, dict):
            return {k: semantic(item) for k, item in v.items()}
        if isinstance(v, list):
            return [semantic(item) for item in v]
        if type(v) is float and math.isfinite(v) and v.is_integer():
            return int(v)
        return v

    return json.dumps(semantic(value), ensure_ascii=False, sort_keys=True,
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
    p.add_argument("--dir", dest="owner_dir", type=Path,
                   help="read-only owner patch folder, recursively scanning *.json")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--source-sha", default="", help="full PR source head SHA for provenance")
    args = p.parse_args()
    owner_mode = args.owner_dir is not None
    args.report = args.report or (
        OWNER_REPORT if owner_mode else ROOT / "build_reports/ob/patch_roundtrip.json")
    if owner_mode:
        try:
            prepare_owner_report(args.report, args.owner_dir)
        except (OSError, ValueError) as exc:
            p.error(str(exc))
    if args.source_sha and not re.fullmatch("[a-f0-9]{40}", args.source_sha):
        p.error("--source-sha requires a full lowercase Git commit SHA")
    report = {"test": "OB-a2" if owner_mode else "OB-a1", "source_sha": args.source_sha or None,
              "checkout_sha": os.getenv("GITHUB_SHA"), "runner_event": os.getenv("GITHUB_EVENT_NAME"),
              "renderer_sha256": None, "rate": RATE, "frames": FRAMES, "block": BLOCK,
              "bundled": 0, "config_shapes": 0, "cases": [], "negative": None, "passed": False}
    try:
        renderer = args.renderer.resolve(strict=True)
        if not renderer.is_file():
            raise ValueError(f"renderer is not a file: {renderer}")
        report["renderer_sha256"] = sha(renderer.read_bytes())
        if owner_mode:
            cases, invalid, before, located, original_paths = owner_inventory(args.owner_dir)
            report["cases"].extend(invalid)
            report["owner_files"] = len(original_paths)
            folder = args.owner_dir.resolve(strict=True)
            if Path(tempfile.gettempdir()).resolve().is_relative_to(folder):
                raise ValueError("temporary directory is inside the input folder")
        else:
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
            codec_failures = {}
            if owner_mode:
                try:
                    studio_codec(source, work)
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    # One invalid owner document must not erase all other results.
                    for i, case in enumerate(manifest):
                        solo = work / f"{i:03d}-solo-manifest.json"
                        solo.write_text(json.dumps([case]), encoding="utf-8")
                        try:
                            studio_codec(solo, work)
                        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                            codec_failures[i] = str(exc)
            else:
                studio_codec(source, work)
            for i, case in enumerate(manifest):
                try:
                    if i in codec_failures:
                        raise ValueError("Studio codec: " + codec_failures[i])
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
        if owner_mode:
            verify_owner_inputs(report, before, located, original_paths, folder)
        expected_count = report["owner_files"] if owner_mode else len(cases)
        report["passed"] = (len(report["cases"]) == expected_count
                            and all(c["status"] == "pass" for c in report["cases"])
                            and not report.get("setup_error")
                            and bool(report["negative"] and report["negative"].get("document_difference_detected")
                                     and report["negative"].get("render_difference_detected")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        report["setup_error"] = str(exc)
        print(f"FAIL OB-a1 setup: {exc}", file=sys.stderr, flush=True)
    content = json.dumps(report, indent=2) + "\n"
    if owner_mode:
        try:
            write_owner_report_atomic(args.report, content)
        except (OSError, ValueError) as exc:
            print(f"FAIL OB-a2 report write: {exc}", file=sys.stderr, flush=True)
            return 1
    else:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content, encoding="utf-8")
    total = report.get("owner_files", 0) if owner_mode else report["bundled"] + report["config_shapes"]
    print(f"{report['test']} {sum(c['status']=='pass' for c in report['cases'])}/"
          f"{total} cases; report={args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
