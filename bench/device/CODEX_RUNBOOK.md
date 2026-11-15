<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device runbook for Codex (Pi 5 and Windows laptop)

**Version 1, 2026-11-15, written by Fable.** The owner starts Codex on the owner's laptop. Codex runs this
runbook and nothing else (`docs/context/CONSTRAINTS.md`, devices-off rule, owner's change of 2026-11-15).

## Rules for Codex
1. Run only the commands in this file, in order. Do not edit code, scripts, scenarios or settings. Do not
   install anything this file does not name.
2. Device flags (`--confirm-audio`, `--confirm-midi`) appear only where this file writes them.
3. **If a step fails:** copy the last 40 lines of its output into your notes, do the "If it fails" action
   for that step, and carry on with the next run. Never patch around a failure. Never retry more than once.
4. Never commit recordings, ZIPs, `events.ndjson`, host names, user names or absolute home paths. Machine
   labels are `pi5` and `windows-laptop`.
5. `<…>` values come from the owner's prompt or from the discovery step that names them. If one is missing,
   ask the owner; do not guess.
6. The owner listens. Before any step marked 🔊, tell the owner sound is about to start and wait for "go".
7. At the end, deliver the report in §5. Sign it `Signed: gpt-helper, <YYYY-MM-DD>` (New York date).

Values the owner gives you: `<pi-ssh>` (SSH alias or user@address of the Pi), `<pi-repo>` (path of the lab
clone on the Pi), whether an output-to-input **loopback cable** is connected (Pi and/or laptop), and which
parts to run (default: all of §2, then §3).

## 1. Prepare (both machines, devices off)

Run on the Pi through `ssh <pi-ssh>` inside `<pi-repo>`, and on the laptop in PowerShell at the lab clone.

```sh
git fetch origin main && git checkout main && git pull --ff-only origin main
git rev-parse --short=7 HEAD            # note this as <sha7>
python -m pip install -r bench/device/requirements.txt
python tools/dev.py build --headless
python -m unittest discover -s bench/device/tests
```
Real-engine dry run (no devices). Pi: `--engine build/native/wirescape-engine`;
Windows: `--engine build/native/Release/wirescape-engine.exe`.
```sh
python bench/device/run.py --dry-run --scenario all --engine <engine> --results bench/device/results-dry
```
*If any of these fail:* stop that machine's runs, report, go on to the other machine.

Windows only, build the capture helper (does not run it):
```powershell
cmake -S bench/device -B build/device-capture -G "Visual Studio 17 2022"
cmake --build build/device-capture --config Release
```
*If it fails:* use `--record none` in §3 and say so.

Discovery (write the answers in your notes):
- Pi monitor node: `wpctl status` → the monitor of the USB audio output the owner uses = `<monitor-node>`.
  If unclear, ask the owner. If there is none, use `--record none` and say so.
- Windows: confirm with the owner that loopMIDI has a port named `Wirescape Bench`.

## 2. Raspberry Pi 5 runs

Each run writes to its own `--results` folder so runs never overwrite each other. Run them in this order.
Total about 2 h 45 min.

### P0. Health logger (start before P1, stop after P4)
```sh
nohup sh -c 'while true; do echo "$(date +%s) $(vcgencmd measure_temp) $(vcgencmd get_throttled) used_mb=$(free -m | awk "/Mem:/{print \$3}") load=$(cut -d" " -f1 /proc/loadavg)"; sleep 10; done' > bench/device/pi-health.log 2>&1 &
echo $! > bench/device/pi-health.pid
```
Stop: `kill "$(cat bench/device/pi-health.pid)"`. *If `vcgencmd` is missing:* carry on without the logger.

### P1. 🔊 60-minute full run at 256 frames (baseline)
```sh
python bench/device/run.py --scenario full --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5 --block 256 --results bench/device/results-p1-full-256
```
### P2. 🔊 60-minute full run at 128 frames (target buffer)
```sh
python bench/device/run.py --scenario full --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5 --block 128 --results bench/device/results-p2-full-128
```
*If P1 or P2 exits non-zero or the owner reports continuous break-up in the first two minutes:* stop it
(Ctrl-C), keep the partial folder, note the time it ran, continue with the next run.
The full scenario already scripts buffer-size changes, panic, patch switches and note storms during
playback; the analysis reports the silence around each.

### P3. 🔊 Heaviest patches at 128 frames (about 15 min together)
```sh
python bench/device/run.py --scenario scene --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5 --block 128 --results bench/device/results-p3-scene-128
python bench/device/run.py --scenario chaos --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5 --block 128 --results bench/device/results-p3-chaos-128
```
### P4. Small-buffer probe, 64 frames (about 5 min)
```sh
python bench/device/run.py --scenario basics --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5 --block 64 --results bench/device/results-p4-basics-64
```
Stop the health logger now (P0).

### P5. GUTTR cost on the Pi (no audio device, about 1 min)
```sh
cmake -S docs/context/future_modules/guttur/package -B build/guttur -DCMAKE_BUILD_TYPE=Release
cmake --build build/guttur --target guttur_benchmark
./build/guttur/guttur_benchmark 30000 > bench/device/guttr-benchmark-pi5.jsonl
```
It prints one JSON line for 1 throat and one for 16 (p50, p95, worst µs per 128-frame block against a
2,667 µs period). This finds the cost, not a pass mark. *If the build fails:* skip, report.

### P6. Memory of the full app on the Pi (devices off, about 5 min)
Build the apps, then run the existing app smoke while sampling memory:
```sh
(cd apps/studio && npm ci && npm run build) && (cd apps/desktop && npm ci && npm run build)
nohup sh -c 'while true; do echo "$(date +%s) electron_kb=$(ps -eo rss,args | awk "/[e]lectron/{s+=\$1} END{print s+0}") engine_kb=$(ps -eo rss,args | awk "/[w]irescape-engine/{s+=\$1} END{print s+0}")"; sleep 2; done' > bench/device/pi-app-memory.log 2>&1 &
echo $! > bench/device/pi-app-memory.pid
python tools/pi/app_smoke.py --report build_reports/pi-app-smoke
kill "$(cat bench/device/pi-app-memory.pid)"
```
*If the smoke fails:* keep the memory log anyway, report the failure text.

### P7. Round-trip latency — not available yet
Skip. The measuring tool is not written. Report whether the owner has a loopback cable on the Pi.

## 3. Windows laptop runs

### W1. 🔊 15-minute quick run at 256 frames (baseline)
```powershell
python bench/device/run.py --scenario quick --confirm-audio --confirm-midi --midi-port "Wirescape Bench" --record process-loopback --process-helper build/device-capture/Release/wirescape_device_capture.exe --machine windows-laptop --block 256 --results bench/device/results-w1-quick-256
```
With a loopback cable instead, the owner gives `<input-id>`: replace the two `--record`/`--process-helper`
options with `--record input --input-device <input-id>`. With neither, use `--record none`.
*If it fails on the capture helper:* rerun once with `--record none`.

### W2. 🔊 15-minute quick run at 128 frames
Same command with `--block 128 --results bench/device/results-w2-quick-128`.

## 4. File the results

For each `results-*` folder, on the machine that produced it:
```sh
python bench/device/pack.py <the run folder inside it, e.g. bench/device/results-p1-full-256/pi5/<date>-<sha7>>
```
**Large files** (the ZIPs): upload to the draft GitHub release `bench-<YYYY-MM-DD>` with
`gh release upload bench-<YYYY-MM-DD> <zip> --repo kalharbi11/wirescape-lab` (create it as a draft with
`gh release create bench-<YYYY-MM-DD> --draft --title "bench <YYYY-MM-DD>" --notes "device runs"` if it
does not exist). *If `gh` is missing or refuses:* leave the ZIPs where they are and list their paths.

**Small files** (each under 1 MB) go in one PR to the lab, branch `facts/device-<YYYY-MM-DD>-<sha7>`:
```
facts/device/results/<machine>/<YYYY-MM-DD>-<sha7>-<scope>/
```
with `<scope>` = `full-256`, `full-128`, `scene-128`, `chaos-128`, `basics-64`, `guttr`, `app-memory`,
`quick-256`, `quick-128`. Copy from each run folder only: `manifest.json`, `analysis.json`, `report.md`,
`settings.json`, `waveform.png`. Add `pi-health.log` to both `full-*` folders, the benchmark `.jsonl` to
`guttr`, and `pi-app-memory.log` plus the smoke summary JSON to `app-memory`. Add one row per run to
`facts/device/results/README.md`. Before committing, search the copied files for the machine's host name
and user name and stop if either appears. No recordings, no `events.ndjson`, no ZIPs.

PR title: `facts(device): Pi 5 and Windows runs, <YYYY-MM-DD> (<sha7>)`. Do not merge it; Fable reviews.

## 5. Report to the owner (paste into the PR description too)

```
**Runbook:** v1   **Commit:** <sha7>   **PR:** #…
| Run | Machine | Buffer | Ran (min) | Exit | Engine CPU max % | Dropouts | Longest silence ms | Notes |
(one row per run P1–P6, W1–W2; "skipped" or "failed: <one line>" where it applies)
**GUTTR (Pi):** 1 throat p50/p95/worst µs; 16 throats p50/p95/worst µs
**Pi health:** max temperature, any throttling flag other than 0x0, max memory used
**App memory (Pi):** max Electron total MB, max engine MB
**What the owner heard:** (ask after each 🔊 run: any glitches, silence, distortion? write their words)
**Loopback cable available:** Pi yes/no, laptop yes/no
**Failures:** step, last lines of output
**Large files:** uploaded to release … / left at …
Signed: gpt-helper, <YYYY-MM-DD>
```
