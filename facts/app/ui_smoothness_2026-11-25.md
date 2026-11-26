<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-f1 pre-candidate UI smoothness — 2026-11-25 ET

Status: measured hosted diagnostic, **pre-candidate** under A87 (#578), not final acceptance: OB-d owner listening disposition pending. Source is the measured checkout, not this facts commit.

## Provenance

- [A87 dispatch](https://github.com/kalharbi11/wirescape-lab/issues/578#issuecomment-7176972645); [workflow run 45717349754](https://github.com/kalharbi11/wirescape-lab/actions/runs/45717349754), job 139566697305, workflow_dispatch, success including known-answer regressions, capture and upload. Exact captured SHA `6b3789bdba166faa607b3657e3e1efb2e31f8da1` verified in captured_sha.txt, ranking and summary.
- GitHub Actions runner 1000054764, ubuntu24 Linux x64, AMD EPYC 9V74 80-Core Processor, Node v22.23.5, Chromium 131.0.6778.33. Native Release null-audio stdio sidecar, local Vite preview; no physical audio or MIDI devices.
- [Artifact 15070143074](https://github.com/kalharbi11/wirescape-lab/actions/runs/45717349754/artifacts/15070143074), 11,579 bytes, uploaded 2026-11-25 22:59:44 UTC, expires 2026-12-09 22:59:43 UTC. ZIP SHA-256 independently computed, matches API: `79803e9b45d90759adcf8b7ca71162d50cc557d8dea42019cf4bf196b46389ef`.
- Captured CLI SHA-256 `f50fc7b3deca0de391d0090f59b0d5ab73768fea14c64ea7c378bc446c28b24d`; sidecar `387bc79bd5783b7c6f9805dc18f08a69469327b2033458668f55d0ab256f3d45` (binaries not archived). Collector `de944f71fcb8e1723fad7e2d274d0ca9c1ac5c4ffb198844b8816de0aebd1050`; metrics `87845ce96b6e6a0f1d1584299abe882838b6c4899151689e2255885b9f916b41`; both match [2026-11-20 facts](ui_cpu_rank_2026-11-20.md).

## CPU ranking and selection

One default-state offline 10 s render per patch, 48 kHz/128 frames, period 2666.6667 µs; 24/24 measured, 0 unavailable. Rank descending p95/period, then p50, then filename. Full ranking and CLI observations archived. Active/sounding CPU not resolved.

| Rank | Bundled patch | p50 µs | p95 µs | p95/period |
|---:|---|---:|---:|---:|
| 1 | chaos-01-ember-veil-pad.json | 109.295 | 118.388 | 4.43955% |
| 2 | scene-05-glass-cathedrals.json | 110.146 | 118.058 | 4.42718% |
| 3 | scene-03-black-ice-choir.json | 109.366 | 117.587 | 4.40951% |

The unchanged selector chose **Ember Veil Pad**, 12 modules, 16 connections, patch SHA-256 `903d22c6742b4803a91e630c69b6d14e03fde65aa1eb687cf1c5ac64469625e0`. Black Ice Choir, the prior r2.3 winner, is rank 3 at this pin. Its UI rows were **not measured** on this run; no Black Ice Choir UI claim is made. Different hosted CPUs and small rank differences are not a regression or a device comparison.

## Captured winner UI rows

Recomputed nearest-rank p50/p95/max from the four raw frame arrays; all agree with summary.json. All four gestures completed, no raw transport or action errors. Compare to unchanged r2.3 per-row p95 ≤17.5 ms and max ≤33.4 ms; numbers displayed to 0.1 ms, comparison on raw values.

| Action (Ember Veil Pad) | Frames | p50 ms | p95 ms | max ms | p95 target | max target |
|---|---:|---:|---:|---:|---|---|
| Knob drag | 41 | 16.7 | 16.8 | 16.8 | met | met |
| Module move | 40 | 16.7 | 16.7 | 16.8 | met | met |
| Cable draw | 42 | 16.7 | 16.7 | 16.7 | met | met |
| Telemetry | 84 | 16.7 | 16.7 | 16.8 | met | met |

Module position changed; cable gesture was on an existing bundled edge (new edge not claimed); telemetry row recorded 40 notifications. Knob: 31 distinct setParam sends (module 2, shape_a) and 31 correlated successful native replies, no missing/refused ACKs; raw send→receive times p50 2.1 ms, p95 2.7 ms, max 2.8 ms. **Native send→ACK p95 ≤5 ms: met**. Drag start→first ACK 17.1 ms; drag start→last ACK 502.0 ms (includes the drag). Other actions do not issue setParam. These are bridge/IPC latencies, not audio application latency. Summary native stderr contains two setup commit path=d5 lines (gen 1,2), not classified as transport failures.

All measured winner targets met. No measured row fails r2.3; no OB-f2 fix row is implied by these numbers. Final candidate capture/owner observations are not established here; headless Chromium rAF is vsync-capped and does not measure physical Pi compositor, audio or stutter.

## Raw member SHA-256 (independently computed)

| Member | SHA-256 |
|---|---|
| captured_sha.txt | 9b4537eaad0eec2fb775e130405e351b07ba3e545b6e769eefc1c4999f91dff1 |
| cpu-ranking.json | 711de6f564ea6bfecd6692f7c0cb4ae448af37d9e289b4cde26366c11ccdc1ed |
| patch-selection.json | 66ee178bf9278de50a1f71a2a47e2b484ff3654261f3533c0553ad6f086d4c2c |
| summary.json | bf9025af3cd349d3cc1f21351d49f5e8fd2d5d2ad367429ddbd2f670b5e1bfee |
| raw/knob.json | 5531468ed6a16b7f8d73c8e1d56de48e04c50e6ede0ef48cfc24ec221a9c1188 |
| raw/module.json | 7dd10708f58216fdf309068e643c611479fcfcacfffd513cb82ba5f0ef0e853b |
| raw/cable.json | 64d3111f99ad1bb684818863cc7596e4897dbf217df0a1163babc699f294539a |
| raw/telemetry.json | a079c5c76bb615c273526afd0e11427d0153a6f2554f7ffba1f9a88a5e2abd4b |

Signed: gpt-builder3, 2026-11-25.
