// SPDX-License-Identifier: GPL-3.0-only
// Compile the real helper with Qt's keyword macro in scope, before session.h includes it.
#include <nlohmann/json.hpp>
#define slots
#include "../document/telemetry_taps.h"
#undef slots
#include "../audio/callback_render.h"
#include "../audio/portaudio_service.h"
#include "../../tests/native/abi2/allocation_watch.h"
#include "d5_gap_deadline.h"
#include "devices.h"
#include "../osc/codec.h"
#include "midi_service.h"
#include "null_sink_wait.h"
#include "runtime_patch.h"
#include "session.h"
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
using namespace wirescape::sidecar;
void check(bool ok) {
    if (!ok) throw std::runtime_error("sidecar unit assertion failed");
}
void midi_hotplug_observation() {
    using namespace wirescape::midi;
    ObservedMidi backend(true, false);
    const Endpoint m8{"M8 MIDI 1", "M8:M8 MIDI 1"}, pad{"Pad", "pad"};
    check(backend.set_fake_endpoints({m8, pad}));
    std::vector<ws2_event> events;
    events.reserve(16);
    Sink sink{&events, [](void* context, uint32_t, const ws2_event& event, uint64_t) noexcept -> int {
        static_cast<std::vector<ws2_event>*>(context)->push_back(event);
        return WS2_OK;
    }};
    Service service(backend, sink);
    check(service.enable({m8.name, m8.system_name}) && service.enable({pad.name, pad.system_name}));
    check(service.subscribe({1, {}, true}));
    const std::vector<Endpoint> remembered{m8, pad};
    auto listing = [&] { return midi_devices({backend.observed(), remembered}, true); };
    service.poll();
    backend.arm_learning(true);
    check(backend.learning() == Json({{"armed", true}}));
    uint8_t first_cc[]{0xB0, 21, 74};
    check(backend.inject(m8, first_cc, 3, app_engine_clock_ns()));
    check(backend.learning()["deviceId"] == "M8 MIDI 1|M8:M8 MIDI 1");
    auto initial = listing();
    check(initial.size() == 2 && initial[0]["enabled"] == true);
    const uint8_t a[]{0x90, 60, 100}, b[]{0x90, 62, 100};
    check(backend.inject(m8, a, 3, app_engine_clock_ns()));
    check(backend.inject(pad, b, 3, app_engine_clock_ns()));
    service.poll();
    check(backend.held() == Json::array({60, 62}));
    events.clear();
    check(backend.set_fake_endpoints({pad})); service.poll();
    check(listing() != initial && listing().size() == 1);
    check(backend.learning() == Json({{"armed", true}})); // removed slot cannot be remapped
    check(backend.held() == Json::array({62}));
    check(events.size() == 1 && events[0].type == WS2_NOTE_CHOKE && events[0].source_id == 1);
    check(service.endpoint_states()[0].saved.system_name == m8.system_name);
    check(!backend.inject(m8, a, 3, app_engine_clock_ns()));
    check(backend.set_fake_endpoints({m8, pad})); service.poll();
    check(listing() == initial); // Same IDs and enabled choices return without a new selection.
    check(backend.inject(m8, a, 3, app_engine_clock_ns())); service.poll();
    check(backend.learning() == Json({{"armed", true}}));
    check(backend.held() == Json::array({60, 62}) && events.back().source_id == 1);
    service.stop();
    check(backend.held().empty());
}
void midi_learn_observation() {
    using namespace wirescape::midi;
    ObservedMidi fake(true, false);
    auto endpoints = fake.endpoints();
    check(endpoints.size() == 1);
    check(fake.open(endpoints[0], {}));
    uint8_t cc[]{0xB3, 21, 64};
    check(fake.inject(endpoints[0], cc, 3, app_engine_clock_ns()));
    check(fake.learning().is_null()); // unarmed callbacks publish nothing
    fake.arm_learning(true);
    check(fake.learning() == Json({{"armed", true}}));
    check(fake.inject(endpoints[0], cc, 3, app_engine_clock_ns()));
    const auto first = fake.learning();
    check(first["armed"] == true && first["channel"] == 4 && first["controller"] == 21);
    check(first["value"] == 64 && first["deviceId"] == "M8 MIDI 1|M8:M8 MIDI 1");
    check(first["seq"].is_string());
    uint64_t allocations = 0;
    {
        allocation_watch::ThreadScope scope;
        for (int i = 0; i < 1000; ++i) {
            cc[1] = uint8_t(i % 128);
            cc[2] = uint8_t((i * 3) % 128);
            check(fake.inject(endpoints[0], cc, 3, app_engine_clock_ns()));
        }
        allocations = scope.allocations();
    }
    check(allocations == 0);
    const auto newest = fake.learning();
    check(newest["seq"] != first["seq"] && newest["controller"] == cc[1] && newest["value"] == cc[2]);
    check(newest.size() == 6); // one observation, not a queue/history
    fake.expire_learning(std::chrono::steady_clock::now() + std::chrono::seconds(31));
    check(fake.learning()["armed"] == true); // captured: no no-capture timeout
    fake.arm_learning(true);
    check(fake.learning() == Json({{"armed", true}})); // rearm resets the observation
    fake.expire_learning(std::chrono::steady_clock::now() + std::chrono::seconds(31));
    check(fake.learning().is_null());
    fake.arm_learning(true);
    uint32_t ump_cc[]{0x20BF7F01}; // MIDI 1 UMP: channel 16, controller 127, value 1
    check(fake.inject_ump(endpoints[0], ump_cc, 1, app_engine_clock_ns()));
    check(fake.learning()["channel"] == 16 && fake.learning()["controller"] == 127);
    fake.close(endpoints[0]);
    check(fake.learning() == Json({{"armed", true}}));
    fake.arm_learning(false);
    check(fake.learning().is_null());
}

