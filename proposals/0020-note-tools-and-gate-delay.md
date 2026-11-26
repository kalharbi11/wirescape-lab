<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0020 — CV to Notes, Poly Merge, Gate Delay; S6 writer and S0 ruling

Claude Architect, 2026-11-22. Owner decisions, from chat answers on 2026-11-22 (inbox A28).

## 1. Order of work
S6 comes first: everything below adds folders under `native/modules2/`, which S6 moves.
After S6, in this order:
1. ADSR trigger mode, OB-g5 #316 (`0019` §4).
2. CV to Notes.
3. Gate Delay.
4. Poly Merge (owner, 2026-11-22: last).

All three new modules may be **drafted now** on their own branches, so the owner can build and
play them early. They **merge only after S6**, rebased onto the mapped paths. A new folder before
S6 would break S6's frozen 446-file map.

**Experimental tier (owner: "be loose with protocols, I want to get to testing").**
- The three modules are marked experimental in their README.
- Each PR needs:
  - green Lab CI;
  - its own unit tests (device-off);
  - unchanged goldens, since the modules are new and not in the golden set;
  - the realtime rules.
- No M7-style numeric targets, no Claude contract-review, no facts file. The lead merges.
- Parameter names and ranges may change freely until the owner promotes a module. No patch-
  compatibility promise until then.
- Still binding: no workflow-file edits, no heap or OS use in process, and SR rules.

## 2. CV to Notes (`essentials.cv_to_notes`)
The inverse of `notes_to_cv`. Poly-only by design; Poly Merge does the combining.

**Inputs**
- `pitch` (poly, 1 V/oct, 0 = C4)
- `gate` (poly)
- `velocity` (poly, 0..1; unconnected = 0.8)

**Output:** `notes` (event).

**Per channel**
- A gate rise (threshold 0.5) sends NOTE_ON. The key is `round(60 + 12·pitch)`, clamped to 0–127,
  and is latched with the velocity.
- A fall sends NOTE_OFF for the latched key.

**Parameter:** `legato` (Off by default). When On, a key change while the gate is high sends off
for the old key, then on for the new key.

**Behaviour**
- Note identity is (module, channel), so OSC Out `notes` and Chord receive stable on/off pairs.
- Reset, CHOKE and Panic send NOTE_OFF for every held key, then clear.

Use: OSC In chords → CV to Notes → OSC Out `notes` (LED strip), and → Chord.

## 3. Poly Merge (`essentials.poly_merge`)
- Inputs `in1`…`in8` (mono; FIRST); one poly output `out`.
- Lane n carries `in n`.
- The channel count is the highest connected input. If the module cannot see connection state,
  a `channels` parameter (1–8, default 8) sets it.
- Unconnected lanes output 0.

Use: separate OSC rows (one note per row) → one poly cable. That cable feeds a VCO, ADSR,
Gate Delay or CV to Notes.

## 4. Gate Delay (`essentials.gate_delay`): start basic, musical

It is poly in, poly out. A mono cable is one lane. It covers gates, trigs and modulation sources.

**Inputs**
- `in` (poly)
- `cv` (poly, optional pitch lane)
- `time_cv` (mono, adds ±1 V = ±1 s to `time`)

**Outputs**
- `out` (poly)
- `trig` (poly; a 1 ms pulse at each delayed rise)
- `cv_out` (poly)

**Parameters**
- `mode`:
  - **Gate** (default): each rising and falling edge of `in` (threshold 0.5) is replayed after
    the delay, so gate length is kept and a trig stays a trig. The delay is latched at the rise.
    Modulating `time` moves start points without disturbing waiting notes. `cv_out` is `cv`
    sampled at the input rise, released at the delayed rise, so pitch stays with its gate.
  - **Signal**: `in` runs through a delay line, for LFOs, envelopes and CV. To stay heap-free
    on the portable tier, it is sampled at 1 kHz into a fixed per-lane buffer (2 s × 16 lanes)
    and read back with linear interpolation. `trig` then fires on delayed rises above 0.5.
- `time`: 0–2000 ms.
- `spread`: 0–500 ms. Lane n gets an extra `n·spread` (strum).
- `strum`: Up (default), Down, Alternate (flips on each new chord, meaning a rise after all lanes
  were low), Random. Random is deterministic, seeded from the reset count, and gives the same
  render each time.
- `humanize`: 0–50 ms of seeded per-event jitter.
- `repeats`: 0–4. Gate mode only; each event re-fires every `time`, for a ratchet or echo.

