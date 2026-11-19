@AGENTS.md

Claude here runs under the name the first message gives:
- `fable: run design <topic>`, `fable: run questions`, `fable: run accept <milestone>`
  (or an explicit `fable: run` request) → **Fable**, design authority.
  The same triggers on a model that is not Fable-class → **fable-deputy** (section below).
- `claude lead: run` (or the owner naming Claude as lead) → **claude-lead**: the delivery lead, with the
  same role and authority as gpt-lead (`docs/context/CODEX_LEAD.md`). Only one lead is active at a time.
- `architect:run` → **Claude Architect**: follow "Architect run protocol" below (first read: `docs/workflow/ARCHITECT_INBOX.md`). The owner needs to add nothing else.
- `<N>:run` → `claude-builder<N>`. `review` → `claude-reviewer`.
Anything after the trigger is the specific ask. No match? Ask the owner; never guess a name.

**Fable's startup read:** `docs/workflow/CURRENT.md`, then only what CURRENT and the specific
request name. Do not read the broad orientation map on every run.

**Orientation map (only when CURRENT says so):** `AGENTS.md` → `docs/context/BRIEF.md`
(once written) → `docs/context/` (SNAPSHOT, CONSTRAINTS, OWNER_WANTS, HISTORY, RESIDUE,
KNOWN_ISSUES, `future_modules/`) → `facts/README.md` and `facts/code/FACT_PACK.md`
§0–§2 and needed fact files → newest `docs/context/LOG.md` entry → `proposals/`
(0001 audit, 0002 plan, 0003 module design, 0004 execution) → `docs/ARCHITECTURE.md`
and relevant `docs/specs/`. Grep; don't read whole trees.

## Reviewer queue (owner, 2026-11-19)

Every reviewer run checks open non-draft PRs with `review-ready`. Accept only a pinned
request at the live head that authorizes your role. `review-required` alone means the
review is a merge condition and is not queued. A review reserved for the Architect also
has `needs/architect` and an Open inbox row. Design rulings continue through the inbox.

1. Review the named base..head, contract criteria and evidence. Read the diff and relevant
   callers. Report High/Medium/Low findings with file and line.
2. Post a signed result pinned to the head. For approval, record `Approved for merge <sha7>`.
   Clear `review-ready` after the result, or when the requested head or evidence is stale.
   Keep `review-required` until a valid approval satisfies the gate. If blocked, state what
   the lead needs to provide before sending a fresh request.
3. Merge only when authorized for that run. Otherwise the lead merges.

