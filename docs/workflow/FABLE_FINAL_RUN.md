<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Fable's final run: packet (prepared 2026-11-17 ET)

The owner is retiring the Fable seat after this run. A Claude (Opus) session becomes the
**Claude Architect** and holds the design seat from then on. Items are ranked. Each has evidence
and a recommended answer, so a ruling can be "yes", "no" or a change. Line refs are against
`main` at `bc75afa`. `native/engine2/engine2.cpp` is still one file.

## A. Succession (decide first; it changes what the rest of this packet needs)
**1. Reserved authority after Fable.** `CLAUDE.md` reserves for Fable: new proposals, the meaning
of a measurement, invariants, gate thresholds and tolerances, `0012`, panel and patch formats,
protocol versions and realtime ownership. Open reserved items with no QUESTIONS entry
(CURRENT, Fable run 2): the Sub-patch note, M9 r2 state carry, the M12 P0 live-panel limit,
T4.2 smoothing, and the build page (T6.3). Also reserved: the tolerances in `0016` R4 and M10 X4.
*Recommend:* hand all of them to the Claude Architect, under the same evidence rules. Fixed
CONSTRAINTS stay with the owner. Rewrite the deputy section of `CLAUDE.md` into an Architect section.

## B. Engine rulings M4 needs before its builders start (from the engine code, not from the notes)
**2. Host packets and `panic` (before M3 TR1e).** `panic` increments `generation` (`engine2.cpp:966`).
`collect` drops packets from an older generation and packets older than the node's
`born_revision` (`:481`, `:483`, `:501`, `:503`). It also drops when `future` is full (`:493`).
Transport (`0008`), the live mod amount (M4 E6) and data blocks (`0005` §6) all travel this way.
After a panic, a change the sidecar already acknowledged is lost, which breaks `0008` K4. A data
block also leaks, because `pop_egress` filters its return by generation (`:953`).
*Recommend:* one host-state packet class that skips the generation and born filters. Data blocks
are freed through a per-slot acknowledged-serial atomic, not through the egress return.
**3. Revision stamp and adoption (E4b).** Today the edit pause makes `0005` assumption B2 true.
Under E4 the audio thread adopts a new layout up to 3 blocks after it is published. In that window
a note can reach the old instance or be dropped by the new one.
*Recommend:* the audio thread stamps routed packets with `adopted_revision`, and packets newer
than that wait in `future`. This changes event ordering, which M4 lists as an escalation.
**4. Who calls `latency_frames` without the pause (E4b).** Today the control thread calls it on
live instances during replan (`:1259`). Replan also prunes removed routes, hands over
`replan_chokes` and swaps the telemetry values while the audio thread is parked
(`:1211-1259`). `0005` §5 does not give these work items an owner.
*Recommend:* the audio thread samples it in the block where it adopts the layout and publishes
it through an atomic. The other work items travel in the layout and are applied when it is
adopted (builder work, with tests).
**5. Duplicate modulation cables (E6).** Once the amount leaves the edge's identity, two
modulation cables between the same ports collide. The loader does not refuse them
(`runtime_patch.cpp:74`).
*Recommend:* refuse them in the loader and in `connect`, after a grep shows no bundled patch has one.
**6. M4 r2, mechanical.** (a) Put M4's sidecar tasks (E6, E3a, E5, E7) into the
PV2b → TR1h → PV3 lane, and put E7 after PV3. Both touch the device handlers, and E6 moves
`setModAmount` from swap to live. (b) Make E6 create an `EdgeState` (the cable-state split that
`0007` lacks). (c) Bring Groove `tempo_source` (added by TR2) into E3b's scope. (d) Make PV3 list
`setData` and the swap-to-live change, or M5 acceptance trips on them. (e) Add test notes: the
injectable clock (`null_sink_wait.h`) for G3, an allocation-counting hook around `render` for
G1/G7, a fake device backend for E7, and a cap of 2 generations per ID during a replace (P5).
*Recommend:* accept as M4 r2. The Architect can write it if Fable agrees in one line.

## C. The Owner Build (see `PRIORITY.md`)
**7. OB contract.** No contract defines a build the owner can use. These needs have no owning task:
- the owner's saved patches round-trip across M1 S5/S6, E3a and E5 (only the bundled patches have golden renders);
- the Pi install and launch path after the S6 rename (T6.7 is "later");
- T6.8 regressions, plus the 4 unverified items in `KNOWN_ISSUES.md`;
- rebuilding the bundled patches after M7.

V1 (removing native v1) has no migration for the owner's patches.
*Recommend:* a small OB contract with OB-a to OB-d (class A/B), OB0 and OB1 tags, and V1 held
until OB-a passes. Accepting the OB0/OB1 definitions in `PRIORITY.md` is enough. The Architect
writes the contract.

## D. Errata in 0012–0016 and M6–M12 (mechanical unless noted)
**8.** Rule which side wins, or let the Architect fix them in one errata PR:
- (a) `0012:214` says the `0016` matrix covers 32–96 kHz, but T2 tests only 44.1, 48 and 96 kHz.
- (b) The ID regex at `0016:96` is looser than the one at `0012:283`.
- (c) `0015` A2 asks for larger `BLOCK` records, but `0012:269` freezes them at 4,096 bytes. *Format: Fable.*
- (d) `0012:94-96` refuses an unknown config key, but M8 W3 says old patches load unchanged. A migration rule is needed. *Patch format: Fable.*
- (e) `0014:116` has Transport's panel call `setTransport`, which exists only in the custom-panel API (`0015:245`). M11 K3 should depend on M12 P3.
- (f) `0012:172` shows an unknown category as "Other", but the `0014` list has no `other`.
- (g) The M6 mutant rule "every other test unchanged" cannot hold. It needs a named set of unaffected tests.
- (h) The `metrics.py` imports clash with "numpy optional" in M6.
- (i) M8 H3a lacks the `audio.in`, `midi.out` and `stream.out` bindings.
- (j) M8's `ws2_` grep conflicts with `abi_ws2.h` staying in place.
- (k) Missing edges: K4 needs M12 P2, and P6 needs C3.
- (l) M10 tests only refusal rules 1–3 of 6.

*Recommend:* Fable rules on (c) and (d). The rest goes to the Architect as errata.

## E. Worth Fable's deeper thought, if usage remains
**9.** Cost of a transition on the Pi. The null sink never underruns, so no CI number shows the
cost of an E5 fade or an E4 transition. *Ask:* should M4 add a worst-block-cost row (two
instances alive), with a threshold set from the S-facts?
**10.** Daisy-class memory against the `0012` header and `0013` compiler: byte-identical output
across platforms, and detecting portable-tier symbols on Windows. Only an outline is needed now;
M10 is far off.

Signed: claude-architect (owner-directed), 2026-11-17
