<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S2 — Engine protocol and process model (scout)

Lab commit: 11a68c2. Facts only. Paths relative to the lab repo. "EP" = docs/specs/ENGINE_PROTOCOL.md, "DES" = host/sidecar/DESIGN.md, "SES" = host/sidecar/session.cpp.

## 1. Process model

- Binary `wirescape-engine` (`.exe` on win32), Qt-free C++17 (DES:4). Electron looks for it at `<appPath>/wirescape-engine`, else `../../build/native/` (apps/desktop/main.ts:219-226).
- Start: child process, stdin/stdout NDJSON, one UTF-8 JSON object per LF line; stderr = diagnostics only; no socket/HTTP/WebSocket for control (EP:4,16; DES:7). OSC In UDP is the only socket, loopback default (DES:5-7).
- Startup order: `hello` is sent first, then reader starts, `wait_hello` strictly before render/device startup, then `session.start()` (host/sidecar/main.cpp:13-17).
- Main loop (main.cpp:19-47): poll next request (5 ms timeout), reply, flush config events; after successful `selectAudioDevice`/`setMidiEnabled` also push `devices`; status every 100 ms (main.cpp:32), telemetry every 34 ms (:38), device poll every 100 ms (:42).
- Threads (protocol.cpp:108-110): watchdog, writer, reader. Main thread = sole control executor owning catalogue, execution copy, generation, ID history, settings, MIDI host, OSC host (DES:11-12). Writer alone serializes stdout (DES:16-17). Plus a nonblocking OSC UDP worker (DES:5-6, 85-86), audio callback thread (PortAudio) or paced null-sink thread (DES:26-27), libremidi/MIDI worker (refreshes endpoints every 500 ms, DES:96-97).
- Bounds:
  - Line cap 2,097,152 bytes, pending commands 256 (`LineLimit`, `PendingLimit`, protocol.h:15). Over-long line discarded through LF without growing buffer (protocol.cpp:132; DES:13-14). Saturated queue yields ordered `busy` markers (DES:15-17; EP:18).
  - Reply queue max 256 reliable messages; status/telemetry coalesced single slots (protocol.cpp:199; DES:20-21).
  - JSON nesting <=64, duplicate keys/BOM/invalid UTF-8 rejected (DES:14-15; EP:17).
  - Graph: <=64 nodes, <=128 cables (EP:35; SES:1533 `connections.size() <= 128`).
  - OSC: 32 routes max, 65,507 B recv buffer, 2,048 B datagram cap, 64 msgs/socket/poll (DES:85-88).
  - Status <=10 Hz, telemetry <30 Hz (DES:108; EP:34,49).
- Exit codes:
  - 0: clean EOF teardown (main.cpp:48-57; DES:24; EP:19). Final partial line discarded.
  - 1: startup/option/control exception, message on stderr (main.cpp:49-61). Unknown/invalid flag -> nonzero, no device opened (EP:219).
  - 2: audio shutdown failure / quarantine, `std::_Exit(2)` (SES:1651-1654; DES:33-35).
  - 3: stdout pipe write or shutdown cannot finish within 5 s, `_Exit(3)` (protocol.cpp:126,228,246,264,273; DES:17-19).
  - SIGTERM/crash is not EOF success (EP:19). SIGPIPE ignored on non-win (main.cpp:6-8).
- Persistence: settings file default `user_data/settings.json` relative to process cwd (host/sidecar/session.h:22), override `--settings FILE`; atomic replace (DES:49-50; EP:~213 settings paragraph). Holds audio id, rate/buffer, enabled MIDI pairs; never the patch.

## 2. Commands and async messages

Envelope `{"v":0,"id":"<=64 ASCII","type":...}`; reply `{v,session,re,ok,gen[,result|code,message]}` (EP:25-34). Error codes: unknown-module, kind-mismatch, duplicate, not-found, refused, invalid, busy, limit, unavailable (EP:35; protocol_v0.ts:4). Wire list in protocol_v0.ts:189-340 and EP:71-93; dispatch in SES:1230-1607.

