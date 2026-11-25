<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, 2026-11-25 (run 38: #504, #515 and #449 merged). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E3a-2 #522 released** (E3a-1 #515 merged `df925fe`): shared loader, façade, `applyGraph`/`setData`, A75 host latest-refused coalescing. **Binding (run 38):** deliver the candidate document `data` for retained and replaced nodes; report busy separately from other refusals. B2 reviews the sidecar paths. Claude contract review at the merge-ready head. | **Pull-ahead (SR21c):** E3b Groove data draft now (E3a header merged). Not tag-holding. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#504 merged `f5c0b75`.** #497 stays draft, unmerged: A67 parked as advisory until after OB1 (A74 disposition). Now: review B5's #522 sidecar paths as they land. | **Pull-ahead (SR21c):** E3c CC/OSC data draft now (E3a header merged; OB1.1). |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts (except `facts/sound/ob_d_patches.md`, now B1), module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **#520 E7c-b Delay v2, exclusively until merged** (#449 merged `bae5e67`): rebase on main and keep the settled Delay path Golden-identical (S7.6 L2). Close #456 unmerged as the archive. **#499/#502** Lows: lead merge on exact green, no further B4 work. | OB1 sound follow-ups after #520 merges. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`, **`facts/sound/ob_d_patches.md` (run 38b, from B4)**; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **OB-d #492** (taken over from B4 on the same branch and PR): replace the stale S7.6 section with the final `bae5e67` rows, including the `tone` margin of 0.0068 dB (S7.6 L1). Prepare the rebuild and the owner-listening handoff now. Finalize at the candidate pin after #520 merges, adding a row only if #520's Golden differs. | Studio/OB-c verification. CN remains B3 #523. |
| **B3** `gpt-builder3` · **Floater / facts** | Assigned paths only; for CN: `facts/` CN rows only, no `bench/continuity/` writes while #485 is open | **#523/#525 intermediate capture released** (#504 merged `f5c0b75`; #507 merged). A76: final-pin Lab assertions plus the A62 trace; recheck replacement-path applicability. Final Delay-inclusive evidence after #520. | Signed exact evidence, lead merge; then KNOWN_ISSUES A2 from measured rows and M4 acceptance. |

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

Signed: codex-lead, 2026-11-25
