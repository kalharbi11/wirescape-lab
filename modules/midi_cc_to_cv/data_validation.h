// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only: generic packing validates scalar types/ranges before this check.
#include "dsp.h"
#include <string>
namespace wirescape::midi {
inline bool validate_cc_rows(const CcRows &data, std::string &error) {
    error.clear();
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &row = data.rows[i];
        if (row.fourteen_bit && row.controller > 31) {
            error = "mapping.rows[" + std::to_string(i) + "].controller: 14-bit controller must be 0..31";
            return false;
        }
    }
    return true;
}
// Called off RT after the existing legacy parser has materialized partial
// rows. Conversion is one-way, and refusal leaves the destination untouched.
inline bool materialize_cc_rows(const CcConfiguration &legacy, CcRows &out, std::string &error) {
    CcRows candidate{};
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &r = legacy.rows[i];
        const double min = r.minimum(), max = r.maximum();
        const auto prefix = "mapping.rows[" + std::to_string(i) + "].";
        if (!std::isfinite(min) || std::abs(min) > double(cc_data_limit)) {
            error = prefix + "min: outside finite F32 range";
            return false;
        }
        if (!std::isfinite(max) || std::abs(max) > double(cc_data_limit)) {
            error = prefix + "max: outside finite F32 range";
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
