// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape/module2.h"

#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>
namespace wirescape::osc {
struct Route {
    uint32_t node = 0;
    uint16_t port = 9000;
    bool lan = false;
};
struct Sink {
    void *context = nullptr;
    int (*deliver)(void *, uint32_t node, const ws2_event &, uint64_t timestamp_ns) noexcept = nullptr;
    // Optional worker-thread filter (#612): false skips one decoded message for
    // one route before delivery, without counting it as received or dropped.
    bool (*accept)(void *, uint32_t node, std::string_view address) noexcept = nullptr;
};
struct RouteState {
    uint32_t node = 0;
    uint16_t port = 0;
    bool lan_requested = false;
    bool lan_bound = false;
    const char *state = "port-busy"; // listening | port-busy | lan-not-confirmed
    uint64_t received = 0, dropped = 0;
    // Budget discards count on every enabled route sharing this listener;
    // enqueue refusals count only on the route whose delivery failed.
    uint64_t budget_dropped = 0, enqueue_dropped = 0;
    uint64_t listener_budget_dropped = 0, listener_enqueue_dropped = 0;
};
struct ListenerState {
    uint16_t port = 0; // actual bound port (including OS-assigned test ports)
    uint64_t dropped = 0, budget_dropped = 0, enqueue_dropped = 0;
};
struct Counters {
    uint64_t received = 0, malformed = 0, dropped = 0, truncated = 0;
    uint32_t sockets = 0;
    // Global legacy dropped additionally includes oversized/encode failures.
    uint64_t budget_dropped = 0, enqueue_dropped = 0;
};
// One network worker polls all ports; one socket per distinct port is shared by its routes.
// add() is quiescent; LAN needs both Route.lan and Service(confirm_lan=true).
class Service {
    struct Impl;
    std::unique_ptr<Impl> impl_;

  public:
    explicit Service(Sink, bool confirm_lan = false);
    ~Service();
    bool add(Route);
    bool start();
    void stop(); // join acquisition before host engine destruction
    const std::string &error() const;
    Counters counters() const noexcept;
    // Control-thread snapshot only. Every route has an independent bounded count.
    std::vector<RouteState> states() const;
    // Physical listeners, not one entry per route. Like states(), this is a
    // control-thread observational snapshot, not a transactional read.
    std::vector<ListenerState> listener_states() const;
    uint16_t bound_port(uint32_t socket = 0) const; // tests may add port0 for OS-assigned localhost port
};
} // namespace wirescape::osc
