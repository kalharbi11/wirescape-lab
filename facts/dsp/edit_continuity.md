<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Edit continuity (T0.13b)

Lab commit `4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad`; cloud container, null sink, devices off; Linux x86_64, Intel(R) Xeon(R) Processor @ 2.10GHz; 2026-11-16T19:00Z UTC; 48000 Hz, 256 frames; 3 repeats, worst shown.
Method: proposals/0005 section 4 as amended by M0 r3 ruling R7; bench/continuity/DESIGN.md. Edit position from the marks file only; "bracket" is `b1 + 1 − b0` blocks. `—` means not measured; the JSON gives the reason and every repeat. No thresholds.

| edit | witness | ch | reply | bracket | silence_ms | dip_db | time_slip_ms | jump_ratio | disturbed_ms | restarted |
|---|---|---|---|---|---|---|---|---|---|---|
| addModule unconnected | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| addModule unconnected | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| addModule unconnected | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| addModule unconnected | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| addModule unconnected | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| removeModule unconnected | tone | 0 | ok | 6 | 0.0417 | -26 | — | 1 | 10.6 | — |
| removeModule unconnected | slip_tone | 1 | ok | 6 | — | — | -3.44e-08 | — | — | — |
| removeModule unconnected | tail | 2 | ok | 6 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| removeModule unconnected | held_note | 3 | ok | 6 | 0.0417 | -27.8 | — | 1 | 10.6 | — |
| removeModule unconnected | clock | 4 | ok | 6 | — | — | 0 | 1 | 0 | — |
| removeModule connected | tone | 0 | ok | 4 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| removeModule connected | slip_tone | 1 | ok | 4 | — | — | -3.37e-08 | — | — | — |
| removeModule connected | tail | 2 | ok | 4 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| removeModule connected | held_note | 3 | ok | 4 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| removeModule connected | clock | 4 | ok | 4 | — | — | 0 | 1 | 0 | — |
| removeModule connected | subject | 5 | ok | 4 | — | — | — | — | — | — |
| connect signal | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| connect signal | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| connect signal | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| connect signal | held_note | 3 | ok | 5 | 0.0208 | -23.9 | — | 1 | 10.6 | — |
| connect signal | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect signal | subject | 8 | ok | 5 | — | — | — | — | — | — |
| disconnect signal | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| disconnect signal | slip_tone | 1 | ok | 5 | — | — | -3.37e-08 | — | — | — |
| disconnect signal | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| disconnect signal | held_note | 3 | ok | 5 | 0.0208 | -27.8 | — | 1 | 10.6 | — |
| disconnect signal | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect signal | subject | 5 | ok | 5 | — | — | — | — | — | — |
| connect event | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| connect event | slip_tone | 1 | ok | 5 | — | — | -3.37e-08 | — | — | — |
| connect event | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.794 | 10.6 | — |
| connect event | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| connect event | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect event | subject | 6 | ok | 5 | — | — | — | — | — | False |
| disconnect event | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| disconnect event | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| disconnect event | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| disconnect event | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| disconnect event | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect event | subject | 7 | ok | 5 | — | — | — | — | — | — |
| connect modulation | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| connect modulation | slip_tone | 1 | ok | 5 | — | — | -3.44e-08 | — | — | — |
| connect modulation | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| connect modulation | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| connect modulation | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect modulation | subject | 6 | ok | 5 | — | — | — | — | — | — |
| disconnect modulation | tone | 0 | ok | 5 | 0.0208 | -24.9 | — | 1 | 10.6 | — |
| disconnect modulation | slip_tone | 1 | ok | 5 | — | — | -3.74e-08 | — | — | — |
| disconnect modulation | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.794 | 10.6 | — |
| disconnect modulation | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| disconnect modulation | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect modulation | subject | 5 | ok | 5 | — | — | — | — | — | — |
| setModAmount | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| setModAmount | slip_tone | 1 | ok | 5 | — | — | 1.87e-08 | — | — | — |
| setModAmount | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| setModAmount | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| setModAmount | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| setModAmount | subject | 5 | ok | 5 | — | — | — | — | — | — |
| ccMap.set | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| ccMap.set | slip_tone | 1 | ok | 5 | — | — | -3.44e-08 | — | — | — |
| ccMap.set | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| ccMap.set | held_note | 3 | ok | 5 | 0.0208 | -27.8 | — | 1 | 10.6 | — |
| ccMap.set | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| loadGraph identical | tone | 0 | ok | 8 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph identical | slip_tone | 1 | ok | 8 | — | — | 33.3 | — | — | — |
| loadGraph identical | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph identical | held_note | 3 | ok | 8 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph identical | clock | 4 | ok | 8 | — | — | -122 | 1 | 1.01e+03 | — |
| loadGraph identical | subject | 5 | ok | 8 | — | — | — | — | — | True |
| loadGraph Groove steps | tone | 0 | ok | 10 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph Groove steps | slip_tone | 1 | ok | 10 | — | — | 33.3 | — | — | — |
| loadGraph Groove steps | tail | 2 | ok | 10 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph Groove steps | held_note | 3 | ok | 10 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph Groove steps | clock | 4 | ok | 10 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph Groove steps | subject | 7 | ok | 10 | — | — | — | — | — | True |
| loadGraph Groove length | tone | 0 | ok | 8 | 6.04 | -164 | — | 1 | 1.03e+03 | — |
| loadGraph Groove length | slip_tone | 1 | ok | 8 | — | — | 33.3 | — | — | — |
| loadGraph Groove length | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph Groove length | held_note | 3 | ok | 8 | 1.02e+03 | -147 | — | 1 | 1.03e+03 | — |
| loadGraph Groove length | clock | 4 | ok | 8 | — | — | -117 | 1 | 1.01e+03 | — |
| loadGraph Groove length | subject | 7 | ok | 8 | — | — | — | — | — | True |
| loadGraph voice count | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph voice count | slip_tone | 1 | ok | 9 | — | — | -45.3 | — | — | — |
| loadGraph voice count | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph voice count | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph voice count | clock | 4 | ok | 9 | — | — | -122 | 1 | 1.01e+03 | — |
| loadGraph voice count | subject | 3 | ok | 9 | — | — | — | — | — | — |
| loadGraph OSC In row | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph OSC In row | slip_tone | 1 | ok | 9 | — | — | 49.3 | — | — | — |
| loadGraph OSC In row | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph OSC In row | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph OSC In row | clock | 4 | ok | 9 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph one parameter | tone | 0 | ok | 8 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph one parameter | slip_tone | 1 | ok | 8 | — | — | 38.7 | — | — | — |
| loadGraph one parameter | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph one parameter | held_note | 3 | ok | 8 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph one parameter | clock | 4 | ok | 8 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph one parameter | subject | 5 | ok | 8 | — | — | — | — | — | — |
| loadGraph deleted module | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph deleted module | slip_tone | 1 | ok | 9 | — | — | 28 | — | — | — |
| loadGraph deleted module | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph deleted module | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph deleted module | clock | 4 | ok | 9 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph restored module | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph restored module | slip_tone | 1 | ok | 9 | — | — | 33.3 | — | — | — |
| loadGraph restored module | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph restored module | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph restored module | clock | 4 | ok | 9 | — | — | -117 | 1 | 1.01e+03 | — |
| setBufferFrames | tone | 0 | ok | 4 | 0.0208 | -24.7 | — | 1 | 9.94 | — |
| setBufferFrames | slip_tone | 1 | ok | 4 | — | — | 32.5 | — | — | — |
| setBufferFrames | tail | 2 | ok | 4 | 250 | -inf | — | 0.941 | 1.01e+03 | — |
| setBufferFrames | held_note | 3 | ok | 4 | 1.01e+03 | -147 | — | 17.2 | 1.01e+03 | — |
| setBufferFrames | clock | 4 | ok | 4 | — | — | 112 | 1 | 1.01e+03 | — |
| panic | tone | 0 | ok | 1 | 0.0208 | -1.09 | — | 7.08 | 1.01e+03 | — |
| panic | slip_tone | 1 | ok | 1 | — | — | -9.33 | — | — | — |
| panic | tail | 2 | ok | 1 | 250 | -inf | — | 0.941 | 1.01e+03 | — |
| panic | held_note | 3 | ok | 1 | 1.01e+03 | -147 | — | 17.2 | 1.01e+03 | — |
| panic | clock | 4 | ok | 1 | — | — | 101 | 1.1 | 1.01e+03 | — |
| panic | subject | 3 | ok | 1 | — | — | — | — | — | — |

