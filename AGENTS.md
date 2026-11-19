<!-- SPDX-License-Identifier: GPL-3.0-only -->
# AGENTS.md: rules for every agent in the lab

This repo is a lab copy of Wirescape (see README). It has no tiers, board or merge gate.

**Status (owner, 2026-11-15): Fable leads design and milestone acceptance.** The gpt-lead delivers
milestones under a Fable-accepted written contract in `docs/workflow/milestones/`, dispatches builders,
reviews their evidence and merges only tasks delegated by that contract. Builders no longer wait for
routine owner approval. Without an accepted contract, the fallback authority in `proposals/0004-execution-plan.md`
still applies. The engineering constraints below still apply.

## Who's who
| Name | Family | Does |
|---|---|---|
| **Fable** | Claude | design authority: design notes, milestone contracts, queued rulings, milestone acceptance |
| `fable-deputy` | Claude (Opus) | holds Fable's seat for routine work from 2026-11-17: reviews, queued questions, acceptance, contract upkeep; limits in `CLAUDE.md` and `docs/workflow/STANDING.md` |
| `gpt-lead` | GPT | delivery lead: runs a contracted milestone end to end (`docs/context/CODEX_LEAD.md`); trigger `lead: run` |
| `gpt-builder1` … `gpt-builder4` | GPT | build one contracted task each, fix CI and review corrections, leave a PR result |
| `claude-lead` | Claude | delivery lead with the same role and authority as `gpt-lead` (owner, 2026-11-16), used when the owner assigns the lead to a Claude session; follows `docs/context/CODEX_LEAD.md`; trigger `claude lead: run`. One lead is active at a time; the active lead is named in `CURRENT.md` |
| `claude-builder1` … `claude-builder3` | Claude | build one explicitly assigned task each, fix CI and review corrections, leave a PR result |
| `gpt-reviewer` | GPT | independent source, tests, CI and evidence review when owner-assigned; records signed findings and readiness, but never replaces a required Claude contract-review or Fable decision |
| `claude-reviewer` | Claude | independent review when assigned, including contracts that explicitly require a Claude reviewer |

Triggers: `fable: run design <topic>`, `fable: run questions`, `fable: run accept <milestone>`
→ Fable. `lead: run` or `lead: run B<n>` → gpt-lead. `claude lead: run` → claude-lead. `1:run` → the builder identified by the
active chat's family and assigned task. A trigger never grants authority beyond the accepted contract.

**Short triggers and first reads (owner, 2026-11-17).** No other instruction is needed after these.
| Trigger | Who | Read first, in order |
|---|---|---|
| `architect:run` | Claude Architect (Claude session) | `docs/workflow/ARCHITECT_INBOX.md` → Architect rows of `docs/workflow/CURRENT.md` → its "Next run should" list; protocol in `CLAUDE.md` "Architect run protocol" (scout: `docs/workflow/ARCHITECT_SCOUT.md`) |
| `lead:run` (= `lead: run`) | gpt-lead (Codex) | [Lead brief](docs/context/CODEX_LEAD.md) → [builder queue](docs/workflow/BUILDERS.md) → [roadmap](docs/workflow/ROADMAP.md) → [CURRENT](docs/workflow/CURRENT.md) and newly Cleared Architect rows |

**Architect workflow, for every agent (owner, 2026-11-17).** The Architect runs low-effort quick
checks and escalates only on findings. Ask it by adding a row to `ARCHITECT_INBOX.md` plus the
`needs/architect` label; its rulings land in the inbox Cleared table and CURRENT, never only in chat.
Its scheduled check-ins are listed in CURRENT ("Architect schedule"); the lead plans around them by
filing inbox rows before each check-in. The owner granted the Architect full git authority
(2026-11-17); it still follows contracts, gates and SR rules.

## Each builder task has one issue, branch and PR

