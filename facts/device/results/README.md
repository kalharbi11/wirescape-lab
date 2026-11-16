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
| `pi5` | [`2026-11-15-ab7ce36-full-256`](pi5/2026-11-15-ab7ce36-full-256/) | ab7ce36 | P1 partial: event queue full | attempted; owner heard no |
| `pi5` | [`2026-11-15-ab7ce36-guttr`](pi5/2026-11-15-ab7ce36-guttr/) | ab7ce36 | GUTTR 1/16-throat benchmark | no |
| `pi5` | [`2026-11-15-ab7ce36-app-memory`](pi5/2026-11-15-ab7ce36-app-memory/) | ab7ce36 | P6 passed ARM64 app smoke; sampled memory | no |
| `windows-laptop` | [`2026-11-15-156af4b-quick-256`](windows-laptop/2026-11-15-156af4b-quick-256/) | 156af4b | W1 completed; 25 engine dropouts | yes, process-loopback |
| `pi5` | [`2026-11-15-ab7ce36-full-128`](pi5/2026-11-15-ab7ce36-full-128/) | ab7ce36 | p2-full-128: failed, unsupported sample format then queue full | attempted; no sound reported |
| `pi5` | [`2026-11-15-ab7ce36-scene-128`](pi5/2026-11-15-ab7ce36-scene-128/) | ab7ce36 | p3-scene-128: failed, unsupported sample format then queue full | attempted; no sound reported |
| `pi5` | [`2026-11-15-ab7ce36-chaos-128`](pi5/2026-11-15-ab7ce36-chaos-128/) | ab7ce36 | p3-chaos-128: failed, unsupported sample format then queue full | attempted; no sound reported |
| `pi5` | [`2026-11-15-ab7ce36-basics-64`](pi5/2026-11-15-ab7ce36-basics-64/) | ab7ce36 | p4-basics-64: failed, unsupported sample format then queue full | attempted; no sound reported |
| `windows-laptop` | [`2026-11-15-156af4b-quick-128`](windows-laptop/2026-11-15-156af4b-quick-128/) | 156af4b | W2 completed; zero engine dropouts | yes, process-loopback |

Cross-machine summary of the cd9a6a5 device-off runs: [`device-off-2026-11-14-cd9a6a5.md`](device-off-2026-11-14-cd9a6a5.md).

Session report: [2026-11-15](2026-11-15-device-session.md). MIDI naming fix: PR #50.