## Not measured (not supported today)

- applyGraph identical: applyGraph is not implemented before M2 E1
- applyGraph Groove steps: applyGraph is not implemented before M2 E1
- applyGraph Groove length: applyGraph is not implemented before M2 E1
- applyGraph voice count: applyGraph is not implemented before M2 E1
- applyGraph OSC In row: applyGraph is not implemented before M2 E1
- applyGraph one parameter: applyGraph is not implemented before M2 E1
- applyGraph deleted module: applyGraph is not implemented before M2 E1
- applyGraph restored module: applyGraph is not implemented before M2 E1

## M4 CN — E4a/E4b Linux x64, 2026-11-24 (A50)

The T0.13b table above is historical; its absolute waveform metrics and unsupported
entries describe its own source pin, not the later A50 harness. These new rows use
the setup-matched no-edit control comparison (proposals/0005 sections 4–5, R7,
A50; `bench/continuity/DESIGN.md`). The comparison window begins 48,000
samples before b0 and ends 48,000 samples after the inclusive edit bracket
(b1 + 1 blocks). Raw absolute-waveform metrics remain in each report's
`worst` and `repeats`; edit-induced metrics below are the
`repeats[].control_comparison` values, not those absolute values.

### Source pins and retained evidence

All runs: Linux x86_64 hosted Ubuntu 24.04, null sink, devices off, 48,000 Hz,
256 frames, three repeats; Python 3.12.16, CMake 4.2.3, GCC 13.3.0
(Ubuntu 13.3.0-6ubuntu2~24.04.1). Engine and harness reported clean,
built-head claims matched engine pins. Binary digests are recorded by the
harness (the binary itself is not in the archives).

| dataset | engine commit | binary SHA-256 | machine / UTC |
|---|---|---|---|
| Before E4a | `c8a3c38d2fc1e4128aeecd0b596c383f09c12c83` | `917f169539d9fc7a05764b0f8a0e4af3ffd449f098eb92f54a0ff15772cbced0` | AMD EPYC 7763 64-Core Processor, 2026-11-24T18:36Z |
| E4a | `b3e11ea3242aa2711054c0b177002e85499c8d9c` | `38004a08f46ce81ac502a604bca65029f51d387c678739ad88267a6d80b3e493` | AMD EPYC 9V45 96-Core Processor, 2026-11-24T18:36Z |
| E4b | `8e8783b0602660d964892f9fe66e0cfe310dc009` | `92fea825472f0355d7eb1f5781fe58d46f948fac1c3834c1083c43b31ec84e42` | Intel Xeon Platinum 8573C, 2026-11-24T18:36Z |
| Corrected latency, E4b | `8e8783b0602660d964892f9fe66e0cfe310dc009` | `92fea825472f0355d7eb1f5781fe58d46f948fac1c3834c1083c43b31ec84e42` | Intel Xeon 6975P-C, 2026-11-24T18:43Z |

