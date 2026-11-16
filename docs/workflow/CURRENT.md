<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `35a6ef2ce299a143a9eaddce5a6bccd0e35611ea`.

## Active contracts
- **[M0 r3](milestones/M0.md)**: Phase 0 remainder, T1.1, P1–P4 (all four inventories merged; P3 `65a365e`). R7 (Q10/Q11) adds the marks file to
  T0.13a and mark-based edit location plus `.github/workflows/continuity.yml` to T0.13b.
- **[M1 r2](milestones/M1.md)**: one engine, S0 and S2–S6. S0, T1.1 and P1 are merged, so **S2 is
  dispatched** (#111). One writer owns S2–S6.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 is merged. PV1 is in PR #105 under Q8. **E1a is
  dispatched** (#112).
- **[CI1 r2](milestones/CI1.md)**: CI1.1 and CI1.2 are merged. CI1.3 (#109) is released and owns `ci.yml`.

Fable's Q7–Q11 answers (CI1 r2, M0 r3, M2 r3) merged with #107 (`6702d6a`).

**Sidecar ordering (M1 r2):** T0.13a (#104, merged `35a6ef2`), E1a (#112 / PR #116) and PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | T0.5 #51 / PR #60 | R2 packet on integrated head `afd244a`; CI1.2/P3 already merged |
| gpt-builder2 | CI1.3 #109 | ownership re-confirmed; single `ci.yml` writer, K7/K8; prepare evidence but coordinate pushes with Q12/#117 |
| gpt-builder3 | PV1 #86 / PR #105 | head `569e187`; drift/Q8 passed, required aggregate API403 blocked by #117 |
| gpt-builder4 | T0.10 #113 | draft baseline now; final pass/merge only after T0.5/T0.9 inputs merge |
| claude-builder1 | T0.13b #100 / PR #106 | T0.13a merged `35a6ef2`; #106 end-to-end facts now unblocked |
| claude-builder2 | M1 S2 #111 | new; then S3–S6 serially, each filed when the prior stage merges |
| claude-builder3 | M2 E1a #112 / PR #116 | head `ea27e2a`; `needs/fable` contract-review requested (J1–J5); CI pending |

## Open work (verify heads live; this is a snapshot)
| Task | Issue / PR | Next |
|---|---|---|
| CI1.3 | #109 | gpt-builder2 |
| T0.5 | #51 / PR #60 | ordinary integration is already pushed at `afd244a`; finish R2 evidence and review latest head |
| T0.9 | PR #50 | `main` merged at `55cf2d8` (runbook conflict: both sections kept); fresh CI, then lead review |
| T0.13b | #100 / PR #106 | end-to-end facts on merged capture and marks |
| PV1 | #86 / PR #105 | exact-head evidence, then lead review |
| M1 S2 | #111 | claude-builder2 |
| E1a | #112 / PR #116 | `review #116` (owner to a Claude session); B1/B2 recorded true in the PR |
| T0.10 | #113 | draft assigned to gpt-builder4; final pass after T0.5/T0.9 merge |
| T0.14 | owner | see the cloud build note below |

## Resumed lead checkpoint

The interim lead stopped lead actions. Batch #82's latest dispatch table is the ownership record;
verify live PRs and claims before new assignments. #117 blocks required aggregate verification through
anonymous API rate limits; no permission change or red-check waiver is authorized yet. Q12 is queued
for Fable. E1a #116 requires a Claude contract review against J1–J5 plus exact-head CI and Golden x3.
Whichever of #105 and #116 merges second must update the applyGraph schema corpus or record a PV1 disagreement.

## Notes for every builder
- **CI queue time dominates.** In run 43919414792 the `native build linux-x64` job waited 11 min for a
  runner, longer than it ran. Push each correction round as **one push**. Per-file API commits queue a
  full run each, and cancelled runs still hold runners.
- **Native build in a Claude cloud container:** the proxy refuses `codeload.github.com` tarballs.
  `git fetch --depth 1 https://github.com/<owner>/<repo> <sha>`, then
  `git archive --format=tar --prefix=<repo>-<sha>/ FETCH_HEAD | gzip -n`, reproduces each pinned
  tarball **byte-identically**. The SHA-256 equals the `URL_HASH`, checked for all five deps on
  2026-11-16. Copy it to `build/native/_deps/<name>-subbuild/<name>-populate-prefix/src/archive.tar`
  before configuring, and the configure then passes. Local runs are not acceptance evidence.

## Decisions
- Rulings R1–R7 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q11 answered; Q12/#117 open.
- Q5: bundled patches and presets may be reset after the rebuild. Nothing moves now, and golden
  "24 identical" stays through M1 and M2.

## Next action by role
- **gpt-lead:** prioritize Q12/#117 coordination with the CI1.3 writer; review #50 and R2 evidence on #60;
  review #106/#105 and E1a contract-review results without bypassing required CI; file
  S3 when S2 merges, E1b when E1a merges, and T0.10 when its inputs merge.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Contract-review (`review #<PR>` to a Claude session):** E1a **#116 now**; later M1 S3, S5b, S6.
- **Fable:** M0 acceptance needs T0.5, T0.9, T0.10 and T0.13b. Record the owner's Q5 item 7 answer (comment on #107, 2026-11-16): no owner patches, none to be added, so the ID migration and v1 conversion in Q5 points 4 and 6 are not needed. Next: `fable: run accept M0` once T0.5, T0.9, T0.10 and T0.13a/b merge.
  PV2 waits on M1 S5b; T1.6/T1.7 on S5b; T1.8 on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). Q5 point 7 answered: no owner patches.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: gpt-lead, 2026-11-16
