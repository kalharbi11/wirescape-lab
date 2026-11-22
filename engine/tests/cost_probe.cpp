// SPDX-License-Identifier: GPL-3.0-only
#include "../../modules/quad_vca/dsp.h"
#include "benchmark_graph.h"
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <string>

static void probe(int argc, char **argv) {
    VERIFY(argc == 4);
    const std::string mode = argv[2];
    char *end = nullptr;
    auto blocks = std::strtoul(argv[3], &end, 10);
    VERIFY(*argv[3] && !*end && blocks > 0 && blocks <= 1000000);
    float buffer[256]{};
    float *out[]{buffer};
    if (mode == "abi2_quad_vca_lpg8") {
        // An eight-voice oscillator feeds all four normalled LPG channels.
        Config config;
        config.max_channels = 8;
        Engine graph(config);
        VERIFY(graph.add_node(1, ws::Module<ws2ports::Vco>::descriptor()));
        VERIFY(graph.add_node(2, ws::Module<quad_vca::QuadVca>::descriptor()));
        VERIFY(graph.set_channels(1, 8) && graph.set_channels(2, 8));
        VERIFY(graph.connect(1, 0, 2, 0));
        for (uint32_t channel = 0; channel < 4; ++channel) {
            VERIFY(graph.set_parameter(2, 4 + channel, 1.f));
        }
        VERIFY(graph.output(2, 4, 0) && graph.prepare());
        for (unsigned long i = 0; i < blocks; ++i) VERIFY(graph.render(out, 1, 256) == 0);
    } else {
        VERIFY(mode == "abi2_mono" || mode == "abi2_modulated" || mode == "abi2_poly8");
        auto graph = make(mode == "abi2_poly8" ? 8 : 1, mode == "abi2_modulated");
        for (unsigned long i = 0; i < blocks; ++i) VERIFY(graph->render(out, 1, 256) == 0);
    }
}

int main(int argc, char **argv) {
    try {
        probe(argc, argv);
        return 0;
    } catch (const std::exception &e) {
        std::fprintf(stderr, "%s\n", e.what());
        return 2;
    }
}
