<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB delivery plan — 2026-11-17 ET

Owner-directed scope: OB r2.1, PRIORITY, M1 r3.1, M2 r4, M3 r1, M4 r2, M7 r1.2 and signed Architect rulings. Local gpt-lead delivers; Claude Architect owns design/required reviews. This is a delivery plan, not a contract amendment. All builders work only toward OB0/OB1. SDK/drop-in/dev-loop/panels/Daisy/other hardware/protocol publication/web features and MT2+ are parked. M4's contracted internal protocol/header changes remain necessary for OB1.

Use [ROADMAP](ROADMAP.md) for the summary and [BUILDERS](BUILDERS.md) for live assignments.
The dated dispatch entries below are history.

## Active OB1 sequence — 2026-11-24 21:33 EST

[BUILDERS](BUILDERS.md) holds current assignments and [CURRENT](CURRENT.md) holds exact evidence
and Architect routing. OB0 and M1 are accepted. M3 prerequisites, E6, E4a/E4b, E5v, E7, OB-c and
initial CN facts have merged.

- **Engine critical path:** E5 #436 at `31ab651` needs full CI, the #480 continuity packet and
  one exact-head Architect contract review. B1's #485 captures a stock non-adopt replacement;
  B5-CN asks for the synthetic adopt seam and transition-cost method. B1 #474 has E7 A62 buffer
  measurements; A68 asks how its larger-buffer observations count toward M4 acceptance.
  Then refresh CN and rewrite the KNOWN_ISSUES A2 row from the measured table.
- **Sound parallel:** S7.5 #291 at `a875881` has exact-head checks and refreshed D5. The Architect
  re-reviews H1 before the lead merges. S7.6 #449 follows #291, tone evidence and the A64
  clocked-division ruling. S7.9 #444 awaits A65, with #467's tooling question separate under A66.
  Finish OB-d after remaining sound. Keep catalogue/S0 writers serialized.
- **I/O parallel:** #425, #433 and #463 merged. A67 routes a separate cause-specific enqueue fix.
  B2's #475/#482 egress diagnostic is independent. Note Trigger #322 is optional after E5v.
  Advisory hosted and Pi soaks retain their existing treatment.
- **Candidate:** OB-f1, the owner's real-patch folder round trip, install, and the owner Pi session
  with 100 edits, zero xruns, no visible stutter and both CN costs. PI-1 and Pi soaks are candidate
  work. Architect acceptance and owner-build-1 tag follow. E3a/b/c stay in OB1.1.

Signed: codex-lead, 2026-11-24, 21:33 EST

## Next-day delivery queue — 2026-11-21 18:34 EST

Start the current row for each builder. A numbered successor starts only when its release condition is met. Use one issue, branch and PR per task. Use hosted device-off CI and publish a signed Result with exact head and evidence.

