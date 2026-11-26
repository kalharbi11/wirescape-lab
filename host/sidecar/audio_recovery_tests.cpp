// SPDX-License-Identifier: GPL-3.0-only
// Link-time fake implements the existing audio service boundary; never loads PortAudio.
#ifdef _WIN32
#include <winsock2.h>
#else
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif
#include "../osc/codec.h"
#include "../../modules/osc_out/dsp.h"
#include "session.h"
#include "wirescape_sdk.h"
#include <cstring>
#include <algorithm>
#include <cerrno>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
namespace fake {
std::vector<wirescape::audio::Device> outputs;
std::vector<std::string> attempts;
std::string refuse_id;  // fake a single device-specific PortAudio open failure
std::string open_error; // injected malformed/multibyte host diagnostic
std::vector<std::string> installed_asio;
bool active = true, refuse = false, enumeration_throws = false, render = false;
uint32_t rejected_rate = 0;
// Fake ASIO buffer negotiation: when accept_block is set, any other block fails to
// open; a first attempt then reports `preferred` (0 = driver offers no size).
uint32_t accept_block = 0;
std::string accept_block_device; // empty: all fake devices; otherwise only this endpoint
int64_t preferred = 0;
std::vector<uint32_t> blocks;
std::string rate_refused_id;
int stopped = 0, exchanges = 0;
std::vector<wirescape::audio::DeviceQuery> queries;
std::atomic<uint64_t> completed_blocks{0};
AppEngine *engine = nullptr;
// Test-only: join the paced callback without closing the fake stream, so state
// snapshots and manually stepped renders have a single, quiescent owner.
std::function<void()> freeze_render;
}
// Legacy-shaped fake output: the id is the bare name, as before host-API identity.
wirescape::audio::Device output(const std::string &name, int index, bool is_default = false) {
    return {name, name, "", index, is_default};
}
namespace wirescape::audio {
std::vector<std::string> installed_asio_drivers() { return fake::installed_asio; }
std::vector<Device> devices(const std::string &, const DeviceQuery &query) {
    fake::queries.push_back(query);
    if (fake::enumeration_throws) throw std::runtime_error("fake enumeration failure");
    return fake::outputs;
}
struct Stream::Impl {
    EngineOwner engine{nullptr, app_engine_destroy};
    std::function<void()> producers;
    // With fake::render, a paced thread plays the device callback (block-boundary adopt).
    EngineSlot slot;
    std::atomic<bool> quit{false};
    std::thread callback;
    uint32_t frames = 0;
};
Stream::Stream(EngineOwner &owner, const StreamSelection &selection, double rate, uint32_t block,
               std::function<void()> producers, bool allow_preferred_retry)
    : impl_(std::make_unique<Impl>()) {
    fake::attempts.push_back(selection.name);
    fake::blocks.push_back(block);
    if (fake::accept_block && block != fake::accept_block &&
        (fake::accept_block_device.empty() || selection.name == fake::accept_block_device)) {
        if (allow_preferred_retry && fake::preferred) throw PreferredBufferSize(fake::preferred);
        throw std::runtime_error("fake ASIO buffer refused");
    }
    impl_->frames = block;
    if (resolve_device(fake::outputs, selection.name) < 0 || fake::refuse || selection.name == fake::refuse_id)
        throw std::runtime_error(fake::open_error.empty() ? "fake unavailable/ambiguous output" : fake::open_error);
    if (uint32_t(rate) == fake::rejected_rate || selection.name == fake::rate_refused_id) throw RateUnsupported();
    impl_->engine = std::move(owner);
    impl_->producers = std::move(producers);
    fake::engine = impl_->engine.get();
    fake::active = true;
    if (fake::render) {
        impl_->callback = std::thread([impl = impl_.get(), live = impl_->engine.get(), block, rate]() mutable {
            std::vector<float> left(block), right(block);
            float *rows[] = {left.data(), right.data()};
            const auto period = std::chrono::duration<double>(block / rate);
            while (!impl->quit.load()) {
                live = impl->slot.adopt(live);
                app_engine_render_live(live, rows, 2, block, app_engine_clock_ns());
                fake::completed_blocks.fetch_add(1, std::memory_order_release);
                std::this_thread::sleep_for(period);
            }
        });
        fake::freeze_render = [impl = impl_.get()] {
            impl->quit.store(true);
            if (impl->callback.joinable()) impl->callback.join();
        };
    }
}
Stream::~Stream() { stop(); }
EngineOwner Stream::stop() {
    impl_->quit.store(true);
    if (impl_->callback.joinable()) impl_->callback.join();
    if (impl_->engine) {
        fake::freeze_render = {};
        if (impl_->producers) impl_->producers();
        ++fake::stopped;
    }
    return std::move(impl_->engine);
}
bool Stream::exchange(EngineOwner &next, std::chrono::steady_clock::time_point deadline) {
    if (!impl_->engine || !impl_->callback.joinable() || !impl_->slot.offer(next.get(), deadline)) return false;
    std::swap(impl_->engine, next);
    fake::engine = impl_->engine.get();
    ++fake::exchanges;
    return true;
}
bool Stream::running() const { return bool(impl_->engine) && fake::active; }
double Stream::cpu_percent() const { return 0; }
uint64_t Stream::dropouts() const { return 0; }
uint32_t Stream::buffer_frames() const noexcept { return impl_->frames; }
} // namespace wirescape::audio
using namespace wirescape::sidecar;
using namespace std::chrono_literals;
void check(bool ok, const char *message) {
    if (!ok) throw std::runtime_error(message);
}
Json audio(const Session &s) { return s.status()["status"]["audio"]; }
// Only loopback UDP: no real audio, MIDI, device enumeration, or LAN binding.
void send_local_osc(uint16_t port) {
    wirescape::osc::Message m;
    m.address = "/reconnect";
    m.count = 1;
    m.arguments[0].type = 'f';
    m.arguments[0].real = 0.5f;
    uint8_t packet[1024]{};
    bool truncated = false;
    const auto size = wirescape::osc::encode(m, packet, sizeof(packet), truncated);
    check(size > 0 && !truncated, "encode bounded OSC loopback message");
    const auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    check(sender != -1, "create UDP loopback sender");
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const auto sent = ::sendto(sender, reinterpret_cast<const char *>(packet), int(size), 0,
                               reinterpret_cast<sockaddr *>(&address), sizeof(address));
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    check(sent == int(size), "send OSC packet to localhost only");
}
// Reserve an OS-selected loopback port briefly, then let the sidecar bind it.
// The release/rebind interval remains a TOCTOU window; check route state below.
uint16_t select_loopback_osc_port() {
#ifdef _WIN32
    WSADATA startup{};
    check(WSAStartup(MAKEWORD(2, 2), &startup) == 0, "initialize Winsock for loopback port selection");
    const auto sock = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) {
        WSACleanup();
        throw std::runtime_error("create loopback port selection socket");
    }
#else
    const auto sock = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    check(sock >= 0, "create loopback port selection socket");
#endif
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(0);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const bool bound = ::bind(sock, reinterpret_cast<sockaddr *>(&address), sizeof(address)) == 0;
#ifdef _WIN32
    int length = sizeof(address);
#else
    socklen_t length = sizeof(address);
#endif
    const bool named = bound && ::getsockname(sock, reinterpret_cast<sockaddr *>(&address), &length) == 0;
    const uint16_t port = named ? ntohs(address.sin_port) : 0;
#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif
    check(port != 0, "select OS-assigned UDP loopback port");
    return port;
}
// A deterministic EWOULDBLOCK seam verifies honest send-error accounting and
// bounded coalescing without relying on UDP receiver liveness.
std::atomic<uint32_t> injected_calls{0};
std::array<float, 4> injected_values{};
bool fail_outgoing(const wirescape::osc::Message &message, uint16_t) {
    const auto n = injected_calls.fetch_add(1, std::memory_order_relaxed);
    if (n < injected_values.size()) injected_values[n] = message.arguments[0].real;
    errno = EWOULDBLOCK;
    return false;
}
bool accept_outgoing(const wirescape::osc::Message &message, uint16_t) {
    const auto n = injected_calls.fetch_add(1, std::memory_order_relaxed);
    if (n < injected_values.size()) injected_values[n] = message.arguments[0].real;
    return true;
}
void test_osc_out_budget() {
    Json config = {{"port", 9001}, {"rows", Json::array()}, {"notes", {{"enabled", false}}}};
    config["rows"].push_back({{"kind", "gate"}});
    for (int i = 1; i < 8; ++i) config["rows"].push_back({{"enabled", false}});
    const Json patch = {{"modules", Json::array({{{"id", 19}, {"module", "osc.out"}, {"config", config}}})}};
    for (const auto hook :
         {wirescape::osc::SendOverride(fail_outgoing), wirescape::osc::SendOverride(accept_outgoing)}) {
        injected_calls.store(0, std::memory_order_relaxed);
        injected_values.fill(-1);
        wirescape::osc::OutHost sender(patch.dump(), hook);
        auto *bus = sender.buses().at(19);
        bus->rows[0].rises.store(500, std::memory_order_relaxed);
        bus->rows[0].falls.store(500, std::memory_order_relaxed);
        bus->rows[0].value.store(0, std::memory_order_relaxed);
        bus->rows[0].blocks.store(1, std::memory_order_release);
        sender.start();
        const auto deadline = std::chrono::steady_clock::now() + 2s;
        while (injected_calls.load(std::memory_order_relaxed) < 2 && std::chrono::steady_clock::now() < deadline)
            std::this_thread::sleep_for(5ms);
        sender.stop();
        const auto state = sender.states().at(0);
        check(injected_calls.load() == 2 && injected_values[0] == 1 && injected_values[1] == 0,
              "1000 gate crossings coalesce to one ordered pulse");
        check(state.sent == (hook == accept_outgoing ? 2u : 0u) &&
                  state.dropped == (hook == accept_outgoing ? 998u : 1000u),
              "coalesced edges and deterministic EWOULDBLOCK count as observed drops");
    }
}
// A98 diagnostic only: the #635 forced-poll schedule, expressed using the
// actual pre-E3c producer stores (value, counters, release blocks).
// The later gate row is an independent sentinel, not a timing assumption.
std::vector<float> historic_gate_trace;
std::atomic<unsigned> historic_sentinels{0};
bool historic_gate_send(const wirescape::osc::Message &message, uint16_t) {
    if (message.address == "/ws/row/1") historic_gate_trace.push_back(message.arguments[0].real);
    if (message.address == "/ws/row/2")
        historic_sentinels.fetch_add(1, std::memory_order_release);
    return true;
}
void test_631_historical_gate_snapshot_interleaving() {
    using namespace wirescape::osc;
    Json rows = Json::array();
    for (unsigned i = 0; i < 8; ++i)
        rows.push_back({{"kind", "gate"}, {"enabled", i < 2}});
    const Json patch = {{"modules", Json::array({{{"id", 19}, {"module", "osc.out"},
        {"config", {{"rows", rows}, {"notes", {{"enabled", false}}}}}}})}};
    historic_gate_trace.clear();
    historic_sentinels.store(0);
    OutHost sender(patch.dump(), historic_gate_send);
    auto *bus = sender.buses().at(19);
    auto &gate = bus->rows[0];
    auto &sentinel = bus->rows[1];
    auto publish = [](OutRow &row, float value, uint32_t rises, uint32_t falls) {
        row.value.store(value, std::memory_order_relaxed);
        if (rises) row.rises.fetch_add(rises, std::memory_order_relaxed);
        if (falls) row.falls.fetch_add(falls, std::memory_order_relaxed);
        row.blocks.fetch_add(1, std::memory_order_release);
    };
    std::vector<std::vector<float>> observed;
    auto poll = [&](unsigned expected_sentinels) {
        sender.start();
        const auto deadline = std::chrono::steady_clock::now() + 2s;
        while (historic_sentinels.load(std::memory_order_acquire) < expected_sentinels &&
               std::chrono::steady_clock::now() < deadline)
            std::this_thread::sleep_for(1ms);
        sender.stop();
        check(historic_sentinels.load() == expected_sentinels, "#631 historical sentinel poll observed");
        observed.push_back(historic_gate_trace);
        std::cerr << "#631 historical poll " << expected_sentinels << " gate:";
        for (float value : historic_gate_trace) std::cerr << ' ' << value;
        std::cerr << '\n';
    };
    publish(gate, 0.f, 0, 0);
    publish(sentinel, 0.f, 0, 0);
    poll(1);
    gate.value.store(1.f, std::memory_order_relaxed);
    publish(sentinel, 1.f, 1, 0);
    poll(2);
    gate.rises.fetch_add(1, std::memory_order_relaxed);
    gate.blocks.fetch_add(1, std::memory_order_release);
    publish(sentinel, 0.f, 0, 1);
    poll(3);
    gate.value.store(0.f, std::memory_order_relaxed);
    publish(sentinel, 1.f, 1, 0);
    poll(4);
    gate.falls.fetch_add(1, std::memory_order_relaxed);
    gate.blocks.fetch_add(1, std::memory_order_release);
    publish(sentinel, 0.f, 0, 1);
    poll(5);
    // Same cumulative expected traces as #635; evaluate after all five polls
    // so the first partial-rise violation cannot hide the falling-block trace.
    const std::vector<std::vector<float>> expected{
        {0.f}, {0.f}, {0.f, 1.f}, {0.f, 1.f}, {0.f, 1.f, 0.f}};
    check(sender.states().at(0).dropped == 0, "#631 historical zero drops");
    check(observed == expected, "#631 gate trace contains only completed-block edges");
}

