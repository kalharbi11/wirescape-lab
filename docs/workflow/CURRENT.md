<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by claude-lead. Last reviewed `main`: `2c4d3d083fdd24299e31d86828629033d61edf0a`.

**Active lead: claude-lead** (owner, 2026-11-16). It has the same role and authority as gpt-lead
(`AGENTS.md`, `docs/context/CODEX_LEAD.md`). One lead at a time: gpt-lead resumes only when the owner
says so, and then reads this file first. Codex's local-lead notes stay in
[LOCAL_LEAD_HANDOFF](LOCAL_LEAD_HANDOFF.md) for history.

## Active contracts
- **[M0 r3](milestones/M0.md)**: every task is merged except **T0.10** (#113 / PR #118, final pass
  released) and **T0.14** (owner). Then the lead files the acceptance report and Fable runs `fable: run accept M0`.
- **[M1 r2](milestones/M1.md)**: one engine. S0, T1.1 and P1 are merged. **S2 #111** belongs to claude-builder2
  and has no branch yet. One writer owns S2–S6; S3 staffing is decided when S2 merges.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 is merged. **E1a** PR #116 has its review-round-1
  correction at `c4db68c`; review found nothing High. **E1b** #125 was filed for gpt-builder1 as a draft and
  merges after E1a. **PV1** PR #105 waits for Q13 (Fable).
- **[CI1 r3](milestones/CI1.md)**: CI1.1, CI1.2 and CI1.4 are merged (CI1.4 `49747bd`: authenticated
  required aggregates). **CI1.3** #109 is released and is the single writer of `ci.yml`.

**Sidecar ordering (M1 r2):** T0.13a is merged. E1a (#116) and PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`. Whichever of
#105 and #116 merges second adds `applyGraph` to the PV1 schema corpus or records it as a disagreement.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | E1b #125 | new; draft PR now, merges after #116 |
| gpt-builder2 | CI1.3 #109 | released after CI1.4; integrate `main`, K7/K8 |
| gpt-builder3 | PV1 #86 / PR #105 | branch updated with `main` for the Q12 full re-run; waits for the Q13 ruling before any edit |
| gpt-builder4 | T0.10 #113 / PR #118 | final pass: replace the `pending` rows with T0.5/T0.9 facts; last M0 task |
| claude-builder1 | — | T0.13a/b merged; free |
| claude-builder2 | M1 S2 #111 | start now; no branch yet |
| claude-builder3 | E1a #112 / PR #116 | round-1 correction pushed; exact-head CI, then the lead merges |

## Merged this session (2026-11-16, after 18:30 ET)
- CI1.4 #123 → `49747bd`
- Q12 #119 → `9f883a1`
- T0.5 #60 → `2c4d3d0` (`ringmod2` unmeasured, written down)
- Earlier: T0.9 #50 → `1918cf7`; T0.13b #106 → `7bf71ae`

## Notes for every builder
- **CI queue time dominates.** Push each correction round as **one push**. Per-file API commits queue a
  full run each.
- **Failed required aggregate:** repair it with "re-run all jobs", never failed-only (Q12 point 5).
- **Native build in a Claude cloud container:** the proxy refuses `codeload.github.com` tarballs.
  `git fetch --depth 1 https://github.com/<owner>/<repo> <sha>`, then
  `git archive --format=tar --prefix=<repo>-<sha>/ FETCH_HEAD | gzip -n`, reproduces each pinned tarball
  byte-identically (SHA-256 equals `URL_HASH`). Copy it to
  `build/native/_deps/<name>-subbuild/<name>-populate-prefix/src/archive.tar` before configuring.
  Local runs are not acceptance evidence.
- **S0 snapshot copy:** `native/CMakeLists.txt` writes a copy of `session.cpp` only at configure time.
  After editing `session.cpp`, re-run `cmake build/native` before building locally. CI is unaffected.

## Decisions
- Rulings R1–R7 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q12 answered. **Q13 (PV1 bounded packet) is
  open for Fable.**
- Q5: bundled patches and presets may be reset after the rebuild. The owner has no personal patches
  (Q5 point 8). Golden "24 identical" stays through M1 and M2.

## Next action by role
- **claude-lead:**
  - merge #116 on green exact-head CI and Golden ×3;
  - merge #118 when its final pass is green, then file the M0 acceptance report;
  - review #125 when E1a lands, and #109;
  - decide S3 staffing with the owner when S2 merges.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Fable:** `fable: run questions` for Q13. Then `fable: run accept M0` once T0.10 merges and the
  lead's acceptance report is filed. PV2, T1.6 and T1.7 wait on M1 S5b; T1.8 waits on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). The S3–S6 staffing decision when S2 merges.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: claude-lead, 2026-11-16
