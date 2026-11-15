<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Extracted parameter reference

All 37 retained controls; these are prototype units and ranges, before any native-unit conversion. Tuple order in source is [default, minimum, maximum]. Continuous controls remain externally settable; this prototype is control-block driven, not a sample-rate modulation API.

| ID | Default | Minimum | Maximum |
|---|---:|---:|---:|
| pressure | 0.5 | 0 | 1 |
| breath | 0.12 | 0 | 1 |
| whisper | 0 | 0 | 1 |
| jitter | 0.3 | 0 | 5 |
| shimmer | 2.5 | 0 | 20 |
| tremor | 6 | 0 | 60 |
| wander | 4 | 0 | 40 |
| vibrato | 0 | 0 | 80 |
| growl | 0 | 0 | 1 |
| creak | 0 | 0 | 1 |
| tailFry | 0 | 0 | 1 |
| flutter | 0 | 0 | 1 |
| rasp | 0 | 0 | 1 |
| breaks | 0 | 0 | 1 |
| size | 17.5 | 13 | 20.5 |
| pharynx | 0 | 0 | 1 |
| mouth | 0.5 | 0 | 1 |
| ring | 0.3 | 0 | 1 |
| vowel | 0.5 | 0 | 1 |
| style | 0.45 | 0 | 1 |
| attack | 60 | 3 | 1200 |
| release | 220 | 20 | 2500 |
| glide | 60 | 0 | 600 |
| throats | 3 | 1 | 8 |
| looseness | 0.35 | 0 | 1 |
| spread | 0.5 | 0 | 1 |
| sizeSpread | 0.4 | 0 | 1 |
| distance | 0.15 | 0 | 1 |
| azimuth | 0 | -180 | 180 |
| room | 0.5 | 0 | 1 |
| decay | 1.8 | 0.3 | 7 |
| wet | 0.28 | 0 | 1 |
| drive | 0 | 0 | 1 |
| body | 0 | -12 | 6 |
| air | 0 | -6 | 9 |
| level | 0 | -24 | 6 |
| gritAfter | 0 | 0 | 1 |

Time controls attack/release/glide are milliseconds; size is reference tract length in cm; azimuth is degrees; body/air/level are dB. Jitter/shimmer are percent; tremor/wander/vibrato act as pitch variation depths in cents in the implementation. Other shape/roughness/space controls are normalized amounts; throats is an integer count. Decay is the room RT parameter in seconds. gritAfter is a thresholded comparison switch (>0.5), retaining the original before/after grit experiment for full control coverage; it is not a continuous distortion mix.

Texture presets: clean, weathered, raspy, chant, growl, fry, ayn, ring, whisper, small, kargyraa. Presets are partial parameter patches: merge into defaultParams() for a reproducible reset preset, or into live state to preserve unrelated settings. Calibration trim is selected independently by presetId; setting presetId alone does not apply the preset values.
