// SPDX-License-Identifier: GPL-3.0-only
#include "../../host/midi/module_test_support.h"
#include "dsp.h"
#include "data_validation.h"
#include <array>
#include <cstring>
#include <vector>

using namespace wirescape;

struct Rig {
    MidiArena arena;
    ws2_host host{sizeof(host), &arena, MidiArena::alloc};
    const ws2_descriptor *desc = ws::Module<osc::OscOut>::descriptor();
    void *state = nullptr;
    float samples[8][2][1024]{};
    const float *channel_ptrs[8][2]{};
    ws2_signal inputs[9]{};
    ws2_event_list event_inputs[9]{};
    ws2_process ctx{};
    alignas(16) osc::OscOutRoutes slot_data{};
    ws2_data view{sizeof(ws2_data), &slot_data, sizeof(slot_data), 1};

    explicit Rig(const osc::OutConfiguration *config = nullptr) {
        state = desc->create(&host);
        REQUIRE(state);
        ws2_config setup{sizeof(setup),
                         48000.,
                         1024,
                         16,
                         1,
                         reinterpret_cast<const uint8_t *>(config),
                         config ? uint32_t(sizeof(*config)) : 0u};
        REQUIRE(desc->prepare(state, &setup, &host) == WS2_OK);
        for (uint32_t i = 0; i < 8; ++i) {
            channel_ptrs[i][0] = samples[i][0];
            channel_ptrs[i][1] = samples[i][1];
            inputs[i] = {sizeof(ws2_signal), channel_ptrs[i], 2, WS2_CONNECTED};
        }
        inputs[8] = {sizeof(ws2_signal), nullptr, 0, 0};
        ctx.struct_size = sizeof(ctx);
        ctx.sample_rate = 48000.;
        ctx.channels = 1;
        ctx.input_count = 9;
        ctx.inputs = inputs;
        ctx.event_inputs = event_inputs;
        const osc::OutConfiguration defaults;
        const auto &cfg = config ? *config : defaults;
        char error[128]{};
        REQUIRE(osc::materialize_osc_out_routes(cfg, slot_data, error));
        ctx.data_count = 1; ctx.data = &view;
    }
    ~Rig() { desc->destroy(state); }
    void run(const std::vector<ws2_event> &events = {}, uint32_t frames = 8) {
        ctx.frames = frames;
        ctx.events = {sizeof(ws2_event_list), uint32_t(events.size()), events.data()};
        event_inputs[8] = ctx.events;
        int result;
        {
            allocation_watch::Scope no_alloc;
            result = desc->process(state, &ctx);
            REQUIRE(no_alloc.allocations() == 0);
        }
        REQUIRE(result == WS2_OK);
        ctx.frame_position += frames;
    }
};

