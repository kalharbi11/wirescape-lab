<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner-run audio/MIDI stress harness

**Hardware access is strictly owner-authorized.** Only run real-device scenarios on the owner's Windows laptop or Raspberry Pi 5. CI, unit tests and `--dry-run` do not open audio/MIDI devices or LAN sockets. The harness drives `wirescape-engine` over stdin/stdout NDJSON; it never asks the engine to start OSC.

## Install and verify, devices off

From the lab repository root with Python 3.11+:

```sh
python -m pip install -r bench/device/requirements.txt
python tools/dev.py build --headless
python -m unittest discover -s bench/device/tests
python bench/device/run.py --dry-run --scenario all
```

The engine binary is discovered under `build/native`, `build/native/Release`, or `build`, or provided with `--engine <path>`. If absent, `--dry-run` is a **clearly identified protocol simulation**, not real engine validation. It exercises scheduling and report writing but cannot attest to native correctness. When present, the engine starts with `--null-audio` and MIDI is fake.

For an explicit real-engine null-sink check after a headless Release build, run `python bench/device/run.py --dry-run --scenario all --engine build/native/wirescape-engine` (Linux) or `python bench/device/run.py --dry-run --scenario all --engine build/native/Release/wirescape-engine.exe` (Windows). This refuses command errors and a nonzero native exit. CI checks all six families separately and preserves their `report.md` files, the protocol stream, and the 64-module/128-connection refusal probe. No physical audio or MIDI device is opened.

Pi: install PipeWire's `pw-record` or PulseAudio `parec`, ALSA, and PortAudio dependencies. The Python packages `mido` and `python-rtmidi` create an ALSA virtual output `Wirescape Bench` for scripted MIDI. For a PipeWire monitor, identify the **correct monitor node** with `wpctl status` or `pw-cli ls Node` and pass it through `--monitor-target`. For PulseAudio, specify the actual `<sink-name>.monitor`; the runner intentionally does not select a microphone as fallback.

Windows: build `wirescape-engine.exe`; install loopMIDI, create a port named `Wirescape Bench`, and specify it using `--midi-port`. For a physical output-to-input cable, use `--record input --input-device <input-id>`. The legacy `tools/capture` helper captures **its own process**, not the sidecar. This task ships an independent `bench/device/capture_engine.cpp` WASAPI capture helper that targets the explicit sidecar PID and finalizes its WAV on stdin EOF. Build it **without running it**:

```powershell
cmake -S bench/device -B build/device-capture -G "Visual Studio 17 2022"
cmake --build build/device-capture --config Release
```

On Windows build 20348+, use `--record process-loopback --process-helper build/device-capture/Release/wirescape_device_capture.exe` as a microphone-free alternative to physical `input` capture. The helper is never run in CI, and it refuses without `--confirm-audio`, a live sidecar PID and a fresh output path. If unavailable, the runner stops rather than capturing the system mix.

## One-command owner runs

For the Pi 5 with PipeWire monitor (fill in the actual monitor target):

**15-minute quick run**

```sh
python bench/device/run.py --scenario quick --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5
```

**60-minute full run**

```sh
python bench/device/run.py --scenario full --confirm-audio --confirm-midi --record monitor --monitor-target <monitor-node> --machine pi5
```

For Windows with a physical loopback cable:

**15-minute quick run**

```powershell
python bench/device/run.py --scenario quick --confirm-audio --confirm-midi --midi-port "Wirescape Bench" --record input --input-device 2 --machine win-audio
```

**60-minute full run**

```powershell
python bench/device/run.py --scenario full --confirm-audio --confirm-midi --midi-port "Wirescape Bench" --record input --input-device 2 --machine win-audio
```

Windows process-tree loopback example (same 15-minute quick sequence):

```powershell
python bench/device/run.py --scenario quick --confirm-audio --confirm-midi --midi-port "Wirescape Bench" --record process-loopback --process-helper build/device-capture/Release/wirescape_device_capture.exe --machine win-loopback
```

Optional: use `--device <engine-device-id> --rate 48000 --block 256` to select the owner's real audio device, rate and buffer. Set `--record none` when no capture backend is available. For manual playing, use `--manual-midi --midi-port <controller-input-name> --confirm-midi` and play the desired phrases; that mode records incoming MIDI but produces no scripted external MIDI notes. Check routing and lower the physical amplifier gain before stressing parameters.

`quick` and `full` run 900 and 3600 *planned* seconds of scenario steps (startup and cleanup extra). `all` executes all four patch-family scenarios, the all-parameter extreme set, and a 600-second endurance scenario. A 50 ms ramp at 200 updates/s, randomized parameter walks, topology edits, patch switches, panic, note storms, stray note-offs and buffer changes are all scripted. The engine's native parameter bounds in the hello catalogue determine extrema; the pure simulator cannot validate those bounds. External MIDI actions require explicit `--confirm-midi` and a visible port.

## Reports, offline references and transfer

Results are generated under `bench/device/results/<machine>/<YYYY-MM-DD>-<sha7>/` with `manifest.json`, monotonic protocol `events.ndjson`, `analysis.json`, `report.md`, `offline_scripts/`, and optional `capture.flac` and `waveform.png` (PNG limited to 200 kB). Provide `--render <path-to-wirescape_render>` to render exported `--script` files into audio references. Such scripts reproduce **only parameter and note-only spans**; real MIDI, graph edits, and hardware jitter are excluded from exact offline comparison. Use aligned differences only when a reference is actually rendered and available.

Click, dropout and stuck-note detectors are *diagnostic flags*, not automatic verdicts on musical intent. The report captures engine CPU and dropout snapshots plus command acknowledgement percentiles. The manifest avoids personal usernames and hostnames; engine stderr and recorded voice may contain sensitive information and require owner review before sharing.

To pack a complete, reviewed run for release attachment:

```sh
python bench/device/pack.py bench/device/results/pi5/<YYYY-MM-DD>-<sha7>
```

Attach the ZIP manually to a GitHub release named `bench-<date>`. Never commit the ZIP, recordings, or generated results. Record verified numeric outcomes in `facts/` with date, lab commit, machine, units, commands and sources; opinions belong outside `facts/`.
