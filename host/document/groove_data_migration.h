// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only Groove migration adapter. The portable module neither parses JSON
// nor allocates. Shared loader and Session call sites are integrated separately.
#include "groove_data_validator.h"
#include "runtime_module_config.h"
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
#include <vector>

namespace wirescape::document {
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
    auto source = config;
    // Canonical construction-only tracks omit steps. Reuse the strict
    // legacy parser for all remaining fields; provide one silent row only
    // for that shape, never silently repair a partially legacy document.
    if (source.is_object() && source.contains("tracks") && source["tracks"].is_array() &&
        !source["tracks"].empty()) {
        bool construction_only = true;
        for (const auto &track : source["tracks"])
            construction_only &= track.is_object() && !track.contains("steps") && !track.contains("length");
        if (construction_only && !source.contains("tempo_source"))
            for (auto &track : source["tracks"])
                track["steps"] = nlohmann::json::array({{{"kind", "rest"}}});
    }
    const auto bytes = runtime_module_config_impl("sequencing.groove", source, instance_id, nullptr);
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

// Execution copy only. Legacy rows are removed after materialization, so a
// later removal of the slot resets to defaults and never resurrects a pattern.
// The caller owns the saved source document and its unknown fields.
inline void materialize_groove_legacy_data(nlohmann::json &module, uint32_t instance_id) {
    using Json = nlohmann::json;
    if (module.value("module", std::string{}) != "sequencing.groove") return;
    auto config = module.value("config", Json::object());
    auto data = module.value("data", Json::object());
    if (!config.is_object()) throw std::runtime_error("Module config must be an object");
    if (!data.is_object()) throw std::runtime_error("data: expected object");
    // A legacy shape has actual pattern fields. A canonical shape does not.
    bool legacy = config.contains("tempo_source");
    if (config.contains("tracks") && config["tracks"].is_array())
        for (const auto &track : config["tracks"])
            legacy |= track.is_object() && (track.contains("steps") || track.contains("length"));
    if (!data.contains("pattern"))
        data["pattern"] = legacy ? groove_legacy_pattern_value(config, instance_id) : Json::object();
    // Validate legacy configuration even when explicit slot data wins.
    // This preserves the prior malformed-config refusal.
    (void)decode_groove_legacy_config(config, instance_id);
    config.erase("tempo_source");
    if (config.contains("tracks") && config["tracks"].is_array())
        for (auto &track : config["tracks"]) {
            track.erase("steps");
            track.erase("length");
        }
    if (config.empty()) module.erase("config");
    else module["config"] = std::move(config);
    module["data"] = std::move(data);
}
} // namespace wirescape::document
