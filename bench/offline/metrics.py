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



def folded_alias_frequencies(fundamental_hz, rate=RATE, *, max_harmonic=None):
    """Aliased harmonic centers strictly above Nyquist, excluding true harmonics."""
    if not (0 < fundamental_hz < rate * .5):
        raise ValueError("fundamental must lie between DC and Nyquist")
    limit = max_harmonic or min(4096, int(2 * rate / fundamental_hz))
    base = int(math.floor((rate * .5) / fundamental_hz)) + 1
    true_harmonics = np.arange(1, base, dtype=float) * fundamental_hz
    aliases = []
    for order in range(base, limit + 1):
        folded = abs((order * fundamental_hz + rate * .5) % rate - rate * .5)
        if folded <= 0 or folded >= rate * .5:
            continue
        if true_harmonics.size and np.min(abs(true_harmonics - folded)) < 1e-6:
            continue
        aliases.append(float(folded))
    return sorted(set(round(hz, 6) for hz in aliases))


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
    # Count energy only in predicted folded-harmonic bins that are not already
    # occupied by the true below-Nyquist harmonics.
    alias_bins = np.zeros(len(power), dtype=bool)
    for predicted in folded_alias_frequencies(target_hz, rate):
        center = int(round(predicted / width))
        if 1 <= center < len(power):
            alias_bins[max(1, center - 4):min(len(power), center + 5)] = True
    alias_bins &= ~harmonic
    aliased = max(0.0, float(np.sum(power[alias_bins])))
    thd = (10 * math.log10(max(sum(component[1:]), 1e-30) /
                           max(component[0], 1e-30))) if component else None
    return dict(base, observed_hz=observed,
                pitch_cents=1200 * math.log2(observed / target_hz) if observed > 0 else None,
                thd_db=thd, alias_floor_dbfs=10 * math.log10(max(aliased, 1e-30)),
                nonharmonic_floor_dbfs=10 * math.log10(max(residual, 1e-30)),
                alias_expected_bin_count=int(np.count_nonzero(alias_bins)),
                harmonic_bins_half_width=4)


def parabolic_peak_hz(frequency, magnitude, index):
    """Three-bin vertex on an equally spaced frequency grid."""
    if not 0 < index < len(magnitude) - 1:
        return float(frequency[index])
    left, center, right = map(float, magnitude[index - 1:index + 2])
    denominator = left - 2 * center + right
    offset = .5 * (left - right) / denominator if abs(denominator) > 1e-12 else 0.
    return float(frequency[index] + np.clip(offset, -.5, .5) *
                 (frequency[index + 1] - frequency[index]))


def parabolic_crossing_hz(frequency, magnitude_db, reference_db, nominal_hz):
    """Choose descending -3 dB crossing nearest nominal; quadratic interpolation."""
    goal = reference_db - 10 * math.log10(2)
    valid = ((magnitude_db[:-1] >= goal) & (magnitude_db[1:] < goal) &
             (frequency[:-1] > 0))
    crossings = np.flatnonzero(valid)
    if not len(crossings):
        return None
    index = int(crossings[np.argmin(abs(frequency[crossings] - nominal_hz))])
    lo, hi = float(frequency[index]), float(frequency[index + 1])
    slope = float(magnitude_db[index + 1] - magnitude_db[index])
    linear = (lo + (goal - magnitude_db[index]) * (hi - lo) / slope
              if abs(slope) > 1e-12 else .5 * (lo + hi))
    if 0 < index < len(frequency) - 2:
        # Three points around the crossing constrain a parabola, whose root
        # must lie in the physically observed bracket or we use linear.
        xs = np.asarray(frequency[index - 1:index + 2], dtype=float)
        ys = np.asarray(magnitude_db[index - 1:index + 2], dtype=float)
        coeff = np.polyfit(xs - lo, ys - goal, 2)
        roots = np.roots(coeff)
        valid_roots = [lo + float(root.real) for root in roots
                       if abs(root.imag) < 1e-8 and 0 <= root.real <= hi - lo]
        if valid_roots:
            return min(valid_roots, key=lambda x: abs(x - linear))
    return float(linear)


