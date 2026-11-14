# SPDX-License-Identifier: GPL-3.0-only
"""Device-free diagnostics for owner-recorded cross-tool audio.

Spectral non-harmonic floor is an alias *proxy*, not an isolated alias
measurement. Harmonic distortion is not comparable without matched levels,
waveforms, window and DSP settings.
"""
import math
from pathlib import Path


def _numpy():
    import numpy as np
    return np


def clicks(samples, rate, threshold=.18):
    """High-passed sample-difference outliers; times in seconds."""
    import numpy as np
    from scipy.ndimage import uniform_filter1d
    x = np.asarray(samples, dtype=float)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if x.size < 5 or not np.isfinite(x).all():
        return []
    delta = np.diff(x)
    high = delta - uniform_filter1d(delta, size=max(5, int(rate * .003)),
                                    mode="nearest")
    median = float(np.median(high))
    mad = float(np.median(np.abs(high - median)))
    cut = max(threshold, 14 * 1.4826 * mad)
    indexes = np.flatnonzero(abs(high) > cut) + 1
    times = []
    last = -rate
    for index in indexes:
        if index - last >= max(2, int(rate * .002)):
            times.append(round(float(index) / rate, 6))
        last = index
    return times


def stats(signal):
    np = _numpy()
    x = np.asarray(signal, dtype="float64")
    if not x.size:
        return {"rms": 0., "peak": 0., "dc": 0.}
    if not np.isfinite(x).all():
        raise ValueError("non-finite recorded signal")
    return {"rms": round(float(np.sqrt(np.mean(x * x))), 9),
            "peak": round(float(np.max(np.abs(x))), 9),
            "dc": round(float(np.mean(x)), 9)}


def analyse_recording(path, gate_times=None):
    import soundfile as sf
    np = _numpy()
    with sf.SoundFile(str(path)) as f:
        rate, channels = f.samplerate, f.channels
        if channels not in (1, 2):
            raise ValueError("expected mono or stereo recording")
        # Bound diagnostics memory (one minute at 48 kHz stereo float64).
        max_frames = rate * 65
        data = f.read(max_frames, dtype="float32", always_2d=True)
        clipped = len(f) > max_frames
    mono = np.mean(data, axis=1)
    click_times = clicks(mono, rate)
    result = {"sample_rate_hz": rate, "channels": channels,
              "analysed_seconds": round(len(data) / rate, 4),
              "truncated_at_65_seconds": clipped,
              "overall": stats(data), "click_times_s": click_times[:1000],
              "click_count": len(click_times)}
    if gate_times:
        result["gate_edge_clicks"] = {
            str(g): [t for t in click_times if abs(t - g) <= .01] for g in gate_times}
    return result


def tone_metrics(samples, rate, frequency):
    """Steady-state Hann/FFT THD and non-harmonic-floor alias proxy."""
    np = _numpy()
    from scipy.signal import get_window
    x = np.asarray(samples, dtype=float)
    if x.ndim == 2:
        x = np.mean(x, axis=1)
    if rate < 2 * frequency or frequency <= 0:
        raise ValueError("tone frequency exceeds Nyquist")
    if len(x) < round(.5 * rate):
        raise ValueError("tone probe needs at least half a second of audio")
    # Ignore entry/exit transients and take at most one central second.
    width = min(rate, len(x) // 2)
    start = (len(x) - width) // 2
    block = x[start:start + width]
    window = get_window("hann", width, fftbins=True)
    spectrum = np.abs(np.fft.rfft((block - np.mean(block)) * window))
    freqs = np.fft.rfftfreq(width, 1. / rate)
    resolution = rate / width
    span = max(2, round(3. * frequency / max(frequency, resolution)))  # +/- 3 bins
    covered = np.zeros(len(spectrum), dtype=bool)

    def component(hz):
        center = int(round(hz / resolution))
        lo = max(1, center - span)
        hi = min(len(spectrum), center + span + 1)
        covered[lo:hi] = True
        return float(np.sqrt(np.sum(spectrum[lo:hi] ** 2)))

    fundamental = component(frequency)
    harmonics = [component(frequency * harmonic)
                 for harmonic in range(2, int((rate / 2) // frequency) + 1)]
    # DC and the lowest 2 FFT bins are not counted toward non-harmonic floor.
    covered[:3] = True
    residual = float(np.sqrt(np.sum(spectrum[~covered] ** 2)))
    ratio = lambda x: 20. * math.log10(max(x, 1e-15) / max(fundamental, 1e-15))
    return {"frequency_hz": frequency,
            "thd_percent": round(100 * math.sqrt(sum(x*x for x in harmonics)) /
                                 max(fundamental, 1e-15), 5),
            "nonharmonic_floor_db_relative": round(ratio(residual), 4),
            "fundamental_fft_amplitude": round(fundamental / max(np.sum(window) / 2, 1), 8),
            "window": "hann_centered_1s_max", "fft_resolution_hz": round(resolution, 6),
            "alias": "proxy_only_not_identified"}


def _read_probe(path):
    import soundfile as sf
    with sf.SoundFile(str(path)) as f:
        if len(f) > f.samplerate * 65:
            raise ValueError("probe recording longer than 65 seconds")
        return f.read(dtype="float32", always_2d=True), f.samplerate


def analyse_probes(tone_files, filter_files):
    """Frequency-keyed recordings, with file basename only in the result."""
    import numpy as np
    tones, filters = {}, {}
    for hz, path in tone_files.items():
        data, rate = _read_probe(path)
        tones[hz] = {"recording": Path(path).name,
                     **tone_metrics(data, rate, float(hz)),
                     "dc": stats(data)["dc"],
                     "clicks": clicks(data, rate)[:1000]}
    amplitudes = {}
    for hz, path in filter_files.items():
        data, rate = _read_probe(path)
        value = tone_metrics(data, rate, float(hz))
        amplitudes[hz] = value["fundamental_fft_amplitude"]
        filters[hz] = {"recording": Path(path).name, "amplitude": amplitudes[hz]}
    if amplitudes:
        base = amplitudes.get("110")
        if base is None:
            base = amplitudes[min(amplitudes, key=lambda x: float(x))]
        for hz, item in filters.items():
            item["relative_gain_db"] = round(20 * math.log10(max(item["amplitude"], 1e-15) /
                                                          max(base, 1e-15)), 4)
        # Relative response only; needs equal-amplitude source at each frequency.
    return {"oscillator": tones, "filter_response": filters,
            "filter_reference": "110Hz_if_present_else_lowest_frequency",
            "note": "THD excludes harmonics above Nyquist; floor is a nonharmonic proxy"}
