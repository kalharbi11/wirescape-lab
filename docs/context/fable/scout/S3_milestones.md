<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S3 — Milestone and plan state (scout)

Lab commit read: `11a68c2` (2026-11-25 18:08 -0500), branch `claude/wirescape-modes-architecture-tnszf8`. Facts only. ROADMAP = `docs/workflow/ROADMAP.md`, BUILDERS = `docs/workflow/BUILDERS.md`. Statuses of 0003–0016 are the headers' own words; 0017–0020 and 0022 carry no clean status line except where quoted.

## 1. Proposals (proposals/README.md is 3 lines, no index)
| No | Title | Author | Date | Status (header) | Content |
|---|---|---|---|---|---|
| 0001 | Audit of Wirescape at the snapshot | Fable | 2026-11-15 | for the owner (0001:3) | Judgement of the app; perf section provisional |
| 0002 | Plan for the restructuring | Fable | 2026-11-15 | waiting for the owner (0002:3) | Phases and owner decisions D1–D8 |
| 0003 | Wire module API (v3) and dev loop | Fable | 2026-11-15 | design, details settle as built (0003:7) | Module API, dev loop levels, module tools |
| 0004 | Execution plan | Fable | 2026-11-15 | live (0004:4) | Task list T-numbers, owners; engine named Wire |
| 0005 | Edits without restart | Fable | 2026-11-16 | none stated | Design for T0.13, T2.0–T2.4; applyGraph |
| 0006 | One engine migration | Fable | 2026-11-16 | none stated | Remove ABI1 (T1.2–T1.4), contract M1 |
| 0007 | Engine file split | Fable | 2026-11-16 | not yet contracted; after M1 S5b (0007:4) | Seams for T1.6 (engine2.cpp 1,271 lines) |
| 0008 | Transport | Fable | 2026-11-16 | not yet contracted; after S5b (0008:4) | Host tempo/play-stop to modules (T1.7) |
| 0009 | Module build and registry | Fable | 2026-11-16 | not yet contracted; after S6 (0009:4) | Drop-folder build, MB1–MB3 |
| 0010 | Protocol v1 and client edit queue | Fable | 2026-11-16 | PV1 in M2, rest later (0010:5) | Schema-generated protocol, T2.5 |
| 0011 | Sound quality order | Fable (+Opus helper) | 2026-11-16 | contract M7 | Measured order of Phase 4 work |
| 0012 | Wire module header | Fable | 2026-11-16 | design; Part 1 exact, Part 2 frozen header (0012:4) | module header fields, M4/M8 |
| 0013 | Portability | Fable | 2026-11-16 | design (0013:4) | One module source for app, plugins, hardware |
| 0014 | Module categories | Fable | 2026-11-16 | design for T5.1–T5.4, M11 (0014:6); erratum A4 at :3 | GUTTR/Macro/CHAOS categories |
| 0015 | Module panels | Fable | 2026-11-16 | design for T5.5/T5.6, M12; panel file frozen v1 (0015:4) | Panel file and host API |
| 0016 | Module tools v0 | Fable | 2026-11-16 | contract M6 | check/test/render for one folder |
| 0017 | Final rulings and succession | Fable | 2026-11-17 | in force; accepted per PRIORITY:13 | Succession to Claude Architect; M4 engine rules ER1–ER6; Owner Build |
| 0018 | Errata for 0012–0016, M6–M12 | Claude Architect | 2026-11-17 | in force (stricter text wins) | Items (a)–(l) table |
| 0019 | I/O endurance and triggered envelopes | Claude Architect | 2026-11-21 | contract OB r2.4 (0019:5) | OB-g1–OB-g7; Pi all-day OSC/MIDI soak |
| 0020 | CV to Notes, Poly Merge, Gate Delay; S6 writer | Claude Architect | 2026-11-22 | owner decisions, inbox A28 (0020:3) | Order after S6: ADSR trigger, CV to Notes, Gate Delay, Poly Merge |
| 0021 | Replan to OB1 | Claude Architect | 2026-11-23 | owner answered D1–D6; section 6 in effect (0021:3) | Fewer tracks, one serial chain, CI as builder computer |
| 0022 | OB1.1 Tier 1: installation readiness | Claude Architect | 2026-11-25 | accepted for implementation (0022:3) | OB-h1–OB-h6; OSC, patch switching, Gate Delay, presets |

