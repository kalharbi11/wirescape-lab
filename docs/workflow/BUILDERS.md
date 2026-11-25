<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-24 (after Architect run 34). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5 #436** `b4b11ac`: Golden green; Lab 45536579166 and paired 45536579387 running at check. Evaluate [A69 raw adopt finding](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7151724857) against ER4/A59 (subject held bus transient, not untouched witness); correct if required. Sync latest main if needed, preserve exact pins, post signed merge-ready Result after full gates. Architect contract-review only then; CN not a merge gate. | E3a after E5 (OB1.1); no competing product writer. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#486/#491 E7b HOLD:** A68 overturn condition met: 10,389,504 B vs 8,388,608 B ([probe 45536610982](https://github.com/kalharbi11/wirescape-lab/actions/runs/45536610982)); post signed memory table, no cap product change until Architect state-hook ruling. #482 merged `3b06273`. **Proceed independently:** A67 hosted enqueue fix, one issue, same load/limits, fail-first, A61/A58, disjoint from #486; no egress remedy inferred. | E7b successor only as ruled, short contract-review if applicable; A67 is not tag-holding. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | **OB-d #492** `5fd2485`, draft Lab green; complete ledger for merged S7.x, Ladder reported row and VCO post-CHOKE note. **#456** final paired A27 evidence at #449 `4fcaa04` verifies tone/division; mode awaits A64 follow-up. Preserve raw, no unchanged rerender; finish neutral classification/evidence. | Final S7.6 ledger after #449 approval, candidate rebuild and owner listen; CHAOS provenance Low. Serialize catalogue/S0. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **#485** `07611d9` native red (preserve raw; assess cases, no weakened oracle); stock untouched witnesses identical, no adopt proof. #474 merged `5820f89`; shared CN writer slot released. **#449** `4fcaa04`: tone/division met; mode awaits A64 exact-row ruling, keep draft, no retune. **#495** three inbox rows consolidated in lead handoff; do not edit competing inbox branch until integrated. | Final E5 CN after settled review pin and A69 cost subject ruling; larger-buffer rerun after ruled E7b solution merges; no premature acceptance. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | #462 merged `51f4b1f`. **#487/#490** `47b0dee`: fail-first Windows libremidi compile red reproduced; MSVC v143/14.44 pin; exact Lab 45538413841 running, facts 45538413826 pending. Verify full Windows measured sections and Linux results, then signed Result. **#322** `c89c111`: unchanged arm64 Function Envelope rows red, A60 scope question merged via #493; no exception yet. | #322 optional, no OB1 tag hold; after A66 disposition resume only as ruled. |

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

Signed: codex-lead, 2026-11-24, 22:14 EST
