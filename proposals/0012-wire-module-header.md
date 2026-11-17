<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0012 — The Wire module header (design note)

**Author:** Fable · **Date:** 2026-11-16 (ET) · **Status:** design. Part 1 is exact and is the
header text M4 E5 and E3a build from. Part 2 is the frozen header of `0004` T3.2 (contract M8).
**Rests on:** `0003` §2 (changes 1–11), `0005` §6–7, M4 G4, G5, G7,
`native/include/wirescape/module2.h` as read on `ef3e0fe`, `facts/code/capability_map.md`,
`docs/specs/ABI2_SPEC.md`, `docs/specs/EMBEDDED_PORTABILITY.md`.

## 0. Decisions

- **H1. Two steps.** Part 1 adds fields to `module2.h` with no break (M4). Part 2 is the one
  break: `wire/module.h`, ABI version 3, while no outside module exists. Part 1's structs carry
  into Part 2 with the prefix changed and nothing else.
- **H2. One field table for everything that is not a float signal.** Data slots, config and
  telemetry records are all "a plain C struct plus a table that describes it". The host packs
  JSON into the struct and unpacks records to JSON with one generic routine. The patch compiler
  of `0013` uses the same routine at build time.
- **H3. Host things arrive as bound ports, not function calls,** wherever the thing is a stream
  (device audio, MIDI, notes, messages). A port carries a `binding` name; the host connects it.
  Core code then looks for bindings, never for module IDs, and a firmware or plugin host
  satisfies the same binding with its own source.
- **H4. Services are few and versioned.** What cannot be a port (tables, telemetry, transport
  control) is a function table fetched by ID at `prepare`. A host that lacks one returns null,
  and the SDK turns that into a no-op.
- **H5. The tier is a promise the tools check,** not a comment (section 8).
- **H6. Nothing here changes** block processing, the event structs, port kinds and hints, host
  allocation, parameter smoothing or the 16-channel limit (M4 G4).

## Part 1 — additions to `module2.h` (M4; exact)

### 1. Text to add

`WS_ABI2_VERSION` stays 2. Add the constants and types before `ws2_process`, and the fields at
the **end** of `ws2_process` and `ws2_descriptor`, in this order and spelling:

```c
#define WS2_MAX_DATA_SLOTS 8u
#define WS2_MAX_DATA_BYTES 65536u
#define WS2_MAX_FIELDS 64u            /* per table, nested tables counted separately */
#define WS2_REPLACE_FADE_DEFAULT_MS 20u
#define WS2_REPLACE_FADE_MAX_MS 500u
#define WS2_NO_FIELD UINT32_MAX
enum ws2_field_type { WS2_F_F32=1, WS2_F_I32=2, WS2_F_U32=3, WS2_F_U8=4, WS2_F_BOOL=5,
                      WS2_F_ENUM=6, WS2_F_TEXT=7, WS2_F_RECORD=8 };
typedef struct ws2_field {
    uint32_t struct_size; const char *id,*name;
    uint32_t type,offset,count,stride;     /* count: array length, 1 = scalar */
    uint32_t length_field;                 /* index of the U32 field holding the live length, or WS2_NO_FIELD */
    uint32_t option_count; const char *const *options;      /* ENUM */
    double minimum,maximum,initial;
    uint32_t field_count; const struct ws2_field *fields;   /* RECORD: one level only */
} ws2_field;
typedef struct ws2_data_slot {
    uint32_t struct_size; const char *id,*name;
    uint32_t bytes,field_count; const ws2_field *fields; uint32_t flags;   /* flags: 0 */
} ws2_data_slot;
typedef struct ws2_data { uint32_t struct_size; const void *data; uint32_t bytes,serial; } ws2_data;

/* appended to ws2_process */
    uint32_t data_count; const ws2_data *data;
/* appended to ws2_descriptor */
    uint32_t data_slot_count; const ws2_data_slot *data_slots;
    int (WS2_CALL *adopt)(void *self,const void *old);
    uint32_t replace_fade_ms;
```

