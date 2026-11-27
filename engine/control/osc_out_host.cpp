// SPDX-License-Identifier: GPL-3.0-only
#include "osc_out_host.h"
#include "../../host/document/io_data_migration.h"
#include "../../host/osc/codec.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <nlohmann/json.hpp>
#include <stdexcept>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace wirescape::osc {
namespace {
#ifdef _WIN32
using Socket = SOCKET;
constexpr Socket invalid_socket = INVALID_SOCKET;
void close_socket(Socket s) noexcept { closesocket(s); }
#else
using Socket = int;
constexpr Socket invalid_socket = -1;
void close_socket(Socket s) noexcept { close(s); }
#endif
// Only the sender thread performs network operations.
bool send_message(Socket sock, const Message &message, uint16_t port, uint32_t destination) noexcept {
    std::array<uint8_t, 1472> buffer{};
    bool truncated = false;
    const auto size = encode(message, buffer.data(), buffer.size(), truncated);
    if (!size || truncated) return false;
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    address.sin_addr.s_addr = htonl(destination);
    const auto result = sendto(sock, reinterpret_cast<const char *>(buffer.data()), int(size), 0,
                               reinterpret_cast<const sockaddr *>(&address), sizeof(address));
    return result == static_cast<decltype(result)>(size);
}
} // namespace

