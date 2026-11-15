<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR → Wirescape implementation review

## Conclusion

Wirescape can accommodate a native throat synthesizer within its existing ABI2 module model. Port GUTTUR's model to C++17; no JavaScript runtime, HTML importer or AudioWorklet compatibility layer is needed. The DSP is conventional numeric code and should translate reasonably directly. A production port is more than syntax conversion: voice ownership, sample timing, memory, modulation and reset need deliberate rebuilding.

Scope: preparation and review only, no native implementation and no repository publication. Wirescape evidence is the local checkout at `44da1e4a235e606ebecd5bd6232f908d4df9b97f`; this is not a claim about today's remote HEAD. Owner context: the prototype was influenced somewhat by Pink Trombone. That is design context, not verified code provenance or a claim of equivalent physical modelling.

## What the model actually contains

`guttur-core.js`: `lfParams`, `lfSample`, `buildPulseTables` create band-limited LF glottal pulse tables and harmonic data. `areaFunction`, `tubeResonances`, `buildTubeGrid`, `gridLookup` build/interpolate tube-derived resonances. `Singer.closure` chooses pulse period, shape, amplitude, growl doubling, fry gaps and irregularity each glottal cycle. `Singer.control` computes envelopes, pitch wander/tremor/vibrato, throat coefficients and spatial targets. `Singer.render` generates source plus aspiration, runs a parallel resonator bank with ramped SVF coefficients, high-pass, drive and stereo placement. `Room` adds early reflections and an eight-line FDN. `Engine.block` mixes and applies tone, adaptive low-mid reduction, DC blocking and a look-ahead limiter.

This is a source-plus-resonator voice model, not a live articulatory waveguide solver or a speech/text engine. No mouth graphics or keyboard logic are necessary to preserve its sound. Internal modulation is part of the model: keep it even though external modulation is available in Wirescape.

## Recommended first native module

Build one integrated `GUTTUR` instrument first, with a proposed ID such as `guttur.throat` (reserve it before shipping). Keep fold source, throat filter, envelopes and group traits together for initial sound parity. Later, optionally expose a glottal source, throat resonator accepting external audio, group/humanisation helper, and separate space/bus processor. Splitting those now would introduce new contracts before the combined reference is stable.

Distinguish **host voices** from **throats within a voice**. One host channel is one independent note, which may contain 1–8 sub-throats. Wirescape's 1–16 channel limit does not mean 16 throats total. A naive 16-note × 8-throat implementation would run 128 singers plus effects, far above this prototype's default 24-slot budget. Choose and document a total singer budget, allocation fallback and maximum note count; do not silently multiply the work. Keep whole-note steals coherent and preserve note-off ownership.

Suggested initial contract (proposal, not a shipped descriptor): polyphonic pitch and gate signals, a note-event input, optional velocity CV, stereo `left`/`right` outputs, and the continuous controls listed in PARAMETERS.md. Define CV precedence: a connected gate owns articulation, matching the existing ADSR convention; otherwise note events own articulation. Pitch uses Wirescape's 1/oct signal with 0 = C4; convert explicitly to Hz. Gate uses its Schmitt convention (>0.5 on, <0.25 off). Velocity is 0..1. Never treat L/R as two poly channels.

Resolve the output topology before implementation. Recommended: dry/placed L/R per host voice, with shared room and output protection downstream as a separate companion effect/subpatch. This preserves clean poly routing and avoids a separate FDN per note. For a parity-first integrated stereo-mix version, expose mono-channel L/R outputs, explicitly sum the internal voices and own note allocation there; document that it is an internally polyphonic instrument with a mixed output. Shared adaptive EQ and limiting are nonlinear: applying them independently per voice will not reproduce the original shared bus.

## What can carry over and what must change

