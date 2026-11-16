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
| `gpt-lead` | GPT | delivery lead: runs a contracted milestone end to end (`docs/context/CODEX_LEAD.md`); trigger `lead: run` |
| `gpt-builder1` … `gpt-builder4` | GPT | build one contracted task each, fix CI and review corrections, leave a PR result |
| `claude-lead` | Claude | delivery lead with the same role and authority as `gpt-lead` (owner, 2026-11-16), used when the owner assigns the lead to a Claude session; follows `docs/context/CODEX_LEAD.md`; trigger `claude lead: run`. One lead is active at a time; the active lead is named in `CURRENT.md` |
| `claude-builder1` … `claude-builder3` | Claude | build one explicitly assigned task each, fix CI and review corrections, leave a PR result |
| `gpt-reviewer`, `claude-reviewer` | either | review only, when assigned |

Triggers: `fable: run design <topic>`, `fable: run questions`, `fable: run accept <milestone>`
→ Fable. `lead: run` or `lead: run B<n>` → gpt-lead. `claude lead: run` → claude-lead. `1:run` → the builder identified by the
active chat's family and assigned task. A trigger never grants authority beyond the accepted contract.

## A builder run = one task and one PR
1. Read the assigned task issue, `docs/workflow/CURRENT.md`, the active milestone contract, and
   relevant files named in the task. Do not pick up the next queued task on your own.
2. Work on one branch `task/<issue#>-<slug>` and one PR with `Closes #<issue#>`. Reuse that same
   branch and PR for corrections. Respect allowed paths and single-writer areas.
3. Implement, test, resolve CI failures and review feedback. Do not merge.
4. Finish with a **result comment on the PR**, using the template in `docs/workflow/README.md`;
   set `status/review` or `status/blocked`. Stop when ready or blocked. The lead owns subsequent
   dispatch and merge decisions.

## Rules
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
- No model run waits on or re-checks unchanged state. Scripts and GitHub Actions may watch CI and events.

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
