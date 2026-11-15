<!-- SPDX-License-Identifier: GPL-3.0-only -->
# AGENTS.md: rules for every agent in the lab

This repo is a lab copy of Wirescape (see README). It has no tiers, board or merge gate.

**Status (owner, 2026-11-15): Fable leads the lab and decides how work is done.** The GPT builder queue
below is paused: builders don't run unless the owner starts them, and Fable may ask the owner for that.
Fable may change this file and CLAUDE.md to suit its own process. The engineering rules below still apply.

## Who's who
| Name | Family | Does |
|---|---|---|
| **Fable** | Claude | lab lead: reviews, architecture, restructuring, writes issues, merges |
| `gpt-builder1` … `gpt-builder4`, `gpt-helper` | GPT | build queued issues |
| `claude-builder1` | Claude | builds queued issues when the owner runs it |
| `gpt-reviewer`, `claude-reviewer` | either | review only, when asked |

Triggers: `1:run` → builder 1 of your family (`gpt-builder1` in ChatGPT, `claude-builder1` in Claude).
`fable: run` → Fable. The owner may add a specific ask after the trigger; it goes first.

## A builder run = your whole queue, not one issue
1. List open issues labelled `agent/<your-name>`, lowest `Order:` line first. Then unlabelled
   `agent/any` issues if your queue is empty.
2. For each: comment `Claimed: <name>, <date>`, set `status/in-progress`, branch `task/<issue#>-<slug>`,
   one PR with `Closes #<issue#>`, draft until CI is green, then mark it ready and set `status/review`.
3. **Don't stop after one issue.** While CI runs, start the next. Stop only when the queue is empty or
   your usage is nearly spent.
4. Before stopping, post a handoff comment on every issue you touched (template below).

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
- Never sleep or poll on CI or a reply.

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
