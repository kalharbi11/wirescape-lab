<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR — throat engine extraction

> **In the lab:** only the docs are here. The engine files this README names (`guttur-core.js`, `guttur-worklet.js`, `tests/verify.cjs`) are held back until their licence and provenance are confirmed (see PROVENANCE.md). The owner has them.

This is the engine-only reference for a future native C++ Wirescape module. It is **not an installed Wirescape module**. No Wirescape repository files were changed or posted.

Removed: the entire application UI (including keyboard, crowd editor and proof screens), chant scenes/transport/scheduling/layers, syllable gesture curves, claps and stamps. Retained: LF pulse source, tube/resonance model, multi-throat groups, all intrinsic modulation, envelopes, spatialisation, room, tone, drive, calibration, limiter, 37 parameters and 11 voice texture presets. The `chant` preset is only a static rough voice texture; it has no sequencer.

The note API remains so a future host can excite/release voices; it does not include a keyboard. UI styling and embedded UI engine copies are intentionally omitted. Everything needed to generate the current sound is in `guttur-core.js`.

## Files

- `guttur-core.js`: standalone engine and model/table builders; Node CommonJS or browser global `GutturCore`.
- `guttur-worklet.js`: optional browser adapter; import with `audioWorklet.addModule()`, create node `guttur` with `outputChannelCount: [2]`. No automatic UI telemetry messages.
- `docs/IMPLEMENTATION_REVIEW.md`: compatibility, rebuild plan, host capabilities and acceptance criteria.
- `docs/PARAMETERS.md`: complete extracted ranges/defaults, not a new native module contract.
- `docs/PROVENANCE.md`: source hashes and scope.
- `tests/verify.cjs`: offline checks; optional original-file parity mode.

## Offline use

```js
const C = require('./guttur-core.js');
const engine = new C.Engine({sampleRate: 48000, maxSingers: 24, seed: 17});
engine.setParams({throats: 3, growl: .7, vowel: .4, pharynx: .3});
engine.noteOn(45, .8); // MIDI-number pitch and velocity 0..1
const left = new Float32Array(48000), right = new Float32Array(48000);
engine.process(left, right, left.length);
engine.noteOff(45);
// Continue processing to hear release and room tail.
```

Run `node tests/verify.cjs`. For exact comparison with the upload, run `node tests/verify.cjs /path/to/original/guttur-worklet.js`.

This extraction deliberately preserves the prototype's note-mode sound and its limitations. It is a reference, not realtime-safe native code. Defaults: 24 singer slots total, 1–8 throats per note (3 default), 128-frame control blocks. Pass valid finite parameter values within the documented ranges. Do not increase `ctlBlock` above 512 (fixed scratch capacity). `panic()` retains prototype behavior and does not clear room/limiter tails. Browser adapter was source-reviewed, not browser-tested. There are no npm dependencies.
