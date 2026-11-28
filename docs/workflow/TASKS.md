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

## Lead check — 2026-11-27 17:32 EST

#752 merged as b5cc475: V1 complete, V2 #748 released from current main to the existing V session.
#755 merged as 137e0b0: N complete. W #753 still awaits ready-state gates.
Owner assigned #725 to the Architect; preserve that task and branch. S, T and B dependencies unchanged.

## Bundles (Architect run 60, 2026-11-28: SDK-1 and MB3 merged, M3 accepted)

**MB2 #725 merged as `027db95`** (contract review; A116, A118 and A119; bounded A120). The lab module freeze is over.
Claims live on the task issues. Check the gate column on current `main` before claiming.

| Bundle | Next task | State / gate | Paths (summary) | Merge |
|---|---|---|---|---|
| **S: Studio export and OSC** | SC2 [#721](https://github.com/kalharbi11/wirescape-lab/issues/721) (PR #763) | **In progress (B2).** A121: integrate `main`, fresh full Lab at the new head; if the soak fails wake-only again, stop (waits for X3). A117 paths | `apps/studio/`, `host/osc/`, `host/net/osc_service`, `engine/control/osc_host`, `host/sidecar/` status, schema | Claude contract review |
| **X: CPU probe** | X1 [#759](https://github.com/kalharbi11/wirescape-lab/issues/759) deterministic probe (A120, PR #762) → X2 [#760](https://github.com/kalharbi11/wirescape-lab/issues/760) notes mode (test LR-5) | **Released.** X2 starts after X1 merges | `engine/tests/module_cpu_probe.cpp` and its tests (+ a `bench/gate/instructions.py` flag only if needed) | X1 Claude contract review; X2 lead |
| **X3: soak flake** (new, A121) | X3 [#776](https://github.com/kalharbi11/wirescape-lab/issues/776) Linux ASan wake-only overruns in the edit soak | **Released.** Fact row first, then main-only `/dev-run … repeat=10` | `facts/tests/` only; no harness change without a ruling | lead |
| **T: transport** | TR1h [#740](https://github.com/kalharbi11/wirescape-lab/issues/740) → TR3 [#741](https://github.com/kalharbi11/wirescape-lab/issues/741) | **Held behind SC2.** Both write `host/sidecar/` and `engine/control/` (SR16), so claim T after SC2 merges. It no longer waits for SDK-1. TR3 also needs TR2 | sidecar transport, `engine/control/`, Studio | lead, M3 |

**Done:** U (`3d3db7a`), R (`bbe07ff`, `74f4a3a`), N (`137e0b0`), SC1 (`23f3fe2`), SC4 (`99f7c7f`), MB2 (`027db95`), V (`b5cc475`, `1e2ea1d`), W P1-h (`e8a1ffc`), M SDK-1 (`869e088`), B MB3 (`6d50a9f`).

**Overlap rules.**
- SC2 owns `host/sidecar/` and `engine/control/osc_host` until it merges.
- X owns `engine/tests/module_cpu_probe.cpp`.
- B writes no MB2 evidence files and no `bench/m1/` verdict logic.

**Later (filed when their gate opens):**
- the P1-h OSC-worker half, after SC2;
- PROMO of `wirescape-test` modules (B4, M3 r2.2 and 0024 §2.7): open now that MB2 has merged, but each promotion needs the module's T2 run, which the owner requests;
- #734 (VS18/libremidi pin) now has its post-M slot, but still needs an Architect dependency-pin scope before anyone claims it.

Rules 1–6 above still apply. SR16/SR21 serialize overlapping writers. These packets do not change contracts.

Signed: claude-architect, 2026-11-27
