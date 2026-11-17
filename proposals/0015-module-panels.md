<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0015 — Custom module UIs: the panel file and the panel host API (design note)

**Author:** Fable · **Date:** 2026-11-16 (ET) · **Status:** design for `0004` T5.5 and T5.6
(contract M12). The panel file (section 2) is a format and is frozen by this note at version 1.
**Rests on:** `0002` D7, `0003` §1 and §4, `0012` §9–10, `0014` §4, `OWNER_WANTS.md:97–103`,
`apps/studio/src/panels/layouts.ts`, `panes.ts`, `apps/desktop/main.ts:520–557`,
`facts/compare/ui_systems.md`, `facts/app/*/ui.json`.

## 1. Decisions

- **U1. Three layers, each optional above the first.** (1) The generic panel, built from the
  descriptor; it always exists. (2) `panel.json` in the module folder: layout and widget
  choices, no code. (3) `ui/`: an HTML panel in a sandbox that talks to a small message API.
- **U2. Every parameter stays reachable without layer 3.** The generic panel can always be
  shown instead of a custom one. Hardware, plugins and keyboard users depend on this.
- **U3. A custom panel holds no state.** Everything it shows comes from parameters, data
  slots and telemetry, so the host may destroy and re-create it at any time.
- **U4. A panel sees only its own module instance.** It cannot read the patch, other
  modules, files, the network or the engine.
- **U5. The panel talks to a library, not to Studio.** `wire-panel.js` (MIT, in the SDK) is
  the only interface. A plugin WebView can implement the same messages later (the JUCE 8
  approach the owner named), and the same `ui/` folder then runs there unchanged.
- **U6. Module-specific code leaves Studio.** Groove, the OSC editors, the Macro model grid,
  the monitor log and the CHAOS presets move into their module folders. Studio keeps generic
  widgets only (`modules/types.ts:5`: "Nothing in the UI may hand-code a module").

## 2. `panel.json`, version 1

It lives in the module folder. The module build copies it into the manifest; the hand-kept
`public/panels/index.json` is deleted. The keys are today's override keys
(`layouts.ts:33–53`), written down as a schema, plus four:

