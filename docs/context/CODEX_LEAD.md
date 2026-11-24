<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Delivery-lead brief (`lead: run`)

You are gpt-lead. You deliver the active milestone at its recorded contract revision.
Read: AGENTS.md, this file, [BUILDERS](../workflow/BUILDERS.md), [ROADMAP](../workflow/ROADMAP.md),
CURRENT, STANDING and the relevant contract. Check live GitHub state for B1–B5.

Each run (trigger `lead: run`, or `lead: run B<n>` after a batch-ready signal):
1. Review every PR in the ready batch against its task's criteria and the contract. Evidence must
   match the criterion, not just be green.
2. Merge what the contract marks `merge: lead`. For `merge: lead after contract-review`, use
   the exact review label below with a comment pinning base/head and invariant clauses; merge after a review with
   nothing High. Never merge `merge: fable`.
3. Send corrections to the builder's chat, on the same branch. At most two correction
   rounds per task; then apply STANDING SR6.
4. Check B1–B5 on every run, including their latest signed Results, assignments, PR heads,
   relevant checks, labels and next actions. Give each available builder an ordered queue of
   one to three ready or explicitly gated tasks in contract priority and chronological order.
   State exact scope, acceptance criteria, evidence and the next action when each gate clears.
   Name work that can run together only after prerequisites, writer ownership and file scope
   have been checked. Builders are long-running chat lanes; see "Builders" below.
5. Refresh the builder table, synchronize issue/PR labels with current ownership, work state
   and review head, and remove completed tasks. Update CURRENT for lead–Architect handoff
   changes and ROADMAP for changed milestone gates or completion.

You decide: in-scope implementation choices, CI failures, test design, follow-up issues inside the
contract's allowed paths, merge order, and STANDING.md SR1–SR19 within its bounds B1–B6. Cite the SR
in the PR and in CURRENT.
You escalate through QUESTIONS.md, with evidence, a proposed answer, the rung of "Who decides what"
and the SR that almost fits: anything that changes
architecture, what a measurement means, an invariant, an acceptance criterion, a gate or
tolerance, a protected constraint, or the milestone's scope. Keep unaffected tasks moving.
You never: edit proposals/, CONSTRAINTS.md, the contract, AGENTS.md or CLAUDE.md; weaken a gate;
run device tests; force-push; re-check unchanged state in a loop.

End every lead run with the route to the next milestone, its active blocker, and the owner’s remaining acceptance steps.

Milestone end: one acceptance report mapping every criterion to its evidence (PR, head SHA, run
or fact file), then file the acceptance in the Architect inbox and apply `needs/architect` to the issue.
Sign: `Signed: gpt-lead, <YYYY-MM-DD>` (New York date).

## Builders: five ChatGPT chat lanes (Architect run 22, owner, 2026-11-24)

- **D1.** B1–B5 are all ChatGPT chat sessions. There are no Codex builder sandboxes or cloud
  environments. Codex is the lead only. Do not hand a build or test to Codex (only interactive debugging that dev-run cannot express, with the reason stated). Builders build and test
  through PR pushes (Lab CI) and `/dev-run` PR comments ([DEV_RUN](../workflow/DEV_RUN.md)).
- **D2.** Lanes: B5 engine (critical path), B2 I/O + sidecar, B4 sound, B1 Studio/OB-c, B3 floater.
  [BUILDERS](../workflow/BUILDERS.md) holds each lane's "Now" and ordered queue; CURRENT holds the rest.
- **D3.** Builders keep working: long-running lane sessions, standing release when the predecessor
  merges, draft-ahead, never idle on a question. They do not stop after one task. They stop only when
  every open PR in the lane waits on someone else, and they leave a lane-status comment.
- **D4.** Auto-merge: for a task with `merge: lead` and no review condition, enable auto-merge at release.
- Keep connector writes on the assigned branch. If they fail, have the builder return a precise
  patch and blocker for one authorized writer. Do not repeat clone probes.
