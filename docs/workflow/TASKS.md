<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Lab task pool: short bundles (owner, 2026-11-27)

The owner moved new lab work from fixed lanes to a small pool of short, lettered bundles, as in
`wirescape-test` and `wirescape-headless`. **No bundle is assigned to an agent until a session claims it.**
Each bundle has one session and no more than three tasks. Each task gets one issue, one branch and one PR.
Only a few PRs are open at a time. The owner can stop after any bundle and re-plan.

Started lane work finishes as it is: SC1 #685 stays with its session. The [BUILDERS](BUILDERS.md) hold still
covers lane queues that are not listed here. Contracts, reviews, CI gates and SR rules are unchanged.

## Rules
1. **Claim.** Comment `Claimed: <session>; <date>; branch: <branch>` on the bundle's next open task issue.
   Do not claim a second bundle while yours has an open PR. A claim is not permission to skip a dependency.
   - Before you take over an old claim, check its branch and PR and record the handoff.
2. **One open PR per bundle.** Start the next task from current `main` only after the previous task merges.
   - A task may run as a draft ahead only when its issue says so.
3. **Test first,** then the fix. Post a signed Result comment (template in [README](README.md)) with the
   exact head and the exact-head CI links.
4. **Review** follows the task's contract row:
   - `lead` tasks merge on exact-head green plus the Result.
   - `Claude contract review` and `Architect review` tasks get one [inbox](ARCHITECT_INBOX.md) row and
     the `needs/architect` label.
   - A task the Architect wrote needs a separate session's review.
5. **Stay in your paths.** If a file belongs to another open bundle PR, ship your own part now. The rest
   becomes a follow-up task (SR21).
6. **Stopping:** leave `Status: handoff-ready | blocked` and remove your claim.

## Bundles

Claims live on the task issues. Lead check, 2026-11-27: M, S and R remain claimed; MB2 #725 and SDK-1 #731 are drafts, SC4 #726 and #663 #727 merged, and renderer #736 is open. T, B and N are unassigned; check the release gates below before claiming.
Rulings: A112 (SC4 bridge and headless check), A113 (MB2 order and projection), A114/A115 (MB2 isolation evidence and SDK trial runner).
**2026-11-27 run 59:** #663 merged (`bbe07ff`), so R moves to #722. SC4 merged (`99f7c7f`), so S's SC2 waits on SC1 #685 and, under A117 (it writes `engine/control/osc_host`), on MB2 #725. A116 rules on MB2's `finite_samples` regression.

| Bundle | Tasks in order | Paths (summary) | Why now |
|---|---|---|---|
| **U: unblock wirescape-test** (done) | #718 + #719 C4 | — | Merged as `3d3db7a` (#724), 2026-11-27. Test bundle G may bump the pin. |
| **M: module build** | MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358) → SDK-1 [#682](https://github.com/kalharbi11/wirescape-lab/issues/682) | per [M3](milestones/M3.md) MB2 and SDK-1 rows | Ends the lab module freeze and accepts M3. Promotions from `wirescape-test` wait on it. |
| **S: Studio export and OSC** | SC4 [#720](https://github.com/kalharbi11/wirescape-lab/issues/720) → SC2 [#721](https://github.com/kalharbi11/wirescape-lab/issues/721) (after SC1 #685 merges) | `apps/studio/`, `apps/desktop/main.ts`; SC2 also `host/osc/`, `host/sidecar/` status, protocol schema | The Studio→Player bundle path and the OSC In indicator ([SC](milestones/SC.md)). |
| **R: render and engine gaps** (done: #663 `bbe07ff`, #722 `74f4a3a`) | #663 `feedback_block` default → renderer UMP events [#722](https://github.com/kalharbi11/wirescape-lab/issues/722) | engine prepare for #663; `tools/render/` for #722 | Small fixes. #722 gives MIDI modules real render coverage (test LR-13). |

**Overlap.** M, S and R write different areas. Two files are shared:
- `engine/CMakeLists.txt`: M owns it, so R rebases onto M on conflict.
- `host/sidecar/`: S (SC2) owns it.

Do not start TR1h until M merges: TR1h writes `engine/control/`, and MB2 requires no open PR there.

## New unassigned bundles (owner request, 2026-11-27)

| Bundle | Tasks in order | Release / writer gate | Merge |
|---|---|---|---|
| **T: transport** | TR1h [#740](https://github.com/kalharbi11/wirescape-lab/issues/740) → TR3 [#741](https://github.com/kalharbi11/wirescape-lab/issues/741) | After M completes (#725 and #731), Gate P0/TR1e; serialize sidecar/control with active SC2, and Studio with SC1/SC2. TR3 also requires TR2. | lead, M3 |
| **B: build verification** | MB3 [#742](https://github.com/kalharbi11/wirescape-lab/issues/742) | After M completes. Only its new workflow and tools/ci or bench helpers; no MB2 evidence-file overlap. | lead, M3 |
| **N: neutral fixture names** | [#622](https://github.com/kalharbi11/wirescape-lab/issues/622) | **Released** (SC1 merged `23f3fe2`, run 59e). Serialize fixture, spec and sidecar files with SC2 or T once they open. Historical facts unchanged. | lead, original issue |

These are task packets, not advance agent assignments. No draft-ahead for T, B or N.

## Released now: no dependency on M or open bundles (Architect run 59d, owner, 2026-11-27)

Claimable today. Their paths are disjoint from #725 at `bf32d05` and from S, T, B and N, so they wait on nothing.

| Bundle | Tasks in order | Paths (summary) | Release gate | Merge |
|---|---|---|---|---|
| **V: render case coverage** (test LR-7) | V1 [#747](https://github.com/kalharbi11/wirescape-lab/issues/747) per-note velocity and channel → V2 [#748](https://github.com/kalharbi11/wirescape-lab/issues/748) per-channel evidence | `tools/render/` only (`main.cpp`, `evidence.py`, tests, one new case). Existing cases and goldens are unchanged | none; V2 after V1 merges | lead |
| **W: realtime coverage** (P1-h, audio half) | [#749](https://github.com/kalharbi11/wirescape-lab/issues/749) allocation and lock checks on the real PortAudio callback | `host/audio/` tests and test-only seams; `allocation_watch.*` read-only | none | lead (Claude contract review only if a product line changes) |

- **V and W share no files.** Two sessions may hold them at once.
- **The OSC-worker half of P1-h** is filed after SC2 merges, because it writes SC2's `host/osc`/`host/net` paths (A117).
- **LR-5 (probe plays notes)** is not released: it writes the CPU probe that MB2's gates measure. File it after M.
Use the claim comment in rule 1 on the first issue; read its complete paths, tests and evidence gates.
Release gates are checked on current main, not inferred from a green draft.
SR16/SR21 serialize overlapping writers; new packets do not change contracts.
SC2 remains behind **SC1 and MB2**, including A117's engine/control/osc_host paths.
SDK-1 #731 is an existing owner-authorized draft-ahead exception, not a general permission.

**Parked:** #734 (VS18/libremidi) still needs the Architect's post-M slot and dependency-pin contract scope.
#326 and #494 are closed; do not create duplicate soak work from the one diagnostic L2 overrun.

Signed: codex-lead, 2026-11-27, 13:51 EST

Signed: claude-architect, 2026-11-27
