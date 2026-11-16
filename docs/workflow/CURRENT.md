<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `84dcc02cd11fd8541fb1438eb2b3b88e986291d2`.

## Active contracts
- **[M0 r3](milestones/M0.md)**: Phase 0 remainder, T1.1, P1–P4 (all four inventories merged; P3 `65a365e`). R7 (Q10/Q11) adds the marks file to
  T0.13a and mark-based edit location plus `.github/workflows/continuity.yml` to T0.13b.
- **[M1 r2](milestones/M1.md)**: one engine, S0 and S2–S6. S0, T1.1 and P1 are merged, so **S2 is
  dispatched** (#111). One writer owns S2–S6.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 is merged. PV1 is in PR #105 under Q8. **E1a is
  dispatched** (#112).
- **CI1 r3 accepted at [PR #119 head fbbf771](https://github.com/kalharbi11/wirescape-lab/pull/119)**: CI1.4/#122 is next exclusive `ci.yml` writer; CI1.3/#109 prepares only until #122 merges. Fable permits dispatch before #119 merges.

Fable's Q7–Q11 answers (CI1 r2, M0 r3, M2 r3) merged with #107 (`6702d6a`).

**Sidecar ordering (M1 r2):** T0.13a (#104, merged `35a6ef2`), E1a (#112 / PR #116) and PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | T0.5 #51 / PR #60 | head `7ed7c54` fixes probe prepare(); Lab/Golden green; all full-facts jobs now succeeded, B1 verifying/staging actual artifacts |
| gpt-builder2 | CI1.3 #109 | staging Result verified; no push before #122 merges, then integrate latest main; K7/K8 unchanged |
| gpt-builder3 | PV1 #86 / PR #105 | head `569e187`; CI403 plus bus-channel/client disagreement findings; Q13 disposition before another correction |
| gpt-builder4 | CI1.4 #122 | PR #123 b39d170 delivered; all real aggregates passed, foundation test correction round1 dispatched. #113/118 parked |
| claude-builder1 | T0.13b #100 / PR #106 | MERGED7bf71ae after lead/Worker2 review and all exact-head checks; writer finished/stopped |
| claude-builder2 | M1 S2 #111 | finish S2 only; owner stopped new Claude assignments after current tasks |
| claude-builder3 | M2 E1a #112 / PR #116 | completed Claude review; current rule6/spec correction, then stop |

## Open work (verify heads live; this is a snapshot)
| Task | Issue / PR | Next |
|---|---|---|
| CI1.3 | #109 | gpt-builder2 |
| T0.5 | #51 / PR #60 | B1 verifies/stages completed43930176728 Linux artifacts on7ed7c54; no numerical acceptance from job success alone |
| T0.9 | PR #50 | merged `1918cf75c1223b4a7b83b640b64fce595016468f` after independent review and green exact-head Device/Lab CI |
| T0.13b | #100 / PR #106 | merged7bf71ae;119rows/21edits/3repeats, rawcaptured audit limit recorded |
| PV1 | #86 / PR #105 | exact-head evidence, then lead review |
| M1 S2 | #111 | claude-builder2 |
| E1a | #112 / PR #116 | review DONE, nothing High; apply existing correction packet; exact corrected-head CI/Golden x3 required |
| T0.10 | #113 / PR #118 | draft assigned to gpt-builder4; T0.9/#50 merged, final pass still waits for T0.5/#60 |
| T0.14 | owner | see the cloud build note below |

## Local lead takeover, 2026-11-16

Sole local lead is thread `01a1e5ad-ea43-7b12-bc15-85ff572f1843`; app host and Windows cwd verified.
Existing `wlab-lead-review` retargeted and read back ACTIVE every 45 minutes. No duplicate timer.
Q12 is answered in accepted PR119/fbbf771, not yet merged: CI1.4/#122 GPT-B4 first, then109.
PR119 Lab43931737998 failed only windows-x64 aggregate133530240036 with API403; no waiver.
After CI1.4 lands, integrate it and fully rerun105 and other affected PRs; no failed-only repair.
#116 review5925370959 is DONE: current branch needs fake-stream D5 rule6 test and spec clarifications,
not another identical review. #106 merged7bf71ae after both reset findings fixed, independent final review and exact-head green CI.
#105 has exhausted the two original correction rounds; Q13 asks Fable for the bounded remaining packet.
Whichever105/116 merges second must add applyGraph corpus or record PV1 disagreement.
**Owner steering:** Claude builders finish current tasks/branches and existing corrections, then stop.
No new Claude tasks or automatic S3/E1b dispatch. Keep existing owners/branches until disposition.
See [LOCAL_LEAD_HANDOFF](LOCAL_LEAD_HANDOFF.md) for heads, evidence, routing and execution limits.

## Notes for every builder
- **CI queue time dominates.** In run 43919414792 the `native build linux-x64` job waited 11 min for a
  runner, longer than it ran. Push each correction round as **one push**. Per-file API commits queue a
  full run each, and cancelled runs still hold runners.
- **Native build in a Claude cloud container:** the proxy refuses `codeload.github.com` tarballs.
  `git fetch --depth 1 https://github.com/<owner>/<repo> <sha>`, then
  `git archive --format=tar --prefix=<repo>-<sha>/ FETCH_HEAD | gzip -n`, reproduces each pinned
  tarball **byte-identically**. The SHA-256 equals the `URL_HASH`, checked for all five deps on
  2026-11-16. Copy it to `build/native/_deps/<name>-subbuild/<name>-populate-prefix/src/archive.tar`
  before configuring, and the configure then passes. Local runs are not acceptance evidence.

## Decisions
- Rulings R1–R7 are in M0. Q12 answered at accepted PR119/fbbf771 (merge pending); Q13 PV1 correction disposition is queued in [QUESTIONS](QUESTIONS.md).
- Q5: bundled patches and presets may be reset after the rebuild. Nothing moves now, and golden
  "24 identical" stays through M1 and M2.

## Next action by role
- **gpt-lead:** deliver/review122 first; preserve109 hold, review60 R2 and116 corrections;106 completed; obtain Q13 disposition. Leave S3/E1b unassigned under owner steering.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Contract-review:** #116 DONE; no duplicate request. Future M1 reviews are not dispatched.
- **Fable:** M0 acceptance needs T0.5, T0.9, T0.10 and T0.13b. Owner Q5 item7 answered: no owner patches; Fable recorded it in PR119/Q5 point8. No repeat owner request. Next: `fable: run accept M0` once T0.5, T0.9, T0.10 and T0.13a/b merge.
  PV2 waits on M1 S5b; T1.6/T1.7 on S5b; T1.8 on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). Q5 point 7 answered: no owner patches.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: gpt-lead, 2026-11-16

## Current review boundary
PR123 Lab43935029115:13/14 jobs passed, foundation failed239tests/4 assertions in workflow-section parsing. Same-branch correction1/2 sent; no gate weakening/rerun oldhead. Raw full-facts60 artifacts exist for x64/ARM64; B1 continuation sent. Lead independently checked106 JSON:119rows,21edits,357 aligned repeats, no repeat-count/bracket/offset/residual violations; raw captures not uploaded, so waveform values not independently recalculated. Answered issues90/103 closed;117 still tracks122 implementation. No new Claude assignments. Preserve20percent usage reserve; substantial future review waits actual reset when exhausted.

Signed: gpt-lead, 2026-11-16

Final disposition:106 squash-merged7bf71aeaaef42ce051e89351c293efaca37e6bf3. Lead and Worker2 found no blocking issue; actual78 synthetic tests and all14Lab jobs passed at730794c. Rawwaveform/capture-to-binary reproduction remains explicitly unverified; no contract waiver. Claude1 done/stopped.
