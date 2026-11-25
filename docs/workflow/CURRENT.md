<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

The chronological lead–Architect handoff, newest first. Assignments live in [BUILDERS](BUILDERS.md),
delivery order in [ROADMAP](ROADMAP.md), open asks in the [inbox](ARCHITECT_INBOX.md).
**Older entries** (before Architect run 43, 2026-11-25 04:15 ET) were trimmed in run 44. They stay
valid where nothing below replaces them: [CURRENT as of `6ede6f8`](https://github.com/kalharbi11/wirescape-lab/blob/6ede6f8f009793296b4484d4020377bc8600f6de/docs/workflow/CURRENT.md); earlier trims are linked from there.

**Active lead:** `gpt-lead` (Codex). The Claude Architect also acted as lead in run 44 at the owner's request. **Builders:** five ChatGPT chat lanes ([BUILDERS](BUILDERS.md)).

## Lead run — 2026-11-25 17:52 EST

- Checked B1–B5 live heads, latest signed checkpoints and exact-head workflow reports. Shared account usage/reset is unavailable (unknown).
- Merged #580 `a85137f` (A85/A85a, six same-value typing edits; signed Result, Lab/Golden/paired/portability success) and inbox #588 `3775061`. B4 #567 is released; B5 legacy editor ruling remains open.
- B1 #585 and B5 #545 latest Lab pending; B2 #540 latest exact workflows absent from connector. No product review-ready claim. Preserve B1 → B2 → B5 shared transport boundaries and #540-first slot witness.
- Architect needed for #588 legacy editor policy, #594 owner observation boundary, and #593 CMP-1 execution route. #593/#594 are inbox-only requests, not product approval; automatic approval review rejected their merges as premature. They remain open and linked here for manual disposition; no workaround or gate waiver.
- #578 remains an operational dispatch hold: A87 full-pin pre-candidate command is on issue comment 7170294924. GitHub connector lacks workflow_dispatch; shell proxy failed. Architect/owner authenticated dispatch is needed, then B3 verifies raw artifacts and publishes facts. No unchanged rerun.
- Next milestone OB1: owner OB-d listening disposition, candidate OB-f1 recheck, real-patch-folder OB-a2, and owner 100-edit Pi session (zero xruns, no visible stutter, both CN costs), then Architect acceptance/tag. #590 has no uploads. OB1.1 data work does not hold the OB1 tag. Pi runner hold and parked work unchanged.
- Manual starts: B1 `1:run`, B2 `2:run`, B4 `4:run`, B5 `5:run`; B3 `3:run` after dispatch artifacts or observation ruling. Owner `architect:run` should read the two unmerged inbox PRs as well as merged #588. No automatic wake issued while the full request batch is unmerged.

Signed: gpt-lead, 2026-11-25

## Architect run 44 (also lead) — 2026-11-25 05:20 EST (A86, A87, cleanup, owner testing; owner `architect:run`)

- **M4 A86** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7159038650)), B2 #540:
  - the route-only `setData` is the required live path;
  - the `osc.out` fresh-bus exception on whole-document `applyGraph` stays, bounded and documented, until OB1.1 close;
  - accepted-only adoption is sufficient, with three both-arch witnesses.
  Inbox PR #587 is closed as superseded.
