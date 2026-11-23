// SPDX-License-Identifier: GPL-3.0-only
#include "engine2.h"
#include "midi_release.h"
#include "types.h"
#include "wirescape_sdk.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <functional>
#include <limits>
#include <new>
#include <string_view>
#include <thread>
#include <tuple>
#include <utility>
#if defined(__SSE2__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace wirescape::engine2 {
namespace {
bool release(const ws2_event &e) { return e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE || midi_release(e); }
bool ordered(const Item &a, const Item &b) {
    return std::make_tuple(a.frame, !a.cleanup, a.order) < std::make_tuple(b.frame, !b.cleanup, b.order);
}
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
    uint32_t channels = 1, latency = 0;
    size_t requested_fast = 0, requested_large = 0;
    void *emit_context = nullptr;
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
bool pitch_layout(const Node *node, Instance::Pitch &pitch) {
    if (!node) return false;
    pitch.vco = !std::strcmp(node->instance.d->id, "essentials.vco");
    if (!pitch.vco && std::strcmp(node->instance.d->id, "ports.macro_oscillator")) return false;
    const auto index = [](const auto &ports, const char *id) {
        for (uint32_t i = 0; i < ports.size(); ++i)
            if (ports[i].id && !std::strcmp(ports[i].id, id)) return i;
        return UINT32_MAX;
    };
    pitch.input = index(node->instance.inputs, "pitch");
    pitch.tune = index(node->instance.parameters, pitch.vco ? "frequency" : "coarse");
    if (!pitch.vco) {
        pitch.trigger = index(node->instance.inputs, "trigger");
        pitch.gate = index(node->instance.inputs, "gate");
    }
    return pitch.input < node->slot.in.size() && pitch.tune < node->instance.param.size() &&
           (pitch.vco || (pitch.trigger < node->slot.in.size() && pitch.gate < node->slot.in.size()));
}
bool valid_tap(const Node *node, const Tap &tap) {
    if (!node || tap.kind > Tap::OscPitch) return false;
    if (tap.kind == Tap::OscPitch) {
        Instance::Pitch layout;
        return tap.index == 0 && pitch_layout(node, layout);
    }
    if (tap.kind == Tap::Param) return tap.index < node->instance.parameters.size();
    return tap.index < node->instance.outputs.size() &&
           node->instance.outputs[tap.index].kind == (tap.kind == Tap::EventOut ? WS2_EVENT : WS2_SIGNAL);
}
enum class Park : uint8_t { Running, Requested, Parked, Cancelled };
} // namespace

