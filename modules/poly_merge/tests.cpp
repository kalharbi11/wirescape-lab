// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include "../vco/dsp.h"
#include "../../sdk/examples/test_support.h"
#include "../../tests/native/abi2/allocation_watch.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <memory>

using poly_merge::PolyMerge;
namespace {
constexpr uint32_t kFrames = 256;
struct Rig {
    Pool pool{};
    ws2_host host{sizeof(host), &pool, allocate};
    const ws2_descriptor *desc = ws::Module<PolyMerge>::descriptor();
    void *instance = nullptr;
    struct Storage {
        float input[8][kFrames]{};
        float output[16][kFrames]{};
    };
    std::unique_ptr<Storage> storage = std::make_unique<Storage>();
    const float *input_ptr[8][1]{};
    float *output_ptr[16]{};
    ws2_signal in[8]{};
    ws2_signal_out out{};
    ws2_process ctx{};
    uint32_t capacity = 16;

    explicit Rig(uint32_t cap = 16, double rate = 48000.) : capacity(cap) {
        REQUIRE(cap >= 1 && cap <= 16);
        const ws2_config cfg{sizeof(cfg), rate, kFrames, cap, 123, nullptr, 0};
        instance = desc->create(&host);
        REQUIRE(instance && desc->prepare(instance, &cfg, &host) == WS2_OK);
        for (uint32_t p = 0; p < 8; ++p) {
            input_ptr[p][0] = storage->input[p];
            in[p] = {sizeof(ws2_signal), input_ptr[p], 1, WS2_CONSTANT};
        }
        for (uint32_t c = 0; c < 16; ++c) output_ptr[c] = storage->output[c];
        out = {sizeof(ws2_signal_out), output_ptr, 0, 0, cap};
        ctx.struct_size = sizeof(ctx);
        ctx.sample_rate = rate;
        ctx.channels = cap;
        ctx.input_count = 8;
        ctx.output_count = 1;
        ctx.inputs = in;
        ctx.outputs = &out;
    }
    ~Rig() { desc->destroy(instance); }
    void connect(uint32_t port, bool constant = false) {
        REQUIRE(port < 8);
        in[port].flags = WS2_CONNECTED | (constant ? uint32_t(WS2_CONSTANT) : 0u);
    }
    void disconnect(uint32_t port) {
        REQUIRE(port < 8);
        in[port].flags = 0;
    }
    void sample(uint32_t port, uint32_t frame, float value) {
        storage->input[port][frame] = value;
    }
    void run(uint32_t frames) {
        REQUIRE(frames >= 1 && frames <= kFrames);
        ctx.frames = frames;
        REQUIRE(desc->process(instance, &ctx) == WS2_OK);
        ctx.frame_position += frames;
    }
    float value(uint32_t lane, uint32_t frame) const {
        return storage->output[lane][frame];
    }
};

void sparse_poly_and_disconnection() {
    Rig rig;
    for (uint32_t p : {0u, 2u, 7u}) {
        rig.connect(p);
        for (uint32_t i = 0; i < 256; ++i)
            rig.sample(p, i, float(int(p) - 3) * .25f + float(i) / 256.f);
    }
    rig.run(256);
    REQUIRE(rig.out.channels == 8);
    for (uint32_t p = 0; p < 8; ++p)
        for (uint32_t i : {0u, 1u, 127u, 255u})
            REQUIRE(same_element(rig.value(p, i),
                                 (p == 0 || p == 2 || p == 7) ? rig.storage->input[p][i] : 0.f));
    rig.disconnect(7);
    rig.run(256);
    REQUIRE(rig.out.channels == 3);
    REQUIRE(rig.value(1, 1) == 0.f);
    rig.disconnect(2);
    rig.disconnect(0);
    rig.run(256);
    REQUIRE(rig.out.channels == 1 && rig.value(0, 0) == 0.f && rig.value(0, 255) == 0.f);
}

void one_through_eight_and_host_caps() {
    for (uint32_t cap : {1u, 3u, 8u, 16u})
        for (uint32_t n : {1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u})
            for (uint32_t frames : {1u, 7u, 128u, 256u}) {
                Rig rig(cap);
                rig.connect(n - 1, true);
                rig.sample(n - 1, 0, .875f);
                rig.run(frames);
                REQUIRE(rig.out.channels == std::min(cap, n));
                for (uint32_t p = 0; p < rig.out.channels; ++p)
                    for (uint32_t i : {0u, frames - 1})
                        REQUIRE(same_element(rig.value(p, i), p == n - 1 ? .875f : 0.f));
                REQUIRE((rig.out.flags & WS2_CONSTANT) != 0);
            }
}

void block_equivalence_and_allocations() {
    for (double rate : {44100., 48000., 96000.})
        for (uint32_t frames : {1u, 7u, 128u, 256u}) {
            Rig rig(16, rate);
            rig.connect(0);
            rig.connect(3);
            for (uint32_t i = 0; i < frames; ++i) {
                rig.sample(0, i, float(i) * .000125f);
                rig.sample(3, i, -float(i) * .00025f);
            }
            uint64_t count = 0;
            {
                allocation_watch::Scope watch;
                rig.run(frames);
                count = watch.allocations();
            }
            REQUIRE(count == 0 && rig.out.channels == 4);
            for (uint32_t i = 0; i < frames; ++i) {
                REQUIRE(same_element(rig.value(0, i), rig.storage->input[0][i]));
                REQUIRE(same_element(rig.value(1, i), 0.f));
                REQUIRE(same_element(rig.value(2, i), 0.f));
                REQUIRE(same_element(rig.value(3, i), rig.storage->input[3][i]));
            }
            rig.desc->reset(rig.instance);
            rig.run(frames);
            REQUIRE(rig.out.channels == 4);
        }
}

void downstream_vco_poly() {
    Rig poly;
    poly.connect(0, true);
    poly.connect(3, true);
    poly.sample(0, 0, 0.f);  // C4
    poly.sample(3, 0, 1.f);  // C5
    poly.run(128);
    REQUIRE(poly.out.channels == 4);

    Pool pool{};
    ws2_host host{sizeof(host), &pool, allocate};
    auto *vco = ws::Module<ws2ports::Vco>::descriptor();
    void *instance = vco->create(&host);
    const ws2_config cfg{sizeof(cfg), 48000., kFrames, 16, 42, nullptr, 0};
    REQUIRE(instance && vco->prepare(instance, &cfg, &host) == WS2_OK);
    const float *pitch[16]{};
    for (uint32_t c = 0; c < 16; ++c) pitch[c] = poly.storage->output[c];
    ws2_signal inputs[3]{{sizeof(ws2_signal), pitch, 4, WS2_CONNECTED}};
    float frequency = 220.f;
    const float *frequency_row[]{&frequency};
    ws2_signal params[1]{{sizeof(ws2_signal), frequency_row, 1, WS2_CONSTANT}};
    std::array<std::array<float, 128>, 16> storage{};
    float *voice[16]{};
    for (uint32_t c = 0; c < 16; ++c) voice[c] = storage[c].data();
    ws2_signal_out output{sizeof(output), voice, 0, 0, 16};
    ws2_process ctx{};
    ctx.struct_size = sizeof(ctx);
    ctx.sample_rate = 48000.;
    ctx.frames = 128;
    ctx.channels = 4;
    ctx.input_count = 3;
    ctx.output_count = 1;
    ctx.param_count = 1;
    ctx.inputs = inputs;
    ctx.outputs = &output;
    ctx.params = params;
    REQUIRE(vco->process(instance, &ctx) == WS2_OK);
    REQUIRE(output.channels == 4);
    REQUIRE(std::isfinite(storage[0][16]) && std::isfinite(storage[3][16]));
    REQUIRE(std::abs(storage[0][16] - storage[3][16]) > .0001f);
    vco->destroy(instance);
}
} // namespace

int main() {
    sparse_poly_and_disconnection();
    one_through_eight_and_host_caps();
    block_equivalence_and_allocations();
    downstream_vco_poly();
}
