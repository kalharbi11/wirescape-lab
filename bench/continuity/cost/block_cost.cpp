// SPDX-License-Identifier: GPL-3.0-only
// Device-free A69a: actual AppEngine and bundled runtime documents.
#include "runtime_patch.h"
#include "runtime_module_config.h"
#include <valgrind/callgrind.h>
#include <valgrind/valgrind.h>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <thread>

using Json = nlohmann::json;
using App = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;
namespace {
constexpr unsigned rate = 48000, block = 256, warmup = 240, steady_blocks = 64;
constexpr unsigned fade_frames = rate * WS2_REPLACE_FADE_DEFAULT_MS / 1000;
constexpr unsigned fade_blocks = (fade_frames + block - 1) / block;
constexpr unsigned max_profile_blocks = 128;
constexpr uint64_t deadline_ns = uint64_t(block) * 3 * 1000000000 / rate;

void need(bool ok, const char *why) {
    if (!ok) throw std::runtime_error(why);
}
Json read_patch(const char *path) {
    need(std::filesystem::file_size(path) <= wirescape::document::RuntimePatchLimit, "patch size");
    std::ifstream in(path, std::ios::binary);
    need(bool(in), "patch open");
    auto patch = Json::parse(std::string(std::istreambuf_iterator<char>(in), {}));
    need(patch.at("format") == "wirescape.native.patch" && patch.at("version") == 2,
         "patch identity");
    return patch;
}
void validate_devices_off(const Json &patch) {
    for (const auto &m : patch.at("modules")) {
        const auto id = m.at("module").get<std::string>();
        need(id != "osc.in" && id != "osc.out" && id != "midi.in",
             "external ingress/egress not allowed in this seam");
    }
}
App load(const Json &patch, AppEngine *catalog, const wirescape::engine2::Config &cfg) {
    std::string error;
    App graph(wirescape::document::load_runtime_patch(patch.dump(), catalog, cfg, error),
              app_engine_destroy);
    if (!graph) throw std::runtime_error("runtime patch rejected: " + error);
    return graph;
}
void seed_held_notes(const Json &patch, AppEngine *engine) {
    // The paired instruction ranking uses a C4 note-on for each keyboard.
    // Keep the note held through the measurement window (well before note-off).
    for (const auto &m : patch.at("modules")) {
        if (m.at("module") != "host.keyboard") continue;
        ws2_event note{};
        note.struct_size = sizeof(note);
        note.type = WS2_NOTE_ON;
        note.note_id = 60;
        note.source_id = 1;
        note.value = 60.f;
        need(app_engine_enqueue(engine, m.at("id").get<uint32_t>(), note, 0,
                                app_engine_generation(engine)) == WS2_OK, "note enqueue");
    }
}
struct Renderer {
    std::array<float, block> left{}, right{};
    unsigned completed = 0;
    double peak = 0;
    int render(AppEngine *engine, bool profile) {
        float *rows[]{left.data(), right.data()};
        char label[32];
        std::snprintf(label, sizeof(label), "block-%u", completed);
        if (profile) {
            CALLGRIND_ZERO_STATS;
            CALLGRIND_TOGGLE_COLLECT;
        }
        const int result = app_engine_render_channels(engine, rows, 2, block);
        if (profile) {
            CALLGRIND_TOGGLE_COLLECT;
            CALLGRIND_DUMP_STATS_AT(label);
        }
        if (result != WS2_OK) return result;
        for (const auto *channel : rows)
            for (unsigned i = 0; i < block; ++i) {
                if (!std::isfinite(channel[i])) return WS2_STATE;
                peak = std::max(peak, std::abs(double(channel[i])));
            }
        ++completed;
        return WS2_OK;
    }
};
}

