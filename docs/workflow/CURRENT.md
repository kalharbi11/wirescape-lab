<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead. Last verified main: `cc1c223ca7239666c56d4ec0462cdf34b7fe74f8`.

**Sole LOCAL root lead:** WLAB | LEAD | 5, `01a1e688-a40c-7273-ab2a-3100d5731573`. Local app inventory and CODEX_THREAD_ID agree. Lead 4 is idle/stepped down. The existing `wlab-lead-review` heartbeat is ACTIVE every 45 minutes on this verified ID; no new timer. Scoped M1 delivery is delegated below.

## Contracts and acceptance

- **M0 r3:** **ACCEPTED AND CLOSED by Fable, 2026-11-16** against report #132. Every exception has a disposition in [M0.md](milestones/M0.md) "Milestone acceptance". T0.14 is no longer an M0 gate (owner environment item; the seeding recipe below stays the working route). No lead action remains on M0; drop it from the heartbeat.
- **M1 r2:** S0/T1.1/P1 merged. S2 #111 belongs to delegated LOCAL lead `01a1e676-f444-7653-839e-8659fb7209af`; B4 regular Chat `6afb8252-992c-83ea-a4d0-e7734bb17b7b` is sole writer. Root does not duplicate S2 dispatch. Owner-authorized additions: `native/cli/play.cpp` and `native/document/runtime_patch.cpp`, only obsolete ABI1 discovery/registration removal; [QUESTIONS Q15](QUESTIONS.md) records the resolution. M1 lead owns planning, execution verification, independent review, corrections and delegated merge. Release delivered, one startup retry sent, implementation execution unverified. S3 staffing/start remains owner decision.
- **M2 r3:** E0 and E1a merged (E1a #116 → e0d4437). E1b #125/PR130 is held after final ordinary correction; Q14 needs Fable. PV1 #86/PR105 Q13 revert-and-record disposition applied; exact-head acceptance pending.
- **CI1 r3:** CI1.1/1.2/1.4 merged. CI1.3 #109/PR129 retains sole ci.yml ownership, sanitizer job only. K7/K8 unchanged; missing warm evidence holds merge.

## Writers and next actions

| Writer | Task / branch / head | Verified disposition |
|---|---|---|
| B1 | #125 / #130, task/125-studio-apply-graph, `8d0bd29467d1b505c8ac9838fc267301e4537cc0` | final ordinary 2/2 spent; Lab43968790557 red Studio1/3 + aggregate; independently confirmed overlap/refusal rollback HIGH; Q14 proposed bounded final packet, no redispatch before ruling |
| B2 | #109 / #129, task/109-sanitizer-ccache, `21bc87c405be6813cdbc9bb382c9058d3f4b35c8` | full43964380415 attempt2 green; sanitizer133653972206 cacheMISS/428s/49 of274 hits is cold, K8 unmeasured; branch stable, no blind rerun |
| B3 | #86 / #105, task/86-pv1-protocol-v0, `8c15a941c1a4e21c4616d20ea5bdfe2a75e27f35` | Q13 3/3 spent; lead reverted only new missing-paramId negative fixture to prior absence and recorded D09; normalized duplicated D08 text; fresh Lab43973824231 + drift43973824173 in progress at inspection |
| B4 | #111, task/111-s2-native-catalogue planned | delegated M1 lead owns startup check; latest implementation release has no substantive assistant result yet; do not claim execution |
| Claude builders1–3 | finished/stopped | no new tasks |

## Review evidence and holds

**PV1:** previous8b23600 Lab43967315210 passed all14 jobs, drift43967315137 failed TS2578 at test_generated.ts123 and intended TS2741 at125. The new incompleteApplyResult fixture and void reference were absent at prior e984561; Q13 point5 authorized reverting this item. D09 neutrally states the unretained compile-time coverage. applyGraph schema/type/corpus, bus_channel0..15, Q8 and unknown-field preservation remain; generators unwired. D08 factual Desktop-space discrepancy preserved after removing duplicated embedded document text. Require NEW exact-head corpus/TS/C++/drift/null-sidecar Q8/Q13, full required CI and M2 acceptance4. No fourth builder round or red waiver.

**E1b:** from confirmed220, queued snapshots440 then660 both reject, but latest revision restores optimistic440 while engine stays220. Root independently traced App.ts788–802 and RealEngine.ts338–348 after Worker2 review. Separate OSC test failure is a live counter-reference alias (test216–217, setter286–290), not proven runtime replacement failure. Q14 asks Fable for one bounded final packet or defer/close; hold draft/blocked. No third ordinary correction.

**CI1.3:** manual43966200132/head21bc87c cold-saved cache10628646155 at refs/heads/task/109-sanitizer-ccache; key fingerprint0471e1e.../run43966200132-1, version b97fbe098767aae2aa5efb5d4f8da4e488678a6aaf72931965bfb19f3ef9e00a, size102097945. PR attempt2 explicitly missed this prefix. Official cache docs permit feature-branch restores; cause remains unproved, not assumed merge-ref isolation. Same image/action/path/cross-OS inputs observed. Worker2 read-only diagnosis complete; compare exact bundled version inputs/lookup before any further run, no blind timing retry. K7 independently compared hosted base133628142310 and exact-head133653972206 ordered ctest -N -R abi2 inventories:82 names each, equal/zero additions/deletions. K8 needs genuine restored warm <=318s; cold428s establishes neither warm pass nor warm failure. No bootstrap merge, PR cache save or settings change.

## Operating rules and routes

B1 regular Chat `6afadca6-071c-83ea-a029-b22c1560a794`; B2 `6afadc8d-5138-83ea-bb36-88048b6bf54d`; B3 `6afadc7c-9b44-83ea-be32-dbd465646ce0`; B4 new route above (old6afadc5f superseded). Worker2 cloud support `6afad0f1-55a8-8191-975f-f008479ba02f`, host durable. Verify actual execution/results before one supported retry; delivery/active flags alone do not prove execution. Keep GPT builders in regular Chat, never Work/Codex substitutes.

Lead does reviews. Fable handles design/questions/acceptance and merge:fable only; Fable does no PR monitoring. Notify owner if a contract requires a Claude reviewer; owner assigns one. S2 requires none; later S3/S5b/S6 require contract review. No new Claude builder tasks. Preserve one writer per task, existing branches, full rerun-all for failed aggregates, one cohesive push per round; two ordinary corrections then QUESTIONS except explicitly authorized Q13.

Keep byte-identical dependency-seeding recipe (git archive --prefix=<repo>-<sha>/ FETCH_HEAD | gzip -n; verify URL_HASH), configure CMake again after session.cpp changes because S0 copy occurs at configure, and native OSC Out replacement semantics. Preserve devices-off/realtime/neutral-facts rules; no force/settings/gate weakening. Keep >=20% five-hour usage reserve; no credit/reset spending. No model waits/polling loops; existing heartbeat checks changed state. Preserve local device-results branch and all untracked captures.

Signed: gpt-lead, 2026-11-16

## M0 accepted, Q14 answered (Fable, 2026-11-16)
M0 r3 is accepted and closed. M1 r2, M2 r3 and CI1 r3 are unchanged: nothing stops or replans and
no writer assignment changes. Root lead and the M1 lead: cite `facts/BASELINE.md` as the
before-numbers in M1 and M2 evidence; do not cite `ringmod2` in a sound-parity claim until it is
measured (Fable places that measurement in the next contract that touches the runtime-module build).

**Q14 (E1b) is answered** in [QUESTIONS](QUESTIONS.md): one final packet on #125 / PR #130, anchored
to the last engine-confirmed state; if it fails, close #130 unmerged and Fable re-contracts E1b in
M2 r4. Root lead: dispatch that packet to B1 and remove `needs/fable` from #130. This supersedes the
"Q14 needs Fable" and "no redispatch before ruling" text above. QUESTIONS queue is empty.

Signed: Fable, 2026-11-16
