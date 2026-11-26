// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only A77 validator. Scalar limits are checked by the generic packer.
#include "dsp.h"
#include <cstdio>
namespace wirescape::osc {
inline bool valid_out_data_address(const char *text, size_t size) {
    const auto *end = static_cast<const char *>(std::memchr(text, 0, size));
    if (!end || end - text < 2 || text[0] != '/') return false;
    for (const char *p = text; p != end; ++p) {
        const unsigned char ch = static_cast<unsigned char>(*p);
        if (ch < 33 || ch > 126 || std::strchr("#*,?[]{}", ch)) return false;
    }
    return true;
}
inline bool validate_osc_out_routes(const OscOutRoutes &data, char (&error)[128]) {
    error[0] = '\0';
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &r = data.rows[i];
        if (!valid_out_data_address(r.address, sizeof(r.address))) {
            std::snprintf(error, sizeof(error), "routes.rows[%u].address: invalid literal OSC address", i);
            return false;
        }
    }
    if (!valid_out_data_address(data.notes_address, sizeof(data.notes_address))) {
        std::snprintf(error, sizeof(error), "%s", "routes.notes_address: invalid literal OSC address");
        return false;
    }
    return true;
}
// Off-RT conversion of already validated legacy config, including all eight
// row-specific defaults. Host-owned pointers are deliberately excluded.
inline bool materialize_osc_out_routes(const OutConfiguration &legacy, OscOutRoutes &out, char (&error)[128]) {
    OscOutRoutes candidate{};
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &src = legacy.rows[i];
        auto &dst = candidate.rows[i];
        std::memcpy(dst.address, src.address, sizeof(dst.address));
        dst.kind = src.kind; dst.deadband = src.deadband; dst.enabled = uint8_t(src.enabled);
    }
    std::memcpy(candidate.notes_address, legacy.notes.address, sizeof(candidate.notes_address));
    candidate.notes_enabled = uint8_t(legacy.notes.enabled);
    if (!validate_osc_out_routes(candidate, error)) return false;
    out = candidate;
    return true;
}
} // namespace wirescape::osc
