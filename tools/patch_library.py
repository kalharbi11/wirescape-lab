# SPDX-License-Identifier: GPL-3.0-only
"""Check patches offline, validate shared JSON, or install to a local patch folder."""
import argparse
import json
import math
import os
from pathlib import Path
import tempfile
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 2 * 1024 * 1024


def need(ok, message):
    if not ok:
        raise ValueError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate(data, catalogue, shared=False):
    need(isinstance(data, dict), "patch must be an object")
    need(data.get("format") == "wirescape.native.patch" and data.get("version") == 2,
         "export a native patch v2 from Studio")
    modules, cables = data.get("modules"), data.get("connections")
    need(isinstance(modules, list) and 0 < len(modules) <= 32, "require 1–32 modules")
    need(isinstance(cables, list) and len(cables) <= 128, "require <=128 connections")
    registry = {item["id"]: item for item in catalogue["modules"]}
    nodes = {}
    for module in modules:
        need(isinstance(module, dict), "invalid module")
        ident = module.get("id")
        need(type(ident) is int and 0 <= ident <= 0xffffffff and ident not in nodes,
             "invalid/duplicate node ID")
        descriptor = registry.get(module.get("module"))
        need(descriptor is not None, f"module unavailable: {module.get('module')}")
        need(module.get("version", descriptor["version"]) == descriptor["version"],
             f"module version differs from catalogue: {module.get('module')}")
        params = module.get("parameters", {})
        need(isinstance(params, dict), "invalid parameters")
        specs = {p["id"]: p for p in descriptor["parameters"]}
        for key, value in params.items():
            spec = specs.get(key)
            need(spec is not None and number(value), f"unknown/nonfinite parameter: {key}")
            need(spec["minimum"] <= value <= spec["maximum"], f"parameter out of range: {key}")
        nodes[ident] = descriptor

    def port(endpoint, direction, kind):
        need(isinstance(endpoint, dict), "invalid endpoint")
        descriptor = nodes.get(endpoint.get("module"))
        need(descriptor is not None, "dangling module reference")
        matches = [p for p in descriptor["ports"] if p["id"] == endpoint.get("port")
                   and p["direction"] == direction and p["kind"] == kind]
        need(bool(matches), f"missing/wrong-kind {direction} port: {endpoint}")
        return descriptor

    for cable in cables:
        need(isinstance(cable, dict), "invalid connection")
        kind = cable.get("kind")
        need(kind in ("signal", "event", "modulation"), "invalid connection kind")
        port(cable.get("from"), "output", "event" if kind == "event" else "signal")
        if kind == "modulation":
            target = cable.get("to")
            need(isinstance(target, dict), "invalid modulation target")
            descriptor = nodes.get(target.get("module"))
            need(descriptor is not None, "dangling modulation target")
            need(any(p["id"] == target.get("port") and p.get("modulatable")
                     for p in descriptor["parameters"]), "target is not a modulatable parameter")
            amount = cable.get("amount", 1)
            need(number(amount) and -1 <= amount <= 1, "modulation amount outside [-1,1]")
        else:
            port(cable.get("to"), "input", kind)
    routes = data.get("outputs")
    need(isinstance(routes, list) and routes, "explicit output routes required")
    for route in routes:
        port(route, "output", "signal")
        bus = route.get("bus_channel")
        need(type(bus) is int and 0 <= bus < 16, "invalid output bus")
    if shared:
        need("name" not in data or (isinstance(data["name"], str) and 0 < len(data["name"]) <= 240), "shared patch name must be 1–240 characters")
        need(not data.get("devices"), "remove private device bindings before sharing")
        need(not any(m["module"].startswith("midi.") for m in modules), "web library excludes hardware MIDI modules; use host.keyboard")
        settings = data.get("settings", {})
        need(isinstance(settings, dict), "invalid settings")
        need(settings.get("sample_rate", 48000) == 48000, "shared fast lane uses 48 kHz")
        need(all(r["bus_channel"] in (0, 1) for r in routes), "shared fast lane is stereo")
    return sorted({m["module"] for m in modules})


def read_patch(path, catalogue, shared=False):
    need(path.is_file() and not path.is_symlink(), f"not a regular patch file: {path}")
    need(path.suffix.lower() == ".json" and path.stat().st_size <= LIMIT, "JSON limit is 2 MiB")
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(
        ValueError("nonfinite JSON: " + x)))
    return raw, validate(data, catalogue, shared)


