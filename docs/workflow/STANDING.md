<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Standing rulings: what the lead decides without asking
Accepted by Fable, 2026-11-16 (ET). These rulings apply to every active contract, unless a contract says otherwise.
The lead acts, records the SR number in the PR and in CURRENT, and does not queue a question.

**Bounds on every SR (B1–B6).** B1: never weaken a gate, tolerance, invariant or acceptance
criterion. B2: never change architecture, the meaning of a protocol command or measurement,
`module2.h`, public engine API, module/port/parameter IDs, or a Fixed constraint. B3: devices off.
B4: no force-push, history rewrite, repository-setting change or admin merge. B5: one writer per
file. B6: if an SR does not clearly fit, escalate and name the SR that almost fits.
**SR1 CI speed and structure.** The lead may file and merge CI tasks (parallelism, sharding,
job split, path-scope rules) that touch only workflows and `tools/ci/`. Bound: CI1 K1–K5 hold
(same test list at base and head, no skip/retry/timeout raise/`continue-on-error`, every job on
`main` push and manual run); before/after times go in `facts/tests/`. Precedent: Q6.
**SR2 Caches.** Allowed on any CI job: `main` and manual runs build cold and save, pull requests
only restore; key includes OS, arch, compiler identity and flags. Keep-or-drop is fixed in advance:
keep only if a warm PR run saves at least 2.0 min; else close the PR and file the
numbers. Cold or missing-cache runs prove nothing either way. Precedent: Q9, CI1 K7/K8.
**SR3 Required check names.** The lead may rename jobs and add literal aggregate jobs, so the seven
required names always report. An aggregate passes only if exactly one matching job in the same run
attempt concluded `success`. Logic lives in `tools/ci/` with unit tests for each failing case. No job
succeeds without checking. The required list itself is the owner's. Precedent: Q7.
**SR4 Workflow permissions.** Job-level `contents: read` and `actions: read` only, on the job that needs them; `github.token` only, sent as a header to
`api.github.com`, never printed, stored or output. Every HTTP error fails; no retry, no anonymous
fallback. Any other scope, secrets and `pull_request_target` are reserved. Precedent: Q12.
**SR5 Red and flaky checks.** Infrastructure failure (runner lost, cache/API 5xx/403/429,
checkout timeout): one full "re-run all jobs" per head, with the error quoted in the PR. A test
failure is never rerun to green: diagnose it. A test that fails then passes on the same head is
logged as a fact in `facts/tests/flaky.md` and becomes a task; it is never marked flaky, retried or
skipped. Merge needs a fully green exact-head run. Precedent: Q12 point 5, Q14.
**SR6 After two correction rounds.** Work ordered by a ruling uses no round and resets nothing.
After round 2, pick the first that fits, with no question: (a) the failing items existed before:
revert each to the PR's previous state, file a neutral disagreement or fact row, and merge if every
criterion still holds; (b) one final packet, if the fix stays in allowed paths, the lead can write
the exact rule and the new tests, and no invariant moves; (c) otherwise, or if (b) fails: close
the PR unmerged, keep the branch, file a new task issue under the same contract with the findings.
Escalate only if refiling needs a contract change. Precedent: Q13 point 5, Q14 point 6.
**SR7 A file outside the task's paths.** The lead may grant up to 3 extra files when the edit is
forced by the contracted change and mechanical: removing or renaming uses of a symbol the task
deletes, an include, a CMake list entry, a test expectation that names that symbol. No new
behaviour, no new feature test, no edit to `module2.h`, protocol spec meaning, `proposals/`,
CONSTRAINTS or a contract. Not when the file is another open task's single-writer area (order the
tasks instead). List files and reason in the PR and CURRENT. Precedent: Q15.
**SR8 Test wiring.** A task's own tests with no CI hook get a new workflow file, modelled on
`continuity.yml`: pull requests touching the test directory or the workflow, plus manual runs; one
job; no `continue-on-error`; not a required check. `ci.yml` is edited only by its single writer.
The file counts as part of the task's allowed paths. Precedent: Q11.
**SR9 Evidence substitutions.** Hosted-runner results satisfy a criterion that names no machine.
Hosted timing is an advisory fact, never a pass mark. Device-only rows stay device-only: no agent
run fills them. `/dev-run` and local builds support diagnosis; merge needs hosted exact-head CI. "Golden
24 identical" is always three platforms. Precedent: R2, M0 acceptance table.
**SR10 Unmeasured rows.** Record `unmeasured`, `not_built_*`, `unavailable` or `device-only`
with the reason. Never zero, never interpolated or copied from another row. Carry it into the
acceptance report as an exception; no claim may cite it until it is measured. Precedent: R4,
M0 acceptance (`ringmod2`).
**SR11 Contract review.** A reviewer independent of the lead and builder checks the quoted
  invariants and evidence at the exact head. Nothing High means the lead can merge under the
  existing contract. Routing (owner, 2026-11-24): the Claude Architect performs all independent
  and Claude contract reviews via the inbox, with pinned base/head, `review-required` and
  `needs/architect`. The owner or lead may apply one `architect-ready` wake per verified batch.
  Builders and the lead keep unrelated work moving.
