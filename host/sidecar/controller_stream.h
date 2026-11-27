// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "protocol.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace wirescape::sidecar {
// A callback reserves a bank and ingress ordinal in one atomic RMW. One
// producer per enabled MIDI endpoint and one OSC worker: writers of the same
// key are serialized by the ingress owner, never by a capture-side mutex.
// The control thread closes a bank before inspecting any non-atomic payload;
// if an admitted producer was preempted, try again on the next control poll.
// No render thread touches this object. Banks are allocated at session start.
class ControllerStream {
public:
    struct Number {
        int64_t integer = 0;
        double real = 0;
        bool floating = false;
    };
private:
    enum class Kind : uint8_t { cc, pc, note_on, note_off, osc };
    static constexpr uint64_t cc_bit = 1, pc_bit = 2, note_bit = 4, osc_bit = 8, unmatched_bit = 16;
    static constexpr uint64_t kind_bits = 15, filter_bits = 31;
    // Wire device IDs already have a 256-Unicode-scalar limit. A valid
    // UTF-8 ID therefore fits 1024 bytes without truncation.
    static constexpr size_t identity_bytes = 1024, latest_capacity = 128, fifo_capacity = 256;
    static constexpr uint64_t bank_bit = uint64_t{1} << 63, fifo_increment = uint64_t{1} << 32;
    static constexpr uint64_t count_mask = 0xffffffffULL, fifo_mask = 0x7fffffffULL;
    // One bank cannot admit 2^31 events during a bounded flush or pipe
    // watchdog interval. Guard the packed counters anyway, with slack for
    // the maximum 16 endpoint writers plus the single OSC worker.
    static constexpr uint64_t reservation_limit = fifo_mask - 32;
    static_assert(std::atomic<uint64_t>::is_always_lock_free);
    static_assert(std::atomic<uint8_t>::is_always_lock_free);

    struct Key {
        std::array<char, identity_bytes> text{};
        uint16_t length = 0, port = 0;
        uint8_t channel = 0, index = 0;
        bool osc = false;
        bool equals(const Key &other) const noexcept {
            return osc == other.osc && port == other.port && channel == other.channel &&
                   index == other.index && length == other.length &&
                   std::memcmp(text.data(), other.text.data(), length) == 0;
        }
    };
    struct Payload {
        Kind kind = Kind::cc;
        uint64_t time = 0, epoch = 0, ordinal = 0;
        uint8_t value = 0, arg_count = 0;
        bool matched = false, more = false;
        std::array<Number, 4> args{};
    };
    struct Latest {
        std::atomic<uint8_t> state{0}; // 0 empty, 1 claimed, 2 published
        Key key;
        Payload payload;
    };
    struct Fifo {
        Key key;
        Payload payload;
    };
    struct Bank {
        std::array<Latest, latest_capacity> latest{};
        std::array<Fifo, fifo_capacity> fifo{};
        std::atomic<uint64_t> completed{0};
    };
    struct Pending {
        const Key *key;
        const Payload *payload;
    };

    std::unique_ptr<Bank[]> banks_ = std::make_unique<Bank[]>(2);
    // bit 63 selects the active bank, bits 32..62 count FIFO reservations,
    // bits 0..31 count all reservations (the per-window ingress ordinal).
    std::atomic<uint64_t> gate_{0};
    // High bits are a subscription epoch (changed on off/on), low bits
    // encode selected kinds and unmatched OSC. Control is the sole writer.
    std::atomic<uint64_t> filter_{0};
    std::atomic<uint64_t> dropped_fifo_{0}, dropped_latest_{0}, oversize_{0};
    uint64_t emitted_ = 0, retired_ = 0; // control owner only
    bool has_retired_ = false;

