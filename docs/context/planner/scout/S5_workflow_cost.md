<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S5 — Workflow cost (scout)

Lab commit: origin/main 11a68c2 (read-only; counts from `git log origin/main --numstat`; 2026-11-26).

## 1. Commits and rate
| Metric | Value |
|---|---|
| Commits on main | 358 (all squash) |
| Date range | 2026-11-14 to 2026-11-25 (12 days) |
| Mean per day | 29.8 |

| Day | 11-14 | 11-15 | 11-16 | 11-17 | 11-18 | 11-19 | 11-20 | 11-21 | 11-22 | 11-23 | 11-24 | 11-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Commits | 19 | 21 | 59 | 25 | 18 | 21 | 12 | 7 | 5 | 38 | 79 | 54 |

## 2. Docs/workflow-only vs product
Product = touches engine/, host/, modules/, apps/, sdk/, tools/, ci/ or .github/workflows/ (any file).
Non-product = everything else (docs/, proposals/, facts/, root *.md, plus bench/, native/, tests/).

| Category | Commits | Share | Lines added | Lines removed |
|---|---|---|---|---|
| Non-product only | 257 | 71.8% | 273,423 | 6,697 |
| Product (any product file) | 101 | 28.2% | 264,645 | 18,380 |

Notes:
- 67 of the 101 product commits also touch non-product files (docs, facts etc.).
- Per-file split (all commits): product-path files +88,881 / -6,063; non-product-path files +449,187 / -19,014.
- Non-product-only commits by first path: docs 194, AGENTS.md 19, facts 18, bench 10, native 8, CLAUDE.md 5, tests 2, CODEX.md 1.
  So 20 of the 257 are bench/native/tests (not docs/proposals/facts/root md); 237 are strictly docs/facts/root md.
- Large added-line counts include facts/ data files.

## 3. Subject keywords (case-insensitive, subject line only)
| Keyword | Commits |
|---|---|
| "Architect run" | 54 |
| "architect" (any) | 85 |
| "lead run" | 7 |
| "lead" (word) | 30 |
| "review" | 28 |
| "inbox" | 14 |
| "Result" | 2 |

## 4. Product commits per area (a commit counts once per area it touches)
| Area | Commits |
|---|---|
| .github/workflows | 58 |
| tools | 27 |
| engine | 20 |
| apps/studio | 19 |
| host | 18 |
| modules | 17 |
| sdk | 3 |
| apps/desktop | 3 |
| ci | 1 |

(Sum exceeds 101 because commits span areas.)

## 5. Ruling numbers (A<n>)
| Source | Distinct A-numbers | Highest |
|---|---|---|
| docs/workflow/ARCHITECT_INBOX.md | 5 | A90 |
| docs/workflow/QUESTIONS.md (the file is under docs/workflow/, not root) | 7 | A64 |
| Both files together | 12 | A90 |
| All commit messages on main (A\d\d pattern, incl. bodies) | 81 | A94 |

Inbox is 44 lines (open rows only); closed rulings live in commit messages/contracts, so file-only counts understate the total.

## 6. Rule/process document line counts
| Group | Files | Lines |
|---|---|---|
| AGENTS.md | 1 | 102 |
| CLAUDE.md | 1 | 89 |
| CODEX.md | 1 | 30 |
| docs/context/*.md | 9 | 1,016 |
| docs/workflow/*.md | 13 | 1,782 |
| docs/workflow/milestones/*.md | 16 | 1,560 |
| Total | 41 | 4,579 |

## 7. GitHub Actions workflows: 29 files in .github/workflows
Triggers (PR = pull_request, WD = workflow_dispatch):
| Workflow | Triggers |
|---|---|
| ci.yml | push, PR, WD |
| ci-digest.yml | workflow_run |
| dev-run.yml | issue_comment, WD |
| facts.yml | push, PR, WD |
| golden-renders.yml | push, PR, WD |
| instruction-gate.yml | push, PR, WD |
| portability.yml | push, PR, WD |
| protocol-v0-drift.yml | push, PR, WD |
| web-demo.yml | push, PR, WD |
| choke-listening, compare-offline, continuity, device-harness, e4b-stress | PR, WD |
| m1-stage-evidence, module-tools, ob-c-a10, ob-f1-ui-facts, out-of-tree | PR, WD |
| offline-facts, ui-profile-advisory | PR, WD |
| ob-g7-hosted-soak.yml | PR, schedule |
| continuity-e5, continuity-e5-cost, continuity-e5-native, continuity-e5v | PR only |
| e5v-keyboard-attribution, osc-gate-snapshot-witness, quad-vca-d5 | PR only |

## 8. Ten most recent product commits (newest first; index = position from tip, 0 = newest)
| Idx | SHA | Date | Subject (trimmed) | Files | Non-product-only commits since the next-newer product commit |
|---|---|---|---|---|---|
| 4 | a85137f | 11-25 | M10 S2a: explicit uint32_t min/max typing on ARM (A85) (#580) | 5 | 4 before it (tip side) |
| 5 | 4de561c | 11-25 | docs+tools: Architect run 44 — A86, A87 OB-f1 workflow restore... | 13 | 0 |
| 12 | ff20670 | 11-25 | M4 CN: integrated buffer continuity and transition cost evidence (#525) | 4 | 6 |
| 14 | 4f0bf18 | 11-25 | M4 E3a-2: shared document data and live sidecar delivery (#538) | 31 | 1 |
| 23 | 8c9bb10 | 11-25 | M4 E7c-b: Delay v2 same-rate saved state (#539) | 3 | 8 |
| 32 | f229507 | 11-25 | ci(dev-run): target check, build=none and first-error lines; run 39 lane refresh (#550) | 6 | 8 |
| 40 | df0b022 | 11-25 | S7.3 A60 Low: document CHAOS compensation provenance (#502) | 1 | 7 |
| 41 | b54cdfc | 11-25 | S7.8 A53 Low: report intermediate Ladder resonance peak ratios (#499) | 1 | 0 |
| 44 | bae5e67 | 11-25 | M7 S7.6: Delay switch crossfades (#449) | 4 | 2 |
| 45 | df925fe | 11-25 | M4 E3a-1: module data slots, live delivery and A75 generation bound (#515) | 16 | 0 |

Column note: for rows after the first, the count is non-product-only commits between that commit and the next-newer one in the table. Idx 0-3 (4 commits) are all non-product-only and sit above idx 4. From idx 4 to idx 45 the span is 42 commits: 10 product, 32 non-product-only (0+6+1+8+8+7+0+2+0).