## 2. Milestones (ROADMAP:17–25, 62–68; PRIORITY; contract headers)
Contract files in `docs/workflow/milestones/`. CI2 and OB1/OB1.1 have no own file (OB.md covers OB0/OB1/OB-g/OB-h).
| Item | Contract | State | Merged (PRs) | Remains | Parked why |
|---|---|---|---|---|---|
| M0 measurement floor | M0.md | Accepted, closed (M0:3, Fable 2026-11-16) | per ROADMAP:11 "r3 with stated exceptions" | Keep unmeasured rows unmeasured | — |
| CI1 Lab CI | CI1.md | Accepted (r4; ROADMAP:12, #172) | CI1.1 #96 | Follows priority | — |
| CI2 (A42/A54) | none | Merged; draft timing target missed (ROADMAP:13) | #393 → 0056d4f; #406 → a3b2de1 | 16m54s draft recorded not waived; ready-head and main gates | — |
| M1 one engine | M1.md | Accepted 2026-11-22 (M1:3) | S3 #159, S4 #188/#190, S5a #234/#242, S6 #295 → 25b1a82 | Done | — |
| M2 applyGraph | M2.md | Accepted 2026-11-18, A14 (M2:3) | E1b-r, PV1 #105 | M4 E5 continuity recheck; M5 PV2 follow-ups | — |
| M3 engine split, transport | M3.md | OB1 prerequisite code merged; milestone not accepted (ROADMAP:19) | T1.6a #344, T1.6b #360, T1.6c #376, TR2 #345, Poly Merge+Split #356, TR1e #385 | MB1–MB3, V1, T1.5, TR1h/TR3; A39 exception (LFO voices1/8, ≤+2.5 %) expires at CAT-1 #358 | CAT-1 #358 + MB1 parked until after OB1 (BUILDERS:48) |
| M4 gapless live edits | M4.md | In progress, critical path (ROADMAP:20) | E6 #395, E4a+E4b #416, CN harness #422, E5v #441/#469, E5 #436 (9809dfb), E7 #442, E7 CN #474, E7b #504, E7c voice #507, Delay #539, E5 CN #485 | Final CN/cost facts #523 (B3): audit, exact-source assertions, signed Result; KNOWN_ISSUES A2 rewrite; E3a/b/c in OB1.1 | — |
| M5 protocol v1 | M5.md | PV1 merged in M2; later follows priority (ROADMAP:62) | PV1 | PV2a→PV2b→PV3→PV4→PV5 | Queued, P4 |
| M6 module tools | M6.md | MT1 merged; MT2+ parked (ROADMAP:63) | MT1 #169 | MT2 #176 (PR closed run 44, branch kept), MT3+ | Parked until OB1 and A3 (inbox A3) |
| M7 sound work | M7.md | In progress (ROADMAP:21) | T7.0, S7.1, S7.2, S7.4, T7.0b #300, S7.3 #432, S7.5 #291, S7.6 #449, S7.7 #380, S7.8 #405, S7.9 #444, #499, #502 | OB-d owner listening list (B1 #492) | Batch 2 unparked by r1.6 (A56) |
| M8 module format, SDK | M8.md | Parked (ROADMAP:64) | none | H1 after M4 E3a/E5 and M3 MB2 | New-module freeze; after OB1 |
| M9 rebuild and swap | M9.md | Parked (ROADMAP:65) | none | L1 after M4 E5 and M8 H5 | Same |
| M10 portability | M10.md | Batch 0 facts in spare slots; rest parked (ROADMAP:66) | not itemised | R1, PL1, CP1, CP2 | After M8; A4 applies |
| M11 module classes | M11.md | Parked (ROADMAP:67) | none | needs M8 services, M3 TR3 | Same |
| M12 module panels | M12.md | P0 facts in spare slots; rest parked (ROADMAP:68) | not itemised | P1 needs M3 MB2 | Same |
| OB0 | OB.md | Accepted 2026-11-20 (ROADMAP:7,17) | M2 E1b-r, T7.0/S7.1/S7.2/S7.4, OB-a1; tag `owner-build-0` → a440d71 | Owner-only Pi smoke #198 recorded, not waived | — |
| OB support (OB-a/b/c/e/f) | OB.md | In progress (ROADMAP:22) | OB-a1, OB-a2, OB-e1, OB-e2, OB-b #336, OB-a3 #298, G-W1 #384 (7a750b4), OB-c #275 (6d2de36) | Owner-folder check, OB-d sound list, OB-f1 candidate recheck (run 45717349754 at 6b3789b, pre-candidate; B3 verifying) | — |
| OB-g I/O endurance | OB.md | In progress, advisory (ROADMAP:23) | #312, #311, #325, #309, #357, #324, #394 (8cc9355), #419, #433, #463, #482, #425, #322 (7590eeb) | A67 #494 (unparked by r2.12) | Soaks advisory (r2.4a); Pi runs postponed (r2.6) |
| OB1 | OB.md + PRIORITY | Waiting on required paths (ROADMAP:24) | prerequisites above | Final CN/cost, OB-d, OB-f1 recheck, install; owner items | — |
| OB1.1 data editing | OB.md r2.5 | After OB1 (ROADMAP:25) | E3a-1 #515 (df925fe) | E3a-2 #522/#538 ready-state evidence + review; A80 client #555; E3b #545, E3c #540 draft-ahead (A81 slot witness) | Does not hold OB1 tag |
| OB-h Tier 1 | OB.md r2.12 | Queued, none merged | none | OB-h1 #600, h2 #601, h3 #602, h4 #329 (Gate Delay), h5 #603, h6 #604; A67 #494 | Queued after lane current tasks (OB:80–98) |
| CAT-1 #358 (+MB1) | — | Parked until after OB1 (BUILDERS:48) | PR closed run 44, branch kept | all | New-module freeze / OB1 priority |
| A3 (MT2 T11 option-metadata) | inbox row | Open, "later" (ARCHITECT_INBOX:35) | — | re-rule when MT2 reopens | MT2 parked |
| A4 | errata sweep | A4 errata notes on M6/M10/M11/M12; "Architect reviews A4 after OB0" (ROADMAP:58) | — | applies before CP1, K3/K4 | — |
| MB1 | M3.md:37 | Parked with CAT-1 | — | `wire-describe`, catalogue from it | see above |

## 3. OB1 acceptance (OB.md:108–115, "Acceptance")
Quoted:
1. "**OB0:** M2 E1b-r, M7 T7.0, S7.1, S7.2, S7.4 merged; OB-a1 green; tag on `main`." — met (ROADMAP:7).
2. "**OB1:** every PRIORITY OB1 row merged; OB-a1, OB-a3, OB-b, OB-c merged; OB-d done." — PRIORITY:27 OB1 row needs "M1 S3–S6; M3 T1.6a–c, TR1e; M4 E6, E4a, E4b, E5v, E5, E7, CN; M7 batches 1 and 2; G-W1 #368". Met per docs: M1, M3 T1.6, TR1e, E6, E4a/b, E5v, E5, E7, M7 batches, G-W1, OB-a1/a3/b/c. Not met: CN final facts (#523 pending), OB-d (B1 #492 transferred, owner listening outstanding).
3. "The owner's OB-a2 run over their real patch folder: zero document or render-hash differences not explained by an OB-d entry." — owner-only, not met (CURRENT:57; #590 has no uploads).
4. "The owner's Pi session (last criterion): 100 scripted edits at the owner's buffer size, zero xruns (`0017` section 6), with the two CN transition-cost rows reported." — owner-only, not met; Pi postponed to candidate (r2.6). R2.11 (A88) splits the Pi half into 6a runner (#579) and 6b witnessed Studio session (≥100 hand edits; one stutter or xrun fails).
"Owner-only items (3, 4) are recorded, never waived; the rest is accepted without them."
Items numbered 5–7 are not in the Acceptance block; references: "acceptance item 6" (r2.3, r2.11) = UI smoothness (OB-f); "acceptance item 7" (r2.4a) = OB-g soaks, "recorded, not required". OB-f1 recheck: not yet run on a candidate.
Tag `owner-build-1` conditions: OB1.1 (E3a/b/c, OB-h) excluded (r2.5, r2.12). Held until owner OB-d, OB-a2, 6a/6b (CURRENT:58).

## 4. Lanes (BUILDERS:37–41, refreshed 2026-11-25 17:52 EST)
| Lane | Now | Then |
|---|---|---|
| B1 Studio/OB-c/facts | #585 `73bda36` golden-v0 mock corrected; signed Result next | A80/golden diagnostic, ready gates; OB-h5 #603 after #585; then OB-h2 Studio Host field |
| B2 I/O + sidecar | #540 `d128f43` (own-path parts; shared RealEngine/App waits for #585) | Route/drop/release witnesses; OB-h2 #601 after #540; A67 #494 first only if OB-h1 finds `still` failure |
| B3 Floater/facts | #578 OB-f1 run 45717349754 at 6b3789b; #584 `8795ddc` (owner items 6a/6b doc) | OB-h1 #600 after #579 Result; then OB-h6 #604 |
| B4 Sound | #567 (merge main, ARM rows); CMP-1 A89 bootstrap workflow PR | CMP-1 #592 (6dc6645); then OB-h4 Gate Delay #329 |
| B5 Engine | #545 `7f4cc83` (A90 witnesses (a)–(c) both arches; exact-head evidence needed) | Native/module-local corrections; OB-h3 #602 after #545 |

## 5. Size of the plan
- Milestone dir: 16 files, 1,560 lines total (`wc -l`). 15 are contracts (M0–M12, CI1, OB: 1,351 lines); `PATHS.md` (209) is an inventory, not a contract. Largest: M4 196, M0 161, OB 121, M7 119, CI1 117.
- Highest ruling number referenced: **A94** (OB-h6 patch check tool, CURRENT:21; A91–A94 from run 46). Highest Q number: Q28. Inbox Open rows: 2 (A31 postponed, A3 later; ARCHITECT_INBOX:32–35).
- Line counts: AGENTS.md 102, CLAUDE.md 89, CODEX.md 30. docs/workflow/*.md: 2,003 total — QUESTIONS 655, CURRENT 129, STANDING 131, README 120, OB_PLAN 222, WINDOWS_EVAL 98, DEV_RUN 90, ROADMAP 75, OWNER_LOCAL_TESTS 60, ARCHITECT_SCOUT 60, BUILDERS 57, ARCHITECT_INBOX 44, PRIORITY 41 (13 files).
