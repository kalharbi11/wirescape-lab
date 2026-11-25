<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-d bundled-patch sound-change ledger (draft)

2026-11-25 ET. OB r2.9, M7 r1.9a. This is a per-stage record, not a cumulative
OB0→OB1 measurement or owner listening result. Final S7.6 is accepted; candidate rebuild and owner listening
remain pending after E7c-b #520. No preset edits in this draft. OB0 was accepted at
`a440d7175659402474290e34a1d63b4404dcaa72` ([release record](../../docs/RELEASES.md));
S7.1/S7.2/S7.4 are already in that baseline, not new OB1 sound-change rows.

## Source and method

Each table is from the exact accepted PR's same-runner Linux x64 Golden diagnostic
archive, downloaded and SHA-256 checked against GitHub artifact metadata on
2026-11-24. Before/after are SHA-256 of little-endian float32 PCM (not WAV or FLAC
file digests), 48 kHz, stereo, 480000 frames, block 128, seed 37; same fixture source
at each head. Each changed row has distinct hashes and both renders report repeat
identity. RMS delta = 20 log10(after RMS / before RMS); band delta = reported
largest third-octave difference. Cross-architecture hashes are not equated.
All three accepted Golden runs had the declared patch sets on all three platforms.
The 27 Golden fixtures include 24 bundled patches and three coverage fixtures;
only bundled patches appear in the changed-patch tables. The hashes and RMS
ratios in all 18 rows were independently checked against the archived
`before.json`, `after.json` and `primary.json`. The chronological stage order is
S7.7, S7.8, then S7.3; cross-stage hashes are not a cumulative same-runner comparison.
The paths below are under `patches/bundled/` with `.json` suffix.

### S7.3 — CHAOS band-limiting (9 / 27)