// A deterministic sender seam observes the actual OSC Out DSP bus. Panic
// while a gate stays high must not inject an extra 0/1 pair on the wire.
void test_osc_out_held_gate_reset_sender() {
    Json config = {{"port", 9001}, {"rows", Json::array()}, {"notes", {{"enabled", false}}}};
    config["rows"].push_back({{"kind", "gate"}});
    for (int i = 1; i < 8; ++i) config["rows"].push_back({{"enabled", false}});
    const Json patch = {{"modules", Json::array({{{"id", 19}, {"module", "osc.out"}, {"config", config}}})}};
    injected_calls.store(0, std::memory_order_relaxed);
    injected_values.fill(-1.f);
    wirescape::osc::OutHost sender(patch.dump(), accept_outgoing);
    auto *bus = sender.buses().at(19);

    wirescape::osc::OutConfiguration cfg;
    cfg.rows[0].kind = 1;
    cfg.bus = bus;
    ws2_config setup{sizeof(setup), 48000., 16, 16, 1,
                     reinterpret_cast<const uint8_t *>(&cfg), uint32_t(sizeof(cfg))};
    ws2_host host{};
    host.struct_size = sizeof(host);
    wirescape::osc::OscOut module;
    check(module.prepare(ws::Setup{setup, host}), "OSC Out gate module accepts test bus");
    module.reset();
    float level = 0.f;
    const float *channel[] = {&level};
    std::array<ws2_signal, 9> inputs{};
    inputs[0] = {sizeof(ws2_signal), channel, 1, WS2_CONNECTED | WS2_CONSTANT};
    ws2_process context{};
    context.frames = 1;
    context.input_count = uint32_t(inputs.size());
    context.inputs = inputs.data();
    ws::Block block(context);

    auto consume = [&](uint32_t expected) {
        sender.start();
        const auto deadline = std::chrono::steady_clock::now() + 2s;
        while (injected_calls.load(std::memory_order_acquire) < expected &&
               std::chrono::steady_clock::now() < deadline)
            std::this_thread::sleep_for(5ms);
        sender.stop();
        check(injected_calls.load(std::memory_order_acquire) == expected,
              "sender publishes the expected gate level once");
    };
    module.process(block); // cold start: publish low as the initial value
    consume(1);
    level = 1.f;
    module.process(block); // a real rising edge
    consume(2);
    check(bus->rows[0].rises == 1 && bus->rows[0].falls == 0,
          "before panic, only the actual rise is counted");

    module.reset(); // panic while the source continues holding high
    module.process(block);
    check(bus->rows[0].rises == 1 && bus->rows[0].falls == 0,
          "held-high panic cannot invent a rise or fall");
    level = 0.f;
    module.process(block); // a real falling edge must still be transmitted
    check(bus->rows[0].rises == 1 && bus->rows[0].falls == 1,
          "first fall after panic is counted exactly once");
    consume(3);
    check(injected_values[0] == 0.f && injected_values[1] == 1.f && injected_values[2] == 0.f,
          "sender emits only the initial low, actual rise and actual fall");
}

// A70/A73 E7c-a: larger blocks rebuild. Delay v2 is the separate E7c-b
// follow-up; its full tail witness is preserved at c0219b5. Observe the actual DSP path
// against an uninterrupted, equally stepped twin, not merely a successful
// reply or a serialized version word. Fake streams never open real devices.
using A70Samples = std::array<std::vector<float>, 2>;
struct A70Witness {
    A70Samples before, after, wide;
    Json fresh = Json::array();
    bool held_before = false, held_after = false, released = false;
};
A70Witness a70_buffer_witness(const std::filesystem::path &root, bool rebuild) {
    Options options;
    options.audio = true;
    options.rate = 48000;
    options.block = 256;
    options.settings = (root / (rebuild ? "a70-rebuild.json" : "a70-control.json")).string();
    fake::outputs = {output("A70 stereo", 0, true)};
    fake::render = true;
    Session s(options);
    s.start();
    auto call = [&](const char *id, const char *type, const Json &payload = Json::object()) {
        Json command = {{"v", 0}, {"id", id}, {"type", type}};
        command.update(payload);
        return s.reply({command, {}, {}});
    };
    const Json patch = {
        {"format", "wirescape.native.patch"}, {"version", 2},
        {"modules", Json::array({
            {{"id", 1}, {"module", "essentials.output"}},
            {{"id", 4}, {"module", "host.keyboard"}, {"parameters", {{"voices", 1}}}},
            {{"id", 5}, {"module", "essentials.adsr"},
             {"parameters", {{"attack", .0001}, {"decay", .01}, {"sustain", .7}, {"release", .01}}}},
            {{"id", 6}, {"module", "essentials.vco"}, {"parameters", {{"frequency", 431.}}}},
            {{"id", 7}, {"module", "essentials.vca"}}
        })},
        {"connections", Json::array({
            {{"kind", "signal"}, {"from", {{"module", 4}, {"port", "gate"}}},
                                 {"to", {{"module", 5}, {"port", "gate"}}}},
            {{"kind", "signal"}, {"from", {{"module", 5}, {"port", "envelope"}}},
                                 {"to", {{"module", 7}, {"port", "gain_cv"}}}},
            {{"kind", "signal"}, {"from", {{"module", 6}, {"port", "audio"}}},
                                 {"to", {{"module", 7}, {"port", "audio"}}}},
            {{"kind", "signal"}, {"from", {{"module", 7}, {"port", "audio"}}},
                                 {"to", {{"module", 1}, {"port", "audio"}}}}
        })}
    };
    check(call("a70-load", "loadGraph", {{"patch", patch}})["ok"] == true,
          "A70 patch loads");
    check(bool(fake::freeze_render), "A70 fake callback can quiesce");
    fake::freeze_render();
    fake::render = false;
    // The paced load handoff can have rendered a different number of blocks
    // in each twin. Reset both once, BEFORE either witness starts. From here
    // all samples are deterministic and manually advanced by the same owner.
    check(app_engine_reset(fake::engine) == WS2_OK, "A70 align cold twin state");
    check(call("a70-held", "noteOn", {{"note", 60}, {"velocity", .8}})["ok"] == true,
          "A70 initial held note");
    std::array<float, 512> bus{};
    auto step = [&](uint32_t frames) {
        check(app_engine_render(fake::engine, bus.data(), frames) == WS2_OK,
              "A70 manual render");
    };
    auto raw = [&](uint32_t node, uint32_t port, uint32_t frame) {
        return app_engine_native(fake::engine).output_sample(node, port, 0, frame);
    };
    auto record = [&](A70Samples &dst, uint32_t frames) {
        // Inspect the raw node outputs, before the stopped-stream master fade.
        // A70 is a module-state witness; the output-device fade is unchanged.
        constexpr uint32_t nodes[] = {7, 6}; // held-note VCA, free-running VCO
        for (size_t i = 0; i < dst.size(); ++i)
            for (uint32_t f = 0; f < frames; ++f)
                dst[i].push_back(raw(nodes[i], 0, f));
    };
    for (int i = 0; i < 68; ++i) step(256); // retain original held-note warmup
    A70Witness result;
    record(result.before, 256);
    result.held_before = raw(4, 1, 255) == 1.f && raw(5, 0, 255) > .5f;
    if (rebuild) {
        const auto *old = fake::engine;
        const auto reply = call("a70-larger", "setBufferFrames", {{"frames", 512}});
        check(reply["ok"] == true && fake::engine != old && audio(s)["bufferFrames"] == 512,
              "A70 must still take rule 2 and reopen at 512");
        check(reply.contains("result") && reply["result"].contains("freshModules") &&
                  reply["result"]["freshModules"].is_array(),
              "A70 rebuild must report freshModules");
        result.fresh = reply["result"]["freshModules"];
    }
    // Same sample partition on both sides of the edit, even though the
    // rebuilt engine now supports 512. Also exercise the actual larger size.
    for (int i = 0; i < 2; ++i) {
        step(256);
        record(result.after, 256);
    }
    result.held_after = raw(4, 1, 255) == 1.f && raw(5, 0, 255) > .5f;
    // Keep the note held through a real 512-frame
    // block. The uninterrupted 256-frame twin supplies the same 512 samples
    // as two blocks, so this also detects a block-size-dependent discontinuity.
    if (rebuild) {
        step(512);
        record(result.wide, 512);
    } else {
        for (int i = 0; i < 2; ++i) {
            step(256);
            record(result.wide, 256);
        }
    }
    result.held_after = result.held_after &&
        raw(4, 1, rebuild ? 511 : 255) == 1.f &&
        raw(5, 0, rebuild ? 511 : 255) > .5f;
    check(call("a70-release", "noteOff", {{"note", 60}})["ok"] == true,
          "A70 later NOTE_OFF must be accepted");
    if (rebuild) step(512);
    else { step(256); step(256); }
    result.released = raw(4, 1, rebuild ? 511 : 255) == 0.f &&
                      raw(5, 0, rebuild ? 511 : 255) == 0.f;
    s.shutdown();
    return result;
}
void test_a70_buffer_state(const std::filesystem::path &root) {
    const auto reference = a70_buffer_witness(root, false);
    const auto switched = a70_buffer_witness(root, true);
    auto peak = [](const std::vector<float> &samples) {
        float value = 0.f;
        for (float sample : samples) value = (std::max)(value, std::abs(sample));
        return value;
    };
    check(reference.before == switched.before && reference.held_before && switched.held_before,
          "A70 uninterrupted and restart twins must agree before the edit");
    check(reference.held_after && reference.released,
          "A70 uninterrupted note remains held and releases on NOTE_OFF");
    for (size_t i = 0; i < reference.before.size(); ++i) {
        check(peak(reference.before[i]) > .001f && peak(reference.after[i]) > .001f &&
                  peak(reference.wide[i]) > .001f,
              "A70 control must have nontrivial held-note and VCO witnesses");
        std::cout << "A70 raw witness " << i << " before_peak=" << peak(reference.before[i])
                  << " control_peak=" << peak(reference.after[i])
                  << " rebuilt_peak=" << peak(switched.after[i])
                  << " identical=" << (reference.after[i] == switched.after[i])
                  << " wide_control_peak=" << peak(reference.wide[i])
                  << " wide_rebuilt_peak=" << peak(switched.wide[i])
                  << " wide_identical=" << (reference.wide[i] == switched.wide[i]) << '\n';
    }
    std::cout << "A70 freshModules=" << switched.fresh.dump()
              << " held=" << switched.held_after << " released=" << switched.released << std::endl;
    check(switched.held_after, "A70 held note must continue through a larger-buffer rebuild");
    check(reference.after[0] == switched.after[0], "A70 held-note waveform continues exactly");
    check(reference.after[1] == switched.after[1], "A70 VCO phase continues exactly");
    check(reference.wide[0] == switched.wide[0], "A70 held waveform at 512 matches two 256 blocks");
    check(reference.wide[1] == switched.wide[1], "A70 VCO phase at 512 matches two 256 blocks");
    for (const auto &entry : switched.fresh) {
        const uint32_t id = entry.at("moduleId").get<uint32_t>();
        check(id != 4 && id != 5 && id != 6 && id != 7,
              "A70 carried modules must not be named fresh");
    }
    check(switched.released, "A70 restored held-note ID must match later NOTE_OFF");
}

