// SPDX-License-Identifier: GPL-3.0-only
#include "impl.h"
#include "publication.h"
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
        if (bus.removed) continue;
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
    p.last_settle_attempt_position.reset();
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
    p.settle_layout();
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
        if (n->retired) continue;
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
        if (bus.removed) continue;
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
    fresh.settled_revision.store(next_revision);
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

bool Engine::Impl::publish_layout(Layout *next, uint64_t timeout_ns) noexcept {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::nanoseconds(timeout_ns);
    return publish_and_wait(pending_layout, adopted_revision, next, next->revision, deadline,
                            [] { return std::chrono::steady_clock::now(); },
                            [] { std::this_thread::yield(); });
}

void Engine::Impl::prune_edge_states() noexcept {
    auto referenced = [](const Layout *l, const EdgeState *state) {
        return l && (std::any_of(l->edges.begin(), l->edges.end(), [&](const Edge &edge) { return edge.state == state; }) ||
                     std::any_of(l->buses.begin(), l->buses.end(), [&](const Bus &bus) { return bus.state == state; }));
    };
    for (auto it = edge_states.begin(); it != edge_states.end();) {
        if (!referenced(layout.get(), it->first) && !referenced(steady_layout.get(), it->first))
            it = edge_states.erase(it);
        else ++it;
    }
}

void Engine::Impl::settle_layout() noexcept {
    if (!steady_layout || settled_revision.load(std::memory_order_acquire) < layout->revision) return;
    // Retry only after a callback advances the render position. If audio
    // stopped, repeated status refreshes must not each wait three blocks.
    const auto frame = position.load(std::memory_order_acquire);
    if (last_settle_attempt_position == frame) return;
    last_settle_attempt_position = frame;
    // The next edit may also fold this housekeeping into its transition.
    // A stopped stream can cancel this attempt without changing the graph.
    auto &steady = *steady_layout;
    for (auto &edge : steady.edges) {
        if (edge.kind != 2) continue;
        auto *prior = layout->find_mod_edge(edge.from, edge.output, edge.to, edge.input);
        if (prior) {
            edge.amount = prior->amount;
            edge.sent_serial = prior->sent_serial;
        }
    }
    const auto revision = published_revision.load(std::memory_order_acquire) + 1;
    if (!revision) return;
    steady.revision = revision;
    const auto bound = uint64_t(3.e9 * cfg.max_block / cfg.sample_rate);
    if (!publish_layout(&steady, bound)) return;
    layout.swap(steady_layout);
    steady_layout.reset();
    last_settle_attempt_position.reset();
    retired_instances.clear();
    prune_edge_states();
    published_revision.store(revision, std::memory_order_release);
}

