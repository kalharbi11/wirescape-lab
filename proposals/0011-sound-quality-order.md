<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0011 — Sound quality: measured order of work (Phase 4)

Fable, 2026-11-16 (ET). Inventory and first draft by an Opus helper; order, targets and rulings
by Fable. Contract: `M7`. The measured values below are quoted from `facts/`; the order and the
targets are this note's opinion.

Drafted from main `b02db25` (2026-11-16 ET), read-only. Phase 4 text: `proposals/0002-plan.md:131-136`; D5: `:19`;
audit: `proposals/0001-audit.md:98-134`; owner change on bundled patches: `docs/context/CONSTRAINTS.md:14-19`.
"(derived)" means I computed the value from committed arrays; the method is stated. Everything else is quoted from the file.

## Three findings that set the scope

- **F1 Frozen ABI1 references block sound changes in 13 modules.** `vco lfo vcf adsr vca clock function_envelope ladder
  mixer noise output scale_offset slew` are built from `native/engine2/CMakeLists.txt:108,147,191`, and their outputs are compared
  bit-for-bit against frozen ABI1 samples (`native/tests2/module_tests.cpp:198-206`, `native/tests2/utility_port_tests.h:26-50`,
  unpack target `native/engine2/CMakeLists.txt:170-201`). T1.1 kept these as frozen data (`proposals/0006-one-engine-migration.md:58,107`).
  Any intended sound change there breaks tests in `native/tests2/` and `native/engine2/`, which M1 locks
  (`docs/workflow/milestones/M1.md:17,25-26`). So VCF, Ladder, ADSR CHOKE, VCO and LFO fixes are **not module-local** today.
- **F2 Modules that are module-local.** These folders have their own `CMakeLists.txt` and `tests.cpp`: blend, chaos_lite, chord,
  delay, macro_oscillator, notes_to_cv, quad_vca, quantizer, resonator, reverb, spectral. They are added by
  `native/engine2/CMakeLists.txt:237,329-334` (no edit there is needed). Of their tests, only `macro_oscillator/tests.cpp:275-289` holds
  output hashes (FNV over model output).
- **F3 "Envelope timing 10 % short" is how the metric is defined, not a measured defect.** `bench/offline/metrics.py:435-438` measures the attack
  as the time to reach 90 % of the held level and the release as the time to fall to 10 %. ADSR ramps are linear over `round(seconds*rate)`
  samples (`native/modules2/adsr/dsp.h:14`). A linear 50 ms ramp crosses 90 % at 45 ms and a 100 ms release crosses 10 % at 90 ms, which are
  exactly the measured values (`facts/dsp/ci-linux-x64/envelopes.json`, rows `attack_measured_s` 0.045, `release_measured_s` 0.09).

## 1. What is measured

Source abbreviations: **F** = `facts/dsp/ci-linux-x64/filters.json` (commit `7d3842d`, 48 kHz, Welch, nperseg 4096, 11.7 Hz bins);
**MO** = `.../module_outputs.json`; **PS** = `.../parameter_steps.json`; **OS** = `.../oscillators.json`; **EN** = `.../envelopes.json`
(all `7d3842d`, 2026-11-14, Linux x64); **R2** = `facts/dsp/m4_r2_verified_measurements_2026-11-16.json` `numerical_rows` (line 116+;
the x64 and arm64 values are the same unless two are given); **V2** = `facts/dsp/ci-linux-x64/m4_verified_measurements_2026-11-15.json`
`observed_numeric_summary` (line 118; aggregates only, rows not committed); **IR** = `facts/perf/linux-x64/instruction_baseline.json`.

