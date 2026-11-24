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
// A topology entry belongs to exactly one layout; the instance can outlive it.
// Layouts reference instances; only the control owner owns their lifetime.
struct Node {
    Instance &instance;
    Slot slot;
    explicit Node(Instance &value) : instance(value) {}
    Node(const Node &) = delete;
    Node &operator=(const Node &) = delete;
};

// Topology is built before publication. Scratch buffers and telemetry values
// are mutable render state; the routing entries are not edited after adoption.
struct Layout {
    std::vector<std::unique_ptr<Node>> nodes;
    std::vector<Edge> edges;
    std::vector<Component> components;
    std::vector<std::pair<uint32_t, Node *>> node_table;
    std::array<uint32_t, 32> bus_latency{};
    std::vector<uint32_t> distance;
    std::vector<Bus> buses;
    std::vector<Tap> taps;
    std::vector<Node *> tap_nodes;
    std::unique_ptr<std::atomic<float>[]> tap_values;
    std::unique_ptr<std::atomic<uint32_t>[]> tap_counts;

    Edge *find_mod_edge(uint32_t from, uint32_t output, uint32_t to, uint32_t input) noexcept {
        const auto key = std::tuple{from, output, to, input, 2};
        auto edge = std::lower_bound(edges.begin(), edges.end(), key,
                                     [](const Edge &e, const auto &k) { return e.key() < k; });
        // A transition may contain a retired and a live edge with the same key.
        // Never deliver a live amount packet to the retired edge.
        for (; edge != edges.end() && edge->key() == key; ++edge)
            if (!edge->removed) return &*edge;
        return nullptr;
    }
};
} // namespace wirescape::engine2
