<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Rebuild versus previous engine (CMP-1)

## Subjects, provenance and coverage

- Previous engine as imported: upstream `44da1e4a235e606ebecd5bd6232f908d4df9b97f` (upstream main read 2026-11-25 ET; commit 2026-11-14 19:54:06 UTC); lab import `660556fbfb6ef30f828c68e9a05afa38ce0ee957`.
- Rebuild: lab main `73f411dd1010675967230ed535ad163d35ebaf24`. This is also the workflow SHA, not the later PR merge head.
- [Workflow run 45791608325](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325): both jobs succeeded; both native subjects built on each runner. Release, same job per architecture, no audio/MIDI devices or LAN. Hosted timings are diagnostics; no hardware or Pi extrapolation.
- Before/after and nested provenance match the dispatch pins. ZIP SHA-256 independently verified, and paired engine/module/patch timings independently matched against raw rows. Date: 2026-11-26 New York. Each table below inherits the full pins, run and CPU of the labelled architecture.
- Δ = after − before; × = after / before (rounded display). Absolute timing in ns/block unless specified. A missing row is not zero. Comparison across two historical subjects is distinct from the exact-head structural golden gate.

| Machine | CPU | Capture ET | Artifact / verified ZIP SHA-256 |
|---|---|---|---|
| linux-x64 | Intel(R) Xeon(R) 6975P-C | 2026-11-26T04:26:12.036910-05:00 | [15106255348](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325/artifacts/15106255348) `621d8e5e141430da15b6459a1d673f99a7466776c5f9f06669a37b0e08e5ac6f` |
| linux-arm64 | CPU implementer 0x41 / CPU part 0xd49 | 2026-11-26T04:25:27.944169-05:00 | [15104379390](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325/artifacts/15104379390) `c78dfd5471746727e1ea08ebf1cb5b558b3766e94c158a78c06db4de2a90a8df` |

The 33 original JSON members are retained byte-for-byte in `rebuild_vs_previous/linux-x64/` (17) and `rebuild_vs_previous/linux-arm64/` (16). Both archive SHA-256 values and all member SHA-256 values match `rebuild_vs_previous/raw-artifact-manifest.json`; the Architect verified the extracted and committed bytes, and B4 independently matched every committed Git blob SHA-1 to the corresponding original ZIP member. The adjacent `derived-comparison.json` is a transcription of the measured numeric rows, not a replacement for raw JSON. Log members are excluded. See PR #592 for exact-head CI and Result.

## 1. Engine: abi2_poly8

48 kHz, 256 frames; five repetitions, 4000 measured blocks. Mean is the median of repetition means. Method: both subjects use the original two-argument abi2_benchmark invocation; raw before/after-engine.json and paired-timing-summary.json.

| Machine | mean (ns/block) | p99 (ns/block) |
|---|---|---|
| linux-x64 | 66400.299 → 66205.29; Δ -195.009; ×0.9971 | 76694 → 75376; Δ -1318; ×0.9828 |
| linux-arm64 | 73500.71 → 72567.67; Δ -933.04; ×0.9873 | 77378 → 75131; Δ -2247; ×0.9710 |

## 2. Bundled patch cost

Original import fixture bytes on both subjects (24 common filenames); wirescape_soak, 48 kHz/128, 30 seconds. No keyboard-input substitution. Period = 2,666,666.667 ns. Both subjects measured 12/24 on each architecture, so the maximum p99 for the full inventory is unmeasured. The maximum among measured rows is scene-05-glass-cathedrals.json on each subject and architecture. Source: patch-cost.json and paired-timing-summary.json.

### linux-x64: patch cost (ns/block)

