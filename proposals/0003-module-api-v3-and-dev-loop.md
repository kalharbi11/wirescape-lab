<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0003 — Module API v3, the developer loop and module tools (design note)

**Author:** Fable · **Date:** 2026-11-15 (ET) · **Status:** design, for the owner to read; details settle as
Phase 1–3 are built · **Rests on:** `proposals/0001-audit.md` §1, §5, §7; owner decisions in `0002`
(D2, D8, items 2–3); `native/include/wirescape/module2.h`; `facts/code/out_of_tree_trial.md`;
`facts/code/capability_map.md`.

The current interface ("ABI 2") is a sound base: a plain-C descriptor of ports and parameters, host-owned
memory, block processing with sample-accurate events, per-voice channels. v3 keeps that and changes what
the audit found wrong. One break, while no outside modules exist.

## 1. What a module is, after v3

A module is **one folder** that nothing else has to know about:

```
modules/vca/
  module.cpp        the DSP class and one registration line (the only required file)
  panel.json        optional: layout, sections, widget choices, presets (no rebuild to change)
  ui/               optional: custom HTML/JS panel (D7)
  patches/          optional: example patches; also used as the module's listening tests
  README.md
```

There is no `module.json`, no catalogue entry, no CMake edit, no test file to write. The C++ descriptor is
the only description; everything else (Studio catalogue, docs tables, the manifest of a built library) is
generated from it by the build.

## 2. Changes to the interface

| # | Change | Why (audit) |
|---|---|---|
| 1 | Remove `legacy_index`. Parameters are addressed by string ID in patches and by position at run time. | X15: silent misrouting by default; ABI1 residue |
| 2 | Descriptor gains `category`, `tier` (portable / desktop) and `capabilities` (bit set + small records). | core code keyed on module IDs |
| 3 | **Host services by declared capability**, obtained from `ws_host` at `prepare`: MIDI device stream, message bus (OSC), transport, table/sample store, telemetry channel. Today these are wired by module ID in five core files. | §1 "module-specific code in the core" |
| 4 | **Module data, separate from config.** A module may declare typed data blocks (for example a step pattern, a CC map). The host delivers a new block between process calls with one pointer swap; the module keeps playing. Config is left only for things that really change the module's shape (port count). | §2 causes 1–2: editing musical data restarts the module |
| 5 | **State transfer on replace**: optional `adopt(old_instance_state)` so a re-created instance (config change, hot reload) continues phases, tails and held notes; default is `save_state`→`load_state`. | §2 cause 1; D10; developer loop |
| 6 | **Telemetry out**: a module may publish small fixed-size records (per voice or per module) through a lock-free host channel; panels subscribe by name. | GUTTR deviation 12; taps keyed on module IDs |
| 7 | **Smoothing and modulation policy in the port/parameter declaration** (`smooth: none / 5 ms / audio-rate`), applied by the host, also to cable modulation. Modules stop carrying their own ramps unless they need a special one. | §3: unsmoothed modulation, double smoothing |
| 8 | Fixed-width fields only in ABI structs (`uint64_t`, no `size_t`); `float` sample rate alongside `double`. | 32-bit targets |
| 9 | Config schema declared by the module (field names, types, ranges), validated generically. The 375-line per-module adapter in `runtime_module_config.h` goes. | complexity 223 function |
| 10 | Voices: unchanged model (channels, ≤16), plus an opt-in **voice-owner** capability for modules that manage their own voices and groups, with a declared internal voice count for meters and telemetry. | GUTTR |
| 11 | Entry point returns a **list** of descriptors, so one library can hold several modules; a version function stays for the loader. | static-link name clashes |

Not changed: block processing, event structs, port kinds and hints, host allocation, the 16-channel limit.

### What the basic module looks like

The VCA today is 34 lines, of which 5 are arithmetic; the rest handles constant inputs, scratch rows and
SIMD by hand. In v3 the SDK supplies those as helpers, so a basic module is its maths:

```cpp
struct Vca {
    WS_MODULE("vca", "VCA", category::dynamics, tier::portable)
    WS_IN (audio,  "Audio",   hint::audio)
    WS_IN (cv,     "Gain CV", hint::cv_uni, unpatched(1))
    WS_OUT(out,    "Audio",   hint::audio)
    WS_PARAM(gain, "Gain", range(0, 2), initial(1), per_voice, smooth::audio_rate)

    void process(ws::Voices v) {              // called per voice group; constant inputs handled by the SDK
        v.out(out) = v.in(audio) * v.in(cv) * v.param(gain);
    }
};
WS_REGISTER(Vca)
```