    static uint64_t now_us() noexcept {
        return static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count());
    }
    static uint64_t bit(Kind kind) noexcept {
        switch (kind) {
            case Kind::cc: return cc_bit;
            case Kind::pc: return pc_bit;
            case Kind::note_on:
            case Kind::note_off: return note_bit;
            case Kind::osc: return osc_bit;
        }
        return 0;
    }
    static bool allowed(uint64_t filter, Kind kind, bool matched) noexcept {
        return (filter & bit(kind)) &&
               (kind != Kind::osc || matched || (filter & unmatched_bit));
    }
    static const char *name(Kind kind) noexcept {
        switch (kind) {
            case Kind::cc: return "cc";
            case Kind::pc: return "pc";
            case Kind::note_on: return "noteOn";
            case Kind::note_off: return "noteOff";
            case Kind::osc: return "osc";
        }
        return "";
    }
    static Json kinds(uint64_t filter) {
        Json result = Json::array();
        if (filter & cc_bit) result.push_back("cc");
        if (filter & note_bit) result.push_back("note");
        if (filter & osc_bit) result.push_back("osc");
        if (filter & pc_bit) result.push_back("pc");
        return result;
    }

    void submit(const Key &key, Payload payload, uint64_t filter) noexcept {
        const bool latest = payload.kind == Kind::cc || payload.kind == Kind::osc;
        if ((gate_.load(std::memory_order_relaxed) & count_mask) >= reservation_limit) {
            if (latest) dropped_latest_.fetch_add(1, std::memory_order_relaxed);
            else dropped_fifo_.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        const uint64_t reservation = gate_.fetch_add(1 + (latest ? 0 : fifo_increment),
                                                       std::memory_order_acq_rel);
        Bank &bank = banks_[(reservation & bank_bit) != 0];
        payload.ordinal = reservation & count_mask;
        payload.epoch = filter & ~filter_bits;
        // An old subscription epoch may complete after unsubscribe; the
        // control owner filters that epoch before any event is serialized.
        if (!latest) {
            const uint64_t i = (reservation >> 32) & fifo_mask;
            if (i < fifo_capacity) {
                bank.fifo[i].key = key;
                bank.fifo[i].payload = payload;
            } else dropped_fifo_.fetch_add(1, std::memory_order_relaxed);
        } else {
            Latest *match = nullptr;
            for (auto &cell : bank.latest) {
                if (cell.state.load(std::memory_order_acquire) == 2 && cell.key.equals(key)) {
                    match = &cell;
                    break;
                }
            }
            if (match) {
                // The same physical ingress writer owns this key. The key
                // itself is immutable until all bank writers have completed.
                match->payload = payload;
            } else {
                for (auto &cell : bank.latest) {
                    uint8_t empty = 0;
                    if (!cell.state.compare_exchange_strong(empty, 1, std::memory_order_acq_rel))
                        continue;
                    cell.key = key;
                    cell.payload = payload;
                    cell.state.store(2, std::memory_order_release);
                    match = &cell;
                    break;
                }
                if (!match) dropped_latest_.fetch_add(1, std::memory_order_relaxed);
            }
        }
        bank.completed.fetch_add(1, std::memory_order_acq_rel);
    }
    static Json wire(const Key &key, const Payload &payload) {
        Json event = {{"kind", name(payload.kind)}, {"t", payload.time}};
        if (key.osc) {
            event["port"] = key.port;
            event["address"] = std::string(key.text.data(), key.length);
            event["matched"] = payload.matched;
            event["args"] = Json::array();
            for (unsigned i = 0; i < payload.arg_count; ++i) {
                const auto &arg = payload.args[i];
                if (arg.floating) event["args"].push_back(arg.real);
                else event["args"].push_back(arg.integer);
            }
            if (payload.more) event["more"] = true;
        } else {
            event["deviceId"] = std::string(key.text.data(), key.length);
            event["channel"] = key.channel;
            switch (payload.kind) {
                case Kind::cc:
                    event["controller"] = key.index; event["value"] = payload.value; break;
                case Kind::pc:
                    event["program"] = key.index; break;
                case Kind::note_on:
                case Kind::note_off:
                    event["note"] = key.index; event["velocity"] = payload.value; break;
                case Kind::osc: break;
            }
        }
        return event;
    }

public:
    // Control owner only. The protocol command validates unknown/repeated kinds.
    void configure(const std::vector<std::string> &selected, bool unmatched) {
        uint64_t mask = 0;
        for (const auto &kind : selected) {
            if (kind == "cc") mask |= cc_bit;
            if (kind == "pc") mask |= pc_bit;
            if (kind == "note") mask |= note_bit;
            if (kind == "osc") mask |= osc_bit;
        }
        if (unmatched) mask |= unmatched_bit;
        const auto old = filter_.load(std::memory_order_relaxed);
        const bool was_on = (old & kind_bits) != 0, on = (mask & kind_bits) != 0;
        const auto epoch = (old & ~filter_bits) + (was_on != on ? filter_bits + 1 : 0);
        // Discard prior subscription windows without waiting for an OS callback.
        // Epoch tagging also covers a preempted writer which finishes later.
        if (!was_on && on) {
            (void)drain();
            (void)drain();
        }
        filter_.store(epoch | mask, std::memory_order_release);
        if (!on) {
            (void)drain();
            (void)drain();
        }
    }
    Json setting() const {
        const auto filter = filter_.load(std::memory_order_acquire);
        return {{"kinds", kinds(filter)}, {"oscUnmatched", bool(filter & unmatched_bit)}};
    }
    bool enabled() const noexcept { return (filter_.load(std::memory_order_acquire) & kind_bits) != 0; }

    // Backend callback: use the full stable device ID, never a reusable slot
    // index. Only fixed-size copies, clock read and lock-free atomics here.
    void midi(std::string_view device, std::string_view system, const uint8_t *bytes, size_t size) noexcept {
        if (!bytes || !size) return;
        const uint64_t filter = filter_.load(std::memory_order_acquire);
        if (!(filter & (cc_bit | pc_bit | note_bit))) return;
        Kind kind;
        switch (bytes[0] >> 4) {
            case 8: kind = Kind::note_off; break;
            case 9:
                if (size != 3) return;
                kind = bytes[2] ? Kind::note_on : Kind::note_off; break;
            case 11: kind = Kind::cc; break;
            case 12: kind = Kind::pc; break;
            default: return;
        }
        if (!allowed(filter, kind, false) || size != (kind == Kind::pc ? 2u : 3u) ||
            bytes[1] > 127 || (size == 3 && bytes[2] > 127)) return;
        // Invalid IDs cannot be advertised by the existing device schema.
        if (device.size() >= identity_bytes || system.size() > identity_bytes - device.size() - 1)
            return;
        Payload payload;
        payload.kind = kind;
        payload.time = now_us();
        payload.value = size == 3 ? bytes[2] : 0;
        Key key;
        key.channel = uint8_t((bytes[0] & 15u) + 1);
        key.index = bytes[1];
        key.length = static_cast<uint16_t>(device.size() + 1 + system.size());
        std::memcpy(key.text.data(), device.data(), device.size());
        key.text[device.size()] = '|';
        std::memcpy(key.text.data() + device.size() + 1, system.data(), system.size());
        submit(key, payload, filter);
    }
    // Single OSC ingress worker; raw numeric arguments have already been
    // decoded, and enabled/disabled-only match classification is provided by
    // the existing host route filters. No graph or render work here.
    void osc(uint16_t port, std::string_view address, bool matched, bool disabled_only,
             const std::array<Number, 4> &args, uint8_t count, bool more) noexcept {
        const uint64_t filter = filter_.load(std::memory_order_acquire);
        if (disabled_only || !allowed(filter, Kind::osc, matched)) return;
        if (address.size() > 128) {
            oversize_.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        if (address.empty()) return;
        Key key;
        key.osc = true; key.port = port; key.length = static_cast<uint16_t>(address.size());
        std::memcpy(key.text.data(), address.data(), address.size());
        Payload payload;
        payload.kind = Kind::osc; payload.time = now_us();
        payload.matched = matched; payload.more = more || count > 4;
        for (unsigned i = 0; i < count && i < args.size(); ++i) {
            if (args[i].floating && !std::isfinite(args[i].real)) {
                payload.more = true;
                continue;
            }
            payload.args[payload.arg_count++] = args[i];
        }
        submit(key, payload, filter);
    }

    // Control owner only, and only when the writer slot is available. The
    // exchange is the window boundary; no producer can subsequently reserve
    // that bank. Do not touch any payload until every reservation completes.
    Json drain() {
        Json events = Json::array();
        if (!has_retired_) {
            const uint64_t active = gate_.load(std::memory_order_acquire);
            if (!(active & count_mask)) return events;
            retired_ = gate_.exchange((active & bank_bit) ^ bank_bit, std::memory_order_acq_rel);
            has_retired_ = true;
        }
        Bank &bank = banks_[(retired_ & bank_bit) != 0];
        if (bank.completed.load(std::memory_order_acquire) != (retired_ & count_mask))
            return events;
        std::array<Pending, latest_capacity + fifo_capacity> pending{};
        size_t used = 0;
        const auto filter = filter_.load(std::memory_order_acquire);
        auto include = [&](const Key &key, const Payload &payload) {
            if (payload.epoch == (filter & ~filter_bits) &&
                allowed(filter, payload.kind, payload.matched))
                pending[used++] = {&key, &payload};
        };
        for (auto &cell : bank.latest)
            if (cell.state.load(std::memory_order_relaxed) == 2) include(cell.key, cell.payload);
        const size_t fifo_count = static_cast<size_t>((retired_ >> 32) & fifo_mask);
        for (size_t i = 0; i < (std::min)(fifo_count, fifo_capacity); ++i)
            include(bank.fifo[i].key, bank.fifo[i].payload);
        std::sort(pending.begin(), pending.begin() + used, [](const Pending &a, const Pending &b) {
            return a.payload->ordinal < b.payload->ordinal;
        });
        for (size_t i = 0; i < used; ++i)
            events.push_back(wire(*pending[i].key, *pending[i].payload));
        emitted_ += used;
        for (auto &cell : bank.latest) cell.state.store(0, std::memory_order_relaxed);
        bank.completed.store(0, std::memory_order_relaxed);
        has_retired_ = false;
        return events;
    }
    Json status() const {
        if (!enabled()) return nullptr;
        auto result = setting();
        result["events"] = emitted_;
        result["dropped"] = {{"fifo", dropped_fifo_.load(std::memory_order_relaxed)},
                             {"latest", dropped_latest_.load(std::memory_order_relaxed)},
                             {"oversize", oversize_.load(std::memory_order_relaxed)}};
        return result;
    }
};
} // namespace wirescape::sidecar
