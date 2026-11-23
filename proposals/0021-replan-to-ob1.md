<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0021 — Replan to OB1: fewer tracks, one serial chain, CI as the builder's computer

**Status:** proposed by the Claude Architect, 2026-11-23 12:40 ET, at the owner's request ("step back,
zoom out, reorganize"). Section 5 lists owner decisions D1–D6, each with a recommended default.
**In effect now** (Architect authority, no contract meaning changes): §4 rules R1–R3 and the
engine draft-ahead rule in §2. Everything else waits for the owner's answers.

## 1. What went wrong (from the queue on 2026-11-23)

1. **OB1's real length is one serial engine chain.** T1.6c → TR1e → E6 → E4a → E4b → E5 → E3a, then E3b/E3c, with
   E7 in the sidecar lane. Only T1.6a/b are done. T1.6c has not started, because its only writer (B5) is
   on OB-g3 #324. That task is on the OB-g track, which r2.4a made advisory.
2. **Most active PRs are off that path.** Of the 10 open task PRs, three are OB1 items: #298 OB-a3, #291 S7.5 and
   #275 OB-c. #291 has been idle since 2026-11-21 and #275 since 2026-11-20. #333 Gate Delay, #356 Poly Merge, #322 note trigger, and the queued CAT-1 #358 and MB1 #363 are new module
   or module-platform work. MB1 is P4 ("parked until OB1") in PRIORITY. TR2 was P4 and has merged anyway.
3. **New modules collide on shared hand lists:** the catalogue TU, the S0 snapshot, `known_module_ids`, and
   CMake lists. Each module PR then pays one or two correction rounds for reasons that are not its own.
   Examples: #333 LFO inlining (A32), #333 red Golden after TR2 moved S0, #322 `host.keyboard` Ir rise.
4. **The sound work sits in one lane.** M7 S7.3 and S7.5–S7.9 are queued one after another for B3. They touch
   different module folders, so they could run in parallel.
5. **OB-c cause fixes have no owner.** #275 was parked "until after S6". S6 merged on 2026-11-22, and no
   lane has taken #275 since. OB1 acceptance 2 needs OB-c merged.
6. **Every task now needs a build environment.** So every builder runs in Codex or ChatGPT work mode, which
   costs Codex usage. The free chat mode is idle.

## 2. The new OB1 plan: four tracks, one of them serial

| Track | Writer(s) | Order | Notes |
|---|---|---|---|
| **E — engine (critical path)** | B5 only | T1.6c → TR1e → E6 → E4a → E4b → E5 → E7 (sidecar, may start after E4b) | **Draft-ahead (in effect now):** the writer may draft task N+1 on a branch stacked on task N's head while N is in CI or review. Merge order and every "Depends on … merged" condition stay as written. E3a–E3c depend on D1. |
| **S — sound** | B3 and B4, by module folder | B3: S7.5 #291 → S7.6 #314 → S7.9. B4 (after its two PRs): S7.7 → S7.8 (same writer, Claude review). B1 (after OB-c): S7.3. **OB-d once**, after the last S7 merges | The folders do not overlap, so there is no shared writer. |
| **Q — OB quality** | B1 | #298 OB-a3 (Architect review) → OB-c cause fixes (#275/#203, one cause per PR) → S7.3 | OB-b, OB-e2 and OB-f targets are done. OB-f is re-checked once on the candidate. |
| **I/O — advisory (r2.4a)** | B2 | #339 OB-g8 → #324 OB-g3 (moves from B5, D3) → E3c later if D1 keeps it | One writer for `engine/control/{osc,midi}_host*`, so no SR12 hand-offs. |

**Module platform, outside OB1:** #333 and #356 finish under their current rulings. Then **CAT-1 and MB1
become one task** (D2). They touch the same files (catalogue, CMake lists, generated IDs), so they need
only one M1 re-baseline. After MB, a new module edits zero shared files. This is the "one module makes the
next one easier" step, and every module idea in §4 R1 waits for it.

**Critical path with D1 = (a):** 6 serial engine PRs (T1.6c, TR1e, E6, E4a, E4b, E5), with E7 beside
them. Without D1 it is 7 serial PRs plus E3b and E3c. The S and Q tracks have slack against that chain, so they never
set the date.

## 3. Environments: CI is the builder's computer

**Fact:** `kalharbi11/wirescape-lab` is public, so its GitHub-hosted Actions runs are free and unmetered.
The Golden 3-platform workflow took 7 to 36 min on 2026-11-23 (runs 45227103545, 45216595722, 45204610193).
The paid resource is the agent's own sandbox. The builds themselves cost nothing.

