<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0025 — The headless Player, Gate P1 (e), OSC and scripts, order (Planner run 2b)

**Status: final rulings** (`claude-planner`, run 2b; authority in
[`02_PLANNER_RUNS.md`](../docs/context/planner/02_PLANNER_RUNS.md)). The Claude Architect transcribes them
into contracts, issues and lanes without reopening them. It flags only conflicts with CONSTRAINTS "Fixed"
items, factual errors (with the source line) and contradictions with 0023 or 0024.
**Read at:** lab `main` `f0f19ba` (2026-11-26 ET); `wirescape-headless` `main` `39e244d`.
**Builds on:** [0023](0023-review-and-replan.md) R2.1–R2.5 and §7.2, and [0024](0024-test-repo-macros-modules.md)
§3 and §6 as amended by §9. Nothing in 0024 is reopened; this note has no "0024 amendments" section.
**Scope (owner, run 2b ask):** Q2 core (§2), Gate P1 (e) shapes (§3), Q4 (§4), Q8 (§6), Q7 guide list (§7),
Q5 boundaries only (§8). Review items from `docs/context/planner/03_PLANNER_REVIEW.md` §3.2 are placed where
they belong: modulation amounts §2.7, knob latency §2.8, Program Change §2.4, switch test §2.4, headless CI §5.

## 0. Summary
1. **The Player is one Python 3.11 process, standard library only,** that supervises one
   `wirescape-engine` child and one child per script, and serves the **Player API v1** over loopback HTTP:
   JSON commands, a state document and Server-Sent Events. It draws nothing. The **fake player** is the same
   service with a fake engine adapter, so the UI and the service develop against one contract (§2).
2. **`player.json` v1** has a setlist, controls, pages, a hardware map and a Program Change rule. Controls
   have four target forms: 0024's `macro` and `param`, plus **`modAmount`** for ordinary modulation cables
   (moved with `setModAmount`) and **`script`** for declared script controls. A `modAmount` target on a
   mapping cable is a bundle-check **error** (§2.7).
3. **Switching** goes through one arbiter: at most one `loadGraph` in flight, the latest request wins, and
   Program Change bursts are debounced (150 ms, last wins). Live values are written into the in-memory
   document before `loadGraph`, so nothing jumps after a switch or an engine restart (§2.4).
4. **Gate P1 (e)** is one opt-in command, `controllerStream`, and one push, `controller`: CC and OSC are
   latest-wins per key, Program Change and notes are a FIFO, with drop counters in `status.controller`. A
   launch-time **control OSC port** gives the Player patch-independent OSC input without a second socket
   owner (§3).
5. **Hardware knobs through `player.json` have a budget**: p99 ≤ 10 ms added latency, unmeasured until
   facts row H-f1. **In-patch mappings (Studio map mode) are the low-latency path** (§2.8).
6. **OSC naming:** `/ws/<name>` and `/ws/<name>/<n>`, names slugged from labels. OSC In gains a row
   `label`, a four-state indicator, a kind toggle and a generic default. **Script auto-sync is a Studio
   authoring feature**: linked rows are read-only, matched by label, removed outputs are disabled, and
   "unlink" (not overwrite) is how a user takes rows back. Scripts run with the owner's normal rights (§4).
7. **Order:** the fake-player track starts now and needs no engine change. The real-engine Player waits on
   Gate P0; hardware maps wait on P1 (e); scripts are Stage 3 but may start early (§6).

## 1. Facts this note rests on (checked at source, `f0f19ba`)
- **Process and protocol.** The engine is a stdio NDJSON child with bounded queues (256 commands, 256
  replies) and coalesced status (≤10 Hz) and telemetry (<30 Hz) slots (`host/sidecar/DESIGN.md`; scout S2 §1).
- **`setModAmount`** takes the connection identity `kind/from/to` and an amount in [-1, 1]; it is live,
  with a 5 ms transition and no generation change (`docs/specs/ENGINE_PROTOCOL.md:80`, `:125`).
- **Patch connections** carry `{"kind","from":{"module":<int>,"port"},"to":{"module":<int>,"port"}}`, and
  a modulation cable's `to.port` is the parameter ID (example patches; `ENGINE_PROTOCOL.md:268`).
- **Learn** holds one latest-wins CC observation with `deviceId`, `channel`, `controller` and `value`,
  captured with bounded lock-free work in the MIDI callback (`ENGINE_PROTOCOL.md:160`).
  `telemetry.monitor` covers only direct `osc.in`/`midi.in` cabling, at most 32 entries, addresses
  truncated to 64 bytes (`:168`). No Program Change is reported anywhere (scout S2 §7).
- **Client hello** opt-in exists for `configDeferred`, and a second client hello is refused
  (`ENGINE_PROTOCOL.md:205`).
- **`setOsc`** is refused `unavailable` (`host/sidecar/session.cpp:1281`). OSC LAN is a launch flag plus the
  patch (A91).
- **`--null-audio`** turns real audio and MIDI off, uses a fake MIDI observer that never consults physical
  devices, and keeps OSC on loopback (`session.cpp:272`, `:306-321`). **`--scripted-midi`** adds a
  device-off generator (clock, notes and a CC every 10 ms; `host/midi/scripted_backend.h:19-25`). It
  sends no Program Change.
- **Graph cap** is 64 nodes and 128 cables (`session.cpp:726`).
- **Desktop restarts** back off from 250 ms to 30 s with no limit (`apps/desktop/main.ts:15-19`). The
  headless `docs/REQUIREMENTS.md` line saying "stops after 3 crashes in 30 s" is stale; the headless PR of
  this run fixes it.
- **OSC In** ignores unknown config and row keys with bounded load diagnostics. A message matching only
  disabled rows is dropped by the worker. Up to 32 routes share listening ports (`modules/osc_in/README.md`).
