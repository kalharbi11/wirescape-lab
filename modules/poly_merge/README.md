<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Poly Merge (experimental) — implementation plan

Experimental eight-mono-to-one-poly sample-accurate CV cable merger, highest-connected input sets lane count.

**Issue:** #328. **Source:** proposals/0020 §3. **Owner:** gpt-builder4, by Architect run 9 / #328 comment 7095286128. **Implementation base:** post-S6 main, synchronized via non-force two-parent merge; exact test head is recorded on the PR.

This is a device-off, post-S6 draft work branch. **Do not merge** before Gate Delay #329, lead approval, and exact-head Lab, Golden and M1 paired gates. No workflow changes.

## Routing contract

- Eight independent **mono** (`WS2_FIRST`) signal input ports, `in1` through `in8`, feeding one `WS2_POLY` signal output named `out`.
- Lane `n-1` reproduces the input samples of `in n` at the same sample offsets, with no summing, normalizing, quantization or pitch conversion.
- Input connection state is available to ABI2 via `ws::Block::in(n).connected()` (backed by `WS2_CONNECTED`). Therefore **use the highest connected input** for output channel count, rather than adding a redundant `channels` parameter. Count is at most eight. If no input is connected, publish one silent lane, avoiding a zero-channel output.
- Any disconnected input below that highest connected port contributes zero to its corresponding lane, including after a cable is removed; do not let a previously connected value remain.
- The output is an ordinary signal cable. A consumer such as VCO pitch or ADSR gate should receive the same number of active poly lanes, subject to the host's existing channel-capacity contract. No new event protocol or OSC change.
- Respect the `ws2_signal_out.max_channels` destination capacity and `ws2_process` frame bounds. No heap allocation, lock, I/O or system calls in `process()`. Preserve constant inputs correctly over varying block lengths.

## Device-off acceptance matrix (required before review)

1. Single connected `in1` maps one lane and preserves input samples at offsets 0, 1 and the final frame.
2. Connected `in1`, `in3`, `in8` maps eight lanes with `out[0]`, `out[2]`, `out[7]` bit-identical to the respective inputs; all other lanes zero.
3. Highest connected input determines channel count for each of 1–8, independently of nonzero data; removing `in8` reduces the output immediately and zeroes subsequently unconnected lanes.
4. No connected inputs outputs exactly one silent lane; sparse holes remain silent.
5. Repeat cases across block sizes 1, 7, 128, 256 and host channel capacities 1, 8, 16, without buffer overruns.
6. Connect the generated poly output to the VCO pitch input or ADSR gate input in the device-off harness; verify downstream channel count and per-channel signal behavior.
7. Use `allocation_watch::Scope` around `process()`; require zero realtime allocations.
8. Confirm module manifest, native catalogue registration, Studio presentation/derived catalogue and CMake test registration agree. Run `wsmod check modules/poly_merge` and `python tools/gen_ui_catalogue.py --check`.
9. Apply proposal 0020 §7 **only after** the preceding module merge state is inspected: regenerate S0 catalogue using the S0 serializer, with only `essentials.poly_merge` introduced; append it to the existing `experimental` list (or create the shared list only if absent), retain the 34 Golden IDs, all 24 Golden patch renders and every existing Ir row within 1%. No workflow edits.
10. Obtain exact-head hosted Lab, three-platform Golden and M1 paired success before posting the final Result. The delivery lead owns merge.

## Status

**DSP and device-off tests authored.** The existence of tests in this branch is not execution evidence; hosted CI and an exact-head green Result are required before merge.

Signed: gpt-builder4, 2026-11-23 EST.
