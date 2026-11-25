// SPDX-License-Identifier: GPL-3.0-only
// OB-c pre-S6: device-free production MIDI UMP -> MIDI In -> MIDI to CV
// -> VCO / ADSR / VCA / Output. No MIDI host/device is opened.
// Does not stand in for the owner's Windows endpoint/subscription validation.
#include "../../../engine/engine2.h"
#include "../../../host/midi/module_test_support.h"
#include "../../../modules/midi_in/dsp.h"
#include "../../../modules/midi_to_cv/dsp.h"
#include "../../../modules/vco/dsp.h"
#include "../../../modules/adsr/dsp.h"
#include "../../../modules/vca/dsp.h"
#include "../../../modules/output/dsp.h"
#include "allocation_watch.h"
#include <algorithm>
#include <cmath>
#include <cstdio>

using namespace wirescape;
using namespace wirescape::midi;
using namespace wirescape::engine2;

// The owner's MIDI -> CV missing-pitch/gate complaint is not exercised by
// merely checking a module's internal event parser. Traverse the actual
// graph's event port, CV cables, envelope, amplifier and final audio route.
static void midi_to_audio(double rate) {
    Config config;
    config.sample_rate = rate;
    config.max_block = 128;
    Engine engine(config);
    const auto producer = engine.register_producer();
    REQUIRE(producer >= 0);
    REQUIRE(engine.add_node(1, ws::Module<MidiIn>::descriptor()));
    REQUIRE(engine.add_node(2, ws::Module<MidiToCv>::descriptor()));
    REQUIRE(engine.add_node(3, ws::Module<ws2ports::Vco>::descriptor()));
    REQUIRE(engine.add_node(4, ws::Module<ws2ports::Adsr>::descriptor()));
    REQUIRE(engine.add_node(5, ws::Module<ws2ports::Vca>::descriptor()));
    REQUIRE(engine.add_node(6, ws::Module<ws2ports::Output>::descriptor()));
    REQUIRE(engine.connect(1, 0, 2, 0)); // MIDI event, never pitch CV
    REQUIRE(engine.connect(2, 0, 3, 0)); // native pitch CV
    REQUIRE(engine.connect(2, 1, 4, 0)); // native gate CV
    REQUIRE(engine.connect(3, 0, 5, 0)); // audible VCO
    REQUIRE(engine.connect(4, 0, 5, 1)); // ADSR opens VCA
    REQUIRE(engine.connect(5, 0, 6, 0));
    REQUIRE(engine.output(6, 0, 0));
    REQUIRE(engine.set_parameter(2, 0, 1)); // a single, observable C4 voice
    REQUIRE(engine.prepare());

    // Synthetic real UMP event at the engine ingress, not FakeEngine MIDI.
    REQUIRE(engine.enqueue(uint32_t(producer), 1, WS2_DIRECT_PORT,
                           midi1(0x90, 60, 127, 0, 7), 0) == WS2_OK);
    float samples[128]{};
    float *channels[]{samples};
    bool saw_gate = false, saw_envelope = false, saw_audio = false;
    uint64_t allocations = 0;
    // Note-on is held for 4 blocks. Inspect actual sample values after each
    // process, without assuming the envelope is instantaneous at frame zero.
    for (unsigned block = 0; block < 4; ++block) {
        {
            allocation_watch::Scope watch;
            REQUIRE(engine.render(channels, 1, 128) == WS2_OK);
            allocations += watch.allocations();
        }
        for (unsigned frame = 0; frame < 128; ++frame) {
            const float pitch = engine.output_sample(2, 0, 0, frame);
            const float gate = engine.output_sample(2, 1, 0, frame);
            const float envelope = engine.output_sample(4, 0, 0, frame);
            const float audio = samples[frame];
            REQUIRE(std::isfinite(pitch) && std::isfinite(gate)
                    && std::isfinite(envelope) && std::isfinite(audio));
            REQUIRE(std::abs(pitch) < 0.00001f); // MIDI note 60 = 0 V/C4
            saw_gate |= gate == 1.f;
            saw_envelope |= envelope > 0.f;
            saw_audio |= std::abs(audio) > 0.f;
        }
    }
    REQUIRE(saw_gate && saw_envelope && saw_audio);
    REQUIRE(allocations == 0 && engine.meter().faults == 0);
    REQUIRE(engine.enqueue(uint32_t(producer), 1, WS2_DIRECT_PORT,
                           midi1(0x80, 60, 0, 0, 7), engine.meter().frame) == WS2_OK);
    REQUIRE(engine.render(channels, 1, 128) == WS2_OK);
    for (unsigned frame = 0; frame < 128; ++frame)
        REQUIRE(engine.output_sample(2, 1, 0, frame) == 0.f);
    REQUIRE(engine.meter().faults == 0);
}

int main() {
    midi_to_audio(44100.);
    midi_to_audio(48000.);
    std::puts("OB-c MIDI: real UMP -> MIDI In -> MIDI to CV -> VCO/ADSR/VCA audible, device off");
}
