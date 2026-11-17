<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M2 #139 applyGraph continuity — hosted measurements

Lab commit `8eb7898414920a53ca12ad3868fc9b583bcd2490`; cloud container, null sink, devices off; Linux x86_64, Intel(R) Xeon(R) 6975P-C; 2026-11-17T06:37Z UTC; 48000 Hz, 256 frames; 3 repeats, worst shown.
Method: proposals/0005 section 4 as amended by M0 r3 ruling R7; bench/continuity/DESIGN.md. Edit position from the marks file only; "bracket" is `b1 + 1 − b0` blocks. `—` means not measured; the JSON gives the reason and every repeat. No thresholds.

| edit | witness | ch | reply | bracket | silence_ms | dip_db | time_slip_ms | jump_ratio | disturbed_ms | restarted |
|---|---|---|---|---|---|---|---|---|---|---|
| applyGraph identical | tone | 0 | ok | 5 | 0.0208 | -24.9 | — | 1 | 10.6 | — |
| applyGraph identical | slip_tone | 1 | ok | 5 | — | — | -7.34e-09 | — | — | — |
| applyGraph identical | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph identical | held_note | 3 | ok | 5 | 0.0208 | -23.9 | — | 1 | 10.6 | — |
| applyGraph identical | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph identical | subject | 5 | ok | 5 | — | — | — | — | — | False |
| applyGraph Groove steps | tone | 0 | ok | 5 | 0.0208 | -24.9 | — | 1 | 10.6 | — |
| applyGraph Groove steps | slip_tone | 1 | ok | 5 | — | — | -7.34e-09 | — | — | — |
| applyGraph Groove steps | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph Groove steps | held_note | 3 | ok | 5 | 0.0208 | -23.9 | — | 1 | 10.6 | — |
| applyGraph Groove steps | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph Groove steps | subject | 7 | ok | 5 | — | — | — | — | — | — |
| applyGraph Groove length | tone | 0 | ok | 3 | 0.0208 | -24.9 | — | 1 | 10.6 | — |
| applyGraph Groove length | slip_tone | 1 | ok | 3 | — | — | 2.38e-09 | — | — | — |
| applyGraph Groove length | tail | 2 | ok | 3 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph Groove length | held_note | 3 | ok | 3 | 0.0208 | -23.9 | — | 1 | 10.6 | — |
| applyGraph Groove length | clock | 4 | ok | 3 | — | — | 0 | 1 | 0 | — |
| applyGraph Groove length | subject | 7 | ok | 3 | — | — | — | — | — | — |
| applyGraph voice count | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| applyGraph voice count | slip_tone | 1 | ok | 5 | — | — | 1.46e-08 | — | — | — |
| applyGraph voice count | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph voice count | held_note | 3 | ok | 5 | 806 | -inf | — | 1 | 1.01e+03 | — |
| applyGraph voice count | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph voice count | subject | 3 | ok | 5 | — | — | — | — | — | False |
| applyGraph OSC In row | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| applyGraph OSC In row | slip_tone | 1 | ok | 5 | — | — | 1.88e-08 | — | — | — |
| applyGraph OSC In row | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph OSC In row | held_note | 3 | ok | 5 | 0.0208 | -25.4 | — | 1 | 10.6 | — |
| applyGraph OSC In row | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph one parameter | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| applyGraph one parameter | slip_tone | 1 | ok | 5 | — | — | 2.74e-08 | — | — | — |
| applyGraph one parameter | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph one parameter | held_note | 3 | ok | 5 | 0.0208 | -27.9 | — | 1 | 10.6 | — |
| applyGraph one parameter | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph one parameter | subject | 5 | ok | 5 | — | — | — | — | — | — |
| applyGraph deleted module | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| applyGraph deleted module | slip_tone | 1 | ok | 5 | — | — | 3.99e-08 | — | — | — |
| applyGraph deleted module | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph deleted module | held_note | 3 | ok | 5 | 0.0208 | -26.7 | — | 1 | 10.6 | — |
| applyGraph deleted module | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| applyGraph restored module | tone | 0 | ok | 4 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| applyGraph restored module | slip_tone | 1 | ok | 4 | — | — | 3.99e-08 | — | — | — |
| applyGraph restored module | tail | 2 | ok | 4 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| applyGraph restored module | held_note | 3 | ok | 4 | 0.0208 | -26.7 | — | 1 | 10.6 | — |
| applyGraph restored module | clock | 4 | ok | 4 | — | — | 0 | 1 | 0 | — |

## Cases not measured in this new capture


## Hosted capture source and artifact pins

All 45 applyGraph witness rows above are actual measurements on source `8eb7898414920a53ca12ad3868fc9b583bcd2490` from [hosted capture run 44031958143](https://github.com/kalharbi11/wirescape-lab/actions/runs/44031958143), job `133865760607`. The capture used the Linux x64 Release null sink, 48,000 Hz, 256 frames, eight named edits, three repeats and three shared no-edit references. Its runner-reported sidecar binary SHA-256 is `e7295b81ea0c4f0fc35cf0a52ea95199b109fcdcd9d1a8446ee3aa010bf2adcd`. The facts-only commit incorporating this table has a **different** head; these numbers must not be relabeled as measured on that later commit.

Raw float32 + marks: artifact `applygraph-continuity-raw-ubuntu-24.04`, ID 14306002737, ZIP SHA-256 `81a24eee6686c8af8bd5b9a8bc23739d0f392c8a6b69dfa11a829715777a373c`, 172629464 bytes. Numeric summary and per-file manifest: artifact `applygraph-continuity-summary-ubuntu-24.04`, ID 14305109188, ZIP SHA-256 `a1d8098483b12cad98117fa388f0b9e6e62bbcb13bcaa50718103d386ec94ca6`. All 54 raw artifact members were independently SHA-256 rehashed: 24 edit + 3 reference PCM, each with matching marks; the JSON includes their relative names and hashes, and every row retains three measured repeats, mark brackets, reply metadata, alignment and worst-of-three. Null values retain the source reasons, not invented zeros.

The prior 119 rows in `facts/dsp/edit_continuity.{json,md}` remain byte-identical (original lab `4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad`, JSON blob `27c1eaf9b18c6e62474a45984ae022ff0b16491e`, Markdown blob `e2517add497023ee0f42b9cb30d524fee8d76a67`). Older unsupported labels are historical, not claims about the new capture. This fact report introduces no acceptance threshold, pass/fail determination, physical audio parity claim or Studio E1b attribution. Notable raw observation: `applyGraph voice count` held-note worst silence = 805.5 ms and dip = −∞ dB, alongside a recorded `live` path.

