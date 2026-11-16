<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Lab workflow: deployment plan

Written 2026-11-15 against lab `main` at `71daa1c`. This is a plan for other agents to deploy, split
into work packages (WP) that each fit one agent run. Nothing here is in force until WP1 merges; until
then `AGENTS.md`, `CLAUDE.md`, `docs/context/CODEX_LEAD.md` and `proposals/0004` apply as written.

It builds on the Codex proposal the owner shared (`wirescape-workflow-plan.md`). It keeps that
proposal's structure and cuts most of its infrastructure, because the constraint is two days of
Fable usage, not missing tooling.

## 1. The design in one page

**Three roles, three stopping points.**

| Role | Owns | Stops when |
|---|---|---|
| **Fable** (Opus after the promotion) | Design notes, milestone contracts, answers to queued questions, milestone acceptance | The contract or decision is written to a file |
| **gpt-lead** (Codex) | Delivery of one contracted milestone: issues, builder dispatch, review, corrections, merges the contract delegates | Acceptance report filed, or a real escalation |
| **gpt-builder1..4** (ChatGPT chat mode) | One substantial task each: implementation, tests, CI fixes, review corrections | PR ready with a result comment, or blocked |

**Where Fable's usage goes today, and the fix for each.**

| Cost today | Fix |
|---|---|
| Approving each step and assigning each builder | Milestone contract: the lead has written merge authority and never asks for routine approval |
| Re-reading the broad read map at every run | `docs/workflow/CURRENT.md` (about 400 words) is the only startup read |
| Reading code and logs in the main context | A Sonnet `evidence-reader` reads and returns a short cited answer |
| One wake-up per question | The lead appends to `docs/workflow/QUESTIONS.md`; Fable answers the whole file in one run |
| A LOG pull request per check-in | The handoff rides in the PR that did the work; LOG gets one entry per milestone |
| New chat every few prompts, context rebuilt each time | One session per design question; it ends when its file is merged |

**What Fable should spend the promotion on:** design artifacts that outlive it. A finished design
note is worth more than a merged PR, because Opus and the builders can implement against it after
the promotion ends. Order in section 5.

**Deliberately not built during the sprint:** a SQLite controller, a GitHub App, webhooks, Claude
channels, saved dynamic workflows, integration branches, a project board, required GitHub approvals
(every agent is one GitHub identity, so the rule could not be satisfied). Revisit after the sprint
if the manual batch loop proves its worth.

## 2. Authority model (replaces "only Fable merges class B")

Classes A/B/C in `0004` keep their meaning as *risk* classes. Merge authority moves to the milestone
contract, per task:

| Contract says | Meaning |
|---|---|
| `merge: lead` | The lead reviews against the criteria and merges on green |
| `merge: lead after contract-review` | A scoped Claude `contract-reviewer` run (Opus, narrow window) finds nothing High, then the lead merges |
| `merge: fable` | Fable reviews the diff itself |

Proposed defaults, for Fable to confirm or change in each contract:

| Task kind | Default |
|---|---|
| Class A | `merge: lead` |
| Class B with a behaviour-preserving criterion (golden identical, instruction counts not worse) | `merge: lead` |
| Class C implemented from an accepted design note | `merge: lead after contract-review` |
| Class C with no accepted design note | Not delegable. Fable writes the note first |

Always Fable, in any milestone: `proposals/`, `docs/context/CONSTRAINTS.md`, the contract itself,
what a measurement means, a declared sound change, a golden tolerance or gate threshold, protocol /
module API / ABI shape, realtime thread ownership. Always the owner: "Fixed" constraints, listening,
real devices.

The lead decides without asking: in-scope implementation choices, CI failures, test design,
follow-up issues inside the milestone's allowed paths, merge order, rebases by merging `main`.

## 3. Work packages

Run in this order. WP1 is the only one that needs Fable; WP2–WP4 can go to a builder or a Sonnet
session in parallel once WP1 is open.

### WP0 — owner, about 20 minutes, no agent
1. Say yes or no to section 2. A "yes" is the authority for WP1.
2. GitHub settings on the lab: allow squash merge only, auto-delete head branches, protect `main`
   (require a PR, block force-push and deletion, require the Lab CI checks). Take the required check
   names from the checks list of a recent merged PR, not from `ci.yml`: `native` is a matrix job and
   its emitted names differ from the job key. Do **not** require approvals.
3. Rename chats to the scheme in section 6 and archive every chat whose PR is merged.
4. T0.14 (native build in the cloud container) is an environment network setting, not a code
   task. Decide whether to allow the blocked dependency hosts; an agent can name them from the
   failing build log.

### WP1 — policy PR (Fable reviews the diff; any agent may draft it)
One PR, docs only. Draft from the text below, so Fable spends one short review instead of authoring.

