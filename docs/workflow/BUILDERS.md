<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-24 21:13 EST. Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | #436 non-draft at `31ab651` (base `a8b3423`), readiness CI kicked off. B5 handed B1 the stock Groove and synthetic fixture options in [#480](https://github.com/kalharbi11/wirescape-lab/issues/480). B1 stock no-adopt [#485](https://github.com/kalharbi11/wirescape-lab/pull/485) runs fixed-pin capture; synthetic adopt and transition-cost method wait on B5-CN. B5 owns product, B1 owns CN. Wait for exact CN, full gates and signed Result before queuing review. | E3a after E5 (OB1.1). E5 first if E7 shares sidecar `commit`. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | Continue the independent [#475](https://github.com/kalharbi11/wirescape-lab/issues/475)/[#482](https://github.com/kalharbi11/wirescape-lab/pull/482) OSC egress gate-edge diagnosis; test-first draft is open. #463 merged as `a8b3423`; wait for A67 before a separate enqueue product fix. E7 physical MIDI note-off gap stays on the owner candidate checks. | #475 now; A67 product routing follows the Architect. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | #444 exact `c86810e` D5 and numerical evidence ready for A65. #467 tooling waits A66 Windows facts disposition. #456 can document and verify the diagnostic at `b1b27ea`; division disposition waits on the A64 follow-up and final #449 pins. | S7.9 then OB-d bundled-patch list. CHAOS provenance Low is separate. Keep catalogue/S0 writers serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths | #291 `a875881` ready for Architect H1 re-review, exact gates and refreshed D5 published. [E7 CN #474](https://github.com/kalharbi11/wirescape-lab/pull/474) has measured facts with exact-head verification pending; larger-buffer acceptance is A68. Coordinate [#480](https://github.com/kalharbi11/wirescape-lab/issues/480) E5 CN with B5. #449 tone correction checks can run; division acceptance waits on the A64 follow-up and final pins. | After #291, sync Delay, give B4 final A27 pins and collect final M7 evidence. Then CN refresh after E5v/E5/E7, including A62 buffer rows and larger nontrivial-state witness, followed by A2 rewrite and OB-f1. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | #463 merged `a8b3423`; keep the observed enqueue evidence for A67. Continue #462 Windows paired/parser and desktop failures on the same PR; second path-alias correction `a68eb95` awaits exact-head Windows paired, Lab and attribution checks. Optional #322 is released under A55 after E5v. | Resolve #462; continue scoped #322 independently. A67 remains a separate routing decision. |

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

Signed: codex-lead, 2026-11-24, 21:13 EST
