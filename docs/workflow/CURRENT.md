<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

The chronological lead–Architect handoff, newest first. Assignments live in [BUILDERS](BUILDERS.md),
delivery order in [ROADMAP](ROADMAP.md), open asks in the [inbox](ARCHITECT_INBOX.md).
**Older entries** (before Architect run 19, 2026-11-23 12:40 ET) were trimmed in run 22. They stay
valid where nothing below replaces them: [CURRENT as of `cdc8f14`](https://github.com/kalharbi11/wirescape-lab/blob/cdc8f144a66653fba66c78563c2e612ee0f4ba4b/docs/workflow/CURRENT.md) and
[the 2026-11-17 archive](https://github.com/kalharbi11/wirescape-lab/blob/cdc8f144a66653fba66c78563c2e612ee0f4ba4b/docs/workflow/archive/CURRENT-2026-11-17.md).

**Active lead:** `gpt-lead` (Codex); the Architect acted as lead in run 27 at the owner's request (run 28: Architect only; run 29: Architect also acted as lead). **Builders:** five ChatGPT chat lanes ([BUILDERS](BUILDERS.md)).


## Architect run 33 — 2026-11-24 20:15 EST: E7 approved and merged, A64 ruled (scheduled `architect:run`)

- **E7 #442** (Claude contract-review, lead pin 7148957226): [approved](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7149034643) at `2959f7e` and **merged `94d1b0b`** as a lead action, because it blocked B1 CN, B3 #457 and the E5 sync. C1/C2, A62 reply semantics, rollback and resource lifetime, G6 27/27×3 and G8 paired 100/0 were all checked at the exact head. Lows: L1, a note-off during the rule-1 gap can leave a note held (added to the owner's Pi checks); L2, the telemetry `groove_enabled` alignment; L3, the advisory instruction comparison is not G8. #431 closed; review labels cleared.
- **A64 / Q28 → [M7 r1.8](milestones/M7.md)** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7149046840)): for S7.6, the floor is max(old-value, target-from-start) over the r1.4 windows, and a row is met at ≤ +0.1 dB over it (a reading below meets). `mode` is met. `tone` is +0.307 dB: not met, a real defect to fix in the DSP. `division` reports its target control. `needs/architect` is removed from #314.
- **Dependents updated:** #457/#463 released to B3 ([comment](https://github.com/kalharbi11/wirescape-lab/issues/457#issuecomment-7149048964)). B4 #456 adds the division control and the endpoint columns ([comment](https://github.com/kalharbi11/wirescape-lab/pull/456#issuecomment-7149049811)). B1 now owns the A62 CN buffer rows. [BUILDERS](BUILDERS.md) B1–B5 refreshed.
- **Held:**
  - #291 S7.5 at `584e848` waits for B1's Result (Golden identical) and a new lead pin.
  - #449 S7.6 waits for #291, then the `tone` correction and the A64 evidence.
  - #444 S7.9 waits for the #467 windows-x64 facts failure, the D5 publish and a pin.
  - E5 #436 is a draft.

**Next run should:** (1) re-review #291 at B1's corrected head once Golden is identical and a pin exists; (2) review E5 #436 at a merge-ready pinned head; (3) review S7.9 #444 after the D5 publish and pin; (4) check that #463's ready diff adds only read-only status fields, with SR17 schema and regeneration (A61).

Signed: claude-architect, 2026-11-24

## Architect run 32b — 2026-11-24 19:45 EST: S7.5 independent review, changes requested (owner request)

- The owner assigned the independent Claude review of **S7.5 #291** to the Architect. Run 32's scout missed it because it carries `status/review`, not `needs/architect`. The scout brief ([ARCHITECT_SCOUT](ARCHITECT_SCOUT.md)) now covers every label containing `review` or `architect`.
- **Result: [changes requested](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7148569204) at `c1601bc`.**
  - **H1:** `reset()` leaves `mode_blend = 0`, so an LPG-at-load channel fades in from VCA over 10 ms. The declared golden difference (`quad-vca-01-lpg-plucks`, `mode1: 1` fixed, no switch) comes entirely from that startup fade, not from a mode change.
  - **Fix:** start each voice settled. Fail-first test: LPG output at load is bit-identical to before. Expect Golden identical.
  - K1–K5, K7, K8 and the r1.3(a) click (−38.443340 = floor; same `dsp.h` blob `28554d5` at `733cff4`/`c1601bc`) are fine. L1 (a voice leaving mid-fade) and L2 (an audio-rate assertion) do not block.
- **Held:** #291 does not merge; `review-required` stays. **Dependents:** B1's "After #291" queue item (Delay sync, A27 pins) waits for #291 to merge. **S7.6 #449:** the lead checks the same reset-default fade before its Result.

