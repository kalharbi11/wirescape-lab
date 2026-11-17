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
| 6 | **M6 MT2 PR #176** (head 930baed) | B2 | lead reviews; merge or park — must be gone before S6 |
| 7 | M1 S5a → S5b → S6 | B4 | after S4; plan the S6 window a day ahead, every product PR merged or parked (0017 §8.4) |
| 8 | M3 T1.6a → b → c → TR1e; then M4 E6 → E4a → E4b → E5/E3a → E3b/E3c/E7, CN | after S6 | issues quote ER rules: TR1e ER1; E6 ER1, ER2, ER6; E4a ER5 (statement table first); E4b ER3, ER5; E5 ER4 |
| 9 | P3 (M10 S5–S6, M12 P0) | idle builders only | |

**OB0 = rows 2 + 3 (S7.1, S7.2, S7.4, T7.0 merged) + OB-a1 + tag.** It is the next owner deliverable.

## Next action per role
| Role | Next |
|---|---|
| Lead (gpt-lead) | `lead: run`. Dispatch rows 1–5; review #176. Ask the owner for a Claude reviewer for each task the contract marks **Claude** contract-review (S5b, S6, OB-a3, M4 E-tasks). |
| Builders | One task each from the queue. Nothing in flight stops. |
| Claude Architect | 9:00 ET check-in: progress and blockers only. Then: M2 acceptance when #182 merges (criteria 1, 2, 4; 3 is ruled met). Open reserved items: Sub-patch note, M9 r2 state carry, M12 P0 live-panel limit, T4.2 smoothing, T6.3 build page, `0016` R4 / M10 X4 tolerances — none blocks P0. |
| Owner | Say go to the lead (`lead: run`). Assign Claude reviewers when asked. `CLAUDE.md` still carries the deputy section; the Architect will propose its rewrite in a PR you merge. Later: OB-a2 on your patches and the Pi session. |

Signed: claude-architect, 2026-11-17
## Local delivery takeover — 2026-11-17 ET

Owner invoked local **WLAB | LEAD | 7**; Claude Architect keeps the separate design seat.
The accepted OB r1 / CI1 r4 and Architect queue above remain controlling. Specific source
blockers below qualify the older dispatch-ready rows; no acceptance or gate is waived.

| Writer | Preserved task | Exact state / next gate |
|---|---|---|
| B1 | #182 / PR189 | ab8718cb; High6942751502 blocks despite green Lab. Correction1/2 authorized but unpublished (0/2 correction pushes). Test A/B/C queued before A ACK, partialA → acceptB → refuseC → real undo/redo at confirmed amplitude0.5. Reconcile relevant same-chain saved checkpoints, preserve UI/Q16/legitimate later values. Then #191 only after actual merge/release; #192 after report Result and Studio release. |
| B2 | #175 / PR176 | d9af77a, parked: T11 discrete-option metadata needs Architect disposition. No MT3. Accepted OB-a1/OB-c offer independent work after a scoped issue and lane check. |
| B3 | #155 / PR184 | 8823c78, source correction1/2. Three-platform Golden passed; full production R2 after-values and D5 before/head FLAC release pair still missing. #193 owns collection; do not duplicate captures. S7.2 waits actual S7.1 merge/release. |
| B4 | #188 / PR190; #193 | f2e83e05 contains final S3 facts only. S4 parked on actual96000-sample ABI1 comparison at1e-7; existing16384 fixture cannot replace it. Three SR7 mechanical extras already granted; explicit Architect reference-test disposition required. Preserve AppEngine Golden renderer, ABI2 CLI and frozen readers. Signed S4 blocked Result releases separate193; no capture PR yet. |

Four old ordinary ChatGPT builder chats were inspected and are idle. Owner requested four fresh,
issue-named ordinary ChatGPT chats in the wirescape-lab ChatGPT project. Creation is **not done**:
task API supports cloud Work only for that project, and Computer Use app access timed out.
Do not substitute cloud workers or claim fresh dispatch. Preserve existing branches and correction
counts; unpublished cloud working files are unaccepted. Local shared checkout and untracked
device captures were left untouched.

Usage snapshot:53% consumed in each account window; no reset/credit spent. Owner requested two
finite checks after Architect, around05:30 and10:00ET; timing clarification is pending because the
session clock conflicts with the host clock. Only those two local thread checks were created;
the older45-minute monitor remains PAUSED. No CI/reply polling or continuous monitoring.

Signed: gpt-lead, 2026-11-17
