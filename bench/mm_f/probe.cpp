// SPDX-License-Identifier: GPL-3.0-only
// MM-f: Linux-only, device-free diagnostic. Never linked into the product.
#include "runtime_patch.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <sys/resource.h>

using Json = nlohmann::json;
using App = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;
static void need(bool ok, const std::string& reason) {
    if (!ok) throw std::runtime_error(reason);
}
static long rss_kib() {
    std::ifstream in("/proc/self/status");
    std::string line;
    while (std::getline(in, line)) {
        if (line.rfind("VmRSS:", 0) == 0) return std::stol(line.substr(6));
    }
    throw std::runtime_error("VmRSS unavailable");
}
static long peak_kib() {
    struct rusage usage{};
    need(getrusage(RUSAGE_SELF, &usage) == 0, "getrusage failed");
    return usage.ru_maxrss;
}
int main(int argc, char** argv) {
    try {
        need(argc == 5, "usage: mm_f_probe 64|128 available-only|full base.json generated.json");
        const std::string count_arg = argv[1], mode = argv[2];
        need(count_arg == "64" || count_arg == "128", "unsupported node count");
        need(mode == "available-only" || mode == "full", "unsupported workload");
        const unsigned count = std::stoul(count_arg);
        const bool full = mode == "full";
        std::ifstream input(argv[3]);
        need(bool(input), "cannot open base fixture");
        Json patch = Json::parse(input);
        need(patch.at("modules").size() == 2 && patch.at("connections").size() == 1,
             "base fixture drift");
        unsigned next = 3;
        auto add = [&](const char* type) {
            const auto id = next++;
            patch["modules"].push_back({{"id", id}, {"module", type},
                                       {"version", 1}, {"parameters", Json::object()}});
            return id;
        };
        const unsigned pairs = (count-2)/(full ? 4 : 3);
        for (unsigned i=0; i<pairs; ++i) {
            const auto feeder = add("midi.in"), converter = add("midi.cc_to_cv");
            patch["connections"].push_back({{"kind","event"},
                {"from", {{"module",feeder},{"port","midi"}}},
                {"to", {{"module",converter},{"port","midi"}}}});
        }
        const unsigned macro_count = full ? (count-2-2*pairs)/2 : 0;
        const unsigned osc_count = count-2-2*pairs-macro_count;
        for (unsigned i=0; i<osc_count; ++i) add("osc.in");
        for (unsigned i=0; i<macro_count; ++i) add("essentials.macro");
        need(next == count+1 && patch["modules"].size() == count, "bad padding");
        const auto bytes = patch.dump();
        std::ofstream generated(argv[4], std::ios::binary|std::ios::trunc);
        generated << bytes;
        generated.close();
        need(bool(generated), "fixture write failed");
        wirescape::engine2::Config cfg{};
        cfg.sample_rate = 48000;
        cfg.max_block = 128;
        cfg.max_nodes = count;
        cfg.event_budget = 2048;
        std::array<float,128> left{}, right{};
        float* rows[]{left.data(),right.data()};
        std::array<double,3750> durations{};
        const auto before = rss_kib();
        std::string error;
        App engine(wirescape::document::load_runtime_patch(bytes,nullptr,cfg,error),app_engine_destroy);
        need(bool(engine),"load/prepare refused: "+error);
        auto& graph = app_engine_native(engine.get());
        for (const auto& m : patch["modules"]) {
            const auto* d = graph.descriptor(m["id"].get<uint32_t>());
            need(d && m["module"].get<std::string>() == d->id,"prepared graph differs from authored");
        }
        auto render = [&] {
            return app_engine_render_channels(engine.get(), rows, 2, 128);
        };
        auto check = [&](double& peak) {
            for (auto* channel : rows)
                for (unsigned i=0;i<128;++i) {
                    const float s = channel[i];
                    need(std::isfinite(s),"nonfinite sample");
                    peak = std::max(peak,std::abs(double(s)));
                }
        };
        double peak = 0;
        for (unsigned i=0;i<375;++i) {
            need(render()==WS2_OK,"warmup render failed");
            check(peak);
        }
        const auto warmed = rss_kib();
        peak = 0;
        using Clock = std::chrono::steady_clock;
        double sum = 0, worst = 0;
        for (auto& us : durations) {
            const auto start = Clock::now();
            const auto status = render();
            const auto end = Clock::now();
            need(status == WS2_OK,"measured render failed");
            us = std::chrono::duration<double,std::micro>(end-start).count();
            sum += us;
            worst = std::max(worst,us);
            check(peak);
        }
        need(peak>0,"silent base graph");
        const auto meter = graph.meter();
        need(meter.faults==0 && meter.late==0 && meter.dropped==0 &&
             meter.ring_full==0 && meter.stale==0 && meter.arena_full==0,"unclean render counters");
        const auto high = peak_kib();
        Json result = {{"workload",mode},{"nodes",count},{"midi_in",pairs},{"cc_to_cv",pairs},
          {"osc_in",osc_count},{"macro",macro_count},{"cables",patch["connections"].size()},
          {"warmup_blocks",375},{"measured_blocks",durations.size()},
          {"rate",48000},{"block",128},{"period_us",128000000.0/48000},
          {"rss_before_kib",before},{"rss_warmed_kib",warmed},{"peak_rss_kib",high},
          {"mean_block_us",sum/durations.size()},{"worst_block_us",worst},{"peak",peak}};
        std::cout << "MM_F " << result.dump() << '\n';
    } catch(const std::exception& e) {
        std::cerr << "MM_F refused: " << e.what() << '\n';
        return 1;
    }
}
