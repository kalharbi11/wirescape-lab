<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0005 — Edits that never restart (design for Phase 2: T0.13, T2.0–T2.4)

Fable, 2026-11-16 (ET), against `main` at `c692c7a`. Read for this note: `engine2.cpp` render,
reconfigure and replan (lines 853–950, 1014–1270), `engine2.h`, `module2.h`, the sidecar's
`commit` and command handlers (`session.cpp` 672–850, 1083–1160), protocol spec §4–§5, `0002`
Phase 2, `0003` §2. Protocol v1 generation (T2.5) is scoped here but not designed.

## 1. What happens today (observed)

1. **Three paths.** `setParam`, notes and panic are live events. `addModule`, `removeModule`,
   `connect`, `disconnect`, `setModAmount` and `ccMap.set` build a full candidate graph off-thread
   and call `Engine::replan` (`session.cpp:703-722`). `loadGraph` skips replan
   (`new_namespace`, `session.cpp:704`) and takes the mute path: master fade-out, panic, swap of
   the whole engine, fade-in. Every instance is new.
2. **Replan already diffs.** A candidate node whose ID, descriptor and config bytes equal a live
   node's is not used; the live instance continues with its state (`engine2.cpp:1142-1147`).
   Anything else is a new instance born at the new revision. Feedback delay lines of unchanged
   edges are carried. Removed event routes release their targets with a choke.
3. **Replan is not gapless.** The render thread sees the park request at the end of a block and
   ramps that whole block's output to zero (`engine2.cpp:937-940`). While parked it writes zeros
   and processes nothing (`870-875`). The control thread does its pointer swaps, then the first
   block afterwards is ramped in (`932-936`). So every structural edit, including one cable, is a
   master dip of one fade-out block, at least one silent block and one fade-in block: about 16 ms
   at 256 frames and 48 kHz when the control thread is prompt, longer when it is not. Module time
   stops during the park, so phases and tails resume rather than reset.
4. **Why "edits restart the patch" (KNOWN_ISSUES A2).** Studio sends `loadGraph` for config
   edits, undo, redo, snapshot restore, OSC In rows and CC Learn, and `loadGraph` never uses the
   diffing path. The restart is a routing choice in the sidecar and Studio, not an engine limit.
5. **A changed config always means a new instance** with no state in the live path. The state
   carry in `Engine::reconfigure` (`1073`) is quiescent-only and is not used by `commit`.
6. **Routing lives inside the instance.** `Node` holds both DSP state and its topology
   (`incoming`, `signal_edges`, `modulation`, `outgoing`, `index`, `component`, `loop`). That is
   why the swap must stop the render thread: the control thread rewrites fields the render thread
   reads.

## 2. Decisions

**D1. Two steps, in this order.** First route every edit through the diffing path that exists
(section 3). That removes the restart for every untouched module with a sidecar and Studio change
and no engine change. Then make the swap itself gapless (section 5). The first step is cheap and
is contracted now; the second is the engine work of Phase 2.

**D2. The document is the edit.** Undo, redo, restore and config edits send the whole target
document with a new command, `applyGraph`. The sidecar and engine work out the difference. Studio
does not compute edit scripts. Reason: the engine already diffs by (ID, type, config); a second
diff in TypeScript would have to agree with it forever.

**D3. Module IDs may return through `applyGraph`.** Undoing a delete brings the same ID back as a
new instance. The engine already makes this safe: packets older than a node's birth revision are
dropped (`engine2.cpp:483, 503`). The "never reused" rule stays for `addModule`.

**D4. Topology moves out of the instance** into an immutable layout that the render thread adopts
with one pointer exchange at a block boundary. No park, no master fade. Section 5.

**D5. Clicks are handled per edge, not on the master.** A new signal or modulation edge ramps in,
a removed one ramps out before it is dropped. Event edges do not ramp; removal keeps today's choke.

**D6. Musical data is not config.** Steps, CC rows and OSC routes become module data delivered
between blocks; the instance is untouched. Section 6. This is what makes Groove editable while
running, and it removes most real config edits.

**D7. A true config change replaces the instance inside the same mechanism.** Old and new run
side by side for a declared fade; the new one takes over state through an optional realtime
`adopt` hook. With no hook, the old instance rings out under the fade. Section 7.

**D8. Modulation amount is a live value on the edge,** smoothed over 5 ms, not a graph swap.

**D9. No thresholds in the harness.** T0.13 reports numbers. The Phase 2 gate is stated here
(section 9) and applied by Fable at acceptance.

## 3. Step E1: `applyGraph` on the existing replan (contract M2)