void test_e7_state_restart(const std::filesystem::path &root) {
    Options options;
    options.audio = true; // link-time fake only
    options.settings = (root / "e7-state.json").string();
    fake::outputs = {output("E7 stereo", 0, true)};
    fake::render = true;
    Session s(options);
    s.start();
    auto call = [&](const char *id, const char *type, const Json &payload = Json::object()) {
        Json cmd = {{"v", 0}, {"id", id}, {"type", type}};
        cmd.update(payload);
        return s.reply({cmd, {}, {}});
    };
    const Json patch = {
        {"format", "wirescape.native.patch"}, {"version", 2},
        {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}},
                                 {{"id", 2}, {"module", "essentials.noise"}},
                                 {{"id", 3}, {"module", "essentials.vco"}},
                                 {{"id", 4}, {"module", "essentials.clock"},
                                  {"parameters", {{"bpm", 300}, {"ticks_per_beat", 24}, {"duty", 0.5}}}},
                                 {{"id", 5}, {"module", "essentials.function_envelope"},
                                  {"parameters", {{"rise", 0.0001}, {"fall", 0.5}}}},
                                 {{"id", 6}, {"module", "host.keyboard"},
                                  {"parameters", {{"voices", 1}}}},
                                 {{"id", 7}, {"module", "essentials.adsr"},
                                  {"parameters", {{"attack", 0.0001}, {"decay", 0.01}, {"sustain", 0.7}}}}})},
        {"connections", Json::array({{{"kind", "signal"},
                                      {"from", {{"module", 2}, {"port", "audio"}}},
                                      {"to", {{"module", 1}, {"port", "audio"}}}},
                                     {{"kind", "signal"},
                                      {"from", {{"module", 4}, {"port", "clock"}}},
                                      {"to", {{"module", 5}, {"port", "gate"}}}},
                                     {{"kind", "signal"},
                                      {"from", {{"module", 6}, {"port", "gate"}}},
                                      {"to", {{"module", 7}, {"port", "gate"}}}}})}
    };
    check(call("e7-load", "loadGraph", {{"patch", patch}})["ok"] == true,
          "E7 state witness patch must load with a paced fake callback");
    check(bool(fake::freeze_render), "E7 fake must expose its quiescence seam");
    fake::freeze_render();
    fake::render = false; // subsequent fake streams are manually stepped
    const auto state_before_step = app_engine_native(fake::engine).save_state(2);
    std::array<float, 256> samples{};
    check(app_engine_render(fake::engine, samples.data(), uint32_t(samples.size())) == WS2_OK,
          "E7 witness render must advance actual noise state");
    check(call("e7-held", "noteOn", {{"note", 60}, {"velocity", 0.8}})["ok"] == true,
          "E7 hold a keyboard note before the stream edit");
    auto render = [&](uint32_t frames) {
        check(app_engine_render(fake::engine, samples.data(), frames) == WS2_OK,
              "E7 manual witness render must succeed");
    };
    auto witness = [&](uint32_t id, uint32_t port, uint32_t frame) {
        return app_engine_native(fake::engine).output_sample(id, port, 0, frame);
    };
    // 300 BPM × 24 ticks: 400 samples/cycle. Find a real falling gate
    // with an envelope tail, without depending on the paced startup phase.
    for (int n = 0; n < 160; ++n) {
        render(16);
        if (witness(4, 0, 15) == 0.f && witness(5, 0, 15) > 0.5f &&
            witness(7, 0, 15) > 0.5f) break;
    }
    check(witness(4, 0, 15) == 0.f && witness(5, 0, 15) > 0.5f &&
              witness(7, 0, 15) > 0.5f,
          "E7 witnesses must be a live falling envelope tail and held note");
    const auto clock_state = app_engine_native(fake::engine).save_state(4);
    const auto envelope_state = app_engine_native(fake::engine).save_state(5);
    check(!clock_state.empty() && !envelope_state.empty(), "E7 clock and envelope must serialize state");
    const auto state = app_engine_native(fake::engine).save_state(2);
    check(!state.empty() && state != state_before_step,
          "E7 noise witness must have nontrivial, advancing state");
    const auto *prepared = fake::engine;
    check(call("e7-small", "setBufferFrames", {{"frames", 128}})["ok"] == true &&
              fake::engine == prepared && app_engine_native(fake::engine).save_state(2) == state,
          "E7 smaller buffer must retain both engine and exact quiescent state");
    check(call("e7-fit", "setBufferFrames", {{"frames", 256}})["ok"] == true &&
              fake::engine == prepared && app_engine_native(fake::engine).save_state(2) == state,
          "E7 original prepared capacity must remain usable after a smaller stream");
    check(app_engine_native(fake::engine).save_state(4) == clock_state &&
              app_engine_native(fake::engine).save_state(5) == envelope_state,
          "E7 smaller buffer must preserve clock and tail state exactly");
    render(16);
    check(witness(7, 0, 15) > 0.5f && witness(5, 0, 15) > 0.5f,
          "E7 smaller buffer must render the held note envelope and tail after resume");
    const auto next_noise = app_engine_native(fake::engine).save_state(2);
    const auto next_clock = app_engine_native(fake::engine).save_state(4);
    const auto next_envelope = app_engine_native(fake::engine).save_state(5);
    // Deliberately exercise the engine's unsupported-blob retention: this is
    // not a live VCO snapshot and must not be carried by E7 as one.
    const std::vector<uint8_t> unsupported{99, 0, 0, 0};
    check(app_engine_native(fake::engine).load_state(3, unsupported) == WS2_UNSUPPORTED &&
              app_engine_native(fake::engine).preserved_state(3) == unsupported,
          "E7 unsupported state witness must be retained by the old engine");
    auto larger = call("e7-large", "setBufferFrames", {{"frames", 512}});
    check(larger["ok"] == true && fake::engine != prepared,
          "E7 larger buffer must rebuild a runnable engine");
    check(app_engine_native(fake::engine).save_state(2) == next_noise,
          "E7 larger buffer must restore nontrivial stopped-instance state");
    check(app_engine_native(fake::engine).save_state(4) == next_clock &&
              app_engine_native(fake::engine).save_state(5) == next_envelope &&
              app_engine_native(fake::engine).preserved_state(3).empty(),
          "E7 larger buffer must restore clock/tail but not stale unsupported bytes");
    render(16);
    check(witness(5, 0, 15) > 0.5f,
          "E7 larger buffer must render the saved envelope tail after resume");
    const auto restored_noise = app_engine_native(fake::engine).save_state(2);
    const Json fresh_vco = Json::array({{{"moduleId", 3}, {"module", "essentials.vco"}}});
    const Json fresh_rate = Json::array({{{"moduleId", 3}, {"module", "essentials.vco"}},
                                       {{"moduleId", 6}, {"module", "host.keyboard"}},
                                       {{"moduleId", 7}, {"module", "essentials.adsr"}}});
    check(larger["result"]["freshModules"] == fresh_vco,
          "E7 must name only the deliberately unsupported VCO, not restored modules");
    auto rate = call("e7-rate", "setSampleRate", {{"hz", 44100}});
    check(rate["ok"] == true && rate["result"]["freshModules"] == fresh_rate &&
              app_engine_native(fake::engine).save_state(2) == restored_noise,
          "E7 rate change must attempt saved state and name the C2-refused voice chain");
    const auto *at_rate = fake::engine;
    fake::rejected_rate = 96000;
    check(call("e7-rate-refused", "setSampleRate", {{"hz", 96000}})["ok"] == false &&
              fake::engine == at_rate && app_engine_native(fake::engine).save_state(2) == restored_noise &&
              audio(s)["sampleRate"] == 44100,
          "E7 refused rate must roll back the original graph and state");
    fake::rejected_rate = 0;
    fake::outputs.push_back(output("E7 second stereo", 1));
    auto device = call("e7-device", "selectAudioDevice", {{"deviceId", "E7 second stereo"}});
    check(device["ok"] == true && !device.contains("result") && fake::engine == at_rate &&
              app_engine_native(fake::engine).save_state(2) == restored_noise,
          "E7 ordinary device switch must retain the prepared engine");
    fake::accept_block = 128;
    fake::preferred = 128;
    auto smaller_driver = call("e7-driver-small", "selectAudioDevice", {{"deviceId", "E7 stereo"}});
    check(smaller_driver["ok"] == true && !smaller_driver.contains("result") &&
              fake::engine == at_rate && audio(s)["bufferFrames"] == 128 &&
              app_engine_native(fake::engine).save_state(2) == restored_noise,
          "E7 preferred driver size inside prepared capacity must retain the graph");
    fake::accept_block = 1024;
    fake::preferred = 1024;
    auto larger_driver = call("e7-driver-large", "selectAudioDevice", {{"deviceId", "E7 second stereo"}});
    check(larger_driver["ok"] == true && larger_driver["result"]["freshModules"] == Json::array() &&
              fake::engine != at_rate && audio(s)["bufferFrames"] == 1024 &&
              app_engine_native(fake::engine).save_state(2) == restored_noise,
          "E7 preferred driver size beyond capacity must restore matching stopped state");
    // The replacement stream can open successfully, then persistence can fail.
    // Force that exact path; the old device must still accept its old block.
    const auto *before_failed_persist = fake::engine;
    const auto before_failed_gen = s.status()["gen"];
    const auto before_failed_clock = app_engine_native(fake::engine).save_state(4);
    const auto before_failed_envelope = app_engine_native(fake::engine).save_state(5);
    auto read_preferences = [&] {
        std::ifstream file(options.settings);
        Json saved;
        file >> saved;
        return saved;
    };
    const auto before_failed_prefs = read_preferences();
    auto temp = std::filesystem::path(options.settings);
    temp += ".tmp";
    check(std::filesystem::create_directory(temp), "E7 obstruct the temporary settings file");
    fake::accept_block = 2048;
    fake::preferred = 2048;
    fake::accept_block_device = "E7 stereo";
    const auto before_failed_attempts = fake::attempts.size();
    auto failed_persist = call("e7-persist-refused", "selectAudioDevice", {{"deviceId", "E7 stereo"}});
    check(fake::attempts.size() == before_failed_attempts + 3 &&
              fake::blocks[fake::blocks.size() - 3] == 1024 &&
              fake::blocks[fake::blocks.size() - 2] == 2048 &&
              fake::blocks.back() == 1024,
          "E7 must actually open the larger candidate then reopen the original block");
    check(failed_persist["ok"] == false && !failed_persist.contains("result") &&
              fake::engine == before_failed_persist && s.status()["gen"] == before_failed_gen &&
              audio(s)["state"] == "running" && audio(s)["deviceId"] == "E7 second stereo" &&
              audio(s)["bufferFrames"] == 1024 && read_preferences() == before_failed_prefs,
          "E7 failed persistence must restore the original graph, stream and settings");
    check(app_engine_native(fake::engine).save_state(2) == restored_noise &&
              app_engine_native(fake::engine).save_state(4) == before_failed_clock &&
              app_engine_native(fake::engine).save_state(5) == before_failed_envelope,
          "E7 post-open rollback must preserve the original stopped DSP state");
    std::filesystem::remove(temp);
    fake::accept_block_device.clear();
    fake::accept_block = 0;
    fake::preferred = 0;
    s.shutdown();
}


