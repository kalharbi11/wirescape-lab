// SPDX-License-Identifier: GPL-3.0-only
// OB-g5 standalone device-off regression harness; build from this module's CMakeLists.txt.
// The old Gate math below is a frozen, independent source copy, not a wrapper over Adsr::process.
#include "../../tests2/dsp_fixture.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <memory>

struct OriginalGate {
    float level = 0, start = 0;
    uint64_t elapsed = 0, duration = 1;
    int stage = 0;
    bool gated = false;
    ws::Schmitt edge;
    void begin(int next, float seconds, double rate) {
        stage = next;
        start = level;
        elapsed = 0;
        duration = std::max<uint64_t>(1, static_cast<uint64_t>(std::llround(seconds * rate)));
    }
    float sample(float in, float attack, float decay, float sustain, float release, double rate) {
        bool high = edge.process(in);
        if (high && !gated) { gated = true; begin(1, attack, rate); }
        else if (!high && gated) { gated = false; begin(4, release, rate); }
        if (stage == 1) {
            level = start + (1 - start) * static_cast<float>(++elapsed) / static_cast<float>(duration);
            if (elapsed >= duration) { level = 1; begin(2, decay, rate); }
        } else if (stage == 2) {
            level = start + (sustain - start) * static_cast<float>(++elapsed) / static_cast<float>(duration);
            if (elapsed >= duration) { level = sustain; stage = 3; }
        } else if (stage == 3) level = sustain;
        else if (stage == 4) {
            level = start * (1 - static_cast<float>(++elapsed) / static_cast<float>(duration));
            if (elapsed >= duration) { level = 0; stage = 0; }
        }
        return level;
    }
};
static ws2_event note(uint32_t type, uint32_t offset, uint32_t source = 7, int32_t id = 21) {
    ws2_event e{};
    e.struct_size = sizeof(e);
    e.type = type;
    e.offset = offset;
    e.channel = 0;
    e.source_id = source;
    e.note_id = id;
    e.key = 60;
    e.value = 1.f;
    return e;
}
static std::unique_ptr<DspFixture> rig(double rate = 48000.) {
    auto p = std::make_unique<DspFixture>(ws::Module<ws2ports::Adsr>::descriptor(), rate, 1);
    VERIFY(p->d->param_count == 6 && p->d->output_count == 1);
    VERIFY(std::strcmp(p->d->params[4].id, "mode") == 0);
    VERIFY(std::strcmp(p->d->params[5].id, "hold") == 0);
    VERIFY(p->d->params[4].initial == 0.f && p->d->params[5].initial == 0.f);
    return p;
}
static void default_gate_bit_identical() {
    for (double rate : {44100., 48000., 96000.}) {
        auto f = rig(rate);
        // A nonzero hold is inert while the default mode is Gate.
        f->parameter[0][0][0] = .001f;
        f->parameter[1][0][0] = .0015f;
        f->parameter[2][0][0] = .63f;
        f->parameter[3][0][0] = .002f;
        f->parameter[5][0][0] = .2f;
        OriginalGate old;
        uint32_t frame = 0;
        for (uint32_t count : {1u, 17u, 64u, 128u, 17u, 256u, 64u, 128u}) {
            for (uint32_t i = 0; i < count; ++i) {
                const auto absolute = frame + i;
                const bool on = (absolute >= 5 && absolute < 68) ||
                                (absolute >= 110 && absolute < 177) ||
                                (absolute >= 343 && absolute < 455);
                f->input[0][0][i] = on ? 1.f : 0.f;
            }
            f->run(count);
            for (uint32_t i = 0; i < count; ++i) {
                const float expected = old.sample(f->input[0][0][i], .001f, .0015f,
                                                  .63f, .002f, rate);
                const float actual = f->output[0][0][i];
                VERIFY(std::memcmp(&expected, &actual, sizeof(float)) == 0);
            }
            frame += count;
        }
    }
}
static void triggered_gate_timed_hold() {
    const double rate = 48000.;
    auto f = rig(rate);
    f->parameter[0][0][0] = .001f; // 48 samples
    f->parameter[1][0][0] = .001f; // 48 samples
    f->parameter[2][0][0] = .6f;
    f->parameter[3][0][0] = .001f; // 48 samples
    f->parameter[4][0][0] = 1.f;  // Trigger
    f->parameter[5][0][0] = .002f; // 96 samples at Sustain
    std::array<float, 256> samples{};
    for (uint32_t block = 0; block < 2; ++block) {
        for (uint32_t i = 0; i < 128; ++i) f->input[0][0][i] = block == 0 && i < 64 ? 1.f : 0.f;
        f->run(128);
        std::copy_n(f->output[0][0], 128, samples.data() + 128 * block);
    }
    VERIFY(std::abs(samples[47] - 1.f) < 1e-6f);
    VERIFY(std::abs(samples[95] - .6f) < 1e-6f);
    for (uint32_t i = 96; i < 192; ++i) VERIFY(samples[i] == samples[95]);
    VERIFY(samples[192] < .6f && samples[192] > 0);
    VERIFY(samples[239] == 0 && samples[240] == 0);
    // Falling edge at 64 never begins Release in Trigger mode.
    VERIFY(samples[65] > .6f);

    // Zero hold: Release starts as soon as Decay reaches Sustain.
    auto zero = rig(rate);
    zero->parameter[0][0][0] = .001f;
    zero->parameter[1][0][0] = .001f;
    zero->parameter[2][0][0] = .6f;
    zero->parameter[3][0][0] = .001f;
    zero->parameter[4][0][0] = 1.f;
    zero->parameter[5][0][0] = 0.f;
    for (uint32_t i = 0; i < 128; ++i) zero->input[0][0][i] = i < 64 ? 1.f : 0.f;
    zero->run(128);
    VERIFY(std::abs(zero->output[0][0][95] - .6f) < 1e-6f);
    VERIFY(zero->output[0][0][96] < zero->output[0][0][95]);
}
static void note_retrigger_from_current_level_and_choke() {
    auto f = rig(48000.);
    f->ins[0].flags = 0; // Notes events are authoritative without a gate cable.
    f->parameter[0][0][0] = .001f;
    f->parameter[1][0][0] = .001f;
    f->parameter[2][0][0] = .6f;
    f->parameter[3][0][0] = .001f;
    f->parameter[4][0][0] = 1.f;
    f->parameter[5][0][0] = .01f;
    std::array<ws2_event, 3> events{note(WS2_NOTE_ON, 0), note(WS2_NOTE_OFF, 64),
                                    note(WS2_NOTE_ON, 120, 7, 22)};
    f->process.events = {sizeof(ws2_event_list), uint32_t(events.size()), events.data()};
    f->run(256);
    VERIFY(std::abs(f->output[0][0][119] - .6f) < 1e-6f);
    VERIFY(f->output[0][0][120] > f->output[0][0][119]);
    VERIFY(f->output[0][0][120] < .7f); // no jump to full level or back to zero
    VERIFY(f->output[0][0][255] > .5f); // release from Note Off was ignored
    // An obsolete Note Off must not release the new note.
    auto obsolete = note(WS2_NOTE_OFF, 0, 7, 21);
    f->process.events = {sizeof(ws2_event_list), 1, &obsolete};
    f->run(1);
    VERIFY(f->output[0][0][0] > .5f);
    // A matching CHOKE clears the active tail immediately, as in Gate mode.
    auto choke = note(WS2_NOTE_CHOKE, 0, 7, 22);
    f->process.events = {sizeof(ws2_event_list), 1, &choke};
    f->run(64);
    for (uint32_t i = 0; i < 64; ++i) VERIFY(f->output[0][0][i] == 0);
    f->reset();
    f->process.events = {sizeof(ws2_event_list), 0, nullptr};
    f->run(64);
    for (uint32_t i = 0; i < 64; ++i) VERIFY(f->output[0][0][i] == 0);
}
static void cable_trigger_restarts_from_release_tail() {
    auto f = rig(48000.);
    f->parameter[0][0][0] = .001f;
    f->parameter[1][0][0] = .001f;
    f->parameter[2][0][0] = .6f;
    f->parameter[3][0][0] = .002f;
    f->parameter[4][0][0] = 1.f;
    f->parameter[5][0][0] = 0.f;
    // First pulse fully traverses A, D, and part of R.
    for (uint32_t i = 0; i < 256; ++i)
        f->input[0][0][i] = i < 64 || i >= 130 && i < 145 ? 1.f : 0.f;
    f->run(256);
    VERIFY(f->output[0][0][129] > 0 && f->output[0][0][129] < .6f);
    VERIFY(f->output[0][0][130] > f->output[0][0][129]);
    VERIFY(f->output[0][0][130] < .7f);
}
int main() {
    default_gate_bit_identical();
    triggered_gate_timed_hold();
    note_retrigger_from_current_level_and_choke();
    cable_trigger_restarts_from_release_tail();
    std::puts("OB-g5 ADSR device-off source tests PASS");
}
