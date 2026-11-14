# SPDX-License-Identifier: GPL-3.0-only
"""Owner-gated cross-tool measurements; --dry-run never opens devices."""
import argparse
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LEVELS = (1, 2, 4, 8, 16, 32, 64)


@dataclass(frozen=True)
class ProcessStat:
    pid: int
    created: float
    cpu_seconds: float
    rss_bytes: int


class CpuSampler:
    """Process-tree CPU: 100 percent means one logical core fully used."""
    def __init__(self):
        self.previous = {}
        self.previous_at = None

    def observe(self, stats, at):
        current = {(s.pid, s.created): s for s in stats}
        total_rss = sum(s.rss_bytes for s in current.values())
        cpu_delta = sum(max(0., s.cpu_seconds - self.previous[k].cpu_seconds)
                        for k, s in current.items() if k in self.previous)
        interval = None if self.previous_at is None else at - self.previous_at
        percent = None if interval is None or interval <= 0 else 100. * cpu_delta / interval
        self.previous = current
        self.previous_at = at
        return {"elapsed_s": at, "processes": len(current), "cpu_percent": percent,
                "rss_bytes": total_rss}


def process_stats(root):
    import psutil
    try:
        all_processes = [root, *root.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        all_processes = [root]
    result = []
    for process in all_processes:
        try:
            times = process.cpu_times()
            result.append(ProcessStat(process.pid, process.create_time(),
                                      times.user + times.system,
                                      process.memory_info().rss))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return result


def measure_process(root, duration=60., interval=.1):
    """Exactly one observation per scheduled interval; no CPU/device access in tests."""
    if duration <= 0 or interval <= 0:
        raise ValueError("duration and interval must be positive")
    sampler = CpuSampler()
    base = time.monotonic()
    sampler.observe(process_stats(root), base)
    results = []
    for index in range(1, int(duration / interval) + 1):
        target = base + index * interval
        time.sleep(max(0., target - time.monotonic()))
        now = time.monotonic()
        result = sampler.observe(process_stats(root), now)
        result["elapsed_s"] = round(now - base, 4)
        results.append(result)
        if not result["processes"]:
            raise RuntimeError("target process exited during sampling")
    return results


def search_max_n(check, levels=LEVELS):
    """Sequential level search, stopping at first failed capacity or xrun check."""
    if not levels or any(n <= 0 for n in levels):
        raise ValueError("invalid scaling levels")
    last = None
    for n in levels:
        if not check(n):
            return last
        last = n
    return last


def summary(samples):
    valid = [s["cpu_percent"] for s in samples if s["cpu_percent"] is not None]
    rss = [s["rss_bytes"] for s in samples]
    valid.sort()
    percentile = lambda p: valid[round((len(valid) - 1) * p)] if valid else None
    return {"samples": len(samples), "cpu_mean_percent": round(sum(valid) / len(valid), 4) if valid else None,
            "cpu_p95_percent": round(percentile(.95), 4) if valid else None,
            "cpu_max_percent": round(max(valid), 4) if valid else None,
            "rss_max_bytes": max(rss, default=0), "cpu_unit": "percent_of_one_logical_core"}


def sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def ask_number(prompt, value, default=None):
    if value is not None:
        return float(value)
    if not sys.stdin.isatty():
        return default
    entry = input(prompt + " (blank = unmeasured): ").strip()
    return float(entry) if entry else default


def prepare_folder(args):
    today = dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    base = HERE / "results" / args.machine / (today + "-" + sha()[:7])
    folder = base
    i = 0
    while folder.exists():
        i += 1
        folder = Path(str(base) + "-" + str(i))
    folder.mkdir(parents=True)
    return folder


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="synthetic process, no audio/MIDI")
    p.add_argument("--confirm-audio", action="store_true", help="explicit owner authorization")
    p.add_argument("--tool", choices=("wirescape", "cardinal", "rack2", "pd", "plugdata"), default="wirescape")
    p.add_argument("--patch", choices=("mono", "poly8", "poly8-fx", "scaling"), default="mono")
    p.add_argument("--tool-version", default="unmeasured")
    p.add_argument("--pid", type=int, help="already-running target tool process")
    p.add_argument("--machine", default="anonymous", help="anonymous label, never a hostname")
    p.add_argument("--audio-device", default="unmeasured")
    p.add_argument("--driver", default="unmeasured")
    p.add_argument("--rate", type=int, choices=(48000,), default=48000)
    p.add_argument("--block", type=int, choices=(256, 128), default=256)
    p.add_argument("--duration", type=float, default=60., help="seconds per patch")
    p.add_argument("--meter", type=float, help="native tool CPU meter percent, owner-observed")
    p.add_argument("--xruns-before", type=int, help="tool/PipeWire/JACK xrun count before measurement")
    p.add_argument("--xruns-after", type=int, help="tool/PipeWire/JACK xrun count after measurement")
    p.add_argument("--audible-dropouts", action="store_true")
    p.add_argument("--scaling", action="store_true", help="guide through N=1,2,4,... with owner prompts")
    p.add_argument("--record", choices=("none", "monitor", "process-loopback", "input"), default="none")
    p.add_argument("--monitor-target", help="explicit PipeWire/Pulse monitor node, not microphone")
    p.add_argument("--process-helper", type=Path, help="Windows device harness PID capture helper")
    p.add_argument("--input-device", help="physical interface loopback input")
    p.add_argument("--audio-file", type=Path, help="existing recording for signal analysis")
    p.add_argument("--tone-file", action="append", default=[], metavar="HZ:FILE")
    p.add_argument("--filter-file", action="append", default=[], metavar="HZ:FILE")
    p.add_argument("--facts", action="store_true", help="write owner-measured provenance to facts/compare/measured")
    return p


