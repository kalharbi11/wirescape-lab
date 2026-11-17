<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0013 — Portability: one module source for the app, plugins and hardware (design note)

**Author:** Fable · **Date:** 2026-11-16 (ET) · **Status:** design. Section 2 lists what the
format, the modules, the patch and the protocol must guarantee from now on. Section 8 lists
what can start now. The compiler and the build page are designed far enough to protect them;
their contracts come later.
**Rests on:** `docs/context/OWNER_WANTS.md:37–63`, `CONSTRAINTS.md:21`, `0012`,
`docs/specs/EMBEDDED_PORTABILITY.md`, `facts/repo/cortex-m7/`, `facts/perf/*/module_cpu.json`,
`facts/compare/export_pipelines.md`, `sdk_shape.md`, `performance.md`,
`native/engine2/engine2.cpp` as read on `ef3e0fe`.

## 1. Decisions

- **Q1. The engine is not ported to hardware.** `FACT_PACK.md:875` left this open. The engine
  (dynamic graph, rings, `std::vector`, edits while playing) stays a desktop and plugin
  component. Firmware runs a **compiled patch**: generated code that calls each module's
  `process` in a fixed order over buffers assigned at build time.
- **Q2. One planner.** The step that turns a patch into an ordered plan is taken out of
  `engine2.cpp` into one function. The engine loader runs it at load; the compiler runs it at
  build time. Its output is the **patch plan** (section 4, `0004` T6.1).
- **Q3. One copy of the host arithmetic.** Parameter smoothing, the modulation sum, tapers,
  poly rules, unpatched values and the feedback delay are today inside `engine2.cpp`
  (`:604–617`, `:527`, `:883`). They move into a small portable library, `wire/rt`, that
  the engine and the generated code both call. Without this the compiled patch would be a
  second implementation that drifts.
- **Q4. The compiler is tested without a device.** Generated code built for the desktop and
  run on the null device must produce output **bit-identical** to the engine rendering the
  same patch on the same platform, for every patch the compiler accepts. This is the
  compiler's golden gate. A hardware run is the owner's, later.
- **Q5. Strict first.** The compiler accepts portable-tier modules only, a fixed channel
  count and no edits. Everything else is refused with the module and the reason. Nothing is
  dropped silently (`EMBEDDED_PORTABILITY.md:26`).
- **Q6. One control surface.** A patch may carry a list of controls bound to parameters. The
  build page writes it, the hardware compiler maps it to pins, and a patch-as-plugin exposes
  it as plugin parameters. One list, three uses (section 6).

## 2. Guarantees from now on

Each line is a rule for every later contract. A PR that breaks one is a High finding.

**Module format (`0012`)**
- **F1** A portable module reaches the outside world only through `process` arguments, bound
  ports and services. It includes no engine, app or operating-system header.
- **F2** All memory is declared before `prepare` and allocated by the host. `FAST` and `LARGE`
  keep their meaning: internal RAM and the large arena.
- **F3** A module works at any block size from 1 to the prepared maximum and at any rate from
  32 to 96 kHz, and keeps no mutable global state.
- **F4** The channel maximum is a build-time constant, `WIRE_MAX_CHANNELS` (16 on desktop). No
  module writes the literal 16 for a per-voice array. Firmware builds with 1 to 8.
- **F5** Data, config and tables are plain structs described by field tables, so the same
  packer runs on the desktop at load and in the compiler at build time. `fill` functions for
  tables are pure: same key, same bytes.
- **F6** Parameters are plain-unit floats with string IDs that never change after release (an
  alias table covers renames, `0004` T3.7). A hardware knob sets the base value; a CV input is
  a modulation edge with an amount (`ABI2_PLAN.md:127`).
- **F7** Random behaviour uses the seed from `prepare` only (`ABI2_SPEC.md:77`).

**Basic modules**
- **B1** A basic module is portable tier, has no config, no data slot and no capability, and
  its `module.cpp` holds its arithmetic and its declarations. `0004` T3.5 is done when the
  stock basic modules have this shape.
- **B2** A basic module's cost and memory are in a facts file per target before any budget
  cites them (section 8, S2). Until then the compiler prints "unverified".

