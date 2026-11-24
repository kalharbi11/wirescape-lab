// SPDX-License-Identifier: GPL-3.0-only
#include "impl.h"
#include "midi_release.h"
#include "wirescape_sdk.h"
#include <cassert>
#include <cstring>
#include <tuple>
#if defined(__SSE2__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace wirescape::engine2 {
namespace {
bool release(const ws2_event &e) { return e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE || midi_release(e); }
bool ordered(const Item &a, const Item &b) {
    return std::make_tuple(a.frame, !a.cleanup, a.order) < std::make_tuple(b.frame, !b.cleanup, b.order);
}
} // namespace

static_assert(std::atomic<float>::is_always_lock_free, "Telemetry floats must be lock-free");

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

void Engine::Impl::apply_host_packet(const Packet &packet) noexcept {
    if (packet.event.type == WS2_PARAM_MOD) {
        auto *edge = render_layout->find_mod_edge(packet.routed_from, packet.routed_output, packet.node, packet.port);
        if (!edge || packet.revision < edge->born_revision) {
            ++stale;
            return;
        }
        auto &state = edge->state->modulation;
        if (packet.order > state.applied_serial) {
            state.applied_serial = packet.order;
            state.set(packet.event.value, mod_ramp_frames());
            edge->destination->instance.latency_dirty = true;
        }
        return;
    }
    if (packet.node || packet.event.type != WS2_TRANSPORT_EVENT) {
        ++stale;
        return;
    }
    TransportUpdate update{};
    std::memcpy(&update, packet.payload.data(), sizeof(update));
    update.apply(packet.order, transport_applied, cfg, beat);
}

