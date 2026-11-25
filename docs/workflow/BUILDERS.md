<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-25 17:52 EST. Every builder is a
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
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger and module-local M7 paths | **#585 `73bda36`**: golden-v0 mock corrected; exact Lab 45716100808. Next: a signed Result, then release the shared RealEngine/App writer when it merges (SR21; Architect note on #540, run 45) | Inspect combined A80/golden diagnostic and exact Lab, correct failures; then ready-event gates, signed Result and Architect inbox review. Release shared paths after merge. **Then OB1.1 Tier 1: OB-h5 OSC presets [#603](https://github.com/kalharbi11/wirescape-lab/issues/603)** (Script `/ws/…` preset plus save/load; A92) after #585 merges. Then the OB-h2 Studio Host field (SR21 follow-up of [#601](https://github.com/kalharbi11/wirescape-lab/issues/601)). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **#540 `d128f43`**: SR21 as written. Ship the own-path parts now; the shared RealEngine/App writes wait for #585 to merge. Ask for the review (A81(3)/A82/A86 witnesses) with pinned SHAs and an inbox row | Finish bounded route/drop/release witnesses on both arches and module-local work; preserve B1 RealEngine/App boundary until #585 merge, then finish transport. Signed Result and Architect review follow exact gates. #540-first A81/A82 order remains. **Then OB1.1 Tier 1:** OB-h2 OSC Out network destinations [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) (A91; Claude contract review) after #540 merges. If OB-h1 [#600](https://github.com/kalharbi11/wirescape-lab/issues/600) finds a `still`-mode failure, A67 [#494](https://github.com/kalharbi11/wirescape-lab/issues/494) goes first; otherwise #494 follows OB-h2. |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **#578**: A87 dispatch done, run [45717349754](https://github.com/kalharbi11/wirescape-lab/actions/runs/45717349754) at `6b3789b` (pre-candidate). Verify the raw rows, then the facts file and Result. **#584 `8795ddc`**: OB A88 (r2.11) gives two owner items, 6a runner and 6b witnessed Studio session; update the owner doc, then the Result. No discovery bridge | Architect: resolve [#594](https://github.com/kalharbi11/wirescape-lab/pull/594) observation boundary; docs merge blocked by automatic approval review. B3 resumes after dispatch artifacts/ruling; do not restart unchanged checks or claim a UI observation from the standalone runner. **Then OB1.1 Tier 1:** OB-h1 OSC soak status [#600](https://github.com/kalharbi11/wirescape-lab/issues/600) once your #579 Result is posted (draft-ahead now), then OB-h6 patch check tool [#604](https://github.com/kalharbi11/wirescape-lab/issues/604). |
| **B4** `gpt-builder4` · **Sound** | Modules, module tests and sound facts outside B1's OB-d ledger; #564 probe scope | **#567 released**: merge main, collect ARM rows. **CMP-1 A89**: open the workflow-only bootstrap PR (`compare-rebuild.yml`, blob-identical), lead merges, dispatch with pins after #567 merges, then #592 carries the facts | Finish #567 exact evidence/Result, then CMP-1 #592 (`6dc6645`). Execution-route question [#593](https://github.com/kalharbi11/wirescape-lab/pull/593) awaits Architect; docs merge blocked by automatic approval review. Sound findings preempt; parked items unchanged. **Then OB1.1 Tier 1: OB-h4 Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329)** after CMP-1 #592 merges (draft-ahead now; bounded exception in `proposals/0022` §6). |
| **B5** `gpt-builder5` · **Engine** | E3a-2 shared engine/document/server; module-local E3b until shared release | **#545 `7f4cc83`**: M4 A90. Pattern-only Apply keeps the native and saved `authored_version`/`track_count`; construction edits go through `applyGraph` with disclosure; witnesses (a)–(c) on both arches. Exact-head evidence is still needed for `7f4cc83` | Continue native/module-local corrections; no production App wiring before #540 transport merges. #540 merges first; preserve B1 shared writer. Signed Result and Architect contract-review after exact gates. **Then OB1.1 Tier 1: OB-h3 patch switching witness [#602](https://github.com/kalharbi11/wirescape-lab/issues/602)** (A93) after #545 merges; test-only draft-ahead allowed. |

**OB1.1 Tier 1 (OB r2.12, owner 2026-11-25):** OB-h1–OB-h6 plus A67 #494 are queued after each lane's current task (see each row and the [OB-h table](milestones/OB.md)). Gate Delay is OB-h4 (#329, branch `task/329-gate-delay`). A67 #494 is unparked. Tier 2 is suggested only (`proposals/0022` §9).
**Parked until after OB1** (PRs closed in the run-44 cleanup, branches kept): MT2 #176; CAT-1 #358 (+MB1). Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. All reviews go to the Architect inbox.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: gpt-lead, 2026-11-25
