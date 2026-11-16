// SPDX-License-Identifier: GPL-3.0-only
// Standalone generated-header compilation and validation; not wired to runtime.
#include "native/sidecar/generated/protocol_v0.hpp"
#include <cassert>
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

    // JSON Schema 2020-12 lengths count Unicode scalar values, not UTF-8 bytes.
    // The actual sidecar separately requires ASCII request IDs <= 64 bytes;
    // this independent schema test must not add a sidecar waiver or change it.
    for (const std::string scalar : {std::string(u8"é"), std::string(u8"🙂")}) {
        for (std::size_t count : {std::size_t(33), std::size_t(64)}) {
            std::string unicode_id;
            for (std::size_t i = 0; i < count; ++i) unicode_id += scalar;
            assert(unicode_id.size() > 64);
            assert(validate(Json{{"v", 0}, {"id", unicode_id}, {"type", "panic"}}));
        }
        std::string overlong;
        for (int i = 0; i < 65; ++i) overlong += scalar;
        assert(!validate(Json{{"v", 0}, {"id", overlong}, {"type", "panic"}}));
    }
    assert(validate(Json{{"v", 0}, {"id", std::string(64, 'a')}, {"type", "panic"}}));
    assert(!validate(Json{{"v", 0}, {"id", std::string(65, 'a')}, {"type", "panic"}}));

    std::cout << "unwired generated C++ protocol v0 validator passed\n";
}
