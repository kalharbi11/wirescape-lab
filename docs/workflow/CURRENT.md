<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Older handoffs (gpt-lead, gpt-reviewer, Fable runs 1–3) are in
[archive/CURRENT-2026-11-17.md](archive/CURRENT-2026-11-17.md). They stay valid where nothing
below replaces them; this page is the only live queue.

## #190 transport diagnosis — 2026-11-17, 19:34 EST

Owner supplied independent Claude reviewer analysis; verified against live unpack.py and190 rulings.
Existing frozen corpus is LZMA/base64 text with strict manifest digests and inventory; simply adding
a .b64 file does not make the existing unpacker read a new case. Reviewer direction is sound,
but needs explicit new-case unpack wiring/path grant, not a claim that current reader already handles it.

Proposed A7 amendment to190#6960646798: allow a separate losslessly encoded fixture and manifest
under native/tests/fixtures/abi2, plus bounded bench/reference/unpack.py wiring to decode only this
new case to the build directory. Keep old corpus/chunks/inventory/hashes unchanged. Decoded bytes
must be exactly384000 /96000 float32LE, SHA256
485456df74522320047a4ae9361e5de52042c15079ccb4549982fbe41d887419.
Decoded Git blob hash remains4dc06c72035a30979ea84beacc7664999bce77b6; encoded file has its own hash.
No change to frozen_reference.h, original assertions,1e-7 tolerance or capture→convert→delete order.
Architect must approve this amendment before committing encoded fixture/wiring.

Alternative needs no format amendment: GitHub create_blob(encoding=base64) stores decoded binary,
not base64 text. A lead with artifact bytes in the tool runtime could upload exact binary then
fast-forward the branch. Current cloud cannot fetch bytes: connector returns a signed artifact URL,
shell downloads and git fail proxy503. Runtime reports vpn_enrollment_failed and blocked
non-platform networking. This is independent of fixture format; do not fabricate/re-render capture.
Artifact14352740696 remains downloadable via connector; no bytes verified locally or branch edit.

Owner next: architect:run for A7; then B4 4:run on existing190 to preserve exact artifact, decode/hash
check, convert test, delete ABI1 and obtain fresh final-head CI/review. A local session with working
artifact/git access can instead do the original raw binary route under existing ruling.
No agent chat dispatched. #190 remains draft/blocked; no merge or S5 release.
Signed: codex-lead, 2026-11-17, 19:34 EST

## Cloud lead quick check — 2026-11-17, 19:28 EST

Owner resumes gpt-lead in cloud; **manual agent starts only**, no messages sent to builder chats,
no subagents or schedules created. SR5/7/11/13/18/19 applied; scope stays OB0/OB1.
Usage/account reset: unavailable to this session, not inferred from yesterday's snapshot.
Shell clone failed proxy503; GitHub connector supplied live heads, Results and hosted logs.

- Merged owner workflow handoff #215 at 74aabda after exact-head Lab44171081847 success.
- #182/189 edcc97f correction1/2: Lab44134002029 success; independent source review still needed.
- #206/213 9246e55: Lab44170731786 FAILED. Actual OB-a1 28/32: normalized document drift
  in basics-02, basics-03, basics-04, scene-08. Native tests ×3 and Studio passed.
  Report artifact14367992194, checkout dd52b9c. B1 diagnoses exact differing keys first;
  no patch rewrite, normalization relaxation or loader fix authorized; preserve draft red reproducer.
- #207/214 b19d908: Lab44156502991 FAILED, shard2 ob-c-asio-discovery.spec.cjs:27:
  "no RealEngine listener" at emit invoked from line50. B1 corrects fixture startup on same PR
  without weakening assertions; six remaining cases and native wiring remain unexecuted.
  B4 retains shared CMake slot; no new CMake grant in this run.
