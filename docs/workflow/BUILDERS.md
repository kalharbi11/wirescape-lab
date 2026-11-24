<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by the Architect, 2026-11-24 run 29 (rewritten in run 22, owner: "chat mode for every builder"). Every builder is a
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
- **Fewer stops ([SR20](STANDING.md)).** Start the next queue task yourself when its predecessor merges (open the issue if missing). Low findings never block. `merge: lead` tasks merge on exact-head green plus your Result. Ask for a Claude review once, at the merge-ready head.
- **Questions never stop a lane.** Add an [inbox](ARCHITECT_INBOX.md) row plus `needs/architect`, then
  work on the next independent item in your lane.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B5** `gpt-builder5` · **Engine** (critical path) | `engine/` (engine2), engine tests; sole engine writer except `engine/voice/` while E5v #439 is open | **E5** [#429](https://github.com/kalharbi11/wirescape-lab/issues/429)/[#436](https://github.com/kalharbi11/wirescape-lab/pull/436), scope ruled by **A55** (run 29): replacement for a same-descriptor canonical config change (sidecar `commit` chooses replace), ER4 birth inheritance, `adopt` or ring-out with held-note replay, fade 20 ms default / 500 ms cap, the stopped-stream settle Low, `reconfigure` removed if unused. Voice count is **not** E5 (→ E5v). Claude contract-review once, at the merge-ready head. | E3a draft after E5 merges (OB1.1). E5 merges first if E7 also touches `commit`. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/` (net, osc, sidecar, midi), `modules/osc_in/`, `engine/control/` handlers | [#425](https://github.com/kalharbi11/wirescape-lab/issues/425)/[#434](https://github.com/kalharbi11/wirescape-lab/pull/434) session-cumulative MIDI counters, fail-first. | [#431 E7](https://github.com/kalharbi11/wirescape-lab/issues/431) after #425 (draft-ahead allowed now). Post a disjoint-path plan against #436 before writing `host/sidecar/session.cpp`; E5 merges first if shared. Then the #424 OSC fix if A58 routes it to `host/osc`. |
| **B4** `gpt-builder4` · **Sound** | `modules/` DSP, `facts/sound/`, module tests | S7.3 [#428](https://github.com/kalharbi11/wirescape-lab/issues/428)/[#432](https://github.com/kalharbi11/wirescape-lab/pull/432) CHAOS band-limit; lead merges after its contract-review. | **S7.9** [#440](https://github.com/kalharbi11/wirescape-lab/issues/440) CHOKE (ADSR/VCO; draft-ahead allowed) → **OB-d** bundled-patch list. Catalogue/S0 edits stay serialized with B1's sound PRs. Gate Delay #333 stays parked. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, plus sound overflow** | `apps/studio/`, Studio tests, OB-c oracles, `facts/dsp/edit_continuity.md`; for M7 overflow, only the task's module folder | CN facts #437 merged `ba17d7e`. Next: S7.5 takeover. | **S7.5 Quad VCA** [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) (takeover from B4: merge main, exact-head rerun, Result under M7 r1.6 and D5) → **S7.6 Delay** [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) → CN refresh after E5v/E5/E7 merge → KNOWN_ISSUES A2 rewrite → OB-f1 recheck at the candidate. |
| **B3** `gpt-builder3` · **Floater** | Only the paths of its assigned task | [#424](https://github.com/kalharbi11/wirescape-lab/issues/424)/[#433](https://github.com/kalharbi11/wirescape-lab/pull/433) OSC budget/enqueue split, fail-first. Load, limits and queue unchanged. | **E5v** [#439](https://github.com/kalharbi11/wirescape-lab/issues/439) (A55; draft now, `engine/voice/` + three voice module folders) → **Note Trigger** [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) (OB r2.9, optional, same folders; rebase on mapped paths). |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: claude-architect, 2026-11-24
