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

## GitHub labels for work and review

Use literal label names. GitHub triggers receive a single label name per event.
Match `github.event.label.name` exactly, including the slash. Quote the full label when
using the CLI, for example `gh pr edit 255 --add-label "claude-review/reviewer"` **only when
a review is ready**. `claude-review` and `reviewer` are retired split names.

| Label | When to apply | When to remove |
|---|---|---|
| `agent/<name>` and `approver/<role>` | Set the current owner and approver on the task and its linked PR. | Replace stale ownership on reassignment. |
| `status/in-progress` | A released writer has a next action, including a scoped correction. | Replace at review, real blocker or closure. |
| `status/review` | The builder has a review-ready Result for the current head. | Replace on returned work, blocker or closure. |
| `status/blocked` | The task cannot proceed. Record the dependency and how it clears. | Replace as soon as the lead releases work again. |
| `claude-review/reviewer` | Independent Claude review is requested for the current PR head. | Reviewer clears after posting the signed response; lead clears stale requests. |
| `claude-review/architect` and `needs/architect` | Architect-only review with a corresponding Open inbox row. | Clear when the ruling/review is recorded and the row resolved. |
| `needs/architect` | Architect ruling or acceptance with an Open inbox row. | Clear when the ruling/acceptance is recorded and the row resolved. |

Update labels when ownership, state, PR head or review routing changes. At each lead
run, compare every builder's issue and PR with its queue row. Keep one work-status
label on each active item and close out stale operational labels when work finishes.
The issue and PR may differ only when their states actually differ; note the reason
in the queue. Preserve unrelated labels.

For a review, record the full base and head SHAs, the contract criteria and open evidence
in a PR comment, then apply the exact review label as the dispatch signal. On a new head,
clear the old signal and post the new pinned request before reapplying it when ready.
A draft lacking review-ready evidence should stay out of the review queue. An Architect-only
ask also needs its [inbox row](ARCHITECT_INBOX.md). In trigger consumers, check the exact label
and current head again before starting, since a queued event can become stale.

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
post the pinned request before applying the review label.

**Review request to `contract-reviewer`**
```text
Contract revision:     Base SHA:     Head SHA:
Invariant clauses to check (quoted):
Question:
```
The reviewer reads the diff and the surrounding callers it needs, nothing else.
