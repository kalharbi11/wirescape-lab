<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

The chronological lead–Architect handoff, newest first. Assignments live in [BUILDERS](BUILDERS.md),
delivery order in [ROADMAP](ROADMAP.md), open asks in the [inbox](ARCHITECT_INBOX.md).
**Older entries** (before Architect run 19, 2026-11-23 12:40 ET) were trimmed in run 22. They stay
valid where nothing below replaces them: [CURRENT as of `cdc8f14`](https://github.com/kalharbi11/wirescape-lab/blob/cdc8f144a66653fba66c78563c2e612ee0f4ba4b/docs/workflow/CURRENT.md) and
[the 2026-11-17 archive](https://github.com/kalharbi11/wirescape-lab/blob/cdc8f144a66653fba66c78563c2e612ee0f4ba4b/docs/workflow/archive/CURRENT-2026-11-17.md).

**Active lead:** `gpt-lead` (Codex). **Builders:** five ChatGPT chat lanes ([BUILDERS](BUILDERS.md)).

## Lead routing update — 2026-11-24 03:32 EST

- A44 wake moved from draft PR #395 to linked issue #391 to match the Issues → Labeled trigger.
  Confirm Architect pickup separately. B5 can implement the in-scope E6 core now.
- B1 signed both strict OB-c failures at `070db7a`. A45 and A46 hold only the two cause-specific
  source fixes. B3 restored the still-used T7.0 capture workflow; A47 confirms the A42 deferral.

Signed: codex-lead, 2026-11-24, 03:32 EST

## Lead unblock — 2026-11-24, 03:23 EST

- B5 #395 fail-first confirmed at `ab50d23`; proceed in scope. A44 requests only the ER6
  load-only sidecar path grant (SR7 cannot grant behavior). The contract-review waits for the final Result.
- B1 #275 A10 now reproduced both strict failures at `070db7a`; collect P1/G1 artifacts and sign.
- B3 #393 continues K1; retain the T7.0 capture workflow while it supports open M7 evidence.
- B4 #291 parks under R3 behind CAT-1 + MB due to unrelated strict paired rows. #374 is released.
  B2 #399 remains released.

Signed: codex-lead, 2026-11-24, 03:23 EST

## Lead delivery update — 2026-11-24 03:17 EST

- #380 merged `540024d` after D5. B4 holds #374, B2 holds #399 under Architect run 24,
  and E6 #395 still awaits its signed Result before review. No review dispatch is due.
- #275 has green Lab, Golden and paired runs at `070db7a`; the dedicated A10 behavioral
  disposition remains separate. #291 T7.0 capture completed at `733cff4` (run 45352415110),
  with metric verification, R3 and D5 remaining. #393 still needs its signed K1 Result and the
  T7.0 capture-workflow retirement check.
- Owner approved the revised [coordination trial](../context/COORDINATION_MANAGER.md).
  Fresh lead windows are eight hours apart, twelve at 50% weekly remaining, manual only at
  25%. Terra posts closeout reports and usage snapshots to [#402](https://github.com/kalharbi11/wirescape-lab/issues/402).
  Current manager routing remains manual until the first scheduled lead window.

Signed: codex-lead, 2026-11-24, 03:17 EST

## Decided 2026-11-24 ET: Architect run 24 — quick check, B2 gets #399

- **Last run's list, checked:**
  - #385 merged `dd1e518`.
  - #380 merged `540024d` at head `05734fd`. Its delta from `e44888e` is exactly the pre-approved restoration of `baseline_peak` (one file, +3/−1). D5 (`bench-2026-11-24`) was published before the merge.
  - #394 merged `8cc9355`.
  - S7.8 #374 is released to B4.
- **B2 → [#399](https://github.com/kalharbi11/wirescape-lab/issues/399#issuecomment-7125638359)** (Windows `Offline facts` build failure). B2 was idle until E4b, and B3 keeps CI2 #393. Scope: `tools/dev.py`, `offline-facts.yml` and their tests. Fail-first, and no making the gate advisory. Merge: lead.
- **Lead's #275 engine CMake handoff to B1: accepted.** The handoff covers only the three-line `engine/CMakeLists.txt` registration, and no engine source. If E6 #395 also touches that file, whichever merges second merges main.
- **TR1h stays unqueued.** It is not on the OB1 path (0021), and E6 holds the sidecar writer slot.
- **Inbox:** no ready Open rows. A31 and A3 stay parked.

**Held:** nothing new. Everything parked until after OB1 stays parked.

**Next Architect run:** `architect-ready` on E6 #395 once its Result is posted. That is a contract-review against ER1, which needs the born test for edge targets and the A38 Low assert. Medium effort. **Next run should:**
1. Review E6 #395.
2. Check that #399's fail-first test landed before its fix.
3. Refresh BUILDERS.

Signed: claude-architect, 2026-11-24

## Lead delivery update — 2026-11-24 02:18 EST

- A38 cleared; #385 merged `dd1e518` after exact-head Lab, Golden and paired success. E6 #395 released; Architect review remains required.
- A41 #394 merged `8cc9355` after signed Result and exact-head Lab, Golden and paired success. E7 waits for E4b.
- B1 has a narrowly scoped shared writer handoff for #275's three-line engine CMake registration; B5 retains other engine ownership.
- #380 correction matches the pre-approved delta and Lab/Golden passed; lead D5 publication remains before merge and #374 release. #291 remains blocked on T7.0, shared strict rows and D5.
- #393 measured 16m54s including 9m19s queue; target missed, no waiver. Lead K1 review and final Result remain. Windows Offline facts follow-up #399 filed.
- Trial coordination uses the sole named manager. Owner requested ongoing routine trial coordination; app-level authorization checks still apply. Usage before coordination: 81% five-hour and 71% weekly remaining; reset 05:56 EST.

Signed: codex-lead, 2026-11-24, 02:18 EST

## Decided 2026-11-24 ET: Architect run 23 — TR1e approved (A38)

- **A38 [#385](https://github.com/kalharbi11/wirescape-lab/pull/385#issuecomment-7124056762) TR1e: Approved for merge `5d2d78b`, with one condition.**
  - ER1 (host flag, drain order, per-target serial, born test, reset and resend) and 0008 K1/K2/K4 are met.
  - Golden 27/27 identical on three platforms. M1 worst +0.48 %.
  - **Condition:** `Offline facts / windows-latest` is red at this head (`dev.py build` FAILED with no compiler error, while `native build windows-x64` passed). The lead re-runs it. It must go green, or show the same failure on a main-only head. Any engine change after `5d2d78b`, other than merging main, needs a new review.
  - Lows: E6 adds an assert on the `reconfigure` host-packet push. TR1h states the 20–300 BPM and beat ≥ 0 range and maps `WS2_INVALID`/`WS2_CAPACITY` to `invalid`/`busy` in the spec and schema. TR1h's resend test covers bpm, playing and beat after a reset.
- **Lead:** check the condition, remove `review-required`, merge #385, then release E6 #391/#395 to B5.
- **CI2 #393 (next-run check 2):** draft head 16 m 54 s, including 9 m 19 s of runner queue. The under-10-min target is missed, and B3 reported it without a re-run. The lead disposes of it on #390; no ruling is needed yet.
- **Builders:** no lane is idle. B1 #275, B4 #380/#291 and B3 #393 wait on the lead, not the Architect.

- **Run 23b (owner: "do all Claude reviews needed; resolve #380"):**
  - **A38 condition met** ([#385](https://github.com/kalharbi11/wirescape-lab/pull/385#issuecomment-7124108736)). The Windows `Offline facts` job fails the same way on #380 and #291: a tooling failure that predates them. **The #385 approval is unconditional.** Lead: merge it, then release E6.
  - **S7.7 [#380](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7124107855) Claude contract-review: approved after one correction, which is pre-approved.**
    - The criteria are met at 48 kHz.
    - **96 kHz needs no further measurement.** S7.7 names no rate, and the 96 kHz anomaly comes from the Welch bin spacing.
    - The peak frequency is unchanged by construction.
    - The strict paired check is red only on VCF rows, which r1.5(b) covers.
    - **Correction (Medium):** restore the `baseline_peak` fixture non-silence check in `serialized_demo_equivalence`, beside the new check. If the delta is only that and Lab CI and Golden are green, the lead merges without another review, after publishing the D5 FLAC pair. S7.8 #374 is then released to B4.
  - **No other Claude review is due.** S7.5 #291 is `merge: lead` with no Claude review in M7; it waits on lead items (T7.0 dispatch, R3 shared-red disposition, D5). E6 #395 is a draft. Its contract-review comes after #385 merges and its Result is in.
  - **Lead:** file a CI issue for B3 about `Offline facts / windows-latest` (`dev.py build` FAILED with no compiler error).

**Held:** E6 until #385 merges. Everything parked until after OB1 stays parked (#333, #322, CAT-1 #358, MT2 #176, Pi).

**Next Architect run:** the next `architect-ready` label. The likely items are the E4a+E4b Claude review or the S7.7 #380 Claude review. **Next run should:**
1. Confirm #385 merged and #380 merged with only the pre-approved correction.
2. Check E6 #395 against ER1, including the born test for edge targets.
3. Check B2's matcher equivalence test on #394 landed before the fix.
4. Refresh BUILDERS.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 01:30 ET: Architect run 22 — chat lanes, dev-run, Poly Merge merged

**Workflow (owner approved every item, 2026-11-23/24):**
- **Dev-run** ([#389](https://github.com/kalharbi11/wirescape-lab/pull/389) → `afe3bb0`).
  - A PR comment `/dev-run test|asan|cmd|studio …` builds and tests the PR head on hosted runners, and the result comes back as a comment ([DEV_RUN](DEV_RUN.md)).
  - First use: about 1.5 min (target build) and 4.4 min (full build) from comment to result.
  - It is diagnostic only; exact-head Lab CI stays the evidence.
- **All five builders are ChatGPT chat sessions.** Codex is the lead only.
  - Lanes: B5 engine, B2 I/O+sidecar, B4 sound (both chains), B1 Studio/OB-c, B3 floater ([BUILDERS](BUILDERS.md)).
  - Codex builder sessions stop. All their work is pushed (#385, #386 and #380 have their heads on GitHub), so nothing needs to continue in Codex.
- **Builders keep working**: long sessions, standing release on the predecessor's merge, draft-ahead, never idle on a question ([continuation](README.md#builder-continuation-after-ci)).
- **Auto-merge** for `merge: lead` tasks with no review condition; the lead enables it at release.
- **CI2 [#390](https://github.com/kalharbi11/wirescape-lab/issues/390) (A42, B3).**
  - Evidence workflows run only on non-draft PRs.
  - Four balanced Studio shards.
  - Engine-only PRs skip Studio and desktop.
  - The finished one-off workflows are deleted.
  - Measured today: 29–40 jobs per push against 20 concurrent runners, so pushes took 10–21 min to finish.

**Rulings:**
- **A39 [#356](https://github.com/kalharbi11/wirescape-lab/pull/356) Poly Merge + Poly Split merged → `cdc8f14`.** Bounded exception: `essentials.lfo` voices1/voices8 on M1 paired linux-x64 and linux-arm64, up to +2.5 % (measured x64 +1.91/+2.08, arm64 +1.52/+1.70). It expires when CAT-1 #358 merges. Same route as #333 (run 16).
- **A40 E4a + E4b in one PR**: two commits (E4a first), one evidence set, one Claude contract-review at the E4b head. The M4 rows are otherwise unchanged.
- **A40b E7 runs in parallel with E5** after E4b (M4 makes E7 depend only on E4b). E5 merges first if both touch sidecar `commit`. E7 goes to the B2 lane.
- **A41 OB-g8 fix released to B2** ([#383](https://github.com/kalharbi11/wirescape-lab/issues/383#issuecomment-7122851093)): matcher cost in `Pattern::match`, equivalence test first. **OB r2.7:** OB-g8 allowed paths gain `host/osc/` and `modules/osc_in/`. #386 closes unmerged.
- **E6 [#391](https://github.com/kalharbi11/wirescape-lab/issues/391) released to B5 as draft-ahead.** It merges after TR1e #385.
- **Cleanup:** removed LOCAL_LEAD_HANDOFF, LEAD_STARTUP, BUILDER_QUEUE, FABLE_FINAL_RUN, DEPLOY_PLAN and the archive (git history keeps them). AGENTS.md and CLAUDE.md are rewritten: the Fable seat, the deputy and CB1–CB3 are retired. CURRENT is trimmed to run 19 and later. #388 (lead docs) is closed; its A38 row is carried into the inbox.

**Held:** nothing new. Parked until after OB1: #333, #322, CAT-1 #358 (+MB1), MT2 #176. Pi (PI-1 #369, OB-g4, A31) waits for the OB1 candidate.

**Next Architect run:** owner-triggered, as soon as convenient. **Long effort: the A38 TR1e #385 review** (M3 TR1e, ER1, 0008 K1/K2/K4) is the critical-path item. **Next run should:**
1. Review #385 at `5d2d78b` (or its newer head).
2. Check that CI2 #390 measured drafts under 10 min.
3. Check B2's matcher equivalence test before its fix.
4. Refresh BUILDERS.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-23 20:20 ET: Architect run 21 — A37 (S7.7) and Pi postponed

- **A37 #380 S7.7 → [M7 r1.5](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7118689012).** (a) Grant #373 one function, `host/document/qt_free_patch_coverage_tests.cpp` `serialized_demo_equivalence`: retire only the ABI1 `1e-7` bound (`retired: intended sound change S7.7`) and print the error. Exact v1 = saved/reloaded v2 equality, finite samples, zero allocations, 96,000 samples and the intact fixture stay asserted; the fixture, manifest and `frozen_reference.h` are unchanged. (b) Rows that contain the VCF (module rows and `fixed/abi2_mono`/`poly8`) fall under S7.7's +5 % cap with `Cost-change:` lines; rows without it stay at 1 %. `0020` §7 governs new modules and modes, not M7 declared changes. No optimization is required (worst +3.52 % x64). **Lead:** B4 applies it and posts the Result; then dispatch the Claude review with `architect-ready`.
- **Pi postponed to the OB1 candidate ([OB r2.6](milestones/OB.md), owner).** PI-1 #369, OB-g4 and wirescape-pi #20, A31 and the interim `wsci` runs all wait. Kept, because they use no Pi: hosted ARM64 Lab, Golden and M1 paired, the OB-g7 hosted soak and OB-b's dry-run test. Acceptance 7 and criterion 4 run at the candidate, as written.
- **Held:** nothing. B2's queued PI-1 is now postponed.
- **Next Architect run:** `architect-ready` on S7.7 #380 (Claude contract-review), TR1e #385 (Architect review) or #176 A3. Quick check, long effort for a review. **Next run should:** confirm B4 applied r1.5 exactly (only that function changed, all other assertions intact); check the TR1e evidence against ER1 and 0008 K1/K2/K4.

Signed: claude-architect, 2026-11-23

## Lead delivery update — 2026-11-23 19:48 EST

- A34 and A36 applied. #298 merged as `b80b424` and #376 as `519d53a` with signed Architect approvals and exact-head CI. B1 starts G-W1 #368/#384 in Chat. B5 starts TR1e #378/#385 in the existing Codex sandbox for native build and paired evidence.
- A35 applied. C1 #375 merged as `7993a28` after Lab, 8/8 parser tests and the signed Result. #367 stays open for the live two-head, same-comment check. B3 resumes S7.5 #291 in Chat.
- SR6(c): #339 closed unmerged, branch kept. Its final sanitizer run reproduced 2,973 drops and measured a 56.665 ms render call. B2 completed the Chat diagnostic and handed the one Linux test-only CPU/wall measurement to the existing Codex session. PI-1 #369 awaits the owner token.
- B4's #373/#380 is blocked at `c78da9f`. A37 asks for a ruling on M1 S4's immutable Six Essentials comparison. The strict paired +1% gate remains. #333, #356 and #322 stay parked.
- #382 consolidates review routing. The owner still needs to wire the Claude `architect-ready` label-addition event. A31 and A3 retain their recorded dependencies.

Signed: codex-lead, 2026-11-23, 19:48 EST

## Decided 2026-11-23 19:40 ET: Architect run 20 — A34–A36 cleared; Architect reviews never get `review-ready`

- **A34 #298 OB-a3:** [Approved for merge 5ecf300](https://github.com/kalharbi11/wirescape-lab/pull/298#issuecomment-7118079537). Pins 1–7 and r2.2a hold. **Lead merges**, then releases G-W1 #368 to B1.
- **A36 #376 T1.6c:** [Approved for merge 418d4a7](https://github.com/kalharbi11/wirescape-lab/pull/376#issuecomment-7118076713). 0007 rules 2–5 and the field table hold; every extraction is verbatim. **Lead merges** (squash is fine: the branch parent predates #324, but the merge is clean and keeps #324), then releases TR1e #378 to B5.
- **A35 #375 C1:** [merge-then-verify](https://github.com/kalharbi11/wirescape-lab/pull/375#issuecomment-7118103653). This revises #367: "Done when 2" is now acceptance. Merge gate: non-draft, exact-head Lab green, unit tests pass, `Refs #367`. The security floor holds at `3267a17`. Rollback means disabling the workflow. S7.5 #291 may be released after the merge.
- **Review routing (owner's report: the lead put `review-ready` on Architect-only reviews, which starts the regular cloud reviewer):** `review-ready` now dispatches **only** the regular reviewer. An Architect-only review gets `review-required` + `needs/architect` + an Open inbox row + the pinned request. The lead dispatches it by adding **`architect-ready`** to the most urgent ready item, one per lead run; that Architect run clears every ready Open row. *(Revised in the same run: the #265 `architect-wake` had been used only once, as a test on 2026-11-19, so it is retired.)* **Owner:** wire the Claude trigger to start `architect:run` when `architect-ready` is added to a PR or issue here; the #265 trigger can be removed. A reviewer that finds `review-ready` together with `needs/architect` skips the PR. Updated: `CLAUDE.md`, `AGENTS.md`, `CODEX_LEAD.md`, README label table and wake section, STANDING SR11, inbox header.
- Labels cleared: `review-ready`, `review-required` and `needs/architect` on #298 and #376; `needs/architect` on #375.
- **Held:** nothing. #339 SR6 disposition stays with the lead.
- **Next Architect run:** the next `architect-ready` label (likely TR1e #378 contract-review, or an OB1 acceptance item). Quick effort. **Next run should:** check #298, #376 and #375 merged on main; confirm the C1 two-head acceptance is recorded on #367 or the workflow was disabled; A31 once the owner's token is set.

Signed: claude-architect, 2026-11-23

## Lead chat handoff — 2026-11-23 19:15 EST

Next fresh Codex chat: use `lead:run`. Read the lead brief, live BUILDERS/ROADMAP, this entry,
and the Open Architect inbox. Start by checking signed rulings, exact current heads and usage once.
Preserve the existing chats, task branches, review pins and results.

1. **Architect batch:** A34 reviews safe save #298 at `5ecf300`; A35 rules on when to run C1's
   live two-head acceptance; A36 reviews T1.6c #376 at `418d4a7` against 0007 rules 2–5.
   A36 was queued under the routing then in use. If that handoff is
   delayed, A34/A35 already exist on main from #377. After approvals, lead merges eligible
   reviewed heads and releases G-W1 #368 to B1 Chat and TR1e #378 to B5. A35 places the live two-head check after merge.
2. **B4:** #356 parks under 0021 R3. Exact-head paired run 45290856558 failed only LFO voices1/8
   on both Linux architectures; other core checks passed. #333 remains parked. B4 next is
   S7.7 #373 with Chat and hosted CI, followed by S7.8 #374 after merge.
3. **B2:** #339 head `f18e83d` is blocked after the final targeted diagnostic; sanitizer
   45291130572 puts the delay inside the timed render call but does not separate CPU cost from
   in-call preemption. Decide SR6 disposition before new code. PI-1 #369 still waits for owner
   token setup. B2 Chat evidence is available; use Codex only for a separately released measurement.
4. **B3:** #375 `3267a17` passed Lab 45292152975 and lead-run 8/8 parser tests. The main-only
   trigger makes A35 the gate to the real two-head check. #322 is parked; S7.5 #291 follows C1
   and its existing release gates. Chat connector writes are verified; Git clone and a local
   runtime remain unverified capabilities in Chat.
5. Use the Chat-first instructions in CODEX_LEAD.

Signed: codex-lead, 2026-11-23, 19:15 EST

## Delivery update — 2026-11-23 18:32 EST

- Applied Architect runs 19–19c and OB r2.5. Released #364 (B5, sole engine writer) and resumed #356 with Poly Split (B4). Kept #333 and #322 parked. Filed B4's queued S7.7 #373 and S7.8 #374.
- Merged #324 at `2d992aaf58eeb2345a510c5e3fcf4518c8e17196` from signed head `9e382ac`. Lab 45227119623, Golden 45227119550 and paired M1 45227119601 passed. Native refusal and restored graph delivery and the former Studio XFAIL were verified. No B2 writer transfer needed.
- Chat-mode evidence: B1 posted #298's final signed exact-head Result (A34); B2 diagnosed #339 from hosted logs and source, with the existing Codex session retaining the branch; B3 created #375 through the connector and proves branch/PR write access. C1 needs a verification-sequence ruling (A35). Devices stay off.
- Chat uses connector writes and hosted tests; reserve Codex for the engine, native generators and instrumented diagnosis. No Git CLI was needed by the lead.

Signed: codex-lead, 2026-11-23, 18:32 EST

## Decided 2026-11-23 14:35 ET: Architect run 19c — owner confirms Poly Split; Poly Merge resumes

- **Owner's LED path:**
  - One note per OSC row. Each row's gate drives its own ADSR, and that ADSR drives the brightness of the matching OSC Out `row`.
  - The rows' pitch and gate go through **Poly Merge** into **CV to Notes**, then into the OSC Out `notes` input. The notes choose which LEDs light for the chord.
  - **Poly Split** (one poly input → 8 mono outputs) covers a poly chord source.
- **#356 resumes in B4, first:** Poly Merge plus Poly Split in one PR, with one catalogue and S0 change ([`0021` §6](../../proposals/0021-replan-to-ob1.md) D2).
  - Poly Split: input `in` (poly), outputs `out1`…`out8` (mono). Lane n carries channel n; a missing channel outputs 0.
  - Same gates as Poly Merge. A Golden difference is a defect.
- **B4 order:** #356 → S7.7 → S7.8.
- **Still parked:** Gate Delay #333.

Signed: claude-architect, 2026-11-23

## Decided 2026-11-23 14:30 ET: Architect run 19b — owner answered D1–D6 ([`0021` §6](../../proposals/0021-replan-to-ob1.md))

**In effect now.** The lead applies these and refreshes the lanes from the 0021 §6 table.
- **OB1 scope (OB r2.5):** E3a, E3b and E3c move to OB1.1. G-W1 [#368](https://github.com/kalharbi11/wirescape-lab/issues/368), Groove click-free scrolling, joins OB1 (B1, after #298).
- **Parked, branches kept:**
  - Gate Delay #333;
  - Poly Merge #356, until the owner answers on Poly Split;
  - #322, until CAT-1+MB;
  - CAT-1 #358 and MB1 #363, until after OB1.
- **B5:** one correction round on #324, then hand #324 to B2 (SR12). After that, start **T1.6c #364** (draft-ahead is allowed).
- **B3:** C1 [#367](https://github.com/kalharbi11/wirescape-lab/issues/367) is the CI digest and the chat-mode trial. Then S7.5 #291.
- **B4:** S7.7, then S7.8. The lead files the issues if they are missing.
- **Pi:** [PI-1 #369](https://github.com/kalharbi11/wirescape-lab/issues/369) brings private minutes to zero. The repo stays private. It waits for the owner's token. The lab half goes to B2; the Pi half is the Architect's.
- **Owner open items:**
  - Poly Split (yes or no);
  - the PI-1 token setup;
  - further Groove items on #368.

**Next run should:**
1. Review #298 when its inbox row arrives.
2. Contract-review T1.6c.
3. Once PI-1's lab half merges, do the Pi half on wirescape-pi.
4. Apply the owner's Poly Split answer.

Signed: claude-architect, 2026-11-23

## Decided 2026-11-23 12:40 ET: Architect run 19 — replan to OB1 (owner: "step back, zoom out")

Plan: [`proposals/0021`](../../proposals/0021-replan-to-ob1.md). Builders **finish the PRs they hold**. Nothing in flight stops.

**In effect now (lead applies these):**
- **R1 intake freeze:** no new module or feature task is filed until the Architect places it in a 0021 track. Ideas go to the list below.
- **R2:** one active PR per lane. The E-track writer (B5) may also hold one draft-ahead branch.
- **R3:** the critical path comes first. An off-path module PR that is red because of shared code parks behind CAT-1+MB and opens no new diagnosis loop. No gate or tolerance changes.
- **Engine draft-ahead (M3/M4 process ruling):** the single engine writer may draft task N+1 on a branch stacked on task N's head. Merge order and every "Depends on … merged" condition are unchanged. This affects T1.6c → TR1e → E6 → E4a → E4b → E5 only.
- **OB-c cause fixes (#275/#203) are B1's next task after #298.** Today no lane holds them, and OB1 acceptance 2 needs them.

**Pending owner decisions (0021 §5).** Until the owner answers, the lead keeps the current queue:
- **D1:** E3a/E3b/E3c move to OB1.1.
- **D2:** new modules stay frozen, and CAT-1 + MB1 become one task in B4.
- **D3:** B5 hands #324 to B2 and starts T1.6c; #322 parks behind CAT-1+MB.
- **D4:** the CI digest workflow gets `pull-requests: write`.
- **D5:** can chat mode write to GitHub?
- **D6:** what are the "GitHub credits"?

**Ideas parked until OB1 (R1):** any new module from `0020` beyond #333/#356; M3 MB2/MB3; anything in PRIORITY P4.

**Next run should:**
1. Read the owner's D1–D6 answers.
2. Apply them to OB.md, PRIORITY, BUILDERS and ROADMAP (contract revisions where D1 changes scope).
3. File C1 if D4 is yes.
4. Review #298 when its inbox row arrives.

Signed: claude-architect, 2026-11-23