- **OB A87 / r2.10** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/578#issuecomment-7159042191)), B3 #578: the Architect restored `.github/workflows/ob-f1-ui-facts.yml` from `cde8602`. The collectors are unchanged; it adds a full-SHA `ref` input and `captured_sha.txt`. B3 dispatches it at the candidate after this PR merges. Inbox PR #583 is closed as superseded.
- **Owner testing:**
  - new `tools/owner_record.py` (with tests): a device-off Windows/Pi record in quick, standard or long tiers, which writes one redacted zip;
  - the owner uploads each zip to [#590](https://github.com/kalharbi11/wirescape-lab/issues/590), and the lead turns uploads into `facts/device/results/` files;
  - [INSTALL](../INSTALL.md) is rewritten as the single owner guide (Windows, Pi, testing and reporting);
  - `PI_FRESH_INSTALL.md` and `PI_SETUP.md` are now redirects, because their old-repo SHAs and Qt-era steps were stale;
  - `OWNER_LOCAL_TESTS` gains Pi rows P1–P4.
- **Pi without the owner:** not before 2026-11-30 (private-repo minutes), the runner re-registration and PI-1 #369. Until then hosted Linux arm64 CI covers the Pi's CPU architecture, and owner records cover real Pi timing (A31 updated).
- **Cleanup:**
  - closed parked lab PRs #333 (Gate Delay), #176 (MT2) and #497 (A67), branches kept;
  - closed stale wirescape-pi PRs #14–#17, which the sandboxed runner #18 superseded;
  - trimmed this file from 937 lines.
- **New task CMP-1 [#589](https://github.com/kalharbi11/wirescape-lab/issues/589)** (B4, after #567): a measured rebuild vs previous-engine report on paired same-job runs, using the import pin `44da1e4` (or `kalharbi11/wirescape` main if it moved). Facts plus one advisory workflow; lead merge.
- **Lanes refreshed** in [BUILDERS](BUILDERS.md); every lane has active work. No product merge this run.
- **Next Architect run:** `architect-ready` when #540 or #545 is pinned (medium effort), or the OB1 acceptance batch. **Next run should:**
  1. review the first shipped-slot PR against A81(3)/A82 and A86's three witnesses;
  2. check B3's OB-f1 facts against r2.3;
  3. check that owner records on #590 became facts files;
  4. take OB1 acceptance once owner listening, OB-a2 and the #579 Pi session exist.

Signed: claude-architect, 2026-11-25

## Lead run 43d — 2026-11-25 04:45 EST (claude-lead)

- **#570 A2 merged `beafe8c`** (lead class-A review). KNOWN_ISSUES A2 now cites the merged CN facts `ff20670`, with the A83 expiry and overturn conditions quoted verbatim. M4 acceptance 3 (A2 recheck) is done.
- **B3 next:**
  - [#578](https://github.com/kalharbi11/wirescape-lab/issues/578): pinned OB-f1 Studio recheck, the candidate step after final CN and OB-d;
  - then [#579](https://github.com/kalharbi11/wirescape-lab/issues/579): the owner's Pi 100-edit session runner. None existed before this; it is device-gated, and the owner runs it.
- **OB1 remaining:**
  - owner listening (OB-d);
  - the #578 recheck;
  - the owner's OB-a2 run on their real patch folder;
  - the owner's Pi session via #579 (zero xruns, no visible stutter, both CN cost rows).

Signed: claude-lead, 2026-11-25

## Architect quick run 43c — 2026-11-25 04:35 EST (A85)

- **M10 A85** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/564#issuecomment-7158346297)): B4's five ARM compile failures are a real portability defect. A separate product task, **#576 S2a**, does same-value typing only, with Golden identical and G8. #564's scope does not change. #567's ARM rows stay unmeasured until #576 merges. Inbox PR #575 is closed as superseded.

Signed: claude-architect, 2026-11-25

## Lead run 43b — 2026-11-25 04:25 EST (claude-lead at the owner's request)

- **Merged:** #538 `4f0bf18` (Architect approval, A84) and docs #572.
- **Released:**
  - B2 #540 ([dispatch](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7158125250)), with the label set to in-progress;
  - B5 #545 ([dispatch](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7158126722));
  - B1 #555 after owner-listening support ([dispatch](https://github.com/kalharbi11/wirescape-lab/issues/555#issuecomment-7158127785)).
  The first shipped-slot PR carries A81(3)/A82.
- **#525 merged `ff20670`** after Golden 45582645626 passed on top of exact Lab, A62, native and cost runs. B3 is released to A2 #570 ([dispatch](https://github.com/kalharbi11/wirescape-lab/pull/570#issuecomment-7158178541)).
- **B4 #567:** exact Lab green; B4 readies it for the portability evidence.
- **Parked, unchanged:** #497 (A67, until after OB1), #333 Gate Delay, #176 MT2 (A3 later).
- **Auto-merge note:** GitHub refuses auto-merge while an advisory check is red ("unstable"), even with every required check green. The lead then merges by hand on verified required checks; advisory reds are recorded, never counted as a pass.

Signed: claude-lead, 2026-11-25

## Architect run 43 — 2026-11-25 04:15 EST (#538 approved and merged, A84; owner `architect:run`)

- **#538 E3a-2 approved and merged `4f0bf18`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7158068546)) at exact head `bd4b69c`, tested base `5ca0f19`. All E3a §6 criteria, A75/A77/A78/A80/A81 and G8 are met; no High or Medium findings. The Architect merged it directly at the owner's request: auto-merge was refused because advisory checks leave the PR "unstable", while every required check was green. Main's delta since the base touches other files, and the merge is clean.
- **A84** ([M4](milestones/M4.md)): the OSC counter restart after a post-staging publication timeout needs no correction under A51/A78(2). Routes, data and the document stay unchanged; only telemetry restarts. L1 (spec sentence) goes into E3c's next protocol edit.
- **Advisory, kept apart from the gates:** the OB-g7 L0 config-edit drops (osc-heavy route 14: 0→6, mixed route 10: 0→24) are the A67 class, parked until after OB1 (#497). The instruction advisory (8 failures on x64, 12 on arm64 against the historical baseline) is outside G8. Neither is a tier PASS.
- **#525 checked against A83:** every cap is met at `63d90c1`. Smaller 15/15 exact; larger 18/18 post-bracket exact, `freshModules` [], Delay and the held note sounding, clock slip 0; span 479 ≤ 480 frames; first mismatch no earlier than the edit; at most one newly silent sample; dip and jump reported. The arm64 raw A62 row is unmeasured and labelled so. It is a lead merge with no Architect condition; auto-merge was refused ("unstable"). **Lead:** merge after the ready-event Golden run 45582645626 passes.
- **Released by the #538 merge:** B2 #540 E3c shared integration (it carries the A81(3)/A82 witness and L1); B5 #545 E3b integration, which moves the witness to Groove if it merges first; B1 #555 after owner-listening support.
- **Next Architect run:** `architect-ready` when #540 or #545 is pinned (medium effort), or the OB1 acceptance batch. **Next run should:** (1) review the first shipped-slot PR's A81(3)/A82 witness on both Linux arches; (2) confirm #525 merged and A2 #570 was reconciled; (3) take the OB1 acceptance items once their evidence exists: owner listening (OB-d), the candidate Studio recheck, the owner patch-folder round trip, and the 100-edit Pi session (0 xruns, no visible stutter, both transition costs recorded).

Signed: claude-architect, 2026-11-25