struct Engine::Impl {
    Config cfg;
    std::string error;
    std::vector<std::unique_ptr<Node>> nodes;
    std::vector<Edge> edges;
    std::vector<Component> components;
    std::vector<std::pair<uint32_t, Node *>> node_table;
    std::array<uint32_t, 32> bus_latency{};
    std::vector<uint32_t> distance;
    std::vector<Bus> buses;
    std::array<std::unique_ptr<Producer>, 32> producers;
    uint32_t producer_count = 0, dropped_connections = 0;
    std::unique_ptr<Producer> egress;
    std::vector<Packet> future;
    std::vector<uint8_t> arena;
    bool prepared = false;
    std::atomic_flag rendering = ATOMIC_FLAG_INIT;
    std::vector<Tap> taps;
    std::vector<Node *> tap_nodes;
    std::atomic<uint64_t> tap_sequence{0};
    std::unique_ptr<std::atomic<float>[]> tap_values;
    std::unique_ptr<std::atomic<uint32_t>[]> tap_counts;
    std::atomic<uint64_t> tap_frame{0};
    std::atomic<Park> park{Park::Running};
    std::atomic<uint64_t> revision{0};
    std::vector<std::pair<uint32_t, uint32_t>> replan_chokes;
    bool fade_in = false;
    std::atomic<uint64_t> position{0}, generation{1}, applied{1}, event_count{0}, dropped{0}, coalesced{0},
        ring_full{0}, stale{0}, late{0}, emergencies{0}, arena_full{0}, faults{0};
    std::atomic<bool> egress_emergency{false};
    uint64_t anchor_frame = 0, anchor_ns = 0, sequence = 0, block_start = 0;
    double frames_per_ns = 0, beat = 0;
    std::atomic<uint32_t> arena_used{0};
    uint32_t block_frames = 0, ordinary_used = 0, critical_used = 0;
    std::atomic<uint32_t> feedback_count{0}, latency{0};
    std::atomic<size_t> setup_bytes{0};
    Node *processing = nullptr;
    uint32_t processing_start = 0, processing_frames = 0;
    explicit Impl(Config c) : cfg(c), anchor_ns(c.epoch_ns), frames_per_ns(c.sample_rate / 1.e9) {
        nodes.reserve(cfg.max_nodes);
        future.reserve(cfg.future_capacity);
    }
    Node *find(uint32_t id) const {
        if (prepared) {
            auto it = std::lower_bound(node_table.begin(), node_table.end(), id,
                                       [](const auto &entry, uint32_t key) { return entry.first < key; });
            return it != node_table.end() && it->first == id ? it->second : nullptr;
        }
        for (auto &n : nodes)
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
        for (auto &n : nodes) {
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
        for (auto &e : edges)
            if (e.back) {
                e.head = 0;
                std::fill(e.delay_channels.begin(), e.delay_channels.end(), 0);
                if (e.delay.memory) std::fill_n(e.delay.memory.get(), cfg.max_channels * e.delay.stride, 0.f);
            }
        future.clear();
    }
    bool topology();
    void recompute_latency() noexcept;
    bool finish_prepare();
    bool resolve_taps();
    bool setup(Node &);
    bool valid_target(const Node &, uint32_t, const ws2_event &) const;
    bool admit(Node &, uint32_t, const ws2_event &, uint64_t, uint64_t, bool cleanup = false);
    void collect();
    bool route(uint32_t, const ws2_event &);
    void process_node(Node &, uint32_t, uint32_t);
    static int WS2_CALL emit(void *ctx, uint32_t port, const ws2_event *event) {
        if (!event || event->struct_size < sizeof(ws2_event)) return WS2_INVALID;
        auto &engine = *static_cast<Impl *>(ctx);
        const bool accepted = engine.route(port, *event);
        if (accepted && engine.processing && port < engine.processing->slot.event_tap_slots.size()) {
            const uint32_t slot = engine.processing->slot.event_tap_slots[port];
            if (slot != UINT32_MAX) engine.tap_counts[slot].fetch_add(1, std::memory_order_relaxed);
        }
        return accepted ? WS2_OK : WS2_CAPACITY;
    }
};

bool Engine::Impl::setup(Node &n) {
    n.instance.clear_instance();
    n.instance.allocations.reserve(64);
    ws2_config config{sizeof(ws2_config),
                      cfg.sample_rate,
                      cfg.max_block,
                      cfg.max_channels,
                      cfg.seed + n.instance.id,
                      n.instance.config.data(),
                      static_cast<uint32_t>(n.instance.config.size())};
    auto host = n.instance.host();
    n.instance.instance = n.instance.d->create(&host);
    if (!n.instance.instance) return fail("ABI2 create failed");
    ws2_ports ports{sizeof(ports), 0, 0, nullptr, nullptr};
    if (n.instance.d->query_ports(n.instance.instance, &config, &ports) != WS2_OK ||
        ports.input_count > WS2_MAX_PORTS || ports.output_count > WS2_MAX_PORTS ||
        (ports.input_count && !ports.inputs) || (ports.output_count && !ports.outputs))
        return fail("ABI2 query_ports failed");
    n.instance.inputs.clear();
    n.instance.outputs.clear();
    if (ports.input_count) n.instance.inputs.assign(ports.inputs, ports.inputs + ports.input_count);
    if (ports.output_count) n.instance.outputs.assign(ports.outputs, ports.outputs + ports.output_count);
    if (n.instance.d->prepare(n.instance.instance, &config, &host) != WS2_OK) return fail("ABI2 prepare failed");
    ws2_memory memory{sizeof(memory), 0, 0, 0};
    if (n.instance.d->memory_requirements(&config, &memory) != WS2_OK ||
        memory.fast_bytes < n.instance.requested_fast || memory.large_bytes < n.instance.requested_large)
        return fail("Module memory report understates requested storage");
    n.instance.latency = n.instance.d->latency_frames(n.instance.instance);
    auto check_ports = [&](const std::vector<ws2_port> &ports) {
        for (size_t i = 0; i < ports.size(); ++i) {
            const auto &p = ports[i];
            if (p.struct_size < sizeof(ws2_port) || !p.id || !p.name || (p.kind != WS2_SIGNAL && p.kind != WS2_EVENT) ||
                p.poly > WS2_FIRST || !std::isfinite(p.unpatched_value))
                return false;
            for (size_t j = 0; j < i; ++j)
                if (!std::strcmp(ports[j].id, p.id)) return false;
        }
        return true;
    };
    if (!check_ports(n.instance.inputs) || !check_ports(n.instance.outputs))
        return fail("Invalid/duplicate port descriptor");
    n.slot.in.resize(n.instance.inputs.size());
    n.instance.local_out.resize(n.instance.outputs.size());
    n.instance.global_out.resize(n.instance.outputs.size());
    n.instance.param.resize(n.instance.parameters.size());
    for (auto *buffers : {&n.slot.in, &n.instance.local_out, &n.instance.global_out, &n.instance.param})
        for (auto &b : *buffers) b.prepare(cfg.max_channels, cfg.max_block);
    n.instance.modulation_sum.resize(size_t(cfg.max_channels) * cfg.max_block);
    n.slot.in_view.resize(n.slot.in.size());
    n.instance.out_view.resize(n.instance.local_out.size());
    n.slot.param_view.resize(n.instance.param.size());
    n.instance.port_events.resize(n.instance.inputs.size());
    n.instance.event_view.resize(n.instance.inputs.size());
    n.instance.event_outputs.resize(n.instance.outputs.size());
    for (auto &events : n.instance.port_events) events.reserve(cfg.event_budget);
    n.instance.events.reserve(cfg.event_budget);
    n.instance.pending.reserve(cfg.event_budget);
    for (auto &p : n.instance.state) {
        p.base.prepare(cfg.sample_rate);
        p.offset.fill(0);
    }
    for (uint32_t i = 0; i < n.instance.outputs.size(); ++i)
        n.instance.event_outputs[i] = {sizeof(ws2_event_out), this, i, emit};
    setup_bytes += n.instance.requested_fast + n.instance.requested_large;
    return true;
}

bool Engine::Impl::resolve_taps() {
    tap_nodes.clear();
    tap_nodes.reserve(taps.size());
    for (auto &node : nodes) {
        node->slot.event_tap_slots.clear();
        node->instance.pitch.enabled = false;
    }
    for (uint32_t i = 0; i < taps.size(); ++i) {
        const auto &t = taps[i];
        auto *n = find(t.node);
        if (!valid_tap(n, t)) return fail("Telemetry tap endpoint changed during prepare");
        if (t.kind == Tap::OscPitch) {
            if (!pitch_layout(n, n->instance.pitch)) return fail("Oscillator pitch layout changed during prepare");
            n->instance.pitch.enabled = true;
        }
        tap_nodes.push_back(n);
        if (t.kind == Tap::EventOut) {
            if (n->slot.event_tap_slots.empty()) n->slot.event_tap_slots.assign(n->instance.outputs.size(), UINT32_MAX);
            n->slot.event_tap_slots[t.index] = i;
        }
    }
    return true;
}

bool Engine::Impl::finish_prepare() {
    if (!topology()) return false;
    for (auto &bus : buses) {
        auto *n = find(bus.node);
        if (!n || bus.port >= n->instance.outputs.size()) return fail("Output no longer exists");
        bus.source = n;
    }
    if (!resolve_taps()) return false;
    arena.resize(cfg.message_arena_bytes);
    egress = std::make_unique<Producer>(cfg.ring_capacity);
    prepared = true;
    applied.store(generation.load());
    return true;
}

void Engine::Impl::recompute_latency() noexcept {
    std::fill(distance.begin(), distance.end(), 0);
    bus_latency.fill(0);
    uint32_t maximum = 0;
    for (auto &component : components)
        for (auto *n : component.nodes) {
            uint32_t upstream = 0;
            for (auto &e : edges)
                if (!e.removed && !e.back && e.kind == 0 && e.destination == n)
                    upstream = std::max(upstream, distance[e.source->slot.index]);
            distance[n->slot.index] =
                static_cast<uint32_t>(std::min<uint64_t>(UINT32_MAX, uint64_t(upstream) + n->instance.latency));
        }
    for (const auto &bus : buses) {
        auto *n = find(bus.node);
        if (!n) continue;
        bus_latency[bus.channel] = std::max(bus_latency[bus.channel], distance[n->slot.index]);
        maximum = std::max(maximum, bus_latency[bus.channel]);
    }
    latency.store(maximum, std::memory_order_relaxed);
}

bool Engine::Impl::topology() {
    std::sort(nodes.begin(), nodes.end(), [](const auto &a, const auto &b) { return a->instance.id < b->instance.id; });
    for (uint32_t i = 0; i < nodes.size(); ++i) nodes[i]->slot.index = i;
    std::sort(edges.begin(), edges.end(), [](const Edge &a, const Edge &b) {
        return std::tie(a.from, a.output, a.to, a.input, a.kind, a.amount) <
               std::tie(b.from, b.output, b.to, b.input, b.kind, b.amount);
    });
    for (auto &e : edges) {
        e.source = find(e.from);
        e.destination = find(e.to);
        e.back = false;
        if (e.removed) continue;
        if (!e.source || !e.destination || e.output >= e.source->instance.outputs.size() ||
            (e.kind == 2 ? e.input >= e.destination->instance.parameters.size()
                         : e.input >= e.destination->instance.inputs.size()))
            return fail("Unavailable cable endpoint");
        if (e.kind == 2) {
            if (e.source->instance.outputs[e.output].kind != WS2_SIGNAL ||
                !(e.destination->instance.parameters[e.input].flags & WS2_MODULATABLE))
                return fail("Invalid modulation target");
        } else if (e.source->instance.outputs[e.output].kind != e.destination->instance.inputs[e.input].kind)
            return fail("Signal/event kind mismatch");
    }
    node_table.clear();
    for (auto &n : nodes) {
        node_table.emplace_back(n->instance.id, n.get());
        n->slot.incoming.assign(n->instance.inputs.size(), nullptr);
        n->slot.signal_edges.clear();
        n->slot.modulation.assign(n->instance.parameters.size(), {});
        n->slot.outgoing.assign(n->instance.outputs.size(), {});
    }
    for (auto &e : edges)
        if (!e.removed) {
            if (e.kind == 0) e.destination->slot.incoming[e.input] = &e;
            if (e.kind == 2) e.destination->slot.modulation[e.input].push_back(&e);
            if (e.kind == 1) e.source->slot.outgoing[e.output].push_back(&e);
            else e.destination->slot.signal_edges.push_back(&e);
        }
    const uint32_t count = static_cast<uint32_t>(nodes.size());
    std::vector<int> index(count, -1), low(count), stack;
    std::vector<bool> on(count, false);
    int next = 0;
    components.clear();
    std::function<void(uint32_t)> visit = [&](uint32_t v) {
        index[v] = low[v] = next++;
        stack.push_back(v);
        on[v] = true;
        for (auto &e : edges)
            if (!e.removed && e.source->slot.index == v) {
                uint32_t w = e.destination->slot.index;
                if (index[w] < 0) {
                    visit(w);
                    low[v] = std::min(low[v], low[w]);
                } else if (on[w]) low[v] = std::min(low[v], index[w]);
            }
        if (low[v] == index[v]) {
            Component component;
            for (;;) {
                auto w = static_cast<uint32_t>(stack.back());
                stack.pop_back();
                on[w] = false;
                nodes[w]->slot.component = static_cast<uint32_t>(components.size());
                component.nodes.push_back(nodes[w].get());
                if (w == v) break;
            }
            components.push_back(std::move(component));
        }
    };
    for (uint32_t i = 0; i < count; ++i)
        if (index[i] < 0) visit(i);
    feedback_count = 0;
    for (auto &component : components) {
        std::sort(component.nodes.begin(), component.nodes.end(),
                  [](auto *a, auto *b) { return a->instance.id < b->instance.id; });
        component.loop = component.nodes.size() > 1;
        std::vector<uint8_t> colour(count, 0);
        std::function<void(Node *)> dfs = [&](Node *n) {
            colour[n->slot.index] = 1;
            for (auto &e : edges)
                if (!e.removed && e.source == n && e.destination->slot.component == n->slot.component) {
                    auto c = colour[e.destination->slot.index];
                    if (c == 1) {
                        e.back = true;
                        component.loop = true;
                        ++feedback_count;
                    } else if (c == 0) dfs(e.destination);
                }
            colour[n->slot.index] = 2;
        };
        for (auto *n : component.nodes)
            if (!colour[n->slot.index]) dfs(n);
        std::vector<uint32_t> degree(count, 0);
        for (auto &e : edges)
            if (!e.removed && !e.back && e.source->slot.component == e.destination->slot.component &&
                e.source->slot.component == component.nodes.front()->slot.component)
                ++degree[e.destination->slot.index];
        std::vector<Node *> sorted;
        while (sorted.size() < component.nodes.size()) {
            Node *chosen = nullptr;
            for (auto *n : component.nodes)
                if (degree[n->slot.index] == 0 && std::find(sorted.begin(), sorted.end(), n) == sorted.end()) {
                    chosen = n;
                    break;
                }
            if (!chosen) return fail("Feedback back-edge removal did not produce DAG");
            sorted.push_back(chosen);
            for (auto &e : edges)
                if (!e.removed && !e.back && e.source == chosen &&
                    e.destination->slot.component == chosen->slot.component)
                    --degree[e.destination->slot.index];
        }
        component.nodes = std::move(sorted);
    }
    std::vector<uint32_t> degree(components.size(), 0);
    for (auto &e : edges)
        if (!e.removed && e.source->slot.component != e.destination->slot.component)
            ++degree[e.destination->slot.component];
    std::vector<Component> ordered_components;
    std::vector<bool> used(components.size(), false);
    while (ordered_components.size() < components.size()) {
        uint32_t chosen = UINT32_MAX, best = UINT32_MAX;
        for (uint32_t i = 0; i < components.size(); ++i)
            if (!used[i] && !degree[i]) {
                uint32_t id = UINT32_MAX;
                for (auto *n : components[i].nodes) id = std::min(id, n->instance.id);
                if (id < best) {
                    best = id;
                    chosen = i;
                }
            }
        if (chosen == UINT32_MAX) return fail("Invalid component graph");
        used[chosen] = true;
        for (auto &e : edges)
            if (!e.removed && e.source->slot.component == chosen && e.destination->slot.component != chosen)
                --degree[e.destination->slot.component];
        ordered_components.push_back(std::move(components[chosen]));
    }
    components = std::move(ordered_components);
    for (auto &e : edges)
        if (e.back && e.kind != 1) {
            e.delay.prepare(cfg.max_channels, cfg.feedback_block);
            e.delay_channels.assign(cfg.feedback_block, 0);
            e.head = 0;
        }
    for (auto &component : components)
        for (auto *n : component.nodes) n->slot.loop = component.loop;
    // Scratch is sized during topology/prepare, never during a status refresh.
    distance.resize(nodes.size());
    recompute_latency();
    return true;
}

bool Engine::Impl::valid_target(const Node &n, uint32_t port, const ws2_event &e) const {
    if (port != WS2_DIRECT_PORT && (port >= n.instance.inputs.size() || n.instance.inputs[port].kind != WS2_EVENT))
        return false;
    if (e.type == WS2_PARAM || e.type == WS2_PARAM_MOD) {
        if (e.index >= n.instance.parameters.size()) return false;
        if (e.type == WS2_PARAM &&
            (e.value < n.instance.parameters[e.index].minimum || e.value > n.instance.parameters[e.index].maximum))
            return false;
    }
    return true;
}
bool Engine::Impl::admit(Node &n, uint32_t port, const ws2_event &source, uint64_t frame, uint64_t order,
                         bool cleanup) {
    if (!valid_target(n, port, source)) {
        ++dropped;
        return false;
    }
    auto e = source;
    e.port = port;
    const bool critical = release(e);
    bool full = n.instance.pending.size() >= cfg.event_budget || ordinary_used + critical_used >= cfg.event_budget ||
                (!critical && ordinary_used >= cfg.event_budget - cfg.release_reserve);
    if (full) {
        if (e.type == WS2_PARAM)
            for (auto &old : n.instance.pending)
                if (old.event.type == WS2_PARAM && old.event.index == e.index && old.event.source_id == e.source_id &&
                    old.event.channel == e.channel) {
                    old = {e, frame, order};
                    ++coalesced;
                    return true;
                }
        if (critical) emergency();
        else ++dropped;
        return false;
    }
    if (e.bytes) {
        if (e.bytes > WS2_MAX_PAYLOAD || !e.data || e.bytes > arena.size() - arena_used) {
            ++arena_full;
            ++dropped;
            return false;
        }
        std::memcpy(arena.data() + arena_used, e.data, e.bytes);
        e.data = arena.data() + arena_used;
        arena_used += e.bytes;
    }
    n.instance.pending.push_back({e, frame, order, cleanup});
    if (critical) ++critical_used;
    else ++ordinary_used;
    ++event_count;
    return true;
}

void Engine::Impl::collect() {
    for (auto &n : nodes) n->instance.pending.clear();
    Packet p;
    const uint64_t gen = generation.load(std::memory_order_acquire);
    for (auto target : replan_chokes) {
        ws2_event e{};
        e.struct_size = sizeof(e);
        e.type = WS2_NOTE_CHOKE;
        e.source_id = UINT32_MAX;
        e.note_id = -1;
        e.channel = -1;
        e.flags = 1;
        if (auto *n = find(target.first)) admit(*n, target.second, e, block_start, 0, true);
        else ++stale;
    }
    replan_chokes.clear();
    for (uint32_t producer = 0; producer < producer_count; ++producer) {
        auto &source = *producers[producer];
        for (Ring *ring : {&source.critical, &source.normal}) {
            // Snapshot-like bounded drain. A busy producer cannot extend this indefinitely.
            for (uint32_t work = 0; work < cfg.ring_capacity && ring->pop(p); ++work) {
                if (p.generation != gen) {
                    ++stale;
                    continue;
                }
                auto *target = find(p.node);
                if (!target || p.revision < target->instance.born_revision) {
                    ++stale;
                    continue;
                }
                if (!valid_target(*target, p.port, p.event)) {
                    ++dropped;
                    continue;
                }
                if (p.mode == Timing::Immediate) p.when = block_start;
                else if (p.mode == Timing::Timestamped) {
                    uint64_t f = map_time(p.when);
                    p.when = f > UINT64_MAX - cfg.max_block ? UINT64_MAX : f + cfg.max_block;
                }
                if (future.size() == future.capacity()) {
                    if (release(p.event)) emergency();
                    else ++dropped;
                    continue;
                }
                future.push_back(p);
            }
        }
    }
    size_t keep = 0;
    for (size_t i = 0; i < future.size(); ++i) {
        auto &packet = future[i];
        packet.fix();
        if (packet.generation != gen) {
            ++stale;
            continue;
        }
        Node *n = find(packet.node);
        if (!n || packet.revision < n->instance.born_revision) {
            ++stale;
            continue;
        }
        if (!valid_target(*n, packet.port, packet.event)) {
            ++dropped;
            continue;
        }
        if (packet.when >= block_start + block_frames) {
            if (keep != i) future[keep] = packet;
            ++keep;
            continue;
        }
        if (packet.when < block_start) {
            packet.when = block_start;
            ++late;
        }
        admit(*n, packet.port, packet.event, packet.when, packet.order);
    }
    future.resize(keep);
}

bool Engine::Impl::route(uint32_t port, const ws2_event &source) {
    if (!processing || port >= processing->instance.outputs.size() ||
        processing->instance.outputs[port].kind != WS2_EVENT || source.offset >= processing_frames ||
        !ws::valid_event(source))
        return false;
    if (ordinary_used + critical_used >= cfg.event_budget ||
        (!release(source) && ordinary_used >= cfg.event_budget - cfg.release_reserve)) {
        if (release(source)) emergency();
        else ++dropped;
        return false;
    }
    if (release(source)) ++critical_used;
    else ++ordinary_used;
    ++event_count;
    const uint64_t frame = block_start + processing_start + source.offset;
    bool routed = false, okay = true;
    for (auto *edge : processing->slot.outgoing[port]) {
        auto &e = *edge;
        routed = true;
        const uint64_t destination_frame = frame + (e.back ? cfg.feedback_block : 0);
        if (destination_frame < block_start + block_frames)
            okay = admit(*e.destination, e.input, source, destination_frame, (UINT64_C(1) << 63) | sequence++) && okay;
        else {
            if (future.size() == future.capacity()) {
                if (release(source)) emergency();
                else ++dropped;
                okay = false;
                continue;
            }
            Packet p;
            p.node = e.to;
            p.port = e.input;
            p.routed_from = e.from;
            p.routed_output = e.output;
            p.event = source;
            p.when = destination_frame;
            p.generation = generation.load();
            p.revision = revision.load();
            p.order = (UINT64_C(1) << 63) | sequence++;
            if (source.bytes) std::memcpy(p.payload.data(), source.data, source.bytes);
            p.fix();
            future.push_back(p);
        }
    }
    // Every module output is also available to a fake/external dispatcher. Track C
    // will choose endpoint sinks; this headless slice does not perform I/O.
    Packet out;
    out.node = processing->instance.id;
    out.port = port;
    out.when = frame;
    out.order = sequence++;
    out.mapped_time_ns = map_frame(frame);
    out.generation = generation.load();
    out.event = source;
    if (source.bytes) std::memcpy(out.payload.data(), source.data, source.bytes);
    out.fix();
    if (!(release(source) ? egress->critical : egress->normal).push(out)) {
        if (release(source)) emergency();
        else ++dropped;
        okay = false;
    }
    return routed ? okay : okay;
}

void Engine::Impl::process_node(Node &n, uint32_t start, uint32_t frames) {
    const bool direct = !n.slot.loop;
    n.instance.events.clear();
    for (auto &v : n.instance.port_events) v.clear();
    std::sort(n.instance.pending.begin(), n.instance.pending.end(), ordered);
    for (const auto &item : n.instance.pending)
        if (item.frame >= block_start + start && item.frame < block_start + start + frames) {
            auto event = item.event;
            event.offset = static_cast<uint32_t>(item.frame - block_start - start);
            n.instance.events.push_back(event);
            if (event.port < n.instance.port_events.size()) n.instance.port_events[event.port].push_back(event);
        }
    auto raw_channels = [&](const Edge &e) {
        if (!e.back) return e.source->instance.global_out[e.output].channels;
        uint32_t count = 0;
        for (uint32_t i = 0; i < frames; ++i)
            count = std::max(count, e.delay_channels[(e.head + i) % cfg.feedback_block]);
        return count;
    };
    auto value = [&](const Edge &e, uint32_t channel, uint32_t i) {
        if (e.back) {
            auto pos = (e.head + i) % cfg.feedback_block;
            auto count = e.delay_channels[pos];
            if (count == 1) channel = 0;
            return channel < count ? e.delay.data[channel][pos] : 0.f;
        }
        const auto &buffer = e.source->instance.global_out[e.output];
        if (buffer.channels == 1) channel = 0;
        return channel < buffer.channels ? buffer.data[channel][(buffer.flags & WS2_CONSTANT) ? 0 : start + i] : 0.f;
    };
    uint32_t channels = n.instance.forced_channels > 0 ? static_cast<uint32_t>(n.instance.forced_channels) : 1;
    for (const auto *edge : n.slot.signal_edges) {
        const auto &e = *edge;
        if (e.kind == 2 ? (n.instance.parameters[e.input].flags & WS2_PER_VOICE) != 0
                        : n.instance.inputs[e.input].poly == WS2_POLY)
            channels = std::max(channels, raw_channels(e));
    }
    channels = std::min(channels, cfg.max_channels);
    n.instance.channels = channels;
    for (uint32_t j = 0; j < n.instance.inputs.size(); ++j) {
        const auto &port = n.instance.inputs[j];
        auto &buffer = n.slot.in[j];
        const Edge *source = nullptr;
        if (port.kind == WS2_SIGNAL) source = n.slot.incoming[j];
        uint32_t source_channels = source ? raw_channels(*source) : 0;
        bool connected = source_channels > 0;
        bool constant =
            !connected || (!source->back && (source->source->instance.global_out[source->output].flags & WS2_CONSTANT));
        buffer.channels = port.kind == WS2_EVENT ? 0 : port.poly == WS2_POLY ? channels : 1;
        buffer.flags = (constant ? WS2_CONSTANT : 0) | (connected ? WS2_CONNECTED : 0);
        const bool alias = direct && connected && !source->back &&
                           (source_channels == 1 || (port.poly == WS2_POLY && source_channels == buffer.channels));
        for (uint32_t c = 0; c < buffer.channels; ++c)
            buffer.read[c] =
                alias ? source->source->instance.global_out[source->output].data[source_channels == 1 ? 0 : c]
                      : buffer.data[c];
        if (!alias)
            for (uint32_t c = 0; c < buffer.channels; ++c)
                for (uint32_t i = 0; i < (constant ? 1u : frames); ++i) {
                    float sample = port.unpatched_value;
                    if (connected) {
                        if (port.poly == WS2_SUM) {
                            sample = 0;
                            for (uint32_t k = 0; k < source_channels; ++k) sample += value(*source, k, i);
                        } else sample = value(*source, port.poly == WS2_FIRST ? 0 : c, i);
                    }
                    buffer.data[c][i] = sample;
                }
        n.slot.in_view[j] = {sizeof(ws2_signal), buffer.read.data(), buffer.channels, buffer.flags};
        n.instance.event_view[j] = {sizeof(ws2_event_list), static_cast<uint32_t>(n.instance.port_events[j].size()),
                                    n.instance.port_events[j].data()};
    }
    for (uint32_t j = 0; j < n.instance.parameters.size(); ++j) {
        auto &p = n.instance.state[j];
        auto &buffer = n.instance.param[j];
        bool poly = false, constant = p.base.constant();
        for (uint32_t c = 1; c < channels; ++c) poly |= p.offset[c] != p.offset[0];
        for (const auto *edge : n.slot.modulation[j]) {
            const auto &e = *edge;
            poly |= raw_channels(e) > 1;
            constant &= !e.back && (e.source->instance.global_out[e.output].flags & WS2_CONSTANT);
        }
        for (const auto &e : n.instance.events)
            if ((e.type == WS2_PARAM || e.type == WS2_PARAM_MOD) && e.index == j) {
                constant = false;
                if (e.type == WS2_PARAM_MOD && e.channel >= 0) poly = true;
            }
        buffer.channels = (poly && (p.info.flags & WS2_PER_VOICE)) ? channels : 1;
        buffer.flags = constant ? WS2_CONSTANT : 0;
        uint32_t cursor = 0;
        const uint32_t length = constant ? 1 : frames;
        const bool modulated = !n.slot.modulation[j].empty();
        if (modulated)
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                double *sum = n.instance.modulation_sum.data() + size_t(c) * cfg.max_block;
                std::fill_n(sum, length, 0.);
                for (const auto *edge : n.slot.modulation[j])
                    for (uint32_t i = 0; i < length; ++i) sum[i] += edge->amount * value(*edge, c, i);
            }
        bool actually_constant = true;
        for (uint32_t i = 0; i < length; ++i) {
            while (cursor < n.instance.events.size() && n.instance.events[cursor].offset <= i) {
                const auto &e = n.instance.events[cursor++];
                if (e.index == j && e.type == WS2_PARAM) {
                    double target = ws::to_normal(p.info, e.value);
                    if (p.info.flags & WS2_STEPPED) p.base.jump(target);
                    else p.base.set(target);
                    p.requested = true;
                }
                if (e.index == j && e.type == WS2_PARAM_MOD) {
                    if (e.channel < 0) p.offset.fill(e.value);
                    else if (static_cast<uint32_t>(e.channel) < cfg.max_channels) p.offset[e.channel] = e.value;
                }
            }
            const double base = p.base.next();
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                double effective = base + p.offset[c];
                if (modulated) effective += n.instance.modulation_sum[size_t(c) * cfg.max_block + i];
                buffer.data[c][i] = static_cast<float>(p.plain(effective));
                if (i && buffer.data[c][i] != buffer.data[c][0]) actually_constant = false;
            }
        }
        if (actually_constant) buffer.flags |= WS2_CONSTANT;
        n.slot.param_view[j] = {sizeof(ws2_signal), buffer.read.data(), buffer.channels, buffer.flags};
    }
    for (uint32_t j = 0; j < n.instance.outputs.size(); ++j)
        n.instance.out_view[j] = {sizeof(ws2_signal_out),
                                  (direct ? n.instance.global_out[j] : n.instance.local_out[j]).data.data(), channels,
                                  0, cfg.max_channels};
    processing = &n;
    processing_start = start;
    processing_frames = frames;
    if (n.instance.forced_channels == 0) {
        for (auto &o : n.instance.out_view) {
            o.channels = 0;
            o.flags = WS2_CONSTANT;
        }
    } else {
        ws2_transport transport{sizeof(ws2_transport),
                                cfg.playing ? WS2_PLAYING : 0u,
                                cfg.bpm,
                                beat + (cfg.playing ? start * cfg.bpm / (60. * cfg.sample_rate) : 0),
                                0,
                                4,
                                4,
                                0,
                                0};
        transport.bar_start = std::floor(transport.beat / 4) * 4;
        ws2_process context{
            sizeof(ws2_process),
            frames,
            block_start + start,
            generation.load(),
            cfg.sample_rate,
            channels,
            static_cast<uint32_t>(n.instance.inputs.size()),
            static_cast<uint32_t>(n.instance.outputs.size()),
            static_cast<uint32_t>(n.instance.parameters.size()),
            n.slot.in_view.data(),
            n.instance.out_view.data(),
            n.slot.param_view.data(),
            n.instance.event_view.data(),
            n.instance.event_outputs.data(),
            {sizeof(ws2_event_list), static_cast<uint32_t>(n.instance.events.size()), n.instance.events.data()},
            &transport};
        if (n.instance.d->process(n.instance.instance, &context) != WS2_OK) {
            ++faults;
            for (auto &o : n.instance.out_view) {
                o.channels = channels;
                o.flags = WS2_CONSTANT;
                for (uint32_t c = 0; c < channels; ++c) o.data[c][0] = 0;
            }
        }
    }
    processing = nullptr;
    for (uint32_t j = 0; j < n.instance.outputs.size(); ++j) {
        auto &o = n.instance.out_view[j];
        auto &global = n.instance.global_out[j];
        if (direct) {
            global.channels = o.channels;
            global.flags = o.flags;
            continue;
        }
        if (!n.slot.touched) {
            global.channels = o.channels;
            global.flags = o.flags;
        } else {
            if (global.channels != o.channels) global.flags = 0;
            if (!(o.flags & WS2_CONSTANT)) global.flags = 0;
            if (global.flags & WS2_CONSTANT)
                for (uint32_t c = 0; c < o.channels; ++c)
                    if (global.data[c][0] != o.data[c][0]) global.flags = 0;
            global.channels = std::max(global.channels, o.channels);
        }
        for (uint32_t c = 0; c < global.channels; ++c)
            for (uint32_t i = 0; i < frames; ++i)
                global.data[c][start + i] = c < o.channels ? o.data[c][(o.flags & WS2_CONSTANT) ? 0 : i] : 0;
    }
    n.slot.touched = true;
    if (n.instance.pitch.enabled && frames && n.instance.channels) {
        // A typed coordinate avoids accidentally swapping three similar indices.
        struct SignalIndex {
            uint32_t input, channel, sample;
        };
        // For direct edges, the read pointer aliases a whole-block source buffer.
        auto signal = [&](SignalIndex at) {
            const auto &buffer = n.slot.in[at.input];
            const uint32_t channel = std::min(at.channel, buffer.channels - 1);
            const uint32_t sample =
                (buffer.flags & WS2_CONSTANT)
                    ? 0u
                    : (buffer.read[channel] == buffer.data[channel] ? at.sample : start + at.sample);
            return buffer.read[channel][sample];
        };
        auto parameter = [&](uint32_t index, uint32_t channel) {
            const auto &buffer = n.instance.param[index];
            const uint32_t ch = std::min(channel, buffer.channels - 1);
            return buffer.data[ch][(buffer.flags & WS2_CONSTANT) ? 0u : frames - 1];
        };
        if (n.instance.pitch.vco) {
            for (const auto &event : n.instance.events) {
                const uint32_t channel = event.channel < 0 ? 0u : static_cast<uint32_t>(event.channel);
                if (channel >= n.instance.channels) continue;
                if (event.type == WS2_NOTE_ON) {
                    n.instance.pitch.note[channel] = event.key;
                    n.instance.pitch.note_on[channel] = true;
                    n.instance.pitch.latest = channel;
                } else if (event.type == WS2_NOTE_CHOKE) {
                    n.instance.pitch.note_on[channel] = false;
                }
            }
        } else {
            // Plaits renders at most eight voices in 12-frame blocks; scan strikes and held gates.
            for (uint32_t i = 0; i < frames; ++i) {
                for (uint32_t channel = 0; channel < std::min(n.instance.channels, 8u); ++channel) {
                    const bool high = std::max(signal({n.instance.pitch.trigger, channel, i}),
                                               signal({n.instance.pitch.gate, channel, i})) > 0.5f;
                    if (high && !n.instance.pitch.high[channel]) n.instance.pitch.latest = channel;
                    n.instance.pitch.high[channel] = high;
                }
            }
        }
        const uint32_t channel = std::min(n.instance.pitch.latest, n.instance.channels - 1);
        if (n.instance.pitch.vco) {
            const float tune = parameter(n.instance.pitch.tune, channel);
            double hz = tune;
            if (n.slot.in[n.instance.pitch.input].flags & WS2_CONNECTED) {
                hz = 261.6255653005986 * std::pow(2., signal({n.instance.pitch.input, channel, frames - 1})) *
                     (tune / 220.);
            } else if (n.instance.pitch.note_on[channel]) {
                hz = 440. * std::pow(2., (n.instance.pitch.note[channel] - 69.) / 12.);
            }
            // VCO tap stores Hz; the control owner converts to equal-tempered MIDI.
            n.instance.pitch.value = std::numeric_limits<float>::quiet_NaN();
            if (std::isfinite(hz) && hz > 0) n.instance.pitch.value = static_cast<float>(hz);
        } else {
            // Macro tap stores nominal MIDI note. FM and Plaits internal FM excluded.
            n.instance.pitch.value =
                60.f + parameter(n.instance.pitch.tune, channel) +
                std::clamp(12.f * signal({n.instance.pitch.input, channel, frames - 1}), -96.f, 96.f);
        }
    }
}