| type | key fields | reply | notes |
|---|---|---|---|
| hello (client opt-in) | capabilities:["configDeferred"] | ok, no gen change | engine advertises configDeferred; second client hello = duplicate (EP:~203-205; SES:1230) |
| loadGraph | patch (PatchV2) | ok; `result.warnings` if merged mod cables | swap, atomic; new ID namespace (SES:1528-1541) |
| applyGraph | patch | `{path:"live"\|"restart",replaced[],unapplied[]}` | cap-gated; same namespace (SES:1567-1572; EP:97) |
| addModule / removeModule | moduleId, moduleType, params? / moduleId | ok | swap (EP:74-75; SES:1574-1594) |
| connect / disconnect | connection | ok | swap (SES:1594) |
| setParam | moduleId, paramId, value | ok after queue insert; `busy` if full | live (SES:1476) |
| setData | moduleId, slot, value (whole slot) | ok / busy | live (SES:1497) |
| setModAmount | connection, amount [-1,1] | ok | live (SES:1543) |
| noteOn / noteOff / panic | note, velocity / note / {} | ok | live; noteOff/panic priority (SES:1449-1475) |
| listAudioDevices / listMidiDevices | {} | `result.devices[]` | query (SES:1244,1250) |
| selectAudioDevice | deviceId | ok; refuses not-found/duplicate/refused before shutdown | device latency (SES:1350; EP:~133) |
| setMidiEnabled | deviceId, on | ok | SES:1418 |
| midiLearn | armed | `{armed}` | cap-gated, 30 s timeout (EP:88,108) |
| setSampleRate / setBufferFrames | hz {44100,48000,96000} / frames {64..1024} | ok; `result.freshModules[]` when graph rebuilt | stream restart (SES:1258; EP:89-90,95) |
| setOsc | cfg | always refused `unavailable` | SES:1257; never advertised (EP:91,150) |
| ccMap.set | moduleId,row,mapping | ok | SES:1607 |
| app.restartEngine | {} | main-owned, never reaches engine | desktop main.ts:200 (EP:40) |

No other command types exist in the generated union (protocol_v0.ts:3 CommandType; 189-340).

Async pushes (EP:36, 150-155; protocol_v0.ts:377-440), all carry `session`, non-hello carry `gen`:
- `hello`: protocol:0, engine{version "1.0.0", sha} (SES:1723), capabilities, catalogue.modules, audio, midi. Capabilities when OSC installed: midiLearn, telemetry.playhead, telemetry.monitor, setSampleRate, setBufferFrames, osc, osc.out, applyGraph (+configDeferred) (EP:150).
- `status` (<=10 Hz): `audio{state:starting|running|no-device|device-lost|reconnecting, deviceId, deviceName, sampleRate, bufferFrames, latencyMs (calculated 2*buf/rate), cpuPercent (callback wall/period; 0 with no stream), dropouts (cumulative xruns), error?, reason?, requestedBufferFrames?, unavailableDrivers?}`; `midi{devices[],activity{id:0..1},learn?,counters? (only --scripted-midi)}`; optional `osc{enabled,bind,port,lan,last_error?,routes[{module,port,bind,state:listening|lan-not-confirmed|port-busy|disabled,received,dropped,+budget/enqueue_dropped split}],out[{module,port,state:sending|disabled|error,sent,dropped,last_error?}]}` (EP:34-45; DES:108-111; protocol_v0.ts:139-155). OSC status never carries payloads.
- `telemetry` (<=30 Hz): tick, time, effective, phase, envelope, meters (only essentials.output ids), scope ({} in sidecar), eventActivity, heldNotes, optional effective_pitch, outputs, playhead, groove, monitor[nodeId] (<=32 entries, direct osc.in/midi.in only) (EP:49-55, 46; DES:112-118).
- `devices`: unthrottled, `audioDevices[]`, `midiDevices[]` on any enumeration/hotplug change (EP:152).
- `configDeferred`: deferId, moduleId, outcome applied|superseded|failed, generation (EP:85-87).
- App-owned (Electron only): `app.engineExited`, `app.menuOpenPatch`, `app.menuSavePatch` (protocol_v0.ts:416-430).

## 3. Graph changes

