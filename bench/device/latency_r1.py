# SPDX-License-Identifier: GPL-3.0-only
"""M0 R1: duplex harness sample delay, command-to-ADC, and sound *range*.

No audio backend is imported until explicit owner authorization. Synthetic
mode has no native process, stream or real-device dependency.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import threading
import time
from pathlib import Path
from statistics import median, pstdev

import numpy as np

REPEATS = 40
INTERVAL_S = 0.5
MIN_DETECTED = 30
MIN_LEVEL_DBFS = -40.0


def summary(values):
    """Nearest-rank p95; no one-off events can masquerade as a distribution."""
    seq = [float(x) for x in values]
    if len(seq) < 20 or not all(math.isfinite(x) for x in seq):
        raise ValueError("requires at least 20 finite observations")
    ordered = sorted(seq)
    return {
        "repeats": len(seq), "median": float(median(ordered)),
        "p95": ordered[math.ceil(.95 * len(seq)) - 1],
        "min": ordered[0], "max": ordered[-1],
        "stddev": float(pstdev(ordered)),
    }


def harness_loopback_ms(output_indices, captured_indices, rate):
    """ONE duplex stream: output sample index -> input sample index; no clock."""
    if rate <= 0 or len(output_indices) != len(captured_indices):
        raise ValueError("invalid duplex sample indices or sample rate")
    offsets = []
    for output, capture in zip(output_indices, captured_indices):
        if not (isinstance(output, int) and isinstance(capture, int) and
                output >= 0 and capture >= output):
            raise ValueError("duplex capture precedes output or noninteger sample index")
        offsets.append((capture - output) * 1000.0 / rate)
    return {"quantity": "harness_loopback_ms", "units": "ms",
            "method": "single full-duplex stream output/input sample-index difference / rate; no wall clock",
            "statistics": summary(offsets), "observations_ms": offsets}


def block_for_index(blocks, frame):
    for block in blocks:
        if block["start_frame"] <= frame < block["start_frame"] + block["frames"]:
            return block
    raise ValueError(f"no capture callback metadata for onset at frame {frame}")


def command_to_capture_ms(command_writes, onset_indices, blocks, rate):
    """Command-write monotonic to ADC buffer timestamp + within-buffer index/rate.

    ADC relative stream times are projected into Python monotonic by sampling
    PortAudio currentTime and Python monotonic at callback entry. The projection
    carries an uncalibrated scheduling/clock offset: do not invent a finite
    *absolute* error bound. If ADC time is absent use callback time, explicitly
    adding one full capture buffer to stated additional uncertainty.
    """
    if rate <= 0 or len(command_writes) != len(onset_indices):
        raise ValueError("command/onset counts differ or invalid sample rate")
    elapsed, additions, modes = [], [], []
    for command, frame in zip(command_writes, onset_indices):
        if not math.isfinite(float(command)) or not isinstance(frame, int):
            raise ValueError("invalid command time or onset index")
        block = block_for_index(blocks, frame)
        if block["frames"] <= 0 or not math.isfinite(block["callback_monotonic_s"]):
            raise ValueError("invalid callback metadata")
        within_s = (frame - block["start_frame"]) / rate
        adc = block.get("adc_monotonic_s")
        if adc is not None and math.isfinite(float(adc)):
            onset_time = float(adc) + within_s
            additions.append(0.0)
            modes.append("adc")
        else:
            onset_time = block["callback_monotonic_s"] + within_s
            additions.append(block["frames"] * 1000.0 / rate)
            modes.append("callback_fallback")
        elapsed.append((onset_time - float(command)) * 1000.0)
    stats = summary(elapsed)
    return {
        "quantity": "command_to_capture_ms", "units": "ms",
        "statistics": stats, "observations_ms": elapsed,
        "timestamp_sources": {"adc": modes.count("adc"),
                              "callback_fallback": modes.count("callback_fallback")},
        "additional_capture_buffer_uncertainty_ms": {
            "per_observation": additions, "max": max(additions),
            "explanation": "one whole observed capture buffer added for each missing ADC timestamp"
        },
        "absolute_clock_mapping_error_bound_ms": None,
        "clock_limit": "PortAudio relative currentTime/ADC projected at Python callback entry; host scheduling offset not calibrated",
    }


def command_to_sound_ms(command, harness):
    """Never a scalar: exactly [command_to_capture - harness_loopback, capture]."""
    a = command["statistics"]
    b = harness["statistics"]
    ranges = {}
    for quantile in ("median", "p95"):
        capture_ms = a[quantile]
        loopback_ms = b[quantile]
        ranges[quantile] = {
            "lower_ms": capture_ms - loopback_ms,
            "upper_ms": capture_ms
        }
    return {
        "quantity": "command_to_sound_ms", "representation": "range_only",
        "range_ms": ranges, "method": "[command_to_capture_ms - harness_loopback_ms, command_to_capture_ms]",
        "caveat": "range is R1 arithmetic, not a directly timestamped DAC onset or independent absolute-error bound",
    }


def ensure_detected(arrivals, expected=REPEATS):
    if len(arrivals) < MIN_DETECTED:
        raise ValueError(f"only {len(arrivals)} of {expected} clicks found; at least {MIN_DETECTED} required")
    return arrivals


def find_command_onsets(audio, rate, commands, blocks):
    """Detect rising short VCA command pulses after each host write.

    Search an explicit command-relative window; baseline must be silent.
    A 1 ms moving RMS detector tolerates oscillator phase and nonzero driver
    gain smoothing without declaring unrelated constant audio a click.
    """
    samples = np.asarray(audio, dtype=np.float64)
    if samples.ndim != 2 or samples.shape[1] < 1 or not np.isfinite(samples).all():
        raise ValueError("empty or nonfinite command capture")
    rms = float(np.sqrt(np.mean(samples * samples)))
    dbfs = 20 * math.log10(max(rms, 1e-15))
    if dbfs < MIN_LEVEL_DBFS:
        raise ValueError(f"recorded level below -40 dBFS ({dbfs:.2f} dBFS)")
    strength = np.max(np.abs(samples), axis=1)
    smooth_count = max(2, int(round(rate * .001)))
    # Causal window energy; no lookahead offset hidden from reported index.
    squared = strength * strength
    power = np.convolve(squared, np.ones(smooth_count)/smooth_count, mode="same")
    threshold = max(0.008, float(np.median(np.sqrt(power))) * 8)
    arrivals = []
    for k, stamp in enumerate(commands):
        if not blocks:
            raise ValueError("missing capture callback timing blocks")
        anchor = min(blocks, key=lambda b: abs(
            b["start_frame"]/rate -
            ((stamp - blocks[0]["callback_monotonic_s"]) +
             blocks[0]["start_frame"]/rate)))
        reference = anchor.get("adc_monotonic_s")
        if reference is None:
            reference = anchor["callback_monotonic_s"]
        expected = anchor["start_frame"] + round((stamp - reference)*rate)
        lo = max(0, expected - round(.04 * rate))
        hi = min(len(strength), expected + round(.25 * rate))
        if lo >= hi:
            continue
        candidates = np.flatnonzero(power[lo:hi] > threshold*threshold)
        if not candidates.size:
            continue
        # Moving-energy window is centered; subtract half its length.
        onset = max(0, lo + int(candidates[0]) - smooth_count//2)
        arrivals.append({"click": k, "start_frame": int(onset),
                         "command_monotonic_s": float(stamp)})
    return ensure_detected(arrivals)


def generated_duplex_reference(rate, from_latency):
    """40 low-level click pulses with scheduled indices in a single sample axis."""
    first = rate // 4
    starts = [first + int(round(k * INTERVAL_S * rate)) for k in range(REPEATS)]
    wave = np.zeros((starts[-1] + int(.5*rate), 2), dtype=np.float32)
    click, _ = from_latency.envelope_template(rate)
    for start in starts:
        wave[start:start+len(click), 0] += click.astype(np.float32)
        wave[start:start+len(click), 1] -= click.astype(np.float32) * .8
    return wave, starts


def duplex_harness(args, rate, block, latency):
    """Owner-gated PortAudio full-duplex stream (not two independent clocks)."""
    if (getattr(args, "dry_run", False) or not getattr(args, "confirm_audio", False)
            or not getattr(args, "harness_output_device", None)
            or not getattr(args, "input_device", None)
            or not getattr(args, "device", None)):
        raise PermissionError("duplex harness requires --confirm-audio and all selected device IDs")
    import sounddevice as sd  # physical backend only after the guard
    wave, starts = generated_duplex_reference(rate, latency)
    done = threading.Event()
    received, statuses = [], []
    position = 0

    def callback(indata, outdata, frames, time_info, status):
        nonlocal position
        if status:
            statuses.append(str(status))
        low, high = position, position + frames
        outdata.fill(0)
        if low < len(wave):
            copy_frames = min(frames, len(wave) - low)
            outdata[:copy_frames] = wave[low:low+copy_frames]
        received.append(indata.copy())
        position = high
        if high >= len(wave):
            done.set()

    def portaudio_id(text):
        return int(text) if str(text).isdecimal() else text

    with sd.Stream(samplerate=rate, blocksize=block, channels=(2, 2),
                   dtype="float32",
                   device=(portaudio_id(args.input_device),
                           portaudio_id(args.harness_output_device)),
                   callback=callback):
        if not done.wait(timeout=REPEATS * INTERVAL_S + 12):
            raise RuntimeError("duplex callback did not complete all harness pulses")
    if statuses:
        raise RuntimeError("duplex stream callback status: " + statuses[0])
    audio = np.concatenate(received, axis=0)[:len(wave)]
    # The original quadrature matched filter works with arbitrary cable phase.
    matched = latency.measure(audio, rate, starts[0], phase_known=False)
    records = ensure_detected(matched["arrivals"])
    outputs = [starts[x["click"]] for x in records]
    inputs = [int(x["start_frame"]) for x in records]
    summary_data = harness_loopback_ms(outputs, inputs, rate)
    summary_data.update({"clicks_expected": REPEATS,
                         "clicks_found": len(records),
                         "duplex_capture_buffer_frames": block,
                         "duplex_output_buffer_frames": block,
                         "selected_input_rms_dbfs": matched["rms_dbfs"],
                         "single_stream": True,
                         "recorded_output_sample_indices": outputs,
                         "recorded_input_sample_indices": inputs})
    return summary_data


def command_pulse_patch(rate, block):
    """Command writes gate one fixed 1 kHz audio path; no independent clock."""
    return {
        "format": "wirescape.native.patch", "version": 2,
        "settings": {"sample_rate": rate, "max_block_frames": block,
                     "max_channels": 16, "seed": 37, "timing_mode": "immediate"},
        "modules": [
            {"id": 3, "module": "essentials.vco", "version": 2,
             "parameters": {"frequency": 1000}},
            {"id": 4, "module": "essentials.vca", "version": 2,
             "parameters": {"gain": 0}},
            {"id": 5, "module": "essentials.output", "version": 2,
             "parameters": {}}],
        "connections": [
            {"kind": "signal", "from": {"module": 3, "port": "audio"},
             "to": {"module": 4, "port": "audio"}},
            {"kind": "signal", "from": {"module": 4, "port": "audio"},
             "to": {"module": 5, "port": "audio"}}],
        "outputs": [{"module": 5, "port": "audio", "bus_channel": c}
                    for c in (0, 1)]
    }


def physical_command_capture(args, block, folder, latency):
    """40 separate actual command writes, each explicitly monotonic-stamped."""
    if (getattr(args, "dry_run", False) or not getattr(args, "confirm_audio", False)
            or not getattr(args, "device", None) or not getattr(args, "input_device", None)):
        raise PermissionError("command capture requires --confirm-audio and both device IDs")
    from types import SimpleNamespace
    from run import Engine, EventLog
    from record import Recorder
    from speaker_check import check_audio_state
    import soundfile as sf

    config = SimpleNamespace(dry_run=False, engine=args.engine, rate=args.rate,
                             block=block, device=args.device, confirm_midi=False)
    log = EventLog(folder / "events.ndjson")
    engine = recorder = None
    try:
        engine = Engine(config, folder, log)
        engine.start()
        state = check_audio_state(engine, config, log)
        rate = int(state.get("sampleRate", 0))
        actual_block = int(state.get("bufferFrames", 0))
        if rate != args.rate or actual_block != block:
            raise RuntimeError("engine reported rate/buffer differ from requested")
        engine.send({"type":"loadGraph", "patch":command_pulse_patch(rate, block)})
        input_id = int(args.input_device) if args.input_device.isdecimal() else args.input_device
        recorder = Recorder("input", folder, rate, input_device=input_id,
                            capture_buffer_frames=block)
        recorder.start()
        # Intentional safety gap, not part of any latency calculation.
        time.sleep(.35)
        stamps = []
        base = time.monotonic()
        try:
            for k in range(REPEATS):
                due = base + k * INTERVAL_S
                remaining = due - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
                def record_write(stamp):
                    stamps.append(float(stamp))
                engine.send({"type":"setParam", "moduleId":4,"paramId":"gain",
                             "value":.20}, on_write=record_write)
                time.sleep(.022)
                engine.send({"type":"setParam", "moduleId":4,"paramId":"gain",
                             "value":0})
        finally:
            try:
                engine.send({"type":"setParam", "moduleId":4,"paramId":"gain",
                             "value":0}, timeout=3)
            except Exception:
                pass
        time.sleep(.40)
        capture_path = recorder.stop()
        recorded_blocks = list(recorder.timing_blocks)
        if recorder.overruns:
            raise RuntimeError("input callback lost capture buffers")
        with sf.SoundFile(str(capture_path)) as stream:
            if stream.samplerate != rate or stream.channels != 2:
                raise RuntimeError("captured format does not match engine")
            audio = stream.read(dtype="float32",always_2d=True)
        if len(stamps) != REPEATS:
            raise RuntimeError("missing exact engine command-write timestamps")
        if not recorded_blocks:
            raise RuntimeError("missing recorder callback timing metadata")
        arrivals = find_command_onsets(audio, rate, stamps, recorded_blocks)
        selected = [stamps[a["click"]] for a in arrivals]
        observed = [a["start_frame"] for a in arrivals]
        result = command_to_capture_ms(selected, observed, recorded_blocks, rate)
        result.update({
            "clicks_expected": REPEATS, "clicks_found": len(arrivals),
            "input_capture_buffer_frames": block, "engine_output_buffer_frames": actual_block,
            "input_rms_dbfs": 20*math.log10(max(float(np.sqrt(np.mean(audio*audio))), 1e-15)),
            "capture_file": capture_path.name,
            "onset_indices": observed,
            "command_write_monotonic_s": selected,
            "engine_audio_state": {"rate_hz":rate,"buffer_frames":actual_block,
                                   "state":state.get("state")},
        })
        return result
    finally:
        if recorder and recorder.started is not None:
            recorder.stop()
        if engine:
            try:
                if engine.process and engine.process.poll() is None:
                    engine.send({"type":"setParam", "moduleId":4,
                                 "paramId":"gain", "value":0}, timeout=3)
            except Exception:
                pass
            engine.stop()
        log.close()


def synthetic_quantities(rate, block, latency):
    """No device/time sampling. Two independent generated sample sequences."""
    audio, first, delay = latency.synthetic_capture(rate, block, noise=.0015)
    observed = latency.measure(audio, rate, first, phase_known=True)
    arrivals = ensure_detected(observed["arrivals"])
    output = [first + k * round(rate * INTERVAL_S) for k in range(REPEATS)]
    input_samples = [int(row["start_frame"]) for row in arrivals]
    harness = harness_loopback_ms(
        [output[row["click"]] for row in arrivals], input_samples, rate)
    # Synthetic command writes and ADC sample times share an invented discrete
    # sample axis. These are *not* measurements of host/PortAudio clocks.
    epoch = 100.0
    writes = [epoch + output[row["click"]]/rate for row in arrivals]
    blocks = []
    capture_len = len(audio)
    for i in range(0, capture_len, block):
        count = min(block, capture_len - i)
        blocks.append({"start_frame":i, "frames":count,
                       "adc_monotonic_s":epoch+i/rate,
                       "callback_monotonic_s":epoch+(i+count)/rate})
    capture = command_to_capture_ms(writes, input_samples, blocks, rate)
    capture["clicks_expected"] = REPEATS
    capture["clicks_found"] = len(arrivals)
    capture["input_capture_buffer_frames"] = block
    sound = command_to_sound_ms(capture, harness)
    return harness,capture,sound,delay,observed


def run_one(args, block, sha, date, latency):
    base = args.results / args.machine / f"{date}-{sha[:7]}-latency-{block}"
    folder = base
    index = 1
    while folder.exists():
        folder = Path(f"{base}-{index}")
        index += 1
    folder.mkdir(parents=True)
    details = {
        "SPDX-License-Identifier":"GPL-3.0-only",
        "schema":3, "kind":"M0-r2-three-quantity-latency",
        "machine":args.machine, "date_et":date, "commit":sha,
        "dry_run":args.dry_run, "rate_hz":args.rate,
        "buffer_frames":block, "device_class":args.device_class if not args.dry_run else "synthetic",
        "clicks_expected":REPEATS, "click_peak_dbfs":20*math.log10(.20),
        "completed":False, "owner_physical_measurement":False,
        "historical_limitation":"Prior command/ack midpoint offset is not calibrated output-to-input latency; no such offset is treated as harness_loopback_ms"
    }
    try:
        if args.dry_run:
            harness,capture,sound,delay,old = synthetic_quantities(args.rate,block,latency)
            details["synthetic_delay_frames"] = delay
            # Preserve previously tested synthetic matched-filter assertions.
            details["measurement"] = {
                **old,"quantity":"synthetic_known_sample_delay",
                "calibrated_round_trip":False,
            }
            details["historical_kind"] = "uncalibrated-command-to-adc-diagnostic"
        else:
            harness = duplex_harness(args,args.rate,block,latency)
            capture = physical_command_capture(args,block,folder,latency)
            sound = command_to_sound_ms(capture,harness)
            details["owner_physical_measurement"] = True
        details["harness_loopback_ms"] = harness
        details["command_to_capture_ms"] = capture
        details["command_to_sound_ms"] = sound
        details["measured_rate_hz"] = args.rate
        details["engine_output_buffer_frames"] = capture["engine_output_buffer_frames"] if not args.dry_run else block
        details["harness_duplex_output_buffer_frames"] = block
        details["harness_duplex_capture_buffer_frames"] = block
        details["command_capture_buffer_frames"] = capture["input_capture_buffer_frames"]
        details["completed"] = True
    except (RuntimeError, ValueError, OSError, ImportError, TimeoutError) as exc:
        details["error"] = str(exc)
    finally:
        (folder/"latency.json").write_text(
            json.dumps(details,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        concise = {k:v for k,v in details.items() if k not in ("measurement",)}
        (folder/"manifest.json").write_text(
            json.dumps(concise,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        lines=["<!-- SPDX-License-Identifier: GPL-3.0-only -->",
               "# M0 R1: three separate latency quantities", "",
               f"Mode: {'synthetic only — no devices' if args.dry_run else 'owner-gated physical'}",
               f"Status: {'completed' if details['completed'] else 'REFUSED: '+details.get('error','unknown')}",
               f"Rate: {args.rate} Hz, output/capture buffer: {block} frames, device class: {details['device_class']}",
               f"Repetitions requested: {REPEATS}; >=20 observations required", ""]
        if details["completed"]:
            for name in ("harness_loopback_ms", "command_to_capture_ms"):
                data=details[name]
                s=data["statistics"]
                lines.append(f"{name}: median {s['median']:.3f} ms, p95 {s['p95']:.3f} ms (n={s['repeats']})")
            for quantile,limits in details["command_to_sound_ms"]["range_ms"].items():
                lines.append(f"command_to_sound_ms {quantile}: [{limits['lower_ms']:.3f}, {limits['upper_ms']:.3f}] ms (range only)")
            fallback=details["command_to_capture_ms"]["additional_capture_buffer_uncertainty_ms"]["max"]
            lines += [
                f"Missing-ADC callback fallback additional uncertainty: up to {fallback:.3f} ms (one capture buffer)",
                "Absolute host-to-PortAudio clock-mapping uncertainty: unavailable; callback scheduling offset uncalibrated.",
                "No separately measured DAC presentation timestamp; the sound range is the contract-defined arithmetic.",
            ]
        lines += ["", "Owner physical measurements remain unverified until an owner runs the cable probe.",
                  "Do not interpret old run=1 command/ack midpoint values as a DAC-to-ADC round trip."]
        (folder/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(folder/"report.md")
    return bool(details["completed"])
