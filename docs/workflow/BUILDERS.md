<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-24 19:10 EST; B1–B5 cells updated by Architect run 33 (E7 merged, A64). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5** [#429](https://github.com/kalharbi11/wirescape-lab/issues/429)/[#436](https://github.com/kalharbi11/wirescape-lab/pull/436), draft at `bedbf3c` (test-only update; CI running). E7 merged `94d1b0b` without touching sidecar `commit`, so sync main. Finish adopt/fade against the fail-first tests, collect exact-head evidence, post a Result, and get one Claude contract-review at the merge-ready head.  | E3a after E5 (OB1.1). E5 first if E7 shares sidecar `commit`. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E7 merged** `94d1b0b` ([Architect review](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7149034643), approved `2959f7e`; #431 closed). Lane idle until the lead dispatches the next I/O task. L1 (note-off lost during the restart gap) goes to the owner's Pi checks, with no task.  | Ready-head evidence and one pinned Claude review. B3 owns hosted OSC exposure after E7; B1 owns subsequent CN rows. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | **S7.9** [#440](https://github.com/kalharbi11/wirescape-lab/issues/440)/[#444](https://github.com/kalharbi11/wirescape-lab/pull/444) at `c86810e`: Lab and Golden green; the two x64 LFO rows fall within r1.6. D5 FLAC pair [#467](https://github.com/kalharbi11/wirescape-lab/pull/467) at `6cbaf95`: the facts job failed on windows-x64; fix it or explain it, then the lead publishes and pins the review. **A64 (M7 r1.8):** [#456](https://github.com/kalharbi11/wirescape-lab/pull/456#issuecomment-7149049811) adds the clocked-division target control and the endpoint-floor columns for B1.  | S7.9 then OB-d bundled-patch list. CHAOS provenance Low is separate. Keep catalogue/S0 writers serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths | **S7.5** [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) at `c1601bc`: **changes requested** in the [independent review](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7148569204) (H1). `reset()` leaves `mode_blend = 0`, so an LPG-at-load channel fades in from VCA for 10 ms; that fade is the whole golden difference on `quad-vca-01-lpg-plucks`. Fix: start each voice settled (primed flag); write the fail-first test (LPG output at load equals the pre-S7.5 output from sample 0); expect Golden identical; collect exact-head Golden, paired/Ir, Lab and Portability; then post a fresh Result. The lead pins a new request. **S7.6** [#314](https://github.com/kalharbi11/wirescape-lab/issues/314)/[#449](https://github.com/kalharbi11/wirescape-lab/pull/449) at `e772628`, ruled under **A64 / M7 r1.8** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7149046840)). The floor is max(old-value, target-from-start). `mode` (+0.030 dB) is met. `tone` (+0.307 dB) is not, and is a real residual to reduce in the DSP (no longer fade, no gain retune). `division` reports its target control from B4 #456. Still after #291 (live head `584e848`: finish Golden-identical evidence and the Result).  | After #291, sync Delay, give B4 final A27 pins and collect final M7 evidence. Then CN refresh after E5v/E5/E7, including A62 buffer rows and larger nontrivial-state witness, followed by A2 rewrite and OB-f1. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | **E5v** [#439](https://github.com/kalharbi11/wirescape-lab/issues/439)/[#441](https://github.com/kalharbi11/wirescape-lab/pull/441) at `7d89559`: SR6 round 2 passed (Lab 15/15, Golden 3x, paired 100/0); only the advisory L0 is red. [#462](https://github.com/kalharbi11/wirescape-lab/pull/462) attribution evidence is complete. **[#457](https://github.com/kalharbi11/wirescape-lab/issues/457)/[#463](https://github.com/kalharbi11/wirescape-lab/pull/463) released** (E7 merged): sync main, add the hosted serializer/schema fields, then take it out of draft. No product fix before nonzero hosted split counts (A61).  | After E5v paired G8 green, [#452](https://github.com/kalharbi11/wirescape-lab/issues/452) source-pinned CN voice-count capture must show 0 ms held-note silence. Then E5v lead merge, then optional Note Trigger #322. |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. Start `review` separately for the pinned S7.5 request.

## Lead continuation (2026-11-24 20:00 EST)

- **B1:** #291 H1 correction at `584e848` passed Lab and both sanitizers. Provide final synced pin for fresh T7.0 and D5/re-review. Follow A64 on #449. [#472](https://github.com/kalharbi11/wirescape-lab/issues/472) releases the A62 continuity rows.
- **B2:** E7 is merged. Lane available for the next released I/O task. The Architect's physical MIDI note-off Low goes to owner candidate checks.
- **B3:** #441 E5v merged `1d4491a` at `7d89559`; exact Lab, Golden, paired and #469 CN passed, with 0 ms edit-induced held-note silence in three repeats. #463 is released after E7; integrate main and implement the approved status fields. #462/#469 retain the evidence. Optional #322 follows A55.
- **B4:** #444 D5 listening pair published and [A65 manual review pinned](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7148992053). #467 evidence-tool facts failure remains to verify separately. #456 adds the clocked-division control under A64.
- **B5:** #436 `bf3f913` is in verification for E5 retirement and migrated witnesses. Prior `de222d0` Lab and targeted tests passed. Finish exact-head evidence and one Claude review.

## Lead continuation (2026-11-24 20:16 EST)

- **B1:** #291 at `a875881` has a fresh T7.0b capture showing the click equals the no-switch floor. Full checks and the refreshed D5 switch pair [#476](https://github.com/kalharbi11/wirescape-lab/issues/476) precede re-review. #449 tone is test-first under A64. #472 is active in [#474](https://github.com/kalharbi11/wirescape-lab/pull/474), pinned to E7/E5v main. Reuse merged #469 for the existing E5v witness.
- **B2:** E7 is complete. [#475](https://github.com/kalharbi11/wirescape-lab/issues/475) releases device-off diagnostic work on the extra OSC gate edge in the MIDI egress sentinel.
- **B3:** #469 merged `3df3bb8`. #462 has a Windows parser unit failure, with a correction packet on the PR. #463 stays within A61 status/schema scope. Hosted artifact 14981696094 shows two enqueue drops and zero budget drops on route 17; A67 asks for product-fix routing.
- **B4:** #444 awaits A65 manual contract review. #467 has a distinct Windows facts dependency failure, queued as A66. #456 continues the A64 division control at `b1b27ea`.
- **B5:** #436 at `d4043aa` has exact stress, web and Module Tools passes. It remains draft and needs full Lab and ready-head gates, continuity, and a signed Result before Architect review.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: codex-lead, 2026-11-24, 19:10 EST
