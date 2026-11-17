<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated 2026-11-16 ET, **claude-lead** (active lead for every milestone, including M1; owner, 2026-11-16).
Main `cd8b02d7ee4b4a95de08798384568a7267c52436`. No Worker2, no timers, no root/M1 sub-leads: builders run only when the owner starts them.
Builders are GitHub-connector only (no local native build), so every measurement comes from hosted workflows (SR8/SR9/SR18).

## Contracts
- **M0 r3** accepted/closed (Fable). `facts/BASELINE.md` gives before-numbers; ringmod2 unmeasured.
- **M2 r3:** E0, E1a, PV1 merged. E1b #125/PR130 held on **Q16** (design seat). Continuity #139/PR150 waits for hosted capture. Gap report #140/PR149 draft (not an acceptance).
- **CI1 r3:** CI1.1/1.2/1.4 merged. CI1.3 #109/PR129 STOPPED: fresh PR run missed the cache again (run 43984524907); **Q17** asks for the bootstrap-merge ordering.
- **M1 r2:** S2 #111/PR138 evidence packet `c0e020b` running (paired instructions 43986554879, Golden 43986554704, Lab 43986554686). Lead merges S2 on B4's Result if all rows ≤1 % (Chord rows SR10 exceptions), link proof ×3 and Golden 24 identical ×3 hold. Then S3 #143 (needs a **Claude** contract-review).
- **M3/M4/M5/M6/M7 r1** accepted. Ready now: M5 PV2a PR151 (correction 1/2: drop recommendation column; Q18 holds the batch), M6 MT1 PR153 (SR8 workflow granted), M7 T7.0 PR152 (hosted capture workflow granted), new **M3 V1 facts #154**, new **M7 S7.1 #155**.

## Builder queues (run in this order; one active PR each)
| Builder | 1 | 2 | 3 |
|---|---|---|---|
| gpt-builder1 | PR151 correction (lead comment 6933781199) | #154 `native_v1_readers.md` | #155 S7.1 reverb |
| gpt-builder2 | PR153: add `module-tools.yml` per 6933779966, real template check ×3 | #141 CI1 gap-only report (CI1.3 open on Q17) | — |
| gpt-builder3 | PR152: `t7-0-capture.yml` + fill facts (6933783098) | PR150: continuity capture workflow + rows (6933784579) | #142 audit after PR150 Result |
| gpt-builder4 | PR138: Result from the three runs (6933788066) | #143 S3 after S2 merges | — |

## Holds
- **Q16** (E1b anchor) and **Q17** (CI1.3 ordering): design seat; each blocks only its task (SR19). **Q18**: needed before PV2b.
- Claude reviews: none due now. Next due: M1 S3 (after S2), S5b, S6; M7 S7.3/S7.4 contract-review; S7.7/S7.8 Claude.

## Merge policy (unchanged)
Lead merges exact reviewed heads, expected SHA pinned, when every criterion and test holds; auto-merge only for a reviewed head waiting on CI. No gate weakening, no settings changes, devices off.

Signed: claude-lead, 2026-11-16

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