Engine::Engine(Config config) : p_(std::make_unique<Impl>(config)) {}
Engine::~Engine() = default;
static_assert(std::atomic<float>::is_always_lock_free, "Telemetry floats must be lock-free");
bool Engine::add_node(uint32_t id, const ws2_descriptor *d, const std::vector<uint8_t> &config) {
    auto &p = *p_;
    if (!p.cfg.max_channels || p.cfg.max_channels > 16 || !p.cfg.max_block || p.cfg.max_block > 4096)
        return p.fail("Invalid setup bounds");
    if (p.prepared || !id || p.find(id) || p.nodes.size() >= p.cfg.max_nodes || !d ||
        d->struct_size < sizeof(ws2_descriptor) || d->abi_version != 2 || !d->id || !d->name || !d->create ||
        !d->destroy || !d->query_ports || !d->memory_requirements || !d->prepare || !d->reset || !d->process ||
        !d->save_state || !d->load_state || !d->latency_frames || d->input_count > WS2_MAX_PORTS ||
        d->output_count > WS2_MAX_PORTS || d->param_count > WS2_MAX_PARAMS || (d->input_count && !d->inputs) ||
        (d->output_count && !d->outputs) || (d->param_count && !d->params))
        return p.fail("Invalid ABI2 node");
    auto n = std::make_unique<Node>();
    n->instance.id = id;
    n->instance.d = d;
    n->instance.config = config;
    if (d->input_count) n->instance.inputs.assign(d->inputs, d->inputs + d->input_count);
    if (d->output_count) n->instance.outputs.assign(d->outputs, d->outputs + d->output_count);
    if (d->param_count) n->instance.parameters.assign(d->params, d->params + d->param_count);
    for (const auto &info : n->instance.parameters) n->instance.state.emplace_back(info);
    // Resolve configuration-dependent ports quiescently before cable authoring.
    if (!p.setup(*n)) return false;
    p.nodes.push_back(std::move(n));
    return true;
}
bool Engine::connect(uint32_t from, uint32_t output, uint32_t to, uint32_t input) {
    auto &p = *p_;
    auto *a = p.find(from), *b = p.find(to);
    if (p.prepared || !a || !b || output >= a->instance.outputs.size() || input >= b->instance.inputs.size())
        return p.fail("Invalid connection");
    auto kind = a->instance.outputs[output].kind;
    if (kind != b->instance.inputs[input].kind) return p.fail("Signal/event kind mismatch");
    if (kind == WS2_SIGNAL)
        for (auto &e : p.edges)
            if (e.kind == 0 && e.to == to && e.input == input) return p.fail("Signal input already connected");
    p.edges.push_back({from, output, to, input, kind == WS2_EVENT ? 1 : 0, 0});
    return true;
}
bool Engine::modulate(uint32_t from, uint32_t output, uint32_t to, uint32_t param, float amount) {
    auto &p = *p_;
    auto *a = p.find(from), *b = p.find(to);
    if (p.prepared || !a || !b || output >= a->instance.outputs.size() || param >= b->instance.parameters.size() ||
        a->instance.outputs[output].kind != WS2_SIGNAL || !(b->instance.parameters[param].flags & WS2_MODULATABLE) ||
        !std::isfinite(amount) || amount < -1 || amount > 1)
        return p.fail("Invalid modulation cable");
    p.edges.push_back({from, output, to, param, 2, amount});
    return true;
}
bool Engine::output(uint32_t node, uint32_t port, uint32_t channel) {
    auto &p = *p_;
    auto *n = p.find(node);
    if (p.prepared || !n || port >= n->instance.outputs.size() || n->instance.outputs[port].kind != WS2_SIGNAL ||
        channel >= 32)
        return p.fail("Invalid output bus");
    p.buses.push_back({node, port, channel});
    return true;
}
int Engine::register_producer() {
    auto &p = *p_;
    if (p.prepared || p.producer_count == 32 || !p.cfg.ring_capacity || p.cfg.ring_capacity > 65536) return -1;
    uint32_t i = p.producer_count++;
    p.producers[i] = std::make_unique<Producer>(p.cfg.ring_capacity);
    return static_cast<int>(i);
}
bool Engine::set_telemetry_taps(const std::vector<Tap> &requested) {
    auto &p = *p_;
    if (p.prepared || requested.size() > p.cfg.max_taps) return p.fail("Invalid telemetry tap capacity or setup state");
    for (size_t i = 0; i < requested.size(); ++i) {
        const auto &t = requested[i];
        const auto *n = p.find(t.node);
        if (!valid_tap(n, t)) return p.fail("Invalid telemetry tap endpoint");
        for (size_t j = 0; j < i; ++j)
            if (requested[j].kind == t.kind && requested[j].node == t.node && requested[j].index == t.index)
                return p.fail("Duplicate telemetry tap endpoint");
    }
    auto values = std::make_unique<std::atomic<float>[]>(requested.size());
    auto counts = std::make_unique<std::atomic<uint32_t>[]>(requested.size());
    for (size_t i = 0; i < requested.size(); ++i) {
        values[i].store(0, std::memory_order_relaxed);
        counts[i].store(0, std::memory_order_relaxed);
    }
    p.taps = requested;
    p.tap_values.swap(values);
    p.tap_counts.swap(counts);
    p.tap_nodes.clear();
    p.tap_frame.store(0, std::memory_order_relaxed);
    p.tap_sequence.store(0, std::memory_order_relaxed);
    return true;
}
uint32_t Engine::read_telemetry(float *values, uint32_t *counts, uint32_t capacity, uint64_t &frame) const noexcept {
    const auto &p = *p_;
    frame = 0;
    if (capacity < p.taps.size() || (!p.taps.empty() && (!values || !counts))) return 0;
    // A bounded non-render read must not combine two blocks (in particular
    // Groove's split uint32 loop and release-safe position observations).
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        const auto before = p.tap_sequence.load(std::memory_order_acquire);
        if (before & 1u) continue;
        const auto observed = p.tap_frame.load(std::memory_order_relaxed);
        for (size_t i = 0; i < p.taps.size(); ++i) {
            values[i] = p.tap_values[i].load(std::memory_order_relaxed);
            counts[i] = p.tap_counts[i].load(std::memory_order_relaxed);
        }
        std::atomic_thread_fence(std::memory_order_acquire);
        if (before == p.tap_sequence.load(std::memory_order_relaxed)) {
            frame = observed;
            return static_cast<uint32_t>(p.taps.size());
        }
    }
    return static_cast<uint32_t>(p.taps.size()); // frame=0: unavailable, never a torn snapshot.
}
bool Engine::prepare() {
    auto &p = *p_;
    if (p.prepared) return p.fail("Prepare is quiescent and single-use; reconfigure uses staged replacement");
    if (!std::isfinite(p.cfg.sample_rate) || p.cfg.sample_rate < 1000 || p.cfg.sample_rate > 384000 ||
        !p.cfg.max_channels || p.cfg.max_channels > 16 || !p.cfg.max_block || p.cfg.max_block > 4096 ||
        !p.cfg.max_nodes || p.cfg.max_nodes > 1024 || p.cfg.event_budget < 2 || p.cfg.event_budget > 65536 ||
        !p.cfg.release_reserve || p.cfg.release_reserve >= p.cfg.event_budget || !p.cfg.ring_capacity ||
        p.cfg.ring_capacity > 65536 || !p.cfg.future_capacity || p.cfg.future_capacity > 65536 ||
        !p.cfg.feedback_block || p.cfg.feedback_block > p.cfg.max_block ||
        p.cfg.message_arena_bytes > 64 * 1024 * 1024 || p.cfg.max_taps > 4096)
        return p.fail("Invalid engine2 configuration");
    p.setup_bytes = 0;
    for (auto &n : p.nodes)
        if (!p.setup(*n)) return false;
    return p.finish_prepare();
}
bool Engine::set_parameter(uint32_t node, uint32_t index, float plain) {
    auto &p = *p_;
    auto *n = p.find(node);
    if (!n || index >= n->instance.parameters.size() || !std::isfinite(plain)) return false;
    auto &v = n->instance.state[index];
    if (plain < v.info.minimum || plain > v.info.maximum) return false;
    if (p.prepared && p.position.load() != 0) return p.fail("Use PARAM ingress for live changes");
    v.base.set(ws::to_normal(v.info, plain));
    v.requested = true;
    return true;
}
bool Engine::set_channels(uint32_t node, uint32_t channels) {
    auto *n = p_->find(node);
    if (!n || channels > p_->cfg.max_channels) return false;
    n->instance.forced_channels = static_cast<int>(channels);
    return true;
}

