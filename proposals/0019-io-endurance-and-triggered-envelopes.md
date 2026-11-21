<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0019 — I/O endurance testing and triggered envelopes

Claude Architect, 2026-11-21 (ET). Owner request after the Windows MIDI/OSC evaluation
(2026-11-20 report, build `c6ae30a`). Contract: [OB r2.4](../docs/workflow/milestones/OB.md), tasks OB-g1–OB-g7.

## 1. What the owner needs

- An installation on the **Pi 5** that runs **all day**. It uses physical controls, knobs, hardware and
  Python sequencing over **OSC (top priority)** and MIDI, with many parameters modulated at once.
- Stability evidence that machines produce, not the owner. Runs start short and get longer. Each run
  **stops and reports at the first failure or unexplained change**. The Pi is available 24 h a day.
  The Windows laptop is used for patch design and is sometimes off.
- Plucked or percussive envelopes from M8 notes without an `OFF` effect on every phrase, with more
  control than ADSR Sustain = 0.

## 2. What the evidence already says (code read at `main` e13ba34)

- **Live edits restart the patch (KNOWN_ISSUES A2).** Module-config edits, undo/redo, snapshot restore,
  OSC In row edits and MIDI CC Learn all send a full `loadGraph`. That restarts every envelope, held note
  and sequencer, and it fades the output. This alone explains clicks and odd gate behaviour *while
  editing*. **M4 (gapless live edits) removes it**, so it is not patched separately (section 5).
- **A failed MIDI release enqueue panics the engine.** `native/control/midi_host.cpp` `Host::deliver`
  calls `engine.panic()` when a Note Off, CHOKE or release fails to enqueue. A panic cuts every voice,
  which can be heard as clicks and "weird" gates. Nothing counts these panics. This is a plausible cause of
  failures that appear "after a while" under load. It is **not proven**. OB-g2 counts it.
