<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S6 — Studio and desktop code map (scout)

Lab commit: `11a68c2a2cfea1e34390c5c6a8e20549152afaa3` (branch claude/wirescape-modes-architecture-tnszf8). Paths. Facts only.

## 1. Stack
- No UI framework: plain TypeScript with a hand-written DOM helper (`el`, `svgEl` in `apps/studio/src/app/dom.ts`). `apps/studio/package.json`: dependencies only `@fontsource/ibm-plex-mono`, `@fontsource/ibm-plex-sans`; devDependencies `@playwright/test 1.49.1`, `typescript 5.7.2`, `vite 6.0.7`.
- Patch canvas: DOM module cards (`canvas/ModuleCard.ts`) over a world-transformed viewport (`canvas/Viewport.ts`); cables are SVG paths (`canvas/CableLayer.ts:40,57`, `svgEl('svg', ...)`). Per-widget visuals (Scope, Meter, FilterDisplay etc.) use `<canvas>` via `panels/widgets/canvasBase.ts`. No WebGL found.
- Build: Vite (`vite.config.ts`), `npm run build` = `tsc --noEmit && vite build` (package.json). Custom plugin `patch-library.mjs`. Web build flag `VITE_WIRESCAPE_WEB=1` (`src/main.ts:20`).
- Tests: Playwright (`npm test` = `playwright test`; `playwright.config.ts`, `playwright.web.config.ts`); Node tests in `tests-node/`.
- Desktop: Electron 36.9.5 (`apps/desktop/package.json`), main.ts 600 lines, preload.ts 102, DESIGN.md 43; desktop builds Studio first (`build-ui`) and reuses Studio's Playwright.

## 2. Directory map (apps/studio/src, .ts/.tsx/.css lines)
| Folder | Lines | Responsibility |
|---|---|---|
| app/ | 4311 | App shell (App.ts), Learn UI, OSC editors, library, quick-add, keyboard, curated/starter patches, module presets |
| panels/ | 4124 | Module panel builder, layout resolution, widgets (knob, fader, scope, groove pane) |
| engine/ | 2375 | EngineClient interface, RealEngine, FakeEngine, generated protocol_v0.ts |
| canvas/ | 2364 | PatchCanvas, ModuleCard, CableLayer, Viewport |
| styles/ | 1336 | CSS |
| patch/ | 633 | PatchDoc, History (undo), types |
| groove/ | 513 | Groove/step-sequencer session, chords, pattern |
| web/ | 338 | Web-demo bridge, sharing, start, starters |
| modules/ | 360 | Registry/descriptor types, musicalPitch |
| theme/ 174, system/ 163 (StatusBar, Toasts), runtime/ 126 (Ticker) | | |
`src/main.ts` is the entry. 25 largest files (lines, `wc -l` under apps/studio/src):
2112 app/App.ts; 1254 canvas/PatchCanvas.ts; 1112 panels/widgets/GroovePane.ts; 1057 app/bundled/midi-keys-and-knobs.json; 949 engine/FakeEngine.ts; 705 canvas/ModuleCard.ts; 677 styles/app.css; 667 engine/RealEngine.ts; 545 engine/generated/protocol_v0.ts; 451 panels/widgets/Knob.ts; 367 app/OscEditor.ts; 358 patch/PatchDoc.ts; 304 canvas/CableLayer.ts; 296 panels/PanelBuilder.ts; 292 app/curated.ts; 273 app/ccLearn.ts; 246 panels/layouts.ts; 234 modules/registry.ts; 228 styles/chrome.css; 228 panels/widgets/FilterDisplay.ts; 227 panels/widgets/EnvelopeCurve.ts; 214 engine/EngineClient.ts; 201 patch/History.ts; 198 panels/widgets/InfoBox.ts; 188 groove/pattern.ts.

