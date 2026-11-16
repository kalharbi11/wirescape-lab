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

## T0.11: explicit coverage scope and source provenance

Supply --coverage-root head on **both** base and head invocations. The `bench/golden/coverage_manifest.json` fixture inventory is mandatory; a missing or extra top-level coverage fixture and any missing bypass control fail the render. The three top-level native-v2 coverage patches currently target NotesToCV, Chord, and Spectral, with source-control bypass patches stored under `bench/patches/coverage/controls/`. They are keyed by `coverage/` rather than `bundled/` or `owner/`, so the original 24 bundled rows remain individually visible and missing bundled/owner patches still fail.

Each coverage patch must render non-silent float32 PCM and differ from its linked bypass control. The measured per-patch record contains its exact fixture and bypass-control byte SHA-256 plus output RMS/peak and observed peak sample delta. The comparator rejects mismatched coverage fixture/control bytes between base and head before applying sound declarations or dB tolerance. The metadata records engine_source_commit from the checkout whose binary runs, and fixture_source_commit independently from the fixture checkout. These may legitimately differ on the base render; they must never be silently conflated.

The hosted head also renders **25 bundled-module cable-ablation controls** with `bench/golden/probe_bundled.py`. They are generated into temporary directories from byte-hashed original bundled JSON without changing product files. Each intervention removes only cables from the specified module (or cables into Output). These results measure causal output differences; a silent original, zero output delta, invalid control or renderer error remains explicitly `unavailable`. On every runner, `bench/golden/inventory.py` records all 34 registry IDs, the original bundled node/pair inventory, and measured or unverified per-module evidence, with actual engine/fixture SHAs, CPU model and CI run URL.

Current renderer limitations for raw MIDI, OSC ingress and non-PCM outbound/monitor taps are documented with reproduction in `bench/patches/coverage/README.md`. Do not interpret successful 24+3 golden comparisons alone as proof all 34 modules contribute. CI artifacts include numeric `coverage-inventory.json` and `bundled-interventions.json`; keep the final PR draft until the all-34 acceptance criterion is truly met or Fable explicitly handles instrumentability blockers.
