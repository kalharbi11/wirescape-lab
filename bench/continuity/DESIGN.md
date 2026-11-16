<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Edit-continuity harness (T0.13b, #100): probe design

Design source: [proposals/0005 §4](../../proposals/0005-edits-without-restart.md). This file
records how the harness meets it, including how the edit is located (ruling R7).
Status: metrics, capture reader and marks reader are built and unit-tested. Probe patches, the runner and
`facts/dsp/edit_continuity.*` wait for #99 to merge.

## Files
| File | Role |
|---|---|
| `capture.py` | reads `--capture-null-sink` files: segments, header, deinterleaved channels |
| `metrics.py` | the six §4 metrics on one witness channel; numbers only, no thresholds |
| `marks.py` | reads `<capture>.marks`; bracket, block→sample mapping, window, first divergence, alignment |
| `tests/test_marks.py` | known-answer tests: marks refusal, two-segment mapping, window from a bracket, divergence inside/outside, alignment |
| `tests/test_metrics.py` | known-answer tests: clean sine, 3-block gap, phase jump, step, clock grid and missing pulse, temporary displacement, muted tone, restart, phase jump without reset, silent-start envelope |
| `run.py` (after #99) | drives the sidecar over the protocol on the null sink, three repeats per edit |
| `../patches/continuity/*.json` (after #99) | the probe patches |

Run the tests with `python -m unittest discover -s bench/continuity/tests` (stdlib only). CI: `.github/workflows/continuity.yml`.

## Metric choices §4 leaves open
These are in the `metrics.py` docstring and are listed here so a reviewer can overturn them:
- **Steady reference:** the 500 ms before the window, i.e. [edit − 600 ms, edit − 100 ms), where
  edit is `start(b0)` of the command's mark.
- **`silence_ms`:** consecutive samples with |x| < −80 dBFS, counted at sample level.
- **`dip_db`:** sliding 1 ms RMS with a hop of one sample, in dB against the steady RMS. A full
  gap reads −∞; the facts file writes `"-inf"`.
- **`time_slip_ms`, tone:** a sine of the known frequency is fitted over [edit − 50 ms, edit) and
  [late, late + 50 ms) (late = `start(b1 + 1)`), on one absolute time base, so a displacement that recovers later in the
  window is still read. The phase difference is converted to time and wrapped to ±half a period.
  Positive means late. Slip is read from its own 10 Hz tone (unambiguous to ±50 ms); a 1 kHz
  tone would read a 16 ms gap as 0. Dropout runs (≥ 1 ms below −80 dBFS) are left out of each
  fit, so a mute over a running oscillator reads 0 and a paused one reads its pause. If either
  side has under 5 ms of sounding samples, the value is `null` (a muted tone has no phase).
- **`time_slip_ms`, clock:** the grid comes from onsets before the window (median interval,
  last onset as anchor). The expected events are the grid events from the first one at or after
  the edit. The observed events are the onsets after the midpoint between the last grid event
  before the edit and that first one. The i-th observed onset is paired with the i-th expected
  event. The value is the largest-magnitude signed offset over those pairs; `null` if no onset
  follows. The row also carries `next_offset_ms`, `missing` (expected events with no onset
  within half a period) and `extra`. A missing next pulse therefore shows as one period late and
  as missing, never renumbered to 0. For an isochronous clock a dropped pulse and a one-period
  delay look the same; both fields are reported so the reader sees which events are absent.
- **`disturbed_ms`:** first-to-last sample span where |witness − continuation| exceeds −60 dB re
  the steady RMS. Continuation is the fitted sine for the tone and a no-edit capture for the tail
  and the held note. It is sample-level, because 1 ms framing smeared the span by one frame per edge.
- **`restarted`:** `true` when the subject repeats its start-of-load samples within ±30 ms of the
  edit, differs there from its no-edit continuation, and the repeat begins where the subject
  first leaves its continuation, with only silence (< −80 dBFS) in between. The second
  condition is needed because a free-running oscillator repeats its start every period. The
  third is needed because a phase-displaced oscillator reaches its start phase within one
  period (+π/2 at 100 Hz matches 7.5 ms later; see the test). A start-of-load reference that
  opens silent (an envelope before its attack) is matched together with its silent lead. If the
  reference is silent throughout, the reset value is silence. Then a subject that goes silent
  and stays silent is `null`: a reset and a mute give the same output, and the reason is stored.
  A subject that goes silent and then comes back on its continuation is `false`.

## Probe patch (one patch, separate bus channels)
| Bus channel | Witness | Build |
|---|---|---|
| 0 | tone | VCO, 1 kHz sine, straight to output. Never edited. 1 ms is one period, so the 1 ms RMS is flat. |
| 1 | slip tone | VCO, 10 Hz sine, straight to output, used for `time_slip_ms` only. Never edited. |
| 2 | tail | burst into a delay with feedback |
| 3 | held note | `host.keyboard` → envelope → VCA; `noteOn` sent before the edit, held |
| 4 | clock | Groove or clock → short percussive voice |
| 5 | subject | the module each edit targets, with its own output |

## Procedure and edits
48 kHz, 256 frames, null sink with `--capture-null-sink`. The steps are load, wait 2 s, edit,
reply, wait 2 s, stop. The no-edit reference run is the same script without the edit. Each edit
runs three times and the worst value of each metric is reported. The edits are the §4 list
supported today: add/remove an unconnected module, remove a connected one, connect/disconnect a
signal, event and modulation cable, `setModAmount`, `ccMap.set`, identical `loadGraph`,
single-change `loadGraph` (Groove steps, Groove length, voice count, OSC In row, one parameter,
one deleted and restored module), `setBufferFrames` and `panic`. `applyGraph` rows are added once
M2 E1 lands. Until then they are listed as not supported, not left out silently.

## Locating the edit in the capture (ruling R7, QUESTIONS Q10)
Wall-clock bracketing is not used. The edit is located from the sidecar's marks file
(`<capture>.marks`, PR #104; amended 0005 §4), read and validated by `marks.py`:
- **Marks:** one JSON line per handled command, keys exactly `re`, `type`, `ok`, `gen` (decimal
  string, gen after), `b0`, `b1` (the capture's total block count over all segments, read just
  before apply and just after the reply is built). A file with other keys or types, `b0 > b1`,
  `b0` decreasing in file order or a repeated request ID is refused.
- **Bracket:** the command took effect at a block boundary no earlier than block `b0` and no later
  than block `b1 + 1`, i.e. in samples between `start(b0)` and `start(b1 + 1)`. Every row
  reports the **bracket width as `b1 + 1 − b0` blocks** (always ≥ 1).
- **Block to sample:** a total block index is mapped to (segment, sample offset) by walking each
  segment's block count and block size, so a bracket after `setBufferFrames` uses the new block
  size. Samples are counted on the concatenation of all segments; all segments share one rate.
- **Window:** [`start(b0)` − 100 ms, `start(b1 + 1)` + 1 s). `metrics.py` takes the two bracket
  edges (`edit`, `late`); the steady reference stays the 500 ms before the window, and the tone
  slip fits run over 50 ms before `start(b0)` and 50 ms from `start(b1 + 1)`.
- **First divergence** from the aligned no-edit capture may narrow the position: inside blocks
  `b0` to `b1 + 1` it is reported as the narrowed bracket (`b0`, block of the divergence). Outside
  them it is reported as a finding and is never used as the edit position. Edits with no audible
  change (identical `loadGraph`, `panic` with no notes) report the bracket alone.
- **Aligning two captures:** an edit run and its no-edit reference are aligned on the marks of
  one shared earlier command with the same request ID in both scripts (the `noteOn`, else the
  `loadGraph`). Each mark is a bracket, so the block offset is only known to lie in
  [`b0_a − (b1_b + 1)`, `(b1_a + 1) − b0_b`]. The harness uses `b0_a − b0_b` and reports the
  interval's width (`width_a + width_b` blocks) as the alignment uncertainty beside the row.
  The two widths are reported separately from the edit's own bracket.
