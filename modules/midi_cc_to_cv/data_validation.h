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
} // namespace wirescape::midi