- **`AGENTS.md`**: replace the status paragraph with: Fable leads design; gpt-lead delivers
  contracted milestones and starts builders directly; builders no longer wait for the owner.
  Change the gpt-lead row of "Who's who" to "delivery lead: runs a contracted milestone end to end
  (`docs/context/CODEX_LEAD.md`)". Replace "Never sleep or poll on CI or a reply" with "No model
  run waits on or re-checks unchanged state. Scripts and GitHub Actions may watch CI and events."
  Add one line: "A builder task ends with a result comment on its PR (template in
  `docs/workflow/README.md`)."
- **`CLAUDE.md`**: replace Fable's read map with: `docs/workflow/CURRENT.md`, then only what it
  and the specific ask name. The old map stays as "orientation, only when CURRENT says so".
  Replace the "GPT builders are paused" rule with the role table of section 1. Replace "merge
  your own PRs… review and merge builder PRs" with "merge what a contract marks `merge: fable`".
  Change the LOG rule to "one LOG entry per milestone or at the end of a usage block, inside the
  PR that carries the work". Add the Fable run protocol (section 4) verbatim.
- **`docs/context/CODEX_LEAD.md`**: rewrite as the delivery-lead brief (section 7 is the text).
- **`proposals/0004-execution-plan.md`**: under "Who may do what" add: "Merge authority is set per
  task by the active milestone contract in `docs/workflow/milestones/`; without a contract the
  table above applies." Replace "If Fable is unavailable" with a pointer to the contract.
- **New `docs/workflow/CURRENT.md`**: active milestone and contract revision, baseline SHA, open
  task issues and PRs by number, accepted decisions as links, blockers, next action for each role.
  Hard limit 600 words. The lead updates it at each batch boundary, Fable at each contract change.
- **New `docs/workflow/QUESTIONS.md`**: the lead's queue for Fable. Each entry: question, why the
  contract does not settle it, evidence links, the lead's proposed answer, what is blocked
  meanwhile. Fable answers in place and bumps the contract revision if the answer changes it.
- **New `docs/workflow/README.md`**: the three templates of section 8.
- **New `docs/workflow/milestones/M0.md`**: the first contract (section 9).

Done when: the four old documents no longer contradict each other or this plan; CI green.

### WP2 — templates and labels (builder or Sonnet, small)
`.github/ISSUE_TEMPLATE/task.md` and `batch.md`, `.github/pull_request_template.md` from section 8.
Labels: `batch`, `batch/ready`, `milestone/M0`, `milestone/M1`, `needs/fable`. Done when a test
issue from each template renders correctly and is closed again.

### WP3 — Claude agent definitions (Sonnet session, small)
Add `.claude/agents/evidence-reader.md` (Sonnet, tools `Read, Glob, Grep`),
`design-specialist.md` (Opus, `Read, Glob, Grep, Agent`), `contract-reviewer.md` (Opus,
`Read, Glob, Grep, Bash`). Prompts as in the shared Codex proposal section 6, with these changes:
every agent returns at most 400 words plus `file:line` citations; the reviewer gets `Bash` so it
can run `git diff base..head` itself, and its prompt forbids every other command; the specialist
may start at most one `evidence-reader`.

Before committing, check each frontmatter field (`model`, `effort`, `tools`, `maxTurns`) against
the current sub-agents documentation. The same goes for any `settings.json` keys: the env names and
`workflowSizeGuideline` in the Codex proposal are **unverified** and must not be committed on its
word. Skip `.codex/agents/` for now: the builders run in chat mode, where those files do nothing.

Done when: Fable starts each agent once on a trivial question and gets a cited answer.

### WP4 — batch barrier (builder, class A, about 150 lines)
The piece that turns "four builders finished" into one signal, with no model in the loop.

- A **batch issue** (label `batch`) lists its task issues as a checklist and carries a `Deadline:`
  line (ET).
- `.github/workflows/batch-barrier.yml` runs a Python script from the default branch on:
  `issues` and `pull_request` label changes, PR close, completion of the Lab CI workflow
  (`workflow_run`), and a 15-minute `schedule` as the deadline net. It never checks out PR code.
- For each task in each open batch without `batch/ready` the script finds the PR (`Closes #n`),
  its head SHA, its disposition (`status/review`, `status/blocked`, merged, or none) and whether
  every check on that head has completed.
- **Barrier:** every task has a disposition and no checks are pending on its head, **or** any task
  is `status/blocked`, **or** the deadline passed. Then, once: post one comment with the table
  (task, PR, head sha7, checks, disposition), add `batch/ready`, mention the repo owner.
- Idempotent: `batch/ready` present means do nothing. The lead removes it when it dispatches
  corrections, which re-arms the barrier for the new heads.
