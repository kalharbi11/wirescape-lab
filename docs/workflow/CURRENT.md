<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `3dd68f2af0a9fab6056af4b2119987fe842434f0`.

**Active lead: gpt-lead** (owner resumed local chat01a1e5ad-ea43-7b12-bc15-85ff572f1843, 2026-11-16). Claude-lead stepped down. One lead/one existing45-minute heartbeat. [LOCAL_LEAD_HANDOFF](LOCAL_LEAD_HANDOFF.md) is historical; this queue supersedes old snapshots.

## Active contracts
- **[M0 r3](milestones/M0.md)**: all builder tasks merged, T0.10/#118 → `3dd68f2`. [Acceptance report #132](https://github.com/kalharbi11/wirescape-lab/issues/132) is `needs/fable`; T0.14 remains owner-owned/open and exceptions are explicit. No milestone acceptance claimed.
- **[M1 r2](milestones/M1.md)**: one engine. S0, T1.1 and P1 are merged. **S2 #111** is reassigned by the owner to gpt-builder4, reserved for the new owner-started LOCAL Codex M1 lead. B4 is free after #118 and waits for that lead's dispatch. One M1 writer; S3 staffing/start remains an owner decision.
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
| gpt-builder1 | E1b #125 / PR #130 | f4da114 CI green; source review3High/1Medium, final correction2/2 sent6930813610 |
| gpt-builder2 | CI1.3 #109 / PR #129 |21bc87c paired evidence: manualcold43966200132 then fullPRrerun after verifiedsave; K8<=318s, sole ci.ymlwriter |
| gpt-builder3 | PV1 #86 / PR #105 | FINAL round3/3 Q13 dispatched; max15/boundaryparity,D08facts,applyGraph corpus; samebranch |
| gpt-builder4 | M1 S2 #111 | reserved; wait for new LOCAL M1 lead dispatch; previous118 merged |
| claude-builder1 | — | finished/stopped; no new assignments |
| claude-builder2 | — | S2 reassigned to GPT-B4; no M1 implementation ownership |
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
  - M0 report132 filed after118merge; preserve explicitexceptions and obtain Fable acceptance;
  - dispatch the Q13 packet to gpt-builder3 on PR #105 (round 3 of 3, final);
  - review130finalsourcecorrection and129paired cold/warmmeasurement; no gateweakening;
  - decide S3 staffing with the owner when S2 merges.
- **Builders:** one task each, result comment on the PR, one push per round.
- **Fable:** decide M0 acceptance from report132; allbuildertasksmerged, ownerT0.14 and otherexceptions remain explicit. PV2, T1.6 and T1.7 wait on M1 S5b; T1.8 waits on S6.
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
The five-hour usage window reset was verified; existing timer resumes substantive review and preserves20percent reserve.
Preserve ringmod2 unmeasured, rawcontinuitycaptures notuploaded, T0.14open and hostedtimingadvisory
exceptions in M0 acceptance. No acceptance claim before complete report and Fable's decision.

Signed: gpt-lead, 2026-11-16

## Review and cache measurement checkpoint
131Q13 mergedc6cd8fc and128Fableautonomy/activelead merged2b632ee. Fable does no PRreviews; lead reviews, owner assigns Claude-specific reviewer only if contract requires it.130 packet: gen-onlyACK settlement must not confirm unapplied; overlappingapplyGraph must not fall backtoloadGraph; valid reorderedconfig/unapplied accepted; FakeEngine replacedsource/OSCOutparity. Samebranch/finalround, no unsolicitednewtasks.
129 oldassumption thatsamebranchmanualcache is invisible toPR was corrected using officialGitHubcacheaccess docs. K7 permitsmanualcoldsave; lead launched43966200132 on21bc87c. After actualsuccessfulcacheSAVE/key/compilerflags/stats, leadFULLrerunsPR43964380415 for genuine matchedwarmrestore, then K8<=318s. No mainbootstrapmerge, PRcachewrite, settingschange or prematureclosefromcold346s. No extraexperiment/triggers bybuilder. PendingCI is not polled by model loops.

Latest cache pair: manualcold43966200132/head21bc87c completedSUCCESS and sanitizer133646255526 saved matching compilerflag cache; fullPR43964380415 rerun requested for genuinewarm/K8measurement. Observeactualkeyrestore andduration beforeacceptance; no modelpolling or watcher.

Signed: gpt-lead, 2026-11-16

## Delegated M1 lead (owner request)
The owner will start a separate LOCAL Codex M1 lead chat focused on S2. It plans before dispatch, independently reviews B4's code and criterion-specific evidence, routes corrections, and merges S2 only under M1 r2. Root gpt-lead retains cross-milestone coordination, M0/M2/CI and the existing global heartbeat. Do not create another global timer or overlap native/control writers. New M1 lead reports through111/its PR; root maintains CURRENT. Builder4 route: regular Chat6afadc5f-8478-83ea-89a0-6b2bedf3b2a9, never Work/Codex. Issue111 latest owner reassignment is authoritative while this document change is pending. S3 requires the owner's staffing/start decision.

Signed: gpt-lead, 2026-11-16
