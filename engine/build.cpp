// SPDX-License-Identifier: GPL-3.0-only
#include "impl.h"
#include "wirescape_sdk.h"
#include <cstring>
#include <functional>
#include <tuple>

namespace wirescape::engine2 {
namespace {
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
} // namespace

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
    n.instance.held_notes.reserve(Instance::held_note_capacity);
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
    layout->tap_nodes.clear();
    layout->tap_nodes.reserve(layout->taps.size());
    for (auto &node : layout->nodes) {
        node->slot.event_tap_slots.clear();
        node->slot.pitch.enabled = false;
    }
    for (uint32_t i = 0; i < layout->taps.size(); ++i) {
        const auto &t = layout->taps[i];
        auto *n = find(t.node);
        if (!valid_tap(n, t)) return fail("Telemetry tap endpoint changed during prepare");
        if (t.kind == Tap::OscPitch) {
            if (!pitch_layout(n, n->slot.pitch)) return fail("Oscillator pitch layout changed during prepare");
            n->slot.pitch.enabled = true;
        }
        layout->tap_nodes.push_back(n);
        if (t.kind == Tap::EventOut) {
            if (n->slot.event_tap_slots.empty()) n->slot.event_tap_slots.assign(n->instance.outputs.size(), UINT32_MAX);
            n->slot.event_tap_slots[t.index] = i;
        }
    }
    return true;
}

bool Engine::Impl::finish_prepare() {
    if (!topology()) return false;
    for (auto &bus : layout->buses) {
        auto *n = find(bus.node);
        if (!n || bus.port >= n->instance.outputs.size()) return fail("Output no longer exists");
        bus.source = n;
    }
    if (!resolve_taps()) return false;
    arena.resize(cfg.message_arena_bytes);
    egress = std::make_unique<Producer>(cfg.ring_capacity);
    prepared = true;
    render_layout = layout.get();
    applied.store(generation.load());
    return true;
}


bool Engine::Impl::wire_edges() {
    std::stable_sort(layout->nodes.begin(), layout->nodes.end(), [](const auto &a, const auto &b) {
        return std::tie(a->instance.id, a->retired) < std::tie(b->instance.id, b->retired);
    });
    for (uint32_t i = 0; i < layout->nodes.size(); ++i) layout->nodes[i]->slot.index = i;
    std::stable_sort(layout->edges.begin(), layout->edges.end(), [](const Edge &a, const Edge &b) {
        return a.key() < b.key();
    });
    for (auto &e : layout->edges) {
        if (!e.source) e.source = find(e.from);
        if (!e.destination) e.destination = find(e.to);
        e.back = false;
        if (e.removed && !e.ramped) continue;
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
    layout->node_table.clear();
    for (auto &n : layout->nodes) {
        if (!n->retired) layout->node_table.emplace_back(n->instance.id, n.get());
        n->slot.incoming.assign(n->instance.inputs.size(), nullptr);
        n->slot.signal_edges.clear();
        n->slot.transition_inputs.clear();
        n->slot.modulation.assign(n->instance.parameters.size(), {});
        n->slot.outgoing.assign(n->instance.outputs.size(), {});
    }
    for (auto &e : layout->edges)
        if (!e.removed || e.ramped) {
            if (e.kind == 0) {
                auto &slot = e.destination->slot;
                if (!slot.incoming[e.input] || !e.removed) slot.incoming[e.input] = &e;
                if (e.ramped && slot.transition_inputs.empty()) slot.transition_inputs.resize(slot.incoming.size());
            }
            if (e.kind == 2) e.destination->slot.modulation[e.input].push_back(&e);
            if (e.kind == 1) e.source->slot.outgoing[e.output].push_back(&e);
            else e.destination->slot.signal_edges.push_back(&e);
        }
    for (auto &e : layout->edges)
        if (e.kind == 0 && (!e.removed || e.ramped) && !e.destination->slot.transition_inputs.empty())
            e.destination->slot.transition_inputs[e.input].push_back(&e);
    // Only affected input ports use the copy/blend path.
    for (auto &n : layout->nodes)
        for (auto &inputs : n->slot.transition_inputs)
            if (std::none_of(inputs.begin(), inputs.end(), [](const Edge *e) { return e->ramped; }))
                inputs.clear();
    return true;
}

void Engine::Impl::find_components() {
    const uint32_t count = static_cast<uint32_t>(layout->nodes.size());
    std::vector<int> index(count, -1), low(count), stack;
    std::vector<bool> on(count, false);
    int next = 0;
    layout->components.clear();
    std::function<void(uint32_t)> visit = [&](uint32_t v) {
        index[v] = low[v] = next++;
        stack.push_back(v);
        on[v] = true;
        for (auto &e : layout->edges)
            if ((!e.removed || e.ramped) && e.source->slot.index == v) {
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
                layout->nodes[w]->slot.component = static_cast<uint32_t>(layout->components.size());
                component.nodes.push_back(layout->nodes[w].get());
                if (w == v) break;
            }
            layout->components.push_back(std::move(component));
        }
    };
    for (uint32_t i = 0; i < count; ++i)
        if (index[i] < 0) visit(i);
}

