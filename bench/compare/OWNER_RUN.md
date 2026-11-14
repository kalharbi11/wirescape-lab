<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner-run cross-tool comparison

This procedure is for the owner on the Windows laptop and Raspberry Pi 5. The comparison script never starts an audio engine or sends MIDI. The owner starts each tool with the correct patch and authorizes measurement with `--confirm-audio`. **CI and dry runs cannot open audio/MIDI devices or network sockets.** Run each application one at a time with the same interface, driver, 48 kHz rate and 256-frame I/O buffer, then optionally 128 frames where every tool supports it.

## Installation

- Python 3.11+ with `python -m pip install -r bench/compare/requirements.txt`; `psutil` samples a process and its descendant processes. `numpy`, `scipy` and `soundfile` provide device-free analysis for owner-supplied recordings. `tzdata` supplies New York dates on Windows.
- Windows: install Cardinal standalone (https://github.com/DISTRHO/Cardinal/releases), VCV Rack 2 Free standalone (https://vcvrack.com/Rack), Pure Data (https://puredata.info/downloads/pure-data) or plugdata (https://plugdata.org/download); install a MIDI loopback port when needed. Install Wirescape from the build under test.
- Raspberry Pi OS 64-bit: install a Cardinal Linux ARM64 release, or build the version under test; install Debian aarch64 plugdata or `sudo apt install puredata`. VCV Rack 2 Free's published Windows/Linux CPU requirements are x64, so skip it on this Pi. Ensure the selected JACK/PipeWire backend has the target sample rate and buffer size.
- For recordings after device harness PR #13 is merged, install its recorder dependencies and provide the selected capture backend. Linux `pw-record` or `parec` needs the output **monitor** node. On Windows, the PID process-loopback helper is compiled via `cmake -S bench/device -B build/device-capture` and `cmake --build build/device-capture --config Release`, and runs only with authorization. An interface input requires a physical loopback cable and an explicitly chosen input.

Follow [patches.md](patches.md) to build the same four signal paths in the different applications. Save the tool-native source files into `patches/<tool>/` (tool names: `wirescape`, `cardinal`, `rack2`, `pd`, `plugdata`). Record tool and module versions and missing parameter equivalents.

## Device-free verification (CI and development)

```sh
python -m pip install -r bench/compare/requirements.txt
python -m unittest discover -s bench/compare/tests
python bench/compare/measure.py --dry-run
```

The dry run launches a short-lived **synthetic sleeping Python process**, samples its CPU/RSS at 10 Hz for 1.2 s, writes a results folder and labels it `synthetic`. It is not hardware evidence. A live run without `--confirm-audio` exits before opening anything.

## 60-second run per tool and patch

Start the named program manually, open the saved patch, set the same audio interface and 48 kHz / 256-frame settings, and identify its PID using Task Manager on Windows or `pgrep -af` on Linux. Record process version and host driver in the arguments; do not supply hostnames or personal identifiers as the machine label. Read `pw-top`'s **ERR** field or JACK xrun count on Pi before and after the run; use the tool's reported dropout counter on Windows. Document the counter source if it resets during the run. At sampling end the script prompts for the **initial** and final xrun readings, and for the tool's own CPU meter value.

Example: Wirescape mono on Pi (replace PID, version, device and driver with observed values):

```sh
python bench/compare/measure.py --confirm-audio --tool wirescape --patch mono --pid 12345 --tool-version 1.0.0 --machine pi5 --audio-device interface-A --driver PipeWire --rate 48000 --block 256 --xruns-before 0 --xruns-after 0
```

Example: Cardinal polyphonic patch on Windows (use the actual PID and version):

```powershell
python bench/compare/measure.py --confirm-audio --tool cardinal --patch poly8 --pid 12345 --tool-version 24.12 --machine windows-laptop --audio-device interface-A --driver WASAPI --rate 48000 --block 256
```

The default sample is **60 seconds at 10 Hz**. Save one separate run per tool/patch/buffer. For scripted environments supply `--meter <percent>`, `--xruns-before <integer>`, `--xruns-after <integer>`; omitted values stay null when there is no interactive terminal. The `--audible-dropouts` flag records an owner-observed dropout.

For scaling, first construct N=1,2,4,8,16,32,... versions with the same voice settings. Run:

```sh
python bench/compare/measure.py --confirm-audio --tool cardinal --patch scaling --scaling --pid 12345 --tool-version 24.12 --machine pi5 --audio-device interface-A --driver PipeWire
```

The command prompts for each N: load that N patch, press Enter to start the 60-second sample, enter the before and after xrun counters and audible dropout observation. Stops at first xrun, audible dropout or native graph-capacity limit. Missing xrun readings do not establish an xrun-free result. Wirescape's scaling generator has a 64-module limit (6N modules), and reports N=16 as a graph limit. Each measured N has its own metrics in `analysis.json`.

## Audio capture, signal analysis and optional latency

Record with an explicit owner-selected source while the process sampler is running. After PR #13 merges, these options reuse `bench/device/record.py`:

```sh
python bench/compare/measure.py --confirm-audio --tool pd --patch mono --pid 12345 --machine pi5 --record monitor --monitor-target <actual-output-monitor> --audio-device interface-A --driver PipeWire
```

```powershell
python bench/compare/measure.py --confirm-audio --tool rack2 --patch poly8-fx --pid 12345 --machine windows-laptop --record process-loopback --process-helper build/device-capture/Release/wirescape_device_capture.exe --audio-device interface-A --driver WASAPI
```

For hardware loopback use `--record input --input-device <interface-input-id>`. These recorders require real hardware and are never invoked in dry run/CI. Prior to PR #13 merging, `--record` modes exit with a dependency explanation; sampling and analysis of previously recorded `--audio-file` remain available.

For spectral probes, record continuous oscillator tones at 110, 440, 1760 and 5000 Hz with the gate open, using the same output channel and level. Record filter output for equal-amplitude inputs at those frequencies. Supply explicit probe files:

```sh
python bench/compare/measure.py --confirm-audio --tool cardinal --patch mono --pid 12345 --machine pi5 --tone-file 110:110.flac --tone-file 440:440.flac --tone-file 1760:1760.flac --tone-file 5000:5000.flac --filter-file 110:filter-110.flac --filter-file 440:filter-440.flac --filter-file 1760:filter-1760.flac --filter-file 5000:filter-5000.flac --audio-file gate-cycles.flac --gate-time 0.5 --gate-time 1.5
```

The analyzer reports RMS, peak, DC, click timestamps, THD and a **nonharmonic spectral floor proxy** for each tone, plus filter relative gain. It cannot isolate true aliasing without an identical source waveform and controlled spectrum, and tonal diagnostics can differ with implementation. Pass recorded gate transition times using repeated `--gate-time <seconds>` arguments to label clicks within ±10 ms of those edges; the waveform must be aligned to the same time origin. An optional interface round-trip latency measurement uses the identical injected pulse and input capture for every tool; log calibrated round-trip milliseconds outside this script. Do not label process-loopback capture as physical round-trip latency.

## Reports and transfer

Each invocation creates `bench/compare/results/<machine>/<YYYY-MM-DD>-<sha7>/` containing `manifest.json`, 10 Hz `samples.ndjson`, `analysis.json`, `report.md` and optional `capture.flac`. A real-device run with `--facts` also writes sanitized measurements into `facts/compare/measured/`. Inspect those values and the tool version before committing; generated recordings and results folders are git-ignored.

The manifest records OS, CPU model, tool version, audio interface label/driver, rate, block and lab commit. Facts contain metric units and source script but no hostnames, user names, private paths, audio or binaries. Keep source files in `bench/compare/patches/<tool>/` and never commit captures.

**Time allocation per machine:** initial install and patch creation vary by tool; the base sample matrix is four patches × number of installed tools × 60 s, plus 60 s for each scaling N and for each distinct buffer setting. On Windows with four tools this is at least 16 measured minutes per buffer before manual switching, probes and setup; a full two-buffer owner session can require 60–120 minutes. On the Pi omit Rack 2 Free.

Signed: gpt-builder3, 2026-11-14
