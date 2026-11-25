// SPDX-License-Identifier: GPL-3.0-only
// Device-free / LAN-free OSC network-worker regressions.
#include "../../sdk/examples/test_support.h"
#include "../osc/codec.h"
#include "osc_service.h"
#include <array>
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
using namespace wirescape::osc;
struct Capture {
    std::atomic<uint32_t> count{0};
    std::atomic<uint64_t> timestamp{0};
    static int deliver(void *p, uint32_t node, const ws2_event &e, uint64_t when) noexcept {
        auto &c = *static_cast<Capture *>(p);
        if (node == 32) return WS2_INVALID; // exercise a bounded sink rejection
        if (node == 1 || node == 2) {
            if (e.type == WS2_MESSAGE && e.message_kind == WS2_MSG_OSC) {
                c.timestamp.store(when, std::memory_order_release);
                c.count.fetch_add(1, std::memory_order_relaxed);
            }
        }
        return WS2_OK;
    }
};

namespace {
using Clock = std::chrono::steady_clock;
using namespace std::chrono_literals;

// The split is absent at the fail-first head. Compile and run the real UDP
// witness even there, rather than stopping at a missing-member compiler error.
template<class T>
auto verify_split(const T &state, uint64_t budget, uint64_t enqueue, int)
    -> decltype(state.budget_dropped, state.enqueue_dropped, void()) {
    std::fprintf(stderr, "OSC drop split budget=%llu enqueue=%llu expected=%llu/%llu\n",
        static_cast<unsigned long long>(state.budget_dropped),
        static_cast<unsigned long long>(state.enqueue_dropped),
        static_cast<unsigned long long>(budget), static_cast<unsigned long long>(enqueue));
    REQUIRE(state.budget_dropped == budget);
    REQUIRE(state.enqueue_dropped == enqueue);
}
template<class T>
void verify_split(const T &state, uint64_t budget, uint64_t enqueue, long) {
    std::fprintf(stderr, "OSC drop witness total=%llu expected budget=%llu enqueue=%llu; split unavailable\n",
        static_cast<unsigned long long>(state.dropped),
        static_cast<unsigned long long>(budget), static_cast<unsigned long long>(enqueue));
    REQUIRE(false);
}

// Listener counts represent one physical UDP listener; budget counts once
// per discarded decoded message, enqueue once per failed route delivery.
template<class S>
auto verify_listener(const S &service, uint64_t budget, uint64_t enqueue, int)
    -> decltype(service.listener_states(), void()) {
    const auto listeners = service.listener_states();
    REQUIRE(listeners.size() == 1);
    REQUIRE(listeners[0].port == service.bound_port());
    REQUIRE(listeners[0].dropped == budget + enqueue);
    verify_split(listeners[0], budget, enqueue, 0);
}
template<class S>
void verify_listener(const S &, uint64_t, uint64_t, long) {
    REQUIRE(false);
}

// The service-level sink has exactly the nine route matches of the soak.
// A bounded deliberate scheduling stall queues one 64-address cycle behind
// the gate rise. One selected sink refusal witnesses enqueue accounting;
// this is a controlled rejection, not a claim about the engine's root cause.
struct SoakSink {
    std::atomic<bool> gate_high{false}, release{false}, stall_timeout{false};
    std::atomic<uint32_t> falls{0}, seq{0};
    static bool accept(void *, uint32_t node, std::string_view address) noexcept {
        if (address == "/io/gate" || address == "/io/seq") return node == 1;
        if (address.size() != 11 || address.substr(0, 9) != "/io/load/") return false;
        const unsigned index = unsigned(address[9] - '0') * 10 + unsigned(address[10] - '0');
        return index < 64 && node == 10 + index / 8;
    }
    static int deliver(void *p, uint32_t node, const ws2_event &e, uint64_t) noexcept {
        auto &self = *static_cast<SoakSink *>(p);
        int result = WS2_OK;
        parse(static_cast<const uint8_t *>(e.data), e.bytes, [&](const Message &m) {
            if (node == 1 && m.address == "/io/seq") ++self.seq;
            if (node == 1 && m.address == "/io/gate") {
                if (m.arguments[0].real >= .5f) {
                    self.gate_high.store(true, std::memory_order_release);
                    const auto deadline = Clock::now() + 500ms;
                    while (!self.release.load(std::memory_order_acquire) && Clock::now() < deadline)
                        std::this_thread::yield();
                    if (!self.release.load(std::memory_order_acquire)) self.stall_timeout = true;
                } else ++self.falls;
            }
            if (node == 17 && m.address == "/io/load/63") result = WS2_INVALID;
        });
        return result;
    }
};

void soak_backlog_split() {
    SoakSink sink;
    Service service({&sink, SoakSink::deliver, SoakSink::accept});
    REQUIRE(service.add({1, 0, false}));
    for (unsigned node = 10; node <= 17; ++node) REQUIRE(service.add({node, 0, false}));
    REQUIRE(service.start() && service.counters().sockets == 1);
    const auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in dest{};
    dest.sin_family = AF_INET;
    dest.sin_port = htons(service.bound_port());
    dest.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    auto send = [&](std::string_view path, float value) {
        Message m;
        m.address = path;
        m.count = 1;
        m.arguments[0].type = 'f';
        m.arguments[0].real = value;
        uint8_t bytes[1472]{};
        bool truncated = false;
        const auto n = encode(m, bytes, sizeof(bytes), truncated);
        REQUIRE(n && !truncated);
        REQUIRE(sendto(sender, reinterpret_cast<const char *>(bytes), int(n), 0,
                       reinterpret_cast<sockaddr *>(&dest), sizeof(dest)) == int(n));
    };
    send("/io/seq", 1.f / 4096);
    send("/io/gate", 1.f);
    const auto entered_deadline = Clock::now() + 500ms;
    while (!sink.gate_high.load(std::memory_order_acquire) && Clock::now() < entered_deadline)
        std::this_thread::yield();
    REQUIRE(sink.gate_high);
    // One complete cycle accumulates while the worker is stalled. Subsequent
    // cycles retain the actual 5ms cadence and one datagram per address.
    const auto start = Clock::now();
    for (unsigned cycle = 0; cycle < 4; ++cycle) {
        const auto next = start + cycle * 5ms;
        while (Clock::now() < next) std::this_thread::yield();
        for (unsigned i = 0; i < 64; ++i) {
            char address[32]{};
            std::snprintf(address, sizeof(address), "/io/load/%02u", i);
            send(address, (i & 1) ? float((cycle + i) % 2) : float((cycle + i * 17) % 97) / 96.f);
        }
        if (cycle == 0) sink.release.store(true, std::memory_order_release);
    }
    while (Clock::now() < start + 20ms) std::this_thread::yield();
    send("/io/gate", 0.f);
    const auto deadline = Clock::now() + 2s;
    while (service.counters().received < 259 && Clock::now() < deadline)
        std::this_thread::sleep_for(1ms);
    // Join before asserting cross-counter identities: concurrent snapshots
    // are intentionally not a transactional read.
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    service.stop();
    const auto states = service.states();
    const auto total = service.counters();
    std::fprintf(stderr, "OSC 64x200Hz backlog: datagrams=%llu dropped=%llu seq=%u falls=%u\n",
        static_cast<unsigned long long>(total.received),
        static_cast<unsigned long long>(total.dropped), sink.seq.load(), sink.falls.load());
    REQUIRE(!sink.stall_timeout && sink.seq == 1 && sink.falls == 1);
    REQUIRE(total.received == 259 && total.dropped == 4);
    REQUIRE(states.size() == 9 && states[0].received == 3);
    for (unsigned i = 0; i < states.size(); ++i) {
        const uint64_t refused = i == 8 ? 4 : 0;
        REQUIRE(states[i].dropped == refused);
        if (i != 0) REQUIRE(states[i].received == 32 - refused);
        std::fprintf(stderr, "OSC route %u total=%llu\n", states[i].node,
            static_cast<unsigned long long>(states[i].dropped));
    }
    // Report a nonzero drop on old code before failing for the absent split.
    verify_split(states.back(), 0, 4, 0);
    for (const auto &state : states) {
        verify_split(state, 0, state.node == 17 ? 4 : 0, 0);
        REQUIRE(state.listener_budget_dropped == 0);
        REQUIRE(state.listener_enqueue_dropped == 4);
    }
    verify_split(total, 0, 4, 0);
    verify_listener(service, 0, 4, 0);
}
// A67: separate refusal codes without changing the existing soak-profile test.
// The controlled witness does not attribute the historical hosted failure.
template<class T>
auto verify_enqueue_reasons(const T &state, uint64_t invalid, uint64_t capacity,
                            uint64_t not_ready, uint64_t other, int)
    -> decltype(state.enqueue_invalid, state.enqueue_capacity, state.enqueue_state,
                state.enqueue_other, void()) {
    REQUIRE(state.enqueue_invalid == invalid);
    REQUIRE(state.enqueue_capacity == capacity);
    REQUIRE(state.enqueue_state == not_ready);
    REQUIRE(state.enqueue_other == other);
    REQUIRE(state.enqueue_dropped == invalid + capacity + not_ready + other);
}
template<class T>
void verify_enqueue_reasons(const T &state, uint64_t, uint64_t, uint64_t, uint64_t, long) {
    std::fprintf(stderr, "A67 enqueue reason split unavailable; observed drops=%llu\n",
        static_cast<unsigned long long>(state.enqueue_dropped));
    REQUIRE(false);
}
struct ReasonSink {
    static int deliver(void *, uint32_t node, const ws2_event &, uint64_t) noexcept {
        switch (node) {
        case 1: return WS2_INVALID;
        case 2: return WS2_CAPACITY;
        case 3: return WS2_STATE;
        case 4: return WS2_EXCEPTION; // other, not one of Engine::enqueue's three codes
        default: return WS2_OK;
        }
    }
};
void enqueue_reason_split() {
    Service service({nullptr, ReasonSink::deliver});
    for (uint32_t node = 1; node <= 5; ++node) REQUIRE(service.add({node, 0, false}));
    REQUIRE(service.start() && service.counters().sockets == 1);
    const auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in destination{};
    destination.sin_family = AF_INET;
    destination.sin_port = htons(service.bound_port());
    destination.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    Message msg;
    msg.address = "/a67";
    msg.count = 1;
    msg.arguments[0].type = 'f';
    msg.arguments[0].real = .5f;
    uint8_t packet[1472]{};
    bool truncated = false;
    const auto bytes = encode(msg, packet, sizeof(packet), truncated);
    REQUIRE(bytes && !truncated);
    REQUIRE(sendto(sender, reinterpret_cast<const char *>(packet), int(bytes), 0,
                   reinterpret_cast<sockaddr *>(&destination), sizeof(destination)) == int(bytes));
    const auto deadline = Clock::now() + 2s;
    while (service.states().back().received != 1 && Clock::now() < deadline)
        std::this_thread::sleep_for(1ms);
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    service.stop(); // assert identities only after the producer has joined
    const auto states = service.states();
    REQUIRE(states.size() == 5 && states.back().received == 1);
    REQUIRE(service.counters().received == 1 && service.counters().dropped == 4);
    for (const auto &state : states) {
        REQUIRE(state.budget_dropped == 0 && state.listener_enqueue_dropped == 4);
        REQUIRE(state.enqueue_dropped == (state.node == 5 ? 0 : 1));
        REQUIRE(state.dropped == state.enqueue_dropped);
        REQUIRE(state.received == (state.node == 5 ? 1 : 0));
        verify_enqueue_reasons(state, state.node == 1, state.node == 2,
                               state.node == 3, state.node == 4, 0);
    }
    const auto listeners = service.listener_states();
    REQUIRE(listeners.size() == 1);
    verify_enqueue_reasons(listeners[0], 1, 1, 1, 1, 0);
    verify_enqueue_reasons(service.counters(), 1, 1, 1, 1, 0);
}

} // namespace

