// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>

namespace gate_delay {

// Experimental polyphonic gate/CV delay. All queues are fixed-capacity;
// the 1 kHz signal lines come from the host arena in prepare(), never process().
struct GateDelay {
    static constexpr ws::Info info{"essentials.gate_delay", "Gate Delay", 1};
    static constexpr std::array inputs{
        ws::port("in", "In", WS2_CV_BI, WS2_POLY),
        ws::port("cv", "Pitch CV", WS2_PITCH, WS2_POLY),
        ws::port("time_cv", "Time CV", WS2_CV_BI, WS2_FIRST)};
    static constexpr std::array outputs{
        ws::port("out", "Out", WS2_CV_BI, WS2_POLY),
        ws::port("trig", "Trig", WS2_TRIGGER, WS2_POLY),
        ws::port("cv_out", "Pitch CV Out", WS2_PITCH, WS2_POLY)};
    static constexpr uint32_t kStepped = WS2_STEPPED | WS2_AUTOMATABLE;
    static constexpr std::array params{
        ws::param("mode", "Mode", 0, 1, 0, "", kStepped, WS2_LINEAR, 0, 4, 1),
        ws::param("time", "Time", 0, 2000, 250, "ms", WS2_AUTOMATABLE | WS2_MODULATABLE, WS2_LINEAR, 1),
        ws::param("spread", "Spread", 0, 500, 0, "ms", WS2_AUTOMATABLE, WS2_LINEAR, 2),
        ws::param("strum", "Strum", 0, 3, 0, "", kStepped, WS2_LINEAR, 3, 4, 1),
        ws::param("humanize", "Humanize", 0, 50, 0, "ms", WS2_AUTOMATABLE, WS2_LINEAR, 4),
        ws::param("repeats", "Repeats", 0, 4, 0, "", kStepped, WS2_LINEAR, 5, 4, 1)};
    enum Param : uint32_t { kMode, kTime, kSpread, kStrum, kHumanize, kRepeats };
    static constexpr uint32_t kLanes = 16, kQueue = 64, kSignalSlots = 2002;

    struct Edge {
        uint64_t at = 0, order = 0;
        float pitch = 0.f;
        bool on = false;
    };
    struct Lane {
        std::array<Edge, kQueue> queue{};
        uint32_t count = 0, trig_left = 0;
        uint64_t next_order = 0, dropped = 0, rise_delay = 0, repeat_period = 1;
        uint32_t repeat_count = 0;
        float sampled_pitch = 0.f, held_pitch = 0.f;
        bool source_high = false, output_high = false, signal_high = false;
    };
    std::array<Lane, kLanes> lanes{};
    std::array<uint8_t, kLanes> ranks{};
    // Signal line layout: [in lane0..15][pitch lane0..15], 2002 samples per line.
    float *line = nullptr;
    double rate = 48000.;
    uint64_t frame = 0, last_tick = UINT64_MAX;
    uint32_t reset_count = 0, rng = 1, max_channels = kLanes;
    bool alternate_down = false, signal_mode = false;