| # | Change | Cost | Effect |
|---|---|---|---|
| **C1** | **CI digest comment** (D4): a `workflow_run` job posts one sticky comment per PR head, at most 60 lines. It lists each gate's result, the first compiler errors with file:line, failing test names and assertions, Golden mismatches, and M1/Ir rows over 1 %. It never checks out PR code. It needs `pull-requests: write`, which SR4 reserves. | one B-class CI task | A builder that can only read GitHub gets the full build and test loop with no sandbox. |
| **C2** | **`/ci` targeted runs:** a comment from the owner or a collaborator runs one test regex, one module's Ir row or one Golden patch on the PR head. The result goes into the digest. | one B-class CI task, after C1 | About 5 minutes per iteration, instead of waiting for the full matrix. |
| **C3** | **Chat-mode builders push through GitHub** (D5). If ChatGPT chat mode can use a GitHub MCP connector with write actions (developer mode), the builder commits to its task branch and reads the C1 digest. If it cannot, the fallback is that the builder outputs a `git diff` and the owner applies it with one local script on Windows. | owner test: one builder, one B-class task | Moves most lanes off Codex usage. |
| **C4** | **Task classes by environment need.** *Chat mode:* docs and facts, Studio TypeScript, module DSP with existing tests, mechanical refactors proved by Golden, new tests. *Codex or cloud sandbox:* the E-track C-class tasks, perf attribution (callgrind), sanitizer debugging. The lead tags each issue `env/chat` or `env/sandbox`. | lead, at filing | Codex usage goes mostly to B5 and to rare diagnosis. |
| **C5** | **Pi without hosted minutes** (A31): move wirescape-pi's dispatcher jobs to `runs-on: self-hosted` on the Pi. Self-hosted runs use no Actions minutes. Making that repository public is the other option, if it holds no secrets. | one Architect PR on wirescape-pi | Solves A31 part (1). The 401 token in part (2) is still the owner's to fix. |
| **C6** | **No self-hosted runner on the owner's Windows PC for the lab repo.** It is a public repo, so a pull request from a fork could run code on that PC. Hosted Windows CI is free anyway. Real-device runs stay owner-only, as they are today. | none | Keeps the PC safe. |

## 4. Rules that stop the drift (R1–R3 in effect now)

- **R1 Intake.** A new module or feature idea goes to the parking list in CURRENT ("Ideas parked until OB1").
  It is filed as a task only when the Architect places it in a track. No task is filed between rulings without a
  track.
- **R2 Work in progress.** Each lane holds one active PR. Only the E track may also hold one draft-ahead branch.
- **R3 Critical path first.** The E-track writer takes no off-path work. When an off-path module PR fails a gate
  because of shared code (codegen coupling, a shared S0 or ID-list conflict), it parks behind CAT-1+MB and does not open a new
  diagnosis loop. Parking is not loosening: the gate and tolerance stay as they are.

## 5. Owner decisions (recommended default first)

| ID | Question | Recommended | Alternative and cost |
|---|---|---|---|
| **D1** | OB1 scope: move E3a/E3b/E3c (module data in the header; Groove steps and CC/OSC rows as live data) to **OB1.1**? | **Yes.** After E5, a Groove or CC-row edit is already a crossfaded replace that keeps state. So no edit restarts the patch, and E3 only makes these edits cheaper. E3a also changes the `0012` header, which is the largest review on the list. | Keep E3 in OB1: about 3 more serial tasks (planning estimate 26–52 h, OB_PLAN). |
| **D2** | Freeze new modules until OB1, and combine CAT-1 + MB1 into one task in B4 after #356? | **Yes.** | Keep them separate: two re-baselines and two rounds of catalogue churn. |
| **D3** | B5 hands #324 to B2 after its current correction round, then starts T1.6c. #322 parks until CAT-1+MB merges and is then re-measured, and B3 moves to S7.5. | **Yes.** | B5 finishes #324 first: the critical path waits about 1–2 days. |
| **D4** | Allow the C1 digest workflow to have `pull-requests: write` (outside SR4)? | **Yes**, on a `workflow_run` job that never checks out PR code. | No digest: chat-mode builders have to read raw Actions logs, if they can read them at all. |
| **D5** | In your setup, can ChatGPT chat mode write to GitHub (commits, PR comments)? | Test C3 with one builder. | Patch-file fallback: about 1 minute of owner time per iteration. |
| **D6** | What are the "47 of 200 GitHub credits" (Codespaces hours, Copilot requests, Actions minutes on wirescape-pi)? | Keep them for owner-run diagnosis. Hosted lab CI does not use them. | If they are wirescape-pi Actions minutes, C5 removes that need. |

**What would overturn this plan:** the E chain gets shorter (an E task found to be unneeded), or a sound
task turns out to need the engine writer. Either one reorders the tracks, not the rules.

Signed: claude-architect, 2026-11-23
