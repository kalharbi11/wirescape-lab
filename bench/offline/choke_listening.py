#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""D5 listening witness: use the identical subject callback fixture on both trees.
VCO is the directly audible oscillator output; ADSR is a control envelope.
No normalisation, windowing, gain change or product-source edits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy import signal

RATE, FRAMES, SWITCH = 48000, 96000, 48000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_source(path, pin):
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("full source SHA required")
    if subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"],
                               text=True).strip() != pin:
        raise ValueError("source mismatch")
    subprocess.run(["git", "-C", str(path), "diff", "--quiet", "HEAD", "--"], check=True)


def extract(source, start, end):
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("unexpected folder-test fixture")
    return source[source.index(start):source.index(end)]


def peak(x):
    sos = signal.butter(2, 2000, btype="highpass", fs=RATE, output="sos")
    hp = signal.sosfilt(sos, x.astype(np.float64))
    return float(20 * np.log10(np.max(np.abs(hp[46800:49200]))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for role in ("base", "subject", "out"):
        p.add_argument("--" + role, type=Path, required=True)
    for role in ("base", "subject"):
        p.add_argument("--" + role + "-pin", required=True)
    a = p.parse_args()
    base, subject, out = [x.resolve() for x in (a.base, a.subject, a.out)]
    require_source(base, a.base_pin)
    require_source(subject, a.subject_pin)
    if a.base_pin == a.subject_pin:
        raise ValueError("distinct source pins required")
    test = subject / "modules/adsr/tests.cpp"
    witness = test.read_text()
    note = extract(witness, "static ws2_event note(", "static std::unique_ptr<DspFixture> rig(")
    capture = extract(witness, "static std::vector<float> choke_capture(", "static void s79_choke_metric()")
    code = ('#include "tests/native/abi2/dsp_fixture.h"\n'
            '#include <algorithm>\n#include <memory>\n#include <vector>\n' +
            note + capture + '''
int main(int argc, char** argv) {
    VERIFY(argc == 2);
    const auto pcm = choke_capture(true, false, true);
    FILE* f = std::fopen(argv[1], "wb");
    VERIFY(f);
    VERIFY(std::fwrite(pcm.data(), sizeof(float), pcm.size(), f) == pcm.size());
    VERIFY(std::fclose(f) == 0);
}
''')
    out.mkdir(parents=True, exist_ok=False)
    (out / "fixture.cpp").write_text(code)
    rows, pcm = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        for role, src, pin in (("before", base, a.base_pin), ("after", subject, a.subject_pin)):
            exe = temp / role
            raw = temp / (role + ".f32")
            cmd = ["c++", "-std=c++17", "-O3", "-DNDEBUG",
                   *["-I" + str(src / x) for x in (".", "sdk", "sdk/include", "engine/include", "host/include")],
                   str(out / "fixture.cpp"), "-o", str(exe)]
            subprocess.run(cmd, check=True)
            subprocess.run([str(exe), str(raw)], check=True, stdin=subprocess.DEVNULL)
            x = np.fromfile(raw, dtype=np.float32)
            if x.shape != (FRAMES,) or not np.isfinite(x).all() or np.max(np.abs(x)) > 1:
                raise ValueError("invalid raw oscillator PCM")
            pcm[role] = x
            wav = out / (role + ".wav")
            wavfile.write(wav, RATE, x)
            read_rate, roundtrip = wavfile.read(wav)
            if read_rate != RATE or not np.array_equal(x, roundtrip):
                raise ValueError("WAV round-trip mismatch")
            rows[role] = dict(source_commit=pin, wav_sha256=digest(wav), pcm_sha256=digest(raw),
                              executable_sha256=digest(exe), peak_dbfs=peak(x))
    if not np.array_equal(pcm["before"][:SWITCH], pcm["after"][:SWITCH]):
        raise ValueError("pre-CHOKE PCM differs")
    # Reproduce the existing signed callback metrics, not a new acceptance gate.
    if abs(rows["before"]["peak_dbfs"] - (-7.429097628)) > .0001 or abs(rows["after"]["peak_dbfs"] - (-26.407878011)) > .0001:
        raise ValueError("listening fixture did not reproduce existing CHOKE witness")
    report = dict(case="VCO", sample_rate_hz=RATE, frames=FRAMES, channels=1,
                  block_frames=128, note_on_frame=17, note_key=69, choke_frame=SWITCH,
                  fallback_hz=220, note_hz=440, gain=1.0, pre_choke_equal=True,
                  encoding="IEEE float32 WAV", fixture_source=a.subject_pin,
                  folder_test_sha256=digest(test), generated_fixture_sha256=digest(out / "fixture.cpp"),
                  compiler=subprocess.check_output(["c++", "--version"], text=True).splitlines()[0],
                  rows=rows)
    (out / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