| Key | Meaning |
|---|---|
| `version` | 1. A file with a higher number loads as if absent, with a warning |
| `width`, `layout`, `code`, `short`, `hidden`, `roles`, `widgets`, `modPorts`, `ports` | as today |
| `sections` | `[{label, hero, columns, params}]`; without it, sections come from the parameter `group` of the descriptor, then from role inference |
| `panes` | a list of generic widgets, each `{kind, options}` |
| `bind` (new, inside a pane's options) | what the pane shows: `{param}`, `{params: [...]}`, `{stream, field, voice?}` or `{data: slot, field}` |
| `custom` (new) | `{entry: "ui/index.html", placement: "card" or "editor", width, height, minWidth, minHeight}` |
| `strings` (new) | display names by locale for labels; IDs never change |

- **Pane kinds, the closed list of version 1:** `wave`, `envelope`, `filter`, `meter`,
  `scope`, `steps`, `channels`, `grid` (an enum parameter as a button grid; replaces
  `models`), `xy`, `readout`, `log`. A pane reads only what `bind` names. `groove` is not a
  pane kind; it becomes a custom panel.
- **Rules kept from today:** an unknown key is ignored with a warning; an unknown pane kind
  falls back to the generic layout; a parameter the file forgets appears under "MORE", so a
  control is never dropped.
- Ranges, IDs, defaults and units are **not** in this file. They are in the descriptor,
  because they are part of the sound and of saved patches (`0003` §4).
- Presets are separate files (`0014` §4.2), not part of `panel.json`. This keeps the answer
  already recorded in `QUESTIONS.md:92`.

## 3. The custom panel

- **Where it runs.** One `<iframe>` per live panel, sandboxed with scripts allowed and
  nothing else: no same-origin access, forms, popups, top navigation, downloads or pointer
  lock. Files are served read-only from the module's `ui/` folder by the existing
  `app://wirescape/` handler. A content security policy on those responses allows only the
  folder's own scripts, styles, images and fonts; no network, no `eval`.
- **What it cannot reach.** Electron IPC is already refused for subframes
  (`main.ts:324–327`); that check is now a tested invariant. The panel has no storage.
- **Placement.** `card`: inside the module card, at the declared size, scaled with the
  canvas. `editor`: the card shows the generic panel plus an "Open editor" button, and the
  custom panel opens in a host-owned surface (Groove needs 1,060 px).
- **Lifetime.** Created when the card is on screen and large enough to use, or when the
  editor opens. Told `visible: false` when off screen and destroyed soon after. At most 8
  live panels by default, least recently used first out; the others show the generic panel.
  The number 8 is a starting value: see section 6.

## 4. The panel host API, version 1

JSON messages over one `MessagePort` given to the frame at load. Every message has `v: 1`.
Studio is the broker: it checks each request, forwards it through `EngineClient`, and answers.

**Host to panel**
| Message | Carries |
|---|---|
| `init` | API version, the module's descriptor, instance ID, current parameter values, data slots, preset names, theme tokens, density, scale, locale, `readonly` |
| `param` | `{id, value, effective?}` when a value changes from anywhere |
| `data` | `{slot, value, serial}` when a slot changes |
| `telemetry` | `{stream, voice?, record}` for subscribed streams; at most 30 per second per stream, newest wins |
| `theme`, `visible` | token changes; on-screen state |
| `refused` | `{request, field, reason}`: the engine's refusal, in its own words |

**Panel to host**
| Message | Does | Allowed when |
|---|---|---|
| `ready` | asks for `init` | always |
| `setParam {id, value, gesture}` | `gesture` is `begin`, `change` or `end`; one gesture is one undo step | the parameter is the module's own |
| `setData {slot, value}` | replaces one slot; the engine validates it by the field table (`0012` §2) | the slot is the module's own |
| `subscribe`, `unsubscribe {stream, voice?}` | telemetry | the stream is declared |
| `applyPreset {name}` | one undo step | the preset is the module's own |
| `resize {width, height}` | asks for a new size, clamped to the declared limits | `card` placement |
| `setTransport {bpm?, playing?}` | `0008` | the module has `TRANSPORT_CONTROL` |
| `noteOn`, `noteOff` | plays notes into the instance | the module has a `notes.in` port |
| `log {text}` | to the developer console | developer mode |

- **Limits.** `setParam` is coalesced to 120 per second per parameter. A message over 256 KiB,
  or more than 500 messages per second from one panel, is dropped and counted; the count is
  shown in developer mode. A panel that never sends `ready` within 3 s is replaced by the
  generic panel with a plain message.
- **Theme.** `init` carries the token values of `theme/tokens.css` by name. The library sets
  them as CSS variables in the frame, so a panel that uses the tokens follows light, dark and
  the UI scale without knowing them. A panel may ignore them and draw its own look; that is
  the point of a custom panel.
- **Keyboard and screen readers.** Focus enters the frame by Tab and leaves by Tab or
  Escape; the host keeps its global shortcuts. The library ships labelled knob, fader and
  toggle elements with the same keys as Studio's (`Knob.ts:337–353`). U2 is the fallback.
- **Versioning.** A panel states the API version it needs in `ready`. The host serves that
  version or shows the generic panel. Additions are new messages; nothing is repurposed.

## 5. Order of work

| Step | What | Needs |
|---|---|---|
| P1 | `panel.json` schema v1, files moved into module folders, manifest carries them, `index.json` deleted; screenshots identical before and after | M3 MB2 |
| P2 | `bind` for telemetry and data; `scope`, `log`, `grid`, `xy`, `readout` panes; Scope and monitor use them | `0004` T3.4 |
| P3 | Sandbox, broker and `wire-panel.js`, with the security tests of section 6 | P1; class C |
| P4 | Groove editor as a custom panel using `setData` | P3, M4 E3b |
| P5 | OSC In and OSC Out editors as custom panels; CC Learn stays an app feature and writes data | P3, M4 E3c |
| P6 | Example panels for CHAOS (presets, sections) and GUTTR (per-voice telemetry) | P3, `0004` T5.1, T5.3 |
| P7 | Developer mode layer 1: edit `panel.json` live, saved to the module folder by the desktop process; layer 2: declared ports, capabilities, live telemetry records, last test result | P3, `0004` T3.9 |

## 6. Gates and facts

- **Security tests (P3, required).** From inside a panel each of these fails and is
  reported: a fetch to any network address, reading `parent` or `top`, opening a window,
  navigating the top frame, using storage, calling `window.wirescape`, loading a script
  from outside `ui/`, setting a parameter of another module, subscribing to an undeclared
  stream. This protects the Fixed renderer-isolation constraint.
- **Sameness (P1).** Panel screenshots for all stock modules are pixel-identical before and
  after the move.
- **Cost (facts first).** Nothing in `facts/` gives the memory of one frame or the frame time
  with several live. P3 starts with a class A task that measures both on three platforms, at
  1, 8 and 32 live panels in the 200-module patch. The live-panel limit and any frame-time
  gate are set by Fable from those numbers; until then 8 is a default, not a gate.

## 7. Assumptions, and what would overturn them

- **A1** A sandboxed frame without same-origin access can load its own folder under a
  policy that blocks the network. If the scheme handler cannot express that, the files are
  inlined into the frame by the host; the API does not change.
- **A2** 30 telemetry messages per second per stream is enough for a scope and a
  per-voice display. A panel that needs more gets a `BLOCK` stream, which may deliver several
  queued records in one message, not a higher message rate (records stay ≤ 4,096 bytes, `0012`;
  amended by `0017` section 5).
- **A3** Stateless panels are acceptable to authors. A panel that needs view state (a zoom
  level, a selected step) keeps it in a data slot marked as view-only; if several modules
  need this, version 2 adds a small per-instance view store saved under `ui` in the patch.
- **A4** The Groove editor can be rebuilt on `setData` with whole-slot writes. If a slot
  write per keystroke is too heavy, version 2 adds a field-level write.

Signed: Fable, 2026-11-16
