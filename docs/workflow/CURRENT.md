<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

The chronological lead–Architect handoff, newest first. Assignments live in [BUILDERS](BUILDERS.md),
delivery order in [ROADMAP](ROADMAP.md), open asks in the [inbox](ARCHITECT_INBOX.md).
**Older entries** (before Architect run 43, 2026-11-25 04:15 ET) were trimmed in run 44. They stay
valid where nothing below replaces them: [CURRENT as of `6ede6f8`](https://github.com/kalharbi11/wirescape-lab/blob/6ede6f8f009793296b4484d4020377bc8600f6de/docs/workflow/CURRENT.md); earlier trims are linked from there.

**Active lead:** `gpt-lead` (Codex). The Claude Architect also acted as lead in run 44 at the owner's request. **Builders:** five ChatGPT chat lanes ([BUILDERS](BUILDERS.md)).

## Lead run — 2026-11-26 05:10 EST (GPT delivery only)

- Owner: ignore new-plan updates; focus on existing GPT-agent work. Repository verified as `kalharbi11/wirescape-lab`; local preloaded `wirescape` checkout was not used for writes. No new scope released.
- B1 #606 signed Result at `70ad2fa`, draft Lab green: lead marked ready and enabled auto-merge under OB-h5 / SR20(c). Required ready-event checks still gate merge; skipped draft evidence is not a pass.
- B2 #540 `6fbc953`: targeted correction 14/14 passed, full Lab pending; finish evidence before Architect review. B5 #545 `11762c5` has a new construction-default correction and awaits current evidence; shared writer waits for actual #540 merge. #610 Lab green; long-switch and sanitizer rows still need final evidence.
- B3 #608 merged `48479fc38d5d1d74eefd0851ff893988d9398220` after signed Result and all 15 ready Lab jobs verified. Initial non-mergeable snapshot was transient; correction withdrawn (7189022402). Normal squash merge followed auto-merge refusal on advisory unstable status. #600 stays open through pinned-main dispatch and facts; available connector has no workflow-dispatch operation.
- B4 #592 `011485b` remains blocked on original JSON retention, not measured results. Both CMP-1 jobs passed; original ZIPs expire Dec 10. #609 Lab green, but release still waits for #592 merge; Golden/paired/portability and exception evidence follow ready state.
- No new ready Architect batch or wake. Manual continuation: B2 `2:run`, B3 `3:run`, B4 `4:run`, B5 `5:run`; B1 implementation finished, lead owns ready gates. Preserve all branches and correction ledgers.
- OB1 still needs owner OB-d listening, real-patch-folder OB-a2, candidate Studio recheck, and Pi 6a/6b session evidence, then Architect acceptance/tag. No milestone gate changed.

Signed: gpt-lead, 2026-11-26

## Architect run 46 — 2026-11-26 ET (wrap-up mode; owner `architect:run`)

- **Owner direction (wrap-up mode):** while the Fable runs are open, lanes finish their current PR and the draft they already have open, and open nothing new. This replaces "nothing holds" in the session entry below for queue items without a PR: OB-h2 #601, OB-h6 #604, A67 #494 and the OB-h2 Host field **hold until Fable run 1 replans**. Written into [BUILDERS](BUILDERS.md) and the [lead brief](../context/CODEX_LEAD.md#wrap-up-mode-owner-2026-11-26-while-the-fable-design-runs-are-open).
- **#585 A80 approved and merged `05cf0d7`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/585#issuecomment-7187866441)); #555 closed. This releases the shared writer to #540 and #545.
- **M4 A95** ([#540](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7187938502)): CC Learn occupancy, option B. **A96** ([#603](https://github.com/kalharbi11/wirescape-lab/issues/603#issuecomment-7187939926)): `OscOutEditor.ts` granted for preset Save/Load only. Both are bounded rulings inside existing contracts, not frozen-area design.
- **Lead merges taken by the Architect:** #597 CMP-1 bootstrap `8a64caa` (blob `f4d10bb` identical), #598 OB-f1 pre-candidate facts `4310daf` (every r2.3 row met; #578 closed, and the candidate re-dispatch becomes an Architect acceptance step), #584 Pi 6a runner `9fb5943` (#579 closed), #567 M10 S2 facts `73f411d` (#564 closed).
- **CMP-1 dispatched:** [run 45791608325](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325), `before=660556f`, `after=73f411d`. #589 was reopened after #597 auto-closed it; #592 closes it.
- **Cleanup:** inbox PRs #599 and #607 were closed (rows Cleared). Issue #512 (E3a done) was closed as completed. Closed as not planned (stale or superseded; reopen if scheduled): #82, #175, #192, #199, #203, #204, #205, #219, #222, #226, #286, #319, #327, #358, #363. Kept: trackers #198, #200–#202, OB-c #223, wake #265, #326, #451, #494, #590, Pi #369.
- **Open PRs now 7** (#540, #545, #592, #606, #608, #609, #610), at most two per lane, each with a stop point in BUILDERS.
- **Next Architect run:** `architect-ready` when #540 or #545 is pinned for its Claude contract review (medium effort), or after a Fable run. **Next run should:** (1) review #540 against A81(3)/A82/A86/A95; (2) review #545 against A90 (a)–(c); (3) check #592's facts against run 45791608325's raw artifacts; (4) after each Fable run, verify its claims, file its tasks and end wrap-up mode; (5) take OB1 acceptance once the owner evidence exists (OB-d listening, OB-a2, 6a/6b), including the OB-f1 candidate re-dispatch.

Signed: claude-architect, 2026-11-26

## Architect session — 2026-11-26 ET (Fable → Planner)

- **Owner:** no Fable access. The two design runs move to **`claude-planner`** on Opus (`planner: run 1|2`), a seat separate from the Architect, with the same final authority. The brief is now `docs/context/planner/` (renamed from `docs/context/fable/`). Run 1 also decides CI speed: docs and plan changes must not wait on long CI.
- Nothing holds; the freeze in the entry below now applies to the Planner runs.

Signed: claude-architect, 2026-11-26

## Architect session — 2026-11-26 ET (Fable design brief; owner direction)

- **Owner direction:** two products, one engine. Studio (full UI) builds patches. A headless Player (Pi) plays them, in the new repo `kalharbi11/wirescape-headless`. Fast module development happens in the new loose repo `kalharbi11/wirescape-test`, followed by promotion to this lab. Further wants: macros, mapping any parameter, envelope trigger and delay, clock-synced random and division, OSC In indicators, labels and script auto-sync, integrated Python, a tool page host, agent-ready guides. The full list is in [`docs/context/planner/01_OWNER_WANTS.md`](../context/planner/01_OWNER_WANTS.md).
- **Fable design runs 1 and 2** (triggers `fable: design run 1|2`, see `CLAUDE.md`). Their rulings are final ([brief](../context/planner/README.md)). Run 1 reviews the build and replans the roadmap. Run 2 decides the new architecture and contracts.
- **Freeze while the runs are open:** no new Architect rulings or contracts on the roadmap, headless, module-dev workflow, macros and mapping, OSC In features, scripting or the tool host. **Nothing holds:** every lane keeps its current task and queue, including OB-h1–OB-h6.
- **Reframe:** `proposals/0022` is renamed `0022-ob1.1-headless-readiness.md`. Its rationale now treats the rows as permanent headless requirements, not preparation for one event. The rows are unchanged.
- **Found (for run 2):** OB-h2 gates network hosts on `setOsc.allowNetwork`, but the engine refuses `setOsc` (`host/sidecar/session.cpp:1257`). B2 should use `--confirm-lan` until Fable rules. **Settled in run 46** ([#601](https://github.com/kalharbi11/wirescape-lab/issues/601)): a wording slip in A91, not a design gap. `setOsc` is refused by design in v0; the switch is `--confirm-lan`, as for OSC In, and a non-loopback `host` is the per-route opt-in. No Fable ruling is needed.
- **Next Architect run should:** (1) after each Fable run, verify its factual claims and file its tasks; (2) otherwise follow the run-45 list.

Signed: claude-architect, 2026-11-26

## Architect session — 2026-11-25 ET (OB r2.12: OB1.1 Tier 1 plan; owner request)

- **Owner direction:** the headless Pi build needs multi-hour runs, heavy OSC in (Python generative scripts) and OSC out (network controllers: LEDs, servos), and patch switching (reframed 2026-11-26 as permanent requirements). Stability and recovery come before perfect live editing. Patches are designed in Studio and must also run unchanged on a later headless build (separate repo, not planned yet).
- **Plan:** [`proposals/0022`](../../proposals/0022-ob1.1-headless-readiness.md), contract [OB r2.12](milestones/OB.md) (OB-h table), [OB_PLAN](OB_PLAN.md) "OB1.1 Tier 1 plan". Rulings A91 (OSC Out v2 `host`, owner permission, `lan-refused`), A92 (OSC presets, `/ws/…` Script preset, no network keys in presets), A93 (patch switching witness), A94 (patch check tool).
- **Tasks created, each queued after the lane's current task:**
  - B3: OB-h1 [#600](https://github.com/kalharbi11/wirescape-lab/issues/600), then OB-h6 [#604](https://github.com/kalharbi11/wirescape-lab/issues/604);
  - B2: OB-h2 [#601](https://github.com/kalharbi11/wirescape-lab/issues/601);
  - B5: OB-h3 [#602](https://github.com/kalharbi11/wirescape-lab/issues/602);
  - B1: OB-h5 [#603](https://github.com/kalharbi11/wirescape-lab/issues/603);
  - B4: Gate Delay re-released as OB-h4 on [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) with a bounded +3 % catalogue-noise exception;
  - A67 [#494](https://github.com/kalharbi11/wirescape-lab/issues/494) unparked (order set by OB-h1's facts).
- **Found in the existing work:**
  - the `ob-g7-hosted-soak.yml` nightly is parked (`if: ${ false }`) and PR runs skip drafts, so no `osc-heavy` result exists after #394/#433; OB-h1 restores it;
  - #326 stays open until OB-h1 routes it;
  - the sidecar already fades on patch replacement, so OB-h3 is a witness, not a feature.
- **Tier 2** (0022 §9) is suggested only and will be re-evaluated after Tier 1.
- **Held:** nothing new. Current lane tasks keep their order.
- **Next Architect run should** (in addition to the run-45 list): (1) review OB-h2 when pinned; (2) read OB-h1's facts and confirm the #326/#494 routing; (3) take the OB-h4 exception rows from its Result.

Signed: claude-architect, 2026-11-25

## Architect run 45 — 2026-11-25 18:05 EST (A88, A89, A90, OB-f1 dispatch; scheduled `architect:run`)

- **OB-f1 dispatch** (the lead's operational hold on #578): the Architect dispatched run [45717349754](https://github.com/kalharbi11/wirescape-lab/actions/runs/45717349754) at main `6b3789b`, newer than the `4de561c` pin because it includes #580. It is pre-candidate, not acceptance. B3 verifies the raw rows and publishes the facts. The GitHub MCP `actions_run_trigger` `run_workflow` can dispatch, so the lead needs no shell for this.
- **OB A88 / r2.11** ([#584](https://github.com/kalharbi11/wirescape-lab/pull/584#issuecomment-7176975049)): acceptance 6 on the Pi is 6a (runner: 0 xruns, both CN costs) plus 6b (a witnessed Studio session of ≥100 hand edits, same Pi, SHA, patch and day). No bridges. Inbox PR #594 is closed as superseded. #579 is unblocked on the ruling side and waits for the owner session.
- **A89** ([#589](https://github.com/kalharbi11/wirescape-lab/issues/589#issuecomment-7176977235)): CMP-1 uses a workflow-only bootstrap PR (lead merge), then a pinned dispatch, then the facts on #592. A bounded two-PR exception that expires when #592 merges. Inbox PR #593 is closed as superseded.
- **M4 A90** ([#545](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7176979463)): pattern-only Apply keeps the native and saved construction version and track count; construction edits are disclosed through `applyGraph`. Witnesses (a)–(c) on both arches.
- **#540:** SR21 as written. Own-path parts now; shared RealEngine/App writes after #585 merges. No stacking. `needs/architect` removed and `review-required` kept. Stale `needs/architect` labels were cleared on #578, #579, #584, #545 and #589.
- **Held:** #540 shared writes until #585 merges; #592 facts until the bootstrap merges and #567 merges; OB1 acceptance until owner OB-d, OB-a2 and the 6a/6b Pi session.
- **Next Architect run:** `architect-ready` when #540 or #585 is pinned for review, or the OB1 acceptance batch (medium effort). **Next run should:** (1) review the first shipped-slot PR against A81(3)/A82/A86; (2) check B3's OB-f1 facts from run 45717349754 against r2.3; (3) check that #545 has A90 witnesses (a)–(c) at its exact head; (4) check that the CMP-1 bootstrap file is blob-identical to the reviewed one; (5) take OB1 acceptance once the owner evidence exists.

Signed: claude-architect, 2026-11-25

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
