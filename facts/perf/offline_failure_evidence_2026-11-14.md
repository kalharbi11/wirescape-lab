<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Offline soak and Chord probe failure evidence

Source lab commit: `7d3842dc783915cf31aaf43bca508ebdcefb8a48`; source run: [GitHub Actions 43675998104](https://github.com/kalharbi11/wirescape-lab/actions/runs/43675998104), raw artifact `facts-raw-linux-x64` (ID `14146489517`); measurement date ET: 2026-11-14. Source machine: Linux x64, Intel Xeon 6975P-C, Linux 7.0.0-1016-aws x86_64, GitHub-hosted. Source measurement: 48000 Hz, blocks 64/128/256 frames, 1 second per patch/block. Audio, MIDI devices and LAN sockets not accessed.

Inspection date ET: 2026-11-15; lab main commit inspected: `84bd0fe947aeba096b81039d973f1c60cf6dd4dc`. Method: read `l4/full/perf/patch_soak.json` and `module_cpu.json` from the raw artifact, group by status/patch, inspect native code. The sibling JSON file records the grouped patch names and verbatim failure diagnostics.

| Source measurement | Count | Reported diagnostic |
| --- | ---: | --- |
| Patch-soak rows | 72 | 24 patches × 3 block sizes |
| Patch-soak measured rows | 36 | `status=measured` |
| Patch-soak unavailable rows | 36 | 12 patch filenames × 3 block sizes; exit code 1, `wirescape_soak: graph setup/render failed` |
| Chord direct CPU-probe unavailable rows | 6 | 3 block sizes × 2 channel counts; exit code 2, `module_cpu_probe: create/prepare failed` |

All 12 unavailable patch filenames contain a `host.keyboard` module. The native `wirescape_soak` invocation has no external note-script input; `native/engine2/tests/soak.cpp` checks allocations, faults and whether `peak>0` together at the end of a run. The emitted diagnostic does not identify which conjunct failed. `bench/offline/run_all.py` contains a separate original-graph preflight and an explicitly labelled, derived `essentials.clock → example.step_sequencer` note-source path, without changing the bundled patch files.

The direct Chord CPU probe constructs `ws2_config` with no binary config (`native/engine2/tests/module_cpu_probe.cpp`). Chord's `prepare` returns false unless config has exactly four bytes (`native/modules2/chord/dsp.h:54-56`); the document adapter provides them from the instance ID (`native/document/runtime_module_config.h:35-38`). Existing direct-probe CPU rows remain unavailable pending a probe that supplies the native config; no time values are imputed.
