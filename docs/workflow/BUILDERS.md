<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-24 19:54 EST, after Architect run 32b. Every builder is a
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
- **Questions never stop a lane.** Add an [inbox](ARCHITECT_INBOX.md) row plus `needs/architect`, then
  work on the next independent item in your lane.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | #436 at `bf3f913`: E5 retirement and migrated staged witness tests under exact-head verification. Prior `de222d0` Lab and targeted four passed; finish exact Lab/Golden/paired, stress and CN plus one Claude contract-review. Keep existing writer boundaries. | E3a after E5 (OB1.1). E5 first if E7 shares sidecar `commit`. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | #442 at `2959f7e`: exact-head Lab, Golden, paired and drift passed; signed Result and [manual review packet](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7148957226). Owner already started the Architect. B3 #457 and B1 A62 CN wait for merge. | Ready-head evidence and one pinned Claude review. B3 owns hosted OSC exposure after E7; B1 owns subsequent CN rows. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | #444 at `c86810e`: numerical evidence complete, CHOKE listening FLACs published and verified. [Manual A65 review](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7148992053). #467 tooling scope and capture are complete; lead tracks remaining facts jobs. #456 supplemental controls complete; final A27 pin waits for B1 and A64. | S7.9 then OB-d bundled-patch list. CHAOS provenance Low is separate. Keep catalogue/S0 writers serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths | #291 at `584e848`: H1 fail-first reproduced; corrective Lab and both targeted sanitizers passed. Sync current main, capture at final pin, obtain clean Golden and fresh D5/re-review. #449 at `e772628` waits for A64 after matched controls confirmed target spectra exceed the old floor. No gate or DSP change while that ruling is pending. | After #291, sync Delay, give B4 final A27 pins and collect final M7 evidence. Then CN refresh after E5v/E5/E7, including A62 buffer rows and larger nontrivial-state witness, followed by A2 rewrite and OB-f1. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | E5v #441 merged `1d4491a` after exact Lab, Golden, strict paired, and #469 continuity at 0 ms edit-induced held-note silence in all three repeats. #462 and #469 retain the evidence; finish their tooling Results. #463 remains test-only until E7 merges. Optional Note Trigger #322 is released per A55 once the mapped writer is free. | After #442 merges, integrate #463 and add the approved status fields. Keep the optional Note Trigger #322 on its own branch and writer scope. |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. Start `review` separately for the pinned S7.5 request.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: codex-lead, 2026-11-24, 19:54 EST
