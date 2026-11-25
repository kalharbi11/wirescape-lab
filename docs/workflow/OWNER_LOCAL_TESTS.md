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
- **Report:** one comment on [#590](https://github.com/kalharbi11/wirescape-lab/issues/590)
  (or text the owner pastes into the Architect chat) using the template at the end. Leave out
  private patch contents, user names and absolute home paths.

## Windows laptop
Setup is `docs/workflow/WINDOWS_EVAL.md` → "Owner steps" (VS x64 Developer PowerShell, Python
3.12, Node 22 x64).

| ID | Kind | Steps | Pass when | Why it is local |
|---|---|---|---|---|
| L1 | 🔊 owner | Finish WINDOWS_EVAL **T2–T7** (MIDI mono and poly, OSC In, combined, save/load). The owner already reported T1 sound and T5 OSC Out good on `c6ae30a`. | Each row's "Pass when" | Real MIDI device, real UI |
| L2 | 🔊 owner | Play `04-combined` for 20 min at WASAPI 48 kHz / 256, then repeat 10 min at buffer 128. | No crackle, stuck note or UI freeze. Note any glitch with the minute it happened. | Real driver timing |
| L3 | device-off, agent | `py -3.12 tools\owner_record.py --tier standard` at the eval SHA; upload the zip to #590. | Command exits 0 | Owner-hardware CPU numbers for OB-f/M7 (a builder turns them into a `facts/` file with machine and SHA) |
| L4 | device-off, agent | Only if L1 or L2 failed: `python tools\dev.py test` and `cd apps\desktop; npm ci; npm test`. | Same result as Windows CI at that SHA | Separates a machine problem from a product defect |
| L5 | 🔊 owner | Only on request in CURRENT: re-run L1 on a new owner build SHA (for example the OB1 candidate). | As L1 | Candidate sign-off |

## Raspberry Pi 5
The sandboxed `/pi-run` bridge is postponed to the OB1 candidate (inbox A31, PI-1 #369): the private
repo's hosted minutes return on 2026-11-30, and the bridge waits for the owner's token setup.
Until it works, Pi evidence comes from owner-run records. Setup: [INSTALL → Raspberry Pi 5](../INSTALL.md#raspberry-pi-5).

| ID | Kind | Steps | Pass when |
|---|---|---|---|
| P1 | device-off, owner or agent | At the given SHA: `sh tools/pi/update-and-build.sh <sha>`, then `python3 tools/owner_record.py --tier standard --app-smoke` from the desktop session; upload the zip to #590 | Exit 0; the record has no failed step |
| P2 | 🔊 owner | Launch on the Pi screen, load `01-midi-mono` and `04-combined`, and play for 10 min through the USB audio output with a USB MIDI keyboard | Sound, no crackle, UI responsive, no stuck notes |
| P3 | device-off, owner | Overnight: `python3 tools/owner_record.py --tier long`; upload to #590 | Exit 0; max temperature and throttle flags reported |
| P4 | 🔊 owner | OB1: the #579 100-edit session at your buffer size | 0 xruns, no visible stutter, both CN cost rows recorded |

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
