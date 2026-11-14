<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Same-machine audio-tool comparison

`measure.py` samples a selected program's process tree (10 Hz CPU and RSS), captures owner-observed xruns/native CPU meter values, and writes neutral metrics with provenance. `--dry-run` runs solely against a synthetic sleeping process. Owner hardware runs require `--confirm-audio` and an existing target PID.

`generate_scaling.py` produces capacity-checked Wirescape patch-v2 scaling cases. The supplied three Wirescape JSON patches represent the mono, 8-voice MIDI and 8-voice with FX cases. [patches.md](patches.md) describes matching topology for Cardinal, Rack 2 Free and Pure Data; [OWNER_RUN.md](OWNER_RUN.md) contains OS-specific installation, commands and collection protocol.

Recordings stay outside git. The `--record` backends reuse the owner-only recorder in device harness PR #13 **once merged**; optional existing-file `--audio-file` and `--tone-file` inputs work independently. A spectral nonharmonic floor is an alias proxy, not a stand-alone alias measurement.
