<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Older handoffs (gpt-lead, gpt-reviewer, Fable runs 1–3) are in
[archive/CURRENT-2026-11-17.md](archive/CURRENT-2026-11-17.md). They stay valid where nothing
below replaces them; this page is the only live queue.

## Local delivery update — 2026-11-18, 00:03 EST

Applied Architect23:40 decisions A10–A13, OB r2.1 and M7 r1.2. All four builder run prompts
were sent and all four chats were independently confirmed active. B5 remains a bounded floater,
idle after delivered census/readiness work; no fifth product lane.

| Writer | Current authorized task / exact boundary |
|---|---|
| B1 | Continue207/214 six newly ruled OB-c tests in NEW native/tests2 or apps/studio/tests files; existing MIDI/ASIO passes and correction1/2 retained. Strict expected failure names the product cause only; fixes remain afterS6. No sidecar/control/engine/shared CMake/ci.yml grant duringS5. Coordinate any new discovery wiring first. |
| B2 | Continue226/230 offline A12 pitch-applicability classifier from EXISTING44229365015 artifacts, no recapture. Only48k data defines margins before off-rate comparison; unchanged estimator/window/±2cents. Defined-row failure is real210 defect; other rows pitch_not_defined, never pass/zero. Publish rows/models/tests, then re-label Claude reviewer.196/209 source parked. |
| B3 | Continue155/184 correction2/2 for HIGH6969130295, only reverb folder. Four damping rows0.1/0.4/0.7/0.9, default<=5%, no other actual hosted row worse than base; exact48k unchanged. Preserve history/RT/goldens/cap. NoS7.2; another failed round followsSR6/M7 escalation. |
| B4 | NEW234 S5a released, task/234-m1-s5a from main, config/meter/descriptors only. ExactM1r3 paths, I1–I8/evidence1–5. Sole sidecar writer duringS5a/S5b. Do not edit212 Macro block; if that file is needed, defer its edit/rebase after212 actual merge. S5b/S6 remain closed. |

Lead merged approved213/OB-a1 at6998f0547ba6cd172a6a06916dd5014c5acb6882 from reviewed
00664a1 after all exact-head checks green and Architect6969127251 approval;32/32 actual product
roundtrips retained. Low silence-depth/-0 notes retained. This completes OB-a1 only, notOB0.

Lead reviewed and merged232 report atd048049b776ff6e92623f1d6af5c3038722110c5 (source48f913c,
doc-scope checks green).235 now requests Architect M2 acceptance with claude-review/architect +
needs/architect. Real805.5ms edited-subject limitation, Q22 witness interpretation, D08/D09 and
all unmeasured/inspection-only exceptions retained. Report merge does not acceptM2 or release192.

212 remains at7bde1ee unmerged pending A12 table/numeric/Ir/D5 release gates. Its wider-rate
Medium is nonblocking at this head; if source changes, add8/192 finite/latency/zeroalloc tests
and DESIGN passband-from44.1k line under the ruling. No automatic new Macro source task.
184 revised DSP requires new pinned measurements later; old196 evidence cannot certify it.
196 validatorP2/P3 and durable FLAC publication remain open, without concurrent B2 task edits.

Prior notes229 is superseded by this fresh-main handoff: cleared A10–A12 stay Cleared and no
stale Open request is restored. Architect decision text below is preserved verbatim.
Mode quick expanded for actual new rulings/task release; usage entry26% five-hour used/74%
remaining, reset2026-11-18 00:24 EST; weekly61% used/39% remaining. No credits/resets spent.
No devices, new schedules, gate changes, source implementation by lead or polling.
Signed: codex-lead, 2026-11-18, 00:03 EST

## Decided 2026-11-17 23:40 ET (Architect run, base `main` 06e68f0)
Lead: drop rows A10–A12 from PR229's Open table when you merge; they are cleared here.
- **A11 / #199: M1 S5a released.** S4 merged at `8c72722`. E1a and T0.13a merged before it, so
  S5a may open. **Writer:** B4 only, one new issue `task/<n>-m1-s5a` + one PR. **Paths:** the M1 r3 S5a row
  (`native/control/`, `native/sidecar/`, `native/web/`, `native/tools/render/`, `native/document/`,
  `native/io/`, their tests). **Criteria:** 0006 evidence 1–5 on the merged head (golden identical on
  three platforms, no instruction row >1 % worse, sanitizers + S0 snapshots green and unchanged, grep
  table, deleted-test list), I1–I8 untouched, M1 Escalate list unchanged. **Order rules:** PR212 owns the
  Macro block of `native/document/qt_free_patch_coverage_tests.cpp` until it merges; S5a does not edit
  that block, and if S5a must edit that file it rebases after PR212 merges. While S5a/S5b are open, nobody else
  edits `native/sidecar/` (OB-c tests go in new files, see A10). S5b stays closed until S5a merges.
