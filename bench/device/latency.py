# SPDX-License-Identifier: GPL-3.0-only
"""Owner-gated electrical loopback latency probe. --dry-run never opens a device."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import time
from pathlib import Path
from statistics import median, pstdev
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import numpy as np
from scipy.signal import fftconvolve

from run import Engine, EventLog, commit_sha, locate
from speaker_check import check_audio_state

HERE = Path(__file__).resolve().parent
CLICKS = 40
INTERVAL_S = 0.5
DURATION_S = CLICKS * INTERVAL_S
FREQUENCY_HZ = 1000
CLICK_PEAK = 0.20  # -14 dBFS peak, short gated clicks; patch loads muted.
GATE_DUTY = 0.01  # 5 ms at 120 BPM, plus a 3 ms release.
MIN_CLICKS = 30
MIN_RMS_DBFS = -40.0
SEARCH_S = 0.15


def click_patch(rate: int, block: int) -> dict:
    """Clock -> short function envelope -> VCA of a fixed 1 kHz VCO."""
    return {
        "format": "wirescape.native.patch", "version": 2,
        "settings": {"sample_rate": rate, "max_block_frames": block,
                     "max_channels": 16, "seed": 37, "timing_mode": "immediate"},
        "modules": [
            {"id": 1, "module": "essentials.clock", "version": 2,
             "parameters": {"bpm": 120, "ticks_per_beat": 1,
                            "duty": GATE_DUTY, "run": 0}},
            {"id": 2, "module": "essentials.function_envelope", "version": 2,
             "parameters": {"rise": 0.0001, "fall": 0.003, "curve": 0}},
            {"id": 3, "module": "essentials.vco", "version": 2,
             "parameters": {"frequency": FREQUENCY_HZ}},
            {"id": 4, "module": "essentials.vca", "version": 2,
             "parameters": {"gain": 0}},
            {"id": 5, "module": "essentials.output", "version": 2,
             "parameters": {}}],
        "connections": [
            {"kind": "signal", "from": {"module": 1, "port": "clock"},
             "to": {"module": 2, "port": "gate"}},
            {"kind": "signal", "from": {"module": 3, "port": "audio"},
             "to": {"module": 4, "port": "audio"}},
            {"kind": "signal", "from": {"module": 2, "port": "envelope"},
             "to": {"module": 4, "port": "gain_cv"}},
            {"kind": "signal", "from": {"module": 4, "port": "audio"},
             "to": {"module": 5, "port": "audio"}}],
        "outputs": [{"module": 5, "port": "audio", "bus_channel": ch}
                    for ch in (0, 1)],
    }


def envelope_template(rate: int):
    """Analytic envelope for the built-in clock and function envelope modules."""
    n = max(1, round(0.018 * rate))
    rise = max(1, round(0.0001 * rate))
    on = math.ceil(INTERVAL_S * GATE_DUTY * rate)
    fall = max(1, round(0.003 * rate))
    env = np.zeros(n, dtype=np.float64)
    for i in range(min(n, on)):
        env[i] = min(1.0, (i + 1) / rise)
    for j in range(min(fall, max(0, n - on))):
        env[on + j] = max(0.0, 1.0 - (j + 1) / fall)
    t = np.arange(n, dtype=np.float64) / rate
    phase = 2.0 * np.pi * FREQUENCY_HZ * t
    return CLICK_PEAK * env * np.sin(phase), CLICK_PEAK * env * np.cos(phase)


def synthetic_capture(rate: int, block: int, noise: float = 0.001,
                      seed: int = 37):
    """Generated signal only, with a known delay and independently seeded noise."""
    reference, _ = envelope_template(rate)
    first = rate // 4
    delay = 2 * block + 13
    length = first + CLICKS * (rate // 2) + delay + len(reference)
    rng = np.random.default_rng(seed)
    audio = rng.normal(0, noise, (length, 2)).astype(np.float32)
    for k in range(CLICKS):
        start = first + k * (rate // 2) + delay
        audio[start:start + len(reference), 0] += reference.astype(np.float32)
        audio[start:start + len(reference), 1] -= reference.astype(np.float32) * 0.8
    return audio, first, delay


def measure(audio, rate: int, expected_first_frame: float):
    """Quadrature matched filtering; detect clicks separately near each expected edge.

    The two quadratures tolerate unknown oscillator phase and cable polarity.
    The expected anchor is the host-clock start command, not an inferred peak.
    """
    audio = np.asarray(audio, dtype=np.float64)
    if audio.ndim == 1:
        audio = audio[:, None]
    if audio.ndim != 2 or not audio.size or not np.all(np.isfinite(audio)):
        raise ValueError("capture is empty, malformed or non-finite")
    if rate <= 0:
        raise ValueError("sample rate must be positive")
    s, c = envelope_template(rate)
    energy = float(np.dot(s, s) + np.dot(c, c))
    if len(audio) < len(s):
        raise ValueError("capture shorter than a click")
    best = None
    radius = round(SEARCH_S * rate)
    interval = round(rate * INTERVAL_S)
    for channel in range(audio.shape[1]):
        signal = audio[:, channel]
        rms = float(np.sqrt(np.mean(signal ** 2)))
        dbfs = 20 * math.log10(max(rms, 1e-15))
        if dbfs < MIN_RMS_DBFS:
            continue
        sin_corr = fftconvolve(signal, s[::-1], mode="valid")
        cos_corr = fftconvolve(signal, c[::-1], mode="valid")
        magnitude = np.hypot(sin_corr, cos_corr)
        arrivals = []
        for k in range(CLICKS):
            expected = expected_first_frame + interval * k
            lo = max(0, int(math.floor(expected - radius)))
            hi = min(len(magnitude), int(math.ceil(expected + radius)) + 1)
            if lo >= hi:
                continue
            pos = lo + int(np.argmax(magnitude[lo:hi]))
            local_energy = float(np.dot(signal[pos:pos + len(s)],
                                        signal[pos:pos + len(s)]))
            score = float(magnitude[pos]) / max(math.sqrt(energy * local_energy), 1e-15)
            if score >= 0.35:
                arrivals.append({"click": k, "start_frame": pos,
                                 "delay_frames": round(pos - expected, 4),
                                 "match": round(score, 4)})
        candidate = {"rms_dbfs": dbfs, "channel": channel,
                     "clicks_found": len(arrivals), "arrivals": arrivals}
        if best is None or len(arrivals) > best["clicks_found"]:
            best = candidate
    if best is None:
        levels = 20 * np.log10(np.maximum(
            np.sqrt(np.mean(audio ** 2, axis=0)), 1e-15))
        raise ValueError(f"recorded level below -40 dBFS (highest channel {float(np.max(levels)):.2f} dBFS)")
    if best["clicks_found"] < MIN_CLICKS:
        raise ValueError(f"only {best['clicks_found']} of {CLICKS} clicks found; at least {MIN_CLICKS} required")
    frames = [a["delay_frames"] for a in best["arrivals"]]
    best["frames"] = {
        "median": float(median(frames)), "min": float(min(frames)),
        "max": float(max(frames)), "stddev": float(pstdev(frames))}
    best["ms"] = {key: val * 1000.0 / rate for key, val in best["frames"].items()}
    return best


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="generated click train with known delay; no hardware or engine")
    p.add_argument("--confirm-audio", action="store_true",
                   help="explicit owner authorization for real output and input devices")
    p.add_argument("--device", help="engine output audio device ID (required for hardware)")
    p.add_argument("--input-device", help="PortAudio input index/name (required for hardware)")
    p.add_argument("--engine", type=Path, help="wirescape-engine path (auto-detected if omitted)")
    p.add_argument("--rate", type=int, choices=(44100, 48000, 96000), default=48000)
    p.add_argument("--block", type=int, choices=(64, 128, 256, 512, 1024), default=256)
    p.add_argument("--sweep", action="store_true", help="run blocks 64, 128 and 256")
    p.add_argument("--machine", default="device", help="anonymous machine identifier")
    p.add_argument("--results", type=Path, default=HERE / "results")
    return p


def check_options(p, args):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", args.machine):
        p.error("--machine must be an anonymous 1-48 character label")
    if args.dry_run:
        if args.confirm_audio or args.device or args.input_device:
            p.error("--dry-run prohibits authorization flags and device selection")
    elif not args.confirm_audio:
        p.error("--confirm-audio is required; no device has been opened")
    elif not args.device or not args.input_device:
        p.error("hardware latency requires both --device and --input-device")
    if args.engine and not args.engine.is_file():
        p.error("--engine path does not exist")
    if not args.dry_run and not args.engine:
        args.engine = locate("wirescape-engine")
        if args.engine is None:
            p.error("wirescape-engine not found; specify --engine")


def observed_audio(log, initial):
    with log.lock:
        statuses = [e["payload"]["status"]["audio"] for e in log.events
                    if e.get("direction") == "out"
                    and e.get("payload", {}).get("type") == "status"
                    and isinstance(e.get("payload", {}).get("status", {}).get("audio"), dict)]
    return next((s for s in reversed(statuses)
                 if s.get("state") == "running" and s.get("deviceId")), initial)


def physical_capture(args, block, folder):
    """Return captured frames and host-command timing; must never run in dry mode."""
    from record import Recorder
    import soundfile as sf

    config = SimpleNamespace(dry_run=False, engine=args.engine,
                             rate=args.rate, block=block, device=args.device,
                             confirm_midi=False)
    log = EventLog(folder / "events.ndjson")
    engine = recorder = None
    capture_path = None
    error = None
    try:
        engine = Engine(config, folder, log)
        engine.start()
        before = check_audio_state(engine, config, log)
        rate = int(before.get("sampleRate", 0))
        reported_block = int(before.get("bufferFrames", 0))
        if rate != args.rate or reported_block != block:
            raise RuntimeError(f"engine reported rate/block {rate}/{reported_block}; requested {args.rate}/{block}")
        engine.send({"type": "loadGraph", "patch": click_patch(rate, block)})
        input_id = int(args.input_device) if args.input_device.isdecimal() else args.input_device
        recorder = Recorder("input", folder, rate, input_device=input_id)
        recorder.start()
        time.sleep(0.2)
        engine.send({"type": "setParam", "moduleId": 4, "paramId": "gain",
                     "value": CLICK_PEAK})
        sent = time.monotonic()
        engine.send({"type": "setParam", "moduleId": 1, "paramId": "run",
                     "value": 1})
        ack = time.monotonic()
        time.sleep(DURATION_S + 0.3)
        engine.send({"type": "setParam", "moduleId": 1, "paramId": "run",
                     "value": 0})
        engine.send({"type": "setParam", "moduleId": 4, "paramId": "gain",
                     "value": 0})
        capture_path = recorder.stop()
        if recorder.first_sample_monotonic is None:
            raise RuntimeError("input recorder supplied no ADC timestamp")
        after = observed_audio(log, before)
        if after.get("sampleRate") != rate or after.get("bufferFrames") != reported_block:
            raise RuntimeError("engine output rate/buffer changed during capture")
        with sf.SoundFile(str(capture_path)) as wav:
            if wav.samplerate != rate or wav.channels != 2:
                raise RuntimeError("recording format does not match reported engine rate")
            audio = wav.read(dtype="float32", always_2d=True)
        return audio, {
            "rate_hz": rate, "buffer_frames": reported_block,
            "device_id": after.get("deviceId"),
            "input_device": args.input_device,
            "anchor_uncertainty_ms": 500 * (ack - sent),
            "expected_first_frame": ((sent + ack) / 2
                                     - recorder.first_sample_monotonic) * rate,
            "capture_file": str(capture_path.name),
            "anchor": "host-command-midpoint / PortAudio ADC timestamp",
        }
    finally:
        if recorder and recorder.started is not None:
            try:
                recorder.stop()
            except Exception as exc:
                error = str(exc)
        if engine:
            try:
                if engine.process and engine.process.poll() is None:
                    engine.send({"type": "setParam", "moduleId": 4,
                                 "paramId": "gain", "value": 0}, timeout=3)
            except Exception:
                pass
            engine.stop()
        log.close()
        if error and sys.exc_info()[0] is None:
            raise RuntimeError("recorder cleanup: " + error)


def run_one(args, block, sha, date):
    base = args.results / args.machine / f"{date}-{sha[:7]}-latency-{block}"
    folder = base
    suffix = 1
    while folder.exists():
        folder = Path(f"{base}-{suffix}")
        suffix += 1
    folder.mkdir(parents=True)
    details = {
        "schema": 1, "kind": "round-trip-latency", "machine": args.machine,
        "date": date, "commit": sha, "dry_run": args.dry_run,
        "requested_rate_hz": args.rate, "requested_block_frames": block,
        "clicks_expected": CLICKS, "interval_s": INTERVAL_S,
        "duration_s": DURATION_S, "click_peak_dbfs": 20 * math.log10(CLICK_PEAK),
        "completed": False,
    }
    try:
        if args.dry_run:
            audio, first, known = synthetic_capture(args.rate, block)
            meta = {"rate_hz": args.rate, "buffer_frames": block,
                    "expected_first_frame": first, "synthetic_delay_frames": known,
                    "anchor": "exact synthetic sample index"}
        else:
            audio, meta = physical_capture(args, block, folder)
        details.update(meta)
        results = measure(audio, meta["rate_hz"], meta["expected_first_frame"])
        details["measurement"] = results
        details["difference_from_2x_buffer_frames"] = (
            results["frames"]["median"] - 2 * meta["buffer_frames"])
        details["difference_from_2x_buffer_ms"] = (
            details["difference_from_2x_buffer_frames"] * 1000 / meta["rate_hz"])
        details["completed"] = True
    except (RuntimeError, ValueError, OSError, ImportError, TimeoutError) as exc:
        details["error"] = str(exc)
    finally:
        (folder / "latency.json").write_text(
            json.dumps(details, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        lines = ["<!-- SPDX-License-Identifier: GPL-3.0-only -->",
                 "# Electrical loopback latency", "",
                 f"Mode: {'synthetic (no hardware)' if args.dry_run else 'owner-authorized hardware'}",
                 f"Rate: {details.get('rate_hz', args.rate)} Hz; "
                 f"engine buffer: {details.get('buffer_frames', block)} frames",
                 f"Clicks: {details.get('measurement', {}).get('clicks_found', 0)}/{CLICKS}",
                 f"Status: {'complete' if details['completed'] else 'REFUSED: ' + details.get('error', 'unknown')}",
                 ""]
        if details["completed"]:
            r = details["measurement"]
            for unit in ("frames", "ms"):
                numbers = r[unit]
                lines.append(f"{unit}: median={numbers['median']:.3f}, "
                             f"min={numbers['min']:.3f}, max={numbers['max']:.3f}, "
                             f"stddev={numbers['stddev']:.3f}")
            lines.append(f"Median minus 2 × buffer: "
                         f"{details['difference_from_2x_buffer_frames']:.3f} frames "
                         f"({details['difference_from_2x_buffer_ms']:.3f} ms)")
            lines.append(f"Selected input channel RMS: {r['rms_dbfs']:.2f} dBFS")
        if not args.dry_run:
            lines += ["", "Timing limitation: the source is armed by a host command, "
                      "not a DAC timestamp. This is a command-to-ADC loopback "
                      "estimate; the request/ack bracket and driver clocks contribute "
                      "uncertainty. Do not call this a sample-accurate DAC-to-ADC latency. "
                      f"Protocol anchor half-width: {details.get('anchor_uncertainty_ms', 0):.3f} ms."]
        (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(folder / "report.md")
    return bool(details["completed"])


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    check_options(p, args)
    sha = commit_sha()
    date = dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    blocks = (64, 128, 256) if args.sweep else (args.block,)
    success = True
    for block in blocks:
        if not run_one(args, block, sha, date):
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
