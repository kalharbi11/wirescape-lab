<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, 2026-11-26 (run 46, wrap-up mode). Every builder is a
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

**Wrap-up mode (owner, 2026-11-26, while the Fable design runs are open).** Finish what is in hand; open nothing new.
- Each lane finishes its **current PR** and then the draft PR it **already has open** (listed in its row). Nothing else.
- **No new task issues, no new branches or PRs, no new draft-aheads.** Queue items with no open PR (OB-h2 #601, OB-h6 #604, A67 #494 and the OB-h2 Studio Host field) **hold until Fable run 1 replans the roadmap**. The standing release (SR20) is suspended for them.
- Corrections, rebases and Results on existing PRs continue as normal. A question goes to the inbox, and you keep working on your other open PR.
- When the lane's open PRs have merged or are waiting on someone else, post one lane-status comment on your last PR and stop.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger and module-local M7 paths | **#585 merged `05cf0d7`** (A80 approved, run 46). **Now: OB-h5 #606** ([#603](https://github.com/kalharbi11/wirescape-lab/issues/603)): rebase on main, add the A96 `OscOutEditor.ts` Save/Load, exact-head Lab, signed Result, leave draft. `merge: lead` | **Wrap-up: stop after #606.** The OB-h2 Studio Host field holds for Fable run 1. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#540 `7196890`**: #585 has merged, so the shared RealEngine/App writes are released (SR21). Rebase, implement **A95** CC Learn (option B, three tests), finish the A81(3)/A82/A86 witnesses on both Linux arches, then pin base/head and one inbox row for the Claude contract review | **Wrap-up: stop after #540.** OB-h2 #601 and A67 #494 hold for Fable run 1 (the OB-h2 permission switch is `--confirm-lan`; see the run-46 clarification on #601). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **#598 merged `4310daf`**, #578 closed; **#584 merged `9fb5943`**, #579 closed. **Now: OB-h1 #608** ([#600](https://github.com/kalharbi11/wirescape-lab/issues/600)): finish the workflow-only change, exact Lab, dispatch the L0→L2 `still` lanes at main, one facts file, the #326/#494 routing, signed Result | **Wrap-up: stop after #608.** OB-h6 #604 holds for Fable run 1. The OB1-candidate OB-f1 re-dispatch is an Architect acceptance step, not lane work. |
| **B4** `gpt-builder4` · **Sound** | Modules, module tests and sound facts outside B1's OB-d ledger; #564 probe scope | **#567 merged `73f411d`**, #564 closed; bootstrap **#597 merged `8a64caa`**. **Now: CMP-1 #592**: the Architect dispatched [run 45791608325](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325) (`660556f` → `73f411d`). Merge main, write the facts from raw artifacts, post the signed Result. `merge: lead`; A89's two-PR exception expires on merge | **Then OB-h4 #609** (Gate Delay #329, already open): §6 exception rows, goldens identical, signed Result. **Wrap-up: stop after #609.** |
| **B5** `gpt-builder5` · **Engine** | E3a-2 shared engine/document/server; module-local E3b until shared release | **#545 `97717e4`**: Studio shards 1–4, desktop and the web smoke are **red** at this head. Rebase on main (#585 merged), fix them, and show the A90 witnesses (a)–(c) on both arches at the exact head. Then pin base/head with one inbox row for the Claude contract review | **Then OB-h3 #610** ([#602](https://github.com/kalharbi11/wirescape-lab/issues/602), already open, test-only): 200/1000-switch test on both arches plus ASan/LSan, gap and RSS facts. **Wrap-up: stop after #610.** |

**OB1.1 Tier 1 (OB r2.12, owner 2026-11-25):** OB-h1, OB-h3, OB-h4 and OB-h5 continue on their open PRs; OB-h2 #601, OB-h6 #604 and A67 #494 hold under wrap-up mode (see each row and the [OB-h table](milestones/OB.md)). Gate Delay is OB-h4 (#329, branch `task/329-gate-delay`). A67 #494 is unparked. Tier 2 is suggested only (`proposals/0022` §9).
**Parked until after OB1** (PRs closed in the run-44 cleanup, issues closed `not planned` in run 46, branches kept; reopen when scheduled): MT2 #175/#176; CAT-1 #358 (+MB1 #363). Note Trigger #322 and M7 batch 2 were unparked in run 29.
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
