<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-g1 OSC endurance (proposal 0019 §3, OB r2.4a)

This standard-library Python harness runs the native sidecar with --null-audio and
--bench-summary, binds only 127.0.0.1, creates temporary settings, and never
opens audio/MIDI devices or sends LAN packets. It follows the
tools/examples/osc_loopback_check.py protocol without modifying tools/.

## Run (from a clean, pinned repository checkout with a built engine)

    python3 -m unittest discover -s bench/io -p 'test_*.py' -v
    python3 bench/io/soak.py --self-test
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile osc-gates --edit-mode still --tier L0
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile osc-heavy --edit-mode still --ladder
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile osc-stress --edit-mode still --tier L0
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile osc-gates --edit-mode config-edits --tier L0
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile midi-m8 --edit-mode still --tier L0
    python3 bench/io/soak.py --engine build/native/wirescape-engine --profile mixed --edit-mode still --tier L0

Ladder durations: L0=60s, L1=600s, L2=3600s, L3=14400s,
L4=43200s, L5=86400s. Each tier starts only after the previous tier
passes at the same source SHA, profile and edit mode. For a standalone tier
above L0 supply both --baseline-report PATH (passing same-SHA L0) and
--previous-report PATH (passing adjacent lower tier). Stop on the first
non-pass; do not skip a tier. All outcomes are advisory (OB r2.4a).

Profiles: osc-gates sends 10 Hz numbered CV/gate loopback; osc-heavy sends
64 addresses at 200Hz each, 12,800 messages/s total, mixed CV/gate,
alongside an independent numbered 10 Hz echo/gate oracle. osc-stress ramps
from 200 to 1600Hz per address in 15s stages until failure (facts only).
The engine permits 8 OSC In rows per module: 64 addresses use eight
modules, not one oversized row list. Seeding and values are deterministic.
A 500Hz OSC Out cannot echo every individual heavy packet; separate 10Hz
numbered echo verifies end-to-end responsiveness, while real ingress/drop
counters assess heavy traffic. This is not a per-packet delivery proof.

OB-g2 extends the same CLI, stop rules, tier ladder and report formats with
`midi-m8` and `mixed`. These profiles automatically pass `--scripted-midi`
to the null-audio sidecar with an explicit temporary `--settings`; no OS MIDI
endpoint or LAN is opened. The deterministic injected source sends four-voice
Note On/Off, 24 ppqn clock, active sensing, CC floods, sustain and a 10-minute
Panic. The native graph routes `midi.in.midi` into `midi.to_cv.midi`.
Both profiles retain the OSC 10Hz echo/gate sentinel to observe edit-induced
A2 disruptions; `mixed` additionally sends 64 × 200Hz OSC ingress.
The actual opt-in `status.midi.counters` must be present with forward
`received` progress at least every 2 s, and any increase in dropped,
ring_full, malformed, send_fail or release_panics stops the tier.
Before/after MIDI received totals appear in both reports; default OSC
profiles still omit counters and preserve the frozen S0 protocol snapshot.

The still mode never edits the graph. config-edits sends loadGraph every 30s
to exercise known A2. Before M4 E5, an *observed* disruption after an edit is
strict XFAIL; no observed disruption is XPASS and returns failure, rather
than inventing evidence. After E5 is merged use --e5-merged explicitly to
require PASS. The lead must confirm that assertion against the source SHA.

## Stop-and-report

Always write JSON and Markdown to
build_reports/io-soak/<profile>/<edit-mode>/<tier>/{report.json,report.md},
or to an operator-selected --report-dir. Preserve failed/blocked reports.
Include first failure, available counters before/after, last five seconds
of timestamped events, tier, exact Git SHA, engine SHA, RTT p99, RSS and
bench line. Stop on engine termination; OSC In dropped/malformed/truncated,
OSC Out dropped or MIDI dropped/ring_full/malformed/send_fail/release_panic
counter increments *if exported*; missing sequence echo/ordered gate edges;
gate >50ms past expected fall; bench overruns/faults; RSS growth >8MiB/hour
after 10min; RTT p99 >2x same-SHA L0.

The --bench-summary line is emitted only at engine shutdown. It is checked
before a tier can pass, not falsely represented as a live streaming check.
Linux RSS uses /proc; Windows uses GetProcessMemoryInfo. If a counter or
memory metric is unobservable it is listed as such, never claimed measured.

## Known observational gap / parallel fix row

Current status.osc.routes exposes received and dropped, but not malformed
or truncated; current MIDI diagnostics lack OB-g2 counters. The harness
checks those named fields when present and explicitly reports that they
are unavailable when absent. A passing OSC echo is not a certification
that an unexposed counter did not rise. A separately authorized telemetry
task must expose these fields, in parallel with OB-g2. No out-of-scope
engine edits are made. No real Pi, ALSA, WinMM, M8 or owner patches are
touched, and #275 stays parked until S6 merges.

Run --self-test to fault-inject engine exit, dropped echo and stuck gate.
L0 Linux result is separate from unit tests; neither mocked results nor
runner setup failures count as a 60-second engine pass.
