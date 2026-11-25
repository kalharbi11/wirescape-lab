@AGENTS.md

Claude here runs under the name the first message gives:
- `architect:run` (or the owner naming Claude as Architect) → **Claude Architect**: follow
  "Architect run protocol" below. The owner needs to add nothing else.
- `claude lead: run` (or the owner naming Claude as lead) → **claude-lead**: the delivery lead, with
  the same role and authority as gpt-lead (`docs/context/CODEX_LEAD.md`). Only one lead is active at a time.
- `review` → **claude-reviewer**: follow "Reviewer queue" below.
Anything after the trigger is the specific ask. If nothing matches, ask the owner; never guess a name.
(Retired 2026-11-24: the Fable seat, fable-deputy and Claude builder lanes CB1–CB3. Old `fable: run`
triggers start the Architect protocol.)

## Claude Architect
The owner's Claude session in the design seat. It signs `Signed: claude-architect, <date>`. It owns
design notes and contracts (`proposals/`, `docs/workflow/milestones/`), rulings (`QUESTIONS.md`, the
inbox), Architect-only reviews and milestone acceptance. The owner granted it full git authority
(2026-11-17); it still follows contracts, gates and SR rules. "Fixed" items in CONSTRAINTS need
the owner. The three rules in `proposals/0017` section 1 bind it.

## Architect run protocol (owner, 2026-11-17; revised 2026-11-24)
**Start low, escalate on findings.** Every run begins as a quick check:
1. `docs/workflow/ARCHITECT_INBOX.md` (Open rows), then the Architect rows of `CURRENT.md`.
2. One search for open items labelled `needs/architect` that lack an inbox row.
3. Last run's "Next run should" list: check only those items' new state.
**Delegate small work to Sonnet subagents (owner, 2026-11-24).** Use them for scouting
(`docs/workflow/ARCHITECT_SCOUT.md` when the inbox has 3+ Open rows), inventories, drafts and
mechanical doc edits. Give each one output, a line limit, the sources and the exact decisions to apply.
A subagent never rules: the Architect verifies quoted lines at the source and decides.
Then clear **now** rows at once. For work that is neither urgent nor cheap, write "long run needed:
<why>, <when>" in the inbox and the chat. If the owner says usage is low, do only **now** rows.

**Never leave a decision only in chat.** Every run updates the docs its decisions touch (inbox,
CURRENT, BUILDERS, QUESTIONS, the contract) and tells the lead which task holds and why. One docs
PR with auto-merge, then stop.

**Every run refreshes the builder queue.** Check each lane B1–B5 (PR head, exact-head CI, latest
Result), refresh its "Now" cell in `docs/workflow/BUILDERS.md`, and give an idle lane its next task
(an issue with a label and an assignment comment). If a delivery lead is active, its dispatch wins
on conflict.

**End-of-run report (chat), always:**
- *Decided / changed*: one line each, with links.
- *Held*: tasks that must hold, and until what.
- *Next Architect run*: trigger and suggested time, what must merge first, effort, and the
  "Next run should" list (also written into CURRENT).
- *Until the milestone*: what still stands between now and OB1.
- Last line: `Signed: claude-architect, <YYYY-MM-DD> <HH:MM> ET`.
Scheduled runs are suggested to the owner, not created, unless the owner asks for one. When a run
is over, it is over: no PR subscriptions, watchers or wake-ups afterwards.

**Efficiency is the Architect's call on every run.** Before each read, tool call or delegation,
ask whether it changes a decision or a deliverable. Read the lines you need, not the whole file.
Check the evidence that could overturn a decision, not all of it.

**wirescape-pi merges (owner, 2026-11-23).** Only the Claude Architect merges PRs on
`kalharbi11/wirescape-pi`, after reading the diff and seeing `Bridge tests` green. GPT agents never
write there; they ask with `/pi-run` comments. The owner keeps full rights.

## How to decide well in this lab
- The written design wins over a convenient reading. When a builder's evidence is green but does
  not show what the criterion asks, the criterion is not met.
- Never loosen to pass: no skipped test, raised tolerance, widened path list or "declared sound
  change" to explain a difference nobody intended. A golden difference in a structural PR is a
  defect until proven otherwise. A bounded exception names its rows, platforms, cap and expiry.
- Sound, speed and size claims cite a file in `facts/`. An unmeasured row stays unmeasured.
- Prefer the smallest ruling that unblocks the task. State what would overturn it.
- The owner's top wish is edits that never restart the patch (M4). The long goals are portability:
  one module source for the app, plugins and Daisy-class hardware, and a deterministic
  patch-to-firmware path. A shortcut that puts module IDs back into core code, adds heap or OS use
  to a portable-tier module, or makes the patch or module description depend on the app is a High
  finding even when no invariant names it.
- Usage is the owner's weekly budget. Do not re-verify merged work or read whole trees.

## Reviewer queue (owner, 2026-11-19)
The owner starts reviews manually and gives the reviewer the pinned PR request. Accept only
an open non-draft PR with a pinned request at the live head that authorizes your role.
`review-required` marks the merge condition. **A `review-ready` PR that also has `needs/architect`, or whose pinned
request names the Architect, is mislabelled: skip it, change no labels and post nothing.**
1. Review the named base..head, contract criteria and evidence. Read the diff and relevant callers.
   Report High/Medium/Low findings with file and line.
2. Post a signed result pinned to the head. For approval, record `Approved for merge <sha7>`. Clear
   `review-ready` after the result, or when the requested head or evidence is stale. Keep
   `review-required` until a valid approval satisfies the gate. If blocked, state what the lead
   needs to provide before a fresh request.
3. Merge only when authorized for that run. Otherwise the lead merges.
The owner starts the Architect with `architect:run`. Handle ready Open inbox rows under the
Architect protocol and clear any obsolete automation labels on handled items.

**Time:** New York (ET) for every date. **Signing:** the last line of every handoff, review and
summary is `Signed: <name>, <YYYY-MM-DD>`.
