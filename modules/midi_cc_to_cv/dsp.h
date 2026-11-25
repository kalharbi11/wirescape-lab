// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "config.h"
#include "wirescape_sdk.h"
#include <algorithm>
#include <limits>
namespace wirescape::midi {
// A77: endpoints are F32; the host materializes effective legacy endpoints
// (including bipolar defaults), with independent bounds for inverted ranges.
inline constexpr float cc_data_limit = std::numeric_limits<float>::max();
#define WS_CC_ROW_FIELDS(X) \
    X(uint8_t, channel, WS2_F_U8, ws::data_range(0, 16, 0)) \
    X(uint8_t, controller, WS2_F_U8, ws::data_range(0, 127, 1)) \
    X(uint8_t, fourteen_bit, WS2_F_BOOL, ws::data_range(0, 1, 0)) \
    X(float, smoothing_ms, WS2_F_F32, ws::data_range(0, 2000, 5)) \
    X(float, min, WS2_F_F32, ws::data_range(-cc_data_limit, cc_data_limit, 0)) \
    X(float, max, WS2_F_F32, ws::data_range(-cc_data_limit, cc_data_limit, 1))
struct CcRowData {
#define WS_DECLARE(type, id, kind, rules) type id;
    WS_CC_ROW_FIELDS(WS_DECLARE)
#undef WS_DECLARE
};
inline constexpr std::array cc_row_fields{
#define WS_DESCRIBE(type, id, kind, rules) \
    ws::data_field<kind, decltype(CcRowData::id)>(#id, #id, offsetof(CcRowData, id), rules),
    WS_CC_ROW_FIELDS(WS_DESCRIBE)
#undef WS_DESCRIBE
};
#undef WS_CC_ROW_FIELDS
struct CcRows { CcRowData rows[8]; };
inline constexpr std::array cc_data_fields{
    ws::data_field<WS2_F_RECORD, decltype(CcRows::rows)>(
        "rows", "Rows", offsetof(CcRows, rows), ws::data_record(cc_row_fields))};
struct CcToCv {
    static constexpr ws::Info info{"midi.cc_to_cv", "CC to CV", 1};
    static constexpr std::array inputs{ws::port("midi", "MIDI", WS2_EV_MIDI, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array outputs{ws::port("cc1", "CC 1", WS2_CV_BI), ws::port("cc2", "CC 2", WS2_CV_BI), ws::port("cc3", "CC 3", WS2_CV_BI), ws::port("cc4", "CC 4", WS2_CV_BI), ws::port("cc5", "CC 5", WS2_CV_BI), ws::port("cc6", "CC 6", WS2_CV_BI), ws::port("cc7", "CC 7", WS2_CV_BI), ws::port("cc8", "CC 8", WS2_CV_BI)};
    static constexpr std::array<ws2_param, 0> params{};
    static constexpr std::array data_slots{ws::data_slot<CcRows>("mapping", "Mapping", cc_data_fields)};
    uint32_t last_serial = 0;
    double rate = 48000;
    // Match the service's full 16-endpoint x 16-channel identity space.
    static constexpr size_t identity_capacity = size_t{16} * 16;
    struct Row {
        double current = 0, target = 0, coefficient = 1;
        std::array<uint8_t, identity_capacity> msb{}, lsb{};
        uint32_t pairing_key = 0; // derived identity, not a retained data block
    };
    std::array<Row, 8> rows{};
    struct Source { bool used = false; uint32_t id = 0, channel = 0; };
    std::array<Source, identity_capacity> sources{};
    uint64_t dropped = 0;
    int token(uint32_t id, uint32_t channel) {
        int free = -1;
        for (uint32_t i = 0; i < sources.size(); ++i) { if (sources[i].used && sources[i].id == id && sources[i].channel == channel) return int(i); if (!sources[i].used && free < 0) free = int(i); }
        if (free < 0) return -1;
        sources[free] = {true, id, channel}; return free;
    }
    bool prepare(const ws::Setup& s) {
        CcConfiguration legacy;
        if (!cc_configuration(s.config.data, s.config.bytes, legacy)) return false;
        rate = s.sample_rate();
        return true;
    }
    void reset() {
        sources = {};
        dropped = 0;
        rows = {};
        last_serial = 0;
    }
    void derive(const CcRows &data, uint32_t serial) {
        for (uint32_t i = 0; i < rows.size(); ++i) {
            const auto &cfg = data.rows[i];
            auto &row = rows[i];
            const uint32_t key = uint32_t(cfg.channel) | (uint32_t(cfg.controller) << 8) |
                                 (uint32_t(cfg.fourteen_bit) << 16);
            // Never pair a fragment from a previous controller/channel/mode.
            if (row.pairing_key != key) {
                row.msb.fill(0); row.lsb.fill(0);
                row.pairing_key = key;
            }
            if (!last_serial) row.current = row.target = cfg.min;
            row.coefficient = cfg.smoothing_ms > 0 ? 1. - std::exp(-1000. / (cfg.smoothing_ms * rate)) : 1.;
        }
        last_serial = serial;
    }
    void event(const ws2_event& e, const CcRows &data) {
        if (e.type == WS2_NOTE_CHOKE) {
            for (uint32_t t = 0; t < sources.size(); ++t) if (sources[t].used && (e.source_id == UINT32_MAX || sources[t].id == e.source_id)) { sources[t] = {}; for (auto& row : rows) row.msb[t] = row.lsb[t] = 0; }
            return; // continuous controls hold their last target on disconnect
        }
        if (e.type != WS2_MIDI || !e.ump_words) return;
        const uint32_t type = e.ump[0] >> 28;
        if ((e.ump[0] >> 24) & 15) return; // J maps group zero; other groups remain available on raw MIDI.
        if ((type != 2 && type != 4) || ((e.ump[0] >> 20) & 15) != 11 || (type == 4 && e.ump_words < 2)) return;
        const uint32_t channel = (e.ump[0] >> 16) & 15, controller = (e.ump[0] >> 8) & 127;
        for (uint32_t i = 0; i < rows.size(); ++i) {
            const auto& cfg = data.rows[i]; auto& row = rows[i];
            if (cfg.channel && channel != cfg.channel - 1) continue;
            double normalized;
            if (type == 4) { if (controller != cfg.controller) continue; normalized = double(e.ump[1]) / 4294967295.; }
            else if (cfg.fourteen_bit) {
                if (controller != cfg.controller && controller != cfg.controller + 32) continue;
                const int source = token(e.source_id, channel); if (source < 0) { ++dropped; continue; }
                if (controller == cfg.controller) row.msb[source] = uint8_t(e.ump[0] & 127); else row.lsb[source] = uint8_t(e.ump[0] & 127);
                normalized = double(uint32_t(row.msb[source]) * 128 + row.lsb[source]) / 16383.;
            } else { if (controller != cfg.controller) continue; normalized = double(e.ump[0] & 127) / 127.; }
            row.target = double(cfg.min) * (1. - normalized) + double(cfg.max) * normalized;
        }
    }
    void process(ws::Block& b) {
        uint32_t serial = 0;
        const auto *data = b.data<CcRows>(0, serial);
        if (!data) return;
        if (serial != last_serial) derive(*data, serial);
        for (uint32_t p = 0; p < 8; ++p) { b.out(p).set_channels(1); b.out(p).mark_constant(false); }
        b.split([&](uint32_t first, uint32_t end) {
            for (uint32_t p = 0; p < 8; ++p) for (uint32_t i = first; i < end; ++i) {
                    auto &row = rows[p];
                    // A convex update avoids intermediate overflow for inverted finite endpoints.
                    row.current = (1. - row.coefficient) * row.current + row.coefficient * row.target;
                    if (std::abs(row.current - row.target) < 1e-7) row.current = row.target;
                    const double limit = double(std::numeric_limits<float>::max());
                    b.out(p).ch(0)[i] = float(std::clamp(row.current, -limit, limit));
            }
        }, [&](const ws2_event& e) { event(e, *data); });
    }
    int save_state(ws::Writer w) { return w.u32(1) ? WS2_OK : WS2_CAPACITY; }
    int load_state(ws::Reader r) { uint32_t v; if (!r.u32(v)) return WS2_INVALID; if (v != 1) return WS2_UNSUPPORTED; reset(); return WS2_OK; }
};
}
