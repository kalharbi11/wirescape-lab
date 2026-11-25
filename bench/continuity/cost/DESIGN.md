<!-- SPDX-License-Identifier: GPL-3.0-only -->
# A69a per-render Callgrind evidence

Architect run 35, #480 comment 7151868497. Work in the standalone bench only,
using the final E5 review head once B5 completes A71. No product, registry,
protocol, source-patch or top-level CMake edit. No devices or network services.

- Black Ice Choir: verify it ranks first from exact-head paired instructions;
  load the unchanged bundled patch via the pinned runtime document/catalogue,
  reproduce the golden C4 held note, preserve the bundle's authored seed (the ranking uses 37), prepare 48 kHz / 256 frames. Warm up 240 blocks, measure 64 steady blocks.
  Measure max individual render Ir after a declared warm-up, not a whole-run
  subtraction. Report a module's attributed own share only if attributable.
- Clocked Groove: load the unchanged bundle and a prepared candidate differing
  by one canonical Groove step key (module ID 2); verify the canonical bytes
  differ and the native descriptor has no adopt hook. Keep the existing graph
  and all other module configs. Call the real AppEngine replan, no host-bus
  injection or generated descriptor. Render both the original and transition.
- Profile only the render owner: Callgrind collection toggled around each
  complete render, labelled dump after each block, reset counters; no output
  capture, loading, allocation of profile buffers, or control staging inside
  the counted window. Use the real AppEngine facade so the counted scope includes the normal per-render peak meters. Identify actual publication via the adopt_layout call
  in that block's Callgrind trace (including separate housekeeping).
  Record the actual request boundary and control acknowledgement separately from observed publication. Require unique contiguous blocks, exactly one initial publication and one
  steady-layout publication, two before the request and two after housekeeping, positive Ir,
  correct event schema, no dropped/late/faulted events. Check native fade
  default 960 samples; report the max audible fade and max transition-layout blocks separately, plus housekeeping Ir and full request-to-retirement window, rather than silently equating retirement with fade length. A profile that misses the
  unchanged native three-block wall deadline under Valgrind is a failed
  measurement, not a reason to change the deadline.
- Preserve raw labelled dumps, exact engine and harness pins, toolchain,
  patch hashes, actual edited JSON pointer/values, meters, and computed tables.
  The test fixtures use artificial Ir solely to test parser behavior.
  There is no Ir acceptance threshold and no measurement at a provisional pin.

Signed: gpt-builder1, 2026-11-24.

Callgrind 3.22 separate-thread format (45545555089): the base output file is an empty coordinator; accept only that exact zero-byte file, plus explicit zero-count termination records. Require all labelled dumps from one render thread, and sum their Ir totals against the profiler's collected Ir. Preserve every file digest.
