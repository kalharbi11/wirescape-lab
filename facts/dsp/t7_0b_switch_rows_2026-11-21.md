<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M7 T7.0b — source-pinned paired switch / no-switch facts (2026-11-21 ET)

**Disposition:** actual hosted device-off **before** observations for Architect M7 r1.3 [#296](https://github.com/kalharbi11/wirescape-lab/issues/296) / draft [PR #300](https://github.com/kalharbi11/wirescape-lab/pull/300). The four original switch identities are retained, and a fifth **clocked** Delay division fixture was added. Four effects are measurable on Linux x64; the original unclocked division is explicitly **`no_effect`** rather than an invented 0 dB click. ARM64 has a materially different earliest observed `mode` effect, reported below. **Neutral facts only — no production, audible-click or S7.6 acceptance target claim.**

## Exact provenance

- **Measurement source SHA:** `1a5dd859e25038daf038ec747334fa86d4ae4695` (Architect-authorized correction 2/2, bench-only) based on `main` at task start `0d1d7a963ccb1c301cf3fe7216632d84de6554e0`. No `native/`, Studio, DSP, CI, threshold, `step_metrics`, 2 kHz filter, or CHAOS alias-method changes. This subsequently authored facts file does **not** re-pin earlier measurements to its documentation commit.
- **Original automatic source-pinned run:** [T7.0 advisory 44928553979](https://github.com/kalharbi11/wirescape-lab/actions/runs/44928553979), attempt 1, **success** for both ubuntu-24.04 x64 and ubuntu-24.04-arm; actual Release `wirescape_render` and pure test suite succeeded. Original run generated 24 CHAOS alias cases and the four original paired switch cases **plus one clocked division pair**.
- **x64 original ZIP:** [artifact 14716377972](https://github.com/kalharbi11/wirescape-lab/actions/runs/44928553979/artifacts/14716377972), 8,809 bytes, SHA-256 `b82c413123fe67988be0a07cf5d4f911a4acd23de76baa9e506db4a0ada1136c`. `t7-0-summary.json` SHA-256 `cbadf69ded1ebb5039de606686e836900b916ac08cadbfbf76e7bfd342e5f2a9`; `t7-0-raw/dsp/oscillators.json` SHA-256 `f03d03e254ed443561dd33f1a8a8b6cb8912a8c131eb3a2cbd2291450148ec99`. Runner ubuntu24 image 20261116.376.1; AMD EPYC 9V45, x86_64, Python 3.12.16, compiler GCC 13.3.0. Collected 2026-11-21 17:10:23 UTC; recorded Release renderer SHA-256 `06739c54ea62cde5dee63cae7bb606183320eea27f8702ec47aa54dcb49114e5`.
- **ARM64 original ZIP:** [artifact 14716309694](https://github.com/kalharbi11/wirescape-lab/actions/runs/44928553979/artifacts/14716309694), 8,714 bytes, SHA-256 `95fd1f4eaf195d9cac2a384c264bac3f7054e2bde50ecba7f8856ff3350692d6`. `t7-0-summary.json` SHA-256 `ef05626c703d7ee38f8d2970775799f9b7949ebe5345464027e5deaea8ac48ce`; oscillator JSON SHA-256 `e8ec14e704a81c9c9b9d8c52b1350f4d3793590462cf468c13248c9ca9de530a`. Runner ubuntu24-arm64 image 20261116.188.1, aarch64, Python 3.12.16, GCC 13.3.0. Collected 2026-11-21 17:10:26 UTC; recorded Release renderer SHA-256 `f7649108dc91dadd2717bdb7bdb06e5f2a7c9832a91961d56147e1918f6c3459`.
- Both ZIP digests, source SHA, original summary hashes, oscillator member hashes, per-row fields and click-excess arithmetic were independently verified from the downloaded original ZIP bytes. Original artifacts are scheduled to expire **2027-02-19 17:10:09 UTC**. The full 2 s PCM and executable bytes are not archived; their SHA/provenance and online sample-comparison results are retained, so independent post hoc PCM-level verification would require a source-pinned recapture.

## Method and measured Linux x64 before-numbers

Every case uses the actual same native-v2 patch, seed and source twice: one 2-second, 48,000 Hz run with a real `setParam` switch at frame **48,000** (1 s), one with **no switch event**. Each run's result counters show zero faults, dropped, late, stale, arena-full and ring-full events. Both resulting 96,000-frame stereo PCM arrays must be identical before frame 48,000. The collector detects the first **exact unequal PCM sample** in the remaining 1 s; a pair with no difference throughout is **`status: no_effect`**, with **null** click excess, never measured zero. No device or LAN used.

The 2nd-order causal Butterworth 2,000 Hz high-pass is unchanged. The Quad VCA peak uses the original **±25 ms** (2,400-frame) switch-centered window. Each Delay row spans from the switch through 25 ms **after the observed first different frame**. Reported `switch_click_peak_dbfs` and `no_switch_floor_dbfs` are separately measured peaks in the **same row-specific window**. `click_excess_db = 20 log10(switched_peak / baseline_peak)`, not a sample-subtracted waveform or operating-system CPU measure. The additional clocked division fixture connects `essentials.clock` output `clock` to `fx.delay` input `clock` at 120 BPM and 4 ticks/beat; the other four probes remain unclocked.

| Switch identity | Fixture | Status | Switched peak dBFS | No-switch floor dBFS | Excess dB | First different frame | Observation frames [start,end) |
|---|---|---|---:|---:|---:|---:|---|
| Quad VCA `mode1` 0→1 | unclocked | measured | −26.094125 | −38.443340 | +12.349215 | 48000 | [46800,49200) |
| Delay `mode` 0→1 | unclocked | measured | −33.787226 | −40.828496 | +7.041270 | 84001 | [48000,85201) |
| Delay `division` 5→6 | unclocked | **no_effect** | −40.828496 | −40.828496 | **not defined** | none in 2 s | [48000,67200) (reference only) |
| Delay `tone` 0→1 | unclocked | measured | −38.382989 | −40.828496 | +2.445507 | 66000 | [48000,67200) |
| Delay `division` 5→6 | **clocked** | measured | −35.678596 | −38.759374 | +3.080779 | 48000 | [48000,49200) |

The unclocked division row is genuinely unchanged over the full capture because no clock period is applied; its equal high-pass peaks do **not** make a valid measured click-excess value. For the legacy existing four-row CI contract, this row is projected as `unavailable` with a `no_effect` reason. The original `t7_0b_switch_rows` array inside each ZIP retains its authoritative `status: no_effect` and includes the extra clocked row.

## Cross-architecture replication and unresolved discrepancy

| Switch identity | ARM64 switched peak dBFS | ARM64 floor dBFS | ARM64 excess dB | ARM64 first different frame |
|---|---:|---:|---:|---:|
| Quad VCA `mode1` | −26.094125 | −38.443340 | +12.349215 | 48000 |
| Delay `mode` | −40.828518 | −40.828518 | **0.000000** | **66000** |
| Delay `division`, unclocked | −40.828518 | −40.828518 | **no_effect / null** | none |
| Delay `tone` | −38.382967 | −40.828518 | +2.445550 | 66000 |
| Delay `division`, clocked | −35.678595 | −38.759364 | +3.080769 | 48000 |

**Material limitation:** the ARM64 `mode` pair first differs at frame **66,000**, unlike x64 at **84,001**. The first-effect-window rule accordingly yields a 400 ms ARM64 observation and a 775.021 ms x64 observation; ARM64 reports 0.0 dB excess **in its measured window only**. This does **not** prove the absence of an effect or later click on ARM64. The difference may reflect platform-dependent numerical behavior; that explanation is unproven. Do not silently average the two or use 0 dB as a universal `mode` before-number. Architect/lead owns any later target interpretation.

## Independent validation and disposition

Original artifact checks confirmed both ZIP SHA-256s, original 24/24 alias rows and oscillator member SHA-256s, four original-row identities plus one clocked row, source and runner identity, 96,000 frames per stereo pair, matching window frames and lengths, source-recorded first-effect frames inside each measured window, recomputed peak-to-dBFS and dB-excess arithmetic, `no_effect`/null semantics, and **zero** native counter errors on both sides of all five pairs. These are single hosted runs per architecture, not a measured audible-click assessment and not a PASS against a newly invented S7.6 threshold.

The T7.0b implementation and raw capture evidence satisfy the **data-collection** portion of [#296](https://github.com/kalharbi11/wirescape-lab/issues/296). Exact **facts-head Lab CI** and lead/Architect review remain distinct merge gates. S7.6 release belongs to Architect and remains held pending disposition.

Signed: **gpt-builder2 — 2026-11-21 ET**.
