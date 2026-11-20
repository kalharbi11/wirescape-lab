# OB-f1 — headless Studio UI smoothness and native parameter-ACK facts (2026-11-17 ET)

**Status:** measured on actual hosted Linux x64 GitHub Actions; advisory, device-off, no pass/fail smoothness thresholds assigned. These are *observations*, not Pi or production audio claims.

## Provenance and source pin

- Issue: [#209](https://github.com/kalharbi11/wirescape-lab/issues/209); existing draft [PR #216](https://github.com/kalharbi11/wirescape-lab/pull/216).
- **Measurement source commit:** `df0e02c57547687d244f326720a33492a6d465dc` (the exact head checked out by the hosted workflow before this facts-only documentation commit).
- **Hosted evidence:** [OB-f1 advisory run 44210368907](https://github.com/kalharbi11/wirescape-lab/actions/runs/44210368907), attempt 1, job 134486864110, **success**; build, actual Release `--null-audio` native engine, pure selector/metric/ACK regressions, four UI workloads, and artifact upload each passed.
- **Raw artifact:** [`ob-f1-ui-facts-44210368907`, ID 14385414109](https://github.com/kalharbi11/wirescape-lab/actions/runs/44210368907/artifacts/14385414109), 6,417-byte ZIP, GitHub Actions retention 7 days. Independently downloaded ZIP SHA-256: `45828bae4276d01aed037bd7fbe052c4485379de41159162ec9423f7a48d2f46`; matches GitHub's uploaded-artifact digest.
- **Runtime:** GitHub Actions Ubuntu 24.04 Linux x64 (`ubuntu24`); runner `1000038347`; Intel Xeon 6975P-C; Node `v22.23.4`; headless Chromium `131.0.6778.33`; Vite preview on `127.0.0.1`; real native sidecar built Release and run `--null-audio` over stdio. No hardware audio or MIDI opened; no Pi, LAN, physical audio, or hardware GPU performance measurement.
- **Captured native executable SHA-256:** `a883cfc4004ea9fe66ead03197ac67ae1884a7f4ef7d2cff11877ea9f0c1876c` (reported by the hosted collector; the executable itself is not bundled in the artifact).
- **Source hashes independently recomputed against the pinned GitHub commit:** `bench/ui/ob_f1_capture.cjs` SHA-256 `4677f9623986ed3eba3ae3607ce1ada9f70a0725799e6347855c92454569b9e5`; `bench/ui/ob_f1_metrics.cjs` SHA-256 `45126eb46c830a71d41e377bc9fbf69d78bd1048280a5fb3336094d0d93cae3c`.

## Bundled patch selection

Selected `apps/studio/patches/scene-06-dust-reactor.json`: **18 modules, 23 connections**, original patch-byte SHA-256 `910325886fb7d48f0c4f97640efdb90bab210bed0ed793676a7a4da94cfeda28` (independently recomputed against the pinned repository file). The archived `patch-selection.json` inventories and hashes **24** native-v2 bundled patches. Deterministic descending **module count**, then descending **connection count**, then lexical filename selected the first row. This is a recorded *graph-complexity proxy* for the heaviest bundled graph, **not a measured CPU-load ranking**. No bundled patch was modified.

## Measured browser requestAnimationFrame intervals

Intervals are positive, original `requestAnimationFrame` deltas in milliseconds from actual Playwright mouse gestures or the native-telemetry observation window. Percentiles are **nearest rank** (`ceil(p × n / 100)` after ascending sort), independently recomputed from each original `raw/*.json` array. Values below are rounded to 0.1 ms for readability; unrounded values are retained in the artifact.

| Workload | Result | rAF samples | p50 (ms) | p95 (ms) | max (ms) | Actual gesture / observation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Knob drag | measured | 41 | 16.7 | 16.7 | 16.8 | Visible dial, 30-step mouse drag; 31 native parameter ACKs |
| Module move | measured | 40 | 16.7 | 16.7 | 16.8 | Visible module header, 30-step drag; before/after UI positions differ |
| Cable drawing | measured | 40 | 16.7 | 16.8 | 16.8 | 30-step drag between visible, originally compatible ports `port-1-output-audio` → `port-3-input-a` |
| Telemetry | measured | 84 | 16.7 | 16.7 | 16.8 | 75-frame additional observation window; **40 actual native telemetry messages** received |

Cable drawing used an *existing* bundled signal path for compatible endpoints; a newly created graph edge is **not claimed**. The 40 native telemetry messages are observations, not a measured telemetry throughput rate. The original captures report zero bridge transport errors, completed gestures, and no capture errors.

## Actual native parameter-ACK observations

The knob gesture issued **31 `setParam` commands** (`moduleId=1`, `paramId=frequency`) through the real Studio `RealEngine` bridge and native Release `--null-audio` sidecar. All **31/31** were matched by unique command ID to actual native `ok: true` replies (`gen=2`), with browser-monotonic timestamps. These are not mocked, estimated, or inferred from visual movement.

| Measure | Observation |
| --- | ---: |
| Correlated command/reply count | 31 / 31 |
| `send(setParam)` → native reply delivered, p50 | 1.8 ms |
| `send(setParam)` → native reply delivered, p95 | 3.4 ms |
| `send(setParam)` → native reply delivered, max | 3.4 ms |
| Pointer-down → first correlated native ACK | 18.1 ms |
| Pointer-down → last correlated native ACK | 501.8 ms |

The first three latencies use each command's browser `performance.now()` send timestamp and matching native-reply delivery timestamp, so they **include bridge transport and scheduling**, not audio-application or speaker-output latency. Pointer-down-to-last-ACK spans the *whole 30-step gesture* and must not be interpreted as a single command's response time. Parameter-ACK timing is **not applicable** to module move, cable drawing, or telemetry; no fabricated zero is used.

## Original artifact inventory and independently verified member hashes

| ZIP member | SHA-256 |
| --- | --- |
| `patch-selection.json` | `17a52d592d6484d2d1f3f301b7af803b24cff83134c988bd58f0a9ec1e8a525f` |
| `raw/knob.json` | `24cae9dc543122f2612e3bc97fdea42d2a63e16a1168e179596ee0adfd40ee56` |
| `raw/module.json` | `a7eca4bcf4841c81f9eed7d93d7bcc13f18d82a53385e07cf3929ba1eccf363b` |
| `raw/cable.json` | `be927c5744490941229168b165f5aa31172d5a5cdc9664ae819f5bdf2ba07f97` |
| `raw/telemetry.json` | `6c59dbf76aa383b8a55d160c8c798d2ad3a3cb33735602f1e8c06357405b1bc3` |
| `summary.json` | `bd5ae39264e36ed472370e9a3aada5ee17a68de14b938aec43bf3bf2ee813c4f` |

All six members were independently opened and parsed. The four raw gesture records have `completed=true`, `gesture_completed=true`, no `error`, and no transport errors. Independently recomputed nearest-rank frame statistics and every correlated `setParam` latency match the archived summary; all four summary rows are `measured`. Native stderr records only `commit path=d5 gen=1` and `commit path=d5 gen=2`, not an engine fault.

## Scope, caveats, and prior failed captures

This is one **hosted, headless, device-off** sample at one exact source revision. VSync-like ~16.7 ms rAF pacing in Linux Chromium is not a guarantee of compositor smoothness, input-to-photon latency, Pi performance, physical audio timing, or production reliability. No statistical confidence interval, cross-run variance, f2 target, or acceptance threshold is asserted. Architect/lead owns subsequent targets and review.

Two previous automatic advisory captures failed and are **not** merged into these facts: [run 44172138940](https://github.com/kalharbi11/wirescape-lab/actions/runs/44172138940) captured raw gestures but misclassified them due to `completed` vs `gesture_completed` bookkeeping; [run 44208010770](https://github.com/kalharbi11/wirescape-lab/actions/runs/44208010770) timed out during startup because the simulated bridge failed to replay initial native `hello` to Studio's second subscriber. Both were addressed in the two authorized, existing-PR `bench/ui` correction rounds; no third correction, manual rerun, or repeated unchanged capture was used. The successful exact-source hosted run above is the **sole** accepted numeric observation set.

**Disposition:** OB-f1 facts are recorded for neutral review under issue #209; PR #216 remains draft/unmerged, with no change to shared `ci.yml`, production Studio/native sources, devices, thresholds, or release gates.

Signed: **gpt-builder2 — 2026-11-17 ET**.
