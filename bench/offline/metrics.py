# SPDX-License-Identifier: GPL-3.0-only
"""Numeric measurements for offline float32 stereo evidence."""
import math
import struct

import numpy as np
from scipy import signal

RATE = 48000


def read_audio(path, rate=RATE):
    raw = path.read_bytes()
    if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:16] != b"WAVEfmt " or raw[36:40] != b"data":
        raise ValueError("expected RIFF stereo float32 WAV")
    header = struct.unpack_from("<IHHIIHH", raw, 16)
    if header != (16, 3, 2, rate, rate * 8, 8, 32):
        raise ValueError("WAV format, sample rate or channel count mismatch")
    size = struct.unpack_from("<I", raw, 40)[0]
    if size != len(raw) - 44 or size % 8:
        raise ValueError("WAV data length mismatch")
    return np.frombuffer(raw, dtype="<f4", offset=44).reshape(-1, 2).astype(np.float64)


def basic(audio):
    if not audio.size:
        raise ValueError("zero-length audio")
    finite = np.isfinite(audio)
    if not np.all(finite):
        return {"finite_samples": int(np.count_nonzero(finite)),
                "nonfinite_samples": int(finite.size - np.count_nonzero(finite))}
    return {"finite_samples": int(finite.size), "nonfinite_samples": 0,
            "peak_fs": float(np.max(np.abs(audio))),
            "rms_fs": float(np.sqrt(np.mean(np.square(audio)))),
            "dc_fs": float(np.mean(audio))}


def click_events(audio, rate=RATE, *, ratio_threshold=3.0):
    """Broadband transient detector: 1 ms high-pass energy / adjacent 50 ms.

    The surrounding reference excludes the transient window and its nearest
    2 ms on either side. Recurrent saw resets raise the local reference rather
    than yielding thousands of unqualified derivative outliers. Each clustered
    event records a timestamp and a signed-level-independent size estimate.
    """
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 2:
        x = np.mean(x, axis=1)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("click detector requires finite mono or stereo audio")
    window = max(8, int(round(rate * .001)))
    windows = len(x) // window
    if windows < 60:
        return []
    sos = signal.butter(3, min(2000, rate * .2), btype="highpass",
                        fs=rate, output="sos")
    filtered = signal.sosfiltfilt(sos, x)
    blocks = filtered[:windows * window].reshape(windows, window)
    energy = np.mean(blocks ** 2, axis=1)
    sums = np.r_[0., np.cumsum(energy)]
    index = np.arange(windows)
    left, right = np.maximum(0, index - 25), np.minimum(windows, index + 26)
    near_left = np.maximum(left, index - 2)
    near_right = np.minimum(right, index + 3)
    count = (near_left - left) + (right - near_right)
    reference = ((sums[near_left] - sums[left]) +
                 (sums[right] - sums[near_right])) / np.maximum(count, 1)
    ratio = np.sqrt(energy / np.maximum(reference, 1e-15))
    valid = ((index >= 25) & (index < windows - 25) &
             (ratio >= ratio_threshold) & (np.sqrt(energy) >= .002))
    candidates = np.flatnonzero(valid)
    events = []
    for i in candidates:
        center = int(i * window)
        before = x[center - 20 * window:center]
        after = x[center + window:center + 21 * window]
        if not len(before) or not len(after):
            continue
        size = float(abs(np.mean(after) - np.mean(before)))
        if size < .015:
            continue
        event = {"time_s": float((i + .5) * window / rate),
                 "size_fs": size, "highpass_energy_ratio": float(ratio[i])}
        if events and i - events[-1][0] <= 3:
            if event["highpass_energy_ratio"] > events[-1][1]["highpass_energy_ratio"]:
                events[-1] = (int(i), event)
        else:
            events.append((int(i), event))
    return [event for _, event in events]


def patch_metrics(audio, rate=RATE):
    values = basic(audio)
    if values["nonfinite_samples"]:
        return values
    mono = np.mean(audio, axis=1)
    events = click_events(mono, rate)
    windows = max(1, round(rate * .02))
    n = len(mono) // windows
    powers = np.mean(mono[:n * windows].reshape(n, windows) ** 2, axis=1) if n else np.array([])
    quiet = powers < 1e-10
    runs, length = 0, 0
    for silent in quiet:
        if silent:
            if not length:
                runs += 1
            length += 1
        else:
            length = 0
    values.update(click_count=len(events), click_events=events,
                  click_window_ms=1, click_reference_ms=50,
                  click_highpass_hz=min(2000, rate * .2),
                  click_energy_ratio_threshold=3.0,
                  silence_segments=runs, silence_window_ms=20,
                  silence_rms_floor_fs=1e-5)
    return values


