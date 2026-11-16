<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner-run audio/MIDI stress harness

**Codex running the device tests for the owner follows `bench/device/CODEX_RUNBOOK.md`, not this file.**

**Hardware access is strictly owner-authorized.** Only run real-device scenarios on the owner's Windows laptop or Raspberry Pi 5. CI, unit tests and `--dry-run` do not open audio/MIDI devices or LAN sockets. The harness drives `wirescape-engine` over stdin/stdout NDJSON; it never asks the engine to start OSC.

## First owner hardware step: speaker/level check

Before any stress scenario or comparison listening, check the **selected**
audio output independently of the quiet comparison fixtures. Set your physical
speaker/amp level conservatively, then on the owner's machine run:

```sh
python bench/device/run.py --speaker-check --confirm-audio --machine owner-device --device <selected-audio-id> --rate 48000 --block 256
```

This uses the actual sidecar output device, plays a 440 Hz sine at approximately
**-18 dBFS RMS** for five seconds with short gain ramps, then asks whether it
was clearly audible. The reply and selected device are written to
`owner-observations.json` beside `manifest.json`. If it was not audible,
check speaker power, master volume, driver, endpoint and cables before any
performance run. A real run **refuses** without `--confirm-audio`.

The safe rehearsal `python bench/device/run.py --speaker-check --dry-run`
sends the same graph through the available engine with `--null-audio`
(or a clearly labelled protocol simulation if no engine is built).
It is not a hardware or audibility test; it makes no real audio/MIDI device
calls. Keep the comparison patches unchanged; `bench/compare/patches.md`
lists their expected output levels, including the quiet mono fixture.

## Install and verify, devices off

From the lab repository root with Python 3.11+:

```sh
python -m pip install -r bench/device/requirements.txt
python tools/dev.py build --headless
python -m unittest discover -s bench/device/tests
python bench/device/run.py --dry-run --scenario all
```

The engine binary is discovered under `build/native`, `build/native/Release`, or `build`, or provided with `--engine <path>`. If absent, `--dry-run` is a **clearly identified protocol simulation**, not real engine validation. It exercises scheduling and report writing but cannot attest to native correctness. When present, the engine starts with `--null-audio` and MIDI is fake.

For an explicit real-engine null-sink check after a headless Release build, run `python bench/device/run.py --dry-run --scenario all --engine build/native/wirescape-engine` (Linux) or `python bench/device/run.py --dry-run --scenario all --engine build/native/Release/wirescape-engine.exe` (Windows). This refuses command errors and a nonzero native exit. The real null-sink dry run compresses nominal scenario time by 100× while spacing commands at least 3 ms apart to avoid artificial saturation of the bounded event queue; these timings are **not** hardware timing measurements. CI checks all six families separately and preserves their `report.md` files, the protocol stream, and the 64-module/128-connection refusal probe. No physical audio or MIDI device is opened.

Pi: install PipeWire's `pw-record` or PulseAudio `parec`, ALSA, and PortAudio dependencies. The Python packages `mido` and `python-rtmidi` create an ALSA virtual output `Wirescape Bench` for scripted MIDI. Lab issue #31 enables libremidi's virtual-port discovery; no local `source.patch` edit is required for that port. For a PipeWire monitor, identify the **correct monitor node** with `wpctl status` or `pw-cli ls Node` and pass it through `--monitor-target`. For PulseAudio, specify the actual `<sink-name>.monitor`; the runner intentionally does not select a microphone as fallback.

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

## Electrical loopback (M0 r2 ruling R1): three separate quantities

**Owner-gated. Not a CI or dry-run hardware result.** The bench/device/latency.py
CLI now measures and reports *only* these three named quantities:

1. **harness_loopback_ms:** PortAudio opens **one full-duplex stream** on
   the selected physical output-to-input cable. The harness emits forty
   low-level 1 kHz click pulses and records their returns in that *same*
   callback stream. Subtract output-click **sample index** from captured-onset
   **sample index**, divide by sample rate; **no Python or PortAudio wall-clock
   interval is used for this number**. Input and output must belong to the
   same duplex device clock.
2. **command_to_capture_ms:** A separate engine output run sends forty
   individually marked setParam commands, each opening the VCA for about
   22 ms every 500 ms. The command timestamp is time.monotonic() at the
   actual pipe **write**, not send entry or reply. Per pulse, input onset is
   the owning recorder callback's inputBufferAdcTime mapped into the Python
   monotonic reference plus its within-buffer sample index divided by rate.
   If the ADC timestamp is absent/invalid, use the **callback time** plus
   that sample offset and add **one full capture-buffer duration** to the
   explicitly stated additional uncertainty. PortAudio relative time to host
   callback clock projection is not absolutely calibrated: no finite absolute
   clock-mapping error bound is claimed.
