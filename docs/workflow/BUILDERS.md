<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-26 17:10 EST (after Architect run 49). Every builder is a
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

**Freeze (Architect run 49, 2026-11-26; 0024 §8.4).** Planner run 2a decided macros, mapping, the module batch and the design of `wirescape-test`: those areas are open (MM contract for Studio, M3 r2.1 for SDK-1 and promotions). **Still frozen until Planner run 2b merges:** OSC In features, scripts, the tool page host, the Player and the design of `wirescape-headless`. Module work runs in `wirescape-test` under its own rules and agents, not lab lanes (0023 §7.3).

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | **MM1 #643 / #649 `ca3858c`**: runtime red witnessed by dev-run 45901516303 (missing mapping model/Macro/API). Continue tests then implementation; partial-ACK policy waits on merged inbox #651. Coordinate shared App/RealEngine with B5; second merger rebases. | MM2 → MM3 (Claude contract review) → OB-h2 Studio Host field (SR21 follow-up, after #601 merges; takes priority when released) → TR3 (after TR1h) → MM4 (after P1-e #672) → **SC1** OSC In label/toggle/defaults (after OB-h5 #603; may go before MM2 if MM waits) → SC4 bundle export → SC3 runner in desktop (after headless H-10). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#635 merged `a329476`**, #631 historical red/current green verified under A98. Continue **#638 / #601 `49f6a93`** parser and destination work under A99; retired-gate red recorded in 45893480055. Switching-witness edits wait for #610 merge; split independent paths under SR21. | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (OB r2.13 (3), adds the OB-h3 OSC Out gate row test-first; `--confirm-lan`) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → #622 rename (low) → **P1-e [#672](https://github.com/kalharbi11/wirescape-lab/issues/672)** controller stream (after #620; Claude contract review) → P1-e2 control OSC port (same issue) → SC2 OSC In indicator ([SC](milestones/SC.md)). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **OB-h6 #604 / #648 `e2c2800`**: draft Lab and targeted integration green; ready Lab Windows/Golden/paired still pending at check, final signed Result required. **#655 / #644 `7929f0c`** draft-ahead only: full workload waits for real Macro promotion, Pi rows unmeasured. | **MM-f [#644](https://github.com/kalharbi11/wirescape-lab/issues/644)** (64 vs 128 nodes) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | **MB1 #363 / #642 `cddb71e`**: exact Lab 15/15 green; ready-event Golden/paired and final Result pending. Merged inbox #650 carries SDK prefix/offline-reader questions; no final merge before disposition. MB2 waits actual MB1 merge. | **MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358)** → MB3 → **SDK-1** (when `wirescape-test` MOD-4 files its `limitation found` issue) → **PROMO-n** per module after MB2 (M3 r2.1). |
| **B5** `gpt-builder5` · **Engine** | Engine; E3b module-local until shared release; `host/audio/` and status for P0a | **#545 `638d8b6`**: A100 implementation/fixture correction, fresh CI pending; **#627 `949c1ee`** Windows fake-pacing correction and fresh CI/ASan pending. **#610 `b7eda29` now released from #631**: integrate main, run own exact-head gates/heavy tier; switching-witness writer releases to B2 only on merge. | OB-h3 #610 (+ OSC In route-relisten row, OB r2.13 (4)) → **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619)** → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. |

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

Signed: claude-architect, 2026-11-26
