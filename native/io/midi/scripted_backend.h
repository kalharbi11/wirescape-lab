// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "midi_backend.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <stdexcept>

namespace wirescape::midi {

// Explicitly instantiated, in-memory MIDI1 source. No libremidi observer,
// enumeration, kernel MIDI port, or device access is performed. One caller
// advances a virtual clock; bounded batches preserve overdue events for the
// next call. The Host owns this Backend via its existing injection seam.
class ScriptedBackend final : public Backend {
public:
    struct Config {
        unsigned bpm = 160;        // 120..180 BPM, 24 ppqn clock
        unsigned voices = 4;       // 1..4 independent MIDI channels
        uint32_t seed = 19;
        uint64_t origin_ns = 0;    // steady-clock origin supplied by the host
        uint32_t cc_period_ms = 10;
    };

    ScriptedBackend() : ScriptedBackend(Config{}) {}
    explicit ScriptedBackend(Config config) : config_(config) {
        if (config_.bpm < 120 || config_.bpm > 180 || config_.voices < 1 ||
            config_.voices > 4 || config_.cc_period_ms == 0)
            throw std::invalid_argument("Invalid device-off midi-m8 configuration");
    }

    const Endpoint& identity() const noexcept { return endpoint_; }
    std::vector<Endpoint> endpoints() override { return {endpoint_}; }

    bool open(const Endpoint& endpoint, Callback callback) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (online_ || endpoint.name != endpoint_.name ||
            endpoint.system_name != endpoint_.system_name || !callback.message)
            return false;
        callback_ = callback;
        online_ = true;
        return true;
    }

    void close(const Endpoint& endpoint) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (endpoint.name == endpoint_.name && endpoint.system_name == endpoint_.system_name) {
            online_ = false;
            callback_ = {};
        }
    }

    bool opened() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return online_;
    }

    // Test-only direct packets for deterministic saturation/failure assertions.
    // The callback is still the real Host/Service callback, never an engine bypass.
    bool inject(const uint8_t* bytes, size_t length, uint64_t timestamp_ns) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!online_ || !bytes || length < 1 || length > 3) return false;
        callback_.message(callback_.context, bytes, length, timestamp_ns);
        return true;
    }

    // elapsed_ns is monotonic relative to the injected source's virtual clock.
    // A fixed per-call bound makes even a 24-hour seek finite and interruptible.
    // A repeat call at the same elapsed_ns drains any remaining due messages.
    size_t advance_to(uint64_t elapsed_ns, size_t max_messages = 4096) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!online_ || elapsed_ns < last_elapsed_ns_) return 0;
        last_elapsed_ns_ = elapsed_ns;
        size_t count = 0;
        while (count < max_messages) {
            const std::array<uint64_t, 6> next{
                note_phase_ * 60000000000ULL / (uint64_t(config_.bpm) * 8),
                clock_tick_ * 60000000000ULL / (uint64_t(config_.bpm) * 24),
                sense_tick_ * 250000000ULL,
                cc_tick_ * uint64_t(config_.cc_period_ms) * 1000000ULL,
                sustain_tick_ * 4000000000ULL,
                panic_tick_ * 600000000000ULL
            };
            const auto it = std::min_element(next.begin(), next.end());
            const uint64_t at = *it;
            if (at > elapsed_ns) break;
            const size_t kind = size_t(it - next.begin());
            uint8_t bytes[3]{};
            size_t length = 3;
            switch (kind) {
                case 0: {
                    const uint64_t step = note_phase_ / 2;
                    const unsigned channel = unsigned(step % config_.voices);
                    bytes[0] = uint8_t((note_phase_ % 2 ? 0x80 : 0x90) | channel);
                    bytes[1] = uint8_t(48 + (config_.seed + step) % 36);
                    bytes[2] = note_phase_ % 2 ? 0 : 100;
                    ++note_phase_;
                    break;
                }
                case 1: bytes[0] = 0xf8; length = 1; ++clock_tick_; break;
                case 2: bytes[0] = 0xfe; length = 1; ++sense_tick_; break;
                case 3:
                    bytes[0] = 0xb0;
                    bytes[1] = 1;
                    bytes[2] = uint8_t((config_.seed + cc_tick_ * 17) % 128);
                    ++cc_tick_;
                    break;
                case 4:
                    bytes[0] = 0xb0;
                    bytes[1] = 64;
                    bytes[2] = sustain_tick_ % 2 ? 0 : 127;
                    ++sustain_tick_;
                    break;
                default:
                    bytes[0] = uint8_t(0xb0 | panic_channel_);
                    bytes[1] = 123; // All Notes Off: a release-classified MIDI1 CC.
                    bytes[2] = 0;
                    if (++panic_channel_ == config_.voices) {
                        panic_channel_ = 0;
                        ++panic_tick_;
                    }
                    break;
            }
            callback_.message(callback_.context, bytes, length, config_.origin_ns + at);
            ++count;
        }
        return count;
    }

private:
    Config config_;
    const Endpoint endpoint_{"Wirescape Scripted MIDI", "scripted:midi-m8:0"};
    mutable std::mutex mutex_;
    Callback callback_{};
    bool online_ = false;
    uint64_t last_elapsed_ns_ = 0;
    uint64_t note_phase_ = 0, clock_tick_ = 0, sense_tick_ = 0,
             cc_tick_ = 0, sustain_tick_ = 0, panic_tick_ = 1;
    unsigned panic_channel_ = 0;
};
} // namespace wirescape::midi
