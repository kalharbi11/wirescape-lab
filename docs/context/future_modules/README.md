<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Future module ideas (reference, not planned work)

Modules the owner wants Wirescape to be able to host later. They're here so the rebuild considers the
**categories** they belong to, not so they get built now. Each folder holds what the owner has collected;
none of it is a module contract.

| Idea | Category it represents | Folder |
|---|---|---|
| **GUTTUR** throat voice (module in the works, C++17 + ABI 2 adapter; see `guttur/STATUS.md`) | Model-based voice synthesis: large precomputed tables, many voices with internal sub-voices (1–8 throats per note), per-cycle decisions, groups with leader/followers, shared space/bus processing, many parameters with per-voice modulation, internal modulation | `guttur/` |
| **CHAOS** (in the product) | Ported multi-part synth design | `docs/design/ports/CHAOS_DECOMPOSITION.md` |
| **Macro Oscillator** (in the product, Plaits port) | Third-party DSP library brought in as a module | `docs/design/ports/PLAITS_STUDY.md`, `native/modules2/macro_oscillator/` |

GUTTUR folder: `STATUS.md` first, then the package's own README, DESIGN, DEVIATIONS and TEST_RESULTS.
Source code is held back until the owner picks a licence and module ID.