void Engine::Impl::collect() {
    for (auto &n : render_layout->nodes) n->instance.pending.clear();
    Packet p;
    const uint64_t gen = generation.load(std::memory_order_acquire);
    for (auto target : render_layout->chokes) {
        ws2_event e{};
        e.struct_size = sizeof(e);
        e.type = WS2_NOTE_CHOKE;
        e.source_id = UINT32_MAX;
        e.note_id = -1;
        e.channel = -1;
        e.flags = 1;
        if (auto *n = render_layout->find(target.first)) admit(*n, target.second, e, block_start, 0, true);
        else ++stale;
    }
    render_layout->chokes.clear();
    for (uint32_t producer = 0; producer < producer_count; ++producer) {
        auto &source = *producers[producer];
        for (Ring *ring : {&source.critical, &source.normal}) {
            // Snapshot-like bounded drain. A busy producer cannot extend this indefinitely.
            uint64_t blocked = 0;
            for (uint32_t work = 0; work < cfg.ring_capacity &&
                 ring->pop_adopted(p, render_layout->revision, blocked); ++work) {
                if (p.host) {
                    apply_host_packet(p);
                    continue;
                }
                if (p.generation != gen) {
                    ++stale;
                    continue;
                }
                auto *target = render_layout->find(p.node);
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
            if (blocked && blocked > published_revision.load(std::memory_order_acquire)) {
                ++faults;
                assert(false && "Producer stamped an unpublished revision");
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
        Node *n = render_layout->find(packet.node);
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
        source.type == WS2_TRANSPORT_EVENT || !ws::valid_event(source))
        return false;
    if (processing->retired) return true; // Retired sources deliver only their fading signal output.
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
            p.revision = render_layout->revision;
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


// Keep the extracted stages in the same hot path as process_node.
#if defined(_MSC_VER)
#define WS_RENDER_INLINE __forceinline
#else
#define WS_RENDER_INLINE inline __attribute__((always_inline))
#endif

WS_RENDER_INLINE void Engine::Impl::gather_events(Instance &instance, uint32_t start, uint32_t frames) {
    instance.events.clear();
    for (auto &v : instance.port_events) v.clear();
    std::sort(instance.pending.begin(), instance.pending.end(), ordered);
    for (const auto &item : instance.pending)
        if (item.frame >= block_start + start && item.frame < block_start + start + frames) {
            auto event = item.event;
            event.offset = static_cast<uint32_t>(item.frame - block_start - start);
            instance.events.push_back(event);
            if (event.port < instance.port_events.size()) instance.port_events[event.port].push_back(event);
        }
}

WS_RENDER_INLINE uint32_t Engine::Impl::edge_channels(const Edge &e, uint32_t frames) const {
    if (e.ramped && e.state->gain.silent()) return 0;
    if (!e.back) return e.source->instance.global_out[e.output].channels;
    uint32_t count = 0;
    for (uint32_t i = 0; i < frames; ++i)
        count = std::max(count, e.state->delay_channels[(e.state->head + i) % cfg.feedback_block]);
    return count;
}

WS_RENDER_INLINE float Engine::Impl::edge_sample(const Edge &e, uint32_t channel, uint32_t i, uint32_t start) const {
    if (e.back) {
        auto pos = (e.state->head + i) % cfg.feedback_block;
        auto count = e.state->delay_channels[pos];
        if (count == 1) channel = 0;
        return channel < count ? e.state->delay.data[channel][pos] : 0.f;
    }
    const auto &buffer = e.source->instance.global_out[e.output];
    if (buffer.channels == 1) channel = 0;
    return channel < buffer.channels ? buffer.data[channel][(buffer.flags & WS2_CONSTANT) ? 0 : start + i] : 0.f;
}

WS_RENDER_INLINE uint32_t Engine::Impl::resolve_channels(Instance &instance, const Slot &slot, uint32_t frames) const {
    uint32_t channels = instance.forced_channels > 0 ? static_cast<uint32_t>(instance.forced_channels) : 1;
    for (const auto *edge : slot.signal_edges) {
        const auto &e = *edge;
        if (e.kind == 2 ? (instance.parameters[e.input].flags & WS2_PER_VOICE) != 0
                        : instance.inputs[e.input].poly == WS2_POLY)
            channels = std::max(channels, edge_channels(e, frames));
    }
    channels = std::min(channels, cfg.max_channels);
    instance.channels = channels;
    return channels;
}

WS_RENDER_INLINE void Engine::Impl::gather_inputs(Instance &instance, Slot &slot, uint32_t start, uint32_t frames,
                                               uint32_t channels, bool direct) {
    for (uint32_t j = 0; j < instance.inputs.size(); ++j) {
        const auto &port = instance.inputs[j];
        auto &buffer = slot.in[j];
        if (!slot.transition_inputs.empty() && !slot.transition_inputs[j].empty()) {
            // A removed and an added cable may share a destination port during
            // the fade. Blend relative to the port's unpatched value.
            buffer.channels = port.poly == WS2_POLY ? channels : 1;
            bool connected = false;
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                buffer.read[c] = buffer.data[c];
                std::fill_n(buffer.data[c], frames, port.unpatched_value);
            }
            for (const auto *edge : slot.transition_inputs[j]) {
                const auto count = edge_channels(*edge, frames);
                if (!count) continue;
                connected = true;
                for (uint32_t c = 0; c < buffer.channels; ++c)
                    for (uint32_t i = 0; i < frames; ++i) {
                        float sample = 0;
                        if (port.poly == WS2_SUM)
                            for (uint32_t k = 0; k < count; ++k) sample += edge_sample(*edge, k, i, start);
                        else sample = edge_sample(*edge, port.poly == WS2_FIRST ? 0 : c, i, start);
                        const float gain = edge->ramped ? edge->state->gain.at(start + i) : 1.f;
                        buffer.data[c][i] += gain * (sample - port.unpatched_value);
                    }
            }
            buffer.flags = connected ? WS2_CONNECTED : 0;
            slot.in_view[j] = {sizeof(ws2_signal), buffer.read.data(), buffer.channels, buffer.flags};
            instance.event_view[j] = {sizeof(ws2_event_list), static_cast<uint32_t>(instance.port_events[j].size()),
                                      instance.port_events[j].data()};
            continue;
        }
        const Edge *source = nullptr;
        if (port.kind == WS2_SIGNAL) source = slot.incoming[j];
        uint32_t source_channels = source ? edge_channels(*source, frames) : 0;
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
                            for (uint32_t k = 0; k < source_channels; ++k) sample += edge_sample(*source, k, i, start);
                        } else sample = edge_sample(*source, port.poly == WS2_FIRST ? 0 : c, i, start);
                    }
                    buffer.data[c][i] = sample;
                }
        slot.in_view[j] = {sizeof(ws2_signal), buffer.read.data(), buffer.channels, buffer.flags};
        instance.event_view[j] = {sizeof(ws2_event_list), static_cast<uint32_t>(instance.port_events[j].size()),
                                    instance.port_events[j].data()};
    }
}

