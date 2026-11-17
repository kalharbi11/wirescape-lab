<!-- SPDX-License-Identifier: GPL-3.0-only -->

**0017 errata draft:** `other` is the fallback shelf/display label for an unknown category that must keep loading under 0012. Transport's custom panel uses the 0015 broker API `setTransport`; its panel requires M12 P3 (M11 K3), not a direct native renderer call. Architect approval required.

# 0014 — Module categories, tested against GUTTR, Macro Oscillator and CHAOS (design note)

**Author:** Fable · **Date:** 2026-11-16 (ET) · **Status:** design for `0004` T5.1–T5.4
(contract M11). It also closes the three questions `0003` §6 left open.
**Rests on:** `0012`, `0013`, `facts/code/capability_map.md`, `facts/compare/module_categories.md`,
`docs/context/future_modules/guttur/`, `native/modules2/macro_oscillator/`,
`native/modules2/chaos_lite/`, `docs/design/ports/CHAOS_DECOMPOSITION.md`, `0008`.

## 1. Two kinds of category

- **Shelf** is where a module sits in the browser. It is the descriptor's `category` string.
  Today it lives only in `apps/studio/public/catalogue-presentation.json`; with T3.2 the
  descriptor is the source and that file keeps presentation only.
- **Class** is what a module asks of the format. It is not a field. It follows from what the
  descriptor declares, and it decides which rules and tests apply.

### Shelves (the fixed list)
`oscillator`, `source`, `filter`, `envelope`, `modulation`, `dynamics`, `mixer`, `effect`,
`pitch`, `sequencer`, `timing`, `logic`, `sampler`, `instrument`, `control` (MIDI, OSC,
keyboard), `io`, `display`, `utility`. Today's 17 labels map onto these: Motion and Random
become `modulation`, Two-source and Sound become `effect` or `source` per module, the rest by
name. The mapping is a table in the T3.2 PR; display names stay in the presentation file.

### Classes
| Class | Declares | Extra rules | Examples today |
|---|---|---|---|
| **Basic** | nothing beyond ports and parameters; portable | shape B1 of `0013` | VCA, mixer, slew, scale/offset, noise |
| **Buffered** | `LARGE` memory, maybe latency | memory declared per rate; ring-out on replace | delay, reverb, resonator, spectral |
| **Data-driven** | data slots | reads the slot every block, keeps no copy | Groove, CC to CV, OSC In and Out, chord |
| **Host-bound** | a bound port or a service | tier follows the capability | Output, MIDI In, keyboard, OSC, monitor |
| **Ported library** | `native_rate_hz` or a fixed inner block, third-party code | section 3 | Macro Oscillator |
| **Voice owner** | `VOICE_OWNER`, `internal_voices` | section 2 | GUTTR |
| **Multi-part instrument** | many grouped parameters, presets, stereo out | section 4 | CHAOS |

A module can be in several classes. The module tools pick their tests from the declarations.

## 2. GUTTR: the voice owner

What it is (`guttur/README.md`): one `notes` input, a stereo pair out, 16 internal throats, up
to 8 per note, its own stealing, 37 parameters, tables built at `prepare`, a 128-frame
internal control clock, 120 frames of latency, and a telemetry struct nothing can read today.

| Need | Answer | New in the header? |
|---|---|---|
| Its own voices | `VOICE_OWNER`: the host passes note events through untouched and prepares the module with one channel. `internal_voices` = 16 is shown wherever a voice count is shown | declared in `0012` §7, §9 |
| Voice activity for meters | a voice owner publishes the standard stream `voices`: `{active, max, stolen}` (`LATEST`, per module) | no; a naming rule |
| Its telemetry | one per-module stream for the instance values and one per-voice stream for throat values (`0012` §10); a panel reads them (`0015`) | no |
| Per-voice modulation from outside | note expression events (pitch, pressure, timbre, pan) are the per-voice path. Cable modulation applies to the whole instance, as GUTTR's own contract says (`STATUS.md:27`) | no |
| Tables | `wire.tables`: built once by `fill`, shared between instances, placed in flash by the compiler | `0012` §9 |
| 128-frame control clock | the module's own business. The SDK gives a `ControlClock` helper that carries the remainder across blocks. Block-size independence is already in the test matrix | no |
| Dropping it in | 0 core edits once T3.4 and T3.7 are merged (today: 5 files, `STATUS.md:23`) | no |

**Closed from `0003` §6:** the voice-owner shape is the row above; tables are shared by a host
cache; a sub-block control rate is not declared.
**Not designed:** routing one cable channel to one internal voice. No mapping exists between
cable channels and a voice owner's voices, and GUTTR does not ask for it.

## 3. Macro Oscillator: the ported library

What it is: Mutable Instruments Plaits behind an adapter. 48 kHz only, a 12-frame inner block
with 12 frames of latency, 8 voices, a global random generator isolated per voice, sources
fetched by URL and SHA-256 and pinned in two CMake files.

1. **Rate.** The descriptor says `native_rate_hz = 48000`. The SDK gains a `RateAdapter`: at
   the native rate it is bypassed and the output is bit-identical to today; at any other rate
   it runs the inner code at 48 kHz and resamples, and adds its delay to `latency_frames`.
   Until T5.2 lands, another rate is refused with the module's name, as today.
2. **Inner block.** The 12-frame FIFO becomes the SDK helper `FixedBlock`, so the next
   ported library does not write it again.
3. **Channels.** `max_channels = 8`. The host never offers more; nothing is silently silent.
4. **Third-party pin.** One file in the module folder, `third_party.lock`: name, URL,
   SHA-256, SPDX licence, patch list. Every build target reads that file. A second pin in
   another CMake file is a defect. The build collects the licence texts into the product's
   notices, and the descriptor's `licence` is the combined expression.