| Patch | Median | p99 | Worst | p99 % of period (before → after) | Worst % of period (before → after) |
|---|---|---|---|---|---|
| basics-04-sequencer-and-quantizer.json | 29573 → 30714; Δ 1141; ×1.0386 | 34645 → 36368; Δ 1723; ×1.0497 | 54290 → 62890; Δ 8600; ×1.1584 | 1.299 → 1.364 | 2.036 → 2.358 |
| basics-05-random-melody.json | 45662.5 → 49012; Δ 3349.5; ×1.0734 | 53190 → 69584; Δ 16394; ×1.3082 | 89835 → 82243; Δ -7592; ×0.9155 | 1.995 → 2.609 | 3.369 → 3.084 |
| basics-08-clocked-groove.json | 29018 → 27912; Δ -1106; ×0.9619 | 34415 → 33066; Δ -1349; ×0.9608 | 55225 → 61414; Δ 6189; ×1.1121 | 1.291 → 1.240 | 2.071 → 2.303 |
| chaos-03-orbiting-iron-fx.json | 61195 → 64491.5; Δ 3296.5; ×1.0539 | 66914 → 71149; Δ 4235; ×1.0633 | 94964 → 125443; Δ 30479; ×1.3210 | 2.509 → 2.668 | 3.561 → 4.704 |
| chaos-04-radio-static-fx.json | 57082 → 59003.5; Δ 1921.5; ×1.0337 | 81126 → 75477; Δ -5649; ×0.9304 | 97684 → 105956; Δ 8272; ×1.0847 | 3.042 → 2.830 | 3.663 → 3.973 |
| quad-vca-02-four-gate-mix.json | 20167 → 20267.5; Δ 100.5; ×1.0050 | 39587 → 25778; Δ -13809; ×0.6512 | 51508 → 72795; Δ 21287; ×1.4133 | 1.485 → 0.967 | 1.932 → 2.730 |
| scene-01-hollow-chapel.json | 90611.5 → 98219.5; Δ 7608; ×1.0840 | 106510 → 118667; Δ 12157; ×1.1141 | 146949 → 157025; Δ 10076; ×1.0686 | 3.994 → 4.450 | 5.511 → 5.888 |
| scene-02-breathing-walls.json | 78346 → 83732; Δ 5386; ×1.0687 | 85792 → 92561; Δ 6769; ×1.0789 | 122119 → 142886; Δ 20767; ×1.1701 | 3.217 → 3.471 | 4.579 → 5.358 |
| scene-05-glass-cathedrals.json | 104706 → 107537; Δ 2831; ×1.0270 | 134082 → 133004; Δ -1078; ×0.9920 | 152096 → 172492; Δ 20396; ×1.1341 | 5.028 → 4.988 | 5.704 → 6.468 |
| scene-06-dust-reactor.json | 69781.5 → 72932; Δ 3150.5; ×1.0451 | 89059 → 99036; Δ 9977; ×1.1120 | 105458 → 153147; Δ 47689; ×1.4522 | 3.340 → 3.714 | 3.955 → 5.743 |
| scene-07-witching-hour.json | 61110.5 → 61632; Δ 521.5; ×1.0085 | 70238 → 71660; Δ 1422; ×1.0202 | 99458 → 99438; Δ -20; ×0.9998 | 2.634 → 2.687 | 3.730 → 3.729 |
| scene-08-neon-elegy.json | 69109 → 74745; Δ 5636; ×1.0816 | 80525 → 97978; Δ 17453; ×1.2167 | 116614 → 115840; Δ -774; ×0.9934 | 3.020 → 3.674 | 4.373 → 4.344 |

### linux-arm64: patch cost (ns/block)