// P1-e: deterministic MIDI callback witness with the control/writer held.
// Use the existing ObservedMidi injection seam, not a second parser or queue.
void controller_stream_midi_observation() {
    using namespace wirescape::midi;
    auto scripted = std::make_unique<ScriptedBackend>();
    auto *source = scripted.get();
    ObservedMidi fake(false, false, std::move(scripted));
    auto endpoints = fake.endpoints();
    check(endpoints.size() == 1 && fake.open(endpoints[0], {}));
    auto &capture = fake.controller_stream();
    const uint8_t initial[]{0xB0, 1, 7};
    check(source->inject(initial, 3, app_engine_clock_ns()));
    check(capture.drain().empty() && capture.status().is_null());
    capture.configure({"cc", "pc", "note"}, false);
    uint64_t allocations;
    {
        allocation_watch::ThreadScope scope;
        const uint8_t cc1[]{0xB0, 0, 3}, cc2[]{0xB0, 32, 4}, cc3[]{0xB0, 0, 9};
        const uint8_t pc[]{0xC0, 5};
        const uint8_t off[]{0x99, 36, 0};
        check(source->inject(cc1, 3, app_engine_clock_ns()));
        check(source->inject(cc2, 3, app_engine_clock_ns()));
        check(source->inject(pc, 2, app_engine_clock_ns()));
        check(source->inject(cc3, 3, app_engine_clock_ns()));
        check(source->inject(off, 3, app_engine_clock_ns()));
        allocations = scope.allocations();
    }
    check(allocations == 0);
    const auto events = capture.drain();
    check(events.size() == 4);
    check(events[0]["kind"] == "cc" && events[0]["controller"] == 32 && events[0]["value"] == 4);
    check(events[1]["kind"] == "pc" && events[1]["program"] == 5);
    check(events[2]["kind"] == "cc" && events[2]["controller"] == 0 && events[2]["value"] == 9);
    check(events[3]["kind"] == "noteOff" && events[3]["channel"] == 10 &&
          events[3]["note"] == 36 && events[3]["velocity"] == 0);
    for (const auto &event : events)
        check(event["deviceId"] == endpoints[0].name + "|" + endpoints[0].system_name &&
              event["t"].is_number_unsigned());
    check(capture.status()["dropped"] == Json({{"fifo", 0}, {"latest", 0}, {"oversize", 0}}));

    // Exactly 300 FIFO arrivals without draining: reject the newest 44.
    {
        allocation_watch::ThreadScope scope;
        for (unsigned i = 0; i < 300; ++i) {
            const uint8_t pc[]{uint8_t(0xC0 | (i / 128)), uint8_t(i % 128)};
            check(source->inject(pc, 2, app_engine_clock_ns()));
        }
        allocations = scope.allocations();
    }
    check(allocations == 0);
    const auto fifo = capture.drain();
    check(fifo.size() == 256);
    for (unsigned i = 0; i < fifo.size(); ++i)
        check(fifo[i]["kind"] == "pc" && fifo[i]["program"] == i % 128 &&
              fifo[i]["channel"] == i / 128 + 1);
    check(capture.status()["dropped"]["fifo"] == 44);
    // The 128 shared latest keys are a hard bound, not an eviction cache.
    for (unsigned i = 0; i < 128; ++i) {
        const uint8_t cc[]{0xB0, uint8_t(i), 1};
        check(source->inject(cc, 3, app_engine_clock_ns()));
    }
    const uint8_t extra[]{0xB1, 0, 2}, update[]{0xB0, 0, 99};
    check(source->inject(extra, 3, app_engine_clock_ns()));
    check(source->inject(update, 3, app_engine_clock_ns()));
    const auto latest = capture.drain();
    check(latest.size() == 128 && latest.back()["controller"] == 0 && latest.back()["value"] == 99);
    check(capture.status()["dropped"]["latest"] == 1);
    capture.configure({}, false);
    check(source->inject(initial, 3, app_engine_clock_ns()));
    check(capture.drain().empty() && capture.status().is_null());
    fake.close(endpoints[0]);
}