**Protocol (additive to v0).** Capability `applyGraph` in `hello`. Command
`{type:"applyGraph", patch: PatchV2}`. Validation and the execution copy are exactly `loadGraph`'s.
Reply result `{path:"live"|"restart", replaced:[ids], unapplied:[{moduleId,paramId}]}`.

**Semantics.**
1. Same session, same ID namespace; `gen` advances.
2. An ID in both documents with the same module type and identical execution `config` is the same
   instance: phases, tails, held notes and sequencer position continue. Its `state` field in the
   new document is ignored.
3. An ID in both with a different type or config is replaced by a new instance, initialised from
   the document as `loadGraph` would. It is listed in `replaced`.
4. An ID only in the new document is created; one only in the old is removed, with today's
   release of held notes.
5. For every continuing instance, each parameter whose value differs between the committed
   document and the new one is sent as a live parameter event, after the swap succeeds, in
   document order. If the event queue stays full for three block periods the rest are returned in
   `unapplied` and the committed document keeps the old values for them. The reply is still `ok`.
6. Stream stopped, or the live replan refused for a reason other than busy: the existing mute path
   runs and `path` is `restart`. Behaviour is then `loadGraph` without a new namespace.

**Sidecar.** One handler that calls `commit(patch, false)` and then reconciles parameters.
No change to `Engine`, `AppEngine` or `commit`'s swap logic.

**Studio.** `EngineClient.applyGraph`; used for config edits, undo, redo, snapshot restore, OSC In
row edits and CC Learn when the capability is present, otherwise `loadGraph` as today. Opening or
creating a patch stays `loadGraph`. `FakeEngine` implements the same rules 1–5.

**What E1 does not fix,** and T0.13 will show as numbers: the master dip of section 1.3 on every
structural edit, and the restart of the one module whose config changed.

## 4. T0.13: the edit-continuity harness (answers Q3)

**Where it measures.** End to end through the sidecar process and the protocol, with the null
sink. That is the path the user's edits take, including `commit`'s choice between live and mute.

**One product change (T0.13a).** A sidecar flag `--capture-null-sink <file>`: the null-sink
thread appends every rendered block of every configured bus channel as raw float32, with a small
header (rate, channels, block). Refused unless the null sink is in use. The flag absent means no
behaviour change. The null-sink thread is not a device callback, so file writes there break no
realtime rule; nothing is added to `Engine::render`.

**Probe patches** (under `bench/patches/continuity/`), each routed to separate bus channels:
- *Witness tone:* a VCO at a fixed frequency straight to an output. Never touched by the edit.
- *Witness tail:* an impulse or burst into a delay with feedback, to an output.
- *Witness held note:* envelope and VCA held by a `noteOn` sent before the edit.
- *Witness clock:* a running clock or Groove driving a short percussive voice.
- *Subject:* the module the edit targets, with its own output.

**Procedure per edit.** Start the sidecar on the null sink at 48 kHz and 256 frames, load the
probe patch, wait 2 s, send the edit, wait for the reply, wait 2 s, stop. The edit's place in the
capture is read from the marks file, not assumed (amended 2026-11-16, QUESTIONS Q10; `gen` and the
status stream cannot name a block). With the capture flag the sidecar writes `<file>.marks`, one
JSON line per handled command: request ID, type, `ok`, `gen` after, and `b0`/`b1`, the capture's
total block count just before the command is applied and just after its reply is built. The
command took effect in blocks `b0` to `b1 + 1`. The control thread writes the line; the null-sink
thread only increments one atomic count.

**Metrics per witness, in a window from 100 ms before `b0` to 1 s after `b1 + 1`.**
1. `silence_ms`: longest run below −80 dBFS on a witness that should be sounding.
2. `dip_db`: lowest 1 ms RMS relative to the steady RMS.
3. `time_slip_ms`: for the tone, the phase of a sine fit over 50 ms before and after, expressed
   as time; for the clock, the offset of the next onsets from the grid set before the edit.
4. `jump_ratio`: largest sample-to-sample step divided by the largest steady-state step.
5. `disturbed_ms`: span over which the witness differs from its own continuation by more than
   −60 dB (tone: against the fitted sine; tail and held note: against a capture with no edit).
6. `restarted`: for the subject only, whether its phase or envelope returned to the reset value.

Each metric is unit-tested on synthetic signals: a clean sine, a sine with a 3-block gap, with a
phase jump, with a step.

