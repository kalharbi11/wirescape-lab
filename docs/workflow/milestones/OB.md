<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB — Owner Build contract draft

**Revision:** r1 DRAFT. Prepared by gpt-reviewer from accepted 0017 sections 4, 6–8 and PRIORITY.md. **Architect acceptance required before dispatch.** No acceptance, new authority or hardware result is claimed.

## Outcome and order

OB0 and OB1 keep the exact definitions in PRIORITY.md. OB0 is tagged on main before the S6 rename after its listed dependencies. OB1 also requires the OB tasks and owner-only checks below. The delivery lead tags/releases only after the Architect accepts this contract and its evidence criteria hold.

## Tasks proposed for acceptance

| Task | Work and evidence | Proposed paths | Dependencies / disposition |
|---|---|---|---|
| OB-a1 | Device-free CI load→save→load over every bundled patch and one synthetic patch per module config shape; compare normalised document and render hash, retain unknown data | tests and fixtures under native/document/ and native/tests2/; advisory workflow; facts/ | Land initial coverage before S5; repeat across S5/S6/E3a/E5 using actual mapped paths. Lead assigns one writer under active lane reservations |
| OB-a2 | A runner taking an owner-selected folder of real patches on the Pi, load→save→load, compare normalised document and render hash | tools/owner_build/ (new), docs/INSTALL.md, facts/ (sanitised report only) | Owner runs; agent never reaches Pi. Only actual owner result closes OB-a; V1 remains parked meanwhile |
| OB-b | Refresh Pi install/launch after S6, one script and installation instructions; device-free syntax/build validation plus explicit owner launch disposition | one script in tools/owner_build/, docs/INSTALL.md | S6; preserve owner-only hardware checks |
| OB-c | Device-free T6.8 regressions: MIDI→CV, ASIO list, panic and buffer gaps; inventory the four unverified KNOWN_ISSUES items, test using fakes or explicitly record owner-only gap | relevant test folders, facts/tests/, docs/context/KNOWN_ISSUES.md | Lead files bounded per-lane tasks after inspecting current source; do not assume an item fixed |
| OB-d | Record bundled patches to rebuild after M7, with source heads and test/render evidence | facts/patches/, bundled patch descriptions only when task assigned | M7 batches required by the selected build; no redesign or sound exception implied |

Paths and lane-level task decomposition are proposed, not grants. The Architect confirms allowed paths, tests, merge delegations and task classes before dispatch. Product/spec edits outside that accepted list require a new task or ruling.

## Invariants and acceptance

- No patch file is rewritten on load. Saves use a new destination unless the owner explicitly requests replacement. Unknown fields and the owner's existing patches keep loading.
- OB-a compares normalised document and render hash without relaxing sound tolerances. Any pre-existing nondeterministic case is recorded and referred to the Architect; never called equal.
- No real patch corpus or machine-specific paths/identities are committed. Device runs and real audio/MIDI stay owner-only; CI uses null sink/fakes.
- CN reports adoption-block instruction count and worst block with two heaviest-module instances on the heaviest bundled patch (0017 section 6). These rows have no CI threshold.
- Owner's Pi run performs 100 scripted edits at the owner's buffer size, reports xruns; OB1 needs zero. Unmeasured means pending, never zero.
- Keep OB0's tag available when OB1 is released. V1 remains parked until actual OB-a2 passes. Web dispatcher stays building and gains no feature work through OB.

Acceptance report maps both build definitions and every task to merged heads, CI/facts and owner results, with all exceptions explicit. Milestone acceptance belongs to the Architect. Lead merges only under the accepted contract; no reviewer-created draft grants merging.

Signed: gpt-reviewer, 2026-11-17