def filter_metrics(dry, wet, rate=RATE, cutoff_hz=None, resonance=None, output_tap=None):
    if not np.isfinite(dry).all() or not np.isfinite(wet).all():
        return {"nonfinite_samples": int(np.size(wet) - np.count_nonzero(np.isfinite(wet)))}
    nperseg = min(4096, len(dry), len(wet))
    if nperseg < 64:
        return {"frequency_hz": [], "magnitude_db": [], "reason": "fewer than 64 frames"}
    f, p0 = signal.welch(dry[:, 0], rate, nperseg=nperseg)
    _, p1 = signal.welch(wet[:, 0], rate, nperseg=nperseg)
    db = 10 * np.log10(np.maximum(p1, 1e-30) / np.maximum(p0, 1e-30))
    samples = {f"gain_{hz}_hz_db": float(db[np.argmin(np.abs(f - hz))])
               for hz in (100, 1000, 5000)}
    record = {"frequency_hz": [float(v) for v in f],
              "magnitude_db": [float(v) for v in db],
              "nperseg": nperseg, "output_tap": output_tap, **samples}
    if cutoff_hz is not None:
        low = (f >= max(f[1], .08 * cutoff_hz)) & (f < max(f[2], .3 * cutoff_hz))
        reference_db = float(np.median(db[low])) if np.any(low) else float(db[1])
        crossing = parabolic_crossing_hz(f, db, reference_db, cutoff_hz)
        record.update(cutoff_reference_db=reference_db, cutoff_3db_hz=crossing,
                      cutoff_error_hz=(crossing - cutoff_hz) if crossing is not None else None,
                      cutoff_error_reason=None if crossing is not None
                      else "no descending 3 dB crossing in measured frequency range")
        if resonance and resonance > 0:
            focus = np.flatnonzero((f >= .25 * cutoff_hz) &
                                   (f <= min(.49 * rate, 3 * cutoff_hz)))
            if len(focus):
                peak = int(focus[np.argmax(db[focus])])
                observed = parabolic_peak_hz(f, db, peak)
                record.update(resonance_peak_hz=observed,
                              resonance_peak_error_hz=observed - cutoff_hz,
                              resonance_peak_gain_db=float(db[peak]))
    return record


def self_oscillation_metrics(audio, rate=RATE, impulse_end_s=.001, observe_after_s=2.0):
    """RMS of the post-impulse tail, excluding the initial excitation."""
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 2:
        x = x[:, 0]
    if not np.isfinite(x).all():
        return {"status": "nonfinite", "reason": "nonfinite tail samples"}
    start = int(round(rate * observe_after_s))
    end = int(round(rate * impulse_end_s))
    if len(x) <= start or end >= start:
        return {"status": "insufficient_duration",
                "reason": "render shorter than required post-2-second observation"}
    tail = x[start:]
    return {"status": "measured", "impulse_end_s": impulse_end_s,
            "tail_begin_s": observe_after_s,
            "tail_rms_fs": float(np.sqrt(np.mean(tail * tail))),
            "tail_peak_fs": float(np.max(abs(tail)))}



def sweep_residual_metrics(fast, slow, rate=RATE):
    """Compare high-pass energy of 1 s param sweep to an 8x slower sweep."""
    fast = np.asarray(fast, dtype=np.float64)
    slow = np.asarray(slow, dtype=np.float64)
    if fast.ndim == 2:
        fast = np.mean(fast, axis=1)
    if slow.ndim == 2:
        slow = np.mean(slow, axis=1)
    if len(fast) < rate or len(slow) < 8 * rate:
        raise ValueError("requires >=1-second fast and >=8-second slow sweeps")
    if not np.isfinite(fast).all() or not np.isfinite(slow).all():
        raise ValueError("nonfinite sweep samples")
    sos = signal.butter(2, min(2000, rate * .2), btype="highpass",
                        fs=rate, output="sos")
    # Compare same fraction of each sweep after initial setup transient.
    def residual(x):
        filtered = signal.sosfilt(sos, x)
        cut = max(1, int(round(rate * .025)))
        tail = filtered[cut:]
        return float(np.sqrt(np.mean(tail ** 2)))
    fast_hp, slow_hp = residual(fast), residual(slow)
    return {"fast_highpass_rms_fs": fast_hp, "slow_highpass_rms_fs": slow_hp,
            "fast_to_slow_highpass_ratio": fast_hp / max(slow_hp, 1e-12),
            "fast_to_slow_highpass_db": 20 * math.log10(
                max(fast_hp, 1e-12) / max(slow_hp, 1e-12)),
            "highpass_hz": min(2000, rate * .2),
            "fast_duration_s": len(fast) / rate,
            "slow_duration_s": len(slow) / rate}

