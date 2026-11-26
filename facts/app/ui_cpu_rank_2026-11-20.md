<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-f1 — actual offline idle-only CPU ranking and winner UI facts (2026-11-20 ET)

**Status:** measured on a single hosted Ubuntu 24.04 Linux x64 device-off run; independently rechecked against original artifact ZIP. **Idle/default-state only; active/sounding CPU unresolved.** Neutral observations, not an OB-f2 acceptance gate or Pi/audio-device performance claim.

## Exact source and original evidence

- Issue [#209](https://github.com/kalharbi11/wirescape-lab/issues/209), draft [PR #216](https://github.com/kalharbi11/wirescape-lab/pull/216), A20 Architect release [#7036893891](https://github.com/kalharbi11/wirescape-lab/issues/209#issuecomment-7036893891).
- **Measured checkout:** `cde860221c8006d03051e81e05852834ebff4f46`; branch based on integrated main `5e6d16c9af600494b38f99a448af4ac61b26ac8b`. This facts-only commit is subsequent to measurement, and does not re-pin measurements to itself.
- **Automatic exact-source advisory:** [run 44719535007](https://github.com/kalharbi11/wirescape-lab/actions/runs/44719535007), attempt 1, **success**, job 136231439891. Release native build, Studio build, known-answer tests, all 24 real offline CLI invocations, four browser captures, actual native ACKs and artifact upload passed. [Lab CI run 44719535027](https://github.com/kalharbi11/wirescape-lab/actions/runs/44719535027) also **success** at the same source SHA. No manual rerun.
- **Original ZIP:** [artifact 14620489021](https://github.com/kalharbi11/wirescape-lab/actions/runs/44719535007/artifacts/14620489021), 11,400 bytes, SHA-256 `fd347304c3f641e52ed36d5a3d3f2888db83a84b62bb48cb43187c6e3b46b07d` independently recomputed and matching the uploader and GitHub API digest. Uploaded 2026-11-20 10:32 UTC, expires 2026-11-27 10:32 UTC.
- **ZIP members and original SHA-256:** `cpu-ranking.json` `28a01cf7369d3a36c1b688137e04491cdc8ca6592795b66c9f064100fdd4aba9`; `patch-selection.json` `cf0caf3f874912475bf237b29b9080e42c6ab8cebf347fad3d055c7006a568df`; `summary.json` `70f9404b6b35e375adc1ddd5ef35ae083c2caa6abb053565a6ad218050b38e29`; `raw/knob.json` `b4fb089bcc4c15dae7282b25194917c0f23346899f2df0577db42b7490b2bed6`; `raw/module.json` `6335a48ec06cd72b2b3262621d265842db08aff00630e4d66092841eedc8370d`; `raw/cable.json` `1b10d7e6a0a019969133a51681fa31a601e76410db24484d39c98a2440eb81ac`; `raw/telemetry.json` `1e417e73bb03de565cd1c0028396f8e83a46d1cf349ee39d2b809f179050f740`.
- **Runner:** GitHub Actions `1000040407`, Ubuntu 24.04 x64, Intel Xeon 6975P-C, Node 22.23.4, Chromium 131.0.6778.33. Captured Release CLI binary SHA-256 `fbefd9f6c1af5dc5adc25040e1cba391e85d6b5a5a99d3d672bbb43832e232ce`, native sidecar SHA-256 `876c895d33170050250a996b3337281530421b19ea2b7fafad314623460c5db8` (binary bytes not archived). Captured collector source SHA-256 `de944f71fcb8e1723fad7e2d274d0ca9c1ac5c4ffb198844b8816de0aebd1050`; metrics source SHA-256 `87845ce96b6e6a0f1d1584299abe882838b6c4899151689e2255885b9f916b41`.

## CPU method and complete measured order

Enumerated and hashed **all 24 original** bundled native-v2 JSON files in `apps/studio/patches/` (all original byte hashes, sizes and graph counts retained in `patch-selection.json` and `cpu-ranking.json`). Each was run once through actual built Release `wirescape_cli play <patch.json> --rate 48000 --block 128 --seconds 10 --output <distinct temporary WAV>` with **no `--confirm-*`, no `--pace`, no audio or MIDI device opened**. Each WAV was discarded. The CLI JSON times `app_engine_render_channels` only, excluding WAV encoding, and records `p50_us`, `p95_us`, `p99_us`, `worst_us`, `overruns`, `blocks`, rate, frames and offline status. Original complete stdout and exact arguments for every patch are preserved in `cpu-ranking.json`. All **24/24 measured**, **0 unavailable**, **0 overruns**; each reports 480,000 frames and 3,750 blocks. Refusals would be unavailable, not zero.

At 48 kHz/128, render period is **2,666.6667 µs**. Rank is descending **observed p95 render duration / period**, then p50, then lexical filename. Percent values below are ratios of the block render p95 to its period, **not operating-system CPU utilization**.

| Rank | Bundled native-v2 patch | p50 (µs) | p95 (µs) | p95 / period |
| ---: | --- | ---: | ---: | ---: |
| 1 | `scene-03-black-ice-choir.json` | 99.174 | 106.994 | 4.0123% |
| 2 | `chaos-01-ember-veil-pad.json` | 97.387 | 105.431 | 3.9537% |
| 3 | `scene-05-glass-cathedrals.json` | 89.234 | 96.810 | 3.6304% |
| 4 | `chaos-05-moonlit-drift-pad.json` | 85.430 | 93.200 | 3.4950% |
| 5 | `basics-06-chaos-keys.json` | 81.999 | 89.678 | 3.3629% |
| 6 | `chaos-02-wireglass-lead.json` | 76.027 | 83.773 | 3.1415% |
| 7 | `scene-01-hollow-chapel.json` | 67.779 | 75.939 | 2.8477% |
| 8 | `scene-04-vowel-apparitions.json` | 59.049 | 66.343 | 2.4879% |
| 9 | `scene-02-breathing-walls.json` | 53.695 | 63.262 | 2.3723% |
| 10 | `scene-06-dust-reactor.json` | 43.658 | 50.906 | 1.9090% |
| 11 | `scene-08-neon-elegy.json` | 43.739 | 48.948 | 1.8356% |
| 12 | `basics-07-macro-keys.json` | 43.069 | 48.540 | 1.8202% |
| 13 | `chaos-03-orbiting-iron-fx.json` | 41.852 | 46.398 | 1.7399% |
| 14 | `basics-03-echo-and-reverb.json` | 40.914 | 46.307 | 1.7365% |
| 15 | `basics-02-fm-filter-lfo.json` | 39.954 | 44.919 | 1.6845% |
| 16 | `chaos-04-radio-static-fx.json` | 36.520 | 41.700 | 1.5638% |
| 17 | `scene-07-witching-hour.json` | 34.602 | 39.498 | 1.4812% |
| 18 | `basics-05-random-melody.json` | 28.700 | 32.985 | 1.2369% |
| 19 | `quad-vca-01-lpg-plucks.json` | 27.484 | 29.532 | 1.1075% |
| 20 | `osc-out-01.json` | 17.742 | 18.683 | 0.7006% |
| 21 | `basics-04-sequencer-and-quantizer.json` | 17.044 | 17.728 | 0.6648% |
| 22 | `basics-01-first-tone.json` | 14.578 | 15.434 | 0.5788% |
| 23 | `basics-08-clocked-groove.json` | 14.575 | 15.230 | 0.5711% |
| 24 | `quad-vca-02-four-gate-mix.json` | 11.580 | 12.452 | 0.4669% |

**Observed idle-only winner:** `scene-03-black-ice-choir.json` (11 modules / 16 connections, original byte SHA-256 `efc1e0352bcdd082cfa11a07f9106e40f0706e23270c974a65ed2804f00348a3`), p50 **99.174 µs**, p95 **106.994 µs**, ratio **4.0123%** of one render period. Runner timing is one hosted observation per patch, not a statistically repeated benchmark. The earlier graph-size proxy winner `scene-06-dust-reactor.json` ranked **10th** in this idle-only CPU run, p95 **50.906 µs**. Input-gated graphs can be silent, so no claim is made about the highest *active/sounding* CPU cost.

## Re-captured actual Studio rAF and native ACK on measured winner

The same source checkout loaded `scene-03-black-ice-choir.json` into headless Studio with a real Release `wirescape-engine --null-audio` sidecar, stdio bridge and Chromium Playwright; no hardware audio/MIDI. Four original positive rAF interval arrays were independently sorted and their nearest-rank p50/p95/max recomputed. All four gestures completed, with no bridge transport or capture errors.

| Actual workload | Status | Positive rAF samples | p50 (ms) | p95 (ms) | Max (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| Knob drag (30-step) | measured | 41 | 16.7 | 16.7 | 16.8 |
| Module-header move (position changed) | measured | 40 | 16.7 | 16.7 | 16.8 |
| Compatible cable drawing (existing path) | measured | 40 | 16.7 | 16.7 | 16.8 |
| Native telemetry observation | measured | 84 | 16.7 | 16.7 | 16.8 |

The cable gesture traversed an existing compatible path; creation of a new edge is **not** asserted. Telemetry count was **40 actual native messages**. The knob issued **31 actual `setParam` commands** (`moduleId=2`, `paramId=shape_a`), and all **31/31** correlated native `ok=true` ACKs were independently matched by command ID against original `raw/knob.json`. Browser command-send → native-reply latency p50 **1.6 ms**, p95 **2.1 ms**, max **2.3 ms**; pointer-down → first native ACK **17.0 ms**, pointer-down → last native ACK **502.6 ms** (includes the full gesture duration). This is browser/stdio/sidecar reply latency, **not audio-output application latency**.

## Independent check and limitations

Original ZIP was downloaded, byte-hashed and all seven JSON members parsed. Independently checked 24 unique inventory names and byte hashes against archived inventory, per-row original CLI stdout JSON against recorded numeric fields, 48k/128/10s/3,750-block assertions, nonzero/ordered render timings, 0 unavailable, sorted CPU order and winner; four raw rAF arrays against summary nearest-rank percentiles; 31 unique actual command/reply IDs and send/reply percentiles and first/last pointer-down timing; real telemetry count and module position change. All passed. This is hosted headless Linux only, not Pi 5, GPU compositor, active-note cost, audible audio, physical device or a production target. The prior [2026-11-17 dust-reactor facts](ui_smoothness_2026-11-17.md) remain historical source-pinned observations; their source and patch are not relabelled.

Signed: gpt-builder2, 2026-11-20 ET.
