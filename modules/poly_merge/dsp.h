// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
#include <algorithm>
#include <array>
#include <cstdint>

namespace poly_merge {

// Eight FIRST (mono) inputs form one polyphonic signal cable, preserving samples.
struct PolyMerge {
    static constexpr ws::Info info{"essentials.poly_merge", "Poly Merge", 1};
    static constexpr std::array inputs{
        ws::port("in1", "In 1", WS2_CV_BI, WS2_FIRST),
        ws::port("in2", "In 2", WS2_CV_BI, WS2_FIRST),
        ws::port("in3", "In 3", WS2_CV_BI, WS2_FIRST),
        ws::port("in4", "In 4", WS2_CV_BI, WS2_FIRST),
        ws::port("in5", "In 5", WS2_CV_BI, WS2_FIRST),
        ws::port("in6", "In 6", WS2_CV_BI, WS2_FIRST),
        ws::port("in7", "In 7", WS2_CV_BI, WS2_FIRST),
        ws::port("in8", "In 8", WS2_CV_BI, WS2_FIRST)};
    static constexpr std::array outputs{ws::port("out", "Out", WS2_CV_BI, WS2_POLY)};
    static constexpr std::array<ws2_param, 0> params{};

    uint32_t max_channels = 8;
    void prepare(const ws::Setup &s) { max_channels = std::min<uint32_t>(8u, s.max_channels()); }
    void reset() {}

    void process(ws::Block &block) {
        uint32_t highest = 0;
        bool all_constant = true;
        for (uint32_t p = 0; p < 8; ++p) {
            const ws::Signal input = block.in(p);
            if (!input.connected()) continue;
            highest = p + 1;
            all_constant = all_constant && input.constant();
        }
        const uint32_t lanes = std::min(std::max<uint32_t>(1u, highest), max_channels);
        auto output = block.out(0);
        if (!output.set_channels(lanes)) return;
        output.mark_constant(all_constant);
        for (uint32_t lane = 0; lane < lanes; ++lane) {
            const ws::Signal input = block.in(lane);
            const ws::Channel source = input.connected() ? input.ch(0) : ws::Channel{};
            float *const destination = output.ch(lane);
            if (!destination) continue;
            for (uint32_t frame = 0; frame < block.frames(); ++frame)
                destination[frame] = source[frame];
        }
    }
};

} // namespace poly_merge
