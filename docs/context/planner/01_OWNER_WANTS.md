<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Wirescape — owner wants and current decisions (2026-11-26)

Status: owner wants are fixed. Each "Recommended" item is the Claude Architect's suggestion;
the Planner runs (see 02_PLANNER_RUNS.md) make the final decisions.

## A. Standing principles
1. Two products, one engine: **Studio** (full UI, Windows + Pi) for building; **Player**
   (headless, Pi, simple replaceable UI) for playing. Same `wirescape-engine`, same patch files.
2. The headless Player must be very stable and have the functions below. No plan is framed
   around one-off events.
3. Categories, not devices. Hardware adapts to Wirescape. Specific boards and devices appear only
   as guides, presets, example code and test-matrix rows (the M8 is one MIDI device among several).
4. Patches are self-contained: they never need the app, the Player, a script or a preset file.
   Tools may write ordinary patch config; nothing may be required by it.
5. The UI is separate from the Player core and talks only to a documented API.
6. Python never runs inside the engine.
7. Fast module development first; the lab's full rigour applies at promotion.

## B. Wants

### 1. Fast module development — new repo `wirescape-test`
- Loose rules: any agent may merge after a simple review. Kept rules: no secrets, SPDX, a licence
  entry for ports, no Pi runner access.
- Test tiers: **T0** build + module tests + offline render to WAV + NaN/CPU check; **T1** T0 on
  Linux and Windows CI + sanitizers; **T2** the full lab module matrix, run by the owner. Then the
  module is sent to the lab for full CI and Architect review.
- The module folder format matches the lab's `modules/<name>/`, so promotion is a copy.
- Anything outside the module folder (engine, host, SDK, Studio) becomes a lab issue,
  "limitation found". Every module either proves the SDK is enough or names a gap.
- Rewrite `docs/MODULE_BUILD_GUIDE.md` for this two-stage flow (its paths are stale:
  `native/sdk/...` → `sdk/...`, `native/modules2/...` → `modules/...`).
- Found: a new module needs core edits today (`engine/control/module_catalog.h`,
  `engine/CMakeLists.txt:122`). Recommended: unpark CAT-1 #358 / MB1 (the generated module registry from proposal 0009).
  Until then, `wirescape-test` pins the lab and registers the module in a local build only.

### 2. Headless Player — new repo `wirescape-headless`
- Player service: starts and supervises the engine, loads a bundle, switches patches, holds live
  values, runs scripts, reads MIDI/OSC controllers, serves the Player API. Draws nothing.
- Player API: documented, versioned, with a fake player for UI work.
- Reference UI: basic but complete (every menu and parameter), separate and replaceable, for a
  5" 800×480 touch screen. Plus a **UI design guide** to build custom interfaces.
- Bundle: `patches/` (unchanged Studio patches) + `player.json` (setlist, pages, hardware map) +
  `scripts/` + `presets/`. A bundle check runs before copying it to the Pi.
- Sequencers in patches play as-is (they run in the engine). Graphical sequencer editing later;
  skip it if it needs a lot of testing.
