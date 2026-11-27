<!-- SPDX-License-Identifier: GPL-3.0-only -->
# PRIORITY — what to work on first

**r4 (claude-planner, run 1, 2026-11-26, [`proposals/0023`](../../proposals/0023-review-and-replan.md)):**
replaces the 2026-11-17 goal and tiers. Earlier revisions are in git history: r1 (owner-directed,
accepted in `0017`), r2 (`0021` §6) and r3 (`0022`, OB r2.12).

**Goal of the next weeks:** a stable headless Player on the Pi and fast module development, on the same
engine as Studio. OB1 acceptance stands as written (owner-only items recorded, never waived), and it
gates no new work.

The lead picks the highest tier first among ready tasks. Inside a tier, STANDING SR16's order applies.
This page loosens no contract, invariant or gate.

## Tiers
| Tier | Work | Rule |
|---|---|---|
| **P0: finish and foundations** | In-flight lane tasks: #540 E3c, #545 E3b, #592 CMP-1, #600 OB-h1, #609 OB-h4, #610 OB-h3. M4 CN final facts #523, then M4 acceptance. MB1, then MB2 (0023 R3.1). Player gate P0: render liveness and controller faults that degrade (R2.2 a, b); OB-h1, then #494. CI-S1–S3 | Always first |
| **P1: Player and Studio bridge** | OB-h2 with gate release; OB-h6. Studio restart policy (R2.5). Player gate P1 (R2.3 e–i: the controller stream P1-e #672 and control port P1-e2 per 0025 §3, settings fsync, SIGTERM, coverage, TR1h). TR3, MB3, promotions from `wirescape-test` after MB2. Studio macro, mapping, lock and bundle work per run 2. **MM** (B1 MM1 → MM3; B3 MM-f). **MOD** modules in `wirescape-test` (outside lanes B1–B5; Stage 1 MOD-1, 2, 3, 5, then MOD-4) and PROMO-n (B4) after MB2 or the §9.6 fallback date. **SC** (0025 §4: SC1 OSC In label and defaults, SC2 indicator, SC4 bundle export; SC3, SC5–SC7 at Stage 3). **`wirescape-headless`** Player tasks run outside lanes B1–B5 from its task pool | After P0 in the same lane |
| **P2: owner items and docs** | Owner-only: OB-d listening list, OB-a2 folder check, Pi 6a/6b. Doc fixes (0023 §8 item 7) | The owner's time; docs in free slots |
| **P3: future facts, idle builders only** | M10 batch 0 · M12 P0 | Only when nothing in P0–P2 is ready |
| **P4: parked** | M5 PV2a–PV5 · M6 MT2–MT5 · M8 · M9 · M10 beyond batch 0 · M11 · M12 beyond P0 (unless run 2 pulls P3 forward) · M3 V1 · M3 T1.5 (cut) | Do not file |

**Module freeze:** no new module enters the lab until MB2 merges. Gate Delay (OB-h4) is the exception.
New modules start in `wirescape-test` and are promoted after MB2.

**V1 stays parked** until the owner decides (CONSTRAINTS "Fixed": the owner's saved patches keep
loading).

Signed: claude-planner, 2026-11-26
