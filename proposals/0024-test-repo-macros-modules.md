<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0024 — `wirescape-test`, macros and mapping, the module batch (Planner run 2a)

**Status: final rulings** (`claude-planner`, run 2a; authority in
[`02_PLANNER_RUNS.md`](../docs/context/planner/02_PLANNER_RUNS.md)). The Claude Architect writes them into
contracts, tasks and lanes without reopening them. It flags only conflicts with CONSTRAINTS "Fixed" items,
factual errors (with the source line) and contradictions with run 2b. Run 2b builds on this note and does
not reopen it.
**Read at:** lab `main` `0dc33bf` (2026-11-26 ET); `wirescape-test` `main` `f4cb8f1`. Builds on
[0023](0023-review-and-replan.md) (R2.3 (e), R3.2, R3.3, W1, §7.2) without re-deriving it.
**Order:** facts (§1), `wirescape-test` (§2, question 1), macros and mapping (§3, question 3), the module
batch (§4, question 6), order and tasks (§5, question 8 for `wirescape-test`), the hand-off to 2b (§6),
findings (§7), edits for the Architect (§8).

## 0. Summary
1. **`wirescape-test` is a module workshop pinned to one lab commit.** A stdlib-only script, `wstest`,
   builds a scratch copy of the pinned lab with the module registered. Before MB2 it adds the three
   registration lines; after MB2 it only copies the folder. Nothing is ever committed to the lab from
   there. **T0** runs on Linux on every push. **T1** adds arm64, Windows and sanitizers on ready PRs
   only. **T2**
   is the owner's dispatch: three platforms, the full lab test suite, a rate and block sweep, and
   instruction counts. A module either passes on the SDK as it is or files one lab issue labelled
   `limitation found`. Promotion is a byte copy into a lab PR after MB2 (§2).
2. **Macros need no engine change.** A Macro module turns 8 knobs into 8 outputs. One Macro module is
   one page; a patch has as many pages as it wants. A mapping is a modulation cable that owns its
   target's base:
   - `min` is the base;
   - `max` is the base plus the amount;
   - both edits are live (`setParam`, `setModAmount`), so no edit rebuilds the graph.

   Macro, CC and OSC mappings share this one model, one Mappings panel and one map mode.
   - Stepped targets round in the engine.
   - setParam-only targets are not mappable in the patch: the Player maps them in `player.json`.
   - There are no curves per target.
   - Mapping nodes count against the sidecar's 64-node cap (§3).
3. **Module batch** (§4):
   - Function Envelope gains Trigger mode, `hold` and `delay`; ADSR gains `delay`;
   - Random, Clock Div/Mult and Rhythm Lanes (the rhythmic modulator, an original design) are new;
   - LFO gains shapes, a division selector and clock and reset inputs;
   - 39 stepped parameters in the 8 batch modules become `STEPPED|MODULATABLE`.

   New tempo-aware modules share one beat clock (a clock input or the transport) and one table of 18
   divisions.
4. **Order:**
   - **Stage 1:** the harness, then the envelopes, Random, Macro, then Clock Div/Mult. The beat clock
     moves into the lab SDK.
   - **Stage 2:** Rhythm Lanes, modulatable batch A, the LFO additions, and the lab's new **MM**
     contract (Studio macros and mapping).
   - **Stage 3:** batch B (§5).
5. **For 2b:** `player.json` addresses a macro as page and knob, patch-independent, or any parameter
   by module and parameter ID. It moves both with `setParam` only (§6).

## 1. Facts this note rests on (checked at source, `0dc33bf`)
- **Modulation (D7).** `effective_norm = clamp(base_norm + Σ amount·cv, 0, 1)`, then the taper; the base
  stays unchanged (`docs/specs/ABI2_SPEC.md:35`). Render: `engine/render.cpp:536-541`. The plain value
  rounds to the parameter's `step` and clamps to its range (`engine/types.h:136-145`). A `STEPPED`
  base jumps instead of ramping (`engine/render.cpp:525-529`).
- **`setModAmount` is live.** One `WS2_PARAM_MOD` packet goes on the control producer's critical ring
  (`engine/edit.cpp:68-92`; sidecar `host/sidecar/session.cpp:1622-1645`). The amount ramps
  (`engine/render.cpp:509-517`). `setParam` and `setData` are live too
  (`docs/specs/ENGINE_PROTOCOL.md:78-80`). `connect`/`disconnect` go through the swap path, which is
  the live replan when it succeeds (same file, `:69`, `:76-77`).
- **Limits.**
  - Per module: 32 ports and 64 parameters (`sdk/include/wirescape/module2.h:18-19`).
  - Per patch in the sidecar: **64 nodes** (`host/sidecar/session.cpp:281`).
  - No limit on modulation cables per parameter (`engine/build.cpp:385-396`).
  - The "32-producer limit" counts ingress rings, one per event-source thread (`engine/impl.h:25`,
    `engine/build.cpp:409`). Cables and macros use none.
- **CC Learn today** cables a `midi.cc_to_cv` row onto the target with amount 1 and leaves the base where
  it was (`apps/studio/src/app/ccLearn.ts:243`). A CC row outputs 0..1 by default
  (`apps/studio/src/app/ioData.ts:99-101`). The CC therefore sweeps only from the current value upward.
- **Module data** supports fixed record tables with text fields, e.g. OSC In's 8 rows with a 256-byte
  `pattern` (`modules/osc_in/dsp.h:22-48`).
- **OSC addresses reach Studio today** only through `telemetry.monitor`, for a Monitor cabled straight
  from `osc.in.messages` (`docs/specs/ENGINE_PROTOCOL.md:168`).