3. **command_to_sound_ms: range only**, never a point estimate. For median
   and nearest-rank p95 the report is [command_to_capture_ms -
   harness_loopback_ms, command_to_capture_ms], with distinct lower and upper
   endpoint fields. Do not use this range to claim a directly timestamped
   DAC presentation onset or measured absolute timing-error bound.

The report records 40 requested clicks per leg, **at least 30 detections
(required, stronger than the R1 minimum 20)**, sample rate, engine output,
duplex output and duplex capture buffer sizes, input capture buffer size,
device **class** (not machine host or serial), median/p95/min/max/stddev,
callback ADC/fallback counts, plus all actual per-click sample indices.
Refuse a leg if too few clicks or recorded level below -40 dBFS.
The old host-command/ack **midpoint** diagnostic and nominal offset minus
2×buffer remain *historical only*; they are neither the R1 duplex harness
number nor a hardware-overhead estimate. Source code/fixtures contain no
owner hardware measurements.

**Owner procedure:** use a direct electrical output-to-input cable and a
duplex-capable interface. No microphone, OS monitor sink, loopback helper or
MIDI. Ensure the selected PortAudio harness output is the *same physical
endpoint* as the engine output. This identity is owner-verified; the APIs do
not automatically equate device IDs. Keep amplifier low, disable direct
monitoring/feedback, and get the owner's explicit "go" before sound.
The click source is muted until commands begin; maximum 0.20 FS
(approximately -14 dBFS peak), every 500 ms for about 20 seconds *per leg
per buffer size*. Duplex cable calibration occurs first, then the engine
command-capture sequence.

Discover device IDs **without opening streams**:
    python -c "import sounddevice as sd; print(sd.query_devices())"
The owner supplies the engine output ID (--device), corresponding PortAudio
harness output ID (--harness-output-device), and PortAudio physical input
ID (--input-device). Supply an anonymous --device-class such as
usb-interface or built-in; do not include host names or serial numbers.
If any ID is unknown or the stream cannot operate duplex, skip/refuse:
do not substitute separate input/output streams.

Device-free rehearsal (synthetic sample delay + invented compatible
timestamps, **not** a physical calibration):

    python bench/device/latency.py --dry-run --sweep --machine synthetic --results bench/device/results-r1-dry

Actual owner-only Pi command after cable, IDs, gain and "go":

    python bench/device/latency.py --confirm-audio --device <engine-output-id> --harness-output-device <portaudio-output-id> --input-device <portaudio-input-id> --device-class usb-interface --rate 48000 --sweep --machine pi5 --results bench/device/results-r1-pi5

On Windows change --machine windows-laptop and specify that host's
chosen IDs and class. --sweep runs 64, 128, 256 frame configurations.
Device authorization is checked before importing the audio backend,
creating results, or launching the engine. No physical device runs
in unit tests or CI.

Per block, review latency.json, manifest.json, and report.md;
a real leg also writes capture.flac, events.ndjson, and engine stderr.
Do not distribute raw recordings or stderr without reviewing for private
data. A refused leg must stay refused; report the exact error, not inferred
latency values. The owner supplies actual device measurement results later.

## Reports, offline references and transfer

Results are generated under `bench/device/results/<machine>/<YYYY-MM-DD>-<sha7>/` with `manifest.json`, monotonic protocol `events.ndjson`, `analysis.json`, `report.md`, `offline_scripts/`, and optional `capture.flac` and `waveform.png` (PNG limited to 200 kB). Provide `--render <path-to-wirescape_render>` to render exported `--script` files into audio references. Such scripts reproduce **only parameter and note-only spans**; real MIDI, graph edits, and hardware jitter are excluded from exact offline comparison. Use aligned differences only when a reference is actually rendered and available.

Click, dropout and stuck-note detectors are *diagnostic flags*, not automatic verdicts on musical intent. The report captures engine CPU and dropout snapshots plus command acknowledgement percentiles. The manifest avoids personal usernames and hostnames; engine stderr and recorded voice may contain sensitive information and require owner review before sharing.

To pack a complete, reviewed run for release attachment:

```sh
python bench/device/pack.py bench/device/results/pi5/<YYYY-MM-DD>-<sha7>
```

Attach the ZIP manually to a GitHub release named `bench-<date>`. Never commit the ZIP, recordings, or generated results. Record verified numeric outcomes in `facts/` with date, lab commit, machine, units, commands and sources; opinions belong outside `facts/`.