def oscillator_metrics(audio, target_hz, rate=RATE):
    base = basic(audio)
    if base["nonfinite_samples"]:
        return base
    x = np.asarray(audio[:, 0], dtype=np.float64)
    x = x[len(x) // 5:]
    if len(x) < 256 or np.max(np.abs(x)) == 0:
        return dict(base, observed_hz=None, pitch_cents=None, thd_db=None, alias_floor_dbfs=None)
    taper = np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x * taper))
    hz = np.fft.rfftfreq(len(x), 1.0 / rate)
    width = rate / len(x)
    near = (hz >= max(1, target_hz * 0.8)) & (hz <= min(rate * .49, target_hz * 1.2))
    candidates = np.flatnonzero(near)
    peak = int(candidates[np.argmax(spec[candidates])]) if candidates.size else int(np.argmax(spec[1:]) + 1)
    if 1 <= peak < len(spec) - 1:
        a, b, c = np.log(np.maximum(spec[peak - 1:peak + 2], 1e-30))
        denom = a - 2 * b + c
        delta = .5 * (a - c) / denom if abs(denom) > 1e-12 else 0.0
    else:
        delta = 0.0
    observed = (peak + float(np.clip(delta, -.5, .5))) * width
    power = (spec / max(np.sum(taper), 1)) ** 2 * 2
    harmonic = np.zeros(len(power), dtype=bool)
    component = []
    for k in range(1, int((rate / 2) / target_hz) + 1):
        center = int(round(k * target_hz / width))
        lo, hi = max(1, center - 4), min(len(power), center + 5)
        if lo >= hi:
            continue
        harmonic[lo:hi] = True
        component.append(float(np.sum(power[lo:hi])))
    residual = max(0.0, float(np.sum(power[1:][~harmonic[1:]])))
    thd = (10 * math.log10(max(sum(component[1:]), 1e-30) /
                           max(component[0], 1e-30))) if component else None
    return dict(base, observed_hz=observed,
                pitch_cents=1200 * math.log2(observed / target_hz) if observed > 0 else None,
                thd_db=thd, alias_floor_dbfs=10 * math.log10(max(residual, 1e-30)),
                harmonic_bins_half_width=4)


def filter_metrics(dry, wet, rate=RATE):
    if not np.isfinite(dry).all() or not np.isfinite(wet).all():
        return {"nonfinite_samples": int(np.size(wet) - np.count_nonzero(np.isfinite(wet)))}
    nperseg = min(4096, len(dry), len(wet))
    if nperseg < 64:
        return {"frequency_hz": [], "magnitude_db": []}
    f, p0 = signal.welch(dry[:, 0], rate, nperseg=nperseg)
    _, p1 = signal.welch(wet[:, 0], rate, nperseg=nperseg)
    db = 10 * np.log10(np.maximum(p1, 1e-30) / np.maximum(p0, 1e-30))
    samples = {f"gain_{hz}_hz_db": float(db[np.argmin(np.abs(f - hz))])
               for hz in (100, 1000, 5000)}
    return {"frequency_hz": [float(v) for v in f],
            "magnitude_db": [float(v) for v in db],
            "nperseg": nperseg, **samples}


def step_metrics(audio, step_frame, rate=RATE):
    base = basic(audio)
    if base["nonfinite_samples"]:
        return base
    sos = signal.butter(2, 2000, btype="highpass", fs=rate, output="sos")
    mono = np.mean(audio, axis=1)
    filtered = signal.sosfilt(sos, mono)
    half = min(int(.025 * rate), step_frame, len(filtered) - step_frame)
    if half < 2:
        return {"highpass_peak_fs": None, "highpass_rms_fs": None}
    region = filtered[step_frame - half:step_frame + half]
    return {"highpass_peak_fs": float(np.max(np.abs(region))),
            "highpass_rms_fs": float(np.sqrt(np.mean(region ** 2))),
            "window_ms": 2000 * half / rate, "highpass_hz": 2000}


def envelope_metrics(audio, on_frame, off_frame, attack_s, release_s, rate=RATE):
    if not np.isfinite(audio).all():
        return {"nonfinite_samples": int(audio.size - np.count_nonzero(np.isfinite(audio)))}
    x = audio[:, 0]
    smooth = np.convolve(np.abs(signal.hilbert(x)),
                         np.ones(128, dtype=float) / 128, mode="same")
    high = float(np.median(smooth[max(on_frame, off_frame - rate // 5):off_frame]))
    if high <= 1e-8:
        return {"attack_measured_s": None, "release_measured_s": None}
    rise = np.flatnonzero(smooth[on_frame:off_frame] >= high * .9)
    fall = np.flatnonzero(smooth[off_frame:] <= high * .1)
    measured_attack = float(rise[0] / rate) if rise.size else None
    measured_release = float(fall[0] / rate) if fall.size else None
    return {"attack_set_s": attack_s, "release_set_s": release_s,
            "attack_measured_s": measured_attack, "release_measured_s": measured_release,
            "attack_error_ms": (measured_attack - attack_s) * 1000 if measured_attack is not None else None,
            "release_error_ms": (measured_release - release_s) * 1000 if measured_release is not None else None,
            "level_reference_fs": high}


def direct_envelope_metrics(audio, on_frame, off_frame, rise_s, fall_s, rate=RATE):
    """Time to 99% of held peak and 1% of release from direct envelope CV."""
    if not np.isfinite(audio).all():
        return {"nonfinite_samples": int(audio.size - np.count_nonzero(np.isfinite(audio)))}
    x = audio[:, 0]
    if not (0 <= on_frame < off_frame < len(x)):
        return {"rise_measured_s": None, "fall_measured_s": None}
    high = max(float(np.max(x[on_frame:off_frame])), 0.0)
    if high < 1e-8:
        return {"rise_measured_s": None, "fall_measured_s": None}
    rise = np.flatnonzero(x[on_frame:off_frame] >= .99 * high)
    fall = np.flatnonzero(x[off_frame:] <= .01 * high)
    measured_rise = float(rise[0] / rate) if rise.size else None
    measured_fall = float(fall[0] / rate) if fall.size else None
    return {"rise_set_s": rise_s, "fall_set_s": fall_s,
            "rise_measured_s": measured_rise, "fall_measured_s": measured_fall,
            "rise_error_ms": (measured_rise - rise_s) * 1000 if measured_rise is not None else None,
            "fall_error_ms": (measured_fall - fall_s) * 1000 if measured_fall is not None else None,
            "reference_peak_fs": high, "rise_fraction": .99, "fall_fraction": .01}
