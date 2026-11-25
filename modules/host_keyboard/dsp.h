// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../../engine/voice/note_to_cv.h"
#include "wirescape_sdk.h"
namespace ws2ports {
struct HostKeyboard {
    static constexpr ws::Info info{"host.keyboard", "Keyboard", 1};
    static constexpr std::array<ws2_port, 0> inputs{};
    static constexpr std::array outputs{ws::port("pitch", "Pitch", WS2_PITCH), ws::port("gate", "Gate", WS2_GATE),
                                        ws::port("velocity", "Velocity", WS2_CV_UNI),
                                        ws::port("notes", "Notes", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array params{
        ws::param("voices", "Voices", 1, 16, 8, "", WS2_STEPPED | WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 1),
        ws::param("mode", "Mode", 0, 3, 0, "", WS2_STEPPED | WS2_AUTOMATABLE, WS2_LINEAR, 1, 4, 1),
        ws::param("octave", "Octave", -3, 3, 0, "", WS2_STEPPED | WS2_AUTOMATABLE, WS2_LINEAR, 2, 4, 1)};
    wirescape::voice::NoteToCv core;
    uint32_t max_channels = 16;
    int voices = 0, mode = -1;
    std::array<ws2_event, 16> pending{};
    std::array<bool, 16> emitted{};
    void prepare(const ws::Setup &s) { max_channels = s.max_channels(); }
    void reset() {
        core.reset();
        voices = 0;
        mode = -1;
        pending = {};
        emitted = {};
    }
    // Count and policy changes are rare, but configure_at is called every
    // sample. Keep the release/snapshot path out of the steady-state loop
    // so the compiler does not reserve its large temporary stack/register set.
    template <class Emit>
#if defined(_MSC_VER)
    __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
    __attribute__((noinline))
#endif
    void change_configuration(int count, int policy, uint32_t i, Emit emit) {
        ws2_event e{};
        e.struct_size = sizeof(e);
        e.offset = i;
        e.source_id = UINT32_MAX;
        if (voices && policy == mode) core.resize(count, e, emit);
        else {
            core.release_all(UINT32_MAX, e, emit);
            wirescape::voice::Config cfg;
            cfg.max_voices = count;
            cfg.mode = static_cast<wirescape::voice::Mode>(policy);
            core.configure(cfg);
        }
        voices = count;
        mode = policy;
    }
    template <class Emit> void configure_at(ws::Block &b, uint32_t i, Emit emit) {
        const int count =
            std::clamp<int>(static_cast<int>(std::lround(b.param(0).value(0, i))), 1, static_cast<int>(max_channels));
        const int policy = std::clamp<int>(static_cast<int>(std::lround(b.param(1).value(0, i))), 0, 3);
        if (count != voices || policy != mode) change_configuration(count, policy, i, emit);
    }
    void process(ws::Block &b) {
        b.out(3).set_channels(0);
        auto emit = [&](const ws2_event &e) {
            if (e.channel < 0 || e.channel >= 16) return;
            const auto c = static_cast<uint32_t>(e.channel);
            if (pending[c].type) {
                auto retry = pending[c];
                retry.offset = e.offset;
                if (!b.emit(3, retry)) return;
                pending[c] = {};
                emitted[c] = false;
            }
            if (e.type == WS2_NOTE_ON) {
                if (b.emit(3, e)) emitted[c] = true;
            } else if (emitted[c]) {
                if (b.emit(3, e)) emitted[c] = false;
                else pending[c] = e;
            }
        };
        for (uint32_t c = 0; c < 16; ++c)
            if (pending[c].type) {
                auto e = pending[c];
                e.offset = 0;
                if (b.emit(3, e)) {
                    pending[c] = {};
                    emitted[c] = false;
                }
            }
        b.split(
            [&](uint32_t first, uint32_t end) {
                // Constant controls cannot change within this split range.
                // Keep event-offset configuration below and sample evaluation
                // for either nonconstant control.
                const bool fixed_config = b.param(0).constant() && b.param(1).constant();
                if (fixed_config) configure_at(b, first, emit);
                for (uint32_t i = first; i < end; ++i) {
                    if (!fixed_config) configure_at(b, i, emit);
                    for (int p = 0; p < 3; ++p) {
                        b.out(p).set_channels(core.allocator().voice_count());
                        b.out(p).mark_constant(false);
                    }
                    for (int c = 0; c < core.allocator().voice_count(); ++c) {
                        const auto &v = core.allocator().voice(c);
                        b.out(0).ch(c)[i] = v.pitch + b.param(2).value(0, i);
                        b.out(1).ch(c)[i] = v.gate && !(v.trigger && v.retrigger) ? 1.f : 0.f;
                        b.out(2).ch(c)[i] = v.velocity;
                    }
                    core.allocator().clear_triggers();
                }
            },
            [&](const ws2_event &e) {
                configure_at(b, std::min(e.offset, b.frames() - 1), emit);
                core.event(e, emit);
            });
    }
};
} // namespace ws2ports
