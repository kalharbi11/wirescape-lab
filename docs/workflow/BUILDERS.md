<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, run 47, 2026-11-26 13:45 EST (Planner run 1 transcribed; lane queues per [0023 §7.3](../../proposals/0023-review-and-replan.md)). Every builder is a
**ChatGPT chat session** with the GitHub connector. Its PR is its build and test environment: push to
run Lab CI, comment `/dev-run …` for targeted runs ([DEV_RUN](DEV_RUN.md)). No Codex sandbox is needed.
Codex is the **lead** only.

**Owner-started lanes.** The owner starts or resumes the existing builder chats with
`1:run` through `5:run`. Read the live lane row and linked packets on entry. Standing releases
and draft-ahead permissions apply in an active session. The manager/coordinator trial ended.

**How a lane works**
- **Long-running sessions.** A lane is a queue, not a single task. Keep working through it: implement,
  push, read CI, correct, post the Result, then start or draft the next task. Do not end the session
  while your lane has work ([continuation rules](README.md#builder-continuation-after-ci)).
- **Standing release.** A task is released when its predecessor in the same lane merges on `main`.
  Start it without asking, on its own `task/<issue#>-<slug>` branch and PR.
- **Draft-ahead.** While a PR waits on review or merge, you may open the next task in your lane as a
  draft PR. It rebases after its predecessor merges, and only merges after that.
- **Writers.** Stay inside your lane's paths. Shared files (catalogues, `CMakeLists.txt`, workflows)
  follow the merge order named in the row. A file in another lane needs that lane's PR merged first.
- **Auto-merge (owner, 2026-11-24).** For a task whose contract says `merge: lead` and has no review
  condition, the lead turns on auto-merge at release. It merges itself when the Result is posted and
  exact-head required checks are green. A reviewed task waits for its reviewer, then the lead or the Architect merges it.
- **Fewer stops ([SR20](STANDING.md)).** Start the next queue task yourself when its predecessor merges (open the issue if missing). Low findings never block. `merge: lead` tasks merge on exact-head green plus your Result. Ask for a Claude review once, at the merge-ready head.
- **Split, don't wait ([SR21](STANDING.md)).** If your task needs a file another lane is still writing in an open PR, ship the part inside your own paths now. The cross-lane part becomes a follow-up task, released when that PR merges.
- **Keep the Architect inbox current.** When a task is ready for required review, needs a ruling,
  or raises an Architect question, add or update one row in the
  [Architect inbox](ARCHITECT_INBOX.md) through a docs PR. Link the signed Result or question,
  include exact head and base when applicable, and name the task waiting. Use `needs/architect`
  for Architect work. The owner and delivery lead own the `architect-ready` and `review-ready`
  trigger labels. Keep working on independent lane items while the request waits.

**Wrap-up mode ended for Planner run 1's areas (Architect run 47, 2026-11-26; 0023 §8.9).** Standing release (SR20) and
draft-ahead are back for every queue item below. **Still frozen until Planner run 2 merges:** macros, mapping, OSC In
features, scripts, the tool page host and the design of `wirescape-test` and `wirescape-headless`. No lane starts work in
those areas. The two new repos get their own agents under their own rules, not lab lanes (0023 §7.3).

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | **Studio restart policy [#621](https://github.com/kalharbi11/wirescape-lab/issues/621)** on #624 (RS, OB r2.13; `merge: lead`). `App.ts` guard granted, added after #540 merges. | OB-h2 Studio Host field (SR21 follow-up, after #601 merges) → TR3 (after TR1h) → macro/mapping UI (after Planner run 2). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#540 `65a3eb8`** all exact-head gates green (paired 100/102 both arches = base, after the Architect's probe fix). Post signed Result + A81/A82/A86/A95 packet; Architect review next. Shared writer (`App.ts`, `module_catalog.h`) stays B2 until merge. | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (OB r2.13 (3), adds the OB-h3 OSC Out gate row test-first; `--confirm-lan`) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → #622 rename (low) → controller stream (Stage 2, after run 2). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **OB-h1 [#600](https://github.com/kalharbi11/wirescape-lab/issues/600):** Architect dispatched [45877224981](https://github.com/kalharbi11/wirescape-lab/actions/runs/45877224981) (`ref=48479fc…`). Audit four-lane raw artifacts, publish facts, route #326/#494 (Gate P0 d, arm64 rows). | CN final facts #523 (M4) → OB-h6 [#604](https://github.com/kalharbi11/wirescape-lab/issues/604) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | **#592 `4026404`** raw JSON retained and verified; exact-head Lab, then signed Result and lead merge. Then **#609** (waits only on #540 for `module_catalog.h`). | OB-h4 #609 (Gate Delay, last module under the freeze; integrate main after #540, then final gates) → **MB1 [#363](https://github.com/kalharbi11/wirescape-lab/issues/363)** → **MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358)** → MB3 → promotions. If #592 stays blocked, start MB1 now (0023 R3.1). |
| **B5** `gpt-builder5` · **Engine** | Engine; E3b module-local until shared release; `host/audio/` and status for P0a | **#545 `11762c5`** E3b; shared writes wait for #540 merge. **#610** ready at `b7eda29`, auto-merge on. **P0a #627** red-first. | OB-h3 #610 (+ OSC In route-relisten row, OB r2.13 (4)) → **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619)** → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. |

**OB1.1 Tier 1 and Gate P0 (OB r2.12, r2.13):** OB-h1–h4, h6 and #494 continue in their lanes; OB-h5 merged (#606). Gate P0 is P0a #619, P0b #620, OB-h2 gate release and OB-h1. OB1 acceptance stands but gates no new work (0023).
**Parked (0023 §7.1):** M5 PV2+, M6 MT2+ (#175/#176), M8–M12, V1; T1.5 cut. **Unparked:** stage MB (#363, #358).
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. All reviews go to the Architect inbox.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: claude-architect, 2026-11-26

Architect + lead check 14:25 ET: rows refreshed (B1 #624, B2 #540 green, B4 #592 retained, B5 #610 auto-merge). Rulings B1-RS-modal and B3-OBh6-timing in the inbox.

Signed: claude-architect, 2026-11-26
