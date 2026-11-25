<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect, 2026-11-25 (Architect run 37: A72 S7.6 fix, A73 E7c split, A74, SR21 lane changes). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E3a [#512](https://github.com/kalharbi11/wirescape-lab/issues/512) / draft [#515](https://github.com/kalharbi11/wirescape-lab/pull/515)** (OB1.1): engine and header data slots first, failing test first. The sidecar and `setData` parts wait for #504. Carry the E5 Lows L1/L2. | **Pull-ahead (SR21c):** E3b Groove data draft after the E3a engine/header part merges. Not tag-holding. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#486/#504** `c0219b5`: now waits only on **E7c-a** (A73), not on Delay. Make the one fresh-list-only commit on #507, then combine the witness after E7c-a merges. **#497:** A74, one opt-in diagnostic stage, at most two matrix runs, never merged, no auto-merge, back to draft afterwards; park advisory if no cause is found. | #504 merges after E7c-a with exact green and a Result. **Pull-ahead (SR21c):** E3c CC/OSC data draft after the E3a header merges (OB1.1). |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **E7c-a on #507** (A73, SR21): voice-chain hooks only (allocator `friend`, NoteToCv, Keyboard, ADSR, VCO, VCA, Slew). Add the differing-controls fresh-load test, move the `modules/delay/` test changes out, make the Lab green, post a Result and pin it for the short Architect review. | **E7c-b** Delay v2 state (new issue and branch) when #449 merges → **#492** OB-d at the final S7.6 → #456 archival → #499/#502 Lows. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **#449** at Architect head **`c951a47`** (A72: settled samples use the verbatim pre-S7.6 loop; FMA contraction caused the Golden red). Keep the commit. Check exact Lab, Golden (identical), paired and Ir. Revalidate A27/D5 at this pin, then post a signed Result. If x64 Golden is still red, post the first divergent sample and stop under SR6. **#485** `1d8e11a`: A69b repin on `9809dfb`, collector fix, dual/adoption rows. | After #449 and #485 merge: Studio/OB-c follow-ups. **The larger-buffer CN rerun moves to B3 (SR21c).** |
| **B3** `gpt-builder3` · **Floater / facts** | Assigned paths only; for CN: `facts/` CN rows only, no `bench/continuity/` writes while #485 is open | **#487/#490** `47b0dee`: finish the facts run, verify Windows compiler provenance and Linux rows, then post a signed Result. | **Moved from B1 (SR21c):** the M4 larger-buffer CN rerun on the merged harness once E7c-a and #504 merge, then the final A69a CN cost facts. These rows feed the KNOWN_ISSUES A2 rewrite and M4 acceptance. |

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
