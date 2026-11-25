<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Protocol v0 command and error inventory (generated; not runtime-wired)

Source: `docs/specs/protocol.schema.json`; regenerate with `python tools/protocol/generate.py`.

| Command type | Required payload fields |
| --- | --- |
| `loadGraph` | `patch` |
| `applyGraph` | `patch` |
| `addModule` | `moduleId`, `moduleType` |
| `removeModule` | `moduleId` |
| `connect` | `connection` |
| `disconnect` | `connection` |
| `setParam` | `moduleId`, `paramId`, `value` |
| `setData` | `moduleId`, `slot`, `value` |
| `setModAmount` | `connection`, `amount` |
| `noteOn` | `note`, `velocity` |
| `noteOff` | `note` |
| `panic` | — |
| `listAudioDevices` | — |
| `selectAudioDevice` | `deviceId` |
| `listMidiDevices` | — |
| `setMidiEnabled` | `deviceId`, `on` |
| `midiLearn` | `armed` |
| `setSampleRate` | `hz` |
| `setBufferFrames` | `frames` |
| `setOsc` | `cfg` |
| `ccMap.set` | `moduleId`, `row`, `mapping` |
| `app.restartEngine` | — |

| Refusal error code |
| --- |
| `unknown-module` |
| `kind-mismatch` |
| `duplicate` |
| `not-found` |
| `refused` |
| `invalid` |
| `busy` |
| `limit` |
| `unavailable` |
