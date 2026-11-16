<!-- SPDX-License-Identifier: GPL-3.0-only -->
# P4 — transport paths (M0 r2)

- **Examined lab commit:** `7df3331e344b0c9c1951f304fd2e72f711f5da10` (main at task start, 2026-11-16).
- **Date:** 2026-11-16, America/New_York.
- **Environment:** GitHub source inspection only; no local checkout/build, runtime execution, device access, LAN access, or transport timing measurement.
- **Citation convention:** paths and 1-based line numbers below refer to the pinned lab commit, not moving main. “Transport” denotes the musical BPM/beat/play state; audio stream start/stop and a sequencer's own run state are distinguished.

## 1. Protocol and sidecar boundary

| Layer / fact | Pinned source |
| --- | --- |
| v0 protocol command table includes patch edits, `setParam`, notes, panic, audio/MIDI device controls, `setSampleRate`, `setBufferFrames` and `ccMap.set`; it has **no global** `setTempo`, `play`, `stop`, `seek`, or `transport` command. This absence is bounded to the complete command table, not all conceivable IPC. | `docs/specs/ENGINE_PROTOCOL.md:65-93` |
| Protocol does expose `setParam` as a live module-parameter event and `setSampleRate` / `setBufferFrames` as stream reconfiguration, neither specified as a master musical transport command. | `docs/specs/ENGINE_PROTOCOL.md:76-78,88-95` |
| Sidecar receives requests and invokes `Session::reply`, forwards replies; it periodically sends status and telemetry. No transport setter is called by this outer dispatcher. | `native/sidecar/main.cpp:13-40` |
| Sidecar's `setParam` handler targets a *module ID*, resolves the descriptor parameter and enqueues `WS2_PARAM`; it updates that module's execution patch parameter on accepted enqueue. It does not invoke `Engine::transport`. | `native/sidecar/session.cpp:1083-1102` |
| The sidecar command handler's `panic` and keyboard `noteOn`/`noteOff` branches release or enqueue notes, not a global play/stop transition. | `native/sidecar/session.cpp:1056-1081` |
| The sidecar's stream `start_audio` and `stop_audio` functions control an audio/null sink or device stream, not the Engine2 `playing` musical flag. | `native/sidecar/session.cpp:343-425,506-525` |
| The sidecar's `playing` local in device enumeration means an audio stream is running, not `WS2_PLAYING` or a tempo-synced music clock. | `native/sidecar/session.cpp:536-541` |
| The complete sidecar command dispatch is the inspected search boundary for absence of a v0 master tempo/transport command; patch-configuration and parameter control are separate paths. | `native/sidecar/session.cpp:849-1168`; `docs/specs/ENGINE_PROTOCOL.md:71-93` |

## 2. Engine and ABI2 module process boundary

| Layer / fact | Pinned source |
| --- | --- |
| Engine2 configuration carries `bpm=120` and `playing=true` defaults. | `native/engine2/engine2.h:12-18` |
| Engine2 publicly declares `transport(double bpm,bool playing,double beat=0)`. Its implementation changes internal config BPM/play and beat when BPM and beat are valid; this is an engine API, not a v0 sidecar command. | `native/engine2/engine2.h:77`; `native/engine2/engine2.cpp:989`; `docs/specs/ENGINE_PROTOCOL.md:71-93` |
| At ABI2 process time the engine synthesizes a `ws2_transport` containing `WS2_PLAYING` when configured playing, BPM, current beat, calculated bar start and 4/4 signature, then passes its address to the native module `ws2_process` context. | `native/engine2/engine2.cpp:647-654` |
| The engine advances musical beat by frames × BPM / (60 × sample rate) only while `playing`, including its normal render completion path. | `native/engine2/engine2.cpp:867-873,926-930` |
| ABI2 declares `WS2_TRANSPORT_EVENT` among event types and `WS2_PLAYING`, `WS2_RECORDING`, `WS2_LOOPING` flags. This declaration is not evidence that the sidecar sends such events. | `native/include/wirescape/module2.h:30-33`; `docs/specs/ENGINE_PROTOCOL.md:71-93` |
| ABI2 `ws2_transport` contains flags, BPM, beat, bar start, time signature and loop bounds. The process structure provides modules a `const ws2_transport *transport`. | `native/include/wirescape/module2.h:60-64,87-92` |
| The observed break is **command ingress → engine master transport setter**: a setter and process-time transport exist, but neither the complete v0 command table nor the inspected sidecar dispatcher provides a master tempo/play/stop command. This does not mean audio rendering is stopped by default. | `docs/specs/ENGINE_PROTOCOL.md:71-93`; `native/sidecar/session.cpp:849-1168`; `native/engine2/engine2.h:16,77` |

