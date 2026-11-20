<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Windows owner evaluation: sound, MIDI to CV, OSC In, OSC Out (2026-11-20)

The owner is testing on a Windows laptop. **This is not an OB0 or OB1 gate.** It does not change
the OB0 tag, the S6 window, the OB1 order or any acceptance threshold. A pass is recorded as
"Windows owner evaluation passed" for the behaviours actually observed, and nothing more.
Decision: inbox A18 and CURRENT "Decided 2026-11-20".

**Source:** build `a440d7175659402474290e34a1d63b4404dcaa72`, the integrated OB0 candidate. It
passed 14/14 Lab jobs (including Windows x64) and Golden on 3/3 platforms. The test patches and
helper scripts (W1/W2) live on a later `main`. Copy them into the build folder, or open them from
a second checkout. They are data and scripts, not engine source.

## What the Architect checked in source (device-off, at `a440d71`)
- `tools/windows/Wirescape.cmd` passes `--confirm-audio --confirm-midi`. OSC needs no flag on
  loopback. LAN reception needs `--confirm-lan`, which is not needed today.
- The OSC In and OSC Out hosts start with the session (`native/sidecar/session.cpp` `start_osc`).
  OSC In listens on 127.0.0.1:9000, rows `/pico1/knob/1..8`, input range 0..1 → output 0..1, 5 ms
  smoothing. After 1 s without messages a row goes stale and **holds** its value (`stale=0`).
- OSC Out sends to 127.0.0.1:9001 at 100 Hz, rows `/ws/row/1..8`, from a control-thread sender
  (no I/O on the audio thread). A row sends only when its value changes by more than 0.001.
  **Only channel 0 of a poly cable is sent**, so feed it mono signals.
- `midi.to_cv` defaults to **4 voices, rotate**. VCO, ADSR and VCA are per voice, and Output sums
  the voices. Start with `voice_count = 1`.
- Found: `docs/INSTALL.md` step 2 cloned `kalharbi11/wirescape`, not this lab repository. This
  PR fixes it.

## Owner steps
Use the **VS x64 Developer PowerShell**, a normal (not elevated) shell, and Node 22 x64 with
Python 3.12 (`docs/INSTALL.md` → Windows, step 1).

```powershell
git clone https://github.com/kalharbi11/wirescape-lab.git C:\src\wirescape-eval
cd C:\src\wirescape-eval
$Ref = 'a440d7175659402474290e34a1d63b4404dcaa72'
git switch --detach $Ref
.\tools\windows\setup.ps1 -CheckOnly -NoAsio     # "Preflight PASS"
.\tools\windows\setup.ps1 -Ref $Ref -NoAsio      # ends with status=windows-device-off-smoke-passed
git fetch origin main; git checkout origin/main -- bench/owner_eval tools/examples   # W1/W2 kit, once merged
.\tools\windows\Wirescape.cmd
```
`-NoAsio` skips the Steinberg SDK download. Use **WASAPI** at the device's own rate (48 kHz and a
256 buffer are known good), and close any DAW that holds the device.

| # | Test | Patch | Pass when |
|---|---|---|---|
| T1 | Sound | `01-midi-mono` with Computer keyboard (or any VCO→VCA→Output) | Audible tone, no crackle |
| T2 | MIDI mono | `01-midi-mono`. Settings → MIDI → Input device → **Enabled** | Every key sounds at the right pitch; release silences it; no stuck note after 30 s of playing |
| T3 | MIDI poly | `02-midi-poly4` | Four held keys sound together; each releases on its own |
| T4 | OSC In | `03-osc-in-to-out`, then `python tools\examples\osc_in_sender.py /pico1/knob/1 0.5` (or the snippet below) | The Monitor/row value follows the sent value |
| T5 | OSC Out | Same patch, with `python tools\examples\osc_out_receiver.py` in a second window | The receiver prints `/ws/row/1 0.5` and follows a `--sweep` |
| T6 | Combined | `04-combined` | T2 keeps playing while OSC In changes the sound and the receiver prints LFO/envelope values |
| T7 | Save/load | Save `04-combined` under a new name, restart, reopen it | Same modules, cables, OSC/MIDI config |

Without W1, send OSC with stdlib Python:
```python
import socket,struct
def pad(b): return b + b"\0" * (4 - len(b) % 4)
msg = pad(b"/pico1/knob/1") + pad(b",f") + struct.pack(">f", 0.5)
socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(msg, ("127.0.0.1", 9000))
```
If Windows Firewall asks about the engine, choose Cancel: the firewall does not filter loopback by default, so 127.0.0.1 traffic still works.

## If something fails
Write down which test failed, what you saw, and the Settings values (device, rate, buffer, MIDI
device name, voice count). Keep `build_reports\windows-setup\summary.txt`. Do **not** attach
private patches. For MIDI, follow B4's decision tree on #286. Tell the Architect in run 2: each
failure gets a device-off repro and, only if it is a product defect, a narrow fix task (W4).

## Report (paste into #198 or the Architect chat)
```
Windows evaluation — a440d71 — <date>
Windows <ver/arch>; VS <ver>; Node <ver>; Python <ver>; setup status=<...>
Audio: WASAPI <device>, <rate>/<buffer>
T1..T7: pass/fail + one line each
MIDI device: <name>; voices tested: 1 / 4
OSC In: values sent -> seen;  OSC Out: values received
Failures + logs:
```

## Agent work for this evaluation
| Task | Lane | Due (ET) | What |
|---|---|---|---|
| [W1 #284](https://github.com/kalharbi11/wirescape-lab/issues/284) | B5 | 18:00 | OSC In sender, device-off OSC loopback check, tests (tools/examples only) |
| [W2 #285](https://github.com/kalharbi11/wirescape-lab/issues/285) | B1 | 18:00 | Four test patches in `bench/owner_eval/windows/` |
| [W3 #286](https://github.com/kalharbi11/wirescape-lab/issues/286) | B4 | 17:00 | Read-only Windows MIDI path audit and owner decision tree |
| W4 (not opened) | Codex run, held in reserve | after owner test | Narrow fix for a defect the owner reproduces. Lane B4 for engine/sidecar/MIDI, B1 for Studio. Needs a device-off failing test first |

Signed: claude-architect, 2026-11-20
