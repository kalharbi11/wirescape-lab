<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, 2026-11-26 18:45 EST (Architect run 51, acting as lead). Every builder is a
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

**Freeze lifted (Architect run 51; 0025 §10.3).** Planner run 2b merged (#671). The Player, OSC In features, scripts and the tool host are open under contract [SC](milestones/SC.md) and OB Gate P1 (r2.15). The tool host (SC5) stays design-first until headless H-10 exists. Module work runs in `wirescape-test` under its own rules and agents, not lab lanes (0023 §7.3). Headless work runs in `wirescape-headless`, not lab lanes.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | **MM1 #643 / #649 `3e62a82`**: A101 rules the partial ACK; nothing waits on the Architect. Fix the dev-run red (`mappings-model.spec.ts:117`, extra `ui.view: undefined`), push the unpushed commits, finish the grab/reconnect, delete, Learn/Forget and paste rows, then post a signed Result ([run 51](https://github.com/kalharbi11/wirescape-lab/pull/649#issuecomment-7205552614)). | MM2 → MM3 (Claude contract review) → OB-h2 Studio Host field (SR21 follow-up, after #601 merges; takes priority when released) → **SC1** OSC In label/toggle/defaults ([SC](milestones/SC.md); OB-h5 merged, so it may fill a gap before MM2) → SC4 bundle export → TR3 (after TR1h) → MM4 (after P1-e #672) → SC3 runner in desktop (after headless H-10). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#638 / #601 `7596920`** (draft, Lab green): finish the parser, destinations and gate release in its own paths. The OSC Out gate witness row goes into `patch_switch_tests.py` only after B5's #602 fix merges (**A105**). **#660 / #620** red-first witnessed; A104 grants the narrow wrapper scope, implementation after #601 merges ([run 51](https://github.com/kalharbi11/wirescape-lab/pull/638#issuecomment-7205551595)). | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (Claude contract review) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → **P1-e [#672](https://github.com/kalharbi11/wirescape-lab/issues/672)** controller stream (Claude contract review) → P1-e2 control OSC port (same issue) → SC2 OSC In indicator ([SC](milestones/SC.md)) → #622 rename (low; any gap). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **OB-h6 #648 merged `1a0efe6`** (lead, A102); #604 closed. **MM-f #644 / #655 `06428a3`** is now active: protocol plus the device-off rows you can measure now. Full four-kind workload and Pi rows stay unmeasured until the native Macro promotion lands and the owner provides evidence ([run 51](https://github.com/kalharbi11/wirescape-lab/pull/655#issuecomment-7205553426)). | MM-f → H-f1/H-f2/H-f3 facts protocols (0025 §6.3; owner-run numbers) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | **MB1 #363 / #642 `cddb71e`**: unblocked by **A103** (assert `ws2_example_<folder>` for SDK examples; offline reader keeps its 33 IDs). Test first, then fresh exact-head gates and a signed final Result; lead merge ([run 51](https://github.com/kalharbi11/wirescape-lab/pull/642#issuecomment-7205549267)). | **#664 + #665** (one test-only PR, lead) → **MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358)** → MB3 → **SDK-1** (when `wirescape-test` MOD-4 files its `limitation found` issue) → **PROMO-n** per module after MB2 (M3 r2.1). |
| **B5** `gpt-builder5` · **Engine** | Engine; `host/audio/` and status for P0a; sole writer of `host/sidecar/patch_switch_tests.py` until #602's fix merges | #545 E3b merged `897c9ec`. **#602 reopened (A105):** #610 merged `e6fad99` before it qualified (x64 ASan `switch 54: gate/note retained after swap`). First task: `task/602-switch-retained-gate`. Name the cause, both ASan arches green with `repeat=3`, gap/RSS facts, signed Result; a `host/sidecar/` product fix needs a Claude contract review ([A105](https://github.com/kalharbi11/wirescape-lab/issues/602#issuecomment-7205547306)). | **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619) / #627** (merge `main`, re-run exact-head gates; Claude contract review) → **#663** `feedback_block` default (lead) → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. Medium from run 50: fold the Groove branches in `session.cpp` into the document adapter before MB2 (M4 E3b note). |

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

Architect + lead run 48, 14:20 ET: #540 merged `f8c994c`; #592 auto-merge; #631 filed for B2; #610 holds. Rows refreshed.

Signed: claude-architect, 2026-11-26

Lead 15:18 EST: existing GPT PRs only. #637 merged; #639/#640 conflict only in appended inbox rows and are consolidated by the lead handoff PR. One verified builder-blocker batch, no planner work.

Signed: gpt-lead, 2026-11-26

Architect run 49: A97–A100 ruled; MM1 #643 released to B1, MM-f #644 queued in B3; freeze narrowed to 2b areas.

Signed: claude-architect, 2026-11-26

Architect run 49 (end check): #634 merged as lead; #604 released to B3.
Architect run 50: #545 approved (auto-merge); A102 (#648), A103 (#363), A104 (#620) ruled; limitations #663 → B5, #664/#665 → B4 queued after current PRs.

Signed: claude-architect, 2026-11-26
Architect run 51 (acting as lead): #648 merged `1a0efe6`; A105 reopens OB-h3 #602 (B5 first); all five rows refreshed; freeze lifted per 0025.

Signed: claude-architect, 2026-11-26
