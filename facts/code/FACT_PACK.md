<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Wirescape fact pack: code readings and background (snapshot 44da1e4)

**Developing document — v0.2 (2026-11-14).** All six parts (A, B, C1, C2, D, E) are in. A, B, C1 and C2 were checked against their source packs. D was checked only against the files that also appear in packs A and C1, because pack D itself was not supplied with its responses (see §1.3). E has no source files; its licence facts were checked against current public sources.

This document collects what is true about the Wirescape code at snapshot `44da1e4`, plus background knowledge, for an architecture review. Each part was written by a separate LLM session that read one source pack without running anything. A review pass then re-checked a sample of their claims against the sources, fixed the errors it found, and reconciled the parts against each other. These are readings of the code, not measurements: the offline and device runs remain the ground truth. Decisions are left to the reviewer.

## 0. How to read this document

### 0.1 Parts

| Part | Title | Scope | Source pack | Status | Save as (wirescape-lab) |
|---|---|---|---|---|---|
| A | Engine core | engine2, AppEngine facade, runtime patch loader, ABI1 headers, ABI2 spec | `A_engine_core.md` (~37k tokens) | Reviewed | `facts/code/engine_core.md` |
| B | Engine protocol | protocol spec vs sidecar, EngineClient/RealEngine, Electron main/preload | `B_protocol.md` (~53k tokens) | Reviewed | `facts/code/protocol.md` |
| C1 | DSP: sources, filters, envelopes | 13 modules: VCO … Quad VCA | `C1_dsp_sources_filters.md` (~24k tokens) | Reviewed | `facts/code/dsp_sources_filters.md` |
| C2 | DSP: effects, mixing, sequencing, control | 14 modules: fx.delay … osc.out | `C2_dsp_effects_control.md` (~41k tokens) | Reviewed | `facts/code/dsp_effects_control.md` |
| D | Module SDK and portability | SDK wrapper, author guide, template, VCA and step-sequencer examples, ABI contract | `D_sdk_portability` (~31k tokens) | Reviewed in part (pack not supplied) | `facts/code/sdk_portability.md` |
| E | Background reference | hardware targets, patch-to-firmware pipelines, plugin APIs, DSP techniques, Pi 5 and Windows audio, benchmarking | prompt only | Reviewed; licences re-checked | `facts/background/reference.md` |

Order by value (from the pack README): A, C1, D, B, C2, E. Each part keeps its own header line and citation legend, so it can still be split back into its own file.

### 0.2 Tags used in every part

| Tag | Meaning |
|---|---|
| (inf) | Inferred from the code, not stated by it |
| (mk) | From model knowledge (literature, other projects, hardware), unverified, possibly out of date |
| NV | Not visible: the file it depends on is not in that part's pack (Part D wrote this as NP) |
| **(uncertain)** | Part E only: a model-knowledge fact its author could not state with confidence |
| [checked 2026-11] | Part E only: re-checked against a public source in review; sources at the end of Part E |
| [Rn] | Corrected or rewritten in review; see §1.1 |
| [Xn] | Answered or narrowed by another part; see §2 |
| A-Q7, B-Q30, C1-Q8, D-Q9, E-Q11 | Open question 7 of Part A, question Q30 of Part B, and so on |

### 0.3 Citation conventions

The sessions used different line-number schemes. They are kept as written, because rewriting thousands of citations by hand would risk new errors. Use this table to resolve them.

| Part | Form | Meaning |
|---|---|---|
| A | `engine2.cpp:938` or bare `(938)` | Line 938 of the **pack-A bundle file**, not of the repository file. Bundle numbers are unique across files, so a bare number identifies its file. Convert with the offsets below. |
| B | `SE:1099`, `RE:306`, `M:357` | Line in the repository file, counted from that file's first line. S = ENGINE_PROTOCOL.md, PH = protocol.h, P = protocol.cpp, SH = session.h, SE = session.cpp, EC = EngineClient.ts, RE = RealEngine.ts, M = main.ts, PL = preload.ts |
| C1, C2 | `:93` or `delay/dsp.h:100` | Bare `:N` = line N of the module's own `dsp.h` (the one named in the section heading). `file:N` = line N of that file. Both count from the file's first line. |
| D | `M2:16`, `SDK:205`, `SAG:146` | Line in the repository file. M2 = module2.h, SDK = native/sdk/wirescape_sdk.h, SIG = signals.h, FM = fastmath.h, SIMD = simd.h, TPL = native/sdk/template/, VCA = native/modules2/vca/, SEQ = native/sdk/examples/step_sequencer/, SAG = docs/SDK_AUTHOR_GUIDE.md, SPEC = docs/specs/ABI2_SPEC.md |
| E | — | No code citations; model knowledge, plus web sources for the re-checked licence facts |
| Review notes | `A:871` | Line 871 of the pack-A bundle (same scheme as Part A) |

**Pack-A offsets** (repository line = bundle line − offset):

| File | Offset | File | Offset |
|---|---|---|---|
| native/include/wirescape/module2.h | 50 | native/document/runtime_patch.h | 1934 |
| native/engine2/engine2.h | 176 | native/document/runtime_patch.cpp | 1951 |
| native/engine2/engine2.cpp | 284 | native/include/wirescape/engine.h | 2052 |
| native/control/app_engine.h | 1560 | native/include/wirescape/module.h | 2143 |
| native/control/app_engine.cpp | 1620 | docs/specs/ABI2_SPEC.md | 2216 |
| native/control/module_catalog.h | 1882 | | |

Example: `A:871` is `engine2.cpp` line 871 − 284 = 587. The same file appears in several packs (module2.h, signals.h, fastmath.h, ABI2_SPEC.md); repository line numbers agree across them, which is how Part D's `M2:` and `SPEC:` citations were checked.

Section references inside a part, such as "(5.3)" in Part A or "(3c)" in Part B, point to that part's own sections (§A5.3, §B3c).

---

## 1. Review log

The review checked each part against its pack: it re-read the cited lines for the claims most likely to matter or to be wrong, re-computed every table of sizes and constants, and checked each part against the task it was given. It did not re-read every citation. Where a fact in one part answers a question in another, that is recorded in §2 rather than silently merged.

### 1.1 Corrections

| ID | Where | What the session wrote | Corrected to | Evidence |
|---|---|---|---|---|
| R1 | C1 §C1.8 Resonator (Numerics, Artefacts, C1-Q11) | The radiation LP coefficient saturates above ≈12.7 kHz @48k and "never @96k". | It saturates whenever the **fundamental** reaches rate/3.77 (≈11.7 / 12.7 / 25.5 kHz at 44.1 / 48 / 96 kHz). The pitch clamp allows up to 0.45·rate (19.8 / 21.6 / 43.2 kHz), so this is reachable at every rate, including 96k. | `resonator/dsp.h:108`, `:123` |
| R2 | C1 §C1.5 CHAOS, Reference | ADAA "(Parker, Zavalishin, Le Bihan 2016)" | Parker, Zavalishin, Le Bivic, DAFx 2016 (mk) | C2 has the correct name |
| R3 | C2 §C2.1 delay, §C2.2 reverb, §C2.3 spectral, §C2.4 blend, §C2.6 output; C2-Q7, C2-Q28 | reverb, spectral and blend read only ch 0, so "other channels of a poly cable are silently dropped"; whether the host pre-sums WS2_SUM inputs is open. | engine2 pre-sums every source voice into one channel for a `WS2_SUM` input before `process`. These modules' audio inputs are all `WS2_SUM`, so a poly cable is heard as its mono sum. Nothing is dropped. Only blend's Switch input (`WS2_FIRST`) uses voice 0 alone. fx.delay's own channel-sum loop therefore runs over one channel. | engine2.cpp A:864 (`SUM` → 1 channel), A:871 (sum loop); port declarations `reverb/dsp.h:40-41`, `spectral/dsp.h:50`, `blend/dsp.h:17-18`, `delay/dsp.h:11-12`, `output/dsp.h:7` |
| R4 | C2 §C2.6 output | Input `WS2_SUM` cited as `(:8)` | `(:7)` (line 8 is the output port) | `output/dsp.h:7-8` |
| R5 | B §B4a, sidecar engine config | "`config_{sizeof,rate,block,64,2048}`; meaning of 64/2048 not visible (ws_engine_config not in bundle)" | `ws_engine_config` is in pack A. Its fields are `struct_size, sample_rate, max_block_frames, max_nodes, max_events`, so the sidecar sets max_nodes = 64 and max_events = 2048. AppEngine maps max_events to engine2 `event_budget`. | engine.h A:2075-2079; app_engine.cpp A:1694; session.cpp SE:263 |
| R6 | B §B2a, row A17 | "No separate priority path visible" for noteOff/panic | Not at sidecar level, but engine2 has one: releases (NOTE_OFF/CHOKE) go to each producer's critical ring, which is drained before the normal ring, and they spend a reserved 256-event budget. | engine2.cpp A:1119, A:760-764, A:727 (Part A §A5.1, §A5.3) |
| R7 | A §A5.3 | Budget example "Defaults 1024/256 → ordinary cap 768 per call" only | Kept, and added the product value: with the sidecar's config (R5) the budget is 2048/256, so the ordinary cap is 1792 events per render call. | R5 |
| R8 | C2 §C2.2 reverb, Numerics ("Whether the engine sets FTZ is not visible") | FTZ status unknown | engine2 `render()` sets FTZ+DAZ (MXCSR \| 0x8040) on x86/x64 and FZ (FPCR bit 24) on AArch64 for the whole render call. The denormal exposure described applies only to builds without either guard (for example MSVC on ARM64) and to other hosts or adapters. | engine2.cpp A:1139-1149 |
| R9 | C1 legend ("D7 = host base smoothing (NV)") | D7 treated as an unseen mechanism | Visible in pack A. In ABI2_SPEC, base smoothing is **D6** (5 ms linear ramp in normalized space) and modulation is **D7**. The module DESIGN docs use "D7" loosely for the engine's whole parameter pipeline. | ABI2_SPEC.md A:2245, A:2251; engine2.cpp A:879-907 |
| R10 | D §D4.2, §D4.6, §D6.2–D6.5 | Host-side items "NP": descriptor checks, module loading, smoothing/modulation, scheduler, per-instance seed, event order; "event budget 1024" | Those host files are in pack A. The cells now point to the engine code, and the budget note gives the product value (2048). | §2 X16, X17, X19, X20; pack A §A4, §A5 |
| R11 | E §E3.2 VST3 and §E6.1 ASIO (licences; E-Q11) | VST3 SDK "dual GPLv3 / proprietary at cutoff"; ASIO "historically proprietary (GPLv3 option announced later, uncertain)" | Since October 2025 the VST 3.8 SDK is MIT, and the ASIO SDK is offered under GPLv3 alongside the proprietary licence. | Steinberg press release, 29 Oct 2025; E sources |
| R12 | E §E2.1 Oopsy and RNBO rows (E-Q7, E-Q8) | gen~ export licence and RNBO terms "uncertain" | Both are dual-licensed: the Cycling '74 License for Max-Generated Code for Export or GPLv3. Commercial use that does not sell or distribute the code needs no licence. Entities under $200k annual revenue or funding may sell; above that, gen~ users must register with Cycling '74. RNBO 1.x code carries no fees, and RNBO's engine source is MIT. | Cycling '74 licensing FAQs; E sources |
| R13 | E §E2.1 Faust row (E-Q10) | Compiler "GPL (later parts relicensed to LGPL, uncertain)" | Current Faust compiler sources are largely LGPL-2.1+ (Debian packaging of 2.77–2.79), and architecture files carry a FAUST exception. The Faust FAQ says the compiler's licence does not apply to generated code. | Debian copyright file; Faust FAQ; E sources |
| R14 | E §E2.1 / §E2.2 hvcc rows (E-Q9) | Generated-code licence "ISC-style (uncertain)"; `expr`/`expr~` support uncertain | Compiler GPL-3.0+; the C runtime copied into generated code (`ir2c/static`) is ISC. `expr`/`expr~` are supported from v0.15.0 (2025). | Debian copyright for hvcc; Wasted Audio release note; E sources |
| R15 | E §E4.5 linear interpolation; §E4.6 Freeverb | Garbled text ("worst at 0.5: −∞ dB… i.e."; "in DaisySP? no — …") | Rewritten as plain statements, same facts | — |

### 1.2 Cleanups (format only, no change of fact)

- One document: a single H1, parts at H2, and section numbers prefixed by part (A1, B4a, C1.8, C2.10, D4.6, E5.3).
- Inference and knowledge tags unified to (inf) / (mk) / NV across all parts. Part A used the long forms; C2 and D used (MK); D used NP for not visible.
- Removed chat residue: the separators added when the chats were pasted together, `[PART k DONE]` and `[REPORT COMPLETE]` markers, the restatements of the report rules in B and D, C2's closing chat note (its content is already in §C2.14), and E's closing "things to double-check" note (acted on in R11–R14). E repeated its model-knowledge disclaimer under every section; that now appears once at the top of Part E.
- Part B's ALL-CAPS headings changed to sentence case.
- Review annotations are inline and short: `[Rn]` where text was changed, `[Xn]` where another part answers or narrows a point.

### 1.3 Spot checks that held (no change needed)

| Part | Claim | Check |
|---|---|---|
| A | FP-mode guard lines, re-entrancy flag, park handshake, park deadline 3 blocks = 16 ms at 256/48k | Re-read A:1134-1165, A:1402-1413; arithmetic re-done |
| A | `return routed?okay:okay;` (both branches identical) | A:835 |
| A | `load_runtime_patch` validates saved sample_rate / max_block_frames / timing_mode but applies only max_channels / feedback_block / seed | A:1990-1997 |
| A | `setup()` calls `clear_instance()` first, so add-time instances are rebuilt in `prepare` | A:559-600 |
| A | Default arena 1,507,328 B = 1472 KiB; all Config defaults and ranges | Arithmetic and A:1095-1097 |
| B | Reader blocks at 256 queued commands and then enqueues a busy marker | protocol.cpp P:144-162 |
| B | loadGraph always takes the D5 fade/swap path (`new_namespace` skips live replan) | SE:703-705 |
| B | setParam stores the value as `float` in the execution copy | SE:1090-1101 |
| B | removeModule also removes the module's `outputs` routes | SE:1115-1128 |
| B | Library read binds `patchPath`, and `savePatch(saveAs:false)` then overwrites it without a dialog | M:356-366, M:466-482 |
| C1 | VCF ZDF solve, k ≤ 3.2, DC gain 1/(1+k) ≈ −12.5 dB; Ladder (1+k) input gives unity DC gain | `vcf/dsp.h:22-31`, algebra re-done |
| C1 | Macro Oscillator refuses any rate other than 48000 | `macro_oscillator/dsp.h:58` |
| C1 | CHAOS and Resonator memory tables; DC-blocker corners ≈35/38/76 Hz; ADSR and Function-Envelope sample counts | Re-computed |
| C1 | Noise mean offset ≈ −2⁻²⁴ | Re-derived |
| C2 | Delay, reverb and spectral memory tables; reverb allpass lengths 253/399/309/451 are composite and are the whole delay | Re-computed; `reverb/dsp.h:17-36`, `:70-99` |
| C2 | Reverb output scale 0.35/√8, ×6 wet makeup (+15.6 dB), RT60 gain 0.966, denormal-time estimate | Re-computed |
| C2 | Delay glide constants (α ≈ 4.17e-4, −12 st / +7 st) | Re-computed |
| C2 | quantizer has no `save_state`/`load_state`; groove returns WS2_INVALID for an unknown version | grep over all C2 `dsp.h`; `groove/dsp.h:144-156` |
| C2 | midi_to_cv declares sustain at slot 6 but reads `b.param(5)` | `midi_to_cv/dsp.h:20-28`, `:69-76` |
| D | ABI limits and their lines (M2:16-21, including "raised from 32 (additive, #402)"); `ws2_config` doubles/uint64 (M2:68-70); `ws2_memory` size_t fields (M2:73); descriptor layout (M2:94-108) | module2.h in pack A |
| D | `LinearRamp` double state, pre-prepare length 240, prepare `max(1, rate·0.005)`; `Trigger` default 48, 1 ms; `Random::save/restore` "Additive state accessor" (SIG:7-62) | signals.h in pack C1 |
| D | `tan_small` evaluated in double, comment "not used by the VCF port" (FM:4-8) | fastmath.h in pack C1 |
| D | Every `SPEC:` quote checked (D4, D6, D7, D11, D13, D14, D15, limits, status line about the patch-v2 draft) | ABI2_SPEC.md in pack A |
| D | Size arithmetic: VCA scratch 576 B at 48 frames, 49,152 B at 4096; `ws2_param` ≈96 B on LP64; reference bound 1,333 µs = half of 128/48k | Re-computed |
| E | Buffer-latency table (64/128/256 frames at 48 kHz = 1.33/2.67/5.33 ms); DSP-load example (1.0/2.67 ms = 37.5 %); Axoloti k-rate 48000/16 = 3 kHz | Re-computed |
| E | PREEMPT_RT merged in mainline Linux 6.12 (2024); Pi 5 initial mainline support in the same release | Public sources (see Part E sources) |
| All | No "should" or recommendation outside the Open-questions sections | Text search |

### 1.4 Verification limits

- **Part D could be checked only in part.** Its responses arrived without the D pack, so its claims about `wirescape_sdk.h`, `simd.h`, the template, the VCA and step-sequencer examples, and `SDK_AUTHOR_GUIDE.md` are as the session wrote them. Its claims about module2.h, signals.h, fastmath.h and ABI2_SPEC.md were checked through packs A and C1 and held, with no line-number drift. Supplying pack D would let the review settle X5 (below), which needs `wirescape_sdk.h` around SDK:200-210.
- **Part E** has no sources by design. Only the licence items its author flagged, and the PREEMPT_RT status, were re-checked. The board specifications and other **(uncertain)** items were not.

### 1.5 Instruction compliance

| Part | Required sections | Header line | Rules | Gaps |
|---|---|---|---|---|
| A | 9 of 9 | Present | Facts cited; tags used; no recommendations | None |
| B | 8 of 8 | Present | As A | The UI consumers of push fields are traced only to RealEngine, main and preload, because Studio components are not in the pack (stated in §B3) |
| C1 | 13 modules × 7 headings, summary table, open questions | Present | As A | The summary table adds useful columns beyond those requested |
| C2 | 14 modules × 7 headings, summary table, open questions | Present | As A | None |
| D | 7 of 7 (module, authoring flow, portability, ABI contract, comparison, compiler readiness, open questions) | Present | As A; comparison section marked (mk) as a whole | Several host-side cells said "NP" although the files were in pack A (R10) |
| E | 7 topic sections + open questions | Present | All (mk); 25 uncertain items listed | Licence facts out of date (R11–R14) |

### 1.6 Revision history

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-11-14 | Parts A, B, C1, C2 merged, reviewed and corrected (R1–R9); cross-part findings X1–X14 |
| v0.2 | 2026-11-14 | Parts D and E added and reviewed (R10–R15); cross-part findings X15–X20; X2, X4, X6, X12 and X13 updated from D; E's licence facts re-checked |
| v0.3 | — | Planned if pack D is supplied: verify D's SDK claims and settle X5 |

---

## 2. Cross-part findings

These come from reading one part's open questions against another part's sources. Each finding cites the code it rests on.

| ID | Finding | Evidence | Answers or narrows |
|---|---|---|---|
| X1 | **Denormals are flushed during render on both target platforms.** `Engine::render` installs a guard for the whole call: on x86/x64 it ORs MXCSR with 0x8040 (FTZ bit 15 and DAZ bit 6, as Part E §E4.4 also describes, (mk)); on AArch64 (not MSVC) it sets FPCR bit 24 (FZ). Other targets, including MSVC ARM64, get no FP-mode change. Every module `process`/`reset` runs inside this guard. The VCF and Ladder 1e-20 tail cuts stay, because their comment says FTZ is not assumed bit-equivalent. | engine2.cpp A:1138-1150; `vcf/dsp.h:27-29`; ABI2_SPEC D15 A:2293 | C1-Q8, C2-Q1; the subnormal notes in C1 CHAOS / Resonator / Quad VCA and C2 delay / reverb (R8) |
| X2 | **Parameter smoothing.** Base changes (`set_parameter`, PARAM events) on non-stepped parameters ramp linearly in normalized space through `ws::LinearRamp`; the spec says 5 ms, and repeated identical targets do not restart the ramp. Stepped parameters jump. Cable modulation (Σ amount·CV) and PARAM_MOD offsets are added **per sample without smoothing**, then clamped and tapered. So for modulated parameters the only smoothing is whatever the module does itself, for example the PortRamp in Noise, Ladder, Mixer, Scale/Offset and the Clock BPM. Part D reports that `wirescape_sdk.h` includes `signals.h`, so the engine's `ws::LinearRamp` is the `signals.h` class (length max(1, rate·0.005)); this rests on D's reading of the SDK. | ABI2_SPEC D6 A:2245, D7 A:2251; engine2.cpp A:879-907 (Part A §A5.5); `signals.h:9-31`; Part D §D2 step 4 | C1-Q1, C1-Q2, C1-Q3 (partly), C2-Q2; R9 |
| X3 | **WS2_SUM inputs are pre-summed by the engine.** A `WS2_SUM` port gets one channel, the sum of all source voices; `WS2_FIRST` takes voice 0; `WS2_POLY` gets the node's channel count. | engine2.cpp A:856, A:864, A:871-872 | C2-Q7, C2-Q28; R3 |
| X4 | **Channel count is at most 16.** engine2 accepts `max_channels` 1..16, and WS2_MAX_CHANNELS = 16. Part D reports that the SDK's `process` also rejects any call outside 1 ≤ channels ≤ max_channels ≤ 16 (SDK:194, :214). So `b.channels()` ≤ 16 for every module. | engine2.cpp A:1021, A:1095; module2.h A:67; Part D §D3.5 | C2-Q4 (the unchecked `voices[c]` indexing in mixer, scale_offset and clock) |
| X5 | **The engine never resets a module after `prepare`, and host memory is not zeroed.** `setup()` calls create → query_ports → prepare → memory_requirements → latency_frames, with no reset. `Node::allocate` uses aligned `::operator new` (nothrow) without zero-fill. Module `reset` runs only from `reset_processors`, that is, when generation ≠ applied (after panic or emergency) or from `Engine::reset` / `app_engine_reset`. `finish_prepare` sets applied = generation, so the first render does not reset. Neither session.cpp nor runtime_patch.cpp calls `app_engine_reset`. **Still open after Part D:** D lists the wrapper's `prepare` at SDK:203-204 and `reset` at SDK:205, 207, but does not say whether the wrapper calls `reset()` after `prepare()`. If it does not, reverb (and possibly quantizer, chord, midi_to_cv and notes_to_cv) start from uninitialized LARGE buffers and member defaults, for example reverb gain = 0 and delay = 0. | engine2.cpp A:559-600, A:418-425, A:525-536, A:624-630, A:1251-1272; `reverb/dsp.h:105-124`; Part D §D1.3 | C2-Q5 (narrowed; needs pack D, SDK:200-210) |
| X6 | **Non-finite and exception policy.** Part D reports that the SDK scans every output sample (or sample 0 if CONSTANT) after each `process` and returns WS2_INVALID if any is non-finite, and that `guarded()` maps any C++ exception to WS2_EXCEPTION when exceptions are compiled in. engine2 then counts a fault (`++faults`) and forces that node's outputs to constant zero for the block; it does not reset the module. (inf) A module whose recursive state has become NaN therefore stays silent until a reset (panic, emergency or graph reload). | engine2.cpp A:938; ABI2_SPEC D14 A:2289, A:2305; Part D §D3.4, §D4.5 (SDK:163-169, :233-238) | C1-Q6 (narrowed), A-Q4 (answered: the SDK barrier); the NaN notes across C1 and C2 |
| X7 | **Latency is reported, never compensated.** The spec says the host reports latency and does no automatic compensation. The sidecar's 100 ms status tick calls `refresh_latency()` on every status, so module `latency_frames()` (for example spectral's size-dependent N) is re-queried about 10 times per second. The concurrent read is the documented contract in engine2.h (modules "publish dynamic latency atomically from process()"), matching the author guide quoted in D; ABI2_SPEC D13's list of cross-thread surfaces omits it. (inf) The status push's `audio.latencyMs` is 2·block/rate, not graph latency, so the re-queried value is not sent to the UI. | ABI2_SPEC D12 A:2277, A:2309, D13 A:2281; engine2.h A:263-264 (Part A §A2.1); session.cpp SE:1250-1251, SE:1219 | C1-Q13 (no compensation), C2-Q22, A-Q1, D-Q16, D-Q23 |
| X8 | **Transport is fixed in the visible code.** Nothing in app_engine.cpp, runtime_patch.cpp or session.cpp calls `Engine::transport()`. Modules therefore always see the Config defaults: 120 BPM, PLAYING set, beat counting from 0 since prepare, fixed 4/4. (inf) LFO sync (C1 §C1.3) locks to this internal 120 BPM timeline, not to any user tempo; groove uses its own pattern BPM. | grep over those files; engine2.h defaults A:188-194; engine2.cpp A:931-933 | A-Q2, A-Q22; C1 LFO sync |
| X9 | **Product event budget is 2048.** The sidecar creates every engine with max_nodes 64 and max_events 2048 (R5). With release_reserve 256 that gives 1792 ordinary events per render call, shared by all nodes. max_nodes 64 matches the 64-module patch limit. | session.cpp SE:263; app_engine.cpp A:1694; runtime_patch.cpp A:1990 | §A5.3 / §A8 defaults (R7); B §B4a (R5); D §D6.3 (R10) |
| X10 | **Panic is a whole-graph DSP reset, safe from any thread.** `app_engine_panic` → `Engine::panic`: generation +1 (acq_rel) and the egress emergency flag. That is two atomics, `noexcept`, and documented for any thread. The next render runs `reset_processors`: every module is reset, ramps and PARAM_MOD offsets cleared, pending events dropped, feedback delay lines zeroed, `future` cleared. So the sidecar's panic uses (the panic command, failed-noteOff fallback, D5 swap, rate/buffer change) each reset all DSP state in that graph, not just held notes. Notes held downstream of the engine are released by the synthesized NOTE_CHOKE that `pop_egress` returns. | app_engine.cpp A:1872; engine2.cpp A:1250, A:525-536, A:1235-1238; ABI2_SPEC D13 A:2281, A:2285 | B-Q30 (thread safety: by contract; priority: R6); D-Q22 |
| X11 | **Producer 0 has one writer in visible code.** setParam, noteOn and noteOff enqueue on producer 0 from the sidecar control thread, and `app_engine_enqueue` also uses producer 0. The MIDI service is producer 1 and OSC In producer 2; their threads are described in B §B5a. | session.cpp SE:1073, SE:1099; app_engine.cpp A:1659-1661, A:1775 | A-Q5 (narrowed) |
| X12 | **State save/load coverage across C1 and C2.** Seven modules define neither `save_state` nor `load_state`: vco, lfo, vcf, adsr, vca, quad_vca and quantizer. Part D reports that the SDK wrapper then returns WS2_UNSUPPORTED (SDK:241-250). engine2 keeps the bytes of a WS2_UNSUPPORTED load in `preserved` rather than dropping them, as ABI2_SPEC D12 asks. | engine2.cpp A:1023, A:1309; ABI2_SPEC D12 A:2277; grep over all `dsp.h` in C1 and C2; Part D §D1.3 | C1-Q24, C2-Q10 |
| X13 | **Parameter indexing, and what C2 called "slot".** The engine addresses parameters by position in the descriptor array: the PARAM index is `p - d->params`, validation checks `index < parameters.size()`, and parameter signals are laid out in array order. The ninth argument of `ws::param`, which C2 called the "slot", is `legacy_index` (Part D §D1.5, and the helper calls in every C1/C2 `dsp.h`). midi_to_cv's `b.param(5)` (sustain, legacy_index 6) and `b.param(8)` (channel_filter, legacy_index 9) are therefore correct reads by array position. | session.cpp SE:1097; engine2.cpp A:710-718; `midi_to_cv/dsp.h:20-28`, `:69-92`; Part D §D1.5 | C2-Q11 (answered) |
| X14 | **Where engine rate and block come from.** `load_runtime_patch` builds engine2 Config from the caller's `ws_engine_config` (the sidecar's `config_`, built from CLI flags and settings.json), not from the patch's saved settings. That is why saved sample_rate and max_block_frames are validated but unused. Because the same `cfg.sample_rate` is passed to `prepare` and to every `process`, the SDK's exact-equality rate check (D §D3.5) always passes under engine2. | runtime_patch.cpp A:1990-1999; session.cpp SE:263, SE:299, SE:683; engine2.cpp A:561, A:934 | A-Q11 (context), D-Q14 |
| X15 | **`legacy_index` is still read by the host, and a duplicate value would misroute v2 patch parameters (latent).** AppEngine builds an ABI1-style metadata table for every built-in, using each parameter's `legacy_index` as its numeric ID. The v2 patch loader finds a parameter by string ID, then applies its value through `app_engine_initialize_parameter` by that numeric ID, which takes the **first** parameter with a matching ID. If two parameters of a module shared a `legacy_index` (the helper's default is 0), a saved value would be applied to the wrong parameter or refused as out of range. All 25 built-ins in packs C1 and C2 have unique values, so this is not live there; modules outside those packs (the full catalogue is not visible) were not checked. | app_engine.cpp A:1672-1674, A:1758; runtime_patch.cpp A:2033; Part D §D1.5, §D4.4; scan of every `ws::param` call in C1/C2 | D-Q9, D-Q10 |
| X16 | **Module discovery in the product is a compiled-in list.** AppEngine builds its catalogue from `builtin_modules()`, an X-macro over `module_catalog.inc` (`WS_APP_MODULE(Class)` → `ws::Module<Class>::descriptor()`). The only module loader in packs A–D is `app_engine_load_module`, which loads **ABI1** libraries through `ws_engine_load_module`. No code in A–D loads a `ws2_<name>` shared library or reads `module.json`. (inf) The SHARED libraries and `module.json` serve tests and other hosts. | module_catalog.h A:1921-1925; app_engine.cpp A:1662, A:1719 | D-Q5, D-Q7 (no checker found), D §D4.6 |
| X17 | **Descriptor validation and the real limits.** engine2's `add_node` rejects a descriptor unless struct_size ≥ sizeof(ws2_descriptor), abi_version == 2, id and name are non-null, all 10 function pointers are set, and input_count ≤ 32, output_count ≤ 32 and param_count ≤ 64. Ports returned by `query_ports` are checked against 32 per direction as well. So more than 32 parameters is accepted, and ABI2_SPEC's "32 ports/parameters/producers" is stale for parameters. | engine2.cpp A:1022-1024, A:571; module2.h A:68-69; ABI2_SPEC A:2307 | D-Q2, D-Q3, D-Q4 (descriptor side; the exported `ws_module2_abi_version()` has no loader to check it), A-Q23 |
| X18 | **Patch v2 is implemented.** ABI2_SPEC's status line says the draft *schema file and example* are not loaded by the application. The v2 format itself is: `load_runtime_patch` accepts versions 1 and 2, and the sidecar's `loadGraph` requires `format == "wirescape.native.patch"` and `version == 2`. | ABI2_SPEC.md A:2219; runtime_patch.cpp A:1988; B §B1b (SE:1105-1107, SE:605-609) | D-Q24 |
| X19 | **Memory reporting is enforced, and alignment comes from each allocation.** After `prepare`, engine2 calls `memory_requirements` and refuses the module ("Module memory report understates requested storage") if the reported fast or large bytes are less than what it actually allocated. So a module that allocates without reporting fails at prepare, which enforces ABI2_SPEC D11. The engine does not read `ws2_memory.alignment`; each `alloc` call carries its own alignment, raised to at least 32, so a module that needs 64 asks for it per allocation. | engine2.cpp A:576-578, A:418-425 | D-Q13, D-Q15 |
| X20 | **Host-side items Part D could not see.** engine2 derives each node's seed as `cfg.seed + node id`; orders events by (frame, cleanup, order), where order is producer and serial for ingress and traversal serial for module output; and schedules with Tarjan SCCs, DFS back-edges and Kahn order. | engine2.cpp A:561; Part A §A5.4, §A4.1 (topology A:653-708) | D §D6.2, §D6.4 (R10) |

### 2.1 Open-question status

Questions not listed here are still open.

| Question | Status | See |
|---|---|---|
| A-Q1 | Narrowed: the concurrent caller is the sidecar's status tick, and the concurrency is the engine2.h contract | X7 |
| A-Q2 | Narrowed: `transport()` is never called in the visible code | X8 |
| A-Q4 | Answered: the SDK wrapper's exception barrier (when exceptions are compiled in) | X6 |
| A-Q5 | Narrowed | X11, B §B5a |
| A-Q11 | Context added | X14 |
| A-Q22 | Narrowed | X8 |
| A-Q23 | Answered: 64 parameters accepted; the spec line is stale | X17 |
| B §B4a "64/2048 not visible" | Answered | R5, X9 |
| B-Q30 | Answered (thread safety and priority) | X10, R6 |
| C1-Q1, C1-Q2 | Answered | X2 |
| C1-Q3 | Partly answered; PortRamp (`port_state.h`) is in none of the packs | X2 |
| C1-Q6 | Narrowed | X6 |
| C1-Q8 | Answered for x64 and Pi 5 | X1 |
| C1-Q13 | Answered: no compensation | X7 |
| C1-Q14 | Open: D names `b.split` but does not describe its event semantics | — |
| C1-Q24 | Answered | X12 |
| C1-Q33 | Open: `comb_body.h`, `coupler.h`, `drift.h`, `port_state.h` are in none of the packs | — |
| C2-Q1 | Answered for x64 and Pi 5 | X1 |
| C2-Q2 | Answered for the engine side | X2 |
| C2-Q3 | Open: `port_state.h` is in none of the packs | — |
| C2-Q4 | Answered | X4 |
| C2-Q5 | Narrowed; **needs pack D (SDK:200-210)** | X5 |
| C2-Q7 | Answered | X3 |
| C2-Q10 | Answered | X12 |
| C2-Q11 | Answered | X13 |
| C2-Q22 | Partly answered | X7 |
| C2-Q28 | Answered | X3 |
| D-Q2, D-Q3 | Answered | X17 |
| D-Q4 | Answered for the descriptor; no ABI2 loader exists to check the exported version function | X17, X16 |
| D-Q5 | Answered: compiled-in list | X16 |
| D-Q7 | Answered: no checker in A–D | X16 |
| D-Q9 | Answered: AppEngine reads it; latent collision risk | X15 |
| D-Q10 | Context: legacy_index matters only for the ABI1 metadata table, v1 migration and the parameter-initialization path | X15 |
| D-Q13, D-Q15 | Answered | X19 |
| D-Q14 | Answered: identical by construction under engine2 | X14 |
| D-Q16 | Answered: engine2.h documents the concurrent read; D13's list is incomplete | X7 |
| D-Q22 | Answered for engine2 | X10 |
| D-Q23 | Same as A-Q24 | X7 |
| D-Q24 | Answered | X18 |
| E-Q7, E-Q8, E-Q10, E-Q11 | Answered | R12, R13, R11 |
| E-Q9 | Partly answered (licence of runtime, `expr` support) | R14 |
| E-Q14 | Partly answered: no stock RT kernel as of early-2025 reports; not re-checked for 2026 | §E5.3 |

---

## Part A — Engine core: structure, threads, realtime path, ABI1 coupling
Source: Wirescape snapshot 44da1e4, read by an LLM from source (no execution).

**How to read the citations**
- All file contents come from the bundle `A_engine_core.md`. **Every `path:N` is a line number in the bundle**, not in the repository file. Paths are shortened to file names:

| Short name | Full path | Bundle lines |
|---|---|---|
| `module2.h` | native/include/wirescape/module2.h | 49–171 |
| `engine2.h` | native/engine2/engine2.h | 175–279 |
| `engine2.cpp` | native/engine2/engine2.cpp | 283–1555 |
| `app_engine.h` | native/control/app_engine.h | 1559–1615 |
| `app_engine.cpp` | native/control/app_engine.cpp | 1619–1877 |
| `module_catalog.h` | native/control/module_catalog.h | 1881–1929 |
| `runtime_patch.h/.cpp` | native/document/runtime_patch.* | 1933–1946 / 1950–2047 |
| `engine.h` | native/include/wirescape/engine.h | 2051–2138 |
| `module.h` | native/include/wirescape/module.h | 2142–2211 |
| `ABI2_SPEC.md` | docs/specs/ABI2_SPEC.md | 2215–2311 |

- **Referenced but not in the bundle**, so not verified: `wirescape_sdk.h` (`ws::LinearRamp`, `ws::to_normal`, `ws::to_plain`, `ws::valid_event`, `ws::finite_samples`, `ws::port`, `ws::param`; engine2.cpp:289), `midi_release.h` (engine2.cpp:287), `module_catalog.inc` (module_catalog.h:1924), `runtime_module_config.h` (runtime_patch.cpp:1954), the ABI1 engine implementation (`ws_engine_*`), the `wirescape-engine` process main / JSON-lines I/O, and the audio device code. Statements about those are labeled (inf).

---

### A1. Component map

#### A1.1 Table

| Component | Where | Responsibility | Owns | Owned by / lifetime | Called by |
|---|---|---|---|---|---|
| ABI2 C types (`ws2_descriptor`, `ws2_process`, `ws2_event`, `ws2_host`, …) | module2.h:85–158 | C ABI boundary. Descriptor function table: `create, destroy, query_ports, memory_requirements, prepare, reset, process, save_state, load_state, latency_frames` (148–157). Entry `ws_module2_entry` (164–167) | — | Built-in descriptors are static ("Native descriptors are static", app_engine.cpp:1742) | `Node::d` |
| `engine2::Config` | engine2.h:187–195 | Limits and defaults | value | Copied into `Impl::cfg` (engine2.cpp:467) | `AppEngine::config` (app_engine.cpp:1694); `load_runtime_patch` (runtime_patch.cpp:1990–1997) |
| `Tap`, `Meter`, `FeedbackLoop`, `Outgoing` | engine2.h:198–215 | Telemetry endpoint, counter snapshot, loop report, egress record (payload `WS2_MAX_PAYLOAD`, 214) | — | values | `set_telemetry_taps`, `meter`, `feedback_loops`, `pop_egress` |
| `engine2::Engine` | engine2.h:226–278; engine2.cpp:1017–1554 | Public scheduler facade (pimpl); copy deleted (engine2.h:230) | `unique_ptr<Impl> p_` (227) | Member `AppEngine::engine` (app_engine.cpp:1642); temporary `Engine next` in `reconfigure` (engine2.cpp:1316) | `app_engine_*`; `load_runtime_patch` via `app_engine_native` (runtime_patch.cpp:2018) |
| `Engine::Impl` | engine2.cpp:466–557 | All graph and runtime state | `nodes` (`vector<unique_ptr<Node>>`), `edges`, `components`, `node_table`, `buses`, `producers` (`array<unique_ptr<Producer>,32>`), `egress`, `future` (`vector<Packet>`), `arena`, taps, atomics (467–494) | `Engine::p_`; swapped wholesale in `reconfigure` (1388), field by field in `replan` (1530–1538) | `Engine` methods |
| `Node` | engine2.cpp:383–427 | One module instance: ABI2 `d` **or** ABI1 `legacy`, plus `instance`, ports, params, buffers, event vectors, host allocations | `instance` (destroyed in `clear_instance`, 413–417); `allocations` via `Node::allocate` (418–425); `Buffer`s | `Impl::nodes`; moved between Impls by `replan` (1509) and `reconfigure` (1377) | `setup`, `process_node`, `emit` |
| `Parameter` | engine2.cpp:364–381 | Smoothing (`ws::LinearRamp base`), per-channel `offset[16]`, taper `plain()` (log/exp/step) | — | `Node::state` | `process_node` (879–907) |
| `Buffer` | engine2.cpp:311–322 | Planar floats, 32-byte aligned, `stride=(frames+7)&~7` | `memory` (`AlignedDelete`) | `Node::in/local_out/global_out/param`; `Edge::delay` | `setup` (589), `topology` (702) |
| `Edge` | engine2.cpp:456–460 | Cable; `kind` 0 signal, 1 event (1045), 2 modulation (1049); `back` flag; delay line for back-edges | `delay`, `delay_channels` | `Impl::edges` | `topology`, `process_node`, `render` |
| `Component` | engine2.cpp:461 | SCC with ordered `Node*` list and `loop` flag | raw pointers | `Impl::components` | `render` (1166) |
| `Bus` | engine2.cpp:462 | (node, port) → output channel | — | `Impl::buses` | `render` (1180) |
| `Packet` | engine2.cpp:323–329 | Queued event with fixed `std::array<uint8_t,WS2_MAX_PAYLOAD>` payload, timing mode, generation, revision, route origin | — | Ring slots, `future`, locals | `enqueue`, `collect`, `route`, `pop_egress` |
| `Ring` | engine2.cpp:331–350 | SPSC ring, `capacity+1` slots (333) | `vector<Packet> slots` | `Producer` | §2 |
| `Producer` | engine2.cpp:351–354 | `normal` and `critical` rings + `serial` | 2 Rings | `Impl::producers[i]`, `Impl::egress` | `register_producer` (1055); `finish_prepare` (628) |
| `Item` / `ordered` | engine2.cpp:355–362 | Pending event; sort key `(frame, !cleanup, order)` | — | `Node::pending` | `admit`, `process_node` |
| `Allocation` | engine2.cpp:363 | One host allocation record | — | `Node::allocations` | `allocate`, `clear_instance` |
| `Park` | engine2.cpp:463 | Replan handshake `Running, Requested, Parked, Cancelled` | — | `Impl::park` (482) | `render`, `replan`, `reset` |
| `AppEngine` | app_engine.cpp:1633–1696 | Internal facade, "not an ABI" (app_engine.h:1565): catalogue, node→entry map, engine2 instance, meters, master fade | `legacy` `shared_ptr<ws_engine>` (1638); `library_owners` (1639); `entries` `deque<Entry>` (1640); `nodes` `map` (1640); `engine` (1642); atomics (1643–1653) | Heap; `app_engine_create[_config]` (1697–1705) / `app_engine_destroy` (1706); `load_runtime_patch` hands it over with `engine.release()` (runtime_patch.cpp:2044) | `wirescape-engine` process (inf); `load_runtime_patch` |
| `AppEngine::Entry` | app_engine.cpp:1634–1637 | Per module type: `native` ws2 pointer (`nullptr` for entries from `app_engine_register_module`, 1710) + synthesized ABI1 `metadata` and its arrays | vectors | `entries` deque | `find` (1695), `app_engine_add_node_config` (1728) |
| `builtin_modules()` | module_catalog.h:1921–1928 | Function-local static `vector<const ws2_descriptor*>` via X-macro over `module_catalog.inc` | static | Process lifetime | `AppEngine` ctor (1662); `app_engine_parameter_id` (1877) |
| `load_runtime_patch` | runtime_patch.cpp:1980–2046 | Parses v1/v2 JSON patch, builds and prepares a new `AppEngine`; "Quiescent, Qt-free reader/graph builder" (runtime_patch.h:1941) | creates `AppEngine` | Returned to caller | Not in bundle (inf: app + headless runner, runtime_patch.h:1941) |
| `ws_engine` (ABI1) | engine.h:2064–2128 | ABI1 C API; implementation not in bundle | — | `AppEngine::legacy` | `AppEngine` ctor (1656); `app_engine_load_module` (1719) |
| `ws_module_descriptor` (ABI1) | module.h:2189–2204 | ABI1 function table (`create(sample_rate)`, `destroy`, `prepare`, `reset`, `event`, `process`) | — | — | `Node::legacy`; `Entry::metadata` |

#### A1.2 Text diagram

```
wirescape-engine process (not in bundle)
 ├─ load_runtime_patch(bytes, catalog AppEngine*, ws_engine_config) ──creates──┐
 └─ AppEngine  (heap; app_engine_create[_config] / app_engine_destroy) <──────┘
     ├─ legacy        : shared_ptr<ws_engine>     ABI1 engine, used as library loader
     ├─ library_owners: vector<shared_ptr<ws_engine>>  (app_engine_copy_modules)
     ├─ entries       : deque<Entry{native ws2_descriptor*, ws_module_descriptor metadata}>
     ├─ nodes         : map<node id, const Entry*>
     ├─ engine        : engine2::Engine
     │    └─ p_ : unique_ptr<Impl>
     │         ├─ nodes      : vector<unique_ptr<Node>> ── instance (ABI2 d / ABI1 legacy),
     │         │                                          allocations, Buffers, pending/events
     │         ├─ edges      : vector<Edge> ── delay Buffer (back-edges only)
     │         ├─ components : vector<Component{Node*…, loop}>  (render order)
     │         ├─ node_table : sorted vector<(id, Node*)>
     │         ├─ buses, taps, tap_values[], tap_counts[]
     │         ├─ producers  : array<unique_ptr<Producer{Ring normal, Ring critical}>,32>
     │         ├─ egress     : unique_ptr<Producer>
     │         ├─ future     : vector<Packet>  (reserved future_capacity)
     │         └─ arena      : vector<uint8_t> (message_arena_bytes)
     └─ meters / master fade atomics, master_gain (callback-owned)
```

**Destruction order.** `AppEngine` declares `legacy`, `library_owners`, `entries`, `nodes` before `engine` (app_engine.cpp:1638–1642), with the comment "Destroy the scheduler before the metadata and libraries its nodes borrow" (1641). Members are destroyed in reverse declaration order, so `engine` (and every `Node`, which calls `legacy->destroy`/`d->destroy` in `clear_instance`, engine2.cpp:414) goes first (mk).

**`event_outputs` context.** `Node::event_outputs[i]` carries `ctx = Impl*`: set by `setup` (597), rebound to the live `old` Impl by `replan` (1511–1513), rebound to `fresh` by `reconfigure` (1376) before `p_` is swapped (1388).

---

### A2. Threads and execution contexts

#### A2.1 Contexts

No threads are created in the bundle; the only thread primitive is `std::this_thread::yield` (engine2.cpp:1481). Contexts come from contract comments.

| Context | Evidence | Functions |
|---|---|---|
| **Quiescent control** | engine2.h:216–221; engine.h:2129–2134; runtime_patch.h:1941 | `Engine` ctor/dtor, `add_node`, `add_abi1`, `connect`, `modulate`, `output`, `register_producer`, `prepare`, `set_telemetry_taps` (before prepare, engine2.h:221), `set_parameter`, `set_channels`, `reset`, `transport`, `save_state`, `load_state`, `reconfigure`, `rebind_abi1_descriptor` (engine2.h:275); `load_runtime_patch`; `app_engine_prepare_master_fade_in` (app_engine.h:1601) |
| **Control owner, concurrent with render** | engine2.h:219–224, 263–265, 272–274; app_engine.h:1584 | `replan`, `read_telemetry` ("CONTROL-OWNER-ONLY", engine2.h:222), `refresh_latency` (engine2.h:263); `app_engine_replan`; `app_engine_begin_master_fade_out`, `app_engine_resume_master_fade`, fade queries (app_engine.cpp:1832–1858) |
| **Render (audio callback)** | engine2.h:218, 254; app_engine.h:1590–1594 | `render` → `publish_clock` (1152), `reset_processors`, `collect`, `admit`, `process_node`, `emit` → `route`; module `process`/`reset`/ABI1 `event`; `app_engine_render_live`, `_render_channels`, `_render` |
| **Ingress producers** (≤ 32, one writer each) | engine2.h:217; engine2.cpp:330, 1055 | `enqueue`. `AppEngine` registers 3: "producer 0 host keys, 1 MIDI service", "producer 2 OSC worker; idle without osc.in" (app_engine.cpp:1659–1661). `app_engine_enqueue` always uses producer 0 (1775). Threads for 1 and 2 not in bundle (inf); see B §B5a and X11 |
| **Egress consumer** | engine2.h:218; engine2.cpp:330 | `pop_egress`; single consumer (inf from SPSC contract) |
| **Any thread** | engine2.h:218 | `panic`, `meter` (`noexcept`) |

Re-entrancy guard: `rendering.test_and_set(acquire)` returns `WS2_STATE` if already rendering (1137); `Guard` clears it on scope exit (1142/1146/1148).

#### A2.2 Shared data and synchronisation

"default" = no order written, i.e. `seq_cst` (mk).

| Data | Writer → reader | Mechanism | Memory orders (line) |
|---|---|---|---|
| `Ring::head/tail` (ingress) | `enqueue` → `collect` | SPSC, capacity+1 | push: `head` relaxed, `tail` **acquire**, `head` **release** (335–337). pop: `tail` relaxed, `head` **acquire**, `tail` **release** (340–342). peek: relaxed/acquire (345–346) |
| `Ring::clear` | `reset` (quiescent) | consumer index forced | `head` acquire, `tail` release (349) |
| Egress rings | `route` push (832) → `pop_egress` peek/pop (1241–1244) | same SPSC | same |
| `egress_emergency` | `emergency()` (render), `panic()` (any) → `pop_egress` | flag | store **release** (523, 1250); `exchange` **acq_rel** (1235) |
| `generation` / `applied` | `panic`, `emergency`, `reset`, `reconfigure` → render, `enqueue`, `collect` | counter + ack | `panic` `fetch_add` **acq_rel** (1250). `emergency` loads **acquire**, CAS **acq_rel** (521–522). `enqueue` loads **acquire** (1111–1112). `collect` **acquire** (747). `render` compares default, `applied.store(release)` (1161, 1165, 1215). `route` default (822). `reset` default (1267–1268) |
| `park` | `replan` ↔ render | state machine | `replan`: load default (1405); CAS Running→Requested **acq_rel** (1472); spin load **acquire** (1474); CAS →Cancelled **acq_rel** (1477); store Running **release** (1552). `render`: load **acquire** (1153, 1221); store Running **release** (1160, 1228); CAS Requested→Parked **acq_rel**/fail **acquire** (1226–1227). `reset`: default (1271) |
| `revision` | `replan` → `enqueue`, `route` | stamps packets; `collect` drops `revision < born_revision` (767, 787) | `replan` load default (1419), store **release** (1547). `enqueue` **acquire** (1116). `route` default (823). `reconfigure` default (1387) |
| `tap_sequence`, `tap_values[]`, `tap_frame` | render → `read_telemetry` | sequence counter (odd = writing); reader ≤ 3 attempts (1077), else `frame=0` (1091) | writer: `fetch_add` **acq_rel** (1190), values **relaxed** (1208), `tap_frame` **relaxed** (1210), `fetch_add` **release** (1211). Reader: **acquire** (1078), data **relaxed** (1080–1083), `atomic_thread_fence(acquire)` (1085), re-load **relaxed** (1086). `replan` reset: relaxed / `tap_frame` **release** (1539–1540). `set_telemetry_taps`: relaxed (1067–1069) |
| `tap_counts[]` | `emit` → `read_telemetry` | counter | `fetch_add` **relaxed** (553); load relaxed (1083) |
| `position` | render → `meter`, `set_parameter`, `pop_egress` | frame counter | render: load **relaxed** (1151), store **release** (1157, 1214). Others default (1275, 1103, 1236). `reset` default (1262) |
| Counters `dropped, coalesced, ring_full, stale, late, emergencies, arena_full, faults, event_count` | render + producers (`ring_full`, `dropped`, `emergency()` in `enqueue`, 1120) → `meter` | `atomic<uint64_t>` `++` | default (e.g. 722, 1120; 1275) |
| `arena_used` | render (+ `meter`) | atomic | `store(0)` default (1162); `+=` default (735) |
| `latency` | `recompute_latency` via `refresh_latency` | atomic | store **relaxed** (650); `replan` default (1542) |
| `feedback_count`, `setup_bytes` | quiescent / `replan` | atomic | default (598, 679, 684, 1541, 1545) |
| `Node::latency`, `distance`, `bus_latency` (non-atomic) | `refresh_latency` (may overlap render) | plain; render doesn't read them (inf). Calls module `latency_frames` concurrently with `process` (1288); contract: modules "publish dynamic latency atomically from process()" (engine2.h:264) | none |
| Graph structures (`nodes`, `edges`, `components`, `node_table`, `buses`, `taps`, `future`, `replan_chokes`, per-node vectors) | `replan` → render | non-atomic; mutated only after render reports `Parked` (1474) and before `park.store(Running, release)` (1552). Parked render touches only `outputs`, `beat`, `position` (1154–1158) | via `park` acquire/release |
| `cfg.bpm`, `cfg.playing`, `beat` | `transport()` → render | plain | none |
| `Parameter::base`, `requested` | `set_parameter` → render | plain; refused after prepare once `position != 0` (1103) | none |
| AppEngine `master_fade` (0 unity, 1 fade-out, 2 silent block done, 3 fade-in requested, 4 begun; app_engine.cpp:1648) | control ↔ callback | single atomic command/ack | control store **release** (1835, 1849, 1853); callback load **acquire** (1782), CAS **release** (1821, 1823, 1825); queries **acquire** (1844, 1856) |
| `master_fade_out_requested_ns` / `_started_ns` | control → callback / callback → control | timestamps | requested: store **relaxed** (1834) before `master_fade.store(1, release)` (1835); load **acquire** (1787, 1841). started: store relaxed (1833); CAS **release**/fail **relaxed** (1790–1791); load **acquire** (1838) |
| `master_gain`, `master_step` | callback only (1647); exception: `app_engine_prepare_master_fade_in` writes `master_gain=0` quiescently (1848) | plain | none |
| `peak`, `blocks`, `channel_peaks[16]` | callback → meters | atomics | `peak` default (1828); `blocks` default (1829); `channel_peaks` **relaxed** (1798, 1816, 1869) |
| `AppEngine::error`, `nodes` map | `app_engine_replan` | plain | none (control-only, inf) |

#### A2.3 Replan handshake

| Step | Thread | Code |
|---|---|---|
| 1. CAS `Running→Requested` | control | engine2.cpp:1472 |
| 2. At the end of a block that saw `Requested`: linear fade-out, `fade_in=true`, CAS `Requested→Parked`; on failure store `Running` | render | 1221–1228 |
| 3. While `Parked`: write zeros, advance `beat`/`position`, return before `collect` | render | 1154–1158 |
| 4. Spin with `yield` until `Parked` or `timeout_ns`; on timeout CAS `Requested→Cancelled` | control | 1474–1482 |
| 5. Swaps, rebinding, `refresh_latency()`, `park.store(Running, release)` | control | 1487–1552 |
| 6. Render seeing `Cancelled` stores `Running` (1160); next block multiplies by `(i+1)/frames` if `fade_in` | render | 1216–1220 |
| Timeout bound | control | `timeout_ns ≤ uint64_t(3e9 * max_block / sample_rate)` (1411–1413) = 3 blocks; defaults 256/48000 → 16,000,000 ns = 16 ms (from engine2.h:188–189) |

---

### A3. Realtime path inventory

#### A3.1 Call tree on render

```
app_engine_render_live (app_engine.cpp:1778)        ← also via app_engine_render_channels/app_engine_render (1864–1867)
└─ Engine::render (engine2.cpp:1134, noexcept)
   ├─ Guard ctor/dtor (1138–1150)                    FP mode + rendering flag
   ├─ publish_clock (1124)                           only if callback_time_ns != UINT64_MAX (1152)
   ├─ [Parked → zero outputs, advance, return] (1154–1158)
   ├─ Impl::reset_processors (525)                   only if generation != applied (1161, 1165, 1215)
   │   └─ module reset (legacy->reset / d->reset) (527)
   ├─ Impl::collect (744)
   │   ├─ Ring::pop (339) ×producers×2 rings
   │   ├─ Impl::find (498) · valid_target (710) · map_time (503) · release (309 → midi_release, not in bundle)
   │   ├─ Impl::admit (719) → emergency (520)
   ├─ per component / per chunk: Impl::process_node (838)
   │   ├─ std::sort(pending) (841)
   │   ├─ Parameter::plain (373), ws::LinearRamp::next/set/jump, ws::to_normal (SDK, not in bundle)
   │   ├─ ABI2: d->process (938) ──module calls──► ws2_event_out.push = Impl::emit (547)
   │   │                                             └─ Impl::route (801) → admit / future.push_back / egress Ring::push (334) / map_frame (516)
   │   ├─ ABI1: legacy->process per span (917), legacy->event per event (925), ws::finite_samples (928)
   │   └─ pitch tap: std::pow (1001, 1003)
   ├─ loop delay-line write-back (1170–1175)
   ├─ bus mix (1178–1186), telemetry tap publish (1187–1212)
   └─ fade-in / park fade-out + CAS (1216–1229)
```

#### A3.2 Inventory matrix

Columns: **Alloc** heap allocation; **Locks** mutex/blocking wait; **Sys** system calls; **Exc** throw or throwing calls; **Log** logging; **Unb.** loops not bounded by config; **Cont.** `std::` container ops that may allocate; **Ind.** virtual / function-pointer calls. "none" = none found.

| Function (lines) | Alloc | Locks | Sys | Exc | Log | Unb. | Cont. | Ind. |
|---|---|---|---|---|---|---|---|---|
| `app_engine_render_live` (1778–1831) | none | none | none (time passed in) | none; not `noexcept`, calls `noexcept render` | none | none (channels × frames) | none | none |
| `render` (1134–1231) | none | none; `test_and_set` is a non-blocking try → `WS2_STATE` (1137) | none. **found** FP control writes `_mm_setcsr(fp\|0x8040)` (1141), `msr fpcr` bit 24 (1145) — CPU instructions, not syscalls; FTZ+DAZ / FZ meaning (mk) | `noexcept`; no `throw` | none | none; per loop chunk it scans **all** `edges` (1170) | none | none directly |
| `publish_clock` (1124–1132) | none | none | none | none | none | none | none | none |
| `reset_processors` (525–536) | none (`future.clear()` keeps capacity) | none | none | none | none | none; `fill_n` of `max_channels*stride` per back-edge (534) | none | **found**: `legacy->reset` / `d->reset` per node (527) |
| `collect` (744–799) | none; `future.push_back` guarded by `size()==capacity()` (777), reserved in ctor (496); `resize(keep)` shrinks (798) | none | none | none | none | none; chokes ≤ `release_reserve` (1452); `producer_count × 2 × ring_capacity` pops (760–764); `future` ≤ `future_capacity` | push/resize, capacity-guarded | none |
| `Ring::push/pop/peek` (334–348) | none | none | none | none | none | none | Slot copy of a `Packet` with 1472-byte payload, ≈1.6 KiB (inf) | none |
| `admit` (719–742) | none; `pending.push_back` (737) only when `size < event_budget` (727), reserved (594) | none | none | none | none | none; coalescing scan ≤ `event_budget` (729) | push_back, guarded | none |
| `valid_target`, `find` (prepared → `lower_bound`, 499), `map_time`, `map_frame`, `emergency` | none | none | none | none | none | none | none | none |
| `process_node` (838–1015) | none; `events.push_back` (843) reserved (594), count ≤ `pending.size()` ≤ `event_budget` (inf); `port_events[p].push_back` (844) reserved (593); `std::sort` (841) in place (mk) | none | none | none thrown; not `noexcept`; an escaping exception inside `noexcept render` → `std::terminate` (mk) | none | none; inputs×channels×frames; params×length×channels (892–904); mod edges×length (889). ABI1: each `span` refills constant inputs over full `frames` (914) → ≈(events+1)×inputs×frames (inf) | push_back, reserved | **found**: `d->process` (938); `legacy->process` per span (917); `legacy->event` per event (925). SDK `LinearRamp`, `to_normal`, `finite_samples` not in bundle |
| `Parameter::plain` (373–380) | none | none | none | none | none | none | none | none; per sample×channel×param (901); `exp`, `expm1`, `round`, `clamp` |
| Pitch tap (953–1014) | none | none | none | none | none | none; frames × min(channels, 8) (987–988) | none | none; `std::pow` (1001, 1003) |
| `emit` (547–556) | none | none | none | none | none | none | none | reached **through** `ws2_event_out.push` (597); `tap_counts` `fetch_add(relaxed)` (553) |
| `route` (801–836) | none; `future.push_back` capacity-guarded (814) | none | none | none | none | none; loops `outgoing[port]` (810) | two stack `Packet`s `p` (815), `out` (830), ≈1.6 KiB each (inf); payload `memcpy` (825, 831) | none; calls `ws::valid_event` (not in bundle) |

#### A3.3 Found items on the render path

| Item | Location |
|---|---|
| Indirect module calls `process`, `reset`, ABI1 `event` | 527, 917, 925, 938 |
| Module → engine re-entry via function pointer (`emit` → `route`) | 547, 597 |
| FP control-register writes per render | 1141 / 1145 |
| Per-sample transcendental math (`exp`/`expm1` LOG/EXP tapers; `pow` pitch tap) | 375–376, 1001, 1003 |
| Large `Packet` copies (≈1.6 KiB, inf) | 337, 342, 815, 830 |
| `seq_cst` atomics on `generation`/`applied`/counters | 1161, 1165, 1215, 822–823 |
| Only `atomic<float>` has a lock-free `static_assert` (1019); none for `atomic<uint64_t>` / `atomic<Park>` | 1019 |

**Not on the render path:** `fail()`/`error` writes (setup, topology, replan, reconfigure); `std::function` (`topology` 673, 684); `fprintf` (runtime_patch.cpp:2042); `steady_clock::now` (replan 1470/1475; `app_engine_clock_ns` 1861).

---

### A4. Graph lifecycle

#### A4.1 Steps

| Step | Function (lines) | Thread | Failure behaviour | Notes |
|---|---|---|---|---|
| Create | `Engine(Config)` (1017) → `Impl` ctor (495–497); `AppEngine` ctor (1656–1693) | quiescent | `make_unique`/`reserve` may throw; `app_engine_create[_config]` catch all → `nullptr` (1699, 1704) | Reserves `nodes` to `max_nodes`, `future` to `future_capacity`. `AppEngine` registers 3 producers, builds catalogue from `builtin_modules()` |
| Add node (ABI2) | `add_node` (1020–1032) | quiescent | `false` + `error`: "Invalid setup bounds" (1021) / "Invalid ABI2 node" (1024) / `setup` errors; node not inserted | Checks `max_channels` 1..16, `max_block` 1..4096, not prepared, `id≠0` and unique, count < `max_nodes`, all 10 function pointers, counts ≤ `WS2_MAX_PORTS`/`WS2_MAX_PARAMS`. **Calls `setup` immediately** (1030): create, `query_ports`, `prepare`, memory check (559–600) |
| Add node (ABI1) | `add_abi1` (1033–1040) | quiescent | "Invalid ABI1 node" (1034) | No `setup` at add time; ports/params synthesized via `ws::port`/`ws::param` (1036–1038) |
| Connect / modulate / bus | `connect` (1041), `modulate` (1047), `output` (1051) | quiescent | "Invalid connection", "Signal/event kind mismatch", "Signal input already connected" (1044), "Invalid modulation cable", "Invalid output bus" | kind 0/1/2; amount finite in [-1,1]; bus channel < 32 |
| Producers / taps | `register_producer` (1055), `set_telemetry_taps` (1056–1071) | quiescent, before prepare | `-1`; "Invalid telemetry tap…", "Duplicate telemetry tap endpoint" | |
| Prepare | `prepare` (1093–1101) → `setup` for **every** node (1099) → `finish_prepare` (624–630): `topology` (653–708), bus resolve, `resolve_taps`, `arena.resize`, egress `Producer` | quiescent; single use (1094) | Config ranges (1095–1097) → "Invalid engine2 configuration"; any failure → `false`, `prepared` stays `false` | `setup` starts with `clear_instance()` (560), so ABI2 instances from `add_node` are destroyed and recreated (inf, from 560, 1030, 1099). `topology`: Tarjan SCC, DFS back-edges, Kahn order within/across components, delay buffers `max_channels × feedback_block` (702) |
| Initial params / state | `set_parameter` (1102–1106); `load_state` (1304–1310); driven by `load_runtime_patch` after `prepare` (runtime_patch.cpp:2031–2034) | quiescent | `set_parameter` refused once `prepared && position≠0` (1103) | `load_state` cap 1 MiB (1305); `WS2_UNSUPPORTED` keeps bytes in `preserved` (1309) |
| Process | `render` (§3) | render | `WS2_INVALID` bad args (1135–1136); `WS2_STATE` re-entry (1137); module `process ≠ WS2_OK` → `++faults`, constant-zero outputs (938); non-finite ABI1 output → `++faults`, silence (927–929) | |
| Live replan | `app_engine_replan` (1731–1757) → `replan` (1402–1554) | control owner, concurrent with render | Pre-park checks leave live graph unchanged: self/unprepared/not `Running` (1405); config tuple differs or timeout 0 / > 3 blocks (1407–1413); revision exhausted (1420); "Surviving node ports changed" (1429); > `release_reserve` chokes (1452). Timeout → `Cancelled`, "Audio did not park before the edit deadline" (1477–1478). `app_engine_replan` catches `std::exception` (1753–1756) | Retained if `id` matches and `d`, `legacy`, `config` bytes equal (1426); others get `born_revision = next_revision` (1433). Candidate is a separately prepared engine (inf: e.g. from `load_runtime_patch`) |
| Reconfigure one node | `reconfigure` (1313–1389) | quiescent (engine2.h:216, 271) | All failures before the commit section (comment 1368): "Cannot stage reconfiguration", "Staged … failed", "Reconfiguration removes telemetry tap endpoint" (1355), "Staged state restore failed" (1360) | Builds `Engine next(old.cfg)`; only changed node creates DSP, others metadata-only (1326–1329); edges/buses/taps remapped **by ID**; unmappable → `dropped_connections` (1335, 1339); ends `p_.swap(next.p_)` (1388) |
| Reset | `reset` (1251–1272) | quiescent | — | Clears rings, resets processors, `position=0`, clock anchors reset, `generation++` with `applied` matched, clears `replan_chokes`, `park=Running` |
| Destroy | `~Engine` (1018) → `~Impl` → `~Node` → `clear_instance` (412–417) | quiescent | — | `destroy(instance)`, then aligned `operator delete` per allocation (415); `AppEngine` destroys `engine` before catalogue/library owners (1641–1642) |

#### A4.2 What survives

| State | `replan` (live `Impl` kept) | `reconfigure` (`Impl` replaced) |
|---|---|---|
| Retained node (instance, ramps, buffers, `pending`) | Kept, swapped into new list (1498–1510) | Kept except the changed node (1369–1378) |
| Changed / new node | Candidate's fresh instance | New instance; `state` copied (1322); ABI2 state via `save_state` → `load_state` (1360) |
| Back-edge delay lines | Swapped when edge key and both endpoints match (1456–1468, 1523–1529) | Swapped when edge doesn't touch the changed node (1365–1367, 1384) |
| Ingress rings / queued packets | Kept (comment 1483–1484) | New producers (1340); old packets not transferred (inf); `generation+1` makes them stale (1388) |
| `future` packets | Kept, except routed packets on removed `(from, output, to, port)` → `++stale` (1487–1497) | Not copied (inf) |
| Egress ring, arena | Kept | New (628) |
| `position`, `beat`, anchors, `frames_per_ns` | Kept | Copied (1386) |
| `generation` / `applied` | Unchanged | `old+1`, `applied` matched (1388) |
| `revision` | `+1`, release (1547) | Copied (1387) |
| Meter counters | Kept | Start at zero (inf) |
| Telemetry | Candidate's layout/arrays; `tap_sequence=0`, `tap_frame=0` (1537–1540) | Remapped by ID (1344–1358) |
| `pitch.enabled` on retained nodes | **Not** copied (1498–1510) | Copied (1375) |
| Release of removed event edges | `NOTE_CHOKE` (`flags=1`, `source_id=UINT32_MAX`, `cleanup=true`) to surviving destinations (1449–1454, 748–758) | None |
| Audible transition | Fade-out last block before park (1221–1224), zeros while parked, fade-in after (1216–1219) | None (quiescent) |
| Superseded nodes | End up in candidate's `nodes` (1509, 1530); destroyed with the candidate on the control side (engine2.h:273) | In `next`'s old `Impl`; destroyed when `reconfigure` returns |

---

### A5. Event and parameter path

#### A5.1 End-to-end path

| Stage | Function (lines) | Thread | What happens |
|---|---|---|---|
| 1. Host API | `app_engine_enqueue` (app_engine.cpp:1759–1777) | producer 0 (inf, 1660) | `ws_event` → `ws2_event`; defaults `channel=0`, `key=(int32_t)v->value`, `value=1`, `note_id=(int32_t)v->note_id` (1761); mapping in 5.2 |
| 2. Ingress | `enqueue` (1109–1122) | producer | `WS2_STATE` if not prepared, bad producer, `generation≠applied`, or nonzero `wanted_generation` mismatch (1110–1112); `ws::valid_event` fail → `WS2_INVALID` (1113). Packet gets `generation`, `revision` (acquire), `order=(producer<<48)\|(serial & 0x0000ffffffffffff)` (1117), payload `memcpy` (1118). Release → `critical` ring, else `normal` (1119). **Node/port not checked here** |
| 3. Ring full | 1119–1121 | producer | `++ring_full`; release → `emergency()`, else `++dropped`; `WS2_CAPACITY` |
| 4. Drain | `collect` (760–781) | render, once per call | Per producer, **critical first, then normal**, ≤ `ring_capacity` pops per ring (764). Drop: generation differs (`++stale`), node missing or `revision < born_revision` (`++stale`), `valid_target` fails (`++dropped`) |
| 5. Timing | 775–776 | render | `Frames`: absolute frame. `Immediate`: `block_start`. `Timestamped`: `map_time(ns) + max_block` (saturating) |
| 6. Future queue | 777–778, 782–798 | render | All drained packets enter `future` (full: release → `emergency()`, else `++dropped`). Packets ≥ `block_start+block_frames` kept; `< block_start` clamped and `++late` (796); rest → `admit` |
| 7. Admission | `admit` (719–742) | render | Budget, PARAM coalescing, arena copy, `pending.push_back` (5.3) |
| 8. Ordering | `process_node` (841), `ordered` (360–362) | render | `std::sort` by `(frame, !cleanup, order)` |
| 9. Delivery | 842–845, 877, 934–937 | render | `offset = frame − block_start − start`; **all** in `n.events` (`ws2_process.events`); `port < inputs.size()` also in `port_events[port]`; `WS2_DIRECT_PORT` only in `events` |
| 10a. ABI2 params | 879–907 | render | Applied per sample at `offset ≤ i` (893); plain-unit parameter buffers (5.5) |
| 10b. ABI1 events | 911–926 | render | `process` split at each offset, then `legacy->event`; PARAM, NOTE_ON, NOTE_OFF/CHOKE only; **others skipped** (924) |

#### A5.2 `ws_event` → `ws2_event` (app_engine.cpp:1761–1775)

| `ws_event.type` | Result | Notes |
|---|---|---|
| `WS_PARAMETER` (1) | `WS2_PARAM`, `index` = position where `metadata.parameters[i].id == parameter_id`, `value = v->value` | Unknown node → `WS_NOT_FOUND`; unknown param → `WS_INVALID` (1763–1765) |
| `WS_GATE` (4) | `value>0` → `NOTE_ON`, else `NOTE_OFF`; `key=60` (1773) | Native nodes other than `essentials.adsr`/`host.keyboard` → **`WS_OK` without enqueueing** (1770–1772) |
| `WS_NOTE_ON` (2) | `NOTE_ON`, `key=(int)value`, `value=1` | Velocity fixed at 1 |
| anything else | `NOTE_OFF` (1774) | Includes `WS_NOTE_OFF` and unknown types |
| Enqueue | producer **0**, `WS2_DIRECT_PORT`, `time=v->frame`, `Timing::Frames`, `generation=v->generation` (1775) | `WS2_OK`→`WS_OK`, `WS2_CAPACITY`→`WS_CAPACITY`, else `WS_INVALID` (1776) |

#### A5.3 Budgets, reserves, coalescing

| Mechanism | Code | Rule |
|---|---|---|
| Release classification | `release()` (309) | `NOTE_OFF \|\| NOTE_CHOKE \|\| midi_release(e)` (`midi_release` not in bundle) |
| Budget counters | `ordinary_used`, `critical_used`, reset per render (1162) | Shared by **all nodes** in one call |
| Full test | `admit` (727) | `pending.size() ≥ event_budget`, or `ordinary+critical ≥ event_budget`, or (non-release and `ordinary ≥ event_budget − release_reserve`). Defaults 1024/256 → ordinary cap 768 per call; the product sidecar config is 2048/256 → 1792 [R7][X9] |
| Emission budget | `route` (804–807) | Emission spends one unit, then each fan-out destination another in `admit` (812); ABI2_SPEC.md:2259 agrees |
| Coalescing | `admit` (729) | Only when full, only `WS2_PARAM`; first pending PARAM with same `index`, `source_id`, `channel` overwritten, `++coalesced`; `port` not matched |
| Over budget | 730, 805 | Release → `emergency()`; other → `++dropped` |
| Payload | 733–736 | Dropped (`++arena_full`, `++dropped`) if `bytes > 1472`, `data == null`, or no arena room; per-call arena reset at 1162 |
| Validation | `valid_target` (710–718) | Port must be `WS2_DIRECT_PORT` or an event input; PARAM/PARAM_MOD `index < parameters.size()`; PARAM value outside `[min,max]` dropped (not clamped); PARAM_MOD value not checked |
| Emergency | `emergency()` (520–524) | If `generation == applied`, CAS `+1` and `++emergencies`; always sets `egress_emergency`. Next render check (1161/1165/1215) runs `reset_processors`: modules reset, ramps reset, offsets zeroed, `pending` cleared, delay lines zeroed, `future` cleared (525–536). `pop_egress` returns synthesized `NOTE_CHOKE` (`note_id=-1`, `channel=-1`, `source_id=UINT32_MAX`, `flags=1`) (1235–1238) |
| Replan chokes | `collect` (748–759) | At `block_start`, `order=0`, `cleanup=true` (sort first); release budget; count ≤ `release_reserve` (1452) |

#### A5.4 Ordering keys

| Source | `order` | Line |
|---|---|---|
| Replan choke | `0`, `cleanup=true` | 756 |
| Producer ingress | `(producer << 48) \| serial(48 bits)` | 1117 |
| Module emission | `(1 << 63) \| sequence++` | 812, 824 |
| Egress copy | `sequence++` (top bit clear) | 830 |

At equal frames: cleanup chokes, then ingress by producer and serial, then module emissions in traversal order. ABI2_SPEC.md:2259: "(absolute frame, producer index, producer serial)".

#### A5.5 Parameter evaluation (ABI2)

| Aspect | Code | Detail |
|---|---|---|
| Base | `ws::LinearRamp` in normalized space (365) | `set()` non-stepped, `jump()` `WS2_STEPPED` (894); `next()` per sample (897). Ramp length not in bundle; spec says 5 ms linear (ABI2_SPEC.md:2245) |
| PARAM_MOD offset | `offset[16]` (366, 895) | `channel < 0` fills all; else `offset[channel]` if `< max_channels`. **Persists across blocks** until replaced or `reset_processors` (532) |
| Cable modulation | `modulation_sum` (887–890, 900) | `Σ amount × source_sample` per channel/sample in `double` |
| Effective value | 899–901 | `plain(base + offset[c] + Σmod)`: clamp x to [0,1]; LOG `exp(log_min + x·log_ratio)`; EXP `expm1(curve·x)/expm1(curve)` if \|curve\| > 1e-8; `step` quantize; clamp [min,max] (373–380) |
| Channels | 884 | `channels` only if poly **and** `WS2_PER_VOICE`, else 1 |
| Constant flag | 880–883, 891–905 | From `base.constant()`; cleared by non-constant/back-edge mod sources or any PARAM/PARAM_MOD on this index; re-set if all samples equal sample 0 |
| Sample accuracy | 893 | Exact `offset` within the chunk |
| Pre-render init | `set_parameter` (1102–1106) | `base.set` (ramped), `requested=true`; refused once `prepared && position ≠ 0` (1103) |

**ABI1 nodes:** per-sample parameter loop skipped (879). PARAM `jump`s `state[index].base` and is forwarded as `WS_PARAMETER` with `legacy_index` (921). Smoothing is up to the module. Synthesized ABI1 params are `WS2_STEPPED`, `WS2_LINEAR` (1038).

#### A5.6 Timestamps, clock, transport

| Item | Code | Detail |
|---|---|---|
| Anchor | `publish_clock` (1124–1132) | From `render` when `callback_time_ns ≠ UINT64_MAX` (1152); slope clamped to nominal ×[0.999, 1.001], EWMA `+= (measured − fpn)/16`; non-monotonic rejected |
| ns → frame | `map_time` (503–515) | Exact integer path for integer rate with nominal `frames_per_ns`; else `floor(delta × frames_per_ns)` in `long double`; saturates |
| Live callers | app_engine.h:1590–1593 | `app_engine_render_live(callback_time_ns)`; `app_engine_clock_ns` = `steady_clock` ns (app_engine.cpp:1859–1863); comment names "MIDI SystemMonotonic, service chokes" |
| Offline | `app_engine_render_channels` passes `UINT64_MAX` (1865) | No anchor update |
| Transport to modules | 931–933 | Per node per chunk: `PLAYING` or 0, `bpm`, `beat` at chunk start, `bar_start = floor(beat/4)·4`, **4/4 fixed**, loop 0; `RECORDING`/`LOOPING` never set; ABI1 gets no transport |
| Transport source | `transport` (1273) | Non-atomic `cfg.bpm`, `cfg.playing`, `beat`; `beat` advances per render (1156, 1213) |
| `TRANSPORT_EVENT`, `MIDI`, `MESSAGE`, `NOTE_EXPRESSION` | — | Routed opaque; no decoding found; spec says "reserved" (ABI2_SPEC.md:2259) |

#### A5.7 Egress

- Every accepted emission also goes to `egress->critical`/`normal` with `mapped_time_ns = map_frame(frame)` (830–834). Full → release: `emergency()`, else `++dropped`; `emit` returns `WS2_CAPACITY` (555).
- `pop_egress` (1233–1249): emergency choke first; otherwise merges both rings by `(when, order)`, ≤ `2 × ring_capacity` iterations, stale generation → `++stale`.
- Comment: "this headless slice does not perform I/O" (828–829). Consumer not in bundle.

#### A5.8 Limits on this path

| Constant | Value | Valid range |
|---|---|---|
| `event_budget` | 1024 (engine2.h:190); `AppEngine` overrides with `max_events` (app_engine.cpp:1694); the sidecar passes 2048 [X9] | 2..65536 (1096) |
| `release_reserve` | 256 | 1..`event_budget−1` (1096) |
| `ring_capacity` | 256 per ring; 2 rings/producer; +1 slot (333) | 1..65536 (1055, 1096) |
| Producers | 32 slots (472); `AppEngine` uses 3 | `producer_count == 32` → −1 (1055) |
| `future_capacity` | 4096 | 1..65536 (1096) |
| `message_arena_bytes` | 1,507,328 | ≤ 64 MiB (1097) |
| `WS2_MAX_PAYLOAD` | 1472 (module2.h:70) | — |
| Replan chokes / edit | ≤ `release_reserve` (1452) | — |
| Timestamped offset | + `max_block` (776) | — |
| Clock slope | ±0.1%; EWMA 1/16 (1129–1130) | — |
| `read_telemetry` retries | 3 (1077) | — |

---

### A6. ABI1 coupling

Status: **Live** = product path for every build/patch. **Live-if-ABI1** = only when an ABI1 module library is loaded (inf; all built-ins are `ws2_descriptor`s, module_catalog.h:1921–1928). **Compat/test** = other.

#### A6.1 engine2

| # | Location | Use | Status |
|---|---|---|---|
| E1 | engine2.h:184 | Forward decl `struct ws_module_descriptor` in public header | Live (compile dep) |
| E2 | engine2.cpp:288 | `#include "wirescape/module.h"` | Live (compile dep) |
| E3 | engine2.h:232; engine2.cpp:1033–1040 `add_abi1` | Ports → `WS2_FIRST`; `WS_AUDIO`→`WS2_AUDIO`, else `WS2_ANY`; **unpatched 1.0 for input id `"gain_cv"`** (1036); params `WS2_STEPPED`/`WS2_LINEAR`, `legacy_index = v.id`, id `std::to_string(v.id)` (1038); no `setup` at add | Live-if-ABI1 |
| E4 | engine2.cpp:386, 388, 408 | `legacy`, `legacy_ids`, `legacy_in`, `legacy_out`; `legacy_*` resized for **every** node (595) | Live (fields) |
| E5 | 414 `clear_instance` | `legacy->destroy` vs `d->destroy` | Live-if-ABI1 |
| E6 | 527 `reset_processors` | `legacy->reset` | Live-if-ABI1 |
| E7 | 562–566 `setup` | `legacy->create(sample_rate)`; `ws_module_config{…, generation.load()}`; replays `requested` params as `WS_PARAMETER` with `legacy_index`, `ws::to_plain` | Live-if-ABI1 |
| E8 | 839, 856, 879 | `direct = !loop && !legacy` (no aliasing for ABI1); channel inference and param loop skipped | Live (branch per node) |
| E9 | 911–929 | Mono only (`data[0]`); split at event offsets; constant inputs expanded; PARAM/NOTE_ON (`value = key`)/NOTE_OFF+CHOKE, others dropped; `note_id` cast to `uint32_t`; non-finite → `++faults`, silence | Live-if-ABI1 |
| E10 | 429, 452 | OscPitch and Param taps rejected for ABI1 | Live (validation) |
| E11 | 1105 `set_parameter`; 1107 `set_channels` | Direct `WS_PARAMETER` on calling thread; ABI1 channels must be 1 | Live-if-ABI1 |
| E12 | 1299, 1305 | `save_state`/`load_state` empty/`WS2_INVALID` for ABI1 | Live (guard) |
| E13 | 1320, 1324, 1360 `reconfigure` | Re-add via `add_abi1`, explicit `setup`, no state transfer | Live-if-ABI1 |
| E14 | 1426 `replan` | `prior->legacy == n.legacy` in retained identity | Live (comparison); relies on E15 |
| E15 | engine2.h:275–276; engine2.cpp:1391–1400 `rebind_abi1_descriptor` | Replaces `Node::legacy` if id, 5 function pointers, 3 counts match; `reset` not compared (1394–1396) | Live-if-ABI1 (called from A9) |
| E16 | module2.h:93 `ws2_param::legacy_index` | ABI2 field used as ABI1 param id (921, 566, 1105; app_engine.cpp:1674) | Live (catalogue metadata) |

#### A6.2 AppEngine / control

| # | Location | Use | Status |
|---|---|---|---|
| A1 | app_engine.h:1563 | Includes `engine.h`; facade typed in `ws_engine_config`, `ws_module_descriptor`, `ws_event`, `ws_meter`, `WS_*` codes; comment "Legacy structures are UI metadata only" (1565) | Live |
| A2 | app_engine.cpp:1638, 1656 | Every `AppEngine` creates an ABI1 engine via `ws_engine_create`, deleter `ws_engine_destroy` | Live (incl. each patch-load engine, runtime_patch.cpp:1999) |
| A3 | 1694, 1701 `config`/`AppEngineConfig` | Copies `sample_rate`, `max_block_frames`, `max_nodes`, `max_events`→`event_budget`; rest engine2 defaults | Live |
| A4 | 1634–1637, 1662–1692 | Synthesized `ws_module_descriptor metadata` per built-in (`WS_ABI_VERSION`, 6 function pointers `nullptr`); `WS2_AUDIO`→`WS_AUDIO`, else `WS_CONTROL`; param id = `legacy_index` | Live (catalogue keyed on `metadata.id`, 1695) |
| A5 | 1719 `app_engine_load_module` | `ws_engine_load_module`, then registers all ABI1-engine modules | Live-if-ABI1 (caller not in bundle) |
| A6 | 1710 `app_engine_register_module` | Copies descriptor into new `Entry` (`native=nullptr`), dedup by id | Live (also runtime_patch.cpp:2000) |
| A7 | 1711–1718 `app_engine_copy_modules` | Keeps ABI1 library owners alive | Not called in bundle; unknown |
| A8 | 1728 `app_engine_add_node_config` | `native` → `add_node`; else `add_abi1(&metadata)` **only if `config` empty** | Live / Live-if-ABI1 (branch) |
| A9 | 1743 `app_engine_replan` | `rebind_abi1_descriptor` for candidate nodes with null `native`, pointing at live metadata | Live-if-ABI1 |
| A10 | 1758 `app_engine_initialize_parameter` | Lookup by **ABI1 numeric id** | Live (runtime_patch.cpp:2033) |
| A11 | 1759–1777 `app_engine_enqueue` | `ws_event` input; `WS_GATE` special cases | Live (inf), producer-0 host keys |
| A12 | 1874 `app_engine_get_meter` | `ws_meter`; `queued_events`, `overload_blocks`, `overload_reason` hard-coded 0; `overflow_events = dropped` | Live (caller not in bundle) |
| A13 | 1870–1871, 1875 | `activate`/`deactivate` no-ops; `build_essentials` ignores directory, builds VCO→VCA←ADSR→Output (ids 1–4) as engine.h:2126–2127 describes | Compat/test (inf) |
| A14 | 1707 | `app_engine_abi_version()` returns 2 | Live |
| A15 | 1877 `app_engine_parameter_id` | Built-ins: ABI2 string id; others: `std::to_string` of ABI1 id in a `thread_local std::string` | Live (runtime_patch.cpp:2033) |
| A16 | 1667–1691 | `deque<Entry>` gives `metadata` a stable address that `Node::legacy` borrows | Live-if-ABI1 |

#### A6.3 Runtime patch loader

| # | Location | Use | Status |
|---|---|---|---|
| R1 | runtime_patch.h:1943–1945 | Signature takes `const ws_engine_config&` | Live |
| R2 | runtime_patch.cpp:2001–2010 | Module lookup via `app_engine_module` (`ws_module_descriptor`) by id | Live |
| R3 | 2017 | Port names resolve against **ABI1 metadata** arrays, not `query_ports` | Live |
| R4 | 2024 | Modulation targets via `graph.descriptor(to)->params`; null for ABI1 nodes → "Invalid cable graph" | Live |
| R5 | 2028 | v1 `outputNode` port 0 → bus channels 0 **and** 1 | Live (v1) |
| R6 | 2033 | v1 param keys = ABI1 numeric ids; v2 uses `app_engine_parameter_id`; applied via A10 | Live |
| R7 | 2020–2025 | v1 cable kinds `"audio"`/`"control"` accepted | Live (v1) |

#### A6.4 ABI1 headers

| # | Location | Content | Status |
|---|---|---|---|
| H1 | engine.h:2096–2128 | `ws_engine_*` API; documented "at most 256 queue entries examined and 64 graph spans" with overload silencing (2115–2117), not present in engine2 | Implementation not in bundle; only `ws_engine_create`, `_destroy`, `_load_module`, `_module_count`, `_module` called (A2, A5) |
| H2 | module.h:2157–2207 | ABI1 module contract (`WS_ABI_VERSION 1`) | Live-if-ABI1 |
| H3 | ABI2_SPEC.md:2219, 2289, 2301 | "ABI 1 remains unchanged"; "engine2 validates ABI 1 shim outputs once"; ABI1/ABI2 binaries "not interchangeable" | Documentation |

---

### A7. Code shape

#### A7.1 The 15 longest or densest functions

Lines = bundle range inclusive. Branches = approximate hand count of `if`/`else if`/`else`/`for`/`while`/`?:`, including lambdas; `&&`/`||` not counted. **Approximate.**

| # | Function | Lines | Length | Branches | Notes |
|---|---|---|---|---|---|
| 1 | `Impl::process_node` | engine2.cpp:838–1015 | 178 | ≈110 | 5 lambdas (`raw_channels`, `value`, `span`, `signal`, `parameter`); ABI2 path, ABI1 path, pitch tap in one function |
| 2 | `Engine::replan` | 1402–1554 | 153 | ≈40 | clang-format style; lambdas `limits`, `key`, `erase(remove_if)` (1487–1497) |
| 3 | `Engine::render` | 1134–1231 | 98 | ≈55 | 3 preprocessor branches for `Guard` (1139–1149) |
| 4 | `Engine::reconfigure` | 1313–1389 | 77 | ≈50 | Compressed; 1333, 1339, 1366 each hold a loop, conditions, several statements |
| 5 | `load_runtime_patch` | runtime_patch.cpp:1980–2046 | 67 | ≈60 | Many `version==1 ? … : …`; 2024, 2025, 2029, 2033 each hold whole loops/branches |
| 6 | `Impl::topology` | engine2.cpp:653–708 | 56 | ≈55 | Densest block. Two **recursive** `std::function` lambdas: `visit` (Tarjan, 673–677), `dfs` (684). Depth ≤ node count (≤ 1024 per 1095) (inf). Edge scans inside node loops (675, 684, 686, 690) → O(N·E) or worse (inf) |
| 7 | `Impl::collect` | 744–799 | 56 | ≈22 | |
| 8 | `app_engine_render_live` | app_engine.cpp:1778–1831 | 54 | ≈25 | |
| 9 | `Impl::setup` | engine2.cpp:559–600 | 42 | ≈30 | 571–572 is a 7-operand condition; `check_ports` (581–586) O(P²) duplicate scan |
| 10 | `AppEngine::AppEngine` | app_engine.cpp:1656–1693 | 38 | ≈8 | 16-field aggregate init (1676–1691) |
| 11 | `Impl::route` | engine2.cpp:801–836 | 36 | ≈25 | |
| 12 | `app_engine_replan` | app_engine.cpp:1731–1757 | 27 | ≈10 | |
| 13 | `Impl::admit` | engine2.cpp:719–742 | 24 | ≈12 | 727: 3-clause condition; 729: loop, `if`, 3 statements |
| 14 | `Engine::read_telemetry` | 1072–1092 | 21 | ≈8 | |
| 15 | `app_engine_enqueue` | app_engine.cpp:1759–1777 | 19 | ≈12 | 1764: `while` + 3 statements |

**Short functions with very long conditions:** `add_node` 1022–1024 (≈26 `||` clauses); `prepare` 1095–1097 (≈22); `add_abi1` 1034 (one line, 12 clauses + return); `modulate` 1048 (two `find`s + 10 clauses); `rebind_abi1_descriptor` 1393–1396 (11 clauses).

#### A7.2 Lines holding several statements

**A. Braceless `if` followed by more statements on the same line** (only the first is guarded):

| Line | Pattern | Guarded | Always executed |
|---|---|---|---|
| engine2.cpp:825 | `if(source.bytes)std::memcpy(...);p.fix();future.push_back(p);` | `memcpy` | `p.fix()`, `push_back` |
| 831 | `if(source.bytes)std::memcpy(...);out.fix();` | `memcpy` | `out.fix()` |
| 1118 | `if(event.bytes)std::memcpy(...);packet.fix();` | `memcpy` | `packet.fix()` |
| 1247 | `if(out.event.bytes)std::memcpy(...);out.event.data=...;return true;` | `memcpy` | assignment, `return` |
| 1026 | two `if(...)assign(...)` on one line | separate `if`s | — |
| 1309 | `if(...)...;else if(...)...;return result;` | if/else-if | `return` |
| 500 | `for(...)if(...)return n.get();return nullptr;` | loop body | `return nullptr` |
| 805 | `if(release(source))emergency();else ++dropped;return false;` | if/else | `return` |

**B. Closing brace followed by a statement:** engine2.cpp:691, 701, 798, 835–836, 952, 1121, 1131, 1248.

**C. Whole function bodies on one line:** engine2.cpp:1055 `register_producer`; 1102 `set_parameter` (first line: 4 statements, 2 `if`s); 1107 `set_channels`; 1273 `transport`; 1275 `meter`; 1278–1282 `descriptor`, `output_channels`, `output_constant`, `output_sample`, `feedback_edges`; 1311 `preserved_state` (function-local `static`). app_engine.cpp:1694 `config`; 1710 `register_module`; 1719 `load_module`; 1728 `add_node_config`; 1758 `initialize_parameter`; 1868 `reset`; 1874 `get_meter`; 1875 `build_essentials` (8 calls chained with `||` + ternary); 1877 `parameter_id` (2 loops, `thread_local`, 3 returns). runtime_patch.cpp:1967 `id()`.

**D. Loop + nested conditions + several statements on one line:** engine2.cpp:337, 342 (`Ring` push/pop); 499 (`find`); 665, 675, 676, 684, 697 (`topology`); 868, 914, 921, 938, 951 (`process_node`); 1038 (`add_abi1`); 1172–1173 (`render`); 1294 (`feedback_loops`); 1301, 1307 (inline writer/reader lambdas); 1333, 1339, 1366 (`reconfigure`). runtime_patch.cpp:1974–1976 (base64), 1983–1986 (parse callback), 2017 (`port`), 2024, 2025 (cables), 2029 (outputs), 2033 (parameters).

#### A7.3 Mixed formatting

- engine2.cpp mixes **compressed** style (no spaces, several statements per line: 311–427, 838–952, 1020–1122, 1313–1389) and **clang-format-like** style (4-space, one statement per line: 428–455, 719–742, 744–799 partly, 953–1014, 1251–1272, 1402–1554).
- app_engine.cpp uses 1-space indentation in `AppEngine` (1634–1696) and functions up to 1730; later functions (1722–1726, 1731–1757, 1778–1866) use 4-space.

---

### A8. Limits and constants

#### A8.1 ABI2 header (module2.h)

| Constant | Value | Line |
|---|---|---|
| `WS_ABI2_VERSION` | `2u` | 66 |
| `WS2_MAX_CHANNELS` | `16u` | 67 |
| `WS2_MAX_PORTS` | `32u` per direction (engine2.cpp:571, 1024) | 68 |
| `WS2_MAX_PARAMS` | `64u` ("raised from 32 (additive, #402)") | 69 |
| `WS2_MAX_PAYLOAD` | `1472u` bytes | 70 |
| `WS2_DIRECT_PORT` | `UINT32_MAX` | 71 |
| `ws2_event.ump` | 4 words | 103 |

#### A8.2 engine2 Config defaults and ranges

| Field | Default (engine2.h:188–194) | Accepted range (engine2.cpp) |
|---|---|---|
| `sample_rate` | 48000 | finite, 1000..384000 (1095) |
| `max_block` | 256 | 1..4096 (1021, 1095) |
| `max_channels` | 16 | 1..16 (1021, 1095) |
| `max_nodes` | 64 | 1..1024 (1095); add rejected at `size ≥ max_nodes` (1022, 1034) |
| `event_budget` | 1024 | 2..65536 (1096) |
| `release_reserve` | 256 | 1..`event_budget−1` (1096) |
| `ring_capacity` | 256 (+1 slot, 333) | 1..65536 (1055, 1096) |
| `future_capacity` | 4096 | 1..65536 (1096) |
| `message_arena_bytes` | 1,507,328 | ≤ 64 MiB (1097); 0 not rejected |
| `feedback_block` | 32 | 1..`max_block` (1097) |
| `bpm` | 120 | finite, > 0 in `transport()` (1273) |
| `playing` | true | — |
| `epoch_ns` | 0 | — |
| `seed` | 1 (per node `seed + id`, 561) | — |
| `max_taps` | 256 | ≤ 4096 (1097); `set_telemetry_taps` rejects `size > max_taps` (1058) |

#### A8.3 Hard-coded engine2 limits

| Limit | Value | Location (engine2.cpp) |
|---|---|---|
| Producers | 32 | 472, 1055 |
| Bus channels (`output`) | < 32 | 1052 |
| `bus_latency` | 32 | 470 |
| `render` output channels | ≤ 32 | 1135 |
| `bus_written` | `bool[32]` | 1179 |
| Buffer alignment | 32 bytes | 310, 318 |
| Buffer stride | multiple of 8 frames | 317 |
| Host allocations per node | 64 | 560, 420 |
| Max one host allocation | 128 MiB | 420 |
| Min host alignment | 32, power of two | 420–421 |
| State blob save / load | 1 MiB / 1 MiB | 1301 / 1305 |
| Payload per packet / `Outgoing` | 1472 | 327; engine2.h:214 |
| Producer order bits | `<< 48`; serial 48 bits | 1117 |
| Emission order flag | `1 << 63` | 812, 824 |
| Timestamped offset | + `max_block` | 776 |
| Clock slope / EWMA | ×[0.999, 1.001]; 1/16 | 1129–1130 |
| Replan park deadline | ≤ `3e9 × max_block / sample_rate` ns, > 0 | 1411–1412 |
| Replan chokes | ≤ `release_reserve` | 1452 |
| `read_telemetry` attempts | 3 | 1077 |
| Delay line per back-edge | `max_channels × feedback_block` floats | 702 |
| FP mode x86 / AArch64 | `MXCSR \| 0x8040` / `FPCR \| (1<<24)` | 1141 / 1145 |
| Park fades | one block, linear | 1218, 1223 |
| Transport | 4/4, `bar_start = floor(beat/4)·4`, loop 0/0 | 931–933 |
| Pitch tap voices | `min(channels, 8)` | 988 |
| Pitch tap VCO constants | 261.6255653005986 Hz, `/220`, 440 Hz, note 69, `/12` | 1001–1003 |
| Pitch tap macro constants | 60 + `12 × pitch`, clamped ±96 | 1010–1012 |
| Pitch tap module ids | `"essentials.vco"`, `"ports.macro_oscillator"` | 430–431 |
| Pitch tap port/param ids | `"pitch"`, `"frequency"`, `"coarse"`, `"trigger"`, `"gate"` | 437–441 |
| Taper epsilon | `\|curve\| > 1e-8` | 376 |
| ABI1 `"gain_cv"` unpatched | 1.0 | 1036 |
| Modulation amount | finite, [−1, 1] | 1048 |

#### A8.4 AppEngine

| Limit | Value | Line |
|---|---|---|
| Peak meter channels | 16 | 1645 |
| Master fade length | `max(1, floor(sample_rate × 0.01))` samples (10 ms) | 1657–1658 |
| Producers registered | 3 | 1659–1661 |
| `WS_GATE` key | 60 | 1773 |
| Config mapping | `sample_rate`, `max_block_frames`, `max_nodes`, `max_events` only | 1694 |
| `app_engine_abi_version` | 2 | 1707 |
| Master fade states | 0..4 | 1648 |

#### A8.5 Runtime patch loader

| Limit | Value | Line |
|---|---|---|
| Patch size | 2 MiB | runtime_patch.h:1940; 1982 |
| JSON nesting | ≤ 64 | 1983 |
| Duplicate JSON keys | rejected | 1985 |
| Patch version | 1 or 2 | 1988 |
| Modules / connections | ≤ 64 / ≤ 128 | 1989 |
| IDs | 1..`UINT32_MAX` | 1967 |
| `max_block_frames` setting | ≤ 4096; validated, not applied (Q11) | 1993 |
| `max_channels` setting | ≤ 16 (0 rejected later by `prepare`) | 1995 |
| `feedback_block` setting | ≤ `config.max_block_frames` | 1996 |
| `timing_mode` | `"immediate"`/`"timestamped"`; validated only (inf) | 1994 |
| `sample_rate` setting | finite, > 0; validated only (inf) | 1992 |
| v2 bus channel | 0..15 | 2029 |
| v1 output | port 0 → channels 0 and 1 | 2028 |
| Modulation amount | finite, \|x\| ≤ 1 | 2024 |
| State `version` | ≥ 0 | 1970 |
| Base64 length | multiple of 4 | 1971 |

#### A8.6 ABI1 header and spec

| Item | Value | Line |
|---|---|---|
| `WS_ABI_VERSION` | 1 | module.h:2157 |
| ABI1 per-render work | "at most 256 queue entries examined and 64 graph spans" | engine.h:2115 |
| Spec engine limits | "16 voice channels, 32 ports/parameters/producers, 1–4096 prepared block frames, 1024 nodes maximum … event budget1024/release reserve256, payload1472, and 1 MiB quiescent state blob cap … 128 MiB per allocation and 64 allocations per node. Default arena is 1472 KiB" | ABI2_SPEC.md:2307 |
| Spec feedback default | 32 frames | ABI2_SPEC.md:2267 |
| Spec parameter ramp | 5 ms linear (ramp code in `wirescape_sdk.h`, not in bundle) | ABI2_SPEC.md:2245 |
| Spec gate thresholds | on > 0.5, off < 0.25 | ABI2_SPEC.md:2237 |
| Spec trigger | rising pulse ≥ 1 ms | ABI2_SPEC.md:2237 |

---

### A9. Open questions

**Contracts and threading**

1. `refresh_latency` calls module `latency_frames(instance)` while `process` may run (engine2.cpp:1288; engine2.h:263–264). module2.h doesn't say this is safe. Is that guarantee part of ABI2, and where is it documented? **[Narrowed: X7]**
2. `transport()` (1273) writes non-atomic `cfg.bpm`, `cfg.playing`, `beat`; `set_channels` (1107) writes `forced_channels`. Neither is in the cross-thread list (engine2.h:216–225). Does the product call either while audio runs? **[Narrowed: X8]**
3. `set_parameter` is allowed after `prepare` while `position == 0` (1103) and writes render-owned ramp state. Is there a guarantee no render has started by then?
4. `process_node`, `collect` and `route` aren't `noexcept` but run inside `noexcept render` (1134). What guarantees no C++ exception crosses from a module into `render` — only the SDK barrier (ABI2_SPEC.md:2305)? **[Pending D: SDK exception barrier]**
5. The threads behind producers 1 (MIDI) and 2 (OSC), the egress consumer, and callers of `refresh_latency`/`read_telemetry` aren't in the bundle. Which threads are they, and is "one writer per producer" enforced anywhere? **[Narrowed: X11; B §B5a]**
6. Only `atomic<float>` has a lock-free `static_assert` (1019). Are `atomic<uint64_t>`, `atomic<Park>` and `atomic<size_t>` lock-free on Pi 5 and Windows x64?

**Replan and reconfigure**

7. `replan` doesn't copy `pitch.enabled`/pitch layout from the candidate to retained nodes (1498–1510); `reconfigure` does (1375). Intended?
8. ABI2 instances are created in `add_node` and again in `prepare` (1030, 1099, 560); replaced candidate nodes in `replan` were also prepared for nothing. Is that cost acceptable on the Pi 5?
9. While `Parked`, `collect` isn't called (1154–1158), so ingress isn't drained for up to 3 blocks. Can a burst fill rings and, via a dropped release, trigger `emergency()` and a full reset right after the edit?
10. After `reconfigure`, meter counters restart at zero and old queued packets are discarded (generation +1, 1388). Do consumers expect continuous counters?

**Patch loading and the ABI1 facade**

11. `load_runtime_patch` validates saved `sample_rate`, `max_block_frames`, `timing_mode` but never applies them (1992–1994), while it applies `max_channels`, `feedback_block`, `seed`. Intended? **[Context: X14]**
12. Patch port names resolve against ABI1 `metadata` arrays built from static `d->inputs/outputs` (runtime_patch.cpp:2017; app_engine.cpp:1666–1671), but node ports come from `query_ports(config)` (setup 570–575). Can these index spaces differ for config-dependent modules?
13. Every `AppEngine`, including each patch-load engine, creates an ABI1 `ws_engine` (1656). Is the ABI1 engine library still a required build/link dependency, and is its 256-entry / 64-span overload behaviour (engine.h:2115–2117) reachable?
14. `app_engine_enqueue` maps unknown `ws_event.type` to `NOTE_OFF` (1774), and `WS_GATE` silently returns `WS_OK` for most native nodes (1770–1772). Should either be reported?
15. `app_engine_get_meter` always reports `queued_events`, `overload_blocks`, `overload_reason` as 0 (1874). Does the UI read them?
16. `rebind_abi1_descriptor` doesn't compare `reset` (1394–1396). Deliberate?
17. ABI1 nodes get `WS2_FIRST` ports and a 1.0 unpatched value for `"gain_cv"` (1036). Is any ABI1 module still shipped or loaded?

**Events and parameters**

18. Out-of-range PARAM events are dropped, not clamped (714–715); PARAM_MOD values aren't range-checked. Does the spec require either?
19. PARAM coalescing ignores `port` (729). Can two event ports on one node carry distinct PARAM streams?
20. `route` ends with `return routed?okay:okay;` (835) — both branches identical. Was a different result intended for outputs with no edges?
21. PARAM_MOD offsets persist across blocks until replaced or reset (895, 532). Is there a release/decay rule when a voice ends?
22. Transport to modules is fixed 4/4 with no loop/recording flags (931–933), and ABI1 modules get none. Intended long-term? **[Narrowed: X8]**

**Spec and code consistency**

23. ABI2_SPEC.md:2307 says "32 ports/parameters/producers"; `WS2_MAX_PARAMS` is 64 (module2.h:69). Which is authoritative?
24. ABI2_SPEC.md:2309 says latency is the "maximum scheduled forward dependency path across all nodes, includes event-edge dependencies", but `recompute_latency` follows only `kind == 0` edges and reports per-bus maxima (640, 644–649). Which is current?
25. Timestamped events always get `+max_block` (776) regardless of callback size. Is that the right safety offset for real MIDI devices on the Pi 5?

**Cost and shape**

26. Per loop chunk, `render` scans all `edges` (1170); `topology` uses nested edge scans and recursive `std::function` DFS (673–690). How long do topology and render take at `max_nodes` 1024 on a Pi 5?
27. Each event is copied as a full `Packet` with a 1472-byte payload at every ring push/pop and twice on the stack in `route` (337, 342, 815, 830). Has the per-event copy cost been measured on the Pi 5?
28. Several braceless `if`s are followed by unguarded statements on the same line (825, 831, 1118, 1247; §7.2-A). Behaviour looks correct (inf). Was the layout intentional?
29. engine2 uses `std::vector`, `std::function`, `std::string`, `std::unique_ptr` in its core (467–494). Is engine2 meant to run on Daisy-class microcontrollers, or only the module DSP? **[Pending D]**

---

## Part B — Engine protocol: spec vs implementation
Source: Wirescape snapshot 44da1e4, read by an LLM from source (no execution).

### B legend
Files (all in bundle B_protocol.md; "X:n" = line n counted from first line INSIDE that file's code fence; bundle line of fence opening in parens, e.g. S:73 = bundle line 120):
S=docs/specs/ENGINE_PROTOCOL.md(47) | PH=native/sidecar/protocol.h(375) | P=native/sidecar/protocol.cpp(432) | SH=native/sidecar/session.h(727) | SE=native/sidecar/session.cpp(866) | EC=apps/studio/src/engine/EngineClient.ts(2271) | RE=apps/studio/src/engine/RealEngine.ts(2484) | M=apps/desktop/main.ts(3017) | PL=apps/desktop/preload.ts(3605)
Tags: (inf)=inferred; (mk)=from model knowledge, unverified. Row IDs (A1, B2, C6, Q1…) are used for cross-references.
NOT IN BUNDLE: sidecar control loop/main() (calls Transport::next, Session::reply, Transport::complete, Session::status/telemetry/devices); Studio UI components calling EngineClient; audio::Stream; midi::Host; osc::Host/OutHost; ObservedMidi; document::telemetry::Sampler; devices.h; engine2; FakeEngine. Claims depending on them are (inf) or unknown. (engine2, AppEngine and ws_engine_config are in pack A; §2 of this document uses them to settle several points.)

---
### B1. Command tables

#### B1a Spec
Envelope (S:25,32-36,67): {v:0,id,type,…}. id = nonempty printable ASCII ≤64 bytes, unique among outstanding, never reused within session. Every reply (ok or refusal) has gen = base-10 decimal string (64-bit), +1 per committed graph replacement; NOT advanced by event-queue cmds, queries, device selection, rejected edits; starts "0" per process. session token on every reply/push. Error codes: unknown-module, kind-mismatch, duplicate, not-found, refused, invalid, busy, limit, unavailable. Module IDs positive uint32; numbers finite.
Apply classes (S:69): live = enqueued on event queue (ack ≠ rendered); swap = candidate built off-thread → live replan, else D5 (mute → swap at block boundary, no device reopen → fade in), gap ≤150 ms; control = ordered non-RT; query = ordered read. Latency: block / edit (≤150 ms) / device (may exceed 150 ms) / immediate.

| type | Fields | Apply/latency | Ack result | Spec refusal codes | Spec side effects | Cite |
|---|---|---|---|---|---|---|
| loadGraph | patch:PatchV2 (req) | swap atomic/edit | – | unknown-module/unavailable (unknown/inactive module); not-found (param/port); kind-mismatch; duplicate (IDs/edges); limit (>64 modules, >128 conns, >2 MiB); invalid (nesting>64); refused/invalid (out-of-range params, bad output/config/state); refused (no valid Output when outputs absent) | deep execution copy; settings/module version/outputs filled ONLY in copy; new ID namespace + new gen; drains MIDI/control, releases held notes before swap | S:73,110-113 |
| addModule | moduleId:uint32, moduleType:string, params?:{paramId:number} | swap/edit | – | unknown-module (T03); duplicate (ID removed earlier, until next loadGraph) | gen+1 on commit | S:74,113,218-220 |
| removeModule | moduleId:uint32 | swap/edit | – | not-found (generic) | removes attached cables; releases held notes of removed source; ID not reused | S:75,104 |
| connect | connection:{kind:signal\|event\|modulation, from:{module,port}, to:{module,port}, amount?∈[-1,1]} | swap/edit | – | kind-mismatch (T05), duplicate, not-found, limit (128 cables) | gen+1; cable hints never block | S:67,76,112,231-235 |
| disconnect | connection (identity kind/from/to; amount ignored) | swap/edit | – | not-found | gen+1 | S:77 |
| setParam | moduleId:uint32, paramId:string, value:number (native units) | live/block | – | busy (queue full), not-found | gen unchanged (T06) | S:78,104,237-240 |
| setModAmount | connection (identity; nested amount ignored), amount∈[-1,1] (top-level wins) | swap/edit | – | generic | gen+1 (T07); "not a realtime knob event" | S:79,114,243-246 |
| noteOn | note:int 0..127, velocity:0..1 | live/block | – | busy | gen unchanged (T08) | S:80,104 |
| noteOff | note:int 0..127 | live priority/block | – | "never silently drop" | gen unchanged | S:81 |
| panic | {} | live priority release-all/block | – | – | gen unchanged | S:82 |
| listAudioDevices | {} | query/immediate | {devices} + optional result.audio.unavailableDrivers | – | – | S:83,120 |
| selectAudioDevice | deviceId:string | control/audio reopen/device | – | not-found (unknown/stale), duplicate (2 current devices same id), refused+reason (unsupported), refused msg rate-unsupported | all refusals BEFORE stream stop; selection remembered+persisted; gen unchanged | S:84,122-131,137 |
| listMidiDevices | {} | query/immediate | {devices} | – | – | S:85 |
| setMidiEnabled | deviceId:string, on:boolean | control/MIDI subscriptions/device | – | not enumerated | enabled pair persisted; subscriptions refreshed | S:86,137 |
| midiLearn (capability) | armed:boolean | control/immediate | {armed} | – | gen unchanged; arming resets 30 s engine-side timeout; not stored in setting/patch/config | S:87,102 |
| setSampleRate (opt) | hz:int ∈{44100,48000,96000} | control/stream-only restart/device | – | invalid (out of set), refused/rate-unsupported, unavailable | stop stream, rebuild graph, release held notes, reset DSP, restart; persist audio.sampleRate only once running; reply AFTER start; failure restores old config | S:88,95 |
| setBufferFrames (opt) | frames:int ∈{64,128,256,512,1024} | same | – | same | same (audio.bufferFrames) | S:89,95 |
| setOsc (opt) | cfg:{enabled?,port?,allowNetwork?} | immediate | – | always unavailable; no socket | – | S:90 |
| ccMap.set | moduleId:uint32, row:int 0..7, mapping:CcRow{channel 0 or 1..16, controller 0..127, fourteen_bit?/bipolar? bool, smoothing_ms? 0..2000} | swap/config reprepare/edit | – | not-found (non-CC node), limit (row overflow); no holes | replaces/adds config.rows[row]; gen+1 (T12) | S:91,93,280-283 |
| app.restartEngine (main-owned) | {v,id,type} | main, never to engine | {v:0,re,ok:true,gen:"0"} | unavailable on failed restart | EOF/terminate old child, start new with same flags | S:40 |

#### B1b Implementation (SE Session::reply/apply; P Transport::read)
Pipeline:
- Line read: >LineLimit (2,097,152 B) → limit. BOM / parse error / duplicate key at any level / nesting depth≥64 / non-object top → invalid (P:21-34,132-141).
- Queue full: commands_.size()≥PendingLimit (256) → marked busy; reader WAITS for room then enqueues marker (P:147-150).
- Id: string ≤64 B already in outstanding_ → duplicate; else tracked until complete() (P:151-160,182-186).
- re set only if id nonempty, ≤64 B, all bytes 32..126; else re:null; no valid re → invalid "Invalid command" (SE:1175-1182).
- Transport error → code=that error, message "Input refused" (SE:1181).
- Envelope: v must be integer 0, type string, else invalid (SE:1183-1184).
- Exceptions: Json::exception → invalid "Invalid command field"; other std::exception → unavailable "Engine operation unavailable"; audio::ShutdownFailure → std::_Exit(2) (SE:1188-1201).
- Unknown type → invalid "Unknown command type" (SE:1165). Every reply gen = std::to_string(generation_) (uint64) (SE:1202).

Per command:
- loadGraph: command.at("patch") → execution(): format=="wirescape.native.patch", version integer 2, modules/connections arrays → invalid; >64 modules / >128 conns → limit "Graph capacity exceeded" (SE:1105-1107,605-609). commit(patch,true) = new namespace → live replan skipped, always D5 (SE:704).
  - Per module (SE:610-636): id int 1..UINT32_MAX; unique (duplicate "Duplicate module ID"); known descriptor (unknown-module "Module not installed"); not inactive (unavailable "Module is inactive"); ≤32 osc.in (limit "At most 32 OSC input routes"); parameters object; known param (not-found "No such parameter"); finite & in [min,max] (refused "Parameter outside range"). Fills settings:{} and missing module version from descriptor.
  - Per connection (SE:637-657): endpoints exist (not-found "No such module"/"No such port"/"No such parameter"); source port is output; unique identity (duplicate "Duplicate connection"). modulation: to.port is param, source signal (kind-mismatch "Modulation requires a signal source"), WS2_MODULATABLE (refused "Parameter cannot be modulated"), amount REQUIRED ∈[-1,1]. event/signal: both port kinds == cable kind (kind-mismatch "Cable requires matching port kinds"); bad kind/amount → invalid.
  - outputs (SE:658-670): absent → lowest essentials.output routed to bus_channel 0 and 1; none → refused "Patch needs an Output module". Present: nonempty array (refused "Invalid output routes"); port signal output (kind-mismatch "Output requires a signal port"); bus_channel 0..15. Serialized copy ≤LineLimit (limit "Patch exceeds byte limit").
  - load_runtime_patch fails → refused "Graph configuration or state refused" (SE:682-685).
  - D5: mute deadline max(kMuteBudget,3×block period); gap max(kGapBudget,3×period); kMuteBudget 100 ms, kGapBudget 150 ms (1000/1000 ms sanitizer builds). Fails: unavailable "Audio mute did not complete"/"Audio fade callback unavailable"/"Audio swap exceeded gap budget". Effects: midi_->stop(), app_engine_panic old graph, keyboard_ cleared, monitor rings + telemetry sampler reset, new OSC Out host (SE:40-42,724-848).
- addModule: moduleId int≥1 not in used_ids_ (duplicate "Module ID was already used"); builds {id,module:moduleType,parameters:params}; full execution() validation; gen+1. commit(candidate,false): if audio rendering, midi_->replan up to 4× (2 ms sleeps, timeout 3×block period), else/on failure D5; MIDI worker still busy → busy "MIDI worker busy; graph unchanged" (SE:1109-1114,1166,704-723).
- removeModule: node must exist (not-found "No such module"); removes module, its cables AND its outputs entries; if outputs empties → refused "Invalid output routes" (inf, SE:1126-1128 + SE:663); gen+1 (SE:1115-1128).
- connect: connection object; identity via .at(); must not exist (duplicate "Connection exists") + execution() codes; gen+1 (SE:1129-1137).
- disconnect: identity must exist (not-found "No such connection"); gen+1 (SE:1138-1140).
- setModAmount: identity exists; found kind == modulation; top-level amount ∈[-1,1]; not-found/invalid; gen+1 (SE:1138-1143).
- ccMap.set: node exists & module=="midi.cc_to_cv" (not-found "No such module"/"No such CC mapping module"); row<8 (limit "CC row capacity exceeded"); row≤rows.size() (limit "CC rows cannot have holes"); channel 0..16; controller 0..127; fourteen_bit/bipolar bool if present; smoothing_ms 0..2000 if present; writes config.rows[row] in engine copy; commit; gen+1 (SE:1146-1166).
- setParam: module, param exist (not-found); value finite number (invalid); in range (refused "Parameter outside range"); enqueue WS2_PARAM Timing::Immediate on active engine (busy "Event queue full"); ALSO writes patch_ parameters[param] as float; gen unchanged (SE:1083-1103).
- noteOn/noteOff: note int 0..127, velocity 0..1 (noteOn); event to EVERY host.keyboard module in patch_; failed noteOff enqueue → app_engine_panic then busy "Event queue full"; updates keyboard_[key]; no host.keyboard → ok, no event (SE:1062-1082).
- panic: app_engine_panic(active_) direct on control thread (not queued), clears keyboard_, observer_->clear_notes() (SE:1056-1061).
- listAudioDevices: refresh_devices() full enumeration on control thread; {devices} + audio.unavailableDrivers if any (SE:855-860).
- listMidiDevices: cached midi_devices_, no refresh (SE:861).
- midiLearn: armed boolean (invalid); observer_->arm_learning; {armed}; expiry via Session::poll→expire_learning; 30 s constant not in bundle (SE:862-867,1384).
- setOsc: unavailable "Capability not available" (SE:868).
- setSampleRate/setBufferFrames (SE:869-969): out of set → invalid "Rate or buffer size is outside the supported set"; needs --confirm-audio or --null-audio (unavailable "Audio access not authorized"). Real audio: refresh target device; needs running stream or prior rate-unsupported (unavailable "No active audio stream"); exactly 1 matching device (unavailable "Selected audio output is missing or ambiguous"); supported (unavailable "Audio output is unsupported"); rate in sampleRates if present (refused "rate-unsupported"). Null audio: sink joinable (unavailable "No active null-audio stream"). Same value → ok, no-op. Prepare failure → unavailable "Graph cannot prepare at requested stream configuration"; device refuses → unavailable "Audio device refused the new stream"; rollback → unavailable "Stream change refused; previous configuration restored" (or refused rate-unsupported). Success: gen+1. Effects: stop OSC+MIDI, app_engine_panic, stop_audio, rebuild at new rate/block, start_audio, start_midi, persist settings.json, keyboard_ cleared, new telemetry sampler; failure rolls back everything incl. preferences.
- selectAudioDevice (SE:971-1027): deviceId string; refresh_devices(true,true,id); 0 matches → not-found "No such audio output"; >1 → duplicate "Ambiguous audio output name"; unsupported → refused msg=unsupportedReason (or "unsupported"), rate-unsupported reason → refused "rate-unsupported"; current rate not in sampleRates → refused "rate-unsupported"; needs --confirm-audio or --null-audio (unavailable "Audio device access is not authorized"). All checks before stop_audio (SE:977-988 vs 1005). Then stop OSC/MIDI/audio, set device_, reopen (unavailable "Cannot open audio output" or PortAudio error text), persist; failure rolls back to old device. gen unchanged.
- setMidiEnabled (SE:1029-1055): deviceId string, on bool; device in cached midi_devices_ (not-found "No such MIDI input"); needs --confirm-midi or --null-audio (unavailable "MIDI device access is not authorized"); ≤16 enabled (limit "Too many MIDI inputs"); midi_->stop → select → start_midi → persist; failure restores old selection. gen unchanged.

---
### B2. Differences

#### B2a Spec vs sidecar
- A1 Full queue: spec "reply busy without enqueuing" (S:18). Code: at ≥256, marks busy, reader BLOCKS on ready_.wait, then enqueues busy marker into same deque; stdin unread while waiting; (inf) busy markers occupy the 256 slots (P:147-150, PH:15).
- A2 Busy text: T14 "Command queue full" (S:296-299); code "Input refused" for all transport errors (busy/limit/invalid/duplicate) (SE:1181).
- A3 Id reuse: spec unique + never reused in session (S:25); outstanding_ only holds incomplete ids, complete() removes → reusable after completion; outstanding → duplicate (P:151-160,182-186).
- A4 Ids >64 B: not tracked; reply re:null + invalid; client gets no reply with its id (P:153; SE:1177-1182).
- A5 Id chars: spec "printable ASCII"; sidecar 32..126 incl. space; preload/main exclude space (see C9) (SE:1177-1178).
- A6 Nesting: spec ≤64 (S:17); strict_json throws when container opens at callback depth≥64; whether level 64 allowed depends on nlohmann top-level depth (mk: starts at 0 → 64 levels allowed) (P:25-26).
- A7 Invalid UTF-8/NaN/Infinity rejected, CRLF accepted (S:16): no explicit checks; reader splits on \n only, no \r strip; relies on Json::parse (mk: nlohmann rejects invalid UTF-8 and NaN, treats \r as whitespace) (P:21-36,130-141).
- A8 Capabilities: spec conditional (midiLearn only when implemented; full list when OSC hosts installed; telemetry.playhead omitted if seam unavailable) (S:102,141,183); code hardcodes all 7 unconditionally (SE:1236-1237).
- A9 hello fields: spec v,session,type,protocol,engine,capabilities,catalogue,audio,midi (+§6 mentions hello.audioDevices) (S:118,141); code adds top-level audioDevices; no midiDevices (in midi.devices), no osc; engine.version "1.0.0" (SE:1238-1247).
- A10 gen on stream rebuild: spec gen not advanced for device selection; silent on stream-only rebuild (S:32,95). Code: setSampleRate/setBufferFrames ++generation_ on success (SE:948); selectAudioDevice no; open_at_driver_block (ASIO forced size) replaces engine+telemetry sampler WITHOUT gen bump (SE:441-505).
- A11 loadGraph path: spec swap = "live replan, else D5" (S:69,73); loadGraph → commit(patch,true), new_namespace skips replan → ALWAYS D5 mute→swap→fade. Other swap edits try midi_->replan first only while rendering (SE:704).
- A12 Extra busy: swap edits busy "MIDI worker busy; graph unchanged" after 4 attempts / 2 ms sleeps; spec has busy only for full queue (S:18,104; SE:705-722).
- A13 modulation amount: spec optional (S:67); execution() c.at("amount") → missing → invalid "Invalid command field" (SE:650,1195-1197).
- A14 removeModule: spec "remove its attached cables" (S:75,111); code also removes module's outputs routes; patch_ is execution copy where outputs was auto-filled → (inf) removing routed Output empties outputs → refused "Invalid output routes" even if another Output exists; adding new Output never takes over routing (outputs exists, not re-derived) (SE:1126-1128,658-663).
- A15 setParam also writes value as float into patch_ → (inf) later swaps rebuild with it (S:78; SE:1101).
- A16 noteOn/Off without host.keyboard: ok:true, no event, keyboard_[key] still updated and shown in heldNotes; spec noteOff "never silently drop" (S:81; SE:1071-1080,1297-1298).
- A17 Priority: spec noteOff live priority, panic live priority release-all (S:81-82); notes use same enqueue(Timing::Immediate) as setParam, no separate sidecar-level priority path; panic direct app_engine_panic from control thread; failed noteOff → panic then busy (SE:1056-1061,1073-1077). [R6] engine2 itself prioritizes releases: NOTE_OFF/CHOKE go to the producer's critical ring, drained first, within a 256-event release reserve (A:1119, A:760-764, A:727). Panic is a whole-graph DSP reset (X10).
- A18 Extra limit: >16 enabled MIDI inputs → limit (SE:1041).
- A19 listMidiDevices cached, no refresh; listAudioDevices refreshes (S:83,85; SE:855-861).
- A20 deviceName = device_ (id "<hostApi>|<name>[#n]"), not display name; spec examples (illustrative) show same string (S:146; SE:1215-1216).
- A21 status.audio extras reason/error/requestedBufferFrames/unavailableDrivers all emitted — matches (S:146-148; SE:1222-1226); TS type differs (B8).
- A22 Flags: spec --rate "positive supported Hz", 8 flags (S:200); code --rate any 1..UINT32_MAX; settings-file values limited to {44100,48000,96000}/{64,128,256,512,1024}; extra --bench-summary (requires --null-audio) (SE:210-229,243-252,258).
- A23 --device: spec "exact PortAudio output name" (S:200); values without "|" treated as legacy bare names and upgraded to id; (inf) values with "|" used as ids (SE:350-364).

#### B2b Sidecar/spec vs EngineClient.ts/RealEngine.ts
- B1 ccMap.set: in spec+sidecar (S:91; SE:1146); no EngineClient/RealEngine method; applyMutation has no case → falls through return true; other UI senders not visible (EC:174-208; RE:491-527).
- B2 Pipelining: spec 256 queued, journal replays/revalidates (S:18,194); RE "only one edit is in flight", pumpEdits returns after sending one; setParam goes through same journal → waits behind swap acks (RE:47-49,402-419,452).
- B3 Kinds: setParam sent kind:'edit' (journaled); noteOn/noteOff/panic/selectAudioDevice/setMidiEnabled/midiLearn/setSampleRate/setBufferFrames via control()→request() kind:'query', no timeout; refusals to onRefusal with requestId:'' (S:192; RE:431-444,456-487).
- B4 hello.audioDevices ignored; this.audioDevices only from devices push or listAudioDevices reply (SE:1245; RE:257-265).
- B5 Unknown codes mapped to 'refused' by code(); EngineError.code lists same 9 (S:35; RE:38-40; EC:158-159).
- B6 setOsc: sidecar always unavailable; EC declares optional setOsc; RE doesn't define it (SE:868; EC:207).
- B7 applyMutation removeModule filters only modules+connections (not outputs; cf. A14) (SE:1126-1128; RE:500-504).
- B8 SystemStatus.audio type lacks error, requestedBufferFrames (has only reason, unavailableDrivers extras) (SE:1223-1225; EC:52-65).
- B9 Device.index not in TS Device (S:118; EC:11-28).
- B10 Protocol version: RE ignores hello with protocol≠0; main checks only session string (C11) (S:36; RE:232; M:136-137).

#### B2c Spec/sidecar vs main.ts/preload.ts
- C1 Main refusals: spec main forwards busy at limit; broken pipe → pending refused unavailable (S:21). refusal() emits {v:0,re,ok:false,gen:'0',code,message} with NO session; RE drops non-restart replies unless message.session===p.session and drops gen < current → (inf) main's busy/duplicate/"Engine is disconnected"/"Engine pipe failed" never settle a RE edit/query; the single in-flight edit (B2) stays active until next hello or app.engineExited (M:122-124,206-217,241-245; RE:306-310).
- C2 Malformed renderer cmds: spec one terminal reply per parsed command (S:34); main command() silently returns (no reply) on oversize, unparseable, v≠0, non-string type/id, id regex fail; preload rejects most first by throwing synchronously from send (M:191-198; PL:10-36).
- C3 "Pending": spec 256 = awaiting execution (S:18,21); main pending = ids from write until reply with that re (includes executing command); plus byte cap stdin.writableLength + line > MAX_STDIN_BUFFER (4×2 MiB = 8 MiB) → busy (M:13-14,211-214,152).
- C4 Coalescing: spec main drops/coalesces superseded status/telemetry (S:21); main does none — every accepted line → webContents.send via notify(raw); coalescing only in sidecar single-slot status_/telemetry_ (M:153,117-121; P:193-197).
- C5 Forwarding: spec unchanged, no reparse (S:20); main JSON.parses every line for routing but forwards original raw; DROPS lines before first hello, type starting app., v≠0, non-object, invalid UTF-8, >2 MiB (M:129-154,125-128).
- C6 Restart order: T15 ok reply then app.engineExited; spec replies "when restart is initiated" (S:40,304-306). Main sends ok only after restartEngine() resolves (after stopEngine sees close and startEngine spawned); startEngine's close handler sends app.engineExited → (inf, relying on Node listener registration order — mk) app.engineExited arrives BEFORE ok (M:200-203,248-257,269-280,281-289).
- C7 Unexpected exit: spec UI may request restart (S:40); main AUTO-restarts after 250 ms if ≤3 unexpected exits within RESTART_WINDOW_MS=30,000 ms; beyond → modal "Restart engine"/"Quit" (M:15,258-265,290-301).
- C8 Shutdown: spec "bounded cleanup" (S:40); main stdin EOF then child.kill() after 2000 ms; sidecar close watchdog 5 s (close_deadline_) → _Exit(3) (M:274-279; P:273,258-265).
- C9 Id regex: preload+main /^[\x21-\x7e]{1,64}$/ (excludes space); sidecar 32..126 (includes space); preload also limits type ≤64 chars (spec/sidecar don't) (S:25; PL:32-33; M:197; SE:1177-1178).
- C10 openPatch: spec openPatch() no args, "no renderer-supplied path or generic read/write API" (S:51-57,63). Preload openPatch(request?:{library:'list'|'read'|'reset';name?}); main 'list' → ≤256 .json names in userData/patches; 'read' opens renderer-supplied BASENAME there and binds patchPath; 'reset' clears patchPath. RE bridge type adds web?. Exposed object still exactly 5 keys (PL:80-90; M:336-367,565-568; RE:12,16).
- C11 Main accepts any hello with string session; never checks protocol (S:36; M:136-138).
- C12 Menu Panic sends real engine command id menu-<n>; reply forwarded, RE ignores (unknown re). Engine→Restart menu calls restartEngine(true) directly (no app.restartEngine msg) (S:42; M:512-513; RE:306-308).
- C13 webPreferences contextIsolation true, nodeIntegration false, plus sandbox true (S:20; M:524).
- C14 Forwarded flags: --confirm-audio/-midi/-lan, --null-audio, --device/--block/--rate/--settings+value; NOT --bench-summary; other unknown app args silently ignored; --profile-dir rewrites/injects --settings (S:200; M:32-33,38-101).

---
### B3. Pushes
Consumer column limit: Studio components subscribing to onStatus/onTelemetry/onCatalogue not in bundle; "consumer" = last visible reader (RE/main/preload); EC doc comments quoted as "declared intent".

#### B3a Delivery (all pushes)
- Single stdout writer Transport::write; order: replies_ deque (≤256) → status_ slot → telemetry_ slot (P:204-248,213-222).
- send(value,coalesce=true) overwrites one slot: type "status" → status_; ANY other coalesced → telemetry_. Non-coalesced sends block while replies_ holds 256 (P:191-203,196).
- Which pushes coalesced: not visible (control loop missing); (inf) status+telemetry coalesced; devices/hello path unknown.
- hello first: writer sets hello_written_ after writing type "hello"; wait_hello() blocks until then; SH: "Begin rendering only after the hello handshake is flushed." (P:112-115,231,239; SH:123).
- Envelope base() = {v:0,session:token_,gen:"<generation_>"} for status/telemetry/devices; hello built separately, NO gen (SE:1169,1235-1248).
- Token = to_string(random_device()) + "-" + to_string(app_engine_clock_ns()), once per process (SE:267).
- Main: drops non-hello until first hello (engineReady); caches raw hello in lastHello; forwards accepted lines via notify(raw) (M:129-154).
- Preload: drops >2 MiB, unparseable, v≠0; dedupes hello by session; caches lastHello, replays to late subscribers; clears on app.engineExited (PL:39-55,71-73).
- RE gating (status/telemetry/devices): drop if session≠this.session, gen not decimal string, or gen<this.gen (BigInt); gen>this.gen → adopt, clear playhead/statusGen; every accepted push fires generationCbs (RE:275-282).

#### B3b hello — once per process; main re-sends cached line on wirescape:ready (M:558); preload dedupes.
- v, type: constants; all check v===0.
- session: token_; main requires string (M:137); RE requires nonempty string, ignores repeat of current, resets state on new (RE:232-243).
- protocol: 0; RE ignores hello unless protocol===0 (RE:232); main unchecked.
- engine: {version:"1.0.0", sha:WIRESCAPE_ENGINE_SHA} (SE:1242); not read by RE/main/preload.
- capabilities: 7 hardcoded (SE:1236-1237). RE (RE:244-252): telemetry.playhead→playheadEnabled; telemetry.monitor→monitorEnabled; setSampleRate/setBufferFrames/midiLearn enable optional methods; osc, osc.out not read.
- catalogue.modules[]: {id,name,category,ports[{id,name,direction,kind,hint,poly,stereo_pair}],parameters[{id,name,minimum,maximum,default,unit,taper,step,decimals,modulatable,choices?}]} (SE:151-198) → registry.replace(modules), catalogueCbs (RE:253-256).
- audioDevices: audio_devices_ from constructor refresh_devices() (SE:302,1245); NOT read by RE (B4).
- audio: audio_status() (3c) → emitStatus status.audio with statusGen "0" (RE:257-265).
- midi: midi_status(); midi.devices→this.midiDevices; activity+learn into emitted status (RE:258-264).
- gen: absent (spec: only non-hello carry gen); RE sets gen "0" (RE:239).
- Side effect: new session → dispatchLoad (deferred load) or, if patch loaded before, loadGraph(currentDocument()); refusal → graphErrorCbs (RE:266-271).

#### B3c status
Rate: comment "The caller is the existing 100ms control-thread status tick, never render" (SE:1250); loop not in bundle; spec ≤10 Hz (S:145). Each call runs refresh_latency() (SE:1251).
- audio.state: audio_state_; overrides "device-lost" if stream exists but not running, "starting" if running but CPU unmeasured (SE:1211-1213); constructor sets "starting" with --confirm-audio (SE:304). Spec values starting/running/no-device/device-lost/reconnecting. Consumers: canApplyGroove (non-running current-gen state allows Apply) (RE:104); main logs boot-to-audio-running-ms on first running (M:145-150).
- audio.deviceId/deviceName: both device_ (id) while running, else null (SE:1215-1216).
- audio.sampleRate/bufferFrames: options_.rate/options_.block.
- audio.latencyMs: 2.*block/rate*1000 (SE:1219), same as spec; EC intent "Round-trip latency in ms, derived from buffer + sample rate" (EC:60-61).
- audio.cpuPercent: stream_->cpu_percent() while running else 0; null-audio sink stores cpu_ but audio_status reads only stream_ → (inf) 0 under --null-audio (SE:1207-1220,415).
- audio.dropouts: dropouts_ + stream_->dropouts() (SE:1221).
- audio.reason?: audio_reason_ e.g. rate-unsupported (SE:1222); typed (EC:54-55).
- audio.error?: audio_error_ bounded by bounded_audio_error (bound not in bundle) (SE:1223); spec ≤200 B; NOT typed (B8).
- audio.requestedBufferFrames?: when ASIO forced size (SE:1225); NOT typed.
- audio.unavailableDrivers?: ASIO registry diagnostics (SE:1226); spec ≤16 entries, names ≤64 B (not enforced visibly in SE); typed; listAudioDevices() overwrites locally in cached status (RE:472-477); (inf) next status push replaces it.
- midi.devices: midi_devices_ (SE:1230) → this.midiDevices (RE:285).
- midi.activity: observer_->activity(); intent "deviceId -> 0..1 activity, decaying".
- midi.learn?: observer_->learning() when non-null (SE:1231-1232); typed MidiLearn (EC:42-49).
- clock?: NOT emitted; EC declares top-level clock (EC:73-74).
- osc: {enabled,bind,port,lan,last_error?,routes[],out[]}; enabled = any route listening or lan-not-confirmed; bind "0.0.0.0" only if a listening route LAN-bound; port = first route's port; last_error "port-busy" if any busy (SE:1257-1292); typed OscStatus (EC:79-94); ≤32 not checked in status(), relies on 32 osc.in limit (SE:624).
- osc.routes[]: {module:string(node),port,bind,state,received,dropped}.
- osc.out[]: {module,port,state,sent,dropped,last_error?}; ≤32 per spec, no bound check visible.
- gen/session: base(); RE sets statusGen=gen (RE:286).

#### B3d telemetry
Rate not visible; spec ≤30 Hz latest-wins (S:158). Lowest writer priority slot (P:219-222). Sampled on caller thread (inf: control) via app_engine_get_meter, telemetry_.sample(active_), monitor_->snapshot().
- tick: ++tick_. time: seconds since started_ (Session construction) (SH:98; SE:1328).
- meters: only if meter.rendered_blocks; for each patch_.outputs route with port "audio" and module essentials.output: ch0→left, ch1→right, ch2..15→max into left; missing side copies other; keys decimal module IDs (SE:1303-1326). EC intent "Output [left, right], Mixer [A, B]" (EC:137-139); sidecar never emits Mixer meters.
- heldNotes: observer_->held() + keyboard_[] notes not listed (SE:1296-1298); see A16.
- scope: always {} (SE:1331); RE converts arrays to Float32Array (RE:299-300).
- effective, phase, envelope, eventActivity, effective_pitch, playhead, groove: merged from telemetry_.sample(active_) (SE:1332-1333); Sampler not in bundle → key presence/required maps unverifiable. commit plan phase_enabled=true, groove_enabled=true (SE:679); setSampleRate/setBufferFrames plan WITHOUT groove_enabled (SE:917-918). RE: playhead stored only if playheadEnabled && message.gen===this.gen; if not enabled, playhead/groove deleted (RE:297-298); feeds canApplyGroove needing [-1,-1] (RE:105-106).
- monitor?: monitor_->snapshot() when non-empty (SE:1334-1335); RE deletes unless monitorEnabled, adds renderer-only monitorAvailable (RE:294-295).
- outputs?: NOT emitted; EC intent: drives "carrying signal" cable look + sparklines (EC:144-149).
- gen: base(); copied to t.gen (RE:293).
- playhead also cleared locally by loadGraph(), every pumpEdits send, every gen increase (RE:354,413,281).

#### B3e devices
- Fields {v,session,gen,type:"devices",audioDevices,midiDevices,audio?:{unavailableDrivers}} (SE:1341-1348).
- Trigger: Session::poll() true when audio state changed or audio/MIDI/unavailable lists differ; (inf) loop sends devices and/or status; poll interval not visible (SE:1383-1398).
- Pacing: warm when stream exists or audio unconfirmed; else cold PortAudio enumeration ≤ every kColdEnumeration=2 s; warm skips rate probing; MIDI endpoints re-observed only while NO MIDI input enabled (SE:1387-1394).
- Hot-unplug (poll_audio): stream not running or selected id missing from successful enumeration → OSC+MIDI stop, stop_audio, device-lost, retry after 100 ms; each failed retry doubles backoff up to 5000 ms (SE:1349-1382,382-384).
- After commands: selectAudioDevice/setMidiEnabled call refresh_devices after success; whether devices push follows not visible (SE:1026,1053).
- Entry fields built by audio_devices()/midi_devices() (devices.h, not in bundle); refresh_devices reads/edits id,name,hostApi,outputChannels,sampleRates,supported,unsupportedReason; while playing, cached sampleRates/supported kept and running rate appended to sampleRates if list exists (SE:533-579).
- RE: replaces audioDevices/midiDevices, re-emits cached status with new MIDI devices; IGNORES audio.unavailableDrivers here (only from listAudioDevices replies and status) (RE:288-291,463-477).

#### B3f Main-owned pushes
- app.engineExited {v:0,type,exitCode,signal,expected}, no session/gen (M:257); preload clears lastHello (PL:51); RE clears session/ready/confirmed, state 'restarting', rejects pending unavailable "Engine disconnected." (RE:219-230).
- app.menuOpenPatch, app.menuSavePatch{saveAs} from menu (M:498-503); RE ignores (RE:274); app handler not in bundle.

---
### B4. Limits and validation

#### B4a Limits per layer
- Spec: line 2,097,152 UTF-8 B excl LF → limit, discard to LF bounded memory (S:17); nesting ≤64 → invalid (S:17); 256 pending → busy not enqueued (S:18).
- Preload send: depth>64 (top=0, checked before each value incl leaves) → RangeError (PL:14); non-finite, undefined, function, symbol, bigint, cycles, non-Object.prototype/null prototypes → TypeError (PL:15-22); TextEncoder bytes of JSON.stringify ≤2 MiB (LIMIT=2*1024*1024) else RangeError 'Command too large' (PL:4,30); envelope v===0, type string ≤64 chars, id /^[\x21-\x7e]{1,64}$/ else TypeError 'Invalid protocol envelope' (PL:32-35). All synchronous throws, nothing sent, no reply. Inbound >2 MiB dropped silently (PL:40).
- Main command(): Buffer.byteLength>LIMIT → silent drop (M:191); pending.size≥MAX_PENDING(256) → busy "Engine queue full" (no session, C1) (M:13,211-214); writableLength+line+1 > MAX_STDIN_BUFFER (8 MiB) → busy "Engine queue full" (M:14,211).
- Main stdout reassembly: accumulates while size+part ≤ LIMIT+1 (room for trailing CR, then stripped); decodeLine rejects >LIMIT and invalid UTF-8 (fatal:true); dropped silently, drop continues to next LF (M:125-128,166,178). stderr chunks truncated to 2048 chars (M:246).
- Sidecar reader: 65,536 B read chunk (P:120); buffers while bytes.size()<LineLimit, then oversized flag, rest discarded; at LF error "limit"; memory bounded at LineLimit (PH:15; P:131-137). strict_json: leading EF BB BF / container at depth≥64 / repeated key / non-object top → throws; catch(...) → "invalid" (P:21-34,138-142). Id tracked only if string ≤64 B; re rules as 1b (P:151-160; SE:1175-1182).
- replies_ 256 (PendingLimit reused): send() blocks caller until drained (P:199). Outbound dump()>LineLimit → throw → std::_Exit(3), process exits (P:233,243-247).
- Graph: ≤64 modules/≤128 conns → limit (SE:609); ≤32 osc.in (SE:624); bus_channel 0..15 → invalid (SE:668); serialized copy ≤LineLimit (SE:670); CC row<8, row≤rows.size() (SE:1150,1155); ≤16 MIDI inputs (SE:1041).
- Settings file: reads ≤LineLimit+1 B then strict_json; rate/block prefs ignored with stderr note; other prefs fall back to {} (SE:235-256,268-278).
- Engine config config_{sizeof,rate,block,64,2048} (SE:263). [R5] ws_engine_config (pack A, engine.h A:2075-2079) is {struct_size, sample_rate, max_block_frames, max_nodes, max_events}, so this is max_nodes = 64 and max_events = 2048; AppEngine maps max_events → engine2 event_budget (A:1694). Product budget 2048, release reserve 256 (X9).
- RE: no size checks, relies on bridge.
- Rate limits: none per unit time anywhere; only counts (main 256 pending, sidecar 256 queued) + main 8 MiB stdin buffer. Push rates in §3.

#### B4b Failure cases (Preload | Main | Sidecar | RE)
- Malformed JSON: n/a (preload serializes itself, PL:29) | silent drop (M:192-198) | invalid, re:null, "Input refused" vs T14 "Malformed JSON" (SE:1181; S:296-297); (inf) empty line also → one invalid | re:null fails typeof re string → ignored (RE:306).
- Inbound too large: RangeError | silent drop | limit, drained to LF, continues | –.
- Outbound too large: dropped if >2 MiB | dropped (M:166) | writer refuses, exits 3 (P:233) | sees app.engineExited.
- Duplicate JSON keys: impossible (re-serialized) | JSON.parse keeps last (mk) | invalid (P:28-29) | –.
- Duplicate request id: – | duplicate if in main pending (M:210) | duplicate while outstanding (P:154), reply re = that id; (inf) if main bypassed this would settle the ORIGINAL request's pending entry in a client | ids 'ui'+ ++serial unique for renderer lifetime (RE:195).
- Unknown type: allowed if ≤64 chars | app.* other than app.restartEngine → invalid "Unknown app command" (M:205); others forwarded | invalid "Unknown command type" (SE:1165).
- v≠0: throws | silent drop | invalid (SE:1183-1184) | never sends.
- hello protocol≠0: forwarded | accepted (only session checked) (M:136-139) | – | ignored (RE:232); (inf) session stays '', all pushes fail session check, request() rejects "Engine disconnected." (RE:432), state stays 'restarting', user not told version is the reason.
- Non-finite: throws | – | number()/setParam check isfinite (SE:123-128,1091).
- Missing/mistyped field: Json::exception → invalid "Invalid command field" (SE:1195-1197). Other C++ exception → unavailable "Engine operation unavailable" (SE:1198-1200).
- Queue full: – | busy at 256 pending or 8 MiB | busy, reader blocks before enqueuing (A1) | main's busy lacks session → ignored (C1).

#### B4c Exit/crash/restart
Detection:
- stdin read error → stderr "Protocol input unavailable", _Exit(3) (P:123-127).
- stdin EOF (Windows ERROR_BROKEN_PIPE treated as EOF): unfinished line discarded, eof_ set; eof() true only when queue empty → (inf) loop runs all queued commands before shutdown (P:74,128,165-167,178-181).
- Teardown Session::shutdown: OSC Out stop → OSC In stop → MIDI stop → stop_audio; matches spec order; exit code 0 set outside bundle (SE:327-331; S:19).
- stdout write failure → _Exit(3) (P:235,243-247). Write blocked >5 s or shutdown >5 s → watchdog _Exit(3) (P:228,261-264,273).
- audio ShutdownFailure during command → _Exit(2) (SE:1188-1191).
- Child exit (main close handler): refuses main pending unavailable "Engine disconnected" (no session), clears lastHello/engineReady, sends app.engineExited{exitCode,signal,expected} (M:248-257). Late lines from old child dropped unless active.process===owner (M:130). stdin pipe error → all pending unavailable "Engine pipe failed" (M:241-245).
- Unexpected exit: auto-restart 250 ms while ≤3 failures within 30,000 ms; beyond → modal (M:15,258-266,290-301).
- Hung engine w/ stdout open: NO layer detects; no heartbeat/command timeout in main; RE edits/queries no timeout (RE:431-439); only app.restartEngine (10,000 ms) and waitForSessionReady have timeouts (RE:147-176); (inf) stuck control thread → UI waits indefinitely, the one in-flight edit blocks all later edits (B2).
- Graceful stop/restart (stopEngine): stdin EOF, kill after 2000 ms; second restart during one throws → unavailable (M:269-289).
Replayed after new hello:
- Patch: yes, whole document — unsent queued loadGraph sent now, else if loadedOnce RE calls loadGraph(currentDocument()); refusal → graphErrorCbs (RE:234-237,266-271).
- Queued/in-flight edits: NO — rejectPending clears active/queue WITHOUT entry.rollback (contrast failEdit); (inf) optimistic edits reach engine only via full reload (RE:203-215,423).
- Queries/control (device lists, notes, midiLearn…): no — rejected unavailable "Engine disconnected."/"Engine session replaced." (RE:219-237).
- Held notes/keyboard: no (new process, keyboard_ empty) (SH:83).
- MIDI Learn armed: no; RE re-derives midiLearn from capabilities (RE:251-252).
- Audio device + MIDI enables: yes engine-side — constructor reads settings.json (audioDeviceId, devices) unless --device overrides (SE:268-278,289,303).
- Rate/buffer: yes engine-side — parse_options applies stored audio.sampleRate/bufferFrames unless --rate/--block; only allowed sets (SE:233-256).
- Startup flags: same engineArgs reused (M:233-237).
- Initial graph before loadGraph: built-in patch with one essentials.output (id 1) (SE:290-294).

---
### B5. Threading in the sidecar
(Control loop, audio::Stream, midi::Host, osc::Host/OutHost, engine2 missing; their threads from comments/call sites only.)

#### B5a Threads
- Reader (reader_, started 3rd after watchdog, writer in Transport::start): reads stdin via RawPipe::read (ReadFile on Windows, ::read with EINTR retry on POSIX), 64 KiB chunks; splits on \n; PARSES JSON on this thread (strict_json); tracks ids; pushes Request into commands_ under mutex_. Production avoids iostreams so reader/writer never share MSVC/UCRT stdio locks. PH comment "Reader never owns engine state." (P:107-111,37-38,69-82,116-168; PH:21).
- Writer (writer_): sole stdout writer; picks replies_ → status_ → telemetry_; SERIALIZES (value.dump()) on this thread; releases lock while writing; sets hello_written_ after first hello; 64 KiB chunks on Windows; failure/oversize → _Exit(3) (P:204-248,91,232).
- Watchdog (watchdog_, started 1st): wakes on writable_; 5 s write deadline and 5 s close deadline → _Exit(3) (P:249-267).
- Control thread ((inf) process main thread; loop not in bundle): calls Transport::next(req,timeout), Session::reply, Transport::send, Transport::complete, Session::poll/status/telemetry/devices; owns all Session members (patch, devices, preferences, generation). Comments "The caller is the existing 100ms control-thread status tick, never render"; "Control thread only."; rendering begins only after hello flushed (wait_hello) (P:169-177; SE:1250,899; SH:123; P:112-115).
- Null-audio sink (sink_, --null-audio only, Session::start_audio): loop sink_slot_.adopt(live) at block boundary → app_engine_render_live into 2 preallocated float vectors → store cpu_ → wait until next steady-clock deadline. Windows: MMCSS "Pro Audio" fallback THREAD_PRIORITY_TIME_CRITICAL, timeBeginPeriod(1), high-res waitable timer, stop event. POSIX: condition_variable::wait_until. Stops on render result ≠ WS_OK. "The sink thread is the sole writer" of RenderHistogram (SE:395-429,47-108; SH:20).
- PortAudio callback (inside audio::Stream): renders; graphs arrive via stream_->exchange(engine,deadline). Constructor also gets callback [this]{midi_->stop();}, calling thread unknown (SE:367-368,737-742).
- MIDI ingress/worker (midi::Host): start/stop by control thread (start_midi/midi_->stop); midi_->replan(candidate,bytes,timeout_ns,error) does live replans, can fail "MIDI worker busy"; (inf) live replan handed off via MIDI worker (SE:525-528,708).
- OSC In worker (osc::Host): stopped before every graph swap, stream change, device change; restarted by RAII guards (resume_osc); spec: one control-owned nonblocking UDP worker (SE:692-702; S:156).
- OSC Out sender (osc::OutHost): "control-owned loopback sender; never touches the render thread"; own thread not visible (SE:531).

#### B5b Command paths
- All: reader parses → commands_ (one deque, receive order) → control next() → reply → apply → reply JSON → send (non-coalesced, replies_) → writer (P:161,169-177; SE:1170-1204).
- setParam/noteOn/noteOff: control thread app_engine_native(active_).enqueue(...,Timing::Immediate) into engine2 event queue; (inf) render drains; acked on successful insertion (SE:1073-1074,1099).
- panic: control thread calls app_engine_panic(active_) directly WHILE audio runs (SE:1056-1061). [X10] This is engine2's documented any-thread surface: two atomics, noexcept; the render thread performs the reset at the next block.
- Swap edits: control builds candidate (load_runtime_patch, off audio thread) → stops OSC → if rendering, midi_->replan up to 4×; else D5: fade out → poll silence every 1 ms → midi_->stop + panic → exchange at block boundary → poll every 1 ms for fade-in → restart MIDI. Retired engine destroyed on control thread (SE:673-848).
- loadGraph always D5 (A11) (SE:704).
- setSampleRate/setBufferFrames: stop OSC+MIDI → panic → stop_audio (joins sink or stops stream) → prepare new engine → start_audio → start_midi → persist (SE:869-970).
- Device cmds/listing: control thread refresh_devices (PortAudio enumeration); selection also stream reopen + persist (temp file + rename / MoveFileExW) (SE:533-604,971-1027).

#### B5c Blocking
- Reader on stdin read: unbounded, normal (P:122).
- Reader when commands_≥256: until control pops; stdin unread; (inf) pipe fills, main writableLength grows to 8 MiB → main busy (P:147-150; M:211).
- Control next() idle wait: caller's timeout (value not in bundle) (P:171).
- Control send() when replies_=256: until writer drains → command processing stalls behind stdout (P:199).
- Control D5 mute: max(100 ms,3×period) (sanitizer 1000 ms) → unavailable (SE:39-43,749-759).
- Control D5 gap/fade-in: max(150 ms,3×period) → unavailable + rollback (SE:728-731,783-796).
- Control live replan: 4 × (3-block replan timeout + 2 ms sleep) → busy (SE:705-722).
- Control stream restart, device open, PortAudio enumeration (cold init enumerates every host API; throttled to once/2 s in poll but UNTHROTTLED for listAudioDevices, selectAudioDevice, stream changes): unbounded in visible code; (inf) no other command or status/telemetry produced meanwhile, assuming same thread (comment SE:1250) (SH:100-102; SE:855-860,1390).
- Control persist() file I/O: unbounded, synchronous disk write on every device/stream change (SE:580-604).
- Writer write_all on stdout: 5 s then watchdog _Exit(3); (inf) main reads stdout via Node 'data' events with internal buffering, so writer blocks only if main event loop stalls (P:228,261-264; M:159).
- All transport threads share one mutex_ (two condvars); short critical sections; writer releases during I/O (PH:24-25).
- Transport::finish joins reader, which returns only at EOF/read error; 5 s close deadline → _Exit(3); (inf) in-process shutdown without stdin EOF ends exit code 3, not 0; writer drains all queued replies + pending status/telemetry before exit (P:268-289,213-222).
- Render (sink) sink_slot_.adopt: not visible; comment "same block-boundary handoff as the PortAudio callback" (SE:404).

---
### B6. Patch switching and edits
(UI components mapping gestures to EngineClient calls not in bundle; mapping is EngineClient method → wire; spec-stated intent quoted.)

#### B6a UI routing (RE)
- loadGraph(patch): sends loadGraph with deep copy; clears playhead, ready=false, EMPTIES queue+active (no rollback), rejects earlier unsent load "Patch load superseded.", bumps revision; sent once session exists (dispatchLoad) (RE:353-375).
- New hello after prior load: auto loadGraph(currentDocument()); refusal → graphErrorCbs; queued unsent load sent instead (RE:266-271).
- Edit while not ready and no load pending (e.g. initial load failed): sends loadGraph(currentDocument()) INSTEAD; edit never sent ("resubmit the full document instead of sending an edit against an unknown native generation") (RE:377-386).
- addModule/removeModule/connect/disconnect/setParam/setModAmount: journaled, one in flight; before send each checked against confirmed; no longer applies → local not-found "Edit no longer applies to the running graph." (RE:446-455,402-419).
- Edit refused → failEdit: remove, call app rollback, emit onRefusal, send next (checked vs confirmed) (RE:420-430). Edit acked → applyMutation to confirmed, queue.shift(), next (RE:344-350).
- loadGraph refused: ready = confirmed!==null; queue cleared; comment: engine stays on previous graph (RE:319-327).
- whenEditsSettled(): "A document switch must keep its owner visible until all inverses have settled."; waits until no active/queued edit/pending load (RE:177-181).
- settleUnansweredLoad(applied): outside caller can force pending load applied/rejected without engine reply (RE:131-146).
- canApplyGroove(id): true only if ready, state real, no load, no active/queued edit, AND (current-gen audio state ≠ running OR current-gen playhead[id]==[-1,-1]); command Apply sends not visible (RE:102-107).
- File open/menu/toolbar (spec intent): openPatch() then loadGraph; document replaced "only on success"; UI "must await/catch loadGraph (including on initial file open)"; app code not in bundle (S:42,196).
- Library pick openPatch({library:'read',name}): (inf) same loadGraph path; main binds patchPath (M:357-366).
- ccMap.set / MIDI Learn commit (spec intent ccMap.set / addModule): no RE method (B1) (S:93).
- Possible ordering problem (inf): loadGraph() clears active while earlier edit awaits reply but leaves its pending entry; new edits queued (load pending, RE:381); old edit's ok arrives → queue.shift() (RE:346) removes the NEW never-sent edit; load ack sets confirmed to document at load time (RE:334) → shifted edit never reaches engine, never rolled back.

#### B6b Engine audio behaviour (SE)
Commit paths (Session::commit):
- Live replan: when new_namespace false (incremental) AND rendering (stream running or sink rendering). midi_->replan(candidate,bytes,3-block timeout) up to 4×. No fade, no panic, keyboard_ kept. Success: patch, used_ids_, monitor rings, telemetry sampler, OSC Out bus swapped, gen+1. Persistent busy → busy, unchanged. Candidate is a newly built engine (load_runtime_patch); whether untouched modules keep running state NOT visible; comment "Engine2 counts restart at every replan." (SE:682-688,703-723).
- D5: loadGraph always; replan refused for non-busy reason; or not rendering. Output live: master fade-out → poll 1 ms until silent (deadline max(100 ms,3 periods)) → prepare fade-in on candidate → midi_->stop + app_engine_panic old graph → exchange at block boundary (gap deadline max(150 ms,3 periods) from first fade callback) → restart MIDI → wait fade-in started; device NOT reopened. Output not live: stop_audio → swap engine → start_audio (stream/sink restart) → MIDI. All engine state replaced; keyboard_ cleared; held notes released by panic; monitor+telemetry reset; gen+1. Any failure restores previous graph+patch; render thread stall → restore "the slow way" (stop_audio/start_audio) (SE:724-847).
- Both: OSC In+Out stopped before every commit, restarted by guard against whichever graph committed (SE:692-702).
Per command:
- loadGraph: always D5; fade out/swap/fade in, device open; all voices panicked; if no stream, stream/sink restart; gen+1; ID namespace reset to patch IDs (SE:1105-1108,687,704).
- addModule/removeModule/connect/disconnect/setModAmount/ccMap.set: live replan if rendering else D5; normally no fade, fade+panic fallback on refused replan; gen+1; used_ids_ accumulates, removed ID not re-addable until next loadGraph (SE:1109-1166,687).
- setParam: event queue Immediate; next block; no graph change; value stored in patch_ as float; gen unchanged (SE:1083-1103).
- setModAmount: SWAP not live; (inf) every drag step = full graph commit (engine build, OSC stop/start, possible D5 fade if replan fails), serialized by client (B2); gen+1 each (S:114; SE:1129-1145).
- noteOn/noteOff/panic: queue/direct panic; notes only to host.keyboard; gen unchanged (SE:1056-1082).
- setSampleRate/setBufferFrames: stream-only restart; OSC+MIDI stop → panic → stop_audio (stream closed) → rebuild at new rate/block (FRESH DSP state) → start_audio; device reopened; failure rollback; gen+1; namespace not reset (SE:869-970,921,948).
- selectAudioDevice: device reopen; OSC+MIDI stop → stop_audio → start_audio new device; stop_audio takes engine back (engine_ = stream_->stop()) → (inf) same engine object/DSP state carries over; no explicit panic; gen unchanged (SE:971-1028,519).
- setMidiEnabled: MIDI-only (stop → reselect → start_midi); audio untouched; gen unchanged (SE:1029-1055).
- ASIO forced buffer (not a command): engine rebuilt at driver size, not persisted, gen unchanged (A10) (SE:441-505).
- app.restartEngine/crash: new process; silence until new hello + reloaded loadGraph; all DSP state, held notes, Learn state lost; gen restarts "0"; fresh namespace (M:201-205; RE:266-271).

---
### B7. Security surface

#### B7a Electron hardening (M)
- webPreferences contextIsolation true, nodeIntegration false, sandbox true, preload preload.js (M:523-526).
- setWindowOpenHandler → deny; will-navigate → preventDefault (M:528-529).
- UI origin app://wirescape/index.html, scheme privileged standard/secure/supportFetchAPI (M:10-12,539).
- app: handler: GET/HEAD only, host wirescape; decodeURIComponent → path.resolve(UI_DIR,'.'+pathname); must start with UI_DIR+sep and exist → net.fetch(file://…); else 404/400; no symlink check inside UI_DIR (M:547-558).
- senderAllowed: event.sender===window.webContents && senderFrame===mainFrame; applied to all 5 channels (M:325-328,559-573).
- IPC channels: wirescape:ready (re-send cached hello), wirescape:escape (leave fullscreen), wirescape:send (string → command()), wirescape:open (invoke), wirescape:save (invoke) (M:559-573).

#### B7b Renderer reach via window.wirescape
Object.freeze'd, 5 keys send/onMessage/openPatch/savePatch/platform (PL:64-103); preload keydown listener sends wirescape:escape (PL:60-62).
- send(obj): any engine command over stdin; app.* only app.restartEngine accepted; preload validates types/depth/size ≤2 MiB/envelope; main size/envelope/id regex/pending limits; field contents NOT validated before engine (PL:10-36; M:191-219).
- send app.restartEngine: kills/respawns engine with same args; guarded only by restartInProgress; NO rate limit; expected restarts don't count toward crash budget (failures grows only on unexpected exits) (M:201-205,258-266,282-289).
- onMessage(cb): every engine line (raw as parsed by preload) + main app.* (PL:68-79).
- openPatch(): native Open dialog; reads ANY user-picked file: O_NOFOLLOW, regular file, ≤2 MiB, strict UTF-8, nativeFile checks (format, version 1|2, module/connection shape, duplicate keys, nesting ≤64); returns {text, basename}; full path kept in main as patchPath; consent via dialog (M:450-465,424-436,373-423).
- openPatch({library:'list'}): lists userData/patches, ≤256 *.json names ≤240 chars, examines ≤1024 entries; rejects symlinked directory; no dialog (M:337-355).
- openPatch({library:'read',name}): renderer-chosen basename in userData/patches; rejects / \ NUL, non-.json, symlinks, realpath parent ≠ folder; BINDS patchPath; no dialog; preload limits name ≤240 chars (M:357-366; PL:81-91).
- openPatch({library:'reset'}): clears patchPath and v1 backup marker (M:341).
- savePatch(text,{saveAs:false}): OVERWRITES patchPath WITHOUT dialog (patchPath = last opened via dialog/library read or saved); text must pass nativeFile; existing target must be readable supported patch or absent else "Refusing to overwrite an unsupported patch"; temp file (wx, 0600) then rename; overwriting v1 first creates <name>.v1<ext> via hard link; size ≤2 MiB checked in preload+main (M:466-497,437-449).
- savePatch saveAs:true or no patchPath: native Save dialog default userData/patches/Untitled.json; chosen path → patchPath (M:329-336,471-479).
- platform: process.platform, read-only (PL:102).
- (inf) library:'read' + savePatch(saveAs:false) lets renderer overwrite any existing supported patch in userData/patches with any valid patch text, no dialog; conflicts with spec "No renderer-supplied path or generic read/write API exists" and arg-free openPatch() (S:51-63).

#### B7c Process access
- Engine binary: --engine <path> app arg, else <appPath>/wirescape-engine[.exe] or ../../build/native/…; renderer can't change (M:220-226,25).
- Engine args only from app argv allow-list (--confirm-*, --null-audio, --device/--block/--rate/--settings+value; --profile-dir checks); renderer can't change (M:23-35,39-102).
- spawn(executable,engineArgs), no shell, windowsHide; FULL process.env inherited; WIRESCAPE_TEST_STUB=1 in main env → runs process.execPath (Electron) with ELECTRON_RUN_AS_NODE=1 and engine path as script (M:227-238).
- Engine stderr logged, truncated 2048 chars/chunk, never parsed (M:246).

#### B7d Engine-side resources reachable from protocol messages
- selectAudioDevice, setMidiEnabled, setSampleRate/setBufferFrames success, startup when stream opened: WRITES settings file (--settings, default user_data/settings.json relative to cwd); create_directories parent; temp + rename (MoveFileExW Windows); content = prior preferences + audioDeviceId, devices, audio.*; values pre-checked vs device lists/allowed sets; path not renderer-controllable (SE:580-604,311; SH:4).
- selectAudioDevice, stream cmds: open real audio outputs; requires --confirm-audio (or --null-audio, which never opens PortAudio) (SE:877,988).
- setMidiEnabled and any commit (start_midi): open real MIDI inputs; requires --confirm-midi (or --null-audio) (SE:1035).
- listAudioDevices etc.: PortAudio enumeration; READ-ONLY ASIO registry lookup (installed_asio_drivers); comment: ALSA format probes "can open a busy PCM"; listing not gated by --confirm-audio (SE:563-571,1388).
- loadGraph/swap edits with osc.in: BINDS UDP listeners on patch-config ports (osc_->start(active_,patch.dump())); loopback default; 0.0.0.0 only if host built with lan = --confirm-lan && !--null-audio AND route lan:true; ≤32 osc.in; port-range checks not visible; osc::Host not in bundle (SE:287,529-532,624; S:200).
- loadGraph/swap edits with OSC Out: SENDS UDP from one nonblocking socket; spec v1 loopback-only; (inf) destination ports from patch; OutHost not in bundle (SE:296,531; S:153).
- Patch config/state passed verbatim (post-execution()) to load_runtime_patch, midi::Host, both OSC hosts; whether any module reads files (samples, wavetables) not visible (SE:605-670,682-685).
- selectAudioDevice failures forward audio_error_ (PortAudio/ASIO text via bounded_audio_error) as message; spec "no arbitrary path or secret" (SE:1023; S:35).
- Request ids echoed only as re; renderer strings not used to build any filesystem path, command line or socket address, except OSC config via patch (SE:1175-1182).

---
### B8. Open questions

#### B8a Transport/envelope
- Q1 Reader blocks and enqueues busy marker at 256 vs spec "without enqueuing"; is blocking the reader intended? (A1; S:18; P:147-150)
- Q2 May an id be reused after completion? Spec no; sidecar only rejects outstanding ids. (A3; S:25; P:151-160,182-186)
- Q3 Does "printable ASCII" include space 0x20? Sidecar 32..126 yes; preload/main \x21-\x7e no. (A5/C9)
- Q4 Is nesting depth exactly 64 allowed? Sidecar throws at depth≥64, preload at >64; bases may differ. (A6; P:25-26; PL:14)
- Q5 Where is CRLF acceptance handled? Reader splits on \n, never strips \r; relies on parser treating \r as whitespace; same for invalid UTF-8/NaN. (A7)
- Q6 Is reply message text normative? T14 "Malformed JSON"/"Command queue full" vs code "Input refused". (A2)
- Q7 Is exiting on outbound line >2 MiB intended (_Exit(3), no refusal)? Can hello (catalogue+audioDevices) or listAudioDevices reply get that large? (P:233,243-247)
- Q8 app.restartEngine replies gen:"0"; main refusals gen:"0" without session — how should a client settle them, given RE drops replies without matching session or with lower gen? (C1; S:40; M:122-124; RE:306-310)
- Q9 Main silently drops malformed/oversized renderer cmds — does "exactly one terminal reply" apply to main too? (C2)
- Q10 Spec says main coalesces status/telemetry; only sidecar does. Spec outdated or planned? (C4)

#### B8b Lifecycle/restart
- Q11 T15: ok before app.engineExited; (inf) code sends app.engineExited first. Which order is normative; does a client depend on it? (C6)
- Q12 Spec "UI may request" restart vs main auto-restart (≤3 exits/30,000 ms, 250 ms delay). Intended? (C7)
- Q13 What should user see for hello.protocol≠0? Main accepts; RE ignores, stays 'restarting' with no reason. (B10/C11/4b)
- Q14 How is a hung engine with open stdout detected? No heartbeat, no edit/query timeouts, one in-flight edit. (4c; RE:402-419,431-439)
- Q15 Main kill after 2000 ms vs sidecar 5 s close watchdog — which is the spec's "bounded cleanup"? (C8)
- Q16 Where is EOF → exit 0 guaranteed? Code returning 0 not in bundle; finish() without EOF → _Exit(3). (4c/5c; S:19; P:268-289)
- Q17 rejectPending drops queued edits without rollback on session replace; is relying on full reload intended? (4c; RE:203-215,266-271)

#### B8c Client
- Q18 Can: edit in flight → loadGraph() clears active → new edit queued → old ok arrives → queue.shift() removes new never-sent, never-rolled-back edit? (6a; RE:353-375,344-350,381)
- Q19 Where is ccMap.set sent from? Not in EC/RE; applyMutation falls through return true for unknown types. (B1)
- Q20 Intended that setParam waits in one-at-a-time journal behind slow swaps though spec treats it as live? (B2/B3; S:78; RE:452)
- Q21 Is requestId:'' for refusals of noteOn/noteOff/panic/device/midiLearn/rate/buffer cmds the intended onRefusal contract? (B3; RE:440-444)
- Q22 RE ignores hello.audioDevices and devices-push unavailableDrivers; TS types omit audio.error, audio.requestedBufferFrames, Device.index. Meant for UI? (B4/B8/B9)

#### B8d Engine semantics
- Q23 All 7 capabilities hardcoded; any build/runtime condition (e.g. no OSC hosts) where list should shrink? (A8)
- Q24 Is a stream-only rebuild a "committed graph replacement"? setSampleRate/setBufferFrames bump gen; ASIO forced rebuild doesn't; spec example doesn't say. (A10; S:32,95-99)
- Q25 loadGraph always D5 (fade+panic); intended reading of "swap, atomic"? (A11)
- Q26 D5 budgets stretch to 3 block periods (e.g. --block 4096 @44,100 Hz ≈278.6 ms; ASIO-forced block ≤4096 same), above spec ≤150 ms. Is stretch part of the contract? (S:69,104; SE:728-731,749)
- Q27 Intended that removing the routed Output is refused "Invalid output routes" even if another Output exists (inf)? (A14)
- Q28 setParam stores float in execution copy, later swaps rebuild from it; double-precision loss and divergence from UI document acceptable? (A15)
- Q29 No host.keyboard → noteOn/Off ok, note in heldNotes; conflicts with "never silently drop" and accurate heldNotes? (A16; S:81,160)
- Q30 Source of noteOff/panic "priority"? Notes share Immediate queue with params; panic direct on control thread while rendering — RT-safe? (A17) **[Answered: X10, R6]**
- Q31 selectAudioDevice keeps DSP state, no panic — what happens to notes held during a device switch? (6b; SE:1005-1012,519)
- Q32 Rate/buffer change builds telemetry plan without groove_enabled — do playhead/groove vanish while telemetry.playhead still advertised? (3d; SE:917-918,679)
- Q33 Under --null-audio cpuPercent always 0 (inf) vs spec "real rendered meters/counters"? (3c; S:200; SE:415,1207-1220)
- Q34 deviceName = device id, not display name; intended? (A20)
- Q35 listMidiDevices cached; endpoint discovery only while no MIDI input enabled — can a device plugged in after enabling one ever appear? (A19/3e; SE:861,1387)
- Q36 Where are enforced: 30 s Learn timeout, 16-entry/64-B unavailableDrivers bounds, 200-B audio.error, 32-entry OSC route/OSC Out bounds? None visible in SE. (S:102,120,147,152-153)
- Q37 --rate accepts 1..UINT32_MAX vs spec "positive supported Hz"; undocumented --bench-summary and 16-MIDI-input limit — update spec or code? (A18/A22)
- Q38 Control-loop timing (status tick, telemetry rate, poll() interval, whether devices push follows selectAudioDevice/setMidiEnabled)? Loop not in bundle. (3a/3e)

#### B8e Spec internal
- Q39 §6 ids "<host API>|<name>[#n]" vs T09/§6 example bare "USB Stereo"; which do fixtures assert? (S:118,127-129,262)
- Q40 §9 "only the consent-gated OSC In UDP worker opens a network socket" vs §7 osc.out outbound UDP socket — which holds? (S:200,153)
- Q41 T01/T15 list 5 capabilities; §7 and code list 7 (+telemetry.monitor, osc.out). Must fixtures match code? (S:208,141; SE:1236-1237)

#### B8f Security
- Q42 openPatch({library:'read'}) + savePatch(saveAs:false) overwrites a userData/patches file without dialog; conflicts with "no renderer-supplied path or generic read/write API" and arg-free openPatch()? (C10/7b)
- Q43 No rate limit on renderer-triggered app.restartEngine; expected restarts outside crash budget — acceptable? (M:201-205,282-289)
- Q44 Engine inherits full env; WIRESCAPE_TEST_STUB=1 switches spawn to Electron-as-Node — settable in production install? (M:227-238)
- Q45 Without --profile-dir no --settings passed → engine writes user_data/settings.json relative to cwd; what is cwd in packaged app? (SH:4; SE:580-604; M:39-102)
- Q46 Where are OSC In port ranges and OSC Out destination/loopback enforcement validated? Hosts not in bundle. (SE:529-532,624)
- Q47 Can audio_error_ (forwarded as message) contain driver paths? bounded_audio_error not in bundle; spec forbids arbitrary path/secret. (S:35; SE:1023)
- Q48 app: handler checks prefix but not symlinks inside UI_DIR — is UI_DIR content trusted? (M:547-558)

#### B8g Files needed to resolve more
Sidecar control loop/main(), devices.h, audio::Stream, midi::Host, ObservedMidi, osc::Host/OutHost, document::telemetry::Sampler, engine2 event queue + replan, Studio components calling EngineClient, FakeEngine. Q14, Q16, Q19, Q30, Q32, Q35–Q38, Q44–Q47 depend on them.

---

## Part C1 — DSP: oscillators, filters, envelopes
Source: Wirescape snapshot 44da1e4, read by an LLM from source (no execution).

LEGEND: `:N` = line N of the file in the section heading, counted from that file's first line. (inf) = inferred. (mk) = from model knowledge, unverified. NV = not visible (file not in pack). D7 = the engine parameter pipeline, as the module DESIGN docs name it (base ramp 5 ms linear per ABI2_SPEC D6; modulation unsmoothed per D7; see X2) [R9]. sr/rate = sample rate. MOD/PV/ARO/AUTO/STEP = WS2_MODULATABLE/PER_VOICE/AUDIO_RATE_OK/AUTOMATABLE/STEPPED.
NOT IN PACK: port_state.h (PortRamp, port_flags, write_double/read_double), comb_body.h, coupler.h, drift.h, wirescape_sdk.h (ws::Block, split, param().value(), ws::simd), upstream Plaits. (The engine side of "D7" is in pack A; see X2.) Claims depending on these are marked NV.

### C1.0 SDK helpers (native/sdk/signals.h, fastmath.h)
| Helper | Behaviour | Constants | Cite |
|---|---|---|---|
| ws::LinearRamp | sample-counted linear ramp, double accumulator; first set() before any next() jumps to value | length_=max(1,rate*.005) (5 ms) | signals.h:9-31 |
| ws::Schmitt | hysteresis gate | high >0.5, low <0.25 | :32-37 |
| ws::Trigger | pulse | ceil(rate*.001) samples (1 ms) | :38-45 |
| ws::Random | PCG-style: 64-bit LCG (mult 6364136223846793005) + xorshift/rotate output; bipolar()=(next()>>8)/2^23−1 | — | :46-63 |
| fastmath::tan_small | Taylor tan to x⁹ in double, opt-in; comment says VCF does not use it | \|x\|≤0.25 rad, err <6e-8 | fastmath.h:6-9 |
No module in this pack calls LinearRamp or Trigger; modules use PortRamp (NV) or no ramp.

---
### C1.1 VCO (essentials.vco, modules2/vco/dsp.h)
- ALGORITHM: sine only, out=sin(phase), double phase (:22); phase += tau*hz/sr, one `-=tau` wrap (:25). Output written before the advance, so a freq change appears 1 sample later. Freq (:23): pitch cable connected → 261.6255653005986·2^pitch·(frequency/220) (Frequency becomes a ratio to 220 Hz); else held note → note_frequency; else frequency param. FM added linearly in Hz, sum clamped [0,.49·sr] (:24); not through-zero; negative freq holds phase (DESIGN.md). Events (:28-31): NOTE_ON sets 440·2^((key−69)/12) stored as float; NOTE_OFF ignored (pitch kept); NOTE_CHOKE sets phase=0 and clears held note.
- ANTI-ALIAS/NONLIN: none, none needed for sine; linear-FM sidebands above Nyquist and the .49·sr clamp can fold (inf). No saturation.
- PARAMS: frequency .01–20000 Hz, default 220, MOD|PV|ARO|AUTO (:11). No internal smoothing (engine owns base smoothing, DESIGN.md). Per voice: 16 phases/note freqs/active flags (:13). Pitch not clamped before pow; only Hz clamped. Extremes: negative Hz→0 (phase freezes); pitch +inf→.49·sr, −inf→0; NaN passes std::clamp, phase never satisfies >=tau, voice stays NaN until reset/CHOKE (inf).
- NUMERICS: double phase, float out; division by sr unguarded; only the .49·sr clamp depends on rate; reset() zeroes phase (:14).
- COST: 1 double sin/sample (+1 pow with pitch cable), ~2 div, ~3 mul-add; 1 pow per NOTE_ON; no tables; ~208 B.
- ARTEFACTS (inf): CHOKE phase reset clicks unless sine at 0. Note-on: instant pitch change, no glide, waveform continuous (no phase reset). Zipper depends on host smoothing.
- REF (mk): DDS phase accumulator. Alternatives: interpolated wavetable sine, quadrature/"magic circle" oscillator, polynomial sine. For band-limited non-sines: PolyBLEP (Välimäki), BLEP/minBLEP (Brandt 2001), BLIT (Stilson & Smith 1996).

### C1.2 Macro Oscillator (ports.macro_oscillator, modules2/macro_oscillator/dsp.h)
- ALGORITHM: wraps Mutable Instruments Plaits, pinned eurorack f4cfa76…, stmlib e3bd7c9… (DESIGN.md). All 24 engines selectable via model 0–23 (:27,:113). Fixed 12-frame Voice::Render(patch,modulation,output,12) (:146-150) through a 12-frame FIFO; latency_frames()=12 (:93,:107-109). Output out/32768.f, aux/32768.f (int16 frames). Engine algorithms upstream, NV; Plaits has VA, waveshaping, FM, granular, additive, wavetable, chord, speech, swarm, noise, particle, string, modal, drum engines (mk).
- ANTI-ALIAS: none in adapter; Plaits uses BLEP in VA engines and internal oversampling in some engines (mk).
- PARAMS: controls sampled once per 12 frames when fill==0 (4 kHz at 48k) (:110-145). Coarse −48…48 st → note=60+coarse (:28,:112). Pitch in 12·pitch clamp ±96; FM in·6 clamp ±48; harmonics/timbre/morph/model CVs clamp ±1 (:122-127). Trigger = max(trigger,gate) if gate connected (:134). Level = gate if gate connected and level not; else level input (:135-139). *_patched from connected() (:140-144). Model lround, clamp 0–23, STEP, not MOD. Plain params (harmonics, timbre, etc.) unclamped (:114-121). Up to 8 voices, higher channels output zeros (:46,:101-104). No adapter smoothing; Plaits interpolates some params internally (mk).
- NUMERICS: prepare() returns false unless rate==48000 (:58), so 44.1/96 kHz rejected. No denormal/DC/clip guards in adapter. reset(): destroy Voice, zero storage, placement-rebuild, zero 16384-B workspace, Init with per-channel RNG seed (:74-92). Load = reset (:155-161). Per-voice RNG isolated via thread-local RngScope.
- COST: per channel sizeof(Voice)+32 B FAST + 16384 B LARGE, + 12-frame FIFO. Per-sample cost engine-dependent, NV.
- ARTEFACTS (inf): 12-sample control steps (audio-rate mod effectively S&H at 4 kHz); trigger/gate pulses <12 samples can be missed; trigger timing quantised to 0.25 ms; fixed 12-sample delay vs other modules.
- REF (mk): direct Plaits/Braids port; VCV Audible Instruments port comparable.

### C1.3 LFO (essentials.lfo, modules2/lfo/dsp.h)
- ALGORITHM: sine only, sin(phase)·depth+offset, double phase (:17,:32). Second output phase/tau clamped to 0x1.fffffep-1f (<1) (:34). Free run: += tau·rate/sr, fmod wrap (:35). Sync (sync≥.5 and transport present): phase overwritten each sample: position = beat + (PLAYING ? i·bpm/(60·sr) : 0); phase = tau·frac(position/beats) (:28-31).
- ANTI-ALIAS: none, none needed.
- PARAMS: rate .01–20 Hz def 1 MOD|PV|ARO|AUTO linear; depth 0–1 (same); offset −1…1 (same); sync 0/1 STEP; beats .125–16 AUTO|MOD, not PV, log. No internal smoothing. Output up to ±2 on WS2_CV_BI port, no clamp. Negative modulated rate: phase goes <0, never wrapped (only >=tau checked), phase output negative (inf). beats=0 divides by zero (relies on host range).
- NUMERICS: double phase (comment: avoids drift, :17); reset zeroes phase.
- COST: 1 double sin/sample; sync adds 1 div + 1 floor; fmod only on wrap; param(3) read twice/sample; 16×8 B.
- ARTEFACTS (inf): enabling sync or transport locate jumps phase → output step; stopped transport holds phase at beat. [X8] In the visible code the engine transport is never set, so sync follows a fixed 120 BPM, always-playing timeline.
- REF (mk): standard phase-accumulator LFO with host-beat sync (VST ppqPosition / CLAP song_pos_beats).

### C1.4 Noise (essentials.noise, modules2/noise/dsp.h)
- ALGORITHM: xorshift32 shifts 13/17/5 per voice (:13); output (double) ((x>>8)/2^23−1)·level, uniform on [−1,1−2⁻²³]. Seeds: ch0 0x12345678; ch c 0x12345678^(c·0x9e3779b9), 0→1 (:10). Engine seed not used.
- ANTI-ALIAS: none; flat to Nyquist.
- PARAMS: level 0–1 def .2, port_flags (:8). Smoothed by PortRamp level{.2} (time NV) AND D7.
- NUMERICS: integer RNG, no denormals; mean offset ≈ −2⁻²⁴ (inf). Reset re-seeds + resets ramp. State v1 = RNG + ramp; load rejects rng==0 (:14-15).
- COST: 3 shift-XOR, 1 int→double, 2 mul, 1 ramp step per sample.
- ARTEFACTS: nothing beyond inherent white noise; level changes ramped.
- REF (mk): Marsaglia xorshift (2003). Alternatives: PCG; Gaussian via Box–Muller/Ziggurat; pink via Voss–McCartney / Kellet filter.

### C1.5 CHAOS (essentials.chaos_lite, modules2/chaos_lite/dsp.h)
- ALGORITHM (per voice):
  1. Osc A/B naive wave(phase,shape) (:101-105): shape 0–1 saw 2p−1 → hard square; 1–2 square → sin(2πp). Float phases, floor wrap (:106).
  2. Pitch (:151-153): pitch=clamp(pitch_in+.25·fm+instability,−4,6) oct. A: 261.625565·2^clamp(pitch+round(oct_a)+mod_if_target0,−4,8), clamp [16,.45·rate]. B: round(oct_b)+detune/1200, no LFO.
  3. Pan linear .5±pan·.5 per side (:163).
  4. Coupler coupler[side].process(aa,bpan,mode,depth,rate) (:165, NV); delay ceil(rate·.006)+4, linear interp (:66, DESIGN.md).
  5. Comb body body[side].process(coupled,rate/tune,feedback,damping) (:166, NV); DESIGN.md: 3 taps ratios 1, 1.4983, 2.003, saturating feedback, linear-interp delays.
  6. x=(coupled+body_mix·(body−coupled))·rough_gain·gate·velocity (:167).
  7. Output (:160,:168-172): one-pole LP c=1−exp(−2π·fc/rate), fc clamp [20,.45·rate]; DC blocker x−x₁+.995·y₁; ×level; soft clip y/(1+|y|); bound ±0.8912509 (−1 dBFS).
  8. Internal LFO (:123-147): 0 sine; 1 triangle 4|p−.5|−1; 2 S&H (new lfo_random.bipolar() each wrap); 3 cosine-interp random lfo_from→lfo_to. Shape change crossfades linearly from previous output over lround(rate·.01) samples (10 ms; :76,:130-140). Self-mod rate·max(.05,1+lfo_self·lfo_previous) (:142). Target (:149): 0 = +mod oct to A pitch; 1 = +mod oct to body tune; 2 = cutoff ×2^(3·mod).
  9. Roughness (:156-158): S&H from drift.random at rough_rate; gain 1−roughness·(.5+.5·rough) ∈ [1−roughness,1].
  10. Drift drift.process(gate,drift,jitter,fall,rate,new_note) (NV); new note = jump ≥1/24 oct between consecutive pitch samples (:60,:118).
- ANTI-ALIAS: none. Naive saw/square (no PolyBLEP) fold back without limit, worst near .45·rate clamp (21.6 kHz at 48k) (inf). Nonlinear stages: output soft clip, comb saturating feedback, coupler per mode (NV). None oversampled.
- PARAMS: all 27 read per sample via param().value(c,i) (:115), no internal smoothing. Stepped rounded at use (round for octaves; lround+clamp for route, lfo_target, lfo_shape).
  | Param | Range | Def | Note |
  |---|---|---|---|
  | shape_a/b | 0–2 | .4/1.6 | |
  | detune | ±60 cent | 7 | B only |
  | octave_a/b | ±3 | 0/−1 | stepped |
  | feedback | 0–.92 | .3 | comb |
  | damping | 0–.99 | .4 | comb |
  | rough_rate | 1–150 Hz | 70 | |
  | fall | 0–1 "oct/s" | 0 | to drift (NV) |
  | lfo_rate | .02–12 Hz | .3 | |
  | cutoff | 20–20000 Hz | 9000 | LINEAR taper |
  | level | 0–1 | .5 | |
  Gate/velocity clamped [0,1] (:116); ports pass trailing `1` (:11-12), probably default 1 when unconnected (inf). Up to 8 voices, higher channels zeros (:61,:112).
- NUMERICS: all float, no double. DC pole .995 → corner ≈35/38/76 Hz at 44.1/48/96k (inf). No denormal flush in dsp.h; with gate=0, filter and dc_output decay to subnormals unless FTZ/DAZ (inf) [X1: render sets FTZ/DAZ on x64 and FZ on AArch64]. rate/tune safe (tune≥16); soft-clip denominator ≥1; /rate unguarded. Buffers sized from rate: comb ceil(rate/16)+4 (covers 16 Hz) (:65-66). DESIGN.md supports 44.1/48/96k. Reset clears combs, couplers, phases, filters, DC; re-seeds drift + LFO RNG from seed+channel (:85-100). Load (:195-240): staged + validated (finite, phases [0,1), magnitudes ≤1, tick<128, RNG sequence odd), then reset, restore generator/instability state only (tails cleared on purpose); saved fade count capped to current-rate max (:224).
- COST: per voice/sample: 1 sin (always, even non-sine LFO), cos for shape 3, 3 exp2 (+1 target 2), 1 exp, 0–2 sin in wave(), 3 floor, 3 lround, 2 round, drift. Per side ×2: coupler + comb, one-pole, DC, 1 div. Memory 8 voices × 2 sides × (3·comb + delay floats + 64 B) (:67-72):
  | Rate | comb | delay | 8 voices |
  |---|---|---|---|
  | 44.1k | 2761 | 269 | 548,352 B |
  | 48k | 3004 | 292 | 596,480 B (≈0.60 MB, matches DESIGN.md) |
  | 96k | 6004 | 580 | 1,190,912 B |
- ARTEFACTS (inf): naive saw/square aliasing + clip intermod. Gate multiplies directly (:167); only smoothing is 9 kHz one-pole (few samples), so gate edges ≈ steps and comb tail cut when gate closes. Roughness steps gain at rough_rate (apparently intended). S&H LFO jumps pitch/tune/cutoff; only shape changes crossfaded. Body zipper depends on comb_body.h (NV).
- REF (mk): 2 osc + Karplus-Strong-style comb body; x/(1+|x|) cheap sigmoid. Alternatives: PolyBLEP/PolyBLAMP, DPW (Välimäki 2005), ADAA (Parker, Zavalishin, Le Bivic, DAFx 2016) [R2], oversampling.

### C1.6 VCF (essentials.vcf, modules2/vcf/dsp.h)
- ALGORITHM: linear 4-pole cascade of TPT one-poles with zero-delay feedback solution (DESIGN.md "TPT-cascade"). g=tan(π·min(hz,.45·rate)/rate), a=g/(1+g) (:22); k=(3.2/.95)·resonance → k≤3.2 (:23). Zero-input response zero=a·zero+(1−a)·zⱼ (:24); feedback=(a⁴x+zero)/(1+k·a⁴), stage=x−k·feedback (:25). Stage: v=(stage−z)·a; y=z+v; z=y+v (:26-31). low12 = after stage 2, inside the 4-pole loop (:30); low24 = after stage 4, pointer named `hi` (:19,:31).
- ANTI-ALIAS: fully linear, no saturation; input clamp ±1e6 is only an inf guard; prewarped tan + .45·rate cap → filter itself does not alias.
- PARAMS: cutoff 20–20000 Hz def 1000 LOG; resonance 0–.95 def 0 linear (:10); both MOD|PV|ARO|AUTO. No internal smoothing (D7 replaces ABI1 ramps, DESIGN.md). Coefficient recomputed only when cutoff changes (hz!=previous, :22); reset sets previous=−1 so first sample recomputes; coefficient_recomputes counter. Resonance read per sample, not cached. At 44.1k cap = 19,845 Hz (<20 kHz max). NaN cutoff: recomputed each sample (NaN!=x), min(NaN,…)=NaN, state stays NaN until reset (inf); DESIGN.md: NaN out of contract → SDK output silencing. ±inf input → ±1e6; NaN input not filtered. Self-osc threshold k=4 for this topology (mk) → k=3.2 does not self-oscillate (inf). DC gain 1/(1+k) (≈−12.4 dB at k=3.2), no compensation (inf).
- NUMERICS: double state/coeffs, float out (:12). |z|<1e-20 → 0 (:29); comment: FTZ not assumed bit-equivalent. 1+k·a⁴≥1, g>0. No DC blocker, no clip. Exact prewarp except cap. prepare() empty, rate read per sample. Reset zeroes state.
- COST: constant cutoff ≈35 double flops/sample (~4 mul-add for zero, ~6 + 1 div feedback, 4 stages×~4, 4 abs/compare), no transcendental (inf); audio-rate cutoff adds 1 tan + 1 div/sample. Memory 16×(32+4+8)=704 B.
- ARTEFACTS (inf): low12 carries 4-pole feedback, not a standalone 2-pole; bass drops as resonance rises; zipper depends on host; linear, so hot input gives large but bounded peaks.
- REF (mk): Zavalishin linear TPT/ZDF ladder (The Art of VA Filter Design). Alternatives: Huovilainen (2004), Stilson–Smith (1996), D'Angelo–Välimäki (2013), ZDF ladder with tanh solved by Newton, Simper SVF for 12 dB.

### C1.7 Ladder Filter (essentials.ladder, modules2/ladder/dsp.h)
- ALGORITHM (:12): 4-pole TPT cascade, one-sample-delayed global feedback (no ZDF). feedback=(1+k)x−k·previous (previous = last sample's stage-4 out). stage = d==0 ? feedback : tanh(3d·feedback)/(3d). 4 TPT stages; out = stage 4. g=tan(π·min(cutoff,.45·rate)/rate), a=g/(1+g), k=.85·resonance.
- ANTI-ALIAS: single tanh on input+feedback, scaled 1/(3d) (small signals unity gain); not oversampled → aliasing at high drive/level (inf). d=0 branch exactly linear; continuous as d→0 (inf).
- PARAMS: cutoff 20–20000 Hz def 1000 LINEAR (VCF uses LOG); resonance 0–1; drive 0–2 (:8). Double smoothing: per-voice PortRamp each (:9,:12) + D7. k≤0.85. (1+k) input → unity DC gain: y=(1+k)x−ky ⇒ y=x (inf). Non-finite input → 0, then clamp ±1e6. Load range-checks ramps: cutoff 20–20000, res 0–1, drive 0–2 (:14). PortRamp NaN handling NV.
- NUMERICS: double state/ramps/math, float out; 1e-20 tail cut; div by drive only when d≠0. Unit-delay feedback makes peak freq and height shift with sr and cutoff/Nyquist (inf). prepare stores rate + prepares ramps; reset zeroes state + ramps. State v1: 4 poles, previous, 3 ramps, staged + validated (:13-14).
- COST: per sample 1 tan (every sample, no caching), tanh if d≠0, 2–3 div, 3 ramp steps, ≈30 flops (inf). Memory 16×(3·PortRamp + 40 B).
- ARTEFACTS (inf): moderate resonance, no self-osc; peak shifts at high cutoff; tanh aliasing at high drive; zipper unlikely.
- REF (mk): resembles simplified Huovilainen/Stilson–Smith. Delayed-feedback error usually fixed by ZDF or Huovilainen half-sample compensation; tanh in loop: Newton–Raphson (Zavalishin), per-stage tanh with ADAA or oversampling.

### C1.8 Resonator (essentials.resonator, modules2/resonator/dsp.h)
- ALGORITHM:
  1. Strike (:93-105): inline Schmitt (on >.5, off <.25); rising edge burst_left=burst=max(1,ceil(rate·.005)) (5 ms, 240 samples at 48k; :53). Noise one-pole α=.04+.96·tone². Amp .003·strike_level·(burst_left/burst)·noise (linear env 1→1/burst).
  2. Pitch (:106-108): oct=clamp(pitch_in+clamp(tune,±24)/12,±16); hz=clamp(261.625565·2^oct,20,.45·rate).
  3. Delay targets (:109-114): rate/(hz·ratio), clamp [2,line_size−2]; one-pole glide 1−exp(−1/(rate·.012)) (12 ms; :54); first sample after reset jumps. Ratios (:81-82): s0 1,1.4983,2.003 | s1 1,2,3 | s2 1,2.756,5.404 | s3 1,2.32,4.25.
  4. Feedback per tap exp(−6.907755279·delay/(rate·T60)), 6.9078=ln1000 → −60 dB after T60 for every tap (:118-119).
  5. Comb body.process(audio+strike,{delay,feedback},damping) (NV); DESIGN.md: linear-interp fractional delay, per-tap one-pole damping, x/(1+|x|) in each loop, tap weights .6/.25/.15.
  6. "Radiation" LP: 4 cascaded forward-Euler one-poles, c=min(1,3.769911184·hz/rate) (2π·0.6 → tracks 0.6× fundamental), input wet=16·body+.5·strike (:124-129).
  7. Output level·((1−mix)·audio+mix·wet) → DC blocker (pole .995) → clamp ±2 (:130-136).
- ANTI-ALIAS: none; nonlinear = in-loop saturator + ±2 clamp. Linear interp low-passes loop depending on fractional delay. Input pre-clamped ±2 and default burst .003, so loop mostly linear (inf).
- PARAMS: tune ±24 st def 0 linear MOD|AUTO|PV; structure 0–3 def 0 STEP AND MOD; decay .05–20 s def 1.5 LOG; damping 0–1 .3; strike_tone 0–1 .5; strike_level 0–1 .8; mix 0–1 1; level 0–1 .7. Only delay length smoothed (12 ms glide, also covers structure changes); others read per sample, clamped in code. Up to 8 voices, higher channels zeros. Feedback always <1 (delay≥2, decay≥.05 s). NaN passes std::clamp: NaN audio stays in loop until reset (inf); NaN pitch → NaN delay, comb behaviour NV; NaN trigger keeps previous state.
- NUMERICS: all float; no denormal flush visible (comb_body.h NV) (inf). DC corner ≈35/38/76 Hz at 44.1/48/96k, overlapping lowest pitches (20 Hz) (inf). Comb length ceil(rate/20)+4 (:39) matches 20 Hz floor. Radiation coefficient c = min(1, 3.77·hz/rate) saturates at 1 once the fundamental hz ≥ rate/3.77: ≈11.7 kHz @44.1k, ≈12.7 kHz @48k, ≈25.5 kHz @96k (:123). hz is clamped to 0.45·rate (19.8/21.6/43.2 kHz, :108), so this is reachable at every rate; with c = 1 the four stages pass the signal unfiltered (inf) [R1]. Divisions guarded. Reset clears body, re-seeds RNG (config.seed^0x9e3779b97f4a7c15 + channel), zeroes delays/colour/DC/noise/burst/Schmitt (:63-74). State v1 = version marker; load = reset (:141-148).
- COST: 1 exp2f, 3 expf, 1 lround, 3 div, 4 stages, DC, comb (3 interp taps + 3 saturators) ≈60–80 flops (inf). Memory 8×(3·line·4+32) B (:40-47): line 2209/2404/4804 → 212,320/231,040/461,440 B at 44.1/48/96k (<0.5 MiB, matches DESIGN.md).
- ARTEFACTS (inf): pitch steps become 12 ms Doppler-like glide while ringing; brightness and T60 vary slightly with pitch (linear interp); strike starts at full env, tone=1 → white; low fundamentals lose level to DC blocker; radiation LP stops filtering for fundamentals above ≈12.7 kHz at 48k (≈25.5 kHz at 96k) [R1].
- REF (mk): Karplus–Strong/feedback comb with Jaffe–Smith (1983) decay/tuning. Alternatives: allpass or Thiran/Lagrange fractional delay, modal banks (Rings), digital waveguides (J.O. Smith).

### C1.9 ADSR (essentials.adsr, modules2/adsr/dsp.h)
- ALGORITHM: linear segments, float level; start() sets start=level, elapsed=0, duration=max(1,llround(s·rate)) (:14). Attack start+(1−start)e/d → level=1 → Decay; Decay start+(sustain−start)e/d → level=sustain → Sustain; Sustain level=sustain per sample; Release start(1−e/d) → 0 → idle (:26-29). Connected gate via ws::Schmitt: rise→Attack, fall→Release (:20-24). Note events only if gate not connected (:34): NOTE_ON records source_id/note_id, starts Attack; NOTE_OFF/CHOKE only if matching owner; CHOKE sets v=Voice{} (:36-37). Params read at min(e.offset,frames−1) (:35), suggesting sample-accurate events (inf); split semantics NV.
- ANTI-ALIAS: n/a; slope corners at stage boundaries.
- PARAMS: attack/decay/release .0001–30 s, defaults .01/.1/.2; sustain 0–1 def .7 + ARO; all MOD|PV|AUTO, linear (:10). Times latched at stage entry; sustain read live each sample, unsmoothed. 0.1 ms min → 5 samples @48k (llround(4.8)), 4 @44.1k; 30 s max → 1.44 M @48k, 2.88 M @96k, both <2²⁴ so float division exact (inf). Not clamped in module (inf): negative seconds → huge uint64 duration (stage never ends); NaN → unspecified llround. Second NOTE_ON overwrites owner, so first note's NOTE_OFF is ignored.
- NUMERICS: float level, uint64 counters; no denormal risk (exact endpoints); duration≥1; correct at any rate; reset = Voice{}; no save/load.
- COST: per sample Schmitt compare, ≤1 div, ≤3 flops; llround once per stage; ≈0.8 KB (inf).
- ARTEFACTS (inf): CHOKE instant 0 → click through VCA; 4–5-sample minimum times click; sustain steps jump level unless host smooths; linear release sounds abrupt (mk); retrigger starts from current level (no step) but takes full attack time.
- REF (mk): linear retrigger-from-current-level ADSR. Alternatives: RC-exponential with overshoot target (EarLevel), CEM3310/SSM2056 models, curved segments.

### C1.10 Function Envelope (essentials.function_envelope, modules2/function_envelope/dsp.h)
- ALGORITHM: rise / hold at 1 / fall, double (:9,:11-12). Gate high = isfinite(gate) && gate≥.5, no hysteresis. Each edge: start=level, endpoint 1 or 0, latch curve, length=max(1,llround(seconds·rate)), elapsed=0. Shaping u=elapsed/length, k=4·curve, shaped = k==0 ? u : expm1(ku)/expm1(k); level=start+(end−start)·shaped; last sample set exactly to endpoint. k>0 slow-then-fast, k<0 reverse; same mapping for falls (inf).
- ANTI-ALIAS: n/a.
- PARAMS: rise .0001–30 s def .01; fall .0001–30 s def .1; curve −1…1 def 0; port_flags, linear (:8). No PortRamp although port_state.h included; values cached on change (last_*) and latched at edge. NaN params copied every sample (NaN!=last); llround(NaN) unspecified; NaN curve → NaN level (inf). Non-finite gate = low.
- NUMERICS: all double; no denormal risk (exact endpoint); length≥1; expm1(k)≠0 for k≠0. prepare stores rate; reset zeroes level/start/endpoint/high, sets elapsed=length=1, does NOT reset cached params (:10). State v1: 7 doubles; length/elapsed written as uint32 though uint64; flags + cached floats (:13). Load validates length≤11,520,000 (=30 s×384 kHz (inf)), elapsed≤length, level/start ∈[0,1], endpoint ∈{0,1}, param ranges (:14).
- COST: during segment 1 div (+2 expm1 + 1 div if k≠0); expm1(k) constant per segment but recomputed every sample; idle = few compares; ≈1.4 KB (inf).
- ARTEFACTS (inf): gate hovering near .5 retriggers repeatedly → stall/flutter, not click; min time ≈ step; retriggers always take full time.
- REF (mk): SuperCollider Env curve (1−e^{ku})/(1−e^{k}); hardware analogues Maths, Serge function generator.

### C1.11 Slew (essentials.slew, modules2/slew/dsp.h)
- ALGORITHM (:11): linear slew-rate limiter, double. time = x≥level ? rise : fall; time==0 → level=x; else step=1/(time·rate), move toward x by ≤step. Units s/unit. Non-finite input holds state. Missing input slews to 0 (DESIGN.md).
- ANTI-ALIAS: rate limiting nonlinear; audio-rate input → triangle-like with aliasing corners (inf).
- PARAMS: rise/fall 0–10 s/unit def .1, port_flags (:8); cached on change, no ramp, effective immediately. Tiny time safe (min caps step). Negative time (out of range) → level diverges (inf).
- NUMERICS: double; target reached exactly; div guarded by time==0 branch; correct at any rate. Reset zeroes only level (:10). Load (:13): last_* checked isfinite + range, but double rise/fall only checked <0||>10 (NaN passes), level unchecked.
- COST: 1 div, 2–3 compares, 1 add per sample; 512 B.
- ARTEFACTS (inf): slope corners; rate changes take effect without a level jump.
- REF (mk): linear slew as in Maths / Serge DSG. Alternatives: one-pole lag, log/exp slew, constant-time glide.

### C1.12 VCA (essentials.vca, modules2/vca/dsp.h)
- ALGORITHM: out=audio·cv·gain via ws::simd::f4 4-wide + scalar tail (:21-30). Constant fast path: all three constant → CONSTANT, compute 1 sample (:15-17). CV+gain constant → broadcast; else rows via row(c,scratch,count), scratch 3×max_block floats allocated in prepare (:11-12,:19,:28).
- ANTI-ALIAS: none; purely linear.
- PARAMS: gain 0–2 def 1 MOD|PV|ARO|AUTO (:9). Gain CV CV_UNI POLY, default 1 unconnected (:7). CV unclamped: negative inverts, >1 adds gain. No internal smoothing; DESIGN.md: D7 supplies smoothed rows, direct step applies immediately. NaN/inf pass through.
- NUMERICS: stateless, float, rate-independent; reset empty.
- COST: 2 mul/sample (SIMD); scratch 12·max_block_frames B.
- ARTEFACTS (inf): none of its own; clicks come from CV source or unsmoothed gain.
- REF (mk): ideal linear VCA. Alternatives: exp/log laws, OTA/THAT2180 models.

### C1.13 Quad VCA (essentials.quad_vca, modules2/quad_vca/dsp.h)
- ALGORITHM: 4 channels, per voice, mode per channel (:26-35). VCA mode: y=x·clamp(level·cv,0,1); LPG state cleared every sample (:91-93). LPG mode (:95-106): follower f=αf+(1−α)·control; attack α=exp(−1/(.002·rate)) (2 ms) when control>f (:41), else release α from table. Release table .060·25^pos s = 60 ms–1.5 s (≈217 ms at default .4 (inf)) (:46-47). Cutoff table fc=40·(top/40)^pos, top=min(18000,.45·rate), stored as g=tan(π·fc/rate) (:39-45). Both tables 257 entries, built in prepare, lerp lookup (:120-124). Filter: TPT trapezoidal SVF LP v2, a1=1/(1+g(g+k)), k=1/.6 (Q 0.6) (:100-105). y=v2·f (follower drives gain and cutoff). Input normalling (:77): unconnected input k uses k−1 recursively; input 0 unconnected → ws::Channel{} (presumably silence, NV). Mix = sum of 4 outputs, clamp ±4, not normalised (:111).
- ANTI-ALIAS: linear, prewarped; ±4 mix clamp only clip; follower AM sidebands limited by 2 ms attack (inf).
- PARAMS: level1–4 0–1 def 1 MOD|PV|ARO|AUTO; mode1–4 0/1 def VCA STEP|AUTO; response 0–1 def .4 MOD|AUTO, NOT PV (:27-35). CVs default 1 unconnected (:17-20,:86). Control clamped [0,1] (unlike VCA module); response clamped [0,1]. Voices capped 16, outputs set to min(channels,16) (:56,:67). CONSTANT only if all constant AND all channels in VCA mode (:57-65). No smoothing in VCA mode; LPG follower acts as asymmetric smoother.
- NUMERICS: float state and tables (built in double, cast; :43-47). No denormal guard; f/ic1/ic2 decay through subnormals when control=0 (inf) [X1]. a1 denominator ≥1. Tables rebuilt per rate; top=18 kHz at 44.1/48/96k. Reset zeroes 4×16 states (:51-54). No save state.
- COST: LPG 2 table lerps, 1 div, ≈15 flops, no transcendental; VCA 2 mul + clamp. Tables 2,056 B, state 768 B.
- ARTEFACTS (inf): VCA→LPG starts follower at 0 → 2 ms dull fade-in; LPG→VCA switches instantly → click if levels differ; VCA mode clicks from CV steps; Q 0.6 <.707 → no resonant "ping"; short pulses give "plonk" via release; ±4 mix clamp can clip with 4 hot inputs.
- REF (mk): Buchla 292-style LPG; Parker & D'Angelo (DAFx 2013); Simper/Cytomic trapezoidal SVF (2013). Alternatives: nonlinear vactrol models, resonant "combo" mode.

---
### C1.14 Summary across modules
"Smoothing" = inside module only (D7 not counted). n/a = property does not apply.
| Module | Algorithm | Smoothing | Anti-alias | Denormal guard | Double | Voices | Rate | Saved state | Transcendental calls per voice per sample |
|---|---|---|---|---|---|---|---|---|---|
| VCO | phase-acc sine, linear FM in Hz | No | n/a | n/a | Yes | 16 | any | none | 1 sin (+1 pow) |
| Macro Osc | Plaits wrapper, 12-frame blocks + FIFO | No | not in adapter | not in adapter | No | 8 | 48k only | marker; load=reset | upstream |
| LFO | sine, transport sync | No | n/a | n/a | Yes | 16 | any | none | 1 sin |
| Noise | xorshift32 | Yes (PortRamp) | n/a | n/a | Yes | 16 | any | RNG+ramp v1 | 0 |
| CHAOS | naive osc + coupler + 3-tap comb + LP/DC/soft clip | 10 ms LFO-shape fade only | No | No (headers NV) | No | 8 | 44.1/48/96 (DESIGN.md) | generator state v2 | ≥1 sin + 3 exp2 + 1 exp |
| VCF | linear ZDF TPT 4-pole, k≤3.2 | No (coeff cached) | prewarped, linear | Yes (1e-20) | Yes | 16 | any | none | 0 / 1 tan on change |
| Ladder | TPT 4-pole, delayed fb, tanh drive, k≤.85 | Yes (PortRamp×3) | No | Yes | Yes | 16 | any | poles+ramps v1 | 1 tan (+tanh) |
| Resonator | burst + 3-tap comb + 4-pole Euler LP + DC + clamp | delay glide only | No | No (comb_body.h NV) | No | 8 | comb sized for 20 Hz | marker; load=reset | 1 exp2 + 3 exp |
| ADSR | linear segments | No | n/a | n/a | No | 16 | any | none | 0 |
| Function Env | expm1 curve rise/fall | No | n/a | n/a | Yes | 16 | any (load ≤11.52 M samples) | full v1 | 2 expm1 while running |
| Slew | linear rate limiter | is itself a smoother | n/a | n/a | Yes | 16 | any | full v1 | 0 |
| VCA | audio·cv·gain, SIMD | No | n/a | n/a | No | 16 | any | none | 0 |
| Quad VCA | VCA or LPG (follower + TPT SVF, tables) | LPG follower only | No | No | table build only | 16 | tables per rate | none | 0 |

---
### C1.15 Open questions
SMOOTHING/PARAMS
1. What exactly is D7 (type, time constant, per voice)? It is the only smoothing for VCO, LFO, VCF, VCA, CHAOS, Resonator, Quad VCA levels. **[Answered: X2]**
2. Noise and Ladder use PortRamp + D7: intended double smoothing? PortRamp time? **[Answered for the engine layer: X2; PortRamp time pending D]**
3. Who uses LinearRamp (5 ms) and Trigger? Is PortRamp a separate implementation? **[Partly answered: X2; pending D]**
4. Are modulated values guaranteed in range? Relying on it: ADSR (negative/NaN seconds → llround/uint64), LFO (beats=0; negative rate leaves phase unwrapped), Slew (negative times), Macro Osc (unclamped harmonics/timbre/morph).
5. Is ±1 a contract for WS2_CV_BI? LFO outputs up to ±2.
NON-FINITE
6. Policies differ: VCF clamps inf, passes NaN; Ladder non-finite→0; Slew holds; Function Env treats as low gate; VCO, CHAOS, Resonator, VCA do nothing. Is SDK validation/silencing ("D14") the single safety net, and does it reset the module that produced the NaN? **[Narrowed: X6]**
7. Slew::load_state lets NaN rise/fall pass and does not check level. Intended?
DENORMALS/SAMPLE RATE
8. Is FTZ/DAZ set on the render thread on ARM64 and x64? CHAOS, Resonator, Quad VCA have no visible guard. **[Answered for x64 and Pi 5: X1]**
9. Macro Osc at 44.1/96 kHz: module unavailable, or resampled?
10. Fixed .995 DC pole in CHAOS/Resonator moves corner ≈35→76 Hz across rates (inf). Intended?
11. Resonator radiation LP is a pass-through for fundamentals ≥ rate/3.77 (≈12.7 kHz @48k, ≈25.5 kHz @96k) [R1]. Intended?
12. Is 384 kHz supported (Function Env load limit)? length/elapsed are uint64 but saved as uint32.
LATENCY/TIMING
13. Does the host compensate Macro Osc's 12-frame latency? Are gates <12 samples allowed to be missed? **[Answered: X7, no compensation]**
14. What does b.split guarantee for event timing (VCO, ADSR)? **[Pending D]**
FILTERS
15. VCF ZDF (k≤3.2) vs Ladder delayed feedback (k≤.85): which is the reference, and is no self-oscillation intended in both?
16. Is VCF low12 (after stage 2 inside 4-pole feedback) the intended 12 dB response?
17. VCF cutoff LOG vs Ladder LINEAR taper: intended?
18. VCF caches tan, Ladder computes every sample: intended or ABI1 leftover?
19. VCF has no gain compensation (≈1/(1+k) (inf)), Ladder does: intended?
OSCILLATORS
20. Is CHAOS aliasing (naive saw/square up to .45·sr) accepted, including on Daisy?
21. Does the trailing `1` on CHAOS gate/velocity ports mean default 1 when unconnected?
22. VCO NOTE_ON frequency float while phase double: intended?
ENVELOPES/VCAs
23. Are ADSR CHOKE (instant 0) and VCO CHOKE (phase reset) clicks intended?
24. What decides which modules persist DSP state? VCO/LFO/ADSR none; Macro Osc and Resonator reset on load; CHAOS partial; ADSR float/no state vs Function Env double/full state. **[Narrowed: X12]**
25. Function Env no gate hysteresis vs ADSR Schmitt: intended?
26. VCA gain up to 2 with unclamped CV (negative inverts) vs Quad VCA clamp [0,1]: intended?
27. Quad VCA response not PV while levels are: intended?
28. Is the instant step on Quad VCA LPG→VCA switch accepted?
VOICES/STRUCTURE
29. Does the host know Macro Osc, CHAOS, Resonator cap at 8 voices and silence channels 9–16?
30. What does modulating Resonator structure (STEP + MOD) mean?
31. Four-wide voice groups in VCO, LFO, VCF, ADSR run scalar code: is SIMD over voices planned ("pending measured equivalent SIMD")?
32. Does any module use fastmath::tan_small?
33. Comb saturation, denormals, interpolation, PortRamp timing and split semantics can only be verified against comb_body.h, coupler.h, drift.h, port_state.h, wirescape_sdk.h (not in pack). **[Pending D]**

---

## Part C2 — DSP: effects, mixing, sequencing, control
Source: Wirescape snapshot 44da1e4, read by an LLM from source (no execution).

### C2 legend
- `path:N`: line N counted from the first line after that file's opening code fence in C2_dsp_effects_control.md. A bare `:N` means the current module's dsp.h.
- (inf) = inferred. (mk) = from model knowledge, unverified.
- Each module section uses these headings: Alg = Algorithm; AA/NL = Anti-aliasing and nonlinearity; Params = Parameter handling; Num = Numerical safety; Cost; Artefacts (all inferred); Ref (all MK).
- These files are NOT in the pack, so claims that depend on them are (inf):
  - port_state.h (PortRamp, port_flags)
  - wirescape_sdk.h
  - spectral fft.h and approx.h
  - groove/config.h (Config, Step, Note/Tie, condition types, decode)
  - osc_out/config.h (OutConfiguration, OutBus)
  - native/voice/note_to_cv.h and the allocator

### C2.0 SDK helpers (native/sdk/signals.h, fastmath.h)
Of fx.delay and fx.reverb, only fx.delay uses one of these helpers (ws::Schmitt). They are listed because later modules use them.

| Helper | What it does | Constants | Cite |
|---|---|---|---|
| LinearRamp | Sample-counted linear ramp, double state | len = max(1, rate·0.005) = 5 ms: 220 @44.1k, 240 @48k, 480 @96k | signals.h:9-31, :15 |
| LinearRamp::set | Returns if value == destination. Before the first next() it jumps to the value. Otherwise it restarts a full-length ramp from the current value. | – | signals.h:18-23 |
| Schmitt | Goes high above 0.5, low below 0.25 | 0.5 / 0.25 | signals.h:35 |
| Trigger | Outputs 1.0 for ceil(rate·0.001) samples (1 ms): 45 @44.1k, 48 @48k, 96 @96k | – | signals.h:41 |
| Random | PCG32 (XSH-RR, multiplier 6364136223846793005). bipolar() gives 24-bit values in [−1, 1−2⁻²³]. | – | signals.h:49-57 |
| fastmath::tan_small | Taylor series to x⁹, evaluated in double. Comment: valid for \|x\|≤0.25 rad, error <6e-8; not used by the VCF. | – | fastmath.h:4-9 |

(inf) LinearRamp::set(NaN): `NaN == destination_` is false, so NaN becomes the destination and spreads through increment_. There is no guard.
(inf) A new target that arrives mid-ramp restarts the full 5 ms ramp, so a fast-moving target is always lagged.

### C2.1 fx.delay (native/modules2/delay/dsp.h)

**Alg**
- Two circular float lines, line[2] (:31), each ceil(2.0·rate)+8 samples long (:45).
- Read: 4-point, 3rd-order Hermite (Catmull-Rom), standard x-form coefficients (:102-116). If the fractional part is exactly 0, it returns the integer sample (:111).
- Feedback path per channel (loop, :136-147):
  1. one-pole LP, or HP built as x − lp (:139-141);
  2. crossfade by tone_k (:141);
  3. DC blocker y = x − x₁ + R·y₁ (:143).
- Write: limit(input + fb·loop(read)) (:213-214).
- Ping-pong (:209-211): line0 = 0.5(xl+xr) + fb·fr; line1 = fb·fl. Round-trip gain is fb².
- Output: equal-power cos/sin dry/wet mix (:217-223).
- Clock sync (:150-172):
  - Schmitt rising edges; the interval is measured in integer samples.
  - The first interval applies at the 2nd edge.
  - A changed interval needs 2 consistent measurements within 2% (:158-163).
  - No edge for 4 s: restart measuring but keep the last period (:168-171).
  - Time = applied × kDivisions[div], divisions {1/4, 1/3, 1/2, 2/3, 3/4, 1, 3/2, 2} (:29, :192-195).

**AA/NL**
- Soft limiter: identity for |x|≤1, else 1 + 0.5·tanh((|x|−1)/0.5). Ceiling 1.5, slope-continuous at the knee (:95-99; DESIGN.md:12).
- Wet read hard clamp ±1.6 (kWetMax) (:28, :204-205).
- No oversampling.
- (inf) The tanh limiter is not oversampled, so line input above 1 aliases, and it is re-applied on every repeat at fb≈1.
- (inf) During a glide the read speed is 0.5–1.5×. That is resampling without a band-limit; Hermite gives only mild low-passing.

**Params**

| Param | Range / default / unit | Flags | Smoothing in module |
|---|---|---|---|
| time | 0.001–2 s, 0.375, log | modulatable | One-pole τ=50 ms, alpha = 1−exp(−1/(0.05·rate)) (:60), plus slew cap 0.5 samples/sample (:202). Snaps when \|diff\|<1e-4. |
| division | 0–7, default 5, stepped | automatable only (no MODULATABLE) | None. lround + clamp 0..7 (:193) |
| feedback | 0–1, 0.4 | modulatable | None. Clamped 0..1 per sample (:207) |
| tone | −1..1, 0 | modulatable | None. Coefficients recomputed whenever the value changes (:117-134) |
| mode | 0–1, stepped | automatable only | None. lround ≥ 1 per sample (:209) |
| mix | 0–1, 0.35 | modulatable | None. cos/sin at sample 0 of each block, and every sample if the buffer is not constant (:217-221) |

- **Per-voice:** none. In L/R are WS2_SUM (:11-12), so engine2 delivers one pre-summed channel (A:864, A:871) and the module's own channel sum (sum, :89-93) runs over a single channel [R3]. Outputs are 1 channel (:176). Unpatched In R means R = L (:189).
- **Tone mapping:**
  - LP: fc = 800·25^(1+t), 800 Hz at t=−1 rising to 20 kHz as t→0⁻ (:126).
  - HP: fc = 20·75^t, 20 Hz at t→0⁺ rising to 1.5 kHz at t=+1 (:129).
  - Both capped at 0.45·rate (:131). tone_k = min(1, 4|t|) (:133). |t|<1e-6 is a full bypass (:122-123).
- **Extremes:**
  - time is clamped to [0.001·rate, 2·rate] samples (:196), i.e. 48–96000 @48k. A clocked time × division above 2 s is also clamped.
  - fb = 1: loop gain = 1 × tone × DC blocker (<1 near DC), bounded by the limiter at 1.5. (inf) Repeats sustain indefinitely, softly saturated.
  - mix 0/1: dry=1/wet=0 and the reverse, exactly (:219-220).
- **NaN (inf):** clamp(NaN) returns NaN.
  - time: cur becomes NaN; static_cast<int>(NaN) in read (:103) is UB and may index out of range.
  - tone: min(NaN, 0.45·rate) is NaN, so filter state is NaN for good. NaN==tone_seen is never true, so coefficients are recomputed every sample.
  - fb: NaN goes straight into the line.
- **Glide (inf):** @48k alpha ≈ 4.17e-4. The slew cap binds when |diff| > 0.5/alpha ≈ 1200 samples (25 ms). A full 2 s jump moves at 0.5 samples/sample for ≈4 s: about −12 st while the delay grows, +7 st while it shrinks (DESIGN.md:17).

**Num**

| Item | Detail | Cite |
|---|---|---|
| Denormals | flush() zeroes \|x\|<1e-18 on the tone LP state and the DC-blocker output. Lines and the Hermite output are not flushed. No FTZ/DAZ in the module. | :100, :139, :143 |
| DC blocking | R = 1 − 2π·10/rate (10 Hz; 0.998691 @48k). In the feedback path only, so the first wet repeat is not DC-blocked. | :61, :143 |
| Clipping | Line ≤1.5 (soft), wet ±1.6 (hard), output not clamped. DESIGN bound √(1+1.6²) < 2 assumes dry input ≤1. | :204-205; DESIGN.md:15-16 |
| Division guards | None needed | – |
| float vs double | Double: rate, cur, alpha, target, tone-coefficient maths, mix-gain maths. Float: buffers, filter states, DC blocker. | :33, :120-132, :218-220 |
| Sample rate | Buffer length, alpha, DC R and clock timeout scale with rate. (inf) At 44.1k the LP cap is 19845 Hz, so the 20 kHz end is unreachable. At 96k the buffers double. | :45, :60-61, :131, :168 |
| Reset / state | prepare calls reset (:62). load_state checks the version, then reset clears the lines (:80-87). State = version word only. | – |

**Cost (inf)**
- ≈70–90 flops/sample with static params:
  - 2 input sums;
  - clock: Schmitt + ~5 ops;
  - glide: ~6 double ops;
  - 2 Hermite reads (~12 flops + 4 wrapped loads each);
  - 2 loop passes (~8 flops each);
  - 2 limiter calls (fabs + compare);
  - 4 output multiply-adds.
- Transcendentals:
  - 2× tanh per sample, only when line input >1;
  - double cos + sin once per block, every sample if mix is not constant;
  - double pow + exp whenever tone changes (every sample under audio-rate tone modulation);
  - exp once in prepare.
- No tables.
- Memory 2·(len·4 + 64) B (:46-52), len = ceil(2·rate)+8: 44.1k 705,792 B; 48k 768,192 B (≈750 KiB); 96k 1,536,192 B (≈1.47 MiB).

**Artefacts (inf)**
- **Time changes:** Doppler pitch glide (tape-like), up to ≈4 s for a full jump. When clocked, ±1-sample interval jitter (changes within 2%) updates applied and causes a slight pitch wobble.
- **Mode switch:** instant at the sample where lround(mode) flips (:209), so the repeats can step.
- **Tone leaving bypass:** lp[ch] is not updated while tone_kind = 0. A jump from 0 to |t|≥0.25 (tone_k=1) uses the stale lp state, so the repeats can click.
- **Zipper:** feedback, mix and tone are not smoothed in the module. Zipper depends on host interpolation (not visible).
- **Hot input:** anything above 1 is compressed before it enters the line, so loud material is saturated even at fb=0.
- **fb≈1:** the DC blocker and an HP tone thin the low end; an LP tone darkens each repeat. Level is held by the limiter, not the loop gain.

**Ref (mk)**
- Hermite is standard (Smith, *Physical Audio Signal Processing*; musicdsp.org). Alternatives: Lagrange, Thiran allpass, windowed-sinc/polyphase.
- Slew-limited read = "tape delay". The alternative for pitch-free time changes is a crossfade between two read taps.
- tanh is common. Alias reduction: ADAA (Parker, Zavalishin, Le Bivic, DAFx 2016; Bilbao et al.), or oversampling.
- DC blocker = classic leaky differentiator (Smith, *Introduction to Digital Filters*).

### C2.2 fx.reverb (native/modules2/reverb/dsp.h)

**Alg**
- 8-line FDN with Schroeder allpass input diffusion. DESIGN cites Jot & Chaigne 1991, Stautner & Puckette 1982 and Schroeder 1962 (reverb/DESIGN.md:5-9).
- Signal flow per sample (process, :170-252):
  1. Input L/R × drive, where drive = 1 − freeze_amount (:187-193).
  2. Predelay per side, linear-interpolated tap. Bypassed when pre_samples < 1 (:195-198). Capacity ceil(0.25·rate)+8 (:73).
  3. Two Schroeder allpasses in series per side, g = 0.62 (:17-36, :29, :200).
     - Ring length = ceil(base·rate/48000)+2, bases {251, 397, 307, 449} (:55, :74-76). The whole ring is the delay: 253/399/309/451 @48k.
     - (inf) The bases are prime, but the +2 makes the lengths composite: 253=11·23, 399=3·7·19, 309=3·103, 451=11·41.
  4. 8 FDN lines with prime bases {1499, 1741, 1999, 2281, 2617, 3011, 3469, 4789} @48k (:54).
     - Scaled by factor = 0.25 + 0.75·size and by rate/48000, then moved to the nearest prime (minimum 53) by trial division (:87-104).
     - @48k the longest line is 4789 (99.8 ms) at size 1 and ≈1193 (≈25 ms) at size 0 (inf, hand-applied nearest_prime).
     - Line capacity ceil(0.103·rate)+8 (:72).
  5. Taps: linear interpolation (tap, :152-158). Read position clamped to [2, capacity−2] (:215).
  6. Damping: one-pole LP per line, low += (delayed − low)·(1 − damp) (:219).
  7. Feedback gain per line: exp(−ln1000·delay_k/(RT60·rate)) (:168), i.e. −60 dB of amplitude per RT60 at any line length.
  8. Mixing: orthonormal 8×8 Hadamard as an in-place butterfly, 3 stages, ×1/√2 each (:141-150).
  9. Injection after the Hadamard: 0.20 × (L into even lines, R into odd lines), lines 4–7 sign-inverted (:225). Each line write clamped ±8 (:227).
  10. Output projections: L = [1,1,1,1,−1,−1,−1,−1], R = [1,−1,1,−1,1,−1,1,−1] (:57-58). Dot product 0, so orthogonal. Scaled by 0.12374369 (:230-231), (inf) = 0.35/√8.
  11. Width: mid + width·side (:232-234).
  12. Mix: cos/sin × wet makeup (1 + 5·mix²) (:241-249; kWetMakeup = 5, :68). Output clamped ±2 (:250-251). At Mix=0 the dry input passes through bit-exact (:235-239).
- **Freeze:** freeze_amount ramps linearly over 20 ms (:178, :182).
  - Input drive → 0; damping → 0 (:183); motion → 0 (:184); feedback → 1 (:220); the line signal bypasses the damping LP (:221).
  - (inf) Fully frozen, the loop is the orthonormal Hadamard at unity gain with integer taps. It is lossless only if delay[k] sits exactly on its integer target, which is why delay[] is double (:65 comment).
- **Motion:** two sine LFOs at 0.17 and 0.23 Hz, fixed start phase 0 (:204-209). Added to each line's tap with a sign pattern from the line-index bits (:214). Depth = motion samples per LFO, so ±2 samples combined at most.

**AA/NL**
- Hard ±8 on each line write ("normally inactive") (:226-227). Hard ±2 on the output (:250-251). No oversampling.
- (inf) There is no nonlinearity below ±8. The ±2 output clamp hard-clips and aliases when it engages. With ×6 makeup at Mix=1 (+15.6 dB), a wet level of ≈0.33 already reaches the ceiling.
- (inf) Fractional linear taps act as a time-varying LP during motion or size glides. That is a loss, not aliasing. LFO pitch deviation is ≤ 2·2π·0.23/48000 ≈ 6e-5 relative, which is negligible.

**Params**

| Param | Range / default / unit | Flags | How applied |
|---|---|---|---|
| size | 0–1, 0.5 | modulatable | Read every 64 absolute samples (:180). On an exact float change, line targets are recomputed (:160-166). Each delay[k] follows a one-pole glide with coefficient 1/(0.05·rate) in double, snapping within 0.001 (:212-213). |
| decay | 0.2–20 s, 2.5, log | modulatable | Clamped [0.2, 20]. The 8 gains are recomputed every 64 samples from the currently gliding delay[k] (:167-168). |
| damping | 0–1, 0.4 | modulatable | Per sample, not smoothed, × (1 − freeze) (:183) |
| predelay | 0–0.25 s, 0.02 | modulatable | Same 50 ms one-pole, snaps within 0.001 samples (:189-191) |
| width | 0–1, 1 | modulatable | Per sample, not smoothed (:186) |
| motion | 0–1, 0.2 | modulatable | Per sample, × (1 − freeze) (:184) |
| freeze | 0–1, stepped | automatable only | Threshold ≥0.5, then a 20 ms linear ramp (:181-182) |
| mix | 0–1, 0.3 | modulatable | Float cos/sin recomputed only when the value changes (:241). Not smoothed. |

- **Per-voice:** none. Inputs are WS2_SUM (:40-41), so engine2 sums every source voice into one channel before process (A:864, A:871); the module reads that channel via b.in(0).value(0,i) (:187-188) [R3]. Unpatched R means R = L. Outputs are 1 channel although declared WS2_POLY (:42-43, :172-173).
- **Damping = 1:** the coefficient (1 − damp) is 0, so low[k] stops updating and holds its last value (:219). (inf) The constant low[k]·gain recirculates every pass, so the tank decays toward a residual DC level instead of a tail. If damping is 1 from reset, low = 0 and the input passes through the lines once with no recirculation.
- **Damping close to 1 (inf):** cutoff ≈ c·rate/2π. Damping 0.99 gives ≈76 Hz @48k and ≈153 Hz @96k.
- **Size 0/1:** see Alg. Targets are capped at capacity − 3 (:164).
- **Decay 20 s:** per-line gain near 1. Longest line @48k: exp(−6.908·4789/(20·48000)) ≈ 0.966.
- **Mix=1:** dry = 0 exactly, wet = 1·6. **Mix=0:** dry is bit-exact, but the tank keeps running and is heard if Mix is raised later.
- **NaN (inf):**
  - decay NaN: gains NaN; the ±8 clamp passes NaN; the tank is NaN until reset.
  - damping, motion, width or mix NaN: spreads into the tank or output.
  - size NaN: lround(NaN) is unspecified, but min(capacity − 3, …) still bounds the target.
- **Size glide (inf):** @48k the glide coefficient is 1/2400, so the starting speed is diff/2400 samples/sample.
  - A 0→1 jump gives diff ≈3596 on line 7 (1193→4789) and ≈2604 on line 6. Both exceed 2400, so the delay grows faster than 1 sample/sample and the read pointer briefly stands still and runs backward.
  - Line 5 (≈2259) slows to ≈0.06×.
  - fx.delay caps this with kSlew; fx.reverb has no cap.

**Num**

| Item | Detail | Cite |
|---|---|---|
| Denormals | No in-module flush. Lines, low[], allpass and predelay buffers are not guarded (compare delay/dsp.h:100). The render-level FTZ/DAZ (x64) or FZ (AArch64) applies [X1]. | – |
| DC | Not blocked. The damping LP has DC gain 1, so DC enters the tank and only decays by RT60. | :219 |
| Clipping | ±8 per line write, ±2 output, both hard | :227, :250-251 |
| Division guards | rt60 clamped ≥0.2 before the divide (:167). rate comes from the host. | – |
| float vs double | rate is FLOAT (:60). delay[8] double (:65). refresh exp and scaled_length maths double. Taps, LFO phases (float accumulators), gains and buffers float. | – |
| Sample rate: scaled | Line lengths, capacity, allpass lengths, predelay, glide, freeze ramp, gains | – |
| Sample rate: NOT scaled | LFO depth (±1 sample per LFO, so half the time depth @96k); damping coefficient (cutoff for a given knob value ∝ rate); allpass g; the 64-sample refresh (1.45 ms @44.1k, 0.67 ms @96k) | :102-103, :177-178, :214, :219 |
| Reset | reset() clears all buffers, sets delay/target to the size-0.5 lengths, gain = 0.9, pre_samples = 0.02·rate, then glides to the current params (:125-140). prepare() does NOT call reset() (:105-124, unlike delay/dsp.h:62). load_state checks the version and resets, so the tail is not continued (DESIGN.md:17). | – |

(inf) Denormal exposure:
- Without freeze the tail decays exponentially. 1.0 → FLT_MIN (≈1e-38) is ≈760 dB, i.e. ≈12.7 × RT60: ≈32 s at the default 2.5 s, ≈250 s at 20 s. After that, values pass through the subnormal range until they round to 0.
- (mk) The subnormal penalty is large on x86 without FTZ/DAZ and usually small or none on AArch64 (Pi 5 Cortex-A76). engine2 sets FTZ+DAZ on x86/x64 and FZ on AArch64 for the whole render call (A:1139-1149), so this exposure applies only to builds without either guard (for example MSVC ARM64) and to other hosts or adapters [R8][X1].

**Cost (inf)**
- ≈250–300 flops/sample:
  - 2 predelay taps (~5 ops each);
  - 4 allpass steps (~4 each);
  - 2 sinf (when motion > 0 and not frozen);
  - 8 lines × ~18 ops (double glide, wrapped tap, 2 projections, LP, feedback mix) ≈150;
  - Hadamard: 24 adds + 24 multiplies;
  - injection + clamp: 8 × ~4;
  - output: ~15.
- Plus ≈8 b.param().value() calls per sample (overhead unknown).
- Every 64 samples: 8 double exp (≈0.125 per sample). When size changes, nearest_prime runs 8 times with trial division up to √(~9600) ≈ 98, i.e. a few thousand integer divisions per refresh in the worst case (size modulated continuously).
- Mix: float cos + sin only when the value changes. No tables.
- Memory (:77-86), samples × 4 B + 448 B alignment slack:

| Rate | Lines | Predelay | Allpass | Total |
|---|---|---|---|---|
| 44.1k | 8×4551 | 2×11033 | 1300 | 239,544 B |
| 48k | 8×4952 | 2×12008 | 1412 | 260,624 B (≈255 KiB) |
| 96k | 8×9896 | 2×24008 | 2816 | 520,448 B (≈508 KiB) |

- Memory access per sample: 8 scattered reads (2 adjacent floats each) and 8 writes across 8 separate buffers, plus 2 predelay and 4 allpass accesses.

**Artefacts (inf)**
- **Size jumps:** warble, or brief reverse playback on the longest lines. Size changes are also quantized to the 64-sample refresh.
- **Decay modulation:** gains step every 64 samples (750 Hz control rate @48k), so fast decay modulation is stepped and aliased as a control signal.
- **Damping:** at 1, held DC or a stuck tail. Damping cutoff and HF decay vary with sample rate.
- **HF decay depends on size:** one damping coefficient is applied once per pass on every line. Larger size means fewer passes per second, so HF decays slower, even though DC RT60 is independent of size. DESIGN.md:5-6 cites Jot's "line-dependent damping", but the code uses one coefficient.
- **Freeze on:** 20 ms ramps of input fade, gain → 1 and damping removal; the frozen tail briefly brightens. A size change while frozen makes taps fractional during the glide; linear interpolation loses HF, so the frozen tail decays and darkens.
- **Freeze off:** gain and damping return over 20 ms and input fades back in. DESIGN's listening note leaves these transitions unreviewed (DESIGN.md:19).
- **Clipping:** high Mix (×6 makeup) plus the ±2 hard clamp clips audibly on loud material.
- **Zipper:** damping, width, motion and mix are unsmoothed; zipper depends on host interpolation.
- **Poly input:** no voices are dropped: engine2 pre-sums the WS2_SUM inputs, so a poly cable is heard as its mono sum (A:871) [R3].
- **No reset after prepare:** if the host does not call reset() and WS2_LARGE memory is not zero-filled, buffers start uninitialized; pre_samples is the 960 member initializer, gain = 0 (default init), and delay/target are 0 until the first refresh.

**Ref (mk)**
- FDN with Hadamard mixing (Jot & Chaigne 1991; Stautner & Puckette 1982). The topology (diffuser input, 8-channel FDN, Hadamard, per-line RT60 gains) closely matches "Let's Write a Reverb" (G. Luff / Signalsmith, ADC 2021).
- Alternatives: Householder matrix (O(N)); Jot absorbent filters (frequency-dependent RT60 scaled per line length); Dattorro plate (JAES 1997); Freeverb (Schroeder–Moorer comb/allpass); velvet-noise reverbs (Välimäki et al.).
- "Infinite" freeze modes elsewhere set feedback to 1 and cut the input. Denormal protection: FTZ/DAZ, or a tiny noise/DC offset.

### C2.3 sound.spectral (native/modules2/spectral/dsp.h)
fft.h and approx.h are included at :5-6 but are not in the pack. Their internals are known only from DESIGN.

**Alg: STFT framework**

| Item | Value | Cite |
|---|---|---|
| Transform | Real FFT. Per DESIGN: N/2-point complex radix-2 plus a real-split pass; one twiddle table for the largest size, read with a stride by smaller sizes. | :315, :303; DESIGN.md:6 |
| N | {512, 1024, 2048, 4096} × rate_factor. Factor 1 up to 66 kHz, 2 for 66–132 kHz, 4 above 132 kHz. | :32, :38-39 |
| Hop | N/4 (fixed overlap 4) | :217; DESIGN.md:16 |
| Window | Periodic Hann 0.5 − 0.5·cos(2πj/Nmax), built in double, stored float, once for Nmax; smaller N reads it with a stride | :86, :314, :305 |
| Scaling | Analysis 4/N (:313). Synthesis s = N/4 in every render (:354). Hann synthesis × 1/1.5 (:306). | – |
| Latency | N, published through an atomic read by latency_frames() | :128, :221, :561 |
| Frame clock | hop_pos_ counts samples, not process calls, so frames are block-size invariant | :138, :155; DESIGN.md:12 |

- (inf) Periodic Hann² overlapped at N/4 sums to 1.5. So 1/1.5 × (4/N)·(N/4) is identity for an unmodified spectrum, matching "Max with B silent returns A exactly" (DESIGN.md:14).
- **Timing:** the frame is the last N input samples ending at write_ (:312). OLA adds from the current write_ (:306). Each sample reads then zeroes ola_[write_] (:139-140). Input sample s comes out at s+N (DESIGN.md:13).

**Per-hop pipeline (tick, :249-308)**
1. **Size change:** immediate if live_ == 0. Otherwise pending_ is set, drain_ = N − hop (0.75N), and the function returns; no frames are made during the drain (:250-258, :138, :150-154).
2. **Mode change:** only when no fade is running. Sets prev_mode_, fade_ = 4, calls enter(), which resets the new mode's phasors or envelopes (:259-265, :232-246).
3. **Interleave schedule:** advances once per frame in every mode (:267-270).
4. **Silent-frame rule:** if both inputs have been exactly 0 for ≥N samples, clear_bins() runs and no frame is made (:271-275, :146-147).
5. **Analysis:** analyse A and B, then track() (:276-278).
6. **Controls:** read once at this offset (:279-290).
7. **Render:** render(mode_). During a fade, render(prev_mode_) also runs and the complex spectra are blended linearly with g = (5 − fade_)/5 = 0.2/0.4/0.6/0.8 (:291-300).
8. **Inverse + OLA:** imaginary DC and Nyquist set to 0 (:301-302), inverse FFT (:303), OLA (:305-306), live_ = N (:307).

**track() (:319-335):** per bin, magnitudes |A| and |B|; unit phasors u = X/|X|, or (1,0) if |X| = 0 (:322-323); rotation since the last frame = u·conj(u_prev).

**Modes (render, :352-372)**

| Mode | Output magnitude | Output phase | Cite |
|---|---|---|---|
| Morph, curve 0 (geometric) | 2^((1−m)·log2(\|A\|+1e-7) + m·log2(\|B\|+1e-7)) | Running phasor p, advanced by A's rotation if (1−m)\|A\| ≥ m\|B\|, else B's (pitch 0, "louder bin") | :392-402 |
| Morph, curve 1 (linear) | (1−m)\|A\| + m\|B\| | Same | :402 |
| Morph, pitch 1 (blend) | Per curve | Advance = exact quarter turn kπ/2 + blended principal deviation da(1−m) + db·m (approx atan2/sincos) | :380-391 |
| Cross | B·min(2^(amount·log2((Ã+1e-6)/(B̃+1e-6))), 1e3), with Ã, B̃ smoothed magnitudes | B | :498-510 |
| Max | Larger of \|A\| and gb·\|B\|, whole | Louder source | :517-524 |
| Mean | (\|A\| + gb·\|B\|)/2 | Louder source | :525-530 |
| Min | min(\|A\|, gb·\|B\|) | A | :531-536 |
| Diff (A−B) | max(0, \|A\| − gb·\|B\|) | A | :531-536 |
| Interleave, phase 1 (source) | Playing chunk source's complex bins × g | Source | :415-417 |
| Interleave, phase 0 (PV) | Playing source magnitude × g | Running phasor q, advanced by the playing source's rotation | :418-422 |
| Vocoder | B × interpolated band gain, + optional noise | B (noise random) | :449-486 |

- gb = clamp(b_level, 0, 2) in combine (:512). Interleave g = gb on B chunks, 1 on A chunks (:411).
- rotate(): multiplies by the rotation and renormalizes to unit length, 1e-20 guard (:337-342).
- **Cross smoothing** (smooth_row, :488-497): prefix-sum moving average, half-width h = ⌊width·(1+0.18k)⌋ bins, width = smooth·24 (:493, :501). Skipped when width ≤0 (:489).
- **Vocoder layout** (vocoder_layout, :428-447):
  - Log-spaced centres from 70 Hz to min(12 kHz, 0.45·fs) (:105, :440).
  - Each bin's log-axis position comes from a table built in prepare (:106-109), read with a stride (:437).
  - Triangular bands, half-width max(1, (nb−1)/(span·max(centre_bins, 0.5))) in band units (:441). Bin ranges by binary search (:442-445). Rebuilt only when nb or N changes (:429).
- **Vocoder per band (:456-468):**
  - Envelope = √(weighted mean of |X|²).
  - A follower: attack τ = 4 ms; release τ = release param clamped 5–400 ms. B follower: one-pole τ = 11.4 ms.
  - Coefficients exp(−hop_s/τ), recomputed every frame (:452-455).
  - gain = min(envA / (envB+1e-6)^flatten, 1e3) via std::pow (:468).
- **Vocoder per bin:**
  - Gain interpolated linearly between bands j and j+1 (:472-475).
  - Noise w = noise·envA(interpolated)·0.25·min(1, f/3000)·1.3, added to re and im as independent rng_.bipolar() draws (:477-482).
  - (inf) Bins below 70 Hz map to position 0; bins above 12 kHz map to the top band.

**AA/NL**
- No oscillator or waveshaper, so no harmonic aliasing. The FFT/OLA path is linear for unmodified spectra.
- (inf) No zero-padding (analysis length = FFT length, :314-315). Per-bin gains act as circular convolution and wrap energy within the N-sample frame: Cross (ratio ≤1e3), vocoder gains, Min/Diff masks. The Hann synthesis window attenuates the wrap but does not remove it.
- Nonlinear spectral operations: Max/Min/Mean/Diff per-bin selection, louder-bin pitch.
- Hard caps 1e3 (+60 dB) on the Cross ratio (:506) and the vocoder gain (:468). No output clamp or limiter.

**Params**

| Param | Range / default | Flags | Use |
|---|---|---|---|
| mode | 0–7 (Morph, Cross, Max, Mean, Min, Diff, Interleave, Vocoder) / 0 | stepped + mod (:53) | Per hop; ignored during a fade (:260) |
| size | 0–3 / 2 | stepped, NOT mod (:54) | Per hop; drain-and-switch |
| morph | 0–1 / 0.5 | mod (:55) | Per hop, clamped (:376) |
| curve | 0–1 / 0 (geometric) | stepped (:56) | Per hop |
| pitch | 0–1 / 0 (louder) | stepped (:57) | Per hop |
| amount | 0–1 / 1 | mod (:58) | Cross only |
| smooth | 0–1 / 0.15 | mod (:59) | Cross only, ×24 |
| b_level | 0–2 / 1 | mod (:60) | Combine and Interleave only (not Morph, Cross, Vocoder) |
| level | 0–2 / 1 | mod (:61) | PER SAMPLE on the output (:139) |
| chunk_a, chunk_b | 1–64 / 5 | stepped + mod (:62-63) | Per hop; cycle 2–128 frames |
| phase | 0–1 / 0 (PV) | stepped (:64) | Interleave |
| bands | 6–64 / 24 | stepped + mod (:65) | Clamped again at :450 |
| flatten | 0–1 / 0.85 | mod (:66-67) | Vocoder |
| release | 0.005–0.4 s, log / 0.05 | mod (:68) | Vocoder |
| noise | 0–1 / 0.2 | mod (:69) | Vocoder |

- **Control rate (inf):** everything except level is sampled once per hop = fs/(N/4): 375 / 187.5 / 93.75 / 46.9 Hz @48k for N = 512/1024/2048/4096. OLA spreads each change over N samples. No other smoothing.
- **stepped():** lround, then clamp to the declared range (:209-213).
- **Per-voice:** none. A and B are WS2_SUM (:50), so engine2 pre-sums all source voices into the ch(0) the module reads (:135; A:871) [R3]. Output is 1 channel (:132).
- **Extremes (inf):**
  - amount = 0: ratio 1, output exactly B.
  - smooth = 0: no smoothing; magnitude ≈|A| with B's phase. Where |B|≈0 the gain is capped at 1e3.
  - morph = 0: phase from A; geometric magnitude reproduces |A| only within approx error (DESIGN.md:31: log2/exp2 within 2e-5 relative).
  - morph 0.5 geometric, bin in only one source: √(1e-7·y) ≈ −70 dB for y = 1.
  - flatten 0: gain = envA. flatten 1: gain = envA/envB.
- **NaN (inf):**
  - Blend-pitch NaN morph: sincos(NaN) leaves p NaN until enter(Morph) or clear_bins().
  - NaN release: env_a_ NaN until cleared.
  - NaN level: NaN output.
  - Stepped params: lround(NaN) unspecified, then clamped.

**Num**

| Item | Detail | Cite |
|---|---|---|
| Denormals | No flush. Recursive state is only env_a_/env_b_ (per frame) and unit-normalized phasors. Exact silence clears the state. | :225-231, :271-275 |
| Division guards | x>0, y>0 in track; 1e-20 in rotate and vocoder weights; loud>0 and x>0 in combine; epsilons 1e-6 / 1e-7 ("amplitude-sized") | :322-323, :339, :465, :527, :533; DESIGN.md:15 |
| Caps | 1e3 in Cross and Vocoder; no output clamp | :506, :468 |
| DC | DC bin passes; its imaginary part forced to 0 | :301 |
| float vs double | Bins, rings, OLA float. rate_, voc_span_, window build, unit table, vocoder coefficients, layout exp double. | :86, :105-109, :452-455, :440 |
| Sample rate | N scales by factor 1/2/4 at the 66/132 kHz thresholds, so Hz resolution and time smear match at 44.1/48 vs 88.2/96. Vocoder range fixed 70 Hz–12 kHz. (inf) Between thresholds (e.g. 64 kHz, factor 1) resolution scales with rate. | :38, :105 |
| Size invariance (inf) | Cross h is in bins, so the smoothing width in Hz changes 8× across N = 512…4096. Invariant across rate factors (same Hz/bin). | :493 |
| State | 13 words: version, hop_pos, mode, prev_mode, fade, size, drain, pending, RNG (4), chunk_pos. v1 (no chunk_pos) accepted. Load validates ranges, RNG stream oddness and chunk_pos < 128, then reset(); audio history is not restored. | :161-205 |
| Latency | Atomic store in set_size. DESIGN lists "engine re-query of latency_frames() after a parameter-driven change" as NOT done. | :221; DESIGN.md:57 |
| Reset | One fill_n over 3·Nmax clears rings A/B and OLA, relying on contiguity (:87-92). Phasors (1,0), envelopes 0, size default, RNG re-seeded. | :114-127 |

**Cost**
- Per frame (every N/4 samples):
  - 2 forward + 1 inverse real FFT of size N;
  - windowing 2N multiplies; OLA N multiply-adds;
  - track: 2 sqrt, ≤4 divisions, ~16 multiply-adds per bin.
- Extra per bin, by mode:

| Mode | Extra per bin |
|---|---|
| Morph geometric | 2 approx log2 + 1 approx exp2 + rotate (1 sqrt + 1 div) |
| Morph pitch=1 | Also 2 approx atan2 + 1 approx sincos |
| Cross | 2 prefix passes + 2 averaging passes (1 div each) + log2/exp2 + 1 div |
| Combine | ≤1 div |
| Interleave PV | rotate |
| Vocoder | Per band 2 sqrt + 1 std::pow; per frame 3 std::exp; per bin 2 PCG draws if noise > 0; band sums visit each bin ≈2–3× (inf) |

- During a mode fade (4 frames): one extra render per frame.
- Per sample: 1 multiply (level), 2 ring writes, 1 OLA read/zero, counters.
- (inf) ≈2 bin iterations per sample per pass, since (N/2+1)/(N/4) ≈ 2.
- DESIGN x86 measurements: Morph ≈75 µs per 2048 frame (DESIGN.md:19), ≈200 µs per 4096 frame (DESIGN.md:31). (inf) 75 µs is ≈0.7% of a 10.67 ms hop @48k/2048. All of a frame's work runs at one sample per hop ("per-hop burst"), left open for 96 kHz/4096 (DESIGN.md:58).
- Memory: storage_floats = RealFft::floats(Nmax) + 5·Nmax + 28·K + 1, K = Nmax/2+1 (:41-44). RealFft::floats is not visible.

| Rate | Nmax | Floats excl. FFT | Bytes excl. FFT |
|---|---|---|---|
| 44.1/48k | 4096 | 77,853 | 311,412 |
| 88.2/96k | 8192 | 155,677 | 622,708 |
| 176.4/192k | 16384 | 311,325 | 1,245,300 |

- Fixed arrays: 4 × 64 floats + 2 × 64 uint32 (:549-550).

**Artefacts (inf)**
- Latency = N:

| Size | 44.1k | 48k | 96k (N doubled) |
|---|---|---|---|
| 0 | 11.6 ms | 10.7 ms | 10.7 ms |
| 1 | 23.2 ms | 21.3 ms | 21.3 ms |
| 2 | 46.4 ms | 42.7 ms | 42.7 ms |
| 3 | 92.9 ms | 85.3 ms | 85.3 ms |

- **Phase vocoder (Morph, Interleave-PV):** phasiness and transient smear. No phase locking across bins; in louder-bin mode a bin can switch between A's and B's advance from frame to frame.
- **Geometric morph:** bins present in only one source drop to ≈−70 dB at m = 0.5, so the mid-morph between non-overlapping spectra sounds hollow. The linear curve avoids this.
- **Musical noise:** Max/Min/Mean flicker between sources when |A| ≈ gb·|B|.
- **Mode crossfade:** a linear blend of complex spectra, not magnitudes, so out-of-phase bins partly cancel during the 4 frames.
- **Size change:** output fades out over 0.75N, then the new size fades in, giving an audible dip (DESIGN.md:35). The interleave schedule does not advance during the drain.
- **Cross noise lift:** where B is near its noise floor, the 1e3 cap lifts B's noise by up to +60 dB.
- **Time-domain aliasing:** pre/post-echo within N under strong per-bin gains.
- **Silence rule:** fires only on exact zeros; DC, dither or a noise floor keep frames and phases running.
- **Vocoder noise:** per-bin random spectrum, so its texture changes every hop.

**Ref (mk)**
- STFT/WOLA, Hann/Hann at 75% overlap (Allen & Rabiner 1977; Griffin & Lim 1984). Zero-padding avoids circular aliasing when filtering.
- Phase vocoder (Flanagan & Golden 1966; Dolson 1986). Phasiness fixes: phase locking (Laroche & Dolson 1999), PGHI (Průša et al. 2017).
- Cross-synthesis envelopes: moving average here; alternatives cepstral, LPC, true envelope (Röbel & Rodet).
- FFT channel vocoder (after Dudley); alternatives filter-bank, LPC.
- Lower latency: partitioned or multi-resolution STFT.

### C2.4 sound.blend (native/modules2/blend/dsp.h)

**Alg**
- Output = a·cos(π/2·pos) + b·sin(π/2·pos), equal-power, every sample (:169).
- Every jump uses a raised-cosine glide w = 0.5 − 0.5·cos(π·at/len), from glide_from_ toward a possibly moving target (:163-168). A new glide always starts from the current position (:116-120).
- **Crossfade mode:** target = balance, or 1 − balance after an odd number of switch edges (:155-162). Outside a glide, pos = target directly (:168).
- **Splice mode:** A/B alternate in segments; flip on segment end or switch edge, with a new segment and glide (:147-154). Segment length = clamp(seg, 0.01, 2 s)·rate·(1 + jitter·bipolar), floor 2·fade samples (:122-127). The length is drawn when the segment starts (DESIGN.md:14).
- **Mode change:** starts a glide. Entering Splice picks the source by pos ≥ 0.5 and begins a segment (:138-145).
- **Switch input:** inline Schmitt (high >0.5, low <0.25), same thresholds as ws::Schmitt but with member state so it can be saved (:135-137).

**AA/NL**
- No nonlinear operations on audio, only time-varying gains. No oversampling.
- (inf) Gain changes are AM: a fade of length T spreads energy over ≈1/T (e.g. ~1 kHz at the 1 ms minimum). That is splatter, not aliasing.

**Params**

| Param | Range / default | Flags | Use |
|---|---|---|---|
| mode | 0–1 (Crossfade, Splice) / 0 | stepped + mod (:21) | Every sample, lround + clamp (:132) |
| balance | 0–1 / 0.5 | mod (:22) | Every sample; not smoothed outside glides |
| seg_a, seg_b | 0.01–2 s, log / 0.22 | mod (:23-24) | Read only at segment start (:123) |
| fade | 0.001–0.2 s, log / 0.01 | mod (:25) | Every sample: max(1, round(s·rate)) samples (:115, :133); fixed for the duration of each glide |
| jitter | 0–1 / 0.3 | mod (:26) | At segment start; one PCG draw per segment |

- **Per-voice:** none. A and B are WS2_SUM, pre-summed by engine2 (A:871) [R3]; Switch is WS2_FIRST, so only voice 0 drives it (:17-18). The module reads ch(0) of each (:49). Output 1 channel (:47).
- **Fade in samples:** 44–8820 @44.1k, 48–9600 @48k, 96–19200 @96k.
- **Extremes:**
  - balance 0: output = A exactly.
  - balance 1: sin = 1, but (inf) float cos(kHalfPi) ≈ −4.4e-8, so A leaks at ≈−147 dB.
  - jitter 1: length from ≈0 (raised to the 2·fade floor) to ≈2·seg.
  - seg < 2·fade (e.g. 0.01 s vs fade 0.2 s): the segment is 0.4 s.
- **NaN (inf):**
  - fade NaN: max(1.0, NaN) returns 1.0, a 1-sample fade.
  - seg/jitter NaN: max(2·fade, NaN) returns 2·fade.
  - balance NaN: NaN output; pos recovers once balance is valid and no glide runs.
  - mode NaN: lround unspecified, then clamped.

**Num**
- No recursive state, so no denormals. No clipping; peak gain cos + sin = √2 at pos 0.5.
- glide_len_ is ≥1 whenever it is used (:115).
- rate_ is double; segment maths double (:125-126). Gains and position float.
- **Constant fast path:** when all inputs and mode/balance/fade are constant, the mode is Crossfade and no glide runs, process returns after sample 0 with the output marked constant (:52-59).
- **State:** 13 words: position and glide start as raw float bits, glide counters, mode, source, remaining, flags, RNG (4) (:65-86). Load rejects positions outside [0, 1] (including NaN), glide_at > glide_len, and lengths > rate·8 (:97-100). The comment says the longest segment is "2 s × (1 + jitter)" = 4 s.
- prepare calls reset, which re-seeds the RNG (:28-43).

**Cost (inf)**
- Per sample: 3 param reads, lround + clamp, a double multiply and round in samples(), the Schmitt compare, float cos + sin (:169), plus 1 cos during a glide (:165). ≈20 flops + 2–3 transcendentals.
- Per segment: 1 PCG draw + a few double ops.
- Memory: struct members only (:172-177), <~100 B. No buffers or tables.

**Artefacts (inf)**
- **Correlated sources:** same or phase-aligned A/B gives +3 dB mid-glide (cos + sin = √2). Uncorrelated sources keep constant power (DESIGN.md:18).
- **Short fades:** 1 ms fades on low-frequency material sound like clicks. DESIGN's listening note names 3 ms (DESIGN.md:31).
- **Balance zipper:** balance goes straight to the gains outside glides.
- **Splice phase:** splices fall at arbitrary phase (no zero-crossing or correlation alignment), so crossfades between similar material can comb or cancel briefly.
- **CPU:** Splice never takes the constant fast path, even with silent inputs.

**Ref (mk)**
- sin/cos constant-power ("−3 dB pan law") suits uncorrelated signals; linear crossfade suits correlated ones.
- Correlation- or zero-crossing-aligned splicing: SOLA/WSOLA, tape-style editors.
- Randomized segment lengths resemble brassage/shuffle (CDP brassage; Roads, *Microsound*).

### C2.5 essentials.mixer (native/modules2/mixer/dsp.h)
PortRamp and port_flags come from ../port_state.h (:3), not in the pack.
- **Alg:** per voice c and sample i, out = float(in_a·rampA.next() + in_b·rampB.next()) (process, :14). DESIGN: "double multiplies, addition order and 5 ms plain-unit ramps are retained" from ABI1 native/modules/mixer/module.cpp @ f23ea96 (DESIGN.md:4). (inf) PortRamp is probably like ws::LinearRamp (5 ms, double, signals.h:9-31); not verified.
- **AA/NL:** none; linear, no saturation.
- **Params:**
  - level_a, level_b: 0–2, default 0.5, linear, port_flags (:10).
  - Per-voice: 16 fixed voices, 2 ramps each, initialized to 0.5 (:11). Read per voice and per sample with value(c, i) (:14).
  - Output channels = b.channels() (:14). voices[c] is indexed without a bound check.
  - Two smoothing layers: host "D7 parameter pipeline" (DESIGN.md:4) plus the ramps. The host layer is a 5 ms linear ramp on base changes only; cable modulation reaches the module unsmoothed [X2].
  - Extremes: level 2 = +6 dB per input, so output can reach 2|a| + 2|b|; no clamp.
  - NaN (inf): depends on PortRamp. If it behaves like LinearRamp, NaN persists until a valid target's ramp completes (≈5 ms).
- **Num:**
  - No recursive state, so no denormal or DC issues. No clipping.
  - Double multiplies per DESIGN, then a float cast (:14). Missing inputs contribute zero (DESIGN.md:4).
  - State: v1 plus every voice's ramps as little-endian binary64 (DESIGN.md:4). Load uses a staged copy with range (0, 2) and commits atomically (:15-16).
  - Always mark_constant(false) (:14).
- **Cost (inf):** per sample per voice: 2 param reads, 2 ramp update/next, 2 double multiplies + 1 add, 1 cast. 32 ramps ≈ 1.3 KB if each is LinearRamp-sized (≈40 B).
- **Artefacts (inf):**
  - If PortRamp restarts a full 5 ms ramp per new value (LinearRamp semantics, signals.h:18-23), continuous modulation is followed piecewise-linearly with up to 5 ms lag, and audio-rate AM is smoothed and attenuated. Stepped changes do not zipper.
  - More than 16 channels would index out of range; the engine maximum is not visible.
- **Ref (mk):** standard gain-ramped summing mixer. Alternatives: one-pole smoothing, dB-domain smoothing, per-block fixed-length ramps.

### C2.6 essentials.output (native/modules2/output/dsp.h)
- **Alg:** per-voice pass-through out[c][i] = in[c][i]. If the input is constant, only sample 0 is written and the output is marked constant (:12). No params (:10). DESIGN: opens no device; Engine2 output(node, port, bus_channel) mixes voice channels into the bus once; the module does not pre-sum (DESIGN.md:4).
- **AA/NL:** none.
- **Params:** none. But DESIGN.md:4 says "Continuous controls are per-voice D7 parameters" and "Plain-unit ABI1 ramps are retained where present". The input is declared WS2_SUM (:7) [R4]. engine2 does the summing at the input (A:871), so the module receives one channel and DESIGN's "the module does not pre-sum" holds [R3][X3]. Output channels = b.channels() ((inf) 1, since the node has no WS2_POLY input).
- **Num:** no clipping, dither, DC blocking or gain. Final bus conversion and clipping are not visible. State v1 only (:13-14).
- **Cost:** one copy per sample per channel, or one write per channel when constant. No extra memory.
- **Artefacts (inf):** none from the module; output clipping or truncation is in the engine or device layer (outside the pack).
- **Ref (mk):** terminal node. Some designs put a safety limiter or DC blocker here; this one does not.

### C2.7 essentials.quantizer (native/modules2/quantizer/dsp.h)

**Alg**
- Polyphonic nearest-note quantizer on a 12-bit pitch-class mask, with hysteresis, degree shift, octave offset and a "changed" trigger (:2).
- Input × 12 = semitones from C4 (:197, :230, :65). Output = out_note/12.0 in double, rounded to float once (:154). DESIGN: (midi − 60)/12 (DESIGN.md:7).
- Scale tables, 13 interval masks (:37-49); names are (inf), the code has none:

| Idx | Intervals | Name (inf) |
|---|---|---|
| 0 | 0–11 | Chromatic |
| 1 (default) | 0,2,4,5,7,9,11 | Major |
| 2 | 0,2,3,5,7,8,10 | Natural minor |
| 3 | 0,2,3,5,7,8,11 | Harmonic minor |
| 4 | 0,2,3,5,7,9,10 | Dorian |
| 5 | 0,1,3,5,7,8,10 | Phrygian |
| 6 | 0,2,4,6,7,9,11 | Lydian |
| 7 | 0,2,4,5,7,9,10 | Mixolydian |
| 8 | 0,1,3,5,6,8,10 | Locrian |
| 9 | 0,2,4,7,9 | Major pentatonic |
| 10 | 0,3,5,7,10 | Minor pentatonic |
| 11 | 0,3,5,6,7,10 | Blues |
| 12 | 0,2,4,6,8,10 | Whole tone |
| 13 | n0..n11 switches | Custom (kCustom, :33) |

- **Mask** (read_config, :158-176): a table scale is rotated by root (bit p set if table bit (p − root + 12)%12 is set, :171-172). Custom uses the 12 switches directly (:168-169). An empty mask becomes 0xFFF, chromatic (:174). Custom defaults n0..n11 = C major (C, D, E, F, G, A, B) (:25-30).
- **nearest** (:96-110): from f = ⌊x⌋, search down f…f−11 and up f+1…f+12. Ties go down: (hi−x) < (x−lo) ? hi : lo (:109). The mask is never empty, so both searches always end (:95).
- **Hysteresis** (set_hold, :127-143; check :149): on choosing a note, cache the region [mid(below, note) − 0.1, mid(note, above) + 0.1]; neighbours are allowed notes, or ±12 if none (:141-142; kHysteresis = 0.1 st, :34). Inside the region with the mask unchanged, nothing is recomputed (:149).
- **shifted** (:113-124): index = count of allowed pitch classes below the note's class + shift; wraps = floor_div(index, k), k = popcount(mask); degree = index − wraps·k; returns the matching set bit + 12·(octave + wraps). Shift and octave are applied after hysteresis (:150; DESIGN.md:6).
- **update** (:146-156): out = shifted(note) + 12·octave. changed = a note was already held and out differs from the previous output (:151).
- **Trigger input:** if connected, sample only on a Schmitt rising edge (ws::Schmitt 0.5/0.25). The first sample with no held note is always taken: sample = !v.has || (now && !v.high) (:192-196, :225-229). Unconnected: quantize every sample (:224).
- **Changed output:** ws::Trigger 1 ms = ceil(rate·0.001) samples (signals.h:41), fired at :230 and :210.

**AA/NL**
- Staircase nonlinearity on a control signal; no anti-aliasing, and none relevant for discrete-step CV.
- (inf) An audio-rate signal on the pitch input in ungated mode gives a staircase with step discontinuities, not band-limited.

**Params**

| Param | Range / default | Flags |
|---|---|---|
| scale | 0–13 / 1 | stepped + automatable only (:12-14, :23) |
| root | 0–11 / 0 | stepped (:23) |
| shift | −7..7 / 0 | stepped (:24) |
| octave | −3..3 / 0 | stepped (:24) |
| n0..n11 | 0–1, C-major defaults | stepped (:25-30); Custom mask |

- All read with value(0, 0) = ch 0, sample 0, once per block (:160; DESIGN.md:8). Comment on stepped(): "no host smoothing, integer values, no cable modulation" (:11). lround + clamp (:160).
- **Per-voice:** up to 16 (kMaxVoices, :32). n = min(b.channels(), 16) (:179); extra channels are dropped. Settings are shared across voices. Each voice has its own Schmitt, Trigger and hold state (:58-69).
- **Extremes / NaN:**
  - NaN input becomes 0 (:147), then clamped to ±1200 st (±100 oct, kLimit, :35, :148).
  - (inf) With octave ±3 and max shift, the output stays within ≈±1243 st (≈±103.6 in 1.0/oct), so integer maths stays small (:35 comment).
  - (inf) Shift +7 on a 1-note mask moves 7 octaves (wraps = 7); on a pentatonic mask, 1 octave + 2 degrees.
  - (inf) NaN params: lround(NaN) unspecified, then clamped.

**Num**

| Item | Detail | Cite |
|---|---|---|
| Denormals | No recursive float state | – |
| Integer maths | floor_div correct for negative notes; allowed() reduces modulo 12 with floor semantics | :87-88 |
| float vs double | Input promoted to double (×12.0); hold regions double; output float rounded from double | :67, :154 |
| Exactness | Code comment: "exact for every allowed note" (:154). DESIGN: "correctly rounded" (DESIGN.md:7). (inf) n/12 is not exact for most n, so "correctly rounded" is the precise claim. | – |
| Sample rate | Only the 1 ms trigger: 45/48/96 samples @44.1/48/96k | :76; signals.h:41 |
| Reset | reset() rebuilds each voice from defaults and re-prepares its trigger (:80-85). prepare() does not call reset() (:74-77). | – |
| Save/load | The struct defines NO save_state/load_state (:16-237). DESIGN: "Held notes are not saved; they restart on reset or load" (DESIGN.md:8). Every other module in the pack defines both. | – |

**Cost (inf)**
- Per block: up to 16 param reads + 12-iteration mask build (:158-176).
- Per sample per voice:
  - Ungated, inside the hold region: NaN check, clamp, 3 compares, shifted(), 1 double divide, 1 trigger step.
  - shifted() with shift ≠ 0: ≤36 loop iterations of bit ops (2 popcount loops + 1 search) + 2 floor_div.
  - Leaving the hold region: nearest() + set_hold(), ≤24 + 24 allowed() checks, each with a floor_div.
  - Gated: Schmitt compare; update() only on rising edges.
- Constant fast path: when pitch (and the trigger, if connected) is constant, only sample 0 is computed; pitch output marked constant; changed output marked constant when no voice fired and none still has a pulse running (:184-215).
- Memory: 16 voices × ≈48 B ≈ 770 B, plus a 26 B table. No transcendentals.

**Artefacts (inf)**
- **Block-rate settings:** scale/root/shift/octave changes take effect at the next block boundary. Jitter = 1 block; results depend on block size (unlike spectral's sample-counted design).
- **Changed trigger, ungated:** a config change re-quantizes on the next sample; if the output note changes, a trigger fires with no input movement.
- **Gated:** config changes are not visible until the next trigger edge, because v.pitch updates only inside update().
- **Merged pulses:** two changes within 1 ms merge into one long pulse; Trigger::fire() restarts the counter (signals.h:42), so there is no gap.
- **Fixed hysteresis:** 0.1 st for every scale. For chromatic the hold region is note ±0.6 st; input noise above 0.2 st peak-to-peak can still chatter at midpoints.
- **History-dependent S&H:** in gated mode, the same voltage near a midpoint can give different notes depending on the previously held note.
- **Ties:** an exact midpoint with no held note resolves down.
- **No slew:** pitch steps are instant; any portamento is downstream.

**Ref (mk)**
- Nearest-note quantizer with hysteresis is common in Eurorack firmware (Mutable Instruments Braids/Plaits quantizer; Ornament & Crime, which also offers scale-degree transposition, like shift).
- Alternatives: rounding to nearest degree via tables; weighted or "attracting" quantizers; hysteresis as a fraction of the neighbour gap rather than fixed 0.1 st.

### C2.8 essentials.scale_offset (native/modules2/scale_offset/dsp.h)
- **Alg:** per voice and sample, out = float(in·scale_ramp.next() + offset_ramp.next()) (:12). Ported from ABI1 native/modules/scale_offset/module.cpp @ f23ea96: "double scale ramp plus the double offset ramp, preserving operation order" (DESIGN.md:4). Missing input outputs the smoothed offset (DESIGN.md:4).
- **AA/NL:** none; linear, no saturation or clamp.
- **Params:**

| Param | Range / default | Flags | Smoothing |
|---|---|---|---|
| scale | −2..2 / 1, linear | port_flags (:8) | PortRamp per voice (:9); per DESIGN 5 ms "plain-unit ABI1 ramps" + host "D7 base smoothing" (DESIGN.md:4) |
| offset | −1..1 / 0, linear | port_flags (:8) | Same |

  - Per-voice: 16 fixed voices (:9). Output channels = b.channels() (:12); voices[c] not bound-checked, same as mixer.
  - Ports: in and out both WS2_CV_BI, no SUM/POLY flags (:7).
  - Extremes (inf): for input ±1, output up to ±3 (|scale| ≤2, |offset| ≤1), unclamped. Negative scale inverts.
  - NaN: depends on PortRamp (not visible). (inf) If like LinearRamp, NaN stays in ramp state until a valid ramp completes (signals.h:18-23).
- **Num:**
  - No recursive state, so no denormal or DC issues. Double multiply-add, single cast to float (:12).
  - Sample rate: only the ramp length via PortRamp::prepare(rate) (:10).
  - State: v1, every voice's 2 ramps. Load uses a staged copy with range checks (−2, 2) and (−1, 1), then commits (:13-14). DESIGN: binary64 little-endian, atomic validation (DESIGN.md:4). Ramp serialization is in port_state.h (not visible).
  - Reset "snaps both ramps to their user targets" (DESIGN.md:4; :11). prepare() prepares the ramps but does not call reset() (:10).
- **Cost (inf):** per sample per voice: 2 param reads, 2 ramp update/next, 1 double multiply-add, 1 cast; no transcendentals. 32 ramps ≈1.3 KB if LinearRamp-sized.
- **Artefacts (inf):**
  - If PortRamp restarts a full 5 ms ramp per new value, audio-rate modulation of scale (VCA/ring-mod use) or offset is lagged and low-passed, not followed sample by sample.
  - Host D7 + module ramp = two lag layers; combined time constant not visible.
  - >16 channels would index out of range (same as mixer).
- **Ref (mk):** standard attenuverter/offset. Analog hardware is a pure multiply-add with no lag. Software often smooths the knob path but passes CV-rate modulation unsmoothed.

### C2.9 essentials.clock (native/modules2/clock/dsp.h)

**Alg**
- Free-running double-precision phase accumulator per voice. While running, each sample (:12):
  1. output phase + 1e-12 < duty ? 1 : 0, computed before the increment;
  2. phase += bpm·ticks/(60·rate);
  3. if phase ≥1, phase −= floor(phase).
- Ported from ABI1 native/modules/clock/module.cpp @ f23ea96: "free-running double phase with the ABI1 epsilon at duty boundaries … No transport sync is added" (DESIGN.md:4).
- **Reset input:** high = isfinite(input) && input ≥0.5; a rising edge sets phase = 0 (:12). Single threshold, no hysteresis (unlike ws::Schmitt). Applied before output on the same sample, so the gate is high on that sample.
- **Run:** ≥0.5 advances; otherwise output 0 and the phase is frozen, not reset (:12).
- Period = 60·rate/(bpm·ticks) samples:

| Setting | @48k | @44.1k |
|---|---|---|
| 120 BPM, 1 tick | 24,000 (exact) | 22,050 (exact) |
| 300 BPM × 24 ticks (max, 120 Hz) | 400 | 367.5 |

**AA/NL**
- Naive 0/1 gate, edges on the sample grid.
- (inf) Edge times quantized to 1 sample (20.8 µs @48k). Non-integer periods jitter deterministically (367.5 alternates 367/368). Irrelevant for control; aliases if used as audio.

**Params**

| Param | Range / default / unit | Flags | Handling |
|---|---|---|---|
| bpm | 20–300 / 120 / BPM, linear | port_flags (:8) | PortRamp, 5 ms ramp per DESIGN (:9, :12; DESIGN.md:4) |
| ticks_per_beat | 1–24 / 1 | port_flags (:8) | Only on change: ticks = floor(t + 0.5) (:12). NOT clamped in the module. |
| duty | 0.01–0.99 / 0.5 | port_flags (:8) | Applied immediately on change (:12) |
| run | 0–1 / 1 | port_flags (:8) | Threshold 0.5 (:12) |

- ticks/duty/run are cached as floats (last_*) and recomputed only when the float value changes (:9, :12).
- ticks_per_beat and run use port_flags (continuous/modulatable), NOT WS2_STEPPED; rounding and thresholds are done in the module.
- **Per-voice:** 16 fixed voices, each with its own params, reset edge detector and phase (:9). Output channels = b.channels(). voices[c] not bound-checked (:12).
- **Extremes / NaN (inf):**
  - ticks out of range or NaN, no clamp: if the host passes e.g. ≤0 from CV, ticks = 0 stops the phase and the output holds its level. Negative ticks push phase below 0, where the ≥1 wrap never fires, so the output stays high.
  - NaN ticks or bpm: phase NaN; NaN + 1e-12 < duty is false, so output 0 until a reset edge sets phase 0.
  - NaN run: ≥0.5 is false, so stopped.
  - Non-finite reset input: treated as low (:12).
  - State load requires ticks to be an integer in 1–24 and duty in [float(0.01), float(0.99)] (:14). Live values are not validated the same way.

**Num**

| Item | Detail | Cite |
|---|---|---|
| Precision | phase, ticks, duty, run double; cached comparison values float | :9 |
| Epsilon | phase + 1e-12 < duty ("ABI1 epsilon at duty boundaries") | :12; DESIGN.md:4 |
| Wrap | phase −= floor(phase); handles increments ≥1 (not reachable in declared ranges; max increment = 120/rate) | :12 |
| Division | /(60·rate) every sample; rate from host | :12 |
| Denormals | None (phase bounded in [0, 1)) | – |
| Sample rate | Increment ∝ 1/rate; tempo exact at any rate, only edge quantization changes | :12 |
| Reset | prepare calls reset (:10). reset() sets phase = 0, reset_high = false, resets the bpm ramp; does NOT reset ticks/duty/run or the last_* caches (:11). | – |
| State | v1, per voice: 4 doubles (phase, ticks, duty, run), bpm ramp, 3 floats (last_*), reset_high u32. Load validates the ranges above, finiteness, phase in [0, 1), bpm ramp (20, 300), then commits a staged copy. | :13-14 |

**Cost (inf):** per sample per voice ≈10–15 ops: 4 param reads, 3 float compares, isfinite, 1 ramp step, 1 compare, 1 multiply, 1 divide, 1 add, occasional floor (only on wrap or ticks change). No transcendentals. Memory: 16 × ≈90 B ≈1.4 KB.

**Artefacts (inf)**
- **Duty raised mid-cycle** above the current phase while the gate is low: the gate goes high again in the same cycle, an extra rising edge (double trigger). Lowering duty below the phase ends the gate early.
- **Reset while high:** phase → 0 but the output stays high, so downstream edge detectors see no new rising edge.
- **Reset chatter:** single 0.5 threshold, no hysteresis; a noisy or slow reset signal can cause multiple resets.
- **Run resume:** phase frozen while stopped; on resume the gate goes high immediately if the frozen phase is below duty. That can be a partial first pulse, or a full pulse right after a reset.
- **BPM modulation:** the 5 ms ramp + host smoothing lag fast BPM modulation; phase is continuous, so tempo changes are glitch-free.
- **Short pulses:** 120 Hz at duty 0.01 is ≈4 samples high @48k (≈3–4 @44.1k). Schmitt triggers see it; block-rate consumers may miss it.
- **No sync:** no tap tempo, external clock follower or transport link (DESIGN.md:4). Instances drift only by their params; there is no shared timebase.

**Ref (mk)**
- Phase-accumulator (DDS-style) clock with a gate comparator is standard.
- Alternatives: sub-sample edge timestamps (event-based gates); integer sample-counting clocks; a PLL or period-measuring follower like fx.delay's clock_tick (delay/dsp.h:150-172); transport-locked clocks (Ableton Link, plugin host transport).

### C2.10 sequencing.groove (native/modules2/groove/dsp.h)
groove/config.h (Config, Step, Note/Tie, condition types, decode) is not in the pack.

**Alg**
- 2-track step sequencer: kTracks = 2, kSteps = 64, kClock = 512 (:53). The pattern holds 4×64 steps, but only 2 tracks are declared; t3/t4 slots are reserved (:21; DESIGN.md:7-8). Pattern comes from s.config.data via decode(); prepare fails if decoding fails (:93).
- **Internal clock:**
  - 1 tick = 1 sixteenth; samples_per_step = rate·15/bpm, with bpm from the pattern (:94). No BPM param.
  - Double phase: ++phase ≥ samples_per_step, then phase −= samples_per_step (:531-535).
  - (inf) The remainder carries, so average tempo is exact and edges land on the grid. 120 BPM: 6000 samples @48k, 12000 @96k, 5512.5 @44.1k (alternating 5512/5513).
- **External clock:**
  - Each Schmitt rising edge = exactly one sixteenth tick (:441-451, :530-546).
  - The edge interval in samples becomes samples_per_step (:447), used only for gate lengths.
  - No averaging, no consistency check (contrast fx.delay's 2% rule, delay/dsp.h:158-163).
  - A missing pulse holds the position, but gate ages keep advancing (:533). No timeout.
- **Step addressing** (boundary, :346-377):
  - Global sixteenth counter step wraps at 512 (:349).
  - A track advances when step % div == 0; step_t = (step/div) % length (:352-353).
  - DESIGN: lengths 8/16/32/64, div 1/2/4/8 sixteenths (DESIGN.md:10-13). Comment: every approved length × div divides 512 (:347).
  - Loop counter increments on the track's own wrap (:355).
- **Order at a step** (trigger_all, :329-336): all stepping tracks release, then trigger.
- **Same-sample precedence:** RESET > external run fall > STOP > MUTE > START > tick (:466-546; DESIGN.md:25).
- **Step kinds** (trigger, :281-327):
  - Note with velocity > 0: the condition is evaluated. On failure, mod1/mod2 still update and no note sounds (:287-296).
  - Tie: continues the sounding note. Ties after a failed condition still update mods (:297-304).
  - Chords: up to 5 keys (row.keys[0..key_count)) send NOTE_ON at the same offset, root first (:311-319; DESIGN.md:19-21).
- **Conditions** (condition_passes, :177-190):
  - Chance: xorshift32 13/17/5 (:171-176); passes if sample·100 < cond_a·2³², (inf) P ≈ cond_a %.
  - AB: (loop−1) % cond_b == cond_a−1.
  - First / NotFirst: loop == 1 / loop != 1.
  - Unknown types return false ("validated on the control thread", :188).
- **RNG seed:** pattern instance seed XOR host seed (:97-98), then a 32-bit hash per track (:164-170); zero avoided.
- **Gate length** (gate_duration, :206-219):
  - Look-ahead over following Tie steps, at most length−1 (:210-215).
  - duration = samples_per_step·div·(ties + last_gate_q/4) (:218); (inf) gate_q is in quarter-steps.
  - gate_q < 4 is a short gate: released when gate_age ≥ cutoff; gate_age counts sounding samples in double (:436-437, :563).
  - Full gate: released at the next step boundary (release_step, :275-280); comment says this keeps legacy v1 output byte-identical (:433-435).
- **Outputs per track, per sample** (:548-564):

| Output | Value |
|---|---|
| pitch | (row.key − 60)/12, root key only; set only when a note actually sounds (:323), otherwise held |
| gate | sounding.on, 0/1 |
| mod1, mod2 | Stepped CV, no slew |
| notes | Event port 4 + 5t, channel 0 (:227) |
| pos | Current step, or −1 when fully stopped (:558-559) |
| loop lo/hi | 16-bit halves of the loop counter |
| fired | Whether the current trig passed its condition |

**AA/NL:** not applicable; no audio. Gate/pitch/mod outputs are naive steps on the sample grid.

**Params**
- 10 params, all 0/1 stepped "rising-edge requests" (:41-52): run (labelled "Start"), stop, reset, mute, and t1/t2 run/stop/mute.
  - Edge = value > 0.5 after being low. The first observation is a baseline only (edge, :337-343; DESIGN.md:25 "Initial high is baseline"). Detection is per sample, i.e. sample-accurate.
- **Global STOP:** toggles stop_queued while running (:486). Completes only when step % master_steps() == 0 (:357-364). master_steps() = max length·div over playing, entering or armed tracks (:191-205), ≤512 ticks. (inf) At 120 BPM, 512 sixteenths = 64 s, the longest wait.
- **Track STOP:** toggles; completes at that track's own length·div boundary (:367-369, :487-493).
- **Track START while running:** queues an entry at the next multiple of 16 sixteenths (1 bar) in v2, 32 in v1 (:370; DESIGN.md:14-15).
- **MUTE (global or per track):** toggles and releases the affected notes immediately (:494-502).
- **Inputs:**

| Input | Behaviour |
|---|---|
| run, rising edge | Starts on the next tick: after one internal step period, or at the next external clock edge (:513-516, :524-529) |
| run, falling edge | Immediate stop with release (:480-484) |
| reset | Releases all, position → 0. If running, step 0 plays on the NEXT tick (reset_wait, :466-479, :536-540). |

- **Connection changes:** connecting or disconnecting the clock resets its Schmitt and measurement and reverts to the internal step length (:397-415).
- **Per-voice:** none in the CV sense; all outputs 1 channel. Notes (≤5) go only to the event port; pitch CV carries the root only.
- **NaN:** NaN > 0.5 is false, so a NaN param reads low (:338). Schmitt inputs hold their state on NaN (neither >0.5 nor <0.25, signals.h:35).

**Num**

| Item | Detail | Cite |
|---|---|---|
| Precision | phase, samples_per_step, gate_age, gate_cutoff double; outputs float | :72, :80 |
| Overflow | clock_samples saturates at UINT64_MAX (:445). Note IDs wrap 0x7fffffff → 1 (:244, :318). Loop counter uint32, output as exact 16-bit halves. | – |
| Division / modulo | step % master_steps() (:357) and step % div (:333-335, :352); these loops cover both tracks even when track_count < 2. (inf) If master_steps() returns 0 (track_count 0) or an unused track has div 0, the modulo is UB. Whether decode() prevents this is not visible. | – |
| Sample rate | Step length scales with rate; 1-sample resolution | :94 |
| Reset | prepare calls reset (:106). reset() cannot send events; the comment says the host's choke handles sounding notes (:111). | – |
| State | v2 stores loop + RNG per track (:136-141). v1 load → loop = 1 + fresh seed (:145-151). Any other version returns WS2_INVALID (:152); other modules return WS2_UNSUPPORTED. Loop or RNG = 0 rejected (:155-156). Transport, position and sounding notes not saved. | – |

**Cost (inf)**
- Per sample ≈60–80 simple ops, no transcendentals: 2 tracks × (short-gate check + flush check), 3 Schmitt calls (when connected), 10 param edge reads, 18 output writes, a few double ops.
- Per step: condition_passes (one xorshift); gate_duration tie look-ahead ≤63 iterations; unused_note_id ≤21 attempts × 20 slot checks per key, ≤5 keys (the comment bounds live voices at 20, :234-235).
- Memory: Config pattern (4×64 steps, size not visible) + 2 Player structs ≈130 B each (inf).

**Artefacts (inf)**
- **Merged gates:** consecutive full-length notes give a continuous gate with no low sample; release and re-trigger happen on the same sample before the output is written (:329-336, :552). Gate-driven envelopes do not retrigger; only the notes port shows separate OFF/ON. Short gates (gate_q < 4) do leave gaps.
- **Reset + clock on the same sample:** the reset branch skips the tick logic (:466 vs :485-546), so that pulse is used up and step 0 plays one pulse late. Same for an external run fall on a clock edge.
- **External clock jitter:** gate lengths follow the most recent interval as-is. A missed pulse doubles the measured interval, so the next short gates are ≈2× long. Steps stay pulse-locked.
- **Stopped external clock:** the position holds and full gates stay high indefinitely; no timeout (unlike fx.delay's 4 s, delay/dsp.h:168).
- **Internal tempo:** fixed at prepare from the pattern. (inf) Changing it needs a re-prepare or config change; no live tempo modulation.
- **Mods:** stepped, no slew; jump at step boundaries; skipped (failed-condition) steps still change them.
- **Global STOP latency:** up to one master cycle (512 ticks).
- **Refused NOTE_OFFs:** retried every sample (:438); new NOTE_ONs are blocked until they are sent (flush must succeed, :308), so notes drop out while the sink is congested.

**Ref (mk)**
- DESIGN names Westlicht Performer as the behavioural reference (DESIGN.md:4). Trig conditions (Chance, A:B, First/Not-first) match Elektron-style conditional trigs, also in Performer.
- Alternatives: averaging/PLL clock followers; sub-sample event timestamps; a separate trigger output or a guaranteed low sample between notes for retriggering; host transport sync (Ableton Link, MIDI clock 24 PPQN).

### C2.11 essentials.chord (native/modules2/chord/dsp.h)
No chord/DESIGN.md is in the pack; only dsp.h and module.cpp.

**Alg**
- Each incoming note becomes up to 5 notes: root + 4 optionally enabled semitone shifts. Event in and event out only (:20-21).
- **note_on (:133-170):**
  1. Drop if key not in 0–127 or channel not in 0–15 (:134).
  2. If the input note ID is already active, release that chord first (:135-136).
  3. Build keys: root, then each enabled shift in order. Enable is value ≥0.5; shift is lround + clamp ±24; keys outside 0–127 are skipped (:138-145). Params are read at the event's own offset (value(0, e.offset)), so per-event sample-accurate.
  4. Capacity: if pending + active voices + count > 80, the whole chord is dropped (:148). If none of the 16 activation slots is free, dropped too (:149-155).
  5. Each voice gets a new ID and a NOTE_ON with the input velocity; only sink-accepted notes are stored (:163-169).
- **IDs** (next_id, :82-90):
  - id = (tag << 20) | seq, 20-bit seq (kSeqMask, :33).
  - tag = the 4-byte config instance number & 2047 (11 bits) (:55-58). prepare fails without exactly 4 config bytes (:54).
  - At most 161 attempts (2·kPending + 1), skipping reserved IDs (:73-81).
  - The comment says the tag prevents aliasing when two Chord instances fan in (:51-52).
- **Releases:**
  - NOTE_OFF finds the activation by input note ID; for anonymous notes (ID < 0), by source + channel + key, most recent match (find, :124-132).
  - Release sends OFFs for the STORED keys, so param changes while held cannot strand notes (:113-123). OFFs carry the activation's source and channel (:117-119).
  - Refused OFFs go to a queue of 80 (kPending) and are retried at offset 0 at the start of the next block (flush, :104-112, :196).
- **CHOKE:** releases every activation from that source, or all if source is UINT32_MAX (:174-176).
- **Expression:** per-note expression is copied to every voice of the chord with that voice's key and ID (:183-190). Channel-wide (ID < 0) passes through unchanged (:178-182). (inf) Other event types are not forwarded.
- **Ordering** (process, :194-209): events grouped by offset; within a group, all non-ON events before ONs.

**AA/NL:** not applicable (events).

**Params**

| Param | Range / default | Flags |
|---|---|---|
| enable1..4 | 0–1 / 1, 1, 0, 0 | stepped + automatable (:22-31) |
| shift1..4 | −24..24 st / 4, 7, 12, −12 | stepped + automatable |

- Default chord = root, +4, +7 (major triad). +12 and −12 are disabled by default.
- Changes apply only at the next note-on; held chords keep their keys.
- **Extremes (inf):** shift 0 or two equal enabled shifts give duplicate keys with different IDs. Shifted keys outside 0–127 are silently dropped, so chords near the range edges lose notes.
- **NaN (inf):** enable NaN < 0.5 is false, so the voice is ENABLED; the shift is then lround(NaN) (unspecified), clamped ±24.

**Num**
- Fixed storage: 16 activations × 5 voices + 80 pending events (:33, :46-49).
- (inf) If the 80-entry queue is full, a refused OFF is lost (:120) and a note can stick downstream. The note-on capacity check (:148) reserves release space for active voices, which makes this unlikely.
- (inf) tag & 2047 means instance numbers differing by a multiple of 2048 share a tag.
- State: version word only; load calls reset(), comment "Active notes and pending releases are transient; never resurrect" (:210-217). (inf) Notes sounding downstream at load lose their mapping unless the host chokes them.
- reset clears tables without sending OFFs (:60-66). prepare does not call reset.

**Cost (inf)**
- Per block: flush of ≤80 events.
- Per NOTE_ON: 8 param reads; ≤5 next_id calls, each reserved() check scanning ≤16·5 + 80 = 160 entries (typically 1 attempt, worst case 161); ≤5 emits.
- Per NOTE_OFF or expression: find over 16 slots, ≤5 emits.
- Memory: ≈16 × 72 B ≈1.2 KB activations + 80 × sizeof(ws2_event) (size not visible).

**Artefacts (inf)**
- Whole chords dropped silently when the 16 slots or the 80-voice budget run out; no counter is kept (unlike midi_to_cv's dropped).
- Partial chords if the sink refuses some NOTE_ONs (:167).
- Duplicate keys give two same-pitch voices that may phase or double in level downstream.
- Anonymous same-key overlaps are released LIFO (:129).

**Ref (mk):** fixed-interval chord memory / harmonizer (DAW MIDI effects, hardware chord memory). Alternatives: scale-aware diatonic harmonization (combine with quantizer masks), inversions/voicing rules, strum offsets.

### C2.12 midi.to_cv (native/modules2/midi_to_cv/dsp.h)
The voice core comes from ../../voice/note_to_cv.h (:4, :29), not in the pack. DESIGN: the MIT native/voice/ core is the "voice-policy oracle" (DESIGN.md:5-6).

**Alg**
- UMP parser → voice::NoteToCv core.
- Accepted: UMP type 2 (MIDI 1 channel voice) or type 4 (MIDI 2, 2 words); group 0 only; channel filter (0 = omni). Everything else increments ignored (:110-117). DESIGN: other groups stay available on the raw MIDI port (DESIGN.md:12).

| Message | Handling | Cite |
|---|---|---|
| Note on/off | MIDI 1 velocity 0 = OFF (MIDI 1 only, DESIGN.md:10-11). Velocity /127 (MIDI 1) or (data>>16)/65535 (MIDI 2, 16-bit). last_note = (key−60)/12 when the note is assigned or held. | :131-143 |
| CC64 | Pedal on if ≥64 (MIDI 1) or ≥0x80000000 (MIDI 2); only when sustain = hold | :145-147 |
| CC120 / CC123 | Release channel | :148-150 |
| CC1 | /127 or /(2³²−1) | :151 |
| Other CCs | No action and NOT counted in ignored | :144-151 |
| Pitch bend | MIDI 1: 14-bit (lsb \| msb<<7) − 8192, ÷8192 if negative, ÷8191 if positive, exactly −1..+1. MIDI 2: 32-bit ÷2³¹ / (2³¹−1). | :152-159 |
| Channel pressure | Stored per source/channel → aftertouch output | :160-161 |
| Poly pressure | NOTE_EXPRESSION (pressure) to each gated voice with matching source/channel/key | :162-174 |

- **Controller state:** per (source, channel), 256 slots (16 endpoints × 16 channels, :31-32), kept until the source is choked (:104-109).
- **Render:** b.split(segment_fn, event_fn) (:81-176); (inf) splits at event offsets, so CV is sample-accurate at events.
- **Outputs per voice, per sample** (:84-99):
  - pitch = v.pitch + (apply_bend > 0.5 ? bend·range/12 : 0), 1.0/oct;
  - gate 0/1; velocity = v.velocity;
  - aftertouch = channel pressure for the voice's channel;
  - pressure = per-voice v.pressure;
  - bend = raw −1..1;
  - mod = CC1 for the voice's channel;
  - last_note: 1 channel, raw note-on pitch, independent of bend and gate (:36).

**AA/NL:** not applicable; stepped CV at event times.

**Params**

| Param (array idx) | Range / default | Read |
|---|---|---|
| voice_count (0) | 1–16 / 4, clamped to max_channels | Block rate, value(0,0) (:69) |
| allocation_mode (1) | 0–3 rotate/reuse/reset/mono | Block |
| steal_policy (2) | 0–0 "oldest" | NEVER read |
| mono_priority (3) | 0–2 last/low/high | Block |
| legato (4) | 0/1 / 0 | Block |
| sustain (5) | 0/1 / 1 (hold) | Block (:76) |
| pitch_bend_range_semitones (6) | 0–48 / 2 st | PER SAMPLE (:92) |
| apply_bend (7) | 0/1 / 1 | PER SAMPLE (:92) |
| channel_filter (8) | 0–16 / 0 (omni) | Block |

- Any change to voice count, mode, priority, legato or channel filter releases ALL notes, then reconfigures (:73-75).
- Sustain switched hold → ignore releases pedal-held notes (:77).
- Polyphony ≤16; output channels = allocator voice count (:79-80). Bend, mod and channel pressure are per channel, so (inf) MPE-style per-channel bend/pressure reach the right voices. CC74 is not handled.
- No glide or smoothing in this file; core portamento not visible.
- Bend range 0 = no bend; max ±4 octaves (48 st).
- NaN (inf): lround + clamp; NaN apply_bend (> 0.5 false) disables bend.

**Num**
- MIDI 2 bend and CC conversions done in double, then float (:151, :158).
- Refused OFF/CHOKE: 256-entry pending queue, retried at offset 0 in the next block (:55-65). Overflow sets panic_pending → release_all + global CHOKE (:66-67).
- dropped and ignored counters exist (:35) but nothing in this file reads them.
- prepare stores only max_channels and does NOT call reset (:37). reset() clears core, expressions, pending queue and counters (:38-47).
- State: version word only; load resets (:178-179). DESIGN: held activations and controller history deliberately not restored (DESIGN.md:13-15).
- No sample-rate dependence in this file.

**Cost (inf)**
- Per sample per voice: 7 output writes + 2 param reads.
- Per segment per voice: one expression() lookup, a linear scan of 256 slots (:48-53, :86-88); up to ≈4k comparisons per segment with 16 voices.
- Per MIDI event: another 256-slot scan; poly pressure also scans all voices.
- Memory: ≈256 × 28 B ≈7 KB expressions + 256 × sizeof(ws2_event) pending + core (size not visible).

**Artefacts (inf)**
- CC1 in MIDI 1 steps by 1/127 with no smoothing, so it zippers on audio params. 14-bit bend steps at the incoming message rate.
- Changing voice count/mode/legato/priority/filter while playing cuts every note (:73-75).
- Bend range and apply_bend are read per sample, so changing them while bent makes the pitch jump instantly.
- Events beyond 256 controller slots, non-zero groups and unhandled CCs are dropped silently; only the counters record them (not exposed here).

**Ref (mk):** conventional MIDI-to-CV like VCV Rack MIDI-CV (rotate/reuse/reset/mono match VCV's polyphony modes). UMP handling per the MMA/AMEI spec. Alternatives: slew for 7-bit CCs; full MPE (per-note CC74, zone-manager channel bend); 14-bit CC pairs (CC1/CC33); converter portamento.

### C2.13 essentials.notes_to_cv (native/modules2/notes_to_cv/dsp.h)
- **Alg:**
  - Wrapper around wirescape::voice::NoteToCv and its allocator (:3, :22; not in the pack).
  - Mode is always Rotate (:37). Voices = param clamped [1, max_channels] (:32-40).
  - NOTE_ON/OFF/CHOKE/EXPRESSION go to core.event with a no-op emit (:60-66). Comment: the allocator "handles releases and expressions internally; it does not emit here" (:63-64). Other events are ignored.
  - Outputs per voice, per sample (:46-59): pitch = v.pitch; gate = v.gate && !(v.trigger && v.retrigger), so a stolen or retriggered voice dips to 0 for one sample to retrigger an envelope (:52-54). DESIGN: "the established host.keyboard gate convention" (DESIGN.md:6). velocity = v.velocity.
  - clear_triggers() runs AFTER EVERY SAMPLE inside the sample loop (:57), so the dip is exactly 1 sample.
  - b.split (:46); (inf) events are sample-accurate.
- **AA/NL:** not applicable.
- **Params:**
  - voices 1–16 / 4, stepped, block-rate value(0,0) (:20, :33).
  - A change reconfigures the core (:34-40). DESIGN: "reconfigure/release the held allocator state" (DESIGN.md:6). (inf) Unlike midi_to_cv (midi_to_cv/dsp.h:74), there is no release_all before configure; whether configure releases depends on the core (not visible).
  - No bend, glide or smoothing in this file. NOTE_EXPRESSION reaches the core, but its effect on v.pitch is not visible.
  - NaN (inf): lround(NaN) unspecified, then clamped 1..max_channels.
- **Num:**
  - No recursive float state.
  - prepare stores only max_channels, no reset (:26). The first process always configures, since configured_voices starts at 0 (:24, :34). reset() resets the core and sets configured_voices = 0 (:27-30).
  - State: version word; load resets, "Active notes never persist" (:69-76; DESIGN.md:6).
- **Cost (inf):** per sample n × 3 writes + 1 clear_triggers (allocator cost not visible); per event 1 core.event; the module adds 8 B beyond the core.
- **Artefacts (inf):**
  - The 1-sample dip (20.8 µs @48k, 10.4 µs @96k) is missed by block-rate gate readers or consumers that need a minimum low time.
  - midi_to_cv writes v.gate with no dip (midi_to_cv/dsp.h:93) and clears triggers once per segment (:101), so the same note stream gives different gate shapes through the two converters.
  - Changing voices mid-performance stops held notes if configure releases them.
- **Ref (mk):** poly note-to-CV with a retrigger gate dip (VCV Rack MIDI-CV "retrigger"). Common alternative: a separate trigger output.

### C2.14 osc.out (native/modules2/osc_out/dsp.h)
- **Alg:**
  - Moves CV, gate edges and notes from the render thread to a sidecar that sends OSC. No outputs, no params (:21-22). DESIGN: never opens sockets, allocates, logs, waits or locks; the sidecar sends, orders gate edges, and stops/joins before graph retirement (#731) (DESIGN.md:6).
  - Inputs: 8 CV rows WS2_CV_BI, WS2_FIRST (:12-19) + Notes event input (:20).
  - out_configuration() parses setup.config into OutConfiguration (config.h, not in pack); prepare fails if parsing fails (:29-33). Uses the host-injected bus if present, else local_bus (:31).
  - Per enabled row, once per block (:37-61):
    1. value = LAST sample of the block (sample 0 if constant), atomic store, relaxed (:42, :57);
    2. gate rows (kind == 1): rise/fall counts at threshold ≥0.5, no hysteresis, added to monotonic atomic counters (:44-55, :58-59);
    3. blocks.fetch_add(1, release) publishes the update (:60).
  - Notes (:62-75): only NOTE_ON/OFF/CHOKE. Each goes into an SPSC ring as OutNote{int16 key, int16 channel, velocity or 0}. Producer owns note_head, consumer owns note_tail (acquire tail load, release head store, :65-74). Ring = 64 slots (DESIGN.md:6). Full ring: drop and bus->dropped++ (:67-70).
  - Events come from block.events() (:63), not events_in(port) as in chord and midi_to_cv.
  - DESIGN: patch JSON is parsed and validated off the render thread into a private binary config; unknown JSON keys stay in Studio's source patch and appear only as bounded diagnostics (DESIGN.md:8).
- **AA/NL (inf):** CV sampled once per block with no filter = decimation without anti-aliasing. Modulation above half the block rate aliases (e.g. 128-frame block @48k = 375 Hz block rate, so content above 187.5 Hz aliases). Sidecar send rate not visible.
- **Params:**
  - None. Row enable, gate vs value kind and notes enable come from the binary config (:38, :44, :62).
  - Only voice 0 per row ("FIRST poly policy: only voice 0", :39). Note events from all channels are forwarded.
  - NaN (inf): stored and passed on as-is; in gate counting, NaN ≥0.5 is false, so low.
- **Num:**
  - No recursive DSP state. Gate state persists across blocks (high[i], :45, :54).
  - (inf) head % size on a wrapping uint32 is correct only if the size divides 2³²; 64 does.
  - reset clears high only; comment: the consumer owns shared bus counters and ring tails (:34).
  - State: version word; load resets (:77-84).
- **Cost (inf):** per block per enabled row 1–3 atomics (gate rows add a compare-per-sample loop). Per note event: 2 atomic loads, 1 store, 1 slot write. OutBus = 8 rows of atomics + 64-slot ring (exact size not visible).
- **Artefacts (inf):**
  - The sidecar sees only the last CV value and the edge counts per block. Edge order is recoverable (rises and falls alternate) but sub-block timing is lost. A pulse shorter than a block still counts as 1 rise + 1 fall.
  - No hysteresis: a noisy signal near 0.5 inflates edge counts.
  - Bursts of >64 notes between consumer reads are dropped; a dropped NOTE_OFF sticks a note on the OSC receiver.
  - Note IDs are not forwarded (key and channel only), so overlapping same-key notes on one channel cannot be told apart. NOTE_EXPRESSION is not forwarded.
- **Ref (mk):** realtime → lock-free SPSC → network thread is the standard pattern. Alternatives: per-event timestamps (OSC bundle time tags); fixed-rate CV with filtering/decimation; note IDs in the OSC address or arguments.

### C2.15 Summary table
"Partial" = only some params or state. "n/a" = no audio-rate path or recursive state.

| Module | Algorithm | Smoothing | Anti-aliasing | Denormal guard | Double used |
|---|---|---|---|---|---|
| fx.delay | Stereo delay, Hermite read, one-pole LP/HP tone, DC blocker, tanh limiter, clock follower | Partial: time only (one-pole 50 ms + 0.5 slew cap); fb/tone/mix none | No (limiter not oversampled) | Partial (flush <1e-18 on tone LP and DC; lines not) | Yes (time/glide, coefficients, mix gains) |
| fx.reverb | 8-line FDN, Hadamard, 2×2 Schroeder allpasses, linear taps, one-pole damping, freeze, 2 LFOs | Partial: size/predelay 50 ms, freeze 20 ms; decay 64-sample steps; damping/width/motion/mix none | No | No | Partial (delay[8], exp, length scaling; rate float) |
| sound.spectral | Streaming STFT Hann/Hann 75%, latency N; PV morph, cross-synthesis, per-bin combine, interleave, FFT channel vocoder | Partial: per-hop controls spread by OLA; 4-frame mode crossfade; level none | n/a (no zero-padding, circular aliasing possible) | No (exact-zero silence clears state) | Yes (setup tables, vocoder coefficients) |
| sound.blend | Equal-power cos/sin crossfade + splice, raised-cosine glides, jittered segments | Partial: glide on every jump; balance not outside glides | n/a | n/a | Yes (rate, segment lengths) |
| essentials.mixer | 2-input gain-ramped mixer, 16 voices | Yes (PortRamp 5 ms per DESIGN + host D7) | n/a | n/a | Yes (per DESIGN) |
| essentials.output | Per-voice pass-through | n/a | n/a | n/a | No |
| essentials.quantizer | Nearest-note on 12-bit mask, ±0.1 st hysteresis, degree shift, 1 ms trigger | No (by design, block-rate settings) | n/a | n/a | Yes (semitone maths, output rounding) |
| essentials.scale_offset | Per-voice in·scale + offset | Yes (PortRamp + host D7) | n/a | n/a | Yes (per DESIGN) |
| essentials.clock | Phase-accumulator gate clock, 1e-12 duty epsilon | Partial: BPM only (5 ms ramp) | No (naive gate) | n/a | Yes (phase) |
| sequencing.groove | 2-track step sequencer, 512-tick counter, trig conditions, xorshift32 | No | n/a | n/a | Yes (phase, step length, gate age) |
| essentials.chord | Event harmonizer, root + 4 shifts, ID reservation | n/a | n/a | n/a | No |
| midi.to_cv | UMP MIDI 1/2 parser → shared allocator, per-channel controllers | No | n/a | n/a | Yes (MIDI 2 conversions) |
| essentials.notes_to_cv | Notes → shared allocator (Rotate), 1-sample retrigger dip | No | n/a | n/a | No (in this file) |
| osc.out | Block-rate CV snapshot, gate edge counters, 64-slot SPSC note ring | No | No (decimation to block rate) | n/a | No |

### C2.16 Open questions

#### Cross-cutting
1. Does the engine set FTZ/DAZ on the render thread on Pi 5 (AArch64) and Windows x64? Reverb has no denormal guard; delay flushes only tone and DC states, not its lines (delay/dsp.h:100, :139, :143). **[Answered for x64 and Pi 5: X1]**
2. Are the per-sample buffers of WS2_MODULATABLE params smoothed or interpolated by the host (D7), and with what time constant? Raw per-sample use: delay fb/tone/mix; reverb damping/width/mix; blend balance; spectral level. How does D7 combine with PortRamp's 5 ms in mixer, scale_offset and clock? **[Answered for the engine layer: X2]**
3. port_state.h is not in the pack. Does PortRamp share LinearRamp's behaviour (restart per target, NaN pass-through, signals.h:18-23)? **[Pending D]**
4. mixer, scale_offset and clock index voices[c] up to b.channels() unchecked (mixer/dsp.h:14, scale_offset/dsp.h:12, clock/dsp.h:12); quantizer clamps to 16 (quantizer/dsp.h:179). Is b.channels() ≤16 guaranteed? **[Answered (inf): X4]**
5. reverb, quantizer, chord, midi_to_cv and notes_to_cv do not call reset() from prepare(); delay, blend, clock, groove and spectral do. Does the host always call reset() after prepare(), and is WS2_LARGE memory zero-filled? Reverb's default gain[] = 0 and its buffers depend on it. **[Narrowed: X5; high priority for D]**
6. Are param values guaranteed finite and in declared range? quantizer and clock guard inputs. delay, reverb and spectral pass NaN params into recursive state, and delay's static_cast<int>(NaN) in read() is UB (delay/dsp.h:103).
7. Does the host pre-sum polyphonic signals for WS2_SUM inputs? delay sums all channels itself (delay/dsp.h:89-93). reverb, spectral and blend read only ch(0) despite WS2_SUM (reverb/dsp.h:187, spectral/dsp.h:135, blend/dsp.h:49). **[Answered: X3/R3]** engine2 pre-sums WS2_SUM inputs (A:871): reverb, spectral and blend receive the mono sum, and delay's own sum runs over one channel.
8. delay and reverb declare WS2_POLY outputs but always set_channels(1). What does WS2_POLY mean for these outputs?
9. groove returns WS2_INVALID for an unknown state version (groove/dsp.h:152); every other module returns WS2_UNSUPPORTED. Intended?
10. quantizer defines no save_state/load_state. Does the SDK provide defaults, and what do they write and accept? **[Narrowed: X12]**
11. Is b.param(i) indexed by array position or by the declared slot field? In midi_to_cv, sustain is declared with slot 6 and slot 5 is skipped (midi_to_cv/dsp.h:27), but it is read as b.param(5) (:76). **[Narrowed: X13]**
12. Gate conventions differ: notes_to_cv dips 1 sample on retrigger; midi_to_cv does not (midi_to_cv/dsp.h:93); groove's back-to-back full gates have no low sample (groove/dsp.h:329-336, :552). Is one convention intended?

#### fx.delay
13. lp[] is not updated while tone is bypassed (delay/dsp.h:138-142). Is the stale state on leaving bypass a known click source?
14. The first wet repeat is not DC-blocked and the output is not clamped. Does the <2 output bound (DESIGN.md:15-16) assume dry input within ±1?

#### fx.reverb
15. Damping = 1 makes the coefficient 0, so low[k] holds and recirculates (reverb/dsp.h:219). Intended at max damping?
16. DESIGN cites Jot's line-dependent damping (DESIGN.md:5-6), but the code uses one coefficient for all lines, not scaled with sample rate. Intended?
17. Large size changes glide faster than 1 sample/sample on the longest lines (brief backward read); delay caps slew at 0.5, reverb has no cap. Intended?
18. +2 on the prime allpass bases gives composite lengths (253, 399, 309, 451 @48k). Were prime lengths the intent?
19. Motion depth is fixed in samples (±1 per LFO), so its time depth halves at 96 kHz. Intended?
20. Has the ×6 wet makeup at Mix=1 against the ±2 hard clamp been reviewed for clipping?

#### sound.spectral
21. fft.h and approx.h are not in the pack. What is RealFft::floats(N), and what is the FFT cost on Pi 5? **[Pending D]**
22. How does the engine handle the latency change when size moves? "Engine re-query of latency_frames()" is listed as not done (DESIGN.md:57). **[Partly answered: X7]**
23. Has the per-hop burst been measured on the Pi at 96 kHz/N=8192 (DESIGN.md:58)?
24. Analysis frames are not zero-padded and per-bin gains reach 1e3. Was time-domain circular aliasing evaluated?
25. Cross smoothing width is in bins, so its width in Hz changes 8× across N=512…4096. Intended?
26. reset() clears rings A/B and OLA with one fill_n that relies on contiguity (spectral/dsp.h:115). Is that layout guaranteed to stay?

#### sound.blend / essentials.output
27. Splice never takes the constant fast path, even with silent inputs. Acceptable for CPU on Daisy-class targets?
28. output's DESIGN mentions "continuous controls" and ramps, but the module has no params; its input is WS2_SUM while DESIGN says it does not pre-sum (output/DESIGN.md:4, output/dsp.h:8). Which is accurate? **[Answered: X3]**

#### essentials.quantizer / essentials.clock
29. quantizer reads settings once per block, so results depend on block size; spectral, blend and groove are sample-accurate and block-size invariant. Intended?
30. The code says "exact for every allowed note" (quantizer/dsp.h:154); DESIGN says "correctly rounded" (DESIGN.md:7). Which guarantee is intended?
31. clock's ticks_per_beat and run are not stepped, and ticks is not clamped in the module; out-of-range CV can stop the clock or latch the gate high. Is 1–24 enforced elsewhere?
32. clock's reset uses a single 0.5 threshold with no hysteresis (unlike ws::Schmitt), and raising duty mid-cycle can give a second rising edge in one cycle. Both intended?

#### sequencing.groove
33. Do decode()/master_steps() guarantee div ≥1 and a non-zero master cycle, including for unused tracks and track_count = 0? step % div and step % master_steps() (groove/dsp.h:333-335, :357) are UB otherwise.
34. The external clock has no timeout and no interval averaging (unlike fx.delay's follower), so gates can stay high indefinitely when the clock stops. Intended?
35. The internal tempo is fixed at prepare from the pattern. How does a live tempo change reach the module?
36. A reset on the same sample as a clock pulse uses up that pulse, so step 0 plays one pulse late. Intended?

#### essentials.chord / midi.to_cv / notes_to_cv / osc.out
37. chord: no DESIGN.md in the pack; does one exist? Dropped chords are not counted. Tags masked to 11 bits (& 2047) alias every 2048 instances. Known?
38. midi_to_cv: steal_policy has range 0–0 and is never read; dropped/ignored are never exposed in this file. Is telemetry planned elsewhere?
39. notes_to_cv: does core.configure() release held voices when voices changes (midi_to_cv calls release_all first; notes_to_cv does not)? NOTE_EXPRESSION goes to the core, but there are no expression outputs; what does the core do with it?
40. osc.out:
    - It reads block.events() rather than events_in(8). Which ports' events does that return?
    - CV is sent at block rate with no filtering, and gate edges carry no timestamps. What send rate and timing accuracy does the OSC consumer expect?
    - Note IDs and NOTE_EXPRESSION are not forwarded, and notes beyond the 64-slot ring are dropped. Known limits?

---

## Part D — Module SDK: authoring flow and portability
Source: Wirescape snapshot 44da1e4, read by an LLM from source (no execution).

Context: fact pack for a later architecture review of Wirescape (C++17 realtime engine `wirescape-engine`, separate process, JSON lines over stdin/stdout, inside an Electron app with TypeScript UI "Studio"; targets Raspberry Pi 5 first, Windows x64 second; module DSP meant to stay portable to plugins and Daisy-class MCUs; ABI 2 = `module2.h`/engine2 current, ABI1 = `engine.h`/`module.h` older with leftovers).

**Conventions.** Line numbers are within each file (computed from the bundle's file offsets; off-by-one possible). Path codes: M2=`native/include/wirescape/module2.h`; SDK=`native/sdk/wirescape_sdk.h`; SIG=`native/sdk/signals.h`; FM=`native/sdk/fastmath.h`; SIMD=`native/sdk/simd.h`; TPL=`native/sdk/template/`; VCA=`native/modules2/vca/`; SEQ=`native/sdk/examples/step_sequencer/`; SAG=`docs/SDK_AUTHOR_GUIDE.md`; SPEC=`docs/specs/ABI2_SPEC.md`. Labels: (inf)=inferred; (mk)=from model knowledge, unverified (no internet, may be outdated); (NV)=file named in code/docs but not provided.

---
### D1. What a module is

#### D1.1 Author files
| File | Content | Source |
|---|---|---|
| `dsp.h` | the module class ("all the code") | SAG:26 |
| `module.cpp` | SPDX, `#include "dsp.h"`, `WS_REGISTER_MODULE(Class)` | SAG:27; VCA/module.cpp:1-3 |
| `module.json` | metadata "the host and patch migration read" | SAG:28 |
| `tests.cpp` | callback-level tests (CTest) | SAG:29 |
| `README.md` | ports, params, units | SAG:30 |
| `DESIGN.md` | design notes, provenance, pinned third-party revisions + licences; required "always" | SAG:31 |
| `LICENSE` | only if differs from folder default | SAG:32 |

- SPDX header on every file except `module.json`: `GPL-3.0-only` for Essentials/app code, `MIT` for SDK examples (SAG:34).
- Template deviates: class lives in TPL/module.cpp:3-21; no `dsp.h` or `DESIGN.md` for TPL in the bundle.
- `module.json` (SAG:35; TPL/module.json:1; VCA/module.json:1-17): `schema_version` 2, `abi_version` 2, `id` (e.g. `"essentials.vca"`), `name`, `library` (CMake target, prefix `ws2_`, e.g. `"ws2_vca"`), `parameters` = param ID → **slot index** (order in `params`, not a default), `inputs`/`outputs` = port ID → `"signal"`|`"event"`, optional `description`, `license` (SEQ/module.json:7,70). Duplicates descriptor info (IDs, kinds, param order); no generator or consistency check in provided files; "slot indices match `params` order" is a manual DoD item (SAG:169).

#### D1.2 C ABI descriptor `ws2_descriptor` (M2:94-108; wrapper fill SDK:253-258)
| Field | Type | Filled from |
|---|---|---|
| `struct_size` | u32 | `sizeof(ws2_descriptor)` |
| `abi_version` | u32 | `WS_ABI2_VERSION` = `2u` (M2:16) |
| `id`, `name` | `const char*` | `T::info.id/.name` |
| `version` | u32 | `T::info.version` |
| `input_count/output_count/param_count` | u32 | `T::inputs.size()` etc. |
| `inputs`,`outputs` / `params` | `const ws2_port*` / `const ws2_param*` | `.data()` |
| `create` | `void*(const ws2_host*)` | wrapper `create` |
| `destroy` | `void(void*)` | `destroy` |
| `query_ports` | `int(void*,const ws2_config*,ws2_ports*)` | `query` |
| `memory_requirements` | `int(const ws2_config*,ws2_memory*)` | `memory` |
| `prepare` | `int(void*,const ws2_config*,const ws2_host*)` | `prepare` |
| `reset` | `void(void*)` | `reset` |
| `process` | `int(void*,ws2_process*)` | `process` |
| `save_state`/`load_state` | `int(void*,const ws2_writer*)` / `int(void*,const ws2_reader*)` | `save`/`load` |
| `latency_frames` | `uint32_t(void*)` | `latency` |
All function pointers `WS2_CALL` (M2:98-107).

#### D1.3 C++ class shape
| Member | Req? | Signature | Source |
|---|---|---|---|
| `info` | yes | `static constexpr ws::Info` = `{const char *id,*name; uint32_t version;}` | SDK:16; SAG:196 |
| `inputs`,`outputs` | yes | `static constexpr std::array<ws2_port,N>` (empty: `std::array<ws2_port,0>`) | SAG:196 |
| `params` | yes | `static constexpr std::array<ws2_param,N>` | SAG:196 |
| `prepare` | yes | `void` or `bool prepare(const ws::Setup&)`; `false`→`WS2_INVALID` | SDK:203-204 |
| `reset` | yes | `void reset()` | SDK:205,207 |
| `process` | yes | `void process(ws::Block&)` | SDK:233 |
| `memory_requirements` | opt | `static ws2_memory memory_requirements(const ws2_config&)` (trait `HasMemory`) | SDK:156-157,188 |
| `save_state`/`load_state` | opt, both or neither | `int save_state(ws::Writer)` / `int load_state(ws::Reader)`; absent → `WS2_UNSUPPORTED` | SDK:154-155,241-250 |
| `latency_frames` | opt | `uint32_t latency_frames()`, default 0 | SDK:158-159,251 |
| `query_ports` | opt | `int query_ports(const ws2_config&, ws2_ports&)` (config-dependent ports) | SDK:152-153,181 |
Wrapper stores `struct Instance {T dsp; ws2_config config{}; uint32_t inputs=0,outputs=0;}` (SDK:162), constructed via placement-new in host-allocated memory (SDK:170-176).

#### D1.4 Ports `ws2_port` (M2:37-40; helper `ws::port` SDK:17-20)
| Field | Type | Helper default | Values |
|---|---|---|---|
| `struct_size` | u32 | `sizeof(ws2_port)` | |
| `id`,`name` | `const char*` | required | |
| `kind` | u32 | `WS2_SIGNAL` | `SIGNAL=1`, `EVENT=2` (M2:23) |
| `hint` | u32 | `WS2_ANY` | `ANY,AUDIO,PITCH,CV_BI,CV_UNI,GATE,TRIGGER,EV_NOTES,EV_MIDI,EV_MESSAGE` (M2:24) |
| `poly` | u32 | `WS2_POLY` | `POLY,SUM,FIRST` (M2:25) |
| `stereo_pair` | `const char*` | `nullptr` | partner port ID |
| `unpatched_value` | float | `0` | value read when unconnected |
Hints "never block a connection" (SAG:54). Event outputs count as output port indices; their channel count set to 0 (SAG:127; SEQ/dsp.h:138).

#### D1.5 Params `ws2_param` (M2:41-46; helper `ws::param` SDK:21-25)
| Field | Type | Helper default |
|---|---|---|
| `struct_size` | u32 | `sizeof(ws2_param)` |
| `id`,`name`,`unit` | `const char*` | `unit=""` |
| `minimum`,`maximum`,`initial` | float | required |
| `legacy_index` | u32 | `0` |
| `taper` | u32 | `WS2_LINEAR` (`LINEAR,LOG,EXP`, M2:28) |
| `curve` / `step` | float | `4` / `0` |
| `flags` | u32 | `WS2_MODULATABLE\|WS2_AUTOMATABLE` |
| `option_count`,`options` | u32, `const char* const*` | hard-coded `0`,`nullptr` |
| `decimals` | u32 | hard-coded `3` |
| `value_to_text` | `int(WS2_CALL*)(float,char*,uint32_t)` | hard-coded `nullptr` |
- Helper has no args for `options`/`decimals`/`value_to_text` (SDK:24); SEQ edits `.initial` after construction inside a constexpr lambda (SEQ/dsp.h:54).
- Flags (M2:27): `MODULATABLE=1, PER_VOICE=2, AUDIO_RATE_OK=4, STEPPED=8, AUTOMATABLE=16, HIDDEN=32`.
- `prepare` validation (SDK:192-198): non-null `id`; finite min/max/initial/curve/step; `max≥min`; `initial` in range; `step≥0`; `taper≤WS2_EXP`; LOG needs `min>0`.
- `process` receives each param as a `ws2_signal` in plain units, already smoothed+modulated (SAG:123; SPEC:29).

#### D1.6 Signals, events, state, per-voice
| Concept | Type | Source |
|---|---|---|
| Input/param signal | `ws2_signal {u32 struct_size; const float *const *data; u32 channels, flags;}`; flags `CONSTANT=1, CONNECTED=2` | M2:35,26 |
| Output | `ws2_signal_out {…; float *const *data; u32 channels, flags, max_channels;}` | M2:36 |
| C++ views | `ws::Signal` (channels/constant/connected/ch/value/row), `ws::Output` (set_channels/mark_constant/ch/channels), `ws::Channel` | SDK:71-101 |
| Event | `ws2_event {u32 struct_size,type,offset,port,flags; i32 note_id,channel,key; u32 source_id,index; float value,value2; u32 expression,message_kind,bytes; const uint8_t *data; u32 ump[4],ump_words;}` | M2:49-54 |
| Event types | `NOTE_ON=1,NOTE_OFF,NOTE_CHOKE,NOTE_EXPRESSION,PARAM,PARAM_MOD,TRANSPORT_EVENT,MIDI,MESSAGE` | M2:30 |
| Read events | `b.events()`, `b.events_in(port)`, `b.split(range_fn,event_fn)` | SDK:121-122,128-132 |
| Write events | `bool b.emit(port,const ws2_event&)`; false if host `push`≠`WS2_OK` | SDK:123-126 |
| State | `ws::Writer` (`bytes`, `value<T>` trivially copyable, `u32`, `f32`; u32 little-endian byte-by-byte); `ws::Reader` mirrors | SDK:134-151 |
| Transport | `ws2_transport` (double `bpm,beat,bar_start,loop_start,loop_end`; u32 `ts_num,ts_den,flags`); `b.transport()` may be null | M2:60-63; SAG:132 |
| Per-voice | no per-voice ABI struct; channels 1..16 = voices (`WS2_MAX_CHANNELS 16u`, M2:17); guide: fixed `std::array<Voice,16>` (SAG:68); `ch(c)` maps any c→0 for 1-channel signal (SDK:84); `WS2_PER_VOICE` enables per-channel param signals (SPEC:91) | |
| Memory | `ws2_memory {u32 struct_size; size_t fast_bytes,large_bytes,alignment;}`; wrapper adds `sizeof(Instance)` to `fast_bytes`, alignment 32 | M2:73; SDK:187-188 |
| Setup | `ws::Setup`: `sample_rate()`, `max_channels()`, `max_block()`, `alloc(bytes, alignment=32, hint=WS2_FAST)` | SDK:62-70 |
ABI limits (M2:16-21): `WS_ABI2_VERSION 2u`, `WS2_MAX_CHANNELS 16u`, `WS2_MAX_PORTS 32u`, `WS2_MAX_PARAMS 64u` ("raised from 32 (additive, #402)"), `WS2_MAX_PAYLOAD 1472u`, `WS2_DIRECT_PORT UINT32_MAX`.

#### D1.7 Line counts (split is (inf): boilerplate = SPDX/includes, braces, info/ports/params decls, empty reset, signatures, registration; plumbing = scratch, memory_requirements, prepare, channel count, CONSTANT, channel loop, row/value fetch; arithmetic = sample computation)
| File | Total | Boilerplate | Plumbing | Arithmetic |
|---|---|---|---|---|
| TPL/module.cpp (class+registration) | 22 | 13 (1–7,11,12,19–22) | 8 (8–10,13–17) | 1 (18: `out=audio*gain`) |
| VCA/dsp.h | 34 | 15 (1–9,13,14,31–34) | 14 (10–12,15–22,26–28) | 5 (23–25,29–30: f4 broadcast, f4 loops, scalar tails) |
| VCA/module.cpp | 3 | 3 | – | – |
| VCA/module.json | 17 | 17 | – | – |
| TPL/module.json | 1 | 1 | – | – |
| TPL/tests.cpp | 21 | – | – | – |
Scale: SEQ/dsp.h 227 lines; SEQ/module.json 71 lines.

---
### D2. Authoring flow
REPO = needs this repository; OOT = works out of tree with only `module2.h` + `native/sdk/` headers; ? = not settled by provided files.
| # | Step | Detail | Source | Repo/OOT |
|---|---|---|---|---|
| 0 | Read checklist | `MODULE_BUILD_GUIDE.md` (NV): "owner request → builder steps → the five registration edits → review"; the five edits not listed in provided files | SAG:4 | REPO (doc) |
| 1 | Copy example | TPL (processor); `native/sdk/examples/random_source/` (source, NV); SEQ (notes) | SAG:10-14 | TPL OOT; example tests need repo helpers (step 7) |
| 2 | Folder | `native/modules2/<name>/` or `native/sdk/examples/<name>/` for MIT examples | SAG:25 | path convention REPO; files OOT |
| 3 | IDs | module ID `<prefix>.<name>`, independent of CMake `ws2_<name>`; short lowercase port/param IDs; never rename/reuse after merge; retire with `WS2_HIDDEN`; bump `Info.version` on behaviour change | SAG:38-42 | OOT |
| 4 | `dsp.h` | table 1.3; includes only `"wirescape_sdk.h"` | VCA/dsp.h:3; SAG:196 | OOT; SDK header-only (inf: SDK:3-13 includes only module2.h, signals.h, simd.h, fastmath.h + std headers) |
| 5 | `module.cpp` | `WS_REGISTER_MODULE` → two `extern "C" WS2_EXPORT` fns: `ws_module2_abi_version()`→2, `ws_module2_entry()`→descriptor; names overridable via `WS_MODULE2_VERSION_NAME`/`WS_MODULE2_ENTRY_NAME` | SDK:261-263; M2:110-117; SPEC:89 ("may be overridden for static linking") | OOT |
| 6 | `module.json` | §1.1; slot indices; `library` = CMake target | SAG:35 | writing OOT; host reader REPO/? |
| 7 | `tests.cpp` | calls C callbacks via `ws::Module<Class>::descriptor()`; examples include `../test_support.h`, `../../../tests2/allocation_watch.h`, link `native/tests2/allocation_watch.cpp`; TPL test standalone ("compile this file alone"; fixed 8192-byte pool) | SAG:146; SEQ/tests.cpp:5-7; TPL/tests.cpp:2,7 | TPL-style OOT; test_support/allocation_watch REPO |
| 7a | Test matrix | 1) frame matrix 1/17/64/256 bit-identical vs one block; 2) 44.1/48/96 kHz; 3) channels 1/4/16 (single-channel FIRST-input modules use a "reads channel 0 only" test instead); 4) reset determinism; 5) state round trip + reject unknown/truncated; 6) CONSTANT; 7) extremes; 8) no allocation in process; 9) behaviour | SAG:147-155 | item 8 REPO; rest OOT (inf) |
| 7a' | SEQ test coverage (verified) | `test_matrices`, `test_sixteen_block_matrix_and_length_edits` (§3.5); `test_state` (round trip between notes bit-identical; mid-note load emits NOTE_OFF at resume frame then same NOTE_ONs; `reset()` repeats run exactly; version byte 9→`WS2_UNSUPPORTED`; truncated, empty, step byte=17, corrupted velocity→`WS2_INVALID`; instance state unchanged after bad loads); `test_v1_v2_state_migration` (v2 header byte=2; v1 header with position ≥8 → `WS2_INVALID`); `test_capacity_full` (host accepts 1 event/block; refused NOTE_OFF delivered at start of later block; notes balance); `test_reset_wins_and_release`; `test_run_switch`; `test_no_allocation` (body not seen) | SEQ/tests.cpp, named fns | — |
| 7b | Banned includes | under `native/sdk/`: `<vector> <string> <thread> <mutex> <iostream> <filesystem> <map> <unordered_map> <list> <deque> <functional> <sstream> <fstream> <chrono>` (check `abi2_banned_includes`); `native/modules2/*/tests.cpp` exempt | SAG:146 | REPO |
| 8 | CMake | `ws2_<name>` SHARED lib + `abi2_<name>_tests` exe + `add_test` in `native/engine2/CMakeLists.txt`; elsewhere "the appropriate CMake file"; MIDI test wired in `native/io/midi/CMakeLists.txt` | SAG:36,166 | REPO (NV) |
| 9 | Build/test | `python tools/dev.py build --headless`; `python tools/dev.py test`; `ctest --test-dir build/native -R '^abi2_<name>_tests$'` | SAG:162-163,172 | REPO (`tools/dev.py` NV) |
| 10 | RT self-review | no alloc/locks/I/O/exceptions/unbounded loops; block-size independence; finite outputs; seeded randomness; no OS intrinsics | SAG:95-103 | OOT |
| 11 | App catalogue | `WS_APP_MODULE(Class)` in `native/control/module_catalog.inc`, DSP header included by `module_catalog.h` | SAG:173 | REPO (NV); (inf) compiles class into app/engine from header, separate from step-8 SHARED lib |
| 12 | "Plays in a patch" | DoD item; no mechanism beyond step 11 + `docs/ARCHITECTURE.md` (NV) | SAG:173 | REPO/? |
| 13 | Pi evidence (heavy modules) | `pi-run:` line in issue, PR label `ci/pi-accept`, status `pi5/accept`; worst block <50% period at 48 kHz/128 frames, two instances | SAG:174,177,230 | REPO (private bridge) |
| 14 | Docs | README (IDs, units, ranges); DESIGN (provenance, licences) | SAG:170,175 | OOT |
Not shown in provided files: the five registration edits; any generated catalogue; TypeScript/Studio UI catalogue files; contents of `module_catalog.inc/.h`; how host turns `module.json` + `library` into a loaded module. Static list (step 11) vs dynamic loading (step 8) unconfirmed (§4.6).

---
### D3. Portability

#### D3.1 Per file
| File | Heap | Exceptions | RTTI | `double` | std containers / headers | OS/platform | SIMD | Large tables | Threading |
|---|---|---|---|---|---|---|---|---|---|
| M2 | none | none | none | in ABI structs (§3.2) | only `<stdint.h>`,`<stddef.h>` (M2:4-5) | `__declspec(dllexport)`/`__cdecl` on `_WIN32`, else `__attribute__((visibility("default")))` (M2:6-12) | none | none | none |
| SDK | none own; placement-new into host memory (SDK:170-176) | `try/catch(...)` only if `__cpp_exceptions`/`_CPPUNWIND`, else direct call (SDK:163-169) | none found (no typeid/dynamic_cast) (inf) | `to_plain`/`to_normal` (SDK:26-42), `Setup::sample_rate()` (:64), `Block::sample_rate()` (:116) | `std::array` (no heap); includes `<algorithm> <cmath> <cstring> <new> <type_traits> <utility>` (:7-13) | none | includes simd.h (:5) | none | function-local `static const` in `descriptor()` (:254), §3.4 |
| SIG | none | none | none | `LinearRamp` state all double (SIG:10); `Trigger::prepare` `std::ceil(rate*.001)` (:41) | none | none | none | none | none |
| FM | none | none | none | `tan_small` polynomial in double (FM:7-8) | none | none | none | none | none |
| SIMD | none | none | none | none | none | `<emmintrin.h>` if `__SSE2__`/`_M_X64` (SIMD:3-5); `<arm_neon.h>` if `__ARM_NEON` (:6-8) | `f4`: SSE2 / NEON / scalar `float v[4]` (:30-38); `WS_SIMD_SCALAR` forces scalar | none | none |
| VCA/dsp.h | none; scratch via `s.alloc` (VCA/dsp.h:13) | none | none | none | `std::array` descriptors | none | `ws::simd::f4` (:23-24,:29) | none | none |
| SEQ/dsp.h | none (`prepare` empty, SEQ/dsp.h:76) | none | none | none | `std::array` descriptors | none | none | 50 `ws2_param` (§3.3) | none |
| TPL/module.cpp | none; scratch via `s.alloc` (TPL/module.cpp:10) | none | none | none | `std::array` | none | none | none | none |
Outside DSP: TPL/tests.cpp uses `<cstdio>`,`<cstdlib>`, `fprintf`, `abort`; SEQ tests use `std::make_unique` because "Windows gives a test only a 1 MB stack" (SEQ/tests.cpp:56-58). Banned-include list as §2 step 7b (SAG:146).

#### D3.2 double / 64-bit / size_t in ABI
| Struct | Fields |
|---|---|
| `ws2_config` | `double sample_rate`, `uint64_t seed` (M2:68-70) |
| `ws2_process` | `uint64_t frame_position, generation`, `double sample_rate` (M2:88) |
| `ws2_transport` | `double bpm, beat, bar_start, loop_start, loop_end` (M2:61-62) |
| `ws2_memory` | `size_t fast_bytes, large_bytes, alignment` (M2:73) → size differs 32/64-bit (inf) |
| `ws2_host::alloc` | `void*(void*, size_t bytes, size_t align, uint32_t hint)` (M2:66) |
Docs: "float32 is the default. A module using double state MUST document why" (SPEC:77); "keep `double` only where precision needs it" (SAG:200); SIG:7-8: LinearRamp doubles keep "the ABI1 accumulator precision". (mk) Daisy Seed STM32H750 (Cortex-M7) has a double-precision FPU (slower than float); other Cortex-M4F parts are single-precision only.

#### D3.3 Memory sizes
| Item | Size | Source |
|---|---|---|
| TPL scratch | `2*sizeof(float)*max_block_frames`, align 32 | TPL/module.cpp:9-10 |
| VCA scratch | `3*sizeof(float)*max_block_frames`, align 32 | VCA/dsp.h:12-13 |
| Wrapper overhead | `sizeof(Instance)` (T + ws2_config + 2×u32) added to fast_bytes | SDK:162,187 |
| Default alloc alignment | 32 | SDK:67 |
| TPL test pool | 8192 bytes, `alignas(64)` | TPL/tests.cpp:7 |
| Host caps | 128 MiB/FAST-or-LARGE request, 64 allocations/node, default arena 1472 KiB, state blob 1 MiB | SPEC:91 |
VCA scratch (inf arithmetic): 48 frames→576 B; 128→1,536 B; 256→3,072 B; 4096 (engine max)→49,152 B. SEQ object (inf, members SEQ/dsp.h:62-74): `Note` 12 B, whole ≈48 B. Param tables (inf layout): `ws2_param` ≈96 B LP64 / ≈64 B 32-bit ARM → SEQ's 50 ≈4.8 KB / 3.2 KB plus ID/name strings built by `WS_STEP` via `#n` (SEQ/dsp.h:14-17).

#### D3.4 Other bare-metal-relevant C++
| Feature | Where | Note |
|---|---|---|
| Function-local static | `Module<T>::descriptor()` (SDK:254) | (mk) without constant-init, compiler emits thread-safe guard (`__cxa_guard_*`); embedded builds often use `-fno-threadsafe-statics` |
| C++17 | `if constexpr`, `std::void_t`, CTAD on `std::array` (TPL/module.cpp:5-7), constexpr lambda building `params` (SEQ/dsp.h:34-56) | (mk) arm-none-eabi GCC supports C++17 |
| `<cmath>` | `std::exp/log/expm1/log1p/round` (SDK:26-42); `std::isfinite` (:47,:52,:193); `std::lround` (SEQ/dsp.h:118,130,133) | pulls in libm |
| Output check | every output sample (or sample 0 if CONSTANT) scanned after each process (SDK:235-238) | every block, every target |
| Call conv/export | `WS2_CALL`/`WS2_EXPORT` (M2:6-12) | (mk) `__cdecl` no effect on x64 Windows |
| `#undef emit` | SEQ/dsp.h:5-8 (Qt/cppcheck) | header hygiene |

#### D3.5 Sample-rate / block-size assumptions
| Assumption | Value/rule | Source |
|---|---|---|
| Accepted rate | finite, ≥1, ≤384000 else `WS2_INVALID` | SDK:193 |
| Rate fixed after prepare | `process` requires `ctx.sample_rate == config.sample_rate` (exact double `!=`) | SDK:216 |
| Block size | `1 ≤ frames ≤ max_block_frames`; `frames==0` → no-op `WS2_OK` | SDK:211,214 |
| Engine block range | 1–4096 prepared frames | SPEC:91 |
| Block independence | "any `frames` from 1 to `max_block()` must give the same result as one big block" | SAG:100 |
| Channels | `1 ≤ channels ≤ max_channels ≤ 16`; each output `max_channels` == configured | SDK:194,214,220 |
| `LinearRamp` | 5 ms: `max(1, rate*.005)`; pre-prepare default 240 frames (5 ms@48k) | SIG:11,15 |
| `Trigger` | 1 ms: `max(1, ceil(rate*.001))`; pre-prepare default 48 frames | SIG:39,41 |
| VCA/TPL | no time constants → no rate dependency (inf) | VCA/dsp.h:15-32 |
| SEQ (verified) | no time constants. `test_matrices`: one 1000-frame block vs blocks 1/17/64/256 → bit-identical trace; 44.1/48/96 kHz at 128-frame blocks → identical events ("control is frame-based"). `test_sixteen_block_matrix_and_length_edits`: one 640-frame block vs 1/17/128/256 identical; same three rates identical events at 128 | SEQ/tests.cpp, named fns |
| Reference workload | Pi, 48 kHz, 128 frames; bound half period (<1,333 µs) | SAG:179 |
SPEC:77: "NEON/ARM compilation is unverified on this machine".

---
### D4. ABI contract

#### D4.1 Versioning (five numbers)
| Version | Where | Value |
|---|---|---|
| ABI macro | `WS_ABI2_VERSION` (M2:16) | `2u` |
| ABI exported | `ws_module2_abi_version()` (SDK:262), `descriptor.abi_version` (:254) | 2 |
| Module behaviour | `ws::Info::version` → `descriptor.version`; bump on behaviour change, ID stays (SAG:42) | VCA 2 (VCA/dsp.h:7); TPL 1; SEQ 2 |
| Manifest | `module.json` `schema_version`, `abi_version` | 2, 2 |
| Module state | first u32 written by module; SEQ writes 2, accepts 1 or 2, else `WS2_UNSUPPORTED` (SEQ/dsp.h:192,202-203); v1 only positions 0–7 (SEQ/dsp.h:208-209; test_v1_v2_state_migration) | per module |
ABI1 and ABI2 binaries "are not interchangeable" (SPEC:85). SDK wrapper never checks a host ABI version (inf: none in SDK).

#### D4.2 struct_size checks
Rule (SPEC:89): every struct begins with `struct_size`; "Accepted size is at least the current structure size; future trailing fields are ignored, not inferred."
Checked (`size ≥ sizeof`): `ws2_host` (create :171; prepare :192); `ws2_config` (query :179; memory :186; prepare :192); `ws2_ports` (query :179); `ws2_memory` (memory :186); `ws2_param` own table (prepare :195); `ws2_process` (process :209); `ws2_signal` inputs/params (:224); `ws2_signal_out` (process :220; silence_outputs :57); `ws2_event_list` only if count>0 (:230); `ws2_event` via `valid_event` (:51); `ws2_writer`/`ws2_reader` (save :242; load :247).
Not checked (inf): `ws2_port`; `ws2_event_out` before `push` (Block::emit :123-126); `ws2_transport` (Block::transport :127). `ws2_descriptor`: set by wrapper (:254). Host side: engine2 `add_node` requires struct_size ≥ sizeof(ws2_descriptor), abi_version == 2, all 10 function pointers and counts within limits (A:1022-1024) [R10][X17].

#### D4.3 Additive / compatible changes
- `WS2_MAX_PARAMS` 32→64 "additive, #402; hosts reject descriptors above it" (M2:19); "a module above 32 fails cleanly on older hosts" (SAG:201); SEQ comments cite #404 for same change (SEQ/dsp.h:33; SEQ/README.md:28).
- `Random::save()/restore()` "Additive state accessor" (SIG:58-62).
- Promise: "additive SDK changes only; a breaking change needs a migration note" (SAG:203).
- Planned additive fixes "after J9": `Schmitt::high()`, stepped-param helper, 64-bit Writer/Reader helpers, Reader remaining-bytes, events from `reset()` (SAG:202).
- ID rule: append new ports/params at end; retire via `WS2_HIDDEN`; never rename/renumber/reuse (SAG:41).
- SEQ: "Original slots 0–25 are unchanged"; state v2 reads v1 (SEQ/README.md:28-29; dsp.h:208-209).
- `ws2_reader.bytes` exists (M2:85) but `ws::Reader` doesn't expose it (SDK:143-151) = the "can't report remaining bytes" gap.

#### D4.4 legacy_index and historical items
| Item | Fact | Source |
|---|---|---|
| `legacy_index` | u32, helper default 0 | M2:43; SDK:23-24 |
| Meaning | "keeps ABI 1 meaning for ported modules"; spec "Numeric legacy indices MAY be retained for migration" | SAG:194; SPEC:29 |
| SEQ values | run=0, length=1, pitchN=3n−1, gateN=3n, velN=3n+1 (n=1..16) = its module.json slot indices (inf arithmetic) | SEQ/dsp.h:14-17,36-37; module.json:9-58 |
| VCA gain | legacy_index 0 (default), slot 0 | VCA/dsp.h:10; module.json:7-9 |
| Wrapper use | none (inf: not read in SDK). Host use: AppEngine builds ABI1-style metadata IDs from it, and the v2 parameter-initialization path goes through them (A:1674, A:1758, A:2033) [X15] | |
| LinearRamp double | "retain the ABI1 accumulator precision" | SIG:7-8 |
| ABI1 shim | "engine2 validates ABI 1 shim outputs once" | SPEC:73 |
| Namespace `ws2ports` | used by VCA (GPL port of existing module) | VCA/dsp.h:4 |
| SEQ `length` default 8 | "legacy-safe"; patches without `length` keep 8 steps | SEQ/README.md:23,29 |
| Patch format | `native/document` loads v1/v2, saves v2, keeps `<name>.v1.json` backup; v1 objects kept under `preserved` | SPEC:95 |

#### D4.5 Calling conventions / symbols
- `extern "C"` around whole header (M2:13-15,118-120). `WS2_CALL` = `__cdecl` on `_WIN32`, empty elsewhere; `WS2_EXPORT` = `__declspec(dllexport)` / `visibility("default")` (M2:6-12).
- Entry points: `uint32_t ws_module2_abi_version(void)`, `const ws2_descriptor* ws_module2_entry(void)` (M2:110-117); overridable via macros, "may be overridden for static linking" (M2:110,114; SPEC:89). `typedef const ws2_descriptor *(WS2_CALL *ws2_entry_fn)(void)` (M2:109).
- Results: `WS2_OK=0, INVALID=1, CAPACITY=2, UNSUPPORTED=3, EXCEPTION=4, STATE=5` (M2:22).
- Exception barrier `guarded()` maps any exception to `WS2_EXCEPTION`; process then silences outputs (SDK:163-169,233-234). "native plugins are trusted code, not isolated processes" (SPEC:89).

#### D4.6 Host discovery
| Mechanism | Evidence | Status |
|---|---|---|
| Shared lib per module | SHARED `ws2_<name>` (SAG:36); `module.json` `library`; exported entry symbols; `ws2_entry_fn` | No ABI2 library loader in packs A–D; the product uses the compiled-in list [R10][X16] |
| Compiled-in list | `WS_APP_MODULE(Class)` in `native/control/module_catalog.inc`, header via `module_catalog.h` (SAG:173) | Confirmed in pack A: `builtin_modules()` is an X-macro over `module_catalog.inc` and feeds the AppEngine catalogue (A:1662, A:1921-1925) [R10][X16] |
| Static linking of several modules | symbol-name override macros (M2:110-117) | (inf) without overrides, two modules in one binary both define `ws_module2_entry` |
| Tests | `ws::Module<T>::descriptor()` direct, no loader (TPL/tests.cpp:10; SEQ/tests.cpp `Rig`) | present |

---
### D5. Comparison (mk — everything except the Wirescape row/column)

#### D5.1 Declarations
| Framework | Unit | Params | Ports | Polyphony | State | Discovery | Minimal VCA (≈lines) |
|---|---|---|---|---|---|---|---|
| Wirescape ABI2 | C++ struct + `WS_REGISTER_MODULE` → C descriptor | `static constexpr std::array` of `ws2_param` (range, taper, flags, step) | `std::array` of `ws2_port` (kind, hint, poly, unpatched, stereo pair) | 1–16 channels = voices; per-input POLY/SUM/FIRST; PER_VOICE params | optional save/load byte stream; host saves params | exported C entry and/or compiled-in catalogue | 22 (TPL); 34 VCA dsp.h + 3 module.cpp + module.json |
| VCV Rack 2 | `struct X : Module` + separate `ModuleWidget` + `Model` | `configParam(id,min,max,default,label,unit)` in ctor; enum IDs | `configInput/configOutput`; enum IDs; lights | ≤16 ch/cable; `getChannels`, `setChannels`, `getPolyVoltage(c)` | `dataToJson/dataFromJson` (jansson); Rack saves params | `plugin.json` + shared lib `init(Plugin*)` | 30–60 incl. widget + plugin.cpp |
| CLAP | C ABI: `clap_entry` → factory → `clap_plugin` + extensions | `clap_plugin_params` (count, get_info, get_value, flush); per-note-ID/key/channel mod flags | `audio-ports`, `note-ports` extensions | note IDs + (port,channel,key); poly mod events | `clap_plugin_state` streams | shared lib exporting `clap_entry`; host scans folders | few hundred plain C; fewer with helpers |
| DaisySP | plain C++ classes (`Init(sr)`, `Process()`); app uses libDaisy audio callback | none (app maps knobs) | none (callback buffers) | none (app voice arrays) | none | compiled into firmware | few lines in callback; 20–30 whole `main` |
| Faust | DSP language → C++ class (`init`,`compute`,`buildUserInterface`,`metadata`) | `hslider`,`nentry`,`button` + metadata | implicit signal arity | architecture polyphony (`[nvoices:n]`, freq/gain/gate) | param values via architecture | generated per target (architectures for Rack, Daisy, plugins) | 1: `process = *(hslider("gain",1,0,2,0.01));` |
| Pd external | C: `class_new`, new/free, `dsp` adds `perform` | float inlets/messages | `inlet_new/outlet_new`; `CLASS_MAINSIGNALIN` | none per object (`clone`; multichannel in recent Pd) | none (creation args) | shared lib `<name>_setup()` | 30–50 |

#### D5.2 Concept map (Wirescape → Rack | CLAP | DaisySP | Faust | Pd)
| Wirescape (source) | VCV Rack | CLAP | DaisySP | Faust | Pd |
|---|---|---|---|---|---|
| `ws::Info` id/name/version (SDK:16) | plugin.json slug + Model slug; version | `clap_plugin_descriptor` | – | `declare name` | class name |
| SIGNAL port (M2:37-40) | Input/Output | audio port (multichannel bus) | callback buffers | signal arity | signal inlet/outlet |
| EVENT port + `ws2_event` (M2:49-54) | none native (MIDI via core) | note ports + `clap_event_*` (on/off/choke/expression, param, MIDI) | – (libDaisy MIDI separate) | MIDI via metadata/architecture | messages |
| Hints (M2:24) | configInput labels; voltage convention | port type strings / note dialects | – | metadata | – |
| Param taper/step/flags (M2:41-46) | `ParamQuantity` (display base/multiplier, snap) | `clap_param_info` flags (stepped, modulatable, automatable, hidden…) | – | slider step, `[scale:log]` | – |
| Host smoothing+modulation, params as signals (SPEC:29,35) | module reads knob+CV itself | host sends PARAM_VALUE/PARAM_MOD; plugin smooths | app | `si.smoo` | module |
| Channels = voices, 16 max (M2:17) | same, 16 | voices via note ID | – | voice instances | – |
| POLY/SUM/FIRST (M2:25) | module decides | – | – | – | – |
| `WS2_CONSTANT` (M2:26) | – | `constant_mask` | – | – | – (scalar inlet) |
| `unpatched_value` (M2:39) | `getNormalVoltage(v)` | – | – | – | default float |
| `stereo_pair` (M2:39) | separate ports by convention | stereo port type / `in_place_pair` | – | – | – |
| save/load state (M2:105-106) | `dataToJson` | `clap_plugin_state` | – | – | – |
| `memory_requirements` + host alloc (M2:66,101) | – (plain new) | – | – (SDRAM placement by app) | `-mem`/static memory options (uncertain) | – |
| prepare/reset (M2:102-103) | `onSampleRateChange`, `onReset` | `activate`/`reset` | `Init(sr)` | `init`/`instanceClear` | `dsp` method |
| process, 1..max frames (SDK:208-240) | `process(args)` per sample | `process(clap_process)` per block | `Process()` per sample in block callback | `compute(count,in,out)` | `perform` per block (default 64) |
| `latency_frames` (M2:107) | – | `clap_plugin_latency` | – | – | – |
| `ws2_transport` (M2:60-63) | – (clock modules) | `clap_event_transport` | – | – | – |
| `config.seed` + `ws::Random` (SIG:46-63) | `random::uniform()` global | – | `rand()` in some classes | `no.noise` fixed seed | – |
| Pitch 0=C4, 1.0/oct; audio ±1 (SAG:57-59) | 0 V=C4, 1 V/oct; audio ±5 V | note key/Hz | Hz | Hz | Hz/MIDI |
| UI separate (TS Studio) | ModuleWidget in plugin | GUI extension | – | generated from UI primitives | – (patch GUI) |
(inf, from field names) `ws2_event` note_id/channel/key, NOTE_CHOKE, NOTE_EXPRESSION, PARAM_MOD and status-returning `ws2_event_out::push` closely parallel CLAP's note/output-event model; channels-as-voices with 16 max is close to VCV Rack.

---
### D6. Deterministic patch-to-firmware compiler: exists vs absent (NV items may exist elsewhere)

#### D6.1 Build-time descriptor info
| Need | Exists | Absent/limits |
|---|---|---|
| Ports/params as compile-time data | `static constexpr` `inputs/outputs/params/info` (TPL/module.cpp:4-7; VCA/dsp.h:7-10); `ws::port`/`ws::param` constexpr (SDK:17-25) | optional `query_ports(config,ports)` (SDK:152-153,181) → counts known only after runtime call |
| Port kind | `ws2_port.kind` (M2:38); module.json signal/event | no module.json↔C++ check |
| Stable IDs | string IDs, append-only rule (SAG §2); patches use manifest string IDs (SPEC) | – |
| Range/taper/step | `ws2_param`, validated in prepare (SDK:195-198); formulas `to_plain`/`to_normal` (SDK:26-42), SPEC D6 | `options`,`decimals`,`value_to_text` hard-coded by helper (SDK:24); `value_to_text` UI-only fn ptr (inf) |
| Units for hardware | digital conventions (pitch 0=C4 1.0/oct, audio ±1, gate 0/1); "Hardware adapters MAY scale … (±5 V …)" (SPEC D4) | no adapter/scaling table; "Hardware/plugin adapters … remain future work" |
| Physical control → param map | none | no field/file maps knobs/jacks to IDs |
| CPU cost per module | external measurement; ref: 2 CHAOS instances, Pi 48 kHz/128, worst block 489,275 ns, zero callback allocations, zero faults, 120 s, 45,000 blocks, `python tools/chaos_two_probe.py` (SAG §12) | no cost field in descriptor |

#### D6.2 DSP/host separation
| Need | Exists | Absent/limits |
|---|---|---|
| OS-free DSP header | `dsp.h` includes only wirescape_sdk.h (VCA/dsp.h:3; SEQ/dsp.h:9); registration one-line module.cpp (VCA/module.cpp:3) | SDK pulls simd.h, `<cmath>`, std headers (§3.1) |
| Statically linkable entries | override macros; "may be overridden for static linking"; tests call `descriptor()` directly | `WS_REGISTER_MODULE` always uses macro names → clash without renaming (inf); module_catalog.inc/.h NV |
| Param smoothing/modulation | specified host-side: 5 ms linear ramp in normalized space; `effective_norm = clamp(base_norm + Σ amount_i·cv_i, 0, 1)` then taper (SPEC D6–D7); `ws::LinearRamp` (SIG:9-31) | engine2 implementation is in pack A (§A5.5) [R10][X2]; firmware would need its own (inf); engine2 GPL-3.0-only vs ABI/SDK MIT (SPEC D14) |
| Graph scheduling | specified: Tarjan SCCs; nodes by numeric ID; edges by (from,output,to,input,kind,amount); DFS back-edges; topological order; back-edge delay = `feedback_block` (default 32, valid 1..max block) (SPEC D10) | scheduler is in pack A (engine2 `topology`, A:653-708) [R10][X20]; "Persisting the setting in the app remains future work" |
| Exceptions optional | `guarded()` compiles without try/catch (SDK:163-169) | – |
| SIMD optional | `WS_SIMD_SCALAR` (SIMD:3,30-37) | "NEON/ARM compilation is unverified on this machine" (SPEC D15) |

#### D6.3 Fixed sizes / memory
| Need | Exists | Absent/limits |
|---|---|---|
| Global limits | M2:17-20 (16 ch, 32 ports, 64 params, 1472 payload); engine: 1–4096 frames, 1024 nodes, event budget 1024 / release reserve 256 (the product sidecar uses 2048, X9), arena 1472 KiB, state 1 MiB, 128 MiB/alloc, 64 allocs/node (SPEC) | desktop/Pi-sized; configurability for firmware unstated (inf) |
| Per-config memory | `memory_requirements(config)` → fast/large; wrapper adds `sizeof(Instance)` (SDK:185-190) | runtime fn, not constexpr (TPL/module.cpp:9; VCA/dsp.h:12); optional in SDK but SPEC D11 "MUST report"; module's `alignment` dropped, wrapper reports 32 (SDK:187-188). engine2 refuses a module whose report is below what it allocated, and takes alignment from each `alloc` call [X19] |
| Host-only allocation | `ws2_host.alloc`, `Setup::alloc` (SDK:67-69); TPL test static 8192-byte pool (TPL/tests.cpp:7-8) | `ws2_memory` `size_t` layout differs 32/64-bit (inf) |
| FAST/LARGE hints | `WS2_FAST=1`, `WS2_LARGE=2` (M2:29); "placement are adapter policy" | no adapter policy |
| Fixed block/rate | set in prepare; process rejects other rate or larger block (SDK:211-216) | rate is double, exact equality |
| Per-voice storage | guide: fixed `std::array<Voice,16>` (SAG §5) | not ABI-enforced |

#### D6.4 Determinism
| Need | Exists | Absent/limits |
|---|---|---|
| Block-size independence | guide rule + frame-matrix test (SAG §8, §12); SEQ verified (§3.5) | enforced only by tests |
| Seeded randomness | `ws2_config.seed` (M2:70); `ws::Random::seed(instance,channel)` (SIG:46-51); SPEC D15 | host derivation: engine2 passes `cfg.seed + node id` (A:561) [R10][X20] |
| Reset == fresh | required test 4; SEQ `test_state` verifies | – |
| Stable event order | fan-in tie-break (absolute frame, producer index, producer serial) (SPEC D8) | host implementation: Part A §A5.4 [R10][X20] |
| Cross-target numerics | float32 default; no global fast-math (D15) | no bit-exactness rule/test; double in LinearRamp, to_plain, tan_small, ABI structs (§3.2) |
| Deterministic feedback | back-edges from stable IDs, insertion-order independent (D10) | – |

#### D6.5 Patch input and state
| Need | Exists | Absent/limits |
|---|---|---|
| Machine-readable patch | draft `patch_v2_draft.schema.json` + one example; validator rejects duplicate keys, future versions, duplicate module IDs, missing endpoints, `feedback_block > max_block_frames` | schema files NV; SPEC says draft artifacts "are not implemented, loaded, or applied by the application", but later says `native/document` loads v1/v2 + saves v2 and "App engine integration is M2-6". [X18] The v2 format is implemented (loader and sidecar); the status line refers to the draft schema file. |
| Portable state bytes | little-endian u32/f32 helpers (SDK:140-141,149-150); version word first (SAG §11) | layout private per module; no schema/size field; no 64-bit helpers (SAG §13) |
| File I/O (samples, IRs) | none | "modules can't do I/O. That waits for the sample buffer service (PLAN Track S3)" (SAG §15) |
| Patch → C++ generator | none | not found |

---
### D7. Open questions
**Versions/limits**
1. 32→64 params credited to #402 (M2:19; SAG §13) but #404 (SEQ/dsp.h:33; SEQ/README.md:28) — which?
2. SPEC lists current engine limit "32 ports/parameters/producers", yet `WS2_MAX_PARAMS`=64 and SEQ has 50 params — does engine2 accept >32, or is SPEC stale? **[Answered: X17]**
3. `WS2_MAX_PORTS` (32) checked separately for inputs and outputs (SDK:201) — per direction (64 total)? **[Answered: X17, 32 per direction]**
4. Wrapper exports `abi_version` but never checks host version — where does the host check `ws_module2_abi_version()`/`descriptor.abi_version`? **[Answered for the descriptor: X17; no ABI2 loader exists, X16]**
**Discovery/registration**
5. Does the app load `ws2_<name>` shared libs, compile in via `WS_APP_MODULE`, or both? Which does Studio use; does `module.json` `library` matter in the compiled-in path? **[Answered: X16, compiled-in list]**
6. What are the "five registration edits" (`MODULE_BUILD_GUIDE.md`)? Do any touch TypeScript/Studio UI catalogue files?
7. Who checks `module.json` (IDs, kinds, slot indices) against C++ `inputs/outputs/params` (only manual DoD item)? **[Answered: no checker in packs A–D, X16]**
8. TPL has no `dsp.h`/`DESIGN.md` though SAG §1 requires DESIGN.md "always" — is the template exempt?
**legacy_index**
9. Default 0 is also a valid slot — how does a host distinguish "legacy 0" from "none"? Does any host code read `legacy_index` (wrapper doesn't)? **[Answered: X15]**
10. SEQ `legacy_index` = slot index for all 50 params, incl. 24 added after ABI1 — what is "ABI 1 meaning" for params that never existed in ABI1? **[Context: X15]**
**Struct checks/wrapper**
11. No `struct_size` check for `ws2_port`, `ws2_event_out` (before push), `ws2_transport` — intended?
12. `ws2_reader.bytes` unexposed by `ws::Reader` — will the planned remaining-bytes helper use it?
13. Wrapper drops module's `alignment`, always reports 32 — how does a module request e.g. 64? **[Answered: X19]**
14. `process` compares `ctx.sample_rate != config.sample_rate` exactly — must hosts pass the bit-identical value? **[Answered: X14]**
15. SDK makes `memory_requirements` optional; SPEC D11 says "MUST report" — does the wrapper's `sizeof(Instance)` default satisfy it? **[Answered: X19]**
**Threads/realtime**
16. SAG §15: `latency_frames()` may be read "concurrently with process", value "published atomically"; SPEC D13: state changes quiescent, cross-thread surfaces only enqueue/panic/egress-pop/meter (latency not listed) — which holds? Are atomics needed on a single-core MCU? **[Answered: X7]**
17. SPEC D7: non-`AUDIO_RATE_OK` params "MAY be sampled at a documented lower rate through an SDK helper" — no such helper exists; planned, or host-side?
**Portability/numerics**
18. Is SIG:7-8's comment the D15-required documentation for LinearRamp's double? Is double acceptable on firmware targets?
19. `ws2_memory` uses `size_t`; config/process use double/uint64 — is the ABI meant to be identical on 32-bit MCUs, or will firmware have its own ABI build?
20. `descriptor()` uses a function-local static — is constant initialisation (no thread-safe guard) guaranteed on every target compiler?
21. SPEC D15 says NEON unverified, yet Pi 5 (ARM) is first target — has the NEON `f4` path been compiled/tested anywhere?
**Events/latency**
22. `reset()` can't emit; "the host chokes notes on reset" — is that choke part of the ABI contract a firmware host must implement? **[Answered for engine2: X10]**
23. SPEC: engine latency reporting "is broader than an output-only signal latency calculation and needs review" — which definition will adapters use? **[Same as A-Q24: X7]**
**Patch format/licensing**
24. SPEC says patch v2 draft "not implemented, loaded, or applied by the application" and also that `native/document` loads v1/v2, saves v2, app integration M2-6 — which describes snapshot 44da1e4? **[Answered: X18]**
25. engine2 is GPL-3.0-only, `module2.h`/SDK MIT — if a firmware compiler needs host-side smoothing/modulation/scheduling, would it reuse engine2 code, and under which licence?

---

## Part E — Background reference: hardware, export pipelines, DSP techniques
Source: LLM model knowledge, no internet, unverified.

> **Scope:** Background for a later review of Wirescape: an open-source modular synth with a C++17 engine and an Electron app. Raspberry Pi 5 is the first target and Windows the second. Module DSP is meant to be portable to Daisy-class microcontrollers, and a deterministic "patch → firmware" compiler is a future idea.
> **Knowledge cutoff:** early 2025 (approximate). Products, licences and SDK versions may have changed since then.
> **Convention:** **(uncertain)** marks any fact the author could not state with confidence. All figures are typical values or datasheet values recalled from memory. None were measured. Everything in this part is (mk) unless marked [checked 2026-11].
> **Review:** the licence facts and the PREEMPT_RT status were re-checked in November 2026 against the sources in §E10; nothing else was.

---

### E1. Hardware targets

#### E1.1 Core specifications

| Board | CPU | Clock | FPU | RAM / SRAM / SDRAM | Flash |
|---|---|---|---|---|---|
| **Daisy Seed** (Electrosmith) | STM32H750 (ARM Cortex-M7) | 480 MHz | Single **and** double precision (hardware) | ~1 MB internal SRAM (split across DTCM 128 KB, AXI SRAM 512 KB, SRAM1-3, etc.) + 64 MB external SDRAM | 128 KB internal + 8 MB external QSPI flash |
| **Raspberry Pi Pico 2** (RP2350) | 2× Cortex-M33 **or** 2× Hazard3 RISC-V (selectable at boot) | 150 MHz (stock) | M33: single-precision FPU; double precision via the "DCP" coprocessor (acceleration, not a full DP FPU). RISC-V cores: no FPU | 520 KB SRAM, no SDRAM. PSRAM is possible via QMI on custom boards | 4 MB QSPI flash (Pico 2) |
| **Teensy 4.1** (PJRC) | NXP i.MX RT1062 (Cortex-M7) | 600 MHz (overclockable) | Single + double (hardware) | 1 MB on-chip (512 KB tightly coupled + 512 KB OCRAM). Pads for up to 2× 8 MB PSRAM (16 MB) **(uncertain on max)** | 8 MB QSPI flash |
| **ESP32-S3** (Espressif) | 2× Xtensa LX7 (+ ULP co-processor) | Up to 240 MHz | Single-precision only; double is software-emulated (slow) | 512 KB SRAM; external PSRAM up to 8 MB (octal) on common modules **(uncertain on upper limit)** | External, typically 4–16 MB on modules |
| **Bela** | TI AM3358 (Cortex-A8) on BeagleBone Black + 2× PRU | 1 GHz | VFPv3 (single + double) + NEON (single only) | 512 MB DDR3 | 4 GB eMMC + microSD |
| **Bela Mini** | TI AM3358 on PocketBeagle | 1 GHz | VFPv3 + NEON | 512 MB DDR3 | microSD |
| **Raspberry Pi 5** | Broadcom BCM2712, 4× Cortex-A76 | 2.4 GHz | Single + double + NEON (AArch64 ASIMD) | 2 / 4 / 8 GB LPDDR4X (16 GB variant reported early 2025 **(uncertain)**) | microSD; NVMe via PCIe 2.0 ×1 (HAT/adapter) |
| **Axoloti Core** | STM32F427 (Cortex-M4F) | 168 MHz | Single precision only | 192 KB SRAM (incl. 64 KB CCM) + 8 MB SDRAM | 1 MB internal |
| **Ksoloti Core** | STM32F429 (Cortex-M4F) | 180 MHz **(uncertain; possibly 168 MHz for compatibility)** | Single precision only | 256 KB SRAM + 8 MB SDRAM (variants with more SDRAM **(uncertain)**) | 2 MB internal **(uncertain)** |
| **Organelle M** (Critter & Guitari) | Raspberry Pi Compute Module 3 (4× Cortex-A53) **(uncertain on exact CM revision)** | 1.2 GHz | Single + double + NEON | 1 GB | eMMC/SD **(uncertain)** |
| **Organelle (original, 2016)** | Freescale/NXP i.MX6 (Cortex-A9) **(uncertain)** | ~1 GHz | VFPv3 + NEON | 1 GB **(uncertain)** | microSD **(uncertain)** |

#### E1.2 I/O, audio and software

| Board | Audio codec / bit depth / sample rates | ADC channels & resolution | GPIO count | Typical audio block size | Toolchain / SDK | SDK licence |
|---|---|---|---|---|---|---|
| **Daisy Seed** | Rev4: AK4556. Rev5: WM8731. Seed 1.2 / "Rev7": PCM3060 **(uncertain on mapping)**. 24-bit, 8–96 kHz (48 kHz default). Stereo in/out | 12 ADC pins, up to 16-bit (STM32H7 ADC) | 31 GPIO | libDaisy default 48 frames; configurable down to ~1–4 | arm-none-eabi-gcc, Make, libDaisy + DaisySP, DFU or ST-Link/JTAG | libDaisy: MIT. DaisySP: MIT, with some modules in a separate LGPL repo (DaisySP-LGPL) |
| Daisy **Patch** (Eurorack) | Seed codec + second codec → 4 in / 4 out (AC-coupled audio) | 4 knobs + 4 CV in | 2 gate in, 1 gate out, encoder, OLED, MIDI in/out | as Seed | as Seed | as Seed |
| Daisy **Pod** | Stereo in/out + headphone | 2 knobs | 2 buttons, encoder, 2 RGB LEDs, MIDI (TRS) **(uncertain)** | as Seed | as Seed | as Seed |
| Daisy **Field** | Stereo in/out | 8 knobs, 4 CV in, 2 CV out | 16 key buttons (2×8) with LEDs, OLED, MIDI, gate in/out | as Seed | as Seed | as Seed |
| Daisy **Patch.Init / Patch SM** (related) | Stereo, DC-coupled options | Several CV inputs (12 ADC on the SM) **(uncertain)** | Gates, LED, buttons | as Seed | as Seed | as Seed |
| **Pico 2** | No codec. Audio via external I2S DAC/codec (driven by PIO), PWM or PDM | 3 user ADC pins on the Pico 2 board (4 channels on RP2350A; RP2350B has 8), 12-bit, ~500 ksps | 26 usable on the Pico 2 board (30 on RP2350A, 48 on RP2350B) | User-defined (DMA ping-pong; e.g. 32–256 frames) | Pico SDK (C/C++, CMake, GCC), Arduino-Pico core, MicroPython | Pico SDK: BSD-3-Clause |
| **Teensy 4.1** | No on-board codec. Audio Shield (SGTL5000) is standard. Teensy Audio Library: 16-bit integer, 44.1 kHz | 18 analog pins on 2 ADCs; 10-bit default, 12-bit usable | 55 digital I/O pins | Teensy Audio Library: 128 samples (AUDIO_BLOCK_SAMPLES) | Teensyduino (Arduino IDE), PlatformIO, GCC | Teensy cores and Audio Library: MIT-style. Teensy Loader is free but not fully open **(uncertain)** |
| **ESP32-S3** | No codec. 2× I2S peripherals. Common dev boards (e.g. ESP32-S3-Korvo/LyraT) add ES8388/ES8311-type codecs **(uncertain on board/codec pairing)** | 2× SAR ADC, 20 channels, 12-bit (ADC2 unusable while Wi-Fi is active) | 45 GPIO | User-defined (I2S DMA buffers, e.g. 64–512) | ESP-IDF (CMake, GCC/Xtensa), FreeRTOS, ESP-ADF, Arduino-ESP32 | ESP-IDF: Apache-2.0 |
| **Bela** | TLV320AIC3104: 2 in / 2 out, 16-bit, 44.1 kHz. 8× analog in (16-bit, AD7699) + 8× analog out (16-bit, AD5668) at 22.05 kHz (8-ch mode) or 44.1 kHz (4-ch mode) | 8 × 16-bit (DC-coupled) | 16 digital I/O (sampled at audio rate via PRU) | 16 frames default. As low as 2 frames; ~1 ms round trip possible | Bela IDE (browser) + GCC/Clang on board. Xenomai (Cobalt) co-kernel. Supports C++, Pd (libpd/hvcc), SuperCollider, Csound, Faust | Bela core: LGPL-3.0 **(uncertain)**. Hardware: CC-BY-SA **(uncertain)** |
| **Bela Mini** | Same codec family: 2 in / 2 out, 16-bit, 44.1 kHz | 8 × 16-bit analog in (no analog out on the base cape) | 16 digital I/O | as Bela | as Bela | as Bela |
| **Raspberry Pi 5** | **No 3.5 mm analog jack** (removed vs Pi 4). Audio via HDMI, I2S (GPIO header, HATs), or USB audio interfaces | None on-board | 40-pin header (28 GPIO), driven by the RP1 south-bridge | Linux: 64–256 frames typical at 48 kHz (see §5) | GCC/Clang, Raspberry Pi OS (Debian Bookworm, 64-bit), CMake | Linux kernel GPL-2.0. Userland mixed; Raspberry Pi firmware binary blobs are proprietary |
| **Axoloti** | ADAU1961: 24-bit, 48 kHz, stereo in/out + headphone | ~16 analog-capable header pins, 12-bit (STM32 ADC) **(uncertain on count)** | ~16 GPIO on headers (shared with ADC) **(uncertain)** | 16 samples. "k-rate" = 48000/16 = 3 kHz | Axoloti Patcher (Java) + embedded arm-none-eabi-gcc + ChibiOS | GPL-3.0 (patcher + firmware) |
| **Ksoloti** | ADAU1961: 24-bit, 48 kHz | Similar to Axoloti **(uncertain)** | Similar to Axoloti **(uncertain)** | 16 samples (Axoloti-compatible) | Ksoloti Patcher (fork of Axoloti) | GPL-3.0 |
| **Organelle (M)** | Stereo in/out + mic + headphone, 44.1 kHz **(uncertain on codec part)** | 4 knobs + expression pedal (read by on-board MCU) | 24/25 key buttons **(uncertain on 24 vs 25)**, aux button, encoder, OLED, USB host, MIDI | Pd default 64 samples (Pd block). Audio buffer set in config **(uncertain)** | Pure Data (vanilla) on Linux; patches copied via USB/Wi-Fi | Pd: BSD-3-Clause. Organelle OS and mother.pd: open on GitHub, licence **(uncertain)** |

#### E1.3 Portability-relevant notes per target

| Topic | Daisy (H750) | Pico 2 (M33) | Teensy 4.1 | ESP32-S3 | Bela | Pi 5 |
|---|---|---|---|---|---|---|
| `double` in DSP | Hardware DP, slower than SP | Coprocessor-assisted, notably slower than SP | Hardware DP | Software emulated: very slow | Hardware VFP; NEON is SP only | Full speed |
| SIMD | None (DSP extension integer SIMD only) | None for float | None for float | Limited (PIE vector extension on S3, integer-focused) **(uncertain)** | NEON (ARMv7, flush-to-zero always on in NEON) | NEON/ASIMD (AArch64) |
| Dynamic allocation in audio path | Avoided by convention; SDRAM via `DSY_SDRAM_BSS` | Avoided | Avoided | Avoided; PSRAM slower than SRAM | Allowed outside RT thread only | Allowed outside RT thread only |
| Code-from-QSPI execution | Possible (bootloader "Daisy bootloader" runs apps from QSPI/SRAM); slower than internal flash unless cached | XIP from flash with cache | Runs from flash with cache, or `FASTRUN` to ITCM | XIP from flash with cache, `IRAM_ATTR` for hot code | n/a | n/a |
| Denormal behaviour | FPSCR FZ bit available | FPSCR FZ available | FPSCR FZ available | Xtensa FPU: subnormal handling **(uncertain)** | VFP FZ bit; NEON always FTZ | FPCR.FZ |

---

### E2. Patch-to-hardware pipelines

#### E2.1 Overview

| Pipeline | Input format | Generated output | Main targets | Licence (tool / generated code) |
|---|---|---|---|---|
| **Oopsy** (Electrosmith + Graham Wakefield) | `gen~` patcher inside Max (Max/MSP required) | gen~ C++ export + Oopsy wrapper C++ → Daisy firmware binary | Daisy Seed, Patch, Pod, Field, Patch.Init, Versio, custom JSON boards | Oopsy: MIT, and code generated by Oopsy is MIT. gen~ exported code: dual-licensed, Cycling '74 License for Max-Generated Code for Export or GPLv3. Under the Cycling '74 licence, commercial use that does not sell or distribute the code needs no licence; entities under $200k annual revenue or funding may sell; above that they must register with Cycling '74 [checked 2026-11] [R12] |
| **hvcc / Heavy** (Enzien Audio → open-sourced 2018; maintained fork by Wasted-Audio) | Pure Data vanilla patch (subset) | Portable C/C++ (no dynamic deps), optional JS/WASM | `c`, `daisy`, `dpf` (VST2/VST3/LV2/CLAP via DPF), `js`, `unity`, `wwise`, Bela (via Bela's integration), OWL (via OpenWare) | Compiler: GPL-3.0+. The C runtime copied into generated code (`ir2c/static`) is ISC (Enzien Audio) [checked 2026-11] [R14] |
| **Max RNBO** (Cycling '74, 2022) | `rnbo~` patcher in Max (RNBO object subset) | C++ source export; Web (WASM + JS); VST3/AU plugins (via export service); Max externals; Raspberry Pi runner image | Desktop plugins, web, Raspberry Pi (official target), any C++ host | Proprietary product. Exported code is dual-licensed: Cycling '74 License for Max-Generated Code for Export or GPLv3; RNBO's supporting engine source is MIT. Commercial terms as for gen~ (under $200k revenue or funding may sell); code from RNBO 1.x carries no fees [checked 2026-11] [R12] |
| **Faust** (GRAME) | `.dsp` Faust language source | C, C++, Rust, LLVM IR, WASM, CMajor, JAX, etc., wrapped by "architecture files" | `faust2daisy`, `faust2teensy`, `faust2esp32`, `faust2bela`, `faust2rpialsaconsole`, `faust2lv2`, `faust2vst`, `faust2juce`, `faust2jack`, `faust2max6`, `faust2puredata`, `faust2supercollider`, `faust2wasm`, etc. | Compiler: current sources largely LGPL-2.1+, with some GPL files (Debian packaging of Faust 2.77–2.79). Architecture files carry a FAUST exception, and the Faust FAQ says the compiler licence does not apply to generated code [checked 2026-11] [R13] |
| **plugdata "Compiled mode"** (Timothy Schoen et al.) | Pd patch edited in plugdata with object set restricted to Heavy-compatible objects | Through bundled hvcc toolchain: C++ source, Daisy firmware (flash via built-in DFU), DPF plugins, Pd externals | Daisy, desktop plugins, C++ | plugdata: GPLv3. Output: same as hvcc |
| **Axoloti / Ksoloti patcher** | Graphical patch in the Java patcher; objects are `.axo` XML files with embedded C++ snippets | Single C++ file per patch, compiled on host with arm-none-eabi-gcc → binary loaded to SRAM (live) or saved to flash/SD | Axoloti Core, Ksoloti Core | GPL-3.0 |
| **Organelle** | Pure Data vanilla patch folder (`main.pd`) | No compile step: interpreted by Pd on the device (Linux) | Organelle, Organelle M | Pd: BSD-3-Clause |

#### E2.2 Restrictions (what cannot go through)

| Pipeline | Restricted / unsupported features |
|---|---|
| **Oopsy** | Only what gen~ supports (no MSP objects outside gen~). Memory limits: `data`/`buffer` sized to fit SRAM/SDRAM (large buffers go to SDRAM). No file I/O beyond what Oopsy wraps (SD-card WAV loading is limited/experimental **(uncertain)**). CPU budget of the H750 at the chosen block size |
| **hvcc** | Vanilla-only subset. No externals, no GUI-dependent behaviour (GUI objects act as plain number boxes/receives). Unsupported or partial (version-dependent): `expr`/`expr~` (supported from hvcc v0.15.0, late 2025 [checked 2026-11] [R14]), `soundfiler`, `readsf~`/`writesf~`, `netsend`/`netreceive`, `text`/`qlist`/`textfile`, `clone`, `array` sub-features, dynamic patching, `[block~]` resizing/overlap. Tables must be fixed size or resized via message |
| **RNBO** | Only RNBO-compatible objects (a subset of Max/MSP + gen-style code). No Jitter, no arbitrary third-party externals, no JavaScript `js` object (RNBO has its own codebox). Buffers/data handled via declared `buffer~`/`data` with loader hooks |
| **Faust** | No dynamic memory allocation. Delay lengths must have compile-time bounds. No arbitrary control flow (functional block diagram). File loading via `soundfile` primitive (architecture-dependent). Tables via `rdtable`/`rwtable` |
| **plugdata compiled** | Same as hvcc. The UI greys out or blocks non-compatible objects |
| **Axoloti** | Only objects from the Axoloti library or user `.axo` objects. Fixed 16-sample block, 48 kHz. SDRAM used for tables/delays. Patch size limited by SRAM for code/data in live mode |
| **Organelle** | Only Pd vanilla + externals compiled for the device's ARM Linux. CPU limited (≈ A53/A9 class). Display/keys handled through the `mother.pd` host protocol |

#### E2.3 Control mapping (knobs, pins, jacks → parameters)

| Pipeline | Mapping mechanism |
|---|---|
| **Oopsy** | Name matching: gen~ `param`, `in`, `out` and `history` names are matched against names defined in the **board JSON** (e.g. `knob1`, `cv1`, `gate1`, `sw1`, `encoder`, `led1`, `cv_out1`, `midi_*`). Custom hardware: a user-written JSON describing components (pins, types such as `AnalogControl`, `Switch`, `Led`, `GateIn`), modelled on libDaisy's component definitions. Options such as sample rate, block size and `boost` set via an `oopsy` object or patcher attributes |
| **hvcc** | `[r name @hv_param min max default]` exposes parameters (older syntax `@hv_param`). Outputs via `[s name @hv_event]`. The Daisy target uses a board description (JSON) where receive names (`knob1`, `gate1`, `sw1`, `cv1`, `encoder`, etc.) map to hardware components, plus `-m meta.json` for the board selection |
| **RNBO** | `param` objects become host/plugin parameters. The Raspberry Pi target exposes params via web UI, OSC and MIDI CC mapping. `inport`/`outport` for messages. C++ export: host code sets params via `setParameterValue(index, value, time)` |
| **Faust** | Widget metadata. Daisy: `hslider("freq[knob:1]", ...)`, `button("gate[switch:1]")`. Bela: `[BELA: ANALOG_0]`, `[BELA: DIGITAL_0]`. Teensy/ESP32: params exposed as setter methods on generated classes. MIDI: `[midi:ctrl 7]`. OSC: automatic in some architectures |
| **plugdata compiled** | Same as hvcc (receives with `@hv_param`). Board choice in the export dialog |
| **Axoloti** | Each object can expose on-patch knobs/dials. Hardware inputs via `gpio/in/analog`, `gpio/in/digital` objects. MIDI CC via `midi/in/cc` objects or parameter MIDI-learn. Patch "presets" and parameter morphing built in |
| **Organelle** | `mother.pd` sends knob values on `[r knobs]` (list of 4 + expression), keys on `[r notes]`/`[r key]` **(uncertain on exact receive names)**, aux on `[r aux]`. OLED written via `[s oled]`/`screenLine1..5` messages |

#### E2.4 Build / flash steps

| Pipeline | Typical steps |
|---|---|
| **Oopsy** | Place `[oopsy]` in the Max patcher containing the gen~ object(s) → choose target → Oopsy exports gen~ code, generates wrapper, invokes `arm-none-eabi-gcc`/`make`, and flashes via `dfu-util` (board in DFU mode: hold BOOT, press RESET). Multiple gen~ "apps" can share one firmware, switched with the encoder |
| **hvcc** | `hvcc patch.pd -o out -n name -g daisy -m meta.json` → `make` in generated folder (needs libDaisy/DaisySP) → `make program-dfu`. For C: include generated sources in your own build and call `hv_processInline()`/`hv_process()` per block |
| **RNBO** | In Max: Export Sidebar → choose target (C++ source, VST3/AU, Web, Raspberry Pi) → for Pi: install the RNBO runner image on the Pi, export over the network; for C++: integrate with the RNBO C++ adapter (`RNBO::CoreObject`) |
| **Faust** | `faust2daisy -patch file.dsp` (options like `-sr`, `-bs`, `-pod`, `-patch`) → produces a buildable project/binary → flash via DFU. Other `faust2xxx` scripts similar. Faust IDE / Faust Web IDE can also export |
| **plugdata compiled** | Enable Compiled mode → Export dialog (Heavy) → choose Daisy (board, flash/SRAM bootloader options) → plugdata runs bundled toolchain and DFU flash |
| **Axoloti** | Edit patch → "Live" button compiles (GCC on host) and uploads to SRAM over USB → "Upload to SD/flash" for standalone startup patch. Firmware itself updated from patcher |
| **Organelle** | Copy patch folder to `/Patches` on USB stick or internal storage (or via web/Wi-Fi upload) → select from Organelle menu. No compilation unless externals are used |

#### E2.5 Determinism / reproducibility notes (factual)

| Pipeline | Notes |
|---|---|
| Oopsy / gen~ | gen~ code generation is deterministic for a given Max version **(uncertain)**. Output depends on Max/gen~ version and Oopsy version |
| hvcc | Generates code from Pd graph topology. Execution order follows Pd's depth-first message ordering with Heavy-specific rules. Object IDs in output derived from graph |
| Faust | Pure functional semantics: the same `.dsp` + compiler version + options → the same code. Floating-point results can still differ across `-single/-double`, `-vec`, compiler flags and FMA contraction |
| Axoloti | Code is generated from object order. Execution order is determined by patch layout (Axoloti executes objects sorted by **position**: top-to-bottom/left-to-right) **(uncertain on exact sort rule)** |

---

### E3. Module / plugin APIs

#### E3.1 Declaration of ports, params, polyphony, state

| API | Language / ABI | Ports & params declaration | Polyphony | State |
|---|---|---|---|---|
| **VCV Rack 2 Module API** | C++ (not a stable C ABI) | In the `Module` constructor: `config(NUM_PARAMS, NUM_INPUTS, NUM_OUTPUTS, NUM_LIGHTS)`, then `configParam(id, min, max, default, name, unit)`, `configSwitch`, `configButton`, `configInput`, `configOutput`, `configBypass`. Panel and widgets in a separate `ModuleWidget` (SVG panel, `createParamCentered<>` etc.) | Polyphonic cables up to **16 channels**. Modules call `outputs[i].setChannels(n)` and read `inputs[i].getChannels()`. SIMD helpers (`float_4`) | `dataToJson()` / `dataFromJson()` (Jansson `json_t*`). Params saved automatically. `onReset`, `onRandomize`, `onSampleRateChange` events |
| **CLAP** | Pure C ABI (headers), C++ helpers available | Extensions: `clap.audio-ports` (ports, channel counts, port types), `clap.note-ports` (CLAP/MIDI/MIDI-MPE dialects), `clap.params` (`get_info`, `get_value`, `value_to_text`, flags: automatable, modulatable, per-note/key/channel modulation) | First-class per-note **polyphonic modulation** and note expressions. `voice-info` extension. Note IDs, port/channel/key addressing | `clap.state` (`save`/`load` via stream). `state-context` extension (preset vs project vs duplicate) |
| **VST3** | C++ COM-like interfaces (`FUnknown`, IIDs) | `IComponent` + `IAudioProcessor` (processing) and `IEditController` (parameters/UI), usually separate objects. Buses: `addAudioInput/Output`, `addEventInput`. Params: `ParameterInfo` (ID, title, units, step count, default normalized value). **All values normalized 0–1** | Note events (noteOn/noteOff with noteId). `INoteExpressionController` for per-note expression. No standardized per-voice param modulation equivalent to CLAP | `IComponent::getState/setState` + controller `setComponentState`, via `IBStream`. Separate processor and controller state |
| **LV2** | C ABI + RDF/Turtle (`.ttl`) metadata | Ports declared in `.ttl`: `lv2:AudioPort`, `lv2:ControlPort` (float, with `lv2:minimum/maximum/default`), `lv2:CVPort`, `atom:AtomPort` (MIDI, patch messages). Host calls `connect_port()`. Newer style: `patch:writable` properties via atoms | No built-in voice model; MIDI via atom ports. Polyphony is internal to the plugin | `state` extension (`save`/`restore` with key/value + URIDs). Control port values saved by host |
| **AU (Audio Unit)** | AUv2: C API (Component Manager / AudioComponent). AUv3: Obj-C/Swift app extension (`AUAudioUnit`) | Buses via `AUAudioUnitBus`. Parameters via `AudioUnitParameter` (v2) or `AUParameterTree` (v3), with ranges and units (not normalized) | MIDI events in render (`MusicDeviceMIDIEvent`). MIDI 2.0/UMP support in newer AUv3 **(uncertain on version)** | `ClassInfo` property list (v2). `fullState`/`fullStateForDocument` (v3) |
| **DaisySP** | C++ classes (static, no plugin ABI) | No ports/params concept. Each DSP object: `Init(sample_rate)`, setters (`SetFreq`, `SetRes`...), `Process()` per sample (some per block) | None. User instantiates N objects | None. Plain member variables |
| **Faust** | Compiler-generated class (C++ etc.) | Inputs/outputs derived from signal arity of `process`. Params from UI primitives (`hslider`, `vslider`, `nentry`, `button`, `checkbox`; bargraphs for outputs). Exposed via `buildUserInterface(UI*)` | `declare options "[nvoices:8]"` or `[midi:on][nvoices:N]` → polyphonic architectures (`mydsp_poly`) with `freq`/`gain`/`gate` conventions | Params only (architecture-handled). The generated class has `instanceInit`, `instanceClear`, `getSampleRate`, `clone` |
| **Pd external API** | C ABI (`m_pd.h`) | `class_new()`, `class_addmethod()`, `inlet_new()`, `outlet_new()`. Signal objects: `CLASS_MAINSIGNALIN`, `dsp` method adds a perform routine with `dsp_add()` | None built in. `[clone]` object (Pd ≥ 0.47) replicates abstractions | No standard state API. Arguments persist in the patch file. GUI objects use `savefn`/`class_setsavefn` |
| **SuperCollider UGen** | C++ against `SC_PlugIn.h` (interface table, `InterfaceTable *ft`) | Server side: struct `MyUGen : public Unit`, `MyUGen_Ctor`, `MyUGen_next_a/k`, registered with `DefineSimpleUnit`/`DefineDtorUnit` inside `PluginLoad(Name)`. Language side: `.sc` class file with `*ar`/`*kr` methods (`MultiOutUGen` for multiple outputs) | Polyphony at Synth/node level (one Synth per voice). Multichannel expansion in sclang | None per UGen. State lives in Synth args / Buffers |

#### E3.2 Threading, realtime rules, discovery, versioning

| API | Threading model | Realtime rules | Discovery / loading | Versioning / ABI stability |
|---|---|---|---|---|
| **VCV Rack 2** | Engine thread(s) call `process(const ProcessArgs&)` **per sample** (args: `sampleRate`, `sampleTime`, `frame`). Configurable number of engine threads. UI on a separate thread (`step`/`draw`). Expanders exchange messages with 1-sample latency (double-buffered) | No allocation, locks or I/O in `process`. Cable latency: 1 sample per cable | Plugins in user `plugins` folder as directories with `plugin.json` manifest + shared library (`plugin.so`/`.dll`/`.dylib`). Entry point `init(Plugin*)`. Library/store distribution | Major-version ABI: Rack 1 plugins are incompatible with Rack 2. `plugin.json` version must match major. SDK GPL-3.0-or-later; VCV sells commercial licence/exemptions **(uncertain on exact model)** |
| **CLAP** | Explicit thread specs: `[main-thread]`, `[audio-thread]`, `[thread-safe]` on every function. `thread-check` extension. Optional `thread-pool` extension for host-provided worker threads | `process()` must be realtime-safe. Parameter changes arrive as sample-timestamped events in the process call. `request_callback` for main-thread work | `.clap` files (shared libs) in standard paths (`~/.clap`, `/usr/lib/clap`, `%COMMONPROGRAMFILES%\CLAP`, etc.). Exported `clap_entry` → `get_factory(CLAP_PLUGIN_FACTORY_ID)`. Can contain multiple plugins | `clap_version` struct. ABI stable since 1.0 (2022). Extensions identified by string IDs; drafts carry versioned IDs. Licence: MIT |
| **VST3** | UI/controller on the main (UI) thread; `process()` on the audio thread. Communication via `IConnectionPoint`/messages. Sample-accurate params via `IParameterChanges` queues in `ProcessData` | No allocation/locks in `process`. `setupProcessing`/`setActive` outside RT | `.vst3` bundle (folder on all platforms in recent SDKs) in standard folders (e.g. `C:\Program Files\Common Files\VST3`, `/Library/Audio/Plug-Ins/VST3`, `~/.vst3`). Exported `GetPluginFactory()`. Optional `moduleinfo.json` for fast scanning | Interfaces are immutable once published; new functionality = new interface + new IID (COM-style). SDK licence: MIT from VST 3.8 (29 October 2025); the earlier GPLv3 / proprietary dual licence is no longer offered for new SDK versions [checked 2026-11] [R11] |
| **LV2** | Spec defines thread classes: "Discovery", "Instantiation", "Audio". `run()` in Audio class. `worker` extension schedules non-RT work. `options`/`buf-size` extensions for block size info | Hosts may set `lv2:hardRTCapable` expectations. `run()` must be RT-safe when the plugin declares `lv2:hardRTCapable` | Bundles (`name.lv2/` folders containing `manifest.ttl` + `.so`) found via `LV2_PATH`. Hosts typically use **lilv** to query RDF. Exported `lv2_descriptor()` | Versioning via `lv2:minorVersion`/`lv2:microVersion` in Turtle. Spec and libs under ISC licence. C ABI stable |
| **AU** | Render callback on the audio (real-time) thread. Properties/params on the main thread. AUv3 runs out-of-process by default on macOS (can run in-process) | Standard Core Audio RT rules. AUv3 uses `internalRenderBlock` (no Obj-C messaging in the render block) | AUv2: `.component` bundles in `/Library/Audio/Plug-Ins/Components`, registered via Info.plist `AudioComponents`. AUv3: app extension inside an app. Validation with `auval` | Apple-controlled. AUv2 long-lived but deprecated-direction; AUv3 is current. Licence: Apple SDK (proprietary), macOS/iOS only |
| **DaisySP** | Called from the libDaisy audio callback (DMA interrupt context) | No allocation, no blocking. Large buffers in SDRAM via `DSY_SDRAM_BSS` | Static linking only | Source-level library, no ABI guarantees. MIT (+ LGPL sub-repo) |
| **Faust** | Single `compute(count, inputs, outputs)` call per block. UI values read once per block (zone pointers). `-vec`/`-sch`/`-omp` options for vector/parallel code | Generated code allocates nothing in `compute`. Memory allocated by host/architecture (custom memory managers for MCU targets) | Statically compiled, or JIT via libfaust (LLVM or interpreter backend) | Generated code is self-contained. Compiler versions can change output |
| **Pd external** | Single-threaded scheduler (messages and DSP in the same thread, interleaved by logical time). Audio I/O thread separate in some configs. `sys_lock` for external threads | Perform routines run on the DSP tick (default 64-sample block). Avoid blocking I/O; `[clock]`-based deferral | Pd searches its paths for `name.pd_linux`/`.l_arm64`/`.d_fat`/`.dll`/`.m_amd64`/`.dll`/`.so` etc., calls `name_setup()`. Multi-object libraries via `-lib` or `[declare -lib]` | C ABI largely stable over decades. Separate 64-bit-float builds ("Pd64", `.windows-amd64-64.dll`-style extensions) not binary compatible with 32-bit-float Pd **(uncertain on naming)**. Pd licence BSD-3 |
| **SuperCollider UGen** | scsynth: single DSP thread. Supernova: parallel groups (multi-threaded). Calc functions run per control block (default 64 samples) | Use `RTAlloc`/`RTFree` (real-time pool), never `malloc` in calc functions. Async commands (`DoAsynchronousCommand`) for non-RT work | Plugins (`.scx` on macOS, `.so` on Linux, `.scx`/`.dll` on Windows) in extension folders, loaded at server boot. sclang compiles `.sc` class files at startup | `sc_api_version` checked on load. Supernova needs separate builds. SuperCollider licence GPL-3.0 |

---

### E4. DSP technique reference

#### E4.1 Band-limited oscillators

| Technique | Principle | Typical alias performance | Cost | Notes |
|---|---|---|---|---|
| **Naive** (trivial) | Direct waveform from phase (saw = 2·phase−1) | Poor: audible aliasing for fundamentals above ~1–2 kHz at 44.1/48 kHz. Fold-back is inharmonic | Lowest | Acceptable for LFOs and sub-audio rates |
| **PolyBLEP** | Adds a 2-sample polynomial residual (approximate band-limited step) at each discontinuity | Moderate: removes much of the strongest aliasing. Residual aliasing remains for high fundamentals. Some HF roll-off in the passband | Low (a few ops per sample + per discontinuity) | Square/pulse via two BLEPs. Triangle via integrated square or polyBLAMP. Hard sync is possible but less clean. Higher-order variants (4-point) improve results |
| **BLEP / minBLEP** (Brandt 2001, "Hard sync without aliasing") | Insert a pre-computed minimum-phase band-limited step (from windowed sinc) at each discontinuity, with sub-sample offset | Good–very good, depending on table length and oversampling of the table (e.g. 16–64 zero-crossings, high table oversampling) | Medium: overlap-add buffer, table lookups per discontinuity | Minimum phase → low latency. Handles hard sync and arbitrary discontinuities. BLAMP for slope discontinuities |
| **BLIT** (Stilson & Smith 1996) | Generate a band-limited impulse train (closed-form sinc sum, e.g. `sin(Mπx)/(M·sin(πx))`), integrate to get saw/square/triangle | Good in principle. Leaky integrator causes DC/drift and low-frequency issues. Numerical issues near zero denominator | Medium | Modulation of frequency changes integrator state behaviour. Largely superseded by BLEP in practice |
| **Wavetable with mipmaps** | Pre-computed tables, each band-limited for a frequency range (e.g. one per octave or per third-octave); pick table by playback increment; interpolate within and optionally across tables | Good if enough tables and an adequate interpolation method. Aliasing at the top of each band depends on table spacing and headroom | Low CPU, higher memory (e.g. 2048 samples × ~10 tables per waveform) | Allows arbitrary waveforms and wavetable morphing. Crossfading between mip levels avoids timbral steps |
| **Oversampling** | Run naive (or partially band-limited) oscillator at N× rate, then low-pass and decimate | Improves roughly with N but naive saw aliasing decays slowly (~6 dB/oct). Often combined with polyBLEP | Roughly N× oscillator cost + decimation filter (polyphase FIR/IIR halfband) | Also used for nonlinear stages (waveshapers, filter saturation). Adds latency if linear-phase FIR is used |
| **Additive** (reference) | Sum of sinusoids up to Nyquist | Alias-free by construction | High (per-partial) | Useful as reference/oracle in testing |

#### E4.2 Filters and behaviour under audio-rate modulation

| Filter | Origin / reference | Structure | Stability / behaviour under fast/audio-rate cutoff modulation | Cost |
|---|---|---|---|---|
| **Biquad (RBJ cookbook)** | Robert Bristow-Johnson, "Audio EQ Cookbook" | 2nd-order IIR. DF-I, DF-II, transposed DF-II | Stable for fixed coefficients within range. Under rapid coefficient changes, DF-II/TDF-II can produce transients/"zipper" and even temporary instability because the state is not normalised to the new coefficients. DF-I is better behaved. Frequency warping near Nyquist (bilinear transform) | Low (5 mul / sample) |
| **Chamberlin SVF** | Hal Chamberlin, "Musical Applications of Microprocessors" | 2 integrators, forward Euler | Unstable above roughly fs/6 cutoff (or at high resonance) without oversampling | Very low |
| **TPT / ZDF SVF** | Vadim Zavalishin, *The Art of VA Filter Design*. Andrew Simper (Cytomic) "linear trapezoidal SVF" | Trapezoidal integrators, zero-delay feedback solved analytically | Robust under audio-rate modulation (state variables are physically meaningful integrator states). Simultaneous LP/BP/HP/notch outputs. Cutoff prewarping via `tan(π·fc/fs)` | Low–medium (`tan` per update; approximations possible) |
| **Moog ladder: Stilson–Smith** | Stilson & Smith 1996, "Analyzing the Moog VCF with considerations for digital implementation" | 4 one-pole stages with unit delay in the feedback path; tuning/resonance compensation tables or polynomials | The unit delay in feedback causes cutoff/resonance interaction. Generally stable but the response deviates at high cutoff. Linear model (no saturation) | Low |
| **Moog ladder: Huovilainen** | Antti Huovilainen 2004, "Non-linear digital implementation of the Moog ladder filter" (DAFx) | 4 nonlinear stages with `tanh` per stage, half-sample delay compensation, typically 2× oversampled | Behaves well, with self-oscillation and saturation. Cost and aliasing rise with nonlinearity. Improved versions by Välimäki & Huovilainen (2006) and D'Angelo & Välimäki (2013/2014) **(uncertain on years)** | Medium–high (`tanh` ×4–5 per sample, oversampling) |
| **ZDF ladder** | Zavalishin (TPT) | 4 TPT one-poles with the feedback loop solved implicitly. Nonlinear version needs iterative solution (Newton–Raphson) or approximations (e.g. "cheap" tanh estimates from previous state) | Linear ZDF: robust under modulation and accurate cutoff tuning. Nonlinear: robustness depends on solver convergence and iteration count | Linear: low–medium. Nonlinear with Newton: high |
| **One-pole (TPT)** | — | Single trapezoidal integrator | Robust | Very low |
| **Diode ladder / Sallen-Key / MS-20 VA models** | Various (Zavalishin, Pirkle, Stinchcombe analyses) | Coupled ZDF structures | Similar to ZDF ladder | Medium–high |

#### E4.3 Parameter smoothing

| Method | Description | Properties |
|---|---|---|
| **One-pole low-pass (exponential)** | `y += a·(target − y)`, `a = 1 − exp(−1/(τ·fs))` | Cheap. Never exactly reaches target (needs snap threshold). Natural for gain-in-dB-like perception. Common τ 5–50 ms |
| **Linear ramp** | Fixed number of samples (e.g. 64 or N ms) from current to target | Reaches target exactly. Constant-time or constant-rate variants. Retrigger mid-ramp from current value |
| **Per-block linear interpolation** | Compute target at block rate, interpolate across the block | Cheap. Block-size-dependent smoothing time |
| **Multiplicative / exponential-domain ramp** | Ramp in log domain (frequency, gain) | Perceptually uniform for frequency/gain |
| **Slew limiter** | Max change per sample (rise/fall separately) | Matches analog "lag/slew" modules. Non-linear |
| **2-pole / critically damped** | Two cascaded one-poles or a 2nd-order smoother | Smoother start/end (no derivative jump). Slightly more cost |
| **Sample-accurate events** | Apply parameter change at exact sample offset (CLAP/VST3 event timestamps) | Combined with any smoother above |
| **Filter-coefficient vs parameter smoothing** | Smooth the user parameter (e.g. cutoff Hz) then recompute coefficients, vs smoothing coefficients directly | Smoothing coefficients directly can pass through unstable intermediate sets for some structures (e.g. DF biquad). TPT structures tolerate per-sample recompute |

#### E4.4 Denormal (subnormal) handling

| Platform | Mechanism | Details |
|---|---|---|
| **x86 / x86-64 SSE** | MXCSR register: **FTZ** (bit 15) flushes subnormal results to zero; **DAZ** (bit 6) treats subnormal inputs as zero | Set via `_MM_SET_FLUSH_ZERO_MODE(_MM_FLUSH_ZERO_ON)` and `_MM_SET_DENORMALS_ZERO_MODE(_MM_DENORMALS_ZERO_ON)` or `_mm_setcsr`. **Per-thread** state: must be set on the audio thread. x87 FPU has no FTZ (relevant only for 32-bit x87 code). Penalty for subnormals on x86 can be ~10–100× per operation **(uncertain on exact factor; CPU-dependent)** |
| **AArch64 (Pi 5, Cortex-A76)** | FPCR register **FZ** bit (bit 24). FZ16 for half precision | Set via inline asm (`msr fpcr, ...`) or compiler intrinsics. Per-thread. NEON/ASIMD respects FPCR.FZ on AArch64 |
| **ARMv7-A (Bela Cortex-A8, Cortex-A9)** | FPSCR **FZ** bit (bit 24) for VFP | **NEON (ARMv7) always flushes subnormals to zero** regardless of FPSCR. Cortex-A8 VFP is slow (non-pipelined "VFPLite"); hence `-mfpu=neon -ffast-math` common on Bela |
| **ARMv7-M / ARMv8-M (Cortex-M4F/M7/M33)** | FPSCR FZ bit (bit 24) | Cortex-M FPUs handle subnormals in hardware with little or no penalty **(uncertain)**. FZ still affects bit-exactness |
| **Compiler flags** | `-ffast-math` (GCC/Clang) links startup code that sets FTZ/DAZ on x86 (`crtfastmath.o`) | Applies to process startup thread. Other threads may need explicit setting **(uncertain on threading behaviour)**. MSVC `/fp:fast` does not set FTZ automatically **(uncertain)** |
| **Algorithmic methods** | Add tiny DC offset (e.g. 1e-18 to 1e-25) or alternating-sign tiny value / noise to feedback paths; explicit flush (`if (fabs(x) < 1e-15f) x = 0`) | DC offset is blocked by highpass stages if present. Alternating sign avoids DC accumulation. Explicit checks cost branches |
| **Where subnormals appear** | Decaying feedback loops: IIR filters, reverbs, delays with feedback, envelope release tails, after input silence | Typical symptom: CPU spike when audio goes silent |

#### E4.5 Delay-line interpolation and modulated-delay artefacts

| Method | Order / taps | Frequency response | Behaviour when modulated | Cost |
|---|---|---|---|---|
| **None (integer)** | 1 tap | Flat | Zipper noise / clicks at each integer step | Minimal |
| **Linear** | 2 taps | Low-pass that varies with fractional position (worst at fraction 0.5, where it has a zero at Nyquist) [R15] | Modulating the fraction modulates the HF response → HF amplitude modulation/"noise". Generally stable and commonly used for chorus/flanger | Very low |
| **Allpass (1st order, Thiran)** | 1 state | Flat magnitude, frequency-dependent phase | Internal state makes it unsuitable for fast/large modulation (transients when delay changes). Good for fixed fractional delays (e.g. tuning of waveguides) | Low |
| **Lagrange (3rd order)** | 4 taps | Max-flat at DC. Mild HF roll-off. Better than linear | Better than linear, still some fraction-dependent HF variation | Low–medium |
| **Cubic Hermite / Catmull-Rom** | 4 taps | Similar class to 3rd-order Lagrange, slightly different trade-offs | Common for modulated delays and resampling | Low–medium |
| **Windowed sinc / polyphase FIR** | 8–64 taps | Near-flat to high frequency | Best quality. Used for pitch-shift/resampling. Higher latency (needs lookahead) | High |

| Modulated-delay artefact | Cause |
|---|---|
| Doppler pitch shift | Rate of change of delay time (intended in chorus/vibrato) |
| Zipper / stepping | Unsmoothed or block-rate delay-time updates |
| HF modulation / "grain" | Interpolator's fraction-dependent frequency response (linear especially) |
| Clicks on large jumps | Discontinuous read position. Fixes include cross-fading two read heads |
| Reading past the write head | Delay modulated below 0 or above the buffer length. Needs clamping/wrapping |

#### E4.6 Reverb structures

| Structure | Reference | Topology | Characteristics |
|---|---|---|---|
| **Schroeder** | M. R. Schroeder, 1961/1962 ("Natural sounding artificial reverberation") | 4 parallel feedback combs → 2 series allpasses | Metallic/fluttery. Low echo density early. Historically foundational |
| **Moorer** | J. A. Moorer, 1979 ("About this reverberation business") | Schroeder + low-pass in comb feedback + early-reflection tapped delay | More natural HF decay |
| **Freeverb** | "Jezar at Dreampoint", ~2000, public domain | Per channel: 8 parallel low-pass-feedback combs → 4 series allpasses. Right channel delays offset by a stereo spread (23 samples). Tunings defined at 44.1 kHz | Cheap, widely ported. Some metallic character. Needs denormal care. DaisySP's reverb is `ReverbSc` (Csound, Sean Costello), not Freeverb **(uncertain on the full DaisySP reverb list)** [R15] |
| **FDN (Feedback Delay Network)** | Stautner & Puckette 1982; Jot & Chaigne 1991 | N delay lines (4–16+) mixed by a unitary/orthogonal feedback matrix (Householder, Hadamard), with per-line absorption filters | Scalable density. Decay time per band controllable via absorption filters. Modulation of delays reduces ringing |
| **Dattorro plate** | Jon Dattorro, 1997, "Effect Design Part 1: Reverberator and Other Filters" (JAES). Credited as Griesinger-style topology | Input bandwidth filter → 4 input diffusers (allpasses) → "figure-8" tank of two cross-coupled branches with modulated allpasses, delays, damping filters. Multiple output taps. Original tuning at 29761 Hz | Dense, smooth plate sound. Widely reimplemented (e.g. in Eurorack modules and VCV plugins) |
| **Convolution** (reference) | — | FFT partitioned convolution with IR | Realistic. High memory/CPU. Latency depends on partitioning |
| **ReverbSc** (Csound) | Sean Costello | 8 delay-line FDN with randomly modulated delays | Lush. Used in Csound and DaisySP |

#### E4.7 Click-free envelope and gate handling

| Issue | Technique |
|---|---|
| Retrigger clicks | Start the new attack from the **current** envelope level, not from 0 |
| Instant attack/release clicks | Minimum segment time (e.g. ~0.5–2 ms) or a short ramp on any discontinuity |
| Voice stealing | Fast fade-out (e.g. 1–5 ms) of the stolen voice before reuse, or a separate "steal" release |
| Exponential segments | One-pole style segments (RC-like) with overshoot target (e.g. aim at 1.2 and clip at 1.0) for analog-like attack shape |
| Gate detection from CV/audio | Schmitt trigger (hysteresis, e.g. on at 1–2 V / off at ~0.1–1 V); debounce for buttons |
| Sample-accurate gates | Process gate edges at the sample where they occur, not at block boundaries (block-rate gates cause jitter up to one block) |
| Gate retrigger in modular CV | Distinguish gate vs trigger. Retrigger requires a falling edge or a separate trigger input |
| DC/offset steps | Highpass/DC blocker on outputs. Ramps when switching routes or enabling/disabling modules |
| Bypass / patch changes | Crossfade (e.g. 5–20 ms) between old and new graph outputs when rebuilding a patch |

---

### E5. Linux realtime audio on Raspberry Pi 5

#### E5.1 Audio stack options

| Layer | What it is | Pros (factual) | Cons / notes (factual) |
|---|---|---|---|
| **ALSA (direct, `hw:`)** | Kernel sound subsystem + `libasound` | Lowest overhead. Exclusive device access. Full control of period size/count | One client per hw device (without dmix). App must handle xrun recovery (`snd_pcm_recover`) |
| **ALSA `plughw:` / dmix** | Software conversion / mixing plugins | Format/rate conversion, sharing | Extra latency/CPU. dmix not suited to low latency |
| **PipeWire** | Default audio server on Raspberry Pi OS Bookworm (switched from PulseAudio around late 2023 **(uncertain on exact release)**) | Provides PulseAudio and JACK API compatibility (`pw-jack`). Graph quantum configurable. Per-node latency requests (`PIPEWIRE_LATENCY=128/48000`) | Extra scheduling layer. Quantum may be raised by other clients (the graph runs at the max requested by any node unless forced). Needs RT priority via RTKit or limits |
| **JACK2** | Pro-audio server, graph of clients | Mature, deterministic, well-known xrun reporting. Sample-accurate graph | Conflicts with PipeWire/PulseAudio for the device unless bridged. Separate configuration (`jackd -d alsa -p 128 -n 2/3 -r 48000`) |

#### E5.2 Typical buffer sizes (Pi-class ARM SBCs, USB class-compliant interface, 48 kHz)

| Setting | Period × periods | One-way buffer latency | Typical stability **(uncertain; system-dependent)** |
|---|---|---|---|
| 32 frames | 32 × 2/3 | 0.67 ms per period | Often unstable without RT kernel and tuning |
| 64 frames | 64 × 2/3 | 1.33 ms | Achievable with tuning. Occasional xruns under load (especially with GUI/Electron activity) |
| 128 frames | 128 × 2/3 | 2.67 ms | Commonly reported as stable with a tuned stock kernel |
| 256 frames | 256 × 2/3 | 5.33 ms | Typically robust |
| USB note | UAC2 devices add device-side buffering and USB microframe (125 µs) scheduling | Round-trip latency notably larger than 2× buffer (often + 1–5 ms) | — |

#### E5.3 PREEMPT_RT question

| Aspect | State at cutoff |
|---|---|
| Mainline status | PREEMPT_RT was **merged into mainline Linux 6.12** (2024) for x86, ARM64 and RISC-V |
| Raspberry Pi kernel | Raspberry Pi kernels for Pi 5 moved to the 6.6 series (and 6.12 later **(uncertain on timing)**). The default kernel config is a non-RT preemption model (`PREEMPT` or `PREEMPT_VOLUNTARY`) **(uncertain which)**. RT kernels require self-building or community builds (still the case in early-2025 user reports for 6.12 on Pi 5 [checked 2026-11]; later Raspberry Pi kernel packaging not re-checked) |
| Pi 5 page size | Default Pi 5 kernel (`kernel_2712.img`) uses **16 KB pages**. Some software assuming 4 KB pages misbehaves (`kernel=kernel8.img` in `config.txt` reverts to 4 KB) |
| Typical evidence | Measured with `cyclictest`. Stock kernels show occasional multi-hundred-µs latencies under stress; RT kernels typically bound worst case to tens of µs **(uncertain; hardware-dependent)** |
| Bela comparison | Bela uses Xenomai (co-kernel), not PREEMPT_RT, and runs audio outside Linux scheduling |

#### E5.4 System tuning knobs

| Item | Mechanism |
|---|---|
| CPU governor | Default `ondemand`/`schedutil` **(uncertain which on Pi OS)**. `performance` pins max clock: `cpupower frequency-set -g performance` or write to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`. Frequency transitions can cause latency spikes |
| RT scheduling | Audio thread `SCHED_FIFO` (priority e.g. 70–95). Requires `rtprio` and `memlock` limits (`/etc/security/limits.d/audio.conf`: `@audio - rtprio 95`, `@audio - memlock unlimited`) and user in `audio` group, or RTKit (PipeWire uses RTKit by default) |
| Memory locking | `mlockall(MCL_CURRENT \| MCL_FUTURE)` to avoid page faults in the RT thread |
| IRQ priorities | With threaded IRQs (RT kernel), raise the USB (xHCI on RP1) IRQ thread priority (e.g. with `rtirq` scripts) |
| CPU isolation | `isolcpus=`/`nohz_full=` kernel parameters, `taskset`/affinity to pin the audio thread to a dedicated core |
| Throttling / thermal | Pi 5 throttles at ~85 °C (soft limit ~80 °C **(uncertain)**). Active Cooler or a case fan is common. `vcgencmd get_throttled` reports throttling/undervoltage |
| Power | Official 27 W (5 V / 5 A) USB-C PSU. With a 3 A supply, USB peripheral current is limited (~600 mA total) unless overridden (`usb_max_current_enable=1`) |
| Wi-Fi / Bluetooth | Power-saving and firmware activity linked to latency spikes in reports **(uncertain)**. Disabling via `dtoverlay=disable-wifi`/`disable-bt` is common practice |
| GUI load | Desktop compositor (Wayland/labwc or Wayfire on Bookworm) and GPU-accelerated Electron/Chromium rendering compete for CPU/memory bandwidth |

#### E5.5 USB audio class compliance and Pi 5 pitfalls

| Topic | Notes |
|---|---|
| UAC1 / UAC2 | Linux `snd-usb-audio` supports class-compliant UAC1 and UAC2 (no vendor driver needed). UAC2 needed for >48 kHz / >2 ch at low latency on many devices. Vendor-specific mixer/DSP features often not exposed |
| Implicit feedback | Some devices use implicit feedback sync. Historical quirks caused glitches. Kernel quirk tables handle many devices |
| USB on Pi 5 | USB handled by the RP1 chip over PCIe (2× USB 3.0 + 2× USB 2.0 controllers). Generally better USB throughput than Pi 4 |
| No analog jack | Pi 5 has no 3.5 mm output. HDMI audio has high and variable latency. I2S DAC HATs or USB interfaces needed |
| I2S HATs | Use device-tree overlays (`dtoverlay=hifiberry-dacplus`, `iqaudio-codec`, etc.). Some overlays needed RP1-specific updates early in Pi 5's life **(uncertain)**. HAT codecs are often 24/32-bit, up to 192 kHz |
| PipeWire quantum surprises | Graph quantum may change dynamically (`clock.min-quantum`, `clock.force-quantum` settings) |
| 16 KB pages | Affects some binaries (e.g. older Electron/Chromium builds, jemalloc users, Wine) **(uncertain on which Electron versions)** |
| Electron on ARM64 | Official arm64 Linux builds exist. GPU acceleration on V3D (Mesa) varies by version **(uncertain)** |

---

### E6. Windows audio

#### E6.1 APIs and drivers

| API / driver | Description | Typical latency (output buffer) | Notes |
|---|---|---|---|
| **WASAPI shared** | Windows Audio Session API through the audio engine (mixing, SRC, APOs) | Default engine period ~10 ms. With `IAudioClient3` (Win10+) and supporting drivers: down to ~2.67 ms (128 frames @ 48 kHz) or lower **(uncertain on minimum)** | App must match the engine mix format (or use autoconvert). System effects (APOs) may add latency |
| **WASAPI exclusive** | Bypasses the mixer; app owns the device | ~3 ms typical. Driver-dependent minimum period (often 2–3 ms; some lower) | Event-driven or timer-driven modes. Other apps lose access. Format must be exactly supported by the device |
| **ASIO** | Steinberg's driver model; vendor-supplied driver talks directly to hardware | 1–10 ms common (e.g. 32–256 frames). Pro interfaces often lower | Single-client for most drivers (one app at a time; some vendor drivers are multi-client). Since October 2025 the ASIO SDK is offered under GPLv3 alongside the proprietary licence; before that it was proprietary only, which kept it out of most open-source hosts [checked 2026-11] [R11] |
| **FlexASIO** (Etienne Dechamps) | Universal ASIO driver built on PortAudio, wrapping WASAPI (shared/exclusive), WDM-KS, MME, DirectSound | Depends on the backend chosen. Configured via TOML file (`FlexASIO.toml`) | Open source (MIT **(uncertain)**). No GUI control panel by default (FlexASIO GUI is a third-party tool) |
| **ASIO4ALL** (Michael Tippach) | Universal ASIO driver over WDM Kernel Streaming | Often 5–10 ms achievable on onboard audio | Freeware, closed source. Takes exclusive control of the device via KS. Can conflict with other apps |
| **WDM-KS** | Kernel Streaming direct access | Low | Used via PortAudio etc. Fragile across drivers |
| **MME / DirectSound** | Legacy APIs | 20–100+ ms | Highest latency. Broadly compatible |

#### E6.2 Typical failure modes

| Failure mode | Description |
|---|---|
| DPC/ISR latency | Drivers (network, GPU, ACPI, storage, Wi-Fi) holding CPU in DPCs cause dropouts. Diagnosed with **LatencyMon** (Resplendence) |
| Power management | CPU C-states, core parking, "Balanced" power plan, Intel SpeedStep/AMD CPPC frequency changes. USB selective suspend causing device dropouts |
| Exclusive-mode conflicts | Device "in use" errors when another app holds exclusive WASAPI/ASIO/ASIO4ALL |
| Sample-rate mismatch | Device rate (in Sound control panel) vs app rate. Exclusive mode fails if unsupported. Shared mode needs resampling |
| Bluetooth audio | High latency (often 100–200+ ms), codec-dependent. Unsuitable for live monitoring |
| Driver clock drift | Separate input/output devices without shared clock → drift, requiring resampling or periodic glitches |
| MMCSS | Audio threads should register with the Multimedia Class Scheduler Service (`AvSetMmThreadCharacteristics("Pro Audio")`) for priority boosting. Without it, background load can starve audio |
| Thread priority inversion | Locks shared between UI/audio threads |
| Antivirus / indexing | Disk/CPU spikes on first load or sample streaming |
| Vendor ASIO quirks | Buffer-size changes requiring driver reset (`kAsioResetRequest`). Buffer sizes restricted to specific values. Device disconnection handling |

#### E6.3 Common cross-platform host libraries (context)

| Library | Backends on Windows | Licence |
|---|---|---|
| PortAudio | MME, DirectSound, WASAPI, WDM-KS, ASIO (with SDK) | MIT-style |
| RtAudio | WASAPI, DirectSound, ASIO | MIT-style |
| miniaudio | WASAPI, DirectSound, WinMM | Public domain / MIT-0 |
| JUCE | WASAPI, DirectSound, ASIO | AGPLv3 / commercial (JUCE 8) **(uncertain on exact licence version)** |

---

### E7. Benchmarking practice for audio software

#### E7.1 How DSP load is measured

| Metric | Definition | Where used |
|---|---|---|
| **DSP load (callback load)** | `time spent in audio callback / buffer period` (e.g. 1.0 ms used of a 2.67 ms period = 37.5%) | JACK "DSP load", Ableton/Reaper/Bitwig meters (variants), VCV Rack engine meter |
| **Peak vs average load** | Max over a window vs mean. Dropouts depend on peaks | Most DAWs show smoothed average and/or peak |
| **Per-module/plugin time** | Time per `process` call per module | VCV Rack (per-module CPU meter, % of sample time), Reaper performance meter (per FX), Bitwig/others |
| **OS CPU %** | Fraction of total CPU time used by the process (all threads), often normalised to all cores (Windows Task Manager) or per core (`top`: 100% = one core) | Task Manager, `top`/`htop` |
| **Offline throughput** | Seconds of audio rendered per second of wall time ("× realtime") | Offline renderers, benchmark harnesses |

#### E7.2 Why CPU % differs between tools

| Reason | Explanation |
|---|---|
| Normalisation | Per-core vs all-cores percentages (e.g. 100% on a 4-core Pi = 25% of total) |
| Time base | Callback load measures only the RT callback. OS CPU % includes UI, GC (Electron/V8), IPC, idle spinning |
| Frequency scaling | Same work = higher % at lower clock. Governors change clock dynamically |
| Spin-waiting | Some engines busy-wait (multi-threaded DAW engines). Inflates OS CPU % without real DSP work |
| Measurement window | Averages over 0.5–1 s hide spikes. Peak meters reflect worst blocks |
| Block size dependence | Per-block overhead (function calls, cache misses) is amortised differently at 32 vs 512 frames |
| Multi-threading | Parallel graphs reduce wall time but the sum of CPU time may rise |
| Hyper-threading / SMT | Logical vs physical cores (Windows desktop CPUs. Pi 5 has no SMT) |
| Timer resolution | Low-resolution timers distort short-callback measurements. Use `clock_gettime(CLOCK_MONOTONIC)` / `QueryPerformanceCounter` / cycle counters (DWT CYCCNT on Cortex-M7) |

#### E7.3 Xrun counting

| Platform / API | Mechanism |
|---|---|
| ALSA | `snd_pcm_writei/readi` returns `-EPIPE` (underrun/overrun). `snd_pcm_status` (state XRUN). Count recoveries |
| JACK | `jack_set_xrun_callback`. `jack_get_xrun_delayed_usecs`. Server logs |
| PipeWire | `pw-top` shows per-node ERR counts and quantum/rate/busy times. `pw-profiler` |
| Windows WASAPI | Glitches inferred from `GetCurrentPadding`/timestamps (`IAudioClock`) or `AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY` on capture. No universal xrun counter |
| ASIO | No standard xrun API. Hosts infer from late `bufferSwitch` calls/timestamps (`ASIOTime`). Some drivers report via `kAsioResyncRequest` |
| Embedded (Daisy etc.) | Measure callback duration with a cycle counter (DWT) or GPIO toggling on a scope. Overruns detected when the callback exceeds the block period |
| Self-instrumentation | Compare callback start timestamps with expected period. Record histograms of callback duration and lateness |

#### E7.4 Round-trip latency measurement

| Method | Description |
|---|---|
| Physical loopback | Cable from output to input of the same interface. Send an impulse/click or MLS/sine sweep. Cross-correlate input with output to find the delay in samples |
| `jack_iodelay` | JACK tool: measures loopback latency via phase of test tones. Reports frames/ms and suggested `-I/-O` latency compensation |
| `alsa_delay` (zita-alsa-pcmi tools) | ALSA-level round-trip measurement **(uncertain on exact tool name/package)** |
| Oblique Audio **RTL Utility** | Windows/macOS round-trip latency tester (ASIO/Core Audio) |
| Scope method | Oscilloscope on analog input vs output (or GPIO pulse vs audio output) for embedded targets |
| Reported vs measured | Driver-reported latency often excludes converter (ADC/DAC filter) delay and USB safety buffers. Measured RTL is typically larger than `2 × buffer` |

#### E7.5 Fair cross-tool comparison methods

| Practice | Description |
|---|---|
| Identical patch/workload | Same oscillators, filters, voice count, modulation. Equivalent algorithms where possible (e.g. polyBLEP vs polyBLEP) |
| Identical audio settings | Same sample rate, buffer size, period count, bit depth, device/driver |
| Fixed CPU frequency | `performance` governor (Linux) / High Performance plan (Windows). Disable turbo/boost for repeatability. Monitor thermals/throttling |
| Warm-up | Discard initial seconds (JIT, cache warm-up, page faults, lazy init) |
| Long runs and distributions | Record many blocks. Report mean, median, p95/p99/p99.9, max callback time and xrun count rather than a single average |
| Headroom test | Increase instance/voice count until first xrun ("max instances before dropout") |
| Offline vs realtime | Separate pure DSP throughput (offline render) from realtime scheduling performance |
| Isolation | Close background apps. Pin threads/cores. Same OS image and kernel. Document versions/build flags (`-O2/-O3`, `-ffast-math`, `-march`) |
| Same measurement method | Measure with an external harness (callback timestamps or `perf`) rather than each tool's internal meter, since meters define load differently |
| Bit-exactness/quality | Compare outputs (null test, aliasing measurement with FFT) alongside speed, so cheaper-but-worse algorithms are visible |

---

### E8. Open questions (things not stated with confidence)

| # | Topic | Open question |
|---|---|---|
| 1 | Daisy Seed codec revisions | Exact mapping of codec chip (AK4556 / WM8731 / PCM3060) to board revisions, and current production version |
| 2 | Teensy 4.1 PSRAM | Maximum supported external PSRAM (8 vs 16 MB) and speed |
| 3 | ESP32-S3 | Maximum PSRAM/flash configurations, FPU subnormal behaviour, PIE SIMD usefulness for float DSP |
| 4 | Ksoloti | Exact MCU clock, SRAM/flash sizes and SDRAM variants |
| 5 | Organelle | Exact SoC/codec for original vs M models, key count, `mother.pd` receive names, OS licence |
| 6 | Bela | Exact licence of Bela core software and hardware. Status of newer Bela variants (e.g. "Bela Gem") |
| 7 | gen~ export licence | Current commercial terms for gen~-exported code used via Oopsy **[Answered: R12]** |
| 8 | RNBO licence | Current terms and revenue thresholds for exported code. Any official/third-party Daisy target **[Answered: R12; Daisy target not checked]** |
| 9 | hvcc | Current support status of `expr`/`expr~`, `clone` and other objects in the latest Wasted-Audio release. Exact licence of generated code **[Partly answered: R14]** |
| 10 | Faust licence | Whether the compiler is now LGPL vs GPL in current releases **[Answered: R13]** |
| 11 | VST3 / ASIO SDK licences | Whether Steinberg changed VST3 SDK and ASIO SDK licensing after the cutoff (announcements of more permissive terms are possible) **[Answered: R11]** |
| 12 | VCV Rack licensing | Exact terms of commercial/non-GPL plugin licensing under Rack 2 |
| 13 | Pd64 ABI | Exact file-extension conventions and compatibility of double-precision Pd externals |
| 14 | Raspberry Pi kernel | Default preemption model in current Raspberry Pi OS kernels. Availability of official RT kernel packages after mainline PREEMPT_RT (6.12) **[Partly answered: §E5.3]** |
| 15 | Pi 5 thermal thresholds | Exact soft/hard throttle temperatures and fan curve defaults |
| 16 | Pi 5 + Electron | Compatibility of current Electron arm64 builds with 16 KB page kernels and V3D GPU acceleration |
| 17 | Pi 5 I2S HATs | Which overlays required RP1-specific updates and their current status |
| 18 | WASAPI low-latency shared mode | Minimum period achievable with common drivers via `IAudioClient3` |
| 19 | FlexASIO | Exact licence |
| 20 | Cortex-M denormals | Whether Cortex-M4F/M7/M33 FPUs incur any subnormal penalty |
| 21 | `-ffast-math` and threads | Whether FTZ/DAZ set by `crtfastmath.o` applies to threads created later (inheritance of MXCSR) on each OS **[Moot for Wirescape: engine2 sets the FP mode itself on each render call, X1]** |
| 22 | Filter literature dates | Exact years/venues for later Huovilainen/Välimäki/D'Angelo ladder papers |
| 23 | DaisySP contents | Exact current list of DaisySP reverb/effect modules and which moved to DaisySP-LGPL |
| 24 | Axoloti execution order | Exact rule by which object execution order is derived from patch layout |
| 25 | Stable buffer sizes on Pi 5 | Real measured xrun-free buffer sizes for specific USB interfaces, kernels and loads. No measured data is available here |

### E9. Review addition: where this background meets the Wirescape code

Added in review. Each row points from a background topic to the part of this document that says what Wirescape actually does.

| Background topic | What the Wirescape code does | See |
|---|---|---|
| Denormal modes (§E4.4: x86 FTZ bit 15 / DAZ bit 6, AArch64 FPCR.FZ bit 24, set per thread) | engine2 sets exactly these bits at the start of every render call and restores them afterwards, on whichever thread renders | X1 |
| Parameter smoothing (§E4.3) | Base changes ramp linearly for 5 ms in normalized space; cable modulation is unsmoothed | X2 |
| Delay interpolation (§E4.5) | fx.delay reads with 4-point Hermite and caps read speed at 0.5 samples/sample; fx.reverb uses linear taps | §C2.1, §C2.2 |
| Reverb structures (§E4.6) | fx.reverb is an 8-line Hadamard FDN with Schroeder allpass input diffusion and one damping coefficient for all lines | §C2.2 |
| Filters (§E4.2) | VCF is a linear ZDF TPT 4-pole; Ladder uses one-sample-delayed feedback with a tanh drive stage; Quad VCA's LPG uses a TPT SVF | §C1.6, §C1.7, §C1.13 |
| Band-limited oscillators (§E4.1) | VCO and LFO are sine only; CHAOS uses naive saw/square; Macro Oscillator wraps Plaits | §C1.1, §C1.2, §C1.5 |
| Click-free patch changes (§E4.7) | The sidecar's D5 path fades out, swaps at a block boundary and fades in; live replan fades out one block before parking and fades in after | §B6b, §A2.3 |
| Pi 5 buffer sizes (§E5.2) | `setBufferFrames` accepts 64, 128, 256, 512 or 1024; the author guide's reference workload is 48 kHz / 128 frames | §B1a, §D3.5 |
| Windows MMCSS (§E6.2) | The null-audio sink thread registers for MMCSS "Pro Audio"; the PortAudio stream's thread setup is not visible | §B5a |
| ASIO (§E6.1) | The sidecar enumerates ASIO drivers and handles ASIO-forced buffer sizes. (inf) With the ASIO SDK now offered under GPLv3, it can be combined with engine2's GPL-3.0-only code | §B3c, §B6b, R11 |
| Patch-to-firmware pipelines (§E2) | Part D §D6 lists what Wirescape has and lacks for such a compiler | §D6 |
| Benchmarking (§E7) | The author guide's Pi evidence: two CHAOS instances, worst block 489,275 ns at 48 kHz / 128 frames, against a 1,333 µs bound | §D6.1, §D3.5 |

### E10. Sources checked in review (November 2026)

| Fact | Source |
|---|---|
| VST 3.8 SDK under MIT (29 Oct 2025) | Steinberg press release, https://ocl-steinberg-live.steinberg.net/_storage/asset/819253/storage/master/Press%20Release%20-%202025-10-29%20-%20VST%203.8%20-%20EN.pdf ; VST 3 licensing FAQ, https://steinbergmedia.github.io/vst3_dev_portal/pages/FAQ/Licensing.html |
| ASIO SDK adds a GPLv3 option (Oct 2025) | CDM, https://cdm.link/open-steinberg-vst3-and-asio/ ; heise, https://heise.de/-10963451 |
| gen~ export licence terms | Cycling '74 Gen Code Export Licensing FAQ, https://support.cycling74.com/hc/en-us/articles/360050779193-Gen-Code-Export-Licensing-FAQ |
| RNBO export licence terms | Cycling '74 RNBO Export Licensing FAQ, https://support.cycling74.com/hc/en-us/articles/10730637742483 |
| Oopsy licence | https://github.com/infrasonicaudio/oopsy |
| Faust licences | Debian copyright for Faust 2.77 / 2.79, https://sources.debian.org/src/faust/2.79.3%2Bds-2/debian/copyright ; Faust FAQ, https://faustdoc.grame.fr/manual/faq |
| hvcc licences | Debian copyright for hvcc, https://metadata.ftp-master.debian.org/changelogs/main/h/hvcc/testing_copyright |
| hvcc `expr`/`expr~` in v0.15.0 | Wasted Audio announcement (mirror of their Bluesky feed), https://bushdrum.com/bsky/wasted.audio |
| PREEMPT_RT in mainline 6.12; Pi 5 mainline support | https://itsfoss.com/news/linux-kernel-6-12/ |
| Pi 5 RT kernels still self-built (Jan 2025) | LinuxCNC forum, https://forum.linuxcnc.org/9-installing-linuxcnc/54969-rpi-5-with-6-12-preempt-rt-using-posix-non-realtime |

---

## Still open after v0.2

These items need source files that none of the six packs contain, or that pack D contains but was not supplied with its responses.

| Item | Needed for | Where it should be |
|---|---|---|
| Does the SDK wrapper call `reset()` after `prepare()`? | X5, C2-Q5 (highest priority: decides whether reverb and four other modules can start from uninitialized memory) | `wirescape_sdk.h` around SDK:200-210 (pack D) |
| `ws::Block::split` event semantics | C1-Q14 | `wirescape_sdk.h` SDK:128-132 (pack D) |
| PortRamp time constant, restart and NaN behaviour | C1-Q2, C1-Q3, C2-Q3 | `native/modules2/port_state.h` (no pack) |
| Comb, coupler and drift internals | C1-Q33 | `comb_body.h`, `coupler.h`, `drift.h` (no pack) |
| Spectral FFT size and cost | C2-Q21 | `spectral/fft.h`, `approx.h` (no pack) |
| Groove config, OSC Out config, voice allocator | C2-Q33, C2-Q39, C2-Q40 | `groove/config.h`, `osc_out/config.h`, `native/voice/note_to_cv.h` (no pack) |
| Full module catalogue (for the X15 duplicate-`legacy_index` check) | X15 | `native/control/module_catalog.inc` (no pack) |
| Sidecar control loop and `main()` | B-Q14, B-Q16, B-Q38 | not in any pack |