int Engine::enqueue(uint32_t producer, uint32_t node, uint32_t port, const ws2_event &event, uint64_t time, Timing mode,
                    uint64_t wanted_generation) noexcept {
    auto &p = *p_;
    if (!p.prepared || producer >= p.producer_count) return WS2_STATE;
    const auto gen = p.generation.load(std::memory_order_acquire);
    if (gen != p.applied.load(std::memory_order_acquire) || (wanted_generation && wanted_generation != gen))
        return WS2_STATE;
    if (!ws::valid_event(event)) return WS2_INVALID;
    auto &source = *p.producers[producer];
    Packet packet;
    packet.node = node;
    packet.port = port;
    packet.when = time;
    packet.mode = mode;
    packet.producer = producer;
    packet.generation = gen;
    packet.revision = p.revision.load(std::memory_order_acquire);
    packet.order = (static_cast<uint64_t>(producer) << 48) | (source.serial++ & UINT64_C(0x0000ffffffffffff));
    packet.event = event;
    if (event.bytes) std::memcpy(packet.payload.data(), event.data, event.bytes);
    packet.fix();
    if (!(release(event) ? source.critical : source.normal).push(packet)) {
        ++p.ring_full;
        if (release(event)) p.emergency();
        else ++p.dropped;
        return WS2_CAPACITY;
    }
    return WS2_OK;
}