## 3. Engine link
1. `engine/EngineClient.ts:3-7`: "Contract 2" — every UI talk to the engine goes through one `EngineClient` object; nothing else may fake sound or invent values.
2. `RealEngine.ts:7-16` declares `WirescapeBridge` (5 members: `send`, `onMessage`, `openPatch`, `savePatch`, `platform`; plus `web?`) read from `window.wirescape`.
3. RealEngine sends `{v:0, id, type, ...payload}` (`RealEngine.ts:226`), protocol v0 (types in `engine/generated/protocol_v0.ts`); edits carry mutation + inverse for rollback (`RealEngine.ts:21-24`).
4. `apps/desktop/preload.ts` validates commands (≤2 MiB, no cycles, depth ≤64; lines 4-30) and exposes the single `window.wirescape` via contextBridge; IPC channels `wirescape:send/ready/open/save/escape` (`main.ts:575-589`).
5. `desktop/main.ts:233` spawns the engine child; relays bounded NDJSON over stdin/stdout (DESIGN.md:9-10); keeps `lastHello` (main.ts:107); paths stay in main.
6. `FakeEngine.ts` implements the same interface in-browser for tests/dev (capabilities `osc.out`, `applyGraph`, FakeEngine.ts:94); Web build swaps in `WebBridge` (WASM engine in an AudioWorklet, `web/WebBridge.ts:2-5`) so RealEngine runs unchanged.

## 4. Mapping today
- MIDI Learn: `app/MidiLearn.ts` is only the UI bar; reads `status.midi.learn` (MidiLearn.ts:5 "committing the mapping is the host's job"). `app/ccLearn.ts:1-22` header: engine only observes a moved CC; UI writes a `midi.cc_to_cv` row into `config.rows`, adds a CC module and a `midi.in` feeder when needed, cables the row output onto the learned parameter as a `modulation` connection (ccLearn.ts:237), sent as ONE live `loadGraph` replan. `CC_TYPE='midi.cc_to_cv'`, `MAX_CC_ROWS=8` (ccLearn.ts:27-28). Event cable midi.in→cc (ccLearn.ts:203). Forget: App.ts:1202 "MIDI mapping forgotten." Imports in App.ts:34-36; `PatchDoc.ccRows` at PatchDoc.ts:235. So a learned mapping lives in the patch as ordinary modules/rows/cables, not a separate mapping section.
- Module presets: `app/modulePresets.ts:5-6` `MODULE_PRESETS` keyed by module type, `{name, params}`; "Preset names remain UI-only, never saved to patches". Applied as one snapshot through normal setParam (App.ts:1101); `matchingPreset/resolvePreset` used by PanelBuilder.ts:12.
- OSC In editor: `app/OscEditor.ts:6-14` `OscRow {pattern, argument, kind cv|gate|trigger, input_min/max, output_min/max, smoothing_ms, timeout_ms, stale hold|zero, enabled?}`; `OscConfig {version?, port, lan, rows[]}` (line 15). Row ids positional row1..row8 (line 5). Default row `/pico1/knob/${n}` (line 17); `picoDefaults()` port 9000, lan false, 8 rows (lines 19-20). Presets at 283-291: "Pico knobs 1–8", "TouchOSC faders /1/fader1–8", "Reset to Pico defaults", "Clear (all rows off)". Placeholder `/pico1/knob/${i+1}` (line 154). OSC Out: `app/OscOutEditor.ts` (OscOutRow/OscOutConfig lines 6-13). `app/oscCapture.ts` captures raw readings.
- "Macro": only the Plaits-derived module `ports.macro_oscillator` and demo patch `host/examples/class_demo_3_macro.json` (App.ts:39); `tests/macro-panel.spec.ts`. No macro/mapping-layer concept found in app/panels/canvas/patch.
- Lock / perform mode: none found (grep for lock/perform in app, panels, canvas, patch hits only unrelated words such as "performed" App.ts:2004 and clock toggle).

