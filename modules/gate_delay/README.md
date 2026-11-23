<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Gate Delay (experimental)

**ID:** `essentials.gate_delay`. This is an experimental module described in proposals/0020 §4.
Parameter IDs, ranges and scheduling details may change before owner acceptance.

Gate mode replays poly rising/falling edges with the delay captured on each rise.
It forwards a pitch sample captured at input rise when the delayed rise occurs.
`trig` emits a one-millisecond pulse for each delayed rise.
`spread` applies per-lane time offsets; Up, Down, Alternate and seeded Random
choose the order for each new chord (the first active rise after all lanes were low).
`humanize` applies bounded seeded per-rise jitter. `repeats` schedules up to four
additional on/off pairs, each separated by the time parameter (minimum one sample).

In Signal mode, the input and pitch lane are sampled into two fixed 1 kHz
delay-line sets of 2002 entries per 16 channels. Both are interpolated on
output. Combined time-CV and spread delays are clamped to two seconds in this
mode; Gate mode can delay longer when spread contributes. Any input sample
transition may be quantized by up to one millisecond.

The module has a fixed 64-edge queue per lane. Overflow drops the oldest
*insertion* pending edge and increments the lane's `dropped` counter.
Reset clears queues, outputs and counters. All buffer memory is obtained from
the host during preparation; there are no heap allocations or locks in the
audio callback. Default time is 250 ms, spread and humanize zero, and repeats zero.

**Device-off tests:** exact gate duration, delayed trigger shape, pitch
sample-and-hold, strum orders and deterministic random, repeats, delay latching,
signal step delay and trigger, queue overflow/reset, frame-block invariance and
process allocation guard. This draft is **not** an accepted or merged module.
