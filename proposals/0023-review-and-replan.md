<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0023 — Review of the build and the replan (Planner run 1)

**Status: final rulings** (`claude-planner`, run 1; authority in
[`02_PLANNER_RUNS.md`](../docs/context/planner/02_PLANNER_RUNS.md)). The Claude Architect writes them into
contracts, tasks and lanes without reopening them. It flags only conflicts with CONSTRAINTS "Fixed" items,
factual errors (with the source line) and contradictions with run 2.
**Read at:** lab `main` `48479fc` (2026-11-26 ET); scout pack at `11a68c2`. `main` moved to `c8f5e13`
during the run (OB-h5 merged as #606); no ruling depends on that change. **Order:** CI speed (§1), the
engine as the Player's base (§2), the module SDK (§3), workflow cost (§4), build vs plan (§5), ranked
findings (§6), roadmap (§7), edits for the Architect (§8).

## 0. Summary
1. **CI speed.** Notes-only PRs already run only `scope` and `foundation`: 31 s to 1 min 44 s today. The
   seven required checks stay. Facts generators leave the PR triggers. Root `docs/*.md` joins the notes
   scope. Three trigger edits are applied in this PR; three small edits go to the lead (§1).
2. **Engine as the Player's base: yes, after four engine changes.** The process model, protocol v0,
   bounded queues and the faded patch swap can carry a Player. Before the Player relies on the engine:
   - render liveness in `status`: a stalled callback still reads `running` today;
   - controller faults degrade instead of silencing MIDI or ending the process;
   - OSC Out releases its gates on a swap;
   - OB-h1 closes #326 and #494.
   Controller events with Program Change, settings durability and SIGTERM follow before Player v1 (§2).
3. **Module SDK.** Reopen CAT-1 #358 and MB1 #363 now as one stage, **MB**: MB1, then MB2 with one
   translation unit per module, then MB3. The lab module freeze ends when MB2 merges, not at the OB1
   tag. New modules start in `wirescape-test`. Modulatable policy: §3.4. Owner-wants B.4's list is wrong
   for 7 of its 22 modules (§3.1).
4. **Workflow.** The lab stays strict on the engine, host, SDK, protocol, Studio and promotions. Module
   development and the Player move to the loose repos. A ruling lives in the file it changes. Mandatory
   reading per role is at most 400 lines. A bounded exception is never renewed (§4).
5. **Roadmap.** OB1 acceptance stands, but it gates nothing new. Each stage spans the three repos:
   - **Stage 1:** MB, Player gate P0, M4 acceptance, the `wirescape-test` harness, the Player skeleton.
   - **Stage 2:** controller events, transport control, macros and mapping, Player v1.
   - **Stage 3:** scripts, the tool page host, Pi soaks.
   M5 PV2+, M6 MT2+ and M8–M12 are parked; T1.5 is cut (§7).

**Checked at source.** Three helper reports fed this note: a CI inventory, a plan-vs-build extraction
and an engine review. I re-read at `48479fc` every line that a ruling below
rests on, and the citations point there. Claims I did not re-read are marked "(review)" or "(scout)".

## 1. CI speed (question 6)

### 1.1 Facts
- **Required checks.** Main's branch protection requires seven contexts, all jobs of `ci.yml` (Lab CI):
  `desktop`, `foundation`, `linux-arm64`, `linux-x64`, `sanitizers`, `studio` and `windows-x64`.
  `strict=false`; no approvals are required. The list is the owner's (`docs/workflow/STANDING.md:19-22`).
- **Notes classifier.** The `scope` job (`tools/ci/changed_scope.py:16-29`, fail closed) marks a PR
  notes-only when every path is one of: a top-level `*.md`, `proposals/**`, `docs/context/**`,
  `docs/workflow/**`, or `facts/**` other than `facts/dsp/**`.
- **What a notes-only PR runs.** Only `scope` and `foundation` execute (`foundation` is
  `python -m unittest discover -s tools/foundation/tests`). The other six required names report skipped
  jobs, which pass.
- **Timings** (hosted-runner diagnostics, 2026-11-26):

  | PR kind | Runs | Time |
  |---|---|---|
  | notes-only | 45798886381, 45797762693, 45799180059 | 31 s, 39 s, 1 min 44 s |
  | code | 45798673761, 45797945801, 45796776789 | 8 min 12 s, 9 min 26 s, 18 min 41 s |
- **Docs outside the notes scope run the full suite:** every `docs/*.md` guide and `docs/sequencer/**`.
  Readers of those files:
  - `tools/foundation/tests/test_doc_links.py`, which runs on notes PRs anyway;
  - `bench/sdk/out_of_tree_trial.py:39-40`, triggered by `bench/sdk/**` and not by the docs;
  - `tools/pi/ob_b_paths.py:31`, which nothing in CI imports or runs.

  `docs/specs/**` is read by the protocol generator and its tests (`tools/protocol/test_protocol.py:14`,
  `validate.py:12`, `generate.py:11`).
- **Advisory runs on product PRs.** Every ready engine or module PR also starts `offline-facts` (three
  runners). Its Windows leg is a standing red (`docs/context/CODEX_LEAD.md:88`). It only produces facts;
  no open PR or active contract row needs it at a head. `docs/workflow/milestones/M7.md:95-96` names it
  for M7 before/after numbers, and every M7 S-task has merged.
- **`facts.yml`** (device-off facts generator) runs on every push to `main` that touches `bench/**` and
  on PRs touching `bench/offline/**`. Median 57.7 min, max 118.2 min. Eight of its last ten runs failed
  or were cancelled (CI inventory, Actions API).
- **Workflow sprawl.** There are 30 workflow files. Sixteen exist for one task's evidence, for example
  `continuity-e5v.yml`, `quad-vca-d5.yml` and `choke-listening.yml`. `ob-c-a10.yml` failed 9 of its last
  10 runs.
- **Shared queue.** All PRs share one runner pool. A notes PR's two jobs queue behind the advisory
  matrices of code PRs.

### 1.2 Rulings
**R1.1 Required checks are unchanged.** The seven Lab CI names must be green on the exact head of every
PR, plus any workflow the task's contract names. No test, tolerance or required name changes.

**R1.2 What runs, by kind of change** (classified by every path in the PR):

| Change | Lab CI jobs that execute | Advisory on ready PRs | Manual or nightly |
|---|---|---|---|
| **Notes:** `proposals/**`, `docs/context/**`, `docs/workflow/**`, `facts/**` except `facts/dsp/**`, top-level `*.md`; after CI-S1 also every `*.md` under `docs/` outside `docs/specs/` | `scope`, `foundation` | Only where a facts file is a workflow's **input**: `facts/device/**` and `facts/compare/measured/**` start device-harness; `facts/perf/linux-*/instruction_baseline.json` starts instruction-gate | — |
| **Golden fixtures** `facts/dsp/**` | all | golden-renders | — |
| **Specs** `docs/specs/**` | all | protocol-v0-drift for the schema and `ENGINE_PROTOCOL.md` | — |
| **One module** `modules/<m>/**` | all | golden-renders, instruction-gate, m1-stage-evidence, portability, web-demo; ob-g7 for the five I/O modules | offline-facts, dispatched at base and head when a contract asks |
| **Studio** `apps/studio/**` | all | web-demo; ob-g7 for `osc*`/`midi*` files; offline-facts for `apps/studio/patches/**` | — |
| **Engine or host** | all (Studio shards skip on drafts that touch only the ten engine core files) | golden-renders, instruction-gate, m1-stage-evidence, e4b-stress (ready PRs only after CI-S3), web-demo, portability (include dirs), protocol-v0-drift (generated files), ob-g7 (I/O paths) | offline-facts (dispatch) |
| **Workflows, `tools/**`, `bench/**`** | all | the edited workflow itself, and any workflow whose inputs changed | facts.yml (dispatch only, after CI-S2) |

**R1.3 Prose docs join the notes scope.** Every `*.md` under `docs/` outside `docs/specs/` becomes notes
(CI-S1). Specs and every non-Markdown file stay code.

**R1.4 Facts generators leave the PR triggers.**
- `offline-facts` keeps only its own tooling paths and the bundled patches (applied here).
- `facts.yml` becomes dispatch-only (CI-S2).
- A facts file that a workflow writes never triggers that workflow (applied here for out-of-tree and
  ui-profile-advisory).
- A facts file that a workflow reads as input keeps its trigger.

**R1.5 New evidence uses existing tools.** One-off evidence uses `/dev-run` or a dispatch of an existing
workflow. A new workflow file needs a second user and the lead's approval. The lead deletes an evidence
workflow (its facts stay) once the milestone that cites it is accepted: `continuity-e5*.yml`,
`e5v-keyboard-attribution.yml` and `quad-vca-d5.yml` with M4/M7; `choke-listening.yml` with M7;
`osc-gate-snapshot-witness.yml` and `ob-c-a10.yml` with OB-g/OB-c.

**R1.6 Docs PRs never wait.** Planner, Architect and lead docs PRs stay on notes paths where possible,
enable auto-merge when opened, and end the run. Nobody waits for or polls CI. A docs PR that must touch
code paths (workflows, tools) says so in its title.

**R1.7 Nothing new moves to nightly in this run.** ob-g7's nightly stays with OB-h1 (B3);
compare-rebuild stays dispatch-only.

### 1.3 Edits
**Applied in this PR** (`on:` path lists only; no job, step, matrix or check name changes):
1. `.github/workflows/offline-facts.yml`: remove `native/**`, `engine/**`, `host/**`, `modules/**`,
   `sdk/**`, `targets/**` and `tests/native/**` from `pull_request.paths`.
2. `.github/workflows/out-of-tree.yml`: remove `facts/code/out_of_tree_trial.md`, the trial's own output.
3. `.github/workflows/ui-profile-advisory.yml`: remove `facts/app/ui-attribution*.json`, its own output.

This PR also touches workflow files, so it runs the full suite once. The three edited workflows run on
it through their own paths. They are advisory; auto-merge waits only for the seven required checks.

**For the lead** (one small PR each, `merge: lead`; `ci.yml` keeps its single writer):
- **CI-S1** `tools/ci/changed_scope.py` `is_notes_path`, test first. After the `docs/context|workflow`
  test, add:
  ```python
  if parts[0] == "docs":
      return parts[1] != "specs" and path.endswith(".md")
  ```
  New test cases:

  | Path | Expected |
  |---|---|
  | `docs/INSTALL.md` | notes |
  | `docs/sequencer/GROOVE.md` | notes |
  | `docs/specs/ENGINE_PROTOCOL.md` | code |
  | `docs/specs/protocol.schema.json` | code |
  | `docs/x.png` | code |
- **CI-S2** `facts.yml`: delete the `push` and `pull_request` events, leaving `workflow_dispatch`.
- **CI-S3** `e4b-stress.yml`: add `if: github.event_name != 'pull_request' || !github.event.pull_request.draft`
  to the stress job.
- **R1.5 deletions**, when each milestone is accepted.
- **Contract wording.** `M7.md:95-96` changes to: before/after numbers come from `offline-facts`
  dispatched at the base and at the head (§8).

### 1.4 What would overturn this
- A test outside `foundation` that reads a `docs/*.md` file. That file returns to code scope.
- A product defect that only a facts generator caught, missed by Lab CI and golden-renders. Restore that
  trigger for that path.
- Queue measurements showing that advisory jobs are not what delays notes PRs. Then the runner pool, not
  triggers, is the next lever.

## 2. Engine and host as the base for a headless Player (question 2)

### 2.1 What carries a Player as it is
- **The engine is a Qt-free child process** speaking NDJSON on stdio. No environment or Electron is
  needed; any process with pipes can drive it (S2 §1, §5; `host/sidecar/DESIGN.md:4-7`).
- **Every queue is bounded.** 256 commands and 256 replies; status and telemetry are coalesced; a graph
  holds at most 64 nodes and 128 cables (S2 §1).
- **Patch replacement fades out, panics the old graph and fades the new one in**
  (`host/sidecar/session.cpp:1026-1056`). `applyGraph` keeps unchanged instances (M4 E5,
  `ROADMAP.md:20`).
- **Device recovery:** audio loss retries with backoff up to 5 s; MIDI hotplug refreshes every 500 ms
  (S2 §4).
- **Pi facts.** Two 60-minute runs at 256 and 128 frames had zero engine dropouts and at most 27 % CPU,
  through the PulseAudio route (`facts/device/results/2026-11-15-pi-pulse-reruns.md`).

### 2.2 Gaps (verified unless marked)
| # | Gap | Evidence |
|---|---|---|
| G1 | A stalled audio callback is invisible. `running` means "PortAudio stream active", so `status` keeps saying `running`. The pipe watchdog watches only stdout writes and shutdown. The heartbeat planned in 0002 was never built. | `host/audio/portaudio_service.cpp:305`; `host/sidecar/protocol.cpp:249-266`; `proposals/0002-plan.md:107-109` |
| G2 | One MIDI fault can end MIDI for the session. The worker's `catch (...)` sets `running_ = false` with no restart and no status. `start_midi()` throws `unavailable` and runs on graph and device paths; the review traced the poll path to a process exit. | `host/midi/midi_service.cpp:157-160`; `host/sidecar/session.cpp:641-643` and callers `:344`, `:595`, `:1067-1118`, `:1325`, `:1344` |
| G3 | OSC Out leaves a gate high when a graph is replaced or stopped: `stop()` joins the worker and sends no final value. | `engine/control/osc_out_host.cpp:84-87` |
| G4 | OSC In stuck gate #326 and enqueue refusals #494 are open. No OSC soak fact exists. | `facts/perf/ob_g1_linux_l0_advisory_2026-11-21.md` (blocked, not run); `proposals/0022-ob1.1-headless-readiness.md` §3 |
| G5 | Controller input never reaches a client. MIDI Learn reports CCs only; `telemetry.monitor` covers only direct cabling from `osc.in`/`midi.in` (32 entries). There is no Program Change. | S2 §7; `docs/specs/ENGINE_PROTOCOL.md` (learn, monitor) (scout) |
| G6 | No client can set the tempo or play/stop: there is no transport command in the protocol schema. TR1h is parked behind M5 PV2. | `docs/specs/protocol.schema.json`; `docs/workflow/milestones/M3.md:34` |
| G7 | Settings are renamed into place without fsync on POSIX (Windows writes through), and the default path is relative to the working directory. | `host/sidecar/session.cpp:706-718`; `host/sidecar/session.h:22` |
| G8 | stderr is written synchronously on the control thread, one line per commit. An undrained stderr pipe eventually blocks the control thread. | `host/sidecar/session.cpp:957`, `:1131` |
| G9 | No SIGTERM handling (only SIGPIPE is ignored). Under systemd's default stop, the engine dies without a fade. | `host/sidecar/main.cpp:7` |
| G10 | The used-ID set grows without bound in sessions that only use `applyGraph`. | `host/sidecar/session.h:93` |
| G11 | Allocation checks count `operator new` only. The real PortAudio callback and the OSC worker are outside them. | `tests/native/abi2/allocation_watch.cpp:12-16` (review) |

Not gaps:
- **Runtime OSC/LAN config.** LAN stays a launch flag plus the patch (A91).
- **No graph readback.** The Player keeps the document it sent.
- **Exit 3 when stdout is not read for 5 s.** That is fail-fast; the supervisor must read continuously.
- **Protocol v0 is enough** (R2.1).

### 2.3 Rulings
**R2.1 The Player builds on the engine as it is.** One engine child per Player, protocol v0. Additions are
additive, capability-gated v0 fields generated from `protocol.schema.json` (the PV1 machinery). There is
no protocol v1 before the Player, so M5 PV2+ is parked. TR1h loses its PV2 dependency.

**R2.2 Gate P0: lab engine changes before any Player build relies on the engine** (Stage 1):
- **(a) Render liveness.** `status.audio` gains a monotonic count of rendered blocks and the state
  `stalled`, set when the stream is active but the count has not moved for 500 ms. `status` keeps coming
  from the control thread, which proves control-thread liveness. Test: a test module that spins in
  `process` makes status report `stalled` within 1 s. Overturned if the test shows PortAudio's ALSA
  backend already reports a stuck stream as inactive.
- **(b) Degrade, never exit, on controller faults.**
  - A MIDI or OSC start, stop or I/O failure leaves audio running and puts the error in status.
  - The MIDI worker restarts with backoff, and status shows its state.
  - Exit 2 (audio quarantine) and exit 3 (pipe) stay.
  - Test first: an injected MIDI start failure during the device poll, and a throwing MIDI worker.
- **(c) OSC Out releases gates.** On stop, replacement or graph swap, every gate or trigger row whose last
  sent value was nonzero sends 0 once (best effort, counted).
  - The send belongs to OB-h2, which already owns these files; its acceptance gains this row.
  - OB-h3's switching witness gains an OSC Out gate row and an OSC In route-relisten row.
- **(d) OB-h1** closes or routes #326 and #494 as 0022 §3 says, with arm64 rows.

**R2.3 Gate P1: before Player v1 ships** (Stage 2; Player development does not wait for it):
- **(e) Controller input stream.** One opt-in capability carries MIDI CC, Program Change, note on/off and
  OSC address/value to the client.
  - It is bounded. CC and OSC values are latest-wins per key. Program Change and notes go through a small
    FIFO with a drop counter and are never coalesced.
  - The engine stays the single owner of audio, MIDI and OSC devices.
  - Run 2 (0024) fixes the message shapes; a PV-class task implements them.
- **(f) Settings durability.** fsync the file and its directory on POSIX. The Player always passes an
  absolute `--settings` path in its state directory.
- **(g) SIGTERM** gets the same teardown as stdin EOF.
- **(h) Coverage.** Allocation and lock checks cover the real callback and the OSC worker thread.
- **(i) TR1h** (`setTransport`, `status.transport`) lands as an additive v0 capability. TR3 is Studio's
  control.
- **Low, no stage:** bound the used-ID set (G10); bound shutdown when the callback is stuck (the
  supervisor's kill covers it today).

**R2.4 Supervisor obligations.** These are the Player's, not the engine's; run 2 writes them into 0024.
- Read stdout and stderr continuously; send stderr to the journal.
- To stop: stdin EOF, then SIGKILL after 2 s.
- Restart with a growing delay (250 ms, doubling, capped at 30 s) and never give up.
- After every `hello`, send `loadGraph` with the current patch, then replay live values.
- Treat a `status` gap over 1 s, or `stalled` for over 1 s, as a hang: kill and restart.
- Run under systemd with `KillMode=mixed`, the Player as the main process, and a watchdog.

**R2.5 Studio desktop drops its give-up rule.** It replaces 3-exits-in-30-s (`apps/desktop/main.ts:258-266`)
with the same growing delay and no limit. After three fast crashes it shows a non-modal banner. The
renderer already reloads the patch on `hello` (`apps/studio/src/engine/RealEngine.ts:300-304`).

### 2.4 What would overturn this
- The stall test shows the backend already reports stalls (drop R2.2(a)).
- Run 2 shows every Player mapping and Program Change switch can run in the graph with no client event
  stream (drop R2.3(e)). This is unlikely: a Program Change must change the graph itself.
- A Pi soak shows the stdio protocol cannot keep up with status, telemetry and controller events (then
  rate limits, not a socket).

## 3. Module SDK for fast development (question 3)

### 3.1 Facts
- **Registration takes three hand edits in core files** (Architect-verified):
  `engine/control/module_catalog.h:3-48`, `module_catalog.inc:2-38` and `engine/CMakeLists.txt:104-125`.
- **Every module's wrapper code is compiled in one catalogue translation unit** that includes every
  `dsp.h`. Adding Gate Delay moved LFO by +1.85/+2.08 % with identical DSP instructions (#358 body).
  That coupling produced the bounded exceptions A39 (`ROADMAP.md:19`) and M7 r1.6/r1.6a
  (`docs/workflow/milestones/M7.md:11,20`). Every module promotion would trip unrelated rows.
- **CAT-1 #358 and MB1 #363 were closed** "not planned" in Architect run 46's cleanup, to be reopened
  when scheduled (`docs/workflow/BUILDERS.md:50`; `docs/workflow/CURRENT.md:30`).
- **0009 already designs the fix**: one target per folder, a generated registry, and `wire-describe`
  replacing `module.json` (`proposals/0009-module-build-and-registry.md:30-63`).
- **The out-of-tree build** last failed at configure (`facts/BASELINE.md:16`, 2026-11-14) and was never
  re-measured.
- **Module tools** offer only `check`, `test` and `render` (`tools/module/wsmod.py:15`).
- **The developer guides are stale.** `docs/MODULE_BUILD_GUIDE.md` names `native/` paths (S1 §5). The
  Clock README says "No transport sync" (`modules/clock/README.md:3`) while its code syncs
  (`modules/clock/dsp.h:8,17`).
- **Modulatable parameters.** `port_flags` includes `WS2_MODULATABLE` (`modules/port_state.h:22`). Seven
  modules in owner-wants B.4's list use it and so already have modulatable parameters: clock,
  function_envelope, ladder, mixer, noise, scale_offset and slew. The remaining 15:
  - **8 modules have parameters, none modulatable, and all their parameters are stepped:** chord,
    cv_to_notes, groove, host_keyboard, midi_in, midi_to_cv, notes_to_cv, quantizer.
  - **7 modules have no parameters:** midi_cc_to_cv, monitor, osc_in, osc_out, output, poly_merge,
    poly_split.

  Stepped and modulatable together already ships: blend mode, spectral mode, size and bands, resonator
  structure (S1 §2). D7 applies modulation in normalized units before the taper
  (`docs/specs/ABI2_SPEC.md:35`).

### 3.2 R3.1 Reopen CAT-1 and MB1 as one stage, MB
CAT-1's isolation is MB2's design: a target per folder is a translation unit per module. They become one
engine-build stage, following 0009's stages:
1. **MB1.** `wire-describe`, with a field-for-field equality test against every `module.json`;
   `gen_ui_catalogue.py` reads it.
2. **MB2.** One target, in its own translation unit, per `modules/<name>/`. A generated registry replaces
   `module_catalog.h/.inc` and the hand lists. `module.json` is deleted once MB1's equality holds.
3. **MB3.** A CI drop-in check with the SDK template.

Gates:
- **Audio goldens identical** on three platforms.
- **Catalogue order by module ID** (0009 decision 6). Any S0 or catalogue byte change is limited to order
  and listed in the PR.
- **One-time instruction re-baseline at MB2.** No row may be more than 1 % worse than at the MB2 base.
  Rows under a live bounded exception (A39 LFO; M7 r1.6/r1.6a) must come back within 1 % of their values
  before the exception. A miss needs function-level attribution.
- **A39, r1.6 and r1.6a expire** when MB2 merges.
- **Out-of-tree.** After MB2, `out-of-tree.yml` is dispatched to replace the 2026-11-14 fact.

Order: right after the writer lane's current task. CAT-1's original writer was B4, which takes MB after
OB-h4 #609. If B4 is blocked on CMP-1 #592, MB goes first. MB2 is a structural PR under the lab's full
rules and Architect review.

### 3.3 R3.2 The freeze and the new repo
- **The lab's new-module freeze ends when MB2 merges** (it was the OB1 tag). OB-h4 Gate Delay stays the
  one exception until then.
- **New modules are developed in `wirescape-test`** and promoted after MB2 as a folder copy.
- **No `wirescape-test` change ever needs a lab core edit committed.** Before MB2, registration is a
  scripted build-time step in a scratch copy of the pinned lab. After MB2, the folder is copied into the
  pinned checkout's `modules/`. Run 2 specifies the script and the pin rules.

### 3.4 R3.3 Modulatable-parameter policy
1. **Continuous parameters.** Every continuous parameter is `MODULATABLE` unless the module's `DESIGN.md`
   gives the reason: cost, or a value that sets allocation or structure.
2. **Stepped parameters.** A stepped parameter is `STEPPED|MODULATABLE` when a change at a block boundary
   is musically meaningful and safe: scales, roots, shifts, octaves, modes, note toggles. It stays
   setParam-only when it sets allocation or structure: voice counts, allocation and steal modes, channel
   filters, sequence length.
3. **No render change.** Adding the flag leaves unmodulated renders bit-identical (goldens) and passes
   the instruction gate. New parameters are appended with defaults that keep renders identical.
4. **Mapping does not need the flag.** The Player, map mode and controller maps may set any parameter
   with `setParam`. `MODULATABLE` is needed only for cables and for macro ranges carried by modulation.
   Run 2 decides how macros treat setParam-only parameters.
5. **Batch scope.** The module batch covers the 8 stepped-only modules in §3.1, plus new continuous
   parameters. Run 2 lists the parameters per module under rule 2.

### 3.5 What would overturn this
- **MB2's per-module units cost more than 1 % across arm64 rows.** Then use CAT-1's fallback: generated
  per-module `.cpp` files linked into one library (#358 allows it).
- **The owner wants the OB1 candidate cut before any build-system change.** MB2 then waits for the
  candidate commit, not for the tag.

## 4. Workflow cost (question 4)

### 4.1 Facts
- **Commits:** 358 squash commits in 12 days. 72 % touch only non-product paths; 54 subjects say
  "Architect run" (S5 §1-3).
- **Rulings:** 81 distinct A-numbers appear in commit messages; 12 appear in the inbox or QUESTIONS
  files (S5 §5).
- **Rule docs:** 4,579 lines across 41 files (S5 §6).
- **Contract cells read like prose.** `ROADMAP.md:20` (M4) is one cell of about 250 words. ROADMAP also
  carries appended lead deltas.
- **Bounded exceptions recur in one class** (instruction-gate codegen noise: A39, r1.6, r1.6a).
- **Workflows:** 30 files, of which 16 serve one task each (§1.1).

### 4.2 What stays strict in the lab (it pays for itself)
- **Required Lab CI** at the exact head, with the fail-closed scope classifier.
- **Audio goldens.** Base/head goldens are identical for structural PRs; a golden difference is a defect
  until proven otherwise.
- **Realtime rules.** No allocation, locks or I/O in process; sanitizers; devices off; owner-only device
  runs.
- **Facts stay neutral,** and an unmeasured row stays unmeasured.
- **One writer** for `ci.yml` and `host/sidecar/`.
- **Never loosen a test to pass.**
- **Architect review** for engine, host, SDK, protocol and ABI changes and for promotions.

### 4.3 Rulings
- **W1. Two speeds.**
  - `wirescape-test`: module development under T0/T1, one simple review, any agent merges.
  - `wirescape-headless`: the Player service, API, UI, scripts and bundles, under loose rules.
  - The lab keeps its full rules for `engine/`, `host/`, `sdk/`, `docs/specs/`, `apps/`, the gate tools
    and promotions. Run 2 writes the two repos' rules.
- **W2. Merges.** Studio-only and tools-only tasks merge by the lead on exact-head green plus a Result
  (SR20 `merge: lead`). Facts-only PRs auto-merge. Architect review is kept for the W1 strict paths only.
- **W3. A ruling lives in the file it changes.**
  - It binds once it is a revision line in that contract or in STANDING, with date and source link.
  - A commit message or comment is evidence, not a rule. A-numbers become optional labels.
  - The Architect builds one index of live A-rulings (number → contract line) once, with a Sonnet scout.
- **W4. Reading budget.** An agent's mandatory reading is AGENTS.md, its role brief, its lane row and its
  task's contract row: at most 400 lines.
  - Accepted contracts (M0, M1, M2, CI1, OB0) and parked ones carry a one-line banner: "closed" or
    "parked — read only if your task names it".
  - Closed QUESTIONS rows move to a history file.
  - ROADMAP keeps one row per item, each cell at most 40 words, with no appended deltas. CURRENT holds
    deltas and is trimmed weekly.
- **W5. No renewed exceptions.** A bounded exception also names its structural fix. If the same class
  recurs, the fix is scheduled instead of a new exception; MB2 is the fix for the codegen class.
- **W6. Evidence workflows** follow R1.5.

### 4.4 What would overturn this
- **Promoted modules keep failing lab gates.** Tighten T1 in `wirescape-test`; do not slow the lab.
- **The owner prefers rulings by number.** Keep the index (W3) as the primary view.

## 5. Build vs plan (question 1)
The plan read here is 0001–0004 and 0021. Full table: plan-vs-build extraction (helper); the rows used
here were re-read.

### 5.1 Achieved
- **One engine.** ABI1 is gone and M1 was accepted on 2026-11-22 (`ROADMAP.md:18`).
- **The measurement floor.** Goldens, the instruction gate, sanitizers and Cortex-M7 compile-only facts
  exist, and 24/24 bundled patches render on three platforms (`facts/BASELINE.md:17-18`).
- **The live-edit chain is in code.** Edit operations and history (M2 accepted), live modulation amount
  (E4), device and buffer changes that keep the graph (E6), state-carrying replace (E5), voice count in
  place (E5v) and E7 are all merged (`ROADMAP.md:16,20`).
- **Protocol validation** is generated from a schema (PV1).
- **The engine has a transport** (TR1e).
- **Sound work.** M7 batches 1 and 2 are merged.
- **Shipping.** OB0 is tagged and installable, and there is a Pi install script (OB-b).
- **Module tools v0** (MT1).

### 5.2 Missing or weaker than planned
- **Module drop-in and out-of-tree builds** (0002 targets 5–6, `proposals/0002-plan.md:49-50`): not done;
  MB was parked (§3).
- **Module knowledge in core code** (target 9, `:53`). A grep at `48479fc` finds module-ID string
  literals in 10 non-test engine and host files. That is a lower bound, not a facts file.
- **`legacy_index` and native v1 reading remain** (`sdk/include/wirescape/module2.h:43`;
  `host/document/runtime_patch.cpp:152`). V1 is parked under the owner's saved-patch constraint.
- **The heartbeat was never built**, and neither was moving blocking device work off the control thread
  (`proposals/0002-plan.md:107-109`). This is G1.
- **No client can drive the transport** (G6). Clock-synced work cannot be used live.
- **Developer loop:** L1 is partial; L2 and L3 and the tools `new`, `dev` and `bench` are not done.
- **Portability:** Daisy, CLAP and the compiler have not started, and "portable tier" is undefined.
- **Performance targets:**
  - the 8-voice −20 % target has no design (`proposals/0004-execution-plan.md:125`);
  - the 200-module cable drag measured 66.7 ms against a 20 ms target and has not been measured since
    (`facts/BASELINE.md:20`).

### 5.3 Classification
- **Fundamental** (the design or process, not one bug):
  - **F1** module codegen coupled through one translation unit, plus core registration (H2);
  - **F2** no render liveness (H1);
  - **F3** process weight and rulings that cannot be found (H6);
  - **F4** controller input that no client can see (M1).
- **Defects:** H3–H5 and M3–M11 in §6.
- **Unmeasured. All speed conclusions stay provisional:**
  - edit gaps after M4 (CN #523 pending);
  - the device-change gap on hardware;
  - the Pi's worst block at a fixed 128 frames;
  - any OSC or MIDI soak;
  - CPU in long silence (denormal rows unavailable);
  - UI cost on the Pi or a real GPU;
  - CMP-1;
  - Electron RSS;
  - active per-patch CPU;
  - 200-module UI since 2026-11-14 (S4 §6).

  The only Pi CPU facts went through PulseAudio, not exclusive ALSA. No claim about Pi headroom for a
  Player plus a kiosk UI stands until the Player's Pi soak runs.

## 6. Findings, ranked
| Rank | Finding | File:line |
|---|---|---|
| **H1** | A stalled callback still reads `running`; there is no render liveness or heartbeat | `host/audio/portaudio_service.cpp:305`; `host/sidecar/protocol.cpp:249-266` |
| **H2** | Every module compiles in one catalogue TU; adding a module moves unrelated rows; three core edits per module | `engine/control/module_catalog.h:3-48`; `.inc:2-38`; `engine/CMakeLists.txt:104-125`; #358 |
| **H3** | A MIDI fault ends MIDI silently or escapes as a process exit | `host/midi/midi_service.cpp:157-160`; `host/sidecar/session.cpp:641-643` |
| **H4** | OSC Out leaves gates high on stop or swap | `engine/control/osc_out_host.cpp:84-87` |
| **H5** | #326 stuck gate and #494 refusals open; no OSC soak fact | `facts/perf/ob_g1_linux_l0_advisory_2026-11-21.md` |
| **H6** | 72 % of commits are process-only; 81 rulings, 12 in files; 4,579 rule lines | S5 §2, §5, §6 |
| M1 | No controller events or Program Change reach a client | S2 §7 |
| M2 | No transport command in the protocol | `docs/specs/protocol.schema.json`; `M3.md:34` |
| M3 | Settings rename without fsync (POSIX); path relative to the working directory | `host/sidecar/session.cpp:706-718`; `session.h:22` |
| M4 | Synchronous stderr per commit on the control thread | `host/sidecar/session.cpp:957,1131` |
| M5 | No SIGTERM teardown | `host/sidecar/main.cpp:7` |
| M6 | Desktop gives up restarting after 3 exits in 30 s | `apps/desktop/main.ts:258-266` |
| M7 | Module-ID literals in 10 non-test core files (target 0) | grep at `48479fc` |
| M8 | Out-of-tree build last failed; never re-measured | `facts/BASELINE.md:16` |
| M9 | Stale developer docs: build guide `native/` paths, SDK guide paths, Clock README | `docs/MODULE_BUILD_GUIDE.md:65-67`; `modules/clock/README.md:3` |
| M10 | Standing advisory reds (offline-facts Windows; ob-c-a10 9/10; facts.yml 8/10) | `docs/context/CODEX_LEAD.md:88`; CI inventory |
| M11 | Owner-wants B.4 list names 7 modules that already have modulatable parameters | `modules/port_state.h:22` |
| L1 | The used-ID set grows without bound in `applyGraph`-only sessions | `host/sidecar/session.h:93` |
| L2 | Allocation checks miss the real callback and the OSC worker | `tests/native/abi2/allocation_watch.cpp:12-16` (review) |
| L3 | `legacy_index` and native v1 read path remain | `sdk/include/wirescape/module2.h:43`; `host/document/runtime_patch.cpp:152` |
| L4 | EOF shutdown can hang with a stuck callback; the supervisor's kill covers it | `host/sidecar/main.cpp:48,56` |

## 7. Roadmap (question 5)

### 7.1 Keep, cut, merge or park
| Item | Ruling | Next |
|---|---|---|
| M3 MB1–MB3 + CAT-1 #358 | **Merge into stage MB; unpark now** (R3.1) | B4 after OB-h4 |
| M3 TR1h | **Keep, Stage 2**, as an additive v0 capability; the PV2 dependency is cut (R2.3 i) | B5 after Gate P0 |
| M3 TR3 | **Keep, Stage 2** (Studio tempo and play/stop) | B1 after TR1h |
| M3 V1 | **Park** (owner's saved-patch constraint) | owner |
| M3 T1.5 | **Cut**; stale-doc fixes are listed separately (§8) | — |
| M3 acceptance | **Accept when MB2 merges** | Architect |
| M4 | **Keep**: CN final facts #523, then the KNOWN_ISSUES A2 rewrite, then acceptance | B3 |
| M4 E3a/E3b/E3c (OB1.1) | **Keep**: live CC/OSC/Groove data serves Player mapping | B2, B5 in flight |
| M5 PV2a–PV5 | **Park**; reopen only for a breaking change (R2.1) | — |
| M6 MT2+ | **Park** in the lab; module tooling grows in `wirescape-test` and is promoted only if a lab gate needs it | run 2 |
| M7 | **Keep** until OB-d (owner listening) is done, then close; later sound fixes arrive through `wirescape-test` | owner, B1 |
| M8 | **Park** until 3 modules are promoted from `wirescape-test` and their "limitation found" issues are collected; then re-plan M8 from them | — |
| M9, M10, M11 | **Park** (M10 batch 0 facts and `portability.yml` stay) | — |
| M12 | **Park**; run 2 decides whether the tool page host reuses P3's sandbox and pulls it forward | run 2 |
| OB1 acceptance | **Keep as written** (owner-only items recorded, never waived). It no longer gates any new work; the module freeze moves to MB2 | owner |
| OB-h1, #494 | **Keep, Gate P0** | B3, B2 |
| OB-h2 | **Keep, plus gate release** (R2.2 c) | B2 after #540 |
| OB-h3 | **Keep, plus OSC Out gate and route-relisten rows** | B5 #610 |
| OB-h4 | **Keep** (the last module under the freeze exception) | B4 #609 |
| OB-h5 | **Done** (#606); run 2 sets the generic OSC default its presets carry | — |
| OB-h6 | **Keep**; it becomes the core of the Player's bundle check | B3 |
| New: Gate P0 (a) liveness, (b) degrade | **Add, Stage 1** | B5 (a), B2 (b) |
| New: Gate P1 (e)–(h) | **Add, Stage 2**; (e) after run 2 fixes the shapes | B2, B5 |
| New: Studio restart policy | **Add, Stage 1** (R2.5) | B1 |

### 7.2 Stages across the three repos
**Stage 0: now until run 2 merges.**
- **lab:** finish in-flight work (#540, #545, #592, #600, #609, #610, #523). Apply CI-S1–S3. The
  Architect transcribes 0023.
- **`wirescape-test`:** no product work; run 2 writes its rules and layout first.
- **`wirescape-headless`:** no product work; run 2 writes its design first.

**Stage 1: foundations.**
- **lab:**
  - MB1 → MB2 (B4);
  - Gate P0 (a) (B5) and (b) (B2);
  - OB-h2 with gate release; #494 if OB-h1 says so;
  - M4 acceptance;
  - Studio restart policy;
  - doc fixes.
- **`wirescape-test`:**
  - a harness pinned to the lab, with T0/T1 CI and build-time registration;
  - the first modules per run 2 (Random, Clock Div/Mult, envelope Trigger mode and `delay`, Macro).
- **`wirescape-headless`:**
  - the Player service: supervision per R2.4, bundle load, patch switching through the API;
  - a fake player and the API v0 docs;
  - a bundle check on OB-h6;
  - CI against the engine built at `LAB_PIN` with `--null-audio`.

**Stage 2: Player v1 and the Studio bridge.**
- **lab:**
  - Gate P1: the controller stream, settings, SIGTERM, coverage, TR1h;
  - TR3; MB3; the first promotions;
  - Studio's Macro UI, Mappings panel, map mode, lock toggle, bundle export and Player preview (run 2
    specs).
- **`wirescape-test`:** the rhythmic modulator, LFO additions and the modulatable batch.
- **`wirescape-headless`:**
  - the reference UI with every menu and parameter;
  - `player.json` pages and hardware map;
  - switching by UI, controller and Program Change;
  - variations;
  - the UI design guide.

**Stage 3: scripts and soaks.**
- **headless, with Studio:** the Python runner and helper library, OSC auto-sync and declared controls;
  the Studio tool page host (run 2 design).
- **Pi:** Player soaks of 4–12 h (flat memory, flat CPU in silence, zero OSC drops) as Player v1 release
  gates. The owner's OB1 items run whenever the owner runs them.

### 7.3 Lane suggestion (the Architect and lead assign)
| Lane | Queue |
|---|---|
| B1 | restart policy → TR3 and macro/mapping UI (after run 2) |
| B2 | #540 → OB-h2 with release → #494 if needed → P0 (b) → controller stream |
| B3 | OB-h1 → #523 → OB-h6 → Player soak harness facts |
| B4 | OB-h4 → MB1 → MB2 → MB3 → promotions |
| B5 | #545 → OB-h3 → P0 (a) → TR1h → P1 (g)(h) |

The two new repos get their own agents under their loose rules, not lab lanes, so lab path ownership
stays clean.

### 7.4 What would overturn this
- **Owner-only OB1 items land soon.** Tag first; the order is unchanged.
- **A Pi soak shows the engine cannot carry the Player's load.** Measure before adding features; Stage 2
  waits.
- **MB2 slips more than two weeks.** Promote modules with the three registration lines, Architect-reviewed,
  once per module.

## 8. Edits for the Architect
Applied in this PR: this note, `docs/workflow/ROADMAP.md`, `docs/workflow/PRIORITY.md`, and the three
workflow trigger edits (§1.3). For the Architect to transcribe:
1. **Lead tasks for CI:** CI-S1, CI-S2 and CI-S3 (§1.3); R1.5 deletions when their milestones are
   accepted.
2. **`M7.md:95-96`:** before/after numbers come from `offline-facts` dispatched at the base and at the
   head.
3. **`M3.md`:**
   - MB1–MB3 unparked as stage MB, with CAT-1 merged into MB2 (R3.1 gates);
   - TR1h's "M5 PV2 merged" dependency removed;
   - T1.5 cut, V1 parked;
   - M3 accepted at MB2.
4. **Issues:**
   - reopen #358 and #363, or file one "MB" issue that closes both;
   - file Gate P0 (a) and (b) and the Studio restart policy now;
   - file Gate P1 (f)–(i) at Stage 2, and (e) after run 2.
5. **`OB.md`:**
   - OB-h2 gains the gate-release acceptance row;
   - OB-h3's witness gains an OSC Out gate row and a route-relisten row;
   - the new-module freeze ends at MB2;
   - OB1 gates no new work.
6. **STANDING:** W3 (where rulings live), W4 (reading budget), W5 (no renewed exceptions).
7. **Docs fixes, one small `docs:` task** (prose is notes after CI-S1; the spec line runs the full suite):
   - the Clock README transport line;
   - the `SDK_AUTHOR_GUIDE.md` and `ARCHITECTURE.md` missing paths;
   - the `M8 MIDI 1` examples in `docs/specs/ENGINE_PROTOCOL.md`, which become `Test MIDI 1`.

   `MODULE_BUILD_GUIDE.md` is rewritten for the two-stage flow after MB2; run 2 places the guides.
8. **Erratum in `01_OWNER_WANTS.md` B.4:** 7 of the 22 listed modules already have modulatable
   parameters (§3.1). Run 2 inherits the corrected list. The `wirescape-test` modules README row repeats
   the error; run 2 replaces that README.
9. **BUILDERS and CURRENT:** lane queues per §7.3. Run 1's areas leave the freeze; run 2's areas
   (macros, mapping, OSC, scripts, the tool host, the new repos' design) stay frozen until run 2 merges.

Note: this run's branch is `claude/planner-run-1-vosa12`, not `planner/run-1`; the session's push rules
allow only that branch.

Signed: claude-planner, 2026-11-26
