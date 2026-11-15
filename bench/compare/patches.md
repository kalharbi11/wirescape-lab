<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Comparison patch construction

## Experimental constraints

Use 48,000 Hz, 256 frames, the same audio interface and driver family for all programs on a given machine. Repeat at 128 frames only when the complete set runs there. Pin oscillator pitch, note sequence, filter frequency, resonance, envelope, mix level and effects to the values below. Save the actual patch files beneath `bench/compare/patches/<tool>/` after construction; do not commit plugin binaries or recordings. Record the module names and versions selected from each tool.

This is a **topology- and workload-matched** comparison, not sample-identical synthesis. Oscillator spectra, LFO/gate thresholds, filter slopes, envelope curves, MIDI scheduling, summing semantics and effect algorithms differ between software. Signal results retain those differences; do not call a spectrum a hardware-driver measurement.

| Patch | Routing | Fixed settings |
|---|---|---|
| A / `mono` | LFO gate → ADSR CV; 220 Hz VCO → VCF → VCA with ADSR gain → stereo output | LFO 0.5 Hz; VCF low-pass 1800 Hz, resonance 0.15; ADSR A 15 ms/D 140 ms/S 0.65/R 200 ms; voice gain 0.02 |
| B / `poly8` | MIDI note pitch + gate, eight voices of VCO → VCF → VCA←ADSR → stereo output | 8 active voices; MIDI notes 48, 52, 55, 60, 64, 67, 71, 72; same per-voice parameters as A; record voice allocation and MIDI input routing |
| C / `poly8-fx` | Patch B → delay → reverb → stereo output | delay 250 ms, feedback 0.2, mix 0.2; reverb decay 2 s, damping 0.4, mix 0.2 (tool equivalents recorded) |
| D / `scaling` | N independent copies of A → unity summing tree → stereo output | N = 1, 2, 4, 8, 16, 32, 64 where the selected program accepts the graph; identical gain per voice |

VCO waveform and output channel pan must be set to the closest stock equivalent and documented in the manifest notes. For spectral testing, temporarily bypass gate, VCF, VCA modulation, delay and reverb to record a continuous unmodulated oscillator at 110, 440, 1760 and 5000 Hz, with unchanged sample rate and output level. For filter response, drive the filter with equal-amplitude test tones at the same four frequencies and retain source-level evidence. Those probe recordings are separate from the workload measurements.

## Expected output level and speaker-path prerequisite

**Do the five-second speaker check before listening to any comparison patch.** Run
`python bench/device/run.py --speaker-check --confirm-audio --machine <anonymous-label> --device <selected-audio-id>`
on the owner's machine, and confirm the clearly audible 440 Hz, approximately
-18 dBFS RMS calibration tone. For a device-free rehearsal use
`python bench/device/run.py --speaker-check --dry-run`; its null sink cannot
establish speaker audibility. The owner answer is recorded in
`owner-observations.json`. Keep interface and amplifier level fixed after this check.

| Patch | Expected level at the Wirescape output | Listening prerequisite |
|---|---|---|
| A / `mono` | Very quiet: approximately **-62 dBFS RMS** in the owner's offline validation at voice gain **0.02**. This is not a -18 dBFS calibration source. | LFO must open the ADSR gate; a functioning speaker may still make the signal difficult to hear. |
| B / `poly8` | Per-voice VCA gain **0.02**; aggregate RMS is not a fixed value, since it depends on the eight held notes, oscillator phases, filter and envelope. It may be silent with no MIDI notes. | Enable MIDI and hold the fixed eight-note chord. |
| C / `poly8-fx` | Same per-voice VCA gain **0.02** as B before delay/reverb. Output RMS and peaks vary with wet tails and MIDI state; no reference dBFS RMS has been established. | Enable MIDI, hold the chord and allow FX tails to build. |
| D / `scaling` | Each source repeats A's **0.02** voice gain. Aggregate level changes with N and signal summing; there is no one fixed dBFS RMS for all N. | Check the N=1 graph first; verify each load and increase speaker volume cautiously. |

The `0.02` gains are intentional matched-workload settings and **must not
be altered** to make a patch audible. Record the actual output RMS/peak for
each tested tool and condition; the speaker tone checks hardware routing,
not performance or loudness equivalence between programs.

## Wirescape: bundled patch-v2 files

Provided files: `patches/wirescape/mono.json`, `poly8.json`, `poly8-fx.json`. Import them through the Wirescape UI on the device under test. For patch B/C, enable the target MIDI input in the UI before beginning the fixed eight-note sequence. `midi.in` sends to `midi.to_cv` at eight voices and then to the common subtractive graph; runtime graph polyphony is supplied by the native modules. Confirm actual MIDI note response during the owner setup.

Generate the scaling files without opening a device:

```sh
python bench/compare/generate_scaling.py --n 1 --out bench/compare/patches/wirescape/scaling-1.json
python bench/compare/generate_scaling.py --n 2 --out bench/compare/patches/wirescape/scaling-2.json
python bench/compare/generate_scaling.py --n 4 --out bench/compare/patches/wirescape/scaling-4.json
python bench/compare/generate_scaling.py --n 8 --out bench/compare/patches/wirescape/scaling-8.json
```

Each scaling copy uses five nodes, N−1 additional mixer nodes and one output node: **6N nodes**. Current native execution has a 64-node limit. N=16 (96 nodes) is refused by graph capacity, not classified as a CPU or xrun failure. The guided scaling sampler explicitly records this limit. When another program accepts N=16 or 32, those are tool-specific measurements rather than common-N comparisons.

