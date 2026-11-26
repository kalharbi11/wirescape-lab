<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, 2026-11-26 run 49 (after gpt-lead 15:18 EST). Every builder is a
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
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger, module-local M7 paths, `apps/desktop/` for RS | **MM1 [#643](https://github.com/kalharbi11/wirescape-lab/issues/643)** (MM r1, run 49): released now. #624 RS merged `45f71a7`. Test-first; `FakeEngine` declares `essentials.macro` per 0024 §3.1. | MM2 → MM3 (Claude contract review) → OB-h2 Studio Host field (SR21 follow-up, after #601 merges; takes priority when released) → TR3 (after TR1h) → MM4 (after Gate P1 (e)). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#635 `2c9d09a` / #631**: **A98** ruled — run the forced-poll witness on a diagnostic-only branch at `48479fc`; red there plus green here closes #631 as fixed by E3c, otherwise #631 stays open. **#638 `efd4cfa` / #601**: red-first recorded (run 45889339426); **A99** grants the OSC Out parser and staging paths. #631 keeps priority. | **OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) with gate release** (OB r2.13 (3), adds the OB-h3 OSC Out gate row test-first; `--confirm-lan`) → #494 if OB-h1 routes it → **P0b [#620](https://github.com/kalharbi11/wirescape-lab/issues/620)** → #622 rename (low) → controller stream (Stage 2, after run 2). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **#634 `edc6d7e` / #600**: four-lane audit complete, exact facts-only Lab 45889205607 green; signed final Result/ready handoff next. 8 reports pass, 2 heavy fail on extra rise; zero observed exposed drops, no heavy reliability claim. #631 owns extra-rise symptom; #326 stays open. Lead may merge after ready Result/gates; then #604. | CN final facts #523 (M4) → OB-h6 [#604](https://github.com/kalharbi11/wirescape-lab/issues/604) → **MM-f [#644](https://github.com/kalharbi11/wirescape-lab/issues/644)** (64 vs 128 nodes) → Player soak harness facts (Stage 3). |
| **B4** `gpt-builder4` · **Sound + module build** | Modules, module tests, sound facts outside B1's ledger; MB build paths per M3 r2 | **MB1 [#363](https://github.com/kalharbi11/wirescape-lab/issues/363)**: **A97** ruled the L1 field classes (M3 r2.1 note); start test-first now. #609 merged `0330809`. | **MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358)** → MB3 → **SDK-1** (when `wirescape-test` MOD-4 files its `limitation found` issue) → **PROMO-n** per module after MB2 (M3 r2.1). |
| **B5** `gpt-builder5` · **Engine** | Engine; E3b module-local until shared release; `host/audio/` and status for P0a | **#545 `987cff8`**: **A100** ruled — catalogue `data_slots` from descriptors, not `groove.livePattern`; old engine keeps stopped Apply. Shared `App.ts` released (#624 merged). **#610 `b7eda29`** held on #631 (A98). **#627 `440254c`** P0a evidence pending. | OB-h3 #610 (+ OSC In route-relisten row, OB r2.13 (4)) → **P0a [#619](https://github.com/kalharbi11/wirescape-lab/issues/619)** → TR1h (M3 r2, Stage 2) → P1 (g) SIGTERM, (h) coverage. |

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