| Patch | Median | p99 | Worst | p99 % of period (before → after) | Worst % of period (before → after) |
|---|---|---|---|---|---|
| basics-04-sequencer-and-quantizer.json | 21457 → 21808; Δ 351; ×1.0164 | 30889 → 32865; Δ 1976; ×1.0640 | 73210 → 69898; Δ -3312; ×0.9548 | 1.158 → 1.232 | 2.745 → 2.621 |
| basics-05-random-melody.json | 33577 → 34081; Δ 504; ×1.0150 | 44121 → 44090; Δ -31; ×0.9993 | 87610 → 75970; Δ -11640; ×0.8671 | 1.655 → 1.653 | 3.285 → 2.849 |
| basics-08-clocked-groove.json | 19041 → 20345; Δ 1304; ×1.0685 | 28009 → 29617; Δ 1608; ×1.0574 | 82836 → 66450; Δ -16386; ×0.8022 | 1.050 → 1.111 | 3.106 → 2.492 |
| chaos-03-orbiting-iron-fx.json | 52958 → 54718; Δ 1760; ×1.0332 | 64050 → 66394; Δ 2344; ×1.0366 | 147461 → 91811; Δ -55650; ×0.6226 | 2.402 → 2.490 | 5.530 → 3.443 |
| chaos-04-radio-static-fx.json | 45938 → 47466; Δ 1528; ×1.0333 | 58746 → 59394; Δ 648; ×1.0110 | 80738 → 86483; Δ 5745; ×1.0712 | 2.203 → 2.227 | 3.028 → 3.243 |
| quad-vca-02-four-gate-mix.json | 15840 → 15656; Δ -184; ×0.9884 | 21241 → 21481; Δ 240; ×1.0113 | 37545 → 42393; Δ 4848; ×1.1291 | 0.797 → 0.806 | 1.408 → 1.590 |
| scene-01-hollow-chapel.json | 87859 → 98923; Δ 11064; ×1.1259 | 99371 → 114977; Δ 15606; ×1.1570 | 123588 → 159078; Δ 35490; ×1.2872 | 3.726 → 4.312 | 4.635 → 5.965 |
| scene-02-breathing-walls.json | 67754 → 75978; Δ 8224; ×1.1214 | 85011 → 88795; Δ 3784; ×1.0445 | 109651 → 150437; Δ 40786; ×1.3720 | 3.188 → 3.330 | 4.112 → 5.641 |
| scene-05-glass-cathedrals.json | 107131 → 117554; Δ 10423; ×1.0973 | 117811 → 126590; Δ 8779; ×1.0745 | 206486 → 192302; Δ -14184; ×0.9313 | 4.418 → 4.747 | 7.743 → 7.211 |
| scene-06-dust-reactor.json | 53738 → 59530; Δ 5792; ×1.1078 | 70506 → 73875; Δ 3369; ×1.0478 | 98947 → 117317; Δ 18370; ×1.1857 | 2.644 → 2.770 | 3.711 → 4.399 |
| scene-07-witching-hour.json | 44321 → 44697; Δ 376; ×1.0085 | 56706 → 57330; Δ 624; ×1.0110 | 90531 → 98195; Δ 7664; ×1.0847 | 2.126 → 2.150 | 3.395 → 3.682 |
| scene-08-neon-elegy.json | 48769 → 51962; Δ 3193; ×1.0655 | 67442 → 63954; Δ -3488; ×0.9483 | 110739 → 98699; Δ -12040; ×0.8913 | 2.529 → 2.398 | 4.153 → 3.701 |

Both architectures, both subjects — unmeasured: `wirescape_soak: graph setup/render failed` (exit 1), original fixture retained:

- basics-01-first-tone.json
- basics-02-fm-filter-lfo.json
- basics-03-echo-and-reverb.json
- basics-06-chaos-keys.json
- basics-07-macro-keys.json
- chaos-01-ember-veil-pad.json
- chaos-02-wireglass-lead.json
- chaos-05-moonlit-drift-pad.json
- osc-out-01.json
- quad-vca-01-lpg-plucks.json
- scene-03-black-ice-choir.json
- scene-04-vowel-apparitions.json

## 3. Module CPU

Method: abi2_module_cpu_probe, two instances, 48 kHz/128, 2 seconds, one and eight channels. Common 34 catalogue IDs; 66/68 paired rows measured on each runner. Chord (both channel counts) unmeasured: create/prepare failed (exit 2), no substitute workload. The three head-only modules are not paired. Source: module-cpu.json and paired-timing-summary.json.

### linux-x64: module CPU (ns/block)