**Edits measured.** Each `swap` command in protocol §4 (add and remove an unconnected module,
remove a connected one, connect and disconnect signal, event and modulation cables,
`setModAmount`, `ccMap.set`); `loadGraph` of the identical document; `loadGraph` and, once E1
exists, `applyGraph` of the document with one change of each kind in A2 (Groove steps, Groove
length, a voice count, an OSC In row, one parameter, one deleted and restored module);
`setBufferFrames`; `panic`. Three repeats each; report the worst.

**Output.** `facts/dsp/edit_continuity.{json,md}`: one row per edit and witness, with lab commit,
machine and date. No pass or fail.

## 5. Step E4: gapless structural edits

### Structure
- **Instance** (today's `Node`, minus routing): descriptor, DSP instance, parameter state and
  smoothers, output buffers, pending events, memory. Owned by the engine; created and destroyed
  by the control owner; processed only by render.
- **Edge state**: feedback delay line and, for modulation, the live amount and its smoother.
  Looked up by edge identity `(from, output, to, input, kind)`, without the amount.
- **Layout**: everything render needs to walk the graph for one topology. Per slot: instance
  pointer, input views and sum buffers, incoming and outgoing edge lists, component and loop
  membership, order; plus buses, latency compensation, tap table. A layout is immutable once
  published. It references instances and edge states and owns neither.

### Publication
1. The control owner builds layout `L'` completely off-thread: new instances are created and
   prepared, retained instances are referenced, not moved.
2. It stores `L'` in one atomic pointer. At the start of its next block render exchanges that
   pointer for null; if it got a layout, it switches to it and stores the layout's revision in an
   atomic `adopted_revision`. Render never touches the previous layout again after that store.
3. The control owner frees the previous layout, and destroys instances no layout references, only
   after it reads `adopted_revision` ≥ the new revision.
4. One layout in flight. A second publish waits for adoption, bounded by three block periods as
   today; if render is not running the swap is done quiescently.

Render-thread cost of an edit: one atomic exchange per block, always, and one pointer assignment
when a layout arrives. No allocation, no lock, no wait. The park state machine and the master
fade in `render` are removed.

### Ramps
- A layout edge carries `gain_from`, `gain_to` and a length in frames; render owns the ramp
  position. Default length 5 ms; 0 means none.
- An edit is published as a **transition layout**: added signal and modulation edges ramp 0→1;
  removed ones are still present and ramp 1→0. Instances that are being removed stay in the
  transition layout so their outgoing edges can ramp.
- Ramping edges use the copy-with-gain input path. An edge at gain 1 with no ramp may use the
  direct zero-copy view, as today.
- When render has finished every ramp of a revision it stores that revision in an atomic
  `settled_revision`. The control owner then publishes the **steady layout**: removed edges and
  instances gone, finished ramps turned back into direct views. Publishing the steady layout is
  housekeeping: it may be folded into the next edit, and nothing audible depends on when it runs.
- An edit that arrives during a transition is built on the transition layout's target. An edge
  already ramping keeps its position.

### What does not change
Event ordering and budgets, the ingress and egress rings, the clock anchors, parameter smoothing,
feedback block size, poly rules, the FTZ/DAZ guard, the module ABI.

### Known limit, kept
An edit that changes the latency compensation of a path that keeps playing shifts that path in
time. Today it does so inside the master dip; after E4 it will be exposed. T0.13 gets a probe for
it; the fix (cross-fading two compensation delays) is decided when there is a number.

## 6. Step E3: module data

- A module declares up to 8 **data slots**: id, name, a field table (name, scalar type, array
  length) and a maximum size of 64 KiB. The field table describes a plain C struct the module
  defines; the SDK produces both from one declaration. The host packs the document's JSON for the
  slot into that struct generically, off the audio thread, and validates ranges from the table.
  This is the same field-table mechanism `0003` item 9 needs for config; it is built once.
- `ws2_process` gains a `data` array: pointer, size and serial per slot. The pointer is valid for
  that call only. The module reads it every block and keeps no copy; a module that needs derived
  values recomputes them, bounded, when the serial changes.
- Delivery: the control owner allocates the packed block and sends its pointer through the
  ingress ring as a host packet. Render swaps the slot pointer at the next block boundary and
  returns the old block through the egress side for the control owner to free.
- The document stores data per module under `data: {slotId: …}`. It is not part of `save_state`.
  On replacement the host hands the same block to the new instance.
- Additions to `module2.h` are at the end of `ws2_descriptor` and `ws2_process`, guarded by
  `struct_size`, so existing modules build and load unchanged.
- First users: Groove (steps, length), `midi.cc_to_cv` rows, OSC In and Out routes. `ccMap.set`
  becomes a data write. Tempo is transport, not data (T1.7).

## 7. Step E5: replacing an instance

Used when config really changes shape, and for the developer hot reload of `0002` D8 level 2.

1. The control owner creates and prepares the new instance `N` beside the old `O`.
2. The transition layout contains both. Every consumer edge from `O` ramps out and a twin from
   `N` ramps in, over the module's declared `replace_fade_ms` (default 20, maximum 500). Signal
   inputs feed both. Events go to `N` only; `O` receives a release-all at the swap.
3. **Adopt.** If the descriptor has `adopt`, render calls `adopt(N, O)` once, at the block
   boundary where the layout is adopted, before either processes. The hook is realtime code:
   bounded, no allocation. It copies what continues (phases, envelope levels, held-note table,
   smoother values). It may not take pointers into `O`'s memory.
4. **No adopt, or adopt declines.** `N` starts from the document state or reset; held notes the
   host knows about are re-sent to `N` as note-ons at the swap. `O` rings out under the fade. For
   delays and reverbs this is the intended behaviour: the old tail decays while the new one fills.
5. After the ramps settle the steady layout drops `O` and the control owner destroys it.

Voice-count changes use this path: `adopt` carries the voices that fit; the rest are released.

Left open on purpose: moving large buffers from `O` to `N` without copying. It needs shared
ownership of host memory between instances. Decide when a module shows it is needed; the ring-out
covers the cases known today.

## 8. Order, dependencies, who

| Step | What | Needs | Class | Contract |
|---|---|---|---|---|
| T0.13a | Null-sink capture flag in the sidecar | — | B | M0 r2 |
| T0.13b | Harness, probe patches, facts | T0.13a | A | M0 r2 |
| E0 | Canonical config bytes: zero-fill before field writes, test that two encodings of one config are byte-equal | — | C, small | M2 |
| E1a | `applyGraph` in the sidecar, protocol spec, protocol tests | E0 | C, from this note | M2 |
| E1b | Studio: client, call sites, `FakeEngine`, Playwright | E1a | B | M2 |
| E6 | Live modulation amount (D8) | M1 S3 | C | later |
| T1.6 | Split `engine2.cpp` along section 5's seams: instance, layout build, render, edit. No behaviour change | M1 S5 | C | later |
| E3 | Module data | T1.6 | C, edits `module2.h` additively | later, `merge: fable` |
| E4 | Layout/instance split, publication, ramps | T1.6 | C | later, one writer |
| E5 | Replace with adopt and ring-out | E4 | C | later |
| T2.5 | Protocol v1 from one schema | own design | — | not designed |

E1 and T0.13 touch `native/sidecar`; M1 stage S5 does too. They merge before S5a opens or wait
until S5b is merged (M1 r2 says so).

Device changes (`setBufferFrames`, `setSampleRate`) rebuild the graph with the stream stopped.
State could be carried there with `save_state`/`load_state`, which is legal when quiescent. Not
decided: measure it with T0.13 first.

## 9. Phase 2 gate (applied by Fable at acceptance, on T0.13 numbers)
For every edit in section 4, on every witness the edit does not touch: `silence_ms` = 0,
`dip_db` > −0.1, `time_slip_ms` under one sample, `jump_ratio` < 1.5. For the subject of a data
edit: `restarted` false. For the subject of a replacement with `adopt`: `restarted` false and
`jump_ratio` < 1.5. Then the owner listens on the Pi.

E1 alone is expected to pass `restarted` and `time_slip` for witnesses and fail `silence_ms` and
`dip_db`. That is the measured case for E4.

## 10. Assumptions to verify (inventory P2, then the E1a builder)
- **B1** Nothing outside `addModule` depends on an ID never returning in a session: MIDI host,
  OSC hosts, monitor and telemetry are all reconfigured from the committed patch in `commit`.
- **B2** Parameter events sent right after a replan reach instances born in that replan (their
  birth revision is not later than the event's).
- **B3** The null sink can be the only output for a whole sidecar run, and `setBufferFrames`
  works on it.
- **B4** The config bytes compared by replan are a canonical encoding, so an unchanged module in
  a re-sent document always compares equal. **Checked while writing, and it is doubtful:** the
  bytes are a raw copy of a C++ struct (`runtime_module_config.h:183, 261, 347, 400`), and four of
  the structs are declared without value-initialisation (`:54, :189, :268, :362`). If any has
  padding, those bytes are indeterminate and an unchanged module can compare unequal. That would
  already cause needless restarts of config-bearing modules on any structural edit today. Task E0
  settles it before E1a.

A false B1, B2 or B4 goes to `QUESTIONS.md` before code is written.

Signed: Fable, 2026-11-16
