<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead (owner-authorized manual lead run), 2026-11-24 18:24 EST, after #448 merged. Every builder is a
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
| **B5** `gpt-builder5` · **Engine** (critical path) | `engine/` (engine2), engine tests; sole engine writer except `engine/voice/` while E5v #439 is open | **E5** [#429](https://github.com/kalharbi11/wirescape-lab/issues/429)/[#436](https://github.com/kalharbi11/wirescape-lab/pull/436) at `18f89ee`: **released now** after #448 merged `95e18ff`. A55/A59: same-descriptor canonical config replacement, ER4 birth inheritance, adopt or ring-out with bounded held-note replay after collect, fade 20 ms default / 500 ms cap, stopped-stream settle Low, runner size guard. Voice count is E5v. [Ring-out fail-first](https://github.com/kalharbi11/wirescape-lab/actions/runs/45478898801) confirmed. [Lead release](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7147363859); sync main, Lab/Golden/paired/stress/CN and one Claude contract-review at merge-ready head. | E3a draft after E5 merges (OB1.1). E5 first if E7 also touches `commit`; no B3 voice or B2 stopped-handler writes. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/` (net, osc, sidecar, midi), `modules/osc_in/`, `engine/control/` handlers | **E7** [#431](https://github.com/kalharbi11/wirescape-lab/issues/431)/[#442](https://github.com/kalharbi11/wirescape-lab/pull/442) at `0f6d33bc45bf53408e1914a4ed34d4abad412bed`: production unchanged from 6f5b74a; prior 115e315d Lab 15/15, new persistence rollback test pending verification. [Disjoint plan](https://github.com/kalharbi11/wirescape-lab/issues/431#issuecomment-7143193009), [lead continuation](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7147364911). A62 blocks final reply and CN; no device or ABI changes. Read-only triage #444 separate MIDI sanitizer failure; report cause before product task. | E7 ready-head evidence and required contract-review; OSC fix only after A61/A58 diagnostic route names B2. |
| **B4** `gpt-builder4` · **Sound** | `modules/` DSP, `facts/sound/`, module tests; #451 scoped evidence tooling only | S7.3 #432 merged `fe321f9`. S7.9 [#440](https://github.com/kalharbi11/wirescape-lab/issues/440)/[#444](https://github.com/kalharbi11/wirescape-lab/pull/444) pinned `d85c076`: **A63 granted** ([M7 r1.7](milestones/M7.md)): replace only `vco()` CHOKE assertions in `engine/tests/port_behavior_tests.cpp` with the independent oracle, then exact-head evidence; B2 triages the independent MIDI sanitizer failure. **Independent now:** [#451](https://github.com/kalharbi11/wirescape-lab/issues/451) fixed-window A27 evidence tooling for B1 Delay, separate branch/PR, no product/default collector/gate change. [Lead disposition](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7147366119). | S7.9 r1.7 correction first, exact-head M7 evidence and review → OB-d bundled-patch list. CHAOS constants provenance Low separate authorized follow-up. Catalogue/S0 serialized; Gate Delay #333 parked. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, plus sound overflow** | `apps/studio/`, Studio tests, OB-c oracles, `facts/dsp/edit_continuity.md`; for M7 overflow, only the task's module folder | CN facts #437 merged `ba17d7e`. S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) at `c1601bc`: numerical Result, D5 release upload blocked (release-capable session required), independent K1–K8 review pending. **Independent draft-ahead S7.6** [#314](https://github.com/kalharbi11/wirescape-lab/issues/314)/[#449](https://github.com/kalharbi11/wirescape-lab/pull/449) at `83a86e5`: both targeted sanitizer jobs fail line 640 endpoint assertion; [SR5 correction](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7147364351), retain tolerance, distinguish fixture from DSP defect. #451 provides A27 evidence route. | #291 D5 publish + review → #449 merges only afterward → CN refresh after E5v/E5/E7 → KNOWN_ISSUES A2 rewrite → OB-f1 candidate recheck. |
| **B3** `gpt-builder3` · **Floater** | Only assigned task paths | [#424](https://github.com/kalharbi11/wirescape-lab/issues/424)/[#433](https://github.com/kalharbi11/wirescape-lab/pull/433) blocked hosted OSC status (A61). **E5v** [#439](https://github.com/kalharbi11/wirescape-lab/issues/439)/[#441](https://github.com/kalharbi11/wirescape-lab/pull/441) at `27f9881`: Lab/Golden green, x64 paired keyboard voices1/8 +1.148096/+1.126998% (changed-module strict rows); [SR6 round 2](https://github.com/kalharbi11/wirescape-lab/pull/441#issuecomment-7147365530), in-scope attribution/fix only, no exception. | After paired G8 green, [#452](https://github.com/kalharbi11/wirescape-lab/issues/452) separate source-pinned CN evidence route (held-note silence 0 ms), then E5v merge → optional Note Trigger #322 on mapped paths; no shared writer overlap. |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: codex-lead, 2026-11-24, 18:24 EST
