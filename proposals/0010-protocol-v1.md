<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0010 — Protocol v1 and the client edit queue (design for T2.5)

Fable, 2026-11-16 (ET), against `main` at `c692c7a`. Read for this note: `ENGINE_PROTOCOL.md`
§1–§5 and §8, the audit's live-editing and protocol findings (`0001` §2 and lines 183–185), the
shape of `RealEngine.ts`. Depends on `0005` (`applyGraph`). Stage PV1 is contracted in M2; the
rest is contracted later.

## Today (observed)
- The protocol is described once in prose (`docs/specs/ENGINE_PROTOCOL.md`) and implemented three
  times by hand: sidecar (`protocol.cpp`, `session.cpp`), Studio (`RealEngine.ts`, 528 lines;
  `FakeEngine.ts`, 836), Electron main and preload. The audit lists about 35 places where they
  differ from the spec, among them client methods that do not exist (`ccMap.set`, `setOsc`) and
  refusals the client drops because they carry no session.
- The client sends one edit at a time and keeps a journal of mutations with inverses, replaying
  later edits when one is refused (§8). It drops queued edits on a session change without rolling
  the document back, and a load can discard an unsent edit.
- When unsure, the client sends `loadGraph`, which restarts everything.
- There is no heartbeat. A hung engine looks like a quiet one.
- One control executor runs everything in order, including device opens that can block.

## Decisions

**P1. One schema file is the protocol.** `docs/specs/protocol.schema.json`: JSON Schema
2020-12, restricted to objects with `required`, `enum`/`const`, numeric bounds, string and array
length limits, `$ref`, and `oneOf` discriminated on `type`. One more keyword since 2026-11-16
(QUESTIONS Q8): `pattern`, with the single permitted value `^[\\x20-\\x7E]*$` (as written in JSON), which the generator
matches as a literal string and turns into a byte-range check; any other value is a generator error. A Python generator under
`tools/protocol/` produces: TypeScript types and validators (plain generated code, no new runtime
dependency), a C++ header of validation functions over the JSON library already in use, and the
command and error tables of the spec. Generated files are committed and checked for drift in CI.
Limits that are not shape (2 MiB line, nesting 64, 256 queued) stay in prose and tests.

**P2. The schema first describes v0 exactly as the sidecar behaves today.** No behaviour changes
in that step. Every difference between spec, sidecar and client then shows up as a failing
validation or a compile error, which turns the audit's list into a worklist.

**P3. Convergence replaces replay.** The client holds the desired document `D`. It sends small
commands as fast paths and, whenever it is unsure, sends `applyGraph(D)`, which after `0005` is
cheap and restarts nothing. The mutation-and-inverse journal goes.

**P4. Pipelining with a poisoned queue.** The client may have up to 32 commands outstanding.
The engine executes in order. When it refuses an edit-class command it refuses every later
edit-class command with code `stale`, without executing them, until it receives an `applyGraph`
or `loadGraph`. Live-class commands (`setParam`, notes, `panic`, `setTransport`) are never made
stale. Reason: edits sent after a refused one were built on a state that never existed; executing
them is guessing.

**P5. What the client does on a refusal.** Two cases (amended 2026-11-16, QUESTIONS Q4).
*Busy:* code `busy` says nothing about the edit. `D` and undo history stay as they are; the client
resends `applyGraph(D)` after 100, 200, 400 and 800 ms, then once per heartbeat (P8), and from the
fourth try shows "engine busy, edits pending". Nothing is dropped. `unavailable` is a lost session
and follows P6.
*Rejected:* any other code. The client restores the document snapshot taken before the refused
edit, discards its later unacknowledged structural edits, cuts undo history back to that snapshot,
shows one message naming the refused edit and the number of edits discarded, and sends
`applyGraph(D)`. These are rare, because Studio validates with the same generated schema and
catalogue. This is deliberately simpler than §8's selective replay: Studio's history holds
snapshots, not operations, so keeping the later edits that still apply would need a document merge.
That merge is designed only if measured refusals show the need (Q4, point 4).

**P6. A new session never loses edits.** `D` already contains every edit the user made. After
`hello` the client sends `loadGraph(D)` and drops only its list of outstanding request IDs.

**P7. Every engine line carries `session`, refusals included.** A line without it is a schema
violation and a test failure, not something the client tolerates.

**P8. Heartbeat is a push from its own thread.** Once a second the engine emits
`{type:"alive", control:"idle"|"busy", busyType?, audioBlocks}`: whether the control executor is
running a command and which, and a counter of rendered blocks. Electron main declares the engine
hung after 5 s with no `alive` and emits `app.engineHung`; the UI offers a restart. A long device
open shows as `busy`, not as hung.

**P9. Stuck notes cannot wait behind a device open.** `panic` and `noteOff` are executed by the
reader thread directly: both are already bounded enqueues to the engine. Everything else stays on
the one ordered executor. This replaces "move device work off the control thread": what matters
is that the engine stays observable and silenceable, and one executor keeps ordering simple.

**P10. Version switch.** The sidecar accepts `v:0` and `v:1` while Studio moves; `hello` lists
both. When Studio sends only `v:1`, `v:0` is removed in one PR. v1 differs from v0 by P4, P7, P8,
P9, the commands added in `0005` and `0008`, and nothing else: the envelope, `gen` and the error
codes other than `stale` stay.

## Stages
| Stage | What | Needs | Merge |
|---|---|---|---|
| PV1 | Schema of v0 as implemented; generator; generated TS types and C++ validators, not yet wired in; a test that validates every exchange in spec §10 and every line of the sidecar protocol tests against the schema; a written list of each place spec, sidecar or client disagree | — | lead (M2) |
| PV2 | Resolve the list: each item fixed toward the spec, or the spec corrected by Fable. Sidecar and preload validate with the generated code | PV1, M1 S5b | lead after contract-review |
| PV3 | v1 in the sidecar: P4, P7, P8, P9; protocol tests for each | PV2, M2 | lead after contract-review |
| PV4 | Studio client on P3, P5, P6; `FakeEngine` built from the same generated interface so a missing method does not compile; Electron hung detection | PV3 | lead |
| PV5 | Remove v0 | PV4 | lead |

## Invariants
- **Q1** PV1 changes no runtime behaviour: generated code is built and tested but not called by
  the sidecar or the app.
- **Q2** No JSON, validation or allocation on an audio or MIDI callback, as today.
- **Q3** Unknown document fields are preserved; validation of `patch` payloads checks the
  envelope and known fields and never rejects or strips unknown ones.
- **Q4** Exactly one terminal reply per parsed command, in order; `stale` is a terminal reply.
- **Q5** The heartbeat thread reads two atomics and writes one line; it takes no lock the control
  executor or the audio callback can hold. stdout lines stay whole: one writer lock for stdout.
- **Q6** Golden renders unaffected; protocol snapshot tests (M1 S0) change only where a listed
  disagreement is resolved, each named in the PR.

## Open
Whether a document hash in `applyGraph`'s reply is worth having for the client to confirm
convergence. Not needed for correctness under P4–P6; decide if PV4 finds a case.

Signed: Fable, 2026-11-16
