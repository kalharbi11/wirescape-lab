<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Import manifest

`lab/import_from_main.py` copies every tracked file of `kalharbi11/wirescape` at one SHA, except:
- agent process and planning: root `AGENTS.md`/`CLAUDE.md`/`CONTRIBUTING.md`, `.claude/`, `docs/PLAN.md`,
  `docs/PLANNER_HANDOFF.md`, `docs/WORKFLOW.md`, `docs/STATUS.md`, `docs/DEMO_CLASS.md`, `docs/PI_RUNNER.md`,
  `docs/WINDOWS_DEMO_UPDATE.md`, `docs/tasks/`, `docs/planner/`, `docs/reviews/`, design briefs and studies
  in `docs/design/` (module port studies in `docs/design/ports/` are kept), Studio's agent files, old plans,
  handoffs, reviews, `archive/` and `reference/`;
- process tools: board, merge gate, review pack, CI log reader, runner health, docs freshness, guard, and their tests;
- `.github/` except workflows; product workflows are parked in `ci/from-main/` (inactive), process workflows dropped.

The product README moved to `docs/PRODUCT_README.md`. Re-running the import is allowed only while the lab
has not changed the product tree (the script checks).