- **A12 / #230, #212: what "pitch within ±2 cents" means for Macro (M7 r1.2).** The estimator,
  its window and ±2 cents stay unchanged. A row (model, target, rate) **has a defined pitch** only if
  its **48 kHz** render (the same bytes before and after) meets both rules. Each rule is computed once, from
  the 48 kHz data only, and recorded per row *before* any off-rate value is compared:
  (1) **dominance:** the selected bin's magnitude is at least 1 dB above the largest magnitude in the
  80–120 % window outside ±3 bins of it. 1 dB is twice the contracted ±0.5 dB passband ripple, so the converter
  cannot move the peak to another bin; (2) **level:** that bin is within 40 dB of the largest
  bin of the whole spectrum (bin 0 excluded). The contracted 60 dB stopband then cannot shift it by
  more than ~1 dB. Rows with a defined pitch must be within ±2 cents at 44.1 and 96 kHz. One failure means S7.4 is not met
  and goes back to #210's writer as a defect (8 diagnostic outliers on models 6, 7, 12, 15
  are rows to check, not rows to excuse). Other rows are reported `pitch_not_defined` with both
  margins. They are not passes and not zeros, and their rate evidence is the folder passband/stopband test plus finite,
  non-silent output. Models with no defined row are listed by name in the acceptance report.
  B2 computes this offline from the **existing** artifacts of run 44229365015 (they expire about 2026-11-24),
  in new files under `bench/evidence/macro_non48/`, with no recapture. **Claude Medium (8–192 kHz):**
  not blocking. `prepare` stays bounded and realtime-safe at every rate, and S7.4 claims only 44.1/96. If
  PR212 gets another head for any reason, it adds a folder test at 8 and 192 kHz (prepare, finite
  output, latency reported, 0 allocations) and one DESIGN line saying the passband rule applies from 44.1 kHz;
  otherwise it is a follow-up. S7.4 still also needs the D5 FLAC pair in `bench-<date>` (lead).
- **A10 / #223: the six OB-c oracles (OB r2.1).** All are device-free. The owner's 306/546 ms are never a pass
  mark. A test that fails now lands as an *expected failure that is strict* (CTest `WILL_FAIL`
  / pytest `xfail(strict=True)`) naming the cause; the fix after M1 S6 removes the mark. Tests go
  in **new** files under `native/tests2/` or `apps/studio/tests/`, not in `native/sidecar/` while S5 is open.
  1. *Panic gap:* a graph with no note/gate state (VCO → Output) through the null-sink capture. After
     `panic`, the PCM is **bit-identical** to a reference run without panic, and block positions run without a break
     (no missing or repeated frames, 0 overruns).
  2. *Buffer change:* the same drone, `setBufferFrames`. (a) The first block of the new segment is not
     silent past the engine's reported latency; (b) the stop → first-new-block interval from the
     b0/b1 marks is **recorded as a fact** (5 repeats, median and maximum, per architecture). It has no pass mark; the fix task gets
     a budget from the owner.
  3. *basics-04:* render the bundled patch, plus attack 0.001/0.005 × VCA gain at its value and at the parameter maximum.
     Every gate-on step's output peak is within 60 dB of the render's median step peak. 0 nonfinite samples.
  4. *scene-07 after panic:* panic at two fixed frames (mid-note, and between notes). The existing
     `click_events` detector (bench/offline, imported unchanged) over the 500 ms after panic must count ≤
     the same window of the no-panic reference.
  5. *Echo knobs:* time, feedback, tone, mix, each swept over 100 ms and 1 s at Studio's real
     `setParam` cadence (cite the line). `click_events` in the gesture window must be ≤ the no-gesture reference.
     Division/mode switches: record only; the fix is 0011 row 8.
  6. *Groove lag:* frame-stamped start/stop, internal clock. The first gate comes within one block of the frame at which
     the engine applies start; `running` = 0 within one block of stop. With an external clock the first gate is on the first
     clock edge at or after start. UI → sidecar timing is recorded as a fact only.
  When all eight rows have a test landed (passing, or strict-xfail naming a cause), the OB-c
  regression stage is met. Fixes stay after M1 S6.
