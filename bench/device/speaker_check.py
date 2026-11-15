# SPDX-License-Identifier: GPL-3.0-only
"""Owner-authorized 440 Hz speaker-path check; no device access from tests/CI."""
from __future__ import annotations

import json
import math
import sys
import time

FREQUENCY_HZ = 440
TARGET_RMS_DBFS = -18.0
TONE_SECONDS = 5.0
# A full-scale sine has RMS 1/sqrt(2); the VCA must produce a peak of
# 10^(-18/20)*sqrt(2) to place its RMS near -18 dBFS.
TARGET_PEAK = round(10 ** (TARGET_RMS_DBFS / 20) * math.sqrt(2), 6)


def tone_patch(rate, block):
    """The built-in VCO/VCA/output path, sent over v0 loadGraph."""
    return {
        "format": "wirescape.native.patch", "version": 2,
        "settings": {"sample_rate": rate, "max_block_frames": block,
                     "max_channels": 16, "seed": 37, "timing_mode": "immediate"},
        "modules": [
            {"id": 1, "module": "essentials.vco", "version": 2,
             "parameters": {"frequency": FREQUENCY_HZ}},
            {"id": 2, "module": "essentials.vca", "version": 2,
             "parameters": {"gain": 0.0}},
            {"id": 3, "module": "essentials.output", "version": 2,
             "parameters": {}}],
        "connections": [
            {"kind": "signal", "from": {"module": 1, "port": "audio"},
             "to": {"module": 2, "port": "audio"}},
            {"kind": "signal", "from": {"module": 2, "port": "audio"},
             "to": {"module": 3, "port": "audio"}}],
        "outputs": [
            {"module": 3, "port": "audio", "bus_channel": 0},
            {"module": 3, "port": "audio", "bus_channel": 1}],
    }


def check_audio_state(engine, args, log):
    """Refuse a real run when the selected output is not actually running."""
    if args.dry_run:
        return {"state": "null", "deviceId": None}
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        with log.lock:
            statuses = [e["payload"]["status"]["audio"] for e in log.events
                        if e.get("direction") == "out"
                        and e.get("payload", {}).get("type") == "status"
                        and isinstance(e.get("payload", {}).get("status", {}).get("audio"), dict)]
        status = statuses[-1] if statuses else engine.hello.get("audio", {})
        if status.get("state") == "running" and status.get("deviceId"):
            if args.device and status["deviceId"] != args.device:
                raise RuntimeError("speaker check is not on the requested audio device")
            return status
        time.sleep(.1)
    raise RuntimeError("selected audio output was not running; no tone confirmation requested")


def run_check(args, folder, log, engine_class):
    """Return owner observation. The only physical playback is behind --confirm-audio."""
    dry = args.dry_run
    duration = .25 if dry else TONE_SECONDS
    observation = {
        "schema": 1, "kind": "speaker-check",
        "frequency_hz": FREQUENCY_HZ,
        "target_rms_dbfs": TARGET_RMS_DBFS,
        "target_sine_peak": TARGET_PEAK,
        "tone_seconds": TONE_SECONDS,
        "render_elapsed_seconds": duration,
        "rate_hz": args.rate, "block_frames": args.block,
        "requested_device": args.device or "default",
        "mode": "null-audio" if dry else "owner-authorized-device",
        "heard": "not-applicable-null-sink" if dry else "not-confirmed",
        "engine_mode": "simulation" if dry and not args.engine else
                       "null-audio" if dry else "device",
        "completed": False,
    }
    engine = None
    playback_error = None
    try:
        engine = engine_class(args, folder, log)
        engine.start()
        state = check_audio_state(engine, args, log)
        observation["observed_device"] = state.get("deviceId")
        engine.send({"type": "loadGraph", "patch": tone_patch(args.rate, args.block)})
        # Two short ramps bound start/stop transients. Both branches send the
        # same patch and protocol; only null-sink wall time is compressed.
        ramp = .012 if dry else .05
        started = time.monotonic()
        for fraction in (.25, .5, .75, 1.0):
            engine.send({"type": "setParam", "moduleId": 2, "paramId": "gain",
                         "value": round(TARGET_PEAK * fraction, 6)})
            time.sleep(ramp / 4)
        remaining = duration - (time.monotonic() - started) - ramp
        if remaining > 0:
            time.sleep(remaining)
        for fraction in (.75, .5, .25, 0.0):
            engine.send({"type": "setParam", "moduleId": 2, "paramId": "gain",
                         "value": round(TARGET_PEAK * fraction, 6)})
            time.sleep(ramp / 4)
        # The gain ramp ends at zero; stopping the owned sidecar ends playback.
    except (RuntimeError, OSError, ValueError, TimeoutError) as error:
        playback_error = str(error)
        observation["error"] = playback_error
    finally:
        if engine:
            engine.stop()
            if engine.process is not None:
                observation["engine_exit_code"] = engine.process.returncode
                if engine.process.returncode != 0:
                    playback_error = playback_error or "speaker-check engine exited nonzero"
                    observation["error"] = playback_error
    if playback_error is None and not dry:
        if sys.stdin.isatty():
            try:
                response = input("Was the 440 Hz tone clearly audible on the intended speaker? [yes/no]: ").strip().lower()
            except EOFError:
                response = ""
            observation["heard"] = "yes" if response in ("yes", "y") else (
                "no" if response in ("no", "n") else "not-confirmed")
        else:
            observation["heard"] = "not-confirmed-noninteractive"
    observation["completed"] = playback_error is None and (dry or observation["heard"] == "yes")
    (folder / "owner-observations.json").write_text(
        json.dumps(observation, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if playback_error:
        raise RuntimeError(playback_error)
    if not observation["completed"]:
        raise RuntimeError("speaker check not confirmed audible; inspect output device and levels")
    return observation
