<!-- SPDX-License-Identifier: GPL-3.0-only -->
# PRIORITY — what to work on first (owner-directed, 2026-11-17 ET)

**Goal of the next weeks: an Owner Build the owner can use alone on the Pi 5 (Windows second).**
It does not include Daisy or other hardware, third-party module drop-in, the SDK, the dev loop, panels
or protocol publication. Those come later and are already contracted (M6, M8–M12).

**How this sits with STANDING SR16:** the lanes and contracts are unchanged. Among ready tasks,
the lead picks from the highest tier first. Inside a tier SR16's order applies. This replaces only
SR16's line "M10 batch 0 and M12 P0 never wait": they now run only when a builder has nothing
in P0–P2. No contract, invariant or gate changes.

## Owner builds
| Build | What the owner gets | Needs on `main` |
|---|---|---|
| **OB0** (soon, before the S6 rename) | Studio edits (undo/redo, restore, config, OSC rows, CC Learn) stop reloading the whole patch; first sound fixes | M2 E1b-r; M7 T7.0, S7.1, S7.2, S7.4 (and S7.3/S7.5/S7.6 if merged); a tag on `main` |
| **OB1** (the real one) | Edits never restart the patch (gapless add/remove, replace keeps state, Groove editable while running, device and buffer changes keep state); filter and CHOKE fixes | M1 S3–S6; M3 T1.6a–c, TR1e; M4 E6, E4a, E4b, E5, E3a, E3b, E3c, E7, CN; M7 batches 1 and 2; the OB tasks below |

## Tiers
| Tier | Work | Rule |
|---|---|---|
| **P0: OB critical path** | M1 S3→S4→S5a→S5b→S6 · M2 E1b-r (#165) · M3 T1.6a→b→c→TR1e · M4 E6→E4a→E4b→E5/E3a→E3b/E3c/E7, CN · M7 T7.0 (#152), S7.1 (#155), S7.2–S7.9 · M2 evidence #150 (the M4 continuity rows read it) | Always first. Before S6 opens, keep open product PRs few: S6 needs them merged or parked |
| **P1: OB gaps** (need a contract: see `FABLE_FINAL_RUN.md` item 7) | OB-a saved-patch round-trip test across S5/S6/E3a/E5 · OB-b Pi install and launch refresh after S6 (one script plus `docs/INSTALL.md`) · OB-c T6.8 device-free regressions (MIDI to CV, ASIO list, panic and buffer gaps) and the 4 unverified items in `KNOWN_ISSUES.md` · OB-d list of bundled patches to rebuild after M7 | File these when the contract exists. Until then, nothing |
| **P2: finish what is open** | M6 MT1 (#153) to merge or park (it must be gone before S6) · M5 PV2b→PV3 only as M4 needs them (sidecar lane, after TR1e) · M3 RL (Reload engine) | Finish the work in flight. Open no new M6 task |
| **P3: future facts, idle builders only** | M10 S1–S6 · M12 P0 | Only when no P0–P2 task is ready for that builder |
| **P4: parked until OB1** | M6 MT2–MT5 · M3 MB1–MB3, V1, T1.5, TR1h/TR2/TR3 · M5 PV4–PV5 · M8 · M9 · M10 beyond batch 0 · M11 · M12 beyond P0 · CI1 beyond what is open | Do not file. M8–M12 cannot start before M4 anyway |

**V1 (native v1 removal) stays parked** until OB-a proves the owner's saved patches load without it
(CONSTRAINTS "Fixed": the owner's saved patches keep loading).

Signed: claude-architect (owner-directed), 2026-11-17
