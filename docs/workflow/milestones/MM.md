<!-- SPDX-License-Identifier: GPL-3.0-only -->
# MM — macros and mapping in Studio

**r1 (Architect, 2026-11-26, run 49; transcribes Planner run 2a, [`proposals/0024`](../../../proposals/0024-test-repo-macros-modules.md) §3, §5.3 and §8.1, final).**
The design is 0024 §3. This contract adds only tasks, paths, writers, evidence and merge rules. A question
0024 §3 does not answer goes to the [inbox](../ARCHITECT_INBOX.md); it is not settled in a PR.

**Scope.** Studio's macro and mapping layer: one model for macro, CC and OSC mappings, the Mappings
panel and map mode. **No engine, host, SDK or schema change is in scope.** The Macro module itself is
`wirescape-test` MOD-5 and reaches the lab through a B4 promotion (M3 stage MB, PROMO-n). The node-cap
measurement is MM-f (facts only; the cap stays 64).

## Invariants (every MM PR)
- **I1 Live edits only.** A range edit is `setParam` (base) and `setModAmount` (amount). No range edit
  sends `loadGraph` or `applyGraph`. A new mapping or a removal commits as one `applyGraph`, and a
  refusal leaves the document unchanged (0024 §3.2, §3.7).
  - **A101 (Architect, 2026-11-26, inbox B1-MM1-ack, within 0024 §9.5): partial ACK.** An
    `applyGraph` ACK that carries any `unapplied` parameter event counts as a refusal of that mapping
    commit.
  - Studio sends one compensating `applyGraph` of the prior document state, then restores that state
    in the model and shows the refusal text.
  - There is no correlated per-event live compensation: one code path. If the compensating
    `applyGraph` is also refused, Studio reloads the engine's last acknowledged document.
  - Tests: a fake ACK with one `unapplied` event leaves the document byte-identical, with exactly one
    extra `applyGraph` and no `setParam` or `setModAmount`.
- **I2 One owner per parameter** (§3.3); ordinary modulation cables still add under D7.
- **I3 Patches stay self-contained.** Mapping helpers are Studio-only `ui` keys (`ui.mappingNodes`);
  a patch without them loads, renders and saves byte-identically to today (§3.5). Macro names live in the
  Macro module's `labels` data, never under `ui`.
  Writers always send all 8 `labels.rows` (the record is fixed-length; the pinned renderer refuses fewer);
  an empty name shows the default (Architect, 2026-11-26, from wirescape-test #12).
- **I4 setParam-only targets are not mappable** and are dimmed with the §3.4 reason.
- **I5 Node budget.** Mapping nodes and Macro pages count against the sidecar's 64 nodes; map mode
  refuses a mapping that needs a 65th node, with the reason (§3.5).
- **I6 Existing CC Learn mappings keep their base and amount** (§3.3). Only new learns take the full range.
- **I7 One undo step per edit**, including page delete with its mappings.

## Tasks
| # | Title | Paths | Acceptance | Lane | Depends | Merge |
|---|---|---|---|---|---|---|
| **MM1** | Mappings model: derive mappings from the document; ownership; range edits as transactions | `apps/studio/src/**`, Studio tests | Node and Playwright tests for §3.2–§3.3: `min` sends `setParam` then re-sends the amount, `max` sends `setModAmount`, neither sends `loadGraph`/`applyGraph` (I1); a second owner is refused with the §3.3 text; a new mapping is full range, and a Macro knob with no other mapping is first set to the target's value; removal sets the base per §3.3 in one undo step; negative amount shows an inverted range | B1 | none (`FakeEngine` declares `essentials.macro` per §3.1 until PROMO) | lead |
| **MM2** | Mappings panel; hidden mapping nodes and cables; greyed targets; node budget | `apps/studio/src/**`, styles, Studio tests | §3.5–§3.6; `nodes n/64` and the 65th-node refusal (I5); "Show mappings" draws dashed cables; a patch without `ui.mappingNodes` is byte-identical on load and save (I3) | B1 | MM1; PROMO of Macro for the `RealEngine` path (the `FakeEngine` path may merge first) | lead |
| **MM3** | Map mode; CC Learn's full-range default | `apps/studio/src/**`, Studio tests | §3.7 and §3.4 dimming (I4); a newly learned CC sweeps the full range while earlier mappings keep theirs (I6); OSC learn through `telemetry.monitor` on a hidden Monitor | B1 | MM2 | **Claude contract review** (changes CC Learn behaviour) |
| **MM4** | Map mode's CC and OSC learn use the controller stream | `apps/studio/src/**`, Studio tests | no hidden Monitor once the stream capability is advertised; shapes as Gate P1 (e) fixes them (Planner run 2b) | B1 | Gate P1 (e) merged | lead |
| **MM-f** | Facts: 64 vs 128 nodes with idle mapping nodes; memory and worst block; Pi and hosted | `facts/`, `bench/` | numbers with commit, machine and date (hosted timings are diagnostics); the Pi rows come from owner-run zips (A31 interim); **no cap change** | B3 | none | lead |

**Writers.** MM1 → MM2 → MM3 → MM4 is one Studio writer chain in B1. It shares `apps/studio/src/app/`
files (`App.ts`, `ccLearn.ts`) with B5 #545 and the OB-h2 Studio Host field; the PR that merges second
rebases (SR21: split, don't wait).

## Evidence on every MM PR
Studio unit and Playwright suites green on the exact head; `npm run build` green; the CC Learn and
E3c data tests unchanged unless the row names the change (MM3 only). No golden, catalogue or protocol
fixture changes.

## Acceptance
MM is accepted when MM1–MM3 and MM-f are merged with their evidence on the merged head. MM4 follows
Gate P1 (e) and is tracked as an open row after acceptance.

## What would overturn this
0024 §3.8, unchanged. A second-owner request, an unmusical end step, a costly Macro page or a too-small
node cap goes to the inbox with its evidence; the fix named there is applied under its own task.

Signed: claude-architect, 2026-11-26
