// SPDX-License-Identifier: GPL-3.0-only
// A10/OB r2.1: device-free, frame-stamped internal/external Groove transport.
// Compile as an isolated native CTest when the lead grants new target wiring.
#include "../modules2/groove/dsp.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace {
constexpr uint32_t kBlock = 64;
#define INFRA(x) do { if (!(x)) { std::fprintf(stderr, "INFRA_A10_GROOVE:%d: %s\n", __LINE__, #x); std::abort(); } } while (0)
#define ORACLE(x, cause) do { if (!(x)) { std::fprintf(stderr, "PRODUCT_A10_GROOVE:%s frame=%llu\n", cause, static_cast<unsigned long long>(rig.frame)); std::abort(); } } while (0)

struct Event {
    uint64_t frame;
    uint32_t type;
    int32_t key;
};

struct Rig {
    groove::Sequencer sequencer;
    std::array<std::array<float, kBlock>, 18> storage{};
    std::array<float *, 18> output_rows{};
    std::array<ws2_signal_out, 18> outputs{};
    std::array<ws2_event_out, 18> event_outputs{};
    std::array<std::array<float, kBlock>, 3> input_storage{};
    std::array<const float *, 3> input_rows{};
    std::array<ws2_signal, 3> inputs{};
    std::array<float, 10> controls{};
    std::array<const float *, 10> control_rows{};
    std::array<ws2_signal, 10> params{};
    std::vector<Event> events;
    ws2_process raw{};
    uint64_t frame = 0;

    static int WS2_CALL collect(void *context, uint32_t port, const ws2_event *e) {
        auto &r = *static_cast<Rig *>(context);
        INFRA(port == 4 || port == 9);
        INFRA(e->offset < kBlock);
        r.events.push_back({r.frame + e->offset, e->type, e->key});
        return WS2_OK;
    }

    Rig() {
        for (uint32_t i = 0; i < outputs.size(); ++i) {
            output_rows[i] = storage[i].data();
            outputs[i] = {sizeof(ws2_signal_out), &output_rows[i], 1, 0, 1};
            event_outputs[i] = {sizeof(ws2_event_out), this, i, collect};
        }
        for (uint32_t i = 0; i < inputs.size(); ++i) {
            input_rows[i] = input_storage[i].data();
            inputs[i] = {sizeof(ws2_signal), &input_rows[i], 1, 0};
        }
        for (uint32_t i = 0; i < params.size(); ++i) {
            control_rows[i] = &controls[i];
            params[i] = {sizeof(ws2_signal), &control_rows[i], 1, WS2_CONSTANT};
        }
        raw.frames = kBlock;
        raw.input_count = static_cast<uint32_t>(inputs.size());
        raw.inputs = inputs.data();
        raw.output_count = static_cast<uint32_t>(outputs.size());
        raw.outputs = outputs.data();
        raw.event_outputs = event_outputs.data();
        raw.param_count = static_cast<uint32_t>(params.size());
        raw.params = params.data();
        auto &track = sequencer.pattern.tracks[0];
        track.length = 8;
        track.div = 1;
        for (auto &step : track.steps) step.kind = groove::Rest;
        track.steps[0].kind = groove::Note;
        track.steps[0].key = 60;
        track.steps[0].velocity = 0.8f;
        track.steps[0].gate_q = 4;
        sequencer.reset();
        sequencer.internal_samples_per_step = 256.;
        sequencer.samples_per_step = 256.;
    }

    void render() {
        ws::Block block(raw);
        sequencer.process(block);
        frame += kBlock;
    }
    uint64_t first_note() const {
        for (const auto &e : events)
            if (e.type == WS2_NOTE_ON) return e.frame;
        return UINT64_MAX;
    }
};

void internal_start_stop() {
    Rig rig;
    rig.render();
    INFRA(!rig.sequencer.running && rig.events.empty());
    const uint64_t start = rig.frame;
    rig.controls[0] = 1.f; // START applies at first frame of this block.
    rig.render();
    ORACLE(rig.first_note() >= start && rig.first_note() < start + kBlock,
           "internal_start_gate_later_than_one_block");
    ORACLE(rig.sequencer.running, "internal_start_did_not_assert_running");
    rig.controls[0] = 0.f;
    rig.render();
    INFRA(rig.sequencer.running);
    const uint64_t stop = rig.frame;
    rig.controls[1] = 1.f; // STOP applies at exactly this frame.
    rig.render();
    ORACLE(!rig.sequencer.running, "internal_stop_waits_for_cycle_end_not_one_block");
    std::printf("OB-C-A10-GROOVE internal start=%llu gate=%llu stop=%llu stopped_before=%llu\n",
                static_cast<unsigned long long>(start),
                static_cast<unsigned long long>(rig.first_note()),
                static_cast<unsigned long long>(stop),
                static_cast<unsigned long long>(rig.frame));
}

void external_clock_run() {
    Rig rig;
    rig.inputs[0].flags |= WS2_CONNECTED; // clock
    rig.inputs[1].flags |= WS2_CONNECTED; // run
    rig.render(); // no clock/run yet
    const uint64_t start = rig.frame;
    std::fill(rig.input_storage[1].begin(), rig.input_storage[1].end(), 1.f);
    rig.render(); // rising RUN, no clock edge
    ORACLE(rig.first_note() == UINT64_MAX, "external_gate_before_first_clock_edge");
    const uint64_t edge = rig.frame;
    std::fill(rig.input_storage[0].begin(), rig.input_storage[0].end(), 1.f);
    rig.render(); // first external clock edge
    ORACLE(rig.first_note() == edge, "external_first_gate_not_at_first_clock_edge");
    ORACLE(rig.sequencer.running, "external_run_did_not_start");
    const uint64_t stop = rig.frame;
    std::fill(rig.input_storage[1].begin(), rig.input_storage[1].end(), 0.f);
    rig.render(); // falling RUN is external STOP
    ORACLE(!rig.sequencer.running, "external_stop_exceeded_one_block");
    std::printf("OB-C-A10-GROOVE external run=%llu first_clock=%llu gate=%llu stop=%llu\n",
                static_cast<unsigned long long>(start),
                static_cast<unsigned long long>(edge),
                static_cast<unsigned long long>(rig.first_note()),
                static_cast<unsigned long long>(stop));
}
} // namespace

int main(int argc, char **argv) {
    // Register the two named internal/external CTest commands separately.
    if (argc != 2) {
        std::fprintf(stderr, "INFRA_A10_GROOVE: expected internal|external argument\n");
        return 2;
    }
    const std::string which = argv[1];
    if (which == "internal") internal_start_stop();
    else if (which == "external") external_clock_run();
    else {
        std::fprintf(stderr, "INFRA_A10_GROOVE: unknown case %s\n", argv[1]);
        return 2;
    }
    return 0;
}
