// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include "../../sdk/examples/test_support.h"
#include "../../tests/native/abi2/allocation_watch.h"

namespace {
constexpr uint32_t frames = 7;
constexpr uint32_t lanes = 8;

void split_channels() {
    Pool pool{};
    ws2_host host{sizeof(host), &pool, allocate};
    const auto *descriptor = ws::Module<poly_split::PolySplit>::descriptor();
    const ws2_config config{sizeof(config), 48000., frames, lanes, 123, nullptr, 0};
    auto *instance = descriptor->create(&host);
    REQUIRE(instance && descriptor->prepare(instance, &config, &host) == WS2_OK);

    float input_samples[lanes][frames]{};
    const float *input_rows[lanes]{};
    float output_samples[lanes][lanes][frames]{};
    float *output_rows[lanes][lanes]{};
    ws2_signal input{sizeof(input), input_rows, lanes, WS2_CONNECTED};
    ws2_signal_out outputs[lanes]{};
    for (uint32_t lane = 0; lane < lanes; ++lane) {
        input_rows[lane] = input_samples[lane];
        for (uint32_t channel = 0; channel < lanes; ++channel)
            output_rows[lane][channel] = output_samples[lane][channel];
        outputs[lane] = {sizeof(ws2_signal_out), output_rows[lane], 0, 0, lanes};
        for (uint32_t frame = 0; frame < frames; ++frame)
            input_samples[lane][frame] = float(lane + 1) * .125f - float(frame) * .25f;
    }

    ws2_process context{};
    context.struct_size = sizeof(context);
    context.sample_rate = 48000.;
    context.frames = frames;
    context.channels = lanes;
    context.input_count = 1;
    context.output_count = lanes;
    context.inputs = &input;
    context.outputs = outputs;

    const auto check = [&](uint32_t active, bool constant) {
        {
            allocation_watch::Scope watch;
            REQUIRE(descriptor->process(instance, &context) == WS2_OK);
            REQUIRE(watch.allocations() == 0);
        }
        for (uint32_t lane = 0; lane < lanes; ++lane) {
            REQUIRE(outputs[lane].channels == 1);
            REQUIRE(bool(outputs[lane].flags & WS2_CONSTANT) == (constant || lane >= active));
            for (uint32_t frame = 0; frame < frames; ++frame)
                REQUIRE(same_element(output_samples[lane][0][frame],
                                     lane < active ? input_samples[lane][constant ? 0 : frame] : 0.f));
        }
    };

    check(8, false);
    input.channels = 3;
    check(3, false);
    input.channels = 1;
    input.flags = WS2_CONNECTED | WS2_CONSTANT;
    check(1, true);
    descriptor->reset(instance);
    input.channels = 0;
    input.flags = 0;
    check(0, false);
    descriptor->destroy(instance);
}
} // namespace

int main() {
    split_channels();
}
