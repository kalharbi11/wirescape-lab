<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Cortex-M7 compile-only portability probe

The advisory workflow .github/workflows/portability.yml pins Arm GNU 14.2.rel1
and compiles every discovered module translation unit under modules/ and
sdk/examples/, plus the SDK template. The current 38 registered modules and
one template are compiled twice: fpv5-d16 and fpv5-sp-d16. Inventory is
checked against the explicit Golden/experimental ID sets.

The probe does not link, load DSP modules, use audio/MIDI devices or open LAN sockets.
Compile failures are recorded as measurements with their first compiler error.
For successful objects, arm-none-eabi-size -A supplies summed .text.*,
.data.* and .bss.* bytes. Undefined arm-none-eabi-nm symbols are
categorized as double-precision libm or software float, float libm, heap,
or static guard references. The exact symbol spellings are preserved in JSON.

Run on Linux with the pinned cross compiler on PATH and the Macro Oscillator
dependency context prepared by the workflow:

    python3 bench/portability/probe.py --out facts/repo/cortex-m7/modules.json --readme facts/repo/cortex-m7/README.md

The workflow publishes JSON and a Markdown table as short-retention artifacts
and emits PORTABILITY_CHUNK log lines for reproducible fact staging.
Measurements name the actual Git commit tested, cross-compiler version,
archive checksum, FPU variants, and New York date.

Device-free parser and inventory tests:

    python3 -m unittest discover -s bench/portability/tests -v
