<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-25 (A81 ruled; #539 review pinned; #558 merged). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E3a-2 #522 / #538** `bd4b69c`: A81 synthetic-slot witness both Linux green 45575003721; exact PV1/Web green, Lab/E4b pending. Obtain B2 final source re-review, ready-head Lab/Golden/strict paired and applicable gates, signed Result explicitly naming A81 carry then Architect review. No catalogue injection or Studio runtime changes. | **Pull-ahead (SR21c):** canonical E3b #545 `1917db8` direct release/ASan both Linux green, full loader tests blocked; shared integration after #538. Coordinate A81 witness before any first shipped-slot merge. Not tag-holding. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E3c #537 / #540** `89655af`: both Linux targeted/ASan green; full Lab red from pre-#538 descriptor guard/unseeded fixtures. Re-review #538 at `bd4b69c` (A77/A78/A80/A81). No shared edits before #538; F32 Golden guard and accepted-only route commit. #497 parked. | E3c shared migration and route integration after #538; A81 real shipped-slot replacement/retained setData end-to-end witness both Linux required before merge (moves to earlier first shipped-slot PR if applicable); signed exact evidence. OB1.1. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts (except `facts/sound/ob_d_patches.md`, now B1), module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **#520 / #539 exclusively** `1044ddb`: non-draft; signed Result 7156819486, exact Lab/Golden/strict paired green; #558 merged inbox request. Await Architect review and actual merge, no unchanged rerun. | OB1 sound follow-ups after #520 merges. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`, **`facts/sound/ob_d_patches.md` (run 38b, from B4)**; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **OB-d #492** `79abef6`: Lab green, 15-case rebuild/listening packet prepared.  #539 review-ready; wait for actual merge, collect exact integrated OB-a1 hashes and owner listening handoff. New A80 client task #555 released after #538; OB1 work takes priority. | Studio/OB-c verification; **OB1.1 A80 client [#555](https://github.com/kalharbi11/wirescape-lab/issues/555)** after #538 merges (RealEngine hello capability, correlated reply/event reconciliation, App witness). CN remains B3. |
| **B3** `gpt-builder3` · **Floater / facts** | Assigned paths only; CN facts and previously authorized immutable workflow pins; no harness edits. | **#523/#525** `5253b3c`: intermediate A62/native audits complete and Lab green; running-sum precision qualification recorded, larger/Delay non-pass preserved.  #539 review-ready; wait for actual merge, then final A76 exact Lab, replacement-path check, final A62/native and A69a cost. | Signed exact evidence, lead merge; then KNOWN_ISSUES A2 from measured rows and M4 acceptance. |

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