void test_e7_rate_dependent_state_refusal(const std::filesystem::path &root) {
    Options options;
    options.audio = true; // fake backend only
    options.rate = 96000;
    options.settings = (root / "e7-c2.json").string();
    fake::outputs = {output("E7 C2 stereo", 0, true)};
    fake::render = true;
    Session s(options);
    s.start();
    auto call = [&](const char *id, const char *type, const Json &payload = Json::object()) {
        Json cmd = {{"v", 0}, {"id", id}, {"type", type}};
        cmd.update(payload);
        return s.reply({cmd, {}, {}});
    };
    const Json patch = {
        {"format", "wirescape.native.patch"}, {"version", 2},
        {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}},
                                 {{"id", 2}, {"module", "essentials.noise"}},
                                 {{"id", 3}, {"module", "sound.spectral"}}})},
        {"connections", Json::array({{{"kind", "signal"},
                                      {"from", {{"module", 2}, {"port", "audio"}}},
                                      {"to", {{"module", 3}, {"port", "a"}}}},
                                     {{"kind", "signal"},
                                      {"from", {{"module", 3}, {"port", "audio"}}},
                                      {"to", {{"module", 1}, {"port", "audio"}}}}})}
    };
    check(call("c2-load", "loadGraph", {{"patch", patch}})["ok"] == true,
          "C2 spectral witness must prepare at 96 kHz");
    check(bool(fake::freeze_render), "C2 callback quiescence seam available");
    fake::freeze_render();
    fake::render = false;
    // Spectral v2 state: second LE u32 is hop_pos. At default size 2048
    // the hop is 1024 at 96 kHz and 512 at 48 kHz. Obtain a valid live
    // high-rate position that the lower-rate module explicitly refuses.
    auto hop = [](const std::vector<uint8_t> &bytes) {
        check(bytes.size() == 13 * sizeof(uint32_t), "C2 spectral v2 state shape");
        return uint32_t(bytes[4]) | (uint32_t(bytes[5]) << 8) |
               (uint32_t(bytes[6]) << 16) | (uint32_t(bytes[7]) << 24);
    };
    std::array<float, 64> samples{};
    auto state = app_engine_native(fake::engine).save_state(3);
    for (unsigned n = 0; n < 32 && hop(state) < 512; ++n) {
        check(app_engine_render(fake::engine, samples.data(), uint32_t(samples.size())) == WS2_OK,
              "C2 step the live high-rate spectral engine");
        state = app_engine_native(fake::engine).save_state(3);
    }
    check(hop(state) >= 512 && hop(state) < 1024,
          "C2 real saved hop must be valid at 96 kHz but invalid at 48 kHz");
    const auto noise = app_engine_native(fake::engine).save_state(2);
    const auto *before = fake::engine;
    const auto reply = call("c2-rate", "setSampleRate", {{"hz", 48000}});
    check(reply["ok"] == true && fake::engine != before &&
              audio(s)["sampleRate"] == 48000 && audio(s)["state"] == "running",
          "C2 actual module refusal must not refuse the stream change");
    const Json refused = Json::array({{{"moduleId", 3}, {"module", "sound.spectral"}}});
    check(reply["result"]["freshModules"] == refused &&
              hop(app_engine_native(fake::engine).save_state(3)) == 0 &&
              app_engine_native(fake::engine).save_state(2) == noise,
          "C2 refused Spectral starts fresh and compatible Noise restores");
    check(app_engine_render(fake::engine, samples.data(), uint32_t(samples.size())) == WS2_OK,
          "C2 new stream remains runnable after the module refusal");
    s.shutdown();
}

// A81 synthetic slot fixture: no registration in the shipped catalogue.
// A prepared candidate really replaces the DSP by changing its config bytes;
// the same control-side event staging helper as Session is exercised.
struct A81Source {
    static constexpr ws::Info info{"test.a81", "A81 synthetic", 1};
    static constexpr std::array<ws2_port, 0> inputs{};
    static constexpr std::array outputs{ws::port("out", "Out", WS2_CV_BI)};
    static constexpr std::array<ws2_param, 0> params{};
    static constexpr std::array fields{
        ws::data_field<WS2_F_F32, float>("value", "Value", 0, ws::data_range(0, 1, .25))
    };
    static constexpr std::array data_slots{ws::data_slot<float>("settings", "Settings", fields)};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &b) {
        uint32_t serial = 0;
        const auto *value = b.data<float>(0, serial);
        b.out(0).set_channels(1);
        b.out(0).mark_constant();
        b.out(0).ch(0)[0] = value ? *value : 0.f;
    }
};
void test_a81_synthetic_slot() {
    using wirescape::engine2::Engine;
    auto d = *ws::Module<A81Source>::descriptor();
    d.replace_fade_ms = 500;
    wirescape::engine2::Config cfg;
    cfg.max_block = 4096;
    auto packed = [](float value) {
        std::vector<uint8_t> bytes(sizeof(value));
        std::memcpy(bytes.data(), &value, sizeof(value));
        return bytes;
    };
    auto make = [&](uint8_t shape, float value) {
        auto e = std::make_unique<Engine>(cfg);
        check(e->add_node(1, &d, {shape}) && e->output(1, 0, 0), "A81 synthetic slot node");
        check(e->set_data_packed(1, 0, packed(value)) == WS2_OK &&
              e->register_producer() == 0 && e->prepare(), "A81 synthetic candidate prepares");
        return e;
    };
    auto live = make(1, .25f);
    std::array<float, 4096> samples{};
    float *output[] = {samples.data()};
    auto render = [&](uint32_t frames) {
        check(live->render(output, 1, frames) == WS2_OK, "A81 synthetic render");
    };
    auto publish = [&](Engine &next) {
        std::atomic<bool> finished{false};
        bool accepted = false;
        std::thread control([&] {
            accepted = live->replan(next, 200000000);
            finished.store(true, std::memory_order_release);
        });
        do {
            render(1);
            std::this_thread::sleep_for(100us);
        } while (!finished.load(std::memory_order_acquire));
        control.join();
        check(accepted && live->replacement_tail_pending(1), "A81 actual replacement with predecessor");
    };
    auto retire = [&] {
        for (unsigned i = 0; i < 25 && live->replacement_tail_pending(1); ++i) render(4096);
        check(!live->replacement_tail_pending(1), "A81 predecessor retired");
    };
    render(1);
    auto first = make(2, .25f);
    publish(*first);
    auto blocked = make(3, .25f);
    check(!live->replan(*blocked, 200000000) &&
          live->replacement_blocked_ids() == std::vector<uint32_t>{1}, "A81 genuine A75 busy");
    std::map<uint32_t, PendingConfig> pending{{1, {"test.a81", "a81", Json{{"shape", 3}},
        std::chrono::steady_clock::now() + 2s}}};
    Json events = Json::array();
    check(live->set_data_packed(1, 0, packed(.5f)) == WS2_OK, "A81 retained setData");
    render(1);
    stage_data_supersession(pending, events, "synthetic", 1, true, false, 1);
    check(pending.size() == 1 && events.empty() && live->replacement_tail_pending(1),
          "A81 retained data does not supersede");
    retire();
    auto unchanged = make(4, .5f);
    publish(*unchanged);
    stage_data_supersession(pending, events, "synthetic", 1, false, true, 2);
    check(pending.size() == 1 && events.empty(), "A81 unchanged data replacement does not supersede");
    retire();
    auto changed = make(5, .75f);
    // Stage before publication like Session, but only adopt on success.
    auto staged = pending;
    auto staged_events = events;
    stage_data_supersession(staged, staged_events, "synthetic", 1, true, true, 3);
    check(pending.size() == 1 && events.empty(), "A81 pending unchanged before publish");
    publish(*changed);
    pending.swap(staged);
    events.swap(staged_events);
    render(1);
    check(live->output_sample(1, 0, 0, 0) == .75f, "A81 replacement sees candidate data");
    const Json expected = {{"v", 0}, {"session", "synthetic"}, {"type", "configDeferred"},
        {"deferId", "a81"}, {"moduleId", 1}, {"outcome", "superseded"}, {"generation", "3"}};
    check(pending.empty() && events.size() == 1 && events[0] == expected,
          "A81 changed data replacement emits correlated superseded");
    stage_data_supersession(pending, events, "synthetic", 1, true, true, 4);
    check(events.size() == 1, "A81 no duplicate terminal event");
}

