<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-27 15:15 EST (live merge-gate check). Every builder is a
**ChatGPT chat session** with the GitHub connector. Its PR is its build and test environment: push to
run Lab CI, comment `/dev-run …` for targeted runs ([DEV_RUN](DEV_RUN.md)). No Codex sandbox is needed.
Codex is the **lead** only.

**Owner-started lanes.** The owner starts or resumes the existing builder chats with
`1:run` through `5:run`. Read the live lane row and linked packets on entry. Standing releases
and draft-ahead permissions apply in an active session. The manager/coordinator trial ended.

**Owner hold — 2026-11-26:** finish only tasks already started; no newer tasks, claims or draft-aheads until the owner/planner changes this instruction. This overrides standing release, SR20 self-release and all `Then` queues below. A merge releases only an already-started dependent PR. Existing lab set: B1 #649/#685; B2 #638/#660; B3 #678 (#655 merged); B4 no product PR (MB2/SDK-1 not started, held); B5 #627 (#677 merged). Test-repo agents likewise finish already-started work only; no new MOD-T2c claim merely because a predecessor merges. **Headless exception (owner, 2026-11-26):** owner manages the headless run and authorizes continuation through bundles E and F; the lab hold does not stop it. Normal dependency/review/CI gates remain, including lab P1-e for H-7 real-engine coverage. **Hardware-test release (owner via Architect run 55, 2026-11-26):** the hold is lifted for exactly two lab chains: B2 #660 → **P1-e #672** → P1-e2, and B5 **P1-f/g #699**. Every other lane item stays held.

**Bundle pool (owner, 2026-11-27):** new lab work is in [TASKS](TASKS.md), as short bundles that any session can claim. Nobody is assigned a bundle in advance. #358, #682 and #663 moved there from the B4 and B5 queues. The lane rows below record history and started work only.

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

| Lane | Owns (paths) | Now | Later queue (HELD for planner) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | MB2 #725 `bf32d05` ready-state (not review-ready); A118 scratch recovered LFO1/8 on both architectures. Draft-head Lab/Web/SDK trial green; ready-state Lab, paired/A114 and Golden running. Verify gates, sign Result, then Architect review. SDK-1 #731 remains draft. | MM2 → MM3 (Claude contract review) → OB-h2 Studio Host field (SR21 follow-up, after #601 merges; takes priority when released) → **SC1** OSC In label/toggle/defaults ([SC](milestones/SC.md); OB-h5 merged, so it may fill a gap before MM2) → SC4 bundle export → TR3 (after TR1h) → MM4 (after P1-e #672) → SC3 runner in desktop (after headless H-10). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | Bundle S. SC1 merged `23f3fe2` (run 59e). SC2 #721 still waits for MB2 #725 (A117, `engine/control/osc_host`). Start from main after MB2 merges. | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (Claude contract review) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → **P1-e [#672](https://github.com/kalharbi11/wirescape-lab/issues/672)** controller stream (Claude contract review) → P1-e2 control OSC port (same issue) → SC2 OSC In indicator ([SC](milestones/SC.md)) → #622 rename (low; any gap). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **Run 59c:** bundle R done (#663 `bbe07ff`, #722 `74f4a3a`). Idle. **Run 59d:** bundles V (#747 → #748, `tools/render/`) and W (#749, `host/audio/` tests) are released in TASKS and may be claimed now. | MM-f → H-f1/H-f2/H-f3 facts protocols (0025 §6.3; owner-run numbers) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | No started product PR. May claim a released bundle in TASKS: V #747 or W #749 are open now (run 59d); B #742 waits for M. MB2/SDK-1 are already claimed; no takeover or fixed assignment. | **MB2+CAT-1 #358** after control-writer release → MB3 → **SDK-1 #682** (MB1/MOD-T2c and lane order; Architect review) → PROMO-n under M3. |
| **B5** `gpt-builder5` · **Engine** | Engine; `host/audio/` and status for P0a; sole writer of `host/sidecar/patch_switch_tests.py` until #602's fix merges | **Run 59e:** SC1 #685 merged `23f3fe2` (approved). Idle: may claim N #622, V #747 or W #749 in TASKS. | **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619) / #627** (merge `main`, re-run exact-head gates; Claude contract review) → **#663** `feedback_block` default (lead) → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. Medium from run 50: fold the Groove branches in `session.cpp` into the document adapter before MB2 (M4 E3b note). |

**OB1.1 Tier 1 and Gate P0 (OB r2.12, r2.13):** OB-h1–h4, h6 and #494 continue in their lanes; OB-h5 merged (#606). Gate P0 is P0a #619, P0b #620, OB-h2 gate release and OB-h1. OB1 acceptance stands but gates no new work (0023).
**Parked (0023 §7.1):** M5 PV2+, M6 MT2+ (#175/#176), M8–M12, V1; T1.5 cut. **Unparked:** stage MB (#363, #358).
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**New bundles:** [TASKS](TASKS.md) is authoritative for unassigned T (#740 → #741), B (#742), and N (#622). Any session may claim when its release/writer gates hold. Historical Later queues below do not assign or release these packets.

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
