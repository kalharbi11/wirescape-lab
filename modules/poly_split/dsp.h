// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
#include <array>

namespace poly_split {

struct PolySplit {
    static constexpr ws::Info info{"essentials.poly_split", "Poly Split", 1};
    static constexpr std::array inputs{ws::port("in", "In", WS2_CV_BI, WS2_POLY)};
    static constexpr std::array outputs{
        ws::port("out1", "Out 1", WS2_CV_BI, WS2_FIRST),
        ws::port("out2", "Out 2", WS2_CV_BI, WS2_FIRST),
        ws::port("out3", "Out 3", WS2_CV_BI, WS2_FIRST),
        ws::port("out4", "Out 4", WS2_CV_BI, WS2_FIRST),
        ws::port("out5", "Out 5", WS2_CV_BI, WS2_FIRST),
        ws::port("out6", "Out 6", WS2_CV_BI, WS2_FIRST),
        ws::port("out7", "Out 7", WS2_CV_BI, WS2_FIRST),
        ws::port("out8", "Out 8", WS2_CV_BI, WS2_FIRST)};
    static constexpr std::array<ws2_param, 0> params{};

    void prepare(const ws::Setup &) {}
    void reset() {}

    void process(ws::Block &block) {
        const auto input = block.in(0);
        const uint32_t channels = input.connected() ? input.channels() : 0;
        for (uint32_t lane = 0; lane < outputs.size(); ++lane) {
            auto output = block.out(lane);
            if (!output.set_channels(1)) continue;
            // Signal::ch broadcasts mono. Check the lane first to keep missing lanes silent.
            const auto source = lane < channels ? input.ch(lane) : ws::Channel{};
            output.mark_constant(source.is_constant);
            if (auto *destination = output.ch()) {
                for (uint32_t frame = 0; frame < block.frames(); ++frame)
                    destination[frame] = source[frame];
            }
        }
    }
};

} // namespace poly_split
