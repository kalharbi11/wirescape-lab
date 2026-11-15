<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR — headless vocal-tract synthesizer (C++17)

GUTTUR is a **standalone C++17 static-library synth** with an optional **Wirescape ABI 2 adapter**. No browser, GUI, JUCE, audio device, MIDI device, socket or external DSP dependency is required.

This translation uses the provided `guttur-worklet.js` as a **sound/design reference**, not an immutable correctness oracle. Improvements that alter behavior are identified in `DEVIATIONS.md`. The C++ audio engine is newly translated; **the earlier Throat v.2 DSP was not copied**.

## What is included

- LF glottal pulse synthesis (17 Rd tables × 8 mip levels, FFT-built before rendering), flow tables and harmonic magnitudes.
- Closure-time vocal decisions: jitter/shimmer, growl, creak, fry, register breaks; gated breath/rasp and flutter.
- 34-section vowel/tract model with chain-matrix (M22) resonance lookup, a precomputed 9×5×5×4 grid, and ten parallel state-variable filters per throat.
- Internally allocated note groups with leader/followers, voice stealing, per-throat positioning and variation.
- Stereo inter-ear delay/head shadow, room early reflections and eight-line FDN, low-mid guard, anti-aliased drive, and 2.5 ms look-ahead limiter.
- **16 simultaneous throat DSP slots**, **up to 16 tracked note IDs**, **up to 8 throats requested per note**. The 16-slot **global throat budget** is binding: if group requests exceed it, older voices are stolen. Therefore 16 independent notes are simultaneously audible only with a one-throat-per-note setting.
- 37 controllable synth parameters and 11 vocal texture presets (including the **chant voice timbre**, which is *not* the chant sequencer).
- One internally mixed stereo pair; left and right are separate module output ports, each with **one channel**. The 16 throats are not 16 Wirescape cable channels.
- Deterministic reset and seeded per-throat random generation, versioned patch/settings state, fixed-sized work buffers and no allocations during `process`.

**Intentionally excluded:** chant/crowd scene sequencer, gestures, keyframe automation, rhythmic scheduler, multi-layer patches, clap/stamp percussion, browser/HTML/CSS/graphics. Playing a note still creates a variable-size *group of vocal throats*, because that is part of the synthesis.

## Build standalone

Prerequisites: CMake 3.16+, C++17 compiler. No libraries to install.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/guttur_offline --output-dir renders_cpp
./build/guttur_benchmark 3000
```

On Windows use the corresponding `.exe` paths; on multi-config generators add `--config Release` to CMake and CTest commands.

Quick use (compile and link against `libguttur_core.a`):

```cpp
#include "guttur/engine.h"
#include <array>

guttur::Engine synth;
if (!synth.prepare(48000.0, 128, 17)) return 1; // control thread
synth.loadPreset("clean");
synth.setParam(guttur::Param::throats, 3);
synth.noteOn(123, 48, 0.8);                       // audio owner, sample timing controlled by caller
std::array<float, 128> left{}, right{};
synth.process(left.data(), right.data(), 128);   // realtime callback
synth.noteOff(123);
// synth.latencyFrames() returns 120 frames at 48 kHz.
```

`prepare`, `loadState`, and destruction are quiescent/control operations. Note events should be delivered by the **audio/render owner**; `noteOn`, `noteOff` and `process` must not be called concurrently. `setParam` uses atomic targets, safe for an independent parameter writer. `telemetry()` inspects render-owned state and must not be read concurrently with `process()`; Wirescape deliberately does not export it as a cross-thread ABI callback.

Calling `prepare()` multiple times on a host-owned arena consumes another allocation; create a fresh module/arena when rebuilding the graph. The standalone allocator path frees its own allocation.

### Public API

See `include/guttur/engine.h`. Primary functions: `prepare(rate,maxBlock,seed,allocator,user)`, `reset`, `process(L,R,n)`, `noteOn(id,midi,velocity)`, `noteOff(id)`, `allOff`, `setParam`, `loadPreset`, `saveState`/`loadState`, `telemetry`, and `latencyFrames`.

- `note_id` is an opaque nonzero signed 64-bit identifier.
- `midi` is 0–127; velocity is clamped to 0–1.
- `setParam` values are clamped to the ranges in `include/guttur/parameters.h`. Parameter targets are read at the internal 128-frame control clock; state-dependent changes retain that timing across arbitrary host blocks.
- `process` always emits stereo float audio. The limiter bounds the final signal to approximately ±0.891 (−1 dBFS). Look-ahead is `round(0.0025 * sampleRate)` samples.
- `saveState` serializes patch settings, seed and preset trim (not active notes, filters, FDN history or UI). `loadState` resets running DSP state after validation.

## Wirescape integration (read-only packaged adapter)

The repository has **not** been modified. The following operations are for the recipient to perform in a separate checkout, after choosing the licence (see `NOTICE.txt`):

1. Copy this folder into `native/modules2/guttur/` in `kalharbi11/wirescape`.
2. In `native/engine2/CMakeLists.txt`, next to the other module subdirectories, add `add_subdirectory(../modules2/guttur guttur)`.
3. In `native/control/module_catalog.h`, add `#include "../modules2/guttur/dsp.h"`.
4. In `native/control/module_catalog.inc`, add `WS_APP_MODULE(guttur::abi2::Module)`.
5. Add the contents of `wirescape_catalogue_entry.json` as one object in `apps/studio/public/catalogue-presentation.json` (`modules` array); then run `python tools/gen_ui_catalogue.py` to regenerate `apps/studio/public/wirescape_modules.json`. **Never manually edit the generated file.** This is registration metadata, not a custom UI.
6. Update `docs/PATCH_DESIGNER_GUIDE.md` with note routing, 16-throat global budget, one-channel stereo pair, parameter ranges, and a working wiring example.
7. Run `python tools/dev.py build --headless`, `ctest --test-dir build/native -R '^abi2_guttur_tests$' --output-on-failure`, `python tools/dev.py test`, and catalogue drift checks. Check Linux ARM64, Windows, sanitizers, and actual Pi 5 CPU results before merge.

`dsp.h`, `module.cpp`, `module.json`, `wirescape_catalogue_entry.json` and the Wirescape branch of `CMakeLists.txt` are the adapter. `ws2_guttur` links `guttur_core`, and the CMake integration also links it to `wirescape_catalog_dependencies` because the built-in module catalogue instantiates the descriptor out of line.

Module port contract:

| ID | Kind | Meaning |
|---|---|---|
| `notes` | event input | Wirescape note-on, off, choke with sample offsets |
| `left` | audio output | Internally summed left signal, 1 channel, stereo pair `stereo` |
| `right` | audio output | Internally summed right signal, 1 channel, stereo pair `stereo` |

`dsp.h` maps `source_id`, `note_id`, MIDI channel and key into stable private 64-bit handles. MIDI note keys become Hz within the core. Input parameters are sampled at the core's 128-frame clock.

**No engine, ABI, protocol or sidecar changes should be necessary.** The complete in-tree Wirescape build has **not** been run in this external build environment; see `TEST_RESULTS.md` for verified and unverified steps.

## Layout

`include/guttur` public API; `src/` DSP; `apps/` offline WAV and CPU tools; `tests/` standalone and ABI 2 tests; `reference/` original uploaded JS and captured constants; `tools/` self-contained reference renderer and PCM comparison; `dsp.h`/`module.cpp` ABI 2 adapter. `DESIGN.md` covers architecture, `DEVIATIONS.md` covers differences, `NOTICE.txt` covers provenance, `TEST_RESULTS.md` records test evidence.
