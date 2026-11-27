// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// A77, E3c: one control-side migration for loader and route owners.
// Use the existing legacy parser and the generic slot packer; do not parse
// data in the render thread or turn legacy rows into construction config.
#include "runtime_module_config.h"
#include "io_data_validator.h"
#include "../../engine/data_pack.h"

namespace wirescape::document {
using IoJson = nlohmann::json;
inline const char *io_slot_id(const std::string &type) {
    if (type == "midi.cc_to_cv") return "mapping";
    if (type == "osc.in" || type == "osc.out") return "routes";
    return nullptr;
}
inline IoJson cc_data_json(const midi::CcRows &data) {
    IoJson rows = IoJson::array();
    for (const auto &r : data.rows)
        rows.push_back({{"channel", r.channel}, {"controller", r.controller},
                        {"fourteen_bit", bool(r.fourteen_bit)}, {"smoothing_ms", r.smoothing_ms},
                        {"min", r.min}, {"max", r.max}});
    return {{"rows", std::move(rows)}};
}
inline IoJson osc_in_data_json(const osc::OscInRows &data) {
    IoJson rows = IoJson::array();
    for (const auto &r : data.rows)
        rows.push_back({{"pattern", r.pattern}, {"argument", r.argument},
                        {"kind", osc::osc_in_kinds[r.kind]}, {"input_min", r.input_min},
                        {"input_max", r.input_max}, {"output_min", r.output_min}, {"output_max", r.output_max},
                        {"smoothing_ms", r.smoothing_ms}, {"timeout_ms", r.timeout_ms},
                        {"stale", osc::osc_in_stale[r.stale]}, {"enabled", bool(r.enabled)}});
    return {{"rows", std::move(rows)}};
}
inline IoJson osc_out_data_json(const osc::OscOutRoutes &data) {
    IoJson rows = IoJson::array();
    for (const auto &r : data.rows)
        rows.push_back({{"address", r.address}, {"kind", osc::osc_out_kinds[r.kind]},
                        {"deadband", r.deadband}, {"enabled", bool(r.enabled)}});
    return {{"rows", std::move(rows)}, {"notes_address", data.notes_address},
            {"notes_enabled", bool(data.notes_enabled)}};
}
inline IoJson legacy_io_data(const std::string &type, const IoJson &config, uint32_t node,
                             std::vector<std::string> *warnings = nullptr) {
    // Legacy config parsing preserves partial rows, per-row defaults, bipolar
    // endpoints, device settings validation and the existing range rules.
    const auto bytes = runtime_module_config_impl(type, config, node, warnings);
    char diagnostic[128]{};
    if (type == "midi.cc_to_cv") {
        midi::CcConfiguration legacy{};
        midi::CcRows data{};
        if (!midi::cc_configuration(bytes.data(), uint32_t(bytes.size()), legacy))
            throw std::runtime_error("Invalid CC configuration");
        if (!midi::materialize_cc_rows(legacy, data, diagnostic))
            throw std::runtime_error(std::string("data.") + diagnostic);
        return cc_data_json(data);
    }
    if (type == "osc.in") {
        osc::Configuration legacy{};
        osc::OscInRows data{};
        if (!osc::configuration(bytes.data(), uint32_t(bytes.size()), legacy))
            throw std::runtime_error("Invalid OSC In configuration");
        if (!osc::materialize_osc_in_rows(legacy, data, diagnostic))
            throw std::runtime_error(std::string("data.") + diagnostic);
        return osc_in_data_json(data);
    }
    if (type == "osc.out") {
        osc::OutConfiguration legacy{};
        osc::OscOutRoutes data{};
        if (!osc::out_configuration(bytes.data(), uint32_t(bytes.size()), legacy))
            throw std::runtime_error("Invalid OSC Out configuration");
        if (!osc::materialize_osc_out_routes(legacy, data, diagnostic))
            throw std::runtime_error(std::string("data.") + diagnostic);
        return osc_out_data_json(data);
    }
    throw std::runtime_error("Not an I/O data module");
}
// Descriptor defaults are scalar-wide, not row-indexed (and text defaults
// are empty). Complete absent fields with the module's historical defaults,
// but leave wrong types, lengths, unknown keys and explicit values intact
// for the generic packer and its StoredDocument/Edit policy to decide.
inline IoJson complete_io_slot(const std::string &type, const std::string &slot, IoJson value) {
    const auto *id = io_slot_id(type);
    if (!id || slot != id || !value.is_object()) return value;
    const auto defaults = legacy_io_data(type, IoJson::object(), 0);
    for (auto it = defaults.begin(); it != defaults.end(); ++it) {
        if (!value.contains(it.key())) value[it.key()] = it.value();
        else if (it.key() == "rows" && value["rows"].is_array() &&
                 value["rows"].size() == it.value().size()) {
            for (size_t i = 0; i < it.value().size(); ++i) {
                auto &row = value["rows"][i];
                if (!row.is_object()) continue;
                const auto &fallback = it.value()[i];
                for (auto field = fallback.begin(); field != fallback.end(); ++field)
                    if (!row.contains(field.key())) row[field.key()] = field.value();
            }
        }
    }
    return value;
}
// An execution copy only. Explicit slot data wins over legacy config rows,
// even when those rows disagree. Port/LAN/rate and non-row config are not data.
inline void migrate_io_module(IoJson &module, std::vector<std::string> *warnings = nullptr) {
    const auto type = module.value("module", std::string{});
    const auto *slot = io_slot_id(type);
    if (!slot) return;
    auto config = module.value("config", IoJson::object());
    auto data = module.value("data", IoJson::object());
    if (!config.is_object()) throw std::runtime_error("Module config must be an object");
    if (!data.is_object()) throw std::runtime_error("data: expected object");
    const auto node = module.at("id").get<uint32_t>();
    if (!data.contains(slot)) data[slot] = legacy_io_data(type, config, node, warnings);
    else data[slot] = complete_io_slot(type, slot, data.at(slot));
    // SC1: the caller supplied an execution copy. The authored rows retain their labels;
    // the generic route packer sees only its actual execution fields.
    if (type == "osc.in" && data[slot].is_object() && data[slot].contains("rows") &&
        data[slot]["rows"].is_array())
        for (auto &row : data[slot]["rows"])
            if (row.is_object()) row.erase("label");
    config.erase("rows");
    if (type == "osc.out") config.erase("notes");
    if (config.empty()) module.erase("config");
    else module["config"] = std::move(config);
    module["data"] = std::move(data);
}
// A host route uses exactly the same generic packing and module validator
// as the engine candidate, not a second data schema or row parser.
template <class T, class Module, bool (*Validate)(const T &, char (&)[128])>
T read_io_slot(const IoJson &module) {
    const auto &slot = Module::data_slots[0];
    std::vector<uint8_t> packed;
    std::string error;
    if (!ws::data_layout::pack_data_slot(slot, module.at("data").at(slot.id),
            ws::data_layout::DataLoad::StoredDocument, packed, error, nullptr, validate_io_data<T, Validate>))
        throw std::runtime_error("data." + error);
    T result{};
    std::memcpy(&result, packed.data(), sizeof(result));
    return result;
}
} // namespace wirescape::document