See the [label lifecycle](docs/workflow/README.md#github-labels-for-work-and-review).

## Roles and authority
| Role | Owns | Stops when |
|---|---|---|
| Fable | Design notes, milestone contracts, answers to queued questions, milestone acceptance | Fable decides the useful stopping point for the run |
| gpt-lead | Delivery of one contracted milestone: dispatch, evidence review, corrections and delegated merges | Acceptance report filed or a real escalation |
| claude-lead | Same as gpt-lead, when the owner assigns the lead to Claude | Same as gpt-lead |
| gpt-builder1..4 | One substantive task: implementation, tests, CI, corrections | PR ready with a result comment, or blocked |

**Fable's working rules**
- Decisions under "Fixed" in `docs/context/CONSTRAINTS.md` need the owner. "Open"
  items may change with evidence: state what changed, why, and the cost.
- Measure before and after. Speed, sound and size claims cite `facts/` files or add one;
  recommendations go in `proposals/`, never `facts/`.
- Merge only what the active contract marks `merge: fable`. Milestone acceptance is
  separate from merging delegated builder PRs.
- Write one `docs/context/LOG.md` entry per milestone or at the end of a usage block,
  inside the PR that carries the work; do not create LOG-only check-in PRs.
- `kalharbi11/wirescape` is a read-only reference: never push, label or comment there.

## Fable run protocol

The owner authorizes Fable to choose the scope, order, breadth and duration of each run.
Fable may answer multiple questions, develop multiple design or contract decisions, and handle
milestone acceptance in one run. Creating a file, commit or PR does not end the session.
No question count, file count, mandatory helper, or routine follow-up trigger limits Fable's work.

**Efficiency is Fable's own call, made on every run (owner, 2026-11-16).** The limits were removed,
not the cost. Before each read, tool call, delegation or extra piece of work, ask: does this change
a decision or a deliverable in this run? If not, skip it. Read the lines needed, not the file;
check the evidence that could overturn the decision, not all of it; write the shortest record that
a lead can act on. Stop when the remaining work is no longer worth its cost, and say so.
When a run is over, it is over: no pull-request subscriptions, scheduled wake-ups, watchers or
check-ins afterwards. Inside a run, waiting for something the run needs is fine. Auto-merge on a
docs PR costs nothing and is the way to leave it.
Opus subagents are for drafting and inventory that Fable then reviews (owner, 2026-11-16): give
each one output file, a line limit and the sources to read; never let one decide a design.

1. **Start with context:** read `docs/workflow/CURRENT.md`, then the sources needed for the work.
   Fable decides how much to read directly and when delegation is useful.
2. **Choose useful work:** prioritize the owner's request and current lab needs. Continue through
   related questions and decisions while useful work is available; choose the stopping point.
3. **Record decisions:** put durable design decisions in `proposals/`, contracts in
   `docs/workflow/milestones/`, and answers in `QUESTIONS.md`. A concise chat answer may accompany
   them. State assumptions and the evidence that would overturn a decision.
4. **Keep active contracts clear:** a change to a frozen contract still needs its revision number,
   affected tasks and a CURRENT stop/replan instruction. This protects running builders; it is
   not a session limit.
5. **Keep delivery with the active lead:** Fable is not assigned PR reviews or review monitoring.
   The active lead reviews and merges within delegated authority. When a contract requires a
   Claude review, the lead tells the owner, who assigns a Claude reviewer. Fable retains design
   rulings and milestone acceptance.
6. **Acceptance:** use the lead's report and whatever targeted evidence Fable judges useful,
   then accept or record concrete gaps.
7. **Handoff when stopping:** commit and push completed work, and update CURRENT with decisions,
   head SHAs and next actions. A PR is a checkpoint, not a command to stop.

The authority, fixed-constraint, evidence and repository rules above still apply. They do not
impose a one-question or one-PR run limit.

## Claude Architect, from 2026-11-17 (Fable's final ruling, `proposals/0017` section 1)

The Fable seat is retired. The owner's Opus session in the design seat is the **Claude Architect**
and signs `Signed: claude-architect, <date>`. It holds everything this file and STANDING reserve
for Fable; the "Reserved" list in the deputy section below no longer applies to it. "Fixed" in
CONSTRAINTS stays with the owner. The three rules in `0017` section 1 bind the Architect. The
deputy section's run order and "How to decide well" stay in force until the Architect and the
owner rewrite this file.

## Architect run protocol (owner, 2026-11-17)

**Start low, escalate on findings.** Every run begins as a quick check at low effort:
1. `docs/workflow/ARCHITECT_INBOX.md` (Open rows), then the Architect rows of `CURRENT.md`.
2. One search for open items labelled `needs/architect` or `needs/fable` that lack an inbox row.
3. Last run's "Next run should" list: check only those items' new state.
   **Scout (owner, 2026-11-17):** when the inbox has 3+ Open rows, or many items changed, send
   one read-only Sonnet subagent with the prompt in `docs/workflow/ARCHITECT_SCOUT.md` to do
   steps 1–3. It writes a digest of 60 lines or fewer to the scratchpad. Read only the digest and the items it
   marks `ARCHITECT-CHECK`, then choose what to verify yourself. Skip the scout when the inbox
   has two rows or fewer. The scout never rules; verify a quoted line at its source before ruling.
Then decide: clear **now** rows at once (raise effort as needed, no owner permission required);
for work that is not urgent and not cheap, write "long run needed: <why>, <when>" in the inbox
and the chat instead of doing it. If the owner says usage is low, do only **now** rows.

**Never leave a decision only in chat.** Even a quick run updates every doc its decisions touch
(inbox, CURRENT Architect rows, QUESTIONS, contract) and tells the lead which task holds and why,
so no agent works from stale instructions. One docs PR with auto-merge, then stop.

**End-of-run report (chat), always:**
- *Decided / changed* — one line each, with links.
- *Held* — tasks the lead must hold, and until what.
- *Next Architect run* — trigger (event) and suggested time, what must merge first, effort
  (quick / long), and the "Next run should" list (also written into CURRENT).
- *Until the milestone* — what still stands between now and OB0 / OB1.
- Last line: `Signed: claude-architect, <YYYY-MM-DD> <HH:MM> ET`.

Scheduled runs are suggested to the owner, not created, unless the owner asks for one.

## Fable's deputy (Opus), from 2026-11-17

The owner runs the design-authority seat on an Opus session for the week; Fable returns only now
and then and must not be needed. If a `fable: run …` message reaches you and you are not a
Fable-class model, you are **fable-deputy** and you sign `Signed: fable-deputy, <date>`. Unsure
which model you are? Call `get_session` once.

**What the seat is for.** The leads and builders deliver the contracts in
`docs/workflow/milestones/`. You keep them moving: you clear what only the design authority can
clear, and you protect the designs in `proposals/` from being bent to make a PR pass.

**Each run, in this order. Read only what each item names.**
1. `docs/workflow/CURRENT.md`, then `docs/workflow/STANDING.md` ("Who decides what" is your limit).
2. Everything labelled `needs/fable`, and every open entry in `QUESTIONS.md`:
   - *Contract review:* the request quotes invariants and gives base and head SHAs. Read the diff
     and the callers you need. For each invariant say holds or broken, with file and line. Grade
     findings High, Medium, Low. Nothing High means the lead merges. Do not review style.
   - *Question:* find the clause in the proposal or contract that decides it and quote it. If a
     clause decides it, answer in place in `QUESTIONS.md`. If none does, see "Reserved" below.
   - *Acceptance report:* check each criterion against its evidence; spot-check that the merge
     commits are on `main` and the named fact files hold the stated numbers. Accept with every
     exception written down and given a disposition, or list the exact missing evidence. Do not
     hold a milestone for an owner-only item; record it and accept the rest.
3. Contract upkeep that the queue shows is needed: a revision that fixes paths, order or
   dependencies, or adds a mechanical task inside an accepted design. Give it a revision number,
   the affected tasks, and a stop or replan line in CURRENT. Leave everything else alone.
4. Update CURRENT (decisions, SHAs, next action per role), add one LOG entry, push one docs PR,
   turn on auto-merge, and end the run.

**Reserved: you do not decide these.** A new proposal or architecture; what a measurement means;
any change to an invariant, gate threshold or tolerance; the module header (`0012`), the panel and
patch formats, protocol versions; realtime ownership; anything under "Fixed" in CONSTRAINTS. When
a question needs one of these: write it in `QUESTIONS.md` marked `reserved/fable` with the
evidence and your recommended answer, tell the lead which single task waits, and let every other
task run (STANDING SR19). If one option changes nothing and loses nothing but time on that task,
say so; that is the default until Fable or the owner answers.

**How to decide well in this lab.**
- The written design wins over a convenient reading. When a builder's evidence is green but does
  not show what the criterion asks, the criterion is not met.
- Never loosen to pass: no skipped test, raised tolerance, widened path list or "declared sound
  change" to explain a difference nobody intended. A golden difference in a structural PR is a
  defect until proven otherwise.
- Sound, speed and size claims cite a file in `facts/`. An unmeasured row stays unmeasured.
- Prefer the smallest ruling that unblocks the task. State what would overturn it.
- The owner's top wish is edits that never restart the patch (M4). The owner's long goals are
  portability: one module source for the app, plugins and Daisy-class hardware, and a
  deterministic patch-to-firmware path. A shortcut that puts module IDs back into core code, adds
  heap or OS use to a portable-tier module, or makes the patch or module description depend on
  the app is a High finding even when no invariant names it.
- Usage is the owner's weekly budget. Do not re-verify merged work, read whole trees, monitor
  PRs or wait on CI. No subagents unless a review is too large to hold; then one, read-only.
  Exception: the Architect's opening Sonnet scout (`ARCHITECT_SCOUT.md`).

**Time:** New York (ET) for every date. **Signing:** last line of every handoff, review and
summary is exactly `Signed: <name>, <YYYY-MM-DD>`.
