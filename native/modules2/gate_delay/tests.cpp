// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include "../../sdk/examples/test_support.h"
#include "../../tests2/allocation_watch.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <memory>
#include <vector>

using gate_delay::GateDelay;

struct Arena {
    alignas(64) std::array<uint8_t, 400000> bytes{};
    size_t used = 0;
    static void *WS2_CALL allocate(void *context, size_t bytes, size_t alignment, uint32_t) {
        auto &a = *static_cast<Arena *>(context);
        a.used = (a.used + alignment - 1u) & ~(alignment - 1u);
        if (a.used + bytes > a.bytes.size()) return nullptr;
        void *p = a.bytes.data() + a.used;
        a.used += bytes;
        return p;
    }
};
struct Rig {
    static constexpr uint32_t kBlock = 256;
    std::unique_ptr<Arena> arena = std::make_unique<Arena>();
    ws2_host host{sizeof(host), arena.get(), Arena::allocate};
    ws2_config cfg{sizeof(cfg), 48000., kBlock, 16, 23, nullptr, 0};
    const ws2_descriptor *descriptor = ws::Module<GateDelay>::descriptor();
    void *state = nullptr;
    std::array<std::array<std::array<float, kBlock>, 16>, 3> input_storage{};
    std::array<std::array<std::array<float, kBlock>, 16>, 3> output_storage{};
    const float *in_row[3][16]{};
    float *out_row[3][16]{};
    ws2_signal input[3]{};
    ws2_signal_out output[3]{};
    float values[6]{0, 0, 0, 0, 0, 0};
    const float *param_row[6]{};
    ws2_signal param[6]{};
    ws2_process ctx{};
    uint64_t cursor = 0;
    uint32_t channels = 1;
    size_t process_allocations = 0;
    std::array<std::array<std::vector<float>, 16>, 3> rendered{};