WS_RENDER_INLINE void Engine::Impl::apply_parameters(Instance &instance, Slot &slot, uint32_t start, uint32_t frames,
                                                   uint32_t channels) {
    for (uint32_t j = 0; j < instance.parameters.size(); ++j) {
        auto &p = instance.state[j];
        auto &buffer = instance.param[j];
        bool poly = false, constant = p.base.constant();
        for (uint32_t c = 1; c < channels; ++c) poly |= p.offset[c] != p.offset[0];
        for (const auto *edge : slot.modulation[j]) {
            const auto &e = *edge;
            poly |= edge_channels(e, frames) > 1;
            constant &= !e.ramped && !e.state->modulation.remaining && !e.back &&
                        (e.source->instance.global_out[e.output].flags & WS2_CONSTANT);
        }
        for (const auto &e : instance.events)
            if ((e.type == WS2_PARAM || e.type == WS2_PARAM_MOD) && e.index == j) {
                constant = false;
                if (e.type == WS2_PARAM_MOD && e.channel >= 0) poly = true;
            }
        buffer.channels = (poly && (p.info.flags & WS2_PER_VOICE)) ? channels : 1;
        buffer.flags = constant ? WS2_CONSTANT : 0;
        uint32_t cursor = 0;
        const uint32_t length = constant ? 1 : frames;
        const bool modulated = !slot.modulation[j].empty();
        if (modulated)
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                double *sum = instance.modulation_sum.data() + size_t(c) * cfg.max_block;
                std::fill_n(sum, length, 0.);
                for (auto *edge : slot.modulation[j]) {
                    auto &state = edge->state->modulation;
                    if (edge->ramped) {
                        if (edge->state->gain.silent()) continue;
                        auto ramp = state;
                        const auto duration = mod_ramp_frames();
                        for (uint32_t i = 0; i < length; ++i) {
                            const float amount = ramp.remaining ? ramp.next(duration) : ramp.current;
                            sum[i] += (amount * edge->state->gain.at(start + i)) * edge_sample(*edge, c, i, start);
                        }
                        if (c + 1 == buffer.channels) state = ramp;
                    } else if (!state.remaining) {
                        const float amount = state.current;
                        for (uint32_t i = 0; i < length; ++i) sum[i] += amount * edge_sample(*edge, c, i, start);
                    } else {
                        auto ramp = state;
                        const uint32_t duration = mod_ramp_frames();
                        const uint32_t ramp_length = std::min(length, ramp.remaining);
                        for (uint32_t i = 0; i < ramp_length; ++i)
                            sum[i] += ramp.next(duration) * edge_sample(*edge, c, i, start);
                        for (uint32_t i = ramp_length; i < length; ++i)
                            sum[i] += ramp.current * edge_sample(*edge, c, i, start);
                        if (c + 1 == buffer.channels) state = ramp;
                    }
                }
            }
        bool actually_constant = true;
        for (uint32_t i = 0; i < length; ++i) {
            while (cursor < instance.events.size() && instance.events[cursor].offset <= i) {
                const auto &e = instance.events[cursor++];
                if (e.index == j && e.type == WS2_PARAM) {
                    instance.latency_dirty = true;
                    double target = ws::to_normal(p.info, e.value);
                    if (p.info.flags & WS2_STEPPED) p.base.jump(target);
                    else p.base.set(target);
                    p.requested = true;
                }
                if (e.index == j && e.type == WS2_PARAM_MOD) {
                    instance.latency_dirty = true;
                    if (e.channel < 0) p.offset.fill(e.value);
                    else if (static_cast<uint32_t>(e.channel) < cfg.max_channels) p.offset[e.channel] = e.value;
                }
            }
            const double base = p.base.next();
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                double effective = base + p.offset[c];
                if (modulated) effective += instance.modulation_sum[size_t(c) * cfg.max_block + i];
                buffer.data[c][i] = static_cast<float>(p.plain(effective));
                if (i && buffer.data[c][i] != buffer.data[c][0]) actually_constant = false;
            }
        }
        if (actually_constant) buffer.flags |= WS2_CONSTANT;
        slot.param_view[j] = {sizeof(ws2_signal), buffer.read.data(), buffer.channels, buffer.flags};
    }
}

