<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-d bundled-patch sound-change ledger (draft)

2026-11-24 ET. OB r2.9, M7 r1.9a. This is a per-stage record, not a cumulative
OB0→OB1 measurement or owner listening result. Final S7.6 and candidate rebuild
remain pending. No preset edits in this draft. OB0 was accepted at
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
Non-gating r=.25/.75 peak ratios: [#498 / #499](https://github.com/kalharbi11/wirescape-lab/pull/499)
requests the original descriptor impulse and whole-spectrum scan with additional
reported rows, no new threshold. Actual output pending; do not infer it from
r=.5/.9 or the analytic formula.
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
- S7.6 #449: open, evidence base `7661f832f44c2f8388b84b48e766490e1e44418f`,
  subject `4fcaa04abaa8ecd5018f55b98e3c76f5d6e0045d`, [B4 raw Result](https://github.com/kalharbi11/wirescape-lab/pull/456#issuecomment-7151834512).
  x64/ARM64 tone +0.093163/+0.093149 dB over a valid steady target; clocked
  division −2.271051/−2.271145 dB below old floor; unclocked `no_effect`.
  [A64 r1.9a ruling](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7151869667)
  corrects target validity to a one-sided check. Mode fixed-window target is
  −0.302848/−0.302834 dB relative to the last-12k peak, therefore valid;
  governing endpoint excess +0.030469/+0.030424 dB meets the bound.
  [B4 reclassification of preserved raw](https://github.com/kalharbi11/wirescape-lab/pull/456#issuecomment-7151886320):
  all three numeric rows meet; no rerender or changed stimulus. This is not
  final PR acceptance. Record final Golden scope and D5 after B1's final gates
  and Architect review; do not assume unchanged.

## Rebuild and owner listening (pending)

15 distinct bundled patches across the 18 stage rows above. Overlaps: scene-01
and scene-02 (Ladder then CHAOS), scene-06 (VCF then Ladder). Retain both stage rows;
do not sum dB or concatenate hashes across renderers. Collect final S7.6 rows,
check all relevant S7.x scope and rebuild each affected bundled patch at the final
main source pin. The existing Lab native Linux x64 OB-a1 job invokes `tools/patch_roundtrip.py`
with the actual checkout SHA and archives `ob-a1-roundtrip-linux-x64-*` containing
source bytes, normalized document and render hashes plus pass/fail per case.
Use the final integrated candidate's report (source and renderer SHA verified),
not the current docs-only Lab green or a historical source pin. Match all 15
unique changed names and any additional final S7.6 rows to passing cases;
report a missing or failing case explicitly and retain original patch values
unless a scoped rebuild correction is justified. Round-trip hashes use that
harness's stimulus, not the 10-second Golden fixture stimulus.

Owner listening handoff: the union is basics-02, basics-06, chaos-01 through
chaos-05, and scene-01 through scene-08 (each exact name above). Listen at
unchanged gain and compare the relevant per-stage D5/Golden source pairs;
record patch name, candidate SHA, observed differences, and owner disposition.
The candidate rebuild and owner listen are separate records. No listening result
or rebuild claim yet. No change to patch JSON is justified by these records alone.

Signed: gpt-builder4, 2026-11-24
