<!-- SPDX-License-Identifier: GPL-3.0-only -->
# #226 — A12 / M7 r1.2 Macro pitch applicability (offline-only)

**Separate, read-only evidence publication PR from main.** Existing draft [PR #230](https://github.com/kalharbi11/wirescape-lab/pull/230) is untouched at `53317f0e5df33024bf1f6650915d71568a104c28`. Its `.github/workflows/macro-non48-evidence.yml` includes its own path and `bench/evidence/macro_non48/**` in `pull_request.paths`, and has an unguarded `source-capture` job. Both changing that workflow and adding these files to PR230 would automatically recapture source, explicitly forbidden by A12. The lead authorized this **separate PR from main** instead; it changes no capture implementation, trigger, gate or pinned source bytes. See [the original wiring diagnosis](https://github.com/kalharbi11/wirescape-lab/pull/230#issuecomment-6969596497).

## Source and scope

Actual existing [automatic run #44229365015](https://github.com/kalharbi11/wirescape-lab/actions/runs/44229365015), independently downloaded, never recaptured:

| Architecture | Original artifact | Original ZIP SHA-256 |
|---|---|---|
| Linux x64 | [14396920224](https://github.com/kalharbi11/wirescape-lab/actions/runs/44229365015/artifacts/14396920224) | `cc241b117810eb323c0b3a6330ff8b454b8a80dfe31db23cd0a96753cb01a959` |
| Linux ARM64 | [14394124427](https://github.com/kalharbi11/wirescape-lab/actions/runs/44229365015/artifacts/14394124427) | `06e4a12199b9953007bae464d6aafe9c9b7016eb253820c3b56948fe8bfb15b3` |

Before: `cdd608d517ffe3106897de7d80274768375d0e3c`. After B4 A6 compatibility handoff: `7bde1ee9603ae7f231d8d20ac130856b97fa8994`. Original source `bench/offline/metrics.py` SHA-256: `6fdeed51e121b62b6ef4b9fa16b773f4c5b42cc4d28db0d643697390bae09efe`.

`a12_analyze.py` recomputes **only the applicability classifier** using each byte-identical before/head 48 kHz original float32 PCM render. It retains the original Hann-window FFT selected bin, the original 80–120% target window, and the original log-parabolic peak estimator output for off-rate comparisons. A reference is *pitch defined* only when (1) selected-bin magnitude ≥1 dB over the largest competitor outside ±3 bins **in the same window**; and (2) selected-bin magnitude ≥−40 dB relative to the global spectrum maximum (excluding DC). Compute both margins from 48 kHz **before comparing 44.1/96 kHz**. Defined rows then must pass **the original ±2-cent target**; a defined failure is a real S7.4 defect for B3. Other rows are `pitch_not_defined`, with both margins and original diagnostic cents, neither a pass nor zero.

The source script verifies original artifact ZIP SHA/CRC, every raw compressed and decompressed float32 PCM SHA/length, complete 24×5×3 head and 24×5 baseline matrix, source pins, unchanged FFT estimator SHA, 48 kHz PCM equality, and all original off-rate estimator values. It runs **no native renderer, engine, Git operations, network request, audio device or MIDI device**. To reanalyze with already-downloaded original ZIPs:

```sh
python bench/evidence/macro_non48/a12_analyze.py \
  --x64 /path/to/github-actions-artifact-14396920224.zip \
  --arm64 /path/to/github-actions-artifact-14394124427.zip \
  --out /tmp/macro-a12-verified
```

## Actual A12 evidence

| Architecture | Defined 48 kHz model/target references | Off-rate defined pass | Off-rate defined fail | `pitch_not_defined` |
|---|---:|---:|---:|---:|
| Linux x64 | 86 / 120 | 172 | 0 | 68 |
| Linux ARM64 | 86 / 120 | 172 | 0 | 68 |

Across both architectures: **344 defined comparisons pass, 0 defined failures, 136 undefined comparisons**. All eight original greater-than-2-cent diagnostics on models 6, 7, 12 and 15 were checked and are numerically `pitch_not_defined` under A12. They are not blanket model exclusions. Models with **no defined target** among the five original pitches: 03 Six-op FM B, 07 Chiptune, 12 Additive, 14 Chords, 18 Particle. Model 17 Noise at 1760 Hz *is defined* by the numerical test and its two off-rate rows pass: no name-based whitelist.

Files `A12_linux-x64_rows.json` and `A12_linux-arm64_rows.json` each preserve **all 240 exact off-rate rows and 120 48 kHz classifier references**, both margins, original per-row compressed/raw PCM SHA provenance, original frequencies and original delta cents. Matching `.md` files show all rows in readable tables. `A12_model_summary.json` and `A12_summary.md` preserve the full 24-model acceptance matrix, status totals, any defined failures and no-defined models. The JSON and Markdown were regenerated offline from the immutable ZIPs and matched the review bundle byte-for-byte.

The **11 positive/negative known-answer tests** in `test_a12_analyze.py` cover threshold boundaries, DC exclusion, ±3-bin masking, actual original Hann left-channel/last-80% input, silence, NaN, missing observations, original pins, model names and a strict >±2-cent defined failure. A distinct new read-only [SR8 offline unit workflow](https://github.com/kalharbi11/wirescape-lab/blob/5ee999aef0d171b597ce1045b8379475b0036ae3/.github/workflows/macro-a12-offline-review.yml) validates A12 tests **and** pins/executes the eight original collector unit tests from PR230's recorded SHA; it never runs the existing source-capture job or downloads audio. All workflow jobs have read-only `contents` permission, and no `continue-on-error`, gate waiver or skip-CI flag.

**Not a full S7.4 merge/acceptance:** Independent M7 review, PR212 integration and lead-managed D5 FLAC release attachment remain outstanding. The off-rate full nonquick sweep coverage was not proven by this A12 analysis, and A12's 8–192 kHz Medium follow-up remains nonblocking unless PR212 later changes. This publication is limited to applying Architect A12 to **existing, unchanged** run #44229365015 data.

Signed: gpt-builder2, 2026-11-18 ET.
