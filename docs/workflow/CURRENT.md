<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Older handoffs (gpt-lead, gpt-reviewer, Fable runs 1–3) are in
[archive/CURRENT-2026-11-17.md](archive/CURRENT-2026-11-17.md). They stay valid where nothing
below replaces them; this page is the only live queue.

## Seats
- **Design: Claude Architect** (owner's Opus session; `proposals/0017` §1). Plans, rules, accepts,
  does the Claude contract reviews. **Never the delivery lead** (0017 §1 rule 3).
- **Delivery lead: gpt-lead** (Codex), unless the owner names another. Dispatches, reviews
  evidence, merges inside contracts. Builders: gpt-builder1–4 (Codex), one task each.
- **Goal:** the Owner Build ([PRIORITY.md](PRIORITY.md), contract [OB](milestones/OB.md)).
  Pick ready work by tier P0 → P3; P4 is parked.

## Decided 2026-11-17 (Architect run 1, base `main` be928a1)
- **#159 (M1 S3)** contract review passed (I1–I5, I8 hold); merged `b87f881`. **S4 is released.**
- **#180 (M10 S4 facts)** merged `be928a1`.
- **CI1 r4 ACCEPTED** ([report](reports/CI1-r4-acceptance.md)).
- **OB r1 contract accepted** ([milestones/OB.md](milestones/OB.md)): OB-a1/a2/a3, OB-b, OB-c,
  OB-d, OB-tag. PRIORITY P1 now points to it.
- **Errata (a), (b), (e)–(l) ruled** in [proposals/0018](../../proposals/0018-errata-0012-0016.md).
  With 0017 §5 this closes the packet `FABLE_FINAL_RUN.md`.

## Queue — lead dispatches in this order (P0 first, SR16 inside a tier)
| # | Task | Builder | State / gate |
|---|---|---|---|
| 1 | **M1 S4** (`abi1_mono` retire: `facts/perf/abi1_mono_final.md` first, then 96-ID inventory at the unchanged +1%) | B4 (M1 serial writer) | **dispatch now** |
| 2 | **M2 E1b-r #182** (from `60cab7ea`, browser-safe fixtures, history reconciliation) | B1 | dispatch now; M3 RL and OB0 wait on it |
| 3 | **M7 S7.1 reverb #155** | B3 (bench writer free since #150) | dispatch now; then S7.2, S7.4 for OB0 |
| 4 | **OB-a1** round-trip CI test | first free builder | file issue now |
| 5 | **OB-c** regression tests only (no fixes before S6) | first free builder | file issue now |
| 5b | **OB-e1** module census, **OB-f1** UI smoothness facts (OB r2) | first free builders | file issues now; then OB-e2, OB-f2 |
| 6 | **M6 MT2 PR #176** (head 930baed) | B2 | lead reviews; merge or park — must be gone before S6 |
| 7 | M1 S5a → S5b → S6 | B4 | after S4; plan the S6 window a day ahead, every product PR merged or parked (0017 §8.4) |
| 8 | M3 T1.6a → b → c → TR1e; then M4 E6 → E4a → E4b → E5/E3a → E3b/E3c/E7, CN | after S6 | issues quote ER rules: TR1e ER1; E6 ER1, ER2, ER6; E4a ER5 (statement table first); E4b ER3, ER5; E5 ER4 |
| 9 | P3 (M10 S5–S6, M12 P0) | idle builders only | |

**OB0 = rows 2 + 3 (S7.1, S7.2, S7.4, T7.0 merged) + OB-a1 + tag.** It is the next owner deliverable.

**Lead planning ask (owner, OB r2):** break OB into a dated task plan (`docs/workflow/OB_PLAN.md`): every OB0/OB1 row, its issue, builder, dependency and estimate. Every builder works only on OB rows (P0–P2) until OB1; anything else is parked.

## Next action per role
| Role | Next |
|---|---|
| Lead (gpt-lead) | `lead: run`. Dispatch rows 1–5; review #176. Ask the owner for a Claude reviewer for each task the contract marks **Claude** contract-review (S5b, S6, OB-a3, M4 E-tasks). |
| Builders | One task each from the queue. Nothing in flight stops. |
| Claude Architect | 9:00 ET check-in: progress and blockers only. Then: M2 acceptance when #182 merges (criteria 1, 2, 4; 3 is ruled met). Open reserved items: Sub-patch note, M9 r2 state carry, M12 P0 live-panel limit, T4.2 smoothing, T6.3 build page, `0016` R4 / M10 X4 tolerances — none blocks P0. |
| Owner | Say go to the lead (`lead: run`). Assign Claude reviewers when asked. `CLAUDE.md` still carries the deputy section; the Architect will propose its rewrite in a PR you merge. Later: OB-a2 on your patches and the Pi session. |

Signed: claude-architect, 2026-11-17
