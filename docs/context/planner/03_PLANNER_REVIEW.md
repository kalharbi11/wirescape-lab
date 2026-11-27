<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 03 — Planner self-review of 0023/0024, brief for run 2b (2026-11-26)

**Run 2b (or `planner: run 2`) reads this file first, before 02 "Run 2b prep"; it corrects that list.** It is the `claude-planner`'s own review of
0023 and 0024, done at the owner's request (2026-11-26) after 2a merged and MOD-0 ran in `wirescape-test`.
It was written while the Architect was building MOD tasks and changes none of that work; it lands only as this file and inbox row `Planner-review`.
**Authority:** the owner asked the Planner to review and improve its own plans. So run 2b may **amend 0024**
for the items in section 1, in a short "0024 amendments" section of `0025`. That permission covers section 1
only. Everything else in 0024 stands and is not reopened.

**Applied (2026-11-26, run 2b part 1, lab and `wirescape-test` only):** §1 and §3.3 are now
[0024 §9](../../../proposals/0024-test-repo-macros-modules.md#9-amendments-2026-11-26-claude-planner-run-2b-part-1-lab-and-wirescape-test-only).
§1.1 was decided there: the two UI CTests gate again (with a per-module `presentation.json`); the S0 snapshot
stays deferred until promotion. §1.2 adds block 48 and names the `feedback_block` default as the cause. Run 2b
does **not** redo §1 or §3.3. It starts at §2 and §3.1–§3.2, and 0025 has no "0024 amendments" section.

**Read at:** lab `main` `83cc53c`; `wirescape-test` `main` `238017f` (+ open PR #4 `06002cb`);
`wirescape-headless` `main` `39e244d`. Re-check any line before relying on it. Lab state moves fast.

---

## 0. Verdict
0023 and 0024 hold up. The transcription is faithful: MM r1, M3 r2.1, the freeze and the errata. MOD-0 runs:
T0 takes about 1m40s against a 10-minute budget, T1 about 3m, and T2 about 8m. The harness enforces the pin.
The plan has three real defects and two gaps, all fixable with small amendments:
1. **T2 "every lab CTest" was wrong.** It turned T2 red for every new module (lab #652).
2. **0024 §6 "Player uses `setParam` only" conflicts with an owner want:** live control of modulation
   amounts (`01_OWNER_WANTS` B.2; headless `docs/REQUIREMENTS.md`).
3. **Architect independence breaks at promotion** when the Architect itself builds the MOD modules.
4. **Gap:** the hardware-knob path through the Player has no latency budget.
5. **Gap:** nothing fixes a date for the MB2-slip fallback, and MB2 is now the critical path.

## 1. Amendments to 0024 (2b writes them; small and final)

### 1.1 T2 and the catalogue-sync CTests (lab #652). Supersede the deferral if the generators allow it
- **Fact.** With only the three registration lines, these tests drift by construction for any new module:
  `ui_catalogue_sync` (`tools/gen_ui_catalogue.py --check`, `host/document/CMakeLists.txt:40-41`),
  `ui_patch_conformance` and `abi2_sidecar_snapshot_tests` (`native/CMakeLists.txt:180`).
  The Architect's interim ruling (wirescape-test PR #4, open) runs them but records them under
  `deferred_to_promotion` and does not gate on them. That is acceptable as an interim. It still leaves a hole:
  no test checks a new module's UI catalogue entry or patch conformance before the strict lab PR. 0023 §4.4's
  overturn rule says such checks move earlier, into T1/T2, and never later.
- **Amend 0024 §2.3.** Registration may also run **the lab's own generators, unmodified, in the scratch
  tree**, exactly the commands the promotion PR will run. Start with `tools/gen_ui_catalogue.py` without
  `--check`, and add whatever regenerates `ui_starters`/`wirescape_modules.json` and the sidecar snapshot
  testdata, if a generator exists. This counts as mechanical registration, not a hand patch.
- **Then T2 gates on every CTest again.** The deferral stays only for a test with no generator, named in the
  closed list with its reason, and it ends at MB2.
- **2b checks first**, in about 3 reads: which of the three files have a generator, and whether MB2 (#358)
  makes them generated anyway. If MB2 covers all three, keep PR #4's deferral until MB2 and only add the
  expiry "ends at the MB2 pin bump".
- Do not touch PR #4 while the Architect's run is open. The amendment lands in 0025, and a later
  `wirescape-test` PR applies it.

### 1.2 T2 block sizes
- **Fact.** T2 records blocks 16 and 17 as `skip`, because the lab case `adsr-notes` fails to prepare at
  those sizes (`Cannot prepare graph`; `wstest.py:862-876` probe).
- **Amend §2.4.** Change "blocks 16, 17, 128 and 512" to "the blocks the pinned renderer accepts, with skips
  recorded in `t2.json`".
- A lab render case that cannot prepare at block 16 is a lab fact nobody has filed. 2b asks the Architect for
  one `limitation found` issue, or a facts row if the limit is intended. Do not drop the rows silently.

### 1.3 T2 dispatch
Ratify PR #4's wording: an agent may dispatch `t2.yml` when the owner asks in the session or the PR. Minutes
are free; concurrency slots are the cost. 0024 §2.4 "run by the owner" becomes "requested by the owner".

### 1.4 Promotion review when the Architect built the module
- **Fact.** The MOD tasks are being built in the Architect's own session. PROMO-n needs an **Architect
  review**, and Architect independence binds it (CLAUDE.md "Review queue"). That makes the review a
  self-review.
- **Amend §2.7 step 2.** A module whose `wirescape-test` PRs were authored by the Architect gets its PROMO
  review from a **separate Claude session**. Any of these qualifies, signed with its own name:
  - a `claude-planner` run;
  - a fresh `review` session with no build context;
  - a helper reviewer session, as MOD-0's `claude-reviewer` was.
- The Architect may still accept the milestone. The `wirescape-test` "different agent session" review
  already works this way.

### 1.5 MM1 partial ACK (inbox row B1-MM1-ack, open). State 0024's intent only
- 0024 §3.7 meant **mapping commits are atomic from the user's view**. It did not foresee an `applyGraph`
  ACK that carries `unapplied` parameter events (`RealEngine.ts:521-577`).
- Intent: on any `unapplied` event, Studio restores the prior document state and shows the refusal. Prefer
  whichever option has **one code path**: an explicit compensating `applyGraph` is likely simpler than
  correlated live compensation.
- The ruling itself is the Architect's, because MM is its contract now. 2b writes only this intent line, and
  only if the row is still open.

## 2. Corrections to the 2b reading list (02 "Run 2b prep" and the scout pack)
| Claim in prep | State at `83cc53c` |
|---|---|
| A100 `data_slots` is in the `hello` catalogue | **Not on main.** It lands with #545 (open, `638d8b6`). `engine/data_slots.h` exists. Treat discovery as pending #545. |
| `setOsc` refused at `session.cpp:1257` | Now `:1281`, still `unavailable`. Runtime OSC config needs OB-h2 #601 (draft #638). |
| Registration is "three hand edits" | Plus three drifting CTests (lab #652, section 1.1). |
| OB-h1 routing of #326/#494 is settled | Both are open and `status/blocked`. Pi soak claims stay unmeasured. |
| Gate P1 (e) "filed at Stage 2" | **No issue exists.** Only `OB.md:110-111` and 0023 R2.3 mention it. 2b's shapes become its issue body. |
| headless `REQUIREMENTS.md` "desktop stops after 3 crashes in 30 s" | Stale since #624. The backoff is 250 ms to 30 s with no limit (`apps/desktop/main.ts:15-19`). 2b's headless PR fixes the line. |
| — | The engine has `--null-audio` and `--capture-null-sink` (`host/sidecar/session.cpp:214-220`). Player integration tests can run in CI with devices off. Verify that it also skips MIDI enumeration before relying on it. |
| — | MB1 #642 is green at its head but blocked on the A97 follow-up ruling. MB2 #358 has no PR. |
| — | `ROADMAP.md` and `PRIORITY.md` have no MM or MOD rows. That is an Architect edit; list it in 0025 §Edits. |

## 3. What I would change in run 2b

### 3.1 Scope: cut it so it fits one session without compaction
Five questions (2, 4, 5, 7 and 8) is still too much. Order them by what unblocks work, and **park
question 5**:
1. **Q2 core:** the Player service, the API with versioning and the fake player, and `player.json`.
2. **Gate P1 (e)** message shapes.
3. **Q4:** OSC naming, OSC In UI rulings and script auto-sync. The runner and helper library are in scope;
   graphics are out.
4. **Q8:** the stage order and the first task batch per repo.
5. **Q7:** the guide list only: names, homes and the format. No guide text.

For **Q5 (tool page host)**, rule only what fixes its boundaries: it uses the 0015 sandbox, it is never in
the Player, and its first tool is the Python editor. Write a "decide later" row with a trigger, "when the
script runner exists". Nothing in the Player or OB1 path needs it now (`01_OWNER_WANTS` B.9: "Not shipped in
the Player").

If context runs short, commit 1–4 and leave the rest as open items. Never compress the P1 (e) shapes.

### 3.2 Decisions 2b must make that 0024 left open or got wrong
1. **Modulation amounts in the Player (fixes section 0, item 2).**
   - Add a third `player.json` target form for **ordinary modulation cables** (LFO→cutoff and the like),
     moved live with `setModAmount`. 2b picks a stable cable identity from the patch format: source
     module/port plus target module/param.
   - Mapping cables, whose amount is a range, stay Studio-only.
   - Bundle check: a `modAmount` target on a mapping cable is an **error**.
2. **The hardware-knob path and its latency.** The engine owns MIDI and OSC devices (0023 R2.3 e), so a
   `player.json` knob runs: device → engine → P1 (e) stream → Player → `setParam` → engine.
   - Set a budget: a proposal of p99 ≤ 10 ms added latency on the Pi at 100 CC/s across 8 knobs.
   - Make it a facts row before Player v1. It stays unmeasured until then.
   - State the rule: **in-patch mappings (Studio map mode) are the low-latency path**, and `player.json` is
     for patch-independent and setParam-only controls.
   - The overturn: if the budget fails, the Player prefers patch-side mappings. It never edits patches, so
     the bundle check suggests them instead.
3. **Program Change** goes through the P1 (e) FIFO, which never coalesces it. Fix how the Player debounces a
   burst of PCs: the last one wins after N ms, with no queue of swaps.
4. **The Player vs a running sequencer at a switch.** 0023 R2.2 (c) and OB-h3 already release gates. Name
   which OB-h3 rows the Player's switch test reuses.
5. **The headless CI pattern.** Copy `wirescape-test`'s proven shape and do not invent a new one:
   - `LAB_PIN` fetch with `verify()`;
   - a `scope` job plus an always-run gate job;
   - one concurrency group per PR;
   - ccache keyed by pin;
   - pinned cmake and ninja.

   Build only `wirescape-engine` (headless options) from the pin, and run it with `--null-audio`. Copy the
   fetch and verify code from `wstest.py` with its source commit noted, so the repos share no package.
   Tiers: H0 on Linux x64 for every push (fake player, API contract and Player unit tests); H1 on ready PRs
   (arm64 and a real-engine integration run with `--null-audio`); H2 by owner request (a soak and the Pi).
6. **The first headless task needs no engine:** the Player API schema plus the fake player plus contract
   tests. The UI and the service develop against it in parallel. That is the analogue of MOD-0.
7. **Guides that already have a home:** `wirescape-test` README covers the module build guide's stage 1.
   The lab `docs/MODULE_BUILD_GUIDE.md` rewrite becomes stage 2 (promotion) only.

### 3.3 Order and critical path (for Q8)
- **MB2 is the critical path.** It blocks promotions, MM2's RealEngine path, M3 acceptance, the freeze end
  and the Player's catalogue consumers. 0023 §7.4 says "if MB2 slips more than two weeks", but gives no
  start date.
- **2b fixes the date:** two weeks from the MB1 merge, or **2026-12-10 ET** if MB1 has not merged by
  2026-11-30. After that date, the fallback (promote with three registration lines, reviewed once per
  module) applies with no further ruling.
- **Stage the Player behind:**
  - Gate P0 (#619 and #620 are both in draft; P0 rows gate any Player build relying on the engine);
  - #601 for runtime OSC;
  - #545 for `data_slots`.

  The fake-player track starts at once, because it depends on none of them.

## 4. What would overturn this review
- The generators cannot run without hand edits on the pin. Then PR #4's deferral stands until MB2, with an
  expiry.
- The owner rules that the Player never moves modulation amounts. Then drop 3.2.1, and the owner want is
  re-worded instead.
- A measured Pi CC round trip is well under budget. Then `player.json` knobs are a full peer of in-patch
  mappings, and the "low-latency path" rule is dropped.
- The Architect's run finishes MOD work with a helper session as author. Then 1.4 is moot for those
  modules.

## 5. For the Architect's current run (no action from 2b)
- Post the #652 ruling on the lab issue. It lives only in wirescape-test PR #4. Close the issue when PR #4
  merges.
- File the two `limitation found` issues that PR #4 says the envelope overrides need, naming the tests.
- MOD-4 (Clock Div/Mult) is unfiled. It waits on MOD-3 as planned.

Signed: claude-planner, 2026-11-26 17:20 ET