**SR12 Staffing.** The lead may move a task to another builder when the writer gave no substantive
result after one supported retry, or stopped. The old writer is told to stop first; the branch, PR and
round count carry over; a handoff comment records the change. At most five builders (B1–B5, all ChatGPT chat sessions; no Codex builder sandboxes, 2026-11-24).
Claude builder lanes (CB1–CB3) are off. Lead changes are the owner's. Precedent: Q15 staffing, CURRENT.
**SR13 Doc-only PRs.** CURRENT, LOG, QUESTIONS and `facts/` PRs merge on green under the scope
rule. A facts PR also gets a neutral-wording review. A required check that hangs on a doc-only PR is
a CI defect to fix under SR3, never a waiver. Precedent: Q7, CODEX_LEAD step 5.
**SR14 Tooling pins.** The lead may pin or bump CI tooling (actions, runner image, Python/Node for
`tools/ci/`) to fix CI, if the test list is unchanged. Product dependencies (`URL_HASH`, app
lockfile versions) change only when a task names them. The seeding recipe in CURRENT stays
byte-identical. Precedent: CI1.3, CURRENT seeding rule.
**SR15 Paths after the rename.** Contract paths are written in the names the tree had when the
contract was accepted. After M1 S6 they mean wherever the S6 script moved them. The lead writes
the mapped paths into the task issue. Not a contract change.
**SR16 Order between ready tasks.** One writer per lane: engine, sidecar and host, modules and
build, Studio and desktop, tools and bench. When two ready tasks need the same lane or builder:
M1 stages first, then the M4 chain and what it depends on (the owner's top wish), then M5, then
the rest of M3, then M6 and M7, then M8, M9, M10, M11, M12 in number order. M10 batch 0
(facts) and M12 P0 are class A and never wait. A lane with nothing ready does not wait: take the next milestone.
**SR17 Protocol additions.** Every task that adds or changes a command, reply field or capability
also changes `docs/specs/protocol.schema.json`, regenerates, and keeps the drift check green, in
the same PR. Those files count as part of its allowed paths once M2 PV1 is merged.
**SR18 Facts tasks.** The lead may file and merge class-A tasks (`bench/`, `facts/`, advisory
workflows) that measure or inventory something an active or queued contract will need. A facts
file states numbers and sources; it never says what should be done.
**SR19 Nothing waits for the design authority.** A question or review that is pending blocks only
the task it names. Every other ready task proceeds. An acceptance report is filed when a
milestone's tasks are merged; the next milestone's tasks start on their own "Depends on" cells.

**SR20 Fewer stops (Architect, 2026-11-24, run 29, A57; owner: "move forward without many stops
until merge-ready").** (a) **Self-release:** a builder starts the next task in its BUILDERS queue
when its predecessor merges; if the issue does not exist it opens one quoting the contract row.
No lead assignment comment is needed. (b) **Low findings never block a merge.** They become one
follow-up line in the lane queue. (c) **`merge: lead` with no review condition:** exact-head
required checks plus a signed Result are enough; the lead (or the Architect) merges or enables
auto-merge without a separate pinned request. (d) **Facts-only PRs** (`facts/` only, no product
path) auto-merge on required checks under SR18. (e) **Rulings travel:** when a written ruling
covers a case (for example A58's OSC fix routing), the lead releases the task without asking the
Architect again. (f) A Claude contract-review is asked **once**, at the head the builder calls
merge-ready; intermediate heads are not reviewed. None of this changes a gate, a tolerance or a
"Fixed" item.

**SR21 Split, don't wait (Architect, 2026-11-25, run 37; owner: "B4 is stuck because of B1").**
(a) When a task needs a file that another lane is still writing in an open PR, the part inside
the builder's own paths ships on its own. The part that touches the other lane's file becomes a
follow-up task, released when that PR merges. The whole PR never waits for another lane.
(b) The lead names the split in the assignment comment. A split needs no Architect ruling unless
it changes a contract gate. (c) Work that has not started yet moves to the least loaded lane
whose paths fit it, even when an earlier contract row named another lane.

## Who decides what
1. **The lead:** in-scope implementation, test design, merge order, and SR1–SR19 within B1–B6.
2. **The design authority in session** (Fable, or Fable's deputy on an Opus session; see
   `CLAUDE.md`): applying an existing proposal or ruling to a new case; contract revisions that
   fix paths, ordering or dependencies or add a mechanical task inside an accepted design;
   a correction packet beyond SR6; milestone acceptance against the written criteria with the
   exceptions kept explicit; contract reviews; a new SR that writes down an existing precedent.
3. **Fable only:** a new proposal or architecture; what a measurement means; changing an
   invariant, gate threshold or tolerance in any proposal or contract (0005 section 9 and B1–B4,
   0006 I1–I8, 0008 K1–K4, 0009 L1–L5, 0010 P and Q, M2 J1–J5, M4 G1–G8, CI1 K1–K9, M8 W1–W8, M9 V1–V5, M10 X1–X6, M11 Y1–Y6,
   M12 Z1–Z6, the guarantees of 0013 section 2, golden
   "24 identical", the 1 % instruction-count rule); the module header and module API shape; the
   panel and patch formats; protocol versions and schema keywords; realtime ownership.
4. **The owner:** the Fixed constraints; intentional sound changes by ear; IDs before release;
   the required-check list and repository settings; who leads and which Claude sessions run.

A question names its rung and the SR that almost fits. A rung-3 question does not stop the lab:
the deputy records it in QUESTIONS as `reserved/fable` with its recommendation, and SR19 applies.

Signed: Fable, 2026-11-16
