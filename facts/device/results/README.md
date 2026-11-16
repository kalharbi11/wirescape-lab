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
| `pi5` | [`2026-11-15-ab7ce36-full-256-pulse`](pi5/2026-11-15-ab7ce36-full-256-pulse/) | ab7ce36 | p1-full-256 completed via explicit ALSA pulse route | yes, monitor capture |
| `pi5` | [`2026-11-15-ab7ce36-full-128-pulse`](pi5/2026-11-15-ab7ce36-full-128-pulse/) | ab7ce36 | p2-full-128 completed via explicit ALSA pulse route | yes, monitor capture |
| `pi5` | [`2026-11-15-ab7ce36-scene-128-pulse`](pi5/2026-11-15-ab7ce36-scene-128-pulse/) | ab7ce36 | p3-scene-128 completed via explicit ALSA pulse route | yes, monitor capture |
| `pi5` | [`2026-11-15-ab7ce36-chaos-128-pulse`](pi5/2026-11-15-ab7ce36-chaos-128-pulse/) | ab7ce36 | p3-chaos-128 completed via explicit ALSA pulse route | yes, monitor capture |
| `pi5` | [`2026-11-15-ab7ce36-basics-64-pulse`](pi5/2026-11-15-ab7ce36-basics-64-pulse/) | ab7ce36 | p4-basics-64 completed via explicit ALSA pulse route | yes, monitor capture |

Explicit-route Pi rerun report: [2026-11-15](2026-11-15-pi-pulse-reruns.md). Original failures and Windows results: [PR #73](https://github.com/kalharbi11/wirescape-lab/pull/73).