// P1-e stream-only OSC types must not broaden the graph codec. Validate
// the whole bundle before either ingress consumer sees a child.
void controller_stream_osc_codec() {
    using namespace wirescape::osc;
    const uint8_t simple[]{'/', 'x', 0, 0, ',', 'i', 0, 0, 0, 0, 0, 7};
    const uint8_t wide[]{
        '/', 'w', 0, 0, ',', 'h', 'd', 'T', 0, 0, 0, 0,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xd6, // -42 signed int64
        0x3f, 0xd0, 0, 0, 0, 0, 0, 0                     // 0.25 binary64
    };
    std::array<uint8_t, 16 + 4 + sizeof(simple) + 4 + sizeof(wide)> bundle{};
    std::memcpy(bundle.data(), "#bundle", 7);
    size_t at = 16;
    put32(bundle.data() + at, sizeof(simple)); at += 4;
    std::memcpy(bundle.data() + at, simple, sizeof(simple)); at += sizeof(simple);
    put32(bundle.data() + at, sizeof(wide)); at += 4;
    std::memcpy(bundle.data() + at, wide, sizeof(wide));
    unsigned delivered = 0;
    check(!parse(bundle.data(), bundle.size(), [&](const Message &) { ++delivered; }));
    check(delivered == 0); // exact existing graph behavior
    uint64_t allocations;
    {
        allocation_watch::ThreadScope scope;
        check(parse_controller(bundle.data(), bundle.size(), [&](const Message &message, bool legacy_packet) {
            check(!legacy_packet);
            if (delivered++ == 0)
                check(message.address == "/x" && message.arguments[0].integer == 7);
            else {
                check(message.address == "/w" && message.count == 3);
                check(message.arguments[0].type == 'h' && message.arguments[0].wide_integer == -42);
                check(message.arguments[1].type == 'd' && message.arguments[1].wide_real == 0.25);
                check(message.arguments[2].type == 'T');
            }
        }));
        allocations = scope.allocations();
    }
    check(delivered == 2 && allocations == 0);
    delivered = 0;
    check(!parse_controller(bundle.data(), bundle.size() - 4, [&](const Message &, bool) { ++delivered; }));
    check(delivered == 0); // no partial stream capture from malformed tree
    check(parse_controller(simple, sizeof(simple), [&](const Message &, bool legacy_packet) {
        check(legacy_packet); ++delivered;
    }));
    check(delivered == 1);
}