bool Engine::publish_clock(uint64_t frame, uint64_t ns) {
    auto &p = *p_;
    if (frame < p.anchor_frame || ns < p.anchor_ns) return false;
    if (frame > p.anchor_frame && ns > p.anchor_ns) {
        double measured = static_cast<double>(frame - p.anchor_frame) / static_cast<double>(ns - p.anchor_ns);
        double nominal = p.cfg.sample_rate / 1.e9;
        measured = std::clamp(measured, nominal * .999, nominal * 1.001);
        p.frames_per_ns += (measured - p.frames_per_ns) / 16.;
    }
    p.anchor_frame = frame;
    p.anchor_ns = ns;
    return true;
}

int Engine::render(float *const *outputs, uint32_t output_channels, uint32_t frames,
                   uint64_t callback_time_ns) noexcept {
    auto &p = *p_;
    if (!p.prepared || !frames || frames > p.cfg.max_block || output_channels > 32 || (output_channels && !outputs))
        return WS2_INVALID;
    for (uint32_t c = 0; c < output_channels; ++c)
        if (!outputs[c]) return WS2_INVALID;
    if (p.rendering.test_and_set(std::memory_order_acquire)) return WS2_STATE;
    struct Guard {
        std::atomic_flag &flag;
#if defined(__SSE2__) || defined(_M_X64)
        uint32_t fp;
        explicit Guard(std::atomic_flag &f) : flag(f), fp(_mm_getcsr()) { _mm_setcsr(fp | 0x8040); }
        ~Guard() {
            _mm_setcsr(fp);
            flag.clear(std::memory_order_release);
        }
#elif defined(__aarch64__) && !defined(_MSC_VER)
        uint64_t fp;
        explicit Guard(std::atomic_flag &f) : flag(f) {
            asm volatile("mrs %0, fpcr" : "=r"(fp));
            uint64_t value = fp | (UINT64_C(1) << 24);
            asm volatile("msr fpcr, %0" ::"r"(value));
        }
        ~Guard() {
            asm volatile("msr fpcr, %0" ::"r"(fp));
            flag.clear(std::memory_order_release);
        }
#else
        explicit Guard(std::atomic_flag &f) : flag(f) {}
        ~Guard() { flag.clear(std::memory_order_release); }
#endif
    } guard(p.rendering);
    p.block_start = p.position.load(std::memory_order_relaxed);
    p.block_frames = frames;
    if (callback_time_ns != UINT64_MAX) publish_clock(p.block_start, callback_time_ns);
    const auto parked = p.park.load(std::memory_order_acquire);
    if (parked == Park::Parked) {
        for (uint32_t c = 0; c < output_channels; ++c) std::fill_n(outputs[c], frames, 0.f);
        if (p.cfg.playing) p.beat += frames * p.cfg.bpm / (60. * p.cfg.sample_rate);
        p.position.store(p.block_start + frames, std::memory_order_release);
        return WS2_OK;
    }
    if (parked == Park::Cancelled) p.park.store(Park::Running, std::memory_order_release);
    if (p.generation.load() != p.applied.load()) {
        p.reset_processors();
        p.applied.store(p.generation.load(), std::memory_order_release);
    }
    p.arena_used.store(0);
    p.ordinary_used = p.critical_used = 0;
    for (auto &n : p.nodes) n->slot.touched = false;
    p.collect();
    if (p.generation.load() != p.applied.load()) {
        p.reset_processors();
        p.applied.store(p.generation.load(), std::memory_order_release);
    }
    for (auto &component : p.components) {
        uint32_t chunk = component.loop ? p.cfg.feedback_block : frames;
        for (uint32_t start = 0; start < frames; start += chunk) {
            uint32_t length = std::min(chunk, frames - start);
            for (auto *n : component.nodes) p.process_node(*n, start, length);
            if (component.loop)
                for (auto &e : p.edges)
                    if (e.back && e.kind != 1 && e.source->slot.component == component.nodes.front()->slot.component) {
                        auto &source = e.source->instance.global_out[e.output];
                        for (uint32_t i = 0; i < length; ++i) {
                            auto at = (e.head + i) % p.cfg.feedback_block;
                            e.delay_channels[at] = source.channels;
                            for (uint32_t c = 0; c < p.cfg.max_channels; ++c)
                                e.delay.data[c][at] = c < source.channels ? source.data[c][start + i] : 0;
                        }
                        e.head = (e.head + length) % p.cfg.feedback_block;
                    }
        }
    }
    for (uint32_t c = 0; c < output_channels; ++c) std::fill_n(outputs[c], frames, 0.f);
    bool bus_written[32]{};
    for (auto &bus : p.buses)
        if (bus.channel < output_channels) {
            const auto &buffer = bus.source->instance.global_out[bus.port];
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                for (uint32_t i = 0; i < frames; ++i) {
                    const float sample = buffer.data[c][(buffer.flags & WS2_CONSTANT) ? 0 : i];
                    if (!bus_written[bus.channel]) outputs[bus.channel][i] = sample;
                    else outputs[bus.channel][i] += sample;
                }
                bus_written[bus.channel] = true;
            }
        }
    if (!p.taps.empty()) {
        // Render-owned, post-DSP snapshots. Feedback loops process in chunks, so
        // their parameter buffer's last chunk is shorter than the full block.
        p.tap_sequence.fetch_add(1, std::memory_order_acq_rel);
        for (size_t i = 0; i < p.taps.size(); ++i) {
            const auto &t = p.taps[i];
            const auto *n = p.tap_nodes[i];
            float sample = 0;
            if (t.kind == Tap::Param) {
                const auto &b = n->instance.param[t.index];
                const uint32_t last = n->slot.loop ? (frames - 1) % p.cfg.feedback_block : frames - 1;
                sample = b.data[0][(b.flags & WS2_CONSTANT) ? 0 : last];
            } else if (t.kind == Tap::OscPitch) {
                sample = n->instance.pitch.value;
            } else if (t.kind == Tap::Output) {
                const auto &b = n->instance.global_out[t.index];
                const uint32_t at = (b.flags & WS2_CONSTANT) ? 0 : frames - 1;
                if (b.channels) {
                    sample = b.data[0][at];
                    if (t.reduction == Tap::Maximum)
                        for (uint32_t c = 1; c < b.channels; ++c) sample = std::max(sample, b.data[c][at]);
                }
            }
            p.tap_values[i].store(sample, std::memory_order_relaxed);
        }
        p.tap_frame.store(p.block_start + frames, std::memory_order_relaxed);
        p.tap_sequence.fetch_add(1, std::memory_order_release);
    }
    if (p.cfg.playing) p.beat += frames * p.cfg.bpm / (60. * p.cfg.sample_rate);
    p.position.store(p.block_start + frames, std::memory_order_release);
    if (p.generation.load() != p.applied.load()) {
        p.reset_processors();
        p.applied.store(p.generation.load(), std::memory_order_release);
    }
    if (p.fade_in) {
        for (uint32_t c = 0; c < output_channels; ++c)
            for (uint32_t i = 0; i < frames; ++i) outputs[c][i] *= float(i + 1) / float(frames);
        p.fade_in = false;
    }
    if (p.park.load(std::memory_order_acquire) == Park::Requested) {
        for (uint32_t c = 0; c < output_channels; ++c)
            for (uint32_t i = 0; i < frames; ++i) outputs[c][i] *= float(frames - i - 1) / float(frames);
        p.fade_in = true;
        auto expected = Park::Requested;
        if (!p.park.compare_exchange_strong(expected, Park::Parked, std::memory_order_acq_rel,
                                            std::memory_order_acquire))
            p.park.store(Park::Running, std::memory_order_release);
    }
    return WS2_OK;
}