WS_RENDER_INLINE void Engine::Impl::call_module(Node &node, uint32_t start, uint32_t frames,
                                             uint32_t channels, bool direct) {
    auto &instance = node.instance;
    auto &slot = node.slot;
    for (uint32_t j = 0; j < instance.outputs.size(); ++j)
        instance.out_view[j] = {sizeof(ws2_signal_out),
                                  (direct ? instance.global_out[j] : instance.local_out[j]).data.data(), channels,
                                  0, cfg.max_channels};
    processing = &node;
    processing_start = start;
    processing_frames = frames;
    if (instance.forced_channels == 0) {
        for (auto &o : instance.out_view) {
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
            static_cast<uint32_t>(instance.inputs.size()),
            static_cast<uint32_t>(instance.outputs.size()),
            static_cast<uint32_t>(instance.parameters.size()),
            slot.in_view.data(),
            instance.out_view.data(),
            slot.param_view.data(),
            instance.event_view.data(),
            instance.event_outputs.data(),
            {sizeof(ws2_event_list), static_cast<uint32_t>(instance.events.size()), instance.events.data()},
            &transport};
        if (instance.d->process(instance.instance, &context) != WS2_OK) {
            ++faults;
            for (auto &o : instance.out_view) {
                o.channels = channels;
                o.flags = WS2_CONSTANT;
                for (uint32_t c = 0; c < channels; ++c) o.data[c][0] = 0;
            }
        }
    }
    processing = nullptr;
}