## 5. Panels (vs proposals/0015-module-panels.md)
- `panels/PanelBuilder.ts` (296): builds a module's controls; `panels/layouts.ts` (246): roles (hero/primary/secondary/trim/mode/toggle/fader/number/readout/select, layouts.ts:10-12), widget kinds (knob, segmented, toggle, readout, select, fader, number), knob tiers L/M/S; `PanelOverride` (layouts.ts:33) = `panels/<module-id>.json` optional override; `PanelOverrides.load` fetches `panels/index.json` then each `<id>.json` (layouts.ts:228-240). Bundled: `apps/studio/public/panels/*.json` (e.g. essentials.adsr.json, chaos_lite, clock, function_envelope, ladder). `panes.ts` = special panes; widgets: Knob, Fader, Segmented, Selector, Toggle, NumberBox, Meter, Scope, ChannelMeters, EnvelopeCurve, FilterDisplay, ModelGrid, WavePreview, RandomHistory, StepsPane, GroovePane, InfoBox.
- Present: the per-module `panels/<id>.json` override + role-driven generic layout. Not present in src: any `custom` panel kind, `ui/index.html` entry, iframe, or sandbox (grep for `sandbox|iframe` empty; no `modules/*/ui/` files tracked, no `panel*` file in modules/*). 0015 (lines 14, 41) specifies `ui/` sandbox and a `custom` kind `{entry, placement, width, height, ...}`.
- Panel metadata is not saved in patches except `ui.groove`.

## 6. Patch document
- Format `wirescape.native.patch`, `version: 2` (types.ts:49-50); loader accepts versions 1 and 2, v1 migrated (PatchDoc.ts:67,99). Contract 3 comment: unknown fields survive load→save (types.ts:2-6; PatchDoc.ts:101 `...rest`, `preserved`).
- Saved via the bridge `savePatch(text)` (desktop atomic rename, DESIGN.md:13-14); browser autosave key `wirescape.autosave.v2` in localStorage every 4000 ms (App.ts:41,468).
- Studio-only data lives under top-level `ui` (types.ts:35-46): `positions` (id→[x,y]), `view` {x,y,zoom}, `labels`, `cableColors`, `groove` {root, scale} per instance; `[extra]` allowed. PatchDoc validates these as objects (PatchDoc.ts:75-76) and emits `ui` only if the source had one or it is non-empty (PatchDoc.ts:122).
- `patches/basics-07-macro-keys.json` top-level keys: SPDX-License-Identifier, name, description, format, version, settings, modules, connections, outputs, ui. Module entry keys: id, module, version, parameters. `settings` e.g. sample_rate, max_block_frames, max_channels, feedback_block, seed, timing_mode (seen in curated.ts:16).
- `History.ts` (201): undo/redo; `types.ts` also holds `connKey`, `EMPTY_PATCH`.

## 7. Web vs desktop
- `src/web/` (338 lines): `WebBridge.ts` (same 5-member bridge, `web=true`, `platform='linux'`; AudioWorklet+WASM engine; no MIDI, OSC, devices or files; ignores `setOsc`, `setMidiEnabled`, `selectAudioDevice`, lines 2-5, 12-13), `start.ts` (one-click splash for audio gesture), `share.ts` (patch in URL hash `#p=` gzip+base64url, 16 000-char link cap, 2 MiB limit), `starters.ts`.
- Build gate: `VITE_WIRESCAPE_WEB=1` (main.ts:20-26); `vite.config.ts` base from `WIRESCAPE_BASE` (sub-path hosting). FakeEngine drops capabilities when `window.wirescape?.web` (FakeEngine.ts:94). Web smoke config needs `public/web/wirescape.wasm` (playwright.web.config.ts:4).
- Desktop: Electron main owns window, dialogs, engine child, restart/shutdown; local-only `app://wirescape/` handler, contextIsolation, sandboxed preload (DESIGN.md:4-8); Open/Save start in per-user `patches/` dir (DESIGN.md:18-25).

## 8. Tests
- apps/studio `tests/`: 47 entries (about 46 spec files plus `helpers.ts`; `mock-bridge/` dir has 7 files); mix `.spec.ts` and `.spec.cjs`. `tests-web/`: 7 files (Playwright web demo/WASM); `tests-node/`: 2 `.mjs` Node tests (groove-study, patch-library). All browser tests are Playwright (Chromium path `WIRESCAPE_CHROMIUM` default `/opt/pw-browsers/chromium`, workers 1, baseURL localhost:4173); no separate unit-test runner (no vitest/jest in package.json).
- Relevant specs: midi-learn-ui, osc-editor/osc-monitor/osc-pattern/osc-range/osc-tuning, module-presets, macro-panel, session/session-autosave, patch-browser, curated, starters, pi-profile.
- apps/desktop `tests/`: app-e2e, boot, pi-profile, profile-guard, refused-draft-files, shell, windows-setup specs (.cjs) plus `stub-engine.cjs`; run with `npm test` (Electron Playwright, Xvfb on Linux; stub engine with `--null-audio`).
- Run: studio `cd apps/studio && npm ci && npm test` (README/AGENTS); desktop `cd apps/desktop && npm ci && npm test`; web `playwright.web.config.ts`.
