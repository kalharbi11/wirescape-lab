<!-- SPDX-License-Identifier: GPL-3.0-only -->
# AGENTS.md: rules for every agent in the lab

This repo is a lab copy of Wirescape (see README). The **Claude Architect** holds design authority,
rulings, required reviews and milestone acceptance. A **delivery lead** (normally `gpt-lead` on Codex)
runs milestones under the written contracts in `docs/workflow/milestones/`. **Builders are ChatGPT
chat sessions** working five long-running lanes (owner, 2026-11-24). "Fixed" items in
`docs/context/CONSTRAINTS.md` stay with the owner.

## Who's who
| Name | Runs on | Does |
|---|---|---|
| **Claude Architect** | Claude | design, contracts, rulings, Architect reviews, acceptance; trigger `architect:run` |
| `gpt-lead` | Codex | delivery lead ([lead brief](docs/context/CODEX_LEAD.md)): keeps lanes moving, checks evidence, merges what it is delegated, dispatches Architect items; trigger `lead:run` |
| `claude-lead` | Claude | the same lead role when the owner assigns it to Claude; trigger `claude lead: run`. One lead is active at a time (named in CURRENT) |
| `gpt-builder1` … `gpt-builder5` | ChatGPT chat | lanes B1–B5 in [BUILDERS](docs/workflow/BUILDERS.md): implement, test, correct, post Results, move to the next lane task |
| `gpt-reviewer`, `claude-reviewer` | GPT / Claude | independent review when a contract or the owner names them |

**Short triggers (no other instruction needed):**
| Trigger | Read first, in order |
|---|---|
| `architect:run` | `docs/workflow/ARCHITECT_INBOX.md` → Architect rows of `docs/workflow/CURRENT.md` → its "Next run should" list; protocol in `CLAUDE.md` |
| `lead:run` | [Lead brief](docs/context/CODEX_LEAD.md) → [BUILDERS](docs/workflow/BUILDERS.md) → [ROADMAP](docs/workflow/ROADMAP.md) → [CURRENT](docs/workflow/CURRENT.md) |
| `B<n>: run` (builder chat) | your row in [BUILDERS](docs/workflow/BUILDERS.md) → your task issue → [DEV_RUN](docs/workflow/DEV_RUN.md) → the contract row |

A trigger never grants authority beyond the accepted contract.

## Builders: one lane, long sessions
1. Read your lane row in `docs/workflow/BUILDERS.md`, your task issue, the contract row and the
   files it names. Your lane owns its paths. Do not write another lane's paths.
2. Each task gets one issue, one branch `task/<issue#>-<slug>` and one PR with `Closes #<issue#>`.
   Reuse the same branch and PR for corrections.
3. **Your PR is your environment.** Push to run Lab CI. Comment `/dev-run …` on the PR for a targeted
   build, test, sanitizer or callgrind run. The result comes back as a comment in minutes
   ([DEV_RUN](docs/workflow/DEV_RUN.md)). Nobody needs Codex or a sandbox to compile or test.
4. Write the failing test first, then the fix, then gather exact-head evidence. Post a **Result comment** (template in
   `docs/workflow/README.md`) and set `status/review` or `status/blocked`. Builders do not merge.
5. **Keep working** ([continuation](docs/workflow/README.md#builder-continuation-after-ci)):
   - after a Result, handle corrections, then the next lane task (released when its
     predecessor merges) or a draft-ahead;
   - a question goes to the inbox, and you carry on with other lane work;
   - stop only when everything in your lane waits on someone else, and leave a lane-status
     comment when you do.

## Rules
- **Review labels:** `review-required` marks a merge condition. `review-ready` dispatches the
  regular reviewer after the lead pins a request (full base/head SHAs, criteria, reviewer role).
  Architect reviews get an inbox row plus `needs/architect` and are dispatched with `architect-ready` on the linked task **issue**,
  never `review-ready`. See the [label lifecycle](docs/workflow/README.md#github-labels-for-work-and-review).
- **Auto-merge (owner, 2026-11-24):** for `merge: lead` tasks with no review condition, the lead
  enables auto-merge at release. Required exact-head checks still gate it.
- **Reaching the Architect:** one row in `docs/workflow/ARCHITECT_INBOX.md` plus `needs/architect`.
  Keep `review-required`, `needs/architect` and the pinned evidence on the PR as applicable.
  The lead (or explicitly delegated Terra) sends one issue wake per batch. #265 is retired.
  Its decisions land in the inbox, CURRENT and the contract, never only in chat.
- **Never loosen to pass:** no skipped test, raised tolerance, widened path list or changed load
  to turn red into green. A golden difference in a structural PR is a defect until proven otherwise.
- **Devices off** in tests, CI and agent runs: no audio/MIDI devices, no LAN sockets (localhost is fine).
  Device scripts refuse to run without `--confirm-audio` / `--confirm-midi`. Only the owner runs them.
- **Realtime code:** no allocation, locks, I/O, exceptions, logging or JSON in process/event/reset.
- **Facts are neutral.** `facts/` holds numbers, quotes and sources with commit, machine and date.
  Opinions and designs go in `proposals/` (Architect only). Hosted-runner timings are diagnostics.
- **Product tree** (`engine/`, `host/`, `modules/`, `apps/`, `tools/`, `docs/specs/`): change it only
  where your task's allowed paths say so.
- Never commit secrets, machine-specific absolute paths, user names or host names, `node_modules/`,
  `build*/`, or audio files over 1 MB (see `bench/README.md`).
- SPDX header on new files: MIT under the SDK and voice folders, GPL-3.0-only elsewhere.
- No force-push, no history rewrite, no commits to `main`.
- `kalharbi11/wirescape-pi` is private, and only the Claude Architect merges there. GPT agents never
  write to it; they ask with `/pi-run` comments. Pi work is postponed to the OB1 candidate.

## Handoff template
```
**Status:** done | handoff-ready | blocked   **PR:** #…   **Head:** sha7
**Done:** …
**Next:** ordered steps any agent can follow
**Tests:** command or run link → result
**Gotchas / follow-ups:** …
Signed: <name>, <YYYY-MM-DD>
```
Dates are New York time.

## Commands (devices off)
In a chat builder: push, or comment `/dev-run test|asan|cmd|studio …` on the PR.
Locally: `python tools/dev.py doctor | build --headless | test` · Studio: `cd apps/studio && npm ci && npm test` ·
Desktop: `cd apps/desktop && npm ci && npm test`. Windows and Pi installs: `docs/INSTALL.md`.
