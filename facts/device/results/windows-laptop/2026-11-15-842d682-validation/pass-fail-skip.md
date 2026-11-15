# Pass/fail/skip log

- PASS: owner git pull fast-forwarded main to 842d682.
- PASS: Windows toolchain preflight.
- PASS: Release engine, Studio, Desktop, and capture-helper builds.
- PASS: four native protocol/recovery checks.
- PASS: isolated Electron and silent launcher smoke.
- PASS: bench dependency consistency and 15 device-harness unit tests (observed console output; standalone unit-test transcript not saved).
- PASS: real-engine null-audio scenario all; 23874 acknowledgements, zero refusals, no runner/protocol errors, normal exit.
- PASS: loopMIDI port Wirescape Bench created and visually verified.
- PASS: owner device enumeration identified WASAPI Realtek laptop speakers at a 48000 Hz default.
- FAIL: initial quiet speaker check; owner heard silence, despite zero reported xruns/faults.
- PASS: louder diagnostic speaker check; owner confirmed audio. The seven pasted CPU snapshots ranged from 0.365625 to 1.03688 percent, each with zero xruns/faults; this is not an all-time maximum.
- SKIP: 15-minute real-device quick stress run; not performed in this session.
- SKIP: process-loopback recording, live signal analysis, click/silence/stuck-note review for a timed run; no live recording exists.