**Patch format**
- **D1** Sound and layout stay separate. Everything the engine needs is outside `ui`; nothing
  under `ui` or `surface` changes the rendered audio on the desktop.
- **D2** Execution order depends only on module instance IDs and edges, never on file order,
  map iteration order, pointers or the platform (`engine2.cpp:370–417` does this today).
- **D3** Numbers are finite JSON numbers that convert to `float` the same way on every
  platform. The plan stores each as the 32-bit pattern.
- **D4** A patch names each module by type ID and `version`. A build bundle adds the source
  hash of each module. A patch never names a device, a path or a host.
- **D5** New top-level sections are additive and unknown ones are preserved, as today.

**Protocol (`0010`, M5)**
- **R1** Commands fall into three groups by capability: *engine* (graph, parameters, data,
  transport, telemetry), *host* (audio and MIDI devices, rates, buffers) and *desktop*
  (files, dialogs, settings). A host that answers `hello` with the engine group alone is a
  valid peer. No engine-group command carries a path or a device name.
- **R2** The catalogue in `hello` is generated from descriptors and carries tier and
  capabilities, so a client can tell what a target accepts before it asks.

## 3. Three hosts

| | Desktop app | CLAP plugin | Daisy-class firmware |
|---|---|---|---|
| Graph | engine, edited live | one module (first), or the engine inside the plugin (later) | compiled patch, fixed |
| Memory | host arena | host arena | `FAST` in internal RAM, `LARGE` in SDRAM |
| `audio.in` / `audio.out` | device channels | plugin audio ports | codec |
| `midi.in`, `notes.in` | devices, screen keyboard | plugin events | UART or USB MIDI, keys |
| `message.*`, `stream.out` | OSC, files | refused | refused |
| Parameters | protocol | plugin parameters | controls on pins |
| Telemetry | to panels | to the plugin window (later) | no-op |
| Tables | filled at load, shared | the same | filled at build time, in flash |

**Single-module CLAP adapter (T3.11).** Parameters map one to one; the plugin parameter ID is
the 32-bit FNV-1a hash of the string ID, which is why F6 matters. Signal ports become audio
ports, with `stereo_pair` making a stereo port. Poly outputs are summed. Notes and MIDI arrive
on the bound event ports. State is `save_state`. Latency is `latency_frames`.

## 4. The patch plan (T6.1)

A flat, ordered, typed description. One canonical JSON file: keys sorted, no insignificant
whitespace, floats as 8 hex digits, bytes as hex. Same patch, same module manifests and same
build settings give the same bytes on every platform; its SHA-256 names the build.

| Section | Holds |
|---|---|
| `settings` | sample rate, block size, channel maximum, feedback block, seed: the build's values, not the patch's hints |
| `modules` | in execution order: instance ID, type, version, source hash, tier, packed config, packed data blocks, parameter base values, memory (`fast`, `large`), latency |
| `buffers` | every signal buffer with its index, channel count and constant flag |
| `edges` | resolved to port and buffer indices; modulation edges with amount; feedback edges with their delay |
| `bound` | each bound port and the host endpoint it asks for |
| `tables` | each required table: key, size, content hash |
| `surface` | controls resolved to parameter indices (section 6) |
| `refusals` | empty for a valid plan; otherwise module, rule and plain reason |

The engine builds its layout from the same plan (after M4 this is the immutable `Layout` of
`0005` §5, so the plan is its serial form). The order is today's order: T6.1 changes no sound
and its gate is golden 24 identical plus plan hashes equal on three platforms.

## 5. The compiler (T6.2)

Input: a plan and a board file. Output: a folder holding generated C++ (`patch.cpp`: static
buffers, module instances, the schedule), the pinned module sources, `wire/rt`, a board
adapter, a build file and `manifest.json` with every hash and the toolchain version. No
timestamp or path is written, so two runs give identical folders.

Refusal rules, each with the module and a plain sentence:
1. a desktop-tier module, or a capability the board does not provide;
2. a channel count above the board's maximum, or a poly cable the fixed count cannot serve;
3. memory: the sum of `fast` over internal RAM, or `large` over the arena, from the plan;
4. code size over the board's flash, from the built object sizes;
5. a surface control with no free compatible pin;
6. a module version or source hash that differs from the plan's.