def install(path, dest, raw, replace=False):
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / path.name
    need(not target.is_symlink(), "refusing symbolic-link destination")
    if target.exists():
        need(replace, f"{target} exists; use --replace for an intentional edit")
        need(target.is_file(), "destination is not a file")
        # Preserve a recoverable copy; never overwrite an earlier backup.
        with tempfile.NamedTemporaryFile(prefix=path.name + ".", suffix=".bak",
                                         dir=dest, delete=False) as backup:
            backup.write(target.read_bytes())
        print("Backup:", backup.name)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=dest)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        if replace:
            os.replace(temporary, target)
        else:
            # Atomic no-clobber even if a file appears after the earlier check.
            os.link(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print("Installed:", target)


def analyse_pcm(pcm, rate):
    """Count nonfinite samples; peak/RMS over finite stereo float32 samples."""
    need(len(pcm) % 8 == 0 and rate > 0, "invalid stereo PCM")
    count = bad = 0
    peak = energy = 0.0
    post = False
    has_post = len(pcm) > rate * 8
    for i, (value,) in enumerate(struct.iter_unpack("<f", pcm)):
        if i >= rate * 2 and value != 0:
            post = True
        if not math.isfinite(value):
            bad += 1
            continue
        count += 1
        peak = max(peak, abs(value))
        energy += value * value
    return {"nan_inf_samples": bad, "peak": peak if count else None,
            "rms": math.sqrt(energy / count) if count else None,
            "silent": not post if has_post else None}


def offline_check_patch(path, renderer, rate, block, seconds):
    row = {"patch": path.name, "load_ok": False, "reason": None,
           "nan_inf_samples": None, "peak": None, "rms": None,
           "silent": None, "timing": None}
    try:
        need(path.is_file() and not path.is_symlink(), "not a regular patch file")
        need(path.stat().st_size <= LIMIT, "JSON limit is 2 MiB")
        raw = path.read_bytes()
        patch = json.loads(raw.decode("utf-8"), parse_constant=lambda x: (
            _ for _ in ()).throw(ValueError("nonfinite JSON: " + x)))
        need(isinstance(patch, dict), "patch must be an object")
        seed = patch.get("settings", {}).get("seed", 42)
        need(type(seed) is int and 0 <= seed < 2**64, "invalid seed")
        # Snapshot the input; do not let the renderer or report modify a patch.
        with tempfile.TemporaryDirectory(prefix="ws-patch-check-") as tmp:
            work = Path(tmp)
            source, script, wav = (work / "patch.json", work / "events.json",
                                   work / "audio.wav")
            source.write_bytes(raw)
            # No external events: check unattended behavior, not audibility of
            # a keyboard/OSC-triggered performance.
            script.write_text("[]", encoding="utf-8")
            command = [str(renderer), "--patch", str(source), "--script", str(script),
                       "--out", str(wav), "--rate", str(rate), "--block", str(block),
                       "--seconds", str(seconds), "--seed", str(seed), "--timing"]
            run = subprocess.run(command, capture_output=True, text=True, timeout=120)
            need(run.returncode == 0, f"native load/render refused (exit {run.returncode}): "
                 + run.stderr.strip()[-1200:])
            records = [line[len("render_metrics "):] for line in run.stdout.splitlines()
                       if line.startswith("render_metrics ")]
            need(len(records) == 1, "missing native render metrics")
            metrics = json.loads(records[0])
            counters = ("faults", "late_events", "dropped_events",
                        "ring_full_events", "stale_events", "arena_full_events")
            need(all(type(metrics.get(k)) is int and metrics[k] == 0 for k in counters),
                 "native render event accounting failed")
            timing = metrics["timing"]
            frames = math.floor(rate * seconds + 0.5)
            expected_blocks = (frames + block - 1) // block
            need(type(timing["blocks"]) is int and timing["blocks"] == expected_blocks
                 and type(timing["overruns"]) is int
                 and 0 <= timing["overruns"] <= expected_blocks, "invalid timing counts")
            need(all(number(timing[k]) and timing[k] >= 0 for k in
                     ("p50_us", "p99_us", "worst_us", "period_us"))
                 and 0 <= timing["p50_us"] <= timing["p99_us"] <= timing["worst_us"]
                 and math.isclose(timing["period_us"], block * 1e6 / rate),
                 "invalid native timing metrics")
            audio = wav.read_bytes()
            need(len(audio) == 44 + frames * 8 and audio[:4] == b"RIFF"
                 and audio[8:16] == b"WAVEfmt " and audio[36:40] == b"data"
                 and struct.unpack_from("<IHHIIHH", audio, 16) ==
                 (16, 3, 2, rate, rate * 8, 8, 32)
                 and struct.unpack_from("<I", audio, 40)[0] == frames * 8,
                 "invalid native stereo float32 WAV")
            values = analyse_pcm(memoryview(audio)[44:], rate)
            for stat in ("p50", "p99", "worst"):
                timing[stat + "_percent"] = timing[stat + "_us"] * 100 / timing["period_us"]
            row.update(values, load_ok=True, timing=timing)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError,
            subprocess.TimeoutExpired) as error:
        row["reason"] = str(error).replace("\\n", " ").replace("\\r", " ")
    return row


