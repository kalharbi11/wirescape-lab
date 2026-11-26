<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-h3 A93 hosted-runner switch witness — 2026-11-26

Test source: `f1a772ab210cd8f7c0263f94d9ecfe456fa3920b`, base `7037b708144eaf41978f87e377490c46ef01a6f4`.
Scope: issue #602, draft PR #610. Null audio, localhost OSC 9000/9001, fixed 48 kHz / 256-frame blocks, alternating distinct patches, held keyboard note, 200 Hz offered OSC load. No physical audio/MIDI devices or LAN.

## Exact-head 200-switch CI evidence

[Lab CI 45796618735](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796618735) completed successfully. Mandatory `abi2_sidecar_patch_switch_tests` passed in [linux-x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796618735/job/139828867209) and [linux-arm64](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796618735/job/139828867056). The [x64 sanitizer job](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796618735/job/139828867043) also passed this test, with leak detection enabled. All 99 ABI2 sanitizer tests passed. Both-architecture sanitizer qualification is separate.

## Optional 1000-switch diagnostic

[Hosted dev-run 45796635538](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796635538), exact source head above. Command: `ctest --test-dir build/native -C OBH3Long -R ^ob_h3_patch_switch_1000$ -V`. Both runs executed one test and passed all 1000 switches, including correlated successful ACK, fresh ingress route and unique post-ACK OSC echo within 50 ms, held-note release, and exact-zero fade witness.

| Hosted runner | Switches | Captured gap p50 (ms) | Captured gap max (ms) | VmRSS at 100 (KiB) | VmRSS at 1000 (KiB) | ACK p50 (ms) | ACK max (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ubuntu-latest / linux-x64 | 1000 | 6.020833 | 11.354167 | 38260 | 38680 | 23.991716 | 30.098809 |
| ubuntu-24.04-arm / linux-arm64 | 1000 | 6.020833 | 6.020833 | 36980 | 38652 | 24.078098 | 28.817435 |

Raw emitted JSON retained below (source: [ARM64 job](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796635538/job/139828981870), [x64 job](https://github.com/kalharbi11/wirescape-lab/actions/runs/45796635538/job/139828981856), [signed-thread diagnostic result](https://github.com/kalharbi11/wirescape-lab/pull/610#issuecomment-7188779757)).

ARM64:
```json
{"gap_definition": "exact-zero captured samples; excludes stopped wall-clock time", "gap_ms_max": 6.020833333333333, "gap_ms_p50": 6.020833333333333, "load_ack_ms_max": 28.817435000007663, "load_ack_ms_p50": 24.078098000003934, "rss_kib": {"100": 36980, "1000": 38652}, "status": "passed", "switches": 1000}
```

x64:
```json
{"gap_definition": "exact-zero captured samples; excludes stopped wall-clock time", "gap_ms_max": 11.354166666666666, "gap_ms_p50": 6.020833333333333, "load_ack_ms_max": 30.09880899998052, "load_ack_ms_p50": 23.99171599999761, "rss_kib": {"100": 38260, "1000": 38680}, "status": "passed", "switches": 1000}
```

These are test-specific observations, not performance baseline facts: hosted timing is diagnostic only under DEV_RUN, so the record is kept with the test rather than in `facts/`. Gap is exact-zero captured sample duration, not elapsed wall-clock silence across a stopped sink. ACK duration is reported separately, not substituted for acoustic gap. RSS is two Linux process observations, not a leak proof; no threshold is asserted. Leak detection and the exact-head mandatory CI gate remain separate. No product change or waiver.

Signed: gpt-builder5, 2026-11-26

## Post-A98 integrated run (not a passing gate)

Source head `c01eb188d31e7a969e6242287690fa4e4f619465`, base `83cc53c36d5cb2586ce7c7616640740f857ceeb6`. [Lab CI 45903786839](https://github.com/kalharbi11/wirescape-lab/actions/runs/45903786839): Linux native jobs passed, but [x64 sanitizer job](https://github.com/kalharbi11/wirescape-lab/actions/runs/45903786839/job/140195656568) failed 200-switch capture analysis at switch 54, `gate/note retained after swap` (99/100 sanitizer tests passed). No ASan/LSan memory report identified in that failure. Do not treat this as the earlier #631 egress extra-rise defect or as an accepted gate.

[1000-switch hosted diagnostic 45903825009](https://github.com/kalharbi11/wirescape-lab/actions/runs/45903825009) passed both architectures. Raw JSON:
- ARM64: `{"gap_definition":"exact-zero captured samples; excludes stopped wall-clock time","gap_ms_max":6.020833333333333,"gap_ms_p50":6.020833333333333,"load_ack_ms_max":30.47541799969622,"load_ack_ms_p50":24.081236500023806,"rss_kib":{"100":37264,"1000":38560},"status":"passed","switches":1000}`
- x64: `{"gap_definition":"exact-zero captured samples; excludes stopped wall-clock time","gap_ms_max":6.020833333333333,"gap_ms_p50":6.020833333333333,"load_ack_ms_max":30.043782000007013,"load_ack_ms_p50":23.79406549999885,"rss_kib":{"100":38384,"1000":38500},"status":"passed","switches":1000}`

These data do not override the failed mandatory sanitizer gate. Added failure-only capture diagnostics: noteOn/loadGraph R7 marks including the next intended noteOn, block range, nonzero sample positions, per-block nonzero counts and min/max. The existing exact-zero assertion, capture bracket, input load, 50 ms sentinel and all other gates are unchanged. Possible next-command overlap is a hypothesis, not a confirmed cause.

Signed: gpt-builder5, 2026-11-26
