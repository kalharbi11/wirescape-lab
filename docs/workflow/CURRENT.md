<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `042454de51a739ed4cf39324baa07028c42acc9f`.

**Active lead: gpt-lead** (owner resumed this local chat, 2026-11-16). Claude-lead has stepped down. One lead at a time. Existing local chat01a1e5ad-ea43-7b12-bc15-85ff572f1843 and wlab-lead-review retain sole dispatch/timer ownership. [LOCAL_LEAD_HANDOFF](LOCAL_LEAD_HANDOFF.md) is historical; current state below supersedes its old queue.

## Active contracts
- **[M0 r3](milestones/M0.md)**: every task is merged except **T0.10** (#113 / PR #118, final pass
  released) and **T0.14** (owner). Then the lead files the acceptance report and Fable runs `fable: run accept M0`.
- **[M1 r2](milestones/M1.md)**: one engine. S0, T1.1 and P1 are merged. **S2 #111** belongs to claude-builder2
  and has no branch yet. One writer owns S2–S6; S3 staffing is decided when S2 merges.
- **[M2 r3](milestones/M2.md)**: `applyGraph`. E0 and **E1a are merged** (E1a #116 → `e0d4437`). **E1b** #125
  belongs to gpt-builder1; its dependency is met. **PV1** PR #105 waits for Q13 (Fable) and carries the `applyGraph`
  schema-corpus obligation, because it merges after E1a.
- **[CI1 r3](milestones/CI1.md)**: CI1.1, CI1.2 and CI1.4 are merged (CI1.4 `49747bd`: authenticated
  required aggregates). **CI1.3** #109 is released and is the single writer of `ci.yml`.

**Sidecar ordering (M1 r2):** T0.13a and E1a are merged. PV1's `native/sidecar/generated/` files
merge before M1 S5a opens, or wait until S5b. S2–S4 do not touch `native/sidecar/`. PV1 (#105) adds
`applyGraph` to its schema corpus or records it as a disagreement.

## Writers (one task each)
| Writer | Task | State / next |
|---|---|---|
| gpt-builder1 | E1b #125 | E1a merged; build and test, then mark ready |
| gpt-builder2 | CI1.3 #109 | released after CI1.4; integrate `main`, K7/K8 |
| gpt-builder3 | PV1 #86 / PR #105 | branch updated with `main` for the Q12 full re-run; waits for the Q13 ruling before any edit |
| gpt-builder4 | T0.10 #113 / PR #118 | final pass: replace the `pending` rows with T0.5/T0.9 facts; last M0 task |
| claude-builder1 | — | T0.13a/b merged; stopped, no new task |
| claude-builder2 | M1 S2 #111 | no branch yet; owner decides whether to start current S2 task |
| claude-builder3 | — | E1a merged `e0d4437`; stopped, no new task |

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
- Rulings R1–R7 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q12 answered. **Q13 (PV1 bounded packet) is
  open for Fable.**
- Q5: bundled patches and presets may be reset after the rebuild. The owner has no personal patches
  (Q5 point 8). Golden "24 identical" stays through M1 and M2.

## Next action by role
- **gpt-lead:**
  - merge #118 when its final pass is green, then file the M0 acceptance report;
  - review #125 and #109;
  - decide S3 staffing with the owner when S2 merges.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Fable:** `fable: run questions` for Q13. Then `fable: run accept M0` once T0.10 merges and the
  lead's acceptance report is filed. PV2, T1.6 and T1.7 wait on M1 S5b; T1.8 waits on S6.
- **Owner:** T0.14 (or adopt the byte-identical seeding above). The S3–S6 staffing decision when S2 merges.

The lead updates this file at each batch boundary; Fable after contract revisions.

## GPT lead return checkpoint
All four latest builder Results were read. B1/B4 still reported completed60/123, so125 and113finalpass packets were sent to existing chats. B2 acknowledged109release but had no branch/PR in liveinventory; focused continuation sent. B3 correctly holds105/Q13, no duplicateprompt. Do not infer execution from prompt delivery or activeflag. GPT builders regularChat only. Claude builders finish current tasks only; no newClaude assignments. Existing45minutetimer refreshed, no duplicatelead. Sharedusage98percentused; preserve reserve until actualreset16:49ET, no reset/credits spent.

Signed: gpt-lead, 2026-11-16
