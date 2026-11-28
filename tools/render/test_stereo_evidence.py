# SPDX-License-Identifier: GPL-3.0-only
"""V2 contract: real renderer, frozen legacy rows, independent stereo negatives."""
import argparse
import json
import math
from pathlib import Path
import struct
import sys
import tempfile

import evidence

# Frozen v1 measurement oracle from 137e0b05bce2373a68c95e95d29ae2f4eab37d95.
# Keep constants independent of implementation changes.
ACTIVE_RMS = 0.01
SILENT_PEAK = 0.0001
FREQUENCY_TOLERANCE = 0.02

def check(condition, message):
    if not condition:
        raise AssertionError(message)

def legacy_measure(samples, case):
    check(samples and all(math.isfinite(x) for x in samples), "non-finite audio")
    peak = max(abs(x) for x in samples)
    check(peak <= case["peak_limit"], "peak bound exceeded")
    results = [{"check": "finite", "passed": True},
               {"check": "peak", "value": peak, "maximum": case["peak_limit"], "unit": "FS"}]
    for window in case["windows"]:
        a, b = window["start"], window["end"]
        check(0 <= a < b <= len(samples), "invalid window bounds")
        region = samples[a:b]
        if window["kind"] == "active":
            rms = math.sqrt(sum(x * x for x in region) / len(region))
            check(rms > ACTIVE_RMS, f"active window {a}:{b} silent ({rms:.6g} RMS)")
            results.append({"check": "active", "start_frame": a, "end_frame": b, "rms_fs": rms,
                            "minimum_rms_fs": ACTIVE_RMS})
        elif window["kind"] == "silent":
            value = max(abs(x) for x in region)
            check(value < SILENT_PEAK, f"silent window {a}:{b} active ({value:.6g} peak)")
            results.append({"check": "silent", "start_frame": a, "end_frame": b, "peak_fs": value,
                            "maximum_peak_fs": SILENT_PEAK})
        else:
            raise ValueError("unknown window check")
    for window in case["frequencies"]:
        a, b, want = window["start"], window["end"], window["hz"]
        check(0 <= a < b <= len(samples) and want > 0, "invalid frequency window")
        region = samples[a:b]
        crossings = sum((x < 0 <= y) or (x >= 0 > y) for x, y in zip(region, region[1:]))
        observed = crossings * case["rate"] / (2 * (len(region) - 1))
        check(abs(observed / want - 1) <= FREQUENCY_TOLERANCE,
              f"frequency window {a}:{b}: {observed:.3f} Hz, expected {want} Hz")
        results.append({"check": "zero_crossing", "start_frame": a, "end_frame": b,
                        "measured_hz": observed, "expected_hz": want,
                        "tolerance_fraction": FREQUENCY_TOLERANCE})
    return results


def invoke(renderer, case_path, out):
    rc = evidence.run(argparse.Namespace(case=str(case_path), out=str(out),
        render=str(renderer), block=None, compiler="test", configuration="test",
        negative_late=False))
    return rc, json.loads((out / "measurements.json").read_text())


def main(renderer):
    cases = Path(__file__).resolve().parent / "cases"
    with tempfile.TemporaryDirectory(prefix="render-stereo-") as tmp:
        root = Path(tmp)
        # Every pre-V2 case retains its exact assertion rows, including order.
        for name in ("adsr-notes", "blend-selection", "frequency-step"):
            path = cases / (name + ".json")
            case = json.loads(path.read_text())
            out = root / name
            rc, info = invoke(renderer, path, out)
            check(rc == 0, name)
            data = (out / "audio.wav").read_bytes()
            channels = list(struct.iter_unpack("<ff", data[44:]))
            check(max(abs(l - r) for l, r in channels) < 1e-5, "legacy mirror")
            want = legacy_measure([l for l, _ in channels], case)
            check(json.dumps(info["assertions"], sort_keys=True) ==
                  json.dumps(want, sort_keys=True), "legacy assertion rows changed: " + name)
        path = cases / "independent-stereo.json"
        case = json.loads(path.read_text())
        rc, info = invoke(renderer, path, root / "independent")
        check(rc == 0, "independent case did not pass: " + str(info.get("error")))
        rows = info["assertions"]
        check({r["channel"] for r in rows if r["check"] == "active"} == {0, 1},
              "active rows must cover both channels")
        check({(r["channel"], r["expected_hz"]) for r in rows
               if r["check"] == "zero_crossing"} == {(0, 220), (1, 440)}, "frequency rows")
        check({r["channel"] for r in rows if r["check"] == "peak"} == {0, 1}, "peak rows")
        report = (root / "independent" / "report.md").read_text()
        check("channel 0" in report and "channel 1" in report, "report channel labels")

        def variant(name, obj, expected):
            path = root / (name + ".json")
            path.write_text(json.dumps(obj))
            rc, info = invoke(renderer, path, root / name)
            check(rc != 0 and expected in info.get("error", ""),
                  name + ": " + str(info))

        variant("mirrored", dict(case, stereo="mirrored"), "stereo bus mismatch")
        variant("bad-mode", dict(case, stereo="bogus"), "stereo")
        for value in (-1, 2, True, 0.0, "0", None):
            variant("bad-channel-" + str(value), dict(case, windows=[
                {"kind": "active", "start": 100, "end": 300, "channel": value}]), "channel")
        # Use an actual one-sided render: remove left bus mapping.
        one = json.loads(json.dumps(case))
        one["patch"]["outputs"] = [one["patch"]["outputs"][1]]
        one["frequencies"] = []
        window = {"kind": "silent", "start": 10000, "end": 80000}
        one["windows"] = [dict(window, channel=0)]
        path = root / "left-silent.json"
        path.write_text(json.dumps(one))
        rc, info = invoke(renderer, path, root / "left-silent")
        check(rc == 0, "left silent: " + str(info.get("error")))
        variant("right-not-silent", dict(one, windows=[dict(window, channel=1)]), "silent window")
        variant("both-not-silent", dict(one, windows=[window]), "silent window")
    print("V2 stereo evidence contract PASS")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