The first three archives come from harness
`8a1a8ae50cdb15bffd8fe9ae3cc4ecd48f12d35e`, [run 45461091924](https://github.com/kalharbi11/wirescape-lab/actions/runs/45461091924).
The corrected latency archive uses harness
`8bd8014afe8ce14ac1daddd07633dfe935feeaf1`, [run 45462358346](https://github.com/kalharbi11/wirescape-lab/actions/runs/45462358346).
Each contains report.json, report.md, raw captures and marks; report.json
records every repeat, command reply, subject finding, alignment and raw-file
digest. Archive SHA-256 independently verified from downloaded bytes:

| archive | SHA-256 |
|---|---|
| [Before E4a 14954666188](https://github.com/kalharbi11/wirescape-lab/actions/runs/45461091924/artifacts/14954666188) | `9a7b3fae32d280144c6ca95e2664ffdb044fad96812f664c61ad67353045b2df` |
| [E4a 14953068003](https://github.com/kalharbi11/wirescape-lab/actions/runs/45461091924/artifacts/14953068003) | `bb14898b0da394ac212d4e4dfc4e180be8594bff3ca7520fc2c006a900c6fb99` |
| [E4b 14952798923](https://github.com/kalharbi11/wirescape-lab/actions/runs/45461091924/artifacts/14952798923) | `a53f7ce8397b028ccb29f66622f18c03ad2fa6e805e58506ec755113927497ac` |
| [Corrected E4b latency 14952634057](https://github.com/kalharbi11/wirescape-lab/actions/runs/45462358346/artifacts/14952634057) | `2e3a7b904458bdfd7a3467d55b62662dfa18ca72c45143e7ff254454d34039db` |

Source: [signed A50 evidence](https://github.com/kalharbi11/wirescape-lab/pull/416#issuecomment-7141267620).
The original latency fixture's five rows at each pin have three refused
replies (occupied signal input); they are excluded from the 19-edit counts
and superseded for the E4b latency probe only by the corrected fixture below.
They remain in the original reports, not reclassified as accepted edits.

### Edit coverage and E4b comparisons

Each of the 19 commands was accepted 3/3 at each of the three engine pins
(57 edit replies per pin). Per pin there are 108 non-latency report rows:
95 ordinary witness rows and 13 subject rows. One ordinary witness
(`applyGraph voice count`, held_note) is intentionally affected, leaving
94 unaffected rows × 3 = 282 unaffected comparisons. The table gives
maximum bracket size in blocks (as recorded by the reports) and E4b
unaffected sample-identical comparisons, out of the applicable repeats.

| edit | before E4a bracket | E4a bracket | E4b bracket | E4b identical / unaffected repeats |
|---|---:|---:|---:|---:|
| addModule unconnected | 5 | 4 | 5 | 15/15 |
| removeModule unconnected | 5 | 4 | 5 | 15/15 |
| removeModule connected | 5 | 4 | 6 | 15/15 |
| connect signal | 5 | 4 | 6 | 15/15 |
| disconnect signal | 4 | 4 | 6 | 15/15 |
| connect event | 5 | 4 | 5 | 15/15 |
| disconnect event | 5 | 5 | 6 | 15/15 |
| connect modulation | 4 | 5 | 5 | 15/15 |
| disconnect modulation | 5 | 4 | 5 | 15/15 |
| setModAmount | 1 | 1 | 1 | 15/15 |
| ccMap.set | 4 | 5 | 5 | 15/15 |
| applyGraph identical | 5 | 4 | 6 | 15/15 |
| applyGraph Groove steps | 5 | 5 | 5 | 15/15 |
| applyGraph Groove length | 5 | 4 | 6 | 15/15 |
| applyGraph voice count | 4 | 5 | 5 | 12/12 |
| applyGraph OSC In row | 5 | 5 | 5 | 15/15 |
| applyGraph one parameter | 5 | 5 | 6 | 15/15 |
| applyGraph deleted module | 5 | 4 | 6 | 15/15 |
| applyGraph restored module | 4 | 6 | 6 | 15/15 |

### Unaffected witness metrics, before E4a → E4a → E4b

Each entry is the range across all applicable repeats of the named witness
and all 19 edits, with the affected held-note row excluded. The raw reports
retain the individual edit/repeat values. — means not applicable to that
witness; it is not zero.

| witness (channel) | metric | before E4a | E4a | E4b |
|---|---|---|---|---|
| tone (0) | silence_ms | 0 … 0.020833333333333332 | 0 … 0.020833333333333332 | 0 |
| tone (0) | dip_db | -26.021158601841297 … 0 | -26.021158601841297 … 0 | 0 |
| tone (0) | jump_ratio | 1 | 1 | 1 |
| slip_tone (1) | time_slip_ms | 0 | 0 | 0 |
| tail (2) | silence_ms | 0 … 0.041666666666666664 | 0 … 0.041666666666666664 | 0 |
| tail (2) | dip_db | -26.45449381051836 … 0 | -26.84115197142652 … 0 | 0 |
| tail (2) | jump_ratio | 1 | 1 | 1 |
| held_note (3) | silence_ms | 0 … 0.020833333333333332 | 0 … 0.020833333333333332 | 0 |
| held_note (3) | dip_db | -27.983606791537117 … 0 | -28.872903950393717 … 0 | 0 |
| held_note (3) | jump_ratio | 1 | 1 | 1 |
| clock (4) | time_slip_ms | 0 | 0 | 0 |
| clock (4) | jump_ratio | 1 | 1 | 1 |
| clock (4) | edited/control onsets | 4/4 | 4/4 | 4/4 |

E4b has 675 applicable edit-induced metric values (57 tone × 3, 57
slip-tone × 1, 57 tail × 3, 54 held-note × 3, 57 clock × 2).
All silence, dip and time-slip values are zero; all jump ratios are one.
All 57 clock onset pairs match, four onsets each. Independent re-read of
source-pinned raw PCM, using each report's alignment and window length,
confirmed 282/282 comparisons (27,402,752 channel samples), zero mismatches;
raw-file digests verified for the captures used.

### E4a: 18 nonoverlapping minimum-dip repeat ranges

These are the unrounded `control_comparison.dip_db` min/max ranges,
calculated from the three repeats at each pin; the other comparable
control-differenced silence, slip and jump ranges overlap. Absolute raw
waveform metrics are a different field and are not substituted here.
The values below preserve even very small floating-point range differences.

| edit | witness | before E4a dip_db min … max | E4a dip_db min … max |
|---|---|---|---|
| addModule unconnected | held_note | -23.139073498823898 … -23.139073498823276 | -28.146942522847045 … -23.434419614645247 |
| removeModule connected | tone | -24.882662258922608 … -24.882662258922412 | -26.021158601841297 … -25.159661274150558 |
| removeModule connected | tail | -24.996969355265417 … -24.996969355265417 | -26.096104090761052 … -25.629409273814883 |
| removeModule connected | held_note | -23.139073498823898 … -23.139073498823276 | -28.146942522847045 … -26.47083533021135 |
| connect signal | held_note | -23.139073498823898 … -23.139073498823276 | -28.146942522847045 … -23.434419614645247 |
| connect modulation | tone | -24.882662258922412 … -24.882662258922412 | -26.021158601841297 … -25.159661274150345 |
| connect modulation | tail | -24.996969355265417 … -24.996969355265417 | -26.096104090761052 … -25.69255027474634 |
| connect modulation | held_note | -23.139073498823276 … -23.139073498823276 | -28.146942522847045 … -25.18769864968607 |
| applyGraph identical | held_note | -23.370829301529767 … -23.139073498823276 | -28.872903950392775 … -23.434419614645247 |
| applyGraph Groove steps | held_note | -26.47083533021135 … -23.139073498823276 | -28.872903950392775 … -28.146942522847045 |
| applyGraph voice count | tone | -24.882662258922412 … -24.882662258922412 | -26.021158601841297 … -24.882662258922608 |
| applyGraph voice count | tail | -24.996969355265417 … -24.996969355265417 | -26.096104090761052 … -25.479798595822416 |
| applyGraph OSC In row | held_note | -23.139073498823898 … -23.139073498823276 | -28.872903950391834 … -23.434419614645247 |
| applyGraph one parameter | held_note | -23.139073498823898 … -23.139073498823276 | -26.668455269184168 … -23.434419614645247 |
| applyGraph deleted module | tail | -24.996969355265417 … -24.996969355265417 | -26.096104090761052 … -25.479798595822416 |
| applyGraph deleted module | held_note | -23.139073498823898 … -23.139073498823276 | -26.47083533021135 … -24.085390132312 |
| applyGraph restored module | tone | -24.882662258922412 … -24.882662258922412 | -26.021158601841037 … -24.882662258922608 |
| applyGraph restored module | held_note | -23.139073498823276 … -23.139073498823276 | -28.862785771861837 … -23.139073498823898 |

Both engine pins' captured fade-out blocks were independently reconstructed
using their aligned control channel and the original float32 factor
(255 − i)/256 for i = 0…255. For the 18 affected witness rows × 3 repeats,
all 54 witness-blocks (13,824 samples) at the baseline and all 54
(13,824 samples) at E4a match exactly. Connected removal's fade starts at
block 824/824/824 before E4a and 822/823/826 at E4a. This records the measured
landing positions and waveform equality, not a new acceptance decision.

### Intentionally affected subjects and limitations

Subject rows retain the recorded restart assessment; — means the report
does not establish a restart result (see each repeat's restarted_note).
The restart values below are the same at all three pins.

| edit | subject channel | restarted |
|---|---:|---|
| removeModule connected | 5 | — |
| connect signal | 8 | — |
| disconnect signal | 5 | — |
| connect event | 6 | False |
| disconnect event | 7 | — |
| connect modulation | 6 | — |
| disconnect modulation | 5 | — |
| setModAmount | 5 | — |
| applyGraph identical | 5 | False |
| applyGraph Groove steps | 7 | — |
| applyGraph Groove length | 7 | — |
| applyGraph voice count | 3 | False |
| applyGraph one parameter | 5 | — |

The E4b voice-count held-note witness (channel 3) is not included in the
94 unaffected rows: all three comparisons differ, first mismatch 512/1024/1024
samples after b0, max absolute difference 0.699999988079071 each.
Control-differenced silence_ms is 12.479166666666666 each; dip_db
-137.69747643464734 / -136.94331165510536 / -136.94331165510536,
jump_ratio 1 each. Its subject restart assessment is False, not a
claim of identical output.

### Corrected latency compensation limit (report only)

The spare-input mixer fixture replaces the refused occupied-input fixture.
E4b at the corrected harness pin: three accepted edits, bracket 4 blocks
each, all five witness rows × three repeats are sample-identical to
their no-edit controls. Independent re-read verified 1,455,360 channel
samples (15 windows × 97,024), zero mismatches.

| witness | ch | identical | control-differenced silence_ms | dip_db | time_slip_ms | jump_ratio |
|---|---:|---:|---:|---:|---:|---:|
| tone | 0 | 3/3 | 0 | 0 | — | 1 |
| slip_tone | 1 | 3/3 | — | — | 0.000 / 0.000 / 0.000 | — |
| tail | 2 | 3/3 | 0 | 0 | — | 1 |
| held_note | 3 | 3/3 | 0 | 0 | — | 1 |
| clock | 4 | 3/3 | — | — | 0 | 1 |

The slip-tone absolute-waveform worst time_slip_ms in this report is
2.741950536570264e-08; the aligned control displacement is exactly zero.
This is a report-only output measurement, not evidence of a latency
compensation mechanism.

### Not measured in these A50 runs

The historical loadGraph, setBufferFrames and panic rows above are not
fresh measurements at the three A50 engine pins. Standalone setData
per data user, standalone setTransport, setSampleRate, and the separate
transition-cost rows are not measured by these selected reports. No
new device, Pi, wall-clock gap, or transition-cost measurement is inferred.


## M4 CN — E7 smaller/larger buffer (A62, 2026-11-24 ET)

Source-pinned device-off capture [45525665579](https://github.com/kalharbi11/wirescape-lab/actions/runs/45525665579), Linux x86_64 hosted Ubuntu 24.04, Intel Xeon 6975P-C, 2026-11-25T01:29Z UTC, Python 3.12.16, CMake 4.2.3, GCC 13.3.0. Engine `e7d6bcd1a7300e0445eb0dd78ce1d11dd0231405`, harness `873dc8852cf959c05156cd2fd7710fea076d6bab`, both clean. Built-head claim matched; binary SHA-256 `1eab7ed3f1497a4d0376360acb36a4ed17b0dbee2c3a9b6127dbc9e49ab662bd` (recorded, binary not archived). 48 kHz, initial 256 frames, three repeats per case, unchanged A50 metrics and load timing. Smaller 128 retains the original fixture; larger 512 adds only the constant +1 Scale/Offset (94), 10 s/unit Slew (95) and Output (96) on bus 9. The Slew output is advancing and not saturated at the edit.

[Raw archive 14981879624](https://github.com/kalharbi11/wirescape-lab/actions/runs/45525665579/artifacts/14981879624) SHA-256 `4d5168a26a2e62234bb2ea909e3993e8e035c0c70574ac753b2b7459bec7b522`. All 24 raw/marks member sizes and SHA-256s matched report.json; all marks and both segment geometries matched independently parsed capture bytes. All 33 paired windows checked directly from float32 PCM: reported equality, first mismatch and max absolute residual reproduced; each alignment residual 0, offset 0 blocks. All six command replies accepted, brackets four blocks. Actual edited segment boundaries: smaller repeats 256×825 then 128×765/765/768 blocks; larger 256×825 then 512×192/192/191. Control segments remain 256 frames. No wall-clock gap claim.

### Absolute-waveform values (worst across three repeats)

— means not applicable. These are absolute, not control-differenced.

| edit | witness | silence_ms | dip_db | time_slip_ms | jump_ratio | disturbed_ms |
|---|---|---:|---:|---:|---:|---:|
| smaller | tone | 0.020833333333333332 | 0 | — | 1.0000000000379696 | 0 |
| smaller | slip_tone | — | — | -2.2190652265678744e-08 | — | — |
| smaller | tail | 47.083333333333336 | -108.67341619390929 | — | 0.8111067994971224 | 0 |
| smaller | held_note | 0.020833333333333332 | -0.6209527346803779 | — | 1 | 0 |
| smaller | clock | — | — | 0 | 1 | 0 |
| larger | tone | 0.020833333333333332 | -24.66055982878071 | — | 7.078116194284302 | 1021.3333333333334 |
| larger | slip_tone | — | — | -30.666666710306423 | — | — |
| larger | tail | 1021.3333333333334 | -159.99336548939158 | — | 0.7868640870771975 | 1021.3333333333334 |
| larger | held_note | 1021.3333333333334 | -147.0525683274469 | — | 1 | 1021.3333333333334 |
| larger | clock | — | — | -0.020833333333333332 | 1 | 794.9791666666666 |
| larger | slew | 0 | -23.860437878086337 | — | 194656.71643415178 | 9.979166666666666 |

### Control-differenced values (worst across three repeats)

| edit | witness | identical repeats | silence_ms | dip_db | time_slip_ms | jump_ratio |
|---|---|---:|---:|---:|---:|---:|
| smaller | tone | 3/3 | 0 | 0 | — | 1 |
| smaller | slip_tone | 3/3 | — | — | 0 | — |
| smaller | tail | 3/3 | 0 | 0 | — | 1 |
| smaller | held_note | 3/3 | 0 | 0 | — | 1 |
| smaller | clock | 3/3 | — | — | 0 | 1 |
| larger | tone | 0/3 | 0.020833333333333332 | -24.66055982878071 | — | 7.078116194011695 |
| larger | slip_tone | 0/3 | — | — | -30.666666690497927 | — |
| larger | tail | 0/3 | 91.8125 | -inf | — | 1 |
| larger | held_note | 0/3 | 12.479166666666666 | -136.79155752371582 | — | 1 |
| larger | clock | 0/3 | — | — | -0.020833333333333332 | 1 |
| larger | slew | 0/3 | 0 | -24.636130665616214 | — | 194656.71643415178 |

Smaller: all 15/15 witness windows are identical; tail has 20,302 pre and 39,341 post sounding samples (post 48,000-frame window, existing -80 dBFS criterion), held note 23,960/47,920, same counts in controls, each repeat. Tail post peak 0.4796806573867798 FS, held note 0.699999988079071 FS. All clock onsets 4/4, no missing/extra.

Larger: all 18 windows differ. Tail and held note post peaks and sounding counts are zero for every repeat, versus 39,340 and 47,920 sounding control samples; pre counts 20,302 and 23,960. The paired silence metric counts consecutive newly silent samples only while the control is sounding, not the full gap length. Clock onset count 4/4, no missing/extra, one-sample lead (−0.020833333333333332 ms); this is not strictly under one sample. Tone/slip tone differ with fresh oscillators. Slew pre/post sounding samples 24,000/48,000, same as control; all three aligned traces differ for exactly 479 consecutive samples beginning at the new segment (max residual 0.4060876414296217 FS), then match sample-exactly through the remainder of the comparison window, including the entire post-bracket second. First repeat control/edited values immediately before transition 0.40693333745002747 FS; first new segment sample 0.0008477822 FS edited; both 0.409068763256073 FS at bracket end and 0.509066641330719 FS at end of post window. The trace demonstrates retained unsaturated state after transition, not a click-free transition. Dip and jump exceed ordinary CN limits; the measured jump is relative to the small slope of the ramp control, not an absolute FS amplitude. No acceptance exception inferred.

### Fresh instances and limitations

Smaller: `freshModules` absent on each of the three replies. Larger: identical 14-entry host-reported list on each reply: `essentials.vco` IDs 1, 3, 12, 19, 50, 52, 54, 61, 90; `essentials.vca` IDs 6, 14, 18; `host.keyboard` ID 11; `essentials.adsr` ID 13. Each listed instance starts fresh under A62. Delay 9 is not listed because its version-only hook returns OK; its tail is cleared, as measured. E7's [state inventory/Result](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7148694696) also identifies Reverb/Resonator tails and held-note converters (Chord, CV-to-Notes, MIDI-to-CV, Notes-to-CV) with OK-but-empty runtime state, not all present in this probe. These are distinct from host-reported fresh instances. The larger rebuild has measured discontinuities, including the audible tail/note loss and Slew transition; the final M4 gate disposition is not established by these facts. No physical audio/MIDI gap or key-release claim. Final CN refresh awaits E5; prior A50 and historical rows remain unchanged.

## M4 CN — SR21c refresh (#523)

Evidence inventory; intermediate and final measured rows. The merged E5 harness is
`9000e8ffc948f2b4c3d99220e1ebdb5e5d4830bb` (#485). The historical A62
buffer capture above is not a measurement of the integrated OB1 candidate.
The E5 native, stock and transition-cost captures at engine `9809dfb9d1ead244815b8f93a68a02f7a307fe5b`
are separately pinned evidence ([#485 Result](https://github.com/kalharbi11/wirescape-lab/pull/485#issuecomment-7153369689)),
not a final integrated-source cost refresh.

| Evidence row | Source pin | Observation |
|---|---|---|
| Intermediate 256→512, E7c-a voice chain and #504 | `5ca0f1938fb851acce158272377a1ebe7631f4d2` | measured; see intermediate capture below |
| Intermediate E5 synthetic untouched Voice (A76; replacement path changed) | `5ca0f1938fb851acce158272377a1ebe7631f4d2` | measured; see intermediate capture below |
| Final 256→512, including E7c-b Delay v2 | `8c9bb10d9eb8acf616395404c26ed0c3964e19d2` | measured; see final capture below |
| Final A69a Black Ice Choir single-instance Ir | `8c9bb10d9eb8acf616395404c26ed0c3964e19d2` | measured; see final capture below |
| Final A69a Clocked Groove adoption and max dual-instance Ir | `8c9bb10d9eb8acf616395404c26ed0c3964e19d2` | measured; see final capture below |

No continuity disposition, hardware timing, or Pi result follows from these
unmeasured rows. Earlier measured sections and their pins are unchanged.

### Intermediate CN capture (2026-11-25; not the final Delay candidate)

Subject `5ca0f1938fb851acce158272377a1ebe7631f4d2`, harness `4e0fc8e4fda4f2a141633debbc334782c365cc36`, Linux x86_64 hosted null sink, devices off, 48 kHz. A62 [run 45561322999](https://github.com/kalharbi11/wirescape-lab/actions/runs/45561322999), [artifact 14997289975](https://github.com/kalharbi11/wirescape-lab/actions/runs/45561322999/artifacts/14997289975), ZIP SHA-256 `e3b731049444311a986a0e189490e73b9d486d102ce341a85c158bfb2c11cc11`; GCC 13.3.0, CMake 4.2.3, 2026-11-25T06:34Z. Subject binary SHA-256 `9228f993bf7ddd3c6937e04a99e7621eb2d9aa8cce1cb16c9ab2e79d77235135`. Both checkout pins matched, and all 24 edited/control raw and marks member sizes and SHA-256 values matched report.json.

Three matched repeats per buffer case. Smaller 256→128: all five witnesses control-identical (15/15 windows); freshModules absent. Larger 256→512: clock control-identical 3/3; tone, slip_tone, tail, held_note and slew differ in all repeats. Held-note post sounding count 47,920/48,000, equal to control; Delay tail post sounding count 0 versus 39,341 in control, all repeats. Slew post sounding count 48,000, equal to control. Larger replies report freshModules `[]` in all repeats; this does not establish retained Delay runtime state. Larger held-note paired dip is approximately -23.5 dB and jump ratio 4.57; tone approximately -23.8 dB and 7.06. The intermediate larger row is not a continuity pass. A62 does not measure later NOTE_OFF or synthetic untouched Voice.

A76 E5 synthetic [run 45561322888](https://github.com/kalharbi11/wirescape-lab/actions/runs/45561322888), [artifact 14997951447](https://github.com/kalharbi11/wirescape-lab/actions/runs/45561322888/artifacts/14997951447), ZIP SHA-256 `f9190099a8459bcc3376eef86f7e5492c5e2458ec18d5c2966071ccf32798478`, same subject/harness pins, synthetic ABI2 descriptors, 256-frame calls. All 48 raw/marks member sizes and hashes matched synthetic.json. Adopt, ring, decline and cap each completed 3 repeats with no verifier failures; subject oracle residuals respectively 5.960464477539063e-8, 9.536743172944284e-8, 1.362391881531977e-7 and 1.3542175292258207e-7. The verifier asserts held/untouched Voice equality and fallback behavior. Adopt phase equality remains report-only (26 differing samples). This is intermediate-source evidence, not final-pin A76 evidence or stock-patch cost.

Independent intermediate audit: [A62 precision qualification and native audit](https://github.com/kalharbi11/wirescape-lab/pull/525#issuecomment-7156234024). Direct convolution reproduces 579/585 A62 scalar checks; the remaining six absolute tail dips reproduce the report using its running-sum RMS. Direct RMS gives zero (−inf dB) in the larger silent tail window; the running-sum residual reports approximately −152.65 dB. This is numerical cancellation, not retained tail signal. The larger non-pass stands. All 12 native analytic and held/untouched/release checks independently reproduced. No oracle change.

### Final Delay-inclusive capture (2026-11-25)

Subject `8c9bb10d9eb8acf616395404c26ed0c3964e19d2` is the immutable #539 merge on main, released by [the Architect](https://github.com/kalharbi11/wirescape-lab/pull/525#issuecomment-7157031233). A76 comparison against `9809dfb9d1ead244815b8f93a68a02f7a307fe5b` changes all four replacement-path files: `engine/edit.cpp` +102, `engine/render.cpp` +41/−1, `engine/build.cpp` +1/−3, `engine/types.h` +5. Therefore rerun the existing native witness, not reuse the prior pin. Exact-source Lab [45576173843](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843) completed successfully. See the exact-source assertion evidence below. No Pi or physical-device inference.


Subject `8c9bb10d9eb8acf616395404c26ed0c3964e19d2`, capture harness `09e5820dfa14523f90400c44dc7953fd35e6f50f`, hosted Linux x86_64 null sink, devices off, 48 kHz; GCC 13.3.0, CMake 4.2.3, 2026-11-25T08:29Z. A62 [run 45576525996](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576525996), [artifact 15005265410](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576525996/artifacts/15005265410), ZIP SHA-256 `52701c0bd520a56d75da3c688599cd362b4088f8f053e8541bdb85d4e6babbb9`; engine binary SHA-256 `07823e2f070d841db5db97482b6cbff66aed32bceb92a2c6e38221a9ac2f38bc`. Pins and all 24 raw/marks member sizes and digests independently matched. Independent segmented-PCM calculation: 441 scalar checks of all 33 paired windows (sample count, equality, first mismatch, max absolute difference, applicable paired silence/dip/jump and pre/post activity) matched the report at 1e-8 rel/abs; direct 48-sample RMS used. Other reported metrics below are harness output, not separately recomputed in this audit. Load alignment offset zero; all six edited marks record successful generation 1→2. Three matched repeats per size.

| Case / witness | Control-identical windows | Worst paired silence ms | Worst paired dip dB | Worst paired slip ms | Worst paired jump |
|---|---:|---:|---:|---:|---:|
| 256→128 all five | 15/15 | 0 | 0 | 0 | 1 |
| 256→512 tone | 0/3 | 0 | -25.6322 | — | 7.0643 |
| 256→512 slip tone | 0/3 | — | — | 0 | — |
| 256→512 Delay tail | 0/3 | 0 | -25.2041 | — | 1 |
| 256→512 held note | 0/3 | 0.0208333 | -24.4157 | — | 14.3842 |
| 256→512 clock | 3/3 | — | — | 0 | 1 |
| 256→512 Slew | 0/3 | 0 | -24.6361 | — | 194911.841 |

Smaller: freshModules absent; tail activity 39,341/39,340/39,341 post sounding samples, held note 47,920 each, all equal to matched controls. Larger: freshModules [] each; Delay post sounding samples 39,340/48,000 in each repeat, held 47,920 and Slew 48,000, all equal to controls. Independently compared every sample of the post-bracket second: all six larger witnesses exactly equal their controls in all three repeats. First mismatch in each of the 15 nonidentical larger windows is 256 samples after edit bracket start. Harness disturbed spans approximately 9.96 ms (tail) and 9.98 ms (tone, held and Slew). The tail is no longer cleared as on the intermediate source. The larger row still misses the ordinary Phase 2 continuity limits (dip > −0.1 dB, jump < 1.5, silence 0); state retention after the bracket is not a click-free transition or an acceptance exception. The small control ramp slope explains the large relative Slew jump. No inference about physical devices.

**A76 exact-source hard assertions:** [source lines 414–451](https://github.com/kalharbi11/wirescape-lab/blob/8c9bb10d9eb8acf616395404c26ed0c3964e19d2/host/sidecar/audio_recovery_tests.cpp#L414-L451), called at line 1361. `abi2_sidecar_audio_recovery_tests` passed in exact subject Lab [45576173843](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843): [Linux x64 job](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843/job/139074642621) log line 213 (08:30:08.8097759Z); [Linux arm64](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843/job/139074642271) line 213 (08:29:40.6871333Z); [Windows x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843/job/139074642243) line 370; [sanitizers](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843/job/139074642426) lines 1019–1020. CTest successful-test stdout is suppressed, so cite the passing test plus unconditional source assertions, not nonexistent printed peak values. Hard assertions include exact held/VCO waveforms, actual 512 vs two 256 calls, fresh exclusions, and later NOTE_OFF release; A62 raw trace is not this witness.

**A76 synthetic untouched Voice:** [run 45576525980](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576525980), [artifact 15003858598](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576525980/artifacts/15003858598), ZIP SHA-256 `ed7b154d393471a4867ec6a2ddd9189c89b2c2146803398be0fc458159bcfeb9`; native binary `ddc4f2b979393d2482273fee1e144cc939f2ff05ef5d57e160e6b85884896bab`; base `00c39f5cc1d747a75fd7dff264e8c87ef78ddb75`. All 48 members matched reported sizes and SHA-256. Independent raw oracle recomputation: 12/12 pairs, exact untouched Voice throughout, exact paired held witness; adopt release at sample 128000, held 1 before and 0 after; fallback first divergence 51456, fades 960/336/24000 frames and settle .375 by release. Maximum residuals adopt 5.960464477539063e-8, ring 9.536743172944284e-8, decline 1.362391881531977e-7, cap 1.3542175292258207e-7. Adopt phase 26 differing samples, report-only. No failures; synthetic descriptors, not stock module cost.

**A69a transition cost:** [run 45576526381](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576526381), [artifact 15004646786](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576526381/artifacts/15004646786), ZIP SHA-256 `ea9aabaa06e1f80a4f1ae98d49491e5b16cca4915bbc8c16579460a091f0f738`; binary `a5e4bdea6292a731fd890dd31d850c8bc8cc1d9995d3f8d802fa32c490a8f465`; Valgrind 3.22.0. Same engine and harness pins. [Exact-source instruction rank](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173849): Black Ice Choir first of 24 bundled rows at 128 frames, x64 1,729,688.8333 Ir/block ([artifact 15004637197](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173849/artifacts/15004637197)), arm64 1,518,270.8333 ([artifact 15004503344](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173849/artifacts/15004503344)); separate two-length rank method, not the 256-frame per-render cost below. Arm64 advisory Black Ice row +3.39% vs +3% (job 139074553027, line 343); advisory workflow success does not erase this observation.

| A69a row (256 frames, x64) | Ir | Observed block |
|---|---:|---:|
| Black Ice Choir single-instance max | 3,311,400 | 300 |
| Clocked Groove adoption | 800,347 | 248 |
| Clocked Groove max dual-instance | 800,347 | 248 |
| Clocked Groove housekeeping (diagnostic) | 494,736 | 253 |

Single stock patch SHA-256 `efc1e0352bcdd082cfa11a07f9106e40f0706e23270c974a65ed2804f00348a3`; dual patch SHA-256 `d6abf9519bea36d8dc7973f8c9b422874c59767d6dd9e0024f1f4e26db33e2cd` (reported). Clocked Groove module 2 canonical edit /modules/1/config/tracks/0/steps/0/key 60→61, canonical bytes 12376; request 242, actual adoption 248, ack completed blocks 249, 960-frame fade ends in block 251, housekeeping requested and published 253. Both rows have zero fault/late/dropped/ring_full/stale/arena_full counters. Independently reconciled all 87 dump digests (66 single, 21 dual), 82 labelled render blocks, summary=totals, contiguous block IDs, single render thread, actual adopt_layout call labels 248 and 253 and sums with Callgrind collected totals (211,593,376 and 10,490,894 Ir). No threshold, module share estimate, Pi extrapolation, or elapsed-time conclusion.

**Final disposition — bracket reported under A83** ([Architect ruling](https://github.com/kalharbi11/wirescape-lab/issues/523#issuecomment-7157532240), 2026-11-25). This supersedes the ordinary-gate non-pass for the final larger rule-2 row only, not the intermediate failed Delay row. On the Linux x64 acceptance platform: 18/18 larger post-bracket witness seconds sample-exact, freshModules [] 3/3, tail and held note sounding, clock slip 0. Exact raw comparison shows each nonidentical witness (including slip tone) spans 479 frames = 9.9791667 ms, beginning +256 frames in all original repeats; zero difference before the edit block, at most one newly silent sample. A83 caps: first mismatch no earlier than edit block, disturbed span ≤480 frames (10.0 ms), newly silent ≤1 sample. Original full-window paired dip/jump values above remain reported (worst dip −25.6322 dB, Slew jump 194911.841). Smaller 15/15 exact under unchanged full-window gates. These observed x64 rows meet A83; arm64 A62 raw capture not measured by this x64-only workflow (exact-source A70 native tests did pass arm64). Real-device gap and owner Pi listening remain unverified. A83 expires at the earlier of OB1.1 close or a session restart/mute path or max_block preparation change; remeasure against ordinary acceptance 2 then. Post-bracket difference, smaller failure, cap overrun, or owner hearing more than a single restart click overturns the disposition. No harness or gate-file change, no M4 acceptance claim.

**Automatic facts-head capture cross-check, separate harness pin** `bfc92814eb83d07f54d0d81ee1a7b36fedb7e81e`, same subject `8c9bb10d9eb8acf616395404c26ed0c3964e19d2`. [A62 45578581477](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581477) artifact [15005576635](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581477/artifacts/15005576635), ZIP SHA-256 `5251f6382f0f88b8a6b976b33a94d00aadcbb2c52dd555b3220afb71dc0199fe`. Independently parsed segmented raw: smaller 15/15 full windows exact, larger 18/18 post-bracket seconds exact, 15/18 full windows differ; all nonidentical witnesses span exactly 479 frames, first mismatch +256/+256/0 across repeats; maximum newly silent one sample; tail 39,340 and held 47,920 post sounding each, clock exact. All A83 caps remain met; paired dip/jump worst values agree to reported precision. [Native 45578581237](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581237), artifact [15006010339](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581237/artifacts/15006010339), ZIP `6f4185093feb492e1d91deaa11666851db2fd2a94f51dab36da2184833451498`: all 48 member sizes/digests matched, 12/12 verifier cases with same analytic residuals. [Cost 45578581296](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581296), artifact [15005910395](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581296/artifacts/15005910395), ZIP `d684a31e657e9fe034d52d41fd42b67dd3236806f1718a3efc3ab50f34935e34`: dump digests matched; report single max 3,311,386 Ir @300, Groove adoption/max dual 800,333 @248, housekeeping 494,722 @253; request 242, ack 249, fade end 251, zero counters. Each is 14 Ir lower than the original report; preserve separate observations, not an averaged or identical-cost claim. No manual rerun requested.
