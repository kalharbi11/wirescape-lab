<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner-supplied golden patches

Add owner-provided native patch-v2 JSON files here after reviewing them for
private file paths, personal names and device-specific IDs. The directory is
empty by default. `bench/golden/render.py` discovers each `*.json` file here,
in addition to every bundled patch under `apps/studio/patches/`.

Patches requiring notes receive the same C4 host.keyboard on/off script as the
bundled-patch offline benchmark. No MIDI or audio device is opened, and rendered
audio files are held in temporary directories and deleted.
