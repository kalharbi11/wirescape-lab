<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner-local tests (Windows laptop and Pi): guide for a local agent

These checks need the owner's real hardware, which CI cannot supply. They **never block** lab
work. A lane waits on a result only when the Architect names that lane in CURRENT. Since
2026-11-20 no CI runner stays on the laptop (wirescape-pi PR #18), so laptop checks run only
from this page and only when the owner chooses.

## Rules for the local agent (read first)
- **Work only in your eval checkout** (`C:\src\wirescape-eval` on Windows, `~/src/wirescape-eval`
  on the Pi). Do not read other folders, browser data, SSH keys or credential stores, and do not
  print environment variables.
- **Devices off by default.** Steps marked 🔊 open audio or MIDI. Run them only while the owner
  is at the machine and says go: they pass `--confirm-audio` / `--confirm-midi`, or they are UI
  steps the owner performs while you write down what they report.
- **No pushes and no installs** beyond the setup scripts named here. Do not run `sudo` or
  elevated shells, except where the owner runs a Pi step themselves.
- **Use an exact SHA.** Use the SHA given in CURRENT's "Owner-local" row. If none is given, use
  `main`'s head, and record which.
- **Report:** one comment on [#198](https://github.com/kalharbi11/wirescape-lab/issues/198)
  (or text the owner pastes into the Architect chat) using the template at the end. Leave out
  private patch contents, user names and absolute home paths.

## Windows laptop
Setup is `docs/workflow/WINDOWS_EVAL.md` → "Owner steps" (VS x64 Developer PowerShell, Python
3.12, Node 22 x64).

| ID | Kind | Steps | Pass when | Why it is local |
|---|---|---|---|---|
| L1 | 🔊 owner | Finish WINDOWS_EVAL **T2–T7** (MIDI mono and poly, OSC In, combined, save/load). The owner already reported T1 sound and T5 OSC Out good on `c6ae30a`. | Each row's "Pass when" | Real MIDI device, real UI |
| L2 | 🔊 owner | Play `04-combined` for 20 min at WASAPI 48 kHz / 256, then repeat 10 min at buffer 128. | No crackle, stuck note or UI freeze. Note any glitch with the minute it happened. | Real driver timing |
| L3 | device-off, agent | `python tools\dev.py doctor`, then `python tools\dev.py benchmark` at the eval SHA. Copy the `build_reports\…\benchmark-result*.json` path and its top-level numbers into the report. | Command exits 0 | Owner-hardware CPU numbers for OB-f/M7 (a builder turns them into a `facts/` file with machine and SHA) |
| L4 | device-off, agent | Only if L1 or L2 failed: `python tools\dev.py test` and `cd apps\desktop; npm ci; npm test`. | Same result as Windows CI at that SHA | Separates a machine problem from a product defect |
| L5 | 🔊 owner | Only on request in CURRENT: re-run L1 on a new owner build SHA (for example the OB1 candidate). | As L1 | Candidate sign-off |

## Raspberry Pi 5
**CI-style runs** (build, tests and soaks, devices off) go through the sandboxed bridge once its
README "Owner setup" is done. Any agent requests one with a `/pi-run …` comment on a lab PR or
issue (CURRENT "Decided 2026-11-20 17:15 ET"). The local agent does not run them.

The **owner-local** Pi checks are the real screen, audio and MIDI. Use `docs/PI_SETUP.md` and
`docs/PI_APP_SMOKE.md` for setup.

| ID | Kind | Steps | Pass when |
|---|---|---|---|
| P0 | owner, once | wirescape-pi README "Owner setup" steps 1–5, then `sudo bash setup/pi-setup.sh --check` | The check shows user `wsci` with no sudo, the LAN block present and the image present |
| P1 | device-off, agent | At the given SHA: `python3 tools/pi/preflight.py`, then the PI_APP_SMOKE "Exact-head smoke command" | Smoke status passes. This is #198's outstanding OB0 Pi smoke. |
| P2 | 🔊 owner | Launch the app on the Pi screen, load `01-midi-mono` and `04-combined`, and play for 10 min through the Pi's audio output with a USB MIDI keyboard | Sound, no crackle, UI responsive, no stuck notes |
| P3 | 🔊 owner | Only after OB-b merges (Phase C): fresh install with the OB-b script and `docs/INSTALL.md`, then P2 | Install completes with no manual fix |

The Pi agent runs as the owner's normal user, **not** `wsci`. It never touches the runner
folder or the `wsci` home.

## Report template
```
Owner-local — <Windows|Pi> — <SHA7> — <YYYY-MM-DD HH:MM ET>
Machine: <OS/arch>; toolchain: <VS/Node/Python or gcc/cmake>
L/P rows run: <ids>
<id>: pass|fail — one line (settings: device, rate/buffer, MIDI device)
L3 benchmark: <file> — <key numbers>
Failures + logs (paths relative to the checkout):
Signed: owner-local-agent, <YYYY-MM-DD>
```
