<!-- SPDX-License-Identifier: GPL-3.0-only -->
# T7.0 / #148 — pinned offline CHAOS and switch-click capture

This is a *source-pinned capture recipe*, not a completed measurement.
The only repository fact output permitted for T7.0 is
facts/dsp/m7_t7_0_baseline.json. No second facts summary (Markdown pair)
and no changes to native/ or modules are part of this task.

## Source and before-value provenance

- Fable contract: docs/workflow/milestones/M7.md r1 and proposals/0011
  (Fable 2026-11-16 ET), accepted in PR #144.
- Before task's source baseline: main
  5d6bbbc52902afe8416b3c38cc5af82320c93867, after #139 had a
  signed blocked handoff on PR #150. The build to be measured must be
  the exact full 40-character #148 PR head recorded in its Result.
- Historical facts: facts/BASELINE.md before values and
  facts/dsp/ci-linux-x64/oscillators.json, lab source
  7d3842dc783915cf31aaf43bca508ebdcefb8a48 (Linux x64 hosted
  runner, 2026-11-14 ET). The historical oscillator file has 100 rows
  and *zero* CHAOS A rows. Its alias_floor_unit describes historical
  nonharmonic energy, not the later bin-restricted alias metric.
  It does not provide any of the T7.0 before-case numeric values.
- The new probes reuse oscillator_metrics and step_metrics. The
  existing parameter_steps.json, click_events, oscillators.json
  full-suite behavior and metric meanings remain unchanged.

## Exact built-head Worker2 / owner capture

All commands are relative to the checked-out PR #148 repo root.
Use the class-A worker's approved Linux x64 headless environment,
no physical audio, MIDI, or LAN. Never include hostnames, usernames,
private paths, secrets, or device names in a published fact.

1. Checkout EXACT PR #148 40-character head, verify clean git status.
   Use the dependency-seeding recipe pinned in CURRENT.md if needed
   (byte-identical git archive with URL_HASH verification); no waived
   dependency integrity check or substituted native code.
2. Build the native renderer and its dependencies without devices:

       python tools/dev.py build --headless --config Release

   Record full checkout SHA and compiler/CMake/Python versions; the
   generated summary also hashes the exact Release wirescape_render
   binary.
3. Run the synthetic regression suite and record its complete exit code:

       python -m unittest discover -s bench/offline -p 'test_*.py' -v

   The existing offline-facts.yml on pull requests also runs this
   exact command; the workflow and required Lab CI are not modified.
4. Capture the actual before-values, outside the repository:

       HEAD="$(git rev-parse HEAD)"
       python bench/offline/t7_0.py \
         --build-dir build/native \
         --head "$HEAD" \
         --out-dir <APPROVED_ARTIFACT_DIR>/t7-0-raw \
         --summary <APPROVED_ARTIFACT_DIR>/t7-0-summary.json

   The native-only chaos subroutine uses 2-second renders; it
   enumerates 44,100, 48,000, 96,000 Hz; 110, 1760, 3520, 7040 Hz;
   A saw and square = 24 unique source rows, with alias_floor_dbfs,
   rms_fs, isolated folded bin count, and accurate reason when
   unavailable. It fails on missing/duplicate keys, stale source
   commit, or wrong sample-rate set. The switch probe renders four
   explicit 48-kHz setParam changes at frame 48,000, including Quad
   VCA mode1 and Delay mode/division/tone. Peak FS and 20log10(peak)
   from the existing 2-kHz highpass step window are recorded; no
   threshold or new CI gate is used.
5. Publish through the owner-approved artifact store the complete
   summary JSON, t7-0-raw/dsp/oscillators.json (and .md there), the
   stdout/stderr and command/exit-code record, toolchain/machine-class
   provenance and SHA-256 hashes. Do not commit captures >1 MB,
   audio ZIPs, personal host paths or actual device measurements.
   The summary retains all row statuses and full source identity.
   Recompute the oscillator artifact and renderer hashes independently.

## Handoff and neutral facts update

Root/Worker2 separately confirms all 24 exact CHAOS source cases
and four switch cases against the full head, including actual renderer
runs, FFT-bin availability, RMS, and source artifact hashes. If one
case was refused, record its actual status/reason; do not interpolate
an aggregate or reuse an older-rate value. Before merging, replace
only the pending measurements in facts/dsp/m7_t7_0_baseline.json,
keeping the original historical source references. A CHAOS result
already below -80 dBFS is explicitly reported to the lead for the
M7 target-reset ruling, not retuned. ringmod2 remains unmeasured,
not a sound-parity claim.

No module, DSP signal processing, engine, host, SDK, patch, contract,
test tolerance or CI workflow change is authorized here. T7.0 is a
measurement prerequisite; S7.1–S7.9 stay with the lead's assignments.
If native execution/capture access is absent, leave the 24 + 4
pending rows as unmeasured and report the exact missing artifact.
