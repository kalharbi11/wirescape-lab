<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0007 — Splitting the engine source (design for T1.6)

Fable, 2026-11-16 (ET), against `main` at `c692c7a`. Short note. It fixes where the seams go so
that T1.6 prepares the layout work of `0005` section 5 instead of only reformatting. Not yet
contracted: it starts after M1 stage S5b, on the engine without the ABI1 shim.

## Today (observed)
`native/engine2/engine2.cpp` is one 1,271-line file in one anonymous namespace. `Node`
(`:99-131`) mixes five kinds of field, and `Engine::Impl` (`:182-274`) owns everything. The
functions fall into four groups by who may call them:

| Group | Functions (line) | Thread |
|---|---|---|
| Build | `add_node` 736, `connect` 757, `modulate` 763, `output` 767, `setup` 275, `topology` 369, `finish_prepare` 340, `resolve_taps` 318, `prepare` 809 | control, quiescent |
| Render | `render` 850, `collect` 460, `admit` 435, `route` 517, `process_node` 554, `valid_target` 426 | audio |
| Cross-thread surface | `enqueue` 825, `pop_egress` 949, `panic` 966, `meter` 990, `read_telemetry` 788, `publish_clock` 840 | named in `engine2.h` |
| Edit | `reconfigure` 1029, `replan` 1118, `save_state` 1014, `load_state` 1020, `recompute_latency` 348 | control, beside render |

## Decision: five files, and `Node` split in two structs now

```
engine2/
  types.h        Buffer, Packet, Ring, Producer, Item, Parameter, Edge, Bus, Component
  instance.h     struct Instance   (what belongs to one module instance)
  layout.h       struct Slot, struct Layout   (what belongs to one topology)
  build.cpp      Build group
  render.cpp     Render group and the cross-thread surface
  edit.cpp       Edit group
  engine2.cpp    Engine's public methods forwarding to Impl; Impl definition
```

`Node`'s fields are assigned as follows. This is the part that matters for `0005`.

| Goes to `Instance` (survives an edit) | Goes to `Slot` (rebuilt by an edit) |
|---|---|
| `id`, `d`, `instance`, `born_revision`, `config`, `preserved` | `index`, `component`, `loop` |
| `inputs`, `outputs`, `parameters` (port and parameter tables) | `incoming`, `signal_edges`, `modulation`, `outgoing` |
| `state` (parameter values and smoothers), `modulation_sum` | `in` buffers, `in_view`, `param_view` |
| `local_out`, `global_out`, `out_view`, `param` buffers | `event_tap_slots` |
| `port_events`, `event_view`, `events`, `pending`, `event_outputs`, `emit_context` | `touched` |
| `pitch`, `channels`, `forced_channels`, `latency` | |
| `allocations`, `requested_fast`, `requested_large` | |

In T1.6 a `Slot` still lives beside its `Instance` and both are swapped together exactly as `Node`
is today: `struct Node { Instance instance; Slot slot; }`. No ownership or threading changes. The
point is that every line of render and edit code then says which side it reads, and the compiler
shows every place routing and instance state are tangled. Step E4 of `0005` later moves `Slot`
into a `Layout` object without touching the render code's field accesses again.

`process_node` (`:554-735`) is split into named steps in `render.cpp`, in its current order:
resolve channels, gather inputs, apply parameter events and modulation, call the module, publish
outputs and telemetry. Each is a function taking `Instance&` and `Slot&`.

## Rules for the PRs
1. Three PRs, one writer, serial: (a) format the file and move types to `types.h`, no other
   change; (b) split `Node` into `Instance` and `Slot` inside the one file; (c) move functions
   into the four `.cpp` files and split `process_node`.
2. No behaviour change: golden 24 identical on three platforms on each PR.
3. Instruction counts: no row more than 1 % worse on each PR. The render loop must not gain an
   indirection per node; `Instance` and `Slot` stay adjacent in memory in T1.6.
4. No function in `engine2/` above cyclomatic complexity 40 after (c) (the `0004` criterion).
5. No public API change in `engine2.h`. No change to tests except includes.
6. Where a field does not fit either column cleanly, the builder stops and asks through
   `QUESTIONS.md` instead of choosing: a wrong placement here becomes a data race in E4.

Merge: (a) lead; (b) and (c) lead after contract-review against rules 2–5 and the table above.

Signed: Fable, 2026-11-16
