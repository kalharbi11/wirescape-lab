// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only: generic packing validates scalar types/ranges before this check.
#include "dsp.h"
#include <cstdio>
namespace wirescape::midi {
inline bool validate_cc_rows(const CcRows &data, char (&error)[128]) {
    error[0] = '\0';
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &row = data.rows[i];
        if (row.fourteen_bit && row.controller > 31) {
            std::snprintf(error, sizeof(error), "mapping.rows[%u].controller: 14-bit controller must be 0..31", i);
            return false;
        }
    }
    return true;
}
// Called off RT after the existing legacy parser has materialized partial
// rows. Conversion is one-way, and refusal leaves the destination untouched.
inline bool materialize_cc_rows(const CcConfiguration &legacy, CcRows &out, char (&error)[128]) {
    CcRows candidate{};
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &r = legacy.rows[i];
        const double min = r.minimum(), max = r.maximum();
        if (!std::isfinite(min) || std::abs(min) > double(cc_data_limit)) {
            std::snprintf(error, sizeof(error), "mapping.rows[%u].min: outside finite F32 range", i);
            return false;
        }
        if (!std::isfinite(max) || std::abs(max) > double(cc_data_limit)) {
            std::snprintf(error, sizeof(error), "mapping.rows[%u].max: outside finite F32 range", i);
            return false;
        }
        candidate.rows[i] = {r.channel, r.controller, r.fourteen_bit, r.smoothing_ms,
                             static_cast<float>(min), static_cast<float>(max)};
    }
    if (!validate_cc_rows(candidate, error)) return false;
    out = candidate;
    return true;
}
} // namespace wirescape::midi