**Next run should** (on top of run 32's list): (4) re-review #291 at B1's corrected head once Golden is identical and the lead has pinned a new request.

Signed: claude-architect, 2026-11-24

## Architect run 32 — 2026-11-24 19:25 EST: quick check, no ruling due

- Inbox Open: A31 (Pi, postponed to the OB1 candidate) and A3 (MT2 #176, parked until OB1). Neither is ready. No open item carries `architect-ready`, and none has a pinned request that names the Architect.
- **E7 #442** `2959f7e` is now non-draft. Its ready-head Lab, Golden and M1 paired runs are still pending, and there is no signed Result or pinned request yet. **Held:** no Architect review until both exist at the live head.
- **#457/#463** stays draft and waits for #442 to merge, as A61 requires. **E5 #436** is a draft (`d10bfdf`). **S7.9 #444** waits for D5 (#464), its Result and a lead pin. **S7.5 #291** is pinned for `claude-reviewer`, which is not an Architect item.
- BUILDERS (19:10 lead refresh) still holds. Lanes are unchanged and no lane is idle.

**Next Architect run:** start `architect:run` once #442 has a signed merge-ready Result and a lead pin at an exact-head green head. That review is a Claude contract-review of medium-to-long effort. **Next run should:** (1) check that #442's reply matches A62 and that its Result names the version-only modules; (2) check that #463 stayed draft until #442 merged; (3) review E5 #436 and S7.9 #444 only at merge-ready exact heads.

Signed: claude-architect, 2026-11-24

## Manual lead continuation — 2026-11-24 19:10 EST

- S7.5 still awaits the owner's manual independent review. B1 localized the Delay peaks; B4 can collect matched steady-target mode and tone controls in [#456](https://github.com/kalharbi11/wirescape-lab/pull/456#issuecomment-7148160627) before a DSP correction or any Architect question. The existing A27 measure remains the acceptance evidence.
- B4 S7.9 ready Lab and three-platform Golden passed at `c86810e`. Two strict x64 LFO rows use the existing M7 r1.6 bound; ARM64 and Windows passed. [#464](https://github.com/kalharbi11/wirescape-lab/issues/464) provides the CHOKE fixture's required D5 pair. Contract review still waits for the pair and exact-head Result.
- E7 synced main at `2959f7e`, exact drift green and Lab under way. B3's diagnostic drafts [#462](https://github.com/kalharbi11/wirescape-lab/pull/462) and [#463](https://github.com/kalharbi11/wirescape-lab/pull/463) are open, with hosted serializer/schema still behind E7. B5's old scaffold failure cleared at `a80b847`; new `9530256` is the adopt/fade fail-first. No new Architect ruling or review response. The OB1 sequence and owner acceptance steps remain in the prior entry.

Signed: codex-lead, 2026-11-24, 19:10 EST

## Manual lead run — 2026-11-24 19:03 EST

- The owner ended the manager/Luna trial. The coordinator timer was already paused and [#402](https://github.com/kalharbi11/wirescape-lab/issues/402) is closed. Persistent sessions start manually. Every lead interaction starts with a minimal Architect/reviewer/B1–B5 check. Use small helpers and short event-based lead continuations as described in [CODEX](../../CODEX.md).
- B1 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) D5 published and release digests verified. The owner can start independent review at `c1601bc` with the [pinned K1–K8 request](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7147921470). [#449](https://github.com/kalharbi11/wirescape-lab/pull/449) endpoint correction passed Lab at `e772628`. Both A27 diagnostic captures ran; provisional mode and tone remain above floor. B1 continues the module correction before B4 repins.
- A62 and A61 applied to the queues. B2 continues E7's reply/schema/docs and version-only reset inventory. [#433](https://github.com/kalharbi11/wirescape-lab/pull/433) merged as `3277721` at `8cb9d2e` after exact-head Lab [45513094378](https://github.com/kalharbi11/wirescape-lab/actions/runs/45513094378), Golden 45513094318, paired 45513094313 and Offline 45513094094 passed. Advisory soak findings stay with #457/A58. B3 can draft hosted exposure [#457](https://github.com/kalharbi11/wirescape-lab/issues/457) behind E7 and has [#459](https://github.com/kalharbi11/wirescape-lab/issues/459) for E5v attribution. B4 is running full S7.9 evidence after A63 passed Lab. B5's E5 test fails line 615; correction stays with its current writer.
- **Next Architect run:** owner starts `architect:run` once E5, E7 or S7.9 has a signed merge-ready request, or a fresh ruling is needed. Start S7.5's independent review separately. [BUILDERS](BUILDERS.md) holds every lane's next task.
- **OB1 route:** E5v/E5/E7 and CN, then remaining M7/D5 and OB-d, OB-f1 and owner-folder checks, candidate Pi install and owner edit checks, then Architect acceptance and tag.

Signed: codex-lead, 2026-11-24, 19:03 EST

## Decided 2026-11-24 ET: Architect run 31 — A62 and A61 ruled (wake: #431 `architect-ready`)

- **A62 / Q26 → [M4 A62](milestones/M4.md):** E7 `freshModules` lists what the host did not carry (no hook, save/load not OK, no ID/type/config match). A hook that returns OK counts as carried, and no per-type lists go in host code. Version-only resets (delay, reverb, resonator tails; note converters) are named in the E7 Result and report under M4 Escalate. SR17 schema, regeneration and the `ENGINE_PROTOCOL.md` reply paragraph join #442's paths. CN `setBufferFrames` smaller/larger rows go to B1 after #442 merges; the larger row adds a nontrivial-state witness. No threshold change. `architect-ready` and `needs/architect` are removed from #431; `review-required` stays (Claude contract-review at E7's merge-ready head).
- **A61 / Q27:** native-only OSC diagnosis accepted. #433 merges under `merge: lead` at its exact-head green. Hosted exposure is new task [#457](https://github.com/kalharbi11/wirescape-lab/issues/457) (B3): draft-ahead now, ready after #442 merges (`session.cpp` single writer). No product fix until a hosted sample shows nonzero split counts. `needs/architect` is removed from #424.

**Next Architect run:** `architect-ready` at E7 #442's merge-ready Result (Claude contract-review, medium–long effort), or E5 #436 at its merge-ready head. **Next run should:** (1) check that #442's reply matches A62 and that its Result names the version-only modules; (2) check that #457 stayed draft until #442 merged; (3) review E5 only at an exact merge-ready head.

Signed: claude-architect, 2026-11-24

## Lead continuation after Architect run 30 — 2026-11-24, 18:34 EST

- A63/M7 r1.7 released B4 #444 at d85c076, exact independent oracle only in vco(), no tolerance, no other engine edits; B5 #436 has no overlap. Removed stale blocked/needs labels from #440/#444; review-required retained. #451 independent while #444 checks run. MIDI sanitizer failure remains under B2 triage.
- B2 #442 exact 0f6d33b targeted 45508936363 and all 15 Lab jobs 45508926651 pass; draft Golden/paired skipped. A62 remains pending, C2 module refusal not independently verified. B1 #449 exact 83a86e5 Lab 45508971575 fails native and sanitizer; endpoint assertion correction stands. #291 D5 hold unchanged.
- B3 #441 and B5 #436 unchanged; SR6 round 2 and A55/A59 implementation respectively. All five signed continuation packets linked in BUILDERS; chat pickup requires owner trigger. A61/A62 remain open; next Architect wake A62 on #431 (after run 30 completed).

Signed: codex-lead, 2026-11-24, 18:34 EST

## Decided 2026-11-24 ET: Architect run 30 — A63 granted (wake: #440 `architect-ready`)

- **A63 / Q25 → [M7 r1.7](milestones/M7.md):** S7.9 #444 may edit only `vco()` in `engine/tests/port_behavior_tests.cpp`. The CHOKE phase-reset assertions retire as an intended S7.9 sound change and are replaced by an independent oracle (twin first sample, analytic 220 Hz continuation, exact equality, no tolerance). No B5 PR touches the file. The MIDI sanitizer red on #444 is not covered. `architect-ready` and `needs/architect` removed from #440; `review-required` stays (contract-review at the merge-ready head).
- **Held:** A61 (OSC hosted fields) and A62 (E7 reply/state witness) are "soon", not now; they need the next run. Nothing else changes in the lanes; the lead's 18:24 dispatch stands.

**Next Architect run:** `architect-ready` for A61/A62 (medium effort), or E5/E7/S7.9 at merge-ready exact heads. **Next run should:** (1) rule A62 before #442's final reply; (2) rule A61; (3) check #444's r1.7 diff touches only `vco()`.

Signed: claude-architect, 2026-11-24

## Owner-authorized manual lead run — 2026-11-24, 18:24 EST

- **Merged [#448](https://github.com/kalharbi11/wirescape-lab/pull/448)** (closes #443) as `95e18ff9ad0862de308c31921c15898d46367dfd` at reviewed `64c55bdf87c475937286ccc94278e89b38cef442`. [Pre-merge review](https://github.com/kalharbi11/wirescape-lab/pull/448#issuecomment-7147331880), Lab 45487715646 (15/15), Golden 45487715557 (3/3), paired 45487715558 (3/3), stress 45485261020 (2/2). SR20(c); test-only pacing, no relaxed assertions. Ordinary merge rejected by repository policy, squash used. Original Windows scheduling hypothesis unconfirmed. **B5 E5 #436 released**; keep A55/A59 and disjoint E7/voice ownership.
- B1 #291 numerical evidence holds but release upload unavailable; D5 and independent K1–K8 review still required. #449 head 83a86e5 both sanitizer tests fail endpoint assertion line 640; SR5 fixture/DSP diagnosis, no rerun to green. **#451** additive A27 fixed-window evidence route released to blocked B4 under SR18/SR1/SR19.
- B2 #442 head 0f6d33b (production 6f5b74a); A62 exact pin refreshed, fake-backend rollback test pending. Read-only triage of unrelated MIDI sanitizer failure on #444, no causal claim or product task yet.
- B3 #441 head 27f9881 Lab/Golden green, paired 45507409122 x64 keyboard voices1/8 +1.148095955/+1.126998163%; ARM64 and Windows green. **SR6 round 2** correction; changed-module rows do not qualify r1.6. **#452** source-pinned CN evidence-only workflow queued under SR18/SR1 after G8 passes; held-note silence 0 ms is mandatory, no metric change. #433 still A61.
- B4 #444 blocked at d85c076: three native failures on obsolete VCO phase-reset assertion, scope outside M7 K5. **A63/Q25** asks narrowly for only the vco() test change, with B5 coordination (SR7 does not fit). Independent #451 while waiting; S7.9 resumes first on ruling.
- Labels: #443/#448 closed status removed; #288/#291 blocked on D5 with review-required retained; #442 needs/architect; B1 environment labels aligned. No reviewer dispatched early. All lanes have signed continuation comments; direct chat pickup not verified. Shared Codex usage and release/dispatch endpoints are unavailable from this manual ChatGPT connector; no account-setting change or usage assumption.

**Next Architect run:** A61 OSC hosted exposure, A62 E7 reply/state witness, A63 S7.9 K5 scope. Review E5 and E7 only at merge-ready exact heads. No Pi work before OB1 candidate. Route: E5v/E5/E7 + CN, M7 batch 2/D5/reviews and OB-d, then OB-f1 and owner-folder check, candidate install and owner Pi 100 edits, zero xruns, no visible stutter, both CN costs; Architect acceptance/tag.

Signed: codex-lead, 2026-11-24, 18:24 EST

## Lead quick check — 2026-11-24, 16:07 EST

- B1 posted the exact-head S7.5 numerical Result on [#291](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7144258674); D5 release publication and independent review remain. S7.6 [#449](https://github.com/kalharbi11/wirescape-lab/pull/449) is draft-ahead.
- B2 posted the E7 disjoint-path plan and two fail-first probes. [#442](https://github.com/kalharbi11/wirescape-lab/pull/442) continues at `6f5b74a`. A62 requests the capture ownership, witness and reply ruling; E5 precedes E7 if they share `commit`.
- B3's [#433 Result](https://github.com/kalharbi11/wirescape-lab/pull/433#issuecomment-7143352337) does not reproduce natural drops. A61 requests serializer scope before hosted attribution or a product-fix release. E5v [#441](https://github.com/kalharbi11/wirescape-lab/pull/441) is independently ready for evidence; paired and CN witness remain.
- B4 [#444](https://github.com/kalharbi11/wirescape-lab/pull/444) fast-forwarded to the two-parent sync `d85c076` with its five-file diff unchanged. B5 runs [#448](https://github.com/kalharbi11/wirescape-lab/pull/448) at `64c55bd` before resuming [#436](https://github.com/kalharbi11/wirescape-lab/pull/436); draft Lab and E4b stress passed, ready-head checks are pending.
- OB1 still needs E5v/E5/E7, refreshed CN evidence, remaining sound and OB-d/OB-f1, then the owner’s candidate-only Pi checks and Architect acceptance.

Signed: gpt-lead, 2026-11-24

## Lead release — 2026-11-24 ET: all five lanes reopened

- Merged [OB-c #275](https://github.com/kalharbi11/wirescape-lab/pull/275) as `6d2de36` at approved `3aad6e3`. Required Lab, Golden, paired and A10 green; advisory Windows Offline was explicitly tracked under #406. Owner approval and S7.3 release are recorded in the [#275](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7141836048) and [#202](https://github.com/kalharbi11/wirescape-lab/issues/202#issuecomment-7141838083) comments.
- Merged [E4b #416](https://github.com/kalharbi11/wirescape-lab/pull/416) as `cb25a2c` at approved `8e8783b`. Repository disables merge commits; used the explicit A40 fallback. Preserved E4a checkpoint `b3e11ea3242aa2711054c0b177002e85499c8d9c`, Golden 45369039868, Lab 45369040002 and paired G8 45369039828 in the merge message and this record. Architect accepted A50 repeat-noise explanation. CN harness #422 uses branch-protected auto-merge; B1 refreshes facts in #430 before M4 acceptance.
- Merged [#419](https://github.com/kalharbi11/wirescape-lab/pull/419) as `7096cdf` at `40e1a11`. Required Lab passed; four advised soak failures remain documented product findings. Architect run 28b released B3 #424 (diagnostics only) and B2 #425 (session-cumulative MIDI). B2 E7 #431 follows #425, with the shared E5/E7 commit gate.
- B4 S7.3 #428 begins under the owner’s run 28c B4 alternative. Verified all 12 gated T7.0 before-numbers on main. B5 E5 #429 begins the stopped-stream settle Low and pre-code inventory; real voice-count replacement waits for the [scope ruling](https://github.com/kalharbi11/wirescape-lab/issues/429#issuecomment-7142199713).
- The owner closed the Terra/Luna batch. These lanes were released directly to existing builder chats. Cycle limits apply to coordination and usage; released builder queues follow their contracts independently.

Next Architect work: resolve E5 voice-count replacement scope, then use #424's result to pick the OSC fix and review E5 once its implementation and evidence are ready. OB1 next; the owner’s candidate Pi acceptance remains pending.

Signed: gpt-lead, 2026-11-24

## Decided 2026-11-24 ET: Architect run 29c — S7.3 merged, A60 (owner: resolve #432's blockers)

- **#432 S7.3 approved and merged `fe321f9`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/432#issuecomment-7143875832)). T7.0 45478143094 passes all 12 gated rows. The Golden declaration was widened to the nine CHAOS patches (K6), and Golden 45480416512 is green. The CHAOS Ir increases are under the 15 % cap, with `Cost-change:` lines. D5: chaos-01-ember-veil-pad, artifact 14960795824.
- **A60** (M7 r1.6a): r1.6 also covers S7.3, plus a named exception for function_envelope voices1/8, linux-arm64, ≤ +3.0 % (it reproduced at +2.106/+2.605 %), expiring at CAT-1 or the OB1 tag. An issue's `Sound-change:` line is only an example.
- **B4 → S7.9 #440.**

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 29b — A59, T7.0 dispatch, Windows replan red (owner: Architect also acts as lead)

- **S7.3 #432:** full T7.0 capture dispatched as lead: [run 45478143094](https://github.com/kalharbi11/wirescape-lab/actions/runs/45478143094) at `d86c195`, both Linux architectures, compared with baseline 44029050283.
- **A59 E5** ([#436](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7143183539), M4 note): `tools/module/runner/abi_ws2.h` size guard granted (0012 G5), C99 offset and legacy-size tests, and a bounded held-note record replayed after `collect()`'s clear. B5's fail-first at `11b0caa` came back red ([dev-run 45475307438](https://github.com/kalharbi11/wirescape-lab/actions/runs/45475307438)); B5 confirms the assertion line.
- **#434 Windows red** in E4b `signal_ramp_interrupted` (line 349), which #434 doesn't touch. Filed [#443](https://github.com/kalharbi11/wirescape-lab/issues/443) → B5 (test-only pacing fix, own PR, before #436). Failed job re-run once to classify; [disposition](https://github.com/kalharbi11/wirescape-lab/pull/434#issuecomment-7143209103): green → lead merges #434 and E7 is released; red → #434 waits for #443.
- **#434 merged `4b078f9`** (closes #425) after the Windows re-run passed. Every required check was green; the advisory OSC soak rows stay under #424. **E7 #431 released to B2.**
- **Held:** nothing new beyond run 29.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 29 — roadmap revised, A55–A58 (owner: Architect also acts as lead this run)

- **#438 roadmap** revised and merged: live editing first, sound in the free lanes, I/O fixes beside them ([ROADMAP](ROADMAP.md) reconciliation section).
- **A55 E5 scope** ([M4](milestones/M4.md)): voice count stays a live parameter. **E5v [#439](https://github.com/kalharbi11/wirescape-lab/issues/439)** (B3, `merge: lead`) adds in-place `Allocator::resize` (keeps the voices that fit). E5 (B5) = same-descriptor config replacement with ER4, adopt/ring-out, fade, settle Low. `needs/architect` removed from #429.
- **A56 sound unparked** (M7 r1.6, OB r2.9): S7.5 #291 → B1 (takeover), S7.6 #314 → B1 after it, S7.9 [#440](https://github.com/kalharbi11/wirescape-lab/issues/440) → B4 after S7.3, then OB-d. Bounded paired exception: rows without a changed module, linux x64/arm64, ≤ +2.5 %, expires at CAT-1 #358 or the OB1 tag. Note Trigger #322 → B3 after E5v (optional OB1 row).
- **A57 fewer stops** → [STANDING SR20](STANDING.md).
- **A58 OSC routing** (pre-ruled on [#424](https://github.com/kalharbi11/wirescape-lab/issues/424)).
- **Lead actions:** #437 CN facts merged `ba17d7e` (closes #430); #427 closed (superseded: its run 28b text is already on `main`).
- **Held:** E7 writes to `host/sidecar/session.cpp` wait for B2's disjoint-path plan, or for E5 to merge. B5 does not edit `engine/voice/` while E5v is open.

**Next Architect run:** `architect-ready` on #429 at E5's merge-ready Result (long effort: Claude contract-review against ER4, 0012 §4, G1–G9). Quick check before that if #433's split counts need a design call (A58 says when). **Next run should:**
1. Check that #437 and #438 merged, and that B1 picked up #291 on current main.
2. Check that E5v's Result shows the CN voice-count row at held-note silence 0 ms.
3. Check that any r1.6 paired exception listed in an M7 Result is ≤ +2.5 % on a graph without the changed module.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 28b — E4b approved, OB-g7 rulings (owner: run all pending reviews and rulings)

- **#416 E4a+E4b approved `8e8783b`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/416#issuecomment-7141760132)). G1–G8, ER3, ER5 and A51 hold. The 18 E4a dip-range differences are repeat noise: the same park fade lands on a different block. The lead merges with a merge commit (A40). `review-required` and `needs/architect` are removed. One Low for E5: while the stream is stopped, `settle_layout` spends three block periods on each status tick. Before M4 acceptance, CN harness #422 must merge and `facts/dsp/edit_continuity.md` must be refreshed.
- **#417 OSC → [#424](https://github.com/kalharbi11/wirescape-lab/issues/424) (B3)**: product delivery loss. Split the drop counters and write a fail-first soak-profile test before any fix.
- **#417 MIDI → [#425](https://github.com/kalharbi11/wirescape-lab/issues/425) (B2)**: not E5. MIDI counters stay cumulative for the session across `Host` stop/start; B2 takes it after #406 (merged) and before E7.
- **Held:** E5 waits for the #416 merge. E7 waits for E4b, and E5 merges first if both touch `commit`. #275 is with the lead to merge.

**Next Architect run:** `architect-ready` at the #424 Result to pick the OSC product fix (medium effort), or at E5's Claude contract-review (long). **Next run should:**
1. Check that #416 merged as a merge commit at `8e8783b`, and that #275 merged.
2. Check that E5's pre-code post (voice-count behaviour) carries the settle-stall Low.
3. Read #424's split counts and choose the OSC fix and its lane.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 28 — #268 OB-c approved, A40 shape (wake: #268)

- **#275 OB-c approved `3aad6e3`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7140594351)). The A52 identity check finds no identical origin. The strict xfail `P1_STARTUP_MASTER_FADE_VS_UNITY_PANIC` applies only when the loadGraph fade explains every tail sample exactly (83456 of 83456 at origin 29568); an XPASS or an unexplained mismatch is red. The lead merges. Whether panic itself should fade is an OB1 design question, not a defect here. `needs/architect` and `architect-ready` are removed from #268.
- **A40 shape for #416** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/416#issuecomment-7140596739)): keep the ten commits and integrate with a merge commit; `b3e11ea` is the E4a revert point.
- **Held:** #416 E4b merge waits for the lead's CN continuity rows at the exact head (no waiver), then the Claude contract-review. #417 OSC/MIDI rows (soon) are not ready-labelled yet. B4 idles under Cycle 2.

**Next Architect run:** `architect-ready` on #414 once CN evidence and the pinned request are posted (long effort: contract-review against G1–G8, ER3, ER5, A51), or on #417 for the OB-g7 OSC/MIDI dispositions (medium). **Next run should:**
1. Check that #275 merged at the approved head (or a merge of main with A10 still green).
2. Check that #416's CN rows cover every swap command, applyGraph structural change, the E4a repeat-noise comparison and the latency probe.
3. Read #417's OSC/MIDI findings and assign the owning lane.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 27 — A51–A54; CI2 merged (owner: Architect also acts as lead this run)

- **CI2 #393 merged `0056d4f`** (A54). K1 holds: native 120 → 120 and sanitizer 94 → 94 by exact name, Studio 386, Desktop 27. The draft target of under 10 min was missed (16m54s, 9m19s of it queue): recorded, not waived. **From now on, drafts skip Golden, M1, Instruction, Offline, OB-g7 and Portability.** A builder who needs exact-head evidence marks the PR ready for review (not the `review-ready` label). `main` pushes and ready heads run everything.
- **B2 unblocked.** `offline-facts.yml` is B2's, and Offline was dispatched on `task/399-offline-windows-build` at `b6f86e9` for the Windows failure output ([#406](https://github.com/kalharbi11/wirescape-lab/pull/406#issuecomment-7128155286)).
- **A51 → E4b publication** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/414#issuecomment-7128145573), M4 E4b note): pointer, bounded wait for adoption, then `published_revision`, then true. A timeout CAS win returns false with nothing exposed. An output-less removed instance is not carried into the transition layout. ASan regression for removing an OSC Out. No facade or sidecar change.
- **A52 → #275 P1** (OB r2.8a): G1 passes. P1 passes every A45 gate; the extra landmark check becomes post-reset sample identity with a first-mismatch report. `needs/architect` removed.
- **A53 → S7.8 #405 [approved `fbb3ccd`](https://github.com/kalharbi11/wirescape-lab/pull/405#issuecomment-7128153863)**, with three Lows. The paired reds are Ladder rows under r1.5(b), all < +3 %. `review-required` cleared. **Lead:** publish D5 (scene-02 SHA256s in B4's Result), then merge after B4 marks it ready.
- **B3 → [#417](https://github.com/kalharbi11/wirescape-lab/issues/417)**, the OB-g7 row diagnosis.
- **#408 closed**: superseded, since A44 is already on `main`.

**Lead, in order:**
1. D5 and merge #405.
2. CN control-differenced continuity witnesses in `bench/continuity/` before E4b's evidence (A50, still open).
3. Merge #406 when its three Offline jobs are individually green.
4. Release E7 to B2 when E4b merges.

**Held:**
- E4b code waits for Golden identity at the E4a head.
- E5 and E3a wait for E4b; E7 waits for E4b.
- #291, #314 and S7.9 stay parked under R3 (CAT-1 + MB).
- S7.3 waits for the #275 Result.

**Next Architect run:** `architect-ready` on #414 at its E4b Result (long effort: the Claude contract-review against G1–G8, ER3, ER5 and A51), or on #275 once P1 is signed (quick). **Next run should:**
1. Check that #275's P1 now uses sample identity, and whether an origin matched.
2. Check that #416 showed Golden identical at the E4a head before the E4b commit.
3. Check #417's per-row dispositions for any product defect that needs a lane.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 26c — E6 merged; E4a+E4b released to B5

- **E6 #395 merged `3286602`** at the approved head `2d1db86`. The Architect merged it at the
  owner's direct request, because the lead was out of usage. The signed Result is
  [on the PR](https://github.com/kalharbi11/wirescape-lab/pull/395#issuecomment-7127697716).
- **Advisory OB-g7 L0 rows were checked, not waived.** `midi-m8/config-edits` ("received count
  decreased") fails the same way on #393 `8b186fe`, #395 `ab50d23` and #383 `9507378`, so it
  predates E6. `windows midi-m8/still` (`overruns=10`) had no edits. These rows are advisory
  (OB r2.4a).
- **E4a+E4b → [#414](https://github.com/kalharbi11/wirescape-lab/issues/414), B5.** One PR, two
  commits (A40). The issue folds in the E6 Low on `find_mod_edge`. E4b's witness rows need the
  CN control-differenced metrics (A50). **Lead:** CN adds them in `bench/continuity/` before
  E4b's evidence. The direct-loader `fprintf` Low goes with E3a or E5.
- **Unblocked by E6:** E4a+E4b now, then E5/E3a; E7 (B2) after E4b.

**Next Architect run:** `architect-ready` on #414 at its Result (Claude contract-review), or on
#275 once the OB r2.8 rewrite is signed. **Next run should:**
1. Check that #275's P1/G1 match OB r2.8 exactly.
2. Check that #399's fail-first test landed before its fix.
3. Check that #414's E4a commit leaves Golden identical before its E4b commit.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 26b — E6 #395 approved `2d1db86` (owner: lighten the lead's run)

- **A50 correction.** The capture cannot show the subject's `restarted` for an edit that changes
  its sound: `bench/continuity/run.py:112` returns `None` on purpose. For a data edit the property
  is "no instance rebuilt or reset". It is shown by `setModAmount` returning before any candidate
  or commit (`session.cpp`), `set_mod_amount` only pushing an edge packet, and the protocol test's
  unchanged generation (1 → 1 in all repeats). No new capture is needed.
- **E6 contract-review: [Approved for merge `2d1db86`](https://github.com/kalharbi11/wirescape-lab/pull/395#issuecomment-7127643131).**
  No High or Medium findings. Two Low follow-ups: the direct loader prints warnings with `fprintf`
  (return them instead; E3a/E5), and `find_mod_edge` versus removed same-key edges (assert; E4a).
- **Lead, minimum steps:** mark #395 ready, post a three-line signed Result that links the
  approval, and merge it (`merge: lead`). A new push voids the approval, except a pure main merge
  with Golden unchanged. Then release E4a+E4b to B5 (A40, one PR, one Claude review).

**Next Architect run:** `architect-ready` on the E4a+E4b issue once its Result is posted, or on
#275 once the OB r2.8 rewrite is signed. **Next run should:**
1. Check that #395 merged at `2d1db86`, or that its only delta is a main merge.
2. Check that #275's P1/G1 match OB r2.8 exactly.
3. Check that #399's fail-first test landed before its fix.

Signed: claude-architect, 2026-11-24

## Decided 2026-11-24 ET: Architect run 26 — A50, A45, A46, A47 (wake: #391)

- **Run 25 (#409) lands with this PR.** A44 stays cleared as written there.
- **A50 → E6 witness gate met by identity, E6 only.** M4 asks what the edit does to an untouched
  witness. The harness computes `silence_ms`/`dip_db` from the witness alone. The no-edit controls
  give the same tone/tail/held-note numbers, so those numbers describe the witness, not the edit.
  A witness that is **sample-identical** to its source-pinned no-edit control over the whole window
  (48,000 samples before the edit through 48,000 after the bracket) has edit-induced silence 0,
  dip 0, slip 0 and jump 1. That is stricter than every threshold. **Conditions:** the E6 Result
  cites [run 45363157562](https://github.com/kalharbi11/wirescape-lab/actions/runs/45363157562)'s
  raw artifact with the identity per witness and repeat, and shows the subject's `restarted`
  false. **Harness:** CN adds control-differenced metrics before E4a's row, which cannot be
  sample-identical. No tolerance changes. **What would overturn this:** any witness not identical
  in any repeat, or a control not pinned to the same source.
- **A45 → P1 oracle corrected (OB r2.8).** ABI2 `panic()` MUST reset processors
  (`ABI2_SPEC.md:69`). My r2.1 bit-identity oracle contradicted that, and the written spec wins. The
  owner-reported defect is the gap (KNOWN_ISSUES: 306 ms on the Pi). P1 now gates the gap: no
  missing or repeated frames, 0 overruns, and no silent block after the reset boundary past the
  reported latency. Bit identity is reported only. P4 (`click_events` after panic) still catches an
  audible click. A release-only user panic is a new command (R1 intake freeze), so it goes on the
  ideas list for after OB1. **Would overturn:** the owner saying the phase-reset click itself is
  the reported problem.
- **A46 → G1 oracle corrected (OB r2.8).** Groove STOP is documented to queue to the cycle end
  (`modules/groove/README.md:43`, DESIGN G3 release-safe Apply). G1 is now `running` = 0 within
  one block of the documented cycle-end frame. START is unchanged. An immediate-stop command would
  be a new feature (ideas list). **Would overturn:** the owner saying the lag they reported was the
  quantized stop.
- **A47 → granted narrowly.** CI2 #393 keeps `.github/workflows/t7-0-capture.yml` byte-identical. It
  retires in the task that completes #291's M7 evidence, or by OB1 acceptance, whichever comes
  first. The other seven A42 retirements stand.
- **Builders:** no lane is idle. B1 gets the oracle rewrite on #275, B5 the E6 Result, B3 the
  K1 Result, B2 #399, B4 #374.

**Held:** E4a+E4b until E6 merges. A31 and A3 stay parked.

**Next Architect run:** `architect-ready` on #391 once E6's signed Result is posted. It is the
ER1/ER2/ER6 contract-review. Medium effort. **Next run should:**
1. Review E6 #395 against ER1/ER2/ER6, A44, A50 and the A38 Low assert.
2. Check that #399's fail-first test landed before its fix.
3. Check that #275's rewritten P1/G1 match OB r2.8 exactly.

Signed: claude-architect, 2026-11-24

## Lead routing update — 2026-11-24 03:32 EST

- A44 wake moved from draft PR #395 to linked issue #391 to match the Issues → Labeled trigger.
  Confirm Architect pickup separately. B5 can implement the in-scope E6 core now.
- B1 signed both strict OB-c failures at `070db7a`. A45 and A46 hold only the two cause-specific
  source fixes. B3 restored the still-used T7.0 capture workflow; A47 confirms the A42 deferral.

Signed: codex-lead, 2026-11-24, 03:32 EST

## Decided 2026-11-24 03:32 ET: Architect run 25 — A44 ER6 load ingress granted

- **A44 → granted, load-only ([0017 ER6](../../proposals/0017-final-rulings-and-succession.md#er6-duplicate-modulation-cables-e6)).**
  ER6 says the loader does not refuse, and `loadGraph` is how a saved patch is loaded, so the
  sidecar ingress is part of "the loader". E6 may add to `host/sidecar/session.cpp`, in the
  `loadGraph` branch only, one call before `commit(..., true)` that coalesces duplicate
  **modulation** cables.
  - **One rule, one place.** The coalescing function lives in `host/document/runtime_patch.*`. The
    sidecar ingress and the direct loader both call it. Identity is kind/from/to. Keep the
    first cable's position and metadata, add later amounts, clamp to ±1, and give one warning per
    coalesced identity that names the cable. Warnings use the existing sidecar warning/response
    channel. A new message field needs a spec row in the same PR.
  - **Unchanged:** `Session::execution` keeps its duplicate refusal, so `applyGraph` and `connect`
    still return the structured `duplicate` refusal. Duplicate **signal/event** cables still refuse
    on load (ER6 covers modulation only). A single stored amount outside ±1 still refuses.
    No other validation or publication path changes.
  - **Tests (fail-first):** `loadGraph` with two duplicate modulation cables loads one cable with
    the clamped sum and a warning. The same patch through `applyGraph` and two `connect`s is
    refused with `duplicate`. A duplicate signal cable on `loadGraph` is still refused.
  - **What would overturn this:** a golden difference, or a bundled patch that changes on load.
    The 24/24 scan found none.
- **Held:** nothing new. E6 still needs its Architect contract-review on the final Result
  (`architect-ready` on #391 once posted). E4a+E4b waits on E6.

**Next Architect run:** `architect-ready` on #391 once E6's signed Result is posted. It is the
ER1/ER2/ER6 contract-review. Medium effort. **Next run should:**
1. Review E6 #395 against ER1/ER2/ER6, the A44 grant above, and the A38 Low assert.
2. Check that #399's fail-first test landed before its fix.
3. Refresh BUILDERS.

Signed: claude-architect, 2026-11-24

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

