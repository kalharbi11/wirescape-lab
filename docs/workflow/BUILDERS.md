<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 09:00 ET (claude-architect run 13, scheduled: no change to assignments). Earlier: run 12 (T1.6a merged, T1.6b #350 issued). The delivery lead owns this table; with no lead active, the Architect refreshes it every run. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

**Merged so far today:**
- #311 OB-g2 `3f8f646`
- #325 ADSR trigger `d4884bd`
- #334 CV to Notes `5bff39c`
- #343 WEB1 `92747e4`
- #336 OB-b `3eeedd6`
- #344 T1.6a `ef11118`

**Merge order (lead):**
1. #344 T1.6a: **merged `ef11118`** (run 12).
2. #333 Gate Delay, after its main refresh.
3. Poly Merge #328 last among the modules.
4. #298, then #291.

Each needs green Lab, Golden and M1 paired at its exact head; only the non-required `Offline facts / windows-latest` may fail.

**All three Claude builder sessions are waiting on owner permission prompts** (CB1 Bash, CB2 Send Message, CB3 Send Later). Their next steps are on their PRs.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `67c60fa`; OB-g7 [#309](https://github.com/kalharbi11/wirescape-lab/pull/309) `c5103c7` | **#298:** the pin-7 test-only grant is answered ([#287](https://github.com/kalharbi11/wirescape-lab/issues/287#issuecomment-7098932576)). Write the six real no-write tests in the granted paths, post the Result, and pin `review-ready` for claude-reviewer (CB2). **Run 13:** at `71bd210` the native build fails on all platforms after the first pin-7 test; fix the build first. **#309:** its advisory L0 matrix runs. `osc-heavy`/`mixed` failures are OB-g8 #326, and `midi-m8` failures are OB-g9 #348. Post a Result asking for the lead's merge; advisory failures do not block. | #291 rebases after #298. |
| **B2** `gpt-builder2` · injected MIDI / OSC | OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326) / [#339](https://github.com/kalharbi11/wirescape-lab/pull/339) `88d1f96` | Lab fails at this head: native builds on all three platforms, and sanitizers. Fix the build, keep the failing-test-first order, then post a Result. | OB-f1 at candidate. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) / [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) `49b90cd`; S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | #322 still fails M1 paired on x64 and ARM64 for existing rows. Every existing row must be within 1 %, and the tolerance is not widened. Merge `main` (CV to Notes and ADSR are in) and regenerate S0. | #291 after #298, then Delay [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) S7.6 → S7.7 → S7.8 → S7.9. |
| **B4** `gpt-builder4` · Gate Delay, then Poly Merge | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) / [#333](https://github.com/kalharbi11/wirescape-lab/pull/333) `a001a44` | **Lane is back with B4** ([direction](https://github.com/kalharbi11/wirescape-lab/pull/333#issuecomment-7098919241)): merge `main`, append `essentials.gate_delay` to main's `bench/module_sets.json`, regenerate S0, fix `M1 paired / linux-x64`, then the Result. | Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328) next. |
| **B5** `gpt-builder5` · OB-g3 | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) / [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) `9228093` | The Studio XFAIL alone does not meet OB-g3 ([disposition](https://github.com/kalharbi11/wirescape-lab/pull/324#issuecomment-7098921069)). Add a native device-off failing test with `--scripted-midi` (enable an endpoint while running, inject, assert delivery), then the fix on the control thread. | Bounded OB-c marker/PCM proof. |
| **CB1** `claude-builder1` · engine writer (OB1 chain) | **M3 T1.6b [#350](https://github.com/kalharbi11/wirescape-lab/issues/350)** (T1.6a #344 merged `ef11118`, run 12) | Split `Node` into `Instance` + `Slot` in one file, per the 0007 table. Goldens identical, Ir within 1 %, no API change; a field with no clear side stops the task and goes to QUESTIONS. Stop the valgrind step: hosted M1 paired is the evidence. | Architect contract-review → T1.6c → TR1e. |
| **CB2** `claude-builder2` · web, then I/O | WEB1 [#340](https://github.com/kalharbi11/wirescape-lab/issues/340) **merged `92747e4`**; **OB-g9 [#348](https://github.com/kalharbi11/wirescape-lab/issues/348)** (new) | Fix the `main` web-demo/Pages run if it fails. Then OB-g9: `midi-m8/still` missing gate edge, failing test first. | claude-reviewer for #298 when B1 pins it. |
| **CB3** `claude-builder3` · transport / module build | M3 TR2 [#341](https://github.com/kalharbi11/wirescape-lab/issues/341) / [#345](https://github.com/kalharbi11/wirescape-lab/pull/345) `1a9b581` | Lab and M1 paired fail. Fix the build, keep existing rows within 1 %, merge `main` and regenerate S0, then the Result. | MB1 → MB2 → MB3 after TR2 merges. |

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
