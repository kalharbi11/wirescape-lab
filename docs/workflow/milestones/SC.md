<!-- SPDX-License-Identifier: GPL-3.0-only -->
# SC — scripts and OSC features

**r1 (Architect, 2026-11-26, run 50; transcribes Planner run 2b, [`proposals/0025`](../../../proposals/0025-player-osc-scripts-tools.md) §4, §6.3, §8 and §9, final).**
The design is 0025 §4. This contract adds only tasks, paths, writers, evidence and merge rules. A question
0025 does not answer goes to the [inbox](../ARCHITECT_INBOX.md); it is not settled in a PR.

**Scope.** OSC In row labels, kind toggle, generic defaults (In and Out), the per-row indicator, the
script runner in desktop, bundle export, the tool host (design first), auto-sync and script controls. **OSC
In features are unfrozen by 0025.** The runner and helper are developed in `wirescape-headless` (H-10); the
lab vendors them (SC3). The Player is not in this contract (`wirescape-headless`, 0025 §6.2).

## Invariants (every SC PR)
- **S1 Old patches byte-identical.** `label` is written only when set; no new key is required; the engine's
  config-less OSC In fallback keeps its bytes until OB-h6 shows that no patch relies on it (0025 §4.2).
- **S2 Patches never need a script.** `ui.scriptLinks` is Studio-only; the engine and the Player ignore it;
  a patch with or without a link runs identically (§4.4).
- **S3 Realtime.** Indicator counters are counted on the OSC worker at match time; no payloads, no
  allocation, locks or I/O on render or in the MIDI callback.
- **S4 Linked rows are read-only; unlink, never merge** (§4.4). Rows are never shifted or deleted by sync.
- **S5 Scripts run with the owner's rights,** only from the workspace or a bundle's `scripts/`, never from a
  network path (§4.5).
- **S6 Vendored runner.** `apps/desktop/scripting/` changes only by a deliberate bump PR carrying a
  `VENDORED_FROM` line with the headless commit; no local edits.

## Tasks
| # | Title | Paths | Done when | Lane, after | Merge |
|---|---|---|---|---|---|
| **SC1** | OSC In `label`, kind toggle, generic defaults (In and Out) | OSC In config parsing (`label` known), `apps/studio/src/app/OscEditor.ts`, `OscOutEditor.ts`, presets, Studio tests, `modules/osc_in/README.md` | §4.2 except the indicator: `/ws/knob/1…8` default rows written explicitly; `/ws/out/<n>` defaults for new OSC Out only; Pico and TouchOSC built-in presets; old patches byte-identical (S1) | B1, after OB-h5 #603 | lead |
| **SC2** | Per-row indicator | `host/osc/`, `host/sidecar/` (status), schema, spec, Studio row list, tests | §4.2 indicator: `status.osc.routes[i].rows` (≤8 `{received, ageMs}`), four colours; counters on the worker (S3) | B2, after P1-e [#672](https://github.com/kalharbi11/wirescape-lab/issues/672) | Claude contract review |
| **SC3** | Runner in desktop | `apps/desktop/scripting/` (vendored), `apps/desktop/main.ts`, `preload.ts`, tests | `wsrun.py serve` supervised by main over NDJSON stdio; Python discovery with a clear missing-interpreter message (S6) | B1, after headless H-10 merges | lead |
| **SC4** | Bundle export | Studio export, `apps/desktop/main.ts` (folder write), tests | writes `patches/`, `player.json` (one entry per patch, macro pages, scripts from links) and `scripts/`; passes headless `python -m player check` | B1, Stage 2 | lead |
| **SC5** | Tool host and Python editor | per the §8 decision | §8 boundaries: 0015's panel sandbox, another permission profile; Studio only; owner-approved local pages | Stage 3; **design first**, waits on the §9 trigger (H-10 exists) | Claude contract review |
| **SC6** | Auto-sync | Studio OSC In editor, `ui.scriptLinks`, tests | §4.4 rules, each with a test: rename, add, remove, 9th row, unlink | after SC3, SC5 | lead |
| **SC7** | Script controls in the generic panel | Studio panel, tests | §4.3 control types drawn by the 0015 generic panel | after SC6 | lead |

**Writers.** SC1, SC3, SC4, SC6 and SC7 are Studio and desktop work in B1 after its MM chain; SC1 shares
`OscEditor.ts` with OB-h5 and goes after it. SC2 is B2 after P1-e (same files).

## Evidence on every SC PR
Exact-head Lab CI green; Studio unit and Playwright suites green when Studio changes; for SC2, the schema,
spec, generated files and fixtures are updated, and the default status bytes are unchanged when no OSC In
is present. No golden change.

## Acceptance
SC is accepted when SC1–SC4 and SC6–SC7 are merged with their evidence. SC5 is accepted against its own
design note.

## What would overturn this
0025 §4.6, unchanged: fragile label matching → a stable `key` per output; read-only rows block real work →
per-row detach; audible loopback jitter (a facts row) → timestamped bundles before graphics.

Signed: claude-architect, 2026-11-26
