<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Contracted milestone workflow

Use [BUILDERS](BUILDERS.md) for current and queued work by agent, [ROADMAP](ROADMAP.md)
for milestone order and progress, and [CURRENT](CURRENT.md) for the chronological
lead–Architect handoff. The [Architect inbox](ARCHITECT_INBOX.md) routes design decisions.
This directory also holds milestone contracts, design questions and builder templates. Contracts grant merge authority **per task** only after Fable accepts them.
The draft M0 contract confers no authority by itself.

Workflow: Fable accepts a contract → gpt-lead opens task and batch issues → one builder
owns each task's branch and PR → a PR result comment records evidence and disposition
→ the lead reviews, merges delegated tasks and escalates exceptions → Fable accepts the milestone.

`AGENTS.md`, `CLAUDE.md`, `docs/context/CODEX_LEAD.md`, and
`proposals/0004-execution-plan.md` remain the policy sources; this README supplies
copyable templates and the label lifecycle.

## Owner-started workflow

The lead checks every lane, review and Architect update at each interaction and leaves the next
tasks and ready requests in GitHub. The owner starts and resumes persistent agent sessions
manually. Builders already running can continue under standing releases and draft-ahead rules.

## GitHub labels for work and review

| Label | When to apply | When to remove |
|---|---|---|
| `agent/<name>` and `approver/<role>` | Set the current owner and approver on the task and its linked PR. | Replace stale ownership on reassignment. |
| `status/in-progress` | A released writer has a next action, including a scoped correction. | Replace at review, real blocker or closure. |
| `status/review` | The builder has a review-ready Result for the current head. | Replace on returned work, blocker or closure. |
| `status/blocked` | The task cannot proceed. Record the dependency and how it clears. | Replace as soon as the lead releases work again. |
| `review-required` | A contract, Architect ruling or owner instruction makes independent review a merge condition. May be recorded before the PR is ready. This label never dispatches review. | Clear after valid approval at the current head, or closure. Restore if the head changes and the gate still applies. |
| `review-ready` | Legacy regular-reviewer trigger, retired under Architect-only routing. | Clear stale labels. |
| `architect-ready` | Owner or lead applies once to a verified ready issue to wake the Architect for the Open inbox batch. | Clear after the batch or when readiness is lost. |
| `needs/architect` | Architect ruling, acceptance or Architect-only review with an Open inbox row. | Clear when the ruling/acceptance is recorded and the row resolved. |

Update labels when ownership, state, PR head or review routing changes. At each lead
run, compare every builder's issue and PR with its queue row. Keep one work-status
label on each active item and close out stale operational labels when work finishes.
The issue and PR may differ only when their states actually differ; note the reason
in the queue. Preserve unrelated labels.

The Claude Architect performs all independent and Claude contract reviews under the owner's
2026-11-24 direction. Give each ready review an Open inbox row and `needs/architect`. Keep
`review-required` while it gates a merge. Pin full tested base/head SHAs, invariants and evidence
on the PR. Architect independence and all contract gates still apply. The owner or lead may
apply `architect-ready` once on one linked ready issue at the end of a verified batch. That
wake serves the whole inbox. The owner may also run `architect:run` manually.

## Builder continuation after CI

**Builders keep working (owner, 2026-11-24).** Lane tasks are long and CI is fast, so a builder
session runs until its lane has nothing it can do, not until one PR is ready.
1. After a push, a `/dev-run` or a Result, keep going: the next step of the same task, then
   draft-ahead work on the next task in your lane ([BUILDERS](BUILDERS.md)), then evidence prep.
2. When only a result is missing, wait and re-check once per expected duration: dev-run about
   2–5 min, Lab CI about 10–15 min, M1/Golden about 15 min. No tight polling loops.
3. **Standing release:** when your task's predecessor merges on `main`, your lane's next task is
   released. Start it without asking. A task outside your lane needs the lead's or Architect's
   assignment comment.
4. **Never idle on a question:** add an inbox row (or a QUESTIONS entry) plus the label, then
   continue with the next independent work in your lane (SR19).
5. Stop only when every open PR in your lane waits on someone else (review, merge, ruling) and
   nothing is left to draft. Leave one signed lane-status comment on your newest PR: what waits,
   on whom, and what you will do next. The owner restarts you with "continue".

No automatic CI reruns, no loosened gates, no new task authority.

## Architect dispatch: `architect-ready`

Confirm Open inbox rows, exact pins and the absence of a pending wake. The owner or lead can
apply the label to one linked ready issue after the handoff is published. The Architect reviews
the ready batch and records signed outcomes. Manual `architect:run` remains available.

## Templates

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
Update the issue and PR labels using the lifecycle above. When asking for review,
record the pinned request for the owner's manual review start.

**Review request to `contract-reviewer`**
```text
Contract revision:     Base SHA:     Head SHA:
Invariant clauses to check (quoted):
Question:
```
The reviewer reads the diff and the surrounding callers it needs, nothing else.
