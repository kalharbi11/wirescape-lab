<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-g1 Linux L0 advisory — 2026-11-21

- Assignment: #305; proposal 0019 §3, OB r2.4a.
- Intended base: main 23443691b4950b4747ade943d7d8602d281938fc; branch task/305-ob-g1-osc-soak.
- Platform: available Linux Python sandbox; **no native wirescape-engine executable or accessible Git checkout**. GitHub clone failed with "Could not resolve host: github.com".
- Attempted Linux L0 profile osc-gates/still: **BLOCKED / NOT RUN**. The missing-executable path produced a blocked report with first check engine_missing, not 60s of OSC performance data. No L0 latency baseline, delivered-packet counts, Pi facts, or meaningful status on engine health can be inferred.
- Local staging/prototype checks (not release/source-pinned endurance evidence): Python syntax compile; nine stdlib unit tests passed; fault injection engine_exit, missing_echo, stuck_gate passed. The same tests and fault checks are committed under bench/io for exact-head Linux execution.
- Advisory parallel runner task for lead: on an authorized Linux device-off runner, build or provide the exact-PR-head engine, execute Python unit tests and bench/io/soak.py --self-test, then the full 60s osc-gates/still L0 (and osc-heavy/still). Publish the generated report.json/report.md and runner status without treating any failure as a merge veto.
- Separate telemetry gap requiring a parallel authorized product task: status.osc.routes has dropped but no malformed/truncated counters, and MIDI queue counters await OB-g2. The bench harness flags missing observability; no product paths were touched in OB-g1.
- No Pi device, hardware MIDI, audio device, LAN, runner dispatch, repository workflow change or #275 work.
- Signed: gpt-builder5, 2026-11-21 EST.