    Rig() {
        state = descriptor->create(&host);
        REQUIRE(state != nullptr);
        REQUIRE(descriptor->prepare(state, &cfg, &host) == WS2_OK);
        for (uint32_t p = 0; p < 3; ++p) {
            for (uint32_t c = 0; c < 16; ++c) {
                in_row[p][c] = input_storage[p][c].data();
                out_row[p][c] = output_storage[p][c].data();
            }
            input[p] = {sizeof(ws2_signal), in_row[p], 1, WS2_CONNECTED};
            output[p] = {sizeof(ws2_signal_out), out_row[p], 0, 0, 16};
        }
        for (uint32_t k = 0; k < 6; ++k) {
            param_row[k] = &values[k];
            param[k] = {sizeof(ws2_signal), &param_row[k], 1, WS2_CONSTANT};
        }
        ctx.struct_size = sizeof(ctx);
        ctx.sample_rate = cfg.sample_rate;
        ctx.input_count = 3;
        ctx.output_count = 3;
        ctx.param_count = 6;
        ctx.inputs = input;
        ctx.outputs = output;
        ctx.params = param;
    }
    ~Rig() { descriptor->destroy(state); }
    template<class F> void render(uint32_t frames, uint32_t block, F source) {
        REQUIRE(block >= 1 && block <= kBlock);
        for (uint32_t start = 0; start < frames;) {
            const uint32_t n = std::min(block, frames - start);
            for (uint32_t c = 0; c < channels; ++c)
                for (uint32_t i = 0; i < n; ++i) {
                    const uint64_t t = cursor + i;
                    input_storage[0][c][i] = source(t, c);
                    input_storage[1][c][i] = float(c + 1) * .25f;
                    input_storage[2][c][i] = 0.f;
                }
            input[0].channels = channels;
            input[1].channels = channels;
            ctx.channels = channels;
            ctx.frames = n;
            ctx.frame_position = cursor;
            {
                allocation_watch::Scope watch;
                REQUIRE(descriptor->process(state, &ctx) == WS2_OK);
                process_allocations += watch.allocations();
            }
            for (uint32_t p = 0; p < 3; ++p)
                for (uint32_t c = 0; c < channels; ++c)
                    for (uint32_t i = 0; i < n; ++i)
                        rendered[p][c].push_back(output_storage[p][c][i]);
            cursor += n;
            start += n;
        }
    }
    float at(uint32_t port, uint32_t lane, uint32_t frame) const { return rendered[port][lane].at(frame); }
    uint32_t rises(uint32_t port, uint32_t lane) const {
        uint32_t count = 0;
        const auto &v = rendered[port][lane];
        for (size_t i = 0; i < v.size(); ++i)
            if (v[i] >= .5f && (i == 0 || v[i - 1] < .5f)) ++count;
        return count;
    }
};
static void gate_length_pitch_and_trig() {
    Rig r;
    r.values[GateDelay::kTime] = 5;
    r.render(720, 64, [](uint64_t t, uint32_t) { return t < 96 ? 1.f : 0.f; });
    REQUIRE(r.at(0, 0, 239) == 0.f);
    REQUIRE(r.at(0, 0, 240) == 1.f && r.at(0, 0, 335) == 1.f);
    REQUIRE(r.at(0, 0, 336) == 0.f);
    REQUIRE(r.at(1, 0, 240) == 1.f && r.at(1, 0, 287) == 1.f && r.at(1, 0, 288) == 0.f);
    REQUIRE(r.at(2, 0, 239) == 0.f && r.at(2, 0, 240) == .25f);
    REQUIRE(r.rises(0, 0) == 1 && r.process_allocations == 0);
}
static void trig_stays_a_trig() {
    Rig r;
    r.values[GateDelay::kTime] = 1;
    r.render(200, 7, [](uint64_t t, uint32_t) { return t == 0 ? 1.f : 0.f; });
    REQUIRE(r.at(0, 0, 48) == 1.f && r.at(0, 0, 49) == 0.f);
    REQUIRE(r.at(1, 0, 48) == 1.f && r.at(1, 0, 95) == 1.f && r.at(1, 0, 96) == 0.f);
}
static void strum_order_and_repeats() {
    for (int strum : {0, 1, 2, 3}) {
        Rig a;
        a.channels = 3;
        a.values[GateDelay::kTime] = 1;
        a.values[GateDelay::kSpread] = 5;
        a.values[GateDelay::kStrum] = float(strum);
        a.render(1600, 128, [](uint64_t t, uint32_t) { return t < 24 ? 1.f : 0.f; });
        std::array<int, 3> first{};
        for (uint32_t c = 0; c < 3; ++c) {
            auto &v = a.rendered[0][c];
            auto it = std::find_if(v.begin(), v.end(), [](float x) { return x >= .5f; });
            REQUIRE(it != v.end());
            first[c] = int(it - v.begin());
        }
        REQUIRE(first[0] != first[1] && first[1] != first[2] && first[0] != first[2]);
        if (strum == 0) REQUIRE(first[0] < first[1] && first[1] < first[2]);
        if (strum == 1) REQUIRE(first[0] > first[1] && first[1] > first[2]);
        if (strum == 3) {
            Rig same;
            same.channels = 3;
            same.values[GateDelay::kTime] = 1;
            same.values[GateDelay::kSpread] = 5;
            same.values[GateDelay::kStrum] = 3;
            same.render(1600, 17, [](uint64_t t, uint32_t) { return t < 24 ? 1.f : 0.f; });
            for (uint32_t c = 0; c < 3; ++c) REQUIRE(a.rendered[0][c] == same.rendered[0][c]);
        }
    }
    Rig ratchet;
    ratchet.values[GateDelay::kTime] = 4;
    ratchet.values[GateDelay::kRepeats] = 2;
    ratchet.render(900, 17, [](uint64_t t, uint32_t) { return t < 20 ? 1.f : 0.f; });
    REQUIRE(ratchet.rises(0, 0) == 3);
    REQUIRE(ratchet.at(0, 0, 192) == 1.f && ratchet.at(0, 0, 212) == 0.f);
    REQUIRE(ratchet.at(0, 0, 384) == 1.f && ratchet.at(0, 0, 404) == 0.f);
    REQUIRE(ratchet.at(0, 0, 576) == 1.f && ratchet.at(0, 0, 596) == 0.f);
}
static void time_latched_and_block_invariant() {
    Rig a;
    a.values[GateDelay::kTime] = 100;
    a.render(50, 10, [](uint64_t, uint32_t) { return 1.f; });
    a.values[GateDelay::kTime] = 0;
    a.render(5100, 64, [](uint64_t, uint32_t) { return 0.f; });
    REQUIRE(a.at(0, 0, 4799) == 0.f && a.at(0, 0, 4800) == 1.f);
    REQUIRE(a.at(0, 0, 4849) == 1.f && a.at(0, 0, 4850) == 0.f);
    for (uint32_t block : {1u, 7u, 128u, 256u}) {
        Rig b;
        b.values[GateDelay::kTime] = 3;
        b.values[GateDelay::kRepeats] = 2;
        b.render(1024, block, [](uint64_t t, uint32_t) { return (t >= 13 && t < 29) || (t >= 493 && t < 530) ? 1.f : 0.f; });
        if (block != 1) {
            Rig one;
            one.values[GateDelay::kTime] = 3;
            one.values[GateDelay::kRepeats] = 2;
            one.render(1024, 1, [](uint64_t t, uint32_t) { return (t >= 13 && t < 29) || (t >= 493 && t < 530) ? 1.f : 0.f; });
            for (uint32_t p = 0; p < 3; ++p) REQUIRE(one.rendered[p][0] == b.rendered[p][0]);
        }
        REQUIRE(b.process_allocations == 0);
    }
}
static void signal_step_and_overflow() {
    Rig s;
    s.values[GateDelay::kMode] = 1;
    s.values[GateDelay::kTime] = 10;
    s.render(1000, 23, [](uint64_t t, uint32_t) { return t >= 48 ? 1.f : 0.f; });
    uint32_t first = 0;
    while (first < 1000 && s.at(0, 0, first) < .5f) ++first;
    REQUIRE(first >= 480 && first <= 576); // 1 kHz linear interpolation: threshold within 1 ms.
    REQUIRE(s.at(1, 0, first) == 1.f && s.process_allocations == 0);
    GateDelay delay;
    for (uint32_t i = 0; i < 80; ++i) delay.enqueue(0, 1000 + i, bool(i & 1), 0.f);
    REQUIRE(delay.lanes[0].count == 64 && delay.lanes[0].dropped == 16);
    delay.reset();
    REQUIRE(delay.lanes[0].count == 0 && delay.lanes[0].dropped == 0);
}
int main() {
    gate_length_pitch_and_trig();
    trig_stays_a_trig();
    strum_order_and_repeats();
    time_latched_and_block_invariant();
    signal_step_and_overflow();
}
