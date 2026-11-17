<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB — the Owner Build: a Wirescape the owner uses alone on the Pi 5

**Revision:** r2 (adds OB-e module census/smoke, OB-f UI smoothness; nothing in flight stops) — r1 **ACCEPTED by the Claude Architect, 2026-11-17 (ET).** Design: `proposals/0017`
section 4 and section 6, [PRIORITY.md](../PRIORITY.md). Windows is second; the web build is not in it.
**Outcome:** two tagged builds. **OB0** (before the M1 S6 rename): Studio edits stop reloading the
whole patch, plus the first sound fixes. **OB1**: edits never restart the patch (M4), filter and
CHOKE fixes, and the owner's saved patches still load, render and save without loss.

## Tasks
| Task | Class | Allowed paths | Depends on | Merge |
|---|---|---|---|---|
| **OB-a1** CI round-trip: every bundled patch plus one synthetic patch per module config shape: load, save, load; compare the normalised document and a render hash. Runs in Lab | B | `tools/patch_roundtrip.py` (new), `native/tests2/` (new test only), `tests/fixtures/patch_shapes/` (new), `.github/workflows/` only to add the step (SR17 order with CI writers) | none: **file now** | lead |
| **OB-a2** owner runner: same check pointed at a folder (`--dir`), read-only on the input, writes a report to `bench/results/` (gitignored); devices off | B | `tools/patch_roundtrip.py`, `tools/pi/README.md` | OB-a1 | lead |
| **OB-a3** no rewrite on load: a patch loaded from an older shape is never written back by load; its first save writes `<name>.bak-<shape>` beside it first. One test per loader entry point | B | `native/document/`, `native/control/` loader path, `apps/studio/` save path, tests | OB-a1 | lead after **Claude** contract-review (touches the patch format path) |
| **OB-b** Pi install and launch after S6: one script, `docs/INSTALL.md`, a dry-run test that checks paths only | B | `tools/pi/**`, `docs/INSTALL.md` | M1 S6 | lead |
| **OB-c** T6.8 device-free regressions: MIDI to CV, ASIO list while playing, panic gap, buffer-change gap, plus the 4 unverified items in `docs/context/KNOWN_ISSUES.md`. One failing-then-passing test per item; a fix only where the test names the cause | B | tests in `native/tests2/`, `apps/studio/` tests; fixes in the file the test names | regression tests: **now**; fixes after M1 S6 | lead |
| **OB-d** list of bundled patches whose sound changes after M7 batch 2, with before/after render hashes; rebuild each, owner listens | A then B | `facts/sound/ob_d_patches.md`, `patches/` | M7 batch 2 | lead |
| **OB-tag** tag `owner-build-0` (OB0) and later `owner-build-1` (OB1) on `main`; notes in `docs/RELEASES.md` | A | `docs/RELEASES.md` | the build's row in PRIORITY | lead (tag only, never moved) |

### r2 additions (Architect, 2026-11-17, owner request): the four things the owner needs
The owner's minimum: **sound engine, smooth UI, live editing, every module working.** r1 covered
live editing (M2, M4) and sound (M1, M7). r2 adds the two that had no task. Nothing in flight stops.

| Task | Class | Allowed paths | Depends on | Merge |
|---|---|---|---|---|
| **OB-e1** module census (facts): for each of the 33 `native/modules2/` modules, is it in the Studio palette, in a bundled patch, covered by a test, has a known issue. One table, no opinions | A | `facts/code/module_census.md` | none: **file now** | lead |
| **OB-e2** every-module smoke test in Lab: create, prepare at 44.1/48 kHz and blocks 64/256, render 2 s with default params and a patched input; finite output, no allocation in process, not silent where the module makes sound; parameter sweep min→max without NaN | B | `native/tests2/` (new test), CI step only to add it | OB-e1 | lead |
| **OB-e3** fixes for modules OB-e2 fails, one PR per module, golden unchanged unless the fix is the subject | B | that module's folder, its test | OB-e2 | lead |
| **OB-f1** UI smoothness facts: on the heaviest bundled patch in Studio (Playwright, headless, CI Linux): frame-time p50/p95/max while dragging a knob, moving a module, drawing a cable, and telemetry running; time from knob drag to engine param ack. Builds on `facts/app/ui-attribution-*` | A | `facts/app/ui_smoothness_<date>.md`, `bench/ui/` (new) | none: **file now** | lead |
| **OB-f2** UI smoothness fixes for the worst rows of OB-f1, each with a before/after row | B | `apps/studio/` | OB-f1; the Architect sets targets from OB-f1 (0017 §1 rule 1) | lead |

**Added to acceptance:** 5. OB-e2 green for every module in the palette (a module that cannot be
fixed before OB1 is hidden from the palette and listed). 6. OB-f2 targets met on CI, and the
owner's Pi session finds no visible stutter during the 100 scripted edits.

**Out of OB (P4, do not file):** third-party module drop-in, SDK, dev loop, panels, Daisy/hardware,
protocol publication, web build features (M6 MT2+, M8–M12 beyond facts).

## Invariants
- **B1** No patch file is rewritten by load. Unknown keys load as `0017` section 5(d) rules.
- **B2** OB-a never weakens a golden or a tolerance; a round-trip difference is a defect or a
  question to the Architect, not a declared change.
- **B3** `owner-build-0` stays tagged and installable after OB1, as the way back.
- **B4** Devices off in CI. Only the owner runs OB-a2 on real patches and the Pi session.
- **B5** V1 (native v1 removal) stays parked until the owner's OB-a2 run passes.

## Acceptance
1. **OB0:** M2 E1b-r, M7 T7.0, S7.1, S7.2, S7.4 merged; OB-a1 green; tag on `main`.
2. **OB1:** every PRIORITY OB1 row merged; OB-a1, OB-a3, OB-b, OB-c merged; OB-d done.
3. The owner's OB-a2 run over their real patch folder: zero document or render-hash differences
   not explained by an OB-d entry.
4. The owner's Pi session (last criterion): 100 scripted edits at the owner's buffer size, zero
   xruns (`0017` section 6), with the two CN transition-cost rows reported.
Owner-only items (3, 4) are recorded, never waived; the rest is accepted without them.

## Escalate
A bundled or synthetic patch that cannot round-trip today: file it, do not change the loader in
OB-a1. Any loader change that alters a stored document's meaning. A Pi path that needs root.

Signed: claude-architect, 2026-11-17
