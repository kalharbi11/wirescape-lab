// SPDX-License-Identifier: GPL-3.0-only
// P1-h: exercise the production Stream callback, not just its render helper.
// Fake PortAudio invokes the driver on its worker; watches live in this binary.
#include "../../tests/native/abi2/allocation_watch.h"
#include "../third_party/portaudio/portaudio.h"
#include "portaudio_service.h"
#include "wirescape_sdk.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <new>
#include <stdexcept>
#include <thread>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <dlfcn.h>
#endif
#ifdef WS_CALLBACK_LOCK_WATCH
#include <pthread.h>
// Linker wrapping covers calls from the statically linked host and engine.
// The executable's TLS excludes the control thread and fake backend bookkeeping.
namespace {
thread_local bool lock_enabled = false;
thread_local uint64_t lock_calls = 0, trylock_calls = 0;
pthread_mutex_t witness_mutex = PTHREAD_MUTEX_INITIALIZER;
}
extern "C" int __real_pthread_mutex_lock(pthread_mutex_t *);
extern "C" int __real_pthread_mutex_trylock(pthread_mutex_t *);
extern "C" int __wrap_pthread_mutex_lock(pthread_mutex_t *mutex) {
    if (lock_enabled) ++lock_calls;
    return __real_pthread_mutex_lock(mutex);
}
extern "C" int __wrap_pthread_mutex_trylock(pthread_mutex_t *mutex) {
    if (lock_enabled) ++trylock_calls;
    return __real_pthread_mutex_trylock(mutex);
}
#endif

namespace {
using namespace std::chrono_literals;
using Clock = std::chrono::steady_clock;
constexpr unsigned block = 128, prime = 4, required = 64;
enum class Mode { clean, allocation, lock };
Mode mode = Mode::clean;
std::atomic<bool> primed{false}, go{false};
std::atomic<unsigned> completed{0};
// Worker-owned; read only after Stream::stop joins.
unsigned invoked = 0, allocation_blocks = 0, lock_blocks = 0, witness_calls = 0;
uint64_t max_allocations = 0, max_locks = 0, max_trylocks = 0;
bool audible = false, invalid_output = false, bad_callback = false;

void require(bool ok, const char *why) {
    if (!ok) throw std::runtime_error(why);
}
template<class Predicate>
bool wait_for(Predicate predicate) {
    const auto deadline = Clock::now() + 5s;
    while (!predicate() && Clock::now() < deadline) std::this_thread::sleep_for(1ms);
    return predicate();
}

// A genuine DSP process hook: never added to the product catalogue. It is
// connected to VCO FM with a constant zero output, so it executes in the graph.
struct WitnessSource {
    static constexpr ws::Info info{"test.p1h_witness", "P1-h witness", 1};
    static constexpr std::array<ws2_port, 0> inputs{};
    static constexpr std::array outputs{ws::port("out", "Out", WS2_CV_BI)};
    static constexpr std::array<ws2_param, 0> params{};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &b) {
        if (allocation_watch::thread_enabled) {
            ++witness_calls;
            if (mode == Mode::allocation) {
                // Explicit calls, not an elidable new-expression.
                void *memory = ::operator new(32);
                ::operator delete(memory);
            }
#ifdef WS_CALLBACK_LOCK_WATCH
            if (mode == Mode::lock) {
                if (pthread_mutex_lock(&witness_mutex) == 0)
                    pthread_mutex_unlock(&witness_mutex);
                if (pthread_mutex_trylock(&witness_mutex) == 0)
                    pthread_mutex_unlock(&witness_mutex);
            }
#endif
        }
        b.out(0).set_channels(1);
        b.out(0).mark_constant();
        b.out(0).ch(0)[0] = 0.f;
    }
};

// This brackets the callback pointer passed by production Stream::Impl to
// Pa_OpenStream, including engine adoption, clocks, render and metrics.
int drive(PaStreamCallback *callback, void *output, unsigned long frames,
          const PaStreamCallbackTimeInfo *times, void *user) {
    if (invoked++ < prime)
        return callback(nullptr, output, frames, times, 0, user);
    // Pause outside the callback after priming; queue real timestamped MIDI
    // and a parameter change before the first measured invocation.
    if (!go.load(std::memory_order_acquire)) {
        primed.store(true, std::memory_order_release);
        if (!wait_for([] { return go.load(std::memory_order_acquire); })) return paAbort;
    }
    uint64_t allocations;
    int result;
    {
        allocation_watch::ThreadScope watch;
#ifdef WS_CALLBACK_LOCK_WATCH
        lock_calls = trylock_calls = 0;
        lock_enabled = true;
#endif
        result = callback(nullptr, output, frames, times, 0, user);
#ifdef WS_CALLBACK_LOCK_WATCH
        lock_enabled = false;
#endif
        allocations = watch.allocations();
    }
    if (allocations) ++allocation_blocks;
    max_allocations = (std::max)(max_allocations, allocations);
#ifdef WS_CALLBACK_LOCK_WATCH
    if (lock_calls || trylock_calls) ++lock_blocks;
    max_locks = (std::max)(max_locks, lock_calls);
    max_trylocks = (std::max)(max_trylocks, trylock_calls);
#endif
    bad_callback |= result != paContinue || frames != block;
    const auto *samples = static_cast<const float *>(output);
    for (unsigned long i = 0; i < frames * 2; ++i) {
        invalid_output |= !std::isfinite(samples[i]);
        audible |= std::abs(samples[i]) > 1e-6f;
    }
    completed.fetch_add(1, std::memory_order_release);
    return result;
}

