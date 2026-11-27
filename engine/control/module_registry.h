// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "app_engine.h"

namespace wirescape::app {
// Built from the same folder discovery in native and Web. The returned
// descriptors have static lifetime and are ordered by their ABI IDs.
const std::vector<const ws2_descriptor *> &builtin_modules();
AppDataValidator builtin_data_validator(const ws2_descriptor *d);
} // namespace wirescape::app