| # | Module | Metric | Value | Condition | Source |
|---|---|---|---|---|---|
| 1 | vcf | passband level, mean of `magnitude_db` over 20 Hz ≤ f ≤ fc/4 (derived) | −11.77 / −11.72 / −11.20 dB | res 0.9; fc 5000 / 1000 / 100 Hz | F rows 8, 5, 2 |
| 2 | vcf | same | −8.21 / −8.16 / −7.61 dB | res 0.5; fc 5000 / 1000 / 100 | F rows 7, 4, 1 |
| 3 | vcf | `gain_100_hz_db` | −11.91 dB (res .9), −8.37 dB (res .5), −0.10 dB (res 0) | fc 1000 | F rows 5, 4, 3 |
| 4 | ladder | same passband measure (derived) | +0.15 to +0.42 dB (no loss) | res 0.5–0.9 | F rows 11–18 |
| 5 | ladder | resonance peak, argmax `magnitude_db` (derived) | 527.3 Hz for fc 1000 (0.53·fc); 2847.7 Hz for fc 5000 (0.57·fc) | res 0.9 | F rows 15, 18 |
| 6 | ladder | same | 351.6 Hz / 1000; 2085.9 Hz / 5000 | res 0.5 | F rows 14, 17 |
| 7 | vcf | same | 937.5 Hz / 1000; 4699.2 Hz / 5000 | res 0.9 | F rows 5, 8 |
| 8 | ladder / vcf | resonance peak height (derived) | ladder +1.53 dB; vcf +9.08 dB | fc 1000, res 0.9 | F rows 15, 5 |
| 9 | all filters | `filter_frequency_response_resonance_peak_error_hz` min / max | −3261.6 / −6.1 Hz | 3 rates, 54 rows, not attributed | V2 |
| 10 | vcf, ladder | self-oscillation | `unavailable`: "no automated unexcited self-oscillation setup" | — | F rows 9, 19 |
| 11 | sound.blend | impulse peak | 1.41421 FS | 44.1 / 48 / 96 kHz | R2 |
| 12 | fx.reverb | single-module output peak | 1.0994 FS (rms 0.722) | 48 kHz, VCO feed, default params | MO |
| 13 | essentials.resonator | same | 1.0464 FS | same | MO |
| 14 | sound.spectral | impulse peak | 1.00007 / 1.00007 / 1.00014 FS | 44.1 / 48 / 96 | R2 |
| 15 | fx.reverb | `time_to_minus60_db_ms`, by rate | 295.80 / 245.35 / 208.53 ms (spread 35.6 % of the 48 k value) | 44.1 / 48 / 96, defaults | R2 |
| 16 | sound.spectral | same | 46.46 / 42.69 / 42.68 ms (8.9 %) | same | R2 |
| 17 | essentials.resonator | same | 881.90 / 889.29 / 930.50 ms (5.5 %) | same | R2 |
| 18 | ladder, vcf, delay, mixer… | same | spread ≤ 1.5 % (ladder 3.81/3.79/3.75; vcf 20.29/20.29/20.27; delay 1875.06/1875.02/1875.01) | same | R2 |
| 19 | essentials.resonator | impulse peak by rate | 0.02297 / 0.02057 / 0.00748 FS | 44.1 / 48 / 96 | R2 |
| 20 | ports.macro_oscillator | sample-rate support | `prepare()` returns false unless 48000 Hz; 18 sweep rows `unsupported_rate` | 44.1, 96 kHz | `native/modules2/macro_oscillator/dsp.h:58`; V2 `notes.sweep` |
| 21 | parameter step, 2 kHz high-pass peak | noise.level 1.549; vco.frequency 1.035; macro.model 0.327; resonator.tune 0.227; chaos.shape_a 0.140; ladder.cutoff 0.035; mixer.level_a 0.030; vca.gain 0.024; vcf.cutoff 0.023 FS | min→max step at mid-render, 48 kHz | PS `highpass_peak_fs` (audit: the top two are the signal changing, not zipper) |
| 22 | sweeps | fast(1 s)/slow(8 s) high-pass ratio | max 2.061 (+6.28 dB), median 1.004; not attributed to a module | 87 module/param pairs, 3 rates | V2 |
| 23 | bundled patches | `click_events` (1 ms / 50 ms high-pass detector) | 2 in total (44.1: 1, 48: 1, 96: 0); patch not in committed facts | 24 patches | V2 |
| 24 | ADSR | attack / release (to 90 % / 10 %) | 45 ms for 50 ms; 90 ms for 100 ms (see F3) | 48 kHz | EN |
| 25 | VCO | non-harmonic floor (old schema) | −121.9 dBFS at 110/440/1760/5000 Hz | sine only | OS |
| 26 | Macro | non-harmonic floor (old schema: all non-harmonic energy, includes inharmonic/noise models) | max −4.5 dBFS (model 1, 440 Hz); pitch error up to 386 cents (models 12, 15) | 48 kHz | OS |
| 27 | oscillators | alias floor, new schema (only bins where harmonics fold) | max −10.50 dBFS, min −300; not attributed | 180 rows incl. CHAOS A saw/square/sine | V2 |
| 28 | all R2 cases | nonfinite / subnormal / faults | 0 in all 36 measured cases ×2 arch | 1 s signal + 5 s zero, FTZ on | R2 `validated_all_measured_cases` |

