<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-25 04:05 EST. Every builder is a
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
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger and module-local M7 paths | **OB-d [#492](https://github.com/kalharbi11/wirescape-lab/pull/492) merged `3aa0c33`.** [Owner listening handoff](https://github.com/kalharbi11/wirescape-lab/pull/492#issuecomment-7157341656) is ready. Record the owner disposition and remove “(draft)” in the same ledger update. | **A80 Studio [#555](https://github.com/kalharbi11/wirescape-lab/issues/555)** after #538 merges. Coordinate Studio writer scope with B2/B5; OB1 acceptance takes priority. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, OSC/CC module-local paths and `engine/control/` handlers | **E3c [#537/#540](https://github.com/kalharbi11/wirescape-lab/pull/540)** `89655af`, blocked on #538 merge. Both-Linux targeted release/ASan passed; pre-backend full Lab remains red. B2 source review complete; A82 cleared. | After #538, integrate A77 migration and accepted-only routes. The first shipped-slot PR must prove retained setData preserves deferral and changed-data D5 replacement installs new instance/data and emits one correlated superseded on both Linux arches. A82 permits OSC In on #540; coordinate with #545. #497 stays parked. |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **[#523/#525](https://github.com/kalharbi11/wirescape-lab/pull/525)** `63d90c1`, subject `8c9bb10`. A83 facts recorded. Exact A62/native/cost runs passed; finish latest A62 audit, exact Lab and signed Result. Keep the initial larger-buffer non-pass and A83 limits explicit. | Lead merge on verified evidence. **A2 [#569/#570](https://github.com/kalharbi11/wirescape-lab/pull/570)** is draft-ahead; reconcile to merged #525 and post exact-head evidence. Then M4 acceptance handoff. |
| **B4** `gpt-builder4` · **Sound** | Modules, module tests and sound facts outside B1's OB-d ledger; #564 probe scope | **M10 S2 [#564/#567](https://github.com/kalharbi11/wirescape-lab/pull/567)** draft `04cd9fe`. Exact Lab is running. After green, ready the PR for advisory portability evidence, audit the parser and measurements, then commit measured symbols and memory facts, including Delay at 96 kHz. | Exact final Lab and applicable portability, then signed Result and lead merge. An OB1 sound finding takes priority if one is reported. Gate Delay and CAT-1 stay parked. |
| **B5** `gpt-builder5` · **Engine** | E3a-2 shared engine/document/server; module-local E3b until shared release | **E3a-2 [#522/#538](https://github.com/kalharbi11/wirescape-lab/pull/538)** `bd4b69c`. Required Lab/Golden/strict paired passed; [signed Result](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7157636089) and [#568 inbox pin](https://github.com/kalharbi11/wirescape-lab/pull/568) are live. Architect contract review pending, including A51/A78 OSC timeout atomicity. | **[#545](https://github.com/kalharbi11/wirescape-lab/pull/545)** `e64a0eb`: direct Linux ASan/UBSan and foundation passed; full Lab/Web remain red pending #538's shared façade. Coordinate with #540/#555 after merge; A81 binds the first shipped slot. |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. All reviews go to the Architect inbox.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: codex-lead, 2026-11-25, 04:05 EST
