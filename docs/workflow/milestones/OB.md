<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB — the Owner Build: a Wirescape the owner uses alone on the Pi 5

**Revision:** r2 (adds OB-e module census/smoke, OB-f UI smoothness; nothing in flight stops) — r1 **ACCEPTED by the Claude Architect, 2026-11-17 (ET).** Design: `proposals/0017`
section 4 and section 6, [PRIORITY.md](../PRIORITY.md). Windows is second; the web build is not in it.
**r2.1 (Architect, 2026-11-17, inbox A10):** OB-c's six owner-reported cases get the device-free oracles in CURRENT "Decided 2026-11-17 23:40 ET". A test that fails before its fix lands as a strict expected failure. Wall-clock gaps are recorded as facts, not as pass marks. Affects OB-c only.
**r2.2 (Architect, 2026-11-20, inbox A19):** OB-a3 pins: "older shape" = native patch `version` 1; backup `<filename>.bak-v1` (then `.bak-v1.<n>`, n ≥ 2, never overwritten; equal bytes → no write); written before the original is replaced, save refused if it cannot be; Save As never writes the source; the existing `<stem>.v1<ext>` naming is replaced in the OB-a3 PR; native loaders stay execution-only with one no-write test each. Full text: #287. Affects OB-a3 only; nothing in flight stops.
**r2.2a (Architect, 2026-11-20 13:20 ET):** pin 4 "Save As never writes the source" forbids writing the source as a **side effect**. A path the user explicitly chooses in the save dialog is the destination, even when it is the opened file. It gets pins 2–3 if it is v1, otherwise the existing atomic replace. No same-path refusal. Found by the desktop suite: such a refusal breaks `refused-draft-files.spec.cjs` (#298). Affects OB-a3 only.
**r2.3 (Architect, 2026-11-20, inbox A23):** OB-f2 targets, set from `facts/app/ui_cpu_rank_2026-11-20.md` (CI Linux, CPU-ranked winner `scene-03-black-ice-choir.json`). Per row (knob, module move, cable draw, telemetry), rAF interval p95 ≤ 17.5 ms and max ≤ 33.4 ms; native `setParam` send→ACK p95 ≤ 5 ms. OB-f1 at `cde8602` already meets every target (p95 16.7, max 16.8, ACK p95 2.1 ms). So **no OB-f2 fix task opens**. Acceptance item 6's CI half is re-checked once on the OB1 candidate by the existing OB-f1 advisory. Headless rAF is vsync-capped, so the Pi session's "no visible stutter" stays the deciding check. A row that fails at the OB1 candidate opens one `apps/studio/` fix with a before/after row. Affects OB-f2 only.
**r2.4 (Architect, 2026-11-21, owner request, inbox A26):** adds OB-g (I/O endurance and triggered envelopes; design `proposals/0019`) and acceptance item 7. Nothing in flight stops. OB-g1 can start now under the S6 window (`bench/` only). OB-g2–OB-g6 and OB-g7's lab half wait for S6 to merge and use post-S6 paths.
**r2.4a (Architect, 2026-11-21, owner: "runner tests affirm, never restrict"):** OB-g runner results (`pi5/*` and hosted soaks) are **advisory everywhere**. They never block a task, a dispatch or a merge. A failure files one fix row that runs in parallel. Acceptance item 7 is **recorded, not required**. Every OB-g task except OB-g1 may be **drafted now** on its branch and rebased after S6. Only merging waits for S6. OB-g6 no longer depends on OB-g5. OB-g4 needs no OB-g1 merge before drafting. Q24 is answered A.
**r2.4b (Architect, 2026-11-23, run 8):** three changes, each affecting only the named task.
- **OB-g4** is drafted as [wirescape-pi #20](https://github.com/kalharbi11/wirescape-pi/pull/20). Step timeout = tier + 10 % + 60 s for engine start-up. Nightly lanes are `osc-heavy/still`, then `osc-gates/still`, with `mixed/still` first once OB-g2 merges. The `io-soak-alsa` tier is deferred until a lab harness profile opens an ALSA port (Q24).
- **Item 7:** `config-edits` is recorded at **L0** until M4 E5. The harness requires a pass below every tier, so a pre-E5 `xfail` cannot climb. After E5 it climbs like `still`.
- **New OB-g8** ([#326](https://github.com/kalharbi11/wirescape-lab/issues/326)): `osc-heavy/still` failing L0 is a `still`-mode I/O defect, so 0019 §5 "fixed now" applies. The lead releases it to a free lane.
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

### r2.4 additions (Architect, 2026-11-21): OB-g I/O endurance and triggered envelopes
Design and thresholds: `proposals/0019`. Every profile, ladder tier and stop rule is defined there.

| Task | Class | Allowed paths | Depends on | Merge |
|---|---|---|---|---|
| **OB-g1** OSC endurance harness: `bench/io/` driver over the null-audio sidecar and localhost OSC, profiles `osc-gates`, `osc-heavy`, `osc-stress`, `still`/`config-edits`, ladder L0–L5, stop-and-report files; self-test against a fault-injected run (kill, dropped packet, stuck gate) | B | `bench/io/**` (new), `facts/perf/` (results) | none: **file now** (bench only during S6) | lead |
| **OB-g2** injected MIDI source and counters: a device-off scripted MIDI backend selectable in the engine (uses `midi::Host`'s injected-backend path), a release-panic counter in `Host::deliver`, counters exposed through diagnostics; profiles `midi-m8`, `mixed` | B | `native/control/midi_host*`, `native/io/midi/` (test backend), engine flag, tests, `bench/io/` | S6 merged; OB-g1 | lead |
| **OB-g3** MIDI endpoint change while running (W4): failing device-off test first for "enabled input dead until relaunch" through the Studio toggle path, then the fix in the file the test names | B | test in `native/` or `apps/studio/` tests; fix where named | S6 merged | lead |
| **OB-g4** Pi tiers: wirescape-pi task `io-soak profile=<p> tier=<L>` with timeout = tier + 10 % (+ 60 s start-up, r2.4b), and one nightly cron that requests the next tier at main's head (0019 §3). **Drafted:** [wirescape-pi #20](https://github.com/kalharbi11/wirescape-pi/pull/20) | B | wirescape-pi only | OB-g1 | **owner** (Architect-only repo) |
| **OB-g5** ADSR trigger mode: `mode` (Gate default / Trigger) and `hold`; Gate mode bit-identical (goldens unchanged); retrigger from current level; panel controls | B | ADSR module folder, its tests, its panel JSON | S6 merged | lead |
| **OB-g6** MIDI to CV `trig` output: 1 ms pulse per accepted Note On per voice, legato included; Notes to CV too if it shares the voice code | B | MIDI to CV (and Notes to CV) folders, tests, panel JSON | S6 merged (merge only; draft now) | lead |
| **OB-g8** (r2.4b) `osc-heavy/still` L0 fix ([#326](https://github.com/kalharbi11/wirescape-lab/issues/326)). First, a bounded device-off failing test below the harness: 64 addresses at 200 Hz into the OSC service, plus a numbered gate sentinel, with the gate fall asserted within 50 ms and the route `dropped` count asserted 0. Then the fix in the stage the test names. The profile, the 50 ms rule and the drop rule stay unchanged | B | test under `tests/`; fix in `host/net/` or `engine/control/` as named | S6 merged | lead |
| **OB-g7** scheduled hosted soak: Linux L0 per PR touching I/O; Windows and Linux hosted L0–L2 nightly on main (GitHub-hosted only) | B | `.github/workflows/` (SR17 order), `bench/io/` | OB-g1, OB-g2 for MIDI profiles | lead |

**Added to acceptance:** 7 (**recorded, not required**, r2.4a). At the OB1 candidate, record Pi `osc-heavy` and `mixed`
in `still` mode through L2 (1 h), and `config-edits` at L0 until M4 E5 (r2.4b; 0019 §6). A failing row files a fix and never holds the tag.

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
