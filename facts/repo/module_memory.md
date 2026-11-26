<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Module memory measurements

- Measured commit: `0f6149282a9a8032f0403ea73260432e6972ce72`
- Date (New York): 2026-11-25
- Machine: x86_64 hosted Linux; Cortex-M7 object target
- Host compiler: g++ (Ubuntu 15.2.0-16ubuntu1) 15.2.0; executable SHA-256 `fd8730a05275b1f8a149b7df3e38ef67cf7a21ec817a706206955cd2929b900b`
- ARM compiler: Arm GNU Toolchain 14.2.Rel1 (Build arm-14.52), 14.2.1 20241119; executable SHA-256 `55c6e7fe55c98c3360394ca313337d88b6d058aabeee4f0e1f41bd505e78b6ad`
- ARM archive SHA-256: `62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823`
- [Portability run 45718066852](https://github.com/kalharbi11/wirescape-lab/actions/runs/45718066852), [raw artifact 15071440548](https://github.com/kalharbi11/wirescape-lab/actions/runs/45718066852/artifacts/15071440548), ZIP SHA-256 `7a5540fd8d9fdcd1df4dec25d3706feb15fa01a898b27bd08e93341b8f733877`

DSP sizeof excludes SDK wrapper. Host memory hook uses block 256, seed 1, empty config except Chord LE instance tag 1. State measured after prepare/reset with capped counting writer. Each four-value cell orders 48 kHz/1 ch, 48 kHz/8 ch, 96 kHz/1 ch, 96 kHz/8 ch. A single value applies to all four. Status 0 = OK; 2 = CAPACITY; 3 = UNSUPPORTED (probe does not prepare/save stateless modules). Cap = 1,048,576 B. Non-success writes are not saved-state sizes. Source is modules/<name>/module.cpp unless SDK path specified.

| Module | DSP x64 B | DSP M7 B | LARGE B | Alignment B | Prepare status | Save status | Written B | Cap |
|---|---:|---:|---|---:|---|---|---|---|
| adsr | 912 | 912 | 0 | 32 | 0 | 0 | 912 | under/equal |
| blend | 72 | 72 | 0 | 32 | 0 | 0 | 52 | under/equal |
| chaos_lite | 1888 | 1696 | 74560,596480,148864,1190912 | 32 | 0 | 0 | 836 | under/equal |
| chord | 8984 | 8024 | 0 | 32 | 0 | 0 | 4 | under/equal |
| clock | 1416 | 1416 | 0 | 32 | 0 | 0 | 1412 | under/equal |
| cv_to_notes | 204 | 204 | 0 | 32 | 0 | 0 | 4 | under/equal |
| delay | 184 | 168 | 768192,768192,1536192,1536192 | 32 | 0 | 0,0,2,2 | 768208,768208,0,0 | under,under,over,over |
| function_envelope | 1416 | 1416 | 0 | 32 | 0 | 0 | 1284 | under/equal |
| groove | 12856 | 12856 | 0 | 32 | 0 | 0 | 20 | under/equal |
| host_keyboard | 14192 | 14000 | 0 | 32 | 0 | 0 | 20 | under/equal |
| ladder | 2568 | 2568 | 0 | 32 | 0 | 0 | 2564 | under/equal |
| lfo | 128 | 128 | 0 | 32 | 3 | 3 | 0 | n/a |
| macro_oscillator | 1512 | 1448 | 16384,131072,67008,189088 | 32 | 0 | 0 | 4 | under/equal |
| midi_cc_to_cv | 7632 | 7632 | 0 | 32 | 0 | 0 | 4 | under/equal |
| midi_in | 25104 | 22032 | 0 | 32 | 0 | 0 | 4 | under/equal |
| midi_to_cv | 44472 | 41400 | 0 | 32 | 0 | 0 | 4 | under/equal |
| mixer | 1280 | 1280 | 0 | 32 | 0 | 0 | 1284 | under/equal |
| monitor | 36888 | 36888 | 131128 | 32 | 0 | 0 | 4 | under/equal |
| noise | 768 | 768 | 0 | 32 | 0 | 0 | 708 | under/equal |
| notes_to_cv | 12696 | 12696 | 0 | 32 | 0 | 0 | 4 | under/equal |
| osc_in | 96192 | 96176 | 0 | 32 | 0 | 0 | 4 | under/equal |
| osc_out | 1384 | 1368 | 0 | 32 | 0 | 0 | 4 | under/equal |
| output | 1 | 1 | 0 | 32 | 0 | 0 | 4 | under/equal |
| poly_merge | 4 | 4 | 0 | 32 | 3 | 3 | 0 | n/a |
| poly_split | 1 | 1 | 0 | 32 | 3 | 3 | 0 | n/a |
| quad_vca | 3092 | 3092 | 0 | 32 | 3 | 3 | 0 | n/a |
| quantizer | 904 | 904 | 0 | 32 | 3 | 3 | 0 | n/a |
| resonator | 800 | 736 | 28880,231040,57680,461440 | 32 | 0 | 0 | 4 | under/equal |
| reverb | 384 | 328 | 260624 | 32 | 0 | 0 | 4 | under/equal |
| scale_offset | 1280 | 1280 | 0 | 32 | 0 | 0 | 1284 | under/equal |
| slew | 520 | 520 | 0 | 32 | 0 | 0 | 516 | under/equal |
| spectral | 1976 | 1816 | 344180,344180,688244,688244 | 64 | 0 | 0 | 52 | under/equal |
| vca | 16 | 8 | 0 | 32 | 0 | 0 | 4 | under/equal |
| vcf | 712 | 712 | 0 | 32 | 3 | 3 | 0 | n/a |
| vco | 216 | 216 | 0 | 32 | 0 | 0 | 268 | under/equal |
| sdk/examples/random_source | 536 | 536 | 0 | 32 | 0 | 0 | 516 | under/equal |
| sdk/examples/step_sequencer | 48 | 48 | 0 | 32 | 0 | 0 | 48 | under/equal |

Delay at 96 kHz: formula payload 1,536,208 B; preflight refuses (CAPACITY, zero bytes written) at both channel counts. At 48 kHz, both writes are 768,208 B. Raw four-row matrices and relocation details are in the pinned artifact (s2.json, module_memory.md, s2_symbols.md).