The lead owns the builder queue. Each lead run checks B1–B4 and the B5 floater and updates next tasks,
blockers and labels. Builders may pursue multiple explicitly released tasks with disjoint
writers and cleared dependencies.
1. Read your row in `docs/workflow/BUILDERS.md`, the assigned task issue, `docs/workflow/CURRENT.md`, the active milestone contract, and
   relevant files named in the task. Do not pick up the next queued task on your own.
2. Work on one branch `task/<issue#>-<slug>` and one PR with `Closes #<issue#>`. Reuse that same
   branch and PR for corrections. Respect allowed paths and single-writer areas.
3. Implement, test, resolve CI failures and review feedback. Do not merge.
4. Finish with a **result comment on the PR**, using the template in `docs/workflow/README.md`;
   set `status/review` or `status/blocked`. Stop when ready or blocked. The lead owns subsequent
   dispatch and merge decisions.

## Rules
- **Review labels (owner, 2026-11-19):** `review-required` records a merge condition only.
  `review-ready` is the dispatch signal. Apply it only after the lead validates a review-ready
  Result, a non-draft PR and relevant evidence at the current head, and posts a request with
  full base/head SHAs, criteria and the authorized reviewer role. Reviewer eligibility still
  comes from the contract or explicit owner authorization. Architect-only reviews also need
  an Open inbox row and `needs/architect`. See the [complete lifecycle](docs/workflow/README.md#github-labels-for-work-and-review).
- **Builder continuation:** when an active task depends on a running CLI build or test,
  keep doing independent work and schedule one same-task resume near expected completion
  if scheduling is available. Continue this pattern until done or genuinely blocked.
  Record the head/run and next action. No recurring polling. See the
  [continuation rules](docs/workflow/README.md#builder-continuation-after-ci).
- **Architect wakes:** delivery lead only. Post the scoped `/architect-run` comment to
  [#265](https://github.com/kalharbi11/wirescape-lab/issues/265), then add `architect-wake` to #265. The Architect reads the newest command
  and clears the label after the run. Check for a pending wake first, then schedule a one-shot lead check 20 minutes after dispatch. Follow the
  [wake rules](docs/workflow/README.md#intentional-architect-wake).
- **Reaching the Architect:** add one row to `docs/workflow/ARCHITECT_INBOX.md` and label the
  PR/issue `needs/architect`. Leads and builders read the Architect's decisions in CURRENT, not chat.
- **Devices off** in tests, CI and agent runs: no audio/MIDI devices, no LAN sockets (localhost is fine).
  Scripts that use real devices refuse to run without `--confirm-audio` / `--confirm-midi`; only the
  owner runs them.
- **Realtime code:** no allocation, locks, I/O, exceptions, logging or JSON in process/event/reset.
- **Facts are neutral.** Files under `facts/` hold numbers, quotes and sources with the lab commit,
  machine and date. No "should", no ranking. Opinions go in `proposals/` (Fable only).
- **Don't change the product tree** (`native/`, `apps/`, `tools/`, `docs/specs/`) unless your issue says so.
- Never commit secrets, machine-specific absolute paths, user names or host names, `node_modules/`,
  `build*/`, or audio files over 1 MB (see `bench/README.md` for where recordings go).
- SPDX header on new files: MIT under `native/sdk/` and `native/voice/`, GPL-3.0-only elsewhere.
- No force-push, no history rewrite, no commits to `main`.
- No model run polls unchanged state. A builder may schedule a one-shot same-task continuation under the rules above. Scripts and GitHub Actions may watch CI and events.

## Handoff template
```
**Status:** done | handoff-ready | blocked   **PR:** #…   **Head:** sha7
**Done:** …
**Next:** ordered steps any agent can follow
**Tests:** command → result
**Gotchas / follow-ups:** …
Signed: <name>, <YYYY-MM-DD>
```
Dates are New York time.

## Commands (devices off)
`python tools/dev.py doctor | build --headless | test` · Studio: `cd apps/studio && npm ci && npm test` ·
Desktop: `cd apps/desktop && npm ci && npm test`. Cloud container without cmake/ninja:
`bash tools/ci/codex_cloud_setup.sh` and use the PATH it prints.