- Tests: unit tests for the barrier decision with fixture JSON; no network in tests.

Done when: a dry batch of two no-op PRs produces exactly one comment and one notification.

### WP5 — wake-up delivery (owner's machine; only after one manual batch has worked)
- **Stage 0, works today:** the owner gets the `batch/ready` notification on their phone and sends
  the lead one message: `lead: run B<n>`. One tap per batch instead of one per builder. This is
  enough for the sprint.
- **Stage 1, optional:** a 30-line local script polls `gh issue list --label batch/ready` every
  few minutes and delivers the same message to the lead session. The Codex proposal names
  `codex queue --thread <id> --message …`; that is **unverified here**. Test it by hand first:
  queue a harmless message, confirm the lead actually replied, confirm it works with the app
  closed and reopened. If any of that fails, stay on stage 0.
- **Fable:** no automation. The lead sets `needs/fable` on the acceptance issue or on a
  QUESTIONS PR; the owner sends `fable: run accept M0` or `fable: run questions`. Fable wake-ups
  should be rare enough that a tap each is cheaper than any mechanism.

## 4. Fable run protocol (goes into `CLAUDE.md` verbatim)

1. **Start:** read `docs/workflow/CURRENT.md` and the one input the ask names. Nothing else until a
   question needs it.
2. **One question per session.** Triggers: `fable: run design <topic>`, `fable: run questions`,
   `fable: run accept <milestone>`. A session ends when its file is in a PR.
3. **Reading is delegated.** Any question that needs more than about three files goes to
   `evidence-reader` with an exact question; only its cited summary enters your context. A hard
   alternative worth a second opinion goes to one `design-specialist`. At most three Claude agents
   at once, helpers included.
4. **Output is a file,** never a chat answer: a design note in `proposals/`, a contract in
   `docs/workflow/milestones/`, answers in `QUESTIONS.md`. Decisions, not option lists: where you
   are unsure, pick, state the assumption and name the evidence that would overturn it.
5. **Contracts freeze.** Changing one that builders are working under means a new revision number,
   a list of affected tasks, and a line in CURRENT telling the lead to stop or replan them.
6. **Never in a Fable run:** reading CI status, changing labels, assigning builders, reviewing a
   `merge: lead` PR, a LOG-only pull request.
7. **Acceptance:** read the lead's report, spot-check the two riskiest criteria through
   `evidence-reader` or `contract-reviewer`, then accept or list concrete gaps. Do not re-review
   every PR.
8. **Before a usage block ends:** commit, push, update CURRENT with head SHAs and the next action.

## 5. Sprint order for Fable's usage

| Block | Fable produces | Unblocks |
|---|---|---|
| 1 | WP1 review; `M0.md`; rulings already open: what T0.8 latency measures and its timing reference, what T0.5 needs for impulse/tail, the T0.13 edit-continuity harness design | The lead runs all remaining Phase 0 without Fable |
| 2 | Design note for T1.2/T1.3: deletion order, the engine-native types, invariants, which steps must land green on their own; then `M1.md` | One integration-owner builder for T1.2/T1.3; others on T1.1, T0.11, T0.12 |
| 3 | Note `0005` (T2.0): edit operations, state-carrying replace, module data, protocol v1 schema. The largest deep-thinking item and independent of builder progress | All of Phase 2, after the promotion |
| 4 | T1.8 module-build design; `QUESTIONS.md`; contract-review of the first T1.2/T1.3 PR; contract corrections | T1.8, T1.9 |

Keep roughly a fifth of each usage reset for block 4-style corrections. If a block runs short,
drop implementation review before dropping a design note: reviews can be done later by Opus,
the design notes are what the promotion is for.

Builder concurrency follows the dependency graph, not the number four. During T1.2/T1.3 there is
one writer in `native/` engine and scheduler files. T1.4 (rename and layout) is a stop-the-world
step: every other product PR merges or waits, T1.4 lands, open branches merge `main`.

## 6. Chats, branches, pull requests

- **Chat names:** `WLAB | PLAN | <topic>`, `WLAB | LEAD | M0`, `WLAB | BUILD | #55 golden gate`,
  `WLAB | REVIEW | <PR>`. One planning chat per design question, one lead chat per milestone, one
  builder chat per task including its corrections. Archive on merge.
- **New chat when** the task changes or the milestone closes, not every few prompts. Inside one
  coherent task use `/compact`. The handoff file is the memory, so a replacement chat starts from
  CURRENT plus the task issue.
- **One task = one issue = one branch `task/<issue#>-<slug>` = one PR = one writer.** A new chat
  continues the same branch and PR.
- Independent tasks branch from `main` and target `main`. A dependent task starts after its
  prerequisite merges. No stacked PRs and no integration branch during the sprint.
