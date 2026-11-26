<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Fable design runs 1 and 2 (owner direction, 2026-11-26)

## Authority
- The owner gives Fable **final decisions** on the questions below for these two runs. The Claude
  Architect writes them into contracts, tasks and lane assignments without reopening them. It flags
  only (a) conflicts with "Fixed" items in `docs/context/CONSTRAINTS.md` (owner only), (b) factual
  errors, with the source line, and (c) contradictions between the two runs.
- Fable rules on design. It does not write or merge lab product code (`engine/`, `host/`, `modules/`,
  `apps/`, `tools/`, `sdk/`). It may write proposals, contracts and docs in the lab (one docs PR per
  run) and docs/rules in `wirescape-test` and `wirescape-headless`.
- The Architect's recommendations in `01_OWNER_WANTS.md` are inputs, not constraints. The owner's
  wants (section B) and principles (section A) are the requirements. Section C items marked "Fable
  decides" are Fable's.
- Freeze: while the runs are open, no new Architect rulings or contracts in the areas below. The
  builder lanes keep their current tasks.

## Run 1 — independent review of the build, then the roadmap
**Why first:** Fable wrote the first plan (0001–0004) and has not seen the build since. Run 2's designs
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

If only one run is possible: run 2, opening with a short version of run 1's questions 2–4.

## Architect-verified highlights from the scout pack
Checked at source by the Architect on 2026-11-26 (lab `11a68c2`):
- **`setOsc` is refused outright** (`host/sidecar/session.cpp:1257`: "Capability not available"), yet
  0022 OB-h2 gates OSC Out network hosts on `setOsc.allowNetwork` or `--confirm-lan`. Resolve the
  permission path.
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
