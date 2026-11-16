<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Contracted milestone workflow

This directory records the single current handoff (`CURRENT.md`), the batched
design-question queue (`QUESTIONS.md`), milestone contracts and builder packet
templates. Contracts grant merge authority **per task** only after Fable accepts them.
The draft M0 contract confers no authority by itself.

Workflow: Fable accepts a contract → gpt-lead opens task and batch issues → one builder
owns each task's branch and PR → a PR result comment records evidence and disposition
→ the lead reviews, merges delegated tasks and escalates exceptions → Fable accepts the milestone.

`AGENTS.md`, `CLAUDE.md`, `docs/context/CODEX_LEAD.md`, and
`proposals/0004-execution-plan.md` remain the policy sources; this README supplies
copyable templates. WP2 will install GitHub-native issue/PR templates and labels;
WP4 will install the batch barrier. Neither is part of WP1.

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
Then set `status/review` or `status/blocked`. The label is what the barrier reads.

**Review request to `contract-reviewer`**
```text
Contract revision:     Base SHA:     Head SHA:
Invariant clauses to check (quoted):
Question:
```
The reviewer reads the diff and the surrounding callers it needs, nothing else.