## 3. Modules and distinct clocks

| Module / behavior | Pinned source |
| --- | --- |
| ABI2 `essentials.lfo` has `sync` and `beats` parameters. In sync mode it reads `b.transport()->beat`, `flags & WS2_PLAYING` and BPM, computes phase from beats per cycle, and otherwise free-runs from its `rate` parameter. This is a direct read of the engine's ABI2 musical transport. | `native/modules2/lfo/dsp.h:11-16,27-35` |
| ABI2 `essentials.clock` owns a BPM parameter and phase/ramp; the source uses its own `bpm` state rather than showing a read of `b.transport()`. | `native/modules2/clock/dsp.h:7-16` |
| ABI2 Groove is a distinct sequencer transport: its samples-per-step are derived from authored `pattern.bpm`, and `start_transport` manipulates its own `running`, `phase`, step and per-track playing fields. These are not evidence of a global Engine2 `playing` setter. | `native/modules2/groove/dsp.h:90-95,378-394` |
| Groove uses patchable external clock/run/reset inputs to distinguish its sequencer state from clock inputs; these inputs are separate from the ABI2 process transport pointer. | `native/modules2/groove/dsp.h:395-410` |
| Studio's Groove run/stop UI changes module parameters through `setParam`, not a global v0 play/stop wire command. | `apps/studio/src/app/App.ts:1030-1037`; `native/sidecar/session.cpp:1083-1102` |
| Legacy ABI1 `clock` has an independent BPM ramp and Run parameter; it clocks from its own sample rate, BPM and phase. ABI1 has no `ws2_process.transport` in this source. | `native/modules/clock/module.cpp:23-44,59-69`; `native/include/wirescape/module2.h:87-92` |

## 4. Reproducible source-search boundary and limitations

| Examined source scope | Result |
| --- | --- |
| Complete `native/modules2/{groove,host_keyboard,osc_in,osc_out,monitor,vco,lfo,vcf,adsr,vca,clock,function_envelope,ladder,mixer,noise,output,scale_offset,slew,macro_oscillator,chaos_lite,blend,resonator,spectral,delay,reverb,quantizer,quad_vca,notes_to_cv,chord}/dsp.h` contents, plus entry-point `module.cpp` for groove through chaos_lite in this set, searched for `transport|tempo|bpm|WS2_PLAYING|sync|beat` (case-insensitive). The 29 DSP headers belong to the inspected CMake-listed module families. Only LFO in these inspected DSP headers directly dereferences the ABI2 process transport; Groove and clock have their own BPM/run logic. This is a bounded textual finding, not a claim about transitive helpers or uninspected modules. | `native/engine2/CMakeLists.txt:89-110,254-263`; `native/modules2/lfo/dsp.h:27-35`; `native/modules2/groove/dsp.h:90-95,378-405`; `native/modules2/clock/dsp.h:7-16` |
| Searched `native/sidecar/session.cpp` for `transport|tempo|bpm|WS2_PLAYING|sync|beat`; no musical transport setter appears in this file. The only observed `playing` lexical match refers to running audio stream/device listing. | `native/sidecar/session.cpp:536-541,849-1168` |
| Searched `native/engine2/engine2.cpp` for `transport|bpm|playing|beat`; found process transport construction, beat progression and a public setter. These source references alone do not establish sample-exact behavior of a future externally driven tempo change. | `native/engine2/engine2.cpp:647-654,867-873,926-930,989` |
| The findings do not report transport-device synchronization, MIDI clock following, measured clock drift, timing jitter or behavior of an unimplemented transport command; no device or wall-clock experiment was run. | `docs/specs/ENGINE_PROTOCOL.md:71-93`; `native/engine2/engine2.cpp:647-654` |
