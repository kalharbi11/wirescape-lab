// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "config.h"
#include "wirescape_sdk.h"
#include <array>
#include <cstdint>
#include <cstring>

namespace wirescape::osc {
inline constexpr const char *osc_out_kinds[] = {"cv", "gate"};
#define WS_OSC_OUT_ROW_FIELDS(X) \
    X(char, address, [64], WS2_F_TEXT, ws::data_range(0, 0, 0)) \
    X(uint32_t, kind, , WS2_F_ENUM, ws::data_options(osc_out_kinds, 0)) \
    X(float, deadband, , WS2_F_F32, ws::data_range(0, 1, 0.001)) \
    X(uint8_t, enabled, , WS2_F_BOOL, ws::data_range(0, 1, 1))
struct OscOutRowData {
#define WS_DECLARE(type, id, extent, kind, rules) type id extent;
    WS_OSC_OUT_ROW_FIELDS(WS_DECLARE)
#undef WS_DECLARE
};
inline constexpr std::array osc_out_row_fields{
#define WS_DESCRIBE(type, id, extent, kind, rules) \
    ws::data_field<kind, decltype(OscOutRowData::id)>(#id, #id, offsetof(OscOutRowData, id), rules),
    WS_OSC_OUT_ROW_FIELDS(WS_DESCRIBE)
#undef WS_DESCRIBE
};
#undef WS_OSC_OUT_ROW_FIELDS
#define WS_OSC_OUT_FIELDS(X) \
    X(OscOutRowData, rows, [8], WS2_F_RECORD, ws::data_record(osc_out_row_fields)) \
    X(char, notes_address, [64], WS2_F_TEXT, ws::data_range(0, 0, 0)) \
    X(uint8_t, notes_enabled, , WS2_F_BOOL, ws::data_range(0, 1, 0))
struct OscOutRoutes {
#define WS_DECLARE(type, id, extent, kind, rules) type id extent;
    WS_OSC_OUT_FIELDS(WS_DECLARE)
#undef WS_DECLARE
};
inline constexpr std::array osc_out_fields{
#define WS_DESCRIBE(type, id, extent, kind, rules) \
    ws::data_field<kind, decltype(OscOutRoutes::id)>(#id, #id, offsetof(OscOutRoutes, id), rules),
    WS_OSC_OUT_FIELDS(WS_DESCRIBE)
#undef WS_DESCRIBE
};
#undef WS_OSC_OUT_FIELDS
struct OscOut {
    static constexpr ws::Info info{"osc.out", "OSC Out", 1};
    static constexpr std::array inputs{ws::port("row1", "Row 1", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row2", "Row 2", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row3", "Row 3", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row4", "Row 4", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row5", "Row 5", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row6", "Row 6", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row7", "Row 7", WS2_CV_BI, WS2_FIRST),
                                       ws::port("row8", "Row 8", WS2_CV_BI, WS2_FIRST),
                                       ws::port("notes", "Notes", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array<ws2_port, 0> outputs{};
    static constexpr std::array<ws2_param, 0> params{};

    static constexpr std::array data_slots{ws::data_slot<OscOutRoutes>("routes", "Routes", osc_out_fields)};
    uint32_t last_serial = 0;
    std::array<bool, 8> gate_active{};
    OutBus local_bus{};
    OutBus *bus = &local_bus;
    std::array<bool, 8> high{};
    bool has_processed = false;
    bool prime_after_reset = false;

    bool prepare(const ws::Setup &setup) {
        OutConfiguration config{};
        if (!out_configuration(setup.config.data, setup.config.bytes, config)) return false;
        bus = config.bus ? config.bus : &local_bus;
        return true;
    }
    void reset() {
        // prepare() calls reset() too: preserve the initial block's real edges.
        // On panic, use the next nonempty block's first sample as a new baseline.
        prime_after_reset = has_processed;
        last_serial = 0;
        gate_active.fill(false);
        high.fill(false); // Consumer owns shared bus counters and ring tails.
    }

    void process(ws::Block &block) {
        const uint32_t frames = block.frames();
        if (!frames) return; // No sample available to establish a gate baseline.
        uint32_t serial = 0;
        const auto *routes = block.data<OscOutRoutes>(0, serial);
        if (!routes) return;
        const bool changed = serial != last_serial;
        for (uint32_t i = 0; i < 8; ++i) {
            const auto &cfg = routes->rows[i];
            const bool gate = cfg.enabled && cfg.kind == 1;
            // A newly enabled gate observes its current level, not a synthetic
            // leading edge. Initial processing still counts real edges.
            const bool prime = prime_after_reset || (has_processed && changed && gate && !gate_active[i]);
            gate_active[i] = gate;
            if (!cfg.enabled) continue;
            const auto signal = block.in(i).ch(0); // FIRST poly policy: only voice 0
            const bool constant = block.in(i).constant();
            const float last = signal[constant ? 0 : frames - 1];
            uint32_t rises = 0, falls = 0;
            if (gate) {
                bool was = prime ? signal[0] >= .5f : high[i];
                for (uint32_t s = prime ? 1u : 0u; s < frames; ++s) {
                    const bool now = signal[constant ? 0 : s] >= .5f;
                    if (now != was) {
                        if (now) ++rises;
                        else ++falls;
                        was = now;
                    }
                }
                high[i] = was;
            }
            auto &row = bus->rows[i];
            row.value.store(last, std::memory_order_relaxed);
            if (rises) row.rises.fetch_add(rises, std::memory_order_relaxed);
            if (falls) row.falls.fetch_add(falls, std::memory_order_relaxed);
            row.blocks.fetch_add(1, std::memory_order_release);
        }
        last_serial = serial;
        has_processed = true;
        prime_after_reset = false;
        if (!routes->notes_enabled) return;
        for (const auto &event : block.events()) {
            if (event.type != WS2_NOTE_ON && event.type != WS2_NOTE_OFF && event.type != WS2_NOTE_CHOKE) continue;
            const uint32_t head = bus->note_head.load(std::memory_order_relaxed);
            const uint32_t tail = bus->note_tail.load(std::memory_order_acquire);
            if (head - tail >= bus->notes.size()) {
                bus->dropped.fetch_add(1, std::memory_order_relaxed);
                continue;
            }
            bus->notes[head % bus->notes.size()] =
                OutNote{static_cast<int16_t>(event.key), static_cast<int16_t>(event.channel),
                        event.type == WS2_NOTE_ON ? event.value : 0.f};
            bus->note_head.store(head + 1, std::memory_order_release);
        }
    }
    int save_state(ws::Writer w) { return w.u32(1) ? WS2_OK : WS2_CAPACITY; }
    int load_state(ws::Reader r) {
        uint32_t version = 0;
        if (!r.u32(version)) return WS2_INVALID;
        if (version != 1) return WS2_UNSUPPORTED;
        reset();
        return WS2_OK;
    }
};
} // namespace wirescape::osc
