<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect (run 44, also acting as lead), 2026-11-25 05:20 EST. Every builder is a
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

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger and module-local M7 paths | **OB-d owner-listening support**: record the owner's disposition and drop "(draft)" in the same ledger edit. **A80 Studio [#555](https://github.com/kalharbi11/wirescape-lab/issues/555) is in progress** as draft [#585](https://github.com/kalharbi11/wirescape-lab/pull/585) (`f240fee`, test-first). | Finish #585, then the signed Result and the Claude contract review. Coordinate the Studio transport/App wiring with B2 (#540 owns shared live `setData` transport) and B5. OB1 acceptance takes priority. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **E3c [#540](https://github.com/kalharbi11/wirescape-lab/pull/540)** (`0bb23c2`). **A86 answered your question** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7159038650)): keep the `osc.out` fresh-bus exception on whole-document `applyGraph` (document it); accepted-only is sufficient with the three witnesses (one row table per message, ≤ 1 suppressed block with counted drops, old-route release of a high gate). | Also the A81(3)/A82 OSC In witness on both Linux arches, A84 L1, and F32 Golden. Then the signed Result, an inbox row and the Claude contract review. #497 is closed while A67 is parked (branch kept). |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **OB-f1 recheck [#578](https://github.com/kalharbi11/wirescape-lab/issues/578), unblocked by A87** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/578#issuecomment-7159042191)). Once the Architect docs PR merges, dispatch `ob-f1-ui-facts.yml` with `ref=<main SHA>`, commit one facts file reporting the r2.3 targets as met or not met, then a signed Result (lead merge). | **Then the Pi 100-edit runner [#579](https://github.com/kalharbi11/wirescape-lab/issues/579)** (draft [#584](https://github.com/kalharbi11/wirescape-lab/pull/584), tests first). Its owner command goes into INSTALL → Testing and reporting, step 3. |
| **B4** `gpt-builder4` · **Sound** | Modules, module tests and sound facts outside B1's OB-d ledger; #564 probe scope | **S2a [#576](https://github.com/kalharbi11/wirescape-lab/issues/576)** as [#580](https://github.com/kalharbi11/wirescape-lab/pull/580) (`fe859c8`, six lines under A85/A85a): exact Lab green with Golden identical, then the Result and a lead merge. Then merge main into #567, rerun portability, commit the ARM rows, and post the Result. | **Then CMP-1 [#589](https://github.com/kalharbi11/wirescape-lab/issues/589)**: the measured rebuild vs previous-engine report (facts plus one advisory workflow; draft-ahead allowed). An OB1 sound finding preempts it. Gate Delay (#333 closed, branch kept) and CAT-1 stay parked. |
| **B5** `gpt-builder5` · **Engine** | E3a-2 shared engine/document/server; module-local E3b until shared release | **E3b [#545](https://github.com/kalharbi11/wirescape-lab/pull/545)** (`0185016`): Groove on the shared loader, legacy config → data read, Groove-only Studio projection. Sequence: #540 merges first, then integrate B2's hunks unchanged. | Signed Result and the Claude contract review. A81 binds the first shipped slot (B2 or B5, whichever merges first). Wire App only after the B2 transport contract (correlated acceptance/refusal) is merged. |

**Parked until after OB1** (PRs closed in the run-44 cleanup, branches kept): Gate Delay #333, MT2 #176, A67 #497; CAT-1 #358 (+MB1). Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. All reviews go to the Architect inbox.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: claude-architect, 2026-11-25