- loadGraph: full document, fresh ID namespace, new gen; validated off-thread, refusal leaves graph/gen (EP:73,112,121-122; DES:70-72). Refused graphs: 64 nodes/128 cables/2 MiB.
- applyGraph: same validation, same namespace, live replan; unchanged ID+type+canonical config keeps instance (phase, tails, held notes, seq position); changed ones replaced and listed; OSC Out always replaced; `path:"restart"` means D5 rebuilt every instance (EP:97; SES:1171,1222).
- addModule/removeModule/connect/disconnect: `swap` class, edit latency <=150 ms graph gap on working device (EP:69,112).
- setParam/setData/setModAmount/notes: `live`, enqueued on bounded event queue; ack = queue insertion, not render (EP:69,112).
- Replace fade: `WS2_REPLACE_FADE_DEFAULT_MS` = 20 ms, max 500 (sdk/include/wirescape/module2.h:90-91). Per-descriptor `replace_fade_ms` overrides (engine/edit.cpp:494-498; SES:975-978). Used for module replacement crossfade frames and the configDeferred failure bound `2*ms+1000` (SES:983).
- D5 fallback: master-output linear ramp <=10 ms, wait for zero block, activate candidate at zero gain, fade in; 150 ms deadline; failure rolls back (DES:61-69). Fast MIDI replan need not reopen the audio stream (DES:44-46).
- Gapless vs not (as documented): not sample-continuous when a stopped/lost stream restarts; no continuity guarantee for failed hardware (DES:46-49). setSampleRate / larger setBufferFrames rebuild module state, reported in `freshModules` (EP:95,101). Normal edits are a muted <=150 ms gap, not sample-gapless; unchanged modules in applyGraph keep state.
- Pending: busy replies may be deferred (`deferred:true`, `deferId`) only for config changes to engine-reported blocked module IDs (EP:85).

## 4. Devices and network

- Audio: PortAudio stereo outputs only; id `"<hostApi>|<name>[#n]"`; `--device NAME` startup override; selection persisted. Unknown id refuses not-found before stopping stream (EP:133-135). Loss: `device-lost` then `reconnecting`, reopen same name, backoff 100 ms to 5 s, never switches to a different default (DES:52-59).
- Real audio/MIDI only with `--confirm-audio` / `--confirm-midi`; otherwise nothing opens (listing permitted) (DES:79; EP:219; SES:210-211).
- `--null-audio` forces both off, paced null sink, fake M8/USB Stereo devices, loopback OSC (DES:83,89-91; SES:271).
- MIDI: id `name|system_name`; hotplug refreshed every 500 ms, `devices` push on change; enable choices persist across absence (DES:96-103; EP:~139).
- OSC In (module `osc.in`): config `{port, lan, rows[]}`; sockets opened by the sidecar only after successful commit; bind 127.0.0.1 unless BOTH `--confirm-lan` at launch AND route `lan:true`; unconfirmed -> loopback, not refusal; busy port -> graph accepted, route `port-busy`, status.osc.last_error "port-busy" (modules/osc_in/README.md:43-47; DES:79-83; EP:~219).
- OSC Out (`osc.out`): destination always 127.0.0.1, port default 9001, rate_hz 1..500 default 100; no host/lan key; error state on socket failure; allowed in every mode (docs/specs/OSC_OUT.md:19-34,102-103).
- `setOsc` / `allowNetwork` wire command: always `unavailable`; LAN permission is launch-flag + patch only (SES:1257; EP:91; EngineClient.ts:213).

## 5. Supervision

- Desktop main.ts is sole child owner (EP:20). Restart policy, quoted (main.ts:258-266):
  `if (!state.expected && !shuttingDown && !restartInProgress) {` ... `failures.push(now); while (failures.length && now - failures[0] > RESTART_WINDOW_MS) failures.shift(); if (failures.length <= 3) setTimeout(() => { ... startEngine(); }, 250); else void showEngineFailure();`
  `RESTART_WINDOW_MS = 30_000` (main.ts:15). So: auto-restart after 250 ms, up to 3 unexpected exits per 30 s; the 4th shows a dialog (Restart engine / Quit; restart resets counter) (main.ts:289-300).
