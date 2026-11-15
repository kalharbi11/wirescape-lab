<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Future module ideas (reference, not planned work)

Modules the owner wants Wirescape to be able to host later. They're here so the rebuild considers the
**categories** they belong to, not so they get built now. Each folder holds what the owner has collected;
none of it is a module contract.

| Idea | Category it represents | Folder |
|---|---|---|
| **GUTTUR** throat voice | Model-based voice synthesis: large precomputed tables, many voices with internal sub-voices (1–8 throats per note), per-cycle decisions, groups with leader/followers, shared space/bus processing, many parameters with per-voice modulation, internal modulation | `guttur/` |
| **CHAOS** (in the product) | Ported multi-part synth design | `docs/design/ports/CHAOS_DECOMPOSITION.md` |
| **Macro Oscillator** (in the product, Plaits port) | Third-party DSP library brought in as a module | `docs/design/ports/PLAITS_STUDY.md`, `native/modules2/macro_oscillator/` |

GUTTUR folder: `IMPLEMENTATION_REVIEW.md` (an earlier agent's review of how it could run as an ABI 2 module,
with capability table and acceptance ideas), `PARAMETERS.md` (37 controls), `PROVENANCE.md`,
`ENGINE_EXTRACTION_README.md`. The review's recommendations are inputs to judge, not decisions.