## Cardinal (standalone) / Pi ARM64 and Windows

1. Install an official Cardinal standalone build for the machine architecture. Cardinal contains its own modules and does not load the VCV Library. Use the equivalent Fundamental/VCV-style included VCO, VCF/low-pass, VCA, ADSR, LFO and Audio modules through Cardinal's module browser.
2. For A, wire LFO output to ADSR gate, VCO audio to low-pass filter input, filter output to VCA input, ADSR envelope to VCA gain CV, and VCA output to both audio output channels. Enter the settings table above. Record the oscillator waveform and LFO gate threshold used.
3. For B, replace the LFO gate with an included MIDI-CV source. Set eight polyphonic channels or eight independent voice paths as supported by the selected modules; fan out pitch and gate to each voice. Verify exactly eight held notes sustain. Sum voice outputs at unity levels and route to Audio.
4. For C, insert included delay and reverb modules after that sum. Match delay/feedback/mix and the available reverb controls; document control mappings that lack direct numeric equivalence.
5. For D, duplicate the complete A voice N times (each with its own LFO), then sum. Save separately for each N and record first non-loadable N. Choose the same module variants for every N.

Cardinal builds and architectures: https://github.com/DISTRHO/Cardinal/releases ; https://github.com/DISTRHO/Cardinal .

## VCV Rack 2 Free (Windows laptop)

1. Install Rack 2 Free standalone. Use Rack's built-in VCO, VCF, VCA, ADSR, LFO, MIDI-CV and Audio modules, plus Rack built-in/installed modules for delay and reverb. Document module identifiers and revisions; additional modules are recorded as dependencies.
2. For A, follow Cardinal step 2, with a direct audio output module and identical settings.
3. For B, set MIDI-CV polyphony to eight channels, connect poly pitch/gate into poly-capable synthesis/envelope modules or construct eight independent paths. Record whether voice processing is poly cables or independent modules.
4. For C, route the B sum through delay and reverb in series. Record module-specific parameter translations. For D, duplicate A as separate voices and combine using mixer modules, keeping individual voice gain fixed.
5. Save A/B/C and every accepted N as separate `.vcv` files into `bench/compare/patches/rack2/`.

Rack system requirements list x64 CPUs on Windows/Linux and Apple ARM64; this protocol restricts Rack 2 Free to the laptop and does not schedule a Pi ARM64 run: https://vcvrack.com/Rack .

## Pure Data vanilla / plugdata (Pi ARM64 and Windows)

1. Install vanilla Pd or plugdata. Use **vanilla** objects only to keep the patch portable. Set the DSP backend to 48 kHz and the specified interface. In vanilla Pd, confirm its internal 64-sample DSP vector and separately record host audio I/O buffering; a 256-frame external buffer is not the Pd block size.
2. For A, connect `[osc~ 220]` → `[lop~ 1800]` → `[*~]` → `[dac~ 1 2]`. Construct a gate at 0.5 Hz from `[metro 1000]`/`[f]`/`[expr 1-$f1]` (a 2-second full gate cycle), then trigger `[vline~]` with gate-on message `0, 1 15, 0.65 140 15` and gate-off message `0 200`; this implements attack 15 ms, decay 140 ms to sustain 0.65, then release 200 ms. Multiply envelope by 0.02 before the VCA amplitude inlet. Use `[loadbang]` to arm the gate after opening. Document that `[lop~]` is a one-pole filter, unlike the other programs' filter models.
3. For B, use `[notein]` → `[poly 8 1]` → `[pack]` → `[clone voice 8]`; put oscillator, `[lop~]`, `[vline~]`, `[*~]` inside `voice.pd`. Convert MIDI note pitch with `[mtof]`, allocate eight voices, and sum clone outlets. Use a loopMIDI/ALSA controller or external MIDI file player to deliver the same notes.
4. For C, add a 250 ms vanilla delay line using `[delwrite~]`/`[delread4~]` with 0.2 feedback and wet level; implement a documented vanilla multiple-delay approximation for reverb or mark reverb as algorithmically unmatched. Save that implementation with the patch.
5. For D, instantiate N independent `[pd voice_mono]` or `[clone voice_mono N]` with independent 0.5 Hz gates and send their summed audio to one `[dac~]`. Save the exact `.pd` files at each N in `bench/compare/patches/pd/` or `plugdata/`. Include abstractions such as `voice.pd` in the same folder.

plugdata publishes Debian aarch64 builds for Raspberry Pi: https://plugdata.org/download . Plain Pd source and builds: https://puredata.info/downloads/pure-data .

## Sequence and signal probes

Create the deterministic 60-second Standard MIDI File with `python bench/compare/midi_fixture.py --out bench/compare/results/fixtures/benchmark-60s.mid`. Deliver this same file through an owner-selected MIDI player/virtual port to every MIDI-enabled tool, with the player excluded from the measured process tree and documented in session notes. It uses notes 48, 52, 55, 60, 64, 67, 71 and 72, velocity 100/127, chord-on at 0 s, chord-off at 2 s, then repeats every 4 s for 60 s. Mono uses the 0.5 Hz gate without MIDI. Disable auto-updates, background scans, visible analyzers and additional instruments in each application. Record any deviations in each run's notes outside the neutral facts files.

A waveform with zero audible dropouts is not a guarantee of zero reported xruns; log **both**. The CPU sampler reports 100% for one fully occupied logical core, and a tool using multiple cores can report greater than 100%. Do not compare tool-specific CPU meters with the sampler percentages without labelling their distinct units.
