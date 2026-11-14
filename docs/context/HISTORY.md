<!-- SPDX-License-Identifier: GPL-3.0-only -->
# History: how the product got here, and the decisions behind it

The old plan's decisions are cited in specs as D1–D21. Each is listed with what it cost.
Whether a decision is fixed or open to change: `CONSTRAINTS.md`.

## Timeline
1. **Python + browser prototype** with a Surge-based CHAOS synth (deleted; preserved in the main repo at tag `archive/qt-final`).
2. **ABI1 engine + Qt desktop app** (C++ engine with dlopen plugin modules, Qt UI, QtCore patch documents).
3. **ABI 2** (`module2.h`, `engine2`): polyphonic cables (up to 16 channels), audio-rate modulation, feedback,
   per-voice parameters, live replan. Every ABI1 module was re-written; ABI1 kept for equivalence vectors.
4. **Studio** (TypeScript/Vite UI, first built in the separate `Wirescape-UI` repo) imported into `apps/studio`.
5. **Electron app + `wirescape-engine` sidecar** (stdin/stdout JSON lines) replaced Qt. Qt then deleted.
6. v1.0 content: OSC In, OSC Out (loopback), ASIO on Windows, Groove sequencer, Pi 5 launcher.

## Decisions
| # | Decision | Why | Cost / known downside |
|---|---|---|---|
| D1 | Electron app, engine as a separate C++ process | same Chromium as Studio on the Pi; crash isolation | Electron memory/startup on the Pi; two processes |
| D2 | UI lives in this repo (`apps/studio`), shell in `apps/desktop` | one repo, one CI | Studio carries its own older docs |
| D3 | The UI owns the patch document; the engine executes a validated copy and never rewrites it | no second document editor in C++ | two codecs (TS `PatchDoc.ts`, C++ `runtime_patch`) kept in sync by conformance tests |
| D4 | Protocol: one JSON object per line on stdin/stdout, `ack`/`refuse` with graph generation, pushed status ≤10 Hz and telemetry ≤30 Hz; one preload bridge object | simplest transport, nothing to secure | JSON parse cost; protocol is still `v: 0` |
| D5 | Parameters via the engine event queue; topology via live replan; otherwise stop → swap → fade | live edits without a second engine | any module-config edit falls back to a full reload (see KNOWN_ISSUES A2) |
| D6 | Audio and MIDI start with the app; consent via `--confirm-audio --confirm-midi` from the launcher | appliance behaviour on the Pi | long launch command; no installer |
| D7 | MIDI subscriptions refresh on the control thread during live edits; module IDs never reused in a document | held notes and routing stay correct | — |
| D8 | CC mapping = `midi.cc_to_cv` config rows (8 per module) | the DSP already reads that layer | CC Learn edits trigger a full reload |
| D9 | Engine sends its catalogue and device lists on start; unknown modules preserved and marked | IDs stay in sync | generated `wirescape_modules.json` + drift check |
| D10 | Pi 5 first for acceptance; Windows second | owner's target instrument | Windows found later issues (ASIO) |
| D12 | Only electron/electron-builder added as dependencies by default | small surface | — |
| D14 | Web demo: engine in WebAssembly behind the same Studio (GitHub Pages) | showcase | audio still on the main thread, not an AudioWorklet |
| D15 | Qt retired (no fallback) | one product | — |
| D16 | v1 patch import lives in Studio (`migrateV1`); the engine still reads v1 execution copies | no new C++ document library | keeps `legacy_index` alive in the ABI |
| D17 | ABI1 retires after Qt, after freezing equivalence vectors as data | duplicate module path in the realtime core | not done (RESIDUE §1) |
| D18 | Finish before start (limit open PRs) | throughput | process only |
| D19 | Git history is the archive | small tree | — |
| D20 | Versions are releases the owner chooses, not development phases | clarity | — |
| D21 | OSC Out (UDP to 127.0.0.1 only) is in v1.0 | Pi → microcontroller bridge | LAN later |

## Other standing rules from the old repo
- Module, port and parameter IDs never change; patch migration is lossless; unknown data is preserved.
- ABI 2 "soft freeze": additive SDK changes only, otherwise a migration note. No third-party modules exist yet.
- Module DSP is meant to stay portable to plugins and Daisy-class hardware.
