// SPDX-License-Identifier: GPL-3.0-only
// M1 S0: byte-exact tripwires for real Session JSON production serialization.
// Session's random token alone is fixed by the TEST-ONLY generated translation
// unit in native/CMakeLists.txt. No JSON value is normalized or deleted here.
#include "session.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <iterator>

using namespace wirescape::sidecar;
namespace fs = std::filesystem;

static std::string bytes(const fs::path &path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("missing pinned S0 snapshot: " + path.string());
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

static void exact(const fs::path &dir, const char *file, const std::string &actual) {
    const auto expected = bytes(dir / file);
    if (actual == expected) return;
    size_t offset = 0;
    while (offset < expected.size() && offset < actual.size() &&
           expected[offset] == actual[offset]) ++offset;
    // Do not regenerate snapshots automatically: a change must be reviewed.
    throw std::runtime_error(std::string(file) + " byte mismatch at offset " +
                             std::to_string(offset) + " expected bytes " +
                             std::to_string(expected.size()) + ", actual bytes " +
                             std::to_string(actual.size()));
}
static void require(bool condition, const char *reason) {
    if (!condition) throw std::runtime_error(reason);
}
int main(int argc, char **argv) {
    try {
        require(argc == 2, "usage: sidecar_s0_snapshot_tests testdata_dir");
        const fs::path dir(argv[1]);
        Options options;
        options.null_audio = true; // only the existing device-free null-sink
        options.audio = false;
        options.midi = false;
        options.lan = false;
        options.rate = 48000;
        options.block = 256;
        options.settings = (dir / "s0-settings-not-present.json").string();
        require(!fs::exists(options.settings), "test settings path must remain absent");
        Session session(options);
        const auto hello = session.hello();
        require(hello.at("session") == "s0-fixture-session", "test-only token control ineffective");
        // Complete emitted UI catalogue (all modules, ports, parameter values).
        // Json::dump() is exactly the production Transport::write() serializer.
        exact(dir, "s0_catalogue.ndjson", hello.at("catalogue").dump() + "\n");
        // Complete status wire message, including session, generation and all
        // nested audio/MIDI/OSC fields. Captured before starting the sink.
        exact(dir, "s0_status.ndjson", session.status().dump() + "\n");

        session.start(); // null sink only; no PortAudio or physical MIDI.
        const Request seed{
            Json{{"v", 0}, {"id", "s0-seed"}, {"type", "addModule"},
                 {"moduleId", 9}, {"moduleType", "essentials.vco"}}, {}, {}};
        const auto seeded = session.reply(seed);
        require(seeded.at("ok") == true && seeded.at("gen") == "1",
                "deterministic native VCO setup was not committed");

        // Strict-parse committed input bytes as the real reader does. Do not
        // reconstruct or normalize the request. Freeze the exact full reply.
        auto request_bytes = bytes(dir / "s0_setparam_request.ndjson");
        require(!request_bytes.empty() && request_bytes.back() == '\n',
                "setParam request fixture must have a terminal newline");
        request_bytes.pop_back();
        const Request set_param{strict_json(request_bytes), {}, {}};
        require(set_param.value.at("type") == "setParam", "wrong command snapshot");
        const auto reply = session.reply(set_param);
        require(reply.at("ok") == true && reply.at("gen") == "1",
                "setParam round trip failed in production Session");
        exact(dir, "s0_setparam_reply.ndjson", reply.dump() + "\n");
        session.shutdown();
        std::cout << "M1 S0: catalogue (34 modules), full status and setParam "
                  << "request/reply byte snapshots passed (null sink)\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "M1 S0 snapshot mismatch: " << e.what() << '\n';
        return 1;
    }
}
