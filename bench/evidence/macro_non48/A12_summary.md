# A12 Macro pitch applicability — original run 44229365015 (no recapture)

Before `cdd608d517ffe3106897de7d80274768375d0e3c`; after `7bde1ee9603ae7f231d8d20ac130856b97fa8994`. Original estimator SHA256 `6fdeed51e121b62b6ef4b9fa16b773f4c5b42cc4d28db0d643697390bae09efe`.

A12 48k reference rows selected only from byte-identical before/head render. Dominance ≥1 dB; level ≥−40 dB relative to non-DC global peak. Original FFT peak estimator and ±2 cents unchanged.

| Arch | Defined pass | Defined fail | Pitch not defined | Original ZIP SHA256 |
|---|---:|---:|---:|---|
| linux-x64 | 172 | 0 | 68 | `cc241b117810eb323c0b3a6330ff8b454b8a80dfe31db23cd0a96753cb01a959` |
| linux-arm64 | 172 | 0 | 68 | `06e4a12199b9953007bae464d6aafe9c9b7016eb253820c3b56948fe8bfb15b3` |

| Model / pinned Plaits voice.cc registration order | x64 defined Hz | x64 pass/fail/undefined | ARM64 defined Hz | ARM64 pass/fail/undefined |
|---|---|---|---|---|
| 00 Virtual Analog VCF | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 01 Phase Distortion | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 02 Six-op FM A | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 03 Six-op FM B | none | 0/0/10 | none | 0/0/10 |
| 04 Six-op FM C | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 05 Wave Terrain | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 06 String Machine | 110,440,1760,3520 | 8/0/2 | 110,440,1760,3520 | 8/0/2 |
| 07 Chiptune | none | 0/0/10 | none | 0/0/10 |
| 08 Virtual Analog | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 09 Waveshaping | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 10 FM | 440,1760,3520,7040 | 8/0/2 | 440,1760,3520,7040 | 8/0/2 |
| 11 Grain | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 12 Additive | none | 0/0/10 | none | 0/0/10 |
| 13 Wavetable | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 14 Chords | none | 0/0/10 | none | 0/0/10 |
| 15 Speech | 110,440,1760,3520 | 8/0/2 | 110,440,1760,3520 | 8/0/2 |
| 16 Swarm | 440,1760,3520,7040 | 8/0/2 | 440,1760,3520,7040 | 8/0/2 |
| 17 Noise | 1760 | 2/0/8 | 1760 | 2/0/8 |
| 18 Particle | none | 0/0/10 | none | 0/0/10 |
| 19 String | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 20 Modal | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 21 Bass Drum | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 22 Snare Drum | 110,440,1760,3520,7040 | 10/0/0 | 110,440,1760,3520,7040 | 10/0/0 |
| 23 Hi-hat | 440,1760,3520,7040 | 8/0/2 | 440,1760,3520,7040 | 8/0/2 |

**Models with no defined 48k pitch target in either architecture:** 03 Six-op FM B, 07 Chiptune, 12 Additive, 14 Chords, 18 Particle

**Defined-pitch failure rows are real S7.4 defects for the #210 writer, not noise-model exceptions.**

### linux-x64 defined-pitch failures

| Model | Target | Rate | Dominance margin | Level margin | Δ cents |
|---|---:|---:|---:|---:|---:|
| none | — | — | — | — | — |

### linux-arm64 defined-pitch failures

| Model | Target | Rate | Dominance margin | Level margin | Δ cents |
|---|---:|---:|---:|---:|---:|
| none | — | — | — | — | — |