- #193/196 78531a6: Lab44153874650 and evidence44153874673 success.
  Builder reports verified R2 spread2.471322% both architectures and D5 artifacts;
  lead independent source/artifact review and release publication still outstanding.
  Connector offers no release-upload action and shell git route failed; no publication claimed.
- B2 #209/216 361fd59: continue existing UI measurement packet, inspect completed hosted
  outcome once and write neutral facts from actual artifacts; no smoke/MT2 pickup.
- B3 #210/212 d712074: old negative non48 integration assertion blocks Lab.
  #219 + Architect inbox A6 request bounded exception/routing; no native/document edit released.
  Actual non48 pitch/Ir and D5 evidence still missing; Golden ×3 does not replace them.
- B4 #188/190 3858a2a: exact fixture not yet committed. Architect transport ruling stands;
  keep384000 original bytes, SHA256485456df… and blob4dc06c…; no deletion/S5 before sequence.
- B5 #208: no PR/result; resume only census with source access. Otherwise report capability
  blocker and stop, no product-lane takeover.
- #176 remains parked until OB1; #186 remains draft for Architect close/refresh disposition.

Manual starts: B1 `1:run` (#206 diagnosis, then #207 fixture); B2 `2:run` (#209);
B3 `3:run` (bounded source/evidence review of #210, await219 for outside-folder edits);
B4 `4:run` (#188 exact fixture then ordered S4); B5 `5:run` (#208 only).
Architect `architect:run`: #219 ruling and #189 independent M2 review; #212 review after unblock.
Delivery lead still owns independent #196/#184 review, release publication and earned merges.
No product merge or OB0 tag earned by this quick check. Next normal lead run: review #189,
#196/#184 and resolve binary transport/publication with working git access.

Signed: codex-lead, 2026-11-17, 19:28 EST

## Quick check — 2026-11-17, 15:33 EST

Owner run modes, signatures and usage reserves: [CODEX_LEAD.md](../context/CODEX_LEAD.md).
Plan211 merged18eb8e5 after exact-head notes Lab44153759982 success.

| Builder | Changed status / next |
|---|---|
| B1 | #206/PR213 c501d9f:32-case round-trip packet unexecuted. Exclusive ci.yml Lab integration slot released; continue same PR, then207 in free files. #182 preserved. |
| B2 | #193/PR196 78531a6: full-engine R2 measured/artifact-verified, after spread2.471322% on x64/ARM64. D5 encoder fixed; new run pending at builder Result. Finish artifacts, then209; no lead acceptance inferred. |
| B3 | #210/PR212 d712074: Macro implementation published; continue changed-state hosted validation and concrete diagnosis. |
| B4 | #188/PR190 3858a2a: genuine96000-sample/384000-byte reference verified; binary Git publication capability blocked. Preserve original bytes/hash/assertions. Lead transfer repair deferred to normal run; no deletion/S5. |
| B5 | #208 census capability-blocked, no Work substitute. Report actual supported tools once, then await small supported packet/reassignment. |

Usage: five-hour17% used/83% remaining, reset2026-11-17 16:56EST; weekly56% used/44%
remaining, reset2026-11-23 11:49EST. No reset/credit spent. One bounded continuation each,
no polling/new heartbeat. Next normal run: binary transfer and required reviews; suggest an
after-Architect time to owner before scheduling. B1 exclusively owns ci.yml until packet ends.

Signed: codex-lead, 2026-11-17, 15:33 EST

## Local OB dispatch — 2026-11-17 ET

Dated plan: [OB_PLAN.md](OB_PLAN.md), ready issues #206–#210, workstream trackers #198–#205.
**Only OB0/OB1 tasks run. Everything else is parked until OB1.** The owner explicitly authorized
B5 as a floater for small tasks; it has no standing product lane. Prior four-builder staffing
text is superseded only for this bounded owner assignment, with no change to reviews or gates.

| Builder / ordinary ChatGPT chat | Current packet | Next tasks and gate |
|---|---|---|
| B1 / 6afc8740-e58c-83ea-a876-cf6962d3034b | #206 round-trip CI while #182/189 correction1 edcc97f awaits fresh evidence/review | #207 tests-only regression packet in free files; #191 after actual189 merge, then192 behind OB0 work |
| B2 / 6afc875c-9b00-83e9-b9c9-7437e6adab67 | #193/PR196 actual full-engine R2 and D5 artifacts | #209 UI facts after bench release; e2 after208 merge plus exact issue and test slot |
| B3 / 6afc877d-2ac8-83ea-882a-04ca69e3ac08 | #210 Macro S7.4, independent module folder; #155/184 source parked | S7.2 only after155 merge and exact stage issue; then eligible sound task from202 |
| B4 / 6afc878d-90a8-83ea-9f1b-990fb2300ea2 | #188/190 exact96000-sample frozen capture → conversion → deletion | S5a → S5b only after each actual predecessor merge and stage issue; S6 announced ≥1 day ahead |
| B5 / 6afca215-5574-83e9-a59a-55e6449e8dc6 | #208 module census, only facts/code/module_census.md | Small read-only OB0 readiness inventory under198, then available to lead; no arbitrary task pickup |

Architect ruling190#6950233998 has released the exact frozen conversion; older “wait for ruling”
handoffs are superseded. All finite task queues were sent to these regular chats. Historical cloud
workers remain stopped. One writer per file, no self-merge or gate relaxation, no extra monitor.
The two existing finite local check-ins remain the only scheduled checks. Read changed Results
once, resume unfinished authorized work, and preserve current PRs/correction counts.

Signed: gpt-lead, 2026-11-17

## Architect schedule (owner, 2026-11-17)
Fresh Claude sessions fire `architect:run` quick checks **2026-11-18 09:00 ET** and **2026-11-18 21:00 ET**,
and nothing else is scheduled. Lead: file inbox rows (urgency **now** for a blocker) before each check-in. The owner may also
send `architect:run` at any time. Owner granted the Architect full git authority; it still merges only
what contracts and reviews allow. **#190 is not merged:** it is blocked, ABI1 is not yet deleted and it has no M1
review. The 09:00 run will try to commit the exact fixture itself (inbox A1) so that B4 can continue.

- **Design: Claude Architect** (owner's Opus session; `proposals/0017` §1). Plans, rules, accepts,
  does the Claude contract reviews. **Never the delivery lead** (0017 §1 rule 3).
- **Delivery lead: gpt-lead** (Codex), unless the owner names another. Dispatches, reviews
  evidence, merges inside contracts. Builders: gpt-builder1–4 (Codex), one task each.
- **Goal:** the Owner Build ([PRIORITY.md](PRIORITY.md), contract [OB](milestones/OB.md)).
  Pick ready work by tier P0 → P3; P4 is parked.

## Decided 2026-11-17 15:50 ET (Architect quick check, base `main` 18eb8e5)
- **Inbox:** all asks for the Architect go to [ARCHITECT_INBOX.md](ARCHITECT_INBOX.md) plus the
  `needs/architect` label (AGENTS, STANDING SR11). The Architect reads it first every run.
- **#190 M1 S4 blocker is transport, not design.** The verified 384,000-byte capture from Lab run
  44134064502 may be committed to `task/188-s4-delete-abi1` by any agent or the owner with git
  write access (owner assigns: a Claude cloud builder can do it). Exact file only: SHA-256
  `485456df…`, blob `4dc06c…`; no base64 text, no regenerated or derived fixture. B4 then
  resumes ruling 190#6950233998 unchanged. Nothing else holds.
- **#176 MT2** stays parked (inbox A3, later). **#186** close-or-refresh after #215 (A4, later).
- **Hold:** none new.

## Decided 2026-11-17 (Architect run 1, base `main` be928a1)
- **#159 (M1 S3)** contract review passed (I1–I5, I8 hold); merged `b87f881`. **S4 is released.**
- **#180 (M10 S4 facts)** merged `be928a1`.
- **CI1 r4 ACCEPTED** ([report](reports/CI1-r4-acceptance.md)).
- **OB r1 contract accepted** ([milestones/OB.md](milestones/OB.md)): OB-a1/a2/a3, OB-b, OB-c,
  OB-d, OB-tag. PRIORITY P1 now points to it.
- **Errata (a), (b), (e)–(l) ruled** in [proposals/0018](../../proposals/0018-errata-0012-0016.md).
  With 0017 §5 this closes the packet `FABLE_FINAL_RUN.md`.

## Queue — lead dispatches in this order (P0 first, SR16 inside a tier)
| # | Task | Builder | State / gate |
|---|---|---|---|
| 1 | **M1 S4** (`abi1_mono` retire: `facts/perf/abi1_mono_final.md` first, then 96-ID inventory at the unchanged +1%) | B4 (M1 serial writer) | **dispatch now** |
| 2 | **M2 E1b-r #182** (from `60cab7ea`, browser-safe fixtures, history reconciliation) | B1 | dispatch now; M3 RL and OB0 wait on it |
| 3 | **M7 S7.1 reverb #155** | B3 (bench writer free since #150) | dispatch now; then S7.2, S7.4 for OB0 |
| 4 | **OB-a1** round-trip CI test | first free builder | file issue now |
| 5 | **OB-c** regression tests only (no fixes before S6) | first free builder | file issue now |
| 5b | **OB-e1** module census, **OB-f1** UI smoothness facts (OB r2) | first free builders | file issues now; then OB-e2, OB-f2 |
| 6 | **M6 MT2 PR #176** (head 930baed) | B2 | lead reviews; merge or park — must be gone before S6 |
| 7 | M1 S5a → S5b → S6 | B4 | after S4; plan the S6 window a day ahead, every product PR merged or parked (0017 §8.4) |
| 8 | M3 T1.6a → b → c → TR1e; then M4 E6 → E4a → E4b → E5/E3a → E3b/E3c/E7, CN | after S6 | issues quote ER rules: TR1e ER1; E6 ER1, ER2, ER6; E4a ER5 (statement table first); E4b ER3, ER5; E5 ER4 |
| 9 | P3 (M10 S5–S6, M12 P0) | idle builders only | |

**OB0 = rows 2 + 3 (S7.1, S7.2, S7.4, T7.0 merged) + OB-a1 + tag.** It is the next owner deliverable.

**Lead planning ask (owner, OB r2):** break OB into a dated task plan (`docs/workflow/OB_PLAN.md`): every OB0/OB1 row, its issue, builder, dependency and estimate. Every builder works only on OB rows (P0–P2) until OB1; anything else is parked.

## Next action per role
| Role | Next |
|---|---|
| Lead (gpt-lead) | `lead: run`. Dispatch rows 1–5; review #176. Ask the owner for a Claude reviewer for each task the contract marks **Claude** contract-review (S5b, S6, OB-a3, M4 E-tasks). |
| Builders | One task each from the queue. Nothing in flight stops. |
| Claude Architect | Next run on any of: a **now** inbox row; #182/PR189 merged (M2 acceptance, criteria 1, 2, 4); S4 merged (release S5a); S7.4 #212 Claude contract-review request. Otherwise a quick check tomorrow ~09:00 ET. **Next run should:** read inbox; check #190 fixture landed; check #189/#212 state. Reserved items (Sub-patch note, M9 r2, M12 P0, T4.2, T6.3, 0016 R4 / M10 X4) need one long run, not before OB0. |
| Owner | Unblock #190: have an agent with git write commit the exact capture to B4's branch (ARCHITECT_INBOX A1). Say go to the lead (`lead: run`). Assign Claude reviewers when asked. `CLAUDE.md` still carries the deputy section; the Architect will propose its rewrite in a PR you merge. Later: OB-a2 on your patches and the Pi session. |

Signed: claude-architect, 2026-11-17 15:55 ET
