<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR C++ 0.1 — standalone and Wirescape adapter

- New C++17 GUTTUR vocal-tract synthesis engine built from the provided GUTTUR JavaScript reference; no Throat v.2 DSP copied.
- 16 tracked note IDs and 16 internal throat generators (up to eight per note), one internally mixed stereo pair.
- Original LF/Rd excitation, 34-section tube, 10-resonator filter, throat group and bus sound architecture retained.
- Removed chant/crowd sequencer, scene/gesture scheduler, clap/stamp percussion and browser UI.
- Added deterministic event/parameter callback timing, bounded note identity handling and deterministic delayed-note releases.
- Improved abrupt master/wet parameter transitions and precomputed sample-rate/control constants in the hot path.
- Added CMake static library, offline render/bench tools, comparison scripts, ABI2 wrapper, integration metadata and tests.
- See `DEVIATIONS.md` and `TEST_RESULTS.md` for changes and measured limitations.
