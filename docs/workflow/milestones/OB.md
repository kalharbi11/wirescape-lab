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
**r2.5 (Architect, 2026-11-23, owner D1, `proposals/0021` §6):**
**r2.6 (Architect, 2026-11-23, owner: "postpone Pi testing until we hit the milestone"):** no Pi runs or Pi infrastructure before the OB1 candidate. The engine chain (TR1e → E7) changes what would be measured, so earlier Pi numbers would not describe the build the owner uses. **Postponed:** PI-1 [#369](https://github.com/kalharbi11/wirescape-lab/issues/369) (bridge dispatch/publish), OB-g4 tiers and nightly cron ([wirescape-pi #20](https://github.com/kalharbi11/wirescape-pi/pull/20)), inbox A31 and the interim `wsci` sandbox runs. **Kept, because they inform OB1 tasks and use no Pi:** hosted Lab, Golden and M1 paired on Linux ARM64 (ARM correctness and instruction cost), the OB-g7 hosted soak (advisory), and OB-b's CI dry-run test (the installer is needed at OB1). **At the OB1 candidate:** acceptance 7 (recorded, not required) and criterion 4 (the owner's Pi session) run as written. PI-1 is released only if the owner wants bridge-run Pi rows for acceptance 7; otherwise the owner or an agent on the Pi records them directly.
- Acceptance 2 reads the PRIORITY OB1 row as revised. M4 E3a, E3b and E3c are **OB1.1** and no longer hold the `owner-build-1` tag.
- G-W1 [#368](https://github.com/kalharbi11/wirescape-lab/issues/368) is added to the OB1 rows (lead merge).
- Affects only the tag condition. Nothing in flight stops.

**r2.7 (Architect, 2026-11-24, run 22, A41):** OB-g8 allowed paths gain `host/osc/` and `modules/osc_in/`, because the #386 diagnostic names `Pattern::match`. Affects OB-g8 only; nothing in flight stops.
**r2.8 (Architect, 2026-11-24, run 26, A45/A46):** two r2.1 oracles are corrected to the written design. They affect OB-c only. **P1 (panic gap):** ABI2 `panic()` MUST reset processors (`docs/specs/ABI2_SPEC.md:69`), so a stateless VCO restarts its phase. P1 now gates the reported defect, the gap: block positions run without a missing or repeated frame, 0 overruns, and no capture block after the reset boundary is silent past the reported latency. Bit identity to the no-panic run is reported, not gated. P4's `click_events` row is unchanged. **G1 (Groove stop):** STOP queues to the documented cycle end (`modules/groove/README.md:43`). G1 is now `running` = 0 within one block of that cycle-end frame. START and the external-clock row are unchanged. Neither row gets a tolerance.
**r2.8a (Architect, 2026-11-24, run 27, A52):** P1's "no missing frames" check after the reset is post-reset drone **sample identity** to the reference shifted to a block-boundary origin inside `[b0*block, b1*block + latency]`, with the first mismatch reported per origin. It replaces the sign/direction landmark compare. No tolerance. No identical origin → strict xfail naming the cause.
**r2.9 (Architect, 2026-11-24, run 29, A56/A57; owner: "pull parked work into the plan where it helps"):** (1) **M7 batch 2 is an OB1 row again** (M7 r1.6): S7.5 #291, S7.6 #314 and S7.9 #440 run under the bounded paired-row exception and no longer park behind CAT-1 + MB. Acceptance 2 is unchanged and now consistent with PRIORITY. (2) **OB-g6 Note Trigger #322 is unparked** into OB1 as an *optional* row: B3 resumes it after E5v #439 merges (same module folders), on mapped paths, with the r1.6 bounded rule for paired rows. It does not hold the tag. (3) **OB-d** (bundled patch list after M7) is B4's after S7.9, and it may be drafted from the merged S7.x Results earlier. (4) Gate Delay #333, CAT-1 #358 + MB1 and MT2 #176 stay parked: new-module freeze (R1) and no OB1 need.

**r2.10 (Architect, 2026-11-25, A87, [#578](https://github.com/kalharbi11/wirescape-lab/issues/578#issuecomment-7159042191)):** the OB-f1 candidate recheck runs on the restored advisory workflow `ob-f1-ui-facts.yml` (from `cde8602`, collectors unchanged), dispatched with a full-SHA `ref`. r2.3 targets are unchanged. Owner device-off records (`tools/owner_record.py`, uploaded to #590) are advisory Pi/Windows facts under r2.4a. They never replace acceptance item 4. Affects only OB-f1 and how owner evidence is collected.
**r2.11 (Architect, 2026-11-25, run 45, A88, [#584](https://github.com/kalharbi11/wirescape-lab/pull/584#issuecomment-7176975049)):** the Pi half of acceptance item 6 is two owner evidence items, recorded in one sitting. **6a:** the #579 runner, 100 scripted edits with real audio, 0 xruns and both CN costs; its `visible_stutter` stays null and reads "observed in 6b". **6b:** a witnessed Studio session on the same Pi, candidate SHA, patch and day, with at least 100 hand edits (knob, module move, cable). The owner reports stutter as yes or no, plus any xrun Studio shows. One stutter or one xrun fails item 6. If a failure shows in 6b but not in 6a, one OB-f2 `apps/studio/` fix opens. No same-session bridge and no test-discovery bridge. Affects acceptance item 6 and #579/#584 only.

**r2.12 (Architect, 2026-11-25, owner request "OB1.1 Tier 1", design [`proposals/0022`](../../proposals/0022-ob1.1-headless-readiness.md)):** adds the OB-h rows below, for the headless Pi build: long sessions, heavy OSC in and out, and patch switching. They are **OB1.1**. They are queued in each lane **after the task it is working on now**, they never hold the `owner-build-1` tag, and they may merge before it. The owner lifts the module freeze for OB-h4 Gate Delay only. Tier 2 (0022 §9) is suggested, not filed, and is re-evaluated after Tier 1. Nothing in flight stops.

**r2.13 (Architect, 2026-11-26, run 47; transcribes Planner run 1, [`proposals/0023`](../../proposals/0023-review-and-replan.md) §8.5, final):** (1) **OB1 acceptance stands as written** (owner items recorded, never waived), but **it gates no new work.** (2) **The lab new-module freeze ends when M3 MB2 merges**, not at the `owner-build-1` tag; OB-h4 Gate Delay stays the one exception until then. New modules start in `wirescape-test` (0023 R3.2). (3) **OB-h2 gains gate release** (R2.2 c): on stop, replacement or graph swap, every OSC Out gate or trigger row whose last sent value was nonzero sends 0 once (best effort, counted). Test first: a witness row in the OB-h3 switching test that fails before the fix. (4) **OB-h3's witness gains two rows:** an OSC In route-relisten row (in #610 now) and the OSC Out gate row (added by OB-h2 with its fix, because it cannot pass before it). (5) **Wrap-up holds end for run-1 areas:** OB-h2 #601, OB-h6 #604 and #494 return to their lanes (BUILDERS). Run-2 areas (macros, mapping, OSC In features, scripts, tool host, the new repos) stay frozen until Planner run 2 merges.

**r2.14 (Architect, 2026-11-26, run 49; inbox B2-631-historical-red and B2-601-parser-scope):** (1) **A98, Gate P0 #631 disposition.** B2 may push one diagnostic-only branch based on `48479fc` (never merged, no production edits) that runs the same forced-poll witness as #635 against the old sender and bus. **If it is red there and green on #635's head,** the cause is named (a falling block published low before its fall count), E3c `f8c994c` is the fix, #635 merges as a regression test (lead merge on exact-head Lab green plus a signed Result that links both runs), and #631 closes as fixed by #540. #610 then rebases on `main` and runs its own exact-head gates, heavy tier included; no rerun of the old head and no waiver. **If it is green on `48479fc` too,** the cause is not named: #631 stays open, #635 does not close it, and B2 next reproduces the heavy-tier failure on `48479fc` with the sidecar's edge trace before any repair. Green current-head runs alone never close #631. (2) **A99, OB-h2 #601 paths.** Added to OB-h2's paths: the OSC Out branch and its binary staging in `host/document/runtime_module_config.h`, and OSC Out-only normalization in `host/document/io_data_migration.h` if the red test needs it. Nothing in the CC or OSC In branches (OSC In stays frozen until Planner run 2b merges). v1 authored bytes stay identical; a v1 `host` or an invalid v2 `host` fails closed; no new protocol field, thread or queue; LAN only with `--confirm-lan`. The red-first witness is #638 run 45889339426 (`accepts(v2)`).

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

### r2.12 additions (Architect, 2026-11-25, owner): OB-h OB1.1 Tier 1, headless readiness
Design, rules and oracles: `proposals/0022`. Its §2 rules bind every row: one patch file for every host,
devices off and no LAN in CI, no loosening, and gaps recorded as facts.

| Task | Issue | Lane, after | Allowed paths | Done when | Merge |
|---|---|---|---|---|---|
| **OB-h1** OSC reliability status (0022 §3) | [#600](https://github.com/kalharbi11/wirescape-lab/issues/600) | B3, after its #579 Result | `.github/workflows/ob-g7-hosted-soak.yml` (dispatch input and unpark Linux x64/arm64 `still` nightly only), `facts/perf/` | L0 → L2 lanes run at `main`; one facts file; #326 closed as superseded or #494 unparked, per §3 | lead |
| **#494 A67** enqueue refusal fix (unparked by r2.12) | [#494](https://github.com/kalharbi11/wirescape-lab/issues/494) | B2, before OB-h2 if `still` fails; otherwise after it | as #494 | as #494, with no load, queue or deadline change | lead |
| **OB-h2** OSC Out network destinations, A91 (0022 §4) | [#601](https://github.com/kalharbi11/wirescape-lab/issues/601) | B2, after #540 | `modules/osc_out/**`, `engine/control/osc_out_host.*`, `host/osc/**`, the permission plumbing in `host/sidecar/session.*`, `docs/specs/OSC_OUT.md`, tests; Studio Host field as an SR21 follow-up after OB-h5 | v2 `host` sends only with network permission; `lan-refused` status; two modules reach two loopback destinations; v1 configs byte-identical; **gate release** (r2.13): nonzero gate/trigger rows send 0 once on stop, replace or swap, with the OB-h3 OSC Out gate row failing before the fix and passing after | **Claude contract review** |
| **OB-h3** patch switching witness, A93 (0022 §5) | [#602](https://github.com/kalharbi11/wirescape-lab/issues/602) | B5, after #545 | test under `host/sidecar/` or `tests/`; a fix in the stage the test names | 200-switch test green on both Linux arches plus ASan/LSan; gap and RSS facts recorded; plus an OSC In route-relisten row (r2.13) | lead if test-only; a `host/sidecar/` product fix needs a Claude contract review |
| **OB-h4** Gate Delay (0022 §6) | [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) | B4, after CMP-1 #592 (draft-ahead now) | `modules/gate_delay/**`, catalogue registration, its tests and panel | §6 exception rows listed, each ≤ +3 % with DSP-identical attribution; goldens identical | lead |
| **OB-h5** OSC presets, A92 (0022 §7) | [#603](https://github.com/kalharbi11/wirescape-lab/issues/603) | B1, after #585 | `apps/studio/src/app/OscEditor.ts` and preset helpers, `apps/studio/src/app/OscOutEditor.ts` (preset Save/Load only, A96, run 46), `apps/desktop/main.ts` and `preload.ts` (presets folder only), Studio tests, `docs/specs/OSC_PRESETS.md` | Script preset with the pitch test; save/load round trip; presets carry no network settings; patch format unchanged | lead |
| **OB-h6** patch check tool, A94 (0022 §8) | [#604](https://github.com/kalharbi11/wirescape-lab/issues/604) | B3, after OB-h1 | `tools/patch_library.py`, its tests, `docs/INSTALL.md` (one owner step) | renders a folder offline; table and JSON; exit codes as §8 | lead |

### r2.13 additions (Architect, 2026-11-26, run 47): Gate P0 and the Studio restart policy
Design: [`proposals/0023`](../../proposals/0023-review-and-replan.md) §2 (final). Gate P0 must merge before any
`wirescape-headless` Player build relies on the engine; Player development does not wait for it. Protocol
additions are additive, capability-gated v0 fields (R2.1, SR17). Devices off; test first.

| Task | Issue | Lane, after | Allowed paths | Done when | Merge |
|---|---|---|---|---|---|
| **P0a** render liveness (R2.2 a) | [#619](https://github.com/kalharbi11/wirescape-lab/issues/619) | B5, after OB-h3 #610; `host/sidecar/` after #540 | `host/audio/`, `host/sidecar/` (status), schema, spec, generated files, named status fixtures, tests | `status.audio` block count and `stalled` (500 ms); a spinning test module reads `stalled` within 1 s | **Claude contract review** |
| **P0b** degrade, never exit (R2.2 b) | [#620](https://github.com/kalharbi11/wirescape-lab/issues/620) | B2, after OB-h2 #601 (and #494 if routed) | `host/midi/`, `host/osc/`, `host/sidecar/session.*`, schema, spec, generated files, named fixtures, tests | injected MIDI start failure in poll and a throwing worker keep audio running, report status, restart with backoff; exits 2 and 3 unchanged | **Claude contract review** |
| **RS** Studio restart policy (R2.5) | [#621](https://github.com/kalharbi11/wirescape-lab/issues/621) | B1, now | `apps/desktop/main.ts`, `preload.ts` (banner IPC), Studio banner, tests | 250 ms doubling to 30 s, no limit; non-modal banner after three fast crashes; patch reloads on `hello` | lead |
| **P0c, P0d** | — | — | OSC Out gate release is OB-h2 (r2.13 (3)); #326/#494 routing is OB-h1 | as those rows | as those rows |

Gate P1 (0023 R2.3 e–i: controller input stream, settings fsync and absolute path, SIGTERM, coverage, TR1h) is
filed at Stage 2; (e) waits for Planner run 2's message shapes.

**OB-h acceptance (OB1.1 Tier 1, Architect):** every row above merged or closed with its routing; one owner
overnight run on the Pi with the owner's own patches is recorded (not required, r2.4a style).

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
