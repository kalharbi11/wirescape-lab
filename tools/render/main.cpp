// SPDX-License-Identifier: GPL-3.0-only
// Device-free ABI2 evidence renderer; Python evidence.py owns assertions and provenance reports.
#include "runtime_patch.h"
#include <algorithm>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
#include <vector>

using Json = nlohmann::json;
using App = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;
static void need(bool ok, const std::string &message) {
    if (!ok) throw std::runtime_error(message);
}
static std::string read_bounded(const std::string &path, uintmax_t limit) {
    need(std::filesystem::file_size(path) <= limit, "input exceeds size limit: " + path);
    std::ifstream in(path, std::ios::binary);
    need(bool(in), "cannot open " + path);
    return {std::istreambuf_iterator<char>(in), {}};
}
static uint32_t u32(const Json &x, const char *what) {
    need(x.is_number_integer(), std::string("invalid ") + what);
    const int64_t value = x.get<int64_t>();
    need(value >= 0 && value <= UINT32_MAX, std::string("out-of-range ") + what);
    return uint32_t(value);
}
static uint32_t ump_word(const Json &x) {
    need(x.is_number_integer(), "invalid UMP word");
    if (x.is_number_unsigned()) {
        const auto value = x.get<uint64_t>();
        need(value <= UINT32_MAX, "out-of-range UMP word");
        return uint32_t(value);
    }
    const auto value = x.get<int64_t>();
    need(value >= 0 && value <= UINT32_MAX, "out-of-range UMP word");
    return uint32_t(value);
}
static void parse_ump(const Json &entry, ws2_event &event) {
    static constexpr uint8_t widths[16] = {1,1,1,2,2,4,1,1,2,2,2,3,3,4,4,4};
    need(entry.contains("words") && entry["words"].is_array(), "invalid UMP words");
    const auto &words = entry["words"];
    need(!words.empty() && words.size() <= 4, "invalid UMP words size");
    for (size_t i = 0; i < words.size(); ++i) event.ump[i] = ump_word(words[i]);
    need(words.size() == widths[event.ump[0] >> 28], "UMP word count does not match message type");
    event.type = WS2_MIDI;
    event.channel = event.note_id = -1;
    event.ump_words = uint32_t(words.size());
}
static void put16(std::ostream &out, uint16_t x) {
    out.put(char(x & 255));
    out.put(char((x >> 8) & 255));
}
static void put32(std::ostream &out, uint32_t x) {
    put16(out, uint16_t(x));
    put16(out, uint16_t(x >> 16));
}
static void wav(const std::string &path, const std::vector<float> &samples, uint32_t rate) {
    std::filesystem::path dest(path);
    if (!dest.parent_path().empty()) std::filesystem::create_directories(dest.parent_path());
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    need(bool(out), "cannot create WAV: " + path);
    const uint32_t size = uint32_t(samples.size() * sizeof(float));
    out.write("RIFF", 4);
    put32(out, 36 + size);
    out.write("WAVEfmt ", 8);
    put32(out, 16);
    put16(out, 3);
    put16(out, 2); // IEEE float, stereo
    put32(out, rate);
    put32(out, rate * 8);
    put16(out, 8);
    put16(out, 32);
    out.write("data", 4);
    put32(out, size);
    for (float sample : samples) {
        uint32_t bits;
        std::memcpy(&bits, &sample, sizeof(bits));
        put32(out, bits); // explicit little-endian IEEE-754; never clamp
    }
    out.flush();
    need(bool(out), "WAV write failed: " + path);
}
int main(int argc, char **argv) {
    try {
        std::map<std::string, std::string> args;
        bool timing = false;
        for (int i = 1; i < argc;) {
            const std::string key(argv[i++]);
            if (key == "--timing") {
                need(!timing, "duplicate option: --timing");
                timing = true;
                continue;
            }
            need(i < argc, "missing option value");
            const bool io_option = key == "--patch" || key == "--script" || key == "--out";
            const bool run_option = key == "--rate" || key == "--block" || key == "--seconds" || key == "--seed";
            need(io_option || run_option || key == "--late-fixture", "unknown option: " + key);
            need(args.emplace(key, argv[i++]).second, "duplicate option: " + key);
        }
        for (const char *key : {"--patch", "--script", "--out", "--rate", "--block", "--seconds", "--seed"})
            need(args.count(key) != 0, std::string("missing ") + key);
        const auto rate = std::stoul(args.at("--rate")), block = std::stoul(args.at("--block"));
        const double seconds = std::stod(args.at("--seconds"));
        const auto seed = std::stoull(args.at("--seed"));
        const bool valid_rate = rate >= 8000 && rate <= 96000;
        const bool valid_block = block >= 1 && block <= 1024;
        const bool valid_duration = std::isfinite(seconds) && seconds > 0 && seconds <= 10;
        need(valid_rate && valid_block && valid_duration, "invalid rate/block/duration");
        if (args.count("--late-fixture")) need(args.at("--late-fixture") == "1", "invalid late fixture flag");
        const uint64_t frames = uint64_t(std::llround(static_cast<double>(rate) * seconds));
        need(frames > 0 && frames * 8ULL <= 20ULL * 1024 * 1024, "WAV exceeds 20 MiB");
        Json patch = Json::parse(read_bounded(args.at("--patch"), wirescape::document::RuntimePatchLimit));
        need(patch.is_object() && patch.value("version", 0) == 2, "requires ABI2 patch v2");
        patch["settings"]["seed"] = seed;
        const Json script = Json::parse(read_bounded(args.at("--script"), 65536));
        need(script.is_array() && script.size() <= 128, "script must have <=128 events");
        wirescape::engine2::Config cfg{};
        cfg.sample_rate = double(rate);
        cfg.max_block = uint32_t(block);
        cfg.max_nodes = 64;
        cfg.event_budget = 2048;
        App catalog(app_engine_create(&cfg), app_engine_destroy);
        need(bool(catalog), "catalogue creation failed");
        std::string error;
        App engine(wirescape::document::load_runtime_patch(patch.dump(), catalog.get(), cfg, error),
                   app_engine_destroy);
        need(bool(engine), "patch load failed: " + error);
        uint64_t previous = 0;
        for (const auto &entry : script) {
            need(entry.is_object(), "script entry must be an object");
            const uint64_t frame = u32(entry.at("frame"), "event frame");
            need(frame >= previous && frame < frames, "events must be sorted and within duration");
            previous = frame;
            const uint32_t node = u32(entry.at("node"), "event node");
            const std::string type = entry.at("type").get<std::string>();
            ws2_event event{};
            event.struct_size = sizeof(event);
            event.source_id = 1;
            const auto generation = app_engine_generation(engine.get());
            std::string parameter_id;
            bool gate = false;
            float gate_value = 0.f;
            if (type == "noteOn" || type == "noteOff") {
                const auto key = u32(entry.at("key"), "MIDI key");
                need(key <= 127, "MIDI key >127");
                event.type = type == "noteOn" ? WS2_NOTE_ON : WS2_NOTE_OFF;
                event.note_id = key;
                event.value = float(key);
            } else if (type == "midi") {
                parse_ump(entry, event);
                bool found = false;
                for (const auto &m : patch.at("modules"))
                    if (u32(m.at("id"), "module id") == node) found = true;
                need(found, "MIDI target node does not exist");
            } else if (type == "gate") {
                gate = true;
                gate_value = entry.at("value").get<float>();
                need(std::isfinite(gate_value), "non-finite gate");
            } else if (type == "setParam") {
                event.type = WS2_PARAM;
                event.value = entry.at("value").get<float>();
                need(std::isfinite(event.value), "non-finite parameter");
                std::string module;
                for (const auto &m : patch.at("modules")) {
                    if (u32(m.at("id"), "module id") == node) module = m.at("module").get<std::string>();
                }
                need(!module.empty(), "parameter targets missing node");
                const std::string parameter = entry.at("parameter").get<std::string>();
                parameter_id = parameter;
                bool found = false;
                for (uint32_t i = 0; i < app_engine_module_count(engine.get()); ++i) {
                    const auto *descriptor = app_engine_module(engine.get(), i);
                    if (module != descriptor->id) continue;
                    for (uint32_t p = 0; p < descriptor->param_count; ++p) {
                        if (parameter == app_engine_parameter_id(engine.get(), module.c_str(), p)) {
                            const auto &d = descriptor->params[p];
                            need(event.value >= d.minimum && event.value <= d.maximum, "parameter outside range");
                            found = true;
                        }
                    }
                }
                need(found, "unknown parameter: " + parameter);
            } else {
                throw std::runtime_error("unknown event type: " + type);
            }
            const int event_status = event.type == WS2_MIDI
                ? app_engine_native(engine.get()).enqueue(0, node, WS2_DIRECT_PORT, event, frame,
                                                          wirescape::engine2::Timing::Frames, generation)
                : gate
                ? app_engine_enqueue_gate(engine.get(), node, gate_value, frame, generation, 1)
                : app_engine_enqueue(engine.get(), node, event, frame, generation,
                                     parameter_id.empty() ? nullptr : parameter_id.c_str());
            need(event_status == WS2_OK,
                 "frame-addressed event enqueue failed at frame " + std::to_string(frame));
        }
        std::vector<float> interleaved(size_t(frames) * 2);
        std::vector<float> left(block), right(block);
        // Only the opt-in path allocates timing storage or reads the clock.
        using Clock = std::chrono::steady_clock;
        std::vector<double> durations(timing ? size_t((frames + block - 1) / block) : 0);
        const double period_us = double(block) * 1e6 / double(rate);
        size_t overruns = 0;
        for (uint64_t start = 0; start < frames; start += block) {
            const auto n = uint32_t(std::min<uint64_t>(block, frames - start));
            float *rows[]{left.data(), right.data()};
            if (args.count("--late-fixture") && start == block) {
                // Test-only: enqueue an already-rendered frame; this must be detected.
                ws2_event late{};
                late.struct_size = sizeof(late);
                late.source_id = 1;
                late.type = WS2_NOTE_ON;
                late.note_id = 60;
                late.value = 60.f;
                need(app_engine_enqueue(engine.get(), 1, late, 0, app_engine_generation(engine.get())) == WS2_OK,
                     "late fixture enqueue failed");
            }
            if (timing) {
                const auto before = Clock::now();
                const auto status = app_engine_render_channels(engine.get(), rows, 2, n);
                const auto after = Clock::now();
                const double us = std::chrono::duration<double, std::micro>(after - before).count();
                durations[size_t(start / block)] = us;
                // Compare every call against the configured block deadline.
                if (us > period_us) ++overruns;
                need(status == WS2_OK, "render failed at frame " + std::to_string(start));
            } else {
                need(app_engine_render_channels(engine.get(), rows, 2, n) == WS2_OK,
                     "render failed at frame " + std::to_string(start));
            }
            for (uint32_t i = 0; i < n; ++i) {
                interleaved[size_t(start + i) * 2] = left[i];
                interleaved[size_t(start + i) * 2 + 1] = right[i];
            }
        }
        const auto meter = app_engine_native(engine.get()).meter();
        Json counters = Json::object();
        counters["faults"] = meter.faults;
        counters["late_events"] = meter.late;
        counters["dropped_events"] = meter.dropped;
        counters["ring_full_events"] = meter.ring_full;
        counters["stale_events"] = meter.stale;
        counters["arena_full_events"] = meter.arena_full;
        if (timing) {
            std::sort(durations.begin(), durations.end());
            const auto percentile = [&](double q) {
                return durations[size_t(std::ceil(q * durations.size())) - 1];
            };
            counters["timing"] = {{"p50_us", percentile(0.5)}, {"p99_us", percentile(0.99)},
                                  {"worst_us", durations.back()}, {"period_us", period_us},
                                  {"overruns", overruns}, {"blocks", durations.size()}};
        }
        std::cout << "render_metrics " << counters.dump() << '\n';
        std::cout.flush();
        const bool events_clean = meter.faults == 0 && meter.late == 0 && meter.dropped == 0;
        const bool queues_clean = meter.ring_full == 0 && meter.stale == 0 && meter.arena_full == 0;
        need(events_clean && queues_clean, "render event accounting failed: late, dropped, stale or faulted event");
        wav(args.at("--out"), interleaved, uint32_t(rate));
        std::cout << "rendered " << frames << " ABI2 frames; devices off\n";
    } catch (const std::exception &e) {
        std::cerr << "wirescape_render: " << e.what() << '\n';
        return 1;
    }
}