| Module ID | 1ch p99 | 1ch worst | 8ch p99 | 8ch worst |
|---|---|---|---|---|
| essentials.adsr | 1129 → 1230; Δ 101; ×1.0895 | 12823 → 13423; Δ 600; ×1.0468 | 13168 → 12099; Δ -1069; ×0.9188 | 46077 → 27054; Δ -19023; ×0.5871 |
| essentials.chaos_lite | 41752 → 44936; Δ 3184; ×1.0763 | 50875 → 58103; Δ 7228; ×1.1421 | 268318 → 292444; Δ 24126; ×1.0899 | 297584 → 319922; Δ 22338; ×1.0751 |
| essentials.chord | unmeasured | unmeasured | unmeasured | unmeasured |
| essentials.clock | 2576 → 2179; Δ -397; ×0.8459 | 33583 → 8783; Δ -24800; ×0.2615 | 24379 → 25840; Δ 1461; ×1.0599 | 46641 → 53966; Δ 7325; ×1.1571 |
| essentials.function_envelope | 1995 → 2055; Δ 60; ×1.0301 | 14976 → 5828; Δ -9148; ×0.3892 | 17918 → 22010; Δ 4092; ×1.2284 | 35789 → 38217; Δ 2428; ×1.0678 |
| essentials.ladder | 8374 → 6980; Δ -1394; ×0.8335 | 20877 → 41951; Δ 21074; ×2.0094 | 51567 → 62881; Δ 11314; ×1.2194 | 66285 → 67049; Δ 764; ×1.0115 |
| essentials.lfo | 5258 → 4730; Δ -528; ×0.8996 | 19705 → 28160; Δ 8455; ×1.4291 | 40022 → 39314; Δ -708; ×0.9823 | 54534 → 683737; Δ 629203; ×12.5378 |
| essentials.mixer | 1986 → 1627; Δ -359; ×0.8192 | 17379 → 14819; Δ -2560; ×0.8527 | 19854 → 16688; Δ -3166; ×0.8405 | 32184 → 21713; Δ -10471; ×0.6747 |
| essentials.noise | 817 → 775; Δ -42; ×0.9486 | 7674 → 17505; Δ 9831; ×2.2811 | 6977 → 6849; Δ -128; ×0.9817 | 19373 → 27164; Δ 7791; ×1.4022 |
| essentials.notes_to_cv | 3049 → 2614; Δ -435; ×0.8573 | 11231 → 18129; Δ 6898; ×1.6142 | 4010 → 3650; Δ -360; ×0.9102 | 30240 → 14605; Δ -15635; ×0.4830 |
| essentials.output | 488 → 558; Δ 70; ×1.1434 | 2732 → 5603; Δ 2871; ×2.0509 | 3477 → 4207; Δ 730; ×1.2100 | 18105 → 30349; Δ 12244; ×1.6763 |
| essentials.quad_vca | 4149 → 4582; Δ 433; ×1.1044 | 12515 → 25948; Δ 13433; ×2.0734 | 39378 → 35805; Δ -3573; ×0.9093 | 56663 → 44555; Δ -12108; ×0.7863 |
| essentials.quantizer | 1405 → 1143; Δ -262; ×0.8135 | 9643 → 9952; Δ 309; ×1.0320 | 9091 → 14506; Δ 5415; ×1.5956 | 21079 → 39842; Δ 18763; ×1.8901 |
| essentials.resonator | 22160 → 22447; Δ 287; ×1.0130 | 30588 → 26888; Δ -3700; ×0.8790 | 122999 → 122504; Δ -495; ×0.9960 | 144319 → 136522; Δ -7797; ×0.9460 |
| essentials.scale_offset | 1242 → 1802; Δ 560; ×1.4509 | 15683 → 8199; Δ -7484; ×0.5228 | 13744 → 17076; Δ 3332; ×1.2424 | 28933 → 22024; Δ -6909; ×0.7612 |
| essentials.slew | 1781 → 2589; Δ 808; ×1.4537 | 12799 → 20292; Δ 7493; ×1.5854 | 17552 → 18879; Δ 1327; ×1.0756 | 25500 → 25749; Δ 249; ×1.0098 |
| essentials.vca | 200 → 186; Δ -14; ×0.9300 | 3943 → 3867; Δ -76; ×0.9807 | 969 → 1073; Δ 104; ×1.1073 | 4866 → 24561; Δ 19695; ×5.0475 |
| essentials.vcf | 9781 → 5473; Δ -4308; ×0.5596 | 18898 → 16689; Δ -2209; ×0.8831 | 50038 → 51314; Δ 1276; ×1.0255 | 65135 → 61094; Δ -4041; ×0.9380 |
| essentials.vco | 10991 → 11062; Δ 71; ×1.0065 | 27128 → 18947; Δ -8181; ×0.6984 | 63356 → 61993; Δ -1363; ×0.9785 | 73679 → 76014; Δ 2335; ×1.0317 |
| example.random_source | 1891 → 1898; Δ 7; ×1.0037 | 13144 → 12495; Δ -649; ×0.9506 | 1893 → 1883; Δ -10; ×0.9947 | 12447 → 12136; Δ -311; ×0.9750 |
| example.step_sequencer | 1717 → 1755; Δ 38; ×1.0221 | 6530 → 8713; Δ 2183; ×1.3343 | 2170 → 2180; Δ 10; ×1.0046 | 16243 → 18862; Δ 2619; ×1.1612 |
| fx.delay | 5194 → 4258; Δ -936; ×0.8198 | 19650 → 29526; Δ 9876; ×1.5026 | 4324 → 5894; Δ 1570; ×1.3631 | 16356 → 24141; Δ 7785; ×1.4760 |
| fx.reverb | 34680 → 34915; Δ 235; ×1.0068 | 54581 → 50073; Δ -4508; ×0.9174 | 34663 → 32547; Δ -2116; ×0.9390 | 49747 → 49201; Δ -546; ×0.9890 |
| host.keyboard | 15337 → 11145; Δ -4192; ×0.7267 | 19216 → 16593; Δ -2623; ×0.8635 | 10960 → 9331; Δ -1629; ×0.8514 | 19461 → 17355; Δ -2106; ×0.8918 |
| midi.cc_to_cv | 19767 → 20654; Δ 887; ×1.0449 | 31744 → 37266; Δ 5522; ×1.1740 | 19556 → 19664; Δ 108; ×1.0055 | 29140 → 36896; Δ 7756; ×1.2662 |
| midi.in | 75 → 90; Δ 15; ×1.2000 | 4008 → 16201; Δ 12193; ×4.0422 | 69 → 79; Δ 10; ×1.1449 | 5123 → 3310; Δ -1813; ×0.6461 |
| midi.to_cv | 9917 → 4402; Δ -5515; ×0.4439 | 18946 → 14320; Δ -4626; ×0.7558 | 7553 → 5624; Δ -1929; ×0.7446 | 18126 → 14687; Δ -3439; ×0.8103 |
| monitor | 206 → 212; Δ 6; ×1.0291 | 3437 → 4089; Δ 652; ×1.1897 | 204 → 198; Δ -6; ×0.9706 | 1127 → 892; Δ -235; ×0.7915 |
| osc.in | 22703 → 22525; Δ -178; ×0.9922 | 40611 → 46989; Δ 6378; ×1.1571 | 21773 → 22273; Δ 500; ×1.0230 | 25993 → 50054; Δ 24061; ×1.9257 |
| osc.out | 197 → 151; Δ -46; ×0.7665 | 706 → 800; Δ 94; ×1.1331 | 204 → 153; Δ -51; ×0.7500 | 585 → 551; Δ -34; ×0.9419 |
| ports.macro_oscillator | 23815 → 23756; Δ -59; ×0.9975 | 31014 → 28861; Δ -2153; ×0.9306 | 161684 → 160624; Δ -1060; ×0.9934 | 176171 → 179226; Δ 3055; ×1.0173 |
| sequencing.groove | 18147 → 18375; Δ 228; ×1.0126 | 26500 → 28274; Δ 1774; ×1.0669 | 16978 → 17102; Δ 124; ×1.0073 | 33105 → 23911; Δ -9194; ×0.7223 |
| sound.blend | 4261 → 5693; Δ 1432; ×1.3361 | 45996 → 21002; Δ -24994; ×0.4566 | 5614 → 5986; Δ 372; ×1.0663 | 24153 → 14145; Δ -10008; ×0.5856 |
| sound.spectral | 121723 → 125139; Δ 3416; ×1.0281 | 133733 → 143278; Δ 9545; ×1.0714 | 122030 → 122007; Δ -23; ×0.9998 | 134977 → 129757; Δ -5220; ×0.9613 |

