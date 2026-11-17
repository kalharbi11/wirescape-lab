<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

## Design seat update — Fable, 2026-11-16 (run 2 of 2)
This block is newer than the reviewer's block below and replaces its two "Fable/design seat"
items. Operational PR heads below are the reviewer's snapshot and are not re-verified here.

**Rulings (QUESTIONS Q19, Q20). Stop/replan lines:**
- **M1 r3 (Q19), PR #159 / S3:** *replan, do not stop.* B4 makes one push on the same branch:
  restore case 0 of `native/engine2/tests/benchmark.cpp` and its CMake linkage as on the base;
  leave `cost_probe.cpp`. No correction round is used. Offline Facts must be green with seven
  rows; paired stays 97 rows. Then the lead requests the **Claude** I1–I5/I8 review on that head.
  `abi1_mono` retires by name in **S4** (wider S4 paths; `facts/perf/abi1_mono_final.md` first).
- **M2 r4 (Q20), E1b:** refiled as **E1b-r**: new issue and PR from `task/125-studio-apply-graph`
  at `3fbadbd`; Q14 + Q16 rules and tests, plus debounce test (h); a pre-code comment on the 350 ms
  debounce; normal two rounds. #125 closes as superseded. M3 RL waits for E1b-r; nothing else does.

**New design notes on `main` with this PR:** `proposals/0012` (Wire module header),
`0013` (portability, patch plan, compiler, control surface), `0014` (categories, capability
modules), `0015` (panel file and panel host API).
- **M4 E5 and E3a are no longer waiting for a design.** They start on their own "Depends on"
  cells. The E5 PR lands the whole header block of `0012` §1; E3a adds no header text.

**New contracts, all accepted, all queued behind their "Depends on" cells:**
| Contract | What | Starts |
|---|---|---|
| [M8](milestones/M8.md) | Wire header, config tables, bindings and services, SDK, tiers | after M4 E3a and M3 MB2 |
| [M9](milestones/M9.md) | developer loop level 2 (no state carry in r1) | after M4 E5 and M8 H5 |
| [M10](milestones/M10.md) | portability | **batch 0 (facts S1–S6) now**; the rest after M8 |
| [M11](milestones/M11.md) | GUTTR, Macro Oscillator, CHAOS, nine capability modules | after M8 |
| [M12](milestones/M12.md) | panels | **P0 (facts) now**; P1 after M3 MB2; the rest after M8 and M4 |

**Next action by role**
- **Lead:** dispatch the Q19 push to B4 and the E1b-r issue; file M10 S1–S6 and M12 P0 as
  class-A tasks for the first free builder (SR18; order SR16).
- **Builders:** unchanged, one task each.
- **Design seat (deputy from 2026-11-17):** reviews, questions, acceptance reports. Reserved
  for Fable: the Sub-patch note, state carry across builds (M9 r2), the live-panel limit
  (M12 P0 numbers), T4.2 smoothing policy, the build page contract.
- **Owner:** nothing blocks. Three items wait for you without holding work: approve IDs of
  new stock modules (M11 Y6), listen to Macro Oscillator at 44.1 and 96 kHz when C2 lands,
  and say whether `sound.blend` and `sound.spectral` panel files should load (M12 Z4).

Signed: Fable, 2026-11-16

---

