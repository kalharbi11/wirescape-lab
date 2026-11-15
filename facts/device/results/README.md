<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device results

Layout: `<machine>/<YYYY-MM-DD>-<sha7>-<scope>/` (date ET, lab commit of the build that ran).
Only files under 1 MB are committed; full run ZIPs (recordings, `events.ndjson`, logs) are attached
to the draft release `bench-<date>`.

| Machine | Run | Commit | Scope | Real audio |
|---|---|---|---|---|
| `pi5` | [`2026-11-14-cd9a6a5-device-off`](pi5/2026-11-14-cd9a6a5-device-off/) | cd9a6a5 | build, tests, app smoke, dry run, null-sink sample | no |
| `pi5` | [`2026-11-14-b1d92be-quick`](pi5/2026-11-14-b1d92be-quick/) | b1d92be (cd9a6a5 + local MIDI patch) | 15-minute quick scenario, USB audio | yes |
| `windows-laptop` | [`2026-11-14-cd9a6a5-device-off`](windows-laptop/2026-11-14-cd9a6a5-device-off/) | cd9a6a5 | build, setup checks, dry run, null-sink and synthetic samples | no |
| `windows-laptop` | [`2026-11-15-842d682-validation`](windows-laptop/2026-11-15-842d682-validation/) | 842d682 | build, app smoke, dry run, speaker check; 15-minute quick run not performed | speaker check only |

Cross-machine summary of the cd9a6a5 device-off runs: [`device-off-2026-11-14-cd9a6a5.md`](device-off-2026-11-14-cd9a6a5.md).