5. **Offline builds.** A firmware bundle (`0013` §5) carries the pinned sources by hash; the
   compiler never fetches.
6. **Tier.** Decided by `module check`, not by this note. The `.data` bytes the Cortex-M7
   probe shows are a mutable global; if it stays, the module is desktop tier.

## 4. CHAOS: the multi-part instrument

What it is: two oscillators, a coupler, a comb body, drift, an LFO, a post filter, all in one
module with fixed internal routing chosen by stepped parameters; 27 parameters in 6 panel
sections; 8 presets that exist only in Studio code; 8 voices; a stereo pair.

1. **Sections** are the parameter `group` in the descriptor (`0012` §7). Panels, plugin hosts
   and the build page all get the same grouping; `panel.json` may refine it.
2. **Presets** are files in the module folder, `presets/<name>.json`, each a set of parameter
   values and data in the patch's own spelling. The build lists them in the manifest. Applying
   one is an ordinary batch of parameter edits and one undo step. The preset name is not saved
   in the patch, as today. `modulePresets.ts` is deleted when CHAOS moves (T5.3).
3. **Internal routing stays code.** A stepped parameter that selects a route is enough; the
   format does not describe a module's inside.
4. **One module or a patch?** One module while the parts are not useful alone. When they are,
   the instrument is a sub-patch with a front panel (section 5). CHAOS as shipped stays one
   module. The larger design in `CHAOS_DECOMPOSITION.md` is a sub-patch candidate.
5. **Name.** `essentials.chaos_lite` becomes `chaos` through the alias table (T3.7).
6. **Channels.** `max_channels = 8`.

**Result of the three tests.** GUTTR, Macro Oscillator and CHAOS need nothing beyond `0012`
with the three fields this note added to it (`max_channels`, `native_rate_hz`, parameter
`group`). The header may freeze after T3.2 without waiting for the ports; `0003`'s rule
"stable only after those three are ported" becomes "any field these ports show is missing is
added before the first outside module ships".

## 5. Stock modules that bring a capability

Basic versions. "Engine" is the host work the module needs first.

| Module | Capability | Tier | Basic version | Engine work |
|---|---|---|---|---|
| **Logic and Math** | none | portable | compare, AND / OR / XOR / NOT, min / max, add, multiply, sample and hold, switch; one small module each | none |
| **Stereo Out** | `AUDIO_OUT`, two bound inputs as a stereo pair | portable | level, a device channel pair chosen in data | T3.4 bindings |
| **Bus Send / Bus Return** | none | portable | a named bus in data; the planner turns a send and its returns into ordinary edges | planner only |
| **Transport** | reads transport; its panel calls `setTransport` (`0008`) | portable | bpm, play; outputs clock, reset, run | M3 TR1 |
| **Scope** | `TELEMETRY`, a `BLOCK` stream | portable (no-op on firmware) | two inputs, trigger level, time base; drawn by a panel widget | T3.4 telemetry |
| **MIDI Out** | `MIDI_OUT` bound output | portable | notes and CC from event and CV inputs | a MIDI output path in `io/midi`, tested on a null sink |
| **Wavetable** | `TABLES` | portable | built-in tables by `fill`; position, pitch; user tables as assets | table store |
| **Sampler** | `TABLES`, a `WIRE_F_TABLE` field | portable when the sample fits flash | one-shot and loop, pitch, start, per-voice | table store and the asset loader |
| **Recorder** | `STREAM_OUT` | desktop | records its stereo input to a file the desktop chooses | a file writer fed by a ring |
| **Device bridge** | `MESSAGE_OUT`, `MESSAGE_IN` | desktop | OSC to the LAN with the existing consent flag; serial to a microcontroller | a serial endpoint behind the message binding |
| **Sub-patch** | none; planner | as its contents | a patch used as a module, with In and Out modules and a front panel | its own design note |

- **Assets.** A sample is not stored in the patch JSON (2 MiB cap). The patch names an asset
  by file name and SHA-256; the file sits in a folder beside the patch. The desktop host loads
  it off the audio thread into the table store. A missing or changed asset is reported by
  name and the module plays silence. Paths are never sent to the renderer or put in the patch.
- **Sub-patch** is expanded by the planner into the flat plan, so the engine and the
  compiler never see nesting. Its front panel is the inner patch's `surface` (`0013` §6). It
  needs the 64-module limit raised (`0004` T5.7) and stable instance IDs for the expanded
  modules. That is a design of its own and is **not** contracted from this note.
- **Devices off.** MIDI Out, Recorder and the bridge are tested with null sinks, temporary
  files and loopback only. Real ports are the owner's runs.

**Order:** Logic and Math, Stereo Out and Bus, Transport, Scope, MIDI Out, Wavetable, Sampler,
Recorder, Device bridge. Each is one task; the first four need no new host service beyond T3.4.

## 6. Assumptions, and what would overturn them

- **A1** GUTTR's tables fit a shared immutable table and its `fill` is pure. The byte size is
  not measured; T5.1 starts by filing it.
- **A2** A resampler around Plaits is acceptable in sound at 44.1 and 96 kHz. That is the
  owner's ear; the 48 kHz path is bit-identical by rule.
- **A3** Presets as parameter batches are enough for CHAOS. A preset that must also change
  config would use the replace path of `0005` §7 and would be heard as one.
- **A4** A named bus resolved by the planner covers "Bus". A bus that must be re-routed while
  playing without a graph edit would need a host service instead.

Signed: Fable, 2026-11-16
