// SPDX-License-Identifier: GPL-3.0-only
#include "runtime_module_config.h"
#include <cstdio>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
using namespace wirescape::document;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"CHECK failed at line %d: %s\n",__LINE__,#x);std::abort();}}while(0)
static void instance_config_union() {
    const auto chord = runtime_module_config("essentials.chord", nlohmann::json::object(), 0x12345678);
    CHECK(chord == std::vector<uint8_t>({0x78, 0x56, 0x34, 0x12}));
    bool rejected = false;
    try {
        runtime_module_config("essentials.chord", {{"unknown", 1}}, 17);
    } catch (const std::exception &) {
        rejected = true;
    }
    CHECK(rejected);
    auto pattern =
        nlohmann::json::parse(R"({"version":2,"bpm":120,"tracks":[{"length":8,"steps":[{"kind":"rest"}]}]})");
    for (uint32_t instance : {17u, 18u}) {
        const auto bytes = runtime_module_config("sequencing.groove", pattern, instance);
        groove::Config config;
        CHECK(groove::decode(bytes.data(), static_cast<uint32_t>(bytes.size()), config));
        CHECK(config.instance_seed == instance && config.authored_version == 2 && config.tracks[0].length == 8);
    }
    pattern["version"] = 1;
    pattern["tracks"][0].erase("length");
    const auto legacy = runtime_module_config("sequencing.groove", pattern, 19);
    groove::Config config;
    CHECK(groove::decode(legacy.data(), static_cast<uint32_t>(legacy.size()), config));
    CHECK(config.instance_seed == 0 && config.authored_version == 1 && config.tracks[0].length == 32);
}
static void osc_row_enabled() {
    // #612: absent `enabled` means enabled; false disables only that row.
    wirescape::osc::Configuration config;
    auto bytes = runtime_module_config("osc.in", nlohmann::json::parse(R"({"rows":[{"pattern":"/a"}]})"));
    CHECK(wirescape::osc::configuration(bytes.data(), static_cast<uint32_t>(bytes.size()), config));
    for (const auto &row : config.rows) CHECK(row.enabled == 1);
    bytes = runtime_module_config(
        "osc.in", nlohmann::json::parse(R"({"rows":[{"pattern":"/a","enabled":false},{"enabled":true}]})"));
    CHECK(wirescape::osc::configuration(bytes.data(), static_cast<uint32_t>(bytes.size()), config));
    CHECK(config.rows[0].enabled == 0 && std::string(config.rows[0].pattern) == "/a");
    CHECK(config.rows[1].enabled == 1 && config.rows[2].enabled == 1);
    bool rejected = false;
    try {
        runtime_module_config("osc.in", nlohmann::json::parse(R"({"rows":[{"enabled":0}]})"));
    } catch (const std::exception &) {
        rejected = true;
    }
    CHECK(rejected);
}
static void osc_future_keys() {
    using Json = nlohmann::json;
    const Json known = Json::parse(R"({"port":9011,"rows":[{"pattern":"/voice","kind":"gate","argument":2}]})");
    auto assert_known_values = [&](const Json &source, std::vector<std::string> *ignored = nullptr) {
        const auto bytes = runtime_module_config("osc.in", source, 17, ignored);
        wirescape::osc::Configuration decoded;
        CHECK(wirescape::osc::configuration(bytes.data(), static_cast<uint32_t>(bytes.size()), decoded));
        CHECK(decoded.port == 9011 && decoded.rows[0].argument == 2 && decoded.rows[0].kind == 1);
        CHECK(std::strcmp(decoded.rows[0].pattern, "/voice") == 0);
        if (source.at("rows")[0].contains("enabled")) CHECK(decoded.rows[0].enabled == 0);
    };
    assert_known_values(known);
    const auto all_known = Json::parse(
        R"({"port":9011,"lan":false,"rows":[{"pattern":"/voice","kind":"gate","stale":"hold","argument":2,"input_min":0,"input_max":1,"output_min":0,"output_max":1,"smoothing_ms":5,"timeout_ms":100,"enabled":false}]})");
    std::vector<std::string> known_diagnostics;
    assert_known_values(all_known, &known_diagnostics);
    CHECK(known_diagnostics.empty()); // 'enabled' is a validated known v1 field.
    auto v1 = known;
    v1["version"] = 1;
    assert_known_values(v1, &known_diagnostics);
    CHECK(known_diagnostics.empty()); // version is known and accepted at v1.
    const auto legacy_bytes = runtime_module_config("osc.in", all_known, 17);
    wirescape::osc::Configuration legacy;
    CHECK(wirescape::osc::configuration(legacy_bytes.data(), static_cast<uint32_t>(legacy_bytes.size()), legacy));
    CHECK(legacy.port == 9011 && legacy.lan == 0 && legacy.rows[0].argument == 2 && legacy.rows[0].kind == 1);
    // SC1: valid display metadata never enters the binary configuration or diagnostics.
    auto labelled = all_known;
    labelled["rows"][0]["label"] = "Filter";
    const auto original = labelled.dump();
    std::vector<std::string> label_diagnostics;
    const auto labelled_bytes = runtime_module_config("osc.in", labelled, 17, &label_diagnostics);
    if (!label_diagnostics.empty()) throw std::runtime_error("SC1 label emitted a legacy OSC In diagnostic");
    if (labelled_bytes != legacy_bytes) {
        for (size_t i = 0; i < std::min(labelled_bytes.size(), legacy_bytes.size()); ++i)
            if (labelled_bytes[i] != legacy_bytes[i])
                std::fprintf(stderr, "SC1 config byte %zu: labelled=%u baseline=%u\n", i,
                             unsigned(labelled_bytes[i]), unsigned(legacy_bytes[i]));
    }
    CHECK(labelled_bytes == legacy_bytes && labelled.dump() == original);
    // Invalid display metadata is also ignored by the execution parser.
    for (const auto &bad_label : {Json(42), Json(false), Json(nullptr), Json::object(), Json::array()}) {
        auto invalid_label = all_known;
        invalid_label["rows"][0]["label"] = bad_label;
        std::vector<std::string> diagnostics;
        CHECK(runtime_module_config("osc.in", invalid_label, 17, &diagnostics) == legacy_bytes);
        CHECK(diagnostics.empty());
    }
    auto future = known;
    future["futureOption"] = Json::object({{"nested", 1}});
    future["rows"][0]["futureField"] = Json::array({1, 2});
    std::vector<std::string> ignored;
    assert_known_values(future, &ignored);
    CHECK(ignored == std::vector<std::string>({"osc.in#17.futureOption", "osc.in#17.rows[0].futureField"}));
    CHECK(future["futureOption"].is_object() && future["rows"][0]["futureField"].is_array());

    const char *invalid[] = {
        R"({"version":0})",
        R"({"version":2})",
        R"({"version":"1"})",
        R"({"version":1.5})",
        R"({"version":null})",
        R"({"port":"9011","futureOption":true})",
        R"({"rows":[{"pattern":42,"futureField":true}]})",
        R"({"rows":[{"argument":32,"futureField":true}]})",
        R"({"rows":[{"kind":"other"}]})",
        R"({"rows":{}})",
    };
    for (const char *bad : invalid) {
        bool rejected = false;
        try {
            (void)runtime_module_config("osc.in", Json::parse(bad));
        } catch (const std::exception &e) {
            rejected = true;
            if (Json::parse(bad).contains("version")) CHECK(std::string(e.what()) == "Unsupported OSC config version");
        }
        CHECK(rejected); // Known keys still reject invalid values/types.
    }

    auto many = known;
    for (int n = 0; n < 24; ++n) many["rows"][0]["future" + std::to_string(n)] = n;
    many["rows"][0]["a\nunsafe"] = true;
    ignored.clear();
    assert_known_values(many, &ignored);
    CHECK(ignored.size() == 16);
    for (const auto &name : ignored) CHECK(name.size() <= 80 && name.find('\n') == std::string::npos);
}
static void osc_out_config_validation() {
    using Json = nlohmann::json;
    auto source = Json::parse(
        R"({"port":9002,"rate_hz":200,"rows":[{"address":"/dev/gate","kind":"gate","enabled":false},{"deadband":0.02}],"notes":{"enabled":true}})");
    std::vector<std::string> ignored;
    auto raw = runtime_module_config("osc.out", source, 42, &ignored);
    wirescape::osc::OutConfiguration cfg;
    CHECK(wirescape::osc::out_configuration(raw.data(), static_cast<uint32_t>(raw.size()), cfg));
    CHECK(cfg.port == 9002 && cfg.rate_hz == 200 && ignored.empty());
    CHECK(cfg.rows[0].kind == 1 && cfg.rows[0].enabled == 0);
    CHECK(std::strcmp(cfg.rows[0].address, "/dev/gate") == 0);
    CHECK(cfg.rows[1].deadband == .02f && cfg.rows[2].deadband == .001f);
    CHECK(cfg.notes.enabled == 1 && std::strcmp(cfg.notes.address, "/ws/note") == 0);
    source["unknown"] = Json::array({1, 2});
    source["rows"][0]["extra"] = Json::object({{"a", 1}});
    source["notes"]["future"] = true;
    ignored.clear();
    raw = runtime_module_config("osc.out", source, 42, &ignored);
    CHECK(ignored ==
          std::vector<std::string>({"osc.out#42.unknown", "osc.out#42.rows[0].extra", "osc.out#42.notes.future"}));
    CHECK(source["unknown"].is_array() && source["rows"][0]["extra"].is_object());
    auto rejected = [&](const char *json) {
        bool invalid = false;
        try {
            (void)runtime_module_config("osc.out", Json::parse(json));
        } catch (const std::exception &) {
            invalid = true;
        }
        CHECK(invalid);
    };
    // A91/A99: v2 is now authored syntax, but does not change the private
    // DSP blob. Retain the unsupported-version refusal at the next version.
    const auto legacy_bytes = runtime_module_config("osc.out", Json::parse(R"({"version":1,"port":9002})"));
    CHECK(legacy_bytes == runtime_module_config("osc.out", Json::parse(R"({"version":2,"port":9002})")));
    CHECK(legacy_bytes == runtime_module_config("osc.out", Json::parse(
        R"({"version":2,"port":9002,"host":"192.0.2.17"})")));
    CHECK(osc_out_ipv4(Json::parse(R"({"version":2,"host":"192.0.2.17"})")) == 0xc0000211u);
    CHECK(osc_out_ipv4(Json::parse(R"({"version":2})")) == 0x7f000001u);
    for (const char *bad :
         {R"({"version":3})", R"({"version":"1"})", R"({"version":0})",
          R"({"version":1,"host":"127.0.0.1"})", R"({"version":2,"host":"127.000.0.1"})",
          R"({"version":2,"host":"127.0.0.1:9002"})", R"({"version":2,"host":null})",
          R"({"port":65536})", R"({"port":0})", R"({"rate_hz":501})",
          R"({"rate_hz":0})", R"({"host":"127.0.0.1"})", R"({"lan":false})", R"({"rows":{}})",
          R"({"rows":[{"address":"missing-slash"}]})", R"({"rows":[{"address":"/a*"}]})",
          R"({"rows":[{"kind":"trigger"}]})", R"({"rows":[{"enabled":1}]})", R"({"rows":[{"deadband":-0.1}]})",
          R"({"rows":[{"deadband":1.1}]})", R"({"notes":{"enabled":1}})", R"({"notes":{"address":"/a b"}})"})
        rejected(bad);
    const auto defaults = runtime_module_config("osc.out", Json::object());
    CHECK(defaults.size() == sizeof(wirescape::osc::OutConfiguration));
    wirescape::osc::OutConfiguration binary_defaults;
    CHECK(wirescape::osc::out_configuration(defaults.data(), static_cast<uint32_t>(defaults.size()), binary_defaults));
    CHECK(binary_defaults.bus == nullptr && binary_defaults.port == 9001);
    CHECK(binary_defaults.rows[0].enabled == 1 && binary_defaults.notes.enabled == 0);
    CHECK(std::strcmp(binary_defaults.rows[0].address, "/ws/row/1") == 0);
}
// M2 E0: canonical bytes. Each config-bearing branch is encoded twice after the stack and
// heap were dirtied with different patterns; every byte, padding included, must match.
// Branch/type coverage: sequencing.groove v1 and v2 (groove::Config, Step has 3 padding
// bytes), osc.in (osc::Configuration, padding before the statistics pointer on 64-bit),
// osc.out with and without a staged bus (osc::OutConfiguration), midi.cc_to_cv
// (midi::CcConfiguration, CcRow has 6 tail bytes and 4 after version), essentials.chord
// (instance id bytes, no struct). Empty JSON for non-OSC-Out types and midi.in encode no
// bytes at all, so they have nothing to canonicalize.
#if defined(__GNUC__) || defined(__clang__)
#define E0_NOINLINE __attribute__((noinline))
#else
#define E0_NOINLINE __declspec(noinline)
#endif
E0_NOINLINE static std::vector<uint8_t> encode_dirty(unsigned char pattern, const std::string &type,
                                                     const nlohmann::json &value, uint32_t instance) {
    {
        volatile unsigned char stack[64 * 1024];
        for (auto &b : stack) b = pattern;
    }
    for (size_t size : {sizeof(groove::Config), sizeof(wirescape::osc::Configuration),
                        sizeof(wirescape::osc::OutConfiguration), sizeof(wirescape::midi::CcConfiguration)}) {
        auto *heap = static_cast<unsigned char *>(std::malloc(size));
        CHECK(heap);
        std::memset(heap, pattern, size);
        std::free(heap);
    }
    std::vector<std::string> ignored;
    return runtime_module_config(type, value, instance, &ignored);
}
static void canonical_bytes() {
    using Json = nlohmann::json;
    const std::vector<std::pair<std::string, Json>> cases = {
        {"essentials.chord", Json::object()},
        {"sequencing.groove", Json::parse(R"({"version":1,"bpm":97.5,"tracks":[{"steps":[{"kind":"note","key":64,
            "velocity":0.5,"mod1":0.25},{"kind":"tie"},{"kind":"rest"}]},{"mute":true,"steps":[{"kind":"rest"}]}]})")},
        {"sequencing.groove", Json::parse(R"({"version":2,"bpm":140,"tracks":[{"length":16,"div":2,"steps":[
            {"kind":"note","key":60,"velocity":1,"keys":[60,64,67],"gate":0.5,"cond":{"type":"ab","a":1,"b":3}},
            {"kind":"note","key":62,"velocity":0.75,"cond":{"type":"chance","p":40}},{"kind":"tie","gate":0.25}]}]})")},
        {"osc.in", Json::parse(R"({"port":9011,"lan":true,"future":1,"rows":[{"pattern":"/a","kind":"gate",
            "argument":3,"smoothing_ms":2,"stale":"zero"},{"pattern":"/b","enabled":false}]})")},
        {"osc.out", Json::parse(R"({"version":1,"port":9100,"rate_hz":50,"rows":[{"address":"/x","kind":"gate",
            "deadband":0.25}],"notes":{"address":"/n","enabled":true}})")},
        {"osc.out", Json::object()},
        {"midi.cc_to_cv", Json::parse(R"({"rows":[{"channel":3,"controller":7,"fourteen_bit":true,"min":-2,"max":5},
            {"bipolar":true,"smoothing_ms":10}]})")},
    };
    for (const auto &[type, value] : cases) {
        const auto a = encode_dirty(0xA5, type, value, 21);
        const auto b = encode_dirty(0x5A, type, value, 21);
        const auto c = encode_dirty(0xFF, type, value, 21);
        CHECK(!a.empty() && a == b && b == c);
    }
    // Padding bytes are zero, not merely equal between runs.
    const auto cc = encode_dirty(0xC3, "midi.cc_to_cv", cases.back().second, 0);
    for (size_t i = offsetof(wirescape::midi::CcRow, has_max) + 1; i < sizeof(wirescape::midi::CcRow); ++i)
        CHECK(cc[offsetof(wirescape::midi::CcConfiguration, rows) + i] == 0);
    for (size_t i = sizeof(uint32_t); i < offsetof(wirescape::midi::CcConfiguration, rows); ++i) CHECK(cc[i] == 0);
    const auto groove_bytes = encode_dirty(0xC3, "sequencing.groove", cases[2].second, 0);
    const size_t step0 = offsetof(groove::Config, tracks) + offsetof(groove::Track, steps);
    for (size_t i = offsetof(groove::Step, key_count) + 1; i < offsetof(groove::Step, keys); ++i)
        CHECK(groove_bytes[step0 + i] == 0);
    // A staged bus is spliced in after encoding; bytes stay canonical and equal.
    wirescape::osc::OutBus *fake = reinterpret_cast<wirescape::osc::OutBus *>(uintptr_t(0x1000));
    const std::map<uint32_t, wirescape::osc::OutBus *> buses{{21u, fake}};
    ScopedOutBuses scope(buses);
    CHECK(encode_dirty(0x11, "osc.out", cases[4].second, 21) == encode_dirty(0xEE, "osc.out", cases[4].second, 21));
}
int main() try {
 canonical_bytes();
 auto encode=[](const char*s){return runtime_module_config("midi.cc_to_cv",nlohmann::json::parse(s));};
 auto bytes=encode(R"({"rows":[{"channel":16,"controller":31,"fourteen_bit":true,"bipolar":true,"smoothing_ms":0}]})");
 wirescape::midi::CcConfiguration config;CHECK(wirescape::midi::cc_configuration(bytes.data(),static_cast<uint32_t>(bytes.size()),config));
 CHECK(config.rows[0].channel==16&&config.rows[0].controller==31&&config.rows[0].fourteen_bit&&config.rows[0].bipolar&&config.rows[0].smoothing_ms==0);CHECK(config.rows[1].controller==2&&config.rows[1].smoothing_ms==5);
 for(const char*s:{R"({"rows":[{"channel":17}]})",R"({"rows":[{"controller":32,"fourteen_bit":true}]})",R"({"rows":[{"controller":1.5}]})",R"({"rows":[{"fourteen_bit":1}]})",R"({"rows":[{"smoothing_ms":-1}]})",R"({"rows":[{"unknown":1}]})",R"({"rows":[{},{},{},{},{},{},{},{},{}]})"}){bool rejected=false;try{encode(s);}catch(const std::exception&){rejected=true;}CHECK(rejected);}

 auto ranged = encode(
     R"({"rows":[{"controller":21,"bipolar":true,"min":4.0,"max":-2.0},{"max":0.5},{"min":3.0},{"min":0.25,"max":0.25}]})");
 wirescape::midi::CcConfiguration range;
 CHECK(wirescape::midi::cc_configuration(ranged.data(), static_cast<uint32_t>(ranged.size()), range));
 CHECK(range.version == 2 && range.rows[0].minimum() == 4 && range.rows[0].maximum() == -2);
 CHECK(range.rows[1].minimum() == 0 && range.rows[1].maximum() == 0.5);
 CHECK(range.rows[2].minimum() == 3 && range.rows[2].maximum() == 1);
 CHECK(range.rows[3].minimum() == 0.25 && range.rows[3].maximum() == 0.25);
 wirescape::midi::CcConfigurationV1 old;
 old.rows[0].bipolar = 1;
 CHECK(wirescape::midi::cc_configuration(reinterpret_cast<const uint8_t *>(&old), sizeof(old), range));
 CHECK(range.rows[0].minimum() == -1 && range.rows[0].maximum() == 1);
 for (const char *s : {R"({"rows":[{"min":"0"}]})", R"({"rows":[{"max":false}]})", R"({"rows":[{"min":null}]})",
                       R"({"rows":[{"max":1e999}]})", R"({"rows":[{"min":-1e999}]})"}) {
     bool rejected = false;
     try {
         encode(s);
     } catch (const std::exception &) {
         rejected = true;
     }
     CHECK(rejected);
 }
 CHECK(runtime_module_config("midi.in",nlohmann::json::parse(R"({"endpoint":"Controller","system_name":"system"})")).empty());
 bool malformed=false;try{encode("{");}catch(const nlohmann::json::parse_error&){malformed=true;}CHECK(malformed);
 auto groove = [](const char *s) { return runtime_module_config("sequencing.groove", nlohmann::json::parse(s)); };
 const auto groove_old = groove(
     R"({"version":1,"bpm":120,"tracks":[{"steps":[{"kind":"note","key":60,"velocity":0.5},{"kind":"tie"},{"kind":"rest"}]}]})");
 groove::Config g;
 CHECK(groove::decode(groove_old.data(), static_cast<uint32_t>(groove_old.size()), g));
 CHECK(g.track_count == 1 && g.tracks[0].steps[0].kind == groove::Note && g.tracks[0].steps[1].kind == groove::Tie &&
       g.tracks[0].steps[3].kind == groove::Rest);
 CHECK(g.tracks[0].steps[0].mod1 == 0 && g.tracks[0].steps[0].mod2 == 0);
 const auto expanded = groove(
     R"({"version":1,"bpm":123,"tracks":[{"mute":true,"armed":false,"steps":[{"kind":"note","key":71,"velocity":0.8,"mod1":0.25,"mod2":0.75}]},{"steps":[{"kind":"note","key":48,"velocity":1,"mod1":1,"mod2":0}]}]})");
 CHECK(groove::decode(expanded.data(), static_cast<uint32_t>(expanded.size()), g));
 CHECK(g.track_count == 2 && g.tracks[0].armed == 0 && g.tracks[0].mute == 1 && g.tracks[0].steps[0].mod1 == .25f &&
       g.tracks[0].steps[0].mod2 == .75f);
 CHECK(g.tracks[0].steps[31].kind == groove::Rest && g.tracks[1].steps[31].kind == groove::Rest);
 for (const char *bad :
      {R"({"version":1,"bpm":120,"tracks":[{"steps":[{"kind":"rest","unexpected":2}]}]})",
       R"({"version":1,"bpm":120,"tracks":[{"steps":[{"kind":"note","key":60,"velocity":1,"mod1":2}]}]})",
       R"({"version":1,"bpm":120,"tracks":[{"armed":1,"steps":[{"kind":"rest"}]}]})",
       R"({"version":1,"bpm":120,"tracks":[{"steps":[{"kind":"rest","key":60}]}]})",
       R"({"version":1,"bpm":120,"tracks":[]})"}) {
     bool rejected = false;
     try {
         groove(bad);
     } catch (const std::exception &) {
         rejected = true;
     }
     CHECK(rejected);
 }
 const auto v2 = nlohmann::json::parse(
     R"({"version":2,"bpm":120,"tracks":[{"length":16,"steps":[{"kind":"note","key":64,"velocity":0.8}]}]})");
 auto accepted_groove = [&](const nlohmann::json &doc) {
     const auto raw = runtime_module_config("sequencing.groove", doc);
     groove::Config out;
     CHECK(groove::decode(raw.data(), static_cast<uint32_t>(raw.size()), out));
     return out;
 };
 auto refused_groove = [&](const nlohmann::json &doc) {
     bool refused = false;
     try {
         runtime_module_config("sequencing.groove", doc);
     } catch (const std::exception &) {
         refused = true;
     }
     CHECK(refused);
 };
 CHECK(accepted_groove(v2).tracks[0].steps[0].key_count == 1);
 for (const auto &notes :
      {nlohmann::json::array({64}), nlohmann::json::array({64, 60, 67}), nlohmann::json::array({64, 60, 62, 67, 71})}) {
     auto doc = v2;
     doc["tracks"][0]["steps"][0]["keys"] = notes;
     const auto decoded = accepted_groove(doc);
     CHECK(decoded.tracks[0].steps[0].key_count == notes.size());
     for (size_t i = 0; i < notes.size(); ++i) CHECK(decoded.tracks[0].steps[0].keys[i] == notes[i].get<int>());
 }
 for (const auto &notes :
      {nlohmann::json::array(), nlohmann::json::array({64, 60, 62, 67, 71, 72}), nlohmann::json::array({64, -1}),
       nlohmann::json::array({64, 128}), nlohmann::json::array({64, 60.5}), nlohmann::json::array({64, "60"}),
       nlohmann::json::array({64, true}), nlohmann::json::array({60, 64}), nlohmann::json::array({64, 64}),
       nlohmann::json::array({64, 60, 60}), nlohmann::json::array({64, 67, 60})}) {
     auto doc = v2;
     doc["tracks"][0]["steps"][0]["keys"] = notes;
     refused_groove(doc);
 }
 for (const char *kind : {"rest", "tie"}) {
     auto doc = v2;
     doc["tracks"][0]["steps"][0] = {{"kind", kind}, {"keys", nlohmann::json::array({64})}};
     refused_groove(doc);
 }
 for (const auto &speed : {1, 2, 4, 8}) {
     auto doc = v2;
     doc["tracks"][0]["div"] = speed;
     CHECK(accepted_groove(doc).tracks[0].div == static_cast<uint32_t>(speed));
 }
 CHECK(accepted_groove(v2).tracks[0].div == 1);
 for (const auto &speed : {nlohmann::json(0), nlohmann::json(3), nlohmann::json(16), nlohmann::json(-2),
                           nlohmann::json(2.0), nlohmann::json("2"), nlohmann::json(true), nlohmann::json(nullptr)}) {
     auto doc = v2;
     doc["tracks"][0]["div"] = speed;
     refused_groove(doc);
 }
 {
     auto doc = nlohmann::json::parse(
         R"({"version":1,"bpm":120,"tracks":[{"steps":[{"kind":"note","key":64,"velocity":0.8}]}]})");
     doc["tracks"][0]["div"] = 2;
     refused_groove(doc);
     doc["tracks"][0].erase("div");
     doc["tracks"][0]["steps"][0]["keys"] = nlohmann::json::array({64});
     refused_groove(doc);
 }
 instance_config_union();
 osc_row_enabled();
 osc_future_keys();
 osc_out_config_validation();
 std::puts("PASS bounded typed MIDI and Groove configurations and invalid row rejection");
} catch(const std::exception& error) {
 std::fprintf(stderr,"FAIL runtime module configuration: %s\n",error.what());return EXIT_FAILURE;
} catch(...) {
 std::fputs("FAIL runtime module configuration: unknown exception\n",stderr);return EXIT_FAILURE;
}