enum class NoteKind : uint8_t { On, Off, Choke };
static ws2_event note(NoteKind kind, int32_t key) {
    ws2_event event{};
    event.struct_size = sizeof(event);
    event.type = kind == NoteKind::On ? WS2_NOTE_ON : kind == NoteKind::Off ? WS2_NOTE_OFF : WS2_NOTE_CHOKE;
    event.port = 8;
    event.key = key;
    event.channel = 2;
    event.note_id = key;
    event.source_id = 1;
    event.value = .75f;
    return event;
}
static void configuration_checks() {
    osc::OutConfiguration config;
    // The public type itself must be safe for the sender, even without a parser call.
    REQUIRE(config.version == 1 && config.port == 9001 && config.rate_hz == 100);
    REQUIRE(config.bus == nullptr && config.notes.enabled == 0);
    REQUIRE(std::strcmp(config.rows[0].address, "/ws/row/1") == 0);
    REQUIRE(std::strcmp(config.rows[7].address, "/ws/row/8") == 0);
    REQUIRE(std::strcmp(config.notes.address, "/ws/note") == 0);
    REQUIRE(osc::out_configuration(nullptr, 0, config));
    REQUIRE(config.port == 9001 && config.rate_hz == 100 && config.notes.enabled == 0);
    REQUIRE(std::strcmp(config.rows[0].address, "/ws/row/1") == 0);
    REQUIRE(std::strcmp(config.rows[7].address, "/ws/row/8") == 0);
    REQUIRE(std::strcmp(config.notes.address, "/ws/note") == 0);
    auto valid = config;
    auto check = [&](const osc::OutConfiguration &c) {
        osc::OutConfiguration decoded;
        return osc::out_configuration(reinterpret_cast<const uint8_t *>(&c), sizeof(c), decoded);
    };
    REQUIRE(check(valid));
    valid.version = 2;
    REQUIRE(!check(valid));
    valid = config;
    valid.port = 0;
    REQUIRE(!check(valid));
    valid = config;
    valid.rate_hz = 501;
    REQUIRE(!check(valid));
    valid = config;
    valid.rows[0].enabled = 2;
    REQUIRE(!check(valid));
    valid = config;
    valid.rows[0].kind = 2;
    REQUIRE(!check(valid));
    valid = config;
    valid.rows[0].deadband = -0.1f;
    REQUIRE(!check(valid));
    valid = config;
    valid.rows[0].deadband = 1.01f;
    REQUIRE(!check(valid));
    for (const char *bad : {"no/slash", "/a*", "/bad key", "/b[2]", "/c#1"}) {
        valid = config;
        std::strcpy(valid.rows[0].address, bad);
        REQUIRE(!check(valid));
    }
    valid = config;
    std::memset(valid.rows[0].address, 'x', sizeof(valid.rows[0].address));
    REQUIRE(!check(valid));
    valid = config;
    valid.notes.enabled = 2;
    REQUIRE(!check(valid));
    REQUIRE(!osc::out_configuration(nullptr, 1, valid));
}

static void rows_and_gate_edges() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    REQUIRE(osc::out_configuration(nullptr, 0, cfg));
    cfg.rows[0].kind = 1;    // gate, with two short pulses within one callback
    cfg.rows[2].enabled = 0; // disabled rows do not publish
    cfg.bus = &bus;
    Rig r(&cfg);
    r.samples[0][0][1] = 1.f;
    r.samples[0][0][3] = 1.f;
    r.samples[1][0][7] = .25f;
    r.samples[1][1][7] = .99f; // FIRST ignores channel 1
    r.samples[2][0][7] = 1.f;
    r.run();
    REQUIRE(bus.rows[0].rises == 2 && bus.rows[0].falls == 2);
    REQUIRE(bus.rows[0].blocks == 1 && bus.rows[0].value == 0.f);
    REQUIRE(bus.rows[1].blocks == 1 && bus.rows[1].value == .25f);
    REQUIRE(bus.rows[2].blocks == 0);
    r.inputs[0].flags |= WS2_CONSTANT;
    r.samples[0][0][0] = 1.f;
    r.run();
    REQUIRE(bus.rows[0].rises == 3 && bus.rows[0].falls == 2);
    REQUIRE(bus.rows[0].blocks == 2 && bus.rows[0].value == 1.f);
    {
        allocation_watch::Scope no_alloc;
        r.desc->reset(r.state);
        REQUIRE(no_alloc.allocations() == 0);
    }
    REQUIRE(bus.rows[0].blocks == 2); // never zero consumer-visible counters on reset
}

