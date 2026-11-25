// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>

namespace wirescape::osc {
// Exact wire metadata, not a lossy hash or an engine slot serial. The DSP
// never retains a slot pointer/copy: it publishes bounded output metadata to
// the host-owned bus when the slot changes, along with its block observation.
using OutWireMark = std::array<uint32_t, 19>;
inline OutWireMark out_wire_mark(const char (&address)[64], uint32_t kind, float deadband,
                                 bool enabled) noexcept {
    OutWireMark result{};
    std::memcpy(result.data(), address, 64);
    result[16] = kind;
    std::memcpy(&result[17], &deadband, sizeof(deadband));
    result[18] = enabled ? 1u : 0u;
    return result;
}
struct OutRowSnapshot {
    OutWireMark mark{};
    float value = 0;
    uint32_t rises = 0, falls = 0, blocks = 0;
    uint32_t baseline_rises = 0, baseline_falls = 0;
};
struct OutRow {
    std::atomic<float> value{0};
    std::atomic<uint32_t> rises{0}, falls{0};
    std::atomic<uint32_t> blocks{0};
    // Single render writer; all payload fields atomic. An acquire reader
    // seeing any newer payload release must also see its odd/newer sequence.
    // This avoids treating a partially published block as a new route.
    std::atomic<uint32_t> sequence{0}, baseline_rises{0}, baseline_falls{0};
    std::array<std::atomic<uint32_t>, 19> wire{};
    OutRow() noexcept { for (auto &word : wire) word.store(0, std::memory_order_relaxed); }
    void publish(const OutWireMark *mark, bool enabled, float last,
                 uint32_t up, uint32_t down) noexcept {
        sequence.fetch_add(1, std::memory_order_acq_rel);
        if (mark) {
            bool changed = false;
            for (size_t i = 0; i < wire.size(); ++i)
                changed |= wire[i].load(std::memory_order_relaxed) != (*mark)[i];
            if (changed) {
                baseline_rises.store(rises.load(std::memory_order_relaxed), std::memory_order_release);
                baseline_falls.store(falls.load(std::memory_order_relaxed), std::memory_order_release);
                for (size_t i = 0; i < wire.size(); ++i)
                    wire[i].store((*mark)[i], std::memory_order_release);
            }
        }
        if (enabled) {
            value.store(last, std::memory_order_release);
            if (up) rises.fetch_add(up, std::memory_order_release);
            if (down) falls.fetch_add(down, std::memory_order_release);
            blocks.fetch_add(1, std::memory_order_release);
        }
        sequence.fetch_add(1, std::memory_order_release);
    }
    // Bounded observation: if a callback is publishing, defer to next poll.
    bool snapshot(OutRowSnapshot &out) const noexcept {
        const auto before = sequence.load(std::memory_order_acquire);
        if (before & 1u) return false;
        for (size_t i = 0; i < wire.size(); ++i)
            out.mark[i] = wire[i].load(std::memory_order_acquire);
        out.value = value.load(std::memory_order_acquire);
        out.rises = rises.load(std::memory_order_acquire);
        out.falls = falls.load(std::memory_order_acquire);
        out.blocks = blocks.load(std::memory_order_acquire);
        out.baseline_rises = baseline_rises.load(std::memory_order_acquire);
        out.baseline_falls = baseline_falls.load(std::memory_order_acquire);
        return sequence.load(std::memory_order_acquire) == before;
    }
};
struct OutNote {
    int16_t key = 0;
    int16_t channel = 0;
    float velocity = 0;
    char address[64]{}; // exact route of this event, never a slot pointer
}; // velocity 0 = off
struct OutBus {
    std::array<OutRow, 8> rows{};
    OutRow note_route{}; // metadata only, published after note events for a changed slot
    std::array<OutNote, 64> notes{};
    std::atomic<uint32_t> note_head{0}, note_tail{0}; // SPSC: render pushes head, sender pops tail
    std::atomic<uint32_t> dropped{0};                 // ring full on the render side
};
} // namespace wirescape::osc
