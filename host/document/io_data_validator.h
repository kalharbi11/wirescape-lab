// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host catalogue adapter. Never interpret vector<uint8_t> storage as an
// aligned object; the generic packer has already checked scalar fields.
#include "../../modules/midi_cc_to_cv/data_validation.h"
#include "../../modules/osc_in/data_validation.h"
#include "../../modules/osc_out/data_validation.h"
#include <cstring>
#include <string>
#include <vector>

namespace wirescape::document {
template <class T, bool (*Validate)(const T &, char (&)[128])>
bool validate_io_data(const ws2_data_slot &slot, const std::vector<uint8_t> &bytes, std::string &error) {
    if (slot.bytes != sizeof(T) || bytes.size() != sizeof(T)) {
        error = std::string(slot.id) + ": incompatible slot byte size";
        return false;
    }
    T data{};
    std::memcpy(&data, bytes.data(), sizeof(data));
    char diagnostic[128]{};
    if (Validate(data, diagnostic)) return true;
    error = diagnostic;
    return false;
}
} // namespace wirescape::document
