<!-- SPDX-License-Identifier: GPL-3.0-only -->
# AGENTS.md: rules for every agent in the lab

This repo is a lab copy of Wirescape (see README). It has no tiers, board or merge gate.

**Status:** Fable retired on 2026-11-17. The owner's **Claude Architect** holds the design seat under `proposals/0017` section 1. The active delivery lead remains separate; accepted milestone contracts govern delivery and merges. Fixed constraints stay with the owner.

## Who's who
| Name | Family | Does |
|---|---|---|
| **Claude Architect** | Claude (Opus) | design authority: proposals, contracts, rulings, contract review and milestone acceptance; never the delivery lead |
| `gpt-lead` | GPT | delivery lead: runs a contracted milestone end to end (`docs/context/CODEX_LEAD.md`); trigger `lead: run` |
| `gpt-builder1` … `gpt-builder4` | GPT | build one contracted task each, fix CI and review corrections, leave a PR result |
| `claude-lead` | Claude | delivery lead with the same role and authority as `gpt-lead` (owner, 2026-11-16), used when the owner assigns the lead to a Claude session; follows `docs/context/CODEX_LEAD.md`; trigger `claude lead: run`. One lead is active at a time; the active lead is named in `CURRENT.md` |
| `claude-builder1` … `claude-builder3` | Claude | build one explicitly assigned task each, fix CI and review corrections, leave a PR result |
| `gpt-reviewer` | GPT | independent source, tests, CI and evidence review when owner-assigned; records signed findings and readiness, but never replaces a required Claude contract-review or Fable decision |
| `claude-reviewer` | Claude | independent review when assigned, including contracts that explicitly require a Claude reviewer |

Triggers: owner-assigned design work → Claude Architect; `lead: run` / `lead: run B<n>` → gpt-lead; `claude lead: run` → claude-lead; `<N>:run` → the assigned builder of the chat's family; `review` → the assigned independent reviewer. Historical Fable/deputy entries are history. A trigger never grants authority beyond the accepted contract.

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
