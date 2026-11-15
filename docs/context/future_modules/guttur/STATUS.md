<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR — module in the works (status)

**What it is:** the owner's headless C++17 GUTTUR vocal-tract synth with a Wirescape ABI 2 adapter
(version 0.1, 2026-11-15). It replaces every earlier GUTTUR/GUTTR description in this lab (the Surge-based
beta 0.4 and the JS engine extraction review are superseded).

**State:** built and tested standalone by the owner's agent (Linux x86-64): CTest, block-size equality
(1/17/128/512/4096), ASan/UBSan, ABI 2 adapter against a local shim. **Not yet built inside the Wirescape
tree, not run on the Pi or Windows, not listened to at length.** The owner tests it next.

**In this folder:** the package's own docs (README, DESIGN, DEVIATIONS, TEST_RESULTS, CHANGELOG, NOTICE), its
`module.json` and the proposed catalogue entry. **The source code is not in the lab yet**: it has no licence
(NOTICE.txt), and its proposed module ID is still open (below).

**Shape (from its docs):** one note-event input; `left`/`right` audio outputs, one channel each, stereo pair;
37 parameters; 11 texture presets; 16 internal throat generators (up to 8 per note) and up to 16 tracked
notes inside one module instance, internally mixed; tables built in `prepare` (host arena); fixed 128-frame
internal control clock; 2.5 ms look-ahead limiter reported as latency; versioned state.

**What its integration shows about the host (facts from its README):**
- Registering it needs edits to five core files: `native/engine2/CMakeLists.txt`, `native/control/module_catalog.h`,
  `native/control/module_catalog.inc`, `apps/studio/public/catalogue-presentation.json`, the regenerated
  `apps/studio/public/wirescape_modules.json` (plus the patch guide). Compare `facts/code/out_of_tree_trial.md`.
- It needs no engine, ABI, protocol or sidecar change.
- Per-voice CV/modulation of its voices from outside isn't part of its port contract (voices are internal and
  mixed to one stereo pair); parameters apply to the whole instance.
- Its 16-throat worst block on a desktop x86 container was above the 50 %-of-period target for heavy modules;
  no Pi numbers yet.

**Module ID (owner, 2026-11-15): `guttr`**, not `essentials.guttur` as the package proposes. GUTTR is a special
module, not a stock one, so it doesn't go under `essentials`. (Every current ID has a namespace prefix such as
`essentials.`, `ports.`, `sound.`, `osc.`; whether special modules get their own namespace is part of the ID
scheme the rebuild may revisit.)

**Open owner decision:** licence.
