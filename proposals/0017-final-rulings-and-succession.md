<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0017 — Fable's final rulings: succession, engine rules for M4, the Owner Build

Fable, 2026-11-17 (ET). Answers the packet `docs/workflow/FABLE_FINAL_RUN.md` and Q21, Q22.
Line references are `native/engine2/engine2.cpp` on `main` at `518fe3f`. This note amends
`0005` sections 5 and 6 and M4 invariant G4 where it says so. Each ruling ends with what
would overturn it.

## 1. Succession
From this note on, the **Claude Architect** (the owner's Opus session in the design seat) holds
everything `CLAUDE.md` and STANDING "Who decides what" item 3 reserve for Fable: new proposals,
the meaning of a measurement, invariants, gate thresholds and tolerances, the module header
(`0012`), panel and patch formats, protocol versions and realtime ownership. The open reserved
items (Sub-patch note, M9 r2 state carry, M12 P0 live-panel limit, T4.2 smoothing, T6.3 build
page, the tolerances in `0016` R4 and M10 X4) go with it. "Fixed" in CONSTRAINTS stays with the
owner. I approve the transition; the Architect and the owner rewrite the role text.

Three rules travel with the authority. They are the part of the seat that is easy to lose:
1. **A changed invariant or threshold is written down** in `proposals/` with what changed, the
   `facts/` file behind it, the cost, and what would overturn it. Never inside a code PR.
2. **Never changed to pass a PR that is failing it.** A new threshold applies to tasks
   dispatched after it. A task already failing the old one is fixed, or goes to the owner.
3. **The Architect is not the delivery lead.** One session never holds both seats. The Architect
   may do the contract reviews that ask for a Claude reviewer (PR #159 now).

## 2. Engine rulings for M4 (packet items 2–5)

### ER1. Host packets (before M3 TR1e; used by TR1e, E6, E3a)
Evidence: `panic` adds one to `generation` (:966); `collect` drops other-generation packets
(:481, :501) and drops when `future` is full (:493).
- A packet carries a **host** flag that only the control owner's producer sets. It is engine
  state (transport, an edge's amount target, a data-slot pointer), not a module event.
- In `collect`, a host packet **skips the generation test**, is **applied in the drain, in ring
  order, at the block start**, never enters `future` and never counts against a node's event
  budget. `panic` therefore cannot undo acknowledged host state.
- All host packets use one ring of the control producer, so their order is the send order. A
  full ring is the reply `busy` (0008 K4 as written).
- Each host packet carries a **serial** per target. Render applies it only if it is newer than
  the target's current serial. A layout carries the current value and serial of every target at
  publication, so a packet that arrives late is a no-op.
- **The born test stays** for host packets addressed to an instance, edge state or slot. This
  differs from the packet's recommendation. Reason: after remove and re-add of the same ID, an
  old amount or an old data pointer must not reach the new object (the pointer may be freed).
  A target that is not found is counted and its payload is never dereferenced.
- After `Engine::reset` (it clears the rings) the control owner re-sends host state from the
  document. One test.
- *Overturns:* a legitimate host packet whose stamp is lower than its target's birth.

### ER2. Data blocks are freed by acknowledged serial (amends 0005 section 6)
Evidence: `pop_egress` discards other-generation packets (:953), so a block returned through
egress leaks after `panic`, and a full egress ring has no answer.
- Render swaps a slot's pointer and serial, then stores the serial in a per-slot atomic
  `adopted_serial`. It never reads the old pointer after that store.
- The control owner owns every block, keyed by module ID and slot. It frees a superseded block
  when every live instance of that ID reports a newer `adopted_serial` or is destroyed. During
  a replacement two instances share the current block; at most 2 generations per ID.
- Nothing is returned through egress. 0005 section 6 "returns the old block through the egress
  side" is withdrawn.
- *Overturns:* a module that must keep the pointer past `process` (0005 forbids it).

### ER3. Packets newer than the adopted layout wait in their ring (E4b; amends G4)
Evidence: producers stamp `revision` at push (:539, :832). Under E4b render adopts at a block
start, and a packet stamped with the new revision can be drained before that.
- The control owner stores the layout pointer first, then an atomic `published_revision`.
  Every producer stamps from `published_revision`.
- Render exchanges the layout pointer before `collect`. In the drain it **peeks**; if the head
  packet's revision is greater than `adopted_revision`, it stops draining that ring for this
  block. Nothing moves to `future`, so order inside a ring is unchanged and no capacity is used.
  The wait is at most one block, which keeps K4's two blocks.
- G4 now reads: "…unchanged, except that a ring's drain stops at a packet newer than the
  adopted layout." This is the only ordering change allowed; E4b's review quotes it.
- A stamp above `published_revision` would block a ring. Debug assert plus a counter; no drop path.
- *Overturns:* a TSan or ordering test showing a producer that can stamp before the pointer store.

### ER4. A replacement inherits its predecessor's birth (E5)
Not in the packet. `adopt` carries held notes into the new instance. With a fresh
`born_revision`, a note-off stamped just before the edit is dropped (:483) and the note sticks.
- An instance created by an E5 replacement takes the `born_revision` of the instance it
  replaces. Events for that ID go to the successor from the adoption block on; the old instance
  receives nothing more and ends with the fade.
- Remove and re-add of an ID is not a replacement and gets a new birth.
- Test: note-on, replace with `adopt`, note-off pushed before adoption; the note ends.

### ER5. No module call on a live instance from the control thread (E4a inventory, E4b)
Evidence: replan calls `latency_frames` on live instances (:295, :1004 paths) and edits
render-owned state while render is parked (:1205–1262). Spectral's latency changes at run time
(`modules2/spectral/dsp.h:128`), so it cannot be sampled once.
- **G9 (new invariant, from E4b):** the control thread calls no module function on an instance
  that a published layout references, and writes no state that render reads, except through
  the layout pointer, the rings and atomics.
- **Latency:** each instance has an atomic latency. The control owner fills it after `prepare`,
  before first publication. Render refreshes it in the block where it adopts a layout, and at
  the end of a block in which that instance received a parameter or data change. The layout
  builder reads the atomic. Known limit: a latency that changes with no event is seen one edit
  late; the CN latency probe reports it.
- **Work done today under the pause** travels in the layout and is applied by render in the
  adoption block, bounded and without allocation: pruning `future` of removed routes, the
  replan chokes, the tap-table reset. Feedback delay lines and edge state are shared objects
  that do not move.
- **Before E4a code**, the builder posts a table of every statement in today's swap section,
  each marked layout-build, adoption-step or shared-state. The contract reviewer checks the
  table first.
- Only render and the control owner dereference a layout. Any other reader (telemetry, monitor)
  goes through the control owner. TSan covers it in the E4b stress test.
- *Overturns:* an instruction-count row outside G8 from the latency refresh.

### ER6. Duplicate modulation cables (E6)
Evidence: the protocol's connection identity is already kind/from/to (`ENGINE_PROTOCOL.md:79`)
and Studio refuses a second cable (`PatchCanvas.ts:879`). Only a hand-edited file can hold one.
- `connect` and `applyGraph` refuse a duplicate with a structured refusal.
- The **loader does not refuse** (the owner's saved patches keep loading, CONSTRAINTS Fixed). It
  keeps the first cable, adds later amounts into it, clamps to ±1 and warns, naming the cable.
- The E6 builder first files a scan of the bundled patches. A duplicate there, or any golden
  difference, is a question, not a merge.

## 3. M4 r2 (packet item 6): accepted, written into `M4.md`
Accepted as proposed, with one change to (a). The sidecar lane serialises writers; it does not
make M4 wait for parked work. Order: TR1e → E6 → E5/E3a → E7. PV2b, TR1h and PV3 take the lane
only when no M4 task holds it or is ready for it. E7 and PV3 never overlap; whichever comes
second rebases. PV3 lists `setData` and the swap-to-live change whenever it runs.
Added to acceptance 2 from Q22: the `applyGraph voice count` row shows `held_note`
`silence_ms` = 0 after E5.

## 4. The Owner Build (packet item 7): OB0 and OB1 accepted
`PRIORITY.md` tiers and both definitions are accepted. The Architect writes the OB contract.
It must contain:
- **OB-a in two parts.** A CI test over the bundled patches plus one synthetic patch per module
  config shape. And a runner the owner points at a folder of real patches on the Pi: load, save,
  load, compare the normalised document and a render hash. The owner's patches are not in the
  repo, so only the owner's run closes OB-a. V1 stays parked until it does.
- **No patch file is rewritten on load.** The first save of a patch loaded from an older shape
  writes a sibling backup.
- **OB0 stays tagged** and installable after OB1, as the way back.
- OB1's last criterion is the owner's Pi session, with the transition run of section 6.

## 5. Errata (packet item 8)
- **(c) `BLOCK` size: `0012` wins.** Records stay ≤ 4,096 bytes. `0015` A2 now reads "gets a
  `BLOCK` stream, which may deliver several queued records in one message, not a higher message
  rate". Fixed small records are what a Daisy-class target can hold.
- **(d) Unknown config keys.** `0012:94-96` governs **edits**: refused, naming the field. On
  **load** of a stored document, an unknown key is kept in the document, not delivered, and
  listed in a warning (the loader already does this for OSC keys, `runtime_patch.cpp:90`).
  A known key the table would refuse on load must load as it does today: widen the table, or
  give the module a migration. A migration is declarative data in the module description, keyed
  by the module `version` already stored in the patch: rename, drop or default a key. It runs
  in the shared loader and in the `0013` compiler, never on a device. Anything a table cannot
  express is an Architect design.
- (a), (b), (e)–(l): the Architect fixes them in one errata PR. Where two texts disagree, the
  stricter one wins unless a merged test already depends on the looser one.

## 6. Cost of a transition (packet item 9)
Yes. CN gains two reported rows on the heaviest bundled patch: instruction count of the
adoption block, and of the worst block while two instances of the heaviest module are alive
(E5). Not gated in CI. The gate is on the device: the owner's Pi run performs 100 scripted
edits at the owner's buffer size and reports xruns; OB1 needs zero. The Architect may add a CI
threshold once both rows and the S-facts exist (rule 1 of section 1).

## 7. Daisy-class outline (packet item 10)
- **No edits on a device.** Firmware has one layout, fixed at compile time. So render must be
  able to walk a layout that is constant data. E4a note: what render reads from a `Layout` is
  pointer-and-count, with no container type. If that costs a G8 row or more than a day, skip
  it and record it.
- **Memory is a compile-time sum** of `memory_requirements` at the patch's fixed voice counts,
  placed by the compiler; no heap. The compiler refuses a patch that does not fit, naming the
  module.
- **Byte-identical output:** sorted keys, LF, no times or paths, floats written as bit patterns
  from one correctly rounded parser, the tool version in the output.
- **Portable-tier check:** the authority is a freestanding cross-compile in Linux CI. Windows
  gets a header that poisons forbidden names; it is advisory.

## 8. Risks the packet did not list
1. ER4 above (stuck notes after a replacement).
2. The voice-count row (Q22): the reply says `live`, yet the tone witness dips −25 dB. Before
   E5 code, the builder posts what a voice-count change does today and who reallocates.
3. The owner's patches have no corpus in the repo (section 4).
4. M1's file split, M3 and M4 all write `native/engine2/`. One writer, and S6 needs every
   product PR merged or parked; plan the S6 window a day ahead.
5. The web build keeps its own dispatcher. It is not in the Owner Build: keep it building, add
   nothing to it.
6. PR #159 (M1 S3) heads the critical path and waits only for a Claude contract review.

Signed: Fable, 2026-11-17
