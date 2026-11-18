// SPDX-License-Identifier: GPL-3.0-only
// OB-c A10: exact-frame real native patch renders for click oracle comparison.
// This fixture writes raw stereo PCM. It NEVER classifies clicks itself; the
// unchanged bench/offline/metrics.py:38-89 click_events is the only detector.
// No sidecar source, device, PortAudio callback or physical MIDI/LAN touched.
#include "../control/app_engine.h"
#include "../document/runtime_patch.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
using Json = nlohmann::json;
using Owner = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;
constexpr uint32_t kBlock = 128;
constexpr uint32_t kRate = 48000;
constexpr uint32_t kSceneMidNote = 8192;       // fixed frame in step 1
constexpr uint32_t kSceneBetweenNotes = 275200; // fixed frame in gate-off step 16
constexpr uint32_t kEchoGestureStart = 96000;

[[noreturn]] void infra(const std::string &message) {
    throw std::runtime_error("INFRA_A10_AUDIO: " + message);
}
void require(bool b, const std::string &message) { if (!b) infra(message); }
std::string read(const std::filesystem::path &path) {
    std::ifstream f(path, std::ios::binary);
    require(bool(f), "missing input: " + path.string());
    return {std::istreambuf_iterator<char>(f), {}};
}
Owner loaded(AppEngine *catalogue, const std::string &document) {
    ws_engine_config c{sizeof(c), kRate, kBlock, 32, 2048};
    std::string error;
    Owner p(wirescape::document::load_runtime_patch(document, catalogue, c, error), app_engine_destroy);
    require(bool(p), "product patch failed to load: " + error);
    return p;
}
void render_to(AppEngine *graph, const std::filesystem::path &file,
               uint32_t total, uint32_t panic_at = UINT32_MAX, int gate_expect = -1) {
    require(total % kBlock == 0 && (panic_at == UINT32_MAX || panic_at % kBlock == 0),
            "render/panic not exact block-aligned frames");
    std::ofstream out(file, std::ios::binary | std::ios::trunc);
    require(bool(out), "cannot open raw output: " + file.string());
    std::array<float, kBlock> left{}, right{};
    float *rows[]{left.data(), right.data()};
    std::array<float, 2 * kBlock> interleaved{};
    for (uint32_t frame = 0; frame < total; frame += kBlock) {
        if (frame == panic_at) {
            // Gate sample at previous processed frame classifies the fixed
            // mid-note vs between-note stimulus; a wrong stimulus is INFRA.
            if (gate_expect != -1) {
                const float gate = app_engine_native(graph).output_sample(2, 1, 0, kBlock - 1);
                require((gate > 0.5f) == (gate_expect == 1),
                        "fixed frame does not lie in requested scene07 gate phase");
            }
            require(app_engine_panic(graph) == WS_OK, "panic command failed");
        }
        require(app_engine_render_channels(graph, rows, 2, kBlock) == WS_OK,
                "real engine render failed");
        for (uint32_t i = 0; i < kBlock; ++i) {
            require(std::isfinite(left[i]) && std::isfinite(right[i]),
                    "nonfinite native audio");
            interleaved[2 * i] = left[i];
            interleaved[2 * i + 1] = right[i];
        }
        out.write(reinterpret_cast<const char *>(interleaved.data()),
                  std::streamsize(interleaved.size() * sizeof(float)));
        require(bool(out), "raw audio write failed");
    }
}
void scene(const std::filesystem::path &source, const std::filesystem::path &dir) {
    const auto patch = read(source);
    Json graph_spec = Json::parse(patch);
    require(graph_spec.at("format") == "wirescape.native.patch", "wrong scene fixture");
    require(graph_spec.at("name").get<std::string>().find("Witching Hour") != std::string::npos,
            "expected scene07 actual bundled patch");
    ws_engine_config c{sizeof(c), kRate, kBlock, 32, 2048};
    Owner catalogue(app_engine_create(&c), app_engine_destroy);
    require(bool(catalogue), "create production module catalogue");
    const uint32_t total = 328000; // exact block multiple, > latest panic + 500ms+guard
    require(total % kBlock == 0, "scene render total must be block multiple");
    const auto render_case = [&](const char *name, uint32_t panic_frame, int gate) {
        auto graph = loaded(catalogue.get(), patch);
        render_to(graph.get(), dir / name, total, panic_frame, gate);
    };
    render_case("scene-reference.f32le", UINT32_MAX, -1);
    render_case("scene-mid-note.f32le", kSceneMidNote, 1);
    render_case("scene-between-notes.f32le", kSceneBetweenNotes, 0);
    std::cout << "OB-C-A10-SCENE exact_panic_frames=" << kSceneMidNote << ","
              << kSceneBetweenNotes << " reference=none rate=" << kRate << "\n";
}
std::string echo_document() {
    // Same production Echo descriptor/knobs as bundled basics-03 but a steady
    // VCO instead of keyboard notes; audible without physical input.
    return R"({"format":"wirescape.native.patch","version":2,
      "settings":{"sample_rate":48000,"max_block_frames":128,"max_channels":16,
                  "feedback_block":32,"seed":42},
      "modules":[
        {"id":1,"module":"essentials.vco","version":2,"parameters":{"frequency":220}},
        {"id":6,"module":"fx.delay","version":1,
         "parameters":{"time":0.375,"division":4,"feedback":0.4,"tone":-0.2,
                       "mode":1,"mix":0.3}},
        {"id":8,"module":"essentials.output","version":2,"parameters":{}},
        {"id":9,"module":"essentials.output","version":2,"parameters":{}}],
      "connections":[
        {"kind":"signal","from":{"module":1,"port":"audio"},"to":{"module":6,"port":"left"}},
        {"kind":"signal","from":{"module":6,"port":"left"},"to":{"module":8,"port":"audio"}},
        {"kind":"signal","from":{"module":6,"port":"right"},"to":{"module":9,"port":"audio"}}],
      "outputs":[{"module":8,"port":"audio","bus_channel":0},
                 {"module":9,"port":"audio","bus_channel":1}]})";
}
uint32_t param_index(const std::string &name) {
    if (name == "time") return 0;
    if (name == "feedback") return 2;
    if (name == "tone") return 3;
    if (name == "mix") return 5;
    infra("unruled gesture: " + name);
}
void echo(const std::filesystem::path &trace_path, const std::filesystem::path &dir) {
    const Json trace = Json::parse(read(trace_path));
    require(trace.at("real_sidecar_or_audio") == false &&
            trace.at("delay_module_id") == 6, "wrong Studio-only cadence trace");
    const auto &gestures = trace.at("gestures");
    require(gestures.is_array() && gestures.size() == 8, "A10 needs eight real Studio gestures");
    ws_engine_config c{sizeof(c), kRate, kBlock, 32, 2048};
    Owner catalogue(app_engine_create(&c), app_engine_destroy);
    require(bool(catalogue), "create production module catalogue");
    const std::string document = echo_document();
    for (const auto &gesture : gestures) {
        const std::string knob = gesture.at("knob");
        const uint32_t duration = gesture.at("duration_nominal_ms").get<uint32_t>();
        require(duration == 100 || duration == 1000, "wrong Echo duration");
        const auto &events = gesture.at("events");
        require(events.is_array() && events.size() >= 3, "missing actual Studio pointermove events");
        const auto tag = knob + "-" + std::to_string(duration);
        const uint32_t total = ((kEchoGestureStart + duration * 48 + 48000 + kBlock - 1) / kBlock) * kBlock;
        {
            auto graph = loaded(catalogue.get(), document);
            render_to(graph.get(), dir / ("echo-reference-" + tag + ".f32le"), total);
        }
        {
            auto graph = loaded(catalogue.get(), document);
            double previous = -1;
            for (const auto &event : events) {
                require(event.at("moduleId") == 6 && event.at("paramId") == knob,
                        "cross-knob / cross-module UI trace");
                const double when = event.at("t_ms").get<double>();
                const float value = event.at("value").get<float>();
                require(std::isfinite(when) && std::isfinite(value) && when >= previous &&
                        when >= 0 && when <= duration + 300,
                        "out-of-order or nonfinite true Studio event timestamps");
                previous = when;
                ws_event set{};
                set.struct_size = sizeof(set);
                set.type = WS_PARAMETER;
                set.node_id = 6;
                set.parameter_id = param_index(knob);
                set.frame = kEchoGestureStart + uint64_t(std::llround(when * double(kRate) / 1000.));
                set.value = value;
                set.generation = app_engine_generation(graph.get());
                require(app_engine_enqueue(graph.get(), &set) == WS_OK,
                        "could not enqueue Studio-timed product setParam");
            }
            render_to(graph.get(), dir / ("echo-sweep-" + tag + ".f32le"), total);
        }
        std::cout << "OB-C-A10-ECHO knob=" << knob << " nominal_ms=" << duration
                  << " actual_events=" << events.size() << "\n";
    }
    require(trace.contains("mode_division_record_only"),
            "missing division/mode record-only evidence");
}
} // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 4) infra("usage: ob_c_a10_audio_runner scene|echo input.json output-directory");
        const std::string mode = argv[1];
        std::filesystem::create_directories(argv[3]);
        if (mode == "scene") scene(argv[2], argv[3]);
        else if (mode == "echo") echo(argv[2], argv[3]);
        else infra("unknown case");
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << "\n";
        return 2; // infrastructure/renderer failure is NEVER a strict expected product failure
    }
}