Instruction cost before-numbers (IR, Ir per 128-frame block, x64, voices1 / voices8): chaos_lite 257 775 / 2 030 789; reverb
215 840 / 215 836; macro_oscillator 117 939 / 915 250; resonator 95 363 / 737 098; quad_vca 53 357 / 395 674; delay 47 345 / 47 333;
blend 37 966 / 37 974. (ARM64 baseline: `facts/perf/linux-arm64/instruction_baseline.json`.)

**Unmeasured (not zero):** `example.ringmod2` (`not_built_runtime_module`, R2 3 cases/metric/arch); 69 R2 cases `not_applicable` (no
audio input); `essentials.chord` CPU rows (probe cannot prepare, `bench/gate/README.md` §Chord) and outputs (MO "no audio or CV output");
`midi.in`, `monitor` outputs (MO); VCF/Ladder self-oscillation (F); **CHAOS alias per row** (only the V2 aggregate exists; per-row
data was in artifact 14186133633, not committed); clicks on CHOKE, Quad VCA mode switch, delay mode/division/tone switch, reverb freeze
(no switch metric for stepped parameters); NaN input and recovery (R2 only shows that no NaN appears); timed 10 s zero-input
denormal decay (V2: 0 rows); saturator aliasing (Ladder tanh, delay limiter, reverb clamp); all DSP facts on Windows
(`facts/dsp/ci-windows-x64/unavailable.json`); owner-reported, unverified: Echo knob clicks, scene-07 clicks after panic, basics-04
silence (`docs/context/KNOWN_ISSUES.md:11-12`).

## 2. Order of work

Order rule: measured severity first, then whether the fix is local to one module now, then how many bundled patches change.
"Local" means only `native/modules2/<name>/`. "Engine" means it needs `native/engine2`, `native/control`, `native/sidecar` or `native/tests2`, or
a frozen-reference change (F1). Patch counts come from grepping `apps/studio/patches/*.json` for the module ID.

| # | Fix | Files | Before/after metric (better =) | Bundled sound changes? | Where | Depends |
|---|---|---|---|---|---|---|
| 1 | T7.0 measurement completion: commit per-row CHAOS alias; add a click metric for stepped-parameter switches; Macro rows at 44.1/96 once prepare accepts | `bench/offline/`, `facts/dsp/` | — | no (bench only, class A) | parallel now | — |
| 2 | Reverb: rate-independent damping and per-sample constants. The one-pole `low[k] += (delayed-low[k])*(1-damp)` is per sample at any rate (`reverb/dsp.h:219`) | `native/modules2/reverb/dsp.h`, `tests.cpp` | R2 time-to-−60 dB spread across rates (lower) | **no at 48 kHz**: keep the 48 k coefficient bit-identical; 44.1/96 change | local | — |
| 3 | Reverb gain staging: wet makeup `1+5·mix²` (+15.6 dB at mix 1) into `clamp(±2)` (`reverb/dsp.h:68,247-250`) | same | MO peak (≤ 1.0); no clamp engagement | **yes**, 17 patches | local | 2 (same writer, in sequence) |
| 4 | CHAOS band-limited saw/square (naive at `chaos_lite/dsp.h:101-105`), e.g. PolyBLEP | `native/modules2/chaos_lite/dsp.h`, `tests.cpp` | new-schema `alias_floor_dbfs`, CHAOS A saw/square (lower) | **yes**, 9 patches | local | 1 (before-number) |
| 5 | Macro Oscillator at any rate: run Plaits at 48 k internally and resample at 44.1/96 | `native/modules2/macro_oscillator/` (dsp.h `memory_requirements`/`prepare`, tests) | `unsupported_rate` rows 18 → 0; pitch at 44.1/96 vs 48 k | **no** (48 k path bit-identical; test hashes unchanged) | local, unless Plaits sources outside the folder must change (escalate) | — |
| 6 | Resonator: output peak 1.046 and decay spread 5.5 % across rates | `native/modules2/resonator/` | MO peak; R2 spread (lower) | yes, 2 patches | local | — |
| 7 | Quad VCA: crossfade the VCA↔LPG mode switch (instant at `quad_vca/dsp.h:90-91`, state reset) | `native/modules2/quad_vca/` | T7.0 switch-click metric (lower) | probably no (golden does not switch modes); declare if it differs | local | 1 |
| 8 | Delay: crossfade mode/division switches; tone bypass across 0 (`delay/dsp.h:117-133`); owner's Echo knob clicks | `native/modules2/delay/` | T7.0 switch-click metric; PS step | maybe, up to 18 patches | local | 1 |
| 9 | Blend: impulse peak 1.414 (equal-power sum of correlated inputs?) — first confirm that it is a defect | `native/modules2/blend/` | R2 impulse peak | yes, 1 patch | local | Fable ruling |
| 10 | VCF gain compensation (−11.8 dB) and self-oscillation (k ≤ 3.2, `vcf/dsp.h:20`) | `native/modules2/vcf/` + frozen ref | passband level (towards 0 dB), peak position | yes | **engine** (F1) | M1 S3 done; Q1 |
| 11 | Ladder feedback (one-sample delay, peak at 0.53·fc, `ladder/dsp.h:12`) | `native/modules2/ladder/` + frozen ref | peak/fc ratio (towards 1.0) at 3 rates | yes | **engine** (F1) | as 10 |
| 12 | CHOKE clicks: ADSR `v=Voice{}` (`adsr/dsp.h:37`), VCO phase reset (`vco/dsp.h:30`) | adsr, vco + frozen ref | T7.0 click metric | yes | **engine** (F1) | as 10 + T7.0 |
| 13 | Host modulation smoothing (opt-out per port; `0003` item 7) | engine, module API v3 | V2 sweep ratio max 2.06; PS | yes, broadly | **engine** | Phase 3 API |
| 14 | One NaN policy (host guard and/or per-module reset) | engine or every module | new NaN-injection test | no | **engine** | Fable design |

