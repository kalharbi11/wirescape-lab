<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Browser version (WEB1)

The real engine compiled to WebAssembly, running in an AudioWorklet behind the Studio UI.
Built and tested by `.github/workflows/web-demo.yml`; deployed to GitHub Pages from `main`
once Settings → Pages → Source is set to GitHub Actions. Internals: [DESIGN.md](DESIGN.md).

## Works
- Every module discovered by the generated built-in registry except `midi.*` and `osc.*`. The list is
  not kept by hand: `web_module()` in `web_engine.cpp` filters the engine catalogue, and
  `web_engine_tests` checks that the web catalogue equals the engine catalogue minus those two
  prefixes. A newly registered module appears in the browser with no extra change.
- Starter and curated patches whose modules are all in that catalogue; others are hidden.
- Computer and on-screen keyboard, live telemetry (cable values, scope), SAVE and SHARE links.
- Macro Oscillator: the AudioContext is opened at 48000 Hz. Where the browser refuses that rate
  it falls back to the browser's rate and the existing Macro sample-rate error is shown.

## Does not work (yet)
- No MIDI (no Web MIDI): `midi.*` modules are refused as `unknown-module`.
- No OSC: `osc.*` modules are refused; there is no WebSocket relay.
- No live edits: every edit is a `loadGraph` that rebuilds the graph and crossfades from the old
  one over 480 frames (10 ms at 48 kHz). There is no `applyGraph`, so edits restart module state.
- No audio device selection: the browser's default output only.

## Local build (devices off)
```
cmake -S targets/web -B build/web-native -G Ninja && cmake --build build/web-native && ctest --test-dir build/web-native
# with Emscripten 3.1.74 active:
emcmake cmake -S targets/web -B build/web-wasm -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build/web-wasm
cp build/web-wasm/wirescape.wasm apps/studio/public/web/
cd apps/studio && npm ci && npx playwright test -c playwright.web.config.ts
```
