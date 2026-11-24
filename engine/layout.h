// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "instance.h"

namespace wirescape::engine2 {
struct Slot {
    uint32_t index = 0, component = 0;
    bool loop = false, touched = false;
    std::vector<Edge *> incoming, signal_edges;
    std::vector<std::vector<Edge *>> modulation, outgoing;
    std::vector<Buffer> in;
    std::vector<ws2_signal> in_view, param_view;
    std::vector<uint32_t> event_tap_slots; // Precomputed event-output -> telemetry slot; empty when untapped.
};
// In T1.6 a Slot lives beside its Instance and both move together, as Node did.
struct Node {
    Instance instance;
    Slot slot;
    ~Node() { instance.clear_instance(); }
};
} // namespace wirescape::engine2
