<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Milestone roadmap

Updated 2026-11-26 ET by Planner run 1 ([`proposals/0023`](../../proposals/0023-review-and-replan.md) §7).
This page shows order, state and the next gate. [BUILDERS](BUILDERS.md) shows assignments.
[PRIORITY](PRIORITY.md) and the linked contracts control scope. Keep one row per item and cells under
40 words; deltas go in [CURRENT](CURRENT.md) (0023 W4).

**Destination (owner, 2026-11-26):** two products on one engine. **Studio** (Windows and Pi) is for
building; the **headless Player** (Pi) is for playing. Module development is fast. OB1 acceptance stands
as written, but it gates no new work.

## Done
| Item | State | Evidence |
|---|---|---|
| [M0](milestones/M0.md) measurement floor | Accepted (r3, stated exceptions) | contract header |
| [CI1](milestones/CI1.md) Lab CI | Accepted r4 | [#172](https://github.com/kalharbi11/wirescape-lab/issues/172) |
| CI2 (A42/A54) | Merged; the 16m54s draft target was missed and recorded, not waived | #393 `0056d4f`, #406 `a3b2de1` |
| [M2](milestones/M2.md) Studio edits and history | Accepted 2026-11-18 (A14) | E1b-r, PV1 |
| [OB0](milestones/OB.md) first Owner Build | Accepted 2026-11-20; tag `owner-build-0` → `a440d71` | Owner Pi smoke #198 recorded, not waived |
| [M1](milestones/M1.md) one engine | Accepted 2026-11-22 | S6 #295 `25b1a82` |
| OB-h5 OSC presets (A92) | Merged | #606 `9957004` |

## In progress and next
| Stage | Item | State | Next / completion |
|---|---|---|---|
| 0 | [M4](milestones/M4.md) gapless live edits | E6, E4a/b, E5v, E5, E7, E7b and E7c merged | Final CN and cost facts [#523](https://github.com/kalharbi11/wirescape-lab/issues/523) (B3), the KNOWN_ISSUES A2 rewrite, then acceptance |
| 0 | M4 E3a/b/c (OB1.1) | E3a-1 merged; E3b #545 and E3c #540 in flight | Merge under M4; no OB1 hold |
| 0 | [M7](milestones/M7.md) sound work | Batches 1 and 2 merged | OB-d owner listening list, then close |
| 0 | [OB1](milestones/OB.md) gapless Owner Build | Code prerequisites merged | Owner-only: OB-d, the OB-a2 folder check, Pi 6a/6b. Architect tags `owner-build-1`. Gates nothing new |
| 0 | OB-h1–h6 ([0022](../../proposals/0022-ob1.1-headless-readiness.md)) | h1 bootstrap #608; h3 #610 and h4 #609 drafts; h5 merged | As OB.md, plus 0023 R2.2(c): OB-h2 gate release; OB-h3 OSC Out gate and route-relisten rows |
| 0 | CI speed (0023 §1) | Trigger edits merged with 0023 | Lead: CI-S1 notes scope, CI-S2 `facts.yml` dispatch-only, CI-S3 `e4b-stress` on ready PRs only |
| 1 | **MB** ([M3](milestones/M3.md) MB1–MB3 + CAT-1 #358) | Unparked by 0023 R3.1 | MB1, then MB2 (one translation unit per module, generated registry, goldens identical; its re-baseline ends A39 and r1.6/r1.6a), then MB3. The lab module freeze ends when MB2 merges |
| 1 | Player gate P0 (0023 R2.2) | New | (a) render liveness: `stalled` state in status (B5); (b) controller faults degrade, never exit (B2); OB-h1, then #494 if needed |
| 1 | Studio restart policy (0023 R2.5) | New | Growing delay, never gives up, non-modal banner (B1) |
| 1 | M3 acceptance | T1.6a–c and TR1e merged | Accept when MB2 merges |
| 1 | `wirescape-test` | Skeleton | Run 2 rules; harness pinned to the lab; T0/T1 CI; first modules |
| 1 | `wirescape-headless` | Skeleton | Run 2 design; Player service with supervision (0023 R2.4), fake player, API v0, bundle check |
| 2 | Player gate P1 (0023 R2.3) | New | Controller stream with Program Change (after run 2), settings fsync, SIGTERM, callback and OSC allocation coverage |
| 2 | M3 TR1h, then TR3 | Unparked | Additive v0 `setTransport` and `status.transport`; Studio tempo and play control |
| 2 | Studio bridge | Run 2 specs | Macro UI, Mappings panel, map mode, lock toggle, bundle export, Player preview; MB3; first promotions |
| 2 | Player v1 | Run 2 specs | Reference UI, `player.json` pages and hardware map, switching by UI, controller and Program Change, variations, UI guide |
| 3 | Scripts and tool host | Run 2 specs | Python runner and helper library, OSC auto-sync, declared controls, Studio tool page host |
| 3 | Pi soaks | — | Player soaks of 4–12 h as release gates: flat memory, flat CPU in silence, zero OSC drops |

## Parked or cut (0023 §7.1)
| Item | State | Reopens when |
|---|---|---|
| [M5](milestones/M5.md) PV2a–PV5 | Parked | A breaking protocol change is needed |
| [M6](milestones/M6.md) MT2+ (#176), inbox A3 | Parked | A lab gate needs a tool that `wirescape-test` built |
| [M8](milestones/M8.md) module format and SDK | Parked | 3 modules are promoted from `wirescape-test` and their limitation issues are collected |
| [M9](milestones/M9.md), [M10](milestones/M10.md) beyond batch 0, [M11](milestones/M11.md) | Parked | After M8 |
| [M12](milestones/M12.md) module panels | Parked (P0 facts in idle slots) | Run 2 may pull P3's sandbox forward for the tool page host |
| M3 V1 (native v1 removal) | Parked | The owner decides (saved patches keep loading) |
| M3 T1.5 residue sweep | Cut | — |

The lead updates this page when a gate, order or state changes.

Signed: claude-planner, 2026-11-26
