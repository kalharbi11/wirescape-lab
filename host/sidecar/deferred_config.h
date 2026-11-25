// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "protocol.h"
#include <chrono>
#include <cstdint>
#include <map>
#include <string>

namespace wirescape::sidecar {
// Control-owned deferred config state; no catalogue injection or render hook.
struct PendingConfig {
    std::string module, defer_id;
    Json config;
    std::chrono::steady_clock::time_point deadline;
};
inline Json deferred_config_event(const std::string &session, uint32_t id,
                                  const PendingConfig &pending, const char *outcome, uint64_t generation) {
    return {{"v", 0}, {"session", session}, {"type", "configDeferred"},
            {"deferId", pending.defer_id}, {"moduleId", id}, {"outcome", outcome},
            {"generation", std::to_string(generation)}};
}
// A81: only changed data on an actual instance replacement supersedes.
// Mutate the staged queue/event copy; publish it only on accepted graph commit.
inline void stage_data_supersession(std::map<uint32_t, PendingConfig> &pending,
                                    Json &events, const std::string &session,
                                    uint32_t id, bool changed, bool replaced, uint64_t generation) {
    if (!changed || !replaced) return;
    const auto it = pending.find(id);
    if (it == pending.end()) return;
    events.push_back(deferred_config_event(session, id, it->second, "superseded", generation));
    pending.erase(it);
}
} // namespace wirescape::sidecar