**Who lands it.** E5 is first in the engine lane. Its PR adds the **whole** block above, so the
header is edited once and the order cannot depend on merge order. Until E3a merges the host
refuses, with `WS2_UNSUPPORTED` at registration, any descriptor whose `data_slot_count` is not 0.
E3a removes that refusal and adds no header text except the SDK helpers.

**Reading rule (G5).** The host reads an appended descriptor field only when
`struct_size >= offsetof(field) + sizeof(field)`; otherwise it uses 0 or null. The SDK does the
same for `ws2_process`. `header_c99.c` gains offset checks for every appended field.

### 2. Field tables

| Type | Storage in the struct | JSON | Range check |
|---|---|---|---|
| `F32` | `float` | number | `minimum ≤ v ≤ maximum`, finite |
| `I32`, `U32`, `U8` | `int32_t`, `uint32_t`, `uint8_t` | integral number | the same, and the type's own range |
| `BOOL` | `uint8_t` 0 or 1 | `true` / `false` | — |
| `ENUM` | `uint32_t` index | one of `options` (string) | must match an option |
| `TEXT` | `char[count]`, NUL-terminated UTF-8 | string | byte length < `count` |
| `RECORD` | `count` structs of `stride` bytes, described by `fields` | array of objects | each field by its own row |

- `offset` is the byte offset the module's compiler gave the member (`offsetof`); the host
  assumes nothing about padding. `stride` is `sizeof` of one record (0 unless `RECORD`).
- **Arrays.** `count` > 1 makes an array of `count` elements. With `length_field` set, the JSON
  array may hold 0 to `count` items and the host writes the item count into that `U32` field;
  the remaining elements are zero. Without it the JSON array must hold exactly `count` items.
  A `length_field` is never set from JSON directly and has no JSON key.
- **Missing key:** the field's `initial` (TEXT and RECORD: zero bytes, length 0). **Unknown key,
  wrong type, value out of range, array too long:** the edit is refused and the reply names
  the slot and the field ID (`steps[3].velocity`). Nothing is delivered.
- Bytes that no field covers are zero. The packed block is therefore a pure function of the
  table and the JSON; two hosts given the same struct layout produce the same bytes.
- **Descriptor validation, at registration:** at most 8 slots; `bytes` from 1 to 65,536; at most
  64 fields per table; unique IDs matching `[a-z][a-z0-9_]*`; every field inside `bytes`,
  aligned to its type, overlapping nothing; `RECORD` not nested inside `RECORD`;
  `length_field` names a scalar `U32` in the same table; `minimum ≤ initial ≤ maximum`.
  A failure refuses the module and names the field.
- The SDK produces struct and table from one declaration, so they cannot drift. The spelling
  is the E3a builder's; the test is that a struct member cannot be added without its row.

### 3. Data in `process`

- `data[i]` belongs to `data_slots[i]`. For a declared slot `data[i].data` is **never null**:
  before the first `process` the host delivers a block packed from the document, or from the
  `initial` values when the document has none.
- `serial` starts at 1 and goes up by 1 for each block delivered to that slot of that
  instance. The module keeps "last serial seen", sets it to 0 in `reset`, and recomputes
  derived values, bounded, when the two differ.
- The pointer is valid for that call only (G7). The module keeps no copy and no pointer.
- Blocks are 16-byte aligned. On replacement the new instance receives the same blocks.
- Data is not part of `save_state`. The document stores it under `data: {slotId: {...}}`.

### 4. `adopt` and `replace_fade_ms`

- `adopt(self, old)`: `self` is the new, prepared instance; `old` is the instance being
  replaced. Called by render once, at the block boundary where the transition layout is
  adopted, before either instance processes (`0005` §7 step 3).
- **Only between instances of the same descriptor object.** The host calls `adopt` when the
  two instances were created from the same `ws2_descriptor` pointer, so both have the same
  memory layout by construction. For any other pair (a rebuilt library in the developer loop)
  the host takes the no-adopt path. Carrying state across builds is designed with `0004` T3.9
  (M9), as a separate hook; it is not this one.