// Panic/reset must preserve consumer-owned counters and must not manufacture a
// fresh gate rise when the input stayed high. The initial un-reset first block
// still counts a real leading rise (covered above and by the threshold test).
static void gate_reset_primes_without_phantom_edges() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    cfg.bus = &bus;
    cfg.rows[0].kind = 1;
    Rig r(&cfg);
    r.inputs[0].flags |= WS2_CONSTANT;
    r.samples[0][0][0] = 1.f;
    r.run();
    REQUIRE(bus.rows[0].rises == 1 && bus.rows[0].falls == 0);
    {
        allocation_watch::Scope no_alloc;
        r.desc->reset(r.state);
        REQUIRE(no_alloc.allocations() == 0);
    }
    r.run({}, 0); // No samples: do not consume the reset baseline.
    REQUIRE(bus.rows[0].blocks == 1);
    r.run();
    REQUIRE(bus.rows[0].blocks == 2 && bus.rows[0].value == 1.f);
    REQUIRE(bus.rows[0].rises == 1 && bus.rows[0].falls == 0);

    // A genuine fall after a held-high reset baseline must still count.
    r.inputs[0].flags &= ~WS2_CONSTANT;
    r.samples[0][0][0] = 1.f;
    r.samples[0][0][1] = 0.f;
    r.desc->reset(r.state);
    r.run({}, 2);
    REQUIRE(bus.rows[0].rises == 1 && bus.rows[0].falls == 1);
    REQUIRE(bus.rows[0].value == 0.f);

    // A genuine rise after a held-low reset baseline must also count.
    r.samples[0][0][0] = 0.f;
    r.samples[0][0][1] = 1.f;
    r.desc->reset(r.state);
    r.run({}, 2);
    REQUIRE(bus.rows[0].rises == 2 && bus.rows[0].falls == 1);
    REQUIRE(bus.rows[0].value == 1.f);

    // Also exercise OscOut::process's zero-frame guard directly (the SDK
    // adapter short-circuits zero frames before calling the module).
    osc::OscOut direct;
    ws2_process empty{};
    ws::Block block(empty);
    direct.process(block);
    REQUIRE(direct.local_bus.rows[0].blocks == 0);
}

static void gate_threshold_matches_sender() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    cfg.rows[0].kind = 1;
    cfg.bus = &bus;
    Rig r(&cfg);
    // Sender §4 uses value >= 0.5; DSP must count that same threshold.
    r.samples[0][0][0] = .5f;
    r.samples[0][0][1] = .5f;
    r.samples[0][0][2] = .499f;
    r.run({}, 3);
    REQUIRE(bus.rows[0].rises == 1 && bus.rows[0].falls == 1);
    REQUIRE(bus.rows[0].blocks == 1 && bus.rows[0].value == .499f);
}

static void thousand_gate_crossings_in_one_block() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    cfg.rows[0].kind = 1;
    cfg.bus = &bus;
    Rig r(&cfg);
    // A render block may contain far more crossings than the sender's per-poll budget.
    for (uint32_t i = 0; i < 1000; ++i) r.samples[0][0][i] = i % 2 == 0 ? 1.f : 0.f;
    r.run({}, 1001);
    REQUIRE(bus.rows[0].rises == 500);
    REQUIRE(bus.rows[0].falls == 500);
    REQUIRE(bus.rows[0].blocks == 1 && bus.rows[0].value == 0.f);
}