### linux-arm64: module CPU (ns/block)

| Module ID | 1ch p99 | 1ch worst | 8ch p99 | 8ch worst |
|---|---|---|---|---|
| essentials.adsr | 1344 → 1281; Δ -63; ×0.9531 | 16705 → 18177; Δ 1472; ×1.0881 | 10632 → 9344; Δ -1288; ×0.8789 | 20641 → 16400; Δ -4241; ×0.7945 |
| essentials.chaos_lite | 46921 → 49482; Δ 2561; ×1.0546 | 63234 → 70706; Δ 7472; ×1.1182 | 340419 → 363612; Δ 23193; ×1.0681 | 371228 → 379684; Δ 8456; ×1.0228 |
| essentials.chord | unmeasured | unmeasured | unmeasured | unmeasured |
| essentials.clock | 2337 → 2456; Δ 119; ×1.0509 | 32177 → 15585; Δ -16592; ×0.4844 | 19841 → 22953; Δ 3112; ×1.1568 | 45578 → 32433; Δ -13145; ×0.7116 |
| essentials.function_envelope | 1753 → 1784; Δ 31; ×1.0177 | 27929 → 19289; Δ -8640; ×0.6906 | 15305 → 16641; Δ 1336; ×1.0873 | 43849 → 35505; Δ -8344; ×0.8097 |
| essentials.ladder | 7137 → 7160; Δ 23; ×1.0032 | 25705 → 23977; Δ -1728; ×0.9328 | 62306 → 64058; Δ 1752; ×1.0281 | 101299 → 94859; Δ -6440; ×0.9364 |
| essentials.lfo | 5656 → 5504; Δ -152; ×0.9731 | 16977 → 25849; Δ 8872; ×1.5226 | 46529 → 44434; Δ -2095; ×0.9550 | 71915 → 60137; Δ -11778; ×0.8362 |
| essentials.mixer | 1656 → 1584; Δ -72; ×0.9565 | 8368 → 16256; Δ 7888; ×1.9426 | 14936 → 15425; Δ 489; ×1.0327 | 33858 → 29537; Δ -4321; ×0.8724 |
| essentials.noise | 776 → 776; Δ 0; ×1.0000 | 29217 → 12072; Δ -17145; ×0.4132 | 5752 → 5736; Δ -16; ×0.9972 | 44106 → 24153; Δ -19953; ×0.5476 |
| essentials.notes_to_cv | 4752 → 4744; Δ -8; ×0.9983 | 21377 → 42666; Δ 21289; ×1.9959 | 4760 → 4760; Δ 0; ×1.0000 | 22040 → 55802; Δ 33762; ×2.5319 |
| essentials.output | 616 → 616; Δ 0; ×1.0000 | 9736 → 17785; Δ 8049; ×1.8267 | 4416 → 4408; Δ -8; ×0.9982 | 31113 → 19305; Δ -11808; ×0.6205 |
| essentials.quad_vca | 4792 → 3736; Δ -1056; ×0.7796 | 189966 → 18313; Δ -171653; ×0.0964 | 38874 → 30737; Δ -8137; ×0.7907 | 66898 → 57418; Δ -9480; ×0.8583 |
| essentials.quantizer | 960 → 976; Δ 16; ×1.0167 | 7520 → 16721; Δ 9201; ×2.2235 | 6184 → 6105; Δ -79; ×0.9872 | 19593 → 48818; Δ 29225; ×2.4916 |
| essentials.resonator | 18376 → 19272; Δ 896; ×1.0488 | 43770 → 35281; Δ -8489; ×0.8061 | 135108 → 136725; Δ 1617; ×1.0120 | 140117 → 154021; Δ 13904; ×1.0992 |
| essentials.scale_offset | 1432 → 1416; Δ -16; ×0.9888 | 23761 → 22401; Δ -1360; ×0.9428 | 13224 → 12489; Δ -735; ×0.9444 | 40737 → 21681; Δ -19056; ×0.5322 |
| essentials.slew | 1896 → 1904; Δ 8; ×1.0042 | 3216 → 20401; Δ 17185; ×6.3436 | 18345 → 17440; Δ -905; ×0.9507 | 37001 → 41041; Δ 4040; ×1.1092 |
| essentials.vca | 200 → 216; Δ 16; ×1.0800 | 1840 → 20505; Δ 18665; ×11.1440 | 928 → 952; Δ 24; ×1.0259 | 2488 → 43714; Δ 41226; ×17.5699 |
| essentials.vcf | 5176 → 5169; Δ -7; ×0.9986 | 34817 → 21152; Δ -13665; ×0.6075 | 43954 → 48089; Δ 4135; ×1.0941 | 62962 → 62746; Δ -216; ×0.9966 |
| essentials.vco | 10960 → 12457; Δ 1497; ×1.1366 | 24081 → 47913; Δ 23832; ×1.9897 | 79586 → 79618; Δ 32; ×1.0004 | 99427 → 84571; Δ -14856; ×0.8506 |
| example.random_source | 1521 → 1505; Δ -16; ×0.9895 | 70090 → 15528; Δ -54562; ×0.2215 | 1513 → 1512; Δ -1; ×0.9993 | 13161 → 24121; Δ 10960; ×1.8328 |
| example.step_sequencer | 1792 → 1784; Δ -8; ×0.9955 | 4968 → 16649; Δ 11681; ×3.3512 | 1816 → 1792; Δ -24; ×0.9868 | 19417 → 41601; Δ 22184; ×2.1425 |
| fx.delay | 5192 → 5320; Δ 128; ×1.0247 | 15376 → 34089; Δ 18713; ×2.2170 | 5240 → 5248; Δ 8; ×1.0015 | 29481 → 54202; Δ 24721; ×1.8385 |
| fx.reverb | 36081 → 34745; Δ -1336; ×0.9630 | 76987 → 46881; Δ -30106; ×0.6089 | 33169 → 34401; Δ 1232; ×1.0371 | 44714 → 48858; Δ 4144; ×1.0927 |
| host.keyboard | 13505 → 8497; Δ -5008; ×0.6292 | 23753 → 27425; Δ 3672; ×1.1546 | 15281 → 10929; Δ -4352; ×0.7152 | 53986 → 26729; Δ -27257; ×0.4951 |
| midi.cc_to_cv | 12753 → 12649; Δ -104; ×0.9918 | 34769 → 22312; Δ -12457; ×0.6417 | 12448 → 12473; Δ 25; ×1.0020 | 35929 → 24809; Δ -11120; ×0.6905 |
| midi.in | 80 → 88; Δ 8; ×1.1000 | 10400 → 11073; Δ 673; ×1.0647 | 80 → 81; Δ 1; ×1.0125 | 11120 → 9233; Δ -1887; ×0.8303 |
| midi.to_cv | 12153 → 4688; Δ -7465; ×0.3857 | 52178 → 25801; Δ -26377; ×0.4945 | 9929 → 4600; Δ -5329; ×0.4633 | 60434 → 23056; Δ -37378; ×0.3815 |
| monitor | 224 → 208; Δ -16; ×0.9286 | 11168 → 2144; Δ -9024; ×0.1920 | 224 → 200; Δ -24; ×0.8929 | 1976 → 1752; Δ -224; ×0.8866 |
| osc.in | 12665 → 12937; Δ 272; ×1.0215 | 25881 → 20656; Δ -5225; ×0.7981 | 12440 → 12672; Δ 232; ×1.0186 | 101555 → 53274; Δ -48281; ×0.5246 |
| osc.out | 201 → 201; Δ 0; ×1.0000 | 1088 → 1000; Δ -88; ×0.9191 | 208 → 208; Δ 0; ×1.0000 | 736 → 1120; Δ 384; ×1.5217 |
| ports.macro_oscillator | 23281 → 23201; Δ -80; ×0.9966 | 43114 → 34337; Δ -8777; ×0.7964 | 177406 → 182702; Δ 5296; ×1.0299 | 192214 → 205670; Δ 13456; ×1.0700 |
| sequencing.groove | 16241 → 17289; Δ 1048; ×1.0645 | 56882 → 23913; Δ -32969; ×0.4204 | 15456 → 16241; Δ 785; ×1.0508 | 37929 → 33089; Δ -4840; ×0.8724 |
| sound.blend | 4353 → 4408; Δ 55; ×1.0126 | 21712 → 27537; Δ 5825; ×1.2683 | 4352 → 4385; Δ 33; ×1.0076 | 17497 → 19072; Δ 1575; ×1.0900 |
| sound.spectral | 153005 → 154069; Δ 1064; ×1.0070 | 180142 → 160997; Δ -19145; ×0.8937 | 152525 → 155669; Δ 3144; ×1.0206 | 164205 → 180262; Δ 16057; ×1.0978 |

## 4. Edit continuity (historical CN evidence, not paired)

Previous engine: unmeasured; the source grep found no `--capture-null-sink` in native, so the unchanged capture harness could not run. Source: continuity-source.json. After pin: unmeasured in this dispatch. Separate [M4 CN A2 ledger at ff206709b60cb26a34626c2ab38b1d864e59e4fb](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md) contains the edit-class witnesses and actual tested source/CPU/run pins:

- E4b subject `8e8783b0602660d964892f9fe66e0cfe310dc009`, [run 45461091924](https://github.com/kalharbi11/wirescape-lab/actions/runs/45461091924), Intel Xeon Platinum 8573C, 2026-11-24, 48 kHz/256: 19 edit classes accepted 3/3 each; 282/282 unaffected comparisons sample-identical; applicable tone/tail/held-note newly silent time 0 ms, clock slip 0, except intentionally affected held-note witness excluded. See ledger's per-edit and restart witnesses; no aggregate restart count inferred from identical samples.
- Final Delay-inclusive subject `8c9bb10d9eb8acf616395404c26ed0c3964e19d2`, [capture run 45578581477](https://github.com/kalharbi11/wirescape-lab/actions/runs/45578581477), Linux x64 48 kHz/256, 2026-11-25: smaller 15/15 full-window exact; larger 18/18 post-bracket seconds exact, 15/18 full windows differ; disturbed span 479 frames (9.9791667 ms), newly silent at most one sample (0.0208333 ms), clock exact, tail and held sounding. A83's bounded acceptance disposition is historical; not a measurement of `73f411dd1010675967230ed535ad163d35ebaf24`. No paired restart-count or silence delta.

## 5. Core module ID string references

Method: literal quoted catalogue ID occurrence census, C/C++ extensions, excluding paths with a `tests` component. Before scope native/engine2, native/control, native/document, native/sidecar, native/io; after scope engine and host. Both runner artifacts agree. Static occurrence counts (including literals in declarations or repeated references), not a semantic count of branches or module-specific behavior; source lists retained in before/after-core-id-matches.json. Scope follows the mapped core source sets; not an all-Studio search.

| Metric | Before | After | Delta | Ratio |
|---|---:|---:|---:|---:|
| Quoted ID occurrences | 110 | 169 | 59 | 1.5364 |

## 6. External SDK build

Both architectures, both pins: isolated template prepare completed; CMake configure exit 1, build not reached. Error: `Cannot find source file: ../../tests/native/abi2/allocation_watch.cpp`. Actual external module build capability unmeasured: comparison collector omitted that test dependency in the temporary tree. Source external-sdk.json; not evidence of an SDK product regression. No product changes.

## 7. Cortex-M7 compile inventory

Linux x64 host only; Arm GNU 14.2.Rel1 (Build arm-14.52), 14.2.1 20241119, archive SHA-256 `62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823`. Same portability compile flags, subject-specific include paths and pinned macro source. Count includes SDK template (not a catalogue entry). Source portability.json.

| FPU | Previous successes/attempts | Rebuild successes/attempts | Delta successes | Ratio |
|---|---:|---:|---:|---:|
| fpv5-d16 | 35/35 | 38/38 | 3 | 1.0857 |
| fpv5-sp-d16 | 35/35 | 38/38 | 3 | 1.0857 |
| Total | 70/70 | 76/76 | 6 | 1.0857 |

ARM64 host: unmeasured; no toolchain archive configured.

## 8. UI cable drag at 200 modules

Same current ui_frames.cjs harness on both subjects, Chromium rAF intervals during Playwright mouse drags. Raw ui-frames.json. ARM CPU model recorded as implementer/part by native provenance, UI reports unknown CPU.

| Machine | p95 ms |
|---|---|
| linux-x64 | 83.3 → 66.6; Δ -16.7; ×0.7995 |
| linux-arm64 | 50 → 66.7; Δ 16.7; ×1.3340 |

## 9. Golden render availability

Both architectures: all 24 original fixture SHA-256 values match across subjects; 24/24 rendered at each pin and 24/24 repeated renders sample-identical within each subject. Across subjects 6/24 PCM hashes match (18 differ) on each architecture. This is not the Gate Delay golden check. Current collector at `73f411dd1010675967230ed535ad163d35ebaf24` used unchanged against both builds. Source before/after-golden.json.

The six matching fixture names on both architectures:
- basics-01-first-tone.json
- basics-04-sequencer-and-quantizer.json
- basics-08-clocked-groove.json
- osc-out-01.json
- quad-vca-01-lpg-plucks.json
- quad-vca-02-four-gate-mix.json

## 10. Native binary size

File bytes of wirescape-engine; sum of size -A .text / .text.* for module shared libraries in build/native; excluded test/guide/sdk prefixed libraries. Before 34 catalogue libraries, after 37; common-library sum is separately shown for 34. New libraries cv_to_notes, poly_merge, poly_split. Source before/after-binary-size.json. Unit: bytes.

| Machine | Metric | Before → after; Δ; × |
|---|---|---|
| linux-x64 | Engine file bytes | 2488768 → 2857120; Δ 368352; ×1.1480 |
| linux-x64 | Engine .text | 1543549 → 1827382; Δ 283833; ×1.1839 |
| linux-x64 | All catalogue library .text | 586099 → 736452; Δ 150353; ×1.2565 |
| linux-x64 | Common 34 library .text | 586099 → 722937; Δ 136838; ×1.2335 |
| linux-arm64 | Engine file bytes | 2348176 → 2661272; Δ 313096; ×1.1333 |
| linux-arm64 | Engine .text | 1307184 → 1523104; Δ 215920; ×1.1652 |
| linux-arm64 | All catalogue library .text | 473644 → 599224; Δ 125580; ×1.2651 |
| linux-arm64 | Common 34 library .text | 473644 → 585592; Δ 111948; ×1.2364 |

Signed: gpt-builder4, 2026-11-26.
