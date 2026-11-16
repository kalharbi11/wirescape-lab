<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `c6cd8fc0e8a789d6cfce0f78b99df636e301ede4`.

**Active lead: gpt-lead** (owner resumed local chat01a1e5ad-ea43-7b12-bc15-85ff572f1843, 2026-11-16). Claude-lead stepped down. One lead/one existing45-minute heartbeat. [LOCAL_LEAD_HANDOFF](LOCAL_LEAD_HANDOFF.md) is historical; this queue supersedes old snapshots.

## Active contracts
- **[M0 r3](milestones/M0.md)**: every task is merged except **T0.10** (#113 / PR #118, final pass
  released) and **T0.14** (owner). Then the lead files the acceptance report and Fable runs `fable: run accept M0`.
- **[M1 r2](milestones/M1.md)**: one engine. S0, T1.1 and P1 are merged. **S2 #111** belongs to claude-builder2
  and has no branch yet. One writer owns S2–S6; S3 staffing is decided when S2 merges.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 and **E1a are merged** (E1a #116 → `e0d4437`). **E1b** #125
  belongs to gpt-builder1; its dependency is met. **PV1** PR #105 has its Q13 ruling (one final packet) and carries the `applyGraph`
  schema-corpus obligation, because it merges after E1a.
- **[CI1 r3](milestones/CI1.md)**: CI1.1, CI1.2 and CI1.4 are merged (CI1.4 `49747bd`: authenticated
  required aggregates). **CI1.3** #109 is released and is the single writer of `ci.yml`.

**Sidecar ordering (M1 r2):** T0.13a and E1a are merged. PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`. PV1 (#105) adds
`applyGraph` to its schema corpus or records it as a disagreement.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | E1b #125 / PR #130 | actual implementation f4da114 delivered; review signed Result/current CI |
| gpt-builder2 | CI1.3 #109 / PR #129 | actual implementation21bc87c; lead reviews K7/K8 evidence; sole ci.yml writer |
| gpt-builder3 | PV1 #86 / PR #105 | FINAL round3/3 Q13 dispatched; max15/boundaryparity,D08facts,applyGraph corpus; samebranch |
| gpt-builder4 | T0.10 #113 / PR #118 | finalpass ea4dd03 delivered; source/criterion review before merge; last M0 builder task |
| claude-builder1 | — | finished/stopped; no new assignments |
| claude-builder2 | M1 S2 #111 | no branch yet; owner decides current S2 start and later staffing |
| claude-builder3 | — | finished/stopped; no new assignments |

## Merged this session (2026-11-16, after 18:30 ET)
- CI1.4 #123 → `49747bd`
- Q12 #119 → `9f883a1`
- T0.5 #60 → `2c4d3d0` (`ringmod2` unmeasured, written down)
- M2 E1a #116 → `e0d4437`; claude-lead role #126 → `57f866b`
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
- Rulings R1–R7 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q13 answered; queue empty. Q13: PV1 gets
  one final packet on PR #105; M2 stays r3, nothing stops or replans.
- Q5: bundled patches and presets may be reset after the rebuild. The owner has no personal patches
  (Q5 point 8). Golden "24 identical" stays through M1 and M2.

## Next action by role
- **gpt-lead:**
  - merge #118 when its final pass is green, then file the M0 acceptance report;
  - dispatch the Q13 packet to gpt-builder3 on PR #105 (round 3 of 3, final);
  - review #125 and #109;
  - decide S3 staffing with the owner when S2 merges.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Fable:** `fable: run accept M0` once T0.10 merges and the
  lead's acceptance report is filed. PV2, T1.6 and T1.7 wait on M1 S5b; T1.8 waits on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). The S3–S6 staffing decision when S2 merges.

The lead updates this file at each batch boundary; Fable after contract revisions.

## Current coordination and review policy
Owner returned gpt-lead and explicitly authorized removing artificial Fable run limits from CLAUDE.md.
Fable chooses question count, reading/delegation, scope and stopping point; creating a PR does not end a run.
Fable does not do PR reviews or review monitoring. Lead reviews delegated work; if a contract requires
Claude-specific review, tell the owner to assign a Claude reviewer. Milestone acceptance remains Fable's.
No new Claude builder tasks after current branches finish. GPT builders remain regular Chat, not Work/Codex.
Q13 merged via131 atc6cd8fc, explicit86/105 finaldispatch sent. No fourth PV1 correction: follow Fable's
revert/factsdisagreement disposition if finalpacket fails review; no redcheck waiver.
The five-hour usage window reset was verified (0percent); existing timer can resume substantive review.
Preserve ringmod2 unmeasured, rawcontinuitycaptures notuploaded, T0.14open and hostedtimingadvisory
exceptions in M0 acceptance. No acceptance claim before complete report and Fable's decision.

Signed: gpt-lead, 2026-11-16