- **Transport.**
  - The engine fills 4/4 and `bar_start = floor(beat/4)*4`. The beat advances only while `cfg.playing`
    (`engine/render.cpp:568-577`).
  - No client can start the transport until TR1h (0023 R2.3 (i)). Until then, the Clock module running
    free is the only practical tempo source.
- **Random exists as an SDK example.** `example.random_source` (MIT, clocked sample-and-hold with a
  smoothed twin) is in the app catalogue (`engine/control/module_catalog.inc:31`,
  `sdk/examples/random_source/dsp.h`). 02's "no module exists for Random or sample-and-hold" holds only
  for shipped, non-example modules.
- **Port tests.**
  - For adsr, lfo, vca, vcf and vco, every non-stepped parameter must be modulatable
    (`engine/tests/port_behavior_tests.cpp:49-50`).
  - For mixer, noise, output, scale_offset, slew, clock, function_envelope and ladder, a stepped
    parameter must **not** be modulatable (`:65-75`). S8's header names the wrong modules for the second
    rule (§7).
- **Module tooling.**
  - `wsmod check` works (C1–C6). `test` and `render` are stubs that return 4 (`tools/module/matrix.py`,
    `tools/module/render.py`; MT2+ parked).
  - The device-free renderer takes `--patch --script --out --rate --block --seconds --seed`
    (`tools/render/main.cpp:70-90`); its cases are in `tools/render/cases/`.
  - `tools/module_cpu_probe.py` passes a module when the worst block is under half the period with zero
    allocations and faults (`:2-7`).
  - A folder's `module.cpp` names its class in `WS_REGISTER_MODULE(...)` (e.g. `modules/chord/module.cpp:3`).
- **Batch read sites.**
  - `midi_to_cv` parameters 0, 1, 3, 4 and 8 feed the allocator rebuild (`modules/midi_to_cv/dsp.h:74-77`).
  - `host_keyboard` parameters 0 and 1 reconfigure voices (`modules/host_keyboard/dsp.h:98-100`).
  - Groove's controls are per-sample edges (`modules/groove/dsp.h:342-347`).
  - The other read sites are as in S8.
- **Repos.** `wirescape-lab`, `wirescape-test` and `wirescape-headless` are public, so standard hosted
  Actions runners cost no minutes. The account's concurrent-job slots are the shared resource.

## 2. `wirescape-test` (question 1)

### 2.1 Layout
```
README.md  AGENTS.md  CLAUDE.md  LICENSE  LICENSES/  LAB_PIN
modules/README.md            index: one row per folder (kind, status, links)
modules/<name>/              exactly the lab's modules/<name>/ layout, plus demos/
  README.md DESIGN.md dsp.h module.cpp module.json tests.cpp CMakeLists.txt [LICENSE] demos/*.json
tools/wstest.py              the harness (Python 3.10+, standard library only)
tools/fixtures/              harness self-tests (a template copy, a NaN module, an allocating module)
.github/workflows/t0.yml t1.yml t2.yml
```
- **Kinds.** A **new** folder is a module the lab does not have. An **override** has the name of an
  existing lab folder. It starts as a byte copy at `LAB_PIN`, and its `DESIGN.md` names that base commit.
- **Demos** are render cases in the lab's `tools/render/cases` format, with patch, events, windows and
  `peak_limit`. Every module has at least one. They are copied with the folder at promotion, and the lab
  decides whether any becomes a golden case.
- **`module.json`** follows the lab at `LAB_PIN`: required until MB2 deletes it, absent after.
- **No other top-level product paths.** Shared helpers live in a module folder until the lab SDK has
  them (§2.6).

### 2.2 Pinning the lab
- `LAB_PIN` holds `repo`, `commit` (a commit on lab `main`) and `pinned` (ET date). It is the only lab
  reference. `wstest` fetches that commit into `.lab/<sha>/` (git-ignored) and never uses another.
- **One PR per bump**, containing only `LAB_PIN` and the fixes the bump forces. T0 and T1 run for every
  module on a bump PR.
- **Bump when** a lab change a module needs has merged (a `limitation found` fix), when MB2 merges, and
  otherwise at least once a week while any module is in progress, so a promotion copies cleanly.
- **First bump** happens in the harness task (MOD-0), to lab `main` of that day (at least `0dc33bf`).

### 2.3 Registration (`wstest build`)
`wstest build <module>…` recreates `build/scratch-<sha7>/` from the pinned commit on every run, so a
local edit to the scratch tree never survives. Then:
- **Before MB2** (the pin still has `engine/control/module_catalog.inc`), for a new module:
  - copy the folder to `modules/<name>/`;
  - append `add_subdirectory(../modules/<name> <name>)` to `engine/CMakeLists.txt`;
  - add `#include "../../modules/<name>/dsp.h"` to `engine/control/module_catalog.h`;
  - append `WS_APP_MODULE(<Class>)` to `module_catalog.inc`, with the class read from the folder's
    single `WS_REGISTER_MODULE(<Class>)` line. Zero or two such lines refuse the build.
- **An override** replaces the lab folder's files. Nothing is added to the catalogue.
- **After MB2:** copy the folder only. The generated registry finds it.
- **Build.** The script builds only the targets the tier needs (`abi2_<name>_tests`, `wirescape_render`,
  `abi2_module_cpu_probe`), with the lab's own headless options. For overrides it also keeps one
  **pristine** build of the pin.
- **Refusals.** The script refuses any other change to the scratch tree. A module that needs one is
  blocked (§2.6), not patched locally. Devices stay off: nothing opens audio, MIDI or the LAN.

### 2.4 Test tiers
**T0** runs for every changed module, Linux x64, on every push and PR. It runs all modules when `tools/**`
or `LAB_PIN` changes.
1. `wsmod check` (lab `tools/module/wsmod.py`): C1–C5 must pass; C6 portability is advisory.
2. A scratch build with the module registered (§2.3).
3. The module's `tests.cpp`, built with the lab's `allocation_watch`. It must cover:
   - reference maths;
   - reset reproducibility;
   - zero allocations in process;
   - finite output at parameter extremes;
   - 1 and 16 channels where the module is polyphonic;
   - state save and load where the module has state.