def filter_impulse_evidence(audio, rate, excitation_frames):
    """Never label a multi-frame gated pulse as the required exact impulse."""
    measured = self_oscillation_metrics(
        audio, rate, impulse_end_s=excitation_frames / rate)
    result = {"excitation_frames": int(excitation_frames),
              "excitation_shape": ("single_sample_impulse"
                                   if excitation_frames == 1
                                   else "clock_gate_pulse_not_single_sample")}
    if excitation_frames != 1:
        result.update(status="not_exact_impulse",
                      reason="source emitted %d samples, not one" % excitation_frames)
        if measured.get("status") == "measured":
            result["gate_pulse_tail_rms_fs"] = measured["tail_rms_fs"]
            result["gate_pulse_tail_peak_fs"] = measured["tail_peak_fs"]
        else:
            result["gate_pulse_tail_status"] = measured.get("status")
        return result
    result.update(measured)
    return result




def r2_impulse_metrics(capture, rate):
    """R2 after 1 s engine silence: analyze exactly 2 s after one input pulse.

    Time to -60 dB re peak is the first point whose entire remaining
    2-second capture is at or below 0.001 * measured absolute peak.
    This suffix-peak definition does not mistake a sine zero crossing
    for actual decay. A value not reached inside the capture is null.
    """
    samples = np.asarray(capture, dtype=np.float64).reshape(-1)
    if samples.size != 2 * rate:
        raise ValueError("R2 impulse capture must contain exactly two seconds")
    finite = np.isfinite(samples)
    invalid = int(np.count_nonzero(~finite))
    valid = np.abs(samples[finite])
    peak = float(np.max(valid)) if valid.size else None
    result = {
        "capture_frames": int(samples.size), "peak_fs": peak,
        "nan_count": int(np.count_nonzero(np.isnan(samples))),
        "inf_count": int(np.count_nonzero(np.isinf(samples))),
        "nonfinite_samples": invalid,
        "time_to_minus60_db_re_peak_ms": None,
        "decay_status": "not_reached_within_2s",
        "method": "first suffix-maximum abs(sample) <= peak * 1e-3",
    }
    if invalid:
        result["decay_status"] = "nonfinite_response"
        return result
    if peak is None or peak == 0:
        result["decay_status"] = "zero_response"
        return result
    absolute = np.abs(samples)
    threshold = peak * 1e-3
    peak_frame = int(np.argmax(absolute))
    suffix_peak = np.maximum.accumulate(absolute[::-1])[::-1]
    crossings = np.flatnonzero(suffix_peak[peak_frame:] <= threshold)
    if crossings.size:
        result["time_to_minus60_db_re_peak_ms"] = (
            float(peak_frame + crossings[0]) / rate * 1000.0)
        result["decay_status"] = "reached"
    return result


def r2_tail_metrics(repeats):
    """Validate five engine FTZ/DAZ five-second tail timing measurements."""
    if not isinstance(repeats, list) or len(repeats) != 5:
        raise ValueError("R2 requires exactly five tail repeats")
    ratios = []
    subnormals = 0
    nonfinite = 0
    for index, row in enumerate(repeats):
        if row.get("repeat") != index:
            raise ValueError("R2 tail repeat index mismatch")
        active = float(row["active_median_ns"])
        silent = float(row["silent_median_ns"])
        observed = float(row["silent_over_active"])
        if not (np.isfinite(active) and np.isfinite(silent)
                and active > 0 and silent > 0
                and row["active_full_blocks"] > 0
                and row["silent_full_blocks"] > 0
                and np.isclose(observed, silent / active, rtol=2e-6)):
            raise ValueError("R2 invalid block timing or ratio")
        if row["subnormal_output_samples"] < 0 or row["nonfinite_output_samples"] < 0:
            raise ValueError("R2 invalid output category count")
        ratios.append(observed)
        subnormals += row["subnormal_output_samples"]
        nonfinite += row["nonfinite_output_samples"]
    return {
        "repeat_count": 5,
        "median_silent_over_active_block_cost": float(np.median(ratios)),
        "individual_silent_over_active_ratios": [float(x) for x in ratios],
        "subnormal_output_samples_all_repeats": int(subnormals),
        "nonfinite_output_samples_all_repeats": int(nonfinite),
        "method": "median of 5 (silent full-block median ns / active full-block median ns)",
    }


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