Not proposed: an ADSR timing change (F3). LFO depth rate-scaling and DC-blocker corners (audit) have no committed measurement, so they need T7.0 first.
Severity note: #10 (VCF, −11.8 dB) is the largest measured defect, but F1 blocks it this week.

## 3. Rulings
1. **Frozen ABI1 reference cases and intended sound changes.** A frozen case for a module whose
   sound is changed on purpose is retired in that module's PR, listed with the reason. That needs
   the test files M1 holds, so VCF, Ladder, ADSR and VCO wait for M1 S6 (M7 batch 2).
2. **Envelope timing is not a defect** (finding F3). T7.0 renames the fields to
   `attack_to_90pct_s` and `release_to_10pct_s` and adds a 0 to 100 % time.
3. **Cost of a sound fix.** Each task has a cap on its instruction-count rows, stated in M7. The
   PR carries a `Cost-change:` line for any row above +3 %. The lead refreshes the baseline once
   per batch. The gate is not made machine-declarable now.
4. **Renders** go to the `bench-<date>` release, attached by the lead. No audio in git.
5. **No bundled-patch edits in M7.** The patches are reset after the rebuild (owner, 2026-11-16).
   The level change of each affected patch is recorded for that reset.
6. **Reverb is two PRs,** so the golden gate attributes each change.
7. **Blend's 1.414 impulse peak and Spectral's 1.0001 are facts, not defects,** until a note says
   what Blend's balance law is meant to be. Owner's taste decides; listed for the owner.
8. **The `chaos_lite` → `chaos` rename is not part of M7** (`0004` T3.7).
9. **Targets are relative where the before-number is not committed yet** (CHAOS aliasing,
   switch clicks): "lower by N dB, or below a stated floor, whichever is reached first". That
   lets T7.0 land the before-number without a question.
10. **Filters (batch 2) are judged by the owner's ear as well as by number.** VCF and Ladder are
    the character of the instrument. The numbers gate the PR; the render pair goes to the owner.
    Self-oscillation behaviour is not changed in batch 2: it is unmeasured and it is taste.

What would overturn the order: T7.0 showing CHAOS aliasing already below −80 dBFS (then S7.3
drops out), or a Macro resampler that cannot leave 48 kHz bit-identical (then S7.4 becomes a
declared change and moves behind the filters).

Signed: Fable, 2026-11-16