- The two instances may differ in config and in channel count. The hook copies what continues
  (phases, envelope levels, held notes, smoother values, a bounded part of a buffer) for the
  voices that fit. It may read `old`'s host-allocated memory during the call and keeps no
  pointer into it afterwards.
- Returns `WS2_OK` (adopted) or `WS2_UNSUPPORTED` (declined; the host then acts as if there
  were no hook: held notes are sent to the new instance, the old one rings out). Any other
  value is treated as declined and counted in the engine meter.
- Realtime rules apply (G7). The host sets the new instance's parameters to the current
  values before the call, with smoothers at their targets.
- `replace_fade_ms`: 0 or an absent field means 20. Values above 500 are used as 500.

### 5. What Part 1 leaves alone

No capability, tier, telemetry, service or config change. `ws2_config.data` and the adapter in
`runtime_module_config.h` stay until Part 2. `legacy_index` stays. Groove, `midi.cc_to_cv` and
the OSC modules move their rows to data in M4 E3b and E3c with today's config still read one way.

## Part 2 — `wire/module.h` (T3.2; the one break)

### 6. Shape

- **Names:** prefix `wire_` / `WIRE_`, `WIRE_ABI_VERSION 3`. The structs of `module2.h` keep
  their fields and order except where this section says otherwise, so a port is a rename plus
  the listed edits. The SDK hides the rename from module sources.
- **Fixed widths (0003 change 8).** Integer fields are `uint32_t`, `int32_t` or `uint64_t`.
  No `size_t`, `long`, `bool` or enum-typed field. Functions return `int32_t`. `wire_memory`
  uses `uint64_t fast_bytes, large_bytes; uint32_t alignment`. `alloc` takes
  `(void*, uint64_t bytes, uint32_t alignment, uint32_t hint)`. Pointers remain: this is an
  in-process interface, not a file format. The header carries `static_assert`s of every struct
  size for 32-bit and 64-bit pointers, and a C99 test compiles it for both.
- **Sample rate:** `wire_config` and `wire_process` carry `float sample_rate_f` beside the
  `double`. Transport keeps `double` beats.
- **Entry:** `const wire_module_list *wire_modules(void)` returning `{struct_size, abi_version,
  count, const wire_descriptor *const *items}`; `uint32_t wire_abi_version(void)` stays. Both
  names can be overridden for static links, as today.
- **`legacy_index` is removed** (0003 change 1; M1 acceptance point 2 expects it to live only
  here until then).

### 7. Descriptor additions

| Field | Meaning |
|---|---|
| `category` | string ID from the list in `0014`; an unknown value loads and is shown as "Other" |
| `tier` | `WIRE_TIER_PORTABLE` 1 or `WIRE_TIER_DESKTOP` 2 (section 8) |
| `capabilities` | `uint64_t` bit set (section 9) |
| `config_bytes`, `config_field_count`, `config_fields` | the config struct and its field table. `wire_config.data` points at the packed struct. The **default config** is the table's `initial` values. The per-module adapter is deleted (T3.3) |
| `data_slot_count`, `data_slots`, `adopt`, `replace_fade_ms` | as Part 1 |
| `telemetry_count`, `telemetry` | section 10 |
| `internal_voices` | for a voice owner: the largest number of voices it runs inside one channel; 0 otherwise |
| `licence` | SPDX expression of the module, including third-party code linked into it |
| `memory_hint_bytes` | upper bound of `fast_bytes + large_bytes` for the default config at 48 kHz, for catalogues and the compiler's budget; the measured value is still asked through `memory_requirements` |

Port additions: `binding` (string or null, section 9), `smooth` and `smooth_ms`.
Parameter additions: `smooth` and `smooth_ms`. `smooth` is `WIRE_SMOOTH_HOST` 0 (today's host
behaviour), `WIRE_SMOOTH_NONE` 1, `WIRE_SMOOTH_MS` 2, `WIRE_SMOOTH_AUDIO_RATE` 3. In T3.2 every
module declares 0 and nothing changes in the sound; `0004` T4.2 gives the other values meaning.

