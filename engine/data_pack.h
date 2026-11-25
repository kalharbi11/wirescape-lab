// SPDX-License-Identifier: MIT
// Control/host-only generic JSON packing. Do not include from portable DSP.
#pragma once
#include "data_layout.h"
#include <array>
#include <nlohmann/json.hpp>

namespace ws::data_layout {
enum class DataLoad { Edit, StoredDocument };
// Host-only optional cross-field validation, after packing defaults and scalars.
// A callback inspects bytes (copy to an aligned typed value if needed), and
// returns a slot-relative field diagnostic on refusal. Never call from DSP.
using DataValidator = bool (*)(const ws2_data_slot &, const std::vector<uint8_t> &, std::string &);

inline bool valid_text(const std::string &text) {
    // NUL-terminated storage cannot represent an interior U+0000.
    for (size_t i = 0; i < text.size();) {
        const auto first = static_cast<uint8_t>(text[i++]);
        if (!first) return false;
        if (first < 0x80) continue;
        uint32_t code = 0, minimum = 0, remaining = 0;
        if (first >= 0xc2 && first <= 0xdf) { code = first & 0x1f; minimum = 0x80; remaining = 1; }
        else if (first >= 0xe0 && first <= 0xef) { code = first & 0x0f; minimum = 0x800; remaining = 2; }
        else if (first >= 0xf0 && first <= 0xf4) { code = first & 0x07; minimum = 0x10000; remaining = 3; }
        else return false;
        if (remaining > text.size() - i) return false;
        while (remaining--) {
            const auto next = static_cast<uint8_t>(text[i++]);
            if ((next & 0xc0) != 0x80) return false;
            code = (code << 6) | (next & 0x3f);
        }
        if (code < minimum || code > 0x10ffff || (code >= 0xd800 && code <= 0xdfff)) return false;
    }
    return true;
}
inline bool generated_length(const ws2_field *fields, uint32_t count, uint32_t i) {
    for (uint32_t j = 0; j < count; ++j) if (fields[j].length_field == i) return true;
    return false;
}
template<class T> inline void write_scalar(uint8_t *p, T v) { std::memcpy(p, &v, sizeof(v)); }

inline bool pack_scalar(const ws2_field &f, const nlohmann::json &value, uint8_t *p) {
    if (f.type == WS2_F_BOOL) {
        if (!value.is_boolean()) return false;
        *p = value.get<bool>() ? 1 : 0;
        return true;
    }
    if (f.type == WS2_F_ENUM) {
        if (!value.is_string()) return false;
        const auto &name = value.get_ref<const std::string &>();
        for (uint32_t i = 0; i < f.option_count; ++i) {
            if (name == f.options[i]) { write_scalar(p, i); return true; }
        }
        return false;
    }
    if (!value.is_number()) return false;
    const double v = value.get<double>();
    if (!std::isfinite(v) || v < f.minimum || v > f.maximum) return false;
    if (f.type == WS2_F_F32) {
        if (std::abs(v) > std::numeric_limits<float>::max()) return false;
        write_scalar(p, static_cast<float>(v));
        return true;
    }
    if (std::trunc(v) != v) return false;
    switch (f.type) {
        case WS2_F_I32:
            if (v < INT32_MIN || v > INT32_MAX) return false;
            write_scalar(p, static_cast<int32_t>(v)); return true;
        case WS2_F_U32:
            if (v < 0 || v > UINT32_MAX) return false;
            write_scalar(p, static_cast<uint32_t>(v)); return true;
        case WS2_F_U8:
            if (v < 0 || v > UINT8_MAX) return false;
            *p = static_cast<uint8_t>(v); return true;
        default: return false;
    }
}
inline bool pack_fields(const ws2_field *fields, uint32_t count, const nlohmann::json &object,
                        uint8_t *block, const std::string &prefix, DataLoad policy,
                        std::vector<std::string> &warnings, std::string &error) {
    if (!object.is_object()) { error = prefix + ": expected object"; return false; }
    // No write to the original document: stored unknown keys remain authored
    // while the packed block omits them. Generated length fields have no key.
    for (auto it = object.begin(); it != object.end(); ++it) {
        bool known = false;
        for (uint32_t i = 0; i < count; ++i)
            if (it.key() == fields[i].id && !generated_length(fields, count, i)) { known = true; break; }
        if (known) continue;
        const std::string message = prefix + "." + it.key() + ": unknown field";
        if (policy == DataLoad::Edit) { error = message; return false; }
        warnings.push_back(message);
    }
    pack_data_defaults(fields, count, block);
    std::array<uint32_t, WS2_MAX_FIELDS> lengths{};
    std::array<bool, WS2_MAX_FIELDS> length_written{};
    for (uint32_t i = 0; i < count; ++i) {
        const auto &f = fields[i];
        if (generated_length(fields, count, i)) continue;
        const auto value = object.find(f.id);
        const auto path = prefix + "." + f.id;
        auto fail = [&] { error = path + ": invalid type, value or length"; return false; };
        uint8_t *p = block + f.offset;
        const bool variable = f.length_field != WS2_NO_FIELD;
        if (f.type == WS2_F_TEXT) {
            if (value == object.end()) continue;
            if (!value->is_string()) return fail();
            const auto &text = value->get_ref<const std::string &>();
            if (text.size() >= f.count || !valid_text(text)) return fail();
            std::memcpy(p, text.data(), text.size());
            continue;
        }
        const bool array = f.count > 1 || variable || f.type == WS2_F_RECORD;
        uint32_t n = 0;
        if (value != object.end()) {
            if (array) {
                if (!value->is_array() || value->size() > f.count ||
                    (!variable && value->size() != f.count)) return fail();
                n = static_cast<uint32_t>(value->size());
            } else n = 1;
        }
        if (variable) {
            const auto index = f.length_field;
            if (length_written[index] && lengths[index] != n) return fail();
            length_written[index] = true;
            lengths[index] = n;
            write_scalar(block + fields[index].offset, n);
        }
        if (value == object.end()) continue;
        const auto stride = data_element_bytes(f);
        for (uint32_t j = 0; j < n; ++j) {
            const auto &element = array ? (*value)[j] : *value;
            const auto element_path = array ? path + "[" + std::to_string(j) + "]" : path;
            if (f.type == WS2_F_RECORD) {
                if (!pack_fields(f.fields, f.field_count, element, p + j * stride, element_path,
                                 policy, warnings, error)) return false;
            } else if (!pack_scalar(f, element, p + j * stride)) {
                error = element_path + ": invalid type or value";
                return false;
            }
        }
    }
    return true;
}
// Transactional output: an invalid edit leaves both output and warnings alone.
inline bool pack_data_slot(const ws2_data_slot &slot, const nlohmann::json &value, DataLoad policy,
                           std::vector<uint8_t> &out, std::string &error,
                           std::vector<std::string> *warnings = nullptr, DataValidator validator = nullptr) {
    error.clear();
    if (slot.struct_size < sizeof(ws2_data_slot) || !data_id_valid(slot.id) ||
        !slot.name || !slot.bytes || slot.bytes > WS2_MAX_DATA_BYTES || slot.flags) {
        error = "Invalid data slot descriptor"; return false;
    }
    uint32_t alignment = 1;
    if (!validate_data_fields(slot.fields, slot.field_count, slot.bytes, false, slot.id, error, alignment)) return false;
    std::vector<uint8_t> candidate(slot.bytes, 0);
    std::vector<std::string> pending;
    if (!pack_fields(slot.fields, slot.field_count, value, candidate.data(), slot.id, policy, pending, error)) return false;
    if (validator && !validator(slot, candidate, error)) {
        if (error.empty()) error = std::string(slot.id) + ": data validation refused";
        return false;
    }
    if (warnings) warnings->insert(warnings->end(), pending.begin(), pending.end());
    out.swap(candidate);
    return true;
}
} // namespace ws::data_layout
