<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Edit continuity (T0.13b)

Lab commit `4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad`; cloud container, null sink, devices off; Linux x86_64, Intel(R) Xeon(R) Processor @ 2.10GHz; 2026-11-16T19:00Z UTC; 48000 Hz, 256 frames; 3 repeats, worst shown.
Method: proposals/0005 section 4 as amended by M0 r3 ruling R7; bench/continuity/DESIGN.md. Edit position from the marks file only; "bracket" is `b1 + 1 − b0` blocks. `—` means not measured; the JSON gives the reason and every repeat. No thresholds.

| edit | witness | ch | reply | bracket | silence_ms | dip_db | time_slip_ms | jump_ratio | disturbed_ms | restarted |
|---|---|---|---|---|---|---|---|---|---|---|
| addModule unconnected | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| addModule unconnected | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| addModule unconnected | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| addModule unconnected | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| addModule unconnected | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| removeModule unconnected | tone | 0 | ok | 6 | 0.0417 | -26 | — | 1 | 10.6 | — |
| removeModule unconnected | slip_tone | 1 | ok | 6 | — | — | -3.44e-08 | — | — | — |
| removeModule unconnected | tail | 2 | ok | 6 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| removeModule unconnected | held_note | 3 | ok | 6 | 0.0417 | -27.8 | — | 1 | 10.6 | — |
| removeModule unconnected | clock | 4 | ok | 6 | — | — | 0 | 1 | 0 | — |
| removeModule connected | tone | 0 | ok | 4 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| removeModule connected | slip_tone | 1 | ok | 4 | — | — | -3.37e-08 | — | — | — |
| removeModule connected | tail | 2 | ok | 4 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| removeModule connected | held_note | 3 | ok | 4 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| removeModule connected | clock | 4 | ok | 4 | — | — | 0 | 1 | 0 | — |
| removeModule connected | subject | 5 | ok | 4 | — | — | — | — | — | — |
| connect signal | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| connect signal | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| connect signal | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| connect signal | held_note | 3 | ok | 5 | 0.0208 | -23.9 | — | 1 | 10.6 | — |
| connect signal | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect signal | subject | 8 | ok | 5 | — | — | — | — | — | — |
| disconnect signal | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| disconnect signal | slip_tone | 1 | ok | 5 | — | — | -3.37e-08 | — | — | — |
| disconnect signal | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| disconnect signal | held_note | 3 | ok | 5 | 0.0208 | -27.8 | — | 1 | 10.6 | — |
| disconnect signal | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect signal | subject | 5 | ok | 5 | — | — | — | — | — | — |
| connect event | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| connect event | slip_tone | 1 | ok | 5 | — | — | -3.37e-08 | — | — | — |
| connect event | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.794 | 10.6 | — |
| connect event | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| connect event | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect event | subject | 6 | ok | 5 | — | — | — | — | — | False |
| disconnect event | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| disconnect event | slip_tone | 1 | ok | 5 | — | — | 3.38e-08 | — | — | — |
| disconnect event | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| disconnect event | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| disconnect event | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect event | subject | 7 | ok | 5 | — | — | — | — | — | — |
| connect modulation | tone | 0 | ok | 5 | 0.0208 | -25.2 | — | 1 | 10.6 | — |
| connect modulation | slip_tone | 1 | ok | 5 | — | — | -3.44e-08 | — | — | — |
| connect modulation | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| connect modulation | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| connect modulation | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| connect modulation | subject | 6 | ok | 5 | — | — | — | — | — | — |
| disconnect modulation | tone | 0 | ok | 5 | 0.0208 | -24.9 | — | 1 | 10.6 | — |
| disconnect modulation | slip_tone | 1 | ok | 5 | — | — | -3.74e-08 | — | — | — |
| disconnect modulation | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.794 | 10.6 | — |
| disconnect modulation | held_note | 3 | ok | 5 | 0.0208 | -25.5 | — | 1 | 10.6 | — |
| disconnect modulation | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| disconnect modulation | subject | 5 | ok | 5 | — | — | — | — | — | — |
| setModAmount | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| setModAmount | slip_tone | 1 | ok | 5 | — | — | 1.87e-08 | — | — | — |
| setModAmount | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| setModAmount | held_note | 3 | ok | 5 | 0.0208 | -28.6 | — | 1 | 10.6 | — |
| setModAmount | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| setModAmount | subject | 5 | ok | 5 | — | — | — | — | — | — |
| ccMap.set | tone | 0 | ok | 5 | 0.0417 | -26 | — | 1 | 10.6 | — |
| ccMap.set | slip_tone | 1 | ok | 5 | — | — | -3.44e-08 | — | — | — |
| ccMap.set | tail | 2 | ok | 5 | 47.1 | -109 | — | 0.811 | 10.6 | — |
| ccMap.set | held_note | 3 | ok | 5 | 0.0208 | -27.8 | — | 1 | 10.6 | — |
| ccMap.set | clock | 4 | ok | 5 | — | — | 0 | 1 | 0 | — |
| loadGraph identical | tone | 0 | ok | 8 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph identical | slip_tone | 1 | ok | 8 | — | — | 33.3 | — | — | — |
| loadGraph identical | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph identical | held_note | 3 | ok | 8 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph identical | clock | 4 | ok | 8 | — | — | -122 | 1 | 1.01e+03 | — |
| loadGraph identical | subject | 5 | ok | 8 | — | — | — | — | — | True |
| loadGraph Groove steps | tone | 0 | ok | 10 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph Groove steps | slip_tone | 1 | ok | 10 | — | — | 33.3 | — | — | — |
| loadGraph Groove steps | tail | 2 | ok | 10 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph Groove steps | held_note | 3 | ok | 10 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph Groove steps | clock | 4 | ok | 10 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph Groove steps | subject | 7 | ok | 10 | — | — | — | — | — | True |
| loadGraph Groove length | tone | 0 | ok | 8 | 6.04 | -164 | — | 1 | 1.03e+03 | — |
| loadGraph Groove length | slip_tone | 1 | ok | 8 | — | — | 33.3 | — | — | — |
| loadGraph Groove length | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph Groove length | held_note | 3 | ok | 8 | 1.02e+03 | -147 | — | 1 | 1.03e+03 | — |
| loadGraph Groove length | clock | 4 | ok | 8 | — | — | -117 | 1 | 1.01e+03 | — |
| loadGraph Groove length | subject | 7 | ok | 8 | — | — | — | — | — | True |
| loadGraph voice count | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph voice count | slip_tone | 1 | ok | 9 | — | — | -45.3 | — | — | — |
| loadGraph voice count | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph voice count | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph voice count | clock | 4 | ok | 9 | — | — | -122 | 1 | 1.01e+03 | — |
| loadGraph voice count | subject | 3 | ok | 9 | — | — | — | — | — | — |
| loadGraph OSC In row | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph OSC In row | slip_tone | 1 | ok | 9 | — | — | 49.3 | — | — | — |
| loadGraph OSC In row | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph OSC In row | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph OSC In row | clock | 4 | ok | 9 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph one parameter | tone | 0 | ok | 8 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph one parameter | slip_tone | 1 | ok | 8 | — | — | 38.7 | — | — | — |
| loadGraph one parameter | tail | 2 | ok | 8 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph one parameter | held_note | 3 | ok | 8 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph one parameter | clock | 4 | ok | 8 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph one parameter | subject | 5 | ok | 8 | — | — | — | — | — | — |
| loadGraph deleted module | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph deleted module | slip_tone | 1 | ok | 9 | — | — | 28 | — | — | — |
| loadGraph deleted module | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph deleted module | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph deleted module | clock | 4 | ok | 9 | — | — | 123 | 1 | 1.01e+03 | — |
| loadGraph restored module | tone | 0 | ok | 9 | 6.04 | -inf | — | 1 | 1.03e+03 | — |
| loadGraph restored module | slip_tone | 1 | ok | 9 | — | — | 33.3 | — | — | — |
| loadGraph restored module | tail | 2 | ok | 9 | 256 | -inf | — | 0.941 | 1.03e+03 | — |
| loadGraph restored module | held_note | 3 | ok | 9 | 1.02e+03 | -148 | — | 1 | 1.03e+03 | — |
| loadGraph restored module | clock | 4 | ok | 9 | — | — | -117 | 1 | 1.01e+03 | — |
| setBufferFrames | tone | 0 | ok | 4 | 0.0208 | -24.7 | — | 1 | 9.94 | — |
| setBufferFrames | slip_tone | 1 | ok | 4 | — | — | 32.5 | — | — | — |
| setBufferFrames | tail | 2 | ok | 4 | 250 | -inf | — | 0.941 | 1.01e+03 | — |
| setBufferFrames | held_note | 3 | ok | 4 | 1.01e+03 | -147 | — | 17.2 | 1.01e+03 | — |
| setBufferFrames | clock | 4 | ok | 4 | — | — | 112 | 1 | 1.01e+03 | — |
| panic | tone | 0 | ok | 1 | 0.0208 | -1.09 | — | 7.08 | 1.01e+03 | — |
| panic | slip_tone | 1 | ok | 1 | — | — | -9.33 | — | — | — |
| panic | tail | 2 | ok | 1 | 250 | -inf | — | 0.941 | 1.01e+03 | — |
| panic | held_note | 3 | ok | 1 | 1.01e+03 | -147 | — | 17.2 | 1.01e+03 | — |
| panic | clock | 4 | ok | 1 | — | — | 101 | 1.1 | 1.01e+03 | — |
| panic | subject | 3 | ok | 1 | — | — | — | — | — | — |

## Not measured (not supported today)

- applyGraph identical: applyGraph is not implemented before M2 E1
- applyGraph Groove steps: applyGraph is not implemented before M2 E1
- applyGraph Groove length: applyGraph is not implemented before M2 E1
- applyGraph voice count: applyGraph is not implemented before M2 E1
- applyGraph OSC In row: applyGraph is not implemented before M2 E1
- applyGraph one parameter: applyGraph is not implemented before M2 E1
- applyGraph deleted module: applyGraph is not implemented before M2 E1
- applyGraph restored module: applyGraph is not implemented before M2 E1