OutHost::OutHost(const std::string &document, SendOverride send_override, bool allow_network)
    : send_override_(send_override) {
    auto patch = nlohmann::json::parse(document);
    for (auto &module : patch.at("modules")) {
        if (module.value("module", std::string{}) != "osc.out") continue;
        if (routes_.size() >= 32) throw std::runtime_error("At most 32 OSC output routes");
        auto route = std::make_unique<Route>();
        route->node = module.at("id").get<uint32_t>();
        document::migrate_io_module(module);
        const auto data = document::read_io_slot<OscOutRoutes, OscOut, validate_osc_out_routes>(module);
        const auto config = module.value("config", nlohmann::json::object());
        route->destination = document::osc_out_ipv4(config);
        route->lan_refused = route->destination != 0x7f000001u && !allow_network;
        const auto bytes = document::runtime_module_config("osc.out", config, route->node);
        if (bytes.size() != sizeof(route->config)) throw std::runtime_error("OSC Out configuration was not prepared");
        std::memcpy(&route->config, bytes.data(), sizeof(route->config));
        route->config.bus = route->bus.get();
        for (uint32_t i = 0; i < 8; ++i) {
            const auto &src = data.rows[i];
            auto &dst = route->config.rows[i];
            std::memcpy(dst.address, src.address, sizeof(dst.address));
            dst.kind = src.kind;
            dst.deadband = src.deadband;
            dst.enabled = src.enabled;
        }
        std::memcpy(route->config.notes.address, data.notes_address, sizeof(data.notes_address));
        route->config.notes.enabled = data.notes_enabled;
        for (const auto &row : route->config.rows) route->enabled |= row.enabled != 0;
        route->enabled |= route->config.notes.enabled != 0;
        if (!buses_.emplace(route->node, route->bus.get()).second)
            throw std::runtime_error("Duplicate OSC output module ID");
        routes_.push_back(std::move(route));
    }
}
void OutHost::commit_data(uint32_t node, const OscOutRoutes &data) noexcept {
    auto same = [](const OutRowConfig &a, const OscOutRowData &b) {
        return std::strcmp(a.address, b.address) == 0 && a.kind == b.kind &&
               a.deadband == b.deadband && a.enabled == b.enabled;
    };
    for (auto &item : routes_) {
        auto &route = *item;
        if (route.node != node) continue;
        const bool notes_changed = route.config.notes.enabled != data.notes_enabled ||
            std::strcmp(route.config.notes.address, data.notes_address) != 0;
        bool changed = notes_changed;
        for (uint32_t i = 0; i < 8; ++i) changed |= !same(route.config.rows[i], data.rows[i]);
        if (!changed) return;
        // Worker owns cursors; join only after ring acceptance. Do not clear
        // the render bus or its monotonic counters.
        stop();
        route.enabled = false;
        for (uint32_t i = 0; i < 8; ++i) {
            auto &dst = route.config.rows[i];
            const auto &src = data.rows[i];
            if (!same(dst, src)) {
                auto &cursor = route.cursors[i];
                // Preserve the last consumed counters. The worker will use
                // the actual block's wire mark/baseline, even when rendering
                // adopted the new table before this control edit joined it.
                const auto rises = cursor.rises;
                const auto falls = cursor.falls;
                const auto seen_serial = cursor.seen_serial;
                if (dst.enabled && dst.kind == 1 && cursor.sent_high) {
                    route.gate_release[i] = dst;
                    route.release_gates.set(i);
                }
                cursor = {};
                cursor.rises = rises;
                cursor.falls = falls;
                cursor.seen_serial = seen_serial;
                cursor.wait_for_table = true;
                std::memcpy(dst.address, src.address, sizeof(dst.address));
                dst.kind = src.kind;
                dst.deadband = src.deadband;
                dst.enabled = src.enabled;
            }
            route.enabled |= dst.enabled != 0;
        }
        if (notes_changed) {
            std::memcpy(route.release_notes_address, route.config.notes.address,
                        sizeof(route.release_notes_address));
            route.notes_release = route.notes_high;
            for (auto &keys : route.notes_high) keys.reset();
            route.notes_cleanup = true; // worker drops old-address events, keeps fresh ones
            std::memcpy(route.config.notes.address, data.notes_address, sizeof(data.notes_address));
            route.config.notes.enabled = data.notes_enabled;
        }
        route.enabled |= route.config.notes.enabled != 0;
        start();
        return;
    }
}
void OutHost::start() noexcept {
    if (worker_.joinable() || routes_.empty()) return;
    bool enabled = false;
    for (const auto &route : routes_)
        enabled |= !route->lan_refused && (route->enabled || route->has_releases() || route->has_cleanup());
    if (!enabled) return; // disabled modules must not open a socket
    launch_worker(true);
}
void OutHost::launch_worker(bool poll) noexcept {
    socket_error_.store(0);
    running_.store(poll, std::memory_order_release);
    try {
        worker_ = std::thread([this] { loop(); });
    } catch (...) {
        running_.store(false, std::memory_order_release);
        socket_error_.store(1, std::memory_order_release);
        for (auto &route : routes_) route->drop_releases();
    }
}
void OutHost::stop() noexcept {
    running_.store(false, std::memory_order_release);
    if (worker_.joinable()) worker_.join();
}
void OutHost::retire() noexcept {
    stop(); // no sender may mutate the delivered-level cursors after this join
    bool pending = false;
    for (auto &item : routes_) {
        auto &route = *item;
        if (route.lan_refused) continue;
        for (size_t i = 0; i < route.cursors.size(); ++i) {
            auto &cursor = route.cursors[i];
            const auto &cfg = route.config.rows[i];
            if (!cfg.enabled || cfg.kind != 1 || !cursor.sent_high) continue;
            route.gate_release[i] = cfg;
            route.release_gates.set(i);
            cursor.sent_high = false; // one best-effort attempt, even on failure
        }
        pending |= route.has_releases();
    }
    if (pending) {
        launch_worker(false); // drain releases only; never publish a fresh high
        stop();
    }
}
void OutHost::loop() noexcept {
    const bool poll = running_.load(std::memory_order_acquire);
    bool need_socket = false, need_lan = false;
    for (const auto &route : routes_) {
        if (route->lan_refused || !((poll && route->enabled) || route->has_releases())) continue;
        need_socket = true;
        need_lan |= route->destination != 0x7f000001u;
    }
#ifdef _WIN32
    WSADATA data{};
    if (need_socket && WSAStartup(MAKEWORD(2, 2), &data) != 0) {
        socket_error_.store(1, std::memory_order_release);
        for (auto &route : routes_) route->drop_releases();
        return;
    }
#endif
    Socket sock = need_socket ? socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP) : invalid_socket;
    bool ready = !need_socket || sock != invalid_socket;
    if (need_socket && ready) {
        sockaddr_in address{};
        address.sin_family = AF_INET;
        address.sin_port = 0;
        address.sin_addr.s_addr = htonl(need_lan ? INADDR_ANY : INADDR_LOOPBACK);
        ready = bind(sock, reinterpret_cast<const sockaddr *>(&address), sizeof(address)) == 0;
    }
    if (need_socket && ready) {
#ifdef _WIN32
        u_long nonblocking = 1;
        ready = ioctlsocket(sock, FIONBIO, &nonblocking) == 0;
#else
        const int flags = fcntl(sock, F_GETFL, 0);
        ready = flags >= 0 && fcntl(sock, F_SETFL, flags | O_NONBLOCK) == 0;
#endif
    }
    if (!ready) {
        socket_error_.store(1, std::memory_order_release);
        if (sock != invalid_socket) close_socket(sock);
        for (auto &route : routes_) route->drop_releases();
#ifdef _WIN32
        if (need_socket) WSACleanup();
#endif
        return;
    }
    auto send = [&](Route &route, uint32_t &budget, const char *path, uint32_t count, const Argument *args) -> bool {
        if (!budget || route.lan_refused) return false;
        --budget;
        Message message{};
        message.address = path;
        message.count = count;
        for (uint32_t a = 0; a < count; ++a) message.arguments[a] = args[a];
        const bool accepted = send_override_ ? send_override_(message, uint16_t(route.config.port))
                                             : send_message(sock, message, uint16_t(route.config.port), route.destination);
        if (accepted) route.sent.fetch_add(1, std::memory_order_relaxed);
        else {
            route.dropped.fetch_add(1, std::memory_order_relaxed);
            route.error.store(1, std::memory_order_relaxed);
        }
        return accepted;
    };
    // Finish a finite, already accepted old-address release set even if
    // another control edit joins us. Never send new-table data after stop.
    auto pending_releases = [&] {
        for (const auto &item : routes_) if (!item->lan_refused && item->has_releases()) return true;
        return false;
    };
    while (running_.load(std::memory_order_acquire) || pending_releases()) {
        const auto now = std::chrono::steady_clock::now();
        for (const auto &item : routes_) {
            auto &route = *item;
            if (route.lan_refused) continue;
            uint32_t budget = 64; // Release messages share the existing per-poll budget.
            for (uint32_t i = 0; i < 8 && budget; ++i) if (route.release_gates.test(i)) {
                Argument zero{};
                zero.type = 'f';
                send(route, budget, route.gate_release[i].address, 1, &zero);
                route.release_gates.reset(i);
            }
            for (uint32_t channel = 0; channel < route.notes_release.size() && budget; ++channel)
                for (uint32_t key = 0; key < 128 && budget; ++key) if (route.notes_release[channel].test(key)) {
                    Argument args[3]{};
                    args[0].type = 'i'; args[0].integer = int32_t(key);
                    args[1].type = 'f'; args[1].real = 0;
                    args[2].type = 'i'; args[2].integer = int32_t(channel) - 1;
                    send(route, budget, route.release_notes_address, 3, args);
                    route.notes_release[channel].reset(key);
                }
            if (route.has_releases() || !running_.load(std::memory_order_acquire)) continue;
            for (size_t i = 0; i < route.config.rows.size(); ++i) {
                const auto &cfg = route.config.rows[i];
                auto &cursor = route.cursors[i];
                if (!cfg.enabled && !cursor.wait_for_table) continue;
                OutRowSnapshot row;
                if (!route.bus->rows[i].snapshot(row)) continue;
                auto discard = [&](uint32_t rises, uint32_t falls) {
                    route.dropped.fetch_add(uint64_t(uint32_t(rises - cursor.rises)) +
                        uint32_t(falls - cursor.falls), std::memory_order_relaxed);
                    cursor.rises = rises;
                    cursor.falls = falls;
                };
                if (row.mark != out_wire_mark(cfg.address, cfg.kind, cfg.deadband, cfg.enabled != 0)) {
                    // An in-flight old block may publish after ring acceptance.
                    // It can only be suppressed, never encoded using the new table.
                    if (cursor.wait_for_table && row.mark_serial <= cursor.seen_serial)
                        discard(row.rises, row.falls);
                    continue;
                }
                if (cursor.wait_for_table) {
                    // If fresh data already arrived before the host joined the
                    // worker, discard just the crossings before that table's
                    // baseline. Unsigned distance guards an A->B->A edit whose
                    // intermediate table never rendered.
                    const auto rises = uint32_t(row.baseline_rises - cursor.rises) <=
                        uint32_t(row.rises - cursor.rises) ? row.baseline_rises : cursor.rises;
                    const auto falls = uint32_t(row.baseline_falls - cursor.falls) <=
                        uint32_t(row.falls - cursor.falls) ? row.baseline_falls : cursor.falls;
                    discard(rises, falls);
                    cursor.wait_for_table = false;
                }
                cursor.seen_serial = row.serial;
                if (!cfg.enabled || !row.blocks) continue;
                if (cfg.kind == 1) {
                    const auto rises = row.rises;
                    const auto falls = row.falls;
                    // Unsigned deltas remain correct across a 32-bit counter wrap.
                    const uint64_t edges = uint64_t(uint32_t(rises - cursor.rises)) + uint32_t(falls - cursor.falls);
                    const bool high = row.value >= 0.5f;
                    Argument arg{};
                    arg.type = 'f';
                    if (!cursor.initialized && !edges && budget) {
                        arg.real = high ? 1.0f : 0.0f;
                        if (send(route, budget, cfg.address, 1, &arg)) cursor.sent_high = high;
                        cursor.gate_high = high;
                        cursor.initialized = true;
                    }
                    if (edges) {
                        // The first fresh block may begin with a falling
                        // edge from a held-high source. Infer its initial
                        // level from the final level and crossing parity.
                        if (!cursor.initialized) cursor.gate_high = high != bool(edges & 1u);
                        // At most four edges; on overflow preserve the first
                        // pulse and then reconcile with the true current level.
                        const uint32_t first = edges > 4 ? 2u : uint32_t(edges);
                        uint32_t emitted = 0;
                        while (emitted < first && budget) {
                            cursor.gate_high = !cursor.gate_high;
                            arg.real = cursor.gate_high ? 1.0f : 0.0f;
                            if (send(route, budget, cfg.address, 1, &arg)) cursor.sent_high = cursor.gate_high;
                            ++emitted;
                        }
                        if (edges > 4 && budget && cursor.gate_high != high) {
                            arg.real = high ? 1.0f : 0.0f;
                            if (send(route, budget, cfg.address, 1, &arg)) cursor.sent_high = high;
                            cursor.gate_high = high;
                            ++emitted;
                        }
                        route.dropped.fetch_add(edges - emitted, std::memory_order_relaxed);
                        cursor.rises = rises;
                        cursor.falls = falls;
                        cursor.initialized |= emitted != 0;
                    } else if (cursor.initialized && cursor.gate_high != high && budget) {
                        // A previous poll may have exhausted the datagram budget.
                        arg.real = high ? 1.0f : 0.0f;
                        if (send(route, budget, cfg.address, 1, &arg)) cursor.sent_high = high;
                        cursor.gate_high = high;
                    }
                } else {
                    const float value = row.value;
                    const auto interval = std::chrono::duration<double>(1.0 / route.config.rate_hz);
                    if (budget &&
                        (!cursor.initialized || cursor.retry || std::abs(value - cursor.previous) > cfg.deadband) &&
                        (!cursor.initialized || now - cursor.last_send >= interval)) {
                        Argument arg{};
                        arg.type = 'f';
                        arg.real = value;
                        const bool accepted = send(route, budget, cfg.address, 1, &arg);
                        cursor.last_send = now;
                        cursor.initialized = true;
                        cursor.retry = !accepted;
                        if (accepted) cursor.previous = value;
                    }
                }
            }
            if (route.config.notes.enabled || route.notes_cleanup) {
                // A bounded ring entry carries the exact address of its block.
                // Drop only stale entries, not fresh notes that arrived during
                // control's accepted-only host handoff.
                OutRowSnapshot note_mark;
                const bool matching = route.bus->note_route.snapshot(note_mark) &&
                    note_mark.mark == out_wire_mark(route.config.notes.address, 0, 0,
                                                   route.config.notes.enabled != 0);
                if (matching) route.note_serial = std::max(route.note_serial, note_mark.serial);
                const auto head = route.bus->note_head.load(std::memory_order_acquire);
                auto tail = route.bus->note_tail.load(std::memory_order_relaxed);
                while (tail != head) {
                    const auto event = route.bus->notes[tail % route.bus->notes.size()];
                    const bool same_address = std::strncmp(event.address, route.config.notes.address,
                                                           sizeof(event.address)) == 0;
                    const bool stale_same = route.notes_cleanup && same_address &&
                        matching && event.serial < note_mark.mark_serial;
                    if (!route.config.notes.enabled || !same_address || stale_same) {
                        // An event newer than any observation of the current
                        // host table may belong to the next accepted write.
                        // Keep it in the ring until control catches up.
                        if (event.serial > route.note_serial) break;
                        route.dropped.fetch_add(1, std::memory_order_relaxed);
                        route.bus->note_tail.store(++tail, std::memory_order_release);
                        continue;
                    }
                    if (route.notes_cleanup && !matching && event.serial <= route.note_serial) {
                        route.dropped.fetch_add(1, std::memory_order_relaxed);
                        route.bus->note_tail.store(++tail, std::memory_order_release);
                        continue;
                    }
                    if (!budget) break;
                    Argument args[3]{};
                    args[0].type = 'i';
                    args[0].integer = event.key;
                    args[1].type = 'f';
                    args[1].real = event.velocity;
                    args[2].type = 'i';
                    args[2].integer = event.channel;
                    if (send(route, budget, route.config.notes.address, 3, args) &&
                        event.key >= 0 && event.key < 128 && event.channel >= -1 && event.channel <= 16)
                        route.notes_high[uint32_t(event.channel + 1)].set(uint32_t(event.key), event.velocity != 0);
                    route.note_serial = std::max(route.note_serial, event.serial);
                    ++tail;
                    route.bus->note_tail.store(tail, std::memory_order_release);
                }
                if (route.notes_cleanup && matching &&
                    tail == route.bus->note_head.load(std::memory_order_acquire))
                    route.notes_cleanup = false;
            }
        }
        if (need_socket) {
            bool still_needed = false;
            for (const auto &route : routes_)
                still_needed |= !route->lan_refused && (route->enabled || route->has_releases());
            if (!still_needed) {
                close_socket(sock);
                sock = invalid_socket;
#ifdef _WIN32
                WSACleanup();
#endif
                need_socket = false;
            }
        }
        if (!need_socket) {
            bool cleanup = false;
            for (const auto &route : routes_) cleanup |= !route->lan_refused && route->has_cleanup();
            if (!cleanup) break; // disabled cleanup never opens a socket
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    if (sock != invalid_socket) close_socket(sock);
#ifdef _WIN32
    if (need_socket) WSACleanup();
#endif
}
std::vector<OutState> OutHost::states() const {
    std::vector<OutState> result;
    result.reserve(routes_.size());
    for (const auto &item : routes_) {
        const auto &route = *item;
        OutState s;
        s.node = route.node;
        s.port = route.config.port;
        s.state = route.lan_refused ? "lan-refused" : !route.enabled ? "disabled" :
            socket_error_.load(std::memory_order_acquire) ? "error" : "sending";
        s.sent = route.sent.load(std::memory_order_relaxed);
        s.dropped = route.dropped.load(std::memory_order_relaxed) + route.bus->dropped.load(std::memory_order_relaxed);
        if (route.lan_refused) s.last_error = "lan-refused";
        else if (socket_error_.load(std::memory_order_relaxed)) s.last_error = "socket-error";
        else if (route.error.load(std::memory_order_relaxed)) s.last_error = "send-error";
        result.push_back(s);
    }
    return result;
}
} // namespace wirescape::osc
