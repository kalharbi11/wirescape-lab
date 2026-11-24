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
| `needs/architect` | Architect ruling, acceptance or Architect-only review with an Open inbox row. Dispatched by the batched `architect-wake` on #265, not by `review-ready`. | Clear when the ruling/acceptance is recorded and the row resolved. |

Update labels when ownership, state, PR head or review routing changes. At each lead
run, compare every builder's issue and PR with its queue row. Keep one work-status
label on each active item and close out stale operational labels when work finishes.
The issue and PR may differ only when their states actually differ; note the reason
in the queue. Preserve unrelated labels.

For a review request, name the authorized reviewer or role, full base/head SHAs, contract
criteria and the evidence to check. If the contract needs Claude or reserves a review for
the Architect, only that role qualifies unless the owner explicitly changes the requirement.
An Architect-only review gets `needs/architect`, an [Open inbox row](ARCHITECT_INBOX.md) and the pinned
request when it is ready, but **not** `review-ready`; the lead dispatches it with the next `architect-wake`. Record planning conditions on the task and in the builder
queue without requesting an Architect run. Rulings and milestone acceptance keep their own
inbox process. Before acting on an event, verify that the PR is still open and non-draft,
`review-ready` is still present, the pinned request matches the live head and the reviewer
is authorized. A new head requires a new signed request before reapplying the ready label.

## Builder continuation after CI

Continue any independent in-scope work while the needed CLI build or checks run. If results
are the only thing preventing progress, schedule one continuation in the same task session
for the expected finish time, using the observed duration or a reasonable documented estimate.
Record the task/PR, head, run link or local job ID and next action. The continuation checks
that the head and writer still match, reads the result once, then carries out the next
authorized action. Repeat for later testing in the same active task. Replace an existing
pending wake for that task and clear it at completion, reassignment or a real blocker.
If scheduling is unavailable, leave a signed handoff with the exact resume trigger. A local
CLI job can be scheduled only where the job and its output survive the wake.
No recurring polling, automatic CI reruns, extra correction rounds or new task authority.

## Intentional Architect wake

The owner verified the Claude label trigger on 2026-11-19. The [Architect inbox](ARCHITECT_INBOX.md)
still records questions and rulings. Routine comments and inbox labels do not wake the Architect.

1. Only the delivery lead may dispatch. Check [#265](https://github.com/kalharbi11/wirescape-lab/issues/265) for a pending `architect-wake` and avoid duplicate batches. Use a wake for a critical-path blocker that cannot wait or a useful batch of ready Architect-only work.
2. Post a new comment on #265 with exact first line `/architect-run`. Include inbox IDs, linked tasks, pinned heads/evidence, what waits and why now. **Then add `architect-wake` to #265.** The label addition is the trigger. Keep #265 limited to this purpose.
3. The Architect reads the newest `/architect-run` comment on #265 as scope, uses the linked inbox/evidence, records its signed result and removes `architect-wake` when done. The removal resets the next wake. The lead does not clear an active wake to resend.

4. After successfully adding the label, schedule one lead check 20 minutes after dispatch, tied
   to the wake comment and inbox IDs. Check signed rulings and status once, update the queue,
   apply cleared decisions and advance ready work. Record the pending trigger if no ruling has
   landed. Arrange the timer from the local lead when the dispatching runtime lacks scheduling.

Keep `review-ready` for pinned regular-reviewer PR reviews. Ready Architect-only reviews ride the same wake as rulings:
list their inbox IDs and pinned heads in the `/architect-run` comment, so one Architect run clears the batch.
Builders and reviewers route wake requests through the lead.
If the Claude integration is reconfigured, match a label addition for `architect-wake` on #265,
not comments, label removal or this label on another item.

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
