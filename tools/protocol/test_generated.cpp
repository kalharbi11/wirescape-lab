// SPDX-License-Identifier: GPL-3.0-only
// Standalone generated-header compilation and validation; not wired to runtime.
#include "native/sidecar/generated/protocol_v0.hpp"
#include <cassert>
#include <fstream>
#include <iostream>

int main() {
    using Json = nlohmann::json;
    using wirescape::protocol_v0::validate;

    Json patch = {
        {"format", "wirescape.native.patch"}, {"version", 2},
        {"modules", Json::array({{{"id", 7}, {"module", "essentials.output"},
                                   {"future_module", {{"opaque", Json::array({1, 2, 3})}}}}})},
        {"connections", Json::array()},
        {"future_document", {{"revision", 10}, {"blob", "retained"}}}
    };
    const Json before = patch;
    Json good = {{"v", 0}, {"id", "r2"}, {"type", "loadGraph"}, {"patch", patch}};
    assert(validate(good));
    assert(good["patch"] == before);
    good["patch"]["modules"][0]["id"] = 0;
    assert(!validate(good));

    assert(validate(Json{{"v", 0}, {"id", "test"}, {"type", "panic"}}));
    assert(!validate(Json{{"v", 0}, {"id", "test"}, {"type", "not-a-command"}}));
    assert(validate(Json{{"v", 0}, {"re", "r2"}, {"ok", true}, {"gen", "1"},
                         {"session", "s1"}}));
    assert(!validate(Json{{"v", 0}, {"re", "r2"}, {"ok", false}, {"gen", "1"},
                          {"session", "s1"}}));
    // JSON const/enum semantics: Boolean and Number are disjoint kinds.
    assert(!validate(Json{{"v", false}, {"id", "x"}, {"type", "panic"}}));
    assert(!validate(Json{{"v", 0}, {"re", "x"}, {"ok", 1}, {"gen", "0"}}));
    assert(validate(Json{{"v", 0}, {"re", "x"}, {"ok", true}, {"gen", "0"}}));
    assert(!validate(Json{{"v", 0}, {"id", "x"}, {"type", "noteOn"}}));

    // Single source of truth for Python/TS/C++ and real sidecar Q8 verdicts.
    std::ifstream source("tools/protocol/request_id_cases.json");
    assert(source.good());
    Json cases = Json::parse(source);
    assert(cases.is_array() && cases.size() >= 10);
    for (const auto &item : cases) {
        const Json command = {{"v", 0}, {"id", item.at("id")}, {"type", "panic"}};
        const bool expected = item.at("valid").get<bool>();
        if (validate(command) != expected) {
            std::cerr << "Q8 C++ request ID mismatch: " << item.at("name") << "\\n";
            return 1;
        }
    }
    // Generic non-request-ID strings retain Unicode-codepoint semantics.
    for (const std::string& scalar : {std::string(u8"é"), std::string(u8"🙂")}) {
        std::string device;
        for (int i = 0; i < 128; ++i) device += scalar;
        assert(device.size() > 256);
        assert(validate(Json{{"v", 0}, {"id", "ascii"},
                             {"type", "selectAudioDevice"}, {"deviceId", device}}));
        for (int i = 128; i < 257; ++i) device += scalar;
        assert(!validate(Json{{"v", 0}, {"id", "ascii"},
                              {"type", "selectAudioDevice"}, {"deviceId", device}}));
    }

    std::cout << "unwired generated C++ protocol v0 validator passed\n";
}
