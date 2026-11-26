<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Planner runs 1 and 2 (owner direction, 2026-11-26)

## The role
**`claude-planner`** is a planning seat run on Opus, separate from the Claude Architect so that its
review of the build and the Architect's verification stay independent. It replaces the retired Fable
seat for these two runs only. Suggested effort: **max** for both runs (they set months of work and
are read-heavy); xhigh is acceptable for run 1 if usage runs short.

## Before deciding anything
Read the whole plan first: `01_OWNER_WANTS.md` (all of sections A–D), this file, and all seven scout
reports. Only then start the run's questions.

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

Output: `proposals/0024-player-and-test-repos.md` (1, 2, 5, 7), `proposals/0025-macros-mapping-osc-scripts.md`
(3, 4, 6), replacement `AGENTS.md`/`README.md` for the two new repos, and a task list per repo ready
to file as issues (title, paths, acceptance, tier, dependencies).

Suggested order inside run 2: 1 and 8 for `wirescape-test` first (it unblocks module work), then 3 and 6
(macros, mapping, modules), then 2 and 5 (Player, tool host), then 4 and 7. If the session is
cut short, commit what is decided so far; the next `planner: run 2` continues from the open items.

If only one run is possible: run 2, opening with a short version of run 1's questions 2–4.

## Run 2 prep (Architect run 47, 2026-11-26)
Run 1 merged as #618 (`337d8e8`). [`proposals/0023`](../../../proposals/0023-review-and-replan.md) binds run 2. Build on it and do
not re-derive it. The Architect checked 0023's citations at source and found one wrong line: R2.5 cites
`RealEngine.ts:300-304`, but the reload is at `:393-436`. The ruling holds.

**Already done; do not redo:**
- Transcribed: M3 r2 (stage MB, TR1h without PV2, T1.5 cut, V1 parked), M7 r1.7, OB r2.13 (Gate P0 rows,
  OB-h2 gate release, freeze ends at MB2) and STANDING SR22–SR25 (W3, W4, W5, R1.5).
- CI-S1–S3 applied, and the rulings index [`RULINGS.md`](../../workflow/RULINGS.md) built.
- Closed questions moved to `QUESTIONS_HISTORY.md`; banners added on closed and parked contracts.
- Lab issues: MB1 #363 and MB2+CAT-1 #358 reopened; P0a #619, P0b #620, Studio restart #621 and the fake
  MIDI endpoint rename #622 filed.
- B.4 erratum fixed in `01_OWNER_WANTS.md`.
- Stale paths fixed in `SDK_AUTHOR_GUIDE.md` and `ARCHITECTURE.md`, and the Clock README corrected.
- Lab lanes refreshed. Wrap-up has ended for run 1's areas, and run 2's areas stay frozen.

**Reading for run 2 (trimmed):**
- this folder's README;
- `01_OWNER_WANTS.md` (A, B, C);
- the run 2 section above;
- 0023 §0, §2.3–2.4, §3.3–3.4, §4.3 W1 and §7.2;
- scout S2 (sidecar, for the Player), S6 (Studio, for macros, mapping and the tool host), S1 §1–3 (registration,
  for the `wirescape-test` script) and the new **S8** (per-parameter table for question 6).

S3, S4 and S5 are covered by 0023; open them only for a specific fact.

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
- Each also has a leftover branch `claude/wirescape-modes-architecture-tnszf8`, identical to `main`. The owner
  may delete it.
- Neither repo has workflows yet. Both `LAB_PIN` files pin lab `11a68c2` (on lab `main`); run 2 decides the
  bump rule.
- `wirescape-test/modules/README.md` repeats the B.4 error. Its Envelope row also says Function Envelope has
  no modulatable parameters, which is wrong. Run 2 replaces that README.
- Open run 2's repo PRs against `main`. Use whatever branch the session allows. `planner/run-2` is
  preferred, not required.

**Output the Architect needs to file tasks fast:**
- The per-repo task list as a table (title, paths, acceptance, tier, dependencies, lane or agent).
- For the lab, name the contract each row goes into: OB, M3, a new contract, or Gate P1.

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
1. `README.md` (this folder), `01_OWNER_WANTS.md`, this file.
2. The scout pack `scout/S1`–`S7`. Read source only to confirm or overturn a finding you rely on.
3. As needed: `proposals/0001`–`0004`, `0015`, `0021`, `0022`, `docs/workflow/ROADMAP.md`, `OB_PLAN.md`,
   `docs/context/CONSTRAINTS.md`, `host/sidecar/DESIGN.md`, `docs/specs/ENGINE_PROTOCOL.md`,
   `docs/specs/ABI2_SPEC.md` (D7 modulation).
No whole-tree reads. Use Sonnet subagents for any further inventory, and verify what they quote.

## After each run
The Architect checks factual claims against source, files the tasks and gives the owner a one-page
summary. Run 2 starts only after run 1's proposal is merged.

Signed: claude-architect, 2026-11-26
