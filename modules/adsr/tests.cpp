// SPDX-License-Identifier: GPL-3.0-only
// OB-g5 standalone device-off regression harness; build from this module's CMakeLists.txt.
// The old Gate math below is a frozen, independent source copy, not a wrapper over Adsr::process.
#include "../../tests/native/abi2/dsp_fixture.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <memory>
#include <vector>

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

// S7.9 draft-ahead: exact callback-level 2 s CHOKE/no-CHOKE pair. Reuse
// the T7.0 causal Butterworth 2 kHz, +/-25 ms window at 48 kHz. The
// historic T7.0/T7.0b files contain no ADSR or VCO CHOKE rows, so the
// unchanged source's diagnostic before-numbers must be captured first.
static double choke_peak_dbfs(const std::vector<float>& pcm, size_t at) {
    constexpr double rate = 48000., tau = 6.28318530717958647692;
    const double w = tau * 2000. / rate, c = std::cos(w);
    const double alpha = std::sin(w) / std::sqrt(2.);
    const double b0 = (1. + c) / (2. * (1. + alpha));
    const double b1 = -2. * b0, b2 = b0;
    const double a1 = -2. * c / (1. + alpha), a2 = (1. - alpha) / (1. + alpha);
    double x1 = 0., x2 = 0., y1 = 0., y2 = 0., peak = 0.;
    for (size_t i = 0; i < at + 1200; ++i) {
        const double x = pcm[i], y = b0*x + b1*x1 + b2*x2 - a1*y1 - a2*y2;
        x2 = x1; x1 = x; y2 = y1; y1 = y;
        if (i >= at - 1200) peak = std::max(peak, std::abs(y));
    }
    return 20. * std::log10(std::max(peak, 1e-15));
}
static std::vector<float> choke_capture(bool oscillator, bool trigger, bool choke) {
    const auto* d = oscillator ? ws::Module<ws2ports::Vco>::descriptor() :
                                 ws::Module<ws2ports::Adsr>::descriptor();
    auto f = std::make_unique<DspFixture>(d, 48000., 1);
    f->ins[0].flags = 0;
    if (oscillator) {
        f->ins[1].flags = 0;
        std::fill_n(f->input[1][0], DspFixture::frames, 0.f);
        std::fill_n(f->parameter[0][0], DspFixture::frames, 220.f);
    } else {
        f->parameter[0][0][0] = .001f;
        f->parameter[1][0][0] = .001f;
        f->parameter[2][0][0] = .6f;
        f->parameter[4][0][0] = trigger ? 1.f : 0.f;
        f->parameter[5][0][0] = 30.f;
    }
    std::vector<float> pcm(96000);
    for (uint32_t first = 0; first < pcm.size(); first += 128) {
        ws2_event e{};
        uint32_t count = 0;
        if (first == 0) { e = note(WS2_NOTE_ON, 17); e.key = 69; count = 1; }
        if (choke && first == 48000) { e = note(WS2_NOTE_CHOKE, 0); e.key = 69; count = 1; }
        f->process.events = {sizeof(ws2_event_list), count, count ? &e : nullptr};
        f->run(128);
        std::copy_n(f->output[0][0], 128, pcm.data() + first);
    }
    return pcm;
}
static void s79_choke_fail_first() {
    bool all_pass = true;
    for (int mode : {0, 1, 2}) {
        const bool oscillator = mode == 2, trigger = mode == 1;
        const auto ref = choke_capture(oscillator, trigger, false);
        const auto switched = choke_capture(oscillator, trigger, true);
        VERIFY(std::equal(ref.begin(), ref.begin()+48000, switched.begin()));
        VERIFY(std::all_of(switched.begin(), switched.end(), [](float x){ return std::isfinite(x); }));
        if (!oscillator) {
            // Ordinary note-on attack must still reach 1 in 48 samples.
            const auto first = std::find(ref.begin(), ref.begin()+256, 1.f);
            VERIFY(first - ref.begin() == 17+47);
        } else {
            // NOTE_ON preserves phase; no retrigger reset at frame 17.
            constexpr double tau = 6.28318530717958647692;
            VERIFY(std::abs(ref[17] - std::sin(tau * 220. * 17. / 48000.)) < 1e-6);
        }
        const double before = choke_peak_dbfs(switched, 48000);
        const double floor = choke_peak_dbfs(ref, 48000);
        // Absolute/floor alternative from M7. The relative target will
        // additionally be bound to the captured before row in the fix.
        const bool pass = before < -60. || std::abs(before - floor) <= .1;
        std::printf("S7.9 %s CHOKE peak_dbfs=%.9f no_switch_floor_dbfs=%.9f %s\n",
                    oscillator ? "VCO" : trigger ? "ADSR-trigger" : "ADSR-gate",
                    before, floor, pass ? "PASS" : "FAIL");
        all_pass = all_pass && pass;
    }
    std::fflush(stdout);
    VERIFY(all_pass);
}

int main() {
    default_gate_bit_identical();
    triggered_gate_timed_hold();
    note_retrigger_from_current_level_and_choke();
    cable_trigger_restarts_from_release_tail();
    std::puts("OB-g5 ADSR device-off source tests PASS");
    s79_choke_fail_first();
}
