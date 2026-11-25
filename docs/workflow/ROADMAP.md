<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Milestone roadmap

Updated 2026-11-24 ET (after Architect run 35). This page shows order, completion and the next gate.
[BUILDERS](BUILDERS.md) shows current assignments. [PRIORITY](PRIORITY.md),
[OB_PLAN](OB_PLAN.md) and the linked contracts control scope and release criteria.

**OB0 accepted 2026-11-20** (tag `owner-build-0` → `a440d71`; Pi smoke is an owner-only follow-up). **Next delivery is OB1.** M1 accepted; Phase C is active. The OB1 M3 prerequisites, M4 E6/E4a/E4b and OB-c have merged. E5v and E7 are merged. Next: E5, E7c state hooks, E7b witness and CN, remaining S7.6 and OB-d, then candidate checks.
OB1 has a separate engine chain and owner Pi acceptance. **Pi testing is postponed to the OB1 candidate** (OB r2.6, owner 2026-11-23).

| Order | Milestone or path | State | Done | Next / completion condition |
|---|---|---|---|---|
| Foundation | [M0](milestones/M0.md) measurement floor | Accepted | Fable accepted r3 with stated exceptions. | Retain unmeasured rows when reusing baselines. |
| Foundation | [CI1](milestones/CI1.md) Lab CI | Accepted | r4 accepted by the Architect. [#172](https://github.com/kalharbi11/wirescape-lab/issues/172) | Future CI work follows priority. |
| Foundation | CI2 (A42/A54) | Merged; draft timing target missed | [#393](https://github.com/kalharbi11/wirescape-lab/pull/393) → `0056d4f`; K1 preserved; draft evidence deferred until ready. Offline diagnostic [#406](https://github.com/kalharbi11/wirescape-lab/pull/406) → `a3b2de1`. | 16m54s draft (9m19s queue) recorded, not waived. Full ready-head and main gates remain. |
| Foundation | [M2](milestones/M2.md) Studio edits and confirmed history | Accepted | r4 accepted under A14. E1b-r and PV1 merged. | M4 E5 owns the edited-subject continuity recheck. M5 owns PV2 follow-ups. |
| **1** | **[OB0](milestones/OB.md)** first installable Owner Build | **Accepted 2026-11-20** | M2 E1b-r, M7 T7.0/S7.1/S7.2/S7.4 and OB-a1 merged; tag `owner-build-0` → `a440d71`. | Owner-only: Pi source-install/smoke on #198 (recorded, not waived). |
| **2a** | [M1](milestones/M1.md) one engine | **Accepted 2026-11-22** | S3–S6 merged; S6 #295 → `25b1a82`. | Done. Phase C rebases on the mapped paths (CURRENT run 7). |
| **2b** | [M3](milestones/M3.md) engine split and transport | OB1 prerequisite code merged; milestone not accepted | T1.6a [#344](https://github.com/kalharbi11/wirescape-lab/pull/344), T1.6b [#360](https://github.com/kalharbi11/wirescape-lab/pull/360), T1.6c [#376](https://github.com/kalharbi11/wirescape-lab/pull/376), TR2 [#345](https://github.com/kalharbi11/wirescape-lab/pull/345) and Poly Merge + Poly Split [#356](https://github.com/kalharbi11/wirescape-lab/pull/356) (`cdc8f14`) merged. TR1e [#385](https://github.com/kalharbi11/wirescape-lab/pull/385) merged `dd1e518` after A38. | A39 bounded exception: LFO voices1/8, linux x64/arm64, at most +2.5 %, expires at CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358). CAT-1 + MB1 parked until after OB1. |
| **2c** | [M4](milestones/M4.md) gapless live edits | In progress | E6 [#395](https://github.com/kalharbi11/wirescape-lab/pull/395) → `3286602`; E4a+E4b [#416](https://github.com/kalharbi11/wirescape-lab/pull/416) → `cb25a2c` (A40 fallback, A50/A51 review); CN harness [#422](https://github.com/kalharbi11/wirescape-lab/pull/422) → `1acb54d`. | **Live editing, critical path.** E5v [#441](https://github.com/kalharbi11/wirescape-lab/pull/441) → `1d4491a`; E7 [#442](https://github.com/kalharbi11/wirescape-lab/pull/442) → `94d1b0b`; E5v evidence [#469](https://github.com/kalharbi11/wirescape-lab/pull/469) → `3df3bb8`. B5 E5 [#436](https://github.com/kalharbi11/wirescape-lab/pull/436) A71 fail-first `5e60c0f`; correction, full gates, signed Result and Architect contract-review still required, CN not an E5 merge gate (A69). E7 CN [#474](https://github.com/kalharbi11/wirescape-lab/pull/474) merged `5820f89`; smaller met, larger not met. E7b [#486](https://github.com/kalharbi11/wirescape-lab/issues/486) is now test-only [#504](https://github.com/kalharbi11/wirescape-lab/pull/504) after A70 overturned cap route; E7c [#503](https://github.com/kalharbi11/wirescape-lab/issues/503) carries the module hooks first. B1 E5 CN [#480](https://github.com/kalharbi11/wirescape-lab/issues/480) awaits corrected E5 source, A69a costs (Black Ice Choir single, Clocked Groove dual/adoption), and larger-buffer rerun after E7c/#504. Then KNOWN_ISSUES A2 rewrite from measured rows. E3a/b/c follow in OB1.1. |
| **2 in parallel** | [M7](milestones/M7.md) sound work | In progress | T7.0, S7.1, S7.2, S7.4 merged; T7.0b [#300](https://github.com/kalharbi11/wirescape-lab/pull/300) → `fac9473`; S7.7 [#380](https://github.com/kalharbi11/wirescape-lab/pull/380) → `540024d`; S7.8 [#405](https://github.com/kalharbi11/wirescape-lab/pull/405) → `8c9f3d0` after A53. | **Sound, unparked (M7 r1.6, A56).** S7.3 #432 merged. S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) approved and merged `6daa23e`. S7.6 [#449](https://github.com/kalharbi11/wirescape-lab/pull/449) all numerical rows met under r1.9a; ready gates, D5 release publication and Architect review pending. S7.9 [#444](https://github.com/kalharbi11/wirescape-lab/pull/444) approved and merged `1be9da2`. OB-d #492 draft in parallel; catalogue/S0 writers stay serialized. A47 retired the T7.0 capture workflow after #291 exact-head capture and D5 publication. |
| **2 in parallel** | [OB support](milestones/OB.md) patches, installation, regressions, modules and UI | In progress | OB-a1 round-trip, OB-a2 runner, OB-e1 census, OB-e2 smoke, OB-b [#336](https://github.com/kalharbi11/wirescape-lab/pull/336) and OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) landed. G-W1 [#384](https://github.com/kalharbi11/wirescape-lab/pull/384) → `7a750b4`; OB-c [#275](https://github.com/kalharbi11/wirescape-lab/pull/275) → `6d2de36` (A52 strict P1 xfail retained). | Owner-folder check; OB-d sound list; OB-f1 candidate recheck (no OB-f2 fix currently released; if a row fails, open scoped fix under OB r2.3). Owner Pi session still required as recorded. |
| **2 in parallel** | [OB-g](milestones/OB.md) I/O endurance and triggered envelopes | In progress (soaks advisory) | Harness [#312](https://github.com/kalharbi11/wirescape-lab/pull/312), OB-g2 [#311](https://github.com/kalharbi11/wirescape-lab/pull/311), ADSR [#325](https://github.com/kalharbi11/wirescape-lab/pull/325), hosted soaks [#309](https://github.com/kalharbi11/wirescape-lab/pull/309), egress drain [#357](https://github.com/kalharbi11/wirescape-lab/pull/357), MIDI endpoint [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) and OB-g8 [#394](https://github.com/kalharbi11/wirescape-lab/pull/394) → `8cc9355` merged. #339 closed under SR6(c); #386 closed unmerged. Diagnostic [#419](https://github.com/kalharbi11/wirescape-lab/pull/419) → `7096cdf`; four advisory failures recorded, not fixed by that PR. | OSC native diagnostics #433 and hosted attribution [#463](https://github.com/kalharbi11/wirescape-lab/pull/463) merged; A67 routes the separate enqueue fix. B2 independent egress model [#482](https://github.com/kalharbi11/wirescape-lab/pull/482) merged `3b06273`; not historic native attribution. A67 independent enqueue task, not tag-holding. #425 merged. B3 optional Note Trigger #322 merged `7590eeb` under r1.6b; no tag hold. Runner/soak evidence stays advisory under OB r2.4a. |
| **3** | **[OB1](milestones/OB.md)** gapless Owner Build on Pi | Waiting on required paths above | OB-a1/a3/b/c, OB-e2, G-W1 and M1/M2/M3 prerequisite code landed. | Finish E5, E7c hooks plus E7b witness/CN, remaining S7.6 and OB-d; recheck Studio (OB-f1) and install the candidate. Owner checks saved patches and runs 100 Pi edits, zero xruns and no visible stutter, with both CN transition costs recorded. Architect acceptance and tag `owner-build-1`; keep OB0 installable. |
| **4** | **OB1.1** module data and live data editing | After OB1 | Remapped by OB r2.5. | E3a engine/header data slots → E3b Groove data and E3c CC/OSC data. The OB1 tag follows its own row above. |

## Lead progress delta — after Architect run 34, 2026-11-24 ET

- #474, #462, #493 and #482 merged; E7b A68 8 MiB overturn now active. See CURRENT and ARCHITECT_INBOX for exact pins and pending rulings. No gate waived.

Signed: codex-lead, 2026-11-24, 22:14 EST

## Lead progress delta — 2026-11-24, 18:24 EST

- E4b Windows test pacing [#448](https://github.com/kalharbi11/wirescape-lab/pull/448) merged `95e18ff` after exact-head review; E5 unblocked. E5v #441 still strict G8 red (two changed keyboard rows), second correction then [#452](https://github.com/kalharbi11/wirescape-lab/issues/452) CN witness. E7 #442 fake-backend rollback verification and A62 pending. E5 first if shared commit.
- S7.5 #291 D5 release publication and independent review still block; S7.6 #449 endpoint assertion correction plus [#451](https://github.com/kalharbi11/wirescape-lab/issues/451) A27 evidence route; S7.9 #444 had awaited A63 narrow frozen-test scope; Architect run 30 granted M7 r1.7 (only vco() test function, exact oracle). No gate waived. OSC A61 remains diagnostic; MIDI sanitizer failure under read-only triage.
- No change to the OB1 release order, acceptance or candidate-only owner steps below. #451/#452 are evidence tasks, not new product scope.

Signed: codex-lead, 2026-11-24, 18:24 EST

## Lead continuation after Architect run 30 — 2026-11-24, 18:34 EST

A63 granted: B4 resumes S7.9, with #451 independent while checks run. A61/A62 remain open. B2 rollback tests and Lab passed; final E7 evidence/review not complete. B1 Delay full Lab red, endpoint diagnosis continues. Other critical-path gates and owner candidate checks unchanged.

Signed: codex-lead, 2026-11-24, 18:34 EST

## OB1 release-gate reconciliation (Architect, run 29)

- **Order of work.** Live editing first (E5v, E5, E7, CN), sound in parallel in the free lanes (S7.3, S7.5, S7.6, S7.9, OB-d), I/O fixes beside them (#424 fix, #425, optional #322). Nothing in the sound lanes writes `engine/` or `host/sidecar/`.
- **Sound gate reconciled.** M7 r1.6 unparks batch 2 for OB1 with a bounded paired-row exception (rows without a changed module, linux x64/arm64, ≤ +2.5 %, expires at CAT-1 #358 or the OB1 tag). PRIORITY's OB1 row and OB acceptance 2 stand as written; no criterion is waived.
- **Fewer stops (SR20).** Self-release inside a lane queue, Low findings never block, `merge: lead` tasks merge on exact-head green plus a Result, facts-only PRs auto-merge, and a Claude review is asked once at the merge-ready head.
- **Candidate only.** OB-f1 rerun, the owner's real-patch folder round trip, install and the owner's Pi session. PI-1 #369 and Pi soaks stay postponed to the candidate; advisory soak rows do not gate the tag. Owner-only checks are recorded, never waived.
- **Still parked** (no OB1 need, new-module freeze): Gate Delay #333, CAT-1 #358 + MB1, MT2 #176.

## Follow-on milestones

[PRIORITY](PRIORITY.md) permits M5 work needed by M4 and lower priority facts in free lanes.
A3 stays parked until OB1. The Architect reviews A4 after OB0 and before its affected tasks.

| Contract | State | Order / trigger |
|---|---|---|
| [M5](milestones/M5.md) protocol v1 | PV1 merged in M2. Later work follows priority. | PV2a disposition → PV2b after S6 → PV3 after TR1h → PV4 → PV5 after stable v1 or owner direction. |
| [M6](milestones/M6.md) module tools | MT1 merged. MT2+ parked. | Resume MT2 after OB1 and A3 disposition where needed. MT3 onward follows M6 dependencies and A4 where applicable. |
| [M8](milestones/M8.md) module format and SDK | Parked | H1 after M4 E3a/E5 and M3 MB2. Host services, porting, SDK and tier work follow H1 and their prerequisites. |
| [M9](milestones/M9.md) rebuild and swap | Parked | L1 after M4 E5 and M8 H5 → L2 rescan → L3 developer loop and L4 UI. |
| [M10](milestones/M10.md) portability and compiler | Batch 0 facts in spare slots. Later stages parked. | M8 unlocks the adapters and portable runtime. R1 → PL1 with M5 PV2b → CP1 after planner, Daisy adapter and S5 facts → CP2. A4 applies before CP1. |
| [M11](milestones/M11.md) module classes and capabilities | Parked | M8 services and SDK unlock these rows. Transport needs M3 TR3. A4 applies to K3/K4. |
| [M12](milestones/M12.md) module panels | P0 facts in spare slots. Later stages parked. | M3 MB2 → P1. P0 and P1 → P3 sandbox. Panels follow their module and data dependencies. |

Lead updates this page when a gate, order or milestone state changes. Keep completed rows
here with evidence. A contract approved for implementation and an accepted milestone have
different states.

Status pass: gpt-reviewer, 2026-11-24. Order and gates revised and accepted by the Architect (run 29).

Signed: claude-architect, 2026-11-24