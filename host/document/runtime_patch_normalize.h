// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include <nlohmann/json_fwd.hpp>
#include <string>
#include <vector>

namespace wirescape::document {
std::vector<std::string> normalize_stored_modulation(nlohmann::json &connections, int version);
}