- Graceful stop: `stdin.end()` (EOF), SIGKILL via `child.kill()` after 2000 ms (main.ts:271-279). stdin write/pipe errors refuse pending ids as `unavailable` (main.ts:238-241).
- Main never reloads the patch. Grep of main.ts for last-patch/reload finds only the Reload UI menu (main.ts:526). The reload is done by the Studio renderer: on new `hello` after a prior load, `RealEngine` calls `loadGraph(this.currentDocument())` (apps/studio/src/engine/RealEngine.ts:300-304); on `app.engineExited` it sets state `restarting` and rejects pending (RealEngine.ts:250-260). EP:44 states this as contract.
- Engine-only (no Electron needed): full command/reply/push protocol, settings persistence, device recovery, OSC, MIDI, validation. Electron-only: spawn/restart, the 5-member preload bridge, file dialogs/save path, `app.*` messages, process-exit notice, crash-loop dialog, engine path resolution.
- Obstacles to a non-Electron driver: none in the engine's code. It needs only a process with piped stdin/stdout. Env: none required by the engine (grep getenv in host/sidecar finds none; `WIRESCAPE_TEST_STUB` is desktop-only, main.ts:232). Electron passes `process.env` unchanged (main.ts:236).
- Startup args (Electron whitelist main.ts:16,32-33; engine parse SES:204-270): `--confirm-audio --confirm-midi --confirm-lan --null-audio`; valued `--device --block (1..4096, default 256) --rate (default 48000) --settings`; sidecar-only `--scripted-midi` (needs --null-audio + --settings), `--bench-summary` (needs --null-audio), `--capture-null-sink FILE` (needs --null-audio). Unknown flag -> exit 1. Working directory matters: default settings path and, via argv[0] parent dir, `directory` for PortAudio library lookup (SES:206).
- Client obligations: unique request ids per session; wait for `hello` before commands (EP:33,44); stdin EOF must be sent for exit 0 (EP:19).

## 6. host/cli `play` (host/cli/play.cpp; dispatched at host/cli/main.cpp:186)

Not the sidecar; one-shot patch player of a native v1/v2 patch.json.
- `--list-devices` (PortAudio list), `--list-midi --confirm-midi` (print `name|system_name`), `--monitor-midi NAME --confirm-midi [--seconds N<=600]` (prints raw bytes, :40-89).
- Play: `<patch.json> [--confirm-audio] [--device] [--rate (default 48000)] [--block (128)] [--confirm-midi --midi NAME] [--pace] [--output WAV (default build/play-offline.wav)] [--seconds (10)]` (:90-104).
- Without `--confirm-audio`: offline render to 16-bit stereo WAV plus JSON stats (peak/overruns) on stdout (:124-142). With it: real PortAudio stream until SIGINT (:123).
- `--confirm-lan` and `--osc-port` are refused ("await J4/J5") (:98-102): no OSC in `play`. No commands, no live edits, no status; patch loaded once with 2 MiB limit (:108-110).

## 7. Gaps a headless supervisor would hit (evidence searched)

- No heartbeat/ping/liveness command: grep `heartbeat|keepalive|ping|watchdog` in host/sidecar, EP, main.ts finds only the internal pipe watchdog (protocol.cpp:108,262). Liveness = continuing `status` pushes (100 ms, main.cpp:32) and process exit.
- No engine-side "load last patch" at startup: engine starts with a built-in/no graph; it stores settings only, never the patch (EP:44,213; DES:9 "demo patches are runnable execution documents, never rewritten saves"). Supervisor must resend `loadGraph` after every `hello`.
- Restart policy lives in Electron only (main.ts:258-266); the engine has no self-restart and a non-Electron host must replicate the 250 ms/3-in-30 s logic and `app.restartEngine` semantics.
- No Program Change reporting: grep `program.?change` in host/, engine/, modules/, docs/specs finds only host/midi/midi_service.cpp:50 (message-length parsing) and a plan-only mention (docs/specs/COMMUNICATION_MODULES_PLAN.md:137). `status.midi` has only `devices`, `activity` (0..1 decayed), `learn` (CC only, EP:38), optional scripted counters; no event log, clock only if observed.
- No MIDI/OSC event stream to the supervisor except `telemetry.monitor` (<=32 entries, direct cabling from osc.in/midi.in only, EP:46) and per-route counters in `status.osc` (no payloads).
- No runtime change of OSC ports/LAN: `setOsc` always `unavailable` (SES:1257); only launch flags and the loaded patch.
- No command to read the current graph/document back (no getGraph in union, protocol_v0.ts:3); the UI is the document owner (DES:73-74).
- Exit reason not carried in protocol: distinguishing exit 2/3/1 needs the process exit code and stderr (not in a push; Electron logs `engine-exit code=... signal=...` at main.ts:250).
- Settings path is cwd-relative by default (session.h:22); isolation needs `--settings`.
- No graceful `shutdown` command; EOF on stdin is the only clean stop (EP:19).
- Compatibility: protocol is v0; `hello.protocol` must be 0 or the Studio client ignores it (RealEngine.ts:263-264).