// A78: use the existing fake stream, then freeze the paced callback and
// advance the graph one frame at a time. No wall-clock sleep stands in for
// retirement, and no real device is opened.
void test_a78_deferred_config(const std::filesystem::path &root) {
    Options options;
    options.audio = true;
    options.block = 1024;
    options.settings = (root / "a78-deferred.json").string();
    fake::outputs = {output("A78 stereo", 0, true)};
    fake::render = true;
    Session s(options);
    s.start();
    auto call = [&](const char *type, const Json &payload) {
        Json command = {{"v", 0}, {"id", "a78"}, {"type", type}};
        command.update(payload);
        return s.reply({command, {}, {}});
    };
    auto groove = [](int bpm) {
        return Json{{"id", 2}, {"module", "sequencing.groove"},
                    {"config", {{"version", 1}, {"bpm", bpm},
                        {"tracks", Json::array({{{"steps", Json::array({{{"kind", "note"},
                            {"key", 60}, {"velocity", 1}}})}}})}}}};
    };
    Json patch = {{"format", "wirescape.native.patch"}, {"version", 2},
                  {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}},
                                           groove(120), {{"id", 3}, {"module", "essentials.lfo"}}})},
                  {"connections", Json::array({{{"kind", "signal"},
                     {"from", {{"module", 2}, {"port", "t1_mod1"}}},
                     {"to", {{"module", 1}, {"port", "audio"}}}}})}};
    const uint16_t port = select_loopback_osc_port();
    patch["modules"].push_back({{"id", 4}, {"module", "osc.in"},
        {"config", {{"port", port}, {"lan", false},
            {"rows", Json::array({{{"pattern", "/reconnect"}, {"kind", "cv"}}})}}}});
    check(call("loadGraph", {{"patch", patch}})["ok"] == true, "A78 graph loads");
    check(bool(fake::freeze_render), "A78 fake callback available");
    fake::freeze_render();
    fake::render = false;
    auto *const live = fake::engine;
    auto &graph = app_engine_native(live);
    const auto stops = fake::stopped, exchanges = fake::exchanges;
    // For an accepted live publication, a render owner advances only tiny
    // blocks while the control owner executes the real sidecar transaction.
    auto with_render = [&](auto action) {
        std::atomic<bool> done{false}, render_ok{true};
        std::thread renderer([&] {
            float sample = 0;
            for (unsigned i = 0; i < 128 && !done.load(std::memory_order_acquire); ++i) {
                if (app_engine_render(live, &sample, 1) != WS2_OK) render_ok.store(false);
                std::this_thread::sleep_for(200us);
            }
        });
        try {
            action();
        } catch (...) {
            done.store(true, std::memory_order_release);
            renderer.join();
            throw;
        }
        done.store(true, std::memory_order_release);
        renderer.join();
        check(render_ok.load(), "A78 publication render succeeds");
        check(fake::engine == live && fake::stopped == stops && fake::exchanges == exchanges,
              "A78 never falls back to D5 or reopens the stream");
    };
    auto apply = [&](const Json &p) { return call("applyGraph", {{"patch", p}}); };
    auto edit = [&](int bpm) {
        auto p = patch;
        p["modules"][1] = groove(bpm);
        return p;
    };
    auto accept = [&](const Json &p) {
        Json reply;
        with_render([&] { reply = apply(p); });
        check(reply["ok"] == true && reply["result"]["path"] == "live",
              ("A78 live commit: " + reply.dump()).c_str());
        return reply["gen"];
    };
    auto retire = [&] {
        std::array<float, 1024> samples{};
        for (unsigned i = 0; i < 25 && graph.replacement_tail_pending(2); ++i)
            check(app_engine_render(live, samples.data(), uint32_t(samples.size())) == WS2_OK,
                  "A78 render predecessor retirement");
        check(!graph.replacement_tail_pending(2), "A78 predecessor retired by samples");
    };
    auto deferred = [&](const Json &p, const Json &gen) {
        const auto reply = apply(p);
        check(reply["ok"] == false && reply["code"] == "busy" &&
              reply["gen"] == gen && reply["deferred"] == true &&
              reply["deferId"].is_string(), ("A78 deferred refusal: " + reply.dump()).c_str());
        return reply["deferId"];
    };
    auto terminal = [&](const Json &id, const char *outcome, const Json &gen) {
        const auto events = s.take_config_events();
        check(events.size() == 1 && events[0]["type"] == "configDeferred" &&
              events[0]["deferId"] == id && events[0]["moduleId"] == 2 &&
              events[0]["outcome"] == outcome && events[0]["generation"] == gen,
              ("A78 correlated terminal event: " + events.dump()).c_str());
        check(s.take_config_events().empty(), "A78 terminal event is drained exactly once");
    };
    auto current = edit(140);
    auto gen = accept(current);
    check(graph.replacement_tail_pending(2), "A78 unfinished predecessor witness");
    send_local_osc(port);
    auto route = [&] { return s.status()["status"]["osc"]["routes"].at(0); };
    const auto received_deadline = std::chrono::steady_clock::now() + 1s;
    while (route()["received"].get<uint64_t>() == 0 &&
           std::chrono::steady_clock::now() < received_deadline)
        std::this_thread::sleep_for(5ms);
    const auto before_route = route();
    check(before_route["state"] == "listening" && before_route["received"].get<uint64_t>() == 1,
          "A78 active ingress route receives loopback witness");
    // Legacy client cannot silently acquire pending work.
    const auto legacy = apply(edit(160));
    check(legacy["ok"] == false && legacy["code"] == "busy" && legacy["gen"] == gen &&
          !legacy.contains("deferred") && !legacy.contains("deferId") && s.take_config_events().empty(),
          "A80 legacy client gets plain busy");
    check(call("hello", {{"capabilities", Json::array({"configDeferred"})}})["ok"] == true,
          "A80 fake client opts in");
    auto a = deferred(edit(160), gen);
    auto mixed = edit(180);
    mixed["modules"][2]["parameters"] = {{"rate", 2}};
    const auto refused = apply(mixed);
    check(refused["ok"] == false && refused["code"] == "busy" && refused["gen"] == gen &&
          !refused.contains("deferred") && !refused.contains("deferId"),
          ("A78 mixed transaction must not defer: " + refused.dump()).c_str());
    check(s.take_config_events().empty(), "A78 mixed refusal leaves pending request intact");
    auto b = deferred(edit(200), gen);
    check(a != b, "A78 latest edit has new correlation ID");
    terminal(a, "superseded", gen);
    check(route() == before_route, "A78 refused initial/mixed/latest edits preserve active OSC counters and binding");
    // A80: same pending config in a full snapshot does not reapply it.
    auto other = edit(200);
    other["modules"][2]["parameters"] = {{"rate", 3}};
    gen = accept(other);
    check(s.take_config_events().empty() && graph.replacement_tail_pending(2),
          "A80 unrelated snapshot retains pending config");
    // Keep the unrelated authored change in all subsequent snapshots.
    patch["modules"][2]["parameters"] = {{"rate", 3}};
    // No frames advance while polling. The graph may not commit or emit.
    auto now = std::chrono::steady_clock::now();
    const auto after_other = route();
    for (unsigned i = 0; i < 4; ++i) {
        s.poll(now);
        check(s.status()["gen"] == gen && s.take_config_events().empty() &&
              graph.replacement_tail_pending(2) && route() == after_other, "A78 poll before retirement is inert");
    }
    retire();
    with_render([&] { s.poll(now); });
    gen = s.status()["gen"];
    terminal(b, "applied", gen);
    // The exact applied document is now a no-op; no replacement or stale retry.
    current = edit(200);
    retire();
    const auto reply = [&] { Json r; with_render([&] { r = apply(current); }); return r; }();
    check(reply["ok"] == true && reply["result"]["replaced"].empty(),
          "A78 latest config actually committed");
    // A second predecessor, explicit revert, then removal, each under a
    // manually held tail. Expiry uses the injected control clock.
    current = edit(220);
    gen = accept(current);
    a = deferred(edit(240), gen);
    gen = accept(current);
    terminal(a, "superseded", gen);
    retire();
    current = edit(250);
    gen = accept(current);
    a = deferred(edit(260), gen);
    s.poll(std::chrono::steady_clock::now() + 3s);
    terminal(a, "failed", gen);
    check(s.status()["gen"] == gen, "A78 deadline leaves document unchanged");
    retire();
    current = edit(270);
    gen = accept(current);
    a = deferred(edit(280), gen);
    auto removed = current;
    removed["modules"].erase(1);
    removed["connections"] = Json::array();
    gen = accept(removed);
    terminal(a, "superseded", gen);
    retire();
    s.poll(std::chrono::steady_clock::now() + 3s);
    check(s.status()["gen"] == gen && s.take_config_events().empty(),
          "A78 removed ID cannot be resurrected");
    // Two independently blocked IDs share one request-level defer ID.
    // Use fresh IDs in the same namespace and the same real Groove module.
    auto multi = removed;
    auto first = groove(120), second = groove(120);
    first["id"] = 5;
    second["id"] = 6;
    multi["modules"].push_back(first);
    multi["modules"].push_back(second);
    // Each signal input accepts one connection. Give the two predecessors
    // independent output paths so one can retire while the other fades.
    multi["modules"].push_back({{"id", 7}, {"module", "essentials.output"}});
    multi["outputs"] = Json::array({{{"module", 1}, {"port", "audio"}, {"bus_channel", 0}},
                                    {{"module", 7}, {"port", "audio"}, {"bus_channel", 1}}});
    for (auto id : {5, 6}) multi["connections"].push_back({{"kind", "signal"},
        {"from", {{"module", id}, {"port", "t1_mod1"}}},
        {"to", {{"module", id == 5 ? 1 : 7}, {"port", "audio"}}}});
    gen = accept(multi);
    for (auto &m : multi["modules"]) if (m["id"] == 5) m["config"]["bpm"] = 140;
    gen = accept(multi);
    std::array<float, 1024> samples{};
    // Separate the two replacement starts by 480 samples, not wall time.
    check(app_engine_render(live, samples.data(), 480) == WS2_OK, "A80 stagger replacements");
    check(graph.replacement_tail_pending(5), "A80 first predecessor still fading");
    for (auto &m : multi["modules"]) if (m["id"] == 6) m["config"]["bpm"] = 140;
    gen = accept(multi);
    check(graph.replacement_tail_pending(5) && graph.replacement_tail_pending(6),
          "A80 both predecessor tails held");
    auto both = multi;
    for (auto &m : both["modules"]) if (m["id"] == 5 || m["id"] == 6) m["config"]["bpm"] = 160;
    const auto shared = deferred(both, gen);
    // Retire only the first predecessor, then prove its completion does not
    // wait for the other ID. Render in single frames to stop at the boundary.
    for (unsigned i = 0; i < 25000 && graph.replacement_tail_pending(5); ++i)
        check(app_engine_render(live, samples.data(), 1) == WS2_OK, "A80 first retirement");
    check(!graph.replacement_tail_pending(5) && graph.replacement_tail_pending(6),
          "A80 first retired, second still fading");
    const auto multi_now = std::chrono::steady_clock::now();
    auto expect_applied = [&](uint32_t id) {
        with_render([&] { s.poll(multi_now); });
        gen = s.status()["gen"];
        const auto events = s.take_config_events();
        check(events.size() == 1 && events[0]["deferId"] == shared &&
              events[0]["moduleId"] == id && events[0]["outcome"] == "applied" &&
              events[0]["generation"] == gen, ("A80 independent terminal event: " + events.dump()).c_str());
    };
    expect_applied(5);
    check(graph.replacement_tail_pending(6), "A80 other predecessor remains live after first completion");
    for (unsigned i = 0; i < 25 && graph.replacement_tail_pending(6); ++i)
        check(app_engine_render(live, samples.data(), uint32_t(samples.size())) == WS2_OK, "A80 second retirement");
    check(!graph.replacement_tail_pending(6), "A80 second predecessor retired");
    expect_applied(6);
    s.poll(multi_now);
    check(s.take_config_events().empty() && s.status()["gen"] == gen,
          "A80 no duplicate multi-ID completions");
    s.shutdown();
}

