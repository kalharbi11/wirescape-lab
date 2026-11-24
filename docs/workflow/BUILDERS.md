<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Rewritten by the Architect, 2026-11-24 (run 22, owner: "chat mode for every builder"). Every builder is a
**ChatGPT chat session** with the GitHub connector. Its PR is its build and test environment: push to
run Lab CI, comment `/dev-run …` for targeted runs ([DEV_RUN](DEV_RUN.md)). No Codex sandbox is needed.
Codex is the **lead** only.

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
- **Questions never stop a lane.** Add an [inbox](ARCHITECT_INBOX.md) row plus `needs/architect`, then
  work on the next independent item in your lane.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B5** `gpt-builder5` · **Engine** (critical path) | `engine/` (engine2), engine tests; sole engine writer | TR1e [#385](https://github.com/kalharbi11/wirescape-lab/pull/385) is **approved at `5d2d78b`** (A38). The lead merges it once the `Offline facts / windows-latest` re-run is green. Then E6 is released. **Draft-ahead now:** E6 [#391](https://github.com/kalharbi11/wirescape-lab/issues/391) / [#395](https://github.com/kalharbi11/wirescape-lab/pull/395); fold in the A38 Low (assert on the `reconfigure` host-packet push). | E6 → **E4a+E4b in one PR** (two commits, one Claude review; A40) → E5. M4 contracts are unchanged otherwise |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/` (net, osc, sidecar, midi), `modules/osc_in/`, `engine/control/` handlers | **OB-g8 fix** (A41): fast path for literal OSC patterns, tracked on [#383](https://github.com/kalharbi11/wirescape-lab/issues/383). The [#386](https://github.com/kalharbi11/wirescape-lab/pull/386) diagnostic is complete; close it unmerged and keep the branch | **E7** buffer/device changes keep state (M4) once B5's E4b merges (E7 is parallel to E5; E5 merges first if both touch sidecar `commit`) |
| **B4** `gpt-builder4` · **Sound** | `modules/` DSP, `facts/sound/`, module tests | Two chains. Work on one while the other waits: S7.7 [#380](https://github.com/kalharbi11/wirescape-lab/pull/380) (apply M7 r1.5, post the Result), then S7.8 [#374](https://github.com/kalharbi11/wirescape-lab/issues/374). Also S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) (refresh exact-head evidence, ARM64 Ir, D5) | S7.6 [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) after #291 → S7.9 → OB-d list after M7 batch 2. Catalogue/S0 edits are serialised: one sound PR at a time touches them |
| **B1** `gpt-builder1` · **Studio / OB-c** | `apps/studio/`, Studio tests, OB-c oracles | OB-c [#275](https://github.com/kalharbi11/wirescape-lab/pull/275)/[#203](https://github.com/kalharbi11/wirescape-lab/issues/203): panic PCM and Groove STOP oracles with the production sidecar, then cause-specific fixes. Take #275 over from the lead's draft on the same branch | S7.3 (as released in M7) → UI recheck at the OB1 candidate (OB-f1 rows) |
| **B3** `gpt-builder3` · **Floater** | Only the paths of its assigned task | **CI2** [#390](https://github.com/kalharbi11/wirescape-lab/issues/390) (A42): shorter Lab CI for drafts | On call: the lead or the Architect assigns independent tasks (owner priorities such as #356, CI, facts) without disturbing other lanes. Between tasks, post one lane-status comment and wait |

**Parked until after OB1** (branches kept): Gate Delay #333, Note Trigger #322, CAT-1 #358 (+MB1), MT2 #176.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: claude-architect, 2026-11-24