Field tables gain two types in Part 2: `WIRE_F_TABLE` (a reference to a host table, section 9)
and `WIRE_F_F64` for config only. Config fields are shape only: counts of ports, voices, rows.

### 8. Tiers

**Portable** means: this object file runs unchanged on a Cortex-M7 with no operating system.
`wirescape module check` enforces it on the compiled object and the includes:

1. No heap: no `new`, `delete`, `malloc`, `free` symbol. Placement new into host memory is fine.
2. No exceptions and no RTTI; built with `-fno-exceptions -fno-rtti`.
3. No operating-system or stream header: threads, mutexes, files, sockets, `iostream`, `chrono`.
   `std::atomic` is not allowed; the host services replace its uses.
4. No mutable global or function-static object, and no global with a constructor. `const` tables
   are fine.
5. No double-precision library call: the object imports no `sin`, `cos`, `tan`, `exp`, `log`,
   `pow`, `sqrt`, `fmod`, `floor` (and so on) without the `f` suffix. `double` arithmetic and
   the transport's `double` fields are allowed; the bench reports their cost.
6. All memory comes from `memory_requirements` and `alloc` at `prepare`; `memory_hint_bytes` is
   declared; no automatic array above 4 KiB.
7. Vector code only through `sdk/simd.h`, which has a scalar path.
8. Works at every sample rate from 32 kHz to 96 kHz and every block size from 1 to the
   prepared maximum (the module test matrix of `0016` already runs this).
9. Saved state is written with fixed-width little-endian fields.
10. Capabilities only from the portable set (section 9).

**Desktop** means: the realtime rules of `AGENTS.md` and nothing more. A desktop module says so
in its descriptor and is refused, by name and reason, by a firmware or compiler target.
Counts of each tier are a fact file produced by T3.10; this note predicts none.

### 9. Capabilities, bindings and services

A module declares capability bits. The host grants only what is declared: an undeclared
binding is a registration error, an undeclared service request returns null.

| Bit | Name | How it arrives | Portable | Replaces today |
|---|---|---|---|---|
| 0 | `AUDIO_OUT` | signal inputs with `binding: "audio.out"` | yes | `essentials.output` named in `session.cpp`, `ui_patch_conformance.cpp` |
| 1 | `AUDIO_IN` | signal outputs with `binding: "audio.in"` | yes | — (new) |
| 2 | `MIDI_IN` | event input, `binding: "midi.in"` | yes | `midi.in` in `midi_host.cpp` |
| 3 | `MIDI_OUT` | event output, `binding: "midi.out"` | yes | — (new) |
| 4 | `NOTES_IN` | event input, `binding: "notes.in"` (screen keyboard, plugin notes, firmware keys) | yes | `host.keyboard` in `session.cpp`, `midi_host.cpp` |
| 5 | `MESSAGE_IN` | event input, `binding: "message.in"` | no | `osc.in` in `osc_host.cpp` |
| 6 | `MESSAGE_OUT` | event output, `binding: "message.out"` | no | `osc.out`, the `OutBus*` in config |
| 7 | `TRANSPORT_CONTROL` | service `wire.transport` | yes | — (Transport module, `0014`) |
| 8 | `TABLES` | service `wire.tables`, field type `WIRE_F_TABLE` | yes, const tables | per-instance tables |
| 9 | `TELEMETRY` | service `wire.telemetry` | yes (no-op on firmware) | `telemetry_taps.h`, `engine2.cpp:146`, monitor's `Tap*` |
| 10 | `VOICE_OWNER` | `internal_voices`; rules in `0014` | yes | — |
| 11 | `STREAM_OUT` | signal inputs with `binding: "stream.out"` (Recorder) | no | — |

- **Bound ports.** A bound port is not shown as a jack. Which device, channel pair, endpoint
  or route it uses is ordinary data or config of that instance, so several instances can bind
  to different endpoints. A bound event output is delivered through the existing egress ring;
  a bound event input through the existing ingress ring. Ordering and budgets do not change.
