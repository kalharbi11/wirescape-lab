# Windows validation and speaker-check report

Date: 2026-11-15 America/New_York
Commit: 842d68225fb44c167b8714cb4cfc36455138273a

Release build, silent app checks, and the real-engine device-off bench passed. The owner subsequently confirmed audible sound through the laptop speakers using a louder local diagnostic patch. The 15-minute real-device quick scenario has NOT been performed. This package must not be treated as a completed hardware stress benchmark.

## Evidence

- device-off/: complete manifest, report, analysis, protocol stream, stderr, settings, and exported scripts for the null-audio scenario-all check.
- setup/: local setup summary, native-test log, and saved Electron smoke status. The checkout path in the copied log was replaced with [checkout].
- sound-check/: local diagnostic patch and two OFFLINE WAV renders. These are generated reference audio, not recordings of the speaker output.
- owner-observations.json: the owner's listening statements and explicit unmeasured fields.
- review.json: scope, device-off outcomes, and offline signal metrics.
- doc-problems.md and pass-fail-skip.md: session findings and outcomes.

The initial comparison patch was very quiet. Raising gain only in a separate diagnostic copy resolved the owner's reported silence. The reference benchmark patch and repository source remain unchanged. The exact cause of the initial inaudibility beyond the quiet signal was not isolated.

The capture helper is built to target the explicit sidecar PID and its process tree. No process-loopback capture was started. Detector counts and real-device stress CPU/dropout results are unavailable. Zero xruns printed by the speaker check do not establish a clean 15-minute run.