- The lead merges serially. After each product-tree merge it has open PRs that touch the same area
  merge `main` and waits for their checks again: green from before an interacting merge proves
  nothing.
- A review approves a head SHA. A new push needs a new look at the new diff only.

## 7. Delivery-lead brief (new text for `CODEX_LEAD.md`)

```text
You are gpt-lead. You deliver the active milestone at its recorded contract revision.
Read: AGENTS.md, this file, docs/workflow/CURRENT.md, the contract it names. Then live PR state.

Each run (trigger `lead: run`, or `lead: run B<n>` after a batch-ready signal):
1. Review every PR in the ready batch against its task's criteria and the contract. Evidence must
   match the criterion, not just be green.
2. Merge what the contract marks `merge: lead`. For `merge: lead after contract-review`, set
   `needs/fable` with the base and head SHAs and the invariant clauses; merge after a review with
   nothing High. Never merge `merge: fable`.
3. Send corrections to the builder's existing chat, on the same branch. At most two correction
   rounds per task; then write it up in QUESTIONS.md.
4. File the next task issues the contract's dependency graph allows, open a batch issue listing
   them with a deadline, and start the builders yourself. Up to four, fewer when tasks would
   touch the same files.
5. Update CURRENT.md (one PR per batch boundary, merged on green).

You decide: in-scope implementation choices, CI failures, test design, follow-up issues inside the
contract's allowed paths, merge order.
You escalate through QUESTIONS.md, with evidence and a proposed answer: anything that changes
architecture, what a measurement means, an invariant, an acceptance criterion, a gate or
tolerance, a protected constraint, or the milestone's scope. Keep unaffected tasks moving.
You never: edit proposals/, CONSTRAINTS.md, the contract, AGENTS.md or CLAUDE.md; weaken a gate;
run device tests; force-push; re-check unchanged state in a loop.

Milestone end: one acceptance report mapping every criterion to its evidence (PR, head SHA, run
or fact file), then `needs/fable` on the acceptance issue.
Sign: `Signed: gpt-lead, <YYYY-MM-DD>` (New York date).
```

## 8. Templates (for `docs/workflow/README.md`)

**Milestone contract**
```text
Milestone / revision:            Baseline commit:
Outcome:
Accepted design (links):
Invariants (numbered):
Tasks: id | issue | class | allowed paths | depends on | merge: lead / lead after contract-review / fable
Single-writer areas:
Acceptance criteria, each with the exact evidence required:
Out of scope:
Escalate when:
```

**Task issue (builder packet)**
```text
Milestone / revision / batch:     Base SHA:
Goal:
Allowed paths:
Contract clauses that apply:
Read first (files, symbols):      (a starting point; trace further when correctness needs it)
Do (numbered):
Done when:
Order:
You own implementation, tests, CI fixes and review corrections. You do not merge.
```

**Builder result comment (on the PR, last thing in a run)**
```text
Result: ready | blocked     Task: #…     Head: <full sha>
Criteria: <each "Done when" line> → <evidence link>
Not verified / risks:
Blocked on:
Signed: <name>, <YYYY-MM-DD>
```
Then set `status/review` or `status/blocked`. The label is what the barrier reads.

**Review request to `contract-reviewer`**
```text
Contract revision:     Base SHA:     Head SHA:
Invariant clauses to check (quoted):
Question:
```
The reviewer reads the diff and the surrounding callers it needs, nothing else.

## 9. First contract: `M0.md` (draft for Fable to confirm)

- **Outcome:** Phase 0 of `0004` complete; `facts/BASELINE.md` filled.
- **Tasks, `merge: lead`:** T0.5 (#51), T0.6 (#52), T0.7 (#53), T0.8 (#54), T0.9, T0.10, T0.11,
  T0.12. Check each against live state first; several have merged or moved since `0004` was written.
- **T0.13:** blocked on Fable's harness design (block 1), then `merge: lead after contract-review`.
- **T0.14:** owner.
- **Open rulings Fable writes into the contract before T0.5 and T0.8 are accepted:** the quantity
  and timing reference the latency tool reports; the impulse/tail instrumentation T0.5 needs.
- **Evidence beyond green CI:** each criterion's "Done when" from `0004` with the run or fact file
  that shows it; golden gate 24 identical on three platforms for anything touching `native/`.
- **Escalate when:** a metric's definition would change, a gate would become blocking or stop
  being blocking, or a task needs a path outside `bench/`, `facts/`, advisory workflows.

## 10. After the promotion

Same documents, smaller numbers: Opus in Fable's seat, one lead, one builder, occasionally two.
Keep CURRENT, contracts, QUESTIONS and the barrier. Recheck the ChatGPT usage accounting before
relying on chat-mode builders long term; the Codex proposal reports an announced change to shared
usage, which this plan has not verified.