wirescape::audio::EngineOwner graph() {
    wirescape::engine2::Config cfg{};
    cfg.sample_rate = 48000;
    cfg.max_block = block;
    cfg.max_nodes = 16;
    cfg.event_budget = 2048;
    wirescape::audio::EngineOwner app(app_engine_create(&cfg), app_engine_destroy);
    require(bool(app), "create engine");
    const char *modules[]{"midi.in", "midi.to_cv", "essentials.vco",
                          "essentials.adsr", "essentials.vca", "essentials.output"};
    for (unsigned i = 0; i < 6; ++i)
        require(app_engine_add_node(app.get(), i + 1, modules[i]) == WS2_OK, "add MIDI graph node");
    auto &engine = app_engine_native(app.get());
    require(engine.add_node(7, ws::Module<WitnessSource>::descriptor()), "add test-only DSP");
    auto connect = [&](unsigned a, unsigned ap, unsigned b, unsigned bp) {
        require(app_engine_connect(app.get(), a, ap, b, bp) == WS2_OK, "connect graph");
    };
    connect(1, 0, 2, 0);
    connect(2, 0, 3, 0);
    connect(2, 1, 4, 0);
    connect(3, 0, 5, 0);
    connect(4, 0, 5, 1);
    connect(5, 0, 6, 0);
    connect(7, 0, 3, 1);
    require(engine.output(6, 0, 1), "stereo output");
    require(app_engine_prepare(app.get(), 6, 0) == WS2_OK, "prepare");
    require(app_engine_initialize_parameter(app.get(), 2, "voice_count", 1) == WS2_OK, "voice count");
    require(app_engine_initialize_parameter(app.get(), 4, "attack", .0001f) == WS2_OK, "initial attack");
    return app;
}

void queue_inputs(AppEngine *app) {
    auto &engine = app_engine_native(app);
    ws2_event midi{};
    midi.struct_size = sizeof(midi);
    midi.type = WS2_MIDI;
    midi.source_id = 1;
    midi.note_id = -1;
    midi.ump_words = 1;
    midi.ump[0] = 0x20903c64u;
    require(engine.enqueue(1, 1, WS2_DIRECT_PORT, midi, app_engine_clock_ns(),
                wirescape::engine2::Timing::Timestamped, engine.meter().generation) == WS2_OK,
            "enqueue live MIDI note");
    ws2_event param{};
    param.struct_size = sizeof(param);
    param.type = WS2_PARAM;
    param.value = .002f;
    require(app_engine_enqueue(app, 4, param, prime * block, engine.meter().generation, "attack") == WS2_OK,
            "enqueue live attack parameter");
}
} // namespace

int main(int argc, char **argv) {
    try {
        require(argc == 4 || argc == 5, "fake directory, library, sidecar directory, optional witness mode");
        if (argc == 5) {
            if (!std::strcmp(argv[4], "--inject-allocation")) mode = Mode::allocation;
            else if (!std::strcmp(argv[4], "--inject-lock")) mode = Mode::lock;
            else throw std::runtime_error("unknown witness mode");
        }
#ifndef WS_CALLBACK_LOCK_WATCH
        require(mode != Mode::lock, "lock check not measured on this platform");
#endif
        const auto fake_dir = std::filesystem::weakly_canonical(argv[1]);
        require(fake_dir != std::filesystem::weakly_canonical(argv[3]), "fake must not reside beside sidecar");
        require(std::filesystem::weakly_canonical(argv[2]).parent_path() == fake_dir, "fake library path");
#ifdef _WIN32
        auto library = LoadLibraryA(argv[2]);
        require(library != nullptr, "load fake DLL exclusively");
        auto symbol = GetProcAddress(library, "ws_fake_set_callback_driver");
#else
        auto library = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL);
        require(library != nullptr, "load fake shared library exclusively");
        auto symbol = dlsym(library, "ws_fake_set_callback_driver");
#endif
        using Driver = decltype(&drive);
        auto set_driver = reinterpret_cast<void (*)(Driver)>(symbol);
        require(set_driver != nullptr, "fake-only driver symbol");
        set_driver(drive);
        auto engine = graph();
        auto *live = engine.get();
        wirescape::audio::Stream stream(engine, {argv[1], ""}, 48000, block);
        struct Release { ~Release() { go.store(true, std::memory_order_release); } } release;
        require(wait_for([] { return primed.load(std::memory_order_acquire); }), "four priming callbacks");
        require(stream.rendered_blocks() == prime, "priming completed on actual Stream");
        queue_inputs(live);
        go.store(true, std::memory_order_release);
        require(wait_for([] { return completed.load(std::memory_order_acquire) >= required; }),
                "64 measured callbacks");
        engine = stream.stop();
        set_driver(nullptr);
        require(bool(engine) && stream.rendered_blocks() == prime + completed.load(), "every callback completed");
        require(!bad_callback && !invalid_output && audible, "valid audio and live MIDI audible");
        require(witness_calls >= completed.load(), "DSP hook ran in every measured block");
        std::printf("callback blocks=%u allocation_blocks=%u max_allocations=%llu\n",
                    completed.load(), allocation_blocks, static_cast<unsigned long long>(max_allocations));
#ifdef WS_CALLBACK_LOCK_WATCH
        std::printf("lock_blocks=%u max_mutex_lock=%llu max_mutex_trylock=%llu\n", lock_blocks,
                    static_cast<unsigned long long>(max_locks), static_cast<unsigned long long>(max_trylocks));
#else
        std::puts("locks: not measured (no Linux linker interposition)");
#endif
        if (allocation_blocks) std::fprintf(stderr, "FAIL callback allocation watch\n");
        if (lock_blocks) std::fprintf(stderr, "FAIL callback lock watch\n");
        return allocation_blocks || lock_blocks ? 1 : 0;
    } catch (const std::exception &e) {
        std::fprintf(stderr, "fixture failure: %s\n", e.what());
        return 2;
    }
}