int main(int argc, char **argv) {
    try {
        need(argc == 3, "usage: e5_block_cost single|dual <bundled patch>");
        need(RUNNING_ON_VALGRIND, "Callgrind required");
        const std::string kind = argv[1];
        const bool dual = kind == "dual";
        need(dual || kind == "single", "invalid cost mode");
        const auto filename = std::filesystem::path(argv[2]).filename().string();
        need(filename == (dual ? "basics-08-clocked-groove.json" : "scene-03-black-ice-choir.json"),
             "A69a subject mismatch");
        const Json patch = read_patch(argv[2]);
        validate_devices_off(patch);
        wirescape::engine2::Config cfg{};
        cfg.sample_rate = rate;
        cfg.max_block = block;
        cfg.max_nodes = 64;
        cfg.event_budget = 2048;
        App catalog(app_engine_create(&cfg), app_engine_destroy);
        need(bool(catalog), "catalogue create");
        App live = load(patch, catalog.get(), cfg);
        App candidate(nullptr, app_engine_destroy);
        Json edit = nullptr;
        if (dual) {
            Json changed = patch;
            unsigned count = 0;
            for (size_t i = 0; i < changed.at("modules").size(); ++i) {
                auto &m = changed["modules"][i];
                if (m.at("id") != 2) continue;
                need(m.at("module") == "sequencing.groove", "wrong Groove subject");
                auto &step = m.at("config").at("tracks").at(0).at("steps").at(0);
                need(step.at("kind") == "note" && step.at("key") == 60 &&
                     !step.contains("keys"), "unexpected canonical step shape");
                const auto original = wirescape::document::runtime_module_config(
                    "sequencing.groove", m.at("config"), 2);
                step["key"] = 61;
                const auto updated = wirescape::document::runtime_module_config(
                    "sequencing.groove", m.at("config"), 2);
                need(!original.empty() && original != updated, "config replacement not real");
                const auto *d = app_engine_native_descriptor(catalog.get(), "sequencing.groove");
                need(d != nullptr, "missing Groove descriptor");
                need(d->struct_size < offsetof(ws2_descriptor, adopt) + sizeof(d->adopt) || !d->adopt,
                     "expected real stock no-adopt path");
                need(d->struct_size < offsetof(ws2_descriptor, replace_fade_ms) + sizeof(d->replace_fade_ms) ||
                         d->replace_fade_ms == 0 || d->replace_fade_ms == WS2_REPLACE_FADE_DEFAULT_MS,
                     "unexpected replacement fade");
                edit = {{"module_id", 2}, {"json_pointer", "/modules/" + std::to_string(i) +
                         "/config/tracks/0/steps/0/key"}, {"before", 60}, {"after", 61},
                         {"canonical_bytes", updated.size()}};
                ++count;
            }
            need(count == 1 && Json::diff(patch, changed).size() == 1,
                 "one legal config edit only");
            candidate = load(changed, catalog.get(), cfg);
        }
        seed_held_notes(patch, live.get());
        Renderer renderer;
        while (renderer.completed < warmup)
            need(renderer.render(live.get(), false) == WS2_OK, "warm-up render");
        int replan_status = WS2_OK;
        unsigned ack_block = 0, settle_request = 0;
        if (!dual) {
            for (unsigned i = 0; i < steady_blocks; ++i)
                need(renderer.render(live.get(), true) == WS2_OK, "steady render");
        } else {
            // Two real measured renders before the request. A separate control
            // owner publishes the prepared candidate while this owner renders.
            for (unsigned i = 0; i < 2; ++i)
                need(renderer.render(live.get(), true) == WS2_OK, "before replan");
            std::atomic<unsigned> completed{renderer.completed};
            std::atomic<bool> stop{false}, finished{false};
            std::thread control([&] {
                replan_status = app_engine_replan(live.get(), candidate.get(), deadline_ns);
                if (replan_status == WS2_OK) {
                    ack_block = completed.load(std::memory_order_acquire);
                    // Acknowledgement can precede completion of the adoption
                    // render. Wait through the entire declared fade before
                    // requesting the real steady-layout housekeeping path.
                    while (!stop.load(std::memory_order_acquire) &&
                           completed.load(std::memory_order_acquire) < ack_block + fade_blocks)
                        std::this_thread::sleep_for(std::chrono::microseconds(100));
                    if (!stop.load(std::memory_order_acquire)) {
                        settle_request = completed.load(std::memory_order_acquire);
                        app_engine_native(live.get()).refresh_latency();
                    }
                }
                finished.store(true, std::memory_order_release);
            });
            int render_status = WS2_OK;
            while (!finished.load(std::memory_order_acquire) &&
                   renderer.completed < warmup + max_profile_blocks) {
                render_status = renderer.render(live.get(), true);
                if (render_status != WS2_OK) break;
                completed.store(renderer.completed, std::memory_order_release);
                // Outside counted work: allow the control owner to run.
                std::this_thread::sleep_for(std::chrono::microseconds(100));
            }
            const bool finished_in_window = finished.load(std::memory_order_acquire);
            stop.store(true, std::memory_order_release);
            control.join();
            need(render_status == WS2_OK && finished_in_window, "transition render window exhausted");
            need(replan_status == WS2_OK, "real E5 replan refused (including its unchanged deadline)");
            need(settle_request != 0, "missing housekeeping request");
            candidate.reset();
            for (unsigned i = 0; i < 2; ++i)
                need(renderer.render(live.get(), true) == WS2_OK, "after housekeeping");
        }
        const auto meter = app_engine_get_meter(live.get());
        need(meter.frame == uint64_t(renderer.completed) * block, "render frame count");
        need(!meter.faults && !meter.late && !meter.dropped && !meter.ring_full &&
                 !meter.stale && !meter.arena_full, "faulted event accounting");
        need(renderer.peak > 0, "silent bundled patch");
        Json report = {{"kind", kind}, {"patch", filename}, {"rate", rate}, {"block", block},
                       {"warmup_blocks", warmup}, {"completed_blocks", renderer.completed},
                       {"seed", patch.at("settings").at("seed")}, {"edit", edit},
                       {"fade_frames", dual ? fade_frames : 0}, {"deadline_ns", deadline_ns},
                       {"ack_completed_blocks", ack_block}, {"housekeeping_request", settle_request},
                       {"frame", meter.frame}, {"faults", meter.faults}, {"late", meter.late},
                       {"dropped", meter.dropped}, {"ring_full", meter.ring_full},
                       {"stale", meter.stale}, {"arena_full", meter.arena_full},
                       {"peak_fs", renderer.peak}};
        std::cout << report.dump() << '\n';
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "A69a cost: " << error.what() << '\n';
        return 1;
    }
}