| Lane | Start or continue now | Independent work while blocked | Successors in order |
|---|---|---|---|
| B1 | [#309](https://github.com/kalharbi11/wirescape-lab/pull/309) align its dedicated workflow with #312 CLI, reports and tier baselines | Read-only #298 pin 7 matrix for CLI play, soak, golden, render, sidecar and web | After S6, rebase #298 first; get coverage/Claude review, then [#318](https://github.com/kalharbi11/wirescape-lab/issues/318) Pi script/docs and path-only dry run. In parallel, enable hosted OSC after #305 lands and MIDI after #308 integration. Revalidate mapped workflow paths after S6. |
| B2 | [#311](https://github.com/kalharbi11/wirescape-lab/pull/311) fix scripted assertion and inspect sanitizer | Plan MIDI profile integration without editing bench/io; prepare OB-f1 candidate procedure | After #305 merge and bench writer handoff, add `midi-m8` and `mixed` to #308. Sync mapped paths and verify Lab after S6. Run OB-f1 at pinned candidate. [#319](https://github.com/kalharbi11/wirescape-lab/issues/319) is P3 reserve for a released idle slot. |
| B3 | [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) finish MIDI to CV trigger draft and device-off evidence | Plan fixed-window evidence for #314 read-only | If #307 is handed off and S6 is open, draft [#316](https://github.com/kalharbi11/wirescape-lab/issues/316) ADSR. After S6, #291 is the second parked rebase and still needs D5 and K1–K8. Then [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) Delay → S7.7 VCF → S7.8 Ladder → S7.9 CHOKE, with separate scoped issues and ADSR writer held by one task at a time. |
| B4 | [#295](https://github.com/kalharbi11/wirescape-lab/pull/295) classify and resolve 76 preview hits; guarded replay, full evidence and Claude review | Read-only next-stage inventory during check runs | S6 merge and mapped-path release → [#315](https://github.com/kalharbi11/wirescape-lab/issues/315) T1.6a → b → c (b and c require contract-review) → TR1e (full ER1 and contract-review) → E6 (ER1/ER2/ER6) → E4a → E4b. Actual predecessor merges and a released issue control each start. |
| B5 | [#312](https://github.com/kalharbi11/wirescape-lab/pull/312) correction, runner evidence when available | Read #317's Studio test seams while Lab runs | After #312 source review, give up the bench writer slot and draft [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) in Studio tests. #308 owns native MIDI/sidecar overlap until handed off. After S6, bounded OB-c one case at a time, starting with panic raw markers and PCM evidence once released; panic semantics require Architect disposition. |

Phase B lets these five current packets run together: S6 apply work in B4's lane, explicitly authorized OB-g drafts in B2/B3 isolated branches, B1's dedicated workflow, and B5's bench-only correction. Keep product drafts unmerged during S6. The #305 bench writer goes to B2 only by recorded handoff; #317 begins with Studio tests only. Runner and soak outcomes are advisory. P4 stays parked. A28 needs the owner's design choice.

Signed: codex-lead, 2026-11-21, 18:34 EST

## Four-builder queue — 2026-11-19 03:35 EST

B1 now has independent OB-a2 #259. B2 continues #207/#214, B3 #243/#255, and B4 #253.
At every lead run, fill available builder slots from ready contracted work while
respecting dependencies and one writer per file. Report any held slot and its trigger.

Signed: codex-lead, 2026-11-19, 03:35 EST

## Latest dispatch sync — 2026-11-19 03:24 EST

B4 #253 resumes under merged A17/M1 r3.2. B2 released the temporary CMake slot after
the #214 merge at `a05f2a2`; S5b still excludes CMake. Actual A10 and Lab are running.
B3 published Reverb correction 1/2 at `f314b85`. OB0 waits for that task's numeric,
review and release evidence. S6 waits for S5b merge.

Signed: codex-lead, 2026-11-19, 03:24 EST

## Latest dispatch sync — 2026-11-19 03:14 EST

B3 #255 is in its first correction after the Reverb loudness regression. S7.2 remains the
OB0 critical path. B4 #253 waits for Architect A17 on live ABI1 header consumers. B2 #214
owns the short, mechanical CMake conflict integration slot while B4 is stopped. Restore
the slot before B4 resumes any shared CMake work. No OB0 release or S6 dispatch yet.

Signed: codex-lead, 2026-11-19, 03:14 EST

## Latest dispatch sync — 2026-11-18 21:35 EST

S5a and OB-e2 have merged. B4 owns S5b #253; B2 took over the existing A10 #207/#214 after
B1's stop instruction, with #209 still parked. The #249 matrix produced no OB-e3 source task.
B3 retains #243 S7.2, the remaining OB0 source change. S6 is still gated.

Signed: codex-lead, 2026-11-18, 21:35 EST

## Latest dispatch sync — 2026-11-18 19:33 EST

Supersedes older dispatch/wiring holds below. B1 #207/#214 and B2 #240/#249 now have
explicit SR8 grants for separate dedicated workflows on their existing branches; no shared
ci.yml/CMake slot or product edit granted. B2 finishes actual 136-case smoke before #209.
B1 completes A10 execution/identity/every-gate proof; wall-time remains unmeasured until actual
marks exist. B4 #234/#242 is in independent Claude review at fd413424, with all five workflow
runs green; S5b/S6 remain gated by actual merge. B3 #243 is the remaining OB0 source task.
M2 accepted and Macro/S7.1 merged as recorded below. Target OB0 first; a 1–2 day aim depends on
S7.2 evidence/review/release gates and does not apply to OB1's serial migration.
Labels, CURRENT and Architect queue sync together; #246 reviewer instructions apply.

Signed: codex-lead, 2026-11-18, 19:33 EST

## Critical paths and estimates
OB0: max(M2 history + actual review, Reverb S7.1 evidence → S7.2, Macro S7.4, OB-a1) → release/tag. Start S7.4 and OB-a1 now, in separate files. Aim for the first eligible build, not a bundled wait for OB1.
OB1 serial path: M1 S4 → S5a → S5b → S6 → M3 T1.6a → b → c → TR1e → M4 E6 → E4a → E4b → E5 → E3a. Sidecar follows E3a → E3c → E7; Studio E3b/E3c serialize if they touch shared files. Engine/module tests serialize only on actual overlapping files. Other OB tests, sound modules, UI measurements and install work run beside this chain.
Estimates below are initial active engineering hours per task, including a first validation/fix pass. CI queue/runtime, independent/Claude reviews, Architect target-setting and owner Pi availability are additional elapsed time. Re-estimate after each signed Result; do not promise a delivery date before observing those dependencies. OB0 budget roughly 2–4 working days elapsed if evidence/reviews clear; OB1 roughly 4–8 weeks with the current serial engine chain. These are planning ranges, not guarantees or permission to skip gates.

## Immediate dispatch — 2026-11-18, 00:03 EST

B1:207/214 six A10 oracle tests in new test files; existing MIDI/ASIO green, strict expected
failures allowed only perOB r2.1 cause, fixes afterS6.191/232 report mergedd048049;235 Architect
acceptance queued.189 merged06e68f0 and213 OB-a1 merged6998f05.192 separately gated.
B2:226/230 A12 offline classification of original44229365015 artifacts, no recapture; only48k
margins decide defined pitch, then±2cent comparisons. Keep196/209 source parked;196 validator
findings remain a later bounded correction, and revised184 needs later newly pinned evidence.
B3:155/184 HIGH damping regression, correction2/2, four actual hosted damping rows with default
<=5% and no other row worse thanbase. Preserve48k and allinvariants. NoS7.2/212 source changes.
B4:234 S5a nowreleased, same serialM1 writer; exact0006 evidence1–5/I1–I8. Exclusive sidecar lane.
212 Macro test block stays reserved; defer same-file edit/rebase after212 actualmerge. NoS5b/S6.
B5: census221/readiness198 delivered, available only for small explicitly assigned tasks.

A10/A11/A12 are cleared by Architect23:40, not open questions.212 rate Medium nonblocking
unlessnewhead (then8/192 tests+DESIGN line); definedpitchfailures remain real210 defects.
One writer perfile, no source task overlap, no new schedules. Run prompts sent toB1–B4;
all four verifiedactive. Reviewlabels per231, no owner reviewer assignment.
Signed: codex-lead, 2026-11-18, 00:03 EST

## Delivery changes — 2026-11-18 05:41 EST

- B1 continues #207 / #214 on the isolated A10 runner packet after a supported retry.
- B2's Macro A12 analysis is in companion #238 for independent review. B2 owns #193 / #196 now
  for validator corrections and new #184 head capture. Queue #240 after that packet and shared
  wiring release. B3 parks #184 at `32abedde` (2/2) for review and capture; #212 stays parked until
  Macro acceptance evidence and D5 are verified.
- B4 resumed #234 under A15 / M1 r3.1. The entire Qt-free test file waits on actual #212 merge before
  B4 edits it. Sidecar and successor stage ownership stay with B4.
- B5's census #221 merged at `998f56b`: 34 palette IDs, 32 native registrations and two SDK
  examples. B5 is assigned only a read-only Macro artifact/release inventory. #240 covers the live
  palette and waits for dispatch; OB-e2 remains unverified.

Signed: codex-lead, 2026-11-18, 05:41 EST

## Complete task ledger
Ready task issues #206–#210 and blocked workstream trackers #198–#205 cover every row below. A tracker is not permission to implement an unmet dependency. Every future implementation gets its own issue/branch/PR, exact allowed paths, contract criteria and mapped S6 paths at release.

| Build / task | Issue or tracker | Builder | Dependency / gate | Active effort |
|---|---|---|---|---|
| OB0 T7.0 baseline | #152 merged | complete | retained facts | done |
| OB0 M2 E1b-r | #182 / PR189 merged06e68f0 | complete | reviewed exactedcc97f, Lab green | done |
| M2 final report | #191 / PR232 merged d048049; A14/#235 accepted | complete | Architect accepted M2 r4 with stated exceptions; #192 stays gated | done |
| OB0 S7.1 Reverb | #155 / PR184 merged 1909b44 | complete | A13, three-platform Golden and durable D5 verified | done |
| OB0 R2/D5 capture | #193 / PR196 merged 34b3da3 | complete | both production architectures, P2/P3 checks and D5 attached | done |
| OB0 S7.2 Reverb gain | #243 (tracker #202) | B3 | S7.1 merged; same writer; supported retry sent | 4–10h |
| OB0 S7.4 Macro rate support | #210 / PR212 merged 004a1b4 | complete | A12 review, instruction evidence and D5 verified | done |
| OB0 OB-a1 round-trip CI | #206 / PR213 merged6998f05 | complete | actual32/32, approved00664a1 | done |
| OB0 tag/release/install check | #198 | lead |all OB0 criteria on main; preserve immutable fallback tag | 1–3h |
| OB1 M1 S3 | #159 merged | complete |reviewed prior evidence retained | done |
| OB1 M1 S4 | #188 / PR190 merged8c72722 | complete | reviewed26c749d, final facts/CI green | done |
| OB1 M1 S5a | #234 / PR242 merged af62278 | complete | reviewed and evidence verified; standalone web unverified | done |
| OB1 M1 S5b | #253 (tracker #199) | B4 | S5a merged; dispatched; required independent Claude review | in progress |
| OB1 M1 S6 | #199 | B4 |S5b; every product PR merged/explicitly parked; plan window ≥1 day ahead; Claude review | 8–16h |
| OB1 M3 T1.6a | #200 | B4 |S6; mapped paths, mechanical only | 4–8h |
| OB1 M3 T1.6b | #200 | B4 |T1.6a; independent review | 8–16h |
| OB1 M3 T1.6c | #200 | B4 |T1.6b; independent review | 6–12h |
| OB1 M3 TR1e | #200 | B4 |T1.6c; ER1 host/born/serial/reset rules | 8–16h |
| OB1 M4 E6 | #200 | B4 |TR1e; ER1/ER2/ER6; duplicate scan first | 8–16h |
| OB1 M4 E4a | #200 | B4 |E6; ER5 statement classification before code | 12–24h |
| OB1 M4 E4b | #200 | B4 |E4a; ER3/ER5/G9;10000edit ASan/TSan stress; Claude review | 16–32h |
| OB1 M4 E5 | #200 | B4 |E4b; ER4 birth inheritance; inventory before code; Claude review | 12–24h |
| OB1 M4 E3a | #200 | B4 |E5 lane release; ER1/ER2 serial reclamation; Claude review | 12–24h |
| OB1 M4 E3b Groove | #201 | B1 |E3a; no overlapping Studio writer | 6–12h |
| OB1 M4 E3c CC/OSC | #201 | B2 |E3a; Studio call-site slot after E3b if overlap | 8–16h |
| OB1 M4 E7 device/buffer state | #201 | B4 |E4b and sidecar release after E3a/E3c; fake device only; review | 8–16h |
| OB1 M4 CN continuity | #201 | B2 |each respective merge; collect once per changed head | 2–4h per stage |
| OB1 S7.3 CHAOS | #202 | B3 |T7.0; module contract-review and measured target | 8–16h |
| OB1 S7.5 Quad VCA | #202 | B3 |T7.0; module free | 4–8h |
| OB1 S7.6 Delay | #202 | B3 |T7.0; module free | 4–8h |
| OB1 S7.7 VCF | #202 | B3 |S6; mapped paths/frozen cases; Claude review | 8–16h |
| OB1 S7.8 Ladder | #202 | B3 |S6+S7.7; same writer; Claude review | 8–16h |
| OB1 S7.9 ADSR/VCO CHOKE | #202 | B3 |S6+T7.0; one PR per module if contract permits; review | 8–16h |
| OB1 M7 after-facts and sound list | #202 | B2 |last sound merge; one main facts refresh; no duplicate captures | 2–4h |
| OB-a2 owner folder runner | #203 | B1 |OB-a1; read-only inputs; owner runs real patches | 3–6h |
| OB-a3 no rewrite/first-save backup | #203 | B1 |OB-a1; native/document free after S5; Claude review | 6–12h |
| OB-b Pi install/launch | #198 | B2 |S6; dry-run paths; no agent device test | 4–8h |
| OB-c regression tests | #207 / PR214 | B2 | SR12 handoff from B1, current branch/head and 1/2 ledger retained | in progress |
| OB-c cause fixes | #203 | file owner |S6; named cause/test, no blanket product scope | 4–16h provisional |
| OB-d affected patch list/rebuild | #202 | B3 |M7batch2; hash/RMS listing first, owner listens | 4–8h |
| OB-e1 module census | #208 / PR221 merged998f56b | complete | 34 actual palette IDs (32 native, two SDK examples) | done |
| OB-e2 every-module smoke | #240 / PR249 merged 137a6ab | complete | 136/136 and zero render allocations/faults, x64 and ARM64 | done |
| OB-e3 module failures | #204 | B3 | waits for actual OB-e2 failure; none in the verified 34-ID matrix | no task released |
| OB-f1 UI facts | #209 | B2 |bench lane after193; measured heaviest patch, four gestures+ack | 4–8h |
| OB-f2 UI fixes | #205 | B1 |f1+Architect numerical targets; Studio free | 8–20h provisional |
| M3 RL | #192 | B1 |182 merged+191Result+Studio slot; behind OB0 work | 4–8h |
| OB1 tag/report | #198 | lead |all contracted evidence incl e2/f2; owner checks explicit | 2–4h |
| Owner real-patch check | #203 | owner |a2 runner; zero unexplained differences | owner availability |
| Owner100Pi edits/no xruns/no stutter | #198 | owner |candidateOB1; two CN transition-cost rows; measured buffer | owner availability |

## Release and review gates
Each task retains its contract's numeric targets, exact-head hosted tests, Golden/Ir/sanitizer requirements and independent review. Required Claude reviews are never replaced by builder/lead self-review. Request once with pinned heads and clauses; use the Architect's scheduled runs, not polling. Corrective rounds remain with the existing branch/PR.

S6 is a planned exclusive rename window: announce at least one day ahead, inventory all open product PRs, merge or explicitly park each, run only mechanical moves/substitutions, then record the path map and rebase resumed work. No new pre-rename product packet that cannot finish or park in that window.

B5 owns only its assigned facts file and read-only checks; it does not hold a product lane. B1 Studio; B2 evidence/tools and uniquely named smoke files; B3 module source; B4 serial engine/control. OB-a3 waits native/document release. Dedicated workflow files avoid an incidental ci.yml writer collision; adding a Lab step uses an explicit lead slot. E3b/E3c share Studio files only sequentially. CN runs in the bench slot, not concurrently with another collector editing the same files.

## Decisions and escalation
OB-f2 numerical targets are missing until f1 measures them: send the actual rows to Architect; never invent a threshold. Unknown module census or smoke failures become named module issues, not suppressed coverage. Palette hiding, if needed, follows the OB r2 disposition and a recorded scoped task. No claim of all modules working without e2 evidence. Any scope/architecture/format/threshold change goes to Architect with a bounded question; unaffected tasks proceed.

Two existing finite local check-ins only; scheduled continuation must read this plan and trackers #198–#210; no added heartbeat/poll. At each check: inspect changed heads/Results once, check usage, resume a stopped authorized builder with a concrete packet, merge earned work, release the next eligible task. Artifact retention is checked once when evidence is delivered; durable hashes/provenance and required release audio must survive before merge. Agent-local diagnostics never replace required hosted or owner-only checks.

Signed: gpt-lead, 2026-11-17