int main() {
    soak_backlog_split();
    enqueue_reason_split();
    Capture c;
    // Unconfirmed LAN never binds any interface other than loopback.
    Service local({&c, Capture::deliver});
    REQUIRE(local.add({1, 0, true}) && local.add({2, 0, false}) && local.start());
    REQUIRE(local.counters().sockets == 1);
    auto state = local.states();
    REQUIRE(state.size() == 2 && std::strcmp(state[0].state, "lan-not-confirmed") == 0);
    REQUIRE(!state[0].lan_bound && !state[1].lan_bound);
    Message m;
    m.address = "/pico1/knob/3";
    m.count = 1;
    m.arguments[0].type = 'f';
    m.arguments[0].real = .5f;
    uint8_t bytes[1472]{};
    bool truncated = false;
    auto n = encode(m, bytes, sizeof(bytes), truncated);
    REQUIRE(n > 0 && !truncated);
    auto sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(local.bound_port());
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const auto before = std::chrono::steady_clock::now();
    const auto sent = sendto(sender, reinterpret_cast<const char *>(bytes), int(n), 0,
                             reinterpret_cast<sockaddr *>(&address), sizeof(address));
    REQUIRE(sent == int(n));
    uint32_t attempts = 0;
    while (c.count.load() < 2 && attempts++ < 2000) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    const auto after = std::chrono::steady_clock::now();
    state = local.states();
    REQUIRE(c.count == 2 && c.timestamp != 0);
    const auto before_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(before.time_since_epoch()).count();
    const auto after_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(after.time_since_epoch()).count();
    REQUIRE(c.timestamp >= uint64_t(before_ns));
    REQUIRE(c.timestamp <= uint64_t(after_ns));
    REQUIRE(state[0].received == 1 && state[1].received == 1);
    REQUIRE(state[0].dropped == 0 && state[1].dropped == 0);
    // Occupied localhost ports do not fail service startup or accept unwanted data.
    Service busy({&c, Capture::deliver});
    REQUIRE(busy.add({3, local.bound_port(), false}) && busy.start());
    REQUIRE(busy.counters().sockets == 0 && std::strcmp(busy.states()[0].state, "port-busy") == 0);
    busy.stop();
#ifdef _WIN32
    closesocket(sender);
#else
    close(sender);
#endif
    local.stop();
    REQUIRE(local.counters().sockets == 0);
    // All 32 routes share one loopback socket. The 33rd is refused without
    // widening the port set; malformed/oversized packets never reach the DSP.
    Service bounded({&c, Capture::deliver});
    for (uint32_t node = 1; node <= 32; ++node) REQUIRE(bounded.add({node, 0, false}));
    REQUIRE(!bounded.add({33, 0, false}));
    REQUIRE(bounded.start() && bounded.counters().sockets == 1);
    REQUIRE(bounded.states().size() == 32);
    auto flood_sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in flood_address{};
    flood_address.sin_family = AF_INET;
    flood_address.sin_port = htons(bounded.bound_port());
    flood_address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const std::array<uint8_t, 8> malformed{{1, 2, 3, 4, 5, 6, 7, 8}};
    const std::array<uint8_t, 2052> oversized{};
    REQUIRE(sendto(flood_sender, reinterpret_cast<const char *>(bytes), int(n), 0,
                   reinterpret_cast<sockaddr *>(&flood_address), sizeof(flood_address)) == int(n));
    REQUIRE(sendto(flood_sender, reinterpret_cast<const char *>(malformed.data()), int(malformed.size()), 0,
                   reinterpret_cast<sockaddr *>(&flood_address), sizeof(flood_address)) == int(malformed.size()));
    REQUIRE(sendto(flood_sender, reinterpret_cast<const char *>(oversized.data()), int(oversized.size()), 0,
                   reinterpret_cast<sockaddr *>(&flood_address), sizeof(flood_address)) == int(oversized.size()));
    for (uint32_t wait = 0; wait < 2000 && bounded.counters().received < 3; ++wait)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    REQUIRE(bounded.counters().received == 3);
    REQUIRE(bounded.counters().malformed == 1);
    REQUIRE(bounded.counters().dropped >= 2); // one oversized + one rejected enqueue
    const auto bounded_states = bounded.states();
    REQUIRE(bounded_states[0].received == 1 && bounded_states[30].received == 1);
    REQUIRE(bounded_states[31].received == 0 && bounded_states[31].dropped == 1);
#ifdef _WIN32
    closesocket(flood_sender);
#else
    close(flood_sender);
#endif
    bounded.stop();
    REQUIRE(bounded.counters().sockets == 0);
    // One UDP datagram can contain dozens of OSC bundle elements. A 80-message
    // bundle must deliver no more than 64, even though it is one small packet.
    Service bundled({&c, Capture::deliver});
    REQUIRE(bundled.add({1, 0, false}) && bundled.add({2, 0, false}) && bundled.start());
    auto bundle_sender = ::socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    sockaddr_in bundle_address{};
    bundle_address.sin_family = AF_INET;
    bundle_address.sin_port = htons(bundled.bound_port());
    bundle_address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    Message short_message;
    short_message.address = "/x";
    short_message.count = 1;
    short_message.arguments[0].type = 'f';
    short_message.arguments[0].real = 0.25f;
    uint8_t short_packet[1472]{};
    bool short_truncated = false;
    const auto short_bytes = encode(short_message, short_packet, sizeof(short_packet), short_truncated);
    REQUIRE(short_bytes > 0 && !short_truncated);
    std::array<uint8_t, 2048> bundle{};
    std::memcpy(bundle.data(), "#bundle", 7);
    size_t used = 16; // bundle marker + zero timetag
    for (uint32_t element = 0; element < 80; ++element) {
        REQUIRE(used + 4 + short_bytes <= bundle.size());
        put32(bundle.data() + used, uint32_t(short_bytes));
        used += 4;
        std::memcpy(bundle.data() + used, short_packet, short_bytes);
        used += short_bytes;
    }
    REQUIRE(sendto(bundle_sender, reinterpret_cast<const char *>(bundle.data()), int(used), 0,
                   reinterpret_cast<sockaddr *>(&bundle_address), sizeof(bundle_address)) == int(used));
    for (uint32_t wait = 0; wait < 2000 && bundled.counters().dropped < 16; ++wait)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
#ifdef _WIN32
    closesocket(bundle_sender);
#else
    close(bundle_sender);
#endif
    bundled.stop(); // quiesce before exact split identities
    REQUIRE(bundled.counters().received == 1);
    REQUIRE(bundled.states().size() == 2);
    for (const auto &route : bundled.states()) {
        REQUIRE(route.received == 64);
        REQUIRE(route.dropped == 16);
        verify_split(route, 16, 0, 0);
        REQUIRE(route.listener_budget_dropped == 16);
        REQUIRE(route.listener_enqueue_dropped == 0);
    }
    // The physical listener and global counts are NOT multiplied by route count.
    REQUIRE(bundled.counters().dropped == 16);
    verify_split(bundled.counters(), 16, 0, 0);
    verify_listener(bundled, 16, 0, 0);
    REQUIRE(bundled.counters().sockets == 0);
    // LAN/localhost conflicts stay isolated even with explicit permission:
    // no test ever opens a LAN socket.
    Service mismatch({&c, Capture::deliver}, true);
    REQUIRE(mismatch.add({1, 9100, false}) && mismatch.add({2, 9100, true}));
    REQUIRE(std::strcmp(mismatch.states()[1].state, "port-busy") == 0);
    REQUIRE(mismatch.counters().sockets == 0);
}