CPU is reported against the block period from the per-target cost table. It becomes a
refusal only once that table holds measured rows (B2).

Checks in CI: the generated folder builds with the pinned `arm-none-eabi` toolchain
(build only); the desktop build of the same generated code meets Q4.

## 6. The control surface and the build page (T6.3)

```json
"surface": { "controls": [
  { "n": 1, "kind": "knob", "label": "Cutoff", "module": 4, "param": "cutoff",
    "min": 80, "max": 8000, "taper": "log" } ] }
```

- Kinds: `knob`, `slider`, `button`, `switch`, `trigger`, `cv_in`, `gate_in`, `led`, `cv_out`.
  A control targets one parameter (or, for `led` and `cv_out`, one output port).
- **Board file** (`boards/<id>.json`): chip, RAM and flash sizes, codec channels, and a list
  of pins in a fixed order with what each can do (analogue in, digital, DAC, PWM).
- **Pin assignment is a pure function:** controls in order of `n`; each takes the first free
  pin in board-file order that can serve its kind. The same patch and board always give the
  same pins. A manual pin on a control overrides and is checked.
- **Wiring guide:** generated text and a table from per-kind templates in the board file
  (a pot is three wires: 3V3, the pin, ground). No drawing tool is needed for a first version.
- The build page is a Studio view that edits `surface`, picks a board, calls the compiler
  and shows pins, refusals and the guide. It adds no engine code.
- In a patch-as-plugin the same controls are the plugin's parameters, in order of `n`.

## 7. What this costs and what it does not solve

- Q3 is an engine refactor in the render path. It follows M4 E4b and carries the M4 rules:
  golden identical, instruction counts within 1 %.
- A compiled patch has no edits, no undo and no polyphony above the fixed count. That is the
  strict first version the owner asked for.
- Double-precision maths in modules is allowed (`0012` §8.5) and may be slow on hardware.
- Sub-patches, samples from files and panels on hardware are not designed here.

## 8. What can start now

Class A facts tasks; the lead may file them under SR18. None touches product code.

| ID | Task | Output |
|---|---|---|
| S1 | Dump the execution order of the 24 bundled patches on three platforms and compare hashes (D2) | `facts/code/plan_order.md` |
| S2 | Extend the Cortex-M7 probe: per module, the names of double and soft-float symbols on `fpv5-d16`; `sizeof` the instance and `memory_requirements` at 48 kHz for 1 and 8 channels | `facts/repo/cortex-m7/`, `facts/repo/module_memory.md` |
| S3 | Count per-voice arrays written with the literal 16 (F4) | `facts/code/channel_literals.md` |
| S4 | Group every protocol command as engine, host or desktop, with any path or device field it carries (R1) | `facts/code/protocol_groups.md` |
| S5 | Daisy Seed board facts from the libDaisy source at a pinned commit: pins and functions, RAM, flash, codec, licence | `facts/compare/daisy_seed_board.md` |
| S6 | CLAP facts at a pinned version: the required entry and extensions for an instrument and an effect, licence | `facts/compare/clap_minimum.md` |

After M3 MB2 and `0004` T3.5 (contract M10): the two build-only adapters (T3.11), then
`wire/rt` and the planner (T6.1), then the compiler (T6.2), then the build page (T6.3).

## 9. Assumptions, and what would overturn them

- **A1** The engine's order is already platform-independent. S1 tests it; a hash difference
  is a defect to fix before T6.1, not a reason to change the rule.
- **A2** The host arithmetic can be separated without a cost above 1 %. If it cannot, the
  generated code keeps calling the engine's own inner functions compiled for the target, and
  Q3 becomes "one source file, two builds".
- **A3** Bit-identical desktop output (Q4) is reachable because both sides call the same
  modules and the same `wire/rt` in the same order. If compiler flags break it, the gate
  becomes identical on one named platform; it never becomes a tolerance without Fable.
- **A4** The Daisy Seed's flash and RAM (S5) hold a useful patch. If internal flash is too
  small for more than a few modules, the first board file targets the bootloader layout.

Signed: Fable, 2026-11-16
