<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-25 03:32 EST (after Architect run 41). Every builder is a
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
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, OB-d ledger and module-local M7 paths | **OB-d #492 merged `3aa0c33`** (Architect run 42). Support the owner listening handoff and record the disposition in the ledger when it arrives, dropping "(draft)". | OB1 first. **A80 Studio [#555](https://github.com/kalharbi11/wirescape-lab/issues/555)** after #538 merges: RealEngine capability handshake, correlated replies/events and App witness. Coordinate any Studio overlap with B2/B5. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E3c [#537/#540](https://github.com/kalharbi11/wirescape-lab/pull/540)** `89655af`, draft; targeted release/ASan both Linux green, full Lab red on pre-#538 guard and unseeded fixtures. [#538 source re-review complete](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7157016188). Keep shared integration gated on actual #538 merge. | After #538, seed the real shipped-slot witnesses and integrate migrations and accepted-only route commit. A81 requires changed-data replacement with one correlated superseded outcome, new instance/data, and retained setData preserving pending deferral on both Linux arches. **A82 ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7157534847)):** the witness uses OSC In (device-off, no LAN socket, no core seam). Coordinate first shipped-slot merge with #545. Preserve A77 F32 Golden guard. #497 stays parked. |
| **B3** `gpt-builder3` · **Floater / facts** | CN facts and authorized immutable workflow pins | **[#523/#525](https://github.com/kalharbi11/wirescape-lab/pull/525)** draft `09e5820`, integrated subject `8c9bb10`. A76 replacement-path diff required the native rerun. A62, native and A69a workflows completed successfully. Audit the raw evidence and applicable A70 assertions in exact-subject Lab, then finish measured facts and exact-PR Lab/Result. Preserve the intermediate larger-buffer/Delay non-pass. **A83 ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/523#issuecomment-7157532240)):** record the larger row as "bracket reported under A83" with its caps and numbers; post-bracket stays gated. | Lead merge on verified evidence. Then KNOWN_ISSUES A2 from the measured rows and M4 acceptance handoff. |
| **B4** `gpt-builder4` · **Sound** | Modules, module tests and sound facts outside B1's OB-d ledger | **M10 S2 [#564](https://github.com/kalharbi11/wirescape-lab/issues/564)** (Architect run 42): Cortex-M7 double/soft-float symbol names on `fpv5-d16` and `facts/repo/module_memory.md` (instance size, `memory_requirements` 1/8 ch at 48/96 kHz, saved-state size vs the 1 MiB cap). Facts only; advisory workflow; lead merge. | An OB1 sound follow-up from the lead\'s #492 audit preempts #564. Gate Delay and CAT-1 stay parked. |
| **B5** `gpt-builder5` · **Engine** | E3a-2 shared engine, document and server paths; E3b module-local work until shared release | **E3a-2 [#522/#538](https://github.com/kalharbi11/wirescape-lab/pull/538)** `bd4b69c`, ready for evidence CI. Lab/PV1/Web/E4b and both-Linux A81 synthetic witness green; B2 source review complete. Verify ready-head Golden, strict paired and applicable gates. Signed Result must name the A81 carry and B2's OSC timeout caveat (A78/A51); then submit the exact-head Architect pin. | **SR21c [#545](https://github.com/kalharbi11/wirescape-lab/pull/545)** `ecf47ee`: both-Linux direct Groove migration passed, full Lab/Web red. Review failures and keep shared-loader integration behind #538. A81 end-to-end witness moves here if #545 ships the first slot. OB1.1. |

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

Signed: codex-lead, 2026-11-25, 03:32 EST
