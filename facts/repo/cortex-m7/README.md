<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Cortex-M7 module compile-only facts

Commit: 9d04963daf664355c3596d63f2832ed582cf3e3f
Date (New York): 2026-11-15
Compiler: arm-none-eabi-g++ (Arm GNU Toolchain 14.2.Rel1 (Build arm-14.52)) 14.2.1 20241119
Archive SHA-256: 62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823
Target flags: -mcpu=cortex-m7 -mthumb -mfloat-abi=hard -fno-exceptions -fno-rtti -Os

Catalog modules: 34. SDK template: 1. Compilations: 70.
Section sizes are sums of .text.*, .data.* and .bss.* entries reported by arm-none-eabi-size -A.

| Source | FPU | Compiles | .text B | .data B | .bss B | Double/softfloat refs | Float libm refs | Heap refs | Static guard refs |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| native/modules2/adsr/module.cpp | fpv5-d16 | yes | 2564 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/adsr/module.cpp | fpv5-sp-d16 | yes | 2612 | 0 | 0 | 6 | 0 | 0 | 0 |
| native/modules2/blend/module.cpp | fpv5-d16 | yes | 3264 | 0 | 0 | 0 | 2 | 0 | 0 |
| native/modules2/blend/module.cpp | fpv5-sp-d16 | yes | 3380 | 0 | 0 | 9 | 2 | 0 | 0 |
| native/modules2/chaos_lite/module.cpp | fpv5-d16 | yes | 6640 | 0 | 0 | 0 | 4 | 0 | 0 |
| native/modules2/chaos_lite/module.cpp | fpv5-sp-d16 | yes | 6724 | 0 | 0 | 9 | 4 | 0 | 0 |
| native/modules2/chord/module.cpp | fpv5-d16 | yes | 3108 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/chord/module.cpp | fpv5-sp-d16 | yes | 3132 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/clock/module.cpp | fpv5-d16 | yes | 3738 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/clock/module.cpp | fpv5-sp-d16 | yes | 4002 | 0 | 0 | 12 | 0 | 0 | 0 |
| native/modules2/delay/module.cpp | fpv5-d16 | yes | 4270 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/delay/module.cpp | fpv5-sp-d16 | yes | 4746 | 0 | 0 | 18 | 0 | 0 | 0 |
| native/modules2/function_envelope/module.cpp | fpv5-d16 | yes | 3352 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/modules2/function_envelope/module.cpp | fpv5-sp-d16 | yes | 3516 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/groove/module.cpp | fpv5-d16 | yes | 7900 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/groove/module.cpp | fpv5-sp-d16 | yes | 7974 | 0 | 0 | 10 | 0 | 0 | 0 |
| native/modules2/host_keyboard/module.cpp | fpv5-d16 | yes | 4474 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/host_keyboard/module.cpp | fpv5-sp-d16 | yes | 4486 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/ladder/module.cpp | fpv5-d16 | yes | 3410 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/modules2/ladder/module.cpp | fpv5-sp-d16 | yes | 3808 | 0 | 0 | 12 | 0 | 0 | 0 |
| native/modules2/lfo/module.cpp | fpv5-d16 | yes | 2054 | 0 | 0 | 2 | 0 | 0 | 0 |
| native/modules2/lfo/module.cpp | fpv5-sp-d16 | yes | 2214 | 0 | 0 | 14 | 0 | 0 | 0 |
| native/modules2/macro_oscillator/module.cpp | fpv5-d16 | yes | 3822 | 16 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/macro_oscillator/module.cpp | fpv5-sp-d16 | yes | 3838 | 16 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/midi_cc_to_cv/module.cpp | fpv5-d16 | yes | 2956 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/modules2/midi_cc_to_cv/module.cpp | fpv5-sp-d16 | yes | 3152 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/midi_in/module.cpp | fpv5-d16 | yes | 2158 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/midi_in/module.cpp | fpv5-sp-d16 | yes | 2186 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/midi_to_cv/module.cpp | fpv5-d16 | yes | 7216 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/midi_to_cv/module.cpp | fpv5-sp-d16 | yes | 7260 | 0 | 0 | 6 | 0 | 0 | 0 |
| native/modules2/mixer/module.cpp | fpv5-d16 | yes | 2832 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/mixer/module.cpp | fpv5-sp-d16 | yes | 3018 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/monitor/module.cpp | fpv5-d16 | yes | 3578 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/modules2/monitor/module.cpp | fpv5-sp-d16 | yes | 3584 | 0 | 0 | 6 | 0 | 0 | 0 |
| native/modules2/noise/module.cpp | fpv5-d16 | yes | 2516 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/noise/module.cpp | fpv5-sp-d16 | yes | 2656 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/notes_to_cv/module.cpp | fpv5-d16 | yes | 3292 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/notes_to_cv/module.cpp | fpv5-sp-d16 | yes | 3312 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/osc_in/module.cpp | fpv5-d16 | yes | 8852 | 0 | 0 | 2 | 0 | 0 | 0 |
| native/modules2/osc_in/module.cpp | fpv5-sp-d16 | yes | 9056 | 0 | 0 | 14 | 0 | 0 | 0 |
| native/modules2/osc_out/module.cpp | fpv5-d16 | yes | 2294 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/osc_out/module.cpp | fpv5-sp-d16 | yes | 2322 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/output/module.cpp | fpv5-d16 | yes | 1384 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/output/module.cpp | fpv5-sp-d16 | yes | 1408 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/quad_vca/module.cpp | fpv5-d16 | yes | 2962 | 0 | 0 | 3 | 0 | 0 | 0 |
| native/modules2/quad_vca/module.cpp | fpv5-sp-d16 | yes | 3098 | 0 | 0 | 10 | 0 | 0 | 0 |
| native/modules2/quantizer/module.cpp | fpv5-d16 | yes | 3476 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/quantizer/module.cpp | fpv5-sp-d16 | yes | 3520 | 0 | 0 | 16 | 0 | 0 | 0 |
| native/modules2/resonator/module.cpp | fpv5-d16 | yes | 3742 | 0 | 0 | 0 | 2 | 0 | 0 |
| native/modules2/resonator/module.cpp | fpv5-sp-d16 | yes | 3798 | 0 | 0 | 9 | 2 | 0 | 0 |
| native/modules2/reverb/module.cpp | fpv5-d16 | yes | 4776 | 0 | 0 | 1 | 2 | 0 | 0 |
| native/modules2/reverb/module.cpp | fpv5-sp-d16 | yes | 5068 | 0 | 0 | 13 | 2 | 0 | 0 |
| native/modules2/scale_offset/module.cpp | fpv5-d16 | yes | 2776 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/scale_offset/module.cpp | fpv5-sp-d16 | yes | 2974 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/slew/module.cpp | fpv5-d16 | yes | 2560 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/slew/module.cpp | fpv5-sp-d16 | yes | 2784 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/spectral/module.cpp | fpv5-d16 | yes | 9750 | 0 | 0 | 4 | 2 | 0 | 0 |
| native/modules2/spectral/module.cpp | fpv5-sp-d16 | yes | 10086 | 0 | 0 | 13 | 2 | 0 | 0 |
| native/modules2/vca/module.cpp | fpv5-d16 | yes | 2356 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/modules2/vca/module.cpp | fpv5-sp-d16 | yes | 2384 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/modules2/vcf/module.cpp | fpv5-d16 | yes | 2326 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/modules2/vcf/module.cpp | fpv5-sp-d16 | yes | 2638 | 0 | 0 | 11 | 0 | 0 | 0 |
| native/modules2/vco/module.cpp | fpv5-d16 | yes | 2046 | 0 | 0 | 2 | 0 | 0 | 0 |
| native/modules2/vco/module.cpp | fpv5-sp-d16 | yes | 2210 | 0 | 0 | 13 | 0 | 0 | 0 |
| native/sdk/examples/random_source/module.cpp | fpv5-d16 | yes | 3424 | 0 | 0 | 1 | 0 | 0 | 0 |
| native/sdk/examples/random_source/module.cpp | fpv5-sp-d16 | yes | 3660 | 0 | 0 | 12 | 0 | 0 | 0 |
| native/sdk/examples/step_sequencer/module.cpp | fpv5-d16 | yes | 3410 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/sdk/examples/step_sequencer/module.cpp | fpv5-sp-d16 | yes | 3438 | 0 | 0 | 4 | 0 | 0 | 0 |
| native/sdk/template/module.cpp | fpv5-d16 | yes | 1446 | 0 | 0 | 0 | 0 | 0 | 0 |
| native/sdk/template/module.cpp | fpv5-sp-d16 | yes | 1474 | 0 | 0 | 4 | 0 | 0 | 0 |

## First compilation errors

None (70 of 70 compilations succeeded).

Full undefined symbol names are recorded in modules.json.
