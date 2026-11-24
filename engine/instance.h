// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "types.h"
#include <limits>

namespace wirescape::engine2 {
struct Allocation {
    void *p;
    size_t alignment, bytes;
    uint32_t hint;
};
// proposals/0007 (T1.6b): what belongs to one module instance (survives an edit).
struct Instance {
    uint32_t id = 0;
    const ws2_descriptor *d = nullptr;
    uint64_t born_revision = 0;
    void *instance = nullptr;
    std::vector<ws2_port> inputs, outputs;
    std::vector<ws2_param> parameters;
    std::vector<Parameter> state;
    std::vector<uint8_t> config, preserved;
    std::vector<Allocation> allocations;
    std::vector<Buffer> local_out, global_out, param;
    std::vector<double> modulation_sum;
    std::vector<ws2_signal_out> out_view;
    std::vector<std::vector<ws2_event>> port_events;
    std::vector<ws2_event_list> event_view;
    std::vector<ws2_event_out> event_outputs;
    // Render-owned oscillator observation, never read by the control owner.
    struct Pitch {
        bool enabled = false, vco = false;
        uint32_t latest = 0, input = 0, trigger = 0, gate = 0, tune = 0;
        std::array<int32_t, WS2_MAX_CHANNELS> note{};
        std::array<bool, WS2_MAX_CHANNELS> note_on{}, high{};
        float value = std::numeric_limits<float>::quiet_NaN();
    } pitch;
    std::vector<ws2_event> events;
    std::vector<Item> pending;
    int forced_channels = -1;
    uint32_t channels = 1;
    std::atomic<uint32_t> latency{0};
    bool latency_dirty = false; // Render-owned; refresh once at end of the changed block.
    size_t requested_fast = 0, requested_large = 0;
    void *emit_context = nullptr;
    ~Instance() { clear_instance(); }
    void clear_instance() {
        if (instance) {
            if (d) d->destroy(instance);
            instance = nullptr;
        }
        for (auto &a : allocations) ::operator delete(a.p, std::align_val_t(a.alignment));
        allocations.clear();
        requested_fast = requested_large = 0;
    }
    static void *WS2_CALL allocate(void *ctx, size_t bytes, size_t alignment, uint32_t hint) {
        auto &n = *static_cast<Instance *>(ctx);
        if (n.allocations.size() == n.allocations.capacity() || !alignment || (alignment & (alignment - 1)) ||
            bytes > 128 * 1024 * 1024)
            return nullptr;
        alignment = std::max(alignment, size_t(32));
        bytes = std::max(bytes, size_t(1));
        void *p = ::operator new(bytes, std::align_val_t(alignment), std::nothrow);
        if (p) {
            n.allocations.push_back({p, alignment, bytes, hint});
            if (hint == WS2_LARGE) n.requested_large += bytes;
            else n.requested_fast += bytes;
        }
        return p;
    }
    ws2_host host() { return {sizeof(ws2_host), this, allocate}; }
};
// proposals/0007 (T1.6b): what belongs to one topology (rebuilt by an edit).
} // namespace wirescape::engine2
