// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <memory>
#include <new>
#include <string>
#include <vector>

namespace wirescape::engine2 {
struct DataBlockDelete {
    void operator()(uint8_t *p) const noexcept { ::operator delete(p, std::align_val_t(16)); }
};
using DataBlock = std::unique_ptr<uint8_t, DataBlockDelete>;
inline DataBlock allocate_data_block(uint32_t bytes) {
    DataBlock block(static_cast<uint8_t *>(::operator new(bytes, std::align_val_t(16))));
    std::memset(block.get(), 0, bytes);
    return block;
}
inline bool data_id_valid(const char *id) {
    if (!id || *id < 'a' || *id > 'z') return false;
    for (++id; *id; ++id)
        if (!((*id >= 'a' && *id <= 'z') || (*id >= '0' && *id <= '9') || *id == '_')) return false;
    return true;
}
inline uint32_t data_element_bytes(const ws2_field &f) {
    switch (f.type) {
        case WS2_F_F32: case WS2_F_I32: case WS2_F_U32: case WS2_F_ENUM: return 4;
        case WS2_F_U8: case WS2_F_BOOL: case WS2_F_TEXT: return 1;
        case WS2_F_RECORD: return f.stride;
        default: return 0;
    }
}
inline bool data_default_valid(const ws2_field &f) {
    const double v = f.initial;
    if (!std::isfinite(f.minimum) || !std::isfinite(f.maximum) || !std::isfinite(v) ||
        v < f.minimum || v > f.maximum) return false;
    switch (f.type) {
        case WS2_F_F32: return std::abs(v) <= std::numeric_limits<float>::max();
        case WS2_F_I32: return std::trunc(v) == v && v >= INT32_MIN && v <= INT32_MAX;
        case WS2_F_U32: return std::trunc(v) == v && v >= 0 && v <= UINT32_MAX;
        case WS2_F_U8: return std::trunc(v) == v && v >= 0 && v <= UINT8_MAX;
        case WS2_F_BOOL: return v == 0 || v == 1;
        case WS2_F_ENUM: return std::trunc(v) == v && v >= 0 && v < f.option_count;
        case WS2_F_TEXT: case WS2_F_RECORD: return true;
        default: return false;
    }
}
// Control-only descriptor validation. Validate before using any offsets to pack.
inline bool validate_data_fields(const ws2_field *fields, uint32_t count, uint32_t bytes,
                                 bool record, const std::string &prefix, std::string &error,
                                 uint32_t &alignment) {
    alignment = 1;
    if (count > WS2_MAX_FIELDS || (count && !fields)) {
        error = prefix + ": invalid field table";
        return false;
    }
    std::vector<uint8_t> occupied(bytes, 0);
    for (uint32_t i = 0; i < count; ++i) {
        const auto &f = fields[i];
        if (f.struct_size < sizeof(ws2_field)) {
            error = prefix + ": short field descriptor";
            return false;
        }
        const std::string name = prefix + "." + (f.id ? f.id : "(null)");
        auto fail = [&] { error = name + ": invalid field descriptor"; return false; };
        if (!data_id_valid(f.id) || !f.name || !f.count || !data_default_valid(f)) return fail();
        for (uint32_t j = 0; j < i; ++j)
            if (!std::strcmp(fields[j].id, f.id)) return fail();
        const auto size = data_element_bytes(f);
        if (!size || (f.type != WS2_F_RECORD && f.stride)) return fail();
        const uint64_t end = uint64_t(f.offset) + uint64_t(size) * f.count;
        if (end > bytes) return fail();
        uint32_t field_align = size == 4 && f.type != WS2_F_RECORD ? 4u : 1u;
        if (f.type == WS2_F_RECORD) {
            if (record) return fail();
            if (!validate_data_fields(f.fields, f.field_count, f.stride, true, name, error, field_align)) return false;
            if (f.stride % field_align) return fail();
        } else if (f.field_count || f.fields) return fail();
        if (f.offset % field_align) return fail();
        alignment = std::max(alignment, field_align);
        if (f.type == WS2_F_ENUM) {
            if (!f.option_count || !f.options) return fail();
            for (uint32_t j = 0; j < f.option_count; ++j) {
                if (!f.options[j]) return fail();
                for (uint32_t k = 0; k < j; ++k)
                    if (!std::strcmp(f.options[j], f.options[k])) return fail();
            }
        } else if (f.option_count || f.options) return fail();
        if (f.length_field != WS2_NO_FIELD) {
            if (f.length_field >= count || f.length_field == i || f.type == WS2_F_TEXT) return fail();
            const auto &length = fields[f.length_field];
            if (length.struct_size < sizeof(ws2_field) || length.type != WS2_F_U32 ||
                length.count != 1 || length.length_field != WS2_NO_FIELD) return fail();
        }
        for (uint32_t j = f.offset; j < end; ++j) {
            if (occupied[j]) return fail();
            occupied[j] = 1;
        }
    }
    return true;
}
inline void pack_data_defaults(const ws2_field *fields, uint32_t count, uint8_t *block) {
    for (uint32_t i = 0; i < count; ++i) {
        const auto &f = fields[i];
        // Variable-length arrays and their generated counts start empty.
        if (f.length_field != WS2_NO_FIELD || f.type == WS2_F_TEXT || f.type == WS2_F_RECORD) continue;
        bool generated = false;
        for (uint32_t j = 0; j < count; ++j)
            if (fields[j].length_field == i) generated = true;
        if (generated) continue;
        for (uint32_t j = 0; j < f.count; ++j) {
            auto *p = block + f.offset + j * data_element_bytes(f);
            switch (f.type) {
                case WS2_F_F32: { const auto v = static_cast<float>(f.initial); std::memcpy(p, &v, 4); break; }
                case WS2_F_I32: { const auto v = static_cast<int32_t>(f.initial); std::memcpy(p, &v, 4); break; }
                case WS2_F_U32: case WS2_F_ENUM: { const auto v = static_cast<uint32_t>(f.initial); std::memcpy(p, &v, 4); break; }
                case WS2_F_U8: case WS2_F_BOOL: *p = static_cast<uint8_t>(f.initial); break;
                default: break;
            }
        }
    }
}
inline bool initialize_data_slots(const ws2_descriptor &d, std::vector<DataBlock> &blocks,
                                  std::vector<ws2_data> &views, std::string &error) {
    if (d.struct_size < offsetof(ws2_descriptor, data_slot_count) + sizeof(d.data_slot_count) ||
        !d.data_slot_count) return true;
    if (d.data_slot_count > WS2_MAX_DATA_SLOTS ||
        d.struct_size < offsetof(ws2_descriptor, data_slots) + sizeof(d.data_slots) || !d.data_slots) {
        error = "Invalid ABI2 data slot table";
        return false;
    }
    for (uint32_t i = 0; i < d.data_slot_count; ++i) {
        const auto &s = d.data_slots[i];
        if (s.struct_size < sizeof(ws2_data_slot)) { error = "Short data slot descriptor"; return false; }
        const std::string name = s.id ? s.id : "(null)";
        if (!data_id_valid(s.id) || !s.name || !s.bytes || s.bytes > WS2_MAX_DATA_BYTES || s.flags) {
            error = name + ": invalid data slot"; return false;
        }
        for (uint32_t j = 0; j < i; ++j)
            if (!std::strcmp(d.data_slots[j].id, s.id)) { error = name + ": duplicate data slot"; return false; }
        uint32_t alignment = 1;
        if (!validate_data_fields(s.fields, s.field_count, s.bytes, false, name, error, alignment)) return false;
        auto block = allocate_data_block(s.bytes);
        pack_data_defaults(s.fields, s.field_count, block.get());
        views.push_back({sizeof(ws2_data), block.get(), s.bytes, 1});
        blocks.push_back(std::move(block));
    }
    return true;
}
} // namespace wirescape::engine2
