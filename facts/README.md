<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Facts

Neutral data for the review. **No opinions, no "should", no ranking.**

Every entry has: what was measured, the number (with unit), how (command or script + options), the lab
commit (`sha7`), the machine (CPU, OS, audio device if any, rate, block) and the date (ET). Raw data goes
next to its summary as JSON/CSV. Quotes from other projects carry the URL and date read.

| Folder | Holds |
|---|---|
| `repo/` | code size, complexity, long lines, target/include graphs, residue scans, binary sizes |
| `perf/` | offline engine and module CPU, instruction counts, soak results |
| `dsp/` | offline sound measurements: aliasing, THD, filter response, DC, denormals, zipper, clicks |
| `device/` | owner-run results on the laptop and the Pi (real audio/MIDI): dropouts, CPU, latency, recordings' analysis |
| `app/` | startup, memory, UI frame times, protocol latency |
| `tests/` | test inventory, runtimes, CI durations and failures |
| `compare/` | other tools: features, SDK shape, export pipelines, published numbers |