def offline_check(args):
    source = args.source
    need(source.is_dir() and not source.is_symlink(), "check requires a regular patch folder")
    need(8000 <= args.rate <= 96000 and 1 <= args.block <= 1024
         and math.isfinite(args.seconds) and 0 < args.seconds <= 10
         and math.floor(args.rate * args.seconds + 0.5) > 0,
         "invalid rate/block/duration (renderer limit: 10 seconds)")
    paths = sorted(source.glob("*.json"))
    need(bool(paths), "no JSON patches found")
    renderer = args.renderer.resolve()
    need(renderer.is_file(), "compiled wirescape_render missing; build --headless first")
    if args.json is not None:
        dest = args.json
        need(not dest.is_symlink() and not dest.resolve().is_relative_to(source.resolve()),
             "report must be outside patch folder and not a symlink")
        need(dest.parent.is_dir(), "report parent directory does not exist")
    rows = [offline_check_patch(p, renderer, args.rate, args.block, args.seconds) for p in paths]
    report = {"schema_version": 1, "rate": args.rate, "block": args.block,
              "seconds": args.seconds, "patches": rows}
    print("Patch | Load/render | NaN/Inf | Peak | RMS | Silent | p50/p99/worst us (% period) | Overruns")
    print("Timing: host-specific diagnostics; not a real-device latency or CPU guarantee.")
    def fmt(value):
        return "unmeasured" if value is None else f"{value:.6g}"
    for row in rows:
        timing = row["timing"]
        summary = "unmeasured" if timing is None else "/".join(
            f"{timing[k + '_us']:.3f} ({timing[k + '_percent']:.2f}%)"
            for k in ("p50", "p99", "worst"))
        silent = "unmeasured" if row["silent"] is None else str(row["silent"]).lower()
        print(f"{row['patch']} | {'ok' if row['load_ok'] else 'refused'} | "
              f"{fmt(row['nan_inf_samples'])} | {fmt(row['peak'])} | {fmt(row['rms'])} | "
              f"{silent} | {summary} | {timing['overruns'] if timing else 'unmeasured'}")
        if row["reason"]:
            print("  Reason:", row["reason"])
    content = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.json is None:
        print(content, end="")
    else:
        # Atomic replacement avoids truncating a report hard-linked to a source.
        fd, tmp = tempfile.mkstemp(prefix="." + dest.name + ".", dir=dest.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write(content)
            os.replace(tmp, dest)
        finally:
            Path(tmp).unlink(missing_ok=True)
    return int(any(not r["load_ok"] or r["nan_inf_samples"] for r in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "install"))
    parser.add_argument("source", type=Path)
    parser.add_argument("--dest", type=Path, help="actual folder shown by desktop Save As")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--shared", action="store_true", help="48k/stereo/no-device sharing profile")
    parser.add_argument("--rate", type=int, default=48000)
    parser.add_argument("--block", type=int, default=128)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--json", type=Path, help="offline JSON report (outside patch folder)")
    parser.add_argument("--renderer", type=Path, default=ROOT / "build/native" /
                        ("wirescape_render.exe" if sys.platform == "win32" else "wirescape_render"))
    args = parser.parse_args()
    try:
        if args.action == "check" and not args.shared and args.source.is_dir():
            return offline_check(args)
        catalogue = json.loads((ROOT / "apps/studio/public/wirescape_modules.json").read_text())
        paths = sorted(args.source.glob("*.json")) if args.source.is_dir() else [args.source]
        need(bool(paths) or (args.action == "check" and args.source.is_dir()), "no JSON patches found")
        prepared = [(p, *read_patch(p, catalogue, args.shared)) for p in paths]
        if args.action == "install":
            need(args.dest is not None, "install requires --dest; use the actual desktop patch folder")
            for path, raw, _ in prepared:
                install(path, args.dest, raw, args.replace)
        for path, _, modules in prepared:
            web = "desktop MIDI required" if any(m.startswith("midi.") for m in modules) else "web module set"
            print(f"PASS {path}: {len(modules)} module types; {web}; structural check only")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Patch error: {error}\n")


if __name__ == "__main__":
    sys.exit(main())

