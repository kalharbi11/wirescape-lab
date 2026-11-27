<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Player performance facts: H-f1, H-f2, H-f3

Protocol only, 2026-11-26 ET. Source: Planner 0025 §§2.8–2.10, 3.2, 6.3. All rows **unmeasured**. No release or gate claim. The owner runs Pi tests; no agent access to audio/MIDI devices or LAN.

## Shared provenance and evidence
Record full lab and headless commit SHAs, executable hashes and engine capability versions, bundle/patch hashes, date/time ET, machine/CPU/RAM, OS/kernel, power/thermal conditions, audio backend, sample rate/block, UI/browser version and exact executed command/options. Keep raw timestamped samples, logs, exit status and configuration beside the summary; redact secrets and machine-specific private paths. Use a monotonic clock for intervals and a wall-clock timestamp for provenance. Keep Pi and hosted results distinct. Pin the actual commands after H-6/H-7 and H2 harnesses exist; do not infer CLI flags beyond the contracted ones. Missing data is unmeasured, not zero. Record failed/aborted attempts as such and keep their raw data.

## H-f1 — controller ingress to ACK
Contract §2.8: Pi 5, device-off `--null-audio --scripted-midi`, reference UI Play page, 100 CC/s across eight controllers for ten minutes. Hosted arm64 is diagnostic only. Require the controllerStream capability and the hardware map path through the Player; use eight actual mapped controls. If the scripted source cannot supply this workload, leave unmeasured pending P1-e test-source extension.

Capture event ingress `t` (integer steady-clock microseconds per §3.2), controller key/value, session and generation, corresponding setParam request ID, and receipt time of successful matching ACK using the same Linux monotonic clock. Correlate by the actual event driving each write, not by nearest timestamp. Compute added latency as ACK receipt monotonic_ns / 1000 minus ingress t. Retain sent, received, coalesced, unmapped, refused, missing ACK and stream-drop counts separately; do not count missing ACKs as fast samples. Record actual duration/rate/controller distribution and all valid latency samples; report count, p50/p95/p99 and max, specifying nearest-rank quantile convention. Compare p99 against 10 ms. Do not substitute engine-only or UI frame latency.

| Machine | Count | p99 | Loss accounting | Status |
|---|---|---|---|---|
| Pi 5 | unmeasured | unmeasured | unmeasured | Owner run and H-7 pending |
| Hosted arm64 | unmeasured | unmeasured | unmeasured | Diagnostic harness pending |

## H-f2 — kiosk cost
Contract §2.9: Pi, Play page updating at 30 Hz for 30 minutes. Use the same patch, engine settings, scripted activity, audio backend and environment for a UI-off baseline and UI-on run of equal duration. Record actual refresh rate, browser configuration and both dropout counts over the full windows. The UI-off run must exclude the kiosk process tree; Player and engine remain active.

Sample the full kiosk UI process tree throughout the window, including child processes spawned or replaced during the run. Record PID/start identity, cumulative user/system CPU time and RSS in bytes; derive CPU consumption as total tree CPU seconds / wall seconds × 100 (% of one core). Sum process RSS at each timestamp (shared pages may be counted multiple times; report this explicitly, do not replace RSS with PSS); report peak and sample interval and any missing samples. Compare UI-on dropouts to UI-off (equal), mean UI tree CPU to 25% of one core, peak tree RSS to 350 MB (record bytes and MB convention). Record any actual device conditions; only the owner runs on Pi.

| Row | Dropouts | Mean UI CPU | Peak UI RSS | Status |
|---|---|---|---|---|
| UI off | unmeasured | not applicable | not applicable | Baseline pending |
| UI on | unmeasured | unmeasured | unmeasured | H-6/owner run pending |

## H-f3 — PG10 long soaks
Contract PG10: H2 on Pi, 4–12 hours, flat RSS of Player and engine, flat CPU in silence, zero OSC drops, #326 closed. Use H2's actual pinned harness and workload; record exact duration, active/silent intervals, scripted OSC rates/routes, restart events, counters at baseline and throughout and at end. Owner only; no agent device runs. Track Player and engine RSS and CPU separately, identifying process restarts so a reset cannot disguise growth. Retain time series and report first/last/min/max and trend for steady silent windows, with units and intervals; record restarts, faults, dropouts and OSC counter deltas. Counter resets or unavailable counters prevent a zero-drop claim. Capture #326 closure evidence separately; closing that issue does not prove the soak passed. The contract says flat without a numeric slope allowance; report trends and leave the final interpretation to the acceptance authority, not a newly invented threshold.

| Machine / row | Duration | RSS trend | Silent CPU trend | OSC drops | #326 | Status |
|---|---|---|---|---|---|---|
| Pi / H2 | unmeasured | unmeasured | unmeasured | unmeasured | Open at protocol preparation | Owner run and H2 harness pending |

No threshold has been weakened or added. Proposed sampling and quantile conventions are protocol choices, not revisions of 0025. Actual command pins, raw samples and results will be appended only after they exist.

Signed: gpt-builder3, 2026-11-26