def recorder_for(args, folder):
    if args.record == "none":
        return None
    if args.record == "monitor" and not args.monitor_target:
        raise RuntimeError("monitor capture requires --monitor-target")
    if args.record == "input" and args.input_device is None:
        raise RuntimeError("input capture requires --input-device")
    if args.record == "process-loopback" and not args.process_helper:
        raise RuntimeError("Windows PID capture requires --process-helper")
    device_module = ROOT / "bench" / "device"
    if not (device_module / "record.py").is_file():
        raise RuntimeError("recording requires merged bench/device/record.py (PR #13)")
    sys.path.insert(0, str(device_module))
    from record import Recorder
    return Recorder(args.record, folder, args.rate, args.input_device,
                    args.monitor_target, args.process_helper, args.pid)


def probe_files(entries):
    output = {}
    for value in entries:
        freq, sep, path = value.partition(":")
        if not sep or not freq.isdigit() or float(freq) <= 0 or not path:
            raise ValueError("probe entries use HZ:FILE")
        if freq in output:
            raise ValueError("duplicate probe frequency")
        output[freq] = path
    return output


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    # No backend or process is touched before authorization and mode validation.
    if not args.dry_run and not args.confirm_audio:
        p.error("--confirm-audio is required; no audio or MIDI device was opened")
    if args.dry_run and (args.confirm_audio or args.pid or args.record != "none"
                         or args.audio_file or args.tone_file or args.filter_file or args.facts
                         or args.scaling):
        p.error("--dry-run prohibits device/process paths, recordings, scaling and facts publication")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", args.machine):
        p.error("--machine must be a non-identifying label (letters, numbers, _ or -)")
    if not args.dry_run and (not args.pid or args.pid <= 0):
        p.error("owner run requires --pid of an already-running application")
    if args.duration <= 0 or args.duration > 3600:
        p.error("--duration must be within (0, 3600]")
    if args.xruns_before is not None and args.xruns_before < 0:
        p.error("xrun counts cannot be negative")
    if args.xruns_after is not None and args.xruns_after < 0:
        p.error("xrun counts cannot be negative")
    if args.scaling and args.patch != "scaling":
        p.error("--scaling requires --patch scaling")
    import psutil
    folder = prepare_folder(args)
    manifest = {"schema": 1, "mode": "synthetic" if args.dry_run else "owner_device",
                "date_ny": dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
                "commit": sha(), "machine": args.machine, "os": platform.system(),
                "architecture": platform.machine(), "cpu": platform.processor() or platform.machine(),
                "tool": args.tool, "tool_version": args.tool_version,
                "patch": args.patch, "sample_rate_hz": args.rate,
                "buffer_frames": args.block, "audio_device": args.audio_device,
                "driver": args.driver, "sample_interval_s": .1,
                "planned_duration_s": 1.2 if args.dry_run else args.duration,
                "recording_mode": args.record,
                "scope": "same-machine_process_tree_and_manual_device_observations"}
    process = None
    recorder = None
    windows = []
    recordings = []
    error = None
    try:
        if args.dry_run:
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3)"],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            root = psutil.Process(process.pid)
            duration = 1.2
        else:
            root = psutil.Process(args.pid)
            duration = args.duration
        if args.scaling:
            levels = []
            def check(n):
                if args.tool == "wirescape" and 5 * n > 64:
                    levels.append({"n": n, "status": "graph_module_limit", "pass": False})
                    return False
                if not sys.stdin.isatty():
                    raise RuntimeError("scaling needs an interactive owner terminal")
                input(f"Load {n} copies of scaling patch in {args.tool}; press Enter to sample {duration:g}s: ")
                samples = measure_process(root, duration)
                for s in samples:
                    windows.append({"n": n, **s})
                before = ask_number("Read starting xrun counter", None)
                after = ask_number("Read ending xrun counter", None)
                audible = input("Audible dropouts? [y/N]: ").strip().lower().startswith("y")
                xruns = None if before is None or after is None else int(after - before)
                passed = xruns == 0 and not audible
                levels.append({"n": n, "pass": passed, "xruns_delta": xruns,
                               "audible_dropouts": audible, "resources": summary(samples),
                               "status": "measured" if xruns is not None else "unmeasured_xruns"})
                return passed
            max_n = search_max_n(check)
            windows_data = {"levels": levels, "max_passed_n": max_n,
                            "max_n_basis": "sequential_manual_xrun_and_audible_dropout_observations"}
        else:
            if not args.dry_run:
                recorder = recorder_for(args, folder)
                if recorder:
                    recorder.start()
            samples = measure_process(root, duration)
            windows = samples
            before = args.xruns_before
            after = args.xruns_after
            if not args.dry_run:
                before = ask_number("Xrun count at measurement START (from notes)", before)
                after = ask_number("Xrun count at measurement END", after)
            observed = {"native_cpu_meter_percent": ask_number("Tool CPU meter percent", args.meter)
                        if not args.dry_run else None,
                        "xruns_start": before, "xruns_end": after,
                        "xruns_delta": None if before is None or after is None else after - before,
                        "audible_dropouts": args.audible_dropouts if not args.dry_run else None}
            windows_data = {"resources": summary(samples), "owner_observations": observed}
            if recorder:
                audio = recorder.stop()
                if audio:
                    recordings.append(audio)
        from analyse import analyse_recording, analyse_probes
        if args.audio_file:
            recordings.append(args.audio_file)
        analyses = []
        for audio in recordings:
            analyses.append({"file": Path(audio).name, "metrics": analyse_recording(audio)})
        if args.tone_file or args.filter_file:
            windows_data["signal_probes"] = analyse_probes(probe_files(args.tone_file),
                                                           probe_files(args.filter_file))
        windows_data["recordings"] = analyses
    except (OSError, ValueError, RuntimeError, ImportError, psutil.Error) as exc:
        error = str(exc)
        windows_data = locals().get("windows_data", {})
        windows_data["error"] = error
    finally:
        if recorder and recorder.started:
            try:
                recorder.stop()
            except Exception as exc:
                error = error or "recorder cleanup: " + str(exc)
        if process:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        manifest["completed"] = error is None
        manifest["measured"] = not args.dry_run
        write_json(folder / "manifest.json", manifest)
        write_json(folder / "analysis.json", windows_data)
        with (folder / "samples.ndjson").open("w", encoding="utf-8") as out:
            for sample in windows:
                out.write(json.dumps(sample, allow_nan=False) + "\n")
        report = ["# Cross-tool measurement", "",
                  "Mode: " + ("synthetic (no device or benchmark evidence)" if args.dry_run
                              else "owner device measurement"),
                  "", "| Field | Value |", "|---|---|"]
        for key in ("commit", "machine", "tool", "tool_version", "patch", "sample_rate_hz",
                    "buffer_frames", "audio_device", "driver"):
            report.append(f"| {key} | {manifest[key]} |")
        report += ["", "## Measurements", "", "```json",
                   json.dumps(windows_data, indent=2, allow_nan=False), "```", ""]
        if error:
            report += ["## Incomplete", "", error, ""]
        (folder / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print(folder / "report.md")
        if args.facts and not error:
            facts = ROOT / "facts" / "compare" / "measured"
            facts.mkdir(parents=True, exist_ok=True)
            # No recordings, paths, command lines, hostnames or usernames in committed facts.
            write_json(facts / f"{manifest['date_ny']}-{args.machine}-{args.tool}-{args.patch}.json",
                       {"manifest": manifest, "measurement": windows_data,
                        "source": "bench/compare/measure.py", "units": {
                            "cpu": "percent_of_one_logical_core",
                            "rss": "bytes", "duration": "seconds"}})
    if error:
        print("compare harness: " + error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