WS_RENDER_INLINE void Engine::Impl::publish_outputs(Instance &instance, Slot &slot, uint32_t start, uint32_t frames, bool direct) {
    for (uint32_t j = 0; j < instance.outputs.size(); ++j) {
        auto &o = instance.out_view[j];
        auto &global = instance.global_out[j];
        if (direct) {
            global.channels = o.channels;
            global.flags = o.flags;
            continue;
        }
        if (!slot.touched) {
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
    slot.touched = true;
}

WS_RENDER_INLINE void Engine::Impl::observe_pitch(Instance &instance, const Slot &slot, uint32_t start, uint32_t frames) {
    if (slot.pitch.enabled && frames && instance.channels) {
        // A typed coordinate avoids accidentally swapping three similar indices.
        struct SignalIndex {
            uint32_t input, channel, sample;
        };
        // For direct edges, the read pointer aliases a whole-block source buffer.
        auto signal = [&](SignalIndex at) {
            const auto &buffer = slot.in[at.input];
            const uint32_t channel = std::min(at.channel, buffer.channels - 1);
            const uint32_t sample =
                (buffer.flags & WS2_CONSTANT)
                    ? 0u
                    : (buffer.read[channel] == buffer.data[channel] ? at.sample : start + at.sample);
            return buffer.read[channel][sample];
        };
        auto parameter = [&](uint32_t index, uint32_t channel) {
            const auto &buffer = instance.param[index];
            const uint32_t ch = std::min(channel, buffer.channels - 1);
            return buffer.data[ch][(buffer.flags & WS2_CONSTANT) ? 0u : frames - 1];
        };
        if (slot.pitch.vco) {
            for (const auto &event : instance.events) {
                const uint32_t channel = event.channel < 0 ? 0u : static_cast<uint32_t>(event.channel);
                if (channel >= instance.channels) continue;
                if (event.type == WS2_NOTE_ON) {
                    instance.pitch.note[channel] = event.key;
                    instance.pitch.note_on[channel] = true;
                    instance.pitch.latest = channel;
                } else if (event.type == WS2_NOTE_CHOKE) {
                    instance.pitch.note_on[channel] = false;
                }
            }
        } else {
            // Plaits renders at most eight voices in 12-frame blocks; scan strikes and held gates.
            for (uint32_t i = 0; i < frames; ++i) {
                for (uint32_t channel = 0; channel < std::min(instance.channels, 8u); ++channel) {
                    const bool high = std::max(signal({slot.pitch.trigger, channel, i}),
                                               signal({slot.pitch.gate, channel, i})) > 0.5f;
                    if (high && !instance.pitch.high[channel]) instance.pitch.latest = channel;
                    instance.pitch.high[channel] = high;
                }
            }
        }
        const uint32_t channel = std::min(instance.pitch.latest, instance.channels - 1);
        if (slot.pitch.vco) {
            const float tune = parameter(slot.pitch.tune, channel);
            double hz = tune;
            if (slot.in[slot.pitch.input].flags & WS2_CONNECTED) {
                hz = 261.6255653005986 * std::pow(2., signal({slot.pitch.input, channel, frames - 1})) *
                     (tune / 220.);
            } else if (instance.pitch.note_on[channel]) {
                hz = 440. * std::pow(2., (instance.pitch.note[channel] - 69.) / 12.);
            }
            // VCO tap stores Hz; the control owner converts to equal-tempered MIDI.
            instance.pitch.value = std::numeric_limits<float>::quiet_NaN();
            if (std::isfinite(hz) && hz > 0) instance.pitch.value = static_cast<float>(hz);
        } else {
            // Macro tap stores nominal MIDI note. FM and Plaits internal FM excluded.
            instance.pitch.value =
                60.f + parameter(slot.pitch.tune, channel) +
                std::clamp(12.f * signal({slot.pitch.input, channel, frames - 1}), -96.f, 96.f);
        }
    }
}

void Engine::Impl::process_node(Node &n, uint32_t start, uint32_t frames) {
    const bool direct = !n.slot.loop;
    gather_events(n.instance, start, frames);
    const uint32_t channels = resolve_channels(n.instance, n.slot, frames);
    gather_inputs(n.instance, n.slot, start, frames, channels, direct);
    apply_parameters(n.instance, n.slot, start, frames, channels);
    call_module(n, start, frames, channels, direct);
    publish_outputs(n.instance, n.slot, start, frames, direct);
    observe_pitch(n.instance, n.slot, start, frames);
    if (n.instance.latency_dirty && start + frames == block_frames) {
        n.instance.latency.store(n.instance.d->latency_frames(n.instance.instance), std::memory_order_relaxed);
        n.instance.latency_dirty = false;
    }
}

WS_RENDER_INLINE void Engine::Impl::publish_block_outputs(float *const *outputs, uint32_t output_channels, uint32_t frames) {
    for (uint32_t c = 0; c < output_channels; ++c) std::fill_n(outputs[c], frames, 0.f);
    bool bus_written[32]{};
    for (auto &bus : render_layout->buses)
        if (bus.channel < output_channels) {
            const auto &buffer = bus.source->instance.global_out[bus.port];
            for (uint32_t c = 0; c < buffer.channels; ++c) {
                if (!bus.ramped) {
                    // No-edit path: no gain arithmetic or branch per sample.
                    for (uint32_t i = 0; i < frames; ++i) {
                        const float sample = buffer.data[c][(buffer.flags & WS2_CONSTANT) ? 0 : i];
                        if (!bus_written[bus.channel]) outputs[bus.channel][i] = sample;
                        else outputs[bus.channel][i] += sample;
                    }
                } else {
                    for (uint32_t i = 0; i < frames; ++i) {
                        const float sample = buffer.data[c][(buffer.flags & WS2_CONSTANT) ? 0 : i] * bus.state->gain.at(i);
                        if (!bus_written[bus.channel]) outputs[bus.channel][i] = sample;
                        else outputs[bus.channel][i] += sample;
                    }
                }
                bus_written[bus.channel] = true;
            }
        }
    if (!render_layout->taps.empty()) {
        // Render-owned, post-DSP snapshots. Feedback loops process in chunks, so
        // their parameter buffer's last chunk is shorter than the full block.
        tap_sequence.fetch_add(1, std::memory_order_acq_rel);
        for (size_t i = 0; i < render_layout->taps.size(); ++i) {
            const auto &t = render_layout->taps[i];
            const auto *n = render_layout->tap_nodes[i];
            float sample = 0;
            if (t.kind == Tap::Param) {
                const auto &b = n->instance.param[t.index];
                const uint32_t last = n->slot.loop ? (frames - 1) % cfg.feedback_block : frames - 1;
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
            render_layout->tap_values[i].store(sample, std::memory_order_relaxed);
        }
        tap_frame.store(block_start + frames, std::memory_order_relaxed);
        tap_sequence.fetch_add(1, std::memory_order_release);
    }
}

WS_RENDER_INLINE void Engine::Impl::apply_pending_reset() {
    if (generation.load() != applied.load()) {
        reset_processors();
        applied.store(generation.load(), std::memory_order_release);
    }
}

#undef WS_RENDER_INLINE

void Engine::Impl::adopt_layout(Layout *next) noexcept {
    // All adoption work uses preallocated storage. The old layout is not
    // accessed after the acknowledgement; the control owner may retire it.
    if (!next->housekeeping) future.erase(std::remove_if(future.begin(), future.end(), [&](const Packet &p) {
        const std::array<uint32_t, 4> route{p.routed_from, p.routed_output, p.node, p.port};
        if (!p.routed_from || !std::binary_search(next->removed_routes.begin(), next->removed_routes.end(), route))
            return false;
        ++stale;
        return true;
    }), future.end());
    for (const auto &update : next->modulation_adoption) {
        auto &edge = *update.edge;
        if (edge.state != update.prior) edge.state->modulation = update.prior->modulation;
        if (update.reborn) edge.state->modulation.applied_serial = 0;
        if (update.authored) {
            edge.state->modulation.applied_serial = edge.sent_serial;
            edge.state->modulation.set(edge.amount, mod_ramp_frames());
        }
    }
    for (const auto &update : next->gain_adoption) {
        auto &gain = update.state->gain;
        if (!update.prior) gain.jump(0);
        else if (update.prior != update.state) gain = update.prior->gain;
        gain.set(update.target, mod_ramp_frames());
        update.state->faded_out.store(gain.silent(), std::memory_order_release);
    }
    for (auto &node : next->nodes) {
        auto &instance = node->instance;
        instance.latency.store(instance.d->latency_frames(instance.instance), std::memory_order_relaxed);
    }
    if (next->housekeeping) {
        for (size_t i = 0; i < next->taps.size(); ++i) {
            next->tap_values[i].store(render_layout->tap_values[i].load(std::memory_order_relaxed), std::memory_order_relaxed);
            next->tap_counts[i].store(render_layout->tap_counts[i].load(std::memory_order_relaxed), std::memory_order_relaxed);
        }
    } else {
        tap_sequence.store(0, std::memory_order_relaxed);
        tap_frame.store(0, std::memory_order_release);
    }
    feedback_count.store(next->feedback_count, std::memory_order_relaxed);
    setup_bytes.store(next->setup_bytes, std::memory_order_relaxed);
    render_layout = next;
    if (next->ramps.empty()) settled_revision.store(next->revision, std::memory_order_release);
    adopted_revision.store(next->revision, std::memory_order_release);
}

uint32_t Engine::read_telemetry(float *values, uint32_t *counts, uint32_t capacity, uint64_t &frame) const noexcept {
    const auto &p = *p_;
    frame = 0;
    if (capacity < p.layout->taps.size() || (!p.layout->taps.empty() && (!values || !counts))) return 0;
    // A bounded non-render read must not combine two blocks (in particular
    // Groove's split uint32 loop and release-safe position observations).
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        const auto before = p.tap_sequence.load(std::memory_order_acquire);
        if (before & 1u) continue;
        const auto observed = p.tap_frame.load(std::memory_order_relaxed);
        for (size_t i = 0; i < p.layout->taps.size(); ++i) {
            values[i] = p.layout->tap_values[i].load(std::memory_order_relaxed);
            counts[i] = p.layout->tap_counts[i].load(std::memory_order_relaxed);
        }
        std::atomic_thread_fence(std::memory_order_acquire);
        if (before == p.tap_sequence.load(std::memory_order_relaxed)) {
            frame = observed;
            return static_cast<uint32_t>(p.layout->taps.size());
        }
    }
    return static_cast<uint32_t>(p.layout->taps.size()); // frame=0: unavailable, never a torn snapshot.
}

int Engine::enqueue(uint32_t producer, uint32_t node, uint32_t port, const ws2_event &event, uint64_t time, Timing mode,
                    uint64_t wanted_generation) noexcept {
    auto &p = *p_;
    if (!p.prepared || producer >= p.producer_count) return WS2_STATE;
    const auto gen = p.generation.load(std::memory_order_acquire);
    if (gen != p.applied.load(std::memory_order_acquire) || (wanted_generation && wanted_generation != gen))
        return WS2_STATE;
    if (event.type == WS2_TRANSPORT_EVENT || !ws::valid_event(event)) return WS2_INVALID;
    auto &source = *p.producers[producer];
    Packet packet;
    packet.node = node;
    packet.port = port;
    packet.when = time;
    packet.mode = mode;
    packet.generation = gen;
    packet.revision = p.published_revision.load(std::memory_order_acquire);
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
    if (p.reset_beat) {
        p.beat = 0;
        p.reset_beat = false;
    }
    if (callback_time_ns != UINT64_MAX) publish_clock(p.block_start, callback_time_ns);
    if (auto *next = p.pending_layout.exchange(nullptr, std::memory_order_acq_rel))
        p.adopt_layout(next);
    p.apply_pending_reset();
    p.arena_used.store(0);
    p.ordinary_used = p.critical_used = 0;
    for (auto &n : p.render_layout->nodes) n->slot.touched = false;
    p.collect();
    p.apply_pending_reset();
    for (auto &component : p.render_layout->components) {
        uint32_t chunk = component.loop ? p.cfg.feedback_block : frames;
        for (uint32_t start = 0; start < frames; start += chunk) {
            uint32_t length = std::min(chunk, frames - start);
            for (auto *n : component.nodes) p.process_node(*n, start, length);
            if (component.loop)
                for (auto &e : p.render_layout->edges)
                    if (e.back && e.kind != 1 && e.source->slot.component == component.nodes.front()->slot.component) {
                        auto &source = e.source->instance.global_out[e.output];
                        for (uint32_t i = 0; i < length; ++i) {
                            auto at = (e.state->head + i) % p.cfg.feedback_block;
                            e.state->delay_channels[at] = source.channels;
                            for (uint32_t c = 0; c < p.cfg.max_channels; ++c)
                                e.state->delay.data[c][at] = c < source.channels ? source.data[c][start + i] : 0;
                        }
                        e.state->head = (e.state->head + length) % p.cfg.feedback_block;
                    }
        }
    }
    p.publish_block_outputs(outputs, output_channels, frames);
    if (!p.render_layout->ramps.empty() &&
        p.settled_revision.load(std::memory_order_relaxed) < p.render_layout->revision) {
        bool settled = true;
        for (auto *state : p.render_layout->ramps) {
            const bool done = state->gain.advance(frames);
            settled &= done;
            if (done && state->gain.silent()) state->faded_out.store(true, std::memory_order_release);
        }
        if (settled) p.settled_revision.store(p.render_layout->revision, std::memory_order_release);
    }
    if (p.cfg.playing) p.beat += frames * p.cfg.bpm / (60. * p.cfg.sample_rate);
    p.position.store(p.block_start + frames, std::memory_order_release);
    p.apply_pending_reset();
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

Meter Engine::meter() const noexcept {
    auto &p = *p_;
    return {p.position.load(),   p.generation.load(),  p.applied.load(),    p.event_count.load(),
            p.dropped.load(),    p.coalesced.load(),   p.ring_full.load(),  p.stale.load(),
            p.late.load(),       p.emergencies.load(), p.arena_full.load(), p.faults.load(),
            p.arena_used.load(), p.feedback_count,     p.latency,           p.setup_bytes};
}

} // namespace wirescape::engine2