- **#213 OB-a1: approved** at `00664a1` (no High; see PR). **#184 S7.1: High, not approved.** The
  damping calibration was fitted at the default damping only. The Architect reproduced R2 locally
  (x64 GCC, the folder test's own metric). Base spreads at damping 0.1/0.4/0.7/0.9 are 28.5/35.6/18.0/3.5 %;
  at the head they are 17.4/2.5/32.7/61.9 %. **M7 r1.2 for S7.1:** the folder test also reports the spread at damping
  0.1, 0.4, 0.7 and 0.9. Default stays ≤5 %, and no other value may be worse than base. B3 has correction 2/2.
- **#172 closed:** CI1 r4 was accepted earlier (see "Decided 2026-11-17 (Architect run 1)").

Signed: claude-architect, 2026-11-17 23:40 ET

## Owner evening handoff — 2026-11-17, 19:40 EST

Owner will start a **local Codex lead at20:45 ET** to prepare the **21:00 ET Architect run**.
These are owner-run sessions, not new scheduled jobs. Cloud sends no builder chat prompts.

**B4 bounded continuation now, under existing #188/#190:** read-only S4 readiness packet on the
same issue/PR, no new source branch or second task. Inventory the exact frozen-reader conversion
sites, ABI1-only deletion/link consumers and assertions that must survive; identify file:line and
the corresponding post-deletion proof for each. Prepare a step-by-step conversion/deletion/test
checklist from the already-authorized S4 scope. Check whether the original artifact can actually
be retrieved with B4's current tools; if available verify exact length/SHA without regenerating it.
Publish one signed Result with checklist and remaining capability gaps. No source deletion,
encoded-fixture/unpacker edit, shared CMake edit, S5 start or correction-round consumption while
A7 waits. This work is preparation for the existing blocked packet, not permission to implement
a dependent stage. B4 keeps its serial lane. Owner starts B4 with4:run.

**20:45 local lead checklist (read this unmerged PR220 explicitly):**
1. Read latest main CURRENT, inbox and this handoff; reconcile newer Results without overwriting
   Architect decisions. Review/merge220 only after exact-head green; ensure A6/A7 reach main
   before21:00. If checks are unfinished, Architect must explicitly read220's inbox as well.
2. A7/#190: try artifact14352740696 with local working networking; independently hash384000
   bytes SHA485456df74522320047a4ae9361e5de52042c15079ccb4549982fbe41d887419,
   blob4dc06c72035a30979ea84beacc7664999bce77b6. Raw binary upload satisfies existing ruling;
   base64 API transport is decoded binary. If successful, coordinate B4 handoff before branch
   write, commit fixture+manifest/provenance in order and mark A7 transport amendment unnecessary.
   Otherwise ask Architect to authorize exact encoded-fixture path AND bounded unpack wiring;
   preserve old immutable corpus and all assertions. Do not claim a download link is verified bytes.
3. A6/#219: obtain bounded native/document test-path/serial-writer ruling for212; retain strict
   non48 actual pitch/Ir/D5 evidence requirements. No contract-target change by lead.
4. Review189 edcc97f confirmed-history source against queued regression and green Lab; route any
   mandatory Claude review explicitly. Review196/184 evidence and arrange durable D5 release
   attachment with local capabilities before any product merge. These are delivery duties.
5. Carry B1's four roundtrip document drifts and fixture-listener failure as exact unresolved
   findings; request design rulings only if diagnosis actually needs scope/meaning changes.
   Preserve B2 UI facts/B5 census lanes; no new unrelated work or schedules.

**Architect decisions requested at21:00:** A6 and (unless local raw transfer solved it) A7.
B4 source inventory is supporting evidence; capture-only190 is still not merge-ready.
Signed: codex-lead, 2026-11-17, 19:40 EST

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

## Decided 2026-11-17 21:00 ET (Architect quick check, base `main` 52e49ba)
- **A7 / #190: encoded fixture route granted, bounded.** Amends 190#6950233998 and A1 on the
  fixture format only. The raw binary commit (A1) stays first choice; the encoded route is equal
  to it if the decoded bytes match exactly. Conditions: (1) bytes come only from artifact
  `14352740696` (Lab run 44134064502), never re-rendered; (2) one new document under
  `native/tests/fixtures/abi2/` that uses the existing entry shape (`codec: zlib9+b64`,
  `samples` 96000, `bytes` 384000, `sha256` `485456df74522320047a4ae9361e5de52042c15079ccb4549982fbe41d887419`)
  plus provenance (run, artifact, decoded blob `4dc06c72035a30979ea84beacc7664999bce77b6`);
  (3) `bench/reference/unpack.py` may read it, reusing `decode_case` (length, eof, digest checks)
  and writing to the build directory only, and `native/engine2/CMakeLists.txt` may add only that file to the
  existing unpack command's inputs; (4) the old corpus, chunks, inventory and hashes, `frozen_reference.h`,
  every assertion, the 1e-7 tolerance and the capture → convert → delete order stay unchanged.
  A test that the unpacked file hashes to `485456df…` is required. **Transport is still open:**
  this session's proxy also refused the signed artifact URL (403). The owner (local download) or any
  session that can fetch the artifact produces the bytes; the format no longer limits who can commit them.
- **A6 / #219 S7.4: test transition granted, bounded (M7 r1.1).** The S7.4 contract sets
  "0 `unsupported_rate` rows" as the target, so the old test that Macro refuses 44.1/96 kHz is out of date and has to be rewritten. That is a
  fix to match the accepted design, not a loosened gate. In `native/document/qt_free_patch_coverage_tests.cpp`, the Macro off-rate
  block (about 221–240) changes to: load succeeds at 44.1 and 96 kHz and renders finite output with
  0 allocations and 0 faults. The "failed load leaves the separately loaded graph renderable" check
  stays, driven by another genuine refusal (for example an invalid rate), not deleted. The same
  rule covers `protocol_tests.py` only if it depends on Macro refusing off-rate. Every other
  assertion stays. Writer: one file handed off by the lead; B4 by default, or B3 on PR212
  if the lead confirms B4's #190 work does not touch that file. **Evidence packet (B2, after #193
  releases its writer lane) is approved:** `bench/offline/run_all.py` reports measured non48 Macro rows, with no hardcoded
  status; 24 models at 44.1/48/96 kHz with the estimator and ±2-cent target unchanged; Ir at 44.1/96 reported; D5
  pair; one advisory workflow under SR8, not `ci.yml`. If a model's `pitch_cents` cannot be measured
  meaningfully (inharmonic models), report it as unmeasured with the reason, never as 0, and file
  `reserved` in QUESTIONS: the meaning of a measurement is not the lead's call, and the criterion
  is not met for that row until it is ruled.
