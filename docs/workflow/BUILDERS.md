<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect (acting as lead), 2026-11-24 22:30 EST. Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | #436 E5 at `31ab651`; Lab green. B5-CN is ruled (M4 A69): E5's merge waits on its contract-review, not on CN rows. **Next:** sync to main, then post the signed E5 Result at the merge-ready head and ask for the Claude review once. Support B1's bench seam with fixture pointers only. | E3a after E5 (OB1.1). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E7b [#486](https://github.com/kalharbi11/wirescape-lab/issues/486) first** (OB1 M4 row, A68): post the memory delta, then test-first. Continue #475/#482 egress diagnosis while #486's checks run. | A67 enqueue fix (one issue, A61/A58, not tag-holding). |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | S7.9 #444 merged `1be9da2`. **Now: OB-d** bundled-patch list from the merged S7.x Results, including the VCO post-CHOKE behaviour note. #456 adds the r1.9 classification column and gives final division pins with #449. | CHAOS provenance Low. Keep catalogue and S0 writers serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | #291 merged `6daa23e`. **Now:** (1) sync #449 S7.6 to main, fix `tone` in the DSP (A64), and pin final evidence under r1.8/r1.9; (2) post #474's facts Result at green (auto-merge); (3) build the A69 bench seam and the E5 CN rows at E5's pinned head; #485 stock Groove runs in parallel. | E7b larger-row rerun after #486; CN refresh for M4 acceptance. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | #462 is green at `a68eb95`: post the final Result (lead merge). **Next:** [#487](https://github.com/kalharbi11/wirescape-lab/issues/487) Windows facts libremidi fix (A66). Diagnose the #322 `M1 paired / linux-arm64` red (no r1.6 exception on a changed-module graph). | #322 optional OB-g6 row. |

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

Signed: claude-architect, 2026-11-24
