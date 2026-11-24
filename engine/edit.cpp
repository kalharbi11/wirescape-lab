// SPDX-License-Identifier: GPL-3.0-only
#include "impl.h"
#include "wirescape_sdk.h"
#include <cassert>
#include <chrono>
#include <cstring>
#include <thread>
#include <tuple>

namespace wirescape::engine2 {
void Engine::Impl::recompute_latency() noexcept {
    std::fill(layout->distance.begin(), layout->distance.end(), 0);
    layout->bus_latency.fill(0);
    uint32_t maximum = 0;
    for (auto &component : layout->components)
        for (auto *n : component.nodes) {
            uint32_t upstream = 0;
            for (auto &e : layout->edges)
                if (!e.removed && !e.back && e.kind == 0 && e.destination == n)
                    upstream = std::max(upstream, layout->distance[e.source->slot.index]);
            layout->distance[n->slot.index] =
                static_cast<uint32_t>(std::min<uint64_t>(UINT32_MAX, uint64_t(upstream) + n->instance.latency.load(std::memory_order_relaxed)));
        }
    for (const auto &bus : layout->buses) {
        auto *n = find(bus.node);
        if (!n) continue;
        layout->bus_latency[bus.channel] = std::max(layout->bus_latency[bus.channel], layout->distance[n->slot.index]);
        maximum = std::max(maximum, layout->bus_latency[bus.channel]);
    }
    latency.store(maximum, std::memory_order_relaxed);
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
    if (p.render_layout) p.reset_processors();
    p.position.store(0);
    if (p.prepared) p.reset_beat = true;
    else p.beat = 0;
    p.anchor_frame = 0;
    p.anchor_ns = p.cfg.epoch_ns;
    p.frames_per_ns = p.cfg.sample_rate / 1.e9;
    p.generation.fetch_add(1);
    p.applied.store(p.generation.load());
    if (p.render_layout) p.render_layout->chokes.clear();
}
Edge *Engine::Impl::find_mod_edge(uint32_t from, uint32_t output, uint32_t to, uint32_t input) noexcept {
    return layout->find_mod_edge(from, output, to, input);
}

int Engine::set_mod_amount(uint32_t from, uint32_t output, uint32_t to, uint32_t input, float amount) noexcept {
    auto &p = *p_;
    if (!p.prepared || !p.producer_count) return WS2_STATE;
    if (!std::isfinite(amount) || std::abs(amount) > 1) return WS2_INVALID;
    auto *edge = p.find_mod_edge(from, output, to, input);
    if (!edge) return WS2_INVALID;
    if (edge->sent_serial == UINT64_MAX) return WS2_STATE;
    Packet packet;
    packet.host = true;
    packet.event.type = WS2_PARAM_MOD;
    packet.event.value = amount;
    packet.node = to;
    packet.port = input;
    packet.routed_from = from;
    packet.routed_output = output;
    packet.revision = p.published_revision.load(std::memory_order_acquire);
    packet.order = edge->sent_serial + 1;
    if (!p.producers[0]->critical.push(packet)) {
        ++p.ring_full;
        return WS2_CAPACITY;
    }
    edge->sent_serial = packet.order;
    edge->amount = amount;
    return WS2_OK;
}

int Engine::transport(double bpm, bool playing, std::optional<double> beat) noexcept {
    if (!std::isfinite(bpm) || bpm < 20. || bpm > 300. ||
        (beat && (!std::isfinite(*beat) || *beat < 0.)))
        return WS2_INVALID;
    auto &p = *p_;
    const TransportUpdate update{bpm, beat.value_or(0.), playing, beat.has_value()};
    if (!p.prepared) {
        update.set_values(p.cfg, p.beat);
        return WS2_OK;
    }
    if (!p.producer_count || p.transport_sent == UINT64_MAX) return WS2_STATE;
    Packet packet;
    packet.host = true;
    packet.event.type = WS2_TRANSPORT_EVENT;
    packet.revision = p.published_revision.load(std::memory_order_acquire);
    packet.order = p.transport_sent + 1;
    std::memcpy(packet.payload.data(), &update, sizeof(update));
    if (!p.producers[0]->critical.push(packet)) {
        ++p.ring_full;
        return WS2_CAPACITY;
    }
    p.transport_sent = packet.order;
    return WS2_OK;
}

void Engine::refresh_latency() noexcept {
    auto &p = *p_;
    if (!p.prepared) return;
    p.recompute_latency();
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

bool Engine::Impl::stage_reconfiguration(Engine &next, uint32_t node,
                                         const std::vector<uint8_t> &config) {
    auto &old = *this;
    auto &fresh = *next.p_;
    // Stage metadata for retained nodes; only the changed node creates/prepares DSP.
    for (auto &n : old.layout->nodes) {
        if (n->instance.id == node) {
            if (!next.add_node(n->instance.id, n->instance.d, config)) return old.fail("Cannot stage reconfiguration");
            auto *target = fresh.find(node);
            target->instance.config = config;
            target->instance.forced_channels = n->instance.forced_channels;
            target->instance.state = n->instance.state;
            for (uint32_t i = 0; i < target->instance.state.size(); ++i)
                target->instance.state[i].info = target->instance.parameters[i];
        } else {
            auto instance = std::make_unique<Instance>();
            auto target = std::make_unique<Node>(*instance);
            target->instance.id = n->instance.id;
            target->instance.d = n->instance.d;
            target->instance.inputs = n->instance.inputs;
            target->instance.outputs = n->instance.outputs;
            target->instance.parameters = n->instance.parameters;
            target->instance.forced_channels = n->instance.forced_channels;
            target->instance.latency.store(n->instance.latency.load(std::memory_order_relaxed));
            fresh.instances.emplace(n->instance.id, std::move(instance));
            fresh.layout->nodes.push_back(std::move(target));
        }
    }
    auto index_of = [](const auto &ports, const char *id) {
        for (uint32_t i = 0; i < ports.size(); ++i)
            if (!std::strcmp(ports[i].id, id)) return i;
        return UINT32_MAX;
    };
    for (auto &e : old.layout->edges)
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
    for (auto &bus : old.layout->buses) {
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
    remapped.reserve(old.layout->taps.size());
    for (const auto &t : old.layout->taps) {
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
    return true;
}

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
    if (!old.stage_reconfiguration(next, node, config)) return false;
    fresh.beat = old.beat;
    fresh.reset_beat = old.reset_beat;
    fresh.transport_sent = old.transport_sent;
    fresh.transport_applied = old.transport_applied;
    if (!fresh.finish_prepare()) return old.fail("Staged graph prepare failed");
    auto bytes = save_state(node);
    if (!bytes.empty()) {
        int r = next.load_state(node, bytes);
        if (r != WS2_OK && r != WS2_UNSUPPORTED) return old.fail("Staged state restore failed");
    }
    std::vector<Node *> actual;
    actual.reserve(fresh.layout->nodes.size());
    for (auto &n : fresh.layout->nodes) actual.push_back(n->instance.id == node ? n.get() : old.find(n->instance.id));
    // Preserve unchanged loop delay lines as well as processor state.
    const auto next_revision = old.published_revision.load() + 1;
    if (!next_revision) return old.fail("Live graph revision exhausted");
    for (auto &e : fresh.layout->edges) {
        if (e.kind != 2) continue;
        e.born_revision = next_revision;
        if (e.from == node || e.to == node) continue;
        auto *prior = old.find_mod_edge(e.from, e.output, e.to, e.input);
        if (!prior) continue;
        e.state->modulation = prior->state->modulation;
        e.born_revision = prior->born_revision;
        e.sent_serial = prior->sent_serial;
    }
    std::vector<bool> used(old.layout->edges.size(), false);
    std::vector<std::pair<size_t, size_t>> delays;
    for (size_t i = 0; i < fresh.layout->edges.size(); ++i) {
        auto &e = fresh.layout->edges[i];
        if (!e.back || e.kind == 1 || e.from == node || e.to == node) continue;
        for (size_t j = 0; j < old.layout->edges.size(); ++j) {
            auto &v = old.layout->edges[j];
            if (!used[j] && !v.removed && v.back &&
                e.key() == v.key()) {
                used[j] = true;
                delays.emplace_back(i, j);
                break;
            }
        }
    }
    std::vector<std::unique_ptr<Node>> entries(fresh.layout->nodes.size());
    for (size_t i = 0; i < fresh.layout->nodes.size(); ++i)
        if (fresh.layout->nodes[i]->instance.id != node)
            entries[i] = std::make_unique<Node>(actual[i]->instance);
    // Commit: all potentially failing work/allocations precede these swaps.
    for (size_t i = 0; i < fresh.layout->nodes.size(); ++i)
        if (entries[i]) {
            auto &retained = *actual[i];
            auto &entry = *entries[i];
            entry.slot = std::move(fresh.layout->nodes[i]->slot);
            entry.slot.in.swap(retained.slot.in);
            entry.slot.in_view.swap(retained.slot.in_view);
            entry.slot.param_view.swap(retained.slot.param_view);
            for (uint32_t j = 0; j < retained.instance.event_outputs.size(); ++j)
                retained.instance.event_outputs[j] = {sizeof(ws2_event_out), &fresh, j, Impl::emit};
            old.instances.find(retained.instance.id)->second.swap(fresh.instances.find(retained.instance.id)->second);
            actual[i] = &entry;
        }
    for (auto &e : fresh.layout->edges) {
        e.source = actual[e.source->slot.index];
        e.destination = actual[e.destination->slot.index];
    }
    for (auto &component : fresh.layout->components)
        for (auto *&n : component.nodes) n = actual[n->slot.index];
    for (auto *&n : fresh.layout->tap_nodes) n = actual[n->slot.index];
    for (auto &entry : fresh.layout->node_table) entry.second = actual[entry.second->slot.index];
    for (auto &bus : fresh.layout->buses) bus.source = actual[bus.source->slot.index];
    for (size_t i = 0; i < entries.size(); ++i)
        if (entries[i]) fresh.layout->nodes[i].swap(entries[i]);
    for (auto pair : delays) {
        auto &e = fresh.layout->edges[pair.first];
        auto &v = old.layout->edges[pair.second];
        std::swap(e.state->delay, v.state->delay);
        e.state->delay_channels.swap(v.state->delay_channels);
        std::swap(e.state->head, v.state->head);
    }
    fresh.setup_bytes = 0;
    for (auto &n : fresh.layout->nodes) fresh.setup_bytes += n->instance.requested_fast + n->instance.requested_large;
    fresh.position.store(old.position.load());
    fresh.anchor_frame = old.anchor_frame;
    fresh.anchor_ns = old.anchor_ns;
    fresh.frames_per_ns = old.frames_per_ns;
    fresh.published_revision.store(next_revision);
    fresh.adopted_revision.store(next_revision);
    fresh.layout->revision = next_revision;
    fresh.generation.store(old.generation.load() + 1);
    fresh.applied.store(fresh.generation.load());
    // Quiescent replacement retires module ingress but keeps acknowledged
    // host updates in send order. The new ring is empty and the same capacity.
    if (old.producer_count) {
        Packet packet;
        while (old.producers[0]->critical.pop(packet))
            if (packet.host) {
                const bool pushed = fresh.producers[0]->critical.push(packet);
                assert(pushed && "host packet must fit in replacement ring");
                (void)pushed;
            }
    }
    p_.swap(next.p_);
    return true;
}

bool Engine::Impl::plan_edge_transitions(Impl &fresh, const std::vector<Node *> &actual,
                                         std::vector<bool> &used, std::vector<bool> &delay_used,
                                         std::vector<std::pair<uint32_t, uint32_t>> &chokes,
                                         std::vector<std::array<uint32_t, 4>> &removed_routes,
                                         std::vector<std::pair<size_t, size_t>> &delays) {
    auto &old = *this;
    for (auto &e : old.layout->edges)
        if (!e.removed && e.kind == 1) {
            bool kept = false;
            for (size_t i = 0; i < fresh.layout->edges.size(); ++i)
                if (!used[i] && !fresh.layout->edges[i].removed && e.key() == fresh.layout->edges[i].key() &&
                    actual[fresh.layout->edges[i].source->slot.index] == e.source &&
                    actual[fresh.layout->edges[i].destination->slot.index] == e.destination) {
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
    for (size_t i = 0; i < fresh.layout->edges.size(); ++i) {
        auto &e = fresh.layout->edges[i];
        if (!e.back || e.kind == 1) continue;
        for (size_t j = 0; j < old.layout->edges.size(); ++j) {
            auto &prior = old.layout->edges[j];
            if (!delay_used[j] && !prior.removed && prior.back && e.key() == prior.key() &&
                actual[e.source->slot.index] == prior.source &&
                actual[e.destination->slot.index] == prior.destination) {
                delay_used[j] = true;
                delays.emplace_back(i, j);
                break;
            }
        }
    }
    std::sort(removed_routes.begin(), removed_routes.end());
    return true;
}

bool Engine::replan(Engine &candidate, uint64_t timeout_ns) {
    auto &old = *p_;
    auto &fresh = *candidate.p_;
    if (this == &candidate || !old.prepared || !fresh.prepared || old.pending_layout.load())
        return old.fail("Live graph is unavailable or already publishing");
    auto limits = [](const Config &c) {
        return std::tie(c.sample_rate, c.max_block, c.max_channels, c.max_nodes, c.event_budget, c.release_reserve,
                        c.ring_capacity, c.future_capacity, c.message_arena_bytes, c.feedback_block, c.seed, c.max_taps);
    };
    const auto bound = uint64_t(3.e9 * old.cfg.max_block / old.cfg.sample_rate);
    if (limits(old.cfg) != limits(fresh.cfg) || !timeout_ns || timeout_ns > bound)
        return old.fail("Live graph configuration or adoption deadline differs");
    const auto next_revision = old.published_revision.load(std::memory_order_acquire) + 1;
    if (!next_revision) return old.fail("Live graph revision exhausted");

    // Build a separate layout without writing the current render layout or DSP.
    // The candidate remains intact on a timeout (the stopped-stream fallback
    // can still use it). All layout scratch and state storage are allocated here.
    Impl staged(fresh.cfg);
    auto &next = *staged.layout;
    next.revision = next_revision;
    std::vector<uint32_t> retained, introduced;
    for (auto &candidate_node : fresh.layout->nodes) {
        auto &candidate_instance = candidate_node->instance;
        auto *prior = old.find(candidate_instance.id);
        Instance *instance = &candidate_instance;
        if (prior && prior->instance.d == instance->d && prior->instance.config == instance->config) {
            if (prior->instance.inputs.size() != instance->inputs.size() ||
                prior->instance.outputs.size() != instance->outputs.size() ||
                prior->instance.parameters.size() != instance->parameters.size())
                return old.fail("Surviving node ports changed");
            instance = &prior->instance;
            retained.push_back(instance->id);
        } else introduced.push_back(instance->id);
        auto entry = std::make_unique<Node>(*instance);
        entry->slot.in.resize(instance->inputs.size());
        for (auto &buffer : entry->slot.in) buffer.prepare(old.cfg.max_channels, old.cfg.max_block);
        entry->slot.in_view.resize(instance->inputs.size());
        entry->slot.param_view.resize(instance->parameters.size());
        next.setup_bytes += instance->requested_fast + instance->requested_large;
        next.nodes.push_back(std::move(entry));
    }
    for (const auto &edge : fresh.layout->edges)
        if (!edge.removed) next.edges.push_back({edge.from, edge.output, edge.to, edge.input, edge.kind, edge.amount});
    next.buses = fresh.layout->buses;
    next.taps = fresh.layout->taps;
    next.tap_values = std::make_unique<std::atomic<float>[]>(next.taps.size());
    next.tap_counts = std::make_unique<std::atomic<uint32_t>[]>(next.taps.size());
    for (size_t i = 0; i < next.taps.size(); ++i) {
        next.tap_values[i].store(0, std::memory_order_relaxed);
        next.tap_counts[i].store(0, std::memory_order_relaxed);
    }
    if (!staged.topology()) return old.fail("Cannot build live layout");
    for (auto &bus : next.buses) bus.source = staged.find(bus.node);
    if (!staged.resolve_taps()) return old.fail("Cannot build live tap layout");
    next.feedback_count = staged.feedback_count.load();
    std::vector<Node *> actual;
    for (auto &n : next.nodes) {
        auto *prior = old.find(n->instance.id);
        actual.push_back(prior && &prior->instance == &n->instance ? prior : n.get());
    }
    std::vector<bool> used(next.edges.size(), false), delay_used(old.layout->edges.size(), false);
    std::vector<std::pair<size_t, size_t>> delays;
    if (!old.plan_edge_transitions(staged, actual, used, delay_used, next.chokes, next.removed_routes, delays))
        return false;
    for (auto &edge : next.edges) {
        edge.born_revision = next_revision;
        auto prior = std::lower_bound(old.layout->edges.begin(), old.layout->edges.end(), edge.key(),
                                      [](const Edge &e, const auto &key) { return e.key() < key; });
        for (; prior != old.layout->edges.end() && prior->key() == edge.key(); ++prior) {
            if (prior->removed || &prior->source->instance != &edge.source->instance ||
                &prior->destination->instance != &edge.destination->instance) continue;
            edge.born_revision = prior->born_revision;
            edge.sent_serial = prior->sent_serial;
            // Same feedback classification: retain the state object itself.
            // A newly introduced delay has its own preallocated storage.
            if (edge.back == prior->back) edge.state = prior->state;
            if (edge.kind == 2)
                next.modulation_adoption.push_back({&edge, prior->state, edge.amount != prior->amount});
            break;
        }
    }
    // New instances are quiescent until adoption. Retained emitters already
    // refer to this Impl and are not rewritten from the control thread.
    for (auto id : introduced) {
        auto &instance = *fresh.instances.at(id);
        instance.born_revision = next_revision;
        for (uint32_t i = 0; i < instance.event_outputs.size(); ++i)
            instance.event_outputs[i] = {sizeof(ws2_event_out), &old, i, Impl::emit};
    }
    auto *published = &next;
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::nanoseconds(timeout_ns);
    old.pending_layout.store(published, std::memory_order_release);
    bool claimed = false;
    while (old.adopted_revision.load(std::memory_order_acquire) < next_revision) {
        if (!claimed && std::chrono::steady_clock::now() >= deadline) {
            auto *expected = published;
            if (old.pending_layout.compare_exchange_strong(expected, nullptr, std::memory_order_acq_rel)) {
                for (auto id : introduced) {
                    auto &instance = *fresh.instances.at(id);
                    instance.born_revision = 0;
                    for (uint32_t i = 0; i < instance.event_outputs.size(); ++i)
                        instance.event_outputs[i] = {sizeof(ws2_event_out), &fresh, i, Impl::emit};
                }
                return old.fail("Audio did not adopt before the edit deadline");
            }
            // A51: a lost cancellation race is a claim, never a refusal.
            claimed = true;
        }
        std::this_thread::yield();
    }
    // No render can touch the previous layout after the acquire above.
    // Transfer control ownership without allocation, then retire the previous
    // layout and unreferenced state. The render pointer is never control-written.
    for (auto id : retained) old.instances.at(id).swap(fresh.instances.at(id));
    old.instances.swap(fresh.instances);
    for (auto &edge : next.edges) {
        auto state = old.edge_states.extract(edge.state);
        if (!state.empty()) staged.edge_states.insert(std::move(state));
    }
    old.layout.swap(staged.layout);
    old.edge_states.swap(staged.edge_states);
    for (auto it = old.edge_states.begin(); it != old.edge_states.end();) {
        if (std::none_of(next.edges.begin(), next.edges.end(), [&](const Edge &edge) { return edge.state == it->first; }))
            it = old.edge_states.erase(it);
        else ++it;
    }
    old.recompute_latency();
    old.published_revision.store(next_revision, std::memory_order_release);
    old.error.clear();
    return true;
}
} // namespace wirescape::engine2