static void note_ring_and_no_bus() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    REQUIRE(osc::out_configuration(nullptr, 0, cfg));
    cfg.notes.enabled = 1;
    cfg.bus = &bus;
    Rig r(&cfg);
    r.run({note(NoteKind::On, 60), note(NoteKind::Off, 60)}, 1);
    REQUIRE(bus.note_head == 2 && bus.note_tail == 0 && bus.dropped == 0);
    REQUIRE(bus.notes[0].key == 60 && bus.notes[0].channel == 2 && bus.notes[0].velocity == .75f);
    REQUIRE(bus.notes[1].key == 60 && bus.notes[1].velocity == 0.f);
    std::vector<ws2_event> burst;
    burst.reserve(64);
    for (int i = 0; i < 64; ++i) burst.push_back(note(NoteKind::On, i));
    r.run(burst, 1);
    REQUIRE(bus.note_head == 64 && bus.dropped == 2); // head 2 + 62 slots available
    bus.note_tail.store(64, std::memory_order_release);
    r.run({note(NoteKind::Choke, 70)}, 1);
    REQUIRE(bus.note_head == 65 && bus.dropped == 2 && bus.notes[0].velocity == 0.f);

    cfg.bus = nullptr;
    Rig detached(&cfg);
    detached.samples[0][0][0] = .2f;
    detached.run({note(NoteKind::On, 60)}, 1); // private bus, no sender or device
    Rig defaults;
    defaults.run({}, 1); // no binary config also initializes defaults
}
// E3c fail-first: disable and re-enable a row without replacing the
// producer or resetting the consumer-owned counters.
static void live_output_routes() {
    osc::OutBus bus;
    osc::OutConfiguration cfg;
    cfg.bus = &bus;
    Rig rig(&cfg);
    REQUIRE(rig.desc->data_slot_count == 1);
    const auto &slot = rig.desc->data_slots[0];
    const ws2_field *rows = nullptr, *enabled = nullptr;
    for (uint32_t i = 0; i < slot.field_count; ++i)
        if (std::strcmp(slot.fields[i].id, "rows") == 0) rows = &slot.fields[i];
    REQUIRE(rows && rows->type == WS2_F_RECORD && rows->count == 8);
    alignas(16) std::array<uint8_t, WS2_MAX_DATA_BYTES> packed{};
    for (uint32_t row = 0; row < rows->count; ++row) {
        auto *dst = packed.data() + rows->offset + row * rows->stride;
        for (uint32_t i = 0; i < rows->field_count; ++i) {
            const auto &field = rows->fields[i];
            if (field.type == WS2_F_F32) {
                const float v = float(field.initial);
                std::memcpy(dst + field.offset, &v, sizeof(v));
            } else if (field.type == WS2_F_U32 || field.type == WS2_F_ENUM) {
                const uint32_t v = uint32_t(field.initial);
                std::memcpy(dst + field.offset, &v, sizeof(v));
            } else if (field.type == WS2_F_BOOL || field.type == WS2_F_U8) {
                dst[field.offset] = uint8_t(field.initial);
                if (std::strcmp(field.id, "enabled") == 0) enabled = &field;
            } else if (field.type == WS2_F_TEXT && std::strcmp(field.id, "address") == 0) {
                std::snprintf(reinterpret_cast<char *>(dst + field.offset), field.count, "/ws/row/%u", row + 1);
            }
        }
    }
    REQUIRE(enabled && enabled->type == WS2_F_BOOL);
    ws2_data data{sizeof(ws2_data), packed.data(), slot.bytes, 1};
    rig.ctx.data_count = 1; rig.ctx.data = &data;
    rig.samples[0][0][0] = .25f;
    rig.run({}, 1);
    REQUIRE(bus.rows[0].blocks == 1 && bus.rows[1].blocks == 1 && bus.rows[0].value == .25f);
    packed[rows->offset + enabled->offset] = 0;
    ++data.serial;
    rig.samples[0][0][0] = .75f;
    rig.run({}, 1);
    REQUIRE(bus.rows[0].blocks == 1 && bus.rows[1].blocks == 2 && bus.rows[0].value == .25f);
    packed[rows->offset + enabled->offset] = 1;
    ++data.serial;
    rig.run({}, 1);
    REQUIRE(bus.rows[0].blocks == 2 && bus.rows[1].blocks == 3 && bus.rows[0].value == .75f);
}
int main() {
    live_output_routes();
    {
        osc::OutBus bus;
        osc::OutConfiguration cfg;
        cfg.bus = &bus;
        cfg.rows[0].kind = 1;
        Rig rig(&cfg);
        char error[128]{};
        REQUIRE(osc::validate_osc_out_routes(rig.slot_data, error));
        rig.samples[0][0][0] = 1.f;
        rig.run({}, 1);
        REQUIRE(bus.rows[0].rises == 1);
        rig.slot_data.rows[0].enabled = 0;
        ++rig.view.serial;
        rig.run({}, 1);
        rig.slot_data.rows[0].enabled = 1;
        ++rig.view.serial;
        rig.run({}, 1);
        REQUIRE(bus.rows[0].rises == 1 && bus.rows[0].falls == 0);
        rig.samples[0][0][0] = 0.f;
        rig.run({}, 1);
        REQUIRE(bus.rows[0].falls == 1);
        auto invalid = rig.slot_data;
        std::strcpy(invalid.rows[3].address, "/bad/*");
        REQUIRE(!osc::validate_osc_out_routes(invalid, error));
        REQUIRE(std::strstr(error, "routes.rows[3].address") != nullptr);
        invalid = rig.slot_data;
        std::strcpy(invalid.notes_address, "bad");
        REQUIRE(!osc::validate_osc_out_routes(invalid, error));
        REQUIRE(std::strstr(error, "routes.notes_address") != nullptr);
    }
    configuration_checks();
    rows_and_gate_edges();
    gate_reset_primes_without_phantom_edges();
    gate_threshold_matches_sender();
    thousand_gate_crossings_in_one_block();
    note_ring_and_no_bus();
}