| Part | Keep | Native rebuild |
|---|---|---|
| LF source and pulse tables | Shape equations, harmonic selection, closure model | Contiguous bounded tables; build before audio starts; immutable ownership; verify aliasing and precision |
| Tube-derived resonances | Area profiles, roots, lookup interpolation, residue weighting | Prepare tables outside callback; document memory and preparation cost; stable coefficients over all rates/controls |
| Singer | Source, aspiration, growl/fry/roughness, shape and spatial math | Fixed per-host-voice/sub-throat state; no lazy arrays/objects; clear lifecycle |
| Intrinsic modulation | Coupled jitter, per-singer random traits, tremor, wander, vibrato, flutter | Absolute sample/cycle clocks and deterministic per-instance/per-voice seeds |
| Envelope and articulation | Pressure onset style, release, scoop, glide | Sample-offset starts/stops; gate/note precedence and explicit legato/retrigger semantics |
| Group | Leader/followers, looseness, size spread, panning and gain law | Fixed group pool, defined total budget and topology-change behavior |
| Space | Distance, azimuth, early reflections/FDN if sound parity matters | Rate-sized rings; explicit shared-versus-per-voice policy; optional separate module |
| Tone and protection | Drive, body/air shelves, anti-mud behavior and DC block for reference parity | Explicit bus placement and latency reporting; optional separate output effect |
| Presets/calibration | All 11 textures and calibration constants | Versioned preset/state schema; finite/range validation; distinguish timbre from presets' level trims |
| Telemetry | Optional diagnostic meaning | Bounded snapshots consumed off audio thread; no JSON, formatting or postMessage in process |

## Concrete problems in the reference to fix during porting

1. **Realtime allocation:** `allocate`, `noteOn`, `finishSteal`, lazy arrays in `expectedPower`/`Singer.control`, parameter objects, filtering lists and telemetry allocate. Replace with fixed-capacity pools and `Setup::alloc` in prepare. `buildShared()` can do expensive table generation in the constructor: never execute this from the audio callback. Current module-global mutable `SHARED` should become immutable prepared resources with a safe lifetime.
2. **Unbounded note bookkeeping:** `notes` is not routinely pruned when singers finish; allocation also filters it. Use the existing fixed-capacity Wirescape allocator where applicable, plus a bounded sub-throat pool. Original `noteOff(midi)` releases every held note with that key and cannot distinguish duplicate keys, sources or note IDs. Native delivery must honor source/note/channel identity, sustain and choke.
3. **Timing depends on call boundaries:** `process()` chunks each call afresh; `block()` updates control state and checks starts/stops at its boundaries. Host event splits or different block sizes change these boundaries. Replace with an absolute sample counter/control phase and offset-aware rendering. This is required for Wirescape's variable-frame contract; the extraction has not fixed it.
4. **Parameter transport:** `setParams()` accepts unchecked values, stores globals and recalculates room/EQ. Native continuous controls should read smoothed per-voice `b.param()` signals; structural `throats` must be stepped with bounded transitions. Decide a supported rate per control. Do not mark expensive shape controls audio-rate capable until tested. `style` is captured at start in the current model; define whether changing it mid-note should affect the onset or only the next note. `throats` currently affects new notes; it does not resize active groups.
5. **Scratch/rate assumptions:** scratch arrays are 512 samples, room rings 8192, spatial ITD 128 with a 60-sample clamp, limiter rings 1024. Recalculate capacities and delays for the supported maximum rate/block; fixed masks can wrap long room delays at high rates. This is a sonic correctness issue even when output remains finite.
6. **Latency:** limiter adds `round(0.0025 * sampleRate)` samples. Report it through `latency_frames()` if retained. Model the spatial ear delay separately as intentional placement. There is no file-end normalization requirement; the calibrated gain and streaming protection already run live.
7. **Reset/panic/steals:** original panic resets singers but leaves room, limiter and bus history; it can leave deferred ownership state needing explicit handling. Define release-all versus hard reset; clear all pending starts, steals, owners, RNG and histories deterministically for reset. Voice steals currently fade over a control block, another block-dependent behavior to replace with a fixed time/sample count.
8. **Precision and calibration:** prototype uses JS doubles and mixed Float32/Float64 storage. Begin the C++ reference port in double where needed; optimize only after acoustic comparison. Replacing its random generator with `ws::Random` changes individual noise traces: compare envelopes, pitch and spectra rather than require sample equality across languages.
9. **License/provenance:** supplied ZIP contains no license. Owner should confirm original versus reused code and any Pink Trombone-derived portions before redistribution. Do not assume that influence implies code reuse or assign an upstream license without checking.

## Wirescape capabilities: present versus needed

Inspected evidence: `docs/SDK_AUTHOR_GUIDE.md` (especially §§5–10 and 15), `docs/MODULE_BUILD_GUIDE.md`, actual `native/sdk/wirescape_sdk.h`, `native/modules2/vco/dsp.h`, `native/voice/allocator.h`, and catalogue architecture in `docs/ARCHITECTURE.md`. Specs describe intent; the SDK and implementation provide the concrete port contract.