void d5_phase_deadline_regression() {
    using Clock = std::chrono::steady_clock;
    using Ms = std::chrono::milliseconds;
    using Ns = std::chrono::nanoseconds;
    const Ms period{512};               // 4096 frames at 8000 Hz
    const auto gap_budget = 3 * period; // same long-block budget as production
    const Clock::time_point first_fade = Clock::time_point(Ms{1000000});
    const auto since_epoch = std::chrono::duration_cast<Ns>(first_fade.time_since_epoch());
    const auto first_ns = uint64_t(since_epoch.count());
    const auto actual_deadline = d5_gap_deadline(first_ns, gap_budget);
    check(actual_deadline == first_fade + gap_budget);
    for (const auto wait_before_fade : {Ms{1}, period - Ms{1}}) {
        const auto request = first_fade - wait_before_fade;
        const auto fade_in = first_fade + 2 * period + Ms{10};
        check(fade_in < actual_deadline);
        if (wait_before_fade == period - Ms{1}) {
            check(fade_in > request + gap_budget); // fails the old request-origin clock
        } else {
            check(fade_in < request + gap_budget);
        }
        // The unchanged bounded request/mute watchdog still expires independently.
        check(request + gap_budget < actual_deadline);
    }
    check(first_fade + gap_budget + Ns{1} > actual_deadline); // late fade-in refuses
    check(d5_gap_deadline(first_ns, Ms{150}) == first_fade + Ms{150});
    check(first_fade + Ms{151} > d5_gap_deadline(first_ns, Ms{150}));
}

void sink_wait_deadline_regression() {
    using Clock = std::chrono::steady_clock;
    using Ns = std::chrono::nanoseconds;
    using Us = std::chrono::microseconds;
    const Clock::time_point zero{};
    const auto deadline = zero + Ns(5333333); // 256 frames / 48 kHz, rounded to nanoseconds
    check(sink_due_100ns(zero, zero) == 0);
    check(sink_due_100ns(zero, zero + Ns(1)) == -1);
    check(sink_due_100ns(zero, zero + Ns(100)) == -1);
    check(sink_due_100ns(zero, zero + Ns(101)) == -2);
    check(sink_due_100ns(zero, deadline) == -53334);

    // A timer signalled early must be rearmed for the same absolute deadline,
    // not let the next render start early or drift the periodic schedule.
    auto now = zero;
    unsigned arms = 0;
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    const auto reached = sink_wait_until(
        deadline, [&] { return now; },
        [&](int64_t due) {
            ++arms;
            if (arms == 1) {
                check(due == -53334);
                now = zero + Us(5000);
            } else {
                check(arms == 2 && due == -3334);
                now = deadline;
            }
            return SinkWaitResult::deadline;
        });
    check(reached == SinkWaitResult::deadline && arms == 2 && now == deadline);

    // A stop signal interrupts a long-block wait without waiting for the timer;
    // an unavailable kernel timer delegates to the existing CV fallback.
    arms = 0;
    const auto stopped = sink_wait_until(
        zero + Us(512000), [&] { return zero; },
        [&](int64_t due) {
            check(due == -5120000);
            ++arms;
            return SinkWaitResult::stopped;
        });
    check(stopped == SinkWaitResult::stopped && arms == 1);
    const auto unavailable =
        sink_wait_until(deadline, [&] { return zero; }, [&](int64_t) { return SinkWaitResult::unavailable; });
    check(unavailable == SinkWaitResult::unavailable);
    arms = 0;
    const auto early_storm = sink_wait_until(
        deadline, [&] { return zero; },
        [&](int64_t due) {
            check(due == -53334);
            ++arms;
            return SinkWaitResult::deadline;
        });
    check(early_storm == SinkWaitResult::unavailable && arms == 16);
    arms = 0;
    const auto overdue = sink_wait_until(
        zero, [&] { return zero + Us(1); },
        [&](int64_t) {
            ++arms;
            return SinkWaitResult::unavailable;
        });
    check(overdue == SinkWaitResult::deadline && arms == 0);
    allocation_watch::enabled.store(false);
    check(allocation_watch::count.load() == 0);
}

