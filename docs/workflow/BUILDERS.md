<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 03:40 ET (claude-architect run 9: agent check, task assignment). The delivery lead owns this table; with no lead active since run 7, the Architect refreshed it. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

**Merge order (lead):** #336 and #311 when their exact-head Golden finishes green. Modules: #325 → #334 → #333, or the first that is green (SR19). The first module to merge creates `bench/module_sets.json`; later ones append their ID only. Poly Merge #328 goes last. Then #298 → #291. Each needs exact-head green Lab, Golden and M1 paired; only the non-required `Offline facts / windows-latest` may fail.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `67c60fa`; OB-g7 [#309](https://github.com/kalharbi11/wirescape-lab/pull/309); OB-b [#336](https://github.com/kalharbi11/wirescape-lab/pull/336) `a2cdcae` | #336: Lab green (14/14). Mark it ready for the lead's merge, and watch the owner's `/pi-run io-soak` on #318. #298: add the pin-7 matrix, then post the Result and pin a review request naming **claude-reviewer** (CB2 below). Then #309. | OB-a3 merge, then #291 rebases on it. |
| **B2** `gpt-builder2` · evidence / injected MIDI | OB-g2 [#308](https://github.com/kalharbi11/wirescape-lab/issues/308) / [#311](https://github.com/kalharbi11/wirescape-lab/pull/311) `c06517d` | Result posted, Lab green. Wait for the exact-head Golden, then the lead merges. When #311 merges, tell the Architect: wirescape-pi `NIGHTLY_LANES` gets `mixed/still`. | **OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326), released now** (OB r2.4b): bounded device-off failing test below the harness first (64 × 200 Hz into `host/net/` OSC service + numbered gate sentinel; fall within 50 ms, route `dropped` = 0), then the fix in the stage it names. The profile and limits do not change. New branch `task/326-ob-g8`. |
| **B3** `gpt-builder3` · module DSP | OB-g5 [#316](https://github.com/kalharbi11/wirescape-lab/issues/316) / [#325](https://github.com/kalharbi11/wirescape-lab/pull/325) `9e94769`; OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) / [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) `c6df8f5`; S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | #325: the ADSR tests are now registered in hosted CTest. When M1 paired and Golden finish green at `9e94769`, post the final Result. The lead merges it first. #322: correction `c6df8f5` is in CI. The old head was +1.2–1.6 % on existing rows; every existing row must be within 1 %, and the tolerance is not widened. | #291 rebases after #298; then Delay [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) (S7.6) → S7.7 → S7.8 → S7.9. Serialize ADSR with S7.9. |
| **B4** `gpt-builder4` · Gate Delay, then Poly Merge | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) / [#333](https://github.com/kalharbi11/wirescape-lab/pull/333) `99cb2ea` (CB1 rebased it) | Result posted. Lab green; Golden is running. The Architect spot-checked `0020` §7 at this head and it holds: the S0 catalogue gains only `essentials.gate_delay` (34 → 35), and the bench changes are the allowed 34-plus-`EXPERIMENTAL` list and `new` rows. If another module merges first, append to its `bench/module_sets.json` rather than recreating it. | **Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328), moved here from B5** (run 9), on `task/328-poly-merge`, built on the mapped paths with `0020` §7 from the start. It merges last. T1.6a moved to CB1. |
| **B5** `gpt-builder5` · bounded support / note tools | CV to Notes [#327](https://github.com/kalharbi11/wirescape-lab/issues/327) / [#334](https://github.com/kalharbi11/wirescape-lab/pull/334) `24ae7dd`; OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) / [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) `3bf1e02` | #334: the one-byte S0 fix (`legato` decimals) is in CI. When Golden and M1 paired are green, post the Result. Then rebase #324 onto the post-S6 paths and post its first Result. | Then the bounded OB-c marker/PCM proof. Poly Merge moved to B4. |
| **CB1** `claude-builder1` · engine writer (OB1 chain) | M3 T1.6a [#315](https://github.com/kalharbi11/wirescape-lab/issues/315), **assigned run 9** | Branch `task/315-t1-6a`, one PR `Closes #315`. Mechanical only, inside `engine/` minus `control/` and `voice/` (M3 r1.1): formatting, and internal types moved into `engine/types.h`. Behaviour, public headers, targets, build entry points and test expectations do not change. **Goldens identical and every Ir row within 1 %; any Golden difference is a defect.** No T1.6b split. Lab, Golden and M1 paired green at the exact head, then the Result. The lead merges. | T1.6b (contract-review by the Architect) once T1.6a is on `main`, then T1.6c → TR1e. CB1 is the single engine writer for this chain. |
| **CB2** `claude-reviewer` · Claude reviews | OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) when B1 pins a `review-ready` request | Review the pinned base..head against OB-a3 pins 1–7 (r2.2a reading of pin 4) and the evidence. High/Medium/Low with file and line. Record `Approved for merge <sha7>` or the blockers. | Then any Claude review a contract names. Architect-only contract-reviews (T1.6b, T1.6c, TR1e) stay with the Architect. |

## How the lead maintains this table

- Every lead run checks each builder's open issues, PR heads, Results, checks and labels.
  Refresh every row's next action, including lower priority work with no Architect request.
  When a row is unchanged, retain the next action and update the review date above.
- Keep each builder's active and queued work visible. Put serial tasks in order. Mark tasks
  parallel when their prerequisites are met, scopes do not overlap and the lead released
  both. Each keeps its own issue, writer, branch and PR. A queued entry is planning only.
- Prefer continuity in each lane. Fill a free slot with ready independent work. If waiting
  is better, name the dependency, who can clear it and the next trigger.
- Remove finished tasks after merge or final disposition. Keep final evidence on GitHub
  and completed milestones on the roadmap. Update issue and PR labels in the same handoff.
  See [label rules](README.md#github-labels-for-work-and-review).
- In cloud, give the owner one runnable start list. Resume a CI-dependent task when its
  results enable a new action.

Signed: claude-architect, 2026-11-23
