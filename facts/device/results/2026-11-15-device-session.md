<!-- SPDX-License-Identifier: GPL-3.0-only -->
**Runbook:** v1, owner-authorized MIDI naming fix and clean-worktree P6 rerun   **Commits:** Pi ab7ce36; Windows 156af4b   **PR:** results PR (see PR description)

| Run | Machine | Buffer | Ran (min) | Exit | Engine CPU max % | Dropouts | Longest silence ms | Notes |
|---|---|---|---:|---|---:|---|---|---|
| P1 | pi5 | 256 | 0.27 | 1 | 0.0 reported | 0 reported | unavailable | Failed: engine refused setParam: busy Event queue full. No signal metrics. |
| P2 | pi5 | 128 | skipped | — | — | — | — | Not run this session. |
| P3 | pi5 | 128 | skipped | — | — | — | — | Scene and chaos not run this session. |
| P4 | pi5 | 64 | skipped | — | — | — | — | Not run this session. |
| P5 | pi5 | 128 benchmark | not timed | 0, owner transcript | — | — | — | 30,000 blocks per configuration; no devices. |
| P6 | pi5 | devices off | smoke test 0.05; builds not timed | 0 | — | — | — | Five stages passed, one expected test; functional display only. |
| W1 | windows-laptop | initially 256 | 15 planned; 14.98 recorded | 0 | 81.4556 | 25 engine; 18 signal candidates | 1116.083 candidate | MME Realtek speakers; 154 detected clicks, no refused commands. Scenario changes buffers internally. |
| W2 | windows-laptop | 128 | skipped | — | — | — | — | Not run this session. |

**GUTTR (Pi):** 1 throat p50/p95/worst 44.594/46.483/73.873 microseconds; 16 throats 346.249/352.620/440.047 microseconds. Period 2666.667 microseconds.

**Pi health:** max temperature 51.0 C; flags 0x0; maximum used memory 1772 MB as printed by free -m. Logger includes idle time after P1, so these are session-log peaks.

**App memory (Pi):** observed Electron total peak 444.39 MiB; engine 231.47 MiB. Two-second process-name RSS sampling caught the engine in only one sample; includes matching processes and potentially shared pages. Not sustained app-memory evidence. Full memory log retained.

**What the owner heard:** first W1 setup attempt: "no"; second W1 setup attempt: "NO"; P1: "no"; completed W1: "no" (unqualified response to a question about glitches, silence, distortion or volume; not interpreted as a clean-listening assessment).

**Loopback cable available:** Pi not checked; laptop not checked, per owner.

**Failures:**

```text
Pi initial system-Python dependency install:
error: externally-managed-environment
Resolved by owner using the existing bench virtual environment.

Pi P1:
device harness: engine refused setParam: busy Event queue full

Pi initial P6:
Pi app smoke: blocked
['The source must be a clean immutable Git checkout at the PR head']
Resolved by owner running the same commit in a separate clean worktree and placing logger files under ignored build_reports.

Windows W1 initial attempt:
device harness: unknown port 'Wirescape Bench'
Windows MIDI service restart by owner made ports visible.

Windows W1 second attempt:
device harness: MIDI output is not uniquely visible to engine; verify --midi-port
Resolved with separate --midi-port and --engine-midi-port; code fix PR #50.

Pi P1 pack:
pack.py: error: incomplete run; resolve failures before packing
```

Failure outputs above contain all relevant emitted diagnostic lines (fewer than 40 per failed run); local report paths omitted for privacy. Initial sandbox Python/SDK access denials were resolved by permitted execution outside the sandbox.

**Large files:** completed W1 ZIP uploaded to draft release bench-2026-11-15. Its 4.7 MB analysis.json exceeds the 1 MB small-file limit and is included only in the ZIP. P1 packer refused the incomplete run; original partial files remain in bench/device/results-p1-full-256/pi5/2026-11-15-ab7ce36 on pi5. No recordings, ZIPs or events.ndjson are committed.

Signed: gpt-helper, 2026-11-15
