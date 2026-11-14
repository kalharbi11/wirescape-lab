<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Bench

Two tracks. Both write results that `facts/` summarises.

- **`offline/`**: devices off; runs in CI and on any machine. Exact, repeatable numbers: module/engine CPU,
  instruction counts, offline renders of every bundled patch and stress script, DSP analysis of those renders.
- **`device/`**: owner-run, real audio and MIDI on the Windows laptop and the Pi 5. Drives `wirescape-engine`
  over its stdin protocol with scripted scenarios (extreme parameter changes, live edits, patch switches,
  panic, MIDI note storms), records status/telemetry and the audio output, then analyses it. Refuses to
  start without `--confirm-audio` (and `--confirm-midi` for MIDI scenarios). A `--dry-run` uses the null
  sink and fake MIDI so CI can test the harness itself.

The same scenario files run in both tracks: the offline render is the reference, the device recording shows
what the real device path changed (dropouts, clicks, latency).

**Results layout:** `results/<machine>/<YYYY-MM-DD>-<sha7>/` with `manifest.json` (machine, OS, device,
rate, block, commit), `events.ndjson`, `analysis.json` and `report.md`. Recordings (FLAC) stay out of git:
zip the run folder and attach it to a GitHub release named `bench-<date>`. Commit only files under 1 MB.