[Golden 45480416512](https://github.com/kalharbi11/wirescape-lab/actions/runs/45480416512),
[x64 diagnostics 14959829828](https://github.com/kalharbi11/wirescape-lab/actions/runs/45480416512/artifacts/14959829828),
ZIP SHA-256 `0ee14c3206637e72d5dc0dd8ffa675c433e4e122c98fcc0b89d4cdf2f36cac86`.
Base `7096cdfce62b7df43cac2d73ba5e4056c61e8e36` → head `d86c195fa314d6d17ef205ee5a7181edabff361a`,
merged `fe321f9f3b1781108e6f86c62c341bdb6dc8c682`.
AMD EPYC 9V74, [A60 review](https://github.com/kalharbi11/wirescape-lab/pull/432#issuecomment-7143875832).
Saw/square alias reduction; sine path unchanged.

| Patch | Before PCM SHA-256 | After PCM SHA-256 | RMS Δ dB | Largest band Δ dB |
|---|---|---|---:|---:|
| basics-06-chaos-keys | `1cabc0047d8bc03dda5883741c13ab6f0004667fd26e28174d81a373b40262e8` | `cbb2cb80a5dcd2adfe2653aab1365f8fc68f4f22a12e4958d951c8e181f53c0f` | +0.019085 | 22.458668 |
| chaos-01-ember-veil-pad | `ab1585209bed0cfdf9484de61272603b978a28aec9d6efed03845efc7cced5ce` | `d3d8cc545b3e992a5785950876123f09bfc660dd84a3b1585a57e6f08662523e` | +0.005124 | 24.837811 |
| chaos-02-wireglass-lead | `0a14c7a4c65eafcfa17e01dc95d4d9dcc228bc742b9847924176f24a3b7fbbaf` | `51d81aff3d03c9c2b7584121f210883763c61862555bf9eff58e0c8d3544fa89` | +0.006824 | 23.657934 |
| chaos-03-orbiting-iron-fx | `c068160bce32f87218f992b6ee3ee95fafc2fc67711416e06924958ac97650b0` | `b7b1e354fe80006ae3199e4c689116fbefbcde4fe170215a09ffcdea5acfba28` | +0.013280 | 23.022572 |
| chaos-04-radio-static-fx | `46fc515fdbfad91fbf947de853fdd97c23354004b731588467154213c2d5c281` | `2f46a7c23cdead6950d18774d0b3a233ba4a94f7225b5adf6ee6bce41443944a` | +0.014438 | 19.677890 |
| chaos-05-moonlit-drift-pad | `1c8df3b46a4db6de65db63bb8863927f4b7667c621459ab4c60b383ac4fed543` | `fdcc43837fe77d4601f5ab63643ce8008588a8ce6cf53fc634652be23231efba` | +0.003295 | 24.737408 |
| scene-01-hollow-chapel | `9a3e1a40194462a6324ae827ca273f40e4443bf84fa9aed6306512823ee6433c` | `d3a131c33a6fe2cdc09e5e8f5644770f227cf1ffdfbdd27a528404394a574a22` | +0.006511 | 12.424371 |
| scene-02-breathing-walls | `714a221efa385cdad1c3bdd434be4197585398208abcef0db765f6d5d00cd66e` | `07d8460501422b7381c740f4b2efddea1dcd9c4e291c689c8d35b8b8c908ec4b` | +0.004002 | 0.014588 |
| scene-03-black-ice-choir | `882926ff47aa2f9c404c2e4732f330c172571535fd6579f70f95b45540496bae` | `5037a3e72e079e9d70d95c6b7caa305e5ce9be9122cae22f035b96c4bdd2bd55` | +0.004843 | 23.217622 |

D5 source: chaos-01, [verified before/after WAV pair and digests](https://github.com/kalharbi11/wirescape-lab/pull/432#issuecomment-7143230709).

### S7.7 — VCF passband compensation (4 / 27)

[Golden 45342646559](https://github.com/kalharbi11/wirescape-lab/actions/runs/45342646559),
[x64 diagnostics 14896697394](https://github.com/kalharbi11/wirescape-lab/actions/runs/45342646559/artifacts/14896697394),
ZIP SHA-256 `d54597fe82fa67067d49a38abf735fcf22941df4f28f959fde19b69162b2f490`.
Base `c1a411158581513156ec7c914788b46d5c66fdaf` → head `05734fde84aaa7ba56ead6b5159736b938b78c04`,
merged `540024d7604895fc48311d15f5e1196152512e3c`.
AMD EPYC 9V45, [lead verification and D5 scene-06 published](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7125595903).

| Patch | Before PCM SHA-256 | After PCM SHA-256 | RMS Δ dB | Largest band Δ dB |
|---|---|---|---:|---:|
| basics-02-fm-filter-lfo | `f048e68941a1d0b528a18d7e4a95792720a3fa44415fea4b60140c0c8955c110` | `4643f1bd3ae43da71ec6e7c160c0afac93cca8e86e506df6788ab2dfd575a0ed` | +4.899857 | 4.900129 |
| scene-04-vowel-apparitions | `f1c5926f85328bd93a37610d6a7113cf29f3dbcb4bed49019d8a1e71d2c6d43d` | `dcbe0659bbddde61d2528fe691f7f8b5ac2b4cd64e2c0ae8e2c0c2df563fcd52` | +4.899857 | 4.899963 |
| scene-06-dust-reactor | `f3494953cd1bcd13321267c77f9d6f5d7966684eeeca0fcb85c432a8091b9873` | `8d70f3434879b9f8752c47bd77a7e7a87472f4643832f44abce0868084ba46ce` | +7.936050 | 8.152612 |
| scene-07-witching-hour | `06790084f8cff85096e43d915e28fa9256da976f5fed7332ba3bee56121f75b0` | `65ecf02d6d34e910b77ddfb9eb54a8868e469b8843d22a91b45e8baa86a7e750` | +6.281723 | 6.282187 |

### S7.8 — Ladder resonance peak at cutoff (5 / 27)

[Golden 45357636639](https://github.com/kalharbi11/wirescape-lab/actions/runs/45357636639),
[x64 diagnostics 14903442352](https://github.com/kalharbi11/wirescape-lab/actions/runs/45357636639/artifacts/14903442352),
ZIP SHA-256 `895a3177461589471f55a894f04217c1ac9cfb045ec89ea27c7871519ae68544`.
Base `40205d1cafcce5544f92a4319f9dd09fa28884c4` → head `fbb3ccdd249cfff8d61087636bd2b1eac1b8552d`,
merged `8c9f3d0b560ef228549927cc61e438ec0308c6a3`.
AMD EPYC 9V45, [A53 review](https://github.com/kalharbi11/wirescape-lab/pull/405#issuecomment-7128153863);
[scene-02 D5 source and signed evidence](https://github.com/kalharbi11/wirescape-lab/pull/405#issuecomment-7126710831).

| Patch | Before PCM SHA-256 | After PCM SHA-256 | RMS Δ dB | Largest band Δ dB |
|---|---|---|---:|---:|
| scene-01-hollow-chapel | `5021faf7516222f12f4c3ffb94ee60c909cd5e654b5f60d68e9bd9c99d2575b6` | `9a3e1a40194462a6324ae827ca273f40e4443bf84fa9aed6306512823ee6433c` | +0.248180 | 11.907242 |
| scene-02-breathing-walls | `c664a9da99debd14bc72f1af64dd9b08183b877cdadcd82675996b1c835261e5` | `714a221efa385cdad1c3bdd434be4197585398208abcef0db765f6d5d00cd66e` | +2.004410 | 14.668549 |
| scene-05-glass-cathedrals | `cb57529938f6ba1a5c0bb05b9cea6f9eab1a6d8ee6c7c6dc908d1798a650382b` | `09f2e5c8afbaacce769ff09392b7814ccae8220e86569bc7cbbad108ca8e7e52` | +0.562999 | 6.486685 |
| scene-06-dust-reactor | `8d70f3434879b9f8752c47bd77a7e7a87472f4643832f44abce0868084ba46ce` | `edf74008bd3e689390863cf5eb885650c4e8f795111239d8974b0eb3367c792e` | +0.044125 | 6.816143 |
| scene-08-neon-elegy | `0c1395d8c949d14b28ad7d96697c79ff5722693b39b640641aff2033da6dbb4b` | `6274771eed12e1536df13afe12e2b6b9b6ca2be7da2100d4b60f2d4b5b811f84` | +0.917991 | 9.606778 |

A53 Low: full-scale max-resonance step reached 2.4 FS (+7.6 dB); note for listening.
Non-gating r=.25/.75 peak ratios: [#498 / #499](https://github.com/kalharbi11/wirescape-lab/pull/499),
head `97216ec2871ac0c5c056809ac0a64d2f143861d0`, [both Linux runner diagnostics](https://github.com/kalharbi11/wirescape-lab/pull/499#issuecomment-7152174807)
([run 45539446060](https://github.com/kalharbi11/wirescape-lab/actions/runs/45539446060)),
2026-11-24. Both architectures passed the existing Ladder tests and reported
identical values to the printed precision for all twelve extra rows. The
original impulse/whole-spectrum scan uses drive=0; these are reported
measurements only, not new acceptance bounds. Exact-head [Lab 45539447730](https://github.com/kalharbi11/wirescape-lab/actions/runs/45539447730) passed; #499 subsequently merged following [lead approval](https://github.com/kalharbi11/wirescape-lab/pull/499#issuecomment-7154947995).

| Rate Hz | Cutoff Hz | Resonance | Peak Hz | Peak/cutoff | Peak | Passband Δ dB |
|---:|---:|---:|---:|---:|---:|---:|
| 44100 | 1000 | 0.25 | 660.000 | 0.66000 | 1.143203 | 0.214398 |
| 44100 | 1000 | 0.75 | 1080.000 | 1.08000 | 2.957925 | -0.019205 |
| 44100 | 5000 | 0.25 | 3375.000 | 0.67500 | 1.143200 | 0.121669 |
| 44100 | 5000 | 0.75 | 5375.000 | 1.07500 | 2.958051 | -0.140401 |
| 48000 | 1000 | 0.25 | 660.000 | 0.66000 | 1.143203 | 0.215867 |
| 48000 | 1000 | 0.75 | 1080.000 | 1.08000 | 2.957917 | -0.016712 |
| 48000 | 5000 | 0.25 | 3375.000 | 0.67500 | 1.143205 | 0.131231 |
| 48000 | 5000 | 0.75 | 5375.000 | 1.07500 | 2.958044 | -0.127794 |
| 96000 | 1000 | 0.25 | 660.000 | 0.66000 | 1.143205 | 0.223918 |
| 96000 | 1000 | 0.75 | 1080.000 | 1.08000 | 2.957882 | -0.002758 |
| 96000 | 5000 | 0.25 | 3325.000 | 0.66500 | 1.143204 | 0.180705 |
| 96000 | 5000 | 0.75 | 5400.000 | 1.08000 | 2.958060 | -0.056934 |

[Lead-published scene-02 D5 FLACs and verified release digests](https://github.com/kalharbi11/wirescape-lab/pull/405#issuecomment-7140203754).

## Event-specific changes without bundled Golden differences

- S7.5 #291 merged `6daa23e`: [Golden 45525452045](https://github.com/kalharbi11/wirescape-lab/actions/runs/45525452045),
  27/27 identical on each platform. [Signed Result and D5](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7150495995):
  mode switch peak −26.094 → −38.443 dBFS (matches floor). Event capture is not a bundled change.
- S7.9 #444 merged `1be9da2`: [A65 review](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7151198161)
  and [D5 source pin](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7148992053).
  27/27 Golden identical per platform. ADSR drains residual over 5 ms; VCO CHOKE
  clears note identity but **continues sounding at Frequency** with continuous phase.
  A patch that needs silence uses its amplitude envelope / VCA, rather than assuming
  CHOKE itself mutes a free-running oscillator. Owner listening note, not a further DSP fix.
- S7.6 #449 merged `bae5e6786d7f859417c9d46295c0db3d8c412253`: final tested base
  `00c39f5cc1d747a75fd7dff264e8c87ef78ddb75`, head
  `ae8453ab25d3cf2eaf94a1fd2686ab65d1952868`.
  [Final signed Result](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7154605025)
  and [Architect approval](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7154706937).
  [Golden 45554717634](https://github.com/kalharbi11/wirescape-lab/actions/runs/45554717634)
  27/27 identical on each of Linux x64, Linux ARM64 and Windows; no bundled
  sound-change row. Actual switching is event-specific, with 10 ms transitions.

  Final [A27 capture 45558066878](https://github.com/kalharbi11/wirescape-lab/actions/runs/45558066878),
  archival tooling `d5a51c339a61e420fc0dbb158fc856cc66ef9c11` (#456, never merge).
  x64 artifact 14996109380, ZIP SHA-256
  `4684e71a3c22e12d19e588fa62cddc7f15bb1509ff5c945aa22553865ff62113`;
  ARM64 artifact 14996179062, ZIP SHA-256
  `6a7cf231bd6391acfbd8b113d84ebd4eb01c841c2a8303c6b1ad6ac1b87c63d8`.
  Independent B1 raw recomputation verified 57 member digests per arch,
  unchanged fixed windows, stimulus and one-sided r1.9a target validity.

  | Case | Governing floor | x64 excess dB | ARM64 excess dB | +0.1 dB bound |
  |---|---|---:|---:|---|
  | mode | valid target | +0.030468672 | +0.030465060 | met |
  | tone | valid target | +0.093162985 | +0.093143235 | met |
  | clocked division | old floor | -2.271050840 | -2.271074004 | met |

  Unclocked division remains `no_effect` on both arches; non-target time
  +0.0000389732/0 dB, below 1 dB. The tone worst-case margin is **0.0068 dB**
  (review L1), not headroom; any later Delay change touching tone must
  re-measure the row. L2: #520 must preserve the settled path's Golden identity.
  [D5 publication](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7152094695)
  and [release](https://github.com/kalharbi11/wirescape-lab/releases/tag/bench-2026-11-24):
  all six final x64 switched WAVs, paired patch JSON and scripts are
  byte-identical to historical capture 14986894295 (max sample delta 0 FS).
  The six published FLACs and fixed -3 dB conversion remain applicable;
  manifest pin remains historical, with final-pin equivalence in the Result.
  No duplicate capture or publication needed.

## Integrated rebuild and owner listening handoff

15 distinct bundled patches across the 18 stage rows above. Overlaps: scene-01
and scene-02 (Ladder then CHAOS), scene-06 (VCF then Ladder). Retain both stage rows;
do not sum dB or concatenate hashes across renderers. S7.6 adds no bundled row.
E7c-b #520 merged via #539 at `8c9bb10d9eb8acf616395404c26ed0c3964e19d2`.
[Accepted exact-head Golden 45572736238](https://github.com/kalharbi11/wirescape-lab/actions/runs/45572736238):
27/27 identical on each of Linux x64, Linux ARM64 and Windows; no additional
bundled-change row. [Architect approval](https://github.com/kalharbi11/wirescape-lab/pull/539#issuecomment-7157010908).

Integrated main-push [Lab 45576173843](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843)
passed. Linux x64 [OB-a1 artifact 15005210459](https://github.com/kalharbi11/wirescape-lab/actions/runs/45576173843/artifacts/15005210459),
downloaded ZIP SHA-256 `de2b2724054e616b6143cd9be1e9c8a7852f6a11c33fa032edf7921178660063`
matches GitHub metadata. The single member `patch_roundtrip.json` reports source
and checkout SHA both `8c9bb10d9eb8acf616395404c26ed0c3964e19d2`, event `push`,
renderer SHA-256 `66b6776dad5a10e83c63a7e9da5d243b600db15d4548d1f8510edb80c89f0e95`.
48 kHz, 48000 frames, block 128. Overall pass, 32 unique cases (24 bundled,
8 config shapes), all passing; 15/15 affected cases matched the checklist.
Negative control detected both document and render differences, with distinct
original and changed render hashes. All recorded digests are full SHA-256.
Round-trip hashes are the OB-a1 harness stimulus, not the 10-second Golden
fixture stimulus; no cross-harness equality is asserted.

Owner listening handoff (pending; owner only): listen at unchanged gain and
compare relevant per-stage D5/Golden source pairs. For each patch record
candidate SHA, observed differences, and disposition (accept / investigate).
The rebuild evidence is complete at the integrated source pin; listening
remains an independent owner action.

| OB-a1 case | Source bytes SHA-256 | Normalized document SHA-256 | Render SHA-256 | Rebuild | Owner disposition |
|---|---|---|---|---|---|
| `bundled/basics-02-fm-filter-lfo` | `984d169cac944fe2c45c92bdcd8948f35dd0f90f5439b064f179eb3e5c08cbfc` | `81eb75ac77bfe10eeb1029e7f15044f1539e6aaed31e7e9c92f3904542b0657b` | `38acad7c35cfa9a64890cc8afd224b593fae7eec67069e7f6396c52c247b5c39` | pass | pending |
| `bundled/basics-06-chaos-keys` | `b6f7d055d6ce44462a36ea2620c4b02bc12d74c9a805a0b7ea8acbc986f4dd72` | `d54f49d9158be2389e0045294ef8c77ef828e0d4849125f76ac333301c3fdd2e` | `bdc9b7388d0a90c4e75bcac4d4dab514c68b5329a876f8f11e16e83c59acd743` | pass | pending |
| `bundled/chaos-01-ember-veil-pad` | `903d22c6742b4803a91e630c69b6d14e03fde65aa1eb687cf1c5ac64469625e0` | `0f51e4b15df1905078816f23e9aa6c73d43d28aeb3c340e6960c24b5445c6509` | `02ec0de151d0d1681161b7553d1afa67e66bede544fde07ded2ce41bf48fd566` | pass | pending |
| `bundled/chaos-02-wireglass-lead` | `6a8c8e4e5b7c0e8cdbc36ce0fd37584548faa10008bb45d02d3eef3b879ac992` | `5195698f5696878d6afacd990335a75a2559f84375e0c0fedbc166a0977ce312` | `2d62a2838a991a858f604e8a466ee0dae9b3a95398940d9fdf20c8cd7effcf36` | pass | pending |
| `bundled/chaos-03-orbiting-iron-fx` | `b2f3fad43a0a6806694afe854d49f138f936d0599ad79ef2d6ac3e9c5624c695` | `29a4d66cab62907873b88037addb0622a37949da3d2eda20550aa3403e643bd4` | `3457fbbe4c061ea337acf767ad3c3d6d92952edc1634fdbbf2d8f4e5c467d557` | pass | pending |
| `bundled/chaos-04-radio-static-fx` | `09a4863b4512e7572ba36b49c45ae43c4412d4cf1b2fada1f52cda816e350af2` | `401c30be3b7285e4317563df8f2818453185cd42b65b36af8cdae37e5d2df271` | `8d31687da432fbc05bceef9f222478a27ef6cd239ab68f9b3fd8f7dcb2cf3d88` | pass | pending |
| `bundled/chaos-05-moonlit-drift-pad` | `30ed466ba1b208183879d44342322d8cbb37a18baa0a0d2b3930d45426527a58` | `435e1e48115e106c1a25015e9dcb1ef803cc7857aba01431077839482094df6f` | `7c92aeed3812716673d22aa2e9611722ceadc04af50e50dba219c42cfea76085` | pass | pending |
| `bundled/scene-01-hollow-chapel` | `fa9f83c3f6b20120902da733bb102a6326e59cd004342b3770a188c8adbe9287` | `1ab6328f8bf413393dd92dc6e888130a72e2c16326578f0a2f23caeb9f18157c` | `f223cb51910db082fb716f194e97d987b415b417062ecb1af30858a8b48975c8` | pass | pending |
| `bundled/scene-02-breathing-walls` | `370a33ea03ba4d8639ec2432c4bfcffa5581ff078b4b90a446345b697fdc767d` | `383ead6a7dd1dfad8559156d3fc315bd736bb46a5ef988a8d5a924107de89ce6` | `8594318ccf724fc6de0f9c48f7d2f2ce13fadb4b6cfe570996eb25a5a34401c3` | pass | pending |
| `bundled/scene-03-black-ice-choir` | `efc1e0352bcdd082cfa11a07f9106e40f0706e23270c974a65ed2804f00348a3` | `3df2bea569456262f3c91fdbc651202ae30c059e4af166d0c345e8a9edfc7f9e` | `f9da615491ade96a68b58b91ddd65eb6fca893bd2695136a56b551a23dd26b96` | pass | pending |
| `bundled/scene-04-vowel-apparitions` | `7d55d1e052b23b78088b2145dc7630aa4c9742810ef0ebb25d482bd3e6ef75c1` | `b8c4f8c840dcbbe025f151b94a1868c0a83f45eedadf825e8c55cbac57611a06` | `c854f21d05f511b25eea8d42b2712a932955723ba3a3b690f61ce6f2223772c9` | pass | pending |
| `bundled/scene-05-glass-cathedrals` | `15ad782ebdc78526b33f179923b74648d5b3f43cefe7eadcd9106f4b21ddf2cb` | `01462051d867ece0ce014ebc4a717046a7d20a4274e3b7dc1afdb2efd961f380` | `34396dab2aca6735a3cfa6d2de3bca9ef5526c5bdaa79c6010a47eaf19d7920e` | pass | pending |
| `bundled/scene-06-dust-reactor` | `910325886fb7d48f0c4f97640efdb90bab210bed0ed793676a7a4da94cfeda28` | `f5541a1bfbd83b145250d21e38ba77f92be594cd3ca4626746d9a5b2f6d9263e` | `44e9c2bdc1f08ab621f5b3a52e10337b67512a057b620abca5d0ff8fea62cd7e` | pass | pending |
| `bundled/scene-07-witching-hour` | `988f927303253110b1ccfb9db35fd8bae23784e7aabdc3ed2e4dc18a33ae7224` | `61871a60c942de29553b30ccbe4c1db0c7ee487e956ec5ea44e612228805e814` | `e16afc950d8620a416adc1983db8300a85b2c8b5d6e43f50703747b49d8d847d` | pass | pending |
| `bundled/scene-08-neon-elegy` | `f27d78f3b62e68c3af787374294789a47cd4497426cc7bb507fdfcd5057c978b` | `babf77efb1fce03cce03db5db9cd8607b928abc21c4e63ba0cb50b236008727d` | `9f2711951606e6d06793386e5f93d0bacf91f1b31a1f8ec4427c91bbf8213b65` | pass | pending |

Compare VCF level changes, Ladder resonance (including A53 peak caveat),
CHAOS spectral changes, and separately the event-specific D5 examples for
VCA mode, Delay mode/tone/division and ADSR/VCO CHOKE; these events do not
expand the bundled inventory.
No listening result is claimed. No change to patch JSON is justified by
these records alone.

Original stage ledger: gpt-builder4, 2026-11-24.
Final S7.6 and integrated OB-a1 audit/owner handoff: gpt-builder1, 2026-11-25.
