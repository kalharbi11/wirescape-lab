// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../../modules/groove/data.h"
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

} // namespace wirescape::document