- **Hold:** #190 merge until final-head CI shows the fixture test, conversion and ABI1 deletion.
  #212 acceptance until the test transition and measured non48 rows land. Nothing else holds.

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
| Claude Architect | Next run on any of: a **now** inbox row; #232 (M2 acceptance report) ready and labelled; the #230 applicability table posted; a new #184 head. Otherwise the scheduled 2026-11-18 09:00 ET quick check. **Next run should:** read inbox; M2 acceptance from #232; verify the A12 table against the rules (spot-check 3 rows); re-review #184 at its new head; A3/A4 cleanup. Reserved items (Sub-patch note, M9 r2, M12 P0, T4.2, T6.3, 0016 R4 / M10 X4) need one long run, not before OB0. |
| Owner | #190: assign the independent M1 Claude reviewer the lead asks for. The fixture has landed and the Architect has checked it, so no file transfer is needed now. Say go to the lead. Assign Claude reviewers when asked. Later: OB-a2 on your patches and the Pi session. |

## Decided 2026-11-17 21:50 ET (Architect quick check, #190 head `26c749d`)
- **#190 S4: the Architect's invariants hold; nothing more is needed from the Architect.** The fixture
  `native/tests/fixtures/abi2/abi1_s4_qt_free_96000.json` decodes (zlib+b64) to 384,000 bytes with SHA-256
  `485456df…`, which equals the A1/A7 capture. In `serialized_demo_equivalence`, every original assertion
  stays (finite, exact v1→v2 PCM, 0 RT allocations, max_abs_error ≤ 1e-7, 96,000 samples), with
  one finite check added. Lab, Golden, M1 paired, Offline, instruction and T7.0 are green on the head;
  `facts` ×3 was still running at check time.
- **Lead:** do not merge until `facts` ×3 is green on the exact head and the contract's independent M1
  review has passed; then merge per M1. Builder: take #190 out of draft and drop `status/blocked`.
  The `needs/architect` label is removed.

Signed: claude-architect, 2026-11-17 21:50 ET
