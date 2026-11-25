// SPDX-License-Identifier: GPL-3.0-only
#include "allocation_watch.h"
#include "engine2.h"
#include "wirescape_sdk.h"
#include "../../../modules/osc_out/dsp.h"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <random>
#include <thread>
using namespace wirescape::engine2;
using Clock = std::chrono::steady_clock;
#define CHECK(x)                                                                                                       \
    do {                                                                                                               \
        if (!(x)) {                                                                                                    \
            std::fprintf(stderr, "live replan line %d: %s\n", __LINE__, #x);                                           \
            std::abort();                                                                                              \
        }                                                                                                              \
    } while (0)
static uint64_t now_ns() {
    return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count());
}
static constexpr uint32_t frames = 256;
struct Voice {
    static constexpr ws::Info info{"test.live_voice", "Live voice", 1};
    static constexpr std::array inputs{ws::port("events", "Events", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array outputs{ws::port("signal", "Signal"),
                                        ws::port("events", "Events", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array params{ws::param("gain", "Gain", 0, 1, 1, "", WS2_AUTOMATABLE | WS2_MODULATABLE)};
    float held = 0;
    void prepare(const ws::Setup &) {}
    void reset() { held = 0; }
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(false);
        b.out(1).set_channels(0);
        b.split(
            [&](uint32_t first, uint32_t end) {
                for (uint32_t i = first; i < end; ++i) b.out(0).ch(0)[i] = held * b.param(0).value(0, i);
            },
            [&](const ws2_event &e) {
                if (e.type == WS2_NOTE_ON) held = e.value;
                else if (e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE) held = 0;
                else return; // Gain automation belongs to this voice, not its note destination.
                CHECK(b.emit(1, e));
            });
    }
};
struct Pass {
    static constexpr ws::Info info{"test.live_pass", "Live pass", 1};
    static constexpr std::array inputs{ws::port("signal", "Signal")};
    static constexpr std::array outputs{ws::port("signal", "Signal")};
    static constexpr std::array<ws2_param, 0> params{};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(false);
        for (uint32_t i = 0; i < b.frames(); ++i) b.out(0).ch(0)[i] = b.in(0).value(0, i);
    }
};
// E5 synthetic no-adopt module. A release leaves an audible tail whose
// level follows the signal input, so a muted predecessor input, missing
// release-all, or missing successor replay has a distinct sample result.
struct ReplacementTail {
    static constexpr ws::Info info{"test.replacement_tail", "Replacement tail", 1};
    static constexpr std::array inputs{
        ws::port("signal", "Signal"),
        ws::port("notes", "Notes", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array outputs{ws::port("signal", "Signal")};
    static constexpr std::array<ws2_param, 0> params{};
    float gain = 1, level = 0;
    bool held = false;
    void prepare(const ws::Setup &s) { gain = s.config.bytes ? float(s.config.data[0]) : 1.f; }
    void reset() { level = 0; held = false; }
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(false);
        b.split([&](uint32_t first, uint32_t end) {
            for (uint32_t i = first; i < end; ++i)
                b.out(0).ch(0)[i] = level * b.in(0).value(0, i);
        }, [&](const ws2_event &e) {
            if (e.type == WS2_NOTE_ON) { held = true; level = gain; }
            else if (held && (e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE)) {
                held = false;
                level = .5f; // deterministic ring-out witness (not a silence/reset).
            }
        });
    }
};
struct Feedback : Pass {
    static constexpr ws::Info info{"test.live_feedback", "Live feedback", 1};
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(false);
        for (uint32_t i = 0; i < b.frames(); ++i) b.out(0).ch(0)[i] = b.in(0).value(0, i) + 1;
    }
};
static Config config() {
    Config c;
    c.max_block = frames;
    c.event_budget = 256;
    c.release_reserve = 64;
    c.ring_capacity = 512;
    c.future_capacity = 2048;
    return c;
}
struct Topology {
    bool pass, event_edge, fourth;
};
static std::unique_ptr<Engine> graph(Topology topology, const std::vector<Tap> &taps = {}) {
    const auto [pass, event_edge, fourth] = topology;
    auto e = std::make_unique<Engine>(config());
    CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
    CHECK(e->add_node(2, ws::Module<Voice>::descriptor()));
    if (pass) CHECK(e->add_node(3, ws::Module<Pass>::descriptor()));
    if (fourth) CHECK(e->add_node(4, ws::Module<Voice>::descriptor()));
    if (event_edge) CHECK(e->connect(1, 1, 2, 0));
    if (pass) CHECK(e->connect(2, 0, 3, 0));
    CHECK(e->output(pass ? 3 : 2, 0, 0));
    CHECK(e->output(1, 0, 1));
    if (fourth) CHECK(e->output(4, 0, 2));
    CHECK(e->register_producer() == 0);
    CHECK(e->register_producer() == 1);
    CHECK(e->set_telemetry_taps(taps));
    CHECK(e->prepare());
    return e;
}
static ws2_event note(ws2_event_type type = WS2_NOTE_ON, float value = .75f) {
    ws2_event e{};
    e.struct_size = sizeof(e);
    e.type = type;
    e.channel = 0;
    e.note_id = 7;
    e.key = 60;
    e.value = value;
    return e;
}
static void replacement_ring_out(uint32_t declared_ms = 0, uint32_t expected_frames = 960,
                                 bool decline = false, bool fault = false) {
    auto descriptor = *ws::Module<ReplacementTail>::descriptor();
    descriptor.replace_fade_ms = declared_ms;
    if (decline) descriptor.adopt = [](void *, const void *) -> int { return WS2_UNSUPPORTED; };
    if (fault) descriptor.adopt = [](void *, const void *) -> int { return WS2_INVALID; };
    auto make = [&](uint8_t gain) {
        auto e = std::make_unique<Engine>(config());
        CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
        CHECK(e->add_node(2, &descriptor, {gain}));
        CHECK(e->connect(1, 0, 2, 0));
        CHECK(e->output(2, 0, 0));
        CHECK(e->output(1, 0, 1));
        CHECK(e->register_producer() == 0);
        CHECK(e->prepare());
        return e;
    };
    auto live = make(1), successor = make(2);
    CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    CHECK(live->enqueue(0, 2, 1, note(), 0, Timing::Immediate) == WS2_OK);
    float sample[1]{}, witness[1]{};
    float *out[]{sample, witness};
    auto render = [&] {
        allocation_watch::ThreadScope watch;
        CHECK(live->render(out, 2, 1) == WS2_OK);
        CHECK(watch.allocations() == 0);
        CHECK(witness[0] == .75f);
    };
    render();
    CHECK(sample[0] == .75f);
    const auto generation = live->meter().generation;
    std::atomic<bool> done{false};
    bool ok = false;
    std::thread control([&] {
        ok = live->replan(*successor, uint64_t(frames) * 3 * 1000000000 / 48000);
        done.store(true, std::memory_order_release);
    });
    bool changed = false;
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    do {
        render();
        if (sample[0] != .75f) { changed = true; break; }
        std::this_thread::yield();
    } while (!done.load(std::memory_order_acquire) && Clock::now() < deadline);
    control.join();
    if (!ok) std::fprintf(stderr, "replacement_ring_out replan: %s\n", live->error().c_str());
    CHECK(ok);
    CHECK(changed);
    successor.reset();
    // Old receives release-all and keeps its signal input, N receives
    // held-note replay and a full-strength signal input. Only consumer
    // contributions crossfade: .375 -> 1.5 in exactly 960 samples (20 ms).
    const uint32_t fade = expected_frames;
    for (uint32_t n = 1; n <= fade; ++n) {
        if (n != 1) render();
        const float expected = .375f + (1.5f - .375f) * float(n) / fade;
        CHECK(std::abs(sample[0] - expected) < 2.e-6f);
    }
    render();
    CHECK(sample[0] == 1.5f);
    CHECK(live->enqueue(0, 2, 1, note(WS2_NOTE_OFF, 0), 0, Timing::Immediate) == WS2_OK);
    render();
    CHECK(sample[0] == .375f);
    CHECK(live->meter().generation == generation);
    CHECK(live->meter().faults == (fault ? 1u : 0u));
}
// Raw ABI test fixture: no dependence on the SDK's private instance layout.
// The release changes held state but leaves an uninterrupted phase tail.
struct AdoptPhase {
    uint32_t phase = 0, attacks = 0;
    bool held = false;
    static constexpr std::array inputs{ws::port("notes", "Notes", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array outputs{ws::port("phase", "Phase"), ws::port("held", "Held")};
    static void *WS2_CALL create(const ws2_host *host) {
        auto *p = host->alloc(host->ctx, sizeof(AdoptPhase), alignof(AdoptPhase), WS2_FAST);
        return p ? new (p) AdoptPhase{} : nullptr;
    }
    static void WS2_CALL destroy(void *p) { static_cast<AdoptPhase *>(p)->~AdoptPhase(); }
    static int WS2_CALL query(void *, const ws2_config *, ws2_ports *ports) {
        *ports = {sizeof(ws2_ports), 1, 2, inputs.data(), outputs.data()};
        return WS2_OK;
    }
    static int WS2_CALL memory(const ws2_config *, ws2_memory *m) {
        *m = {sizeof(ws2_memory), sizeof(AdoptPhase), 0, 32};
        return WS2_OK;
    }
    static int WS2_CALL prepare(void *, const ws2_config *, const ws2_host *) { return WS2_OK; }
    static void WS2_CALL reset(void *p) { *static_cast<AdoptPhase *>(p) = {}; }
    static int WS2_CALL process(void *p, ws2_process *process) {
        auto &self = *static_cast<AdoptPhase *>(p);
        ws::Block b(*process);
        for (uint32_t port = 0; port < 2; ++port) {
            b.out(port).set_channels(1);
            b.out(port).mark_constant(false);
        }
        b.split([&](uint32_t first, uint32_t end) {
            for (uint32_t i = first; i < end; ++i) {
                b.out(0).ch(0)[i] = float(++self.phase) / 65536.f;
                b.out(1).ch(0)[i] = self.held ? float(self.attacks) : 0.f;
            }
        }, [&](const ws2_event &e) {
            if (e.type == WS2_NOTE_ON) { self.held = true; ++self.attacks; self.phase = 0; }
            else if (e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE) self.held = false;
        });
        return WS2_OK;
    }
    static int WS2_CALL save(void *, const ws2_writer *) { return WS2_OK; }
    static int WS2_CALL load(void *, const ws2_reader *) { return WS2_OK; }
    static uint32_t WS2_CALL latency(void *) { return 0; }
    static int WS2_CALL adopt(void *self, const void *old) {
        *static_cast<AdoptPhase *>(self) = *static_cast<const AdoptPhase *>(old);
        return WS2_OK;
    }
};
static void replacement_adopt() {
    const ws2_descriptor descriptor{
        sizeof(ws2_descriptor), WS_ABI2_VERSION, "test.adopt_phase", "Adopt phase", 1, 1, 2, 0,
        AdoptPhase::inputs.data(), AdoptPhase::outputs.data(), nullptr,
        AdoptPhase::create, AdoptPhase::destroy, AdoptPhase::query, AdoptPhase::memory,
        AdoptPhase::prepare, AdoptPhase::reset, AdoptPhase::process, AdoptPhase::save, AdoptPhase::load,
        AdoptPhase::latency, 0, nullptr, AdoptPhase::adopt, 7};
    auto make = [&](uint8_t config_byte) {
        auto e = std::make_unique<Engine>(config());
        CHECK(e->add_node(1, &descriptor, {config_byte}));
        CHECK(e->output(1, 0, 0));
        CHECK(e->output(1, 1, 1));
        CHECK(e->register_producer() == 0);
        CHECK(e->prepare());
        return e;
    };
    auto live = make(1), successor = make(2);
    CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    float phase[1]{}, held[1]{};
    float *out[]{phase, held};
    uint32_t count = 0;
    auto render = [&] {
        allocation_watch::ThreadScope watch;
        CHECK(live->render(out, 2, 1) == WS2_OK);
        CHECK(watch.allocations() == 0);
        CHECK(std::abs(phase[0] - float(++count) / 65536.f) < 2.e-7f);
    };
    for (unsigned i = 0; i < 64; ++i) render();
    std::atomic<bool> done{false};
    bool ok = false;
    std::thread control([&] {
        ok = live->replan(*successor, uint64_t(frames) * 3 * 1000000000 / 48000);
        done.store(true, std::memory_order_release);
    });
    // Never abort with an unjoined control thread; accumulate the oracle result.
    bool continuous = true;
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    do {
        allocation_watch::ThreadScope watch;
        const int result = live->render(out, 2, 1);
        ++count;
        continuous &= result == WS2_OK && watch.allocations() == 0 &&
                      std::abs(phase[0] - float(count) / 65536.f) < 2.e-7f;
        std::this_thread::yield();
    } while (!done.load(std::memory_order_acquire) && Clock::now() < deadline);
    control.join();
    CHECK(ok);
    CHECK(continuous);
    successor.reset();
    for (unsigned i = 0; i < 336; ++i) render();
    CHECK(held[0] == 1.f); // No duplicate attack from replay after successful adopt.
    CHECK(live->enqueue(0, 1, 0, note(WS2_NOTE_OFF, 0), 0, Timing::Immediate) == WS2_OK);
    render();
    CHECK(held[0] == 0.f);
    CHECK(live->meter().faults == 0);
}
struct EventSink : Voice {
    static constexpr ws::Info info{"test.live_sink", "Live sink", 1};
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(false);
        b.out(1).set_channels(0);
        b.split(
            [&](uint32_t first, uint32_t end) {
                for (uint32_t i = first; i < end; ++i) b.out(0).ch(0)[i] = held;
            },
            [&](const ws2_event &e) {
                if (e.type == WS2_NOTE_ON) held = e.value;
                else if (e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE) held = 0;
            });
    }
};
struct EventEmitter : Voice {
    static constexpr ws::Info info{"test.live_emitter", "Live emitter", 1};
    bool emit_note = true;
    void prepare(const ws::Setup &setup) { emit_note = setup.config.bytes == 0; }
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant(true);
        b.out(0).ch(0)[0] = 1;
        b.out(1).set_channels(0);
        if (emit_note) {
            auto e = note();
            e.offset = b.frames() - 1;
            CHECK(b.emit(1, e));
        }
    }
};
// A51: true is an adoption acknowledgement, not a master-fade marker.
static void replan_with_callbacks(Engine &live, Engine &candidate) {
    std::atomic<bool> done{false}, success{false};
    std::thread edit([&] {
        success = live.replan(candidate, uint64_t(frames) * 3 * 1000000000 / 48000);
        done = true;
    });
    float samples[frames]{}, marker[frames]{};
    float *out[]{samples, marker};
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    while (!done.load() && Clock::now() < deadline) {
        {
            allocation_watch::ThreadScope watch;
            CHECK(live.render(out, 2, frames) == WS2_OK);
            CHECK(watch.allocations() == 0);
        }
        Outgoing outgoing;
        while (live.pop_egress(outgoing)) {
        }
        std::this_thread::yield();
    }
    edit.join();
    CHECK(success.load());
}
static void removed_event_routes_release() {
    for (bool replace_source : {false, true}) {
        auto make = [&](bool candidate) {
            auto e = std::make_unique<Engine>(config());
            CHECK(e->add_node(1, ws::Module<EventSink>::descriptor()));
            CHECK(e->add_node(2, ws::Module<EventEmitter>::descriptor(),
                              candidate && replace_source ? std::vector<uint8_t>{1} : std::vector<uint8_t>{}));
            CHECK(e->connect(1, 1, 2, 0));
            if (!candidate || replace_source) CHECK(e->connect(2, 1, 1, 0));
            CHECK(e->output(1, 0, 0));
            CHECK(e->output(2, 0, 1));
            CHECK(e->register_producer() == 0);
            CHECK(e->prepare());
            return e;
        };
        auto live = make(false), candidate = make(true);
        float samples[frames]{}, marker[frames]{};
        float *out[]{samples, marker};
        CHECK(live->render(out, 2, frames) == WS2_OK);
        CHECK(samples[frames - 1] == .75f);
        const auto stale = live->meter().stale;
        replan_with_callbacks(*live, *candidate);
        candidate.reset();
        // The old source's final back-edge note must not restart the destination
        // after adoption, even if the numeric cable survives source reuse.
        // The replacement emitter is configured silent: any NoteOn is stale.
        {
            allocation_watch::ThreadScope watch;
            CHECK(live->render(out, 2, 1) == WS2_OK);
            CHECK(watch.allocations() == 0);
        }
        CHECK(samples[0] == 0);
        CHECK(live->render(out, 2, frames) == WS2_OK);
        for (float sample : samples) CHECK(sample == 0);
        CHECK(live->meter().stale > stale);
    }
}
struct Audio {
    Engine &engine;
    std::atomic<bool> run{true}, enabled{true}, in_render{false}, measure{false};
    std::atomic<uint64_t> blocks{0}, gap_ns{0};
    std::atomic<float> value{0}, source{0}, fourth{0};
    std::thread thread;
    explicit Audio(Engine &e)
        : engine(e), thread([this] {
              float a[frames]{}, b[frames]{}, c[frames]{};
              float *out[]{a, b, c};
              uint64_t silence_start = 0;
              auto next = Clock::now();
              while (run.load()) {
                  if (enabled.load()) {
                      in_render = true;
                      if (enabled.load()) {
                          const auto begin = now_ns();
                          {
                              allocation_watch::ThreadScope watch;
                              CHECK(engine.render(out, 3, frames, begin) == WS2_OK);
                              CHECK(watch.allocations() == 0);
                          }
                          value = a[frames - 1];
                          source = b[frames - 1];
                          fourth = c[frames - 1];
                          ++blocks;
                          if (measure.load()) {
                              if (b[frames - 1] == 0 && !silence_start) silence_start = begin;
                              if (b[frames - 1] != 0 && silence_start) {
                                  auto gap = now_ns() - silence_start + uint64_t(frames) * 1000000000 / 48000;
                                  auto previous = gap_ns.load();
                                  while (gap > previous && !gap_ns.compare_exchange_weak(previous, gap)) {
                                  }
                                  silence_start = 0;
                              }
                          } else silence_start = 0;
                      }
                      in_render = false;
                  }
                  next += std::chrono::nanoseconds(uint64_t(frames) * 1000000000 / 48000);
                  std::this_thread::sleep_until(next);
              }
          }) {}
    ~Audio() {
        run = false;
        thread.join();
    }
    void wait(float expected, float expected_source) {
        const auto deadline = Clock::now() + std::chrono::seconds(2);
        while ((value.load() != expected || source.load() != expected_source) && Clock::now() < deadline)
            std::this_thread::yield();
        CHECK(value.load() == expected);
        CHECK(source.load() == expected_source);
    }
    void pause() {
        enabled = false;
        while (in_render.load()) std::this_thread::yield();
    }
    void resume() { enabled = true; }
};
// E4b: an unrelated topology edit cannot attenuate a held witness bus.
static void untouched_witness_no_dip() {
    auto live = graph({false, true, false});
    auto candidate = graph({true, true, false});
    CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    float subject[frames]{}, witness[frames]{};
    float *out[]{subject, witness};
    for (unsigned i = 0; i < 4; ++i) CHECK(live->render(out, 2, frames) == WS2_OK);
    const float held = witness[frames - 1];
    CHECK(held == .75f);
    std::atomic<bool> done{false}, success{false};
    std::thread control([&] {
        success = live->replan(*candidate, uint64_t(frames) * 3 * 1000000000 / 48000);
        done.store(true, std::memory_order_release);
    });
    bool identical = true;
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    do {
        {
            allocation_watch::ThreadScope watch;
            CHECK(live->render(out, 2, frames) == WS2_OK);
            CHECK(watch.allocations() == 0);
        }
        for (float sample : witness) identical &= sample == held;
        std::this_thread::yield();
    } while (!done.load(std::memory_order_acquire) && Clock::now() < deadline);
    control.join();
    CHECK(success.load());
    candidate.reset();
    CHECK(live->render(out, 2, frames) == WS2_OK);
    for (float sample : witness) identical &= sample == held;
    CHECK(identical);
}

// A51 regression: the actual output-less OSC Out holds a host-owned bus.
// On successful adoption the host is allowed to free that bus immediately.
// A new signal cable ramps for exactly 5 ms. Reverse the edit while the
// first ramp is still moving, and require the new ramp to start at its actual
// previous sample, rather than jumping to the first ramp's target.
static void signal_ramp_interrupted() {
    auto make = [](bool connected) {
        auto e = std::make_unique<Engine>(config());
        CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
        CHECK(e->add_node(2, ws::Module<Pass>::descriptor()));
        if (connected) CHECK(e->connect(1, 0, 2, 0));
        CHECK(e->output(2, 0, 0));
        CHECK(e->output(1, 0, 1));
        CHECK(e->register_producer() == 0);
        CHECK(e->prepare());
        return e;
    };
    auto live = make(false), add = make(true), remove = make(false);
    CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    float sample[1]{}, witness[1]{};
    float *out[]{sample, witness};
    auto render = [&] {
        allocation_watch::ThreadScope watch;
        CHECK(live->render(out, 2, 1) == WS2_OK);
        CHECK(watch.allocations() == 0);
        CHECK(witness[0] == .75f);
    };
    render();
    CHECK(sample[0] == 0);
    auto edit_until = [&](Engine &candidate, auto changed) {
        std::atomic<bool> done{false}, success{false};
        std::thread control([&] {
            success = live->replan(candidate, uint64_t(frames) * 3 * 1000000000 / 48000);
            done.store(true, std::memory_order_release);
        });
        bool observed = false;
        uint64_t max_sleep_us = 0;
        unsigned paced_waits = 0;
        const auto deadline = Clock::now() + std::chrono::seconds(2);
        do {
            const float previous = sample[0];
            render();
            if (changed(previous, sample[0])) {
                observed = true;
                break;
            }
            // Pace single-sample callbacks so staging cannot consume the
            // entire 240-frame ramp before a reversal is requested.
            const auto wait_start = Clock::now();
            // Test-only short wait: do not round 100us to the host timer tick.
            const auto next_callback = wait_start + std::chrono::microseconds(100);
            while (Clock::now() < next_callback) {}
            const auto wait_us = uint64_t(std::chrono::duration_cast<std::chrono::microseconds>(
                Clock::now() - wait_start).count());
            max_sleep_us = std::max(max_sleep_us, wait_us);
            ++paced_waits;
        } while (!done.load(std::memory_order_acquire) && Clock::now() < deadline);
        control.join();
        std::fprintf(stderr, "#443 pacing: waits=%u max_wait_us=%llu adoption=%s error=%s\n",
                     paced_waits, static_cast<unsigned long long>(max_sleep_us),
                     success.load() ? "ok" : "failed", live->error().c_str());
        CHECK(success.load());
        CHECK(observed);
    };
    edit_until(*add, [](float, float next) { return next > 0; });
    CHECK(std::abs(sample[0] - .75f / 240) < 1.e-6f);
    add.reset();
    for (unsigned i = 0; i < 59; ++i) render();
    CHECK(std::abs(sample[0] - .75f / 4) < 1.e-6f);
    float turn = 0;
    edit_until(*remove, [&](float prior, float next) {
        if (next >= prior) return false;
        turn = prior;
        return true;
    });
    CHECK(turn > 0 && turn < .75f);
    CHECK(std::abs(sample[0] - turn * (239.f / 240)) < 1.e-6f);
    remove.reset();
    for (unsigned i = 1; i < 240; ++i) render();
    CHECK(sample[0] == 0);

    // E5 Low: a settled layout can be waiting for housekeeping when the
    // audio stream stops. At most the first refresh may wait a full
    // publication deadline; unchanged-position status ticks must not stall.
    const auto stopped_frame = live->meter().frame;
    live->refresh_latency();
    constexpr unsigned stopped_ticks = 8;
    const auto bound = std::chrono::nanoseconds(uint64_t(frames) * 3 * 1000000000 / 48000);
    const auto start = Clock::now();
    for (unsigned i = 0; i < stopped_ticks; ++i) live->refresh_latency();
    const auto elapsed = Clock::now() - start;
    CHECK(live->meter().frame == stopped_frame);
    // Aggregate wall-clock margin: the defect waits >= 8 deadlines; allow
    // four deadlines for hosted scheduling noise on the nonwaiting path.
    CHECK(elapsed < 4 * bound);

    // Resume callbacks before attempting housekeeping again. It must be
    // silent on the wire and must not resurrect the removed cable or
    // retire the live witness.
    render();
    CHECK(sample[0] == 0);
    std::atomic<bool> done{false};
    std::thread control([&] {
        live->refresh_latency();
        done.store(true, std::memory_order_release);
    });
    do {
        render();
        CHECK(sample[0] == 0);
        std::this_thread::yield();
    } while (!done.load(std::memory_order_acquire));
    control.join();
    render();
    CHECK(sample[0] == 0);
}

static void osc_out_retirement() {
    using namespace wirescape::osc;
    for (bool replacement : {false, true}) {
        auto old_bus = std::make_unique<OutBus>();
        auto new_bus = std::make_unique<OutBus>();
        auto make = [&](OutBus *bus) {
            auto e = std::make_unique<Engine>(config());
            CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
            if (bus) {
                OutConfiguration cfg;
                cfg.bus = bus;
                cfg.rows[0].enabled = 1;
                const auto *bytes = reinterpret_cast<const uint8_t *>(&cfg);
                CHECK(e->add_node(2, ws::Module<OscOut>::descriptor(),
                                  std::vector<uint8_t>(bytes, bytes + sizeof(cfg))));
                CHECK(e->connect(1, 0, 2, 0));
            }
            CHECK(e->output(1, 0, 0));
            CHECK(e->register_producer() == 0);
            CHECK(e->prepare());
            return e;
        };
        auto live = make(old_bus.get());
        auto candidate = make(replacement ? new_bus.get() : nullptr);
        CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
        float data[frames]{};
        float *out[]{data};
        CHECK(live->render(out, 1, frames) == WS2_OK);
        CHECK(old_bus->rows[0].blocks.load() > 0);
        replan_with_callbacks(*live, *candidate);
        candidate.reset();
        old_bus.reset(); // ASan detects any later access by the retired instance.
        for (unsigned i = 0; i < 8; ++i) {
            allocation_watch::ThreadScope watch;
            CHECK(live->render(out, 1, frames) == WS2_OK);
            CHECK(watch.allocations() == 0);
            for (float sample : data) CHECK(sample == .75f);
        }
        CHECK((live->descriptor(2) != nullptr) == replacement);
        if (replacement) CHECK(new_bus->rows[0].blocks.load() > 0);
    }
}

static void allocation_scope_is_thread_local() {
    std::atomic<bool> go{false}, done{false};
    std::thread control([&] {
        while (!go.load()) std::this_thread::yield();
        auto *p = ::operator new(19);
        ::operator delete(p);
        done = true;
    });
    {
        allocation_watch::ThreadScope watch;
        go = true;
        while (!done.load()) std::this_thread::yield();
        CHECK(watch.allocations() == 0);
        auto *p = ::operator new(23);
        CHECK(watch.allocations() == 1);
        ::operator delete(p);
    }
    control.join();
}
static void counted_target_rejection() {
    auto e = graph({false, true, false});
    const auto before = e->meter();
    CHECK(e->enqueue(0, 99, 0, note(), 0, Timing::Immediate) == WS2_OK);
    CHECK(e->enqueue(0, 1, 9, note(), 0, Timing::Immediate) == WS2_OK);
    auto parameter = note();
    parameter.type = WS2_PARAM;
    parameter.index = 9;
    parameter.value = .5f;
    CHECK(e->enqueue(0, 1, WS2_DIRECT_PORT, parameter, 0, Timing::Immediate) == WS2_OK);
    parameter.index = 0;
    parameter.value = 2;
    CHECK(e->enqueue(0, 1, WS2_DIRECT_PORT, parameter, 0, Timing::Immediate) == WS2_OK);
    float a[frames]{}, b[frames]{}, c[frames]{};
    float *out[]{a, b, c};
    {
        allocation_watch::ThreadScope watch;
        CHECK(e->render(out, 3, frames) == WS2_OK);
        CHECK(watch.allocations() == 0);
    }
    CHECK(e->meter().stale == before.stale + 1);
    CHECK(e->meter().dropped == before.dropped + 3);
    CHECK(e->meter().events == before.events);
}
static void feedback_delay_survives() {
    auto cfg = config();
    cfg.feedback_block = 1;
    auto make = [&](bool additional) {
        auto e = std::make_unique<Engine>(cfg);
        CHECK(e->add_node(1, ws::Module<Feedback>::descriptor()));
        CHECK(e->connect(1, 0, 1, 0));
        CHECK(e->output(1, 0, 0));
        if (additional) CHECK(e->add_node(2, ws::Module<Pass>::descriptor()));
        CHECK(e->prepare());
        return e;
    };
    auto live = make(false), candidate = make(true);
    const auto generation = live->meter().generation;
    float data[frames]{};
    float *out[]{data};
    auto render = [&] {
        allocation_watch::ThreadScope watch;
        CHECK(live->render(out, 1, frames, now_ns()) == WS2_OK);
        CHECK(watch.allocations() == 0);
    };
    for (unsigned i = 0; i < 4; ++i) render();
    float previous = data[frames - 1];
    auto contiguous = [&] {
        render();
        CHECK(data[0] == previous + 1);
        CHECK(data[frames - 1] == previous + frames);
        previous = data[frames - 1];
    };
    std::atomic<bool> done{false}, success{false};
    std::thread edit([&] {
        success = live->replan(*candidate, uint64_t(frames) * 3 * 1000000000 / 48000);
        done = true;
    });
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    while (!done.load() && Clock::now() < deadline) {
        contiguous();
        std::this_thread::yield();
    }
    edit.join();
    CHECK(success.load());
    candidate.reset();
    contiguous();
    CHECK(live->meter().generation == generation);
    CHECK(live->feedback_edges() == 1);
}
static void ramp_survives() {
    auto live = graph({false, true, false}), reference = graph({false, true, false});
    auto candidate = graph({true, true, false});
    float a[1]{}, b[1]{}, x[1]{}, y[1]{};
    float *out[]{a, b}, *expected[]{x, y};
    auto render = [&] {
        allocation_watch::ThreadScope watch;
        CHECK(live->render(out, 2, 1) == WS2_OK);
        CHECK(reference->render(expected, 2, 1) == WS2_OK);
        CHECK(watch.allocations() == 0);
    };
    for (auto *e : {live.get(), reference.get()}) CHECK(e->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    render(); // Start the host ramp before requesting automation.
    std::atomic<bool> done{false}, success{false};
    std::thread edit([&] {
        success = live->replan(*candidate, uint64_t(frames) * 3 * 1000000000 / 48000);
        done = true;
    });
    auto gain = note();
    gain.type = WS2_PARAM;
    gain.channel = -1;
    gain.index = 0;
    unsigned callbacks = 0;
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    while (!done.load() && Clock::now() < deadline) {
        gain.value = (++callbacks & 1) ? .25f : .75f; // Keep the ramp moving even while edit staging runs.
        for (auto *e : {live.get(), reference.get()})
            CHECK(e->enqueue(0, 1, WS2_DIRECT_PORT, gain, 0, Timing::Immediate) == WS2_OK);
        render();
        CHECK(b[0] == y[0]); // Every callback must match the untouched reference.
        std::this_thread::yield();
    }
    edit.join();
    CHECK(success.load());
    CHECK(callbacks > 0);
    candidate.reset();
    CHECK(live->output_sample(1, 0, 0, 0) == reference->output_sample(1, 0, 0, 0));
    render();
    CHECK(live->output_sample(1, 0, 0, 0) == reference->output_sample(1, 0, 0, 0));
    CHECK(b[0] == y[0]);
}
static unsigned replan_attempts = 3, replan_timeouts = 0;
static double live_edits() {
    auto live = graph({false, true, true});
    auto &e = *live;
    const auto generation = e.meter().generation;
    CHECK(e.enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    ws2_event gain{};
    gain.struct_size = sizeof(gain);
    gain.type = WS2_PARAM;
    gain.channel = -1;
    gain.index = 0;
    gain.value = .5f;
    CHECK(e.enqueue(0, 1, WS2_DIRECT_PORT, gain, 0, Timing::Immediate) == WS2_OK);
    Audio audio(e);
    audio.wait(.75f, .375f);
    audio.measure = true;
    std::atomic<bool> producing{true};
    std::atomic<uint64_t> accepted{0};
    std::thread producer([&] {
        auto mod = gain;
        mod.type = WS2_PARAM_MOD;
        mod.value = 0;
        while (producing.load()) {
            auto r = e.enqueue(1, 1, WS2_DIRECT_PORT, mod, 0, Timing::Immediate);
            CHECK(r == WS2_OK || r == WS2_CAPACITY);
            if (r == WS2_OK) ++accepted;
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    });
    // Keel ruling #297: every attempt keeps the full three-block adoption deadline. A timeout is a legal outcome
    // (old graph retained, then a bounded retry, as the sidecar does under D5/D7). Strict mode (Pi evidence via
    // --max-gap-ms, or WIRESCAPE_REPLAN_STRICT=1) still requires every edit to commit on its first attempt.
    auto edit = [&](Topology topology) {
        const auto before = audio.blocks.load();
        bool committed = false;
        for (unsigned attempt = 0; attempt < replan_attempts && !committed; ++attempt) {
            auto next = graph(topology);
            const auto old_generation = e.meter().generation;
            const auto started = now_ns();
            committed = e.replan(*next, uint64_t(frames) * 3 * 1000000000 / 48000);
            next.reset(); // No render callback may retain a staging owner/context.
            if (!committed) {
                const auto error = e.error();
                CHECK(error == "Audio did not adopt before the edit deadline");
                ++replan_timeouts;
                std::fprintf(stderr, "replan attempt %u timed out after %.3f ms, %llu callbacks: %s\n", attempt + 1,
                             double(now_ns() - started) / 1000000.,
                             static_cast<unsigned long long>(audio.blocks.load() - before), error.c_str());
                CHECK(e.meter().generation == old_generation); // A timeout retains the old graph.
                CHECK(e.meter().faults == 0);
                // Allow callbacks to resume before retry; an unclaimed cancellation needs no retirement.
                const auto retired = audio.blocks.load();
                const auto retire_deadline = Clock::now() + std::chrono::seconds(2);
                while (audio.blocks.load() <= retired + 1 && Clock::now() < retire_deadline) std::this_thread::yield();
                CHECK(audio.blocks.load() > retired + 1);
            }
        }
        CHECK(committed);
        const auto deadline = Clock::now() + std::chrono::seconds(2);
        while (audio.blocks.load() < before + 3 && Clock::now() < deadline) std::this_thread::yield();
        CHECK(audio.blocks.load() >= before + 3);
        CHECK(e.meter().generation == generation);
    };
    edit({true, true, true});
    audio.wait(.75f, .375f); // Add and connect without resetting held DSP/ramp state.
    edit({false, true, true});
    audio.wait(.75f, .375f); // Disconnect and remove the signal pass.
    const auto future = e.meter().frame + uint64_t(frames) * 40;
    CHECK(e.enqueue(0, 4, 0, note(WS2_NOTE_ON, .25f), future, Timing::Frames) == WS2_OK);
    const auto stale = e.meter().stale;
    edit({false, true, false});
    edit({false, true, true}); // Numeric ID reuse cannot resurrect the removed node's future note.
    const auto deadline = Clock::now() + std::chrono::seconds(2);
    while (e.meter().frame < future + uint64_t(frames) * 2 && Clock::now() < deadline) std::this_thread::yield();
    CHECK(e.meter().frame >= future + uint64_t(frames) * 2);
    CHECK(audio.fourth.load() == 0);
    CHECK(e.meter().stale > stale);
    edit({false, false, true});
    audio.wait(0, .375f); // Removed event edge chokes former destination, not unrelated source.
    edit({false, true, true});
    CHECK(e.enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    audio.wait(.75f, .375f);
    audio.pause();
    auto next = graph({true, true, true});
    const auto before = e.meter();
    CHECK(!e.replan(*next, 1000000));
    CHECK(e.meter().generation == before.generation);
    CHECK(e.meter().frame == before.frame);
    const auto paused_blocks = audio.blocks.load();
    audio.resume();
    const auto resumed_deadline = Clock::now() + std::chrono::seconds(2);
    while (audio.blocks.load() == paused_blocks && Clock::now() < resumed_deadline) std::this_thread::yield();
    CHECK(audio.blocks.load() > paused_blocks);
    audio.wait(.75f, .375f); // Timeout retains the old graph and resumes it.
    edit({true, true, true});
    audio.wait(.75f, .375f); // A cancelled request cannot poison a subsequent acknowledged edit.
    bool has_pass = true;
    for (unsigned attempt = 0; attempt < 8; ++attempt) {
        auto racing = graph({!has_pass, true, true});
        if (e.replan(*racing, 1)) has_pass = !has_pass; // Either CAS winner is valid; only an ack permits mutation.
        racing.reset();
        audio.pause();
        CHECK((e.descriptor(3) != nullptr) == has_pass);
        CHECK(e.meter().generation == generation);
        const auto block = audio.blocks.load();
        audio.resume();
        const auto deadline = Clock::now() + std::chrono::seconds(2);
        while (audio.blocks.load() == block && Clock::now() < deadline) std::this_thread::yield();
        CHECK(audio.blocks.load() > block);
        audio.wait(.75f, .375f);
    }
    producing = false;
    producer.join();
    CHECK(accepted.load() > 0);
    CHECK(e.meter().generation == generation);
    CHECK(e.meter().faults == 0);
    CHECK(audio.gap_ns.load() == 0);
    audio.measure = false;
    CHECK(e.enqueue(0, 1, 0, note(WS2_NOTE_OFF, 0), 0, Timing::Immediate) == WS2_OK);
    audio.wait(0, 0);
    return double(audio.gap_ns.load()) / 1000000.;
}
static void telemetry_replan_layout() {
    auto live=graph({false,false,false},{{Tap::Param,1,0},{Tap::EventOut,1,1}});
    auto kept=graph({false,false,false},{{Tap::Param,1,0}});
    auto removed=std::make_unique<Engine>(config());
    CHECK(removed->add_node(2,ws::Module<Voice>::descriptor()));
    CHECK(removed->output(2,0,0));
    CHECK(removed->set_telemetry_taps({}));
    CHECK(removed->register_producer()==0);
    CHECK(removed->register_producer()==1);
    CHECK(removed->prepare());
    CHECK(live->enqueue(0,1,0,note(),0,Timing::Immediate)==WS2_OK);
    float a[frames]{},b[frames]{};float*out[]{a,b};
    CHECK(live->render(out,2,frames)==WS2_OK);
    CHECK(b[frames-1]>.1f);
    float values[2]{};uint32_t counts[2]{};uint64_t frame=0;
    CHECK(live->read_telemetry(values,counts,2,frame)==2&&counts[1]==1&&frame==frames);
    replan_with_callbacks(*live,*kept);
    kept.reset();
    CHECK(live->render(out,2,frames)==WS2_OK);
    CHECK(live->read_telemetry(values,counts,2,frame)==1&&frame==live->meter().frame);
    CHECK(values[0]==.75f || values[0]==1.f); // Retained node's rendered gain.
    replan_with_callbacks(*live,*removed);
    removed.reset();
    CHECK(live->render(out,2,frames)==WS2_OK);
    CHECK(live->read_telemetry(values,counts,2,frame)==0&&frame==0);
    CHECK(live->descriptor(1)==nullptr); // Removed nodes cannot retain a stale tap.
}
// Device-free random valid topology stress. Render, control and independent
// ingress producer run concurrently; count successful edits, not attempts.
static void random_edit_stress(unsigned count) {
    auto cfg = config();
    cfg.max_channels = 1;
    cfg.max_nodes = 8;
    cfg.max_block = 1024;
    auto make = [&](uint32_t mask) {
        auto e = std::make_unique<Engine>(cfg);
        CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
        CHECK(e->add_node(2, ws::Module<Pass>::descriptor()));
        CHECK(e->add_node(4, ws::Module<Voice>::descriptor()));
        if (mask & 1) {
            CHECK(e->add_node(3, ws::Module<Pass>::descriptor()));
            CHECK(e->connect((mask & 2) ? 2 : 1, 0, 3, 0));
        }
        if ((mask & 1) && (mask & 4)) CHECK(e->connect(3, 0, 2, 0));
        else if (mask & 8) CHECK(e->connect(1, 0, 2, 0));
        if (mask & 16) CHECK(e->connect(1, 1, 4, 0));
        if (mask & 32) CHECK(e->modulate(2, 0, 4, 0, (mask & 64) ? .25f : -.25f));
        CHECK(e->output(2, 0, 0));
        CHECK(e->output(1, 0, 1));
        CHECK(e->output(4, 0, 2));
        CHECK(e->register_producer() == 0);
        CHECK(e->register_producer() == 1);
        if (mask & 128) CHECK(e->set_telemetry_taps({{Tap::Param, 4, 0}, {Tap::Output, 1, 0}}));
        CHECK(e->prepare());
        return e;
    };
    auto live = make(0);
    CHECK(live->enqueue(0, 1, 0, note(), 0, Timing::Immediate) == WS2_OK);
    const auto generation = live->meter().generation;
    std::atomic<bool> run{true}, started{false};
    std::thread render([&] {
        float a[32]{}, b[32]{}, c[32]{};
        float *out[]{a, b, c};
        while (run.load(std::memory_order_acquire)) {
            {
                allocation_watch::ThreadScope watch;
                CHECK(live->render(out, 3, 32) == WS2_OK);
                CHECK(watch.allocations() == 0);
            }
            for (float sample : b) CHECK(sample == .75f);
            for (float sample : a) CHECK(std::isfinite(sample));
            for (float sample : c) CHECK(std::isfinite(sample));
            Outgoing event;
            while (live->pop_egress(event)) {}
            started.store(true, std::memory_order_release);
            std::this_thread::yield();
        }
    });
    std::thread ingress([&] {
        auto event = note();
        event.type = WS2_PARAM_MOD;
        event.index = 0;
        event.value = .125f;
        while (run.load(std::memory_order_acquire)) {
            const int status = live->enqueue(1, 4, WS2_DIRECT_PORT, event, 0, Timing::Immediate);
            CHECK(status == WS2_OK || status == WS2_CAPACITY);
            std::this_thread::sleep_for(std::chrono::microseconds(100));
        }
    });
    while (!started.load(std::memory_order_acquire)) std::this_thread::yield();
    std::mt19937 random(0xE4B2026u);
    unsigned timeouts = 0;
    for (unsigned i = 0; i < count; ++i) {
        const uint32_t mask = random() & 255u;
        auto candidate = make(mask);
        bool committed = false;
        for (unsigned attempt = 0; attempt < 20 && !committed; ++attempt) {
            committed = live->replan(*candidate, uint64_t(cfg.max_block) * 3 * 1000000000 / 48000);
            if (!committed) {
                CHECK(live->error() == "Audio did not adopt before the edit deadline");
                ++timeouts;
            }
        }
        CHECK(committed);
        candidate.reset();
        CHECK(live->meter().generation == generation);
        CHECK(live->meter().faults == 0);
        CHECK((live->descriptor(3) != nullptr) == bool(mask & 1));
        if (mask & 32) {
            const int status = live->set_mod_amount(2, 0, 4, 0, .5f);
            CHECK(status == WS2_OK || status == WS2_CAPACITY);
        }
        float values[2]{};
        uint32_t counts[2]{};
        uint64_t frame = 0;
        CHECK(live->read_telemetry(values, counts, 2, frame) == ((mask & 128) ? 2u : 0u));
        if (i % 3 == 0) live->refresh_latency();
    }
    run.store(false, std::memory_order_release);
    ingress.join();
    render.join();
    CHECK(live->meter().faults == 0);
    std::printf("PASS E4b random valid edits: %u committed, %u cancelled attempts, generation unchanged, no render allocations\n", count, timeouts);
}
int main(int argc, char **argv) {
    if (argc == 3 && std::strcmp(argv[1], "--stress") == 0) {
        const unsigned count = static_cast<unsigned>(std::strtoul(argv[2], nullptr, 10));
        CHECK(count >= 10000);
        random_edit_stress(count);
        return 0;
    }
    double max_gap_ms = 0;
    if (argc == 3 && std::strcmp(argv[1], "--max-gap-ms") == 0) max_gap_ms = std::strtod(argv[2], nullptr);
    else CHECK(argc == 1);
    const char *strict = std::getenv("WIRESCAPE_REPLAN_STRICT");
    if (max_gap_ms > 0 || (strict && std::strcmp(strict, "1") == 0)) replan_attempts = 1;
    untouched_witness_no_dip();
    osc_out_retirement();
    signal_ramp_interrupted();
    replacement_ring_out();
    replacement_adopt();
    replacement_ring_out(7, 336, true);
    replacement_ring_out(1000, 24000, false, true);
    allocation_scope_is_thread_local();
    counted_target_rejection();
    removed_event_routes_release();
    telemetry_replan_layout();
    feedback_delay_survives();
    ramp_survives();
    const auto gap = live_edits();
    std::printf("PASS live add/connect/disconnect/remove, state/release/ingress/cancel/noalloc; 256-frame gap %.3f ms; "
                "replan timeouts retried %u (%s)\n",
                gap, replan_timeouts, replan_attempts == 1 ? "strict" : "hosted: bounded retry");
    if (max_gap_ms > 0) CHECK(gap <= max_gap_ms);
}