bool Engine::pop_egress(Outgoing &out) noexcept {
    auto &p = *p_;
    if (!p.egress) return false;
    if (p.egress_emergency.exchange(false, std::memory_order_acq_rel)) {
        out = {};
        out.generation = p.generation.load();
        out.frame = p.position.load();
        out.time_ns = 0;
        out.event.struct_size = sizeof(ws2_event);
        out.event.type = WS2_NOTE_CHOKE;
        out.event.note_id = -1;
        out.event.channel = -1;
        out.event.source_id = UINT32_MAX;
        out.event.flags = 1;
        return true;
    }
    Packet packet, normal, critical;
    for (uint32_t work = 0; work < 2 * p.cfg.ring_capacity; ++work) {
        bool a = p.egress->normal.peek(normal), b = p.egress->critical.peek(critical);
        if (!a && !b) return false;
        Ring &ring = (!a || (b && std::tie(critical.when, critical.order) < std::tie(normal.when, normal.order)))
                         ? p.egress->critical
                         : p.egress->normal;
        if (!ring.pop(packet)) continue;
        if (packet.generation != p.generation.load()) {
            ++p.stale;
            continue;
        }
        out.node = packet.node;
        out.port = packet.port;
        out.frame = packet.when;
        out.time_ns = packet.mapped_time_ns;
        out.generation = packet.generation;
        out.event = packet.event;
        if (out.event.bytes) std::memcpy(out.payload, packet.payload.data(), out.event.bytes);
        out.event.data = out.event.bytes ? out.payload : nullptr;
        return true;
    }
    return false;
}
void Engine::panic() noexcept {
    p_->generation.fetch_add(1, std::memory_order_acq_rel);
    p_->egress_emergency.store(true, std::memory_order_release);
}
void Engine::reset() {
    auto &p = *p_;
    for (uint32_t i = 0; i < p.producer_count; ++i) {
        p.producers[i]->normal.clear();
        p.producers[i]->critical.clear();
    }
    if (p.egress) {
        p.egress->normal.clear();
        p.egress->critical.clear();
    }
    p.reset_processors();
    p.position.store(0);
    p.beat = 0;
    p.anchor_frame = 0;
    p.anchor_ns = p.cfg.epoch_ns;
    p.frames_per_ns = p.cfg.sample_rate / 1.e9;
    p.generation.fetch_add(1);
    p.applied.store(p.generation.load());
    p.replan_chokes.clear();
    p.fade_in = false;
    p.park.store(Park::Running);
}
void Engine::transport(double bpm, bool playing, double beat) {
    if (std::isfinite(bpm) && bpm > 0 && std::isfinite(beat)) {
        p_->cfg.bpm = bpm;
        p_->cfg.playing = playing;
        p_->beat = beat;
    }
}
Meter Engine::meter() const noexcept {
    auto &p = *p_;
    return {p.position.load(),   p.generation.load(),  p.applied.load(),    p.event_count.load(),
            p.dropped.load(),    p.coalesced.load(),   p.ring_full.load(),  p.stale.load(),
            p.late.load(),       p.emergencies.load(), p.arena_full.load(), p.faults.load(),
            p.arena_used.load(), p.feedback_count,     p.latency,           p.setup_bytes};
}
const std::string &Engine::error() const { return p_->error; }
const ws2_descriptor *Engine::descriptor(uint32_t node) const {
    auto *n = p_->find(node);
    return n ? n->instance.d : nullptr;
}
uint32_t Engine::output_channels(uint32_t node, uint32_t port) const {
    auto *n = p_->find(node);
    return n && port < n->instance.global_out.size() ? n->instance.global_out[port].channels : 0;
}
bool Engine::output_constant(uint32_t node, uint32_t port) const {
    auto *n = p_->find(node);
    return n && port < n->instance.global_out.size() && (n->instance.global_out[port].flags & WS2_CONSTANT);
}
float Engine::output_sample(uint32_t node, uint32_t port, uint32_t channel, uint32_t frame) const {
    auto *n = p_->find(node);
    if (!n || port >= n->instance.global_out.size()) return 0;
    auto &b = n->instance.global_out[port];
    return channel < b.channels && frame < p_->cfg.max_block ? b.data[channel][(b.flags & WS2_CONSTANT) ? 0 : frame]
                                                             : 0;
}
uint32_t Engine::feedback_edges() const { return p_->feedback_count; }

