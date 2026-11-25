<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-25 (after run 39; B4 length ruling queued). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E3a-2 #522 / #538** `345ec7a`: A78 schema/spec and generated outputs refreshed, control-only blocked-ID/retirement prerequisite implemented; engine diagnostic and PV1/Lab pending. Complete runtime A78, A77 validator seam, deterministic witnesses, B2 re-review and exact gates/Result before Claude review. | **Pull-ahead (SR21c):** canonical E3b #545 expected-red verified; duplicate #546 closed unmerged; shared integration after #538. Not tag-holding. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E3c #537 / #540** `89655af`: wildcard route reclamation fix targeted green on both Linux (45569236322); ASan and Lab pending. All module-local slots/validators implemented; preserve A77 F32 Golden guard. Re-review #538 runtime and seam; shared integration after #538 merge, routes commit only on acceptance. #497 parked. | E3c shared migration and route integration after #538; signed exact evidence. OB1.1. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts (except `facts/sound/ob_d_patches.md`, now B1), module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **#520 / #539 exclusively** `4b3bf18`: Lab 45568673290 and targeted green on both Linux. **A79 ruled:** add the granted `ws::Reader::size()` line, then reject trailing/short/unknown-length v2 payloads atomically with the A79 regressions. Then exact ASan, mark ready, Lab/Golden/strict paired, Result and pin. | OB1 sound follow-ups after #520 merges. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`, **`facts/sound/ob_d_patches.md` (run 38b, from B4)**; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **OB-d #492** `79abef6`: Lab green, 15-case rebuild/listening packet prepared. Blocked only on #539 integrated candidate. After merge, verify Golden and collect exact OB-a1 case hashes, owner-only listening handoff and Result. No redundant S7.6 capture. | Studio/OB-c verification. CN remains B3 #523. |
| **B3** `gpt-builder3` · **Floater / facts** | Assigned paths only; CN facts and previously authorized immutable workflow pins; no harness edits. | **#523/#525** `5253b3c`: intermediate A62 and native independent audits complete, Lab green; larger/Delay non-pass preserved. Wait for actual #539 merge, then final A76 pin/exact Lab assertions, replacement-path check, A62/native as applicable and A69a cost. | Signed exact evidence, lead merge; then KNOWN_ISSUES A2 from measured rows and M4 acceptance. |

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

Signed: claude-architect, 2026-11-25
