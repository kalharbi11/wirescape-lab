<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-20 13:00 ET (claude-architect acting as lead, run 2). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) (**released now**: W2 merged `c974ba5`) | OB r2.2 pins (v1 only, `.bak-v1[.n]`, never overwrite, Save As never writes source, no `native/` source). Device-off tests for every pin; a Result with exact-head Lab. `review-required`: Claude contract-review before merge. | Merge before 2026-11-21 06:00 ET or park and rebase first after S6. Then OB-b Pi setup (Phase C). Cloud tip: `python tools/cloud/git_deps.py` before `dev.py build` when codeload is refused. |
| **B2** `gpt-builder2` · fixtures / evidence | M7 T7.0b [#296](https://github.com/kalharbi11/wirescape-lab/issues/296) (new) | Switch rows report the no-switch floor and click excess; Delay window covers the delay time. `bench/offline/` + one `facts/dsp/` file. Bench only, so it runs through the S6 window. | OB-f1 #216 merged `c6ae30a`; OB-f2 needs no fix task (OB r2.3). #268 stays parked. Next: OB-f1 advisory re-run at the OB1 candidate. |
| **B3** `gpt-builder3` · module DSP | M7 S7.5 #288 / [#291](https://github.com/kalharbi11/wirescape-lab/pull/291), head `cdf666c` (Architect correction) | Read the exact-head Lab, Golden and Ir at `cdf666c` once and post a Result with the five Ir rows and T7.0 at the floor (M7 r1.3). No source edits. | Lead: D5 pair + independent K1–K8 review, then merge before 06:00 or park. **S7.6 held for T7.0b #296.** During S6: read-only S7.7 VCF prep. After S6: S7.7 → S7.8, S7.9. |
| **B4** `gpt-builder4` · engine / sidecar | M1 S6 [#294](https://github.com/kalharbi11/wirescape-lab/issues/294) / draft [#295](https://github.com/kalharbi11/wirescape-lab/pull/295) | Run `lab/m1_s6_map.py --self-test` and the full-main preflight (446 / 444 / 2), then build the guarded move + substitution replay as a no-write dry run. W3 #286 is complete; W4 only on an owner failure with a device-off failing test. | Window opens 2026-11-21 06:00 ET: rebase onto the frozen base, apply, evidence 1–6, Claude contract-review. Then M3 T1.6a → T1.6b → T1.6c → TR1e → M4 E6… |
| **B5** `gpt-builder5` · bounded support | OB-c prep on [#275](https://github.com/kalharbi11/wirescape-lab/pull/275) (read-only) | W1 merged `9448843`. Find the panic PCM identity failure cause (VCO phase reset suspected) and draft its device-off strict-xfail test, uncommitted until S6 merges. | After S6: OB-c fixes, one PR per case. #198 Pi checklist stays ready for the owner. |

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

Signed: claude-architect (acting lead), 2026-11-20
