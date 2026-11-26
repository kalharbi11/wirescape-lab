<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Fable design brief (2026-11-26)

The owner asked for two bounded Fable design runs to review the build and decide the next
architecture: a headless Player, a fast module-development repo, macros and mapping, OSC and
Python scripting, and the roadmap. Fable's rulings in these runs are final (authority in
[02_FABLE_RUNS.md](02_FABLE_RUNS.md)).

## How to start (owner)
Open a Claude session on Fable with `kalharbi11/wirescape-lab`, `kalharbi11/wirescape-test` and
`kalharbi11/wirescape-headless` attached, and send exactly one of:
- `fable: design run 1` — the review and roadmap (run it first);
- `fable: design run 2` — the architecture and contracts (after run 1's proposal merges).

Anything after the trigger is an extra ask. The trigger is defined in `CLAUDE.md`.

## What Fable does in a run
1. Read this folder in the order given in [02_FABLE_RUNS.md](02_FABLE_RUNS.md) ("Reading order").
2. Decide the questions for that run and write the outputs it lists.
3. Open **one docs PR** in the lab (branch `fable/design-run-<n>`), enable auto-merge, and, for run 2,
   one PR in each new repo with its replacement `README.md`/`AGENTS.md`. No product code.
4. End with a chat summary: decisions, what each repo does next, what would overturn the major
   rulings. Last line: `Signed: fable, <YYYY-MM-DD> <HH:MM> ET`.
5. When the run is over, it is over: no watchers or wake-ups.

## Files
| File | What |
|---|---|
| [01_OWNER_WANTS.md](01_OWNER_WANTS.md) | the owner's principles and wants, with the Architect's recommendations and the owner's answers |
| [02_FABLE_RUNS.md](02_FABLE_RUNS.md) | authority, the questions for each run, outputs, verified highlights, reading order |
| `scout/S1_modules.md` | module inventory, registration, modulatable parameters, SDK paths |
| `scout/S2_protocol_sidecar.md` | engine process, commands, status, switching, supervision, gaps |
| `scout/S3_milestones.md` | proposals, milestones, OB1 acceptance, lanes, plan size |
| `scout/S4_facts_index.md` | every facts file; Pi, soak, UI and CPU facts; what is missing |
| `scout/S5_workflow_cost.md` | commit split, process docs, workflows, rulings |
| `scout/S6_studio_map.md` | Studio and desktop code map, mapping today, panels, patch format |
| `scout/S7_docs_patches_tools.md` | user docs and staleness, device wording, patches, tools |
| `examples/generative_ws.py` | example Python generative script (OSC triggers, notes, CV) |

The scout files are Sonnet reports, facts only, at lab `11a68c2`. The Architect verified the
highlights listed in 02; verify anything else you rely on.

Signed: claude-architect, 2026-11-26
