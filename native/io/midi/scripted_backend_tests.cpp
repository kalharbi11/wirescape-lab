// SPDX-License-Identifier: GPL-3.0-only
#include "scripted_backend.h"
#include "midi_host.h"
#include "midi_service.h"
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <thread>

#define CHECK(x) do { if (!(x)) { std::fprintf(stderr, "scripted MIDI line %d: %s\n", __LINE__, #x); std::abort(); } } while (0)

using wirescape::midi::ScriptedBackend;
struct Capture {
    uint64_t last_ns = 0;
    uint64_t events = 0, on = 0, off = 0, clock = 0, sense = 0;
    uint64_t cc = 0, sustain = 0, panic = 0;
    std::array<unsigned, 4> panic_by_channel{};
    static void message(void* context, const uint8_t* bytes, size_t n, uint64_t ns) {
        auto &s = *static_cast<Capture*>(context);
        CHECK(ns >= s.last_ns);
        s.last_ns = ns;
        CHECK(n >= 1 && n <= 3);
        ++s.events;
        if (bytes[0] == 0xf8) { CHECK(n == 1); ++s.clock; }
        else if (bytes[0] == 0xfe) { CHECK(n == 1); ++s.sense; }
        else if ((bytes[0] & 0xf0) == 0x90) { CHECK(n == 3); ++s.on; }
        else if ((bytes[0] & 0xf0) == 0x80) { CHECK(n == 3 && bytes[2] == 0); ++s.off; }
        else {
            CHECK((bytes[0] & 0xf0) == 0xb0 && n == 3);
            if (bytes[1] == 1) ++s.cc;
            else if (bytes[1] == 64) { CHECK(bytes[2] == 0 || bytes[2] == 127); ++s.sustain; }
            else {
                CHECK(bytes[1] == 123 && bytes[2] == 0);
                ++s.panic;
                CHECK((bytes[0] & 15) < 4);
                ++s.panic_by_channel[bytes[0] & 15];
            }
        }
    }
};
static void source_script() {
    ScriptedBackend backend;
    Capture capture;
    const auto identity = backend.identity();
    CHECK(backend.endpoints().size() == 1);
    CHECK(backend.endpoints().at(0).system_name == "scripted:midi-m8:0");
    CHECK(!backend.advance_to(1000000000ULL));
    CHECK(!backend.open({"Physical Keyboard", "alsa:128:0"}, {&capture, Capture::message, {}}));
    CHECK(backend.open(identity, {&capture, Capture::message, {}}));
    CHECK(!backend.open(identity, {&capture, Capture::message, {}}));
    CHECK(backend.advance_to(1000000000ULL) > 0);
    CHECK(capture.on >= 10 && capture.off >= 10);
    CHECK(capture.clock >= 64 && capture.sense >= 4);
    CHECK(capture.cc >= 100 && capture.sustain == 1);
    // Virtual advance to the ten-minute panic. This does not sleep ten minutes
    // or open a real port; the per-call bound preserves all pending messages.
    const uint64_t ten_minutes = 600000000000ULL;
    size_t iterations = 0;
    while (backend.advance_to(ten_minutes, 4096)) CHECK(++iterations < 100);
    CHECK(capture.panic == 4);
    for (auto count : capture.panic_by_channel) CHECK(count == 1);
    CHECK(capture.on > 5000 && capture.off > 5000);
    CHECK(capture.clock > 30000 && capture.sense >= 2400);
    CHECK(capture.cc > 50000 && capture.sustain >= 150);
    CHECK(!backend.advance_to(ten_minutes));
    backend.close(identity);
    CHECK(!backend.opened() && !backend.advance_to(ten_minutes + 100));
    CHECK(backend.open(identity, {&capture, Capture::message, {}}));
    CHECK(backend.advance_to(ten_minutes + 250000000ULL) > 0);
    backend.close(identity);
}
static void host_injection() {
    wirescape::engine2::Config config{};
    config.sample_rate = 48000;
    config.max_nodes = 8;
    config.max_block = 128;
    config.ring_capacity = 64;
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(app_engine_create(&config), app_engine_destroy);
    CHECK(engine);
    CHECK(app_engine_add_node(engine.get(), 1, "host.keyboard") == WS2_OK);
    CHECK(app_engine_prepare(engine.get(), 1, 1) == WS2_OK);
    ScriptedBackend::Config script_config;
    script_config.origin_ns = app_engine_clock_ns();
    auto backend = std::make_unique<ScriptedBackend>(script_config);
    auto *script = backend.get();
    wirescape::midi::Host host(true, std::move(backend));
    host.select(script->identity(), true);
    std::string error;
    CHECK(host.start(engine.get(), R"({"modules":[{"id":1,"module":"host.keyboard"}]})", error));
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
    while (!script->opened() && std::chrono::steady_clock::now() < deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    CHECK(script->opened());
    CHECK(script->advance_to(20000000ULL) >= 5);
    while (host.counters().received < 5 && std::chrono::steady_clock::now() < deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    CHECK(host.counters().received >= 5);
    CHECK(host.counters().dropped == 0 && host.counters().ring_full == 0);
    // Render stays parked: >64 releases saturate the real engine's MIDI
    // producer and exercise Host::deliver's counted panic fallback.
    const uint8_t off[]{0x80, 60, 0};
    for (unsigned i = 0; i < 128; ++i) CHECK(script->inject(off, sizeof(off), app_engine_clock_ns()));
    while (!host.counters().release_panics && std::chrono::steady_clock::now() < deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    CHECK(host.counters().release_panics > 0);
    CHECK(host.counters().send_fail > 0);
    CHECK(host.diagnostics().find("\"release_panics\":") != std::string::npos);
    host.stop();
    CHECK(!script->opened());
    const auto stopped_panics = host.counters().release_panics;
    CHECK(stopped_panics > 0);
    CHECK(host.diagnostics().find(std::string("\"release_panics\":") + std::to_string(stopped_panics)) != std::string::npos);
}
int main() {
    source_script();
    host_injection();
    std::puts("PASS OB-g2 scripted midi-m8 virtual clock, 24ppqn, active sensing, CC/sustain, 10-minute panic, injected Host");
}
