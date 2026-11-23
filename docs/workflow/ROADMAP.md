<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Milestone roadmap

Updated 2026-11-21 18:38 EST. This page shows order, completion and the next gate.
[BUILDERS](BUILDERS.md) shows current assignments. [PRIORITY](PRIORITY.md),
[OB_PLAN](OB_PLAN.md) and the linked contracts control scope and release criteria.

**OB0 accepted 2026-11-20** (tag `owner-build-0` → `a440d71`; Pi smoke is an owner-only follow-up). **Next delivery is OB1.** M1 S6 window **opened 2026-11-20 17:15 ET** (owner); phases in CURRENT "Decided 2026-11-20 05:40" and "17:15".
OB1 has a separate engine chain and owner Pi acceptance.

| Order | Milestone or path | State | Done | Next / completion condition |
|---|---|---|---|---|
| Foundation | [M0](milestones/M0.md) measurement floor | Accepted | Fable accepted r3 with stated exceptions. | Retain unmeasured rows when reusing baselines. |
| Foundation | [CI1](milestones/CI1.md) Lab CI | Accepted | r4 accepted by the Architect. [#172](https://github.com/kalharbi11/wirescape-lab/issues/172) | Future CI work follows priority. |
| Foundation | [M2](milestones/M2.md) Studio edits and confirmed history | Accepted | r4 accepted under A14. E1b-r and PV1 merged. | M4 E5 owns the edited-subject continuity recheck. M5 owns PV2 follow-ups. |
| **1** | **[OB0](milestones/OB.md)** first installable Owner Build | **Accepted 2026-11-20** | M2 E1b-r, M7 T7.0/S7.1/S7.2/S7.4 and OB-a1 merged; tag `owner-build-0` → `a440d71`. | Owner-only: Pi source-install/smoke on #198 (recorded, not waived). |
| **2a** | [M1](milestones/M1.md) one engine | **Accepted 2026-11-22** | S3–S6 merged; S6 #295 → `25b1a82`. | Done. Phase C rebases on the mapped paths (CURRENT run 7). |
| **2b** | [M3](milestones/M3.md) engine split and transport | Queued | S6 merged `25b1a82`; prerequisite met. | T1.6a → T1.6b → T1.6c → TR1e. Reload engine and module build follow their own task rows and priority. |
| **2c** | [M4](milestones/M4.md) gapless live edits | Queued | M2 continuity baseline available with exceptions. | TR1e → E6 → E4a → E4b → E5 and E3a in writer order → E3b/E3c and E7. Collect CN continuity evidence after each applicable change. After E5, verify the applyGraph voice count row has held-note silence of 0 ms and rewrite KNOWN_ISSUES A2 from the measured table per M4 acceptance. |
| **2 in parallel** | [M7](milestones/M7.md) sound work | In progress | T7.0, S7.1, S7.2 and S7.4 merged. | S7.5 #291 parked for S6; T7.0b #300 merged `fac9473`; A27 cleared; S7.6 #314 waits for Phase C. S7.3 as released. S7.7–S7.9 follow S6 and module order. Then main after-facts and OB-d patch list. |
| **2 in parallel** | [OB support](milestones/OB.md) patches, installation, regressions, modules and UI | In progress | OB-a1 round-trip, OB-a2 runner, OB-e1 census and OB-e2 smoke landed. | Owner-run folder check, OB-a3 safe save, OB-b Pi setup after S6, OB-c oracles and cause-specific fixes, OB-d sound list, OB-f1 facts → Architect targets → OB-f2. |
| **2 in parallel** | [OB-g](milestones/OB.md) I/O endurance and triggered envelopes | In progress | #305 released; #312 harness merged `445123b`; #309/#311 in draft; #307 and #317 active. | Product merges wait for S6. Runner/soak evidence and OB1 item 7 are advisory under r2.4a. |
| **3** | **[OB1](milestones/OB.md)** gapless Owner Build on Pi | Waiting on the paths above | OB-a1 and OB-e2 complete. M2 accepted. | Finish OB1 criteria and install. Owner checks saved patches and runs 100 Pi edits, zero xruns and no visible stutter, with both CN transition costs recorded. Tag `owner-build-1` and keep OB0 installable. |

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

Signed: codex-lead, 2026-11-21, 18:38 EST
