<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-24 (after Architect run 35). Every builder is a
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
- **Keep the Architect inbox current.** When a task is ready for required review, needs a ruling,
  or raises an Architect question, add or update one row in the
  [Architect inbox](ARCHITECT_INBOX.md) through a docs PR. Link the signed Result or question,
  include exact head and base when applicable, and name the task waiting. Use `needs/architect`
  for Architect work. The owner and delivery lead own the `architect-ready` and `review-ready`
  trigger labels. Keep working on independent lane items while the request waits.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5 #436 A71** test-only `5e60c0f`: [Lab 45539874580](https://github.com/kalharbi11/wirescape-lab/actions/runs/45539874580) pending. Preserve fail-first runtime red; then narrow render.cpp correction and every-fade-sample oracle, exact-head Lab/Golden/paired/stress/sanitizer and signed Result. Pin once for Claude review; tell B1 final source. | E3a after E5 (OB1.1); CN is not E5 merge gate. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#486/#504** `cc3f8a3`, test-only, Lab 45539885403 pending. Verify actual runtime red (wrong CTest filter not evidence), coordinate combined E7c/#504 witness and old fresh-list compatibility with B4, no `session.cpp` or cap change. #491 closed unmerged. **#497** `a701a57` A67 native fail-first verified, Lab 45540069794 pending; diagnostic-only ready stage authorized after native green, no auto-merge, then remove instrumentation before final remedy. | #504 merges after E7c, exact green and Result; B1 larger CN rerun. A67 does not hold tag. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **E7c #503 first (critical):** no PR observed at check; test-first hooks/bit-identical continuations, C2/refusals, Delay cap reported. Coordinate B2 witness integration and legacy fresh-ID assertions; no simultaneous sidecar writer or scope expansion. **#492** `367fd3a` ledger draft Lab pending; final S7.6/candidate/owner evidence remains. #456 archive historical classifier and signed r1.9a, close unmerged after #449 review; no rerender. | #499 Ladder actual rows and #502 CHAOS Low only after critical work; B3 can help discrete evidence with writer handoff. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **#449** `4fcaa04` r1.9a all numerical rows meet; named ready gates pending. D5 six FLACs prepared, common -3 dB playback gain to prevent float-source clipping, [publication handoff](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7152005571) pending owner/Codex upload; no full Result yet. **#485** `c503ef0`: A69a parser/seam compile pending; repin strict native, stock and cost after B5 final A71 head. | Signed S7.6 review pin after D5/gates; larger CN rerun after E7c/#504 merge, then final CN facts. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | **#322 merged `7590eeb`** under signed r1.6b ruling; raw arm64 exception preserved. **#487/#490** `47b0dee`: Lab 45538413841 green; full facts 45538413826 pending. Verify full Windows measured sections and Linux outcomes, post signed Result (lead merge). | Floater: bounded OB-d evidence-only help after own CI if assigned and writer handoff explicit. |

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

Signed: codex-lead, 2026-11-24, 22:31 EST
