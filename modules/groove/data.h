// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "config.h"
#include "wirescape_sdk.h"
#include <cstddef>

namespace groove {
// Flat records, one variable-length step array per track. Construction-time
// configuration still owns the stable seed, armed/mute defaults and divisors.
// Zero lengths in the engine's unmaterialized default block select legacy
// config for old direct callers; the shared document migration must supply
// both approved lengths and materialize canonical rows.
struct LivePattern {
    uint32_t length_1, length_2, count_1, count_2, tempo_source;
    Step steps_1[64], steps_2[64];
};
inline constexpr const char *step_kinds[]{"rest", "note", "tie"};
inline constexpr const char *tempo_sources[]{"internal", "host"};
inline constexpr std::array live_step_fields{
    ws::data_field<WS2_F_ENUM, uint32_t>("kind", "Kind", offsetof(Step, kind), ws::data_options(step_kinds, 0)),
    ws::data_field<WS2_F_I32, int32_t>("key", "Key", offsetof(Step, key), ws::data_range(0, 127, 60)),
    ws::data_field<WS2_F_F32, float>("velocity", "Velocity", offsetof(Step, velocity), ws::data_range(0, 1, 0)),
    ws::data_field<WS2_F_F32, float>("mod1", "Mod 1", offsetof(Step, mod1), ws::data_range(0, 1, 0)),
    ws::data_field<WS2_F_F32, float>("mod2", "Mod 2", offsetof(Step, mod2), ws::data_range(0, 1, 0)),
    ws::data_field<WS2_F_U8, uint8_t>("gate_q", "Gate quarters", offsetof(Step, gate_q), ws::data_range(1, 4, 4)),
    ws::data_field<WS2_F_U8, uint8_t>("cond_type", "Condition", offsetof(Step, cond_type), ws::data_range(0, 4, 0)),
    ws::data_field<WS2_F_U8, uint8_t>("cond_a", "Condition A", offsetof(Step, cond_a), ws::data_range(0, 99, 0)),
    ws::data_field<WS2_F_U8, uint8_t>("cond_b", "Condition B", offsetof(Step, cond_b), ws::data_range(0, 8, 0)),
    ws::data_field<WS2_F_U8, uint8_t>("key_count", "Key count", offsetof(Step, key_count), ws::data_range(1, 5, 1)),
    // std::array's contiguous int32_t storage is the existing fixed POD layout.
    ws::data_field<WS2_F_I32, int32_t[5]>("keys", "Chord keys", offsetof(Step, keys), ws::data_range(0, 127, 60))
};
static_assert(sizeof(Step::keys) == sizeof(int32_t[5]));
inline constexpr std::array live_pattern_fields{
    ws::data_field<WS2_F_U32, uint32_t>("length_1", "Track 1 length", offsetof(LivePattern, length_1), ws::data_range(0, 64, 0)),
    ws::data_field<WS2_F_U32, uint32_t>("length_2", "Track 2 length", offsetof(LivePattern, length_2), ws::data_range(0, 64, 0)),
    ws::data_field<WS2_F_U32, uint32_t>("count_1", "Track 1 row count", offsetof(LivePattern, count_1), ws::data_range(0, 64, 0)),
    ws::data_field<WS2_F_U32, uint32_t>("count_2", "Track 2 row count", offsetof(LivePattern, count_2), ws::data_range(0, 64, 0)),
    ws::data_field<WS2_F_ENUM, uint32_t>("tempo_source", "Tempo source", offsetof(LivePattern, tempo_source), ws::data_options(tempo_sources, 0)),
    ws::data_field<WS2_F_RECORD, Step[64]>("steps_1", "Track 1 steps", offsetof(LivePattern, steps_1), ws::data_record(live_step_fields, 2)),
    ws::data_field<WS2_F_RECORD, Step[64]>("steps_2", "Track 2 steps", offsetof(LivePattern, steps_2), ws::data_record(live_step_fields, 3))
};
inline bool valid_live_length(uint32_t length) noexcept {
    return length == 8 || length == 16 || length == 32 || length == 64;
}
inline bool valid_live_pattern(const LivePattern &data) noexcept {
    if (!valid_live_length(data.length_1) || !valid_live_length(data.length_2) ||
        data.count_1 > 64 || data.count_2 > 64 || data.tempo_source > TempoHost) return false;
    for (uint32_t i = 0; i < data.count_1; ++i) if (!valid_step(data.steps_1[i])) return false;
    for (uint32_t i = 0; i < data.count_2; ++i) if (!valid_step(data.steps_2[i])) return false;
    return true;
}
} // namespace groove
