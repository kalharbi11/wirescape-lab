<!-- SPDX-License-Identifier: GPL-3.0-only -->
# #475: OSC Out mixed-publication gate snapshot witness

**Classification:** synthetic bounded source-order model, not a product failure
reproduction or a timing measurement. No product changes, no actual device,
network, sentinel, workload, queue or gate changes.

## Provenance and hypothesis

Historical #444 sanitizer job [138778722225](https://github.com/kalharbi11/wirescape-lab/actions/runs/45487734995/job/138778722225)
at `d85c076b060c07a3e02fbc4ba3fe048638ea82fd` reported
`unexpected_gate_edge:0` at approximately 2.86 s; three native release tests
passed, as did a later sanitizer test. See the
[prior B2 triage](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7147616167).
There is no captured failing publication/cursor trace for that historical run.

The four source blobs recorded by the script are byte-identical between that
historical head and source base `a8b34237b252d9fcfedfa3810732ba8feacae560`.
The report checks their Git blob identities before recording its exact head.
The model translates `OscOut::process` and the bounded gate branch of
`OutHost::loop`. The writer stores the last value relaxed, increments edge
counters relaxed, then increments blocks release. The reader loads blocks
acquire, reads rises/falls relaxed, and reads value relaxed. A load acquiring
an *earlier* block's release does not make later stores into one atomic
snapshot. The witness uses a sequentially consistent interleaving of those
source operations, so no speculative or weak-memory reordering is needed.

## Bound and predicted distinguishing trace

One enabled gate row; initial completed low block; cursor initialized by a
successful low send. One rising block; interleave its three actual writes
(value, rises, blocks) with the four reads of one poll (blocks, rises, falls,
value). No fall increment in the rising block. Enumerate all 35 ordered
merges. After the interleaved poll, two complete polls read the unchanged
fully published high row; then one complete falling block and poll. No reset,
wrap, overflow, competing rows or failed sends. With 0/1 edge delta and
successful sends the unchanged per-poll budget of 64 cannot bind.

| Poll | blocks, rises, falls, value | Output | Explanation |
|---|---|---|---|
| baseline | 1, 0, 0, 0 | 0 | initial low |
| split publication | 1, 0, 0, 1 | 1 | zero-edge reconciliation before rise counter increment |
| completed rise | 2, 1, 0, 1 | 0 | counter delta toggles already-high cursor |
| still high | 2, 1, 0, 1 | 1 | reconciliation restores high |
| real fall | 3, 1, 1, 0 | 0 | actual falling edge |

Expected stream: 0,1,0. Predicted distinguishing stream: 0,1,0,1,0.
The extra fall is emitted while the producer remains high and the cursor
has consumed the rise. Coherent-before and coherent-after schedules are
negative controls. The artifact contains the full step-by-step bus,
captured snapshot, cursor and sends for this specific witness, and the
outcome of every bounded schedule. Counts are not probabilities or a
measured incidence rate; the model does not run the native host thread.

## Reproduction

```sh
python -m unittest discover -s bench/io -p test_gate_snapshot_witness.py -v
python bench/io/gate_snapshot_witness.py --output gate-snapshot-witness.json
```

The dedicated read-only advisory workflow runs the same commands on the
exact PR head and retains JSON; its checks do not alter existing gate rules.
This does not attribute the historical sanitizer failure, the OSC ingress
drops in #457, or the owner-only physical MIDI restart gap. No remedy is
authorized. A follow-up real-host witness could use the existing
`OutHost::buses()` and `SendOverride` seams with a manually split producer
publication, without instrumenting the DSP; a full render-thread scheduling
reproducer would require separate authority if new product seams are needed.

Signed: gpt-builder2, 2026-11-24
