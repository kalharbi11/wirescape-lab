<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Cortex-M7 compile-only module measurements

Measured commit: `0f6149282a9a8032f0403ea73260432e6972ce72`; date (New York): 2026-11-25.

Machine: hosted Linux x86_64; Cortex-M7 object target. ARM compiler: arm-none-eabi-g++ (Arm GNU Toolchain 14.2.Rel1, Build arm-14.52) 14.2.1 20241119, executable SHA-256 `55c6e7fe55c98c3360394ca313337d88b6d058aabeee4f0e1f41bd505e78b6ad`, archive SHA-256 `62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823`.

[Portability run 45718066852](https://github.com/kalharbi11/wirescape-lab/actions/runs/45718066852), [artifact 15071440548](https://github.com/kalharbi11/wirescape-lab/actions/runs/45718066852/artifacts/15071440548), ZIP SHA-256 `7a5540fd8d9fdcd1df4dec25d3706feb15fa01a898b27bd08e93341b8f733877`. Raw modules.json and s2.json, generated README.md and s2_symbols.md contain per-object symbol names and exact relocation section/offset. 

Flags: -mcpu=cortex-m7 -mthumb -mfloat-abi=hard -fno-exceptions -fno-rtti -Os, compile only; section bytes from arm-none-eabi-size -A. All 37 catalogue modules and SDK template compiled on both fpv5-d16 and fpv5-sp-d16 (76/76). All .bss = 0; .data = 0 except macro_oscillator (16 B on each FPU). Source paths are modules/<name>/module.cpp unless SDK path specified.

| Module | fpv5-d16 .text B | fpv5-sp-d16 .text B | fpv5-d16 double/soft-float relocation symbols and source functions |
|---|---:|---:|---|
| adsr | 5694 | 5766 | __aeabi_ul2f — Adsr::process_default_gate and process lambdas |
| blend | 3264 | 3380 | none shown |
| chaos_lite | 6972 | 7056 | none shown |
| chord | 3108 | 3132 | none shown |
| clock | 4348 | 4674 | none shown |
| cv_to_notes | 2378 | 2410 | none shown |
| delay | 10306 | 11324 | __aeabi_ul2d — Delay::clock_tick; cos, sin — process_transition and process_settled (Tail and Block); exp — update_tone, update_tone_settled, SDK prepare lambda; pow — update_tone and update_tone_settled |
| function_envelope | 3352 | 3516 | __aeabi_ul2d, expm1 — FunctionEnvelope::process |
| groove | 9888 | 10074 | __aeabi_d2lz — Sequencer::frames<true>; __aeabi_ul2d — frames<true> and process |
| host_keyboard | 9134 | 9162 | none shown |
| ladder | 3554 | 4124 | tan — Ladder::process |
| lfo | 2054 | 2214 | fmod, sin — Lfo::process |
| macro_oscillator | 6128 | 6420 | __aeabi_d2ulz, __aeabi_ul2d — MacroOscillator::process; cos, sin — RateConverter::prepare |
| midi_cc_to_cv | 2956 | 3152 | exp — SDK Module<CcToCv>::prepare lambda |
| midi_in | 2158 | 2186 | none shown |
| midi_to_cv | 13098 | 13162 | none shown |
| mixer | 2832 | 3018 | none shown |
| monitor | 3578 | 3584 | __aeabi_d2ulz — Monitor::permit and process; __aeabi_ul2d — permit |
| noise | 2516 | 2656 | none shown |
| notes_to_cv | 5988 | 6008 | none shown |
| osc_in | 8994 | 9192 | __aeabi_d2ulz — OscIn::process lambda; exp — SDK Module<OscIn>::prepare lambda |
| osc_out | 2294 | 2322 | none shown |
| output | 1384 | 1408 | none shown |
| poly_merge | 1302 | 1322 | none shown |
| poly_split | 1242 | 1298 | none shown |
| quad_vca | 3540 | 3696 | exp, pow, tan — SDK Module<QuadVca>::prepare lambda |
| quantizer | 3476 | 3520 | none shown |
| resonator | 3742 | 3798 | none shown |
| reverb | 6972 | 7356 | exp — Reverb::refresh |
| scale_offset | 2776 | 2974 | none shown |
| slew | 2560 | 2784 | none shown |
| spectral | 9750 | 10086 | cos, log, sin — Spectral::prepare; exp — vocoder_layout and vocoder |
| vca | 2442 | 2470 | none shown |
| vcf | 2350 | 2678 | tan — Vcf::process |
| vco | 2652 | 2856 | pow — Vco::process lambda and Block::split specialization; sin — Vco::process lambda |
| sdk/examples/random_source | 3424 | 3660 | exp — RandomSource::coefficient |
| sdk/examples/step_sequencer | 3410 | 3438 | none shown |
| sdk/template | 1446 | 1474 | not in S2 catalogue symbol probe |

Relocation names above are grouped by source function; full mangled sections and byte offsets are in s2_symbols.md in the pinned ZIP. No linked firmware or timing measurement. See [module memory](../module_memory.md) for DSP sizes and host state/memory matrix.
