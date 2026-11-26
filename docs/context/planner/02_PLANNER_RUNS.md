<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Planner runs 1 and 2 (owner direction, 2026-11-26)

## The role
**`claude-planner`** is a planning seat run on Opus, separate from the Claude Architect so that its
review of the build and the Architect's verification stay independent. It replaces the retired Fable
seat for these runs only. **Run 1 is done** ([0023](../../../proposals/0023-review-and-replan.md), #618). **Run 2 is
recommended as two sessions, `planner: run 2a` then `planner: run 2b`, each at max effort** (see "Run 2").
A single `planner: run 2` at max effort is the fallback.

## Before deciding anything
Run 2 does **not** reread the whole plan. Read only the list for your run in "Reading order" below, and
read "Run 2 prep": it lists the setup that is already done, so a run 2 session does none of it again.

## Authority
- The owner gives the Planner **final decisions** on the questions below for these two runs. The Claude
  Architect writes them into contracts, tasks and lane assignments without reopening them. It flags
  only (a) conflicts with "Fixed" items in `docs/context/CONSTRAINTS.md` (owner only), (b) factual
  errors, with the source line, and (c) contradictions between the two runs.
- The Planner rules on design. It does not write or merge lab product code (`engine/`, `host/`, `modules/`,
  `apps/`, `tools/`, `sdk/`). It may write proposals, contracts and docs in the lab (one docs PR per
  run) and docs/rules in `wirescape-test` and `wirescape-headless`.
- The Architect's recommendations in `01_OWNER_WANTS.md` are inputs, not constraints. The owner's
  wants (section B) and principles (section A) are the requirements. Section C items marked "Planner
  decides" are the Planner's.
- Freeze: while the runs are open, no new Architect rulings or contracts in the areas below. The
  builder lanes keep their current tasks.

## Run 1 — independent review of the build, then the roadmap
**Status: done** (#618 `337d8e8`; transcribed by Architect run 47, #623). Kept for the record.
**Why first:** nobody has reviewed the build as a whole against the first plan (0001–0004, written by the
retired Fable seat) since it was written. Run 2's designs
depend on what the engine, SDK and workflow can actually carry.

Decide:
1. **Build vs plan:** against 0001–0004 and 0021, what the rebuild achieved and what is missing or
   weaker than planned. Separate fundamental problems, defects and unmeasured concerns. Speed
   conclusions stay provisional where facts are missing (S4 "Missing").
2. **Engine and host as the base for a headless Player:** sidecar lifecycle, protocol v0, patch
   switching, OSC/MIDI, crash and hang behaviour, long-run resources, realtime safety. What must change
   before the Player relies on it (S2 §7 lists the gaps)?
3. **Module SDK for fast development:** what blocks building and testing a module outside the lab.
   Rule on CAT-1 #358 / MB1 and on the modulatable-parameter policy (S1 §3).
4. **Workflow cost:** which lab rules keep quality and which cost more than they return (S5).
   Decide what stays strict in the lab and what moves to the loose repos.
5. **Roadmap:** keep, cut, merge or park each of M3–M12, CAT-1, MB1, OB1 acceptance and the 0022 rows
   (OB-h1–h6), against the owner wants. Produce the new order across the three repos.

Output: `proposals/0023-review-and-replan.md`: findings ranked High/Medium/Low with file:line, rulings on
1–5, the new roadmap table, and "what would overturn this" for each major ruling. Update
`ROADMAP.md`/`PRIORITY.md` to match, or list the exact edits for the Architect.

6. **CI speed (owner, 2026-11-26):** docs, plan and proposal changes, and Planner and Architect runs in
   general, must not wait on long CI. Decide which workflows run or skip for each kind of change
   (docs-only, facts-only, module-only, Studio-only, engine/host), what stays required before a merge,
   and what moves to nightly or manual runs. Never loosen a test to pass. Write rulings plus the exact
   workflow edits; apply them in the run-1 PR if they are path filters only.

Suggested order inside run 1: CI speed (6) first, so the rest of the session's PRs merge fast; then 2–4;
then 1 and 5.

## Run 2 — the new architecture and its contracts
Decide:
1. **`wirescape-test`:** layout, how it pins the lab and registers modules (before and after CAT-1), T0/T1/T2,
   review and merge rules, the escalation rule, promotion, Actions minutes (Windows on ready PRs only or not).
2. **`wirescape-headless`:** Player service (language, process model, supervision, boot, files), Player
   API (messages, state model, versioning, fake player), `player.json` (setlist, pages, hardware map,
   controls), the reference UI (technology, Pi cost limit), the UI design guide, stability gates.
3. **Macros and mapping:** the Macro module (8 knobs, pages of 8), range semantics (base/amount vs a new
   engine mode), stepped parameters, curves, live range edits, hidden mapping nodes, the Mappings panel,
   map mode, and how macros reach `player.json`.
4. **OSC and scripts:** naming (owner: the simplest), OSC In label, indicator, toggles and default; the
   script declaration format and auto-sync (matching, removal, overwrite vs unlink, 8-row limit); the
   Python runner and helper library, permissions, declared controls, timing.
5. **Tool page host:** the Tool API, the permission model, and its relation to the 0015 panel host.
6. **Module batch specs:** envelope Trigger mode and `delay`; Random; Clock Div/Mult; the rhythmic
   modulator; LFO additions; which parameters become modulatable per module.
7. **Guides:** the list, where each lives, the agent-ready format.
8. **Order:** stages, cross-repo dependencies, and the first task batch per repo.

### Recommended: two sessions (2a, then 2b), each at max effort
Eight questions, two proposals, two repo rule sets and three task lists will not fit one session's context
without compaction, and compaction loses the nuance these rulings need. The split follows the dependency
order: module work unblocks first, and the Player consumes what 2a decides.

| Session | Questions | Outputs |
|---|---|---|
| **`planner: run 2a`** (modules) | 1 (`wirescape-test`), 3 (macros and mapping), 6 (module batch), 8 for `wirescape-test` | `proposals/0024-test-repo-macros-modules.md`; `wirescape-test` `README.md`/`AGENTS.md` (+ `modules/README.md`); the `wirescape-test` task list; lab rows for macro and mapping engine or Studio work; what `player.json` must carry for macros (for 2b) |
| **`planner: run 2b`** (Player) | 2 (`wirescape-headless`), 4 (OSC and scripts), 5 (tool page host), 7 (guides), 8 for headless, the lab and the cross-repo order | `proposals/0025-player-osc-scripts-tools.md`; `wirescape-headless` `README.md`/`AGENTS.md`; the headless task list; Gate P1 (e) controller stream message shapes; lab task rows; the final stage order across the three repos |

- 2b starts after 2a's lab PR merges. 2b builds on 0024 and does not reopen it. It may flag a contradiction
  in its own proposal, and the Architect brings it to the owner.
- The freeze on run 2's areas lifts only after 2b merges. The Architect may file the `wirescape-test` tasks
  from 2a straight away, so module work starts while 2b runs.

### Fallback: one session (`planner: run 2`, max effort)
Answer all eight questions in this order: 1 and 8 for `wirescape-test`, then 3 and 6, then 2 and 5, then 4
and 7, then 8 for everything. Write 0024 (2a's scope) and then 0025 (2b's scope), with the same file names as
above. If the session is cut short, commit what is decided so far; the next run continues from the open items.

### Every run 2 session
- One docs PR in the lab, with auto-merge enabled.
- One PR in each new repo it covers, against `main`.
- It does not file issues and does not edit lane assignments: the Architect does both from the task lists.
- Task list format: title, repo, paths, acceptance, tier, dependencies, lane or agent. For lab rows, also name
  the contract each row goes into (OB, M3, Gate P1, or a new contract).

## Run 2 prep: already done, do not redo (Architect run 47 and the follow-up session, 2026-11-26)
**Lab `main` at writing: `f8c994c`.** [`proposals/0023`](../../../proposals/0023-review-and-replan.md) binds run 2. Build on it and do not
re-derive it. The Architect checked 0023's citations at source and found one wrong line: R2.5 cites
`RealEngine.ts:300-304`, but the reload is at `:393-436`. The ruling holds.

**Run 1 transcription (#623):**
- **Contracts:**
  - [M3 r2](../../workflow/milestones/M3.md): stage MB unparked, TR1h without PV2, T1.5 cut, V1 parked, M3 accepted at MB2;
  - [M7 r1.7](../../workflow/milestones/M7.md);
  - [OB r2.13](../../workflow/milestones/OB.md): OB1 gates no new work, the freeze ends at MB2, OB-h2 gate release, OB-h3 rows,
    Gate P0 rows;
  - [STANDING](../../workflow/STANDING.md) SR22 (where rulings live), SR23 (reading budget), SR24 (no renewed exceptions) and
    SR25 (evidence workflows).
- **CI:** CI-S1–S3 applied. Docs PRs, including every `docs/**/*.md` outside `docs/specs/`, run only `scope` and
  `foundation` (about 1 min). `facts.yml` is manual-only, and e4b-stress runs on ready PRs only.
- **Process docs:** [`RULINGS.md`](../../workflow/RULINGS.md) index, `QUESTIONS_HISTORY.md`, and banners on closed and parked
  contracts.
- **Doc fixes:** B.4 erratum in `01_OWNER_WANTS.md`; stale paths in `SDK_AUTHOR_GUIDE.md` and `ARCHITECTURE.md`;
  Clock README.

**Lab issues filed or reopened:**
- MB1 [#363](https://github.com/kalharbi11/wirescape-lab/issues/363) and MB2 + CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358) (B4);
- P0a render liveness [#619](https://github.com/kalharbi11/wirescape-lab/issues/619) (B5) and P0b fault tolerance [#620](https://github.com/kalharbi11/wirescape-lab/issues/620) (B2);
- Studio restart policy [#621](https://github.com/kalharbi11/wirescape-lab/issues/621) (B1);
- fake MIDI endpoint rename [#622](https://github.com/kalharbi11/wirescape-lab/issues/622).

Gate P1 (f)–(i) is filed at Stage 2. **P1 (e), the controller input stream, waits for run 2's message shapes**:
2b owns them.

**Merged since run 1 (relevant to run 2):**
- M4 E3c live CC/OSC data (#540, `f8c994c`). Under A95, the eight-row mapping slot is the truth for CC Learn
  occupancy: an unwired default row is free, Learn takes the lowest free index, Forget resets the row, and
  Studio-only hints are refused.
- OB-h5 OSC presets (#606); the generic OSC default its presets carry is run 2's call.
- CMP-1 raw artifacts are retained (#592).

**Lab lanes:** wrap-up has ended for run 1's areas, and lanes B1–B5 run 0023 §7.3 queues ([BUILDERS](../../workflow/BUILDERS.md)).
Nothing in a lane touches run 2's frozen areas: macros, mapping, OSC In features, scripts, the tool page host
and the new repos' design.

**New scout S8:** [`scout/S8_module_params.md`](scout/S8_module_params.md), a per-parameter table for question 6. It covers flags,
ranges, defaults, and whether a parameter sets allocation or structure.

**Facts for run 2 (checked at source, `337d8e8`):**
- No module exists today for Random or sample-and-hold, Clock Div/Mult, Macro, or a rhythmic modulator other
  than Groove. Each is new.
- `function_envelope` is gated AR: `rise`, `fall` and `curve`, all modulatable. It has no trigger mode and no
  `delay`. ADSR already has Gate/Trigger `mode` and `hold`.
- `lfo` has one shape (sine) and no inputs. It has `sync` and `beats` parameters.
- Clock's only multiply is `ticks_per_beat` (1–24).
- Allocation and structure parameters among the batch: `host_keyboard` voices and mode; `midi_to_cv`
  voice_count, allocation_mode, mono_priority, legato and channel_filter; `notes_to_cv` voices; `midi_in`
  channel_filter.
- `midi_to_cv` `steal_policy` has range 0..0 and is never read. Details in S8 §Notes.
- The engine's default settings path is relative (`host/sidecar/session.h:22`). The Player must pass an
  absolute `--settings` (R2.3 f).

**The two new repos (checked 2026-11-26):**
- The default branch of both `wirescape-headless` and `wirescape-test` is **`main`**. The owner switched
  headless today; nothing in either repo named the old branch.
- Neither repo has workflows yet. Both `LAB_PIN` files pin lab `11a68c2`; run 2 decides the bump rule and the
  first bump.
- `wirescape-test/modules/README.md` repeats the B.4 error. Its Envelope row also says Function Envelope has
  no modulatable parameters, which is wrong. 2a replaces that README.
- Open run 2's PRs against `main`. Use whatever branch the session allows.

## Architect-verified highlights from the scout pack
Checked at source by the Architect on 2026-11-26 (lab `11a68c2`):
- **OSC Out network permission:** `setOsc` is refused (`host/sidecar/session.cpp:1257`). Architect run 46
  (A91, #613) already ruled the permission switch is `--confirm-lan`; no action needed.
- **Registering a module means three hand edits in core files:** `engine/control/module_catalog.h`,
  `engine/control/module_catalog.inc` (37 `WS_APP_MODULE` lines) and `engine/CMakeLists.txt`.
- **No shipped patch uses `osc.in`** (apps/studio/patches, host/examples).
- **Replace fade:** `WS2_REPLACE_FADE_DEFAULT_MS 20`, maximum 500 (`sdk/include/wirescape/module2.h:90-91`).
- **Supervisor gaps (S2 §7):**
  - no heartbeat or ping (liveness is the 100 ms `status` stream);
  - no Program Change reporting;
  - no graph readback;
  - no runtime OSC configuration;
  - no shutdown command (stdin EOF only);
  - the settings path is relative to the working directory.
- **Desktop restart policy:** 3 unexpected exits per 30 s, then a dialog; main never reloads the patch
  (`apps/desktop/main.ts:258-266`; the renderer re-sends `loadGraph` on a new `hello`).
- **Process weight (S5):**
  - 358 commits in 12 days; 72 % touch only non-product paths;
  - 4,579 lines of rule and process docs;
  - 29 workflows;
  - 81 distinct rulings (A1–A94).
- **Facts gaps (S4):**
  - no OSC soak result;
  - no CMP-1 benchmarks;
  - no Pi acceptance session;
  - no UI measurement on the Pi or a real GPU;
  - hosted cable-drag p95 is 66.7 ms at 200 modules.
- **Pi facts that exist (S4):** 60-minute runs at 256 and 128 frames, 0 engine dropouts, CPU max about 27 %
  (2026-11-14/15).
- **Stale docs (S1 §5, S7 §1):**
  - `docs/MODULE_BUILD_GUIDE.md` and several READMEs name `native/...` paths that no longer exist;
  - the Clock README says it has no transport sync, but `modules/clock/dsp.h` has it.
- **Studio (S6):**
  - no UI framework (TypeScript, DOM cards, SVG cables, Vite, Playwright);
  - Studio-only data sits under the patch `ui` key, and unknown fields survive load and save;
  - no macro or mapping layer, no lock mode, no sandboxed panel `ui/` yet.

## Reading order and budget
**Every run 2 session**, in order:
1. this folder's `README.md`, then this file's "Authority", "Run 2" and "Run 2 prep";
2. `01_OWNER_WANTS.md` sections A, B and C;
3. 0023 §0, §2.3–2.4, §3.3–3.4, §4.3 W1 and §7.2.

**Then for 2a:** scout S1 §1–3 (registration, for the `wirescape-test` script), S6 (Studio, for map mode and the
Mappings panel), S8 (parameters), and `docs/specs/ABI2_SPEC.md` D7 (modulation) as needed. 2a skips S2.

**Then for 2b:** the 2a proposal (0024) §0 and its `player.json` hand-off, scout S2 (sidecar and protocol), S6
§panels (tool host), `proposals/0015` (panel host) and `0022`, `docs/specs/ENGINE_PROTOCOL.md` as needed,
and `examples/generative_ws.py`.

**Not needed:** S3, S4 and S5 (0023 covers them), `proposals/0001`–`0004` and `0021`. Open one only for a
specific fact. No whole-tree reads. Use Sonnet subagents for any further inventory, and verify what they quote.

## After each run
The Architect checks factual claims against source, files the tasks and gives the owner a one-page
summary. Run 1 is done and transcribed. 2b starts after 2a's lab PR merges. After 2a, the Architect may file
the `wirescape-test` tasks at once. After 2b (or the single run 2), it transcribes everything and lifts the
freeze.

Revised for run 2 (split, setup done): claude-architect, 2026-11-26.

Signed: claude-architect, 2026-11-26
