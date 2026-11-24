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

The review labels describe two different states. For the GitHub `pull_request: labeled`
event, dispatch review only if `github.event.label.name == 'review-ready'`. The former
`claude-review/reviewer`, `claude-review/architect`, `claude-review` and `reviewer`
labels are retired. Update any external automation that still matches them.

| Label | When to apply | When to remove |
|---|---|---|
| `agent/<name>` and `approver/<role>` | Set the current owner and approver on the task and its linked PR. | Replace stale ownership on reassignment. |
| `status/in-progress` | A released writer has a next action, including a scoped correction. | Replace at review, real blocker or closure. |
| `status/review` | The builder has a review-ready Result for the current head. | Replace on returned work, blocker or closure. |
| `status/blocked` | The task cannot proceed. Record the dependency and how it clears. | Replace as soon as the lead releases work again. |
| `review-required` | A contract, Architect ruling or owner instruction makes independent review a merge condition. May be recorded before the PR is ready. This label never dispatches review. | Clear after valid approval at the current head, or closure. Restore if the head changes and the gate still applies. |
| `review-ready` | The lead verified a non-draft PR, the signed Result and evidence needed for review at its current head. After posting the pinned request, add this label to the PR to dispatch. Both review labels may coexist. **Regular reviewer only:** never on an Architect-only review (Architect, 2026-11-23). | Clear after a signed result, loss of readiness, head change, cancellation or closure. Keep `review-required` on findings or missing evidence. |
| `architect-ready` | The lead verified a ready Architect item (Open inbox row, `needs/architect`, pinned request). Starts an Architect run; one per lead run. | The Architect removes it when the item is handled. |
| `needs/architect` | Architect ruling, acceptance or Architect-only review with an Open inbox row. Dispatched by `architect-ready`, never by `review-ready`. | Clear when the ruling/acceptance is recorded and the row resolved. |

Update labels when ownership, state, PR head or review routing changes. At each lead
run, compare every builder's issue and PR with its queue row. Keep one work-status
label on each active item and close out stale operational labels when work finishes.
The issue and PR may differ only when their states actually differ; note the reason
in the queue. Preserve unrelated labels.

For a review request, name the authorized reviewer or role, full base/head SHAs, contract
criteria and the evidence to check. If the contract needs Claude or reserves a review for
the Architect, only that role qualifies unless the owner explicitly changes the requirement.
An Architect-only review gets `needs/architect`, an [Open inbox row](ARCHITECT_INBOX.md) and the pinned
request when it is ready, but **not** `review-ready`; the lead dispatches it with [`architect-ready`](#architect-dispatch-architect-ready). Record planning conditions on the task and in the builder
queue without requesting an Architect run. Rulings and milestone acceptance keep their own
inbox process. Before acting on an event, verify that the PR is still open and non-draft,
`review-ready` is still present, the pinned request matches the live head and the reviewer
is authorized. A new head requires a new signed request before reapplying the ready label.

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

(Architect run 20, 2026-11-23; replaces the #265 `architect-wake`/`/architect-run` wake, which was tested once.)
`architect-ready` works like `review-ready`, but it starts the **Claude Architect** instead of the regular reviewer.
The owner wires the Claude integration to start an `architect:run` session when `architect-ready` is
**added** to a PR or issue in this repository. Label removal and comments do not trigger it.

1. **Lead, when an Architect item is ready** (review, ruling or acceptance): the inbox row is Open, the item
   has `needs/architect` (plus `review-required` for a review gate), and a pinned request names full base/head
   SHAs, criteria and evidence. **Then add `architect-ready` to one item per lead run, the most urgent.** Other
   ready rows ride along: every Architect run clears all ready Open rows, so one trigger serves the whole batch
   and the duplicate runs that one label per item would cause are avoided. Never put `review-ready` on
   Architect-only work.
2. **Architect:** reads the inbox as usual, handles every ready row, and removes `architect-ready` (and
   `needs/architect`, review labels) from each item it finishes. A run that finds nothing new stops at the quick check.
3. **Lead:** reads the outcome in the inbox Cleared table and CURRENT at its next run. No timer is needed.
   Builders and reviewers ask through the lead.

#265 and `architect-wake` are retired. The owner may remove that trigger.

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