- Stability: engine restarts with growing delays and never gives up; it reloads the patch and values;
  a heartbeat detects hangs; UI and script crashes never stop audio; boot to the last bundle;
  systemd watchdog; atomic saves and power-cut safety; switching with no stuck notes; long Pi
  soaks (flat memory, flat CPU in silence, zero OSC drops, #326 closed).
- Patch switching from the UI, a controller or MIDI Program Change.
- Variations: a module's own setting exposed as a control → a sibling patch with a fade → snapshots →
  a variant format only if needed.
- Controllers: any MIDI or OSC device; the owner writes board code. No new controller protocol.
  Feedback (LEDs, servos) through MIDI or OSC out.
- Recommended: the Player service in Python; the reference UI as a kiosk web page, with its cost measured
  on the Pi.

### 3. Macros (global knobs) — the bridge from Studio to headless
- A Macro module: named knobs (e.g. "Knob 1", or anything) → outputs, in pages of 8.
- Each macro maps to any number of parameters, each with its own min/max range (filter 0–100 %,
  resonance 10–50 %).
- A Mappings panel lists the targets with editable ranges. Macro cables are hidden from the canvas.
- Macros live in the patch (they work in Studio too). `player.json` maps physical knobs and menu
  slots to macros or to any raw parameter, like a controller config file. No limit on
  how many are exposed.
- Recommended approach: modulation connections. Studio sets the target base to min and the amount to max − min, and
  greys the target knob. No engine change for linear ranges.
- Open: stepped parameters; curves; whether a range edit is live without a graph rebuild; the
  engine's 32-producer limit.

### 4. Map any parameter without patching (Ableton-style)
- Found (**corrected 2026-11-26**, [0023 §3.1](../../../proposals/0023-review-and-replan.md), checked at
  source; per-parameter table in [`scout/S8_module_params.md`](scout/S8_module_params.md)). The first list
  named 22 modules; 7 of them already have modulatable parameters (clock, function_envelope, ladder,
  mixer, noise, scale_offset, slew). Of the other 15:
  - **8 have parameters, all stepped, none modulatable** (the batch): chord, cv_to_notes, groove,
    host_keyboard, midi_in, midi_to_cv, notes_to_cv, quantizer;
  - **7 have no parameters:** midi_cc_to_cv, monitor, osc_in, osc_out, output, poly_merge, poly_split.
  Mapping by `setParam` does not need the flag (0023 R3.3 rule 4).
- Engine side: mark meaningful parameters modulatable, bit-identical when unmodulated (a module batch).
- Studio side: map mode (click Map, click a parameter, move a CC, OSC address or macro). The helper
  CC/MIDI modules are hidden "mapping" nodes, listed in the Mappings panel. Shared with macros.

### 5. Envelopes and trigger tools
- All envelopes accept triggers. ADSR already has Gate/Trigger mode with hold; add it to Function
  Envelope (gate-only today).
- A `delay` parameter on envelopes (DAHDSR: it pushes the attack start), default 0, appended.
- Gate/trigger delay module (#329, implemented on its branch) stays.

### 6. Clock-synced random and rhythm
- Exists: LFO (sine; tempo sync with continuous beats 0.125–16), Clock (BPM, ticks/beat,
  transport sync), Groove divisions. No shipped random/S&H, divider or multiplier.
- Random module: stepped and smooth, a musical division selector (4 bars … 1/32, dotted, triplet),
  depth, slew, trigger-to-step, seed.
- Clock Div/Mult module.
- Then a multi-output rhythmic modulator (a Pamela's-New-Workout-like function set, original design): per
  output division, shape, width, phase, probability, Euclidean, delay.
- Optional: a division selector and more shapes on the LFO (appended parameters).

### 7. OSC In and Out modules
- Simplest naming: `/ws/<name>` and `/ws/<name>/<n>` for poly (the number must be last). Notes are
  MIDI numbers 0–127; values 0–1; gates 1/0; triggers take no value.
- OSC In: a **message indicator** dot per row (green on receive, grey off, amber timed out, red port or
  LAN refused), counted on the OSC network thread; a **label box** per row, shown as the output name
  (optional `label` key, kept on save); a **quick cv/gate/trigger toggle** in the row list;
  a **generic default** (replace the `/pico1/knob/*` default; Pico and TouchOSC become presets);
  user **presets** (OB-h5 #603).
- **Script auto-sync**: a script declares its outputs, and the linked OSC In rows update automatically
  (label, kind, range, address). Rows are matched by name so cables never jump; removed outputs
  are disabled, not shifted. "Linked to script X" banner; unlink to edit by hand.
  `python script.py --print-config` for use outside Wirescape. 8-row limit: use poly rows or a
  second module.
- OSC Out: network hosts by IP (OB-h2 #601); label, indicator and toggles as on OSC In; renaming the
  default addresses is deferred.

### 8. Python scripting (desktop and headless)
- Write, paste, edit and run scripts in Wirescape with no terminal or manual OSC setup.
- A shared runner: one supervised process per script; a crash, flood or replacement never stops audio;
  all gates go to 0 on stop.
- A stdlib-only helper library: `ws.trig("Kick")`, `ws.voice("Chaos note")`, `ws.cv("Filter")`,
  `ws.knob("Density", 0, 1, 0.5)`.
- Declared controls (knob, slider, toggle, button, dropdown, number, text, note grid, label),
  drawn by the generic module panel (0015), shown in the Player, mappable like any control.
- Example presets: Euclidean, random walk, Markov, chords, probability, polyrhythm, evolving
  modulation. First example: `generative_ws.py`.
- Phases: runner + editor → auto-sync → controls → graphics. Later: timestamped bundles for
  sample-tight timing.

### 9. Tool page host ("mini browser" in Studio)
- A dockable panel that expands to a page and loads local HTML tools in a sandbox, with a Tool API
  (workspace files, allowlisted processes, engine status, Player API, log); each page declares
  its grants and the owner approves once. The same sandbox as module panels (0015), with a different
  permission profile.
- First tool: the Python editor. Later: module test bench, test runner, compile, bundle check,
  patch check, controller monitor.
- Local, owner-approved pages only. Not shipped in the Player.

### 10. Studio
- Lock structure toggle (no add, delete, rewire or hardware settings; everything else live).
- Engine restart fix: today it gives up after 3 crashes in 30 s (`apps/desktop/main.ts:262`).
- Bundle export, Player preview, Mappings panel and macros, map mode, OSC editor features, setlist.

### 11. Guides (agent-ready, self-contained)
- One page per board (Pico, Pico W 2, ESP32, Nano): MIDI and OSC setup with example code.
- OSC and MIDI setup guide; Python scripting guide with examples; a short patching primer; the module
  build guide (two-stage); the Player UI design guide (in `wirescape-headless`).

### 12. Cleanups
- Make device-specific wording generic: `/pico1` defaults, "Pico W 2 boards" in the OB plan, the M8 examples in
  `docs/specs/ENGINE_PROTOCOL.md:144,291,338` and the fake MIDI test (→ `Test MIDI 1`).
- Re-frame 0022, CURRENT line 13 and OB_PLAN lines 12–13 as headless requirements.
- The 0022 Tier 1 tasks stay (OB-h1 to OB-h6) because they serve the headless build.

## C. Answered and delegated questions (owner, 2026-11-26)
- Envelope parameter mapping: dropped as a question (covered by B.4's batch).
- Macros: 8 per Macro module, in pages of 8. **Yes.**
- Bars: 4/4 until the transport has a time signature. **Yes.**
- **Planner decides:** how `wirescape-test` pins the lab and whether Windows CI runs only on ready PRs; the reference UI
  technology (kiosk web page or native); script auto-sync overwrite vs unlink; whether Python scripts
  run with the owner's normal rights; when to rename the OSC Out defaults.

## D. Repos
- `kalharbi11/wirescape-test` and `kalharbi11/wirescape-headless` exist (2026-11-26) with provisional
  skeletons: README, AGENTS/CLAUDE (provisional rules), LICENSE, `LAB_PIN` (lab `11a68c2`). The headless
  repo also has `docs/REQUIREMENTS.md`, six example patches, the example script and its OSC In rows.

Signed: claude-architect, 2026-11-26 (rev 2: owner answers)
