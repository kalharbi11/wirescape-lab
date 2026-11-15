<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device-free golden patch renders

From the lab repo root after a native Release headless build:

```sh
python -m pip install -r bench/offline/requirements.txt
python tools/dev.py build --headless --config Release
python bench/golden/render.py --machine linux-x64 --out build_reports/golden/linux-x64/golden.json
python bench/golden/compare.py facts/dsp/linux-x64/golden.json build_reports/golden/linux-x64/golden.json
python -m unittest discover -s bench/golden/tests -v
```

The runner processes all 24 bundled native patch-v2 JSON files plus every
`*.json` owner patch in `bench/patches/owner/` (empty at repository creation).
Each patch is rendered twice with the same 48 kHz / 128-frame / 10-second /
seed-37 configuration and the C4 host.keyboard event script from the existing
offline fact collector. Byte-unequal repeat renders fail immediately.

A reference is keyed by architecture: `facts/dsp/linux-x64/golden.json`,
`facts/dsp/linux-arm64/golden.json`, and `facts/dsp/windows-x64/golden.json`.
Record JSON includes the lab commit, machine, date, SHA-256 of raw little-endian
float32 stereo PCM, peak/RMS/DC full-scale values, and 31 one-third-octave
mean-square band levels in dBFS. The spectrum uses Welch one-sided PSD,
65,536-sample segments; silent/near-zero bands have a documented -300 dBFS
measurement floor.

`compare.py` defaults to byte-identical SHA-256 matching. Supplying
`--tolerance-db N` with N greater than zero admits patches whose maximum
one-third-octave difference is at most N dB. It reports the largest band
difference and exits nonzero for any `different` patch. If temporary before
and after WAV trees are supplied, `--before-wavs DIR --after-wavs DIR`,
it reports the **exact interleaved float32 sample index** for unequal PCM;
a JSON-only hash does not encode the first differing sample, so the tool prints
`unavailable (hash only)` rather than inventing an index. PCM/WAV files are
never committed or uploaded to facts, by repo policy.

The advisory `golden-renders.yml` runs on PRs touching `native/**`, and on
changes to this collector, against architecture-matched references. Its
three platform jobs also upload candidate JSON reports. Missing reference
files are reported as pending while the initial baseline is being collected.
No physical audio/MIDI devices or network listeners are used.