- **Reading transport** needs no capability; `process->transport` stays as it is.
- **Services:** `wire_host` gains `const void *(*service)(void *ctx, const char *id, uint32_t
  version)`, valid during `prepare` only. Each service is a struct of function pointers that
  starts with `struct_size`. Version 1 of each:
  - `wire.transport`: `request(ctx, const wire_transport_request*)`, realtime-safe; the
    request reaches the control owner through the egress ring and comes back as transport.
  - `wire.tables`: `require(ctx, key, frames, channels, fill, user)` at `prepare` only. The
    host keeps one immutable table per key and shares it between instances; `fill` runs once,
    off the audio thread. A compiler target runs `fill` at build time and puts the table in
    flash. This settles the question `0003` §6 left open: tables are shared by a host cache.
    A `WIRE_F_TABLE` field stores `{const float *frames; uint32_t frame_count, channels;
    float sample_rate}`; the host fills it from an asset named in the document and keeps the
    table alive while a delivered block refers to it.
  - `wire.telemetry`: section 10.
- **Module IDs leave core code** (T3.4): each row of the "core code naming module IDs" table in
  the inventory behind this note is removed by a binding, a service, the field table, or the
  default-patch file. T3.4's acceptance is a grep with zero matches outside tests, the
  default patch and the alias table.

### 10. Telemetry records

- A module declares up to 8 streams: `{id, name, kind, scope, bytes, rate_hz, field table}`.
  `kind` is `LATEST` (one record, the newest wins; `bytes` ≤ 256) or `BLOCK` (a queue of
  records for sample data such as a scope; `bytes` ≤ 4,096; a full queue drops and counts).
  `scope` is per module or per voice. `rate_hz` is a ceiling the host may lower; default 30.
- In `process`: `publish(ctx, stream, voice, const void *record)`, and `wanted(ctx, stream)`
  so a module can skip the work when nobody listens. Both are wait-free: one atomic load when
  there is no subscriber, one bounded copy when there is. No allocation, no lock (G1).
- The host decodes a record to JSON with the field table and sends it only to subscribers. A
  panel asks by module instance and stream ID (`0015`). The module never formats text.
- Existing taps (envelope level, LFO phase, Groove playhead, oscillator pitch, monitor) move
  onto streams in T3.4. Master and bus meters stay host-owned.

### 11. Limits (frozen with the header)

Ports 32, parameters 64, channels 16, data slots 8 of 64 KiB, config 64 KiB, fields 64 per
table, telemetry streams 8, capabilities 64 bits, text IDs `[a-z][a-z0-9_.]*` up to 63 bytes.

## 12. Order and cost

1. Part 1 lands with M4 E5 (header block, `adopt`, fade) and E3a (data delivery, packer, SDK).
2. T3.2 writes `wire/module.h` and the SDK shim; all modules still build; golden 24 identical.
3. T3.3 (config tables), T3.4 (bindings and services), T3.5 (SDK helpers and ports) follow.

Cost of the break: every in-tree module is rebuilt once behind the SDK; saved patches do not
change (parameter IDs are strings already). Risk: the field table is too small for a real
module. The three test modules of `0014` are the check; a field type may be added before T3.2
merges and not after without a version step.

## 13. Assumptions, and what would overturn them

- **A1** Groove steps, CC rows and OSC routes fit "array of flat records with a length". A
  module that needs nested arrays would need a second nesting level: bring the struct.
- **A2** 64 KiB per slot holds every first user. `runtime_module_config.h` sizes are the check;
  the E3a builder posts them before code.
- **A3** No module needs `adopt` across different builds before M9.
- **A4** Egress and ingress rings can carry bound-port traffic at today's budgets. A measured
  drop under the M4 stress test overturns H3 for that stream only.
- **A5** `std::atomic` uses in `monitor`, `osc_in` and `spectral` can all be expressed as
  telemetry or latency reporting. If one cannot, that module is desktop tier.

Signed: Fable, 2026-11-16
