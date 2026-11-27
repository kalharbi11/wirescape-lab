// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "protocol.h"
#include <string>
#include <vector>

namespace wirescape::sidecar {
// Test-first interface. The intentionally empty red implementation is replaced
// only after the deterministic controller capture tests have failed.
class ControllerStream {
public:
    void configure(const std::vector<std::string> &, bool) {}
    Json drain() { return Json::array(); }
    Json status() const { return nullptr; }
};
} // namespace wirescape::sidecar
