<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_SCOUT — the Sonnet digest that opens an Architect run

Owner, 2026-11-17: an Architect run may open by sending one **read-only Sonnet subagent** to
gather the state, so the Architect reads one short digest and decides what to check itself.
The scout collects and quotes. It never rules, grades findings, edits the repo or comments on GitHub.

## When to send it
- **Send** when the inbox has 3 or more Open rows, or more than ~5 PRs/issues changed since the
  last run, or the last "Next run should" list names 3 or more items.
- **Skip** when the inbox is empty or has only one or two rows. Reading them directly is cheaper.
- One scout per run. If the digest leaves a gap, read that one item yourself rather than sending a
  second scout.

## How to send it
`Agent` with `model: "sonnet"`, `subagent_type: "general-purpose"`, `run_in_background: false`,
and the prompt below with `<SCRATCH>`, `<LAST_RUN_SHA>` and `<NEXT_RUN_LIST>` filled in.
The prompt is the scout's only context. Then read `<SCRATCH>/digest.md`, and nothing else
unless the digest marks an item `ARCHITECT-CHECK`.

## Scout prompt (copy, fill, send)
```
You are a read-only scout for the Claude Architect of the wirescape-lab repo
(/home/user/wirescape-lab). Do not edit files, commit, push, comment, label or merge.
Do not judge designs or grade findings; quote and link only.

Read:
1. docs/workflow/ARCHITECT_INBOX.md (Open rows) and docs/workflow/CURRENT.md.
2. Open PRs/issues labelled needs/architect or needs/fable:
   gh api -X GET search/issues -f q='repo:kalharbi11/wirescape-lab is:open is:pull-request label:needs/architect'
   (repeat with is:issue, and with label:needs/fable). gh is allowed for search only; use
   `gh api repos/kalharbi11/wirescape-lab/issues/<n>/comments` to read the last 2 comments of each.
3. Commits on origin/main since <LAST_RUN_SHA> (git fetch origin main; git log --oneline).
4. For each item in this list, its current state: <NEXT_RUN_LIST>

Write <SCRATCH>/digest.md, at most 60 lines, in this exact shape:
## Inbox
| ID | Urg | Ask | State now (1 line) | Head SHA |
## Labelled but not in the inbox
(same columns; say "none" if empty)
## Next-run list
| Item | State now | Merged? (sha) |
## Merged to main since <LAST_RUN_SHA>
one line each: sha, PR, title
## Quotes
For every ask that needs a decision: the exact question as the asker wrote it (max 4 lines),
plus the link. Mark an item ARCHITECT-CHECK if it names an invariant, gate, tolerance,
Golden/frozen difference, or a "High" finding.
## Unclear
anything you could not determine, and why.
Reply with only the path of the digest.
```

## What the Architect keeps for itself
Rulings, contract reviews (the diff against quoted invariants), acceptance and every
ARCHITECT-CHECK item. The digest decides where to look, never what is true: before a ruling,
verify the quoted line at its source.
