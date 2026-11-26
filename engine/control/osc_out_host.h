// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../../modules/osc_out/config.h"
#include <array>
#include <atomic>
#include <bitset>
#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace wirescape::osc {
struct Message;
struct OscOutRoutes;
// Test-only deterministic send seam; production uses the validated route destination.
using SendOverride = bool (*)(const Message &, uint16_t);
struct OutState {
    uint32_t node = 0, port = 0;
    const char *state = "disabled"; // sending | disabled | error | lan-refused
    uint64_t sent = 0, dropped = 0;
    const char *last_error = nullptr;
};

// One quiescently configured, control-owned sender per prepared graph.
// All buses outlive the module instances; the worker never touches AppEngine.
class OutHost {
    struct RowCursor {
        uint32_t rises = 0, falls = 0;
        bool wait_for_table = false;
        uint32_t seen_serial = 0;
        float previous = 0;
        bool initialized = false, gate_high = false, sent_high = false, retry = false;
        std::chrono::steady_clock::time_point last_send{};
    };
    struct Route {
        uint32_t node = 0;
        uint32_t destination = 0x7f000001u; // host byte order
        bool lan_refused = false;
        OutConfiguration config{};
        std::unique_ptr<OutBus> bus = std::make_unique<OutBus>();
        std::array<RowCursor, 8> cursors{};
        // Only the sender updates delivered levels. Control moves them to a
        // bounded old-address release set after joining the worker.
        std::array<std::bitset<128>, 18> notes_high{}, notes_release{}; // channel -1..16
        std::array<OutRowConfig, 8> gate_release{};
        std::bitset<8> release_gates{};
        char release_notes_address[64]{};
        bool notes_cleanup = false;
        uint32_t note_serial = 0;
        bool has_cleanup() const noexcept {
            if (notes_cleanup) return true;
            for (const auto &cursor : cursors) if (cursor.wait_for_table) return true;
            return false;
        }
        void drop_releases() noexcept {
            uint64_t count = release_gates.count();
            release_gates.reset();
            for (auto &keys : notes_release) { count += keys.count(); keys.reset(); }
            dropped.fetch_add(count, std::memory_order_relaxed);
        }
        bool has_releases() const noexcept {
            if (release_gates.any()) return true;
            for (const auto &keys : notes_release) if (keys.any()) return true;
            return false;
        }
        std::atomic<uint64_t> sent{0}, dropped{0};
        std::atomic<uint32_t> error{0};
        bool enabled = false;
    };
    std::vector<std::unique_ptr<Route>> routes_;
    std::map<uint32_t, OutBus *> buses_;
    std::atomic<bool> running_{false};
    std::thread worker_;
    std::atomic<uint32_t> socket_error_{0};
    SendOverride send_override_ = nullptr;

    void loop() noexcept;

  public:
    explicit OutHost(const std::string &document, SendOverride send_override = nullptr,
                     bool allow_network = false);
    ~OutHost() { stop(); }
    OutHost(const OutHost &) = delete;
    OutHost &operator=(const OutHost &) = delete;
    const std::map<uint32_t, OutBus *> &buses() const noexcept { return buses_; }
    // Adopt validated data only after the engine has accepted the slot write.
    // The construction bus stays owned by this graph; no instance replacement.
    void commit_data(uint32_t node, const OscOutRoutes &) noexcept;
    void start() noexcept;
    void stop() noexcept;
    std::vector<OutState> states() const;
};
} // namespace wirescape::osc
