<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device-free golden patch renders

## Primary CI gate: same-runner base/head

For pull requests touching native code or the golden harness, each of three
matrix jobs checks out the actual PR base and actual PR head commits, builds
the headless Release renderer for each in the **same job on one runner**, and
renders each bundled/owner patch twice. Both checkouts use the current
head's bench/golden/render.py so that scripts, sample rate and
instrumentation are identical even when the base predates a harness change.

- 48,000 Hz, block 128 frames, 10 seconds, fixed seed 37, C4 scripted
  key-on/off for every host.keyboard node.
- Bit-identical float32 PCM SHA-256 is required (tolerance 0). An
  undeclared change or missing patch fails the primary step. PR description
  lines can explicitly declare sound changes:
  Sound-change: basics-01-first-tone.json — intentional revised oscillator
  Sound-change: all — intentional global DSP revision
- Each patch reports identical, different or declared, with the largest
  of 31 one-third-octave band differences, the first changed **interleaved**
  stereo float32 sample index, the corresponding **frame time** (index
  divided by two channels and 48 kHz), and peak absolute sample difference.
  Temporary WAVs remain in the job-local runner temporary folder.
  **Only differing patches' before/after WAVs are uploaded**, with
  two-day artifact retention. Audio files are never committed.
- The comparator also supports --tolerance-db for explicitly non-bit-exact
  uses, with exit code 0 for differences within tolerance.
  Use tolerance 0 for the primary CI gate.

The workflow does not cache rendered PCM across runners: different CPUs,
compiler dispatch and libm may cause low-bit changes even on matching
architectures. CMake build artifacts carry absolute paths, so base
SHA build caches are not restored blindly on heterogeneous hosted runners.
Each PR A/B is built and rendered on the same runner.

## Secondary committed reference: warning only

Committed per-architecture JSON snapshots live at
facts/dsp/linux-x64/golden.json, facts/dsp/linux-arm64/golden.json and
facts/dsp/windows-x64/golden.json. Each stores patch hashes, peak/RMS/DC,
31 third-octave levels and provenance. CI compares head against its
architecture-matched snapshot with 0.01 dB spectral tolerance; differences
are warnings, never blockers for the primary gate.

Run the workflow manually (workflow_dispatch) on a real branch head to
generate a candidate JSON with the actual 40-hex commit SHA and runner CPU
model (Linux lscpu Model name where available). Download platform
golden-diagnostics-* artifacts and, after verifying the source commit and
measurements, stage those candidates as the architecture references in a
separate PR. Neither the workflow nor the harness pushes to main.

The historical references contain a 3e702b5 synthetic PR merge-ref commit,
which is not an object in the repo. Do not silently attribute those
measurements to an unrelated commit.

## Run locally, devices off

Install the existing dependencies and build native Release headless
in both checkouts:

    python -m pip install cmake==4.2.3 ninja==1.13.0 -r bench/offline/requirements.txt
    python tools/dev.py build --headless --config Release
    python -m unittest discover -s bench/golden/tests -v

For one checkout and its architecture reference:

    python bench/golden/render.py --machine linux-x64 --out build_reports/golden/current.json
    python bench/golden/compare.py facts/dsp/linux-x64/golden.json build_reports/golden/current.json --tolerance-db 0.01

For same-runner A/B using two built checkouts named base and head, run
the head's measurement script for both, retaining temporary WAVs:

    python head/bench/golden/render.py --root base --machine linux-x64 --out build_reports/golden/base.json --keep-wavs build_reports/golden/base-wavs
    python head/bench/golden/render.py --root head --machine linux-x64 --out build_reports/golden/head.json --keep-wavs build_reports/golden/head-wavs
    python head/bench/golden/compare.py build_reports/golden/base.json build_reports/golden/head.json --before-wavs build_reports/golden/base-wavs --after-wavs build_reports/golden/head-wavs --require-wavs --tolerance-db 0

The #55 PR also exercises an **uncommitted** one-line VCO amplitude
change in an ephemeral runner checkout using bench/golden/experiment.py.
It temporarily changes one line in native/modules2/vco/dsp.h, rebuilds
offline, verifies the primary comparator reports different with a non-null
sample index and positive peak delta, and verifies an explicit
Sound-change: declaration classifies the same measurement as declared.
The script restores the source even on failure. No native change is committed.

No physical audio/MIDI devices or LAN sockets are accessed.
