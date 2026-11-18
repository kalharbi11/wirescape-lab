<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB delivery plan — 2026-11-17 ET

Owner-directed scope: OB r2, PRIORITY, M1 r3, M2 r4, M3 r1, M4 r2, M7 r1 and signed Architect rulings. Local gpt-lead delivers; Claude Architect owns design/required reviews. This is a delivery plan, not a contract amendment. All builders work only toward OB0/OB1. SDK/drop-in/dev-loop/panels/Daisy/other hardware/protocol publication/web features and MT2+ are parked. M4's contracted internal protocol/header changes remain necessary for OB1.

## Critical paths and estimates
OB0: max(M2 history + actual review, Reverb S7.1 evidence → S7.2, Macro S7.4, OB-a1) → release/tag. Start S7.4 and OB-a1 now, in separate files. Aim for the first eligible build, not a bundled wait for OB1.
OB1 serial path: M1 S4 → S5a → S5b → S6 → M3 T1.6a → b → c → TR1e → M4 E6 → E4a → E4b → E5 → E3a. Sidecar follows E3a → E3c → E7; Studio E3b/E3c serialize if they touch shared files. Engine/module tests serialize only on actual overlapping files. Other OB tests, sound modules, UI measurements and install work run beside this chain.
Estimates below are initial active engineering hours per task, including a first validation/fix pass. CI queue/runtime, independent/Claude reviews, Architect target-setting and owner Pi availability are additional elapsed time. Re-estimate after each signed Result; do not promise a delivery date before observing those dependencies. OB0 budget roughly 2–4 working days elapsed if evidence/reviews clear; OB1 roughly 4–8 weeks with the current serial engine chain. These are planning ranges, not guarantees or permission to skip gates.

## Review and merge boundary — 2026-11-17, 22:58 EST

190/S4 merged8c72722 by Claude, source26c749d.189/E1b-r merged06e68f0 by lead after exact
edcc97f green+Claude approval. B1 now191 acceptance report only; Architect accepts M2 later.
B4 parked after2127bde1ee compatibility;199 asks Architect releaseS5a, no tracker-only build.
B2 actual230/53317f0 workflow44229365015 completed success; inspect raw artifacts now, numeric
acceptance not inferred.212 Claude source review passed; numeric/Ir/D5 release gates stay.
Architect230 request covers meaningful pitch applicability and Medium wider-rate support.
B3 collector222 review done;196 needs bounded P2/P3 validator correction after B2 current handoff.
B5 readiness inventory done.214 MIDI/ASIO verified, six223 oracles incomplete.
New231 review-label rules replace owner-assigned reviewers;213 and184 source reviews requested.
No192/S5b/S6 release; no product merge beyond earned189; preserve all surviving source invariants.
Signed: codex-lead, 2026-11-17, 22:58 EST

## Local dispatch — 2026-11-17 22:01 EST

Owner authorized agent chat starts; all five existing Wirescape Lab chats active after dispatch.
B1 #207 MIDI CMake/test; B2 delivered209 then226 collector; B3 independent222 review;
B4 delivered190 evidence/admin handoff then212 one-file compatibility transition; B5 read-only198 readiness.
All190 source/CMake/bench writes parked; B1 sole temporary CMake writer, B2 sole226 bench writer,
B3 parks212 while B4 edits only its native/document compatibility block. Actual226 captures wait
for212 handoff, collector implementation does not. Preserve190 changes in later integration.
19026c749d Architect invariants confirmed21:50; independent M1 review and final facts workflow
still required, no S4 merge/S5 release. Two corrections used.223 oracles remain unresolved.
Census221 delivered34 actual IDs versus contract33;209 heaviest-patch proxy is not CPU proof.
No new product lane, chats, schedules or acceptance waiver.
Signed: codex-lead, 2026-11-17, 22:01 EST