int main() {
    const auto root = std::filesystem::temp_directory_path() /
                      ("wirescape-audio-recovery-" + std::to_string(app_engine_clock_ns()));
    struct Cleanup {
        std::filesystem::path path;
        ~Cleanup() { std::filesystem::remove_all(path); }
    } cleanup{root};
    try {
        std::filesystem::create_directories(root);
        test_631_historical_gate_snapshot_interleaving();
        test_osc_out_budget();
        test_osc_out_held_gate_reset_sender();
        using wirescape::audio::classify_rates;
        const auto supported = classify_rates({0, -1, 0}, -1);
        const auto invalid = classify_rates({-1, -1, -1}, -1);
        const auto busy = classify_rates({-2, -2, -2}, -1);
        const auto mixed = classify_rates({0, -1, -2}, -1);
        check(supported.known && supported.rates == std::vector<uint32_t>{44100, 96000},
              "successful/invalid-rate results produce the exact supported set");
        check(invalid.known && invalid.rates.empty(), "only invalid-rate results prove no supported rate");
        check(!busy.known && busy.rates.empty() && !mixed.known && mixed.rates.empty(),
              "busy/unknown errors omit the set, including mixed success and unknown results");
        // The UI's driver picker receives a real host-API string through the
        // sidecar protocol, exercised here with link-time fakes (no devices opened).
        const auto opens_before_list = fake::attempts.size();
        fake::outputs = {{"ASIO|ASIO4ALL v2", "ASIO4ALL v2", "ASIO", 7, false, "ASIO", 2, {48000}, true, ""}};
        const auto asio_list = audio_devices("", false);
        check(asio_list.size() == 1 && asio_list[0]["hostApi"] == "ASIO" && asio_list[0]["backend"] == "ASIO" &&
                  asio_list[0]["id"] == "ASIO|ASIO4ALL v2",
              "ASIO fake host API is published with its stable device ID");
        check(fake::attempts.size() == opens_before_list, "listAudioDevices never opens a fake or real stream");

        const auto missing_asio = wirescape::audio::unavailable_asio_drivers(
            {"ASIO4ALL v2", "FlexASIO"}, {{"ASIO4ALL v2", "ASIO"}, {"Headphones", "Windows WASAPI"}});
        check(missing_asio == std::vector<std::string>{"FlexASIO"},
              "registry drivers missing from PortAudio are distinct, never selectable devices");
        std::vector<std::string> many_asio;
        many_asio.reserve(30);
        for (int i = 0; i < 30; ++i) many_asio.push_back("Unseen ASIO " + std::to_string(i));
        check(wirescape::audio::unavailable_asio_drivers(many_asio, {}).size() == 16,
              "registry diagnostics are limited to sixteen entries");
        const std::string long_asio = std::string(63, 'a') + "\xc3\xa9" + "driver";
        const auto clipped = wirescape::audio::unavailable_asio_drivers({long_asio, long_asio}, {});
        check(clipped.size() == 1 && clipped.front() == std::string(63, 'a'),
              "ASIO names truncate at UTF-8 boundaries and are deduplicated");
        Options options;
        options.audio = true; // fake linked service, never the physical backend
        options.settings = (root / "settings.json").string();
        std::ofstream(options.settings) << R"({"audioDeviceId":"Remembered","opaque":17})";
        fake::outputs = {output("Other default", 0, true)};
        const auto base = std::chrono::steady_clock::time_point{};
        {
            Session s(options);
            s.start(base);
            check(audio(s)["state"] == "reconnecting", "missing remembered output must retry");
            check(audio(s)["deviceId"].is_null(), "missing output must not be fabricated");
            check(fake::attempts == std::vector<std::string>{"Remembered"}, "must not open default");
            for (int i = 0; i < 100; ++i) s.poll(base); // no busy-spin opens
            check(fake::attempts.size() == 1, "repeated polls before deadline must not reopen");
            s.poll(base + 100ms);
            check(fake::attempts.size() == 2, "first backoff expires");
            s.poll(base + 299ms);
            check(fake::attempts.size() == 2, "failed retries increase backoff");
            fake::outputs.push_back(output("Remembered", 9, false));
            check(s.poll(base + 300ms), "recovery must notify devices");
            check(audio(s)["state"] == "running" && audio(s)["deviceId"] == "Remembered", "identity recovered");
            const auto token = s.status()["session"];
            auto *const graph = fake::engine;
            fake::enumeration_throws = true;
            s.poll(base + 310ms);
            check(audio(s)["state"] == "running" && fake::stopped == 0,
                  "enumeration exception must preserve healthy stream");
            fake::enumeration_throws = false;
            fake::outputs.push_back(output("Remembered", 10, false));
            s.poll(base + 320ms);
            check(audio(s)["state"] == "running" && fake::stopped == 0,
                  "duplicate identity must preserve healthy stream");
            fake::outputs.pop_back();
            fake::active = false;
            check(audio(s)["state"] == "device-lost", "inactive stream status cannot claim running");
            check(s.poll(base + 400ms), "loss must notify devices");
            check(audio(s)["state"] == "device-lost" && fake::stopped == 1, "loss must retire once");
            fake::outputs = {output("Other default", 0, true)};
            const auto count = fake::attempts.size();
            s.poll(base + 499ms);
            check(audio(s)["state"] == "reconnecting", "loss is followed by reconnecting");
            check(fake::attempts.size() == count, "loss retry must wait");
            s.poll(base + 500ms); // permanently missing for a while
            fake::outputs.push_back(output("Remembered", 2, false)); // changed backend index
            s.poll(base + 700ms);
            check(audio(s)["deviceId"] == "Remembered", "re-add must use identity, not stale index");
            check(fake::engine == graph && s.status()["session"] == token && s.status()["gen"] == "0",
                  "recovery must preserve graph, generation and process session");
            for (const auto &name : fake::attempts) check(name == "Remembered", "no silent fallback");
            std::ifstream saved(options.settings);
            Json settings;
            saved >> settings;
            check(settings["audioDeviceId"] == "Remembered" && settings["opaque"] == 17, "preferences preserved");
            fake::outputs = {output("Other default", 0, true)};
            check(s.poll(base + 800ms) && audio(s)["state"] == "device-lost",
                  "enumerated removal must retire even before backend activity reports loss");
            s.shutdown();
            check(fake::stopped == 2, "clean shutdown retires recovered stream");
        }
        // An available device can refuse opening; permanent failure remains alive
        // and caps retry spacing at five seconds without flooding open attempts.
        fake::refuse = true;
        fake::attempts.clear();
        {
            Session s(options);
            s.start(base);
            auto now = base + 100ms;
            for (int delay : {200, 400, 800, 1600, 3200, 5000}) {
                const auto before = fake::attempts.size();
                s.poll(now);
                check(fake::attempts.size() == before + 1, "retry deadline must attempt once");
                s.poll(now + std::chrono::milliseconds(delay - 1));
                check(fake::attempts.size() == before + 1, "bounded exponential delay");
                now += std::chrono::milliseconds(delay);
            }
            check(audio(s)["state"] == "reconnecting", "permanent refusal keeps reconnecting");
            auto reply = s.reply({{{"v", 0}, {"id", "still-alive"}, {"type", "panic"}}, {}, {}});
            check(reply["ok"] == true && reply["gen"] == "0", "commands remain usable without output");
        }
        // Fresh startup without any preference may choose the actual default once.
        fake::refuse = false;
        options.settings = (root / "fresh.json").string();
        {
            Session s(options);
            s.start();
            check(audio(s)["deviceId"] == "Other default", "initial default selection remains supported");
        }
        // The link-time fake is the sidecar's protocol-level audio seam; no OS
        // audio endpoint is enumerated or opened.
        options.settings = (root / "stream-contract.json").string();
        fake::attempts.clear();
        fake::stopped = 0;
        fake::outputs = {
            {"USB Stereo", "USB Stereo", "FakeAudio", 3, true, "FakeAudio", 2, {44100, 48000, 96000}, true, ""},
            {"Mono DAC", "Mono DAC", "FakeAudio", 4, false, "FakeAudio", 1, {}, false, "mono-output"},
            {"No Output", "No Output", "FakeAudio", 5, false, "FakeAudio", 0, {}, false, "no-output"}};
        {
            Session s(options);
            s.start();
            check(audio(s)["state"] == "running" && audio(s)["deviceId"] == "USB Stereo",
                  "fake stereo output must be playing");
            auto call = [&](const char *id, const char *method, const Json &payload = Json::object()) {
                Json cmd = {{"v", 0}, {"id", id}, {"type", method}};
                cmd.update(payload);
                return s.reply({cmd, {}, {}});
            };
            auto hello = s.hello();
            const auto caps = Json::array({"midiLearn", "telemetry.playhead", "telemetry.monitor", "setSampleRate",
                                           "setBufferFrames", "osc", "osc.out", "applyGraph", "configDeferred"});
            check(hello["audioDevices"].size() == 2 && hello["capabilities"] == caps,
                  "hello must expose the supported device catalogue and methods");
            auto listed = call("list", "listAudioDevices")["result"]["devices"];
            check(listed.size() == 2 && listed[0]["backend"] == "FakeAudio" && listed[0]["outputChannels"] == 2 &&
                      listed[0]["supported"] == true,
                  "backend/channels must be reported honestly");
            check(listed[1]["supported"] == false && listed[1]["unsupportedReason"] == "mono-output" &&
                      std::none_of(listed.begin(), listed.end(), [](const Json &d) { return d["id"] == "No Output"; }),
                  "mono outputs stay disabled and input-only endpoints are filtered");
            fake::queries.clear();
            const auto known_rates = listed[0]["sampleRates"];
            fake::outputs[0].sample_rates.clear();
            fake::outputs[0].supported = false;
            fake::outputs[0].unsupported_reason = "rate-unsupported"; // busy warm enumeration is not evidence
            for (int tick = 0; tick < 8; ++tick) {
                s.poll();
                const auto entry = s.devices()["audioDevices"][0];
                check(entry["supported"] == true && entry["sampleRates"] == known_rates,
                      "repeated warm polls preserve active support and known rates");
                check(!fake::queries.back().probe_rates && fake::queries.back().active_id == "USB Stereo",
                      "warm polls never request format probes and identify the held endpoint");
            }
            const auto active_list = call("held-list", "listAudioDevices")["result"]["devices"];
            check(fake::queries.back().probe_rates && fake::queries.back().active_id == "USB Stereo" &&
                      active_list[0]["supported"] == true && active_list[0]["sampleRates"] == known_rates,
                  "explicit enumeration probes only endpoints not held by the current stream");
            fake::outputs[0].sample_rates = {44100, 48000, 96000};
            fake::outputs[0].supported = true;
            fake::outputs[0].unsupported_reason.clear();
            const auto stopped = fake::stopped;
            const auto playing = fake::engine;
            auto missing = call("missing", "selectAudioDevice", {{"deviceId", "outdated-id"}});
            auto mono = call("mono", "selectAudioDevice", {{"deviceId", "Mono DAC"}});
            fake::outputs.push_back(fake::outputs.front()); // volatile index is never a disambiguator
            s.poll();
            auto duplicate = call("duplicate", "selectAudioDevice", {{"deviceId", "USB Stereo"}});
            check(duplicate["code"] == "duplicate" && fake::stopped == stopped,
                  "duplicate IDs must be refused before stopping the old stream");
            fake::outputs.pop_back();
            s.poll();
            check(missing["ok"] == false && missing["code"] == "not-found" && mono["ok"] == false &&
                      mono["code"] == "refused" && mono["message"] == "mono-output" && fake::stopped == stopped &&
                      fake::engine == playing && audio(s)["deviceId"] == "USB Stereo",
                  "stale/mono refusal must not interrupt the active route");
            auto invalid_rate = call("bad", "setSampleRate", {{"hz", 32000}});
            auto invalid_frames = call("bad-block", "setBufferFrames", {{"frames", 33}});
            check(invalid_rate["code"] == "invalid" && invalid_frames["code"] == "invalid" && fake::stopped == stopped,
                  "out-of-set settings must not stop the stream");
            auto rate = call("rate", "setSampleRate", {{"hz", 44100}});
            check(rate["ok"] == true && rate["gen"] == "1" && audio(s)["state"] == "running" &&
                      audio(s)["sampleRate"] == 44100 && audio(s)["bufferFrames"] == 256,
                  "rate ack requires a running new stream");
            check(rate["result"]["freshModules"] == Json::array(),
                  "E7 rebuild without uncarried instances must report an empty list");
            // E7: the prepared 256-frame engine must survive a smaller stream.
            const auto prepared_engine = fake::engine;
            const auto before_buffer_restart = fake::stopped;
            auto frames = call("frames", "setBufferFrames", {{"frames", 128}});
            check(frames["ok"] == true && frames["gen"] == "2" && audio(s)["sampleRate"] == 44100 &&
                      audio(s)["bufferFrames"] == 128,
                  "buffer restart must keep selected rate");
            check(!frames.contains("result"), "E7 retained engine must omit the rebuild result");
            check(fake::engine == prepared_engine && fake::stopped == before_buffer_restart + 1,
                  "E7 smaller buffer must restart the stream without rebuilding the prepared engine");
            std::ifstream saved(options.settings);
            Json prefs;
            saved >> prefs;
            check(prefs["audio"]["sampleRate"] == 44100 && prefs["audio"]["bufferFrames"] == 128,
                  "persist only after successful restart");
            fake::rejected_rate = 96000;
            const auto gen = s.status()["gen"];
            auto unavailable = call("fail", "setSampleRate", {{"hz", 96000}});
            check(unavailable["ok"] == false && unavailable["code"] == "refused" &&
                      unavailable["message"] == "rate-unsupported" && audio(s)["reason"] == "rate-unsupported" &&
                      s.status()["gen"] == gen && audio(s)["sampleRate"] == 44100 && audio(s)["bufferFrames"] == 128 &&
                      audio(s)["state"] == "running" && audio(s)["deviceId"] == "USB Stereo",
                  "failure must roll back to the playing route");
            fake::rejected_rate = 0;
            std::ifstream saved_after(options.settings);
            Json after;
            saved_after >> after;
            check(after["audio"] == prefs["audio"], "rejected stream config must not persist");
            fake::outputs.push_back({"Rate DAC", "Rate DAC", "FakeAudio", 6, false});
            s.poll();
            fake::rate_refused_id = "Rate DAC";
            auto route_rate = call("route-rate", "selectAudioDevice", {{"deviceId", "Rate DAC"}});
            check(route_rate["code"] == "refused" && route_rate["message"] == "rate-unsupported" &&
                      audio(s)["deviceId"] == "USB Stereo" && audio(s)["state"] == "running" &&
                      audio(s)["reason"] == "rate-unsupported",
                  "rate-refused selection restores the old route");
            const auto opened = fake::attempts.size();
            s.poll(std::chrono::steady_clock::now() + 10s);
            check(fake::attempts.size() == opened, "rate refusal must never retry the rejected route");
            fake::rate_refused_id.clear();
            // A failing candidate must report its real open error in the reply,
            // even though the successful rollback clears status.audio.error.
            const auto before_open_error = fake::attempts.size();
            fake::refuse_id = "Rate DAC";
            auto attempted = call("route-open-error", "selectAudioDevice", {{"deviceId", "Rate DAC"}});
            check(attempted["ok"] == false && attempted["code"] == "unavailable" &&
                      attempted["message"] == "fake unavailable/ambiguous output" &&
                      fake::attempts.size() == before_open_error + 2 && audio(s)["deviceId"] == "USB Stereo" &&
                      audio(s)["state"] == "running" && !audio(s).contains("error"),
                  "failed target open preserves its error and restores the previous playing output");
            // Both a split UTF-8 cap and arbitrary host-codepage bytes must
            // serialize in strict JSON on refusal; rollback keeps audio running.
            for (const auto &diagnostic :
                 {std::string(199, 'x') + "\xc3\xa9", std::string("bad ") + "\xff\xc0\xaf" + " device"}) {
                fake::refuse_id = "Rate DAC";
                fake::open_error = diagnostic;
                auto error = call("utf8-open-error", "selectAudioDevice", {{"deviceId", "Rate DAC"}});
                const auto message = error["message"].get<std::string>();
                check(error["code"] == "unavailable" && message.size() <= 200 && !message.empty() &&
                          audio(s)["deviceId"] == "USB Stereo" && error.dump().find("unavailable") != std::string::npos,
                      "failed ASIO open returns valid, bounded UTF-8 and preserves old playing stream");
                check(Json::parse(error.dump())["message"] == message,
                      "host errors must survive strict protocol JSON serialization");
            }
            fake::open_error.clear();
            fake::refuse_id.clear();
            fake::active = false;
            const auto lost = std::chrono::steady_clock::now() + 20s;
            s.poll(lost);
            check(audio(s)["state"] == "device-lost" && !audio(s).contains("reason"),
                  "real device loss supersedes a previous refused setting");
            s.poll(lost + 100ms);
            check(audio(s)["state"] == "running", "real device loss still reconnects the remembered route");
            s.shutdown();
        }
        options.settings = (root / "unknown-rates.json").string();
        fake::outputs = {output("Unknown stereo", 7, true)};
        fake::outputs[0].sample_rates.clear();
        {
            Session s(options);
            s.start();
            for (int tick = 0; tick < 3; ++tick) s.poll();
            const auto entry = s.devices()["audioDevices"][0];
            check(entry["supported"] == true && !entry.contains("sampleRates") && audio(s)["sampleRate"] == 48000,
                  "unknown supported rates stay omitted while status reports the proven current rate");
            auto changed = s.reply({{{"v", 0}, {"id", "unknown-rate"}, {"type", "setSampleRate"}, {"hz", 44100}}, {}, {}});
            check(changed["ok"] == true && audio(s)["sampleRate"] == 44100,
                  "unknown metadata does not prevent a stream-validated rate change");
        }
        fake::outputs = {output("USB Stereo", 3, true)};
        // An unsupported startup rate is a stable refusal, recoverable by an explicit rate choice.
        options.settings = (root / "startup-rate.json").string();
        fake::rejected_rate = options.rate;
        fake::attempts.clear();
        {
            Session s(options);
            s.start();
            check(audio(s)["state"] == "no-device" && audio(s)["reason"] == "rate-unsupported",
                  "startup rate mismatch is not reconnecting");
            const auto opened = fake::attempts.size();
            s.poll(std::chrono::steady_clock::now() + 10s);
            check(fake::attempts.size() == opened, "startup rate refusal never spins retries");
            auto fixed = s.reply({{{"v", 0}, {"id", "fix-rate"}, {"type", "setSampleRate"}, {"hz", 44100}}, {}, {}});
            check(fixed["ok"] == true && audio(s)["state"] == "running" && !audio(s).contains("reason"),
                  "explicit supported rate recovers without changing identity");
        }
        fake::rejected_rate = 0;
        // A failure after stream start must stop the candidate before its telemetry taps die.
        fake::outputs = {output("USB Stereo", 3, true)};
        fake::render = true;
        options.settings = (root / "post-start-rollback.json").string();
        std::ofstream(options.settings) << R"({"audio":"malformed","opaque":17})";
        {
            Session s(options);
            s.start();
            Json patch = {{"format", "wirescape.native.patch"},
                          {"version", 2},
                          {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}},
                                                   {{"id", 2}, {"module", "essentials.lfo"}}})},
                          {"connections", Json::array()}};
            auto loaded = s.reply({{{"v", 0}, {"id", "tap-graph"}, {"type", "loadGraph"}, {"patch", patch}}, {}, {}});
            check(loaded["ok"] == true, "prepare a graph with live telemetry taps");
            const auto gen = s.status()["gen"];
            auto failed = s.reply({{{"v", 0}, {"id", "post-start"}, {"type", "setSampleRate"}, {"hz", 44100}}, {}, {}});
            check(failed["code"] == "unavailable" && s.status()["gen"] == gen && audio(s)["state"] == "running" &&
                      audio(s)["sampleRate"] == 48000,
                  "post-start preferences failure rolls back the live graph and configuration");
            // Starting a stream does not mean its first callback ran (notably on Windows).
            // Panic marks a pending engine reset; wait for real render progress before an edit.
            const auto completed = fake::completed_blocks.load(std::memory_order_acquire);
            const auto deadline = std::chrono::steady_clock::now() + 1s;
            while (fake::completed_blocks.load(std::memory_order_acquire) == completed &&
                   std::chrono::steady_clock::now() < deadline)
                std::this_thread::yield();
            check(fake::completed_blocks.load(std::memory_order_acquire) > completed,
                  "the restored stream must render before testing its editable graph");
            auto edit = s.reply({{{"v", 0},
                                  {"id", "old-graph"},
                                  {"type", "setParam"},
                                  {"moduleId", 2},
                                  {"paramId", "rate"},
                                  {"value", 4}},
                                 {},
                                 {}});
            if (edit["ok"] != true)
                throw std::runtime_error("the previous document remains editable after rollback: " + edit.dump());
            check(s.telemetry()["telemetry"]["phase"].contains("2"), "previous telemetry storage survives rollback");
        }
        // M2 E1a, 0005 section 3 rule 6: with the output lost, applyGraph takes the D5 path in the
        // same ID namespace and reports `restart`; `replaced` lists only type/config changes.
        fake::outputs = {output("USB Stereo", 3, true)};
        options.settings = (root / "apply-graph-restart.json").string();
        std::ofstream(options.settings) << "{}";
        {
            Session s(options);
            s.start();
            auto send = [&](const char *id, const char *type, const Json &payload) {
                Json cmd = {{"v", 0}, {"id", id}, {"type", type}};
                cmd.update(payload);
                return s.reply({cmd, {}, {}});
            };
            auto groove = [](int bpm) {
                return Json{{"id", 2},
                            {"module", "sequencing.groove"},
                            {"config",
                             {{"version", 1},
                              {"bpm", bpm},
                              {"tracks", Json::array({{{"steps", Json::array({{{"kind", "note"}, {"key", 60}, {"velocity", 1}}})}}})}}}};
            };
            Json patch = {{"format", "wirescape.native.patch"},
                          {"version", 2},
                          {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}}, groove(300),
                                                   {{"id", 3}, {"module", "essentials.lfo"}}})},
                          {"connections", Json::array()}};
            auto base = send("rg-load", "loadGraph", {{"patch", patch}});
            check(base["ok"] == true, ("load the applyGraph base graph: " + base.dump()).c_str());
            const auto rendered = fake::completed_blocks.load(std::memory_order_acquire);
            const auto ready = std::chrono::steady_clock::now() + 1s;
            while (fake::completed_blocks.load(std::memory_order_acquire) == rendered &&
                   std::chrono::steady_clock::now() < ready)
                std::this_thread::yield();
            // While rendering, removing the LFO is a live replan.
            Json without_lfo = patch;
            without_lfo["modules"].erase(2);
            auto live = send("rg-live", "applyGraph", {{"patch", without_lfo}});
            check(live["ok"] == true && live["result"] == Json{{"path", "live"},
                                                               {"replaced", Json::array()},
                                                               {"unapplied", Json::array()}},
                  ("a rendering output takes the live replan: " + live.dump()).c_str());
            // Output lost: the next applyGraph cannot replan live and restarts through D5.
            const int exchanges = fake::exchanges, stopped = fake::stopped;
            const int gen = std::stoi(live["gen"].get<std::string>());
            fake::active = false;
            Json slower = without_lfo;
            slower["modules"][1] = groove(240);
            auto restart = send("rg-restart", "applyGraph", {{"patch", slower}});
            check(restart["ok"] == true && restart["gen"] == std::to_string(gen + 1) &&
                      restart["result"] == Json{{"path", "restart"},
                                                {"replaced", Json::array({2})},
                                                {"unapplied", Json::array()}},
                  ("rule 6: a lost output restarts with path restart and lists only the changed config: " +
                      restart.dump()).c_str());
            check(fake::exchanges == exchanges && fake::stopped == stopped + 1,
                  "rule 6 replaces the graph by restarting the stream, not by a live exchange");
            // Same namespace as before the restart, unlike loadGraph: the removed LFO ID stays used.
            auto reused = send("rg-reuse", "addModule", {{"moduleId", 3}, {"moduleType", "essentials.lfo"}});
            check(reused["ok"] == false && reused["code"] == "duplicate",
                  ("rule 6 keeps the session ID namespace: " + reused.dump()).c_str());
        }
        fake::render = false;
        // Windows lists one endpoint per host API and repeats names inside one host API.
        check(wirescape::audio::device_ids({{"Headphones", "MME"},
                                            {"Headphones", "Windows WASAPI"},
                                            {"Headphones ()", "Windows WDM-KS"},
                                            {"Headphones ()", "Windows WDM-KS"},
                                            {"Headphones ()", "Windows WDM-KS"}}) ==
                  std::vector<std::string>{"MME|Headphones", "Windows WASAPI|Headphones",
                                           "Windows WDM-KS|Headphones ()", "Windows WDM-KS|Headphones ()#2",
                                           "Windows WDM-KS|Headphones ()#3"},
              "ids are unique per host API with stable ordinals");
        fake::outputs = {{"MME|Headphones", "Headphones", "MME", 3, true},
                         {"Windows WASAPI|Headphones", "Headphones", "Windows WASAPI", 14, false},
                         {"Windows WDM-KS|Headphones ()", "Headphones ()", "Windows WDM-KS", 27, false},
                         {"Windows WDM-KS|Headphones ()#2", "Headphones ()", "Windows WDM-KS", 30, false}};
        options.settings = (root / "legacy.json").string();
        std::ofstream(options.settings) << R"({"audioDeviceId":"Headphones"})";
        fake::attempts.clear();
        {
            Session s(options);
            s.start();
            check(audio(s)["state"] == "running" && audio(s)["deviceId"] == "MME|Headphones",
                  "an ambiguous legacy name falls back to the default instead of reconnecting forever");
            for (const char *id : {"Windows WASAPI|Headphones", "Windows WDM-KS|Headphones ()#2"}) {
                auto reply =
                    s.reply({{{"v", 0}, {"id", "pick"}, {"type", "selectAudioDevice"}, {"deviceId", id}}, {}, {}});
                check(reply["ok"] == true && audio(s)["deviceId"] == id, "every repeated name is selectable by id");
            }
            for (const auto &attempt : fake::attempts) check(attempt.find('|') != std::string::npos, "opens use ids");
        }
        std::ofstream(options.settings) << R"j({"audioDeviceId":"Headphones ()"})j";
        fake::outputs.pop_back();
        {
            Session s(options);
            s.start();
            check(audio(s)["deviceId"] == "Windows WDM-KS|Headphones ()", "a unique legacy name upgrades to its id");
            s.shutdown();
            std::ifstream saved(options.settings);
            Json settings;
            saved >> settings;
            check(settings["audioDeviceId"] == "Windows WDM-KS|Headphones ()", "the upgraded id is persisted");
        }
        // An offer nobody adopts is withdrawn: the render side keeps its engine.
        {
            wirescape::audio::EngineSlot slot;
            auto *const current = reinterpret_cast<AppEngine *>(0x10);
            auto *const next = reinterpret_cast<AppEngine *>(0x20);
            check(!slot.offer(next, std::chrono::steady_clock::now()), "an unadopted offer times out");
            check(slot.adopt(current) == current, "a withdrawn offer is never adopted later");
        }
        // loadGraph on a running device swaps in place: no reopen, no stop, every gen lands.
        fake::render = true;
        fake::attempts.clear();
        fake::stopped = fake::exchanges = 0;
        options.settings = (root / "inplace.json").string();
        {
            Session s(options);
            s.start();
            check(audio(s)["state"] == "running" && fake::attempts.size() == 1, "one open at startup");
            for (int i = 1; i <= 6; ++i) {
                Json patch = {{"format", "wirescape.native.patch"},
                              {"version", 2},
                              {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}}})},
                              {"connections", Json::array()}};
                if (i % 2) patch["modules"].push_back({{"id", 2}, {"module", "essentials.vco"}});
                auto reply = s.reply({{{"v", 0}, {"id", "load"}, {"type", "loadGraph"}, {"patch", patch}}, {}, {}});
                check(reply["ok"] == true && reply["gen"] == std::to_string(i), "every in-place loadGraph lands");
            }
            check(fake::attempts.size() == 1 && fake::stopped == 0 && fake::exchanges == 6,
                  "patch switches never reopen or stop the device");
            check(audio(s)["state"] == "running", "the stream keeps running across switches");
            s.shutdown();
        }
        fake::render = false;
        // Registry and PortAudio enumeration are separately faked: no OS registry,
        // PortAudio DLL or physical device is ever touched by this test executable.
        fake::installed_asio = {"ASIO4ALL v2", "FlexASIO"};
        fake::outputs = {{"ASIO|ASIO4ALL v2", "ASIO4ALL v2", "ASIO", 3, true}};
        options.settings = (root / "asio-diagnostics.json").string();
        {
            Session s(options);
            s.start(base);
            const auto all = s.devices();
            check(all["audioDevices"].size() == 1 && all["audioDevices"][0]["id"] == "ASIO|ASIO4ALL v2",
                  "existing PortAudio identity is preserved");
            check(all["audio"]["unavailableDrivers"].size() == 1 &&
                      all["audio"]["unavailableDrivers"][0]["name"] == "FlexASIO" &&
                      all["audio"]["unavailableDrivers"][0]["hostApi"] == "ASIO" &&
                      all["audio"]["unavailableDrivers"][0]["reason"] == "driver-init-failed",
                  "missing ASIO init is a separate optional diagnostic, not a selectable endpoint");
            const auto listed = s.reply({{{"v", 0}, {"id", "asio-list"}, {"type", "listAudioDevices"}}, {}, {}});
            check(listed["ok"] == true && listed["result"]["devices"].size() == 1 &&
                      listed["result"]["audio"]["unavailableDrivers"].size() == 1 &&
                      s.hello()["audio"]["unavailableDrivers"].size() == 1,
                  "hello and explicit enumeration expose the same optional unavailable-driver diagnostic");
        }
        fake::refuse = true;
        options.settings = (root / "asio-error.json").string();
        {
            Session s(options);
            s.start(base);
            const auto status = audio(s);
            check(status["state"] == "reconnecting" && status["error"] == "fake unavailable/ambiguous output",
                  "control-thread opening failure must reach bounded audio status");
            fake::refuse = false;
            s.poll(base + 100ms);
            check(audio(s)["state"] == "running" && !audio(s).contains("error"),
                  "successful ASIO recovery clears the preceding failure text");
        }
        fake::refuse = true;
        for (const auto &diagnostic :
             {std::string(199, 'x') + "\xc3\xa9", std::string("host ") + "\xff\xc0" + " refusal"}) {
            fake::open_error = diagnostic;
            options.settings = (root / "asio-invalid-utf8-status.json").string();
            Session s(options);
            s.start(base);
            const auto status = s.status();
            const auto error = status["status"]["audio"]["error"].get<std::string>();
            check(error.size() <= 200 && Json::parse(status.dump())["status"]["audio"]["error"] == error,
                  "malformed/split host failure must serialize as bounded status.audio.error");
            check(error.find('\xff') == std::string::npos && error.find('\xc0') == std::string::npos,
                  "invalid host bytes must not survive in status.audio.error");
            fake::refuse = false;
            s.poll(base + 100ms);
            check(audio(s)["state"] == "running" && !audio(s).contains("error"),
                  "successful reopen clears the sanitized host error");
            fake::refuse = true;
        }
        fake::refuse = false;
        fake::open_error.clear();
        fake::installed_asio.clear();
        // Keel #627 ruling: an ASIO driver that refuses the block gets exactly one
        // retry at its preferred size 1..4096 after a quiescent graph reprepare.
        fake::refuse = false;
        fake::outputs = {{"ASIO|ASIO4ALL v2", "ASIO4ALL v2", "ASIO", 3, true}};
        const auto saved_block = options.block;
        options.block = 256;
        fake::accept_block = 512;
        fake::preferred = 512;
        options.settings = (root / "asio-forced.json").string();
        {
            fake::blocks.clear();
            Session s(options);
            s.start(base);
            const auto status = audio(s);
            check(fake::blocks == std::vector<uint32_t>{256, 512} && status["state"] == "running" &&
                      status["bufferFrames"] == 512 && status["requestedBufferFrames"] == 256 &&
                      !status.contains("error"),
                  "preferred size in range: one retry at the driver size, actual size reported");
            std::ifstream saved(options.settings);
            const auto prefs = Json::parse(saved);
            check(!prefs.contains("audio") || prefs["audio"].value("bufferFrames", 0) != 512,
                  "the driver-forced size is never persisted");
            s.poll(base + 100ms);
            check(fake::blocks.size() == 2, "a running forced stream is not reopened");
        }
        fake::preferred = 8192;
        options.settings = (root / "asio-out-of-range.json").string();
        {
            fake::blocks.clear();
            Session s(options);
            s.start(base);
            const auto status = audio(s);
            check(fake::blocks == std::vector<uint32_t>{256} && status["state"] == "reconnecting" &&
                      status["error"] == "ASIO driver requires 8192 frames (supported 1-4096)" &&
                      status["bufferFrames"] == 256 && !status.contains("requestedBufferFrames"),
                  "preferred size out of range: no second open, bounded error, configured size kept");
        }
        fake::accept_block = 1024; // neither the request nor the preferred size opens
        fake::preferred = 512;
        options.settings = (root / "asio-retry-fails.json").string();
        {
            fake::blocks.clear();
            Session s(options);
            s.start(base);
            const auto status = audio(s);
            check(fake::blocks == std::vector<uint32_t>{256, 512} && status["state"] == "reconnecting" &&
                      status["error"] == "fake ASIO buffer refused" && status["bufferFrames"] == 256 &&
                      !status.contains("requestedBufferFrames"),
                  "failed retry: exactly one retry, error set, no loop and configured size kept");
        }
        // Device-off regression for Codex's OSC worker UAF: the worker holds a
        // borrowed AppEngine* while an ASIO preferred-size retry swaps graphs.
        // Prove loopback ingress still works after both commit and rollback.
        fake::accept_block = 0;
        fake::preferred = 0;
        options.settings = (root / "asio-osc-rebind.json").string();
        fake::render = true; // live loadGraph needs the paced fake callback for its D5 handoff
        {
            Session s(options);
            s.start(base);
            const uint16_t port = select_loopback_osc_port();
            Json patch = {
                {"format", "wirescape.native.patch"},
                {"version", 2},
                {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}},
                                         {{"id", 2},
                                          {"module", "osc.in"},
                                          {"config",
                                           {{"port", port},
                                            {"lan", false},
                                            {"rows", Json::array({{{"pattern", "/reconnect"}, {"kind", "cv"}}})}}}}})},
                {"connections", Json::array()}};
            auto loaded = s.reply({{{"v", 0}, {"id", "osc-rebind"}, {"type", "loadGraph"}, {"patch", patch}}, {}, {}});
            check(loaded["ok"] == true, "OSC graph loads into fake ASIO playback");
            const auto routes_at_bind = s.status()["status"]["osc"]["routes"];
            if (routes_at_bind.size() != 1 || routes_at_bind[0].value("port", 0) != port ||
                routes_at_bind[0].value("state", std::string{}) != "listening")
                throw std::runtime_error("OSC loopback route not listening before ingress: " + routes_at_bind.dump());
            auto packet_received = [&](uint64_t minimum) {
                const auto deadline = std::chrono::steady_clock::now() + 1200ms;
                while (std::chrono::steady_clock::now() < deadline) {
                    const auto routes = s.status()["status"]["osc"]["routes"];
                    if (!routes.empty() && routes[0]["received"].get<uint64_t>() >= minimum) return true;
                    std::this_thread::sleep_for(10ms);
                }
                return false;
            };
            send_local_osc(port);
            check(packet_received(1), "OSC works before ASIO device loss");
            fake::active = false;
            s.poll(base + 100ms);
            fake::accept_block = 512;
            fake::preferred = 512;
            s.poll(base + 200ms);
            check(audio(s)["state"] == "running" && audio(s)["bufferFrames"] == 512,
                  "preferred-size reconnect swaps the live graph");
            send_local_osc(port);
            check(packet_received(1), "OSC worker rebinds to the new graph after preferred-size retry");
            fake::active = false;
            s.poll(base + 300ms);
            fake::accept_block = 1024;
            fake::preferred = 256;
            s.poll(base + 400ms);
            check(audio(s)["state"] == "reconnecting" && audio(s)["bufferFrames"] == 512,
                  "failed ASIO retry restores old block and graph");
            send_local_osc(port);
            check(packet_received(1), "OSC worker rebinds to the restored graph after failed retry");
            s.shutdown();
        }
        fake::render = false;
        fake::accept_block = 0;
        fake::preferred = 0;
        options.block = saved_block;
        test_a70_buffer_state(root);
        test_e7_state_restart(root);
        test_e7_rate_dependent_state_refusal(root);
        test_a78_deferred_config(root);
        test_a81_synthetic_slot();
        std::cout << "audio recovery fake-backend tests passed\n";
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}

