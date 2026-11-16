<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `65a365e6330ed7d4f643f6ce2175aa15427a7708`.

## Active contracts
- **[M0 r3](milestones/M0.md)**: Phase 0 remainder, T1.1, P1–P4 (all four inventories merged; P3 `65a365e`). R7 (Q10/Q11) adds the marks file to
  T0.13a and mark-based edit location plus `.github/workflows/continuity.yml` to T0.13b.
- **[M1 r2](milestones/M1.md)**: one engine, S0 and S2–S6. S0, T1.1 and P1 are merged, so **S2 is
  dispatched** (#111). One writer owns S2–S6.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 is merged. PV1 is in PR #105 under Q8. **E1a is
  dispatched** (#112).
- **[CI1 r2](milestones/CI1.md)**: CI1.1 and CI1.2 are merged. CI1.3 (#109) is released and owns `ci.yml`.

Fable's Q7–Q11 answers are in PR #107: CI1 r2, M0 r3, M2 r3. Tasks already run under them. #107 is
notes-only and merges once its post-CI1.2 run shows the required checks.

**Sidecar ordering (M1 r2):** T0.13a (#104), E1a (#112) and PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | CI1.2 #108, P3 #80 | **both merged** (`371c177`, `65a365e`). Next: T0.5 #60 once its `main` merge is pushed |
| gpt-builder2 | CI1.3 #109 | released 2026-11-16; single `ci.yml` writer; K7/K8 |
| gpt-builder3 | PV1 #86 / PR #105 | Q8 replan at `ffc353e`; exact-head Lab CI and PV1 drift pending |
| gpt-builder4 | — | free; next is E1b once E1a merges, or T0.10 once T0.5/T0.9 merge |
| claude-builder1 | T0.13a #99 / PR #104, then T0.13b #100 / PR #106 | R7 marks at `56739f5` (CI queued); #106 mark-based location at `5151a9c` |
| claude-builder2 | M1 S2 #111 | new; then S3–S6 serially, each filed when the prior stage merges |
| claude-builder3 | M2 E1a #112 | draft until #104 merges (shared `session.cpp`); contract-review before merge |

## Open work (verify heads live; this is a snapshot)
| Task | Issue / PR | Next |
|---|---|---|
| CI1.3 | #109 | gpt-builder2 |
| T0.5 | #51 / PR #60 | needs an ordinary `main` merge for the current Golden harness. A clean merge is prepared, with only #60's 10 files differing from `main`. Push it, then fresh CI |
| T0.9 | PR #50 | lead review |
| T0.13a / b | #99 / PR #104, #100 / PR #106 | exact-head CI; #104 merges first |
| PV1 | #86 / PR #105 | exact-head evidence, then lead review |
| M1 S2 | #111 | claude-builder2 |
| E1a | #112 | claude-builder3; B1/B2 recorded first |
| T0.10 | to file | after T0.5 and T0.9 merge |
| T0.14 | owner | see the cloud build note below |

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
- Rulings R1–R7 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q11 answered, queue empty.
- Q5: bundled patches and presets may be reset after the rebuild. Nothing moves now, and golden
  "24 identical" stays through M1 and M2.

## Next action by role
- **gpt-lead:** merge #107 on green required checks (the seven names now report on notes-only PRs, CI1 acceptance 5 shown on #97); push the prepared #60 integration merge;
  review #104, then #106, #105 and #50; post the E1a and S3 contract-review requests when ready; file
  S3 when S2 merges, E1b when E1a merges, and T0.10 when its inputs merge.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Contract-review (`review #<PR>` to a Claude session):** E1a; M1 S3, S5b, S6.
- **Fable:** record the owner's Q5 item 7 answer (comment on #107, 2026-11-16): no owner patches, none to be added, so the ID migration and v1 conversion in Q5 points 4 and 6 are not needed. Next: `fable: run accept M0` once T0.5, T0.9, T0.10 and T0.13a/b merge.
  PV2 waits on M1 S5b; T1.6/T1.7 on S5b; T1.8 on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). Q5 point 7 answered: no owner patches.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: gpt-lead, 2026-11-16
