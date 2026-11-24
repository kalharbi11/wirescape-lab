<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Rewritten by the Architect, 2026-11-24 (run 22, owner: "chat mode for every builder"). Every builder is a
**ChatGPT chat session** with the GitHub connector. Its PR is its build and test environment: push to
run Lab CI, comment `/dev-run …` for targeted runs ([DEV_RUN](DEV_RUN.md)). No Codex sandbox is needed.
Codex is the **lead** only.

**Trial routing.** Follow the [Terra manager rules](../context/COORDINATION_MANAGER.md) and
[Luna coordinator instructions](../../CODEX.md). Cycle 2 limits Terra and Luna to the existing monitored batch. Builders may continue released lane queues outside that batch, including after it closes. Owner or Architect runs may resume those queues at any time, subject to contract and writer gates. Terra may route a fresh released assignment to a newly named ChatGPT Chat after the previous writer stops.

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
| **B5** `gpt-builder5` · **Engine** (critical path) | `engine/` (engine2), engine tests; sole engine writer | E4b [#416](https://github.com/kalharbi11/wirescape-lab/pull/416) merged `cb25a2c` under A40. E5 [#429](https://github.com/kalharbi11/wirescape-lab/issues/429): start fail-first stopped-stream settle Low and pre-code inventory. Voice-count replacement waits for Architect scope. | E5 → E3a (OB1.1). E5 owns shared sidecar `commit` first if needed by both E5/E7. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/` (net, osc, sidecar, midi), `modules/osc_in/`, `engine/control/` handlers | [#425](https://github.com/kalharbi11/wirescape-lab/issues/425) session-cumulative MIDI counters, fail-first. #406 merged `a3b2de1`. B3 owns the #424 OSC diagnostics while active. | [#431 E7](https://github.com/kalharbi11/wirescape-lab/issues/431) after #425. E4b merged. Confirm disjoint sidecar paths with B5; E5 merges first if both touch `commit`. |
| **B4** `gpt-builder4` · **Sound** | `modules/` DSP, `facts/sound/`, module tests | S7.3 [#428](https://github.com/kalharbi11/wirescape-lab/issues/428) CHAOS after the 12 gated T7.0 baseline rows were verified on main. Assigned to B4 under [run 28c owner authorization](https://github.com/kalharbi11/wirescape-lab/issues/202#issuecomment-7141838083); sole sound writer. #405 merged `8c9f3d0`. | #291, #314, S7.9 and Gate Delay #333 stay parked under their existing gates. Catalogue/S0 edits stay serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c** | `apps/studio/`, Studio tests, OB-c oracles; current scoped facts assignment | OB-c #275 merged `6d2de36` per [owner merge authorization](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7141836048) and run 28. [#430](https://github.com/kalharbi11/wirescape-lab/issues/430) writes the E4 continuity facts only. | Facts merge after #422; Studio OB-f1 recheck at the OB1 candidate. #363 remains parked with CAT-1/MB. |
| **B3** `gpt-builder3` · **Floater** | Only the paths of its assigned task | #419 merged `7096cdf`. [#424](https://github.com/kalharbi11/wirescape-lab/issues/424) OSC budget/enqueue diagnostic split and fail-first soak-profile test. Keep load, limits and queue unchanged. | Architect picks the owning lane and fix after the split-count Result. No product fix released yet. |

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