Updated 2026-11-16 ET, **gpt-reviewer**, under the owner's **one-time A–E task authorization** (PRs #160/#149/#162/#152/#159). **claude-lead remains active delivery lead**; this is not a lead transfer, future merge mandate or contract approval.
Verified `main` before this notes update: `7fda86c22ee61faee409b6345f4bf4d0fc03b3f8` (PRs #160 and #149 merged). All devices/MIDI/LAN off; no model polling or test-gate waiver.

## Controlling decisions and completed merges
- **M2 E1b Q14/Q16 FINAL STOP:** #125 / PR #130 last head `3fbadbd0fc4d34d06436119e96d5170cf74d1ea3` failed exact-head Lab 43991969991 (`TS6133`, unused `frequencySnapshot`, all three Studio shard typechecks + Desktop, before Playwright). Active Claude lead **closed #130 UNMERGED** at 2026-11-16 ET, [signed disposition](https://github.com/kalharbi11/wirescape-lab/pull/130#issuecomment-6935702046), preserving `task/125-studio-apply-graph`. Issue #125 remains open/`needs/fable`: Fable/design seat re-contracts E1b as **M2 r4**; no further r3 fix/push/rerun. The 350 ms history debounce is an unverified carry-forward concern. **M2 r3 is NOT accepted**; M3 Reload engine cannot start from E1b.
- **M3 V1 precondition complete:** owner authorized one-time reviewer merge of [PR #160](https://github.com/kalharbi11/wirescape-lab/pull/160), squash commit `002f264441bcfcf13b79ed90bfd21184c14e80ba`. Issue #154 is **closed**. Exactly `facts/code/native_v1_readers.md` was added; no native-v1 removal permission. **Builder 1's assigned #155 (M7 S7.1 reverb) is now runnable** on its own branch.
- **Historical M2 gap inventory landed:** owner authorized one-time reviewer merge of [PR #149](https://github.com/kalharbi11/wirescape-lab/pull/149), squash commit `7fda86c22ee61faee409b6345f4bf4d0fc03b3f8`. `docs/workflow/reports/M2-r3-acceptance.md` is *source-pinned before the Q16 answer* and is expressly **GAP-ONLY**, not a current E1b status or Fable milestone acceptance. #140 issue may await lead's report disposition.
- **Q17 answered**, CI1 r4. PR #129 (CI1.3) merged to main `879a26c`; main push Lab 43990935312 saved cold sanitizer cache. **K8 is NOT yet ruled:** apply Fable's literal first PR *workflow run created after cache save* with sanitizer, cache restored and ≤318 s for keep; else fail/revert under Q17. An older-created workflow whose sanitizer job warmed later is not automatically qualifying. #141 is evidence assembly only; no CI1 acceptance claim.
- **Q18 answered:** M5 PV2a PR #151 merged `ba3b020dde9abd045cd02238a2517750d92487b3`; D03/D05/D09 decisions recorded, D09 coverage exception retained; PV2b waits for M1 S6.
- **M1 S2** #138 merged `70f2e218d6834385c8acd4f5997bc750591aa9eb`. S3 #159 remains **BLOCKED**: strict paired Ir + Golden + Lab green, but the legacy ABI1 cost-probe/required `fixed/abi1_mono` T0.6 row needs design/contract disposition; independent Claude I1–I5/I8 review still required. In addition, exact-head Offline Facts #43991231171 failed on 3 platforms: `verify_artifacts.py` requires **7** measured engine benchmark rows/block, S3 changed `benchmark.cpp` to **6** rows. Do not waive, weaken or edit that validator without proper authority; S4 not released.
- **M0 r3** accepted; `facts/BASELINE.md` preserves original before measurements and `ringmod2` is unmeasured. M1/M2/M3/M4/M5/M6/M7 are governed by their accepted contracts and STANDING SR1–SR19; no closed PR or green CI grants milestone acceptance.

## Active PRs and exact-head blockers (snapshot, 2026-11-16 ET)
| PR | Work | Verified status / next gate |
|---|---|---|
| [#150](https://github.com/kalharbi11/wirescape-lab/pull/150) | M2 applyGraph continuity, B3 | Draft `d672a650`: synthetic/Lab/Golden green; **actual** 45 continuity witness rows, three repeats, b0/b1 marks and raw/marks hashes uncollected. Lead already authorized hosted capture workflow on same PR under SR8/SR18/SR9. No fabricated parity. |
| [#152](https://github.com/kalharbi11/wirescape-lab/pull/152) | M7 T7.0 before-numbers, B3 | Draft `1847d58e`. Measured CHAOS A alias 24/24 + three Delay switches from capture 43989175810, but Quad VCA switch was **not attempted**: `bench/offline/t7_0.py` uses invalid ID `ports.quad_vca` while descriptor/fixture is `essentials.quad_vca`; mocked test repeats invalid ID. Correct test/ID within remaining permitted correction authority, obtain new real hosted switch row and refresh pinned facts/artifact evidence on same branch, then review. Do **not** merge using SR10 to excuse a known probe bug. |
| [#153](https://github.com/kalharbi11/wirescape-lab/pull/153) | M6 MT1 tool skeleton, B2 | Ready `2c003e92`: Lab 43991606212 and module-tools 43991606284 green, but `check.py` catches `TimeoutError` instead of `subprocess.TimeoutExpired` on describe timeout, violating invariant 7 structured C4 FAIL. Historical correction history shows 2/2 ordinary rounds; **lead SR6 exact bounded packet or refile disposition** required before source edit/merge. |
| [#159](https://github.com/kalharbi11/wirescape-lab/pull/159) | M1 S3 ABI1 shim, B4 | Draft `b438613f`: Lab 43991231173, Golden 43991231260, strict paired 43991231343 pass; **Offline Facts 43991231171 fails all three platforms** with seven-vs-six mandatory engine benchmark rows. ABI1 legacy probe / fixed T0.6 row requires design ruling. Independent Claude contract reviewer mandatory after settled head; no S4 or merge. |

## Ordered task owners — current operational queue
| Agent | Runnable next | Dependencies and restrictions |
|---|---|---|
| **gpt-builder1** | **START assigned #155 / M7 S7.1 reverb rate-independence** | #154 is closed via #160. Read #155 + M7 r1; edit only `native/modules2/reverb/**`. Keep 48-kHz Golden identical ×3 and Ir cap; one branch/PR, no own merge. Do **not** resume closed #130, remove v1 reading, or start S7.2 before S7.1 merges. |
| **gpt-builder2** | #153 only after **lead SR6 correction/disposition**; otherwise prepare #141 CI1 gap report if released after MT1's signed blocked Result | Do not touch exhausted MT1 source rounds without lead ruling, do not assert K8 before literal qualifying post-save PR run. MT2/3 need lead dispatch after MT1 merge. |
| **gpt-builder3** | #152 reviewed Quad ID/test defect and real recapture **after lead confirms remaining correction authority** | 1/2 ordinary corrections previously used; sole bench writer. Keep 24 CHAOS measured cases, measure Quad `mode1` (no fabricated fill), update same-PR hashes/CI, hand off for independent review. Then #150 hosted continuity evidence; #142 audit was already signed, no redundant rerun. |
| **gpt-builder4** | #159 **HOLD implementation and merger** until lead/design authority settles cost-probe/T0.6 and validator-row requirement | No deletion of `fixed/abi1_mono`, validator loosening, native code edits outside S3, or S4. After contract-settled head, assign a separate Claude I1–I5/I8 reviewer. |

## Reviewer and lead handoff
- **One-time owner delegation** applied only to reviewer action A (#160 facts merge), B (#149 historical report merge), C (#162 this one-file CURRENT update/conditional notes merge), D (#152 independent defect review only) and E (#159 independent offline-facts blocker review only). It does **not** grant new correction rounds, Fable decisions, product pushes, lead transfer, or future implementation merges.
- **Lead priority:** decide #153 SR6 bounded source correction or refile; triage #152 correction permission/hosted recapture; route #159's strict ABI1 probe + six-vs-seven benchmark validator discrepancy to design seat; apply CI1 K8 literal first eligible post-save PR run, then file keep/revert. Do not repeatedly review green Lab jobs or poll CI. Q14 #130 is closed; #160 and #149 already merged.
- **Fable/design seat:** E1b M2 r4 re-contract; S3 ABI1/T0.6 row disposition (only Fable may alter metric meaning/invariant). A separately assigned independent Claude contract reviewer is mandatory for M1 S3 under SR11 after final settled evidence.
- **Merge discipline:** no direct main push, force-push, bypass, settings or gate change. Exact-head green checks, independent reviewed evidence, and contract permission before merges. SR19 allows unrelated ready lanes to proceed.

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