4. Every demo rendered with `wirescape_render`:
   - all samples finite;
   - peak at or under `peak_limit`;
   - `active` windows not silent and `silent` windows silent.

   The WAVs are CI artifacts and are never committed.
5. `tools/module_cpu_probe.py <id>`: zero allocations and zero faults are hard. Timing on hosted runners
   is reported as a diagnostic only.
6. **Overrides only**, `wstest identical`: every demo, and every lab render case that uses the module,
   renders byte-identical between the pristine build and the override, with new parameters at their
   defaults.

**T1** runs on non-draft PRs (opened, synchronize, reopened, ready_for_review) and on `main`:
- T0 on linux-arm64 (`ubuntu-24.04-arm`), because the Pi is the first target (CONSTRAINTS, Fixed);
- T0 on Windows x64 (MSVC, the lab's pinned PortAudio steps);
- T0 steps 2–4 on Linux x64 with ASan and UBSan.

**T2** is `workflow_dispatch` with a `module` input, run by the owner:
- the full lab native build and **every lab CTest** with the module registered, on linux-x64, linux-arm64
  (`ubuntu-24.04-arm`) and windows-x64. This catches catalogue-wide tests.
- every demo at 44.1, 48 and 96 kHz × blocks 16, 17, 128 and 512 (within the renderer's limits):
  finite, peak bound, and two runs byte-identical;
- callgrind instruction counts for each demo on linux-x64 (recorded, advisory);
- the Cortex-M7 portability probe (advisory).

T2 writes `t2.json` and a run summary; the promotion PR links the run. T2 replaces the parked MT2
"module matrix" for this repo. The lab's gates still run again on the promotion PR.

### 2.5 Review and merge
- Any agent implements. One PR per task against `main`; the branch name is free.
- **One simple review by a different agent session.** It reads the diff and checks the list in
  `AGENTS.md`, then comments `Reviewed <sha7>: ok` or lists what must change. The list:
  - realtime rules;
  - appended parameters only;
  - bit-identity for overrides;
  - SPDX and port licences;
  - no lab edits;
  - demos, `README.md` and `DESIGN.md` present.
- **Any agent merges (squash)** when the review names the head SHA and T0 and T1 are green on that head.
  T0 and T1 always report: a first `scope` job passes in seconds when a PR changes no module, tool,
  workflow or `LAB_PIN` path, so required checks never block a docs-only PR. Docs-only PRs need only the
  review.
- All agents act as the owner's GitHub account, so the review is a comment, not a GitHub approval.
  Branch protection requires the T0 and T1 checks and no approvals; the owner sets it once (MOD-0).

### 2.6 Escalation: `limitation found`
- **When a module needs anything outside its folder**, the agent files one issue in
  `kalharbi11/wirescape-lab` labelled `limitation found`. Anything means the engine, host, SDK, Studio,
  a lab test or a lab tool. The issue holds:
  - the module and its PR;
  - what the module needed;
  - the smallest lab change that would meet it;
  - any workaround in use.
- **Allowed workaround:** code inside the module's own folder, under the same licence, such as a private
  copy of a helper the SDK lacks. It is listed in `DESIGN.md` "Limitations".
- **Anything that needs a lab behaviour change blocks the module.** `modules/README.md` then shows
  `blocked: lab #N`.
- The Architect triages these issues in lab runs. A fix reaches `wirescape-test` through a pin bump.

### 2.7 Promotion
1. **Preconditions:**
   - T2 green at a named `wirescape-test` commit;
   - lab MB2 merged (0023 R3.2; the 0023 §7.4 fallback applies if MB2 slips);
   - `README.md` and `DESIGN.md` complete, with no private helper copy the lab SDK now provides.
2. **The lab PR** follows the lab's rules: issue, `task/<n>-<slug>`, Result, full CI and Architect review
   (W1: promotions are strict). It is B4's lane work.
   - The folder is copied byte for byte from the named commit. The PR names that commit and the T2 run.
   - Lab tools regenerate the catalogue files. A panel override is optional.
3. **Overrides:** if the lab folder changed after the override's base commit, the promoting agent
   re-applies the diff on lab `main` and reruns T0. It never overwrites lab changes.
4. **After the lab merge,** the next pin bump deletes the folder in `wirescape-test`, and the index shows
   `promoted: lab #PR`. Later changes start a new override copy, so each module has one source of truth.

### 2.8 Actions minutes
- **Windows runs only on ready PRs and `main` (owner question, decided),** and so do arm64 and the
  sanitizers. The repos are public, so minutes cost nothing. The costs are wall time and concurrent-job
  slots shared with the lab's CI. Drafts run Linux x64 T0 only.
- **Every workflow** uses one concurrency group per PR with cancel-in-progress, and a ccache keyed by
  `LAB_PIN` and toolchain.
- **T0's budget is 10 minutes on a hosted runner.** MOD-0 measures it and records the number in its
  Result.
- **T2 never runs on its own.**

### 2.9 What would overturn this
- **T0 takes over 10 minutes even with ccache.** Prebuild the pinned lab once per pin as a cached
  artifact; do not drop a step.
- **Promoted modules fail lab gates that T0–T2 passed** (0023 §4.4). Add the failing check to T1; never
  slow the lab.
- **MB2 changes the folder layout.** `wstest` follows the layout at the pin. Overrides re-copy at the
  bump that crosses MB2.

## 3. Macros and mapping (question 3)

### 3.1 The Macro module (`essentials.macro`, folder `macro`, display name "Macros")
- **Parameters** `knob1`…`knob8`: 0..1, default 0, linear, `MODULATABLE|AUTOMATABLE|AUDIO_RATE_OK`,
  mono.
- **Outputs** `out1`…`out8`: `CV_UNI`, mono. Each output is its knob's effective value per sample, marked
  constant when the parameter signal is constant. **No inputs:** a CC or LFO drives a knob through a
  modulation cable into its parameter.
- **Data slot `labels`:** `page` (text, at most 32 bytes) and 8 rows of `name` (text, at most 32 bytes),
  following OSC In's record pattern (§1). Empty means "Macros n" and "Knob k".
  - The DSP never reads it.
  - Names are edited live with `setData`.
  - Names live in the patch, not under `ui`, so the Player and any other client show them without
    knowing Studio's keys.
- **No state, no heap, no OS:** portable tier.
- **Pages.** A patch holds any number of Macro modules. Page *n* is the *n*-th Macro module in the
  patch's `modules` array. Studio reorders pages by moving the entries; the engine ignores the order.
  This answers "8 per Macro module, in pages of 8" (owner, C).

### 3.2 Range semantics: base and amount (no engine mode)
- **A mapping** is one modulation connection from a mapping source to a `MODULATABLE` parameter, owning
  that parameter's base. A mapping source is:
  - a Macro output;
  - a `midi.cc_to_cv` row;
  - an `osc.in` row.
- **The range** is in the target's normalized units: `min = norm(base)` and `max = min + amount`. It is
  shown in plain units and percent through the parameter's taper and step.
  - A negative amount is an inverted range.
  - Sources must output 0..1. Macro outputs and default CC rows do. Map mode creates OSC rows with
    output 0..1.
- **Edits.** Setting `min` sends `setParam` (base) and then re-sends the amount, so `max` stays put.
  Setting `max` sends `setModAmount`. Both are live, so a range edit never rebuilds the graph (owner open
  question, answered).
- **Why not an engine mode:**
  - the existing path already gives absolute ranges with live edits;
  - it runs in the bare engine, so patches stay self-contained;
  - it adds nothing to portable modules or to the realtime path.

### 3.3 Ownership, defaults and removal
- **One owner per parameter.** At most one mapping owns a parameter's base. Studio refuses a second one
  with: "Mapped to <source>. Remove that mapping, or map the source to a macro."
  - Ordinary modulation cables (LFO, envelope) still add on top under D7. They are drawn and edited as
    cables, not as mappings.
- **New mappings take the full range** (min 0 %, max 100 %), as Ableton does.
  - If the source is a Macro knob with no other mapping, Studio first sets that knob to the target's
    current normalized value, so nothing jumps.
  - Otherwise the target follows the source at once.
  - CC Learn adopts the same default: its commit also sets the base to the parameter minimum. Mappings
    learned earlier keep their base and amount; the panel shows their true clamped range.
- **Removing a mapping** sets the base to the target's current effective value when Studio knows the
  source value: a macro knob, or the live CC or OSC value from M4 E3c. Otherwise the base stays at
  `min`. Removal is one undo step.

### 3.4 Stepped, setParam-only and curves
- **Stepped targets** (`STEPPED|MODULATABLE`): range ends snap to whole steps. The engine rounds the
  effective value (§1), so the first and last steps get half the travel of the others. Accepted for v1;
  Studio draws the step marks on the range bar.
- **setParam-only targets** (no `MODULATABLE`) are **not mappable in the patch**, which answers
  0023 R3.3 rule 4.
  - Map mode dims them with the reason: "sets voices or structure; map it in the Player".
  - The Player sets them from `player.json` with `setParam` (§6).
  - Every in-patch mapping therefore runs in the engine alone, with no client.
  - The batch (§4.6) makes every musically meaningful stepped parameter mappable.
- **No curves per target.** A range is linear in the parameter's normalized space, so the parameter's own
  taper (log cutoff and so on) shapes the sweep. If curves are wanted later, they become a per-knob
  `curve` parameter appended to the Macro module, never per target and never an engine mode.

### 3.5 Mapping nodes, hidden cables and the node budget
These are Studio-only `ui` keys. The engine, the Player and other clients ignore them, and a patch
without them runs identically.
- **`ui.mappingNodes: [moduleId…]`** lists the modules Studio does not draw on the canvas:
  - the CC converters, MIDI In feeders and OSC In modules that map mode creates;
  - Macro modules, which show in the Mappings panel and get "Show on canvas" to leave the list.

  Nodes created by CC Learn before this change stay visible.
- **Mapping cables** are modulation cables whose source is a Macro module or a listed node. They are not
  drawn on the canvas: the target shows a badge, and the view toggle "Show mappings" draws them dashed.
- **Reuse.** A CC takes the lowest free row of a converter fed by the same device (A95); a ninth CC adds
  a converter. There is one MIDI In feeder per device and one OSC In per port until its 8 rows are full.
  An OSC In that map mode creates keeps today's defaults, with LAN off.
- **Node budget.** Every mapping node and every Macro page is a graph node, and the sidecar holds at most
  64 per patch (§1).
  - The Mappings panel shows `nodes n/64`.
  - Map mode refuses, with the reason, a mapping that would need a 65th node.
  - A lab facts row (MM-f) measures a 128-node cap on the Pi before anyone changes it.
- **The 32-producer limit does not apply** to mappings (§1).

### 3.6 The Mappings panel (Studio)
A docked panel, opened from the toolbar.
- **Macro pages:** one tab per Macro module, in page order, with 8 knobs and editable names. Pages can be
  added, renamed, reordered and deleted. Deleting a page removes its mappings, in one undo step.
- **Mapping list:** one row per mapping, with filter.
  - Source: "Macros 1 · Filter", "CC 74 · ch 1 · <device>" or "OSC /ws/knob/1".
  - Target: "<module label> · <parameter name>".
  - Editable `min` and `max` in plain units, with percent.
  - Invert and remove.
  - Clicking a target selects its module.
- **Footer:** the node budget.
- **Target knobs** (in every view): an owned parameter is greyed and cannot be dragged. It shows an arc
  from `min` to `max` and a dot at the effective value where Studio knows the source value.
- **Undo:** every edit is one undo step.

### 3.7 Map mode (Studio)
- A toolbar toggle; Esc leaves.
- **Highlighting.** Mappable parameters are highlighted, owned ones show their source badge, and
  setParam-only ones are dimmed with the reason.
- **Making a mapping.** Click a parameter, then do one of these:
  - move a MIDI CC (existing `midiLearn`);
  - send an OSC message: Studio reads `telemetry.monitor` from a hidden Monitor on the OSC In's
    `messages` output, until the controller stream (Gate P1 (e)) lands and replaces it;
  - click a macro knob in the Mappings panel.

  The mapping commits as one `applyGraph`, as CC Learn does today. A refusal leaves the document
  unchanged.
- **Clicking an owned parameter** selects its row in the Mappings panel.

### 3.8 What would overturn this
- **The owner wants two macros on one parameter with independent absolute ranges.** Then the second
  becomes relative (amount only, shown "±x %"). Still no engine mode.
- **Half-width end steps prove unmusical.** Add an appended per-knob `steps` parameter on the Macro
  module that quantizes its output. Studio does not fake it with fractional bases.
- **A Pi measurement shows a page of 8 macro outputs costs more than a typical module.** Then outputs
  become constant-only until moved. Unlikely: the module only copies its parameter buffers.
- **MM-f shows 64 nodes is too few for real patches** and 128 is cheap. Raise the cap in the lab, as an
  engine/host task under its full rules.

## 4. The module batch (question 6)

### 4.0 Shared conventions
- **C1 Appended only.** New parameters and ports go after the existing ones. Defaults reproduce today's
  output bit for bit (T0 step 6). Parameter IDs are API.
- **C2 Beat clock** (new tempo-aware modules and the LFO additions):
  - **With a `clock` cable** (`WS2_CONNECTED`), the beat comes from it: one beat per `clock_ppq` rising
    edges (≥ 0.5). Between edges the beat is interpolated from the last measured period and never
    passes the next edge's beat before that edge arrives. Before the second edge, the beat moves only at
    edges. After two periods with no edge, it holds.
  - **Otherwise the transport drives it:** locked to `transport.beat` per sample while playing, and
    free-running at `transport.bpm` from its last position while stopped.
  - **A rising `reset`** sets the beat origin to now.

  This works today with the Clock module and later with TR1h and TR3, with no mode switch.
- **C3 Division table**, slowest first, beats in brackets:
  `0` 4 bars (16) · `1` 2 bars (8) · `2` 1 bar (4) · `3` 1/2. (3) · `4` 1/2 (2) · `5` 1/4. (1.5) ·
  `6` 1/2T (4/3) · `7` 1/4 (1) · `8` 1/8. (0.75) · `9` 1/4T (2/3) · `10` 1/8 (0.5) · `11` 1/16. (0.375) ·
  `12` 1/8T (1/3) · `13` 1/16 (0.25) · `14` 1/32. (0.1875) · `15` 1/16T (1/6) · `16` 1/32 (0.125) ·
  `17` 1/32T (1/12).

  Sorted by length, so a sweep is monotonic. A bar is 4 beats (owner, C) until the transport carries a
  time signature; then bars follow `ts_num`/`ts_den`.
- **C4 Seeds.** `seed` 0 uses the engine's per-instance seed; 1..65535 fixes the sequence. Reset
  reproduces it (`docs/specs/ABI2_SPEC.md:77`).
- **C5 Realtime and portable tier.** No allocation, locks, I/O, exceptions, logging or JSON in
  process, event or reset. Fixed arrays (16 voices at most), no heap, no OS calls. A `double` state field
  is documented in `DESIGN.md`.
- **C6 Shared code.** Random writes `beat_clock.h` (C2 and C3, MIT) in its folder. Clock Div/Mult
  copies it and files the `limitation found` issue that moves it to the lab SDK (SDK-1). From the bump
  after SDK-1 merges, modules include the SDK copy and drop their own.

### 4.1 Envelopes
- **Function Envelope** (override): appended parameters:
  - `mode`: 0 Gate (default), 1 Trigger; `STEPPED|AUTOMATABLE`, setParam-only;
  - `hold`: 0–30 s, default 0, `port_flags`;
  - `delay`: 0–30 s, default 0, `port_flags`.

  Behaviour:
  - **Gate mode:** unchanged. With `delay` > 0, a rising edge waits `delay` before the rise. A falling
    edge during the wait cancels the rise, and the fall starts from the current level. `hold` applies in
    Trigger mode only.
  - **Trigger mode:** a rising edge runs delay → rise (from the current level) → hold → fall to 0,
    ignoring the falling edge. A new edge restarts at delay from the current level.
  - **Latching:** `rise`, `fall`, `curve`, `delay` and `hold` latch at the start edge, as today.
  - **State:** version 2 adds the stage counters; version 1 still loads.
  - **Bit-identity:** at `mode` 0 and `delay` 0, the output is bit-identical. The module tests keep a
    copy of the old calculation, as ADSR's do.
- **ADSR** (override): appended `delay`, 0–30 s, default 0, flags as `attack`.
  - **Gate or note on:** wait `delay`, then the attack. Gate off during the wait releases from the
    current level.
  - **Trigger mode:** delay → A → D → hold → R.
  - Retriggering during the wait restarts it. The state version is bumped. At `delay` 0 the output is
    bit-identical.
- **Tests first:**
  - trigger timing and retrigger level;
  - `delay` in both modes;
  - a gate that falls during the wait;
  - v1 → v2 state;
  - 16 channels.
- Both changes respect the port tests (§1). `mode` stays non-modulatable: switching an envelope's mode
  mid-note is not musically meaningful (0023 R3.3 rule 2).

### 4.2 Random (`essentials.random`, folder `random`, new)
Starts from `sdk/examples/random_source` and keeps its `ws::Random` use and smoothing approach.
- **Inputs:** `clock` (`GATE`), `reset` (`TRIGGER`).
- **Outputs:**
  - `stepped` (`CV_BI`): held values × `depth`;
  - `smooth` (`CV_BI`): the same values, glided with an S-curve over `slew` × the step length;
  - `step` (`TRIGGER`): fires on each new value.
- **Parameters:**
  - `division`: 0–17, default 7 (1/4), `STEPPED|MODULATABLE`;
  - `depth`: 0–1, default 1, `MODULATABLE`;
  - `slew`: 0–1, default 1, `MODULATABLE`;
  - `seed`: 0–65535, `STEPPED`;
  - `clock_ppq`: 1–24, default 1, `STEPPED`.
- **A new uniform value in [−1, 1]** starts at every division boundary of the C2 beat.
- **Trigger-to-step** is the default: with `clock_ppq` 1 and division 1/4, every edge on `clock` is one
  step. Patching triggers into `clock` therefore gives sample-and-hold. Irregular triggers work too,
  because steps land on edges.
- **Mono** in v1.

### 4.3 Clock Div/Mult (`essentials.clock_divmult`, folder `clock_divmult`, new)
- **Inputs:** `clock` (`GATE`), `reset` (`TRIGGER`).
- **Outputs:** `out1`…`out4` (`GATE`).
- **Parameters:**
  - `ratio1`…`ratio4`: `STEPPED|MODULATABLE` over ÷16 ÷12 ÷8 ÷7 ÷6 ÷5 ÷4 ÷3 ÷2 ×1 ×2 ×3 ×4 ×5 ×6 ×7
    ×8 ×12 ×16 (index 0–18). Defaults: ×2, ÷2, ÷4 and ÷8.
  - `width`: 0.01–0.99, default 0.5, `MODULATABLE`; the gate length as a fraction of each output period.
- **On the C2 beat with one beat per input edge:**
  - ÷N gates on every Nth edge from reset;
  - ×N gives N gates per input period, the first on the edge, never more than N per period;
  - `reset` makes all outputs fire on the next edge.
- **With no clock cable**, the transport drives it as a synced clock source.
- **A ratio change** applies at that output's next period start, so no gate is cut.

### 4.4 Rhythm Lanes (`sequencing.rhythm_lanes`, folder `rhythm_lanes`, new)
The rhythmic modulator, an original design: original name, panel and labels. It covers the owner's
function set: division, shape, width, phase, probability, Euclidean and delay.
- **Inputs:** `clock`, `reset`.
- **Outputs:** `lane1`…`lane4` (`CV_UNI`, 0..1).
- **Per lane *n*, 8 parameters in lane order:**
  - `division_n`: C3, `STEPPED|MODULATABLE`; defaults 1/4, 1/8, 1/16 and 1 bar;
  - `shape_n`: gate, trigger, ramp up, ramp down, triangle, sine, random stepped, random smooth;
    `STEPPED|MODULATABLE`;
  - `width_n`: 0–1, default 0.5, `MODULATABLE`: duty, triangle peak, trigger length or random slew;
  - `phase_n`: 0–1, default 0, `MODULATABLE`: delays the lane by that fraction of its cycle. This is the
    owner's "delay";
  - `probability_n`: 0–1, default 1, `MODULATABLE`;
  - `steps_n`: 1–16, default 1, `STEPPED|MODULATABLE`;
  - `fill_n`: 0–16, default 1, clamped to `steps_n`, `STEPPED|MODULATABLE`;
  - `rotate_n`: 0–15, `STEPPED|MODULATABLE`.
- **Globals:** `clock_ppq` (1–24, `STEPPED`) and `seed` (`STEPPED`). That makes 34 parameters, 2 inputs
  and 4 outputs, inside the limits in §1.
- **Behaviour:**
  - Each lane's cycle is its division, with cycles counted from reset.
  - The Euclidean pattern (Bjorklund over `steps`, `fill`, `rotate`) picks the active cycles. An active
    cycle plays with probability `p` (seeded per lane); an inactive cycle outputs 0.
  - Lane parameters latch at cycle start, so nothing jumps mid-cycle.
- **Four lanes**, so the panel stays usable; a second instance gives eight.

### 4.5 LFO additions (override; Stage 2, optional per the owner)
- **Appended inputs:** `clock` (`GATE`) and `reset` (`TRIGGER`).
- **Appended parameters:**
  - `shape`: sine (default), triangle, ramp up, ramp down, square, random stepped, random smooth;
    `STEPPED|MODULATABLE`;
  - `width`: 0–1, default 0.5, flags as `rate`;
  - `division`: 0 = "Beats" (use `beats`, default), 1–18 = C3 entries 0–17; `STEPPED|MODULATABLE`;
  - `clock_ppq` and `seed`: `STEPPED`.
- **Behaviour:**
  - A `clock` cable replaces the transport beat in sync mode (C2);
  - `reset` restarts the phase;
  - unpatched and at defaults, the output is bit-identical to today.

### 4.6 Modulatable batch (0023 R3.3 rule 2, per parameter)
**Batch A** covers the 8 modules in 0023 §3.1. Each override is one PR and must be bit-identical
unmodulated.

| Module | Becomes `STEPPED\|MODULATABLE` | Stays setParam-only (why) |
|---|---|---|
| chord | `enable1`–`enable4`, `shift1`–`shift4` (all 8) | none |
| cv_to_notes | `legato` (read per note decision; no allocation) | none |
| groove | `run`, `stop`, `reset`, `mute`, `t1_run`, `t1_stop`, `t1_mute`, `t2_run`, `t2_stop`, `t2_mute` (all 10; per-sample edges, so a trigger cable can start, stop, reset or mute) | none |
| host_keyboard | `octave` | `voices`, `mode` (allocator reconfiguration) |
| midi_in | none | `channel_filter` (channel filter; a change chokes notes) |
| midi_to_cv | `sustain`, `pitch_bend_range_semitones`, `apply_bend` | `voice_count`, `allocation_mode`, `mono_priority`, `legato`, `channel_filter` (allocator rebuild); `steal_policy` (inert, §7) |
| notes_to_cv | none | `voices` (allocation) |
| quantizer | `scale`, `root`, `shift`, `octave`, `n0`–`n11` (all 16; read per block) | none |

That is 39 parameters. No new continuous parameters are added beyond §4.1–§4.5.

**Batch B** (Stage 3) applies rule 2 to the stepped parameters of other modules: delay `division` and
`mode`, reverb `freeze`, quad_vca `mode1`–`mode4`, chaos_lite `octave_a`, `octave_b`, `route`,
`lfo_target` and `lfo_shape`, and spectral's stepped-only ones. The implementing agent checks each read
site, and a parameter that allocates or sets structure stays setParam-only, with the reason in
`DESIGN.md`.

**Excluded by ruling** (switching mid-play is not musically meaningful):
- clock `sync`, lfo `sync`, adsr `mode` and function_envelope `mode`;
- macro_oscillator `model`, which its `model_cv` input already modulates and which is lab-only to build
  (`tools/module/layout.json:17`).

### 4.7 What would overturn this
- **Interpolated clock beats audibly jitter with slowly drifting external clocks.** Add an appended
  "edges only" mode to C2. Do not drop the clock input.
- **A batch-A flag changes an unmodulated render.** The module's read path depends on flags. Then fix the
  module, never the test.
- **The owner wants Rhythm Lanes at 8 lanes.** 8 × 8 + 2 = 66 parameters exceeds 64, so per-lane
  `rotate` would have to merge into `phase`. Keep 4.

## 5. Order and tasks (question 8 for `wirescape-test`; lab rows)

### 5.1 Stages
| Stage | `wirescape-test` | lab |
|---|---|---|
| **1** | MOD-0 harness → MOD-1, MOD-2, MOD-3 and MOD-5 in parallel → MOD-4 | SDK-1 (after MOD-4 files it); MB1 → MB2 (B4, as planned); promotions of Stage 1 modules after MB2 |
| **2** | MOD-6 Rhythm Lanes, MOD-7 batch A, MOD-8 LFO | MM1 → MM2 → MM3 (B1); MM-f (B3); promotions |
| **3** | MOD-9 batch B | MM4 after Gate P1 (e) |

Stage 1 needs no lab change before MOD-0 starts. Promotions wait only for MB2.

### 5.2 `wirescape-test` task list
Agent for every row: any agent under §2.5, as a dedicated module agent outside lab lanes B1–B5 (0023 §7.3).
Tier means what must be green to merge; T2 comes before promotion.

| # | Title | Paths | Acceptance | Tier | Depends |
|---|---|---|---|---|---|
| MOD-0 | Harness: `wstest`, T0/T1/T2 workflows, first pin bump | `tools/**`, `.github/workflows/**`, `LAB_PIN`, `modules/README.md` | `wstest t0` passes `tools/fixtures/gain` registered in a scratch lab; the NaN and allocating fixtures fail with named steps; T1 runs only on ready PRs; T2 dispatches; the scratch tree is never committed; T0 time recorded; branch protection requested from the owner in the Result | T0, T1 | none |
| MOD-1 | Function Envelope Trigger mode, `hold`, `delay` (§4.1) | `modules/function_envelope/**` | §4.1 tests first; `identical` green; state v1 loads | T0, T1 | MOD-0 |
| MOD-2 | ADSR `delay` (§4.1) | `modules/adsr/**` | as MOD-1 | T0, T1 | MOD-0 |
| MOD-3 | Random (§4.2) with `beat_clock.h` (C2, C3) | `modules/random/**` | beat-clock unit tests (clock, transport playing and stopped, reset, hold); trigger-to-step at defaults; seed reproducibility; demo | T0, T1 | MOD-0 |
| MOD-4 | Clock Div/Mult (§4.3); file SDK-1 as `limitation found` | `modules/clock_divmult/**` | ratio table exact against counted edges; ×N never exceeds N per period; ratio change at the next period; demo | T0, T1 | MOD-3 |
| MOD-5 | Macro module (§3.1) | `modules/macro/**` | 8 outputs equal effective knob values; constant flags; `labels` slot packs and round-trips; zero allocations; demo with modulation cables at set base and amount | T0, T1 | MOD-0 |
| MOD-6 | Rhythm Lanes (§4.4) | `modules/rhythm_lanes/**` | Bjorklund table tests; probability seeded; latching at cycle start; 34 parameters within limits; demo | T0, T1 | MOD-3 (SDK-1 if merged) |
| MOD-7 | Modulatable batch A (§4.6), one PR per module | `modules/<module>/**` (8 overrides) | flags exactly as §4.6; `identical` green; lab port tests pass in T2 | T0, T1 | MOD-0 |
| MOD-8 | LFO additions (§4.5) | `modules/lfo/**` | `identical` green at defaults; each shape and division; clock and reset inputs | T0, T1 | MOD-3 or SDK-1 |
| MOD-9 | Batch B (§4.6) | `modules/<module>/**` | per-parameter reason recorded; `identical` green | T0, T1 | MOD-7 |

### 5.3 Lab task rows
| # | Title | Contract | Paths | Acceptance | Lane | Depends |
|---|---|---|---|---|---|---|
| SDK-1 | `sdk/include/wirescape/beat_clock.h` (C2, C3; MIT) with SDK tests | **M3** (stage MB, SDK) | `sdk/include/wirescape/`, `engine/tests/sdk_tests.cpp` | the header from MOD-3/MOD-4 unchanged in behaviour; tests for clock, transport and reset paths; full lab CI; Architect review | B4 | MOD-4's issue |
| PROMO-n | Promote each module (§2.7) | **M3** (stage MB) | `modules/<name>/**` plus generated catalogue files | byte copy of the named commit; T2 link; goldens unchanged except new cases; instruction gate within 1 % on existing rows; Architect review | B4 | MB2; T2 |
| MM1 | Mappings model: derive mappings from the document, ownership, range edits as transactions | **new MM** (macros and mapping) | `apps/studio/src/**` | Node and Playwright tests for §3.2–§3.3 (live `setParam`/`setModAmount`, no `loadGraph`) | B1 | none (FakeEngine declares the Macro module until PROMO) |
| MM2 | Mappings panel, hidden mapping nodes and cables, greyed targets, node budget | **MM** | `apps/studio/src/**`, styles | §3.5–§3.6; patches without `ui.mappingNodes` unchanged | B1 | MM1; PROMO (Macro) for RealEngine |
| MM3 | Map mode; CC Learn's full-range default | **MM** | `apps/studio/src/**` | §3.7; a learned CC sweeps the full range; OSC learn through `telemetry.monitor` | B1 | MM2 |
| MM4 | Map mode's OSC and CC learn use the controller stream | **MM** | `apps/studio/src/**` | no hidden Monitor once the stream is advertised | B1 | Gate P1 (e) |
| MM-f | Facts: 64 vs 128 nodes (idle mapping nodes), memory and worst block, Pi and hosted | **MM** (facts) | `facts/`, `bench/` | numbers with commit, machine and date; no cap change | B3 | none |

No engine row is needed for macros or mapping. Gate P1 (e) stays 2b's (§6).

## 6. Hand-off to 2b
**What `player.json` must carry for macros:**
1. **Two target forms:**
   - `{"macro": {"page": p, "knob": k}}` is patch-independent and resolves in the loaded patch: page *p*
     is the *p*-th Macro module (§3.1). One hardware map then serves the whole setlist.
   - `{"param": {"module": id, "param": "<id>"}}` is patch-specific and reaches any parameter, including
     setParam-only ones.
2. **The Player moves both with `setParam` only.** It never creates cables or edits ranges: ranges live
   in the patch and are edited in Studio.
3. **Labels** come from the Macro module's `labels` data. `player.json` may override a label per
   control.
4. **Live values.** Knob values are ordinary parameters, so the Player's live-value store and replay
   (0023 R2.4) cover them. The Player never rewrites patches.
5. **Bundle-check rows (warnings):**
   - a macro address that resolves in no patch of the setlist;
   - a `param` binding on a parameter a mapping owns (it moves that mapping's range);
   - a CC bound in `player.json` that the patch also maps.
6. **A patch's macros work with no `player.json`.**

**What map mode needs from Gate P1 (e)** (2b fixes the shapes):
- CC observations with device, channel and controller;
- OSC observations with address, including addresses that match no row while a learn is armed.

## 7. Findings (for the Architect; facts, not rulings)
- **Low, factual (S8 header):** it says `port_behavior_tests.cpp:50,75` assert "every STEPPED param is not
  MOD" for adsr, lfo, vca, vcf and vco. That assertion is at `:75` and covers mixer, noise, output,
  scale_offset, slew, clock, function_envelope and ladder. `:50` asserts only non-stepped ⇒ modulatable,
  for adsr, lfo, vca, vcf and vco.
- **Low, factual (02 "Facts for run 2"):** "No module exists today for Random or sample-and-hold".
  `example.random_source` is in the app catalogue (`engine/control/module_catalog.inc:31`).
- **Medium, unmeasured:** the sidecar caps patches at 64 nodes (`host/sidecar/session.cpp:281`), and
  ABI2_SPEC says "1024 nodes maximum" for the engine (`docs/specs/ABI2_SPEC.md:91`). Mapping nodes and
  Macro pages count against the 64. MM-f measures before any change.
- **Low:** `midi_to_cv` `steal_policy` (range 0..0) is never read (S8 notes). A lab cleanup can hide
  it; parameters are not removed.
- **Low:** CC Learn's current base handling limits a learned CC to sweeping upward from the current value
  (§1). MM3 fixes it.

## 8. Edits for the Architect
1. **New contract `MM`** (macros and mapping, Studio) from §3 and §5.3 rows MM1–MM4 and MM-f. B1 per 0023
   §7.3.
2. **`M3.md` stage MB:** add SDK-1 and the PROMO-n row pattern (§2.7, §5.3).
3. **`wirescape-test` issues:** MOD-0 at once (02: the Architect may file these straight away); MOD-1,
   MOD-2, MOD-3 and MOD-5 after MOD-0 merges; the rest per §5.1.
4. **Freeze:** macros, mapping, the module batch and `wirescape-test`'s design are decided here. OSC In
   features, scripts, the tool host and the Player stay frozen until 2b merges (02 "After each run").
5. **Owner:** branch protection on `wirescape-test` `main` with the T0 and T1 checks, once MOD-0's
   workflows exist (§2.5).
6. **Errata:** the two Low factual findings in §7, in S8 and 02.
7. **`wirescape-test` PR:** review and merge the run-2a PR, which replaces `README.md`, `AGENTS.md`,
   `CLAUDE.md` and `modules/README.md`.

Signed: claude-planner, 2026-11-26
