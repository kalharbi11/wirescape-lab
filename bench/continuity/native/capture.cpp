// SPDX-License-Identifier: GPL-3.0-only
// Source-include the pinned native descriptors; never call the original main.
#define main e5_original_test_entry
#include WS_FIXTURE_SOURCE
#undef main
#include <array>
#include <fstream>
#include <string>

namespace {
constexpr unsigned capture_blocks = 640, edit_block = 200, release_block = 500;
constexpr unsigned rate = 48000, buses = 3;
static_assert(frames == 256, "A69 render block");
static_assert(sizeof(float) == 4, "WSNSCAP1 float32");
void le(std::ostream &out, uint64_t value, unsigned bytes) {
    for (unsigned i = 0; i < bytes; ++i)
        out.put(static_cast<char>((value >> (8 * i)) & 255));
}
struct Recorder {
    std::vector<float> pcm;
    std::ofstream marks;
    unsigned blocks = 0;
    explicit Recorder(const std::string &path) : marks(path + ".marks") {
        CHECK(marks.good());
        pcm.reserve(capture_blocks * frames * buses);
    }
    void mark(const char *id, const char *type, uint64_t gen, unsigned begin, unsigned end) {
        marks << "{\"re\":\"" << id << "\",\"type\":\"" << type
              << "\",\"ok\":true,\"gen\":\"" << gen
              << "\",\"b0\":" << begin << ",\"b1\":" << end << "}\n";
        CHECK(marks.good());
    }
    void render(Engine &engine) {
        std::array<std::array<float, frames>, buses> block{};
        float *out[]{block[0].data(), block[1].data(), block[2].data()};
        {
            allocation_watch::ThreadScope watch;
            CHECK(engine.render(out, buses, frames) == WS2_OK);
            CHECK(watch.allocations() == 0);
        }
        // Storage and I/O are outside the watched render.
        for (unsigned i = 0; i < frames; ++i)
            for (unsigned ch = 0; ch < buses; ++ch) pcm.push_back(block[ch][i]);
        ++blocks;
    }
    void write(const std::string &path) {
        CHECK(blocks == capture_blocks);
        std::ofstream out(path, std::ios::binary);
        CHECK(out.good());
        out.write("WSNSCAP1", 8);
        for (uint32_t v : {1u, 40u, rate, buses, frames, 0u}) le(out, v, 4);
        le(out, blocks, 8);
        for (float v : pcm) {
            uint32_t bits;
            std::memcpy(&bits, &v, sizeof(bits));
            le(out, bits, 4);
        }
        out.flush();
        marks.flush();
        CHECK(out.good() && marks.good());
    }
};
}

int main(int argc, char **argv) {
    CHECK(argc == 4);
    const std::string kind = argv[1], mode = argv[2], path = argv[3];
    CHECK(kind == "adopt" || kind == "ring" || kind == "decline" || kind == "cap");
    CHECK(mode == "edited" || mode == "control");
    const bool adopt_case = kind == "adopt", edited = mode == "edited";
    const ws2_descriptor adopt_descriptor{
        sizeof(ws2_descriptor), WS_ABI2_VERSION, "test.adopt_phase", "Adopt phase", 1, 1, 2, 0,
        AdoptPhase::inputs.data(), AdoptPhase::outputs.data(), nullptr,
        AdoptPhase::create, AdoptPhase::destroy, AdoptPhase::query, AdoptPhase::memory,
        AdoptPhase::prepare, AdoptPhase::reset, AdoptPhase::process, AdoptPhase::save, AdoptPhase::load,
        AdoptPhase::latency, 0, nullptr, AdoptPhase::adopt, 7};
    auto tail_descriptor = *ws::Module<ReplacementTail>::descriptor();
    if (kind == "decline") {
        tail_descriptor.replace_fade_ms = 7;
        tail_descriptor.adopt = [](void *, const void *) -> int { return WS2_UNSUPPORTED; };
    } else if (kind == "cap") tail_descriptor.replace_fade_ms = 1000;
    const uint32_t subject = adopt_case ? 1 : 2;
    auto make = [&](uint8_t value) {
        auto e = std::make_unique<Engine>(config());
        if (adopt_case) {
            CHECK(e->add_node(1, &adopt_descriptor, {value}));
            CHECK(e->output(1, 0, 0));
            CHECK(e->output(1, 1, 1));
        } else {
            CHECK(e->add_node(1, ws::Module<Voice>::descriptor()));
            CHECK(e->add_node(2, &tail_descriptor, {value}));
            CHECK(e->connect(1, 0, 2, 0));
            CHECK(e->output(2, 0, 0));
            CHECK(e->output(1, 0, 1));
        }
        CHECK(e->add_node(3, ws::Module<Voice>::descriptor()));
        CHECK(e->output(3, 0, 2));
        CHECK(e->register_producer() == 0);
        CHECK(e->prepare());
        return e;
    };
    auto live = make(1);
    auto successor = edited ? make(2) : nullptr;
    auto send = [&](uint32_t id, uint32_t port, ws2_event ev) {
        CHECK(live->enqueue(0, id, port, ev, 0, Timing::Immediate) == WS2_OK);
    };
    send(1, 0, note());
    if (!adopt_case) send(2, 1, note());
    send(3, 0, note());
    const auto generation = live->meter().generation;
    Recorder rec(path);
    rec.mark("note", "noteOn", generation, 0, 0);
    while (rec.blocks < edit_block) rec.render(*live);
    if (edited) {
        const unsigned begin = rec.blocks;
        std::atomic<bool> done{false};
        bool accepted = false;
        std::thread control([&] {
            accepted = live->replan(*successor, uint64_t(frames) * 3 * 1000000000 / rate);
            done.store(true, std::memory_order_release);
        });
        // Pace only while control is outstanding, outside render.
        const auto deadline = Clock::now() + std::chrono::seconds(2);
        do {
            rec.render(*live);
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        } while (!done.load(std::memory_order_acquire) &&
                 rec.blocks < release_block && Clock::now() < deadline);
        control.join();
        if (!accepted) std::fprintf(stderr, "A69 replan: %s\n", live->error().c_str());
        CHECK(accepted);
        CHECK(rec.blocks < release_block);
        rec.mark("edit", "replan", live->meter().generation, begin, rec.blocks);
        successor.reset();
    }
    while (rec.blocks < release_block) rec.render(*live);
    send(subject, adopt_case ? 0 : 1, note(WS2_NOTE_OFF, 0));
    rec.mark("release", "noteOff", live->meter().generation, rec.blocks, rec.blocks);
    while (rec.blocks < capture_blocks) rec.render(*live);
    CHECK(live->meter().generation == generation);
    CHECK(live->meter().faults == 0);
    rec.write(path);
}