- **MIDI endpoints cannot change while playing.** `Host::select` and `Host::endpoints` throw
  "Stop playback before changing MIDI endpoints" while the service runs. Endpoints are enabled only in
  `Host::start`. If the Studio device toggle does not surface that error or restart the host, a newly
  enabled input stays dead until the next start. That matches the owner's "works after relaunch"
  report (W3 #286). OB-g3 confirms or rules this out with a failing device-off test first.
- **The ADSR and Function Envelope are both gate-held.** Neither has a one-shot mode. MIDI to CV
  has no trigger output and no gate-length option.
- **The Pi sandbox already allows localhost OSC.** wirescape-pi `ci/sandbox.py` runs with
  `--network none`, which keeps loopback, but it has no devices and caps a command at 1800 s.

## 3. Decision: test design (one harness, three sources)

**One harness, `bench/io/`, drives the null-audio engine through its sidecar.** It uses
localhost OSC and an injected MIDI source. The same harness and profile run on Linux CI,
hosted Windows, the Pi and the owner's laptop.

**Duration ladder.** L0 60 s → L1 10 min → L2 1 h → L3 4 h → L4 12 h → L5 24 h. A tier runs only if
the tier below it passed at the same SHA. The ladder stops at the first failure.

**Stop-and-report.** The run fails at once on any of these:
- the engine exits;
- an OSC In drop, malformed or truncated counter rises;
- a MIDI `dropped`, `ring_full`, `malformed`, `send_fail` or release-panic counter rises;
- an expected OSC Out value or gate edge is missing (sequence-numbered);
- a gate stays high more than 50 ms past its expected fall;
- an overrun or fault appears in the bench line;
- resident memory grows more than 8 MiB per hour after the first 10 minutes;
- round-trip latency p99 rises more than 2× above its value at L0.

On a failure the harness writes `report.json` and `report.md` with the first failing check, the
counters before and after, and the last 5 s of events. The Pi pipeline posts these as its usual
`pi5/<task>` comment. These thresholds are **provisional**. OB-g1's first Pi facts confirm or replace
them in one CURRENT line. They become an OB1 gate only as written in section 6.

**Profiles** (seeded, reproducible):
- `osc-gates`: the W1 loopback shape at 10 Hz.
- `osc-heavy`: 64 addresses × 200 Hz = 12,800 messages/s, mixed floats and gates, into parameters
  and OSC In rows. OSC Out echoes a sequence counter. This is the installation case with margin.
- `osc-stress` (facts only, never a gate): ramp until the first loss and record the rate.
- `midi-m8`: 1–4 voices, Note On/Off at 120–180 BPM sixteenths, 24 ppqn clock, active sensing, CC
  floods, sustain pedal, Panic every 10 min.
- `mixed`: `osc-heavy` plus `midi-m8` at the same time.
- Every profile runs in two edit modes:
  - `still`: no edits. A failure here is a real I/O defect and is fixed now.
  - `config-edits`: config edits every 30 s. Until M4 E5 merges, this mode is a **strict expected
    failure** that records A2. After E5 it must pass, and it becomes M4 evidence.
  - The pair tells the owner whether trouble comes from editing or from I/O. The owner does not have
    to find out by standing still.

**Where each part runs.**
| Layer | Runs on | Covers |
|---|---|---|
| Engine + OSC sockets + injected MIDI | Pi sandbox (L0–L5), Linux CI (L0), hosted Windows (L0–L2 nightly) | everything above the OS MIDI driver |
| OS MIDI driver (ALSA sequencer virtual port) | Pi, only if the owner approves Q24 | ALSA enumeration, open and reopen |
| OS MIDI driver (WinMM, loopMIDI, M8) | owner laptop, one scripted `--confirm-midi` run that the owner starts and leaves | Windows driver and endpoint changes |

Hosted runners (GitHub's machines) run public-repo code safely, so the Windows tier needs no laptop.
**No self-hosted runner is ever registered on the public `wirescape-lab`.** A fork PR could run code on
it. The private wirescape-pi runner stays as built in #18/#19: dispatch-only, gate-checked SHAs,
secretless sandbox. It needs no deletion or re-registration.

**Unattended schedule.** wirescape-pi gets one nightly cron that requests the next ladder tier at
`main`'s head. The gate already admits `main`'s head, so this widens no trust. This is the one
exception to #18's "no schedules", and only for that request. The ladder climbs one tier per night
while `main` is unchanged. A new `main` head restarts at L2, since L0–L1 already ran on CI.

## 4. Decision: triggered envelopes (owner: "do both, easiest first")

**First: ADSR trigger mode (OB-g5).** It is the smallest change and gives the most control. It also
works for every gate source: M8, Python, OSC, Groove and clocks.
- New parameter `mode`: Gate (0, default) or Trigger (1). New parameter `hold`, 0–30 s, default 0.
- In Trigger mode, a rising edge (or NOTE_ON on the no-cable path) starts Attack from the
  **current level**, so a retrigger does not click. The cycle runs Attack → Decay → Sustain for `hold`
  → Release and ignores the gate falling and NOTE_OFF. CHOKE, Panic and reset clear it as today.
  Example settings: S = 0 and hold = 0 gives a pluck; S > 0 and hold > 0 gives a timed ADSR.
- Gate mode is **bit-identical** to today: goldens unchanged, and old patches load as Gate.

**Second: a MIDI to CV `trig` output (OB-g6).** It sends a 1 ms pulse per accepted Note On per voice,
including legato pitch changes, where the gate never falls. Notes to CV gets the same output if it
shares the voice code; otherwise it gets a follow-up row.

**Not now: an auto gate length in MIDI to CV.** It gives the same envelope result as OB-g5 with less
control, and it changes voice-allocation timing. That would need new answers for retrigger before
expiry, voice stealing and Note Off shortening. **Overturn if** the owner needs timed gates for something
other than an envelope, such as an external gate out or another module's gate input.

## 5. Decision: build forward, do not patch around

The OB1 chain (S6 → M3 T1.6a–TR1e → M4 E6–E5) removes A2, the largest source of edit-time clicks and
gate loss. Patching edit-time clicks before M4 would be redone by M4. So:
- the I/O defects found in `still` mode are fixed now, each with a failing test first (OB-c rule);
- edit-mode failures are recorded as A2 and wait for M4;
- OB-g work runs in free lanes and never takes a writer from the OB1 chain.

## 6. Gate

OB1 acceptance gains **item 7**: at the OB1 candidate SHA, the Pi passes `osc-heavy` and `mixed`
in `still` mode through **L2 (1 h)**, and `config-edits` through L1. L3–L5 are recorded and not
required, because a 24 h result must not hold the tag. The owner's all-day installation readiness is
L5 on `mixed/still`, recorded in `facts/perf/pi5/io_soak_<date>.json`.

**What would overturn this note:** facts showing kernel UDP loss on the Pi below the installation rate
(the profile changes, not the engine); a release panic in `still` mode traced to engine queue size (it
becomes an engine task under M3/M4 ownership); or the owner rejecting Q24 (the ALSA tier stays
owner-local).

Signed: claude-architect, 2026-11-21