int run_tests() {
    midi_learn_observation();
    controller_stream_midi_observation();
    controller_stream_osc_codec();
    RenderHistogram histogram;
    check(histogram.percentile(50) == 0);
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    for (int percent = 0; percent < 100; ++percent) histogram.record(percent + 0.5, false);
    histogram.record(255.25, true);
    histogram.observe_faults(0);
    histogram.observe_faults(2);
    histogram.observe_faults(2); // a repeated sample is not another fault
    histogram.observe_faults(3);
    histogram.observe_faults(0); // new graph's counter restarted
    histogram.observe_faults(1);
    allocation_watch::enabled.store(false);
    check(histogram.faults == 4);
    check(allocation_watch::count.load() == 0);
    check(histogram.blocks == 101 && histogram.overruns == 1);
    check(histogram.bins[0] == 1 && histogram.bins[199] == 0 && histogram.bins[200] == 1);
    check(histogram.percentile(50) == 50 && histogram.percentile(99) == 99);
    check(histogram.percentile(100) == 200 && histogram.max_percent == 255.25);

    // Synthetic absolute deadlines prove equality, delayed wakes, long renders,
    // and catch-up blocks without relying on host scheduling or sleeping.
    RenderHistogram timing;
    using Clock = std::chrono::steady_clock;
    using Us = std::chrono::microseconds;
    const Clock::time_point zero{};
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    timing.record_timing(100, zero, zero + Us(100), zero, zero + Us(100));
    timing.record_timing(1, zero + Us(201), zero + Us(202), zero + Us(100), zero + Us(200));
    timing.record_timing(101, zero + Us(200), zero + Us(301), zero + Us(200), zero + Us(300));
    timing.record_timing(1, zero + Us(500), zero + Us(501), zero + Us(300), zero + Us(400));
    allocation_watch::enabled.store(false);
    check(allocation_watch::count.load() == 0);
    check(timing.blocks == 4 && timing.overruns == 3);
    check(timing.overrun_render_count == 1 && timing.overrun_render_max_us == 101);
    check(timing.overrun_wake_count == 2 && timing.overrun_wake_max_us == 200);

    sink_wait_deadline_regression();
    d5_phase_deadline_regression();
    midi_hotplug_observation();
    for (const auto &bad : {"{\"x\":1,\"x\":2}", "{\"x\":{\"y\":1,\"y\":2}}", "[]"}) {
        bool refused = false;
        try {
            strict_json(bad);
        } catch (...) {
            refused = true;
        }
        check(refused);
    }
    std::string boundary = "{\"x\":" + std::string(63, '[') + "0" + std::string(63, ']') + "}";
    check(strict_json(boundary).is_object());
    bool too_deep = false;
    try {
        strict_json("{\"x\":" + std::string(64, '[') + "0" + std::string(64, ']') + "}");
    } catch (...) {
        too_deep = true;
    }
    check(too_deep);
    std::ostringstream source;
    for (int i = 0; i < 257; ++i) source << "{\"v\":0,\"id\":\"q" << i << "\",\"type\":\"panic\"}\n";
    std::istringstream input(source.str());
    std::ostringstream output;
    Transport transport(input, output);
    transport.start();
    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    while (transport.pending() < PendingLimit && std::chrono::steady_clock::now() < deadline) std::this_thread::yield();
    check(transport.pending() == PendingLimit);
    // Reader has parsed the 257th command while the control executor is stalled.
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    for (int i = 0; i < 257; ++i) {
        Request request;
        check(transport.next(request, std::chrono::seconds(5)));
        check(request.value["id"] == "q" + std::to_string(i));
        check(request.error == (i == 256 ? "busy" : ""));
    }
    transport.finish();
    // The stream-backed test adapter must parse raw-pipe-sized chunks without
    // splitting or corrupting a newline-delimited request at 64 KiB boundaries.
    const std::string large_payload(65540, 'x');
    const std::string long_line = "{\"v\":0,\"id\":\"long\",\"type\":\"panic\",\"pad\":\"" + large_payload + "\"}\n";
    std::istringstream chunked_input(long_line + "{\"v\":0,\"id\":\"second\",\"type\":\"panic\"}\n" +
                                     std::string(LineLimit + 1, 'x') + "\n");
    std::ostringstream chunked_output;
    Transport chunked(chunked_input, chunked_output);
    chunked.start();
    Request first_chunk, second_chunk, excess_chunk;
    check(chunked.next(first_chunk, std::chrono::seconds(5)));
    check(first_chunk.error.empty() && first_chunk.value["id"] == "long");
    check(first_chunk.value["pad"].get<std::string>() == large_payload);
    chunked.complete(first_chunk);
    check(chunked.next(second_chunk, std::chrono::seconds(5)));
    check(second_chunk.error.empty() && second_chunk.value["id"] == "second");
    chunked.complete(second_chunk);
    check(chunked.next(excess_chunk, std::chrono::seconds(5)));
    check(excess_chunk.error == "limit");
    chunked.finish();

    // Coalescing must inspect the message before moving it into its slot.
    // MSVC evaluates JSON's by-value assignment argument before the left-hand
    // conditional expression, exposing a value() call on a moved-from null.
    std::istringstream coalesced_input("");
    std::ostringstream coalesced_output;
    Transport coalesced(coalesced_input, coalesced_output);
    coalesced.send({{"type", "status"}, {"probe", 0}}, true);
    coalesced.send({{"type", "status"}, {"probe", 1}}, true);
    coalesced.send({{"type", "telemetry"}, {"probe", 2}}, true);
    coalesced.start();
    coalesced.finish();
    std::istringstream coalesced_messages(coalesced_output.str());
    std::string message;
    check(bool(std::getline(coalesced_messages, message)));
    check(strict_json(message) == Json({{"type", "status"}, {"probe", 1}}));
    check(bool(std::getline(coalesced_messages, message)));
    check(strict_json(message) == Json({{"type", "telemetry"}, {"probe", 2}}));
    check(!std::getline(coalesced_messages, message));

    // P1-e: a held writer must retain the first controller push in its own
    // slot. Status and telemetry are independent; reliable replies still win.
    std::istringstream controller_input("");
    std::ostringstream controller_output;
    Transport controller_transport(controller_input, controller_output);
    controller_transport.send({{"type", "controller"}, {"probe", 10}}, true);
    controller_transport.send({{"type", "status"}, {"probe", 20}}, true);
    controller_transport.send({{"type", "telemetry"}, {"probe", 30}}, true);
    controller_transport.send({{"type", "controller"}, {"probe", 11}}, true);
    controller_transport.send({{"re", "reliable"}, {"ok", true}});
    controller_transport.start();
    controller_transport.finish();
    std::istringstream controller_messages(controller_output.str());
    check(bool(std::getline(controller_messages, message)));
    check(strict_json(message) == Json({{"re", "reliable"}, {"ok", true}}));
    std::map<std::string, int> controller_probes;
    while (std::getline(controller_messages, message)) {
        const auto value = strict_json(message);
        check(controller_probes.emplace(value["type"].get<std::string>(),
                                        value["probe"].get<int>()).second);
    }
    check(controller_probes == std::map<std::string, int>{
        {"controller", 10}, {"status", 20}, {"telemetry", 30}});

    ObservedMidi fake(true, false);
    auto endpoints = fake.endpoints();
    check(endpoints.size() == 1);
    int messages = 0;
    wirescape::midi::Callback cb{
        &messages, [](void *context, const uint8_t *, size_t, uint64_t) { ++*static_cast<int *>(context); }, nullptr};
    check(fake.open(endpoints[0], cb));
    check(fake.activity().empty());
    uint8_t on[] = {0x90, 60, 100}, off[] = {0x90, 60, 0};
    check(fake.inject(endpoints[0], on, 3, 100));
    check(fake.held() == Json::array({60}));
    check(fake.inject(endpoints[0], off, 3, 110));
    check(fake.held().empty());
    check(messages == 2);
    fake.inject(endpoints[0], on, 3, app_engine_clock_ns());
    check(!fake.activity().empty());
    fake.clear_notes();
    check(fake.held().empty());
    uint32_t midi2_on[] = {0x40903c00, 0}, midi2_off[] = {0x40803c00, 0};
    check(fake.inject_ump(endpoints[0], midi2_on, 2, app_engine_clock_ns()));
    check(fake.held() == Json::array({60}));
    check(fake.inject_ump(endpoints[0], midi2_off, 2, app_engine_clock_ns()));
    check(fake.held().empty());
    fake.inject(endpoints[0], on, 3, 120);
    fake.close(endpoints[0]);
    check(fake.held().empty());
    wirescape::engine2::Config config{};
    config.sample_rate = 48000;
    config.max_block = 128;
    config.max_nodes = 64;
    config.event_budget = 2048;
    wirescape::audio::EngineOwner catalogue(app_engine_create(&config), app_engine_destroy);
    std::string error;
    const char *patch =
        R"({"format":"wirescape.native.patch","version":2,"settings":{},"modules":[{"id":1,"module":"essentials.vco","version":2},{"id":7,"module":"essentials.output","version":2}],"connections":[{"kind":"signal","from":{"module":1,"port":"audio"},"to":{"module":7,"port":"audio"}}],"outputs":[{"module":7,"port":"audio","bus_channel":0},{"module":7,"port":"audio","bus_channel":1}]})";
    wirescape::audio::EngineOwner engine(wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error),
                                         app_engine_destroy);
    check(bool(engine));
    float scratch[256]{}, output_block[256]{};
    std::atomic<uint64_t> faults{0};
    check(wirescape::audio::render_callback_block(engine.get(), scratch, 128, output_block, 128, app_engine_clock_ns(),
                                                  faults));
    ws2_event parameter{};
    parameter.struct_size = sizeof(parameter);
    parameter.type = WS2_PARAM;
    const char *parameter_id = app_engine_native_descriptor(engine.get(), "essentials.vco")->params[0].id;
    const auto parameter_generation = app_engine_generation(engine.get());
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    bool okay = true;
    for (int i = 0; i < 1000; ++i) {
        parameter.value = float(220 + i % 100);
        okay = okay && app_engine_enqueue(engine.get(), 1, parameter, 0, parameter_generation, parameter_id) == WS2_OK;
        okay = okay && wirescape::audio::render_callback_block(engine.get(), scratch, 128, output_block, 128,
                                                               app_engine_clock_ns(), faults);
    }
    allocation_watch::enabled.store(false);
    check(okay);
    check(allocation_watch::count.load() == 0);
    check(faults.load() == 0);

    // D5: compare ramped samples to a lockstep non-ramped reference. The
    // reference preserves the oscillator's actual audio, not synthesized silence.
    wirescape::audio::EngineOwner reference(
        wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error), app_engine_destroy);
    wirescape::audio::EngineOwner faded(wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error),
                                        app_engine_destroy);
    check(bool(reference) && bool(faded));
    float dry[128]{}, wet[128]{};
    float *dry_rows[] = {dry}, *wet_rows[] = {wet};
    auto render = [&](AppEngine *left, AppEngine *right) {
        check(app_engine_render_channels(left, wet_rows, 1, 128) == WS2_OK);
        check(app_engine_render_channels(right, dry_rows, 1, 128) == WS2_OK);
    };
    auto render_at = [&](uint64_t callback_ns) {
        check(app_engine_render_live(faded.get(), wet_rows, 1, 128, callback_ns) == WS2_OK);
        check(app_engine_render_channels(reference.get(), dry_rows, 1, 128) == WS2_OK);
    };
    render(faded.get(), reference.get()); // both graphs initially at unity
    app_engine_begin_master_fade_out(faded.get());
    check(app_engine_master_fade_out_started_ns(faded.get()) == 0);
    float expected_gain = 1.0f;
    const float step = 1.0f / 480.0f;
    int blocks = 0, nonzero_old = 0;
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    // Normal order: the callback timestamp follows the request and wins the max().
    const uint64_t first_fade_ns = app_engine_clock_ns() + 1000000000ULL;
    check(first_fade_ns > app_engine_master_fade_out_requested_ns(faded.get()));
    while (!app_engine_master_fade_silent(faded.get()) && blocks < 8) {
        render_at(first_fade_ns + uint64_t(blocks) * 2666667ULL);
        ++blocks;
        for (int i = 0; i < 128; ++i) {
            expected_gain = std::max(0.0f, expected_gain - step);
            check(std::abs(wet[i] - dry[i] * expected_gain) < 0.0002f);
            if (std::abs(wet[i]) > 0.001f) ++nonzero_old;
        }
    }
    allocation_watch::enabled.store(false);
    check(app_engine_master_fade_silent(faded.get()) && nonzero_old > 0);
    check(app_engine_master_fade_out_started_ns(faded.get()) == first_fade_ns);
    check(blocks * 128 <= 480 + 256); // fade edge + a complete zero block
    check(allocation_watch::count.load() == 0);
    for (float sample : wet) check(sample == 0.0f);

    // Forced callback/request overlap: render entered before control's fade request.
    // Its entry timestamp is therefore older even if it applies the fade after render.
    app_engine_begin_master_fade_out(reference.get());
    const uint64_t requested_ns = app_engine_master_fade_out_requested_ns(reference.get());
    check(requested_ns > 1 && app_engine_master_fade_out_started_ns(reference.get()) == 0);
    allocation_watch::count.store(0);
    allocation_watch::enabled.store(true);
    const bool overlap_ok = app_engine_render_live(reference.get(), dry_rows, 1, 128, requested_ns - 1) == WS2_OK;
    allocation_watch::enabled.store(false);
    check(overlap_ok && allocation_watch::count.load() == 0);
    check(app_engine_master_fade_out_started_ns(reference.get()) == requested_ns);
    // The once-only render publication must not move if another faded block arrives.
    check(app_engine_render_live(reference.get(), dry_rows, 1, 128, requested_ns + 1000000) == WS2_OK);
    check(app_engine_master_fade_out_started_ns(reference.get()) == requested_ns);

    // No callback: zero timestamp, no synthetic fade-start proof, bounded watchdog.
    wirescape::audio::EngineOwner stalled(
        wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error), app_engine_destroy);
    check(bool(stalled));
    app_engine_begin_master_fade_out(stalled.get());
    check(app_engine_master_fade_out_started_ns(stalled.get()) == 0);
    check(!app_engine_master_fade_silent(stalled.get()));
    app_engine_resume_master_fade(stalled.get());

    // New graph starts hard muted and rises only during its own render blocks.
    wirescape::audio::EngineOwner next(wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error),
                                       app_engine_destroy);
    wirescape::audio::EngineOwner next_reference(
        wirescape::document::load_runtime_patch(patch, catalogue.get(), config, error), app_engine_destroy);
    check(bool(next) && bool(next_reference));
    app_engine_prepare_master_fade_in(next.get());
    expected_gain = 0.0f;
    blocks = 0;
    bool rose = false;
    while (blocks < 8) {
        render(next.get(), next_reference.get());
        ++blocks;
        for (int i = 0; i < 128; ++i) {
            expected_gain = std::min(1.0f, expected_gain + step);
            check(std::abs(wet[i] - dry[i] * expected_gain) < 0.0002f);
            if (std::abs(wet[i]) > 0.001f) rose = true;
        }
        if (expected_gain >= 1.0f) break;
    }
    check(rose && app_engine_master_fade_in_started(next.get()));
    check(blocks * 128 <= 480 + 128);
    // Null-sink deterministic clock bounds the complete mute/swap/unmute
    // envelope well below 150 ms at 48 kHz, independent of device timing.
    check((blocks + 6) * 128.0 / 48000.0 < 0.150);
    return 0;
}
int main() noexcept {
    try {
        return run_tests();
    } catch (const std::exception &error) {
        std::cerr << "sidecar unit: " << error.what() << '\n';
        return 1;
    } catch (...) {
        std::cerr << "sidecar unit: unknown exception\n";
        return 1;
    }
}