## Immediate dispatch, one active writer per file
B1: #182/PR189 correction1 published edcc97f; park source for review, take #206 OB-a1 in new files while waiting. Return to182 only for concrete review/CI failure. #191 report after actual merge; #192 RL lower priority than OB0 tests.
B2: #193/PR196 collector8be53d3; finish real R2/D5 and release handoff. Then #209 UI facts when the bench lane is free; smoke tests follow the census merge and a separate issue. B5 owns #208.
B3: #155/PR184 source8823c78 parked awaiting193; start #210 S7.4 Macro in its own module folder now. S7.2 follows155 actual merge, using the same source owner; finish/park Macro before switching. No duplicate Reverb capture.
B4: #188/PR190 capturefd0b905; verify actual384000-byte reference, commit exact bytes/hash/provenance, convert assertions, then delete. Architect190#6950233998 rules. Then serial S5a/S5b/S6; no other builder edits engine/control.

B5 (owner-authorized floater, no permanent product lane): #208 read-only source census, then a small read-only OB0 evidence-readiness inventory for #198, then available for explicitly assigned gaps. No automatic takeover of B1–B4 files. This is a bounded staffing exception authorized by the owner on 2026-11-17; it does not waive review or lane limits.

## Complete task ledger
Ready task issues #206–#210 and blocked workstream trackers #198–#205 cover every row below. A tracker is not permission to implement an unmet dependency. Every future implementation gets its own issue/branch/PR, exact allowed paths, contract criteria and mapped S6 paths at release.

| Build / task | Issue or tracker | Builder | Dependency / gate | Active effort |
|---|---|---|---|---|
| OB0 T7.0 baseline | #152 merged | complete | retained facts | done |
| OB0 M2 E1b-r | #182 / PR189 | B1 | correction1; exact-head Lab + independent Claude M2 review | 2–6h remaining |
| M2 final report | #191 | B1 |189 merged; Architect accepts milestone separately | 1–2h |
| OB0 S7.1 Reverb | #155 / PR184 | B3 |193 actual evidence + independent lead review/release pair | 1–3h remaining |
| OB0 R2/D5 capture | #193 / PR196 | B2 |actual x64/ARM64 production artifacts; lead release upload | 2–6h |
| OB0 S7.2 Reverb gain | #202 (stage issue after155 merge) | B3 |155 merged; same module writer | 4–10h |
| OB0 S7.4 Macro rate support | #210 | B3 |ready; 24models×rates,48k identical, required contract-review | 12–24h |
| OB0 OB-a1 round-trip CI | #206 | B1 |ready; bundled+each config shape; no loader fixes | 6–12h |
| OB0 tag/release/install check | #198 | lead |all OB0 criteria on main; preserve immutable fallback tag | 1–3h |
| OB1 M1 S3 | #159 merged | complete |reviewed prior evidence retained | done |
| OB1 M1 S4 | #188 / PR190 | B4 |exact frozen capture before conversion/deletion | 8–16h remaining |
| OB1 M1 S5a | #199 | B4 |S4 merged; I1–I8 | 8–16h |
| OB1 M1 S5b | #199 | B4 |S5a merged; required Claude contract-review | 8–16h |
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
| OB-c regression tests | #207 | B1 |ready in isolated tests; Studio lane after182 source park | 8–16h |
| OB-c cause fixes | #203 | file owner |S6; named cause/test, no blanket product scope | 4–16h provisional |
| OB-d affected patch list/rebuild | #202 | B3 |M7batch2; hash/RMS listing first, owner listens | 4–8h |
| OB-e1 module census | #208 | B5 |ready; census33 actual modules, read-only sources | 2–4h |
| OB-e2 every-module smoke | #204 | B2 |e1; native/tests2 slot after a1;44.1/48k,64/256,2s,sweep,RT | 6–12h |
| OB-e3 module failures | #204 | B3 |e2 actual failure; one module PR each; preserve goldens | 2–8h/module provisional |
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
