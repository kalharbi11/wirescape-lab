// SPDX-License-Identifier: GPL-3.0-only
// Internal engine value types (proposal 0007).
#pragma once
#include "engine2.h"
#include "wirescape_sdk.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <memory>
#include <new>
#include <tuple>
#include <vector>

namespace wirescape::engine2 {
struct Node;
struct AlignedDelete {
    void operator()(float *p) const { ::operator delete[](p, std::align_val_t(32)); }
};
struct Buffer {
    std::unique_ptr<float[], AlignedDelete> memory;
    std::array<float *, WS2_MAX_CHANNELS> data{};
    std::array<const float *, WS2_MAX_CHANNELS> read{};
    uint32_t channels = 1, flags = WS2_CONSTANT, stride = 0;
    void prepare(uint32_t count, uint32_t frames) {
        stride = (frames + 7u) & ~7u;
        memory.reset(static_cast<float *>(::operator new[](sizeof(float) * count * stride, std::align_val_t(32))));
        std::fill_n(memory.get(), count * stride, 0.f);
        for (uint32_t c = 0; c < count; ++c) {
            data[c] = memory.get() + c * stride;
            read[c] = data[c];
        }
    }
};
struct Packet {
    uint32_t node = 0, port = WS2_DIRECT_PORT;
    bool host = false;
    Timing mode = Timing::Frames;
    uint32_t routed_from = 0, routed_output = 0; // Zero source denotes external ingress.
    uint64_t when = 0, generation = 1, order = 0, mapped_time_ns = 0, revision = 0;
    ws2_event event{};
    std::array<uint8_t, WS2_MAX_PAYLOAD> payload{};
    void fix() { event.data = event.bytes ? payload.data() : nullptr; }
};
// Host-only payload, copied into Packet storage at ingress. Transport is the
// engine-wide target, so it has a serial but no instance birth revision.
struct TransportUpdate {
    double bpm, beat;
    bool playing, locate;

    void apply(uint64_t serial, uint64_t &last, Config &cfg, double &current_beat) const noexcept {
        if (serial <= last) return;
        set_values(cfg, current_beat);
        last = serial;
    }
    void set_values(Config &cfg, double &current_beat) const noexcept {
        cfg.bpm = bpm;
        cfg.playing = playing;
        if (locate) current_beat = beat;
    }
};
static_assert(sizeof(TransportUpdate) <= WS2_MAX_PAYLOAD);

// One producer/one consumer per ring. The registry never changes while running.
struct Ring {
    std::vector<Packet> slots;
    std::atomic<uint32_t> head{0}, tail{0};
    explicit Ring(uint32_t capacity) : slots(capacity + 1) {}
    bool push(const Packet &p) noexcept {
        auto h = head.load(std::memory_order_relaxed), next = (h + 1) % static_cast<uint32_t>(slots.size());
        if (next == tail.load(std::memory_order_acquire)) return false;
        slots[h] = p;
        slots[h].fix();
        head.store(next, std::memory_order_release);
        return true;
    }
    bool pop(Packet &p) noexcept {
        auto t = tail.load(std::memory_order_relaxed);
        if (t == head.load(std::memory_order_acquire)) return false;
        p = slots[t];
        p.fix();
        tail.store((t + 1) % static_cast<uint32_t>(slots.size()), std::memory_order_release);
        return true;
    }
    // ER3: inspect only the revision before consuming a packet; no extra
    // payload copy and no advancement of a future-revision ring head.
    bool pop_adopted(Packet &p, uint64_t adopted, uint64_t &blocked) noexcept {
        auto t = tail.load(std::memory_order_relaxed);
        if (t == head.load(std::memory_order_acquire)) return false;
        if (slots[t].revision > adopted) {
            blocked = slots[t].revision;
            return false;
        }
        p = slots[t];
        p.fix();
        tail.store((t + 1) % static_cast<uint32_t>(slots.size()), std::memory_order_release);
        return true;
    }
    bool peek(Packet &p) const noexcept {
        auto t = tail.load(std::memory_order_relaxed);
        if (t == head.load(std::memory_order_acquire)) return false;
        p = slots[t];
        p.fix();
        return true;
    }
    void clear() noexcept { tail.store(head.load(std::memory_order_acquire), std::memory_order_release); }
};
struct Producer {
    Ring normal, critical;
    uint64_t serial = 0;
    explicit Producer(uint32_t capacity) : normal(capacity), critical(capacity) {}
};
struct Item {
    ws2_event event{};
    uint64_t frame = 0, order = 0;
    bool cleanup = false;
};
struct Parameter {
    ws2_param info{};
    ws::LinearRamp base;
    std::array<float, WS2_MAX_CHANNELS> offset{};
    bool requested = false;
    double log_min = 0, log_ratio = 0, exp_curve = 0;
    explicit Parameter(ws2_param p) : info(p), base(ws::to_normal(p, p.initial)) {
        if (p.taper == WS2_LOG) {
            log_min = std::log(static_cast<double>(p.minimum));
            log_ratio = std::log(static_cast<double>(p.maximum) / p.minimum);
        }
        if (p.taper == WS2_EXP) exp_curve = std::expm1(static_cast<double>(p.curve));
    }
    double plain(double x) const noexcept {
        const auto &p = info;
        x = std::clamp(x, 0., 1.);
        double y = x;
        if (p.taper == WS2_LOG) y = std::exp(log_min + x * log_ratio);
        if (p.taper == WS2_EXP && std::abs(p.curve) > 1.e-8) y = std::expm1(p.curve * x) / exp_curve;
        double value = p.taper == WS2_LOG ? y : p.minimum + (p.maximum - p.minimum) * y;
        if (p.step > 0) value = p.minimum + std::round((value - p.minimum) / p.step) * p.step;
        return std::clamp(value, static_cast<double>(p.minimum), static_cast<double>(p.maximum));
    }
};
struct ModAmount {
    float current = 0, target = 0;
    double start = 0;
    uint32_t remaining = 0;
    uint64_t applied_serial = 0;

