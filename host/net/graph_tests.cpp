// SPDX-License-Identifier: GPL-3.0-only
#include "../../sdk/examples/test_support.h"
#include "../../tests/native/abi2/allocation_watch.h"
#include "../osc/codec.h"
#include "osc_service.h"
#include "runtime_patch.h"
#include "../document/runtime_module_config.h"
#include <atomic>
#include <chrono>
#include <cstring>
#include <thread>
#ifdef _WIN32
#include <winsock2.h>
#else
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif
struct GraphSink {
    AppEngine *engine;
    std::atomic<int> result{-1};
    std::atomic<uint64_t> timestamp{0};
    static int deliver(void *context, uint32_t node, const ws2_event &event, uint64_t timestamp) noexcept {
        auto &self = *static_cast<GraphSink *>(context);
        const int status = app_engine_native(self.engine)
                               .enqueue(2, node, WS2_DIRECT_PORT, event, timestamp,
                                        wirescape::engine2::Timing::Timestamped, app_engine_generation(self.engine));
        self.timestamp.store(timestamp, std::memory_order_release);
        self.result.store(status, std::memory_order_release);
        return status;
    }
};
// A77/E3c: test legacy partial CC/OSC Out rows via the same loader
// used by sidecar and Web. The direct OSC In legacy witness follows below.
static void legacy_cc_and_out() {
    using namespace wirescape;
    const std::string patch = R"({"format":"wirescape.native.patch","version":2,"settings":{},"modules":[{"id":1,"module":"midi.cc_to_cv","version":1,"config":{"rows":[{"controller":11,"smoothing_ms":0,"min":0.25,"max":0.75}]}},{"id":2,"module":"osc.out","version":1,"config":{"rows":[{"enabled":false},{"address":"/legacy/second"}]}}],"connections":[{"kind":"signal","from":{"module":1,"port":"cc1"},"to":{"module":2,"port":"row2"}}],"outputs":[{"module":1,"port":"cc1","bus_channel":0}]})";
    engine2::Config config{};
    config.max_block = 128;
    osc::OutBus bus;
    const std::map<uint32_t, osc::OutBus *> buses{{2, &bus}};
    document::ScopedOutBuses scoped(buses);
    std::string error;
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(
        document::load_runtime_patch(patch, nullptr, config, error), app_engine_destroy);
    if (!engine) std::fprintf(stderr, "legacy CC/OSC Out load: %s\n", error.c_str());
    REQUIRE(bool(engine));
    auto &graph = app_engine_native(engine.get());
    ws2_event event{};
    event.struct_size = sizeof(event);
    event.type = WS2_MIDI;
    event.channel = -1;
    event.note_id = -1;
    event.source_id = 1;
    event.ump_words = 1;
    event.ump[0] = 0x20b00b7fu; // CC 11, value 127
    REQUIRE(graph.enqueue(0, 1, 0, event, 0, engine2::Timing::Immediate) == WS2_OK);
    float samples[128]{};
    float *outputs[]{samples};
    REQUIRE(graph.render(outputs, 1, 128) == WS2_OK);
    REQUIRE(graph.output_sample(1, 0, 0, 127) == .75f);
    REQUIRE(bus.rows[0].blocks.load() == 0);
    REQUIRE(bus.rows[1].blocks.load() > 0);
    REQUIRE(bus.rows[1].value.load() == .75f);
}
int main() {
    legacy_cc_and_out();
    const std::string patch =
        R"({"format":"wirescape.native.patch","version":2,"settings":{},"modules":[{"id":1,"module":"osc.in","version":1,"parameters":{},"config":{"rows":[{"pattern":"/pico1/knob/*","smoothing_ms":0}]}},{"id":2,"module":"essentials.vco","version":1,"parameters":{}}],"connections":[],"outputs":[{"module":2,"port":"audio","bus_channel":0}]})";
    wirescape::engine2::Config config{};
    config.sample_rate = 48000;
    config.max_block = 128;
    config.max_nodes = 64;
    config.event_budget = 2048;
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> catalog(app_engine_create(&config), app_engine_destroy);
    std::string error;
    std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(
        wirescape::document::load_runtime_patch(patch, catalog.get(), config, error), app_engine_destroy);
    REQUIRE(bool(engine));
    GraphSink sink{engine.get()};
    wirescape::osc::Service service({&sink, GraphSink::deliver});
    REQUIRE(service.add({1, 0, false}) && service.start());
    REQUIRE(service.states().size() == 1 && std::strcmp(service.states()[0].state, "listening") == 0);
    wirescape::osc::Message message;
    message.address = "/pico1/knob/3";
    message.count = 1;
    message.arguments[0].type = 'f';
    message.arguments[0].real = .75f;
    uint8_t packet[1472]{};
    bool shortened = false;
    const auto bytes = wirescape::osc::encode(message, packet, sizeof(packet), shortened);
    const auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(service.bound_port());
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const auto sent_at = app_engine_clock_ns();
    REQUIRE(sendto(sender, reinterpret_cast<const char *>(packet), int(bytes), 0,
                   reinterpret_cast<sockaddr *>(&address), sizeof(address)) == int(bytes));
    for (uint32_t attempt = 0; attempt < 2000 && sink.result.load(std::memory_order_acquire) == -1; ++attempt)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    service.stop(); // producer stops and joins before render/engine teardown
    REQUIRE(sink.result.load() == WS2_OK && service.counters().received == 1);
    REQUIRE(service.states()[0].received == 1 && service.states()[0].dropped == 0);
    const auto callback_time = app_engine_clock_ns();
    REQUIRE(sink.timestamp.load() >= sent_at && sink.timestamp.load() <= callback_time);
    REQUIRE(sink.timestamp.load() != 0);
    float output[128];
    float *channels[] = {output};
    int status;
    {
        allocation_watch::Scope scope;
        status = app_engine_render_live(engine.get(), channels, 1, 128, callback_time);
        REQUIRE(scope.allocations() == 0);
    }
    REQUIRE(status == WS2_OK);
    // Timestamped ingress has one max-block of bounded scheduling lead.
    REQUIRE(app_engine_native(engine.get()).output_sample(1, 0, 0, 0) == 0);
    {
        allocation_watch::Scope scope;
        status = app_engine_render_live(engine.get(), channels, 1, 128, app_engine_clock_ns());
        REQUIRE(scope.allocations() == 0);
    }
    REQUIRE(status == WS2_OK);
    REQUIRE(app_engine_native(engine.get()).output_sample(1, 0, 0, 0) == .75f);
    REQUIRE(app_engine_native(engine.get()).output_sample(1, 0, 0, 127) == .75f);
}
