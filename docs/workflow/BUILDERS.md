<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by codex-lead, 2026-11-24 23:13 EST (after Architect run 35). Every builder is a
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
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5 #436 A71** `2519e306`: [signed Result](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7152566759); nine workflows green, Golden 81/81, strict paired 100/0 both Linux, Lab sanitizer 97/97, stress and supplemental ASan pass. Hold exact pin for Architect review; #510 merged inbox; no unchanged rerun. B1 notified. | E3a after E5 (OB1.1); CN is not E5 merge gate. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **#486/#504** `cc3f8a3`: named fail-first red all three platforms and sanitizer; await E7c hook integration for combined witness and legacy C2/fresh-ID checks; no session.cpp/cap change. **#497** `a701a57`: Lab 45540069794 and targeted ASan 45541021349 green; [proceed diagnostic-only non-draft hosted matrix](https://github.com/kalharbi11/wirescape-lab/pull/497#issuecomment-7152641775), auto-merge off, incomplete stderr unknown; no temporary instrumentation merge. | #504 merges after E7c, exact green and Result; B1 larger CN rerun. A67 does not hold tag. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; A70 hook paths incl. additive `engine/voice/note_to_cv.h` save/load | **E7c #503/#507** `716fcba`: ADSR/VCO/VCA hooks, both-arch ADSR/Slew target green, Lab 45543545301 red Keyboard/sidecar/sanitizer. B4-A70 ruling in main inbox; preserve Keyboard semantics, coordinate B2 C2 tests; continue unaffected hooks and tests. B1 owns Delay DSP #449 until qualified integration. **#492** draft ledger waits final S7.6/candidate/owner. | #499/#502 Low after critical work; #456 archival after #449 review. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths; `bench/continuity/` (incl. A69 `native/`) | **#449** `f8a318b`: Lab and strict paired green; Golden 45541924603 Linux x64/arm64 red, Windows green. [Bounded diagnosis/correction](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7152641383), SR6; preserve settled arithmetic, ramps and gates. D5/A27 historical pin. **#485** `9ffa1131`: corrected E5 held/Voice exact, 9/9 fallback, phase residual within native bound but extra exact diagnostic red; B1-A69 row in main inbox. Stock green; cost compile only. Prepare request-through-retirement marker/report coverage, actual cost on qualified E5 pin. | Revalidate D5/A27 at final S7.6 pin, full gates/Result/review; larger CN after E7c/#504, then final cost facts. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | **#487/#490** `47b0dee`: Lab green, facts 45538413826 still running; verify complete Windows compiler provenance/measurement and both Linux sections, then signed Result. Read-only #449 support delivered; B1 sole writer. No duplicate CI. | Return to #490 when facts complete; signed Result then lead merge. |

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

Signed: codex-lead, 2026-11-24, 23:13 EST
