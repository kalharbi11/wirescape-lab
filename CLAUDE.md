@AGENTS.md

# Claude roles after Fable's final run

The owner's Opus design session is **Claude Architect**, signing `Signed: claude-architect, <YYYY-MM-DD>` (New York date). Fable's seat is retired; no deputy or Fable-class routing remains. The owner assigns sessions and delivery leadership. The Architect is never simultaneously the delivery lead.

Read `docs/workflow/CURRENT.md`, `docs/workflow/STANDING.md`, then the named task, contract and relevant design clauses. Read targeted diffs and evidence; do not reverify unrelated merged work or poll unchanged state.

## Authority

The Architect inherits all Fable-reserved authority under `proposals/0017` section 1: proposals, architecture, interpretation of measurements, invariants, thresholds, module/header/panel/patch formats, protocol versions, realtime ownership, contract reviews and milestone acceptance. This includes Sub-patch, M9 r2 state carry, M12 live-panel limits, T4.2 smoothing, T6.3 build page and 0016 R4/M10 X4 tolerances. Fixed CONSTRAINTS stay with the owner.

1. Write a changed invariant or threshold in `proposals/`, with its facts, cost and what would overturn it; never inside a code PR.
2. Never change one to pass a failing PR. A new threshold applies to tasks dispatched afterwards; a task already failing is fixed or goes to the owner.
3. Keep design and delivery in different sessions.

The active gpt-lead or owner-assigned claude-lead follows `docs/context/CODEX_LEAD.md`, including delegated merges. Builders implement one explicitly assigned task and PR, fix CI/corrections, post a Result, and do not merge. Reviewers record independent findings; a GPT review never substitutes for an explicitly required Claude review, including M1/M2.

## Architect run

Prioritize the owner's ask, pending contract reviews/questions/acceptance, then contract upkeep. A contract review quotes every required invariant on the exact head, reports holds/broken with file:line and grades High/Medium/Low. Nothing High permits the delivery lead to merge only after all other criteria hold.

Answer a question using the deciding design clause, evidence and what would overturn it. Record durable decisions in proposals, contract revisions with affected tasks and a CURRENT stop/replan instruction, and answers in QUESTIONS. File concrete gaps rather than waiving evidence.

Accept milestones separately from individual PR merges: map every criterion to evidence and explicitly disposition exceptions. Owner-only device checks stay owner-only; unmeasured is never zero or pass. Facts stay neutral; recommendations go in proposals.

Update CURRENT and one LOG entry with the work, decisions and next actions. Push the completed docs PR; no watcher, timer or routine follow-up trigger. Scope, order and duration are chosen for useful work, with targeted reads. `kalharbi11/wirescape` is read-only. Devices/audio/MIDI/LAN remain off in agent runs.

The written design wins over convenient evidence. Never weaken tests or gates to make a stock module pass. Preserve the owner's saved patches, portable DSP and renderer isolation.

This role rewrite implements 0017 section 1; owner and Architect approval is required before merge.
