<!-- SPDX-License-Identifier: GPL-3.0-only -->
# PRIORITY — what to work on first (owner-directed, 2026-11-17 ET)

**Goal of the next weeks: an Owner Build the owner can use alone on the Pi 5 (Windows second).**
It does not include Daisy or other hardware, third-party module drop-in, the SDK, the dev loop, panels
or protocol publication. Those come later and are already contracted (M6, M8–M12).

**How this sits with STANDING SR16:** the lanes and contracts are unchanged. Among ready tasks,
the lead picks from the highest tier first. Inside a tier SR16's order applies. This replaces only
SR16's line "M10 batch 0 and M12 P0 never wait": they now run only when a builder has nothing
in P0–P2. No contract, invariant or gate changes.

**Accepted by Fable, 2026-11-17** (`proposals/0017` sections 3 and 4). Two clarifications:
the sidecar lane order is TR1e → E6 → E5/E3a → E7, and PV2b/TR1h/PV3 never make an M4 task wait;
MT1 has merged (#169), so the open M6 work to finish or park before S6 is MT2 (PR #176).

**r2 (claude-architect, owner-answered, 2026-11-23, `proposals/0021` §6):** OB1's M4 set is E6, E4a, E4b, E5, E7 and CN. **E3a, E3b and E3c move to OB1.1.** G-W1 #368 (Groove scrolling without a click) is added to OB1. New module work is frozen until OB1, except a Poly Split if the owner confirms it.

## Owner builds
| Build | What the owner gets | Needs on `main` |
|---|---|---|
| **OB0** (soon, before the S6 rename) | Studio edits (undo/redo, restore, config, OSC rows, CC Learn) stop reloading the whole patch; first sound fixes | M2 E1b-r; M7 T7.0, S7.1, S7.2, S7.4 (and S7.3/S7.5/S7.6 if merged); a tag on `main` |
| **OB1** (the real one) | Edits never restart the patch (gapless add/remove, replace keeps state, Groove editable while running, device and buffer changes keep state); filter and CHOKE fixes | M1 S3–S6; M3 T1.6a–c, TR1e; M4 E6, E4a, E4b, E5, E7, CN; M7 batches 1 and 2; G-W1 #368; the OB tasks below |

## Tiers
| Tier | Work | Rule |
|---|---|---|
| **P0: OB critical path** | M1 S3→S4→S5a→S5b→S6 · M2 E1b-r (#165) · M3 T1.6a→b→c→TR1e · M4 E6→E4a→E4b→E5 and E7, CN · G-W1 #368 · M7 T7.0 (#152), S7.1 (#155), S7.2–S7.9 · M2 evidence #150 (the M4 continuity rows read it) | Always first. Before S6 opens, keep open product PRs few: S6 needs them merged or parked |
| **P1: OB gaps** (contract: [OB](milestones/OB.md)) | OB-a saved-patch round-trip test across S5/S6/E5 for OB1 and E3a for OB1.1 · OB-b Pi install and launch refresh after S6 (one script plus `docs/INSTALL.md`) · OB-c T6.8 device-free regressions (MIDI to CV, ASIO list, panic and buffer gaps) and the 4 unverified items in `KNOWN_ISSUES.md` · OB-d list of bundled patches to rebuild after M7 | File OB-a1 and the OB-c regression tests now; the rest on their Depends cells |
| **P2: finish what is open** | M6 MT1 (#153) to merge or park (it must be gone before S6) · M5 PV2b→PV3 only as M4 needs them (sidecar lane, after TR1e) · M3 RL (Reload engine) | Finish the work in flight. Open no new M6 task |
| **P3: future facts, idle builders only** | M10 S1–S6 · M12 P0 | Only when no P0–P2 task is ready for that builder |
| **P4: parked until OB1** | M6 MT2–MT5 · M3 MB1–MB3, V1, T1.5, TR1h/TR2/TR3 · M5 PV4–PV5 · M8 · M9 · M10 beyond batch 0 · M11 · M12 beyond P0 · CI1 beyond what is open | Do not file. M8–M12 cannot start before M4 anyway |

**V1 (native v1 removal) stays parked** until OB-a proves the owner's saved patches load without it
(CONSTRAINTS "Fixed": the owner's saved patches keep loading).

Signed: claude-architect (owner-directed), 2026-11-17