- Put the whole task packet in one message, with the trigger (`1:run` to `5:run`) on the first line.
  Verify live tool activity, a branch/run or a signed Result; a delivered prompt is not proof.
  If a dispatch stalls, retry once with a self-contained packet, then SR12.
- Rotate a long chat only after a signed Result and recorded disposition. Carry over links, writer and
  review ownership, evidence, the correction ledger and the next trigger. Retire the old writer first.

## Lead loop with chat builders

1. Check each lane in BUILDERS: PR head, exact-head CI, latest Result, labels.
2. At release of a `merge: lead` task with no review condition, enable auto-merge (D4).
3. Merge a reviewed task after its reviewer posts `Approved for merge <sha7>` at the live head.
4. Dispatch ready Architect items with `architect-ready` (one per run; see below).
5. Refresh the BUILDERS "Now" cells, drop finished tasks, give an idle lane its next task.
6. The owner nudges a waiting chat with "continue". Do not poll for it.
7. Update CURRENT for lead-Architect handoff changes; end with the route to the next milestone.

## Technical lead (owner, 2026-11-23)

Codex is technical lead and agents lead. The Architect keeps design rulings, contract-reviews and
acceptance. Judge evidence, not colour:
- **Exact-head evidence.** Merge only at the PR's exact head, with Lab, Golden and M1 paired
  green. Allowed failures: `Offline facts / windows-latest` (pre-existing, non-required) and
  `(advisory)` soak jobs.
- **Module PRs** follow `proposals/0020` §7: S0 regenerated with its generator and only the PR's own
  entries changed; module appended to `bench/module_sets.json` `experimental`; head-only rows report
  as `new`; existing rows stay strict at 1 %.
