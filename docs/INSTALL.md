<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Install Wirescape 1.0 from source

Wirescape 1.0 is the Electron app (Studio patch editor plus the native
`wirescape-engine`). There is no installer yet; you build one exact commit from
source. Until the owner accepts a build as **v1.0**, each test build is a beta (`beta_01`,
`beta_02`, …) listed with its commit in [releases/betas.md](releases/betas.md). The old Qt app is retired, so don't use its shortcuts, packages or
`--qt-prefix` launches. What's in 1.0 and how to report a test:
[releases/v1.0.md](releases/v1.0.md).

- [Where things live](#where-things-live)
- [Windows 10/11 x64](#windows-1011-x64)
- [Raspberry Pi 5](#raspberry-pi-5)
- [Testing and reporting](#testing-and-reporting)
- [Update to a later version](#update-to-a-later-version)
- [Remove a version](#remove-a-version)
- [Troubleshooting](#troubleshooting)

## Where things live

Shared tools go in normal system places and each version builds in its own folder. A new
version never needs anything from an old folder, and deleting a version folder never removes a
shared tool.

| What | Where | Shared by all versions? |
|---|---|---|
| Compilers, Git, Python, CMake, Ninja, Node.js | system or user tool folders (step 1 of each platform) | yes |
| ALSA, PortAudio, GTK and other libraries (Pi) | `/usr/lib`, installed with apt | yes |
| npm and Electron download caches (Pi) | `~/.npm`, `~/.cache/electron` | yes |
| npm and Electron caches, pinned PortAudio + ASIO SDK build (Windows) | `.tools\windows-setup\` inside the version folder (moving to shared caches is planned) | no |
| `node_modules`, `build`, `build_reports`, `user_data/settings.json` | inside the version folder | no |
| Window size and the default patch folder | Pi `~/.config/wirescape-desktop`, Windows `%APPDATA%\wirescape-desktop` | **yes** |
| `wirescape` command, menu entry, autostart (Pi, optional) | `~/.local/bin/wirescape`, `~/.local/share/applications/wirescape.desktop`, `~/.config/autostart/wirescape.desktop` | **one at a time** |

- **Patches:** every version opens and saves in the same default patch folder, so your patches
  survive deleting a version. An older version may not open a patch saved by a newer one; keep a
  copy before going back.
- **Pi launcher:** there is one `wirescape` command and menu entry. It runs the folder you last ran
  `install-desktop-entry.sh` from. After deleting that folder, rerun the script from the version you
  keep, or remove the entry ([Remove a version](#remove-a-version)).

## Windows 10/11 x64

### 1. Install once

| Tool | Version | Notes |
|---|---|---|
| Git | any recent | |
| Visual Studio 2022 or 2026 | C++ x64 workload + Windows SDK | Build Tools edition is enough |
| Python | **3.12 x64** with the `py` launcher | `py -3.12 --version` |
| Node.js | **22 LTS x64** (npm included) | `node --version` must print `v22.*` |
| CMake + Ninja | CMake 4.2.3, Ninja 1.13.0 | `py -3.12 -m pip install cmake==4.2.3 ninja==1.13.0` |

Visual Studio Code is **not** Visual Studio; you need the Visual Studio C++
build tools above.

**Open an x64 developer shell.** The Start-menu "Developer PowerShell for VS"
shortcut can open an x86 shell, which setup rejects. From any PowerShell window,
paste this instead:

```powershell
$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
Import-Module "$vs\Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments "-arch=x64 -host_arch=x64"
```

**Check the tools** in that shell before running setup:

```powershell
$env:WindowsSDKVersion          # must print e.g. 10.0.26100.0\ ; empty = add a Windows SDK in VS Installer -> Modify -> Desktop development with C++
where.exe cl cmake ninja node   # the FIRST cmake listed is the one used
cmake --version                 # must be 4.2.3
node --version                  # must be v22.*
```

- **CMake shows another version (e.g. 4.4):** pip installed 4.2.3 into a folder
  that isn't on PATH. For this shell, put it first:
  `$env:Path = (py -3.12 -c "import sysconfig;print(sysconfig.get_path('scripts','nt_user'))") + ';' + $env:Path`
- **Node 24 is installed:** 1.0 is tested on Node 22 only. Install nvm-windows
  (`winget install CoreyButler.NVMforWindows`), open a **new** PowerShell, run
  `nvm install 22` then `nvm use 22`, and enter the developer shell again.
- A normal (non-Administrator) window is recommended, so later runs don't hit
  permission errors on files created as Administrator.
- `npm` prints vulnerability and deprecation warnings during setup. They come
  from Electron's build tooling; ignore them and **don't** run
  `npm audit fix --force` (it changes pinned versions).

The setup script prints a **Tool / Found / Required / OK** table for all
prerequisites, then reports every missing or incompatible tool together. If
`cl.exe` is missing but Visual Studio C++ tools are installed, setup attempts
an x64 developer-shell import in its own process. It also prefers pinned CMake 4.2.3 from Python 3.12's user or global
Scripts directory, and checks the pinned CMake/Ninja versions before reporting
a mismatch. Toolchain version ranges remain unchanged pending CI evidence. Neither step changes your machine-wide PATH or installs software.
An elevated shell produces a warning; use a normal user shell when possible.

### 2. Get a clean checkout of the version

Use a **new folder** for each beta, named after it, inside one `C:\wirescape` folder
(for example `C:\wirescape\beta_02`). Your old folder, patches and settings
stay untouched, and stale Qt build caches can't leak in.
Any folder works, including paths with spaces. You don't need to uninstall an
earlier beta; just close it before launching 1.0 so they don't share audio and
MIDI devices.

```powershell
git clone https://github.com/kalharbi11/wirescape-lab.git C:\wirescape\beta_02
cd C:\wirescape\beta_02
# Use the commit listed for this beta in docs/releases/betas.md, or current main:
$Ref = (git rev-parse origin/main).Trim()
git switch --detach $Ref
```

### 3. Build and self-test (devices stay off)

```powershell
.\tools\windows\setup.ps1 -CheckOnly        # read-only preflight: prints "Preflight PASS"
.\tools\windows\setup.ps1 -Ref $Ref         # about 10-20 min the first time
```

Re-running later in the same folder (detached checkout): use
`$Ref = (git rev-parse HEAD).Trim()`, not `origin/main`.

The script:
- builds pinned PortAudio and puts `libportaudio64bit.dll` next to the engine;
- builds the engine (`build\native\Release\wirescape-engine.exe`);
- runs the engine protocol tests;
- builds Studio and the desktop app;
- opens the real app once with audio off, as a smoke test.

The final status is `status=windows-device-off-smoke-passed` in
`build_reports\windows-setup\summary.txt`. After the isolated Electron test,
setup also launches the actual `Wirescape.cmd --null-audio` briefly and
terminates that smoke-test process tree. It does **not** open audio or MIDI
devices. The script prints the exact launcher path and summary path when done.
If you see `W1 failed: …`, the message and `build_reports\windows-setup\`
say which step failed.

### 4. Launch with sound and MIDI

```powershell
.\tools\windows\Wirescape.cmd
```

This is the owner launcher. It enables audio and MIDI (`--confirm-audio --confirm-midi`). Close
any DAW that holds the audio device exclusively. With shared WASAPI, set Wirescape to
the device's own sample rate; 48 kHz with a buffer of 256 is the known-good setting.

**ASIO:** in Settings, choose **Driver type: ASIO** and then an installed
**ASIO driver** as the Device. These entries are drivers, not individual
speakers/headphones; direct Windows headphone outputs are under **WASAPI**.
ASIO4ALL needs its outputs enabled in its own control panel. FlexASIO must be
installed separately and configured (usually `%USERPROFILE%\FlexASIO.toml`).
Only drivers PortAudio successfully enumerates can appear; a driver visible in
Ableton but absent here is not proof it is uninstalled. ASIO buffer size and
sample rate often require a matching setting in the driver panel. Close Ableton
or any other app holding the ASIO driver, then reopen Settings to enumerate.
If the ASIO SDK download fails, rerun setup with `-NoAsio`.
Settings live in `user_data\settings.json` in this checkout. Patch files you saved
earlier stay where you saved them: open them with **Load**.

Device-off launch (silent, for checking the window only):

```powershell
& .\apps\desktop\node_modules\.bin\electron.cmd .\apps\desktop\build\main.js --engine "$PWD\build\native\Release\wirescape-engine.exe" --null-audio
```

## Raspberry Pi 5

Use **64-bit Raspberry Pi OS (desktop)** on a Pi 5 (4 GB or more), with a USB audio interface
for real sound. Build in a **new folder**; an older checkout stays untouched.

### 1. Install once (owner, needs sudo)

```sh
sudo apt update
sudo apt install -y git build-essential pkg-config python3 python3-venv cmake ninja-build \
  libasound2-dev libportaudio2 libasound2-plugins \
  libnss3 libgbm1 libgtk-3-0t64 libatk1.0-0t64 libatk-bridge2.0-0t64 libxcomposite1 libxdamage1 libxrandr2
```

On Bookworm, drop the `t64` suffixes if apt cannot find those names. The apt `cmake` and
`ninja-build` are enough: Wirescape needs CMake 3.20 or newer (CI tests 4.2.3). Nothing is
installed inside the Wirescape folder.

**Node.js 22 or newer (arm64), installed once for the whole system.** The apt `nodejs` package is
too old, so use NodeSource:

```sh
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version      # v22.x; the preflight accepts 22, 24 and 26
```

If `node` is already 22, 24 or 26 (from apt, NodeSource or nvm), keep it.

**Realtime audio (recommended, once):** run `sudo usermod -aG audio "$USER"`, then create
`/etc/security/limits.d/99-wirescape-audio.conf` with these two lines, and log out and back in:

```
@audio - rtprio 90
@audio - memlock unlimited
```

### 2. Get the version and build (devices stay off)

```sh
mkdir -p ~/wirescape
git clone https://github.com/kalharbi11/wirescape-lab.git ~/wirescape/beta_02
cd ~/wirescape/beta_02                    # one new folder per beta, named after it
Ref=$(git rev-parse origin/main)          # or the commit listed for this beta in docs/releases/betas.md
git switch --detach "$Ref"
python3 tools/pi/preflight.py --check-only   # read-only; lists anything missing
sh tools/pi/update-and-build.sh "$Ref"       # ~30-60 min the first time; add --jobs 1 if low on memory
python3 tools/dev.py test                    # headless tests
python3 tools/pi/app_smoke.py --report build_reports/pi-app-smoke   # needs the desktop session
```

The build logs and summary are in `build_reports/pi-source-build/<sha>/`. A failed stage names
its log file. Fix that, then rerun the same command. Run `tools/dev.py test` in one version folder
at a time: some tests use fixed localhost ports.

### 3. Launch

```sh
python3 tools/dev.py launch --confirm-audio --confirm-midi            # sound + MIDI
python3 tools/dev.py launch --confirm-audio --confirm-midi --confirm-lan   # + LAN OSC (ESP32)
```

LAN consent alone keeps null audio and loopback-only OSC; all three flags are needed for a network
controller ([CONTROLLERS.md](CONTROLLERS.md)). The launcher refuses a stale or incomplete build.
Optional, per user, no sudo: `sh tools/pi/install-desktop-entry.sh` adds a menu entry, and
`sh tools/pi/install-autostart.sh` (`--remove` to undo) starts Wirescape at login.

To check realtime priority while it runs: `chrt -p "$(pgrep -fo '(^|/)wirescape-engine( |$)')"`
should print `SCHED_FIFO` with a nonzero priority.

**What CI already covers for the Pi:** every PR builds and runs the full headless suite on hosted
Linux arm64 (same CPU architecture), with Golden renders and portability checks. What it cannot do:
real Pi timing, the screen, audio and MIDI. Those come from the records below.

## Testing and reporting

**Offline patch preflight (OB-h6, on the Pi).** Before deploying your Studio patch folder,
run the compiled device-off renderer on the target Pi:

```sh
python3 tools/patch_library.py check /path/to/patch-folder --rate 48000 --block 128 --seconds 10 --json build_reports/patch-check.json
```

Use your actual rate and block size, and an existing report parent directory outside the patch
folder. The tool uses no input events, audio or MIDI devices, or sockets; it reports every patch's
load/render status, nonfinite samples, peak/RMS, post-first-second silence and per-block render
wall time as a percentage of the configured period. Silence and overruns are informational;
inspect overruns and worst-block headroom on the Pi. Load/render refusal or NaN/Inf fails the
check. Silence is unmeasured for durations without samples after the first second. Timing is
host-specific and does not establish real-device reliability. The existing `check --shared`
structural validation and `install` commands are unchanged.

Every record is device-off unless the step says 🔊. Upload each zip to
[OWNER-REC #590](https://github.com/kalharbi11/wirescape-lab/issues/590) and paste its summary table.
The lead turns it into a `facts/device/results/` file.

**Device-off record (Windows or Pi, same command).** Run it after a successful build, in the same folder:

```sh
python3 tools/owner_record.py --tier quick      # ~10 min: tests, engine benchmark, every module's CPU, 60 s edit soak
python3 tools/owner_record.py --tier standard   # ~45 min: longer probes, CHAOS 120 s, 10 min edit soak
python3 tools/owner_record.py --tier long       # ~2.5 h: 60 s per module, 1 h edit soak (leave it running)
```

On Windows use `py -3.12 tools\owner_record.py …` in the x64 developer shell. On the Pi, add
`--app-smoke` from the desktop session, and the record also samples CPU temperature and throttling.
It writes `build_reports/owner-record/owner-record-<sha>-<kind>-<tier>-<time>.zip`. User names
and home paths are removed. Exit code 0 means every step passed.

**🔊 Owner acceptance (OB1).** These need you at the machine:
1. **Listening (OB-d):** play the patches listed in `facts/sound/ob_d_patches.md` and note anything wrong.
2. **Your patch folder (OB-a2):** copy your patches to a temporary folder, then
   `python3 tools/patch_roundtrip.py --renderer build/native/wirescape_render --dir <copy-folder>`
   ([tools/pi/README.md](../tools/pi/README.md)). Upload only the pass/fail summary, never private patches.
3. **Pi acceptance (A88):** record both items in one sitting, in this order, on the same Pi,
   candidate SHA, bundled Clocked Groove patch and day.

   **6a — protocol runner:** on the clean, built candidate, close Wirescape and other audio apps.
   Replace the exact output name and 256 with your device and actual buffer size. Start at safe volume.

   ```sh
   python3 tools/pi/acceptance_session.py --dry-run --buffer 256
   python3 tools/pi/acceptance_session.py --confirm-audio --device "EXACT OUTPUT NAME" --buffer 256 --report build_reports/pi-owner-session.json
   ```

   The dry run opens no device. The owner run requires 100 accepted edits, zero observed cumulative
   xruns and a correlated configuration deferral. It records build, edit latencies and both hosted
   CN cost rows. Keep its `visible_stutter` null; observation belongs to 6b.

   **6b — witnessed Studio session:** after the runner exits, launch Wirescape with audio consent
   on the same Pi, candidate SHA, patch and day. Use the same output, rate and buffer. Open the
   original bundled Clocked Groove patch (`basics-08-clocked-groove.json`), make at least 100
   hand edits mixing knob drags, module moves and cable draws, and record the actual count,
   visible stutter (yes/no) and any xruns shown by Studio. One stutter or one xrun fails item 6.
   If an xrun count is unavailable, say so; never invent zero. Upload the 6a report unchanged
   and the 6b observation to [OWNER-REC #590](https://github.com/kalharbi11/wirescape-lab/issues/590).
   See [owner-only acceptance details](PI_APP_SMOKE.md#owner-only-ob1-100-edit-session-579).
   A device-off soak is not a substitute for either item.
4. **Windows play test:** `04-combined` for 20 min at WASAPI 48 kHz / 256, then 10 min at 128. Note
   any crackle, stuck note or UI freeze, with the minute it happened.

## Update to a later version

Versions are 1.0, 1.1, 1.2, … ([releases/README.md](releases/README.md)).
There are two ways to update. Both leave saved patch files where they are.

### Update the folder you already built (fastest)

Settings (`user_data\settings.json`) and build caches stay, so only what
changed is rebuilt (usually a few minutes). Close Wirescape first.

**Windows** (VS x64 Developer PowerShell, in your existing folder):

```powershell
cd C:\wirescape\beta_02                    # your existing checkout
git status --short                          # must print nothing; commit or move local edits first
git fetch --prune origin
$Ref = (git rev-parse origin/main).Trim()   # or the commit named in the release notes
git switch --detach $Ref
.\tools\windows\setup.ps1 -CheckOnly        # prints "Preflight PASS: <sha>"
.\tools\windows\setup.ps1 -Ref $Ref         # ends with status=windows-device-off-smoke-passed
.\tools\windows\Wirescape.cmd               # sound + MIDI
```

If preflight says **Stale/Qt-enabled CMake cache**, the folder predates the
Qt-free build: use a new folder (below) instead of deleting anything.

**Raspberry Pi 5** (terminal in your existing checkout):

```sh
git status --short                           # must print nothing
git fetch --prune origin
Ref=$(git rev-parse origin/main)             # use the same commit as Windows
sh tools/pi/update-and-build.sh "$Ref"       # fetch, switch, Release build, Studio + Desktop; --jobs 1 if low on memory
python3 tools/dev.py test                    # headless tests, devices off
python3 tools/pi/app_smoke.py --report build_reports/pi-app-smoke
```

Then launch with sound and MIDI using the updater's printed command, or from the checkout:
`python3 tools/dev.py launch --confirm-audio --confirm-midi`.
The launcher checks the Release engine and Electron provenance; it refuses stale or incomplete builds.

To go back, `git switch --detach <old sha>` and rerun the same build commands.
`build_reports\windows-setup\summary.txt` (Windows) and
`build_reports/pi-source-build/<sha>/` (Pi) record which commit each build used.

### Or: a new folder per version (safest)

Repeat Windows steps 2–4 in a **new folder**, using that version's commit from
its release notes. Keep the previous folder until the new one passes your test.
Switching back just means running the old folder's `tools\windows\Wirescape.cmd`.
On the Pi, repeat [Pi step 2](#2-get-the-version-and-build-devices-stay-off) in a new folder.

## Remove a version

**Windows:** close Wirescape and delete the version folder (for example `C:\wirescape\beta_02`).
Nothing outside it points at it.

**Raspberry Pi 5:** close Wirescape. If the `wirescape` command or menu entry runs this folder,
remove them first, then delete the folder:

```sh
sh ~/wirescape/beta_02/tools/pi/install-autostart.sh --remove
rm -f ~/.local/bin/wirescape ~/.local/share/applications/wirescape.desktop
rm -rf ~/wirescape/beta_02
```

Shared tools, caches and `~/.config/wirescape-desktop` (window size and the default patch folder)
stay for the next version. To remove those too, for every version, copy your patches out of
`~/.config/wirescape-desktop/patches` first, then `rm -rf ~/.config/wirescape-desktop`.

## Troubleshooting

| Message | Fix |
|---|---|
| `Use Windows x64 Developer PowerShell…` / `cl.exe missing` | Open the VS x64 Developer PowerShell, not plain PowerShell. |
| `Node.js 22 LTS x64 required.` | Install Node 22 LTS x64. Node 24/26 are not supported on Windows yet. |
| `Python 3.12 x64 with py launcher required.` | Install Python 3.12 x64 and tick "py launcher". |
| `Stale/Qt-enabled CMake cache.` | You reused an old folder. Do step 2 again in a new folder. |
| `Source worktree is dirty` | Setup builds only an exact commit. Move stray files (logs) out of the folder; for edited repo files, `git stash` them. To try a local hotfix, commit it locally and pass that commit: `git commit -am "local fix"`, then `$Ref = (git rev-parse HEAD).Trim()`. Report the fix so it lands on `main`. |
| No sound | Check the output device and rate in Settings, close any DAW that holds the device, try 48 kHz / 256. |
| Crackles | Try an `ASIO` device (FlexASIO or your interface driver), then a 512 buffer; copy any `overrun` lines from the terminal into your report. |
