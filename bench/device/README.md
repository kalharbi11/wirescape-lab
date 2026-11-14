<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device stress harness

The owner-gated \`run.py\` expands timed JSON scenarios, speaks the sidecar v0 NDJSON protocol, logs each line with a monotonic timestamp, measures acknowledgement latency, optionally records output to FLAC, and generates DSP analysis plus Markdown report.

**No hardware is opened by dry runs, unit tests or CI.** Owner runs require explicit \`--confirm-audio\`, and scripted external MIDI also requires \`--confirm-midi\`. The dry run uses the real sidecar with \`--null-audio\` if a binary is available; otherwise it labels the evidence as a protocol simulation.

See [OWNER_RUN.md](OWNER_RUN.md) for Windows/Pi installation, 15- and 60-minute commands, recording caveats, and result transfer. Scenario families: basics, chaos, scene, groove, all-parameter extreme, and a ten-minute endurance mix. Applicable parameter and note events are exported as exact \`wirescape_render --script\` inputs.