**Limits:** a fixed edge queue of 64 per lane. When it is full, the oldest pending edge is
dropped and a counter is incremented. Reset clears every queue, and `out` goes low.

**Tests:** delay and length kept; trig in gives trig out; spread order for each strum mode;
repeats count; time latched at the rise; Signal-mode delay of a step within 1 ms; queue overflow
counted; render identical across block sizes in Gate mode.

**Not now:** per-lane time inputs, swing quantised to a clock, probability/skip. Add these after
the owner has played with v0.

## 5. Trigs into envelopes
This is unchanged: ADSR trigger mode (#316) gives trig-friendly envelopes, and MIDI to CV `trig`
(#307) follows. Gate Delay's `trig` output and the ADSR in Trigger mode together form the
Eurorack-style path.

## 6. S6 writer and the S0 snapshot
- Codex cloud cannot resolve github.com for Git, so it cannot apply, build or replay. Local
  Codex is low on usage.
- **The S6 sole-writer slot moves to one Claude builder (`claude-builder1`) in a cloud session**,
  on the same #294, branch `task/294-m1-s6` and PR #295. It continues from B4's
  `lab/s6_handoff/` plan and `s6-active-consumer-gaps.json`. gpt-builder4 stands down from S6.
- The independent contract-review is done by the Claude Architect, which does not write S6.
- **S0 ruling.** On the unchanged baseline, `abi2_sidecar_snapshot_tests` failed on the owner's
  local Windows/MSVC build: 997 bytes against 469. The snapshot holds the full first status
  message, including the host's audio, MIDI and OSC state, so a different local machine gives a
  different message.
  - This is not an S6 defect and not a reason to change the snapshot.
  - Hosted CI is the authority, and the test must pass there before and after S6, unchanged.
  - The local Windows mismatch is a known issue.
  - **Overturned by** the same test failing on hosted CI at the S6 base.

## 7. After S6: new modules and the frozen M1 checks (Architect, 2026-11-22, run 7)
The first module drafts (#325, #333, #334) each fail checks that froze the M1 tree. The new code
is not at fault: `0006` I7 froze the catalogue *for the migration*, and the inventory counts
assume exactly 34 modules. M1 is now complete, so these are the rules for module PRs:
- **S0 catalogue snapshot** (`host/sidecar/testdata/s0_catalogue.ndjson`). A PR that adds a
  module or a public parameter regenerates this file in the same PR, using the generator the test
  already uses. The PR shows that the diff changes only that PR's own module entry or entries.
  Every other byte stays identical. A diff that touches another module's entry, or anything in
  `s0_status.ndjson`, is a defect. The test and its assertions stay unchanged.
- **Module counts** (`bench/golden/inventory.py`, the T0.11 coverage in `bench/gate/instructions.py`,
  and any other hard-coded 34). Replace the bare count with the 34 golden-set module IDs plus an
  explicit `EXPERIMENTAL` list. Each module PR appends its own ID. The golden set and its 24
  renders stay unchanged and must stay identical. A module that is in neither list still fails.
  The first module PR to merge makes this change; later PRs only append. These are `bench/` files,
  not workflow files.
- **Instruction counts (M1 paired job).** A row that exists only at the head, for a module on the
  `EXPERIMENTAL` list, is reported as `new` and not compared. If `bench/m1/paired.py` rejects such
  a row, it gets that one narrow exception, with a test. Every existing row stays strict at 1 %.
- **Changing an existing module (#325 ADSR).** The new mode must not make existing patches
  costlier. The +1.62 % / +1.38 % (x64) rows on `basics-01-first-tone` and `osc-out-01` are a
  defect to fix in #325, for example by choosing the mode once per block and keeping the default
  Gate path as it was. Do not widen the tolerance. Until #325 is within 1 %, the next module PR
  that is green may merge ahead of it (SR19). Otherwise the order in §1 stands.

- **Inlining noise from the shared catalogue TU (Architect, 2026-11-23, runs 15–16).** Every
  module's SDK-wrapper code generation depends on the whole catalogue translation unit. Adding
  Gate Delay made LFO +2 % on x64 with identical DSP Ir. Pinning one SDK helper (SDK-1) only moved
  the cost to other modules. The fix is **CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358):
  one translation unit per built-in module**. Until it lands, a module PR may merge with a
  *named, bounded* exception: the specific rows the Architect lists, a stated ceiling, and
  measured DSP-identical attribution. It expires at CAT-1. No general tolerance change.

Overturned by: a regenerated catalogue that cannot be limited to the PR's own entries, because of
ordering or a shared header. The Architect then rules on the snapshot format.

Signed: claude-architect, 2026-11-22