| Capability | Assessment for GUTTUR |
|---|---|
| Native C++17 ABI2 source/processor modules | Present; this is the target |
| 1–16 voice channels, mono broadcast and per-voice parameter modulation | Present; model sub-throats inside a voice separately |
| Sample-offset note events and internal range splitting | Present; translate the current block scheduler into this model |
| Stable IDs, units, tapers, stepped controls and modulation flags | Present; use these instead of a bespoke control protocol |
| Fixed-capacity note allocator and event-to-CV helpers | Present; reuse rather than copy the JS allocator |
| Stereo pair metadata | Present in SDK; paired-cable UI gestures are separately listed as future work in PLAN Phase 3E |
| Prepared large memory, versioned state and latency hooks | Present; use for tables/rings, settings/RNG and limiter delay |
| Registering a new synthesis category | Catalogue/presentation work, not an audio ABI change; generic controls can serve first |
| Original rich throat diagnostics | Optional future telemetry integration; PLAN 3A lists bounded telemetry as unfinished. Not required for sound |
| Direct JavaScript/AudioWorklet import | Not needed for this goal; do not build it |
| Importing arbitrary app source as a native module | Requires a source port, contract and build/registration; a ZIP alone is not executable module metadata |

**No GUTTUR-specific engine ABI expansion is demonstrated as necessary.** The infrastructure work worth doing is generic: reliable per-voice control delivery, bounded prepared resources for table-heavy synthesis, explicit internal-unison budgets, stable state/import mappings and clear stereo/poly routing. Verify existing support in the owner's ongoing engine branch before duplicating it. Native ports of other synthesis categories can use the same contract.

## Import and registration plan

1. Freeze the sound reference and document provenance. Choose instrument topology, note limit, singer budget, parameter scope/rates, reset behavior and stable IDs.
2. Port pure table/model functions and one singer to offline C++. Compare pitch, spectral peaks, LF shape and amplitude envelopes against this reference.
3. Add bounded groups, host note/gate input, per-voice controls and state; keep effects in place for initial comparison or use a documented companion chain.
4. Add native folder `native/modules2/guttur/` with DSP, wrapper, descriptor, tests, DESIGN, README and CMake. The existing build guide requires five registration steps: engine2 CMake, control catalogue header/list, presentation metadata and regenerated UI catalogue. Add the patch guide wiring. No custom UI required.
5. Add preset import as plain versioned data, if desired. Map existing camel-case IDs (`tailFry`, `sizeSpread`, `gritAfter`) to the chosen native IDs; preserve source keys in the importer. Convert attack/release/glide ms to seconds, group size to an integer, size cm to the chosen documented unit, and output dB to linear if following SDK level conventions. Jitter/shimmer are percentages and pitch-modulation depths use the reference semantics. Do not normalize away their meaning. Never import crowd/transport fields. Keep unknown source data in import metadata for lossless future migration; do not run code from an imported preset.
6. Benchmark worst cases before promising Pi voice counts. No repository changes are part of this delivery.

## Acceptance for a future production port

- Offline acoustic parity across all presets, multiple pitches, roughness extremes, sizes/vowels and group counts: pitch, resonances, RMS envelope and spectral/noise balance, with tolerances declared before optimization. Include listening comparison by the owner.
- Frame matrix: 1 through max_block, awkward sizes, host events splitting control ticks, deterministic seeds and identical event schedules. Compare regardless of partition.
- 44.1/48/96 kHz, all advertised host channels, every control's range extremes, rapid automation and per-voice modulation. Finite output and stable feedback at every rate.
- Duplicate keys with distinct identities; voice exhaustion, sustain, note-off after steals, choke, rapid reset/panic, active-group count changes and bounded event overflow. No stuck or resurrected voices.
- Allocation watcher across process/event/reset, fixed memory bounds, state version round trip and latency check. Exercise long tails and long-run index rollover.
- Pi 5 CPU and memory at the chosen total singer budget, including two instances. The current SDK guide requests worst block under 50% of the 48 kHz/128-frame period for heavy modules with two instances. Desktop timing or Node throughput is not Pi evidence.

## Validation performed for this extraction

`node tests/verify.cjs /path/to/original/guttur-worklet.js` passed: 11 presets × 3 rates (44.1/48/96 kHz), with note starts, overlapping pitches, live parameter changes, releases, all-off and panic. 231 comparisons produced exactly matching Float32 stereo buffers against original note mode. Checks also cover finite samples, nonzero signal, limiter ceiling on the checked left buffer and absence of removed exports/methods/parameters.

This validates the stripping operation on those schedules, not a native port. Browser execution, block-partition invariance, every control combination, perceptual aliasing and realtime performance were not validated. Exact match includes inherited shortcomings such as residual tails after panic.
