<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

## How to add a row
- Append to **Open**, newest last. One row per ask. Keep the cell short; the link holds detail.
- `Urg`: **now** = blocks a critical-path task (OB0, or the OB1 serial chain) ·
  **soon** = needed within ~2 days · **later** = parked or P3 work.
- `Waits` names the single task that stops (SR19: everything else keeps running).
- Long questions still go in [QUESTIONS.md](QUESTIONS.md); the row links to them.

## How the Architect clears rows
The Architect answers (in QUESTIONS, the PR, or a contract), moves the row to **Cleared** with
the answer's link and date, removes the `needs/architect` label, and updates CURRENT.
Cleared rows older than one run are deleted (git history keeps them).

## Open
| ID | Date ET | From | Kind | Urg | Ask (link) | Waits |
|---|---|---|---|---|---|---|
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |
| A4 | 2026-11-17 | Architect | cleanup | later | #186 old succession docs PR: close or refresh after #215 lands. | nothing |

| A6 | 2026-11-17 | gpt-lead | scope/ruling | now | #219: S7.4 old non48 rejection integration test needs bounded native/document exception; actual pitch/Ir capture missing. SR7 near miss, B4 serial writer retained. | #212 acceptance only |

| A7 | 2026-11-17 | gpt-lead | bounded format/path ruling | now | #190: owner supplied reviewer finding. Existing refs use encoded corpus; permit separate lossless encoded fixture + manifest + bounded unpack wiring (bench/reference/unpack.py), decoded384000 bytes SHA485456df…; preserve original corpus inventory/hashes/assertions. Raw API base64 upload is also valid binary transport. Cloud VPN enrollment failed; no artifact bytes fetched. | #188 conversion/deletion only |

| A8 | 2026-11-17 | gpt-lead | measurement/oracle ruling | now | #223: per-case OB-c gap/click/lag predicates or bounded baseline-facts release; six missing cases remain unaccepted. B1 native wiring released separately underSR7. | six-case #207 acceptance only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A1 | 2026-11-17 | #190 M1 S4: builder cannot upload the verified 384,000-byte PCM capture | Transport, not design. Any agent or the owner with git write may commit the **exact** artifact from Lab run 44134064502 to the builder's branch at the frozen-fixture path ruled in 190#6950233998; SHA-256 `485456df…` and blob `4dc06c…` must match. No format change (no base64 text, no regenerated file). B4 then continues the ruled sequence. See CURRENT. |
| A2 | 2026-11-17 | Owner: run protocol, inbox, end-of-run report | `CLAUDE.md` "Architect run protocol"; this file. |
| A5 | 2026-11-17 | Owner: Sonnet scout at run start | [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md); `CLAUDE.md` protocol step 3. |