- **Open lab work the order depends on:** P0a #619 (draft #627), P0b #620 (draft #660), OB-h2 #601
  (draft #638), OB-h3 #602 (#610), OB-h6 #604 (#648), #545 (`data_slots`), MB1 (#642), MB2 #358. No
  Gate P1 (e) issue exists (03 §2).

## 2. The Player (question 2 core)

### 2.1 Language, process model and files
- **Python 3.11 or later, standard library only at runtime** (Raspberry Pi OS Bookworm ships 3.11).
  Install means copying files plus systemd units; there is no `pip` step on the Pi. Development and CI may
  use pinned dev-only packages listed in `requirements-dev.txt` (a JSON Schema validator, Playwright).
- **One `asyncio` process, `wsplayer`.** Its children are one engine and one process per running script.
  The reference UI is **not** a child: it is a separate process (a kiosk browser) under its own systemd
  unit, so a UI crash cannot reach the Player or the engine.
- **CLI:**
  - `python -m player run --bundle-root DIR --state DIR --engine PATH [--engine-arg ARG]…`
  - `python -m player fake [--bundle DIR] [--port N]` (§2.6)
  - `python -m player check BUNDLE [--lab DIR]` (§2.7)
  - `python -m player install SRC --state DIR` (atomic copy, §2.3)
- **Engine arguments.** The Player always passes `--settings <state>/engine-settings.json` (absolute, R2.3 f).
  Device consent (`--confirm-audio`, `--confirm-midi`, `--confirm-lan`) is never a Player default. The
  owner's systemd unit passes it with `--engine-arg`, and CI passes `--null-audio`.
- **Logs** go to stdout and stderr, which means the journal under systemd. The Player drains the engine's
  stdout and stderr continuously (R2.4) and forwards stderr lines to its own log with an `engine:` prefix.

### 2.2 Supervision (R2.4, made exact)
- **Start:** spawn the engine, wait for `hello` (timeout 10 s, then treat as a crash). Then send
  `controllerStream` when the capability is advertised (§3), then `loadGraph` with the composed document
  (§2.4). Nothing is replayed separately.
- **Restart:** the delay starts at 250 ms, doubles to a 30 s cap and never gives up. It resets to 250 ms
  after 30 s of healthy `status`. The state document shows `engine.restarts` and the last exit code and
  signal.
- **Hang:** a `status` gap over 1 s, or `status.audio.state == "stalled"` for over 1 s once P0a merges, is a
  hang. The Player sends SIGKILL and restarts. Before P0a, only the gap applies.
- **Stop:** close stdin, wait 2 s, then SIGKILL. On SIGTERM the Player saves state (§2.3), stops scripts
  (§4.5), stops the engine this way and exits 0.
- **systemd:** `wirescape-player.service` uses `Type=notify`, `Restart=always`, `KillMode=mixed`,
  `TimeoutStopSec=8` and `WatchdogSec=10`.
  - `READY=1` is sent when the API listens, not when the engine is up, so a broken engine never blocks the
    UI from showing the fault.
  - `WATCHDOG=1` is sent every 2 s from the event loop, and only while the loop's measured lag is under 2 s.
    `sd_notify` is a few lines over `AF_UNIX`; no library is used.

### 2.3 Boot, state and saves
- **State directory** (`--state`, `StateDirectory=` under systemd):
  - `state.json`: `{"format":"wirescape.player.state","version":1,"bundle":"<name>","index":<int>,"values":{…}}`;
  - `state.good.json`: a copy written after each successful boot;
  - `engine-settings.json`: the engine's own file;
  - `bundles/<name>/`: installed bundles.
- **Every write is atomic:** write `<file>.tmp` in the same directory, flush, `fsync`, `os.replace`, then
  `fsync` the directory. Values save 2 s after the last change, on every switch and on SIGTERM. That is at
  most one write per 2 s.
- **Boot:** read `state.json`. If it is missing or unreadable, use `state.good.json`. If that fails too, use
  the first installed bundle at index 0, and with no bundle, run the engine with no patch and say so in
  the state. Boot needs no input.
- **The Player never writes `patches/` or `scripts/`.** It writes `player.json` only through `config.put`
  (Stage 2, validated, previous file kept as `player.json.bak`) and `presets/` only for snapshots.
- **`install`** copies a bundle to `bundles/<name>.tmp-<n>/`, fsyncs it, runs `check` (errors refuse),
  renames any existing `<name>` to `<name>.old`, renames the new copy into place and deletes `.old`. A
  power cut leaves either the old or the new bundle, plus a leftover temp folder that the next boot deletes.

### 2.4 Live values, switching and Program Change
- **Live values** are kept per setlist entry, keyed by target:
  - `param:<module>:<param>` (a macro resolves to `param:<macro module>:knob<k>`);
  - `mod:<from module>:<from port>><to module>:<param>`;
  - `script:<file>:<control>`.

  They are plain values. A `recall` of `"last"` (the default) keeps them across switches and reboots;
  `"patch"` clears them on every load of that entry.
- **Composition.** Before every `loadGraph`, the Player copies the patch document in memory and writes the
  live values into it: `modules[i].parameters[param]` and the modulation connection's `amount`. The file
  on disk is never touched. A switch or an engine restart is therefore **one `loadGraph`, with no jump** after
  the fade, and no separate replay.
- **The switch arbiter:**
  - At most one `loadGraph` is in flight. A request while one is in flight replaces the single `pending`
    target. When the ACK arrives, the Player switches once more if `pending` differs from the current
    entry. There is never a queue of swaps.
  - `next` and `prev` count from the latest requested index, so three quick presses move three entries.
  - A refused `loadGraph` keeps the previous patch, since the engine leaves its graph untouched. The entry
    shows the refusal reason and the error stays in the state until the next successful switch.
- **Program Change and controller switches** pass a debounce before the arbiter: each event restarts a
  timer of `debounceMs` (default **150 ms**, range 0–1000), and when it fires the last target wins. UI
  selection skips the debounce, but not the arbiter. The engine never coalesces PC (0023 R2.3 e), so the
  Player is the one place where a burst collapses.
- **A running sequencer at a switch.** The engine's replacement fades out, panics the old graph and starts
  the new patch's sequencers from their own start (0023 §2.1). OB-h2's gate release (R2.2 c) covers OSC
  Out. The Player adds no transport sync until TR1h (P1 i) exists.
- **The Player's switch test reuses these OB-h3 rows (0022 §5, r2.13):**
  1. the ACK is `ok`;
  2. the new OSC In route listens and a sentinel sent after the ACK arrives within 50 ms;
  3. no gate or MIDI note is held after the switch;
  4. the captured output fades to zero before the swap and rises from zero after it (engine fade, no new
     threshold);
  5. the OSC Out gate row (nonzero gate rows send 0 once).

  It drives the switches through the Player API `select` rather than raw `loadGraph`, with
  `examples/patches/basics-08-clocked-groove.json` running across each switch.
  - Player-only rows: a burst of 20 Program Changes within 100 ms leads to at most 2 `loadGraph` commands
    and ends on the last PC's entry; the document sent for a patch with live values carries those values.
  - H1 runs 50 switches; H2 runs 200 (§5.3).

### 2.5 Player API v1
**Transport.** HTTP/1.1 on `127.0.0.1:8770` (`--api-port`). There is no LAN binding in v1 (§9). Three
endpoints, plus static files:

| Endpoint | Use |
|---|---|
| `GET /api/v1/state` | the whole state document |
| `POST /api/v1/command` | one command: `{"type":"…", …}` → `{"ok":true,"result":{…}}` or `{"ok":false,"code":"…","message":"…"}` (HTTP 200 for both; 400 only for malformed JSON) |
| `GET /api/v1/events` | Server-Sent Events: `state`, `values`, `status`, and `controller` when `?controller=1` |
| `GET /ui/…` | the reference UI's static files |

Every stream starts with a `state` event. SSE is plain HTTP, browsers read it natively, and the standard
library can serve it, so no WebSocket code exists.

**Versioning.** `state.api` is `"1.<minor>"`.
- Additive fields, commands, events and codes bump the minor. Clients ignore what they do not know.
- A breaking change gets `/api/v2/`, served beside v1 for at least one Player release.
- The contract is `api/player-api.v1.schema.json`. Every command, reply and event of both the real and the
  fake Player is validated against it in H0. A PR that changes the API changes the schema, `docs/API.md`
  and the fake in the same PR.

**State document** (top-level keys; H-1 writes the full schema):
- `api`, `rev` (an integer that increases on every change);
- `player`: `version`, `uptimeS`;
- `engine`: `state` (`starting|running|restarting|stalled|stopped`), `restarts`, `lastExit`
  (`code`, `signal`, `at`), `audio` (a copy of `status.audio`), `capabilities`;
- `bundle`: `name`, `title`, `check` (`ok`, counts of errors and warnings);
- `setlist`: entries with `index` (0-based), `title`, `patch`, `program`;
- `current`: `index`, `switching`, `pending`, `error`;
- `pages`: `title` and a list of control IDs;
- `controls`: by ID, each with `label`, `kind`, `target`, `min`, `max`, `step`, `unit`, `taper`,
  `choices`, `value`, `norm`, `display`, `resolved` (false when the target is absent from the loaded patch);
- `scripts`: `file`, `state` (`running|stopped|crashed|restarting`), `restarts`, `controls`;
- `midi`: `devices` with `enabled`; `osc`: `controlPort` and the route states;
- `warnings`: the live list (unresolved targets, dropped controller events, refusals).

**Commands (v1.0):**
| Type | Fields | Notes |
|---|---|---|
| `select` / `next` / `prev` | `index` (select) | through the arbiter (§2.4) |
| `set` | `control` or `target`; `value` (plain) or `norm` (0..1 via the parameter's taper) | `target` lets the UI set any parameter or cable not in `player.json` |
| `reset` | optional `control` or `target` | back to the patch's value; no field resets all |
| `panic` | — | engine `panic` |
| `params.list` | — | modules, parameters (with catalogue metadata, current value and `mapped` when a mapping owns it) and the modulation cables (with `mapping: true/false`) of the loaded patch |
| `bundle.list` / `bundle.load` / `bundle.check` | `name` | `load` switches bundle through the arbiter |
| `audio.devices` / `audio.select` / `audio.buffer` / `audio.rate` | `deviceId`, `frames`, `hz` | engine passthrough |
| `midi.devices` / `midi.enable` | `deviceId`, `on` | engine passthrough |
| `engine.restart` | — | counted as a restart, with no backoff |
| `script.start` / `script.stop` / `script.restart` | `file` | `unavailable` until Stage 3 |
| `config.get` / `config.put` | `json` | Stage 2; `put` validates and saves atomically |
| `fake.inject` | `what`: `engineCrash`, `engineStall`, `scriptCrash`, `controller` (+ `event`) | **fake only**; the real Player answers `unavailable` |

**Error codes:** `invalid`, `not-found`, `busy`, `refused`, `unavailable`, and `engine` (with
`engineCode` from the engine's reply).

**Events.**
- `state` carries the whole document. It is sent on connect and on every structural change (bundle,
  switch, script set, devices).
- `values` carries `{"rev":n,"values":{"<control or target key>":{"value","norm"}}}`, coalesced to at most
  30 Hz.
- `status` carries the `engine`, `scripts` and `osc` health at most 4 Hz.
- `controller` carries the raw observations of §3 at most 30 Hz, for a UI that learns `player.json`
  bindings.

**Taper.** `norm` uses the lab's parameter taper definitions. The Player's `taper.py` cites the lab
source file and commit and is tested against values the lab catalogue produces at `LAB_PIN`.

### 2.6 The fake player
- `python -m player fake` runs **the same API server and Player core** with a `FakeEngine` adapter in place
  of the engine client:
  - it accepts the engine commands the Player sends and checks them against the bundle;
  - it emits `hello` with a catalogue snapshot taken from the engine at `LAB_PIN` and committed as
    `tests/data/catalogue.json`;
  - it emits synthetic `status` at 10 Hz;
  - it answers `fake.inject` with crashes, stalls and controller events.
- The fake bundle is `examples/bundle/` with the six example patches, a `player.json` exercising every
  target form, and `generative_ws.py`.
- **Contract tests** run the same command and event suite against the fake (H0) and the real engine
  (H1). A behaviour that differs is a defect in the fake.

### 2.7 `player.json` v1
```json
{
  "format": "wirescape.player", "version": 1, "title": "Set name",
  "setlist": [
    { "patch": "patches/song-a.json", "title": "Song A", "program": 0, "recall": "last",
      "controls": [
        {"id": "cut", "label": "Cutoff", "target": {"param": {"module": 9, "param": "cutoff"}}},
        {"id": "wob", "target": {"modAmount": {"from": {"module": 10, "port": "out"},
                                               "to": {"module": 9, "param": "cutoff"}}}}
      ],
      "pages": [{"title": "Song A", "controls": ["cut", "wob"]}],
      "scripts": [{"file": "scripts/generative_ws.py", "port": 9000}] }
  ],
  "controls": [
    {"id": "m1", "target": {"macro": {"page": 1, "knob": 1}}},
    {"id": "dens", "label": "Density", "target": {"script": {"file": "scripts/generative_ws.py", "control": "density"}}}
  ],
  "pages": [{"title": "Main", "controls": ["m1", "dens"]}],
  "hardware": [
    {"source": {"midi": {"device": "*", "channel": 1, "cc": 74}}, "control": "m1", "takeover": "pickup"},
    {"source": {"osc": {"address": "/ws/knob/1", "arg": 0, "min": 0, "max": 1}}, "control": "dens"},
    {"source": {"midi": {"device": "*", "channel": "any", "note": 36}}, "action": "next"}
  ],
  "programChange": {"enabled": true, "device": "*", "channel": "any", "debounceMs": 150},
  "osc": {"controlPort": 9100}
}
```
- **Target forms:**
  - **`macro`** (0024 §6): `page` 1.. is the *page*-th `essentials.macro` module in the patch's `modules`
    array; `knob` 1..8 is the parameter `knob<k>`. It is patch-independent and resolves on every load.
  - **`param`** (0024 §6): module ID (the patch's integer node ID) and parameter ID. It reaches any
    parameter, setParam-only ones included. It is patch-specific, so it is allowed only in a setlist
    entry's `controls`.
  - **`modAmount`** (03 §3.2.1, new): one ordinary modulation cable. The identity is
    `from.module`, `from.port`, `to.module` and `to.param`, which is the patch connection's `from` plus
    `to` with `to.port` as the parameter. It is exactly what `setModAmount` takes, so it needs no new
    patch key. The value is the amount in [-1, 1], moved live with `setModAmount`. Patch-specific: entry
    `controls` only.
  - **`script`**: a declared control of a script the entry runs (§4.5). The value goes to the script, not
    the engine.
- **Mapping cables stay Studio-only.** A mapping cable is a modulation cable whose source module type is one
  of 0024 §3.2's mapping sources: `essentials.macro`, `midi.cc_to_cv` or `osc.in`. The Player keeps that
  list in one constant and never reads Studio's `ui.mappingNodes`. If the lab later marks mapping sources
  in the catalogue, the constant gives way to that marker.
- **Global controls** (top level) may use only `macro` and `script` targets. Entry controls may use all
  four. IDs are `[a-z0-9_-]{1,32}` and unique across the global list and each entry.
- **Pages** are UI slots: global pages first, then the loaded entry's pages. There is no limit on pages
  or controls.
- **Labels:** the `label` field, else the Macro `labels` data for macros (0024 §3.1), else
  `"<module name> <id> · <parameter name>"`. The Player may read `ui.labels` for a display name only. No
  behaviour depends on any `ui` key.
- **Hardware map:**
  - **Sources:** `midi` with `device` (a glob over the engine's `deviceId`, written by the owner; default
    `"*"`), `channel` (1–16 or `"any"`) and one of `cc` or `note`; or `osc` with an exact `address`, `arg`
    (default 0) and `min`/`max` (default 0..1).
  - **Each binding** names a `control` or an `action`: `next`, `prev`, `panic`, or `{"select": n}`.
  - **Values:** CC maps to `norm = value/127`. `takeover` is `"jump"` (default) or `"pickup"`, which
    ignores the knob until it crosses the current value. A button fires on CC ≥ 64 after < 64, or on note-on.
  - **OSC sources** arrive through the engine's control port (§3.3). `osc.controlPort` 0 or absent means
    none.
- **Program Change:** if any entry has `program`, PC *n* selects that entry; otherwise PC *n* selects index
  *n*. A PC with no entry is ignored and counted in `warnings`.
- **The Player moves every target live and never edits structure:** `setParam`, `setModAmount`, or a
  value sent to a script. It never creates cables or changes ranges (0024 §6.2).
- **Bundle check** (`python -m player check`) exits non-zero only on an error, like OB-h6.
  - With `--lab DIR` it also runs the lab's `tools/patch_library.py check` on `patches/`, once OB-h6
    merges.
  - Errors:
    - schema violation;
    - a missing patch or script file;
    - a `param` or `modAmount` target that does not exist in its entry's patch;
    - **a `modAmount` target on a mapping cable**;
    - a global control with a patch-specific target;
    - a duplicate `program`;
    - the same hardware source bound twice;
    - a patch OSC In on `osc.controlPort`.
  - Warnings (0024 §6.5):
    - a macro address that resolves in no patch;
    - a `param` binding on a parameter a mapping owns;
    - a CC bound in `player.json` that the patch also maps.
  - Warnings (this note):
    - a script output with no matching OSC In row in the entries that run it (§4.4).
  - Info:
    - a hardware CC bound to a `MODULATABLE` `param`: "an in-patch mapping has lower latency" (§2.8).
- A patch's macros work with no `player.json` (0024 §6.6). A bundle with no `player.json` plays its
  `patches/` in name order.

### 2.8 The hardware-knob path and its latency budget
- **Path:** device → engine (owns the device) → `controller` push → Player → `setParam` → engine queue.
- **Budget:** at most **10 ms added latency at p99**, measured from the event's ingress time `t` (§3.2) to
  the Player receiving the `setParam` ACK. The load is 100 CC/s across 8 controllers on a Pi 5, with the
  reference UI showing the Play page, for 10 minutes.
- **Facts row H-f1** records it before Player v1. It runs device-off with `--null-audio --scripted-midi`
  on the Pi (the owner's run) and as a diagnostic on hosted arm64. **It stays unmeasured until then.**
  If the scripted source cannot produce 8 controllers, the P1 (e) task extends its test-only sequence.
- **Rule:** in-patch mappings (Studio map mode) are the low-latency path, because they run inside the engine
  with no client. `player.json` is for patch-independent controls, setParam-only targets, cable amounts and
  script controls.
- **Overturn:** if H-f1 fails, the bundle check's info row becomes a warning that suggests the in-patch
  mapping. The Player still never edits patches. If H-f1 passes with a wide margin, the info row is
  dropped.

### 2.9 The reference UI
- **Technology (owner question C, decided): a kiosk web page.** Plain HTML, CSS and JavaScript in `ui/`,
  with no framework and no build step, served by the Player at `/ui/`. A kiosk browser opens it full
  screen under `wirescape-ui.service` with `Restart=always`. The browser and compositor packages belong in
  the install guide, not in code.
- **800 × 480 touch first:** no hover, touch targets of at least 48 px, a dark theme, and every value
  readable at arm's length.
- **Menus (complete):**
  - **Play:** pages of controls;
  - **Setlist:** select, next, previous;
  - **Parameters:** every module, parameter and ordinary cable amount of the loaded patch, settable;
  - **Scripts:** state, controls, restart;
  - **Devices:** audio device, rate, buffer; MIDI enables;
  - **Status:** engine, OSC routes, controller drops, bundle check;
  - **System:** bundles, engine restart.
- **Pi cost limit (facts row H-f2, before Player v1, unmeasured):** with the Play page updating at 30 Hz
  for 30 minutes:
  - engine dropouts equal the UI-off baseline on the same patch;
  - the UI process tree averages ≤ 25 % of one core;
  - its RSS stays ≤ 350 MB.

  If it fails, try a lighter web engine with the same page first. A native UI is the last resort.
- **UI tests** run in Playwright against the fake player (H0 when `ui/` changes, always in H1).

### 2.10 Player v1 gates (each a test; tiers in §5.3)
| Gate | Requirement (`docs/REQUIREMENTS.md`) | Test |
|---|---|---|
| PG1 | engine restarts, reloads patch and values | kill -9 the engine (H1): the restart sequence is `hello` → `controllerStream` → `loadGraph(composed)`; delays follow §2.2 |
| PG2 | heartbeat detects a hang | fake `engineStall` (H0); after P0a, the lab's spinning test module (H1): killed within 1.5 s |
| PG3 | UI crash never stops audio | SSE clients killed mid-stream while switching (H1); the engine is untouched |
| PG4 | script crash never stops audio | a crashing script restarts with backoff and its gates get 0 (H0 with a UDP listener; H1 with the engine) |
| PG5 | boot to last bundle and patch | Player restart with state (H1); corrupt `state.json` falls back to `state.good.json` |
| PG6 | atomic saves, power-cut safe | kill -9 the Player 500 times during value saves (H1): `state.json` always parses |
| PG7 | switching, no stuck notes | §2.4 switch test |
| PG8 | systemd watchdog | a blocked event loop stops `WATCHDOG=1` (H0 unit test); service restart on the Pi (H2) |
| PG9 | bundle check | §2.7 rows, one test each |
| PG10 | long soaks | H2 on the Pi, 4–12 h: flat RSS of Player and engine, flat CPU in silence, zero OSC drops, #326 closed (0023 §7.2 Stage 3) |
Player v1 also needs Gate P0 merged, P1 (e)–(h) merged, and facts rows H-f1 and H-f2 recorded.

### 2.11 What would overturn §2
- **Python on the Pi cannot hold the knob budget** (H-f1 fails because of the Player, not the engine). Then
  first move controller handling to a dedicated thread. Rewriting in another language is the last step.
- **The kiosk browser fails H-f2** with a lighter engine too. Then use a native UI against the same API;
  the API does not change.
- **SSE proves unreliable** on the chosen browser. Then add a WebSocket transport carrying the same events
  as a minor version.
- **The owner wants a remote UI** (phone or laptop). Then a LAN API with a token (§9).

## 3. Gate P1 (e): the controller input stream (message shapes, final)
This section is the body of the Gate P1 (e) lab issue. It is additive and capability-gated in protocol v0
(R2.1, SR17). The engine stays the only owner of MIDI and OSC devices (R2.3 e). The capture runs at
ingress on the MIDI and OSC worker threads, never on render, with the bounded lock-free work Learn already
uses: no allocation, locks, I/O or JSON in the MIDI callback. Tables are allocated at session start.

### 3.1 Capability and command
- **`hello.capabilities` gains `"controllerStream"`.** With the control port (§3.3) it also gains
  `"controllerStream.controlPort"`.
- **Command** (control class, immediate, no generation change):
```
> {"v":0,"id":"c1","type":"controllerStream","kinds":["cc","pc","note","osc"],"oscUnmatched":false}
< {"v":0,"session":"s1","re":"c1","ok":true,"gen":"5","result":{"kinds":["cc","note","osc","pc"],"oscUnmatched":false}}
```
  - `kinds`: a subset of `"cc"`, `"pc"`, `"note"`, `"osc"`. An unknown or repeated kind is `invalid`.
    `[]` turns the stream off.
  - `oscUnmatched` (boolean, default `false`): also report OSC messages on a patch route that match no
    row. Studio sets it only while map mode's OSC learn is armed (0024 §6).
  - The result echoes the normalized setting, with kinds sorted.
  - The setting is session-scoped. It is off at session start, survives graph commits, and is cleared by an
    engine restart (a new session). The Player re-sends it after every `hello`.
  - Without the capability, the command is refused like any unknown type.

### 3.2 The `controller` push
```
< {"v":0,"session":"s1","type":"controller","gen":"5","events":[
   {"kind":"cc","t":81234567,"deviceId":"Test MIDI 1|test:midi:0","channel":1,"controller":0,"value":2},
   {"kind":"pc","t":81234601,"deviceId":"Test MIDI 1|test:midi:0","channel":1,"program":5},
   {"kind":"noteOn","t":81240012,"deviceId":"Test MIDI 1|test:midi:0","channel":10,"note":36,"velocity":100},
   {"kind":"noteOff","t":81290450,"deviceId":"Test MIDI 1|test:midi:0","channel":10,"note":36,"velocity":0},
   {"kind":"osc","t":81291002,"port":9000,"address":"/ws/knob/1","args":[0.42],"matched":true},
   {"kind":"osc","t":81291500,"port":9100,"address":"/ws/next","args":[],"matched":false}
 ]}
```
**Common fields.**
- `kind` is one of `cc`, `pc`, `noteOn`, `noteOff`, `osc`. Clients ignore kinds they do not know; new
  kinds arrive with a new capability name.
- `t` is the ingress time in integer microseconds of the host steady clock (`std::chrono::steady_clock`).
  On Linux this is `CLOCK_MONOTONIC`, the same clock as Python's `time.monotonic_ns()`, so a client on the
  same machine can measure latency. On other systems it is diagnostic only.
- `gen` is the graph generation at flush. `matched` refers to that graph.

**MIDI events.** They come only from enabled MIDI devices (`setMidiEnabled`), and real devices only with
`--confirm-midi`. `deviceId` is the engine's device ID as in `status.midi.devices`. `channel` is 1–16.
- `cc`: `controller` 0–127, `value` 0–127. **Latest-wins** per (`deviceId`, `channel`, `controller`).
  There is no 14-bit pairing, NRPN or RPN, as with Learn. Bank Select is ordinary `cc` 0 and 32.
- `pc`: `program` 0–127. **FIFO, never coalesced.**
- `noteOn`: `note` 0–127, `velocity` 1–127. **FIFO.** A note-on with velocity 0 is reported as
  `noteOff` with velocity 0.
- `noteOff`: `note`, `velocity` 0–127. **FIFO.**
- Clock, start, stop, pitch bend, pressure and SysEx are not reported. They may be added with new
  capability names.

**OSC events.** They come from patch OSC In routes and the control port (§3.3), and only from sockets the
engine already listens on.
- `port` is the receiving UDP port. `address` is the full address, at most 128 bytes. A longer address is
  dropped and counted in `oversize`, never truncated, because learn must see the real address.
- `args` holds up to 4 numbers, from the OSC types `i`, `f`, `d`, `h`, `T` (1) and `F` (0). `"more":true`
  is present when any argument was skipped (another type or beyond 4). A message with no arguments has
  `args:[]`.
- `matched` is `true` when the message matched at least one enabled row of a patch OSC In on that port.
  A message matching only disabled rows is not reported, which matches the worker dropping it.
  Unmatched messages on a patch port are reported only with `oscUnmatched:true`. Control-port messages are
  always `matched:false` and always reported when `osc` is subscribed.
- Bundles are unpacked into one event per message; timetags are ignored.
- **Latest-wins** per (`port`, `address`).

**Order and coalescing.**
- `events` are in ingress order. A latest-wins entry sits at the position of its latest update within the
  flush, so a Bank Select CC that arrived before a PC is listed before it.
- Latest-wins applies within one flush, so a fast repeat of an OSC trigger inside one ≤ 5 ms window counts
  once (0023 R2.3 e).

**Flush and bounds.**
- The control thread flushes on each main-loop iteration, so at most every 5 ms, and only when events are
  pending.
- The push uses **one coalesced writer slot**, like `status`, not the reliable reply queue. While the
  previous push is unwritten, events stay in the tables.
- The latest-wins table holds **128 keys** (CC and OSC together). A new key arriving at a full table is
  dropped and counted in `latest`; existing keys keep updating.
- The FIFO holds **256 events**. The newest event arriving at a full FIFO is dropped and counted in `fifo`.
- Each flush drains both completely, so a push carries at most 384 events (far under the 2 MiB line cap).

### 3.3 The control OSC port (P1 e2)
- **Launch option `--control-osc-port N`** (1024–65535; default off). It opens one more listener in the
  sidecar's OSC host, with no rows. Its messages reach only the controller stream. It counts as one of the
  32 routes and appears in `status.osc.routes` as `{"module":"control",…}` with `received` and `dropped`.
- **Binding:** `127.0.0.1`. It binds the wildcard only with both `--confirm-lan` and `--control-osc-lan`.
  There is no runtime change and no `setOsc` (A91 stands).
- **A patch route on the same port shares the socket** under today's sharing rule. The Player's bundle check
  makes that an error (§2.7), so in practice the ports differ.
- **Why:** patch-independent OSC (a "next patch" button, a script-control knob) must work whatever patch is
  loaded, and a second socket owner in the Player would break R2.3 (e).

### 3.4 Status
When the stream is on, `status.controller` is present (additive):
```
"controller":{"kinds":["cc","osc","pc"],"oscUnmatched":false,"events":1234,"dropped":{"fifo":0,"latest":0,"oversize":0}}
```
The counters are cumulative per session and do not wrap below 2^53. The field is omitted while the stream
is off, so the default status bytes and the S0 snapshot do not change.

### 3.5 Acceptance (test first; devices off)
1. With the stream off (the default), no `controller` push appears; `kinds:[]` stops a running stream.
2. Through `--scripted-midi`, CCs on several controllers deliver the last value per key, with
   `dropped.latest` at 0.
3. Program Changes injected through a test-only scripted sequence (extended if needed) arrive in order
   with none coalesced. 300 in one window with the writer held give 256 events and `dropped.fifo` 44.
4. A note-on with velocity 0 is reported as `noteOff`.
5. OSC on loopback:
   - a matched row gives `matched:true`;
   - an unmatched address is absent with `oscUnmatched:false` and present (`matched:false`) with `true`;
   - a message matching only a disabled row is absent;
   - a 129-byte address adds 1 to `oversize`.
6. Control port: an event with `matched:false` and no patch loaded. `status.osc.routes` reports the
   loopback bind without the LAN flags. No LAN in CI.
7. `allocation_watch` shows zero allocations in the MIDI capture path, and the OSC worker stays within its
   per-poll budget.
8. At 800 events/s, `status` cadence keeps its gap under 150 ms and telemetry cadence is unchanged.
9. The schema, spec (`ENGINE_PROTOCOL.md`), generated files and fixtures are updated, with a T-example
   in the spec.

- **Owner:** a PV-class lab task in Gate P1 (OB contract), lane B2 after P0b #620 (same files), merged after a
  **Claude contract review**.
- **e2 may be a second PR in the same issue.**
- **Consumers:** MM4 replaces map mode's hidden Monitor with this stream once the capability is advertised
  (0024 §3.7), and the Player's hardware map uses it (§2.7).

## 4. OSC and scripts (question 4)

### 4.1 Naming (owner: the simplest)
- **Two forms only:** `/ws/<name>` (mono) and `/ws/<name>/<n>` (poly channel *n*, 1-based; the number is
  always last).
- **`<name>`** is the label slugged: lowercase, every run of characters outside `a-z0-9` becomes `_`, with
  no leading or trailing `_`, and at most 32 characters. "Chaos note" becomes `chaos_note`.
- **Values:**
  - notes are MIDI numbers 0–127, mapped to 1 V/oct with C4 = 0, as MIDI to CV does;
  - CV is 0–1;
  - gates are 1 and 0;
  - triggers carry no value.
- **A voice is three names:** `<name>_pitch`, `<name>_gate` and `<name>_vel` (`_vel` is optional), each
  `/ws/<name>_x/<n>` for voice *n*. The unnamed default voice uses `pitch`, `gate` and `vel`. The existing
  "Script (/ws/…)" preset (0022 §7) and `generative_ws.py` already follow this, unchanged.

### 4.2 OSC In rows and the indicator (unfreezes OSC In)
- **`label`:** an optional row key, a string of at most 32 bytes. The engine treats it as known and ignores
  it, without a diagnostic. Studio shows it as the output's name on the canvas and in the row list, and
  writes it only when set. Old patches are unchanged.
- **Indicator:** one dot per row, from `status.osc.routes[i].rows`. That is an additive field of up to 8
  `{received, ageMs}` entries, counted on the OSC worker thread at match time (`ageMs` is `null` before the
  first message). The colours:
  - **red:** the route state is `port-busy` or `lan-not-confirmed`;
  - **grey:** the row is disabled, or has received nothing since the last commit;
  - **amber:** the row's `timeout_ms > 0` and `ageMs > timeout_ms`;
  - **green:** otherwise, pulsing bright for 250 ms after `received` advances.
- **Quick kind toggle** (cv, gate, trigger) in the row list. It edits the ordinary row config through
  `applyGraph`.
- **Generic default.** Studio writes the default rows explicitly into every new OSC In:
  `/ws/knob/1` … `/ws/knob/8`, cv 0–1, smoothing 5 ms, timeout 0, stale hold. That is today's default shape
  with the `/pico1` prefix replaced. Pico and TouchOSC become built-in presets beside "Script (/ws/…)".
- **The engine's fallback** for a config-less module keeps its bytes until OB-h6 shows that no shipped or
  example patch relies on it. Then it changes in its own lab task.
- **OSC Out defaults (owner question C, decided): rename now, in the same task, for new modules only.**
  Studio writes `/ws/out/<n>`-style defaults into new OSC Out modules. Existing patches keep their bytes.
- **Presets:** OB-h5 #603's user presets stand. A script never writes a preset; it prints its rows (§4.3).

### 4.3 The script declaration and `--print-config`
- **Order inside a script:** it declares outputs and controls through the helper library, then calls
  `ws.start()`.
- `python -I script.py --print-config` stops at `ws.start()`, prints one JSON document to stdout, opens no
  socket and exits 0. Studio and the Player call it with a 5 s timeout. It also works outside Wirescape.
```json
{"format":"wirescape.script","version":1,"name":"generative_ws","port":9000,
 "outputs":[
   {"name":"Kick","address":"/ws/kick","kind":"trigger"},
   {"name":"Filter","address":"/ws/filter","kind":"cv","outMin":0,"outMax":1},
   {"name":"Lead","kind":"voice","voices":4,"velocity":true,
    "addresses":{"pitch":"/ws/lead_pitch/*","gate":"/ws/lead_gate/*","vel":"/ws/lead_vel/*"}}],
 "controls":[{"id":"density","type":"knob","label":"Density","min":0,"max":1,"default":0.5}],
 "oscIn":[{"port":9000,"rows":[
   {"label":"Kick","pattern":"/ws/kick","argument":0,"kind":"trigger","input_min":0,"input_max":1,"output_min":0,"output_max":1,"smoothing_ms":0,"timeout_ms":0,"stale":"hold"}]}]}
```
- **`oscIn`** is generated by the helper from `outputs`, as a list of OSC In configs of at most 8 rows
  each, in declaration order. It is the **single source** for rows:
  - cv: input 0..1 → `outMin..outMax`, smoothing 5 ms;
  - trigger: as preset row 2;
  - gate: `timeout_ms` 2000, `stale` zero;
  - pitch: as preset row 1;
  - vel: 0..1.

  Each row's `label` is the output name, with ` pitch`, ` gate` and ` vel` appended for voices.
- **Control types:** `knob`, `slider`, `toggle`, `button`, `dropdown` (`choices`), `number`, `text`,
  `notes` (a note grid), `label`. Each has `id`, `label` and the type's range or default fields. The 0015
  generic panel draws them (§4.5).

### 4.4 Auto-sync (Studio authoring; owner question C "overwrite vs unlink", decided)
- **A link** says that one or more OSC In modules (in order) are fed by one script. It lives in the
  Studio-only key `ui.scriptLinks: {"<moduleId>": {"script": "<file name>", "part": <k>}}`. The engine and
  the Player ignore it. A patch with or without the link runs identically, and the script is never required.
- **Sync** runs on link, on each script save in the editor, and on "Sync now". It reads `--print-config`
  and, for each linked module, `oscIn[part]`:
  - **Match by label:** a declared row updates the linked row with the same `label` in place (address,
    kind, ranges), so cables never jump.
  - **New outputs** take the first row with no label that is disabled or empty. If none is left, Studio says
    so and offers to link one more OSC In (the 8-row limit: use poly rows or a second module).
  - **Removed outputs** set their row `enabled:false` and keep its label and cables. Rows are never shifted
    or deleted.
- **Linked rows are read-only** in the row editor, under a "Linked to <script>" banner. Sync always
  overwrites them. To edit by hand, the user **unlinks**, and the rows stay exactly as they are. There is
  no merge of hand edits.
- **The Player never syncs or rewrites patches.** Its bundle check warns when a script's outputs have no
  matching row in the entries that run it (§2.7).
- **Bundle export** (lab row SC4) turns links into `player.json` entry `scripts`.

### 4.5 The runner, the helper library, permissions, controls and timing
- **One implementation:** `scripting/wsrun.py` (GPL-3.0-only) is both a library (the Player imports it) and
  a CLI. Studio desktop spawns `python -I wsrun.py serve`, which speaks NDJSON on stdio to the Electron main
  process. The helper `scripting/ws.py` is **MIT**, so user scripts may copy it freely.
  - Home: `wirescape-headless`. The lab desktop vendors both files under `apps/desktop/scripting/` with a
    `VENDORED_FROM` line naming the headless commit, updated deliberately, one PR per bump (the `LAB_PIN`
    pattern in reverse). There is no shared package.
- **Per script:** one process, `python -I -u <script> --ws-runner`, with the working directory set to the
  script's folder and only these variables added: `WS_OSC_HOST=127.0.0.1` and `WS_OSC_PORT=<port>`.
  - stdin carries NDJSON controls: `{"type":"control","id":"density","value":0.7}` and `{"type":"stop"}`.
  - stdout lines starting with `@ws ` are structured: `declare` once at start, then `heartbeat` (at most
    1/s, with a drop count). Every other line is log.
- **Stop:** send `{"type":"stop"}`, wait 500 ms, terminate, wait 2 s, kill. Then **the runner itself
  sends 0 to every declared gate address**, from the declaration it received. This holds even after a crash.
- **Restart:** the same backoff as the engine (250 ms doubling to 30 s), no limit, with the count shown in
  the state. A crash, flood or replacement never touches the engine.
- **Flood:** the helper caps sends at 1000 messages/s and counts drops. A script that bypasses the helper is
  bounded by the engine's per-poll OSC budget and counted in `status.osc`.
- **Helper API (standard library only):**
  - outputs: `ws.trig(name)`, `ws.gate(name)`, `ws.cv(name, out_min=0, out_max=1)`,
    `ws.voice(name="", voices=1, velocity=True)`;
  - controls: `ws.knob(label, lo, hi, default)` and the other types of §4.3;
  - lifecycle: `ws.start()`, `ws.sleep(s)`, `ws.wait_until(t)`.

  Outputs return objects with `.send(...)`, `.on(...)` and `.off(...)`. Controls have a `.value` updated
  by a stdin reader thread.
- **Held gates and hangs:** while a gate is held, `ws.sleep` and every send re-send it every 500 ms. A
  script whose main loop stops for 2 s therefore loses its gates to the row timeout (`stale` zero) rather
  than leaving notes stuck. The runner marks a script `stalled` after 5 s without a heartbeat, but does not
  kill it.
- **Permissions (owner question C, decided): scripts run with the owner's normal rights,** as the same
  user as Studio or the Player, with no sandbox. They are the owner's code, like board code.
  - The runner starts only files inside the workspace (Studio) or the bundle's `scripts/` (Player), never a
    path from the network.
  - The guide says a script is trusted code.
  - Overturn: third-party scripts become a supported thing. Then a separate user and a sandbox are needed.
- **Declared controls:** Studio draws them with the 0015 generic panel (layer 1) in the script's panel. The
  Player shows them as `script` controls. They are mappable from `player.json`, but not by Studio map mode,
  because they are not engine parameters. Their values live in the Player's live-value store and are
  re-sent after a script restart.
- **Timing:** scripts send untimed UDP on loopback, and jitter is accepted. Timestamped bundles for
  sample-tight timing come later (§9).
- **Phases (owner B.8):** runner and helper with `--print-config` → the editor (Studio tool host, §8) →
  auto-sync → controls in Studio's panel → graphics later.

### 4.6 What would overturn §4
- **Label matching proves fragile**, for example when users rename outputs. Then add a stable `key` per
  output, defaulting to the slug, and match on it. Still never by position.
- **Read-only linked rows block real work.** Then allow per-row "detach" inside a link. Still no merge.
- **Loopback UDP from Python cannot hold musical timing on the Pi** (a facts row shows it). Then bring
  timestamped bundles forward, before graphics.

## 5. `wirescape-headless`: layout, CI and rules

### 5.1 Layout
```
README.md AGENTS.md CLAUDE.md LICENSE LICENSES/ LAB_PIN requirements-dev.txt
docs/REQUIREMENTS.md  docs/API.md  docs/PLAYER_JSON.md  docs/UI_GUIDE.md  docs/guides/
api/player-api.v1.schema.json  api/examples/
player/        the Player service (Python 3.11+, standard library only): core, engine client,
               fake engine, API server, player.json, check, install, sd_notify, taper
scripting/     wsrun.py (runner, GPL-3.0-only) and ws.py (helper, MIT)
ui/            the reference UI (static HTML, CSS and JS; no build step)
systemd/       wirescape-player.service, wirescape-ui.service
tools/labpin.py   LAB_PIN fetch and verify, copied from wirescape-test tools/wstest.py (source commit noted)
tests/         unit and contract tests (H0); tests/integration/ (H1, real engine)
examples/      bundle/ (patches/, player.json, scripts/, presets/), patches/, scripts/
.github/workflows/h0.yml h1.yml h2.yml
```

### 5.2 Pinning the lab
`LAB_PIN` follows `wirescape-test` (0024 §2.2): one PR per bump. The first bump comes with H-4, to lab
`main` of that day. Bump when a needed lab change merges (P0a, P0b, P1 e) and otherwise at most weekly.
`tests/data/catalogue.json` is regenerated on each bump.

### 5.3 CI tiers (the `wirescape-test` shape, not a new one)
- **Shared shape:**
  - a `scope` job that passes in seconds for docs-only changes, plus an always-run gate job, so required
    checks never block docs;
  - one concurrency group per PR with cancel-in-progress;
  - ccache keyed by `LAB_PIN` and toolchain;
  - pinned cmake and ninja.
- **H0:** Linux x64, every push and PR. `python -m unittest` covers the Player core with the fake engine,
  the API contract against the schema, `player.json` and check rows, the runner and helper (with a UDP
  listener), and `--print-config` for every example script. The UI Playwright suite runs when `ui/` or
  `api/` changes. Budget: 5 minutes.
- **H1:** non-draft PRs and `main`.
  - Build `wirescape-engine` only, from `LAB_PIN`, with the lab's headless options read from
    `tools/dev.py` at the pin, on linux-x64 and linux-arm64 (`ubuntu-24.04-arm`).
  - Run the integration tests with `--null-audio` (and `--scripted-midi` once P1 e is pinned).
  - Then the contract suite against the real engine, the 50-switch test, PG1, PG3, PG5 and PG6, and the UI
    suite.
- **H2:** `workflow_dispatch`, requested by the owner (agents may dispatch it when asked): the 200-switch
  test. The Pi soaks, H-f1 and H-f2 are the owner's device runs; their numbers go to lab `facts/` rows.
- **No Windows CI:** the Player targets the Pi, and the runner's Windows use is covered in the lab, where
  desktop vendors it.

### 5.4 Review and merge (0024 §2.5 pattern)
- Any agent implements. One PR per task against `main`.
- **One simple review by a different agent session.** It comments `Reviewed <sha7>: ok` or lists changes.
  It checks the `AGENTS.md` list.
- **Any agent squash-merges** when the review names the head SHA and H0 and H1 are green on it. Docs-only
  PRs need only the review.
- The owner sets branch protection once (H-0): H0 and H1 required, no approvals.

## 6. Order (question 8)

### 6.1 Stages across the three repos (0023 §7.2 and 0024 §5.1 stand; 2b adds the headless and OSC rows)
| Stage | lab | `wirescape-test` | `wirescape-headless` |
|---|---|---|---|
| **1 (now)** | Gate P0 (P0a #619, P0b #620), OB-h1/h2/h3/h6, #545, MB1 → MB2 (fallback date: 0024 §9.6). **File P1 (e) now** (§3; B2 after #620). P1 (f) and (g) may start when a lane is free. | MOD tasks per 0024 §5 | **H-0, H-1, H-2 at once** (no engine change); H-3 after H-1; H-4 when P0a or P0b is pinned, or at the first weekly bump; H-5 |
| **2** | P1 (e) and (e2), (h), (i) TR1h; MM2–MM4; **SC1** OSC In label, toggle and default; **SC2** indicator; **SC4** bundle export | rhythm, LFO, batch A | H-6 reference UI v1 and H-f2; H-7 hardware map and PC (needs P1 e pinned); H-8 systemd, boot and install guide; H-9 UI design guide; H-f1 |
| **3** | **SC3** runner vendored in desktop; **SC5** tool host (§8) with the Python editor; **SC6** auto-sync; **SC7** script controls in the generic panel | batch B | H-10 runner and helper (may start after H-1, in parallel); H-11 scripts in the Player; H-12 soaks (PG10) → **Player v1** |
- **The critical paths:**
  - for promotions, MB2 (0024 §9.6);
  - for a Player on real hardware, P0 → P1 (e) → H-7 → H-f1.
- The fake-player track (H-1 to H-3, H-6) depends on none of them.

### 6.2 `wirescape-headless` tasks
| ID | Title | Paths | Acceptance | Tier | Depends on | Agent |
|---|---|---|---|---|---|---|
| **H-0** | Repo skeleton and CI | `.github/workflows/`, `tools/labpin.py`, `requirements-dev.txt`, `tests/` | H0 and H1 scope and gate jobs run; docs-only PR passes in seconds; `labpin.py verify` against `LAB_PIN`; owner sets branch protection | H0 | — | any |
| **H-1** | Player API v1 schema, fake player, contract tests | `api/`, `docs/API.md`, `player/` (API server, core skeleton, fake engine), `tests/` | §2.5 endpoints, state and commands in the schema; the fake serves them; every command, reply and event validated; SSE `state` on connect; `fake.inject` works | H0 | H-0 | any |
| **H-2** | `player.json` v1 and the check rows | `player/` (bundle, check), `docs/PLAYER_JSON.md`, `examples/bundle/`, `tests/` | §2.7 format and four target forms resolved against example patches; every error and warning row has a test; `check` exit codes as OB-h6 | H0 | H-0 | any |
| **H-3** | Player core: supervisor, state, values, arbiter | `player/`, `tests/` | §2.2–§2.4 with the fake engine: restart backoff, hang kill, composition, arbiter and PC debounce tests; atomic writes (PG5, PG6 in unit form) | H0 | H-1 | any |
| **H-4** | Real engine in CI | `LAB_PIN`, `.github/workflows/h1.yml`, `tests/integration/` | engine built at the pin on both arches; contract suite, PG1, PG3, PG5, PG6 and the 50-switch test green with `--null-audio` | H1 | H-3 | any |
| **H-5** | `install` and boot | `player/`, `tests/` | §2.3 install atomicity (kill during install leaves old or new); boot fallback chain | H0, H1 | H-3 | any |
| **H-6** | Reference UI v1 | `ui/`, `tests/ui/` | every §2.9 menu against the fake; Playwright at 800 × 480; H-f2 protocol written (the owner runs it) | H0, H1 | H-1 | any |
| **H-7** | Hardware map and Program Change | `player/`, `tests/` | §2.7 sources, takeover and actions; PC rule and debounce with fake events; real-engine test with `--scripted-midi` once P1 (e) is pinned | H0, H1 | H-3; P1 (e) for H1 | any |
| **H-8** | systemd units and install guide | `systemd/`, `docs/guides/INSTALL_PI.md` | units as §2.2; watchdog unit test (PG8); guide in the §7 format | H0 | H-5 | any |
| **H-9** | UI design guide | `docs/UI_GUIDE.md`, `examples/ui-minimal/` | a minimal custom UI (one page) built only from the guide passes a smoke test against the fake | H0 | H-6 | any |
| **H-10** | Runner and helper | `scripting/`, `examples/scripts/`, `tests/` | §4.3 and §4.5: `--print-config`, stop gates 0, backoff, flood cap, held-gate re-send; `generative_ws.py` ported to the helper with the same addresses | H0 | H-1 | any |
| **H-11** | Scripts in the Player | `player/`, `tests/` | entry `scripts` start and stop with switches; `script` targets; PG4 | H0, H1 | H-3, H-10 | any |
| **H-12** | Player v1 soak protocol | `docs/`, `tools/` | PG10 runbook and result template for lab `facts/` | H2 | H-7, H-11 | any; owner runs |

### 6.3 Lab rows (the Architect files them; contract named)
| Row | Contract | Paths | Done when | Lane, after | Merge |
|---|---|---|---|---|---|
| **P1-e** controller stream | OB (Gate P1) | `host/midi/`, `host/osc/`, `host/sidecar/`, schema, spec, generated files, fixtures, tests | §3.1, §3.2, §3.4 and the §3.5 rows | B2, after P0b #620 | Claude contract review |
| **P1-e2** control OSC port | OB (Gate P1) | `host/osc/`, `host/sidecar/session.*`, spec, tests | §3.3 and §3.5 row 6 | B2, after P1-e | Claude contract review |
| **P1-f, P1-g, P1-h, P1-i** | OB (Gate P1) | as 0023 R2.3 | as 0023 R2.3 | f and g when a lane is free; h and i as filed | as filed |
| **SC1** OSC In label, kind toggle, generic defaults (In and Out) | new contract **SC** (scripts and OSC features) | OSC In config parsing (`label` known), `apps/studio/src/app/OscEditor.ts`, `OscOutEditor.ts`, presets, Studio tests, `modules/osc_in/README.md` | §4.2 (not the indicator); old patches byte-identical | B1, after OB-h5 #603 | lead |
| **SC2** per-row indicator | SC | `host/osc/`, `host/sidecar/` (status), schema, spec, Studio row list, tests | §4.2 indicator; counters on the worker; no payloads | B2, after P1-e | Claude contract review |
| **SC3** runner in desktop | SC | `apps/desktop/scripting/` (vendored), `apps/desktop/main.ts`, `preload.ts`, tests | `wsrun.py serve` supervised by main; Python discovery with a clear missing-interpreter message | B1, after H-10 merges | lead |
| **SC4** bundle export | SC | Studio export, `apps/desktop/main.ts` (folder write), tests | writes `patches/`, a `player.json` (one entry per patch, macro pages, scripts from links) and `scripts/`; passes headless `check` | B1, Stage 2 | lead |
| **SC5** tool host and Python editor | SC | per the §8 decision | §8 boundaries | Stage 3; design first (§9) | Claude contract review |
| **SC6** auto-sync | SC | Studio OSC In editor, `ui.scriptLinks`, tests | §4.4 rules, each with a test (rename, add, remove, 9th row, unlink) | after SC3, SC5 | lead |
| **SC7** script controls in the generic panel | SC | Studio panel, tests | §4.3 control types drawn by the 0015 generic panel | after SC6 | lead |
| **H-f1, H-f2, H-f3** facts rows | facts | `facts/perf/` | §2.8, §2.9, PG10 numbers with commit, machine and date | owner runs | lead |
No new `wirescape-test` tasks come from 2b.

## 7. Guides (question 7): list, homes and format
**Format (agent-ready, every guide):**
- one Markdown page, self-contained, at most about 300 lines;
- a header block: `Applies to` (lab pin or headless commit), `You need`, `Time`;
- numbered steps with exact commands, each followed by a **Check** line with the expected output;
- a "If it fails" table of symptom, cause and fix;
- example code lives in `examples/` and is referenced by path. CI runs it where possible (scripts with
  `--print-config` in H0);
- device names appear only in board pages and preset names.

| Guide | Home |
|---|---|
| Module build, stage 1 (build and test outside the lab) | `wirescape-test` `README.md` (03 §3.2.7; exists) |
| Module build, stage 2 (promotion) | lab `docs/MODULE_BUILD_GUIDE.md`, rewritten to promotion only, with paths fixed |
| Patching primer | lab `docs/guides/PATCHING_PRIMER.md` |
| OSC and MIDI setup (naming §4.1, rows, LAN flags, control port) | `wirescape-headless` `docs/guides/OSC_MIDI_SETUP.md` |
| Board pages: Pico, Pico W 2, ESP32, Nano (MIDI and OSC with example code) | `wirescape-headless` `docs/guides/boards/<board>.md` |
| Python scripting (helper API, examples, `--print-config`, trust) | `wirescape-headless` `docs/guides/SCRIPTING.md` |
| Player install on the Pi (units, kiosk, consent flags) | `wirescape-headless` `docs/guides/INSTALL_PI.md` |
| Bundles and `player.json` | `wirescape-headless` `docs/PLAYER_JSON.md` |
| Player UI design guide | `wirescape-headless` `docs/UI_GUIDE.md` |
- **Rationale:** what a user reads to play and control lives in the looser headless repo. Studio
  authoring stays in the lab. Lab `docs/` links to the headless guides.

## 8. Tool page host (question 5): boundaries only
- **The sandbox is 0015's panel sandbox**, with a different permission profile. There is no second sandbox
  technology.
- **Studio only. Never in the Player** (owner B.9), and never required by a patch or bundle.
- **The first tool is the Python editor.**
- **Local, owner-approved pages only.** Each page declares its grants and the owner approves once.
- **Everything else is decided later:** the Tool API surface, the grant list, the file layout and
  approval storage (§9).

## 9. Decide later
| Item | Trigger | Default until then |
|---|---|---|
| Tool page host: Tool API, grants, approval storage | the script runner (H-10) exists | no tool host; SC5 waits |
| LAN Player API (phone or remote UI) with a token | the owner asks for a remote UI | loopback only |
| Player-originated MIDI or OSC feedback (LEDs and the like) | first feedback need beyond in-patch MIDI out and OSC Out modules | feedback through patch modules only |
| Snapshot morph and the variant format | snapshots in use, and a need shown | instant snapshot recall; sibling patches as setlist entries |
| Graphical sequencer editing in the Player | after Player v1, if cheap to test | not built |
| Timestamped OSC bundles for scripts | a facts row shows untimed loopback jitter is audible | untimed UDP |
| 14-bit CC, NRPN, pitch bend, clock in the controller stream | a `player.json` need | not reported |
| Text and note-grid script control values in the Player API (Architect A108, transcribed) | the owner wants to edit text or note grids on the Player UI | not Player controls in v1 (a check warning); `button` is a momentary press (H-11a) |
| Script graphics | after SC7 | none |
| Engine fallback OSC In default bytes | OB-h6 shows no patch relies on them | unchanged |

## 10. Edits for the Architect
1. **Gate P1 (e):** file one lab issue whose body is §3 (shapes verbatim), with P1-e2 as a second PR. Add it
   to `OB.md` Gate P1 with the lane and merge rule of §6.3. MM4's dependency points at it.
2. **New contract `SC`** (scripts and OSC features) from §4 and the §6.3 rows SC1–SC7. OSC In features
   are unfrozen by this note. SC5 waits on the §9 trigger.
3. **The freeze lifts** for the Player, OSC In features, scripts and the tool host when this PR merges
   (02 "After each run"). The tool host stays design-first.
4. **`wirescape-headless`:** review and merge this run's PR, which replaces `README.md`, `AGENTS.md` and
   `CLAUDE.md` and fixes the stale restart line in `docs/REQUIREMENTS.md`. File H-0, H-1 and H-2 at once,
   and the rest per §6.2. Ask the owner to set branch protection after H-0.
5. **`ROADMAP.md` and `PRIORITY.md`:** add the Player track (H rows, Player v1 gates §2.10), Gate P1 (e)
   and (e2), and SC, beside 0024 §9.7's MM and MOD rows.
6. **Facts:** add H-f1, H-f2 and H-f3 as unmeasured rows in the facts index.
7. **`docs/context/planner/`:** this PR marks run 2b done in `README.md`; point `02` "After each run" at 0025.
8. **Errata:** headless `docs/REQUIREMENTS.md` restart line (fixed in the headless PR); 02 "Run 2b prep"
   already marks the desktop line stale.

Signed: claude-planner, 2026-11-26