void Engine::refresh_latency() noexcept {
    auto &p = *p_;
    if (!p.prepared) return;
    for (auto &n : p.nodes)
        if (n->instance.d && n->instance.instance)
            n->instance.latency = n->instance.d->latency_frames(n->instance.instance);
    p.recompute_latency();
}
uint32_t Engine::latency_frames(uint32_t bus) const { return bus < p_->bus_latency.size() ? p_->bus_latency[bus] : 0; }
std::vector<FeedbackLoop> Engine::feedback_loops() const {
    std::vector<FeedbackLoop> result;
    for (auto &component : p_->components)
        if (component.loop) {
            FeedbackLoop loop;
            loop.delay_frames = p_->cfg.feedback_block;
            for (auto *n : component.nodes) loop.nodes.push_back(n->instance.id);
            std::sort(loop.nodes.begin(), loop.nodes.end());
            result.push_back(std::move(loop));
        }
    return result;
}

std::vector<uint8_t> Engine::save_state(uint32_t node) {
    auto *n = p_->find(node);
    if (!n) return {};
    if (!n->instance.preserved.empty()) return n->instance.preserved;
    std::vector<uint8_t> bytes;
    ws2_writer writer{sizeof(writer), &bytes, [](void *ctx, const void *data, uint32_t count) {
                          auto &out = *static_cast<std::vector<uint8_t> *>(ctx);
                          if (count > 1024 * 1024 - out.size()) return int(WS2_CAPACITY);
                          auto *p = static_cast<const uint8_t *>(data);
                          out.insert(out.end(), p, p + count);
                          return int(WS2_OK);
                      }};
    return n->instance.d->save_state(n->instance.instance, &writer) == WS2_OK ? bytes : std::vector<uint8_t>{};
}
int Engine::load_state(uint32_t node, const std::vector<uint8_t> &bytes) {
    auto *n = p_->find(node);
    if (!n || bytes.size() > 1024 * 1024) return WS2_INVALID;
    struct Context {
        const std::vector<uint8_t> &bytes;
        size_t cursor = 0;
    } context{bytes};
    ws2_reader reader{sizeof(reader), &context,
                      [](void *ctx, void *data, uint32_t count) {
                          auto &c = *static_cast<Context *>(ctx);
                          if (count > c.bytes.size() - c.cursor) return int(WS2_INVALID);
                          std::memcpy(data, c.bytes.data() + c.cursor, count);
                          c.cursor += count;
                          return int(WS2_OK);
                      },
                      static_cast<uint32_t>(bytes.size())};
    int result = n->instance.d->load_state(n->instance.instance, &reader);
    if (result == WS2_UNSUPPORTED) n->instance.preserved = bytes;
    else if (result == WS2_OK) n->instance.preserved.clear();
    return result;
}
const std::vector<uint8_t> &Engine::preserved_state(uint32_t node) const {
    auto *n = p_->find(node);
    if (n) return n->instance.preserved;
    static const std::vector<uint8_t> empty;
    return empty;
}
uint32_t Engine::dropped_connections() const { return p_->dropped_connections; }
bool Engine::reconfigure(uint32_t node, const std::vector<uint8_t> &config) {
    auto &old = *p_;
    auto *changed = old.find(node);
    if (!old.prepared || !changed) return false;
    if (config == changed->instance.config) {
        old.dropped_connections = 0;
        return true;
    }
    Engine next(old.cfg);
    auto &fresh = *next.p_;
    // Stage metadata for retained nodes; only the changed node creates/prepares DSP.
    for (auto &n : old.nodes) {
        if (n->instance.id == node) {
            if (!next.add_node(n->instance.id, n->instance.d, config)) return old.fail("Cannot stage reconfiguration");
            auto *target = fresh.find(node);
            target->instance.config = config;
            target->instance.forced_channels = n->instance.forced_channels;
            target->instance.state = n->instance.state;
            for (uint32_t i = 0; i < target->instance.state.size(); ++i)
                target->instance.state[i].info = target->instance.parameters[i];
        } else {
            auto target = std::make_unique<Node>();
            target->instance.id = n->instance.id;
            target->instance.d = n->instance.d;
            target->instance.inputs = n->instance.inputs;
            target->instance.outputs = n->instance.outputs;
            target->instance.parameters = n->instance.parameters;
            target->instance.forced_channels = n->instance.forced_channels;
            target->instance.latency = n->instance.latency;
            fresh.nodes.push_back(std::move(target));
        }
    }
    auto index_of = [](const auto &ports, const char *id) {
        for (uint32_t i = 0; i < ports.size(); ++i)
            if (!std::strcmp(ports[i].id, id)) return i;
        return UINT32_MAX;
    };
    for (auto &e : old.edges)
        if (!e.removed) {
            auto *a = fresh.find(e.from), *b = fresh.find(e.to);
            auto sp = index_of(a->instance.outputs, e.source->instance.outputs[e.output].id);
            uint32_t dp = UINT32_MAX;
            if (e.kind == 2) dp = index_of(b->instance.parameters, e.destination->instance.parameters[e.input].id);
            else dp = index_of(b->instance.inputs, e.destination->instance.inputs[e.input].id);
            if (sp == UINT32_MAX || dp == UINT32_MAX) {
                ++fresh.dropped_connections;
                continue;
            }
            if (e.kind == 2) {
                if (!next.modulate(e.from, sp, e.to, dp, e.amount)) return old.fail("Staged modulation failed");
            } else if (!next.connect(e.from, sp, e.to, dp)) return old.fail("Staged connection failed");
        }
    for (auto &bus : old.buses) {
        auto *source = old.find(bus.node), *target = fresh.find(bus.node);
        uint32_t port = index_of(target->instance.outputs, source->instance.outputs[bus.port].id);
        if (port == UINT32_MAX) {
            ++fresh.dropped_connections;
            continue;
        }
        if (!next.output(bus.node, port, bus.channel)) return old.fail("Staged bus failed");
    }
    for (uint32_t i = 0; i < old.producer_count; ++i)
        if (next.register_producer() < 0) return old.fail("Staged producer failed");
    // Keep the tap order stable across quiescent reconfiguration. Dynamic port
    // indices can shift, so resolve the old endpoint ID against the new layout.
    // Refuse a removed tap endpoint rather than silently shifting reader slots.
    std::vector<Tap> remapped;
    remapped.reserve(old.taps.size());
    for (const auto &t : old.taps) {
        if (t.kind == Tap::OscPitch) {
            if (!valid_tap(fresh.find(t.node), t)) return old.fail("Reconfiguration removes oscillator pitch layout");
            remapped.push_back(t);
            continue;
        }
        const auto *prior = old.find(t.node);
        const auto *target = fresh.find(t.node);
        const char *id =
            t.kind == Tap::Param ? prior->instance.parameters[t.index].id : prior->instance.outputs[t.index].id;
        const uint32_t index =
            t.kind == Tap::Param ? index_of(target->instance.parameters, id) : index_of(target->instance.outputs, id);
        if (index == UINT32_MAX) return old.fail("Reconfiguration removes telemetry tap endpoint");
        auto mapped = t;
        mapped.index = index;
        remapped.push_back(mapped);
    }
    if (!remapped.empty() && !next.set_telemetry_taps(remapped)) return old.fail("Cannot stage telemetry tap layout");
    if (!fresh.finish_prepare()) return old.fail("Staged graph prepare failed");
    auto bytes = save_state(node);
    if (!bytes.empty()) {
        int r = next.load_state(node, bytes);
        if (r != WS2_OK && r != WS2_UNSUPPORTED) return old.fail("Staged state restore failed");
    }
    std::vector<Node *> actual;
    actual.reserve(fresh.nodes.size());
    for (auto &n : fresh.nodes) actual.push_back(n->instance.id == node ? n.get() : old.find(n->instance.id));
    // Preserve unchanged loop delay lines as well as processor state.
    std::vector<bool> used(old.edges.size(), false);
    std::vector<std::pair<size_t, size_t>> delays;
    for (size_t i = 0; i < fresh.edges.size(); ++i) {
        auto &e = fresh.edges[i];
        if (!e.back || e.kind == 1 || e.from == node || e.to == node) continue;
        for (size_t j = 0; j < old.edges.size(); ++j) {
            auto &v = old.edges[j];
            if (!used[j] && !v.removed && v.back &&
                std::tie(e.from, e.output, e.to, e.input, e.kind, e.amount) ==
                    std::tie(v.from, v.output, v.to, v.input, v.kind, v.amount)) {
                used[j] = true;
                delays.emplace_back(i, j);
                break;
            }
        }
    }
    // Commit: all potentially failing work/allocations precede these swaps.
    for (size_t i = 0; i < fresh.nodes.size(); ++i)
        if (fresh.nodes[i]->instance.id != node) {
            auto &retained = *old.nodes[i];
            auto &layout = *fresh.nodes[i];
            retained.slot.index = layout.slot.index;
            retained.slot.component = layout.slot.component;
            retained.slot.loop = layout.slot.loop;
            retained.slot.incoming.swap(layout.slot.incoming);
            retained.slot.signal_edges.swap(layout.slot.signal_edges);
            retained.slot.modulation.swap(layout.slot.modulation);
            retained.slot.outgoing.swap(layout.slot.outgoing);
            retained.slot.event_tap_slots.swap(layout.slot.event_tap_slots);
            retained.instance.pitch.enabled = layout.instance.pitch.enabled;
            for (uint32_t j = 0; j < retained.instance.event_outputs.size(); ++j)
                retained.instance.event_outputs[j] = {sizeof(ws2_event_out), &fresh, j, Impl::emit};
            fresh.nodes[i].swap(old.nodes[i]);
        }
    for (auto &e : fresh.edges) {
        e.source = actual[e.source->slot.index];
        e.destination = actual[e.destination->slot.index];
    }
    for (auto &component : fresh.components)
        for (auto *&n : component.nodes) n = actual[n->slot.index];
    for (auto *&n : fresh.tap_nodes) n = actual[n->slot.index];
    for (auto &entry : fresh.node_table) entry.second = actual[entry.second->slot.index];
    for (auto &bus : fresh.buses) bus.source = actual[bus.source->slot.index];
    for (auto pair : delays) {
        auto &e = fresh.edges[pair.first];
        auto &v = old.edges[pair.second];
        std::swap(e.delay, v.delay);
        e.delay_channels.swap(v.delay_channels);
        std::swap(e.head, v.head);
    }
    fresh.setup_bytes = 0;
    for (auto &n : fresh.nodes) fresh.setup_bytes += n->instance.requested_fast + n->instance.requested_large;
    fresh.position.store(old.position.load());
    fresh.beat = old.beat;
    fresh.anchor_frame = old.anchor_frame;
    fresh.anchor_ns = old.anchor_ns;
    fresh.frames_per_ns = old.frames_per_ns;
    fresh.revision.store(old.revision.load());
    fresh.generation.store(old.generation.load() + 1);
    fresh.applied.store(fresh.generation.load());
    p_.swap(next.p_);
    return true;
}

