<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Planner brief (2026-11-26)

The owner asked for two bounded Planner runs to review the build and decide the next
architecture: a headless Player, a fast module-development repo, macros and mapping, OSC and
Python scripting, and the roadmap. The Planner's rulings in these runs are final (authority in
[02_PLANNER_RUNS.md](02_PLANNER_RUNS.md)).

## How to start (owner)
Open a Claude Code session on Opus with `kalharbi11/wirescape-lab`, `kalharbi11/wirescape-test` and
`kalharbi11/wirescape-headless` attached, and send exactly one of:
- ~~`planner: run 1`~~ — **done** (#618, `proposals/0023`; transcribed by Architect run 47);
- ~~`planner: run 2a`~~ — **done** ([`proposals/0024`](../../../proposals/0024-test-repo-macros-modules.md);
  `wirescape-test` rules PR open for review);
- ~~2b part 1~~ — **done** (lab and `wirescape-test` items of `03_PLANNER_REVIEW.md`:
  [0024 §9](../../../proposals/0024-test-repo-macros-modules.md));
- ~~`planner: run 2b`~~ — **done** ([`proposals/0025`](../../../proposals/0025-player-osc-scripts-tools.md):
  the headless Player, Gate P1 (e) shapes, OSC and scripts, order, guide list, tool-host boundaries;
  `wirescape-headless` rules PR open for review);
- `planner: run 2` — fallback: all of run 2 in one session (max effort).

Run 2 does not redo setup: read "Run 2 prep" in [02_PLANNER_RUNS.md](02_PLANNER_RUNS.md) first.

Anything after the trigger is an extra ask. The trigger is defined in `CLAUDE.md`.

## What the Planner does in a run
1. Read this folder in the order given in [02_PLANNER_RUNS.md](02_PLANNER_RUNS.md) ("Reading order").
2. Decide the questions for that run and write the outputs it lists.
3. Open **one docs PR** in the lab (any branch the session allows), enable auto-merge, and, for run 2,
   one PR against `main` in each new repo the session covers (2a: `wirescape-test`; 2b: `wirescape-headless`)
   with its replacement `README.md`/`AGENTS.md`. No product code, no issues, no lane edits.
4. End with a chat summary: decisions, what each repo does next, what would overturn the major
   rulings. Last line: `Signed: claude-planner, <YYYY-MM-DD> <HH:MM> ET`.
5. When the run is over, it is over: no watchers or wake-ups.

## Files
| File | What |
|---|---|
| [01_OWNER_WANTS.md](01_OWNER_WANTS.md) | the owner's principles and wants, with the Architect's recommendations and the owner's answers |
| [02_PLANNER_RUNS.md](02_PLANNER_RUNS.md) | authority, the questions for each run, outputs, verified highlights, reading order |
| [03_PLANNER_REVIEW.md](03_PLANNER_REVIEW.md) | Planner self-review (2026-11-26): 0024 amendments 2b may make, prep corrections, 2b scope and open decisions, Architect actions |
| `scout/S1_modules.md` | module inventory, registration, modulatable parameters, SDK paths |
| `scout/S2_protocol_sidecar.md` | engine process, commands, status, switching, supervision, gaps |
| `scout/S3_milestones.md` | proposals, milestones, OB1 acceptance, lanes, plan size |
| `scout/S4_facts_index.md` | every facts file; Pi, soak, UI and CPU facts; what is missing |
| `scout/S5_workflow_cost.md` | commit split, process docs, workflows, rulings |
| `scout/S6_studio_map.md` | Studio and desktop code map, mapping today, panels, patch format |
| `scout/S7_docs_patches_tools.md` | user docs and staleness, device wording, patches, tools |
| `scout/S8_module_params.md` | per-parameter table for the run-2 module batch (Architect run 47, at `337d8e8`) |
| `examples/generative_ws.py` | example Python generative script (OSC triggers, notes, CV) |

The scout files are Sonnet reports, facts only, at lab `11a68c2`. The Architect verified the
highlights listed in 02; verify anything else you rely on.

Signed: claude-architect, 2026-11-26
