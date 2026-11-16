<!-- SPDX-License-Identifier: GPL-3.0-only -->
**Runbook:** v1 with owner-authorized explicit audio route   **Commit:** ab7ce36 (Pi); 156af4b (prior Windows runs)   **PR:** see PR description

The original default-route Pi runs failed before opening an audio device. Saved audio status showed `Sample format not supported`, `state=reconnecting`, and no selected device; the harness later stopped on `busy Event queue full`. Those failures remain in PR #73. These separately authorized reruns use the already-enumerated `--device 'ALSA|pulse'`, reaching the desktop audio route to the USB output. No Pi source code or persistent system settings were changed. All five rerun manifests report completed=true, engine exit 0 and no warnings.

| Run | Machine | Buffer | Ran (min) | Exit | Engine CPU max % | Dropouts | Longest silence ms | Notes |
|---|---|---|---:|---|---:|---|---|---|
| P1 | pi5 | 256 initially | 59.990 recorded | 0 | 26.1884 | 0 engine; 10 signal candidates | 1110.729 candidate | 276 click candidates |
| P2 | pi5 | 128 initially | 59.988 recorded | 0 | 26.9766 | 0 engine; 10 signal candidates | 1114.771 candidate | 270 click candidates |
| P3 scene | pi5 | 128 initially | 0.583 recorded | 0 | 13.0222 | 0 engine; 0 signal candidates | 0 candidate | 24 click candidates |
| P3 chaos | pi5 | 128 initially | 0.583 recorded | 0 | 14.5000 | 0 engine; 0 signal candidates | 0 candidate | 0 click candidates |
| P4 | pi5 | 64 initially | 0.583 recorded | 0 | 3.2208 | 0 engine; 0 signal candidates | 0 candidate | 0 click candidates |
| P5 | pi5 | 128 benchmark | not timed | 0, owner transcript | — | — | — | Completed previously; original results PR #73. |
| P6 | pi5 | devices off | smoke 0.05; builds not timed | 0 | — | — | — | Passed previously in clean worktree; original results PR #73. |
| W1 | windows-laptop | 256 initially | 15 planned | 0 | 81.4556 | 25 engine; 18 signal candidates | 1116.083 candidate | Completed previously; PR #73. |
| W2 | windows-laptop | 128 initially | 15 planned | 0 | 63.9750 | 0 engine; 22 signal candidates | 387.979 candidate | Completed previously; PR #73. |

Actual planned durations: P1/P2 3600 seconds each; scene/chaos/basics 35 seconds each. The scenario files differ from the runbook's approximate short-run estimates. All scenarios may change buffer sizes internally, so these results do not establish sustained operation at each initial buffer size. This tests the ALSA pulse desktop route, not direct exclusive access to the hardware.

**GUTTR (Pi):** prior 1 throat p50/p95/worst 44.594/46.483/73.873 microseconds; 16 throats 346.249/352.620/440.047 microseconds, 2666.667 microsecond period. Not rerun.

**Pi health:** rerun log maximum temperature 59.3 C; throttling flags 0x0; maximum used memory 1862 MB as printed by free -m. Log spans P1/P2/scene/chaos, not the earlier short P4 probe.

**App memory (Pi):** previous smoke sampled peaks: Electron 444.39 MiB; engine 231.47 MiB. Only one two-second sample caught the engine running, so these are observed process-name RSS peaks, not sustained memory measurements. Not rerun.

**What the owner heard:** P4 retry: "pi is working i heard a sound". During P1 the owner reported: "one of the patches on the pi makes a pop sound at the beggining its like when u plugin an aux. it happens with cheap synth apps or sometimes amateur html apps i think its sounds familiar. it might be the pi problem, just if that seems smth that is could be an actual familiar error then make a note of that, i might be wrong.". Full post-run assessments for P1/P2/scene/chaos were requested and were not yet supplied at filing time. Prior W1/W2 replies were "no" (unqualified).

The patch-start pop has an unconfirmed cause and no identified patch or timestamp. It is not attributed to the Pi hardware. Recorded full runs reached a sample peak of 1.0, and detector click/dropout candidates remain; successful process completion and zero engine dropouts do not establish clean audible playback. No sound-specific code repair is claimed.

**Loopback cable available:** Pi not checked; laptop not checked, per owner. P7 round-trip latency remains unavailable because the runbook has no measuring tool.

**Failures:** no rerun harness failures or manifest warnings. Original failures remain preserved separately in PR #73.

**Large files:** five uniquely named pi5-2026-11-15-ab7ce36-p*-pulse.zip archives uploaded to draft release bench-2026-11-15. Full analysis files over 1 MB remain in the ZIPs; small derived summaries are committed here. No recordings, archives or events.ndjson are committed. No merges requested.

Signed: gpt-helper, 2026-11-15