    static ws2_memory memory_requirements(const ws2_config &) {
        ws2_memory m{};
        m.struct_size = sizeof(m);
        m.alignment = 32;
        m.large_bytes = size_t(2 * kLanes * kSignalSlots) * sizeof(float);
        return m;
    }
    bool prepare(const ws::Setup &s) {
        rate = s.sample_rate();
        max_channels = std::min<uint32_t>(kLanes, s.max_channels());
        line = static_cast<float *>(s.alloc(size_t(2 * kLanes * kSignalSlots) * sizeof(float), 32, WS2_LARGE));
        if (!line) return false;
        reset_count = 0;
        reset();
        return true;
    }
    void reset() {
        lanes = {};
        frame = 0;
        last_tick = UINT64_MAX;
        alternate_down = signal_mode = false;
        ++reset_count;
        rng = 0x6d2b79f5u ^ (0x9e3779b9u * reset_count);
        if (!rng) rng = 1;
        for (uint32_t i = 0; i < kLanes; ++i) ranks[i] = uint8_t(i);
        if (line) std::fill_n(line, size_t(2 * kLanes * kSignalSlots), 0.f);
    }
    uint32_t random() {
        rng ^= rng << 13u;
        rng ^= rng >> 17u;
        rng ^= rng << 5u;
        return rng;
    }
    void chord_begin(uint32_t count, uint32_t strum) {
        if (strum == 2) alternate_down = !alternate_down;
        for (uint32_t i = 0; i < count; ++i) ranks[i] = uint8_t(i);
        if (strum == 3) {
            // One permutation per chord: every lane occurs exactly once.
            for (uint32_t n = count; n > 1; --n) {
                const uint32_t index = random() % n;
                std::swap(ranks[n - 1], ranks[index]);
            }
        } else if (strum == 1 || (strum == 2 && alternate_down)) {
            for (uint32_t i = 0; i < count; ++i) ranks[i] = uint8_t(count - i - 1);
        }
    }
    static bool before(const Edge &a, const Edge &b) {
        if (a.at != b.at) return a.at < b.at;
        if (a.on != b.on) return !a.on; // release before retrigger at equal time
        return a.order < b.order;
    }
    void enqueue(uint32_t channel, uint64_t at, bool on, float pitch) {
        auto &lane = lanes[channel];
        if (lane.count == kQueue) {
            uint32_t oldest = 0;
            for (uint32_t j = 1; j < lane.count; ++j)
                if (lane.queue[j].order < lane.queue[oldest].order) oldest = j;
            for (uint32_t j = oldest + 1; j < lane.count; ++j) lane.queue[j - 1] = lane.queue[j];
            --lane.count;
            ++lane.dropped;
        }
        const Edge edge{at, lane.next_order++, pitch, on};
        uint32_t i = lane.count++;
        while (i && before(edge, lane.queue[i - 1])) {
            lane.queue[i] = lane.queue[i - 1];
            --i;
        }
        lane.queue[i] = edge;
    }
    void due(uint32_t channel, uint64_t now) {
        auto &lane = lanes[channel];
        while (lane.count && lane.queue[0].at <= now) {
            const Edge edge = lane.queue[0];
            for (uint32_t j = 1; j < lane.count; ++j) lane.queue[j - 1] = lane.queue[j];
            --lane.count;
            lane.output_high = edge.on;
            if (edge.on) {
                lane.held_pitch = edge.pitch;
                lane.trig_left = std::max<uint32_t>(1, static_cast<uint32_t>(std::ceil(rate / 1000.)));
            }
        }
    }
    uint64_t samples(double ms) const {
        return static_cast<uint64_t>(std::llround(std::max(0., ms) * rate * .001));
    }
    double gate_delay_ms(ws::Block &b, uint32_t channel, uint32_t sample) {
        const double base = std::clamp(double(b.param(kTime).value(0, sample)) +
                                          1000. * double(b.in(2).value(0, sample)), 0., 2000.);
        const double spread = double(ranks[channel]) * std::clamp(double(b.param(kSpread).value(0, sample)), 0., 500.);
        const double human = std::clamp(double(b.param(kHumanize).value(0, sample)), 0., 50.);
        const double jitter = human ? human * (2. * (double(random()) / 4294967295.) - 1.) : 0.;
        return std::max(0., base + spread + jitter);
    }
    float *slot(uint32_t type, uint32_t channel, uint64_t tick) const {
        return line + (size_t(type) * kLanes + channel) * kSignalSlots + tick % kSignalSlots;
    }
    float interpolated(uint32_t type, uint32_t channel, double target, uint64_t newest) const {
        if (target < 0. || target + double(kSignalSlots - 2) < double(newest)) return 0.f;
        const uint64_t lo = uint64_t(std::floor(target));
        const uint64_t hi = lo + 1;
        const float a = *slot(type, channel, lo);
        if (hi > newest) return a;
        const float b = *slot(type, channel, hi);
        return static_cast<float>(a + (b - a) * (target - double(lo)));
    }
    void sample_signal(ws::Block &b, uint32_t i, uint32_t count, uint64_t tick) {
        if (last_tick == tick) return;
        const uint64_t begin = last_tick == UINT64_MAX ? tick :
                               (tick > last_tick + kSignalSlots ? tick - kSignalSlots + 1 : last_tick + 1);
        for (uint64_t t = begin; t <= tick; ++t) {
            for (uint32_t c = 0; c < count; ++c) {
                *slot(0, c, t) = b.in(0).value(c, i);
                *slot(1, c, t) = b.in(1).value(c, i);
            }
        }
        last_tick = tick;
    }
    void clear_mode() {
        for (auto &v : lanes) {
            v.queue = {};
            v.count = v.trig_left = 0;
            v.source_high = v.output_high = v.signal_high = false;
            v.held_pitch = 0.f;
        }
        last_tick = UINT64_MAX;
        if (line) std::fill_n(line, size_t(2 * kLanes * kSignalSlots), 0.f);
    }
    void process(ws::Block &b) {
        const uint32_t n = std::min<uint32_t>(max_channels,
            std::max<uint32_t>({1u, b.in(0).channels(), b.in(1).channels()}));
        for (uint32_t o = 0; o < 3; ++o) {
            b.out(o).set_channels(n);
            b.out(o).mark_constant(false);
        }
        const bool signal = b.param(kMode).value(0, 0) >= .5f;
        if (signal != signal_mode) {
            signal_mode = signal;
            clear_mode();
        }
        for (uint32_t i = 0; i < b.frames(); ++i, ++frame) {
            if (signal_mode) {
                const double ms = double(frame) * 1000. / rate;
                const uint64_t tick = uint64_t(std::floor(ms));
                sample_signal(b, i, n, tick);
                for (uint32_t c = 0; c < n; ++c) {
                    const double base = std::clamp(
                        double(b.param(kTime).value(0, i)) + 1000. * double(b.in(2).value(0, i)), 0., 2000.);
                    const double d = std::clamp(base + double(c) *
                        std::clamp(double(b.param(kSpread).value(0, i)), 0., 500.), 0., 2000.);
                    const float output = d <= 0. ? b.in(0).value(c, i) : interpolated(0, c, ms - d, tick);
                    const float pitch = d <= 0. ? b.in(1).value(c, i) : interpolated(1, c, ms - d, tick);
                    auto &lane = lanes[c];
                    const bool high = output >= .5f;
                    if (high && !lane.signal_high)
                        lane.trig_left = std::max<uint32_t>(1, uint32_t(std::ceil(rate / 1000.)));
                    lane.signal_high = high;
                    b.out(0).ch(c)[i] = output;
                    b.out(1).ch(c)[i] = lane.trig_left ? 1.f : 0.f;
                    b.out(2).ch(c)[i] = pitch;
                    if (lane.trig_left) --lane.trig_left;
                }
                continue;
            }
            for (uint32_t c = 0; c < n; ++c) {
                auto &lane = lanes[c];
                const bool high = b.in(0).value(c, i) >= .5f;
                if (high != lane.source_high) {
                    if (high) {
                        bool any_high = false;
                        for (uint32_t k = 0; k < n; ++k) any_high |= lanes[k].source_high;
                        if (!any_high) {
                            const auto strum = uint32_t(std::clamp(std::lround(b.param(kStrum).value(0, i)), 0l, 3l));
                            chord_begin(n, strum);
                        }
                        lane.rise_delay = samples(gate_delay_ms(b, c, i));
                        lane.repeat_period = std::max<uint64_t>(1, samples(
                            std::clamp(double(b.param(kTime).value(0, i)), 0., 2000.)));
                        lane.repeat_count = uint32_t(std::clamp(std::lround(
                            b.param(kRepeats).value(0, i)), 0l, 4l));
                        lane.sampled_pitch = b.in(1).value(c, i);
                        for (uint32_t r = 0; r <= lane.repeat_count; ++r)
                            enqueue(c, frame + lane.rise_delay + uint64_t(r) * lane.repeat_period,
                                    true, lane.sampled_pitch);
                    } else {
                        for (uint32_t r = 0; r <= lane.repeat_count; ++r)
                            enqueue(c, frame + lane.rise_delay + uint64_t(r) * lane.repeat_period,
                                    false, lane.sampled_pitch);
                    }
                    lane.source_high = high;
                }
                due(c, frame);
                b.out(0).ch(c)[i] = lane.output_high ? 1.f : 0.f;
                b.out(1).ch(c)[i] = lane.trig_left ? 1.f : 0.f;
                b.out(2).ch(c)[i] = lane.held_pitch;
                if (lane.trig_left) --lane.trig_left;
            }
        }
    }
    int save_state(ws::Writer w) const { return w.u32(1) ? WS2_OK : WS2_CAPACITY; }
    int load_state(ws::Reader r) {
        uint32_t version = 0;
        if (!r.u32(version)) return WS2_INVALID;
        if (version != 1) return WS2_UNSUPPORTED;
        reset();
        return WS2_OK;
    }
};

} // namespace gate_delay