bool Engine::replan(Engine &candidate, uint64_t timeout_ns) {
    auto &old = *p_;
    auto &fresh = *candidate.p_;
    if (this == &candidate || !old.prepared || !fresh.prepared || old.pending_layout.load())
        return old.fail("Live graph is unavailable or already publishing");
    auto limits = [](const Config &c) {
        return std::tie(c.sample_rate, c.max_block, c.max_channels, c.max_nodes, c.event_budget, c.release_reserve,
                        c.ring_capacity, c.future_capacity, c.message_arena_bytes, c.feedback_block, c.seed,
                        c.max_taps);
    };
    const auto bound = uint64_t(3.e9 * old.cfg.max_block / old.cfg.sample_rate);
    if (limits(old.cfg) != limits(fresh.cfg) || !timeout_ns || timeout_ns > bound)
        return old.fail("Live graph configuration or adoption deadline differs");
    const auto next_revision = old.published_revision.load(std::memory_order_acquire) + 1;
    if (!next_revision) return old.fail("Live graph revision exhausted");
    const bool settled = old.settled_revision.load(std::memory_order_acquire) >= old.layout->revision;
    auto finished_removal = [&](const auto &edge) {
        return edge.removed && (settled || edge.state->faded_out.load(std::memory_order_acquire));
    };

    Impl staged(fresh.cfg), steady(fresh.cfg);
    auto &next = *staged.layout;
    auto &target = *steady.layout;
    next.revision = next_revision;
    target.housekeeping = true;
    std::vector<uint32_t> retained, introduced;
    std::map<Instance *, Node *> transition_nodes, target_nodes;
    std::map<uint32_t, Instance *> target_instances;
    auto add_entry = [&](Layout &l, auto &index, Instance &instance, bool retired) {
        auto entry = std::make_unique<Node>(instance);
        entry->retired = retired;
        entry->slot.in.resize(instance.inputs.size());
        for (auto &buffer : entry->slot.in) buffer.prepare(old.cfg.max_channels, old.cfg.max_block);
        entry->slot.in_view.resize(instance.inputs.size());
        entry->slot.param_view.resize(instance.parameters.size());
        auto *result = entry.get();
        l.setup_bytes += instance.requested_fast + instance.requested_large;
        l.nodes.push_back(std::move(entry));
        index.emplace(&instance, result);
        return result;
    };
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
        target_instances.emplace(instance->id, instance);
        add_entry(next, transition_nodes, *instance, false);
        add_entry(target, target_nodes, *instance, false);
    }
    auto include_retired = [&](Instance &instance) {
        if (transition_nodes.count(&instance)) return false;
        add_entry(next, transition_nodes, instance, true);
        return true;
    };
    // An output bus is an outgoing signal edge. Keep its source if its old
    // contribution must fade, but never keep output-less removed sinks.
    for (const auto &bus : old.layout->buses)
        if (!finished_removal(bus)) include_retired(bus.source->instance);
    // Keep the old upstream signal/modulation path only when it can reach
    // a destination or a bus which remains in the transition.
    bool added;
    do {
        added = false;
        for (const auto &edge : old.layout->edges)
            if (edge.kind != 1 && !finished_removal(edge) &&
                transition_nodes.count(&edge.destination->instance))
                added |= include_retired(edge.source->instance);
    } while (added);

    std::map<Instance *, Instance *> replacement_pairs;
    for (auto id : introduced) {
        auto *prior = old.find(id);
        auto *successor = target_instances.at(id);
        if (prior && prior->instance.d == successor->d && prior->instance.config != successor->config) {
            auto tail = transition_nodes.find(&prior->instance);
            next.replacements.push_back({&prior->instance, transition_nodes.at(successor),
                tail == transition_nodes.end() ? nullptr : tail->second});
            replacement_pairs.emplace(&prior->instance, successor);
        }
    }
    auto replacement_of = [&](Instance *prior, Instance *successor) {
        const auto it = replacement_pairs.find(prior);
        return it != replacement_pairs.end() && it->second == successor;
    };
    auto replacement_source = [&](const Instance &instance) {
        return std::any_of(replacement_pairs.begin(), replacement_pairs.end(), [&](const auto &pair) {
            return pair.first == &instance || pair.second == &instance;
        });
    };
    const auto replacement_frames = static_cast<uint32_t>(std::max(1., old.cfg.sample_rate * .020));
    auto same_edge = [](const Edge &a, const Edge &b) {
        return a.key() == b.key() && &a.source->instance == &b.source->instance &&
               &a.destination->instance == &b.destination->instance;
    };
    auto same_bus = [](const Bus &a, const Bus &b) {
        return a.key() == b.key() && &a.source->instance == &b.source->instance;
    };
    std::vector<bool> old_edges_used(old.layout->edges.size()), old_buses_used(old.layout->buses.size());
    for (const auto &authored : fresh.layout->edges) {
        if (authored.removed) continue;
        Edge edge{authored.from, authored.output, authored.to, authored.input, authored.kind, authored.amount};
        edge.source = target_nodes.at(target_instances.at(edge.from));
        edge.destination = target_nodes.at(target_instances.at(edge.to));
        target.edges.push_back(edge);
        edge.source = transition_nodes.at(&edge.source->instance);
        edge.destination = transition_nodes.at(&edge.destination->instance);
        bool matched = false;
        for (size_t i = 0; i < old.layout->edges.size(); ++i) {
            const auto &prior = old.layout->edges[i];
            if (old_edges_used[i] || finished_removal(prior) || !same_edge(edge, prior)) continue;
            old_edges_used[i] = true;
            matched = true;
            edge.ramped = edge.kind != 1 && (prior.removed || (prior.ramped && !settled));
            break;
        }
        if (!matched && edge.kind != 1) {
            // An unchanged signal input feeds both replacement instances at
            // full strength. Only consumer contributions crossfade.
            const bool shared_input = edge.kind == 0 && std::any_of(old.layout->edges.begin(),
                old.layout->edges.end(), [&](const auto &prior) {
                    return !prior.removed && prior.key() == edge.key() &&
                           &prior.source->instance == &edge.source->instance &&
                           replacement_of(&prior.destination->instance, &edge.destination->instance);
                });
            edge.ramped = !shared_input;
        }
        next.edges.push_back(edge);
    }
    for (size_t i = 0; i < old.layout->edges.size(); ++i) {
        const auto &prior = old.layout->edges[i];
        if (old_edges_used[i] || prior.kind == 1 || finished_removal(prior) ||
            !transition_nodes.count(&prior.source->instance) || !transition_nodes.count(&prior.destination->instance))
            continue;
        Edge edge{prior.from, prior.output, prior.to, prior.input, prior.kind, prior.amount};
        edge.source = transition_nodes.at(&prior.source->instance);
        edge.destination = transition_nodes.at(&prior.destination->instance);
        edge.removed = edge.ramped = true;
        edge.replacement_input = prior.replacement_input || (prior.kind == 0 &&
            std::any_of(fresh.layout->edges.begin(), fresh.layout->edges.end(), [&](const auto &authored) {
                return !authored.removed && authored.key() == prior.key() &&
                       target_instances.at(authored.from) == &prior.source->instance &&
                       replacement_of(&prior.destination->instance, target_instances.at(authored.to));
            }));
        next.edges.push_back(edge);
    }
    for (const auto &authored : fresh.layout->buses) {
        if (authored.removed) continue;
        Bus bus{authored.node, authored.port, authored.channel};
        bus.source = target_nodes.at(target_instances.at(bus.node));
        target.buses.push_back(bus);
        bus.source = transition_nodes.at(&bus.source->instance);
        bool matched = false;
        for (size_t i = 0; i < old.layout->buses.size(); ++i) {
            const auto &prior = old.layout->buses[i];
            if (old_buses_used[i] || finished_removal(prior) || !same_bus(bus, prior)) continue;
            old_buses_used[i] = true;
            matched = true;
            bus.ramped = prior.removed || (prior.ramped && !settled);
            break;
        }
        if (!matched) bus.ramped = true;
        next.buses.push_back(bus);
    }
    for (size_t i = 0; i < old.layout->buses.size(); ++i) {
        const auto &prior = old.layout->buses[i];
        if (old_buses_used[i] || finished_removal(prior)) continue;
        Bus bus{prior.node, prior.port, prior.channel};
        bus.source = transition_nodes.at(&prior.source->instance);
        bus.removed = bus.ramped = true;
        next.buses.push_back(bus);
    }
    auto finish = [&](Impl &builder) {
        auto &l = *builder.layout;
        l.taps = fresh.layout->taps;
        l.tap_values = std::make_unique<std::atomic<float>[]>(l.taps.size());
        l.tap_counts = std::make_unique<std::atomic<uint32_t>[]>(l.taps.size());
        for (size_t i = 0; i < l.taps.size(); ++i) {
            l.tap_values[i].store(0, std::memory_order_relaxed);
            l.tap_counts[i].store(0, std::memory_order_relaxed);
        }
        if (!builder.topology() || !builder.resolve_taps()) return false;
        l.feedback_count = builder.feedback_count.load();
        return true;
    };
    if (!finish(staged) || !finish(steady)) return old.fail("Cannot build live layout");
    std::vector<Node *> actual;
    actual.reserve(next.nodes.size());
    for (auto &n : next.nodes) {
        auto prior = std::find_if(old.layout->nodes.begin(), old.layout->nodes.end(),
                                  [&](const auto &node) { return &node->instance == &n->instance; });
        actual.push_back(prior == old.layout->nodes.end() ? n.get() : prior->get());
    }
    std::vector<bool> used(next.edges.size(), false), delay_used(old.layout->edges.size(), false);
    std::vector<std::pair<size_t, size_t>> delays;
    if (!old.plan_edge_transitions(staged, actual, used, delay_used, next.chokes, next.removed_routes, delays))
        return false;

    // Transfer edge-state identity (not DSP samples) on control. Adoption
    // changes the render-owned envelope or authored amount at a block boundary.
    std::fill(old_edges_used.begin(), old_edges_used.end(), false);
    for (auto &edge : next.edges) {
        edge.born_revision = next_revision;
        const Edge *prior = nullptr;
        for (size_t i = 0; i < old.layout->edges.size(); ++i) {
            const auto &candidate_edge = old.layout->edges[i];
            if (old_edges_used[i] || finished_removal(candidate_edge) || !same_edge(edge, candidate_edge)) continue;
            old_edges_used[i] = true;
            prior = &candidate_edge;
            break;
        }
        if (prior) {
            const bool reborn = prior->removed && !edge.removed;
            if (!reborn) {
                edge.born_revision = prior->born_revision;
                edge.sent_serial = prior->sent_serial;
            }
            if (edge.back == prior->back) edge.state = prior->state;
            if (edge.kind == 2)
                next.modulation_adoption.push_back({&edge, prior->state,
                    !edge.removed && (reborn || edge.amount != prior->amount), reborn});
        }
        if (edge.ramped) {
            next.gain_adoption.push_back({edge.state, prior ? prior->state : nullptr,
                edge.removed && !edge.replacement_input ? 0.f : 1.f,
                replacement_source(edge.source->instance) ? replacement_frames : 0});
            next.ramps.push_back(edge.state);
        } else if (prior && edge.state != prior->state)
            next.gain_adoption.push_back({edge.state, prior->state, 1.f});
    }
    std::fill(old_buses_used.begin(), old_buses_used.end(), false);
    for (auto &bus : next.buses) {
        const Bus *prior = nullptr;
        for (size_t i = 0; i < old.layout->buses.size(); ++i) {
            const auto &candidate_bus = old.layout->buses[i];
            if (old_buses_used[i] || finished_removal(candidate_bus) || !same_bus(bus, candidate_bus)) continue;
            old_buses_used[i] = true;
            prior = &candidate_bus;
            break;
        }
        if (prior) bus.state = prior->state;
        if (bus.ramped) {
            next.gain_adoption.push_back({bus.state, prior ? prior->state : nullptr, bus.removed ? 0.f : 1.f,
                replacement_source(bus.source->instance) ? replacement_frames : 0});
            next.ramps.push_back(bus.state);
        }
    }
    std::vector<bool> transition_used(next.edges.size(), false);
    for (auto &edge : target.edges) {
        for (size_t i = 0; i < next.edges.size(); ++i) {
            auto &prior = next.edges[i];
            if (transition_used[i] || prior.removed || !same_edge(edge, prior)) continue;
            transition_used[i] = true;
            edge.born_revision = prior.born_revision;
            edge.sent_serial = prior.sent_serial;
            if (edge.back == prior.back) edge.state = prior.state;
            if (edge.kind == 2 && edge.state != prior.state)
                target.modulation_adoption.push_back({&edge, prior.state, false});
            break;
        }
    }
    std::vector<bool> transition_buses_used(next.buses.size(), false);
    for (auto &bus : target.buses)
        for (size_t i = 0; i < next.buses.size(); ++i) {
            auto &prior = next.buses[i];
            if (transition_buses_used[i] || prior.removed || !same_bus(bus, prior)) continue;
            transition_buses_used[i] = true;
            bus.state = prior.state;
            break;
        }
    // Preallocate retirement storage before the pointer is visible.
    std::vector<std::unique_ptr<Instance>> retired;
    retired.reserve(next.nodes.size());
    for (auto id : introduced) {
        auto &instance = *fresh.instances.at(id);
        // ER4 / A55: only a same-descriptor config replacement inherits birth.
        // find() excludes retired nodes: remove/readd gets a fresh revision.
        const auto *predecessor = old.find(id);
        instance.born_revision = predecessor && predecessor->instance.d == instance.d &&
                                 predecessor->instance.config != instance.config
                                     ? predecessor->instance.born_revision : next_revision;
        for (uint32_t i = 0; i < instance.event_outputs.size(); ++i)
            instance.event_outputs[i] = {sizeof(ws2_event_out), &old, i, Impl::emit};
    }
    if (!old.publish_layout(&next, timeout_ns)) {
        for (auto id : introduced) {
            auto &instance = *fresh.instances.at(id);
            instance.born_revision = 0;
            for (uint32_t i = 0; i < instance.event_outputs.size(); ++i)
                instance.event_outputs[i] = {sizeof(ws2_event_out), &fresh, i, Impl::emit};
        }
        return old.fail("Audio did not adopt before the edit deadline");
    }
    // No render can touch the old topology after acknowledgement.
    for (auto id : retained) old.instances.at(id).swap(fresh.instances.at(id));
    old.instances.swap(fresh.instances);
    auto carry = [&](std::unique_ptr<Instance> &instance) {
        if (instance && transition_nodes.count(instance.get()) &&
            transition_nodes.at(instance.get())->retired) retired.push_back(std::move(instance));
    };
    for (auto &entry : fresh.instances) carry(entry.second);
    for (auto &instance : old.retired_instances) carry(instance);
    old.retired_instances.swap(retired);
    staged.edge_states.merge(steady.edge_states);
    auto transfer = [&](const Layout &l) {
        for (auto &edge : l.edges) {
            auto state = old.edge_states.extract(edge.state);
            if (!state.empty()) staged.edge_states.insert(std::move(state));
        }
        for (auto &bus : l.buses) {
            auto state = old.edge_states.extract(bus.state);
            if (!state.empty()) staged.edge_states.insert(std::move(state));
        }
    };
    transfer(next);
    transfer(target);
    old.layout.swap(staged.layout);
    old.steady_layout = std::move(steady.layout);
    old.last_settle_attempt_position.reset();
    old.edge_states.swap(staged.edge_states);
    old.prune_edge_states();
    old.recompute_latency();
    old.published_revision.store(next_revision, std::memory_order_release);
    old.error.clear();
    return true;
}
} // namespace wirescape::engine2
