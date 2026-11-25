// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only Groove migration adapter. The portable module neither parses JSON
// nor allocates. Shared loader and Session call sites are integrated separately.
#include "../../modules/groove/data.h"
#include "runtime_module_config.h"
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
#include <vector>

namespace wirescape::document {
inline bool validate_groove_data_slot(const ws2_data_slot &slot,
                                      const std::vector<uint8_t> &packed, std::string &error) {
    const auto result = groove::validate_pattern_slot(slot, packed.data(), packed.size());
    if (result) return true;
    error = result.field;
    if (result.row >= 0) error += "[" + std::to_string(result.row) + "]";
    error += ": invalid Groove pattern field";
    return false;
}

// Generated row counts are intentionally absent from the authored object.
// Preserve every decoded row, including rows outside the current track length.
// Float values have already been validated and rounded by the legacy decoder.
inline nlohmann::json groove_pattern_value(const groove::LivePattern &data) {
    using Json = nlohmann::json;
    auto rows = [](const groove::Step *steps, uint32_t count) {
        Json out = Json::array();
        for (uint32_t i = 0; i < count; ++i) {
            const auto &s = steps[i];
            // A default rest can omit all fields; the table supplies the same
            // audible defaults. Unused chord entries have no playback meaning.
            if (s.kind == groove::Rest && s.key == 60 && s.velocity == 0.f &&
                s.mod1 == 0.f && s.mod2 == 0.f && s.gate_q == 4 &&
                s.cond_type == groove::Always && s.cond_a == 0 &&
                s.cond_b == 0 && s.key_count == 1 && s.keys[0] == 60) {
                out.push_back(Json::object());
                continue;
            }
            out.push_back({{"kind", groove::step_kinds[s.kind]}, {"key", s.key},
                           {"velocity", s.velocity}, {"mod1", s.mod1}, {"mod2", s.mod2},
                           {"gate_q", s.gate_q}, {"cond_type", s.cond_type},
                           {"cond_a", s.cond_a}, {"cond_b", s.cond_b},
                           {"key_count", s.key_count}, {"keys", s.keys}});
        }
        return out;
    };
    return {{"length_1", data.length_1}, {"length_2", data.length_2},
            {"tempo_source", groove::tempo_sources[data.tempo_source]},
            {"steps_1", rows(data.steps_1, data.count_1)},
            {"steps_2", rows(data.steps_2, data.count_2)}};
}

inline groove::Config decode_groove_legacy_config(const nlohmann::json &config, uint32_t instance_id) {
    // Use the legacy implementation directly: the future public runtime
    // wrapper must not recurse through this adapter.
    const auto bytes = runtime_module_config_impl("sequencing.groove", config, instance_id, nullptr);
    groove::Config decoded{};
    if (!groove::decode(bytes.data(), static_cast<uint32_t>(bytes.size()), decoded))
        throw std::runtime_error("Invalid Groove legacy config");
    return decoded;
}

inline nlohmann::json groove_legacy_pattern_value(const nlohmann::json &config, uint32_t instance_id) {
    return groove_pattern_value(groove::materialize_legacy_pattern(
        decode_groove_legacy_config(config, instance_id)));
}

// The new live slot owns the steps, lengths and tempo source. Construction
// bytes retain only version/seed, BPM, track count, armed/mute and divisors;
// equal construction settings compare identically for live replan regardless
// of pattern edits. ZeroFilledConfig ensures padding stays canonical (E0).
inline std::vector<uint8_t> groove_construction_bytes(const nlohmann::json &legacy, uint32_t instance_id) {
    const auto source = decode_groove_legacy_config(legacy, instance_id);
    ZeroFilledConfig<groove::Config> storage;
    auto &config = storage.get();
    config.bpm = source.bpm;
    config.track_count = source.track_count;
    config.instance_seed = source.instance_seed;
    config.authored_version = source.authored_version;
    for (uint32_t t = 0; t < config.track_count; ++t) {
        config.tracks[t].armed = source.tracks[t].armed;
        config.tracks[t].mute = source.tracks[t].mute;
        config.tracks[t].div = source.tracks[t].div;
    }
    return storage.bytes();
}

// Only materialize an absent legacy slot. An explicit pattern, even an empty
// object, is not overwritten. The caller retains the existing stored/edit
// validation policy and independently normalizes construction-only config.
inline void materialize_groove_legacy_data(nlohmann::json &module, uint32_t instance_id) {
    using Json = nlohmann::json;
    auto data = module.value("data", Json::object());
    if (!data.is_object()) throw std::runtime_error("data: expected object");
    if (data.contains("pattern")) return;
    const auto config = module.value("config", Json::object());
    data["pattern"] = groove_legacy_pattern_value(config, instance_id);
    module["data"] = std::move(data);
}
} // namespace wirescape::document