bool Engine::replan(Engine &candidate, uint64_t timeout_ns) {
    auto &old = *p_;
    auto &fresh = *candidate.p_;
    if (this == &candidate || !old.prepared || !fresh.prepared || old.park.load() != Park::Running)
        return old.fail("Live graph is unavailable or already parking");
    auto limits = [](const Config &c) {
        return std::tie(c.sample_rate, c.max_block, c.max_channels, c.max_nodes, c.event_budget, c.release_reserve,
                        c.ring_capacity, c.future_capacity, c.message_arena_bytes, c.feedback_block, c.seed,
                        c.max_taps);
    };
    const auto bound = uint64_t(3.e9 * old.cfg.max_block / old.cfg.sample_rate);
    if (limits(old.cfg) != limits(fresh.cfg) || !timeout_ns || timeout_ns > bound)
        return old.fail("Live graph configuration or park deadline differs");
    std::vector<Node *> actual;
    std::vector<std::pair<size_t, size_t>> retained, delays;
    std::vector<std::pair<uint32_t, uint32_t>> chokes;
    std::vector<std::array<uint32_t, 4>> removed_routes;
    std::vector<bool> used(fresh.edges.size(), false), delay_used(old.edges.size(), false);
    const auto next_revision = old.revision.load() + 1;
    if (!next_revision) return old.fail("Live graph revision exhausted");
    actual.reserve(fresh.nodes.size());
    retained.reserve(fresh.nodes.size());
    for (size_t i = 0; i < fresh.nodes.size(); ++i) {
        auto &n = *fresh.nodes[i];
        auto *prior = old.find(n.instance.id);
        if (prior && prior->instance.d == n.instance.d && prior->instance.config == n.instance.config) {
            if (prior->instance.inputs.size() != n.instance.inputs.size() ||
                prior->instance.outputs.size() != n.instance.outputs.size() ||
                prior->instance.parameters.size() != n.instance.parameters.size())
                return old.fail("Surviving node ports changed");
            actual.push_back(prior);
            retained.emplace_back(i, prior->slot.index);
        } else {
            n.instance.born_revision = next_revision;
            actual.push_back(&n);
        }
    }
    auto key = [](const Edge &e) { return std::tie(e.from, e.output, e.to, e.input, e.kind, e.amount); };
    for (auto &e : old.edges)
        if (!e.removed && e.kind == 1) {
            bool kept = false;
            for (size_t i = 0; i < fresh.edges.size(); ++i)
                if (!used[i] && !fresh.edges[i].removed && key(e) == key(fresh.edges[i]) &&
                    actual[fresh.edges[i].source->slot.index] == e.source &&
                    actual[fresh.edges[i].destination->slot.index] == e.destination) {
                    used[i] = true;
                    kept = true;
                    break;
                }
            auto *destination = fresh.find(e.to);
            if (!kept) removed_routes.push_back({e.from, e.output, e.to, e.input});
            if (!kept && destination && actual[destination->slot.index] == e.destination) {
                if (chokes.size() == old.cfg.release_reserve) return old.fail("Too many edge releases for one edit");
                chokes.emplace_back(e.to, e.input);
            }
        }
    for (size_t i = 0; i < fresh.edges.size(); ++i) {
        auto &e = fresh.edges[i];
        if (!e.back || e.kind == 1) continue;
        for (size_t j = 0; j < old.edges.size(); ++j) {
            auto &prior = old.edges[j];
            if (!delay_used[j] && !prior.removed && prior.back && key(e) == key(prior) &&
                actual[e.source->slot.index] == prior.source &&
                actual[e.destination->slot.index] == prior.destination) {
                delay_used[j] = true;
                delays.emplace_back(i, j);
                break;
            }
        }
    }
    std::sort(removed_routes.begin(), removed_routes.end());
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::nanoseconds(timeout_ns);
    auto expected = Park::Running;
    if (!old.park.compare_exchange_strong(expected, Park::Requested, std::memory_order_acq_rel))
        return old.fail("Another graph edit is pending");
    while (old.park.load(std::memory_order_acquire) != Park::Parked) {
        if (std::chrono::steady_clock::now() >= deadline) {
            expected = Park::Requested;
            if (old.park.compare_exchange_strong(expected, Park::Cancelled, std::memory_order_acq_rel))
                return old.fail("Audio did not park before the edit deadline");
            if (expected == Park::Parked) break;
        }
        std::this_thread::yield();
    }
    // All allocation and fallible work precedes the ack. Keep this Impl and its
    // ingress/egress rings, clock, future packets and generation in place.
    // A disconnected feedback edge must not replay an old NoteOn after its choke.
    // Preserve independently scheduled producer events to surviving targets.
    old.future.erase(std::remove_if(old.future.begin(), old.future.end(),
                                    [&](const Packet &p) {
                                        const std::array<uint32_t, 4> route{p.routed_from, p.routed_output, p.node,
                                                                            p.port};
                                        if (!p.routed_from ||
                                            !std::binary_search(removed_routes.begin(), removed_routes.end(), route))
                                            return false;
                                        ++old.stale;
                                        return true;
                                    }),
                     old.future.end());
    for (auto pair : retained) {
        auto &node = *old.nodes[pair.second];
        auto &layout = *fresh.nodes[pair.first];
        node.slot.index = layout.slot.index;
        node.slot.component = layout.slot.component;
        node.slot.loop = layout.slot.loop;
        node.slot.incoming.swap(layout.slot.incoming);
        node.slot.signal_edges.swap(layout.slot.signal_edges);
        node.slot.modulation.swap(layout.slot.modulation);
        node.slot.outgoing.swap(layout.slot.outgoing);
        node.slot.event_tap_slots.swap(layout.slot.event_tap_slots);
        fresh.nodes[pair.first].swap(old.nodes[pair.second]);
    }
    for (auto *n : actual)
        for (uint32_t i = 0; i < n->instance.event_outputs.size(); ++i)
            n->instance.event_outputs[i] = {sizeof(ws2_event_out), &old, i, Impl::emit};
    for (auto *&node : fresh.tap_nodes) node = actual[node->slot.index];
    for (auto &e : fresh.edges) {
        e.source = actual[e.source->slot.index];
        e.destination = actual[e.destination->slot.index];
    }
    for (auto &component : fresh.components)
        for (auto *&n : component.nodes) n = actual[n->slot.index];
    for (auto &entry : fresh.node_table) entry.second = actual[entry.second->slot.index];
    for (auto &bus : fresh.buses) bus.source = actual[bus.source->slot.index];
    for (auto pair : delays) {
        auto &e = fresh.edges[pair.first];
        auto &prior = old.edges[pair.second];
        std::swap(e.delay, prior.delay);
        e.delay_channels.swap(prior.delay_channels);
        std::swap(e.head, prior.head);
    }
    old.nodes.swap(fresh.nodes);
    old.edges.swap(fresh.edges);
    old.components.swap(fresh.components);
    old.node_table.swap(fresh.node_table);
    old.buses.swap(fresh.buses);
    old.bus_latency.swap(fresh.bus_latency);
    old.distance.swap(fresh.distance);
    old.taps.swap(fresh.taps);
    old.tap_nodes.swap(fresh.tap_nodes);
    old.tap_values.swap(fresh.tap_values);
    old.tap_counts.swap(fresh.tap_counts);
    old.tap_sequence.store(0, std::memory_order_relaxed);
    old.tap_frame.store(0, std::memory_order_release);
    old.feedback_count.store(fresh.feedback_count.load());
    old.latency.store(fresh.latency.load());
    size_t bytes = 0;
    for (auto &node : old.nodes) bytes += node->instance.requested_fast + node->instance.requested_large;
    old.setup_bytes.store(bytes);
    old.replan_chokes.swap(chokes);
    old.revision.store(next_revision, std::memory_order_release);
    old.error.clear();
    // Retained instances may have advanced their reported latency since the
    // candidate was prepared. Publish the live result before the park ack.
    refresh_latency();
    old.park.store(Park::Running, std::memory_order_release);
    return true;
}
} // namespace wirescape::engine2
