// SPDX-License-Identifier: GPL-3.0-only
// OB-g8 #326: a bounded localhost-only, device-off OSC ingress reproduction.
// Run the real Host/Service/Engine path beneath bench/io, with the same L0
// 64-address x 200 Hz load and an independent numbered 10 Hz gate sentinel.
// This is intentionally a failing-first regression: do not weaken 50 ms or
// zero route drops to make the historical failure disappear.
#include "../../sdk/examples/test_support.h"
#include "../../engine/control/monitor_capture.h"
#include "../../engine/control/osc_host.h"
#include "../osc/codec.h"
#include "osc_service.h"
#include "runtime_patch.h"
#include <nlohmann/json.hpp>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <memory>
#include <string>
#include <thread>
#include <vector>
#ifdef _WIN32
#include <winsock2.h>
#else
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace {
using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
using namespace std::chrono_literals;

// Windows' default sleep timer is often ~15ms; sleeping for 200us silently
// lowers this load to ~64Hz/address. Yield instead of altering the required
// 200Hz profile. The CI test remains bounded to 400ms of input traffic.
void wait_for_callback(Clock::time_point deadline) {
#ifdef _WIN32
    while (Clock::now() < deadline) std::this_thread::yield();
#else
    std::this_thread::sleep_until(deadline);
#endif
}
// Reserve an OS-assigned port rather than colliding with another CI process.
// Host validates a nonzero configured OSC port, so release the reservation
// immediately before its loopback-only listener starts.
uint16_t loopback_port() {
    wirescape::osc::Service probe({});
    REQUIRE(probe.add({1, 0, false}) && probe.start());
    REQUIRE(probe.counters().sockets == 1);
    const auto port = probe.bound_port();
    probe.stop();
    REQUIRE(port != 0);
    return port;
}

json row(const std::string &pattern, const char *kind) {
    return {{"pattern", pattern}, {"argument", 0}, {"kind", kind},
            {"input_min", 0}, {"input_max", 1}, {"output_min", 0},
            {"output_max", 1}, {"smoothing_ms", 0}, {"timeout_ms", 0},
            {"stale", "hold"}};
}

json heavy_patch(uint16_t port) {
    json patch = {{"format", "wirescape.native.patch"}, {"version", 2}};
    patch["settings"] = {{"sample_rate", 48000}, {"max_block_frames", 128},
                         {"max_channels", 16}, {"seed", 305}};
    patch["modules"] = json::array();
    patch["connections"] = json::array();
    patch["outputs"] = json::array();
    patch["outputs"].push_back({{"module", 90}, {"port", "audio"}, {"bus_channel", 0}});
    auto add_input = [&](int id, const json &rows) {
        patch["modules"].push_back({{"id", id}, {"module", "osc.in"}, {"version", 1},
            {"config", {{"version", 1}, {"port", port}, {"lan", false}, {"rows", rows}}}});
    };
    json sentinel = json::array();
    sentinel.push_back(row("/io/seq", "cv"));
    sentinel.push_back(row("/io/gate", "gate"));
    add_input(1, sentinel);
    for (int group = 0; group < 8; ++group) {
        json rows = json::array();
        for (int i = 0; i < 8; ++i) {
            const int index = group * 8 + i;
            char address[32]{};
            std::snprintf(address, sizeof(address), "/io/load/%02d", index);
            rows.push_back(row(address, (index & 1) ? "gate" : "cv"));
        }
        add_input(10 + group, rows);
    }
    patch["modules"].push_back({{"id", 90}, {"module", "essentials.output"}, {"version", 2}});
    return patch;
}

// Observe only *successfully enqueued* sentinel events. A control ACK or an
// accepted UDP send alone is not evidence that a falling gate reached the DSP.
json sentinel_monitor_patch() {
    json patch;
    patch["modules"] = json::array();
    patch["modules"].push_back({{"id", 1}, {"module", "osc.in"}});
    patch["modules"].push_back({{"id", 100}, {"module", "monitor"}});
    patch["connections"] = json::array();
    patch["connections"].push_back({
        {"kind", "event"},
        {"from", {{"module", 1}, {"port", "messages"}}},
        {"to", {{"module", 100}, {"port", "events"}}}
    });
    return patch;
}

void reproduce(bool panic_only) {
    const auto port = loopback_port();
    const json patch = heavy_patch(port);
    wirescape::engine2::Config config{};
    config.sample_rate = 48000;
    config.max_block = 128;
    config.max_channels = 16;
    config.max_nodes = 64;
    config.event_budget = 2048;
    config.ring_capacity = 256; // production bound, not an artificially unbounded sink
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> catalog(
        app_engine_create(&config), app_engine_destroy);
    REQUIRE(bool(catalog));
    std::string error;
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(
        wirescape::document::load_runtime_patch(patch.dump(), catalog.get(), config, error),
        app_engine_destroy);
    if (!engine) std::fprintf(stderr, "OB-g8 graph load: %s\n", error.c_str());
    REQUIRE(bool(engine));

    wirescape::monitor::Capture monitor;
    // Capture::Entry::t is measured against its internal steady-clock epoch.
    // Bracket the configure call so we can compare actual *ingress timestamps*
    // with the sender's gate-fall send times. JSON polling latency must not be
    // mistaken for native queue latency, especially under ASan/UBSan.
    monitor.configure(sentinel_monitor_patch());
    const auto epoch_after = Clock::now();
    wirescape::osc::Host host;
    host.observe(&monitor);
    host.start(engine.get(), patch.dump());
    const auto initial = host.states();
    REQUIRE(initial.size() == 9);
    for (const auto &route : initial) REQUIRE(std::string(route.state) == "listening");

    const auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in destination{};
    destination.sin_family = AF_INET;
    destination.sin_port = htons(port);
    destination.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    auto send_osc = [&](const std::string &address, float value) {
        wirescape::osc::Message m;
        m.address = address;
        m.count = 1;
        m.arguments[0].type = 'f';
        m.arguments[0].real = value;
        uint8_t bytes[1472]{};
        bool truncated = false;
        const auto size = wirescape::osc::encode(m, bytes, sizeof(bytes), truncated);
        return size && !truncated &&
            sendto(sender, reinterpret_cast<const char *>(bytes), int(size), 0,
                   reinterpret_cast<sockaddr *>(&destination), sizeof(destination)) == int(size);
    };

    if (panic_only) {
        auto &graph = app_engine_native(engine.get());
        const auto generation = app_engine_generation(engine.get());
        graph.panic();
        std::array<float, 128> output{};
        float *channels[] = {output.data()};
        REQUIRE(app_engine_render_live(engine.get(), channels, 1, 128, app_engine_clock_ns()) == WS2_OK);
        REQUIRE(app_engine_generation(engine.get()) != generation);
        REQUIRE(send_osc("/io/seq", .75f));
        const auto deadline = Clock::now() + 500ms;
        while (Clock::now() < deadline) {
            const auto route = host.states().front();
            if (route.received || route.dropped) break;
            std::this_thread::sleep_for(1ms);
        }
        const auto route = host.states().front();
        host.stop();
#ifdef _WIN32
        closesocket(sender);
#else
        close(sender);
#endif
        REQUIRE(route.received == 1 && route.dropped == 0);
        for (int block = 0; block < 2; ++block)
            REQUIRE(app_engine_render_live(engine.get(), channels, 1, 128, app_engine_clock_ns()) == WS2_OK);
        REQUIRE(graph.output_sample(1, 0, 0, 127) == .75f);
        return;
    }

    constexpr auto render_period = 2666667ns; // 128 frames at 48 kHz
    constexpr auto load_period = 5ms;
    std::atomic<bool> rendering{true};
    // Render-thread counters are read only after join.
    uint32_t render_failures = 0, render_blocks = 0;
    uint32_t render_late_starts = 0, render_long_calls = 0;
    Clock::duration render_max_interval{}, render_max_call{}, render_total_call{};
    Clock::duration render_max_lateness{}, render_max_wait_overshoot{};
    std::thread render([&] {
        std::array<float, 128> left{}, right{};
        float *out[] = {left.data(), right.data()};
        auto next = Clock::now(), previous_start = next, previous_end = next;
        while (rendering.load(std::memory_order_acquire)) {
            const auto started = Clock::now();
            const auto lateness = started - next;
            render_max_lateness = (std::max)(render_max_lateness, lateness);
            render_late_starts += lateness >= render_period;
            if (render_blocks) {
                render_max_interval = (std::max)(render_max_interval, started - previous_start);
                render_max_wait_overshoot = (std::max)(render_max_wait_overshoot,
                    started - (std::max)(next, previous_end));
            }
            const int result = app_engine_render_live(engine.get(), out, 2, 128, app_engine_clock_ns());
            const auto finished = Clock::now();
            const auto duration = finished - started;
            render_max_call = (std::max)(render_max_call, duration);
            render_total_call += duration;
            render_long_calls += duration >= render_period;
            render_failures += result != WS2_OK;
            ++render_blocks;
            previous_start = started;
            previous_end = finished;
            next += render_period;
            wait_for_callback(next);
        }
    });
    std::vector<Clock::time_point> sent_falls;
    size_t seen_falls = 0, seen_sequences = 0, sent_load = 0, sent_sequences = 0;
    bool sender_ok = true, fall_late = false;
    double worst_fall_ms = 0.;
    uint32_t early_falls = 0, late_falls = 0;
    // Read the fixed 32-entry ingress monitor *after* the bounded send window.
    // Frequent monitor.snapshot() JSON allocation during the 200Hz sender loop
    // previously consumed a large fraction of CPU under sanitizers, turning
    // the diagnostic collector itself into an extra load producer. The true
    // ingress timestamp is still checked against 50ms, without forgiveness.
    const auto observe = [&] {
        const auto samples = monitor.snapshot();
        if (!samples.contains("100")) return;
        double previous = -1;
        for (const auto &e : samples.at("100")) {
            const double when = e.at("t").get<double>();
            if (when < previous) { fall_late = true; continue; }
            previous = when;
            const auto address = e.value("address", std::string{});
            const auto &args = e.at("args");
            if (args.empty()) continue;
            if (address == "/io/seq") {
                ++seen_sequences;
                if (seen_sequences > sent_sequences ||
                    std::abs(args.at(0).get<double>() -
                             double(seen_sequences) / 4096.) > 1e-6)
                    fall_late = true; // the gate sentinel must be numbered
            }
            if (address != "/io/gate" || args.at(0).get<double>() >= 0.5) continue;
            if (seen_falls < sent_falls.size()) {
                const auto received_by = epoch_after +
                    std::chrono::duration_cast<Clock::duration>(
                        std::chrono::duration<double>(when));
                const auto latest_ms = std::chrono::duration<double, std::milli>(
                    received_by - sent_falls[seen_falls]).count();
                worst_fall_ms = (std::max)(worst_fall_ms, latest_ms);
                if (latest_ms > 50.) { ++late_falls; fall_late = true; }
                // The monitor clock epoch is known only within the
                // configure() bracket. An ingress is *proven* early only
                // when even its latest possible time precedes sendto.
                // Checking the earliest bound rejected valid immediate
                // loopback deliveries while leaving the 50ms upper bound
                // unchanged.
                if (received_by < sent_falls[seen_falls]) {
                    ++early_falls;
                    fall_late = true;
                } // unchanged strict 50ms, actual ingress timestamps
                ++seen_falls;
            } else fall_late = true;
        }
    };

    auto &graph = app_engine_native(engine.get());
    const auto drain_egress = [&] {
        // Mirror the sidecar's bounded control-thread drain. The render
        // thread remains the producer and this thread is the sole consumer.
        wirescape::engine2::Outgoing message;
        for (unsigned i = 0; i < 256 && graph.pop_egress(message); ++i) {}
    };
    const auto start = Clock::now(), end = start + 400ms;
    auto next_load = start, next_sequence = start, next_fall = end + 1s;
    Clock::time_point previous_load{};
    Clock::duration load_max_lateness{}, load_max_send{}, gate_max_lateness{}, sequence_max_lateness{};
    auto load_min_interval = (Clock::duration::max)();
    uint32_t load_overdue = 0, load_short_intervals = 0;
    size_t load_cycle = 0;
    bool fall_pending = false;
    while (Clock::now() < end) {
        drain_egress();
        const auto now = Clock::now();
        if (now >= next_sequence) {
            // A unique sequence identifies each 100 ms sentinel cycle.
            sequence_max_lateness = (std::max)(sequence_max_lateness, now - next_sequence);
            ++sent_sequences;
            sender_ok &= send_osc("/io/seq", float(sent_sequences) / 4096);
            sender_ok &= send_osc("/io/gate", 1.f);
            next_fall = now + 20ms;
            fall_pending = true;
            next_sequence += 100ms;
        }
        if (fall_pending && now >= next_fall) {
            // Record the scheduled fall before sendto: a localhost UDP worker
            // can enqueue the datagram before sendto returns. Sampling after
            // sendto incorrectly calls an actually on-time fall "too early".
            const auto fall_sent_at = Clock::now();
            gate_max_lateness = (std::max)(gate_max_lateness, fall_sent_at - next_fall);
            sender_ok &= send_osc("/io/gate", 0.f);
            sent_falls.push_back(fall_sent_at);
            fall_pending = false;
        }
        if (now >= next_load && load_cycle < 80) {
            const auto load_started = Clock::now();
            const auto lateness = load_started - next_load;
            load_max_lateness = (std::max)(load_max_lateness, lateness);
            load_overdue += lateness >= load_period;
            if (load_cycle) {
                const auto interval = load_started - previous_load;
                load_min_interval = (std::min)(load_min_interval, interval);
                load_short_intervals += interval < load_period / 2;
            }
            previous_load = load_started;
            // Match the L0 harness: one datagram per address per 5ms cycle.
            for (unsigned i = 0; i < 64; ++i) {
                char address[32]{};
                std::snprintf(address, sizeof(address), "/io/load/%02u", i);
                const float value = (i & 1)
                    ? float((load_cycle + i) % 2)
                    : float((load_cycle + i * 17) % 97) / 96.f;
                sender_ok &= send_osc(address, value);
                ++sent_load;
            }
            load_max_send = (std::max)(load_max_send, Clock::now() - load_started);
            ++load_cycle;
            next_load += load_period;
        }
        auto wake = (std::min)(end, (std::min)(next_load, next_sequence));
        if (fall_pending) wake = (std::min)(wake, next_fall);
        wait_for_callback(wake);
    }
    // Drain accepted traffic and judge falls by their ingress timestamps.
    const auto witness_deadline = Clock::now() + 55ms;
    while (Clock::now() < witness_deadline) {
        drain_egress();
        std::this_thread::sleep_for(1ms);
    }
    observe();

    const auto states = host.states();
    uint64_t route_dropped = 0, route_received = 0;
    for (const auto &state : states) {
        route_dropped += state.dropped;
        route_received += state.received;
    }
    rendering.store(false, std::memory_order_release);
    render.join();
    const auto meter = app_engine_native(engine.get()).meter();
    host.stop();
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    std::fprintf(stderr,
        "OB-g8 device-off: 64x200Hz 400ms; load_sent=%zu seq=%zu falls=%zu observed=%zu "
        "route_received=%llu route_dropped=%llu render_errors=%u render_blocks=%u "
        "ring_full=%llu engine_dropped=%llu arena_full=%llu engine_events=%llu "
        "sender_ok=%d late=%d seq_seen=%zu worst_fall_ms=%.3f early_falls=%u late_falls=%u\n",
        sent_load, sent_sequences, sent_falls.size(), seen_falls,
        static_cast<unsigned long long>(route_received),
        static_cast<unsigned long long>(route_dropped),
        render_failures, render_blocks,
        static_cast<unsigned long long>(meter.ring_full),
        static_cast<unsigned long long>(meter.dropped),
        static_cast<unsigned long long>(meter.arena_full),
        static_cast<unsigned long long>(meter.events),
        int(sender_ok), int(fall_late), seen_sequences,
        worst_fall_ms, early_falls, late_falls);
    const auto ms = [](Clock::duration d) { return std::chrono::duration<double, std::milli>(d).count(); };
    std::fprintf(stderr,
        "OB-g8 timing ms: render_interval_max=%.3f render_call_max=%.3f render_call_total=%.3f "
        "render_start_late_max=%.3f render_wait_overshoot_max=%.3f "
        "render_starts_late_by_period=%u render_calls_over_period=%u\n",
        ms(render_max_interval), ms(render_max_call), ms(render_total_call), ms(render_max_lateness),
        ms(render_max_wait_overshoot), render_late_starts, render_long_calls);
    std::fprintf(stderr,
        "OB-g8 timing ms: load_interval_min=%.3f load_send_max=%.3f load_start_late_max=%.3f "
        "load_starts_late_by_period=%u load_intervals_under_half_period=%u "
        "sequence_send_late_max=%.3f gate_fall_send_late_max=%.3f\n",
        load_cycle > 1 ? ms(load_min_interval) : 0., ms(load_max_send), ms(load_max_lateness),
        load_overdue, load_short_intervals, ms(sequence_max_lateness), ms(gate_max_lateness));
    REQUIRE(sender_ok);
    REQUIRE(sent_sequences == 4 && sent_falls.size() == 4);
    REQUIRE(sent_load >= 64 * 70); // at least 350ms of the unaltered 200Hz profile
    REQUIRE(render_failures == 0);
    REQUIRE(seen_sequences == sent_sequences); // numbered independent sentinel
    REQUIRE(seen_falls == sent_falls.size() && !fall_late); // strict 50ms gate fall
    REQUIRE(route_dropped == 0); // never waive nonzero engine-route drops
    REQUIRE(route_received == sent_load + 3 * sent_sequences); // no unreceived UDP work
}
} // namespace

int main(int argc, char **) {
    reproduce(argc > 1);
    if (argc > 1) {
        std::puts("PASS OSC delivery after engine panic");
        return 0;
    }
    std::puts("PASS OB-g8 localhost OSC heavy ingress and numbered gate fall");
}
