<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-26 19:58 EST (all-lane live check). Every builder is a
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
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | **Live lead update:** #649 `d7071a8`: MM1 staged corrections and exact-head Studio/Lab pending. SC1 gap slot #684/#685 `7cb3341` opened after #674 merged; coordinate B2 overlap. Neither ready to merge. | MM2 → MM3 (Claude contract review) → OB-h2 Studio Host field (SR21 follow-up, after #601 merges; takes priority when released) → **SC1** OSC In label/toggle/defaults ([SC](milestones/SC.md); OB-h5 merged, so it may fill a gap before MM2) → SC4 bundle export → TR3 (after TR1h) → MM4 (after P1-e #672) → SC3 runner in desktop (after headless H-10). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **Live lead update:** #638 `0a772b2`: own-path evidence green; shared gate witness still waits actual #677 merge. #660 stays draft-ahead; #672 follows #620. No new Architect question. | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (Claude contract review) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → **P1-e [#672](https://github.com/kalharbi11/wirescape-lab/issues/672)** controller stream (Claude contract review) → P1-e2 control OSC port (same issue) → SC2 OSC In indicator ([SC](milestones/SC.md)) → #622 rename (low; any gap). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **Live lead update:** #655 `4cb2aca`: Lab green, final signed Result and exact Golden/paired not reported; lead requested completion. #678 waits actual #655 merge. Full workload and Pi remain unmeasured. | MM-f → H-f1/H-f2/H-f3 facts protocols (0025 §6.3; owner-run numbers) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | **Live lead update:** MB1 #642 merged `fad44d0` on exact-head gates and final Result. #683 fixture fixes merged (Architect). MB2 #358 waits no open engine/control writer (#638). Test #18 MOD-T2c gates first MB1 pin bump (A106). SDK-1 #682 remains queued. | **MB2+CAT-1 #358** after control-writer release → MB3 → **SDK-1 #682** (MB1/MOD-T2c and lane order; Architect review) → PROMO-n under M3. |
| **B5** `gpt-builder5` · **Engine** | Engine; `host/audio/` and status for P0a; sole writer of `host/sidecar/patch_switch_tests.py` until #602's fix merges | **Live lead update:** #677 `74043db`: causal red and passing 1000-switch raw gap/RSS committed; final-head Lab/ASan and signed Result pending. Sole patch-switch witness writer until actual merge. #627 then integrates fix and qualifies for Architect review. | **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619) / #627** (merge `main`, re-run exact-head gates; Claude contract review) → **#663** `feedback_block` default (lead) → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. Medium from run 50: fold the Groove branches in `session.cpp` into the document adapter before MB2 (M4 E3b note). |

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
