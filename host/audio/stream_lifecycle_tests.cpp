// SPDX-License-Identifier: GPL-3.0-only
// Exercises the production audio::Stream against only the device-off fake PortAudio DLL/so.
#include "../document/runtime_patch.h"
#include "portaudio_service.h"
#include "wirescape_sdk.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <dlfcn.h>
#endif
static void require(bool value, const char *message) {
    if (!value) throw std::runtime_error(message);
}
namespace {
// Test-only descriptor, never added to the shipped catalogue. The actual
// production callback enters process and spins until the control owner releases it.
std::atomic<bool> stall_requested{false}, stall_entered{false};
struct StallSource {
    static constexpr ws::Info info{"test.p0a_stall", "P0a stall fixture", 1};
    static constexpr std::array<ws2_port, 0> inputs{};
    static constexpr std::array outputs{ws::port("out", "Out", WS2_CV_BI)};
    static constexpr std::array<ws2_param, 0> params{};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &b) {
        if (stall_requested.load(std::memory_order_acquire)) {
            stall_entered.store(true, std::memory_order_release);
            while (stall_requested.load(std::memory_order_acquire)) {}
        }
        b.out(0).set_channels(1);
        b.out(0).mark_constant();
        b.out(0).ch(0)[0] = 0.f;
    }
};

void test_render_liveness(const wirescape::engine2::Config &config,
                          const wirescape::audio::StreamSelection &selection) {
    using namespace std::chrono;
    using namespace std::chrono_literals;
    wirescape::audio::EngineOwner engine(app_engine_create(&config), app_engine_destroy);
    require(bool(engine), "P0a engine");
    require(app_engine_native(engine.get()).add_node(1, ws::Module<StallSource>::descriptor()) &&
                app_engine_prepare(engine.get(), 1, 0) == WS2_OK, "P0a synthetic graph prepares");
    stall_requested.store(false);
    stall_entered.store(false);
    wirescape::audio::Stream stream(engine, selection, 48000, 128);
    // Unblock before the Stream destructor joins, even if an assertion throws.
    struct Release { ~Release() { stall_requested.store(false, std::memory_order_release); } } release;
    auto wait = [](auto predicate, steady_clock::time_point deadline) {
        while (!predicate() && steady_clock::now() < deadline) std::this_thread::sleep_for(1ms);
        return predicate();
    };
    require(wait([&] { return stream.rendered_blocks() >= 2; }, steady_clock::now() + 2s),
            "P0a completed blocks advance while rendering");
    require(stream.running() && !stream.stalled(), "P0a healthy active stream is not stalled");
    stall_requested.store(true, std::memory_order_release);
    require(wait([] { return stall_entered.load(std::memory_order_acquire); }, steady_clock::now() + 2s),
            "P0a actual DSP entered bounded test spin");
    const auto entered = steady_clock::now();
    const auto frozen = stream.rendered_blocks();
    require(stream.running() && !stream.stalled(), "P0a active immediately before stall deadline");
    require(wait([&] { return stream.stalled(); }, entered + 1s), "P0a detect stalled within one second");
    require(stream.running() && stream.rendered_blocks() == frozen,
            "P0a backend active despite no completed render");
    stall_requested.store(false, std::memory_order_release);
    require(wait([&] { return stream.rendered_blocks() > frozen && !stream.stalled(); },
                 steady_clock::now() + 1s), "P0a progress clears stalled state");
    engine = stream.stop();
    require(bool(engine) && !stream.running() && !stream.stalled(), "P0a stopped is not stalled");
}
} // namespace

int main(int argc, char **argv) {
    try {
        require(argc == 4, "fake backend directory, library, and sidecar directory required");
        require(std::filesystem::weakly_canonical(argv[1]) != std::filesystem::weakly_canonical(argv[3]),
                "fake PortAudio must never be placed beside wirescape-engine");
        const auto fake_dir = std::filesystem::weakly_canonical(argv[1]);
        const auto library_dir = std::filesystem::weakly_canonical(argv[2]).parent_path();
        require(library_dir == fake_dir, "fake PortAudio library must reside inside its test-only directory");
#ifdef _WIN32
        auto *library = LoadLibraryA(argv[2]);
        require(library != nullptr, "load fake DLL exclusively");
        auto symbol = [&](const char *name) { return GetProcAddress(library, name); };
#else
        auto *library = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL);
        require(library != nullptr, "load fake PortAudio shared library exclusively");
        auto symbol = [&](const char *name) { return dlsym(library, name); };
#endif
        const auto fail = reinterpret_cast<void (*)(int)>(symbol("ws_fake_fail"));
        const auto stats = reinterpret_cast<void (*)(int *)>(symbol("ws_fake_stats"));
        require(fail && stats, "fake-only symbol signatures present");
        wirescape::engine2::Config config{};
    config.sample_rate = 48000;
    config.max_block = 128;
    config.max_nodes = 16;
    config.event_budget = 2048;
        wirescape::audio::EngineOwner catalogue(app_engine_create(&config), app_engine_destroy);
        require(bool(catalogue), "create test catalogue");
        const std::string patch = R"({"format":"wirescape.native.patch","version":2,
          "settings":{"sample_rate":48000},
          "modules":[{"id":1,"module":"essentials.output","version":2,"parameters":{}}],
          "connections":[],"outputs":[{"module":1,"port":"audio","bus_channel":0}]})";
        const auto make = [&] {
            std::string error;
            wirescape::audio::EngineOwner engine(
                wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error), app_engine_destroy);
            require(bool(engine), "prepare fake Stream graph");
            return engine;
        };
        const wirescape::audio::StreamSelection selection{argv[1], ""};
        for (int mode : {1, 2}) {
            auto engine = make();
            fail(mode);
            bool refused = false;
            try {
                wirescape::audio::Stream stream(engine, selection, 48000, 128);
            } catch (const std::exception &) {
                refused = true;
            }
            require(refused && engine != nullptr, "failed open/start must return graph ownership and clean up backend");
        }
        auto engine = make();
        fail(0);
        int stopped_producers = 0;
        wirescape::audio::Stream stream(engine, selection, 48000, 128, [&] { ++stopped_producers; });
        require(!engine && stream.buffer_frames() == 128, "stream owns engine and real block size");
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        int before[5]{};
        do {
            stats(before);
            if (before[2] > 0) break;
            std::this_thread::yield();
        } while (std::chrono::steady_clock::now() < deadline);
        require(before[0] >= 3 && before[1] >= 2 && before[2] > 0, "fake callbacks actually entered production Stream");
        engine = stream.stop();
        require(bool(engine) && stopped_producers > 0, "quiescent stop returns engine after stopping producers");
        int stopped[5]{};
        stats(stopped);
        std::this_thread::yield();
        int later[5]{};
        stats(later);
        require(stopped[2] == later[2] && stopped[3] >= 2 && stopped[4] >= 2,
                "no callback runs after Stream stop; start failure also closed");
        auto abort_engine = make();
        fail(3);
        wirescape::audio::Stream abort_stream(abort_engine, selection, 48000, 128);
        abort_engine = abort_stream.stop();
        require(bool(abort_engine), "stop failure uses abort then returns graph ownership");
        fail(0);
        test_render_liveness(config, selection);
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