bool Engine::Impl::order_feedback_components() {
    const uint32_t count = static_cast<uint32_t>(layout->nodes.size());
    feedback_count = 0;
    for (auto &component : layout->components) {
        std::sort(component.nodes.begin(), component.nodes.end(),
                  [](auto *a, auto *b) { return a->instance.id < b->instance.id; });
        component.loop = component.nodes.size() > 1;
        std::vector<uint8_t> colour(count, 0);
        std::function<void(Node *)> dfs = [&](Node *n) {
            colour[n->slot.index] = 1;
            for (auto &e : layout->edges)
                if ((!e.removed || e.ramped) && e.source == n && e.destination->slot.component == n->slot.component) {
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
        for (auto &e : layout->edges)
            if ((!e.removed || e.ramped) && !e.back && e.source->slot.component == e.destination->slot.component &&
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
            for (auto &e : layout->edges)
                if ((!e.removed || e.ramped) && !e.back && e.source == chosen &&
                    e.destination->slot.component == chosen->slot.component)
                    --degree[e.destination->slot.index];
        }
        component.nodes = std::move(sorted);
    }
    return true;
}

bool Engine::Impl::order_components() {
    std::vector<uint32_t> degree(layout->components.size(), 0);
    for (auto &e : layout->edges)
        if ((!e.removed || e.ramped) && e.source->slot.component != e.destination->slot.component)
            ++degree[e.destination->slot.component];
    std::vector<Component> ordered_components;
    std::vector<bool> used(layout->components.size(), false);
    while (ordered_components.size() < layout->components.size()) {
        uint32_t chosen = UINT32_MAX, best = UINT32_MAX;
        for (uint32_t i = 0; i < layout->components.size(); ++i)
            if (!used[i] && !degree[i]) {
                uint32_t id = UINT32_MAX;
                for (auto *n : layout->components[i].nodes) id = std::min(id, n->instance.id);
                if (id < best) {
                    best = id;
                    chosen = i;
                }
            }
        if (chosen == UINT32_MAX) return fail("Invalid component graph");
        used[chosen] = true;
        for (auto &e : layout->edges)
            if ((!e.removed || e.ramped) && e.source->slot.component == chosen && e.destination->slot.component != chosen)
                --degree[e.destination->slot.component];
        ordered_components.push_back(std::move(layout->components[chosen]));
    }
    layout->components = std::move(ordered_components);
    return true;
}

bool Engine::Impl::topology() {
    if (!wire_edges()) return false;
    find_components();
    if (!order_feedback_components() || !order_components()) return false;
    for (auto &e : layout->edges) {
        auto state = std::make_unique<EdgeState>();
        state->modulation.current = state->modulation.target = e.amount;
        if (e.back && e.kind != 1) {
            state->delay.prepare(cfg.max_channels, cfg.feedback_block);
            state->delay_channels.assign(cfg.feedback_block, 0);
        }
        e.state = state.get();
        edge_states.emplace(state.get(), std::move(state));
    }
    for (auto &bus : layout->buses) {
        if (!bus.source) bus.source = find(bus.node);
        auto state = std::make_unique<EdgeState>();
        bus.state = state.get();
        edge_states.emplace(state.get(), std::move(state));
    }
    for (auto &component : layout->components)
        for (auto *n : component.nodes) n->slot.loop = component.loop;
    // Scratch is sized during topology/prepare, never during a status refresh.
    layout->distance.resize(layout->nodes.size());
    recompute_latency();
    return true;
}

bool Engine::add_node(uint32_t id, const ws2_descriptor *d, const std::vector<uint8_t> &config) {
    auto &p = *p_;
    if (!p.cfg.max_channels || p.cfg.max_channels > 16 || !p.cfg.max_block || p.cfg.max_block > 4096)
        return p.fail("Invalid setup bounds");
    if (p.prepared || !id || p.find(id) || p.layout->nodes.size() >= p.cfg.max_nodes || !d ||
        d->struct_size < offsetof(ws2_descriptor, data_slot_count) || d->abi_version != 2 || !d->id || !d->name || !d->create ||
        !d->destroy || !d->query_ports || !d->memory_requirements || !d->prepare || !d->reset || !d->process ||
        !d->save_state || !d->load_state || !d->latency_frames || d->input_count > WS2_MAX_PORTS ||
        d->output_count > WS2_MAX_PORTS || d->param_count > WS2_MAX_PARAMS || (d->input_count && !d->inputs) ||
        (d->output_count && !d->outputs) || (d->param_count && !d->params))
        return p.fail("Invalid ABI2 node");
    auto instance = std::make_unique<Instance>();
    auto n = std::make_unique<Node>(*instance);
    n->instance.id = id;
    n->instance.d = d;
    n->instance.config = config;
    if (!initialize_data_slots(*d, instance->data, p.error)) return false;
    if (d->input_count) n->instance.inputs.assign(d->inputs, d->inputs + d->input_count);
    if (d->output_count) n->instance.outputs.assign(d->outputs, d->outputs + d->output_count);
    if (d->param_count) n->instance.parameters.assign(d->params, d->params + d->param_count);
    for (const auto &info : n->instance.parameters) n->instance.state.emplace_back(info);
    // Resolve configuration-dependent ports quiescently before cable authoring.
    if (!p.setup(*n)) return false;
    p.instances.emplace(id, std::move(instance));
    p.layout->nodes.push_back(std::move(n));
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
        for (auto &e : p.layout->edges)
            if (e.kind == 0 && e.to == to && e.input == input) return p.fail("Signal input already connected");
    p.layout->edges.push_back({from, output, to, input, kind == WS2_EVENT ? 1 : 0, 0});
    return true;
}
bool Engine::modulate(uint32_t from, uint32_t output, uint32_t to, uint32_t param, float amount) {
    auto &p = *p_;
    auto *a = p.find(from), *b = p.find(to);
    if (p.prepared || !a || !b || output >= a->instance.outputs.size() || param >= b->instance.parameters.size() ||
        a->instance.outputs[output].kind != WS2_SIGNAL || !(b->instance.parameters[param].flags & WS2_MODULATABLE) ||
        !std::isfinite(amount) || amount < -1 || amount > 1)
        return p.fail("Invalid modulation cable");
    for (const auto &edge : p.layout->edges)
        if (!edge.removed && edge.key() == std::tuple{from, output, to, param, 2})
            return p.fail("Duplicate modulation cable");
    p.layout->edges.push_back({from, output, to, param, 2, amount});
    return true;
}
bool Engine::output(uint32_t node, uint32_t port, uint32_t channel) {
    auto &p = *p_;
    auto *n = p.find(node);
    if (p.prepared || !n || port >= n->instance.outputs.size() || n->instance.outputs[port].kind != WS2_SIGNAL ||
        channel >= 32)
        return p.fail("Invalid output bus");
    p.layout->buses.push_back({node, port, channel});
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
    p.layout->taps = requested;
    p.layout->tap_values.swap(values);
    p.layout->tap_counts.swap(counts);
    p.layout->tap_nodes.clear();
    p.tap_frame.store(0, std::memory_order_relaxed);
    p.tap_sequence.store(0, std::memory_order_relaxed);
    return true;
}

bool Engine::prepare() {
    auto &p = *p_;
    if (p.prepared) return p.fail("Prepare is quiescent and single-use; replan uses a prepared candidate");
    if (!std::isfinite(p.cfg.sample_rate) || p.cfg.sample_rate < 1000 || p.cfg.sample_rate > 384000 ||
        !p.cfg.max_channels || p.cfg.max_channels > 16 || !p.cfg.max_block || p.cfg.max_block > 4096 ||
        !p.cfg.max_nodes || p.cfg.max_nodes > 1024 || p.cfg.event_budget < 2 || p.cfg.event_budget > 65536 ||
        !p.cfg.release_reserve || p.cfg.release_reserve >= p.cfg.event_budget || !p.cfg.ring_capacity ||
        p.cfg.ring_capacity > 65536 || !p.cfg.future_capacity || p.cfg.future_capacity > 65536 ||
        !p.cfg.feedback_block || p.cfg.feedback_block > p.cfg.max_block ||
        p.cfg.message_arena_bytes > 64 * 1024 * 1024 || p.cfg.max_taps > 4096)
        return p.fail("Invalid engine2 configuration");
    p.setup_bytes = 0;
    for (auto &n : p.layout->nodes)
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


} // namespace wirescape::engine2
