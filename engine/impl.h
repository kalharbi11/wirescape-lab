// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "layout.h"
#include <map>
#include <utility>

namespace wirescape::engine2 {
static_assert(std::atomic<Layout *>::is_always_lock_free, "Layout publication must be lock-free");

bool valid_tap(const Node *, const Tap &);

struct Engine::Impl {
    Config cfg;
    std::string error;
    // Control-owned storage, independent of the layout's topology entries.
    std::map<uint32_t, std::unique_ptr<Instance>> instances;
    std::map<EdgeState *, std::unique_ptr<EdgeState>> edge_states;
    std::unique_ptr<Layout> layout = std::make_unique<Layout>(); // control-only
    Layout *render_layout = nullptr; // render-only after prepare
    std::atomic<Layout *> pending_layout{nullptr};
    std::array<std::unique_ptr<Producer>, 32> producers;
    uint32_t producer_count = 0, dropped_connections = 0;
    std::unique_ptr<Producer> egress;
    std::vector<Packet> future;
    std::vector<uint8_t> arena;
    bool prepared = false;
    std::atomic_flag rendering = ATOMIC_FLAG_INIT;
    std::atomic<uint64_t> tap_sequence{0};
    std::atomic<uint64_t> tap_frame{0};
    std::atomic<uint64_t> published_revision{0}, adopted_revision{0};
    std::atomic<uint64_t> position{0}, generation{1}, applied{1}, event_count{0}, dropped{0}, coalesced{0},
        ring_full{0}, stale{0}, late{0}, emergencies{0}, arena_full{0}, faults{0};
    std::atomic<bool> egress_emergency{false};
    uint64_t anchor_frame = 0, anchor_ns = 0, sequence = 0, block_start = 0;
    double frames_per_ns = 0, beat = 0;
    uint64_t transport_sent = 0; // Control owner only.
    uint64_t transport_applied = 0; // Render owner after prepare.
    bool reset_beat = false; // Set only by quiescent reset, consumed by render.
    std::atomic<uint32_t> arena_used{0};
    uint32_t block_frames = 0, ordinary_used = 0, critical_used = 0;
    std::atomic<uint32_t> feedback_count{0}, latency{0};
    std::atomic<size_t> setup_bytes{0};
    Node *processing = nullptr;
    uint32_t processing_start = 0, processing_frames = 0;
    explicit Impl(Config c) : cfg(c), anchor_ns(c.epoch_ns), frames_per_ns(c.sample_rate / 1.e9) {
        layout->nodes.reserve(cfg.max_nodes);
        future.reserve(cfg.future_capacity);
    }
    Node *find(uint32_t id) const {
        if (prepared) return layout->find(id);
        for (auto &n : layout->nodes)
            if (n->instance.id == id) return n.get();
        return nullptr;
    }
    bool fail(const char *s) {
        error = s;
        return false;
    }
    uint64_t map_time(uint64_t ns) const noexcept {
        const bool before = ns < anchor_ns;
        const uint64_t delta = before ? anchor_ns - ns : ns - anchor_ns;
        long double distance;
        if (frames_per_ns == cfg.sample_rate / 1.e9 && cfg.sample_rate == std::floor(cfg.sample_rate)) {
            const uint64_t rate = static_cast<uint64_t>(cfg.sample_rate), seconds = delta / UINT64_C(1000000000);
            if (seconds > UINT64_MAX / rate) return before ? 0 : UINT64_MAX;
            distance =
                static_cast<long double>(seconds * rate) + (delta % UINT64_C(1000000000)) * rate / UINT64_C(1000000000);
        } else distance = std::floor(static_cast<long double>(delta) * frames_per_ns);
        if (distance > static_cast<long double>(UINT64_MAX / 2)) return before ? 0 : UINT64_MAX;
        const uint64_t d = static_cast<uint64_t>(distance);
        if (before) return d > anchor_frame ? 0 : anchor_frame - d;
        return d > UINT64_MAX - anchor_frame ? UINT64_MAX : anchor_frame + d;
    }
    uint64_t map_frame(uint64_t frame) const noexcept {
        const long double t =
            static_cast<long double>(anchor_ns) + (static_cast<long double>(frame) - anchor_frame) / frames_per_ns;
        return t < 0 ? 0 : t > UINT64_MAX ? UINT64_MAX : static_cast<uint64_t>(t);
    }
    void emergency() noexcept {
        auto g = generation.load(std::memory_order_acquire);
        if (g == applied.load(std::memory_order_acquire) &&
            generation.compare_exchange_strong(g, g + 1, std::memory_order_acq_rel))
            ++emergencies;
        egress_emergency.store(true, std::memory_order_release);
    }
    void reset_processors() noexcept {
        for (auto &n : render_layout->nodes) {
            n->instance.d->reset(n->instance.instance);
            n->instance.pitch.latest = 0;
            n->instance.pitch.note_on.fill(false);
            n->instance.pitch.high.fill(false);
            n->instance.pitch.value = std::numeric_limits<float>::quiet_NaN();
            for (auto &p : n->instance.state) {
                p.base.reset();
                p.offset.fill(0);
            }
            n->instance.pending.clear();
        }
        for (auto &e : render_layout->edges)
            if (e.back && e.kind != 1) {
                e.state->head = 0;
                std::fill(e.state->delay_channels.begin(), e.state->delay_channels.end(), 0);
                if (e.state->delay.memory) std::fill_n(e.state->delay.memory.get(), cfg.max_channels * e.state->delay.stride, 0.f);
            }
        future.clear();
    }
    bool topology();
    bool wire_edges();
    void find_components();
    bool order_feedback_components();
    bool order_components();
    bool stage_reconfiguration(Engine &next, uint32_t node, const std::vector<uint8_t> &config);
    bool plan_edge_transitions(Impl &fresh, const std::vector<Node *> &actual,
                               std::vector<bool> &used, std::vector<bool> &delay_used,
                               std::vector<std::pair<uint32_t, uint32_t>> &chokes,
                               std::vector<std::array<uint32_t, 4>> &removed_routes,
                               std::vector<std::pair<size_t, size_t>> &delays);
    void recompute_latency() noexcept;
    void adopt_layout(Layout *) noexcept;
    bool finish_prepare();
    bool resolve_taps();
    bool setup(Node &);
    bool valid_target(const Node &, uint32_t, const ws2_event &) const;
    bool admit(Node &, uint32_t, const ws2_event &, uint64_t, uint64_t, bool cleanup = false);
    Edge *find_mod_edge(uint32_t from, uint32_t output, uint32_t to, uint32_t input) noexcept;
    uint32_t mod_ramp_frames() const noexcept { return static_cast<uint32_t>(cfg.sample_rate * .005); }
    void apply_host_packet(const Packet &) noexcept;
    void collect();
    bool route(uint32_t, const ws2_event &);
    void process_node(Node &, uint32_t, uint32_t);
    void gather_events(Instance &, uint32_t start, uint32_t frames);
    uint32_t edge_channels(const Edge &, uint32_t frames) const;
    float edge_sample(const Edge &, uint32_t channel, uint32_t sample, uint32_t start) const;
    uint32_t resolve_channels(Instance &, const Slot &, uint32_t frames) const;
    void gather_inputs(Instance &, Slot &, uint32_t start, uint32_t frames, uint32_t channels, bool direct);
    void apply_parameters(Instance &, Slot &, uint32_t start, uint32_t frames, uint32_t channels);
    void call_module(Node &, uint32_t start, uint32_t frames, uint32_t channels, bool direct);
    void publish_outputs(Instance &, Slot &, uint32_t start, uint32_t frames, bool direct);
    void observe_pitch(Instance &, const Slot &, uint32_t start, uint32_t frames);
    void apply_pending_reset();
    void publish_block_outputs(float *const *, uint32_t output_channels, uint32_t frames);
    static int WS2_CALL emit(void *ctx, uint32_t port, const ws2_event *event) {
        if (!event || event->struct_size < sizeof(ws2_event)) return WS2_INVALID;
        auto &engine = *static_cast<Impl *>(ctx);
        const bool accepted = engine.route(port, *event);
        if (accepted && engine.processing && port < engine.processing->slot.event_tap_slots.size()) {
            const uint32_t slot = engine.processing->slot.event_tap_slots[port];
            if (slot != UINT32_MAX) engine.render_layout->tap_counts[slot].fetch_add(1, std::memory_order_relaxed);
        }
        return accepted ? WS2_OK : WS2_CAPACITY;
    }
};
} // namespace wirescape::engine2