    void set(float value, uint32_t duration) noexcept {
        if (value == target) return;
        target = value;
        start = current;
        remaining = current == target ? 0 : duration;
    }

    float next(uint32_t duration) noexcept {
        const double fraction = double(duration - --remaining) / duration;
        current = remaining ? float(start + (target - start) * fraction) : target;
        return current;
    }
};
// Render-owned linear edge envelope. Sample zero advances one frame; a
// retarget begins from the actual last sample, not the prior authored target.
struct EdgeGain {
    float start = 1, target = 1;
    uint32_t length = 0, position = 0;
    float current() const noexcept {
        return position >= length ? target : float(start + (target - start) * (double(position) / length));
    }
    float at(uint32_t offset) const noexcept {
        const auto n = std::min<uint64_t>(length, uint64_t(position) + offset + 1);
        return n >= length ? target : float(start + (target - start) * (double(n) / length));
    }
    void jump(float value) noexcept { start = target = value; length = position = 0; }
    void set(float value, uint32_t frames) noexcept {
        if (value == target) return;
        const float now = current();
        start = now;
        target = value;
        length = now == value ? 0 : frames;
        position = 0;
    }
    bool advance(uint32_t frames) noexcept {
        position = static_cast<uint32_t>(std::min<uint64_t>(length, uint64_t(position) + frames));
        return position == length;
    }
    bool silent() const noexcept { return target == 0 && position == length; }
};
struct EdgeState {
    ModAmount modulation;
    EdgeGain gain;
    // Render publishes retirement completion; control never reads gain fields.
    std::atomic<bool> faded_out{false};
    Buffer delay;
    std::vector<uint32_t> delay_channels;
    uint32_t head = 0;
};
struct Edge {
    uint32_t from, output, to, input;
    int kind;
    float amount; // Authored target, control-owned after prepare.
    EdgeState *state = nullptr; // Control-owned, stable across adopted layouts.
    uint64_t born_revision = 0;
    uint64_t sent_serial = 0; // Control-owned.
    auto key() const noexcept { return std::tie(from, output, to, input, kind); }
    Node *source = nullptr, *destination = nullptr;
    bool back = false, removed = false, ramped = false;
    bool replacement_input = false; // Keep a retired replacement's unchanged signal input live.
};
struct Component {
    std::vector<Node *> nodes;
    bool loop = false;
};
struct Bus {
    uint32_t node, port, channel;
    Node *source = nullptr;
    EdgeState *state = nullptr;
    bool removed = false, ramped = false;
    auto key() const noexcept { return std::tie(node, port, channel); }
};
} // namespace wirescape::engine2