The explicit block form (`process(ws::Block&)`) remains for modules that need it. The exact spelling is
decided when it is built; the commitment is: no hand-written scratch management, no duplicated
descriptor, and a portable-tier module uses no heap, no exceptions, no double-precision library calls.

## 3. How a module gets into the app (D8)

- **Drop-in:** the build globs `modules/*/` and any folder listed in `WIRESCAPE_MODULE_DIRS`. Each module
  is its own small library target; a generated registry replaces `module_catalog.inc/.h`. Changing one
  module rebuilds that library only.
- **Desktop:** the engine loads module libraries from a modules directory at start. **"Update library"**
  in Settings (and `wirescape module rescan`) asks the engine to rescan: new modules appear in the
  catalogue; changed ones are swapped (§4). Web, firmware and plugin builds link the same modules
  statically from the same folders.
- **Out of tree:** the SDK folder is self-contained (it carries the header and its own test support), so
  `cmake -S my_module -B build -DWIRESCAPE_SDK=<path>` works anywhere.

## 4. The developer loop

| Level | What you do | What happens | When |
|---|---|---|---|
| 1 | Edit a module, press **Reload engine** | That module's library rebuilds; the engine process restarts and reloads the current patch; the UI stays open | Phase 1–2 |
| 2 | `wirescape module dev <folder>` | Watches the folder; on save: build the library, run the quick tests, and if they pass the running engine swaps the module in place, carrying state with a short crossfade (change 5). On Windows the library is copied to a temporary name before loading. | Phase 3 |
| 3 | Edit `panel.json` or the custom UI | Applied live, no build | Phase 5 |

A failed build or failed quick test leaves the old module playing and shows the error in the app and the
terminal.

**Developer mode in the app** (layers, opening deeper as you click in):
1. *Panel:* layout, names, ranges shown, defaults, presets — live, saved to `panel.json`.
2. *Module:* ports, parameters, capabilities as declared; live meters per voice; telemetry records; CPU per
   block; the last test result; **Build & reload**.
3. *Code:* opens the module folder in the owner's editor; the SDK reference for what is under the cursor
   is a later nicety.

Layer 1 edits never need a rebuild. Parameter *ranges and IDs* live in the C++ descriptor (they are part
of the sound and of saved patches), so changing those is a layer-2 rebuild, which at level 2 takes seconds.

## 5. Module tools

One command with subcommands, usable on a single folder with no test code from the author:

| Command | Does |
|---|---|
| `wirescape module new <id>` | Scaffold a folder from the template |
| `wirescape module check <folder>` | Static checks: descriptor valid, IDs unique and well-formed, ranges sane, tier rules (portable tier: banned includes, no heap/exception/double-libm symbols in the object), licence header. Each failure says what is wrong and how to fix it. |
| `wirescape module test <folder>` | The standard matrix against the built module: sample rates 44.1/48/96 kHz; block sizes 1, 17, 64, 256; 1, 4, 16 voices; reset equals fresh; state round trip; no allocation in process; NaN/Inf in → finite out; denormal decay time; parameter extremes and fast sweeps; block-size independence. Quick mode (default) runs a reduced set in seconds; `--full` runs all. |
| `wirescape module render <folder> [--patch p.json]` | Renders the module alone (test tone, noise or scripted notes into it) or inside a small patch to a WAV, and prints peak, DC, aliasing, click count and CPU per block. Listening and numbers without the app or an audio device. |
| `wirescape module dev <folder>` | Watch mode: build → check → quick test → hot reload (level 2); `--no-app` just re-renders the WAV. |
| `wirescape module bench <folder>` | Cost per sample by voice count, against the block period for a chosen target. |

The matrix and metrics are the same code the lab's own CI uses for the stock modules (issue #51 builds the
metrics), so an author sees what the project's gate sees.

## 6. Order of work and what is deliberately left open

1. Phase 1 removes `legacy_index` from loader paths and gives each module its own library target with a
   generated registry (drop-in at build time; level 1 loop).
2. Phase 2 adds module data (change 4) and state transfer (change 5), because live editing needs them.
3. Phase 3 freezes the v3 header with capabilities and services, adds the loader, tools and level 2.
4. Phase 5 adds telemetry-driven and custom panels and developer mode layers.

Open until built against GUTTR, Macro Oscillator and CHAOS: the exact shape of the voice-owner capability;
whether tables are shared by a host cache or stay per-instance; how a module declares sub-block control
rates. v3 is called stable only after those three are ported.

Signed: Fable, 2026-11-15