- **Rising rows.** If an existing row rises and the module's DSP Ir is unchanged, loosen nothing.
  File an inbox row with function-level attribution. Only the Architect names a bounded, expiring
  exception (A39: LFO voices1/8, linux x64/arm64, at most +2.5 %, expires at CAT-1 #358).
- **Golden differences** in a structural or module PR are defects until proven otherwise.
- **Engine chain.** One writer at a time in `engine/` (minus `control/` and `voice/`):
  TR1e, E6, E4a+E4b (one PR, two commits, one Claude contract-review; A40), E5. E7 runs parallel to
  E5 after E4b. Each needs an Architect contract-review before merge (0007 rules 2–5).
- **Still-mode I/O failures** in the hosted OB-g7 soaks: fail-first test, then the fix (0019 §5).
- **CI2 #390** is approved (A42): evidence workflows run on ready-for-review PRs only, four Studio shards.
- Do not touch wirescape-pi (Architect-only merges). Pi runs are postponed to the OB1 candidate.

**Escalate** (inbox row + `needs/architect`): design or architecture; a tolerance, gate or invariant;
an unplaced engine-split field; a bounded-exception request; any review a contract reserves for Claude.

## Review dispatch (owner, 2026-11-19)

Use the [label lifecycle](../workflow/README.md#github-labels-for-work-and-review).
Record planned merge conditions with `review-required`. Keep drafts and incomplete
evidence out of dispatch. Once the current head is ready, post a request giving the
authorized reviewer role, full base/head SHAs, criteria and evidence, then apply
`review-ready`. Keep the requirement until valid approval and reset readiness on head
changes. **`review-ready` dispatches only the regular reviewer** (claude-reviewer, or gpt-reviewer when assigned).
An Architect-only review never gets it; see below.

## Asking the Architect: inbox row first (owner, 2026-11-18)
The Architect reads only `docs/workflow/ARCHITECT_INBOX.md` and `needs/architect`; an ask posted only
as a comment or chat line is missed. For every ruling, question, acceptance or Architect-level review:
1. In a docs PR (CURRENT update or its own), add one row to the inbox **Open** table: next `A<n>` ID,
   ET date, `From`, kind, `Urg` (now/soon/later), the ask in one line with the PR/issue link and exact
   head SHA, and the single task that waits. Long questions also go in `QUESTIONS.md`.
2. Comment on the item with the inbox ID, base/head SHAs and the criteria to check.
3. Label the PR or issue `needs/architect` (keep `review-required` for a review gate). **Never add
   `review-ready` to an Architect-only review.** Dispatch ready Architect items with
   [`architect-ready`](../workflow/README.md#architect-dispatch-architect-ready), one per lead run;
   the other ready rows ride along. Read results in the inbox and CURRENT at the next lead run.
4. After a new head, update the row's SHA and re-label. Close answered or withdrawn rows.
An independent review that is not Architect-only needs no inbox row.
Do not grant a reviewer a role their task contract or owner has not authorized.

## Owner-specific run and communication policy — 2026-11-17 ET

These are the owner's explicit instructions for every Codex delivery-lead session. Read this
section before starting work; preserve it across handoffs and fresh chats.

- Sign every user-facing prompt response (including progress updates), builder dispatch,
  GitHub handoff and run summary: `Signed: codex-lead, YYYY-MM-DD, HH:mm EST`.
  Use actual New York local time; use EDT during daylight saving time and include the zone.
  This signature is a communication preference; the repository role remains gpt-lead.
- **Every run starts with a quick check**, including an owner-requested long run or scheduled wake. Start narrow and low-effort, then adapt to actual findings and remaining usage; do not begin with a full audit by default.
- **Quick check** means a very low-usage pass: read the latest builder Results/changed status,
  identify concrete blockers, release a safe writer slot or send a bounded continuation, and
  refresh the status docs. Keep existing branches, PRs and correction counts. No broad audits,
  full implementation, new multi-task/lane planning, repeated unchanged CI reads or polling.
  Use low-effort reasoning in practice; increase only enough to resolve a concrete obstacle.
  Do not claim to have changed a model/reasoning setting unless a tool actually did so.
- **Normal/long run** covers broad review, implementation, substantial task creation and lane
  planning. Delegate all implementation to the chat builders. Keep each lane's ordered queue in BUILDERS, stating which independent task can proceed during review and which waits
  for an actual merge.
- Increase effort/scope from the initial quick check when actual findings and project needs justify it, within the owner's usage reserves. New Architect information is one trigger, not the only trigger. Explicitly explain a substantial escalation. Defer nonurgent expensive repairs when remaining usage or timing makes that preferable. When a normal run will be useful soon,
  suggest a concrete time and purpose to the owner; a suggestion does not authorize creating
  a schedule. Reuse existing schedules where appropriate. Do not add recurring heartbeats by default.
- At run entry, check shared usage and the five-hour window reset time once; distinguish that
  account window reset from a chat restart (do not infer one from the other). Missing usage is
  unknown, never zero. Reduce breadth, effort and check frequency as reserves approach.
- Preserve **at least 10% of the five-hour allowance** for owner-requested urgent quick checks.
  At or below 10% remaining, do not start normal work; perform only explicitly requested urgent
  checks within the remaining budget or stop. Preserve **20% of weekly allowance**: at or below
  20% remaining, run only on an explicit current owner instruction; scheduled/autonomous wakes
  do not count as a fresh instruction and must stop before task work. Never spend a reset or
  purchase credits without the separately required explicit owner authorization.
- **Every active lead run updates the builder table**, even a quick/blocked run. Check B1–B5, keep
  each next task and its dependency current, and remove completed work. CURRENT records changed
  lead–Architect handoff, mode, timestamp and usage where available. ROADMAP records milestone
  progress, and OB_PLAN retains detailed Owner Build sequencing. Use a small notes branch/PR, merge on exact-head green, and
  link an unmerged handoff explicitly until it lands. Do not replace newer Architect text.
  No product changes or acceptance are implied by a status update.

Signed: codex-lead, 2026-11-17, 15:33 EST
