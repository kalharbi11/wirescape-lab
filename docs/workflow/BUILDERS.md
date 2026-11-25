<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-25 (after Architect run 37). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E3a-1 #512/#515** `bd7c421`: A75 cap correction, stress green, Lab red portable SDK include guard (`sdk/data_layout.h` string/vector). [Lead correction](https://github.com/kalharbi11/wirescape-lab/pull/515#issuecomment-7153665282): host-only placement, no whitelist; keep draft until exact Lab green then full ready gates and review. E3a-2 #522 waits #504, B5 writer/B2 review. | **Pull-ahead (SR21c):** E3b Groove data draft after the E3a engine/header part merges. Not tag-holding. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#486/#504** `c2461a0`: voice-only fail-first; A70a compatibility commit `3031bcb` already delivered on #507. Wait for E7c-a merge then exact-head witness. **#497** `edfd3e0`: Lab/ASan green, lead verified auto_merge null before/after non-draft, first A74 matrix [45552779925](https://github.com/kalharbi11/wirescape-lab/actions/runs/45552779925) queued. Diagnostic only; no merge, return to draft, at most two matrices, explicitly mark per-producer drains unavailable. | #504 merges after E7c-a with exact green and a Result. **Pull-ahead (SR21c):** E3c CC/OSC data draft after the E3a header merges (OB1.1). |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **E7c-a #507** `398e426`: native Lab and both-arch targeted Keyboard/sidecar pass. Lead moved non-draft; Golden 45552787002, strict paired 45552787013, ready Lab 45552787051 queued. No Delay paths; verify A73 differing-control, single friend and B2 compat; signed Result and Architect pin only after full gates. | **E7c-b #520** Delay v2 state (new issue and branch) when #449 merges → **#492** OB-d at the final S7.6 → #456 archival → #499/#502 Lows. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **OWNER HOLD:** #449 `c951a47` failed Linux Golden and x64 strict paired; Architect is diagnosing a new fix. Preserve current head, no Delay writes, duplicate CI, or A27/D5 repin until Architect handoff. #485 merged `9000e8f`; CN handed to B3 #523. | On explicit new Architect pin: exact gates, A27/D5 applicability, signed Result and qualified review; then Studio/OB-c follow-ups. |
| **B3** `gpt-builder3` · **Floater / facts** | Assigned paths only; for CN: `facts/` CN rows only, no `bench/continuity/` writes while #485 is open | **#523 CN evidence:** #490 merged `b4820a8`, #485 merged `9000e8f`. Prepare exact-source capture packet now; only facts CN rows and two workflow pin/trigger paths authorized. Intermediate voice capture after #507/#504 merge; final Delay-inclusive larger buffer after #449/#520; final A69a costs on integrated OB1 source. No harness changes. | Signed exact evidence, lead merge; then KNOWN_ISSUES A2 from measured rows and M4 acceptance. |

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

Signed: codex-lead, 2026-11-25, 00:18 EST
