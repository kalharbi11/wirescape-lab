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

| Bundle | Tasks in order | Paths (summary) | Why now |
|---|---|---|---|
| **U: unblock wirescape-test** (Architect, in review) | #718 CPU probe per-instance config + #719 C4 singleton range (one PR) | `engine/tests/module_cpu_probe.cpp`, `engine/CMakeLists.txt` probe target, `tools/module/runner/abi_ws2.h`, `tools/module/tests/` | Unblocks test PRs #40 (Chord) and #47 (MIDI to CV), then test bundle G (pin bump). Needs a separate session's review. |
| **M: module build** | MB2+CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358) → SDK-1 [#682](https://github.com/kalharbi11/wirescape-lab/issues/682) | per [M3](milestones/M3.md) MB2 and SDK-1 rows | Ends the lab module freeze and accepts M3. Promotions from `wirescape-test` wait on it. |
| **S: Studio export and OSC** | SC4 [#720](https://github.com/kalharbi11/wirescape-lab/issues/720) → SC2 [#721](https://github.com/kalharbi11/wirescape-lab/issues/721) (after SC1 #685 merges) | `apps/studio/`, `apps/desktop/main.ts`; SC2 also `host/osc/`, `host/sidecar/` status, protocol schema | The Studio→Player bundle path and the OSC In indicator ([SC](milestones/SC.md)). |
| **R: render and engine gaps** | #663 `feedback_block` default → renderer UMP events [#722](https://github.com/kalharbi11/wirescape-lab/issues/722) | engine prepare for #663; `tools/render/` for #722 | Small fixes. #722 gives MIDI modules real render coverage (test LR-13). |

**Overlap.** M, S and R write different areas. Two files are shared:
- `engine/CMakeLists.txt`: M owns it, so R rebases onto M on conflict.
- `host/sidecar/`: S (SC2) owns it.

Do not start TR1h until M merges: TR1h writes `engine/control/`, and MB2 requires no open PR there.

**Next bundle, not filed yet:** **T: transport**, TR1h → TR3 ([M3](milestones/M3.md)). It opens when M merges.

Signed: claude-architect, 2026-11-27
