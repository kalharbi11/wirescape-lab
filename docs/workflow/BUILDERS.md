<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by claude-architect (run 35), 2026-11-24 22:45 EST. Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5 #436** `b4b11ac`: **fix A71 first** (High H1: no release-all to `O` after a successful adopt; `engine/render.cpp` and `live_replan_tests.cpp`; fail-first, held bus within 2e-7 on every fade sample). Then exact-head gates and the signed Result at the merge-ready head, and ask for the Claude review once. Tell B1 the new pin. | E3a after E5 (OB1.1). |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E7b #486, now A70 witness only:** a `host/sidecar` test that a 256→512 rule-2 rebuild keeps the held note, Delay tail and VCO phase. Write it now (expected red); it turns green on B4's E7c head. No `session.cpp` change. Close #491 unmerged as a diagnostic record. | A67 #494/#497 with the granted opt-in reason summary (not tag-holding). |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **E7c [#503](https://github.com/kalharbi11/wirescape-lab/issues/503) (A70, OB1 critical path):** state hooks for adsr, vco, host_keyboard, vca and delay v2, plus a slew round-trip; each a bit-identical continuation test. Finish #492 OB-d's Result in parallel (docs only). #456 adds the r1.9a one-sided column. | CHAOS provenance Low. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **#449 S7.6:** mode/tone/division met under r1.9a; post the per-row table and signed Result, then pin for Architect review. **#485/#480:** keep the strict adopt verifier and rerun at B5's A71 head; add the A69a cost rows (Black Ice Choir single, clocked-groove dual and adoption). | Larger CN row rerun after E7c and #486 merge. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | **#487/#490** Windows libremidi pin: finish the exact-head Result (lead merge). **#322:** the arm64 Function Envelope rows are covered by r1.6b; list them and post the Result (optional row). | Floater: take B4's OB-d follow-ups if E7c runs long. |

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
