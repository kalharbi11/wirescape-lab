<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated 2026-11-16 ET, **gpt-reviewer** (owner-assigned independent review checkpoint).
**claude-lead remains the active delivery lead** for all milestones. Review is not a lead transfer.
Main at review: `879a26cc4a6261cf49ab46afb63e1ee6a993612f` (PR #129 merged). Builders use GitHub connector / hosted device-off evidence; no Worker2, no device/LAN tests, no model polling.

## Controlling decisions and completed merges
- **Q16 answered** by Fable: the single final E1b packet stays on PR #130, one push, `apps/studio/**` only. It must drain unconfirmed incremental edits before a graph chain and add Q14 plus Q16 tests (e–g); on failed review/CI, STOP and close unmerged under Q14, not another correction. #130 is still at `8d0bd29467d1b505c8ac9838fc267301e4537cc0`, draft and red at Lab 43968790557. M2 remains incomplete.
- **Q17 answered**, CI1 r4. PR #129 (CI1.3) merged to main `879a26c`; main push Lab 43990935312 succeeded. **K8 is NOT yet decided by that success**: the first PR sanitizer run *after the main cache save* must show cache restored and job ≤318 s, else lead reverts its sanitizer change and records facts. Do not use an earlier/overlapping PR run as a warm verdict. #141 is an evidence report, not CI1 acceptance until K8 is recorded.
- **Q18 answered:** M5 PV2a PR #151 merged `ba3b020dde9abd045cd02238a2517750d92487b3`; D03/D05/D09 answered with D09 coverage gap retained, no PV2b work before M1 S6.
- **M1 S2** PR #138 merged `70f2e218d6834385c8acd4f5997bc750591aa9eb`. M1 S3 is now PR #159. Full-head Lab/Golden/paired workflows are green, but a fixed/ABI1 cost-probe-versus-strict-T0.6 conflict and required **Claude** I1–I5/I8 contract-review still block merger; green CI is not a waiver.
- **M0 r3** accepted; `facts/BASELINE.md` retains original before-numbers and `ringmod2` is unmeasured. **M2 r3** E0/E1a/PV1 merged; #130/#139 completion still missing. M3/M4/M5/M6/M7 r1 active under their accepted dependencies and STANDING SR1–SR19.

## Active PRs and review evidence (snapshot, 2026-11-16 ET)
| PR | Work | Evidence and next gate |
|---|---|---|
| #130 | M2 E1b, builder 1 | Q16 final packet not pushed; draft/block on current code and red Studio; same branch, no extra ordinary round |
| #149 | M2 gap-only report | Exact-head Lab 43985506389 green; report is source-pinned to pre-Q16 main and describes Q16 as unanswered, so lead should assess a clearly dated addendum before treating it as current; no M2 acceptance claim |
| #150 | M2 continuity, builder 3 | Head `d672a650` has Lab/synthetic/Golden green; actual 45 witness rows and raw/marks hashes still missing; lead authorized new hosted capture workflow on existing branch (SR8/SR18/SR9) |
| #152 | M7 T7.0, builder 3 | Head `1847d58e`: facts JSON now contains 24/24 CHAOS alias rows and three measured Delay switch rows sourced from hosted capture 43989175810 at built head `d4d2b351`; Quad VCA mode1 remains explicitly unmeasured. Lab 43991585936 and x64/ARM64 advisory 43991586082 are green. Independent artifact-to-facts review and acceptance of the explicit SR10 exception remain; no target reset triggered |
| #153 | M6 MT1, builder 2 | Corrected head `2c003e92`: Lab 43991606212 green, three-platform module-tools workflow 43991606284 green including real template check; needs independent source/evidence review and lead disposition |
| #159 | M1 S3, builder 4 | Head `b438613f`: hosted Lab/Golden/paired green; ABI1 cost-probe/T0.6 conflict, exact per-row evidence review, and Claude contract-review unresolved; do not merge |
| #160 | M3 native-v1 fact inventory, builder 1 | Head `ff8f885a`: notes-scope Lab 43991267461 green (foundation passed; code jobs correctly skipped); independent facts review then lead merge |

## Owner-run builder queue (no self-dispatch, one writer/branch at a time)
| Builder | First | Next | Then |
|---|---|---|---|
| **1** | #130 final E1b packet (owner's top priority; resume same PR) | #154 / PR #160 review/merge disposition | #155 reverb after #154 closes |
| **2** | #147 / PR #153 review disposition | #141 CI1 evidence report with K8 pending/actual | — |
| **3** | #148 / PR #152 measured facts and artifact-to-row review | #139 / PR #150 hosted continuity capture/rows | #142 read-only audit already filed (issue comment 6933738092; no duplicate run); revisit only upon new completed evidence |
| **4** | #143 / PR #159 S3 contract conflict/evidence | Claude I1–I5/I8 review when ready | — |

## Reviewer / lead handoff
- **Do not spend Claude on routine CI or source-review work that GPT can prepare.** Immediate lead-authority items: review/merge verified class-A #160 and MT1 #153 as warranted by evidence; review notes-only #149 and request a current-status addendum if needed; apply K8 to the first qualifying post-save sanitizer PR run and file the fact/keep-or-revert decision.
- **Claude-specific work:** #159 requires an independent Claude contract reviewer (not a GPT substitute) on a *settled exact head*. Its separate cost-probe/T0.6 scope conflict must first receive a design/contract disposition; do not ask a reviewer to waive measurement criteria. Later M1 S5b/S6 and specified M7 contract reviews follow their dependencies.
- **Fable-only if needed:** changing instruction-row measurement meaning, the 1% rule or another frozen acceptance threshold. No such change is authorized by a green workflow.
- **Merge policy:** no commits directly to main; lead merges independently reviewed exact heads with all contract criteria and checks satisfied. Notes-only review may use SR13; a draft gap report does not constitute milestone acceptance. SR19 leaves unrelated ready work moving.

Signed: gpt-reviewer, 2026-11-16

## Preserved design-authority weekly queue
The following is Fable's merged #144 catalog/ordering. Operational heads and Q16 status above supersede its historical Q14-dispatch snapshot; no catalog task or standing ruling is removed.

## Queue for the week (Fable, 2026-11-16, run 1)
**Read first:** [STANDING.md](STANDING.md). It lets the lead settle CI, process, correction-limit
and small path questions alone (SR1–SR19) and says who decides what. From 2026-11-17 the design
seat is usually **fable-deputy** (an Opus session, `CLAUDE.md`); Fable is not needed for routine work.

**New contracts, all accepted. Nothing stops or replans: M1 r2, M2 r3 and CI1 r3 are unchanged.**
| Contract | What | Starts |
|---|---|---|
| [M6](milestones/M6.md) | module tools v0 (`check`, `test`, `render` for one folder), new paths only | **now** |
| [M7](milestones/M7.md) | sound quality: batch 1 module-local; batch 2 filters and CHOKE | batch 1 **now**; batch 2 after M1 S6 |
| [M3](milestones/M3.md) | Phase 1 tail: engine split, transport, module build and registry, Reload engine, native v1 removal, residue | RL after E1b; the rest after M1 S6 |
| [M4](milestones/M4.md) | edits never restart: live mod amount, gapless swaps, module data, replace with state, device changes | after M3 TR1e; E5 and E3a also need `proposals/0012` |
| [M5](milestones/M5.md) | protocol v1 | PV2a **now** (PV1 merged, `4161b90`); the rest after M1 S6 |

[PATHS.md](milestones/PATHS.md) lists the files each M3 to M5 task touches, for writing issues.
Each task starts when its own "Depends on" cell is true on `main`; no task waits for a
milestone acceptance report. Order between ready tasks: SR16 (M1, then the M4 chain, then M5,
M3, M6, M7). Design notes behind them: `proposals/0011` (sound), `0016` (module tools), and the
Phase 3 to 6 task list in `proposals/0004`. Notes `0012` to `0015` (Wire module header,
portability and compiler, categories, panels) are Fable's run 2.

**Next action by role**
- **Root lead:** dispatch the Q14 packet to B1 (still open). File M6 MT1 and M7 T7.0 now and
  give them to the first free builders (B2 and B3 when CI1.3 and PV1 close); then S7.1 and S7.4.
  File `facts/code/native_v1_readers.md` (M3 V1 precondition) and M5 PV2a as class-A tasks when
  a builder is free. M6 and M7 pull requests merge or park before M1 S6 opens.
- **M1 lead:** unchanged. For S6, note what `milestones/PATHS.md` found: the 0002 layout does
  not name a place for `native/tests2`, `native/voice`, `native/tools/render`, `native/third_party`,
  `native/examples`, the top-level `tests/protocol/` or the subfolders of `host/`; path filters in
  the workflows other than `ci.yml`, `tools/ci/changed_scope.py`, and `bench/` scripts with
  `native/` written in them move with the rename. Choosing those names is inside S6 (the script
  is the record); `ci.yml` edits are ordered with CI1.3 by the root lead. When S5b merges, S6 is next; when S6 merges, tell the root lead: that
  opens M3 T1.6a, TR2, V1, M5 PV2b and M7 batch 2.
- **Builders:** one task each, as before.
- **Owner:** nothing is needed for the queue. Optional: one `fable: run` to a Claude session
  clears any pending contract review (M1 S3, S5b, S6 need a Claude reviewer; SR11).
- **Design seat (Fable or deputy):** review requests, questions and acceptance reports as they
  arrive. M1, M2 and CI1 acceptance reports are expected this week.

Signed: Fable, 2026-11-16


Signed: gpt-lead, 2026-11-16
