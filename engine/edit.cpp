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
    if (p.prepared) p.reset_beat = true;
    else p.beat = 0;
    p.anchor_frame = 0;
    p.anchor_ns = p.cfg.epoch_ns;
    p.frames_per_ns = p.cfg.sample_rate / 1.e9;
    p.generation.fetch_add(1);
    p.applied.store(p.generation.load());
    p.replan_chokes.clear();
    p.fade_in = false;
    p.park.store(Park::Running);
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
    for (auto &n : p.nodes)
        if (n->instance.d && n->instance.instance)
            n->instance.latency = n->instance.d->latency_frames(n->instance.instance);
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
    fresh.anchor_frame = old.anchor_frame;
    fresh.anchor_ns = old.anchor_ns;
    fresh.frames_per_ns = old.frames_per_ns;
    fresh.revision.store(old.revision.load());
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
    if (!old.plan_edge_transitions(fresh, actual, used, delay_used, chokes, removed_routes, delays))
        return false;
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
