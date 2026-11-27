// SPDX-License-Identifier: GPL-3.0-only
#include "runtime_patch.h"
#include "runtime_patch_normalize.h"
#include "io_data_migration.h"
#include "../../engine/engine2.h"
#include <filesystem>
#include <cstring>
#include "../../tests/native/abi2/allocation_watch.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <cmath>
using Json=nlohmann::json;
using Owner=std::unique_ptr<AppEngine,decltype(&app_engine_destroy)>;
static void check(bool value,const char*why){if(!value)throw std::runtime_error(why);}

static void saved_lfo_patch(const char *demo, AppEngine *catalog, const wirescape::engine2::Config &cfg) {
    const auto path = std::filesystem::path(demo).parent_path().parent_path() / "document/ui_starters.json";
    std::ifstream input(path);
    check(bool(input), "open existing saved starters");
    Json starters;
    input >> starters;
    Json patch;
    for (const auto &entry : starters)
        if (entry.at("id") == "qt-lfo-filter") patch = entry.at("patch");
    check(!patch.is_null(), "find existing pre-phase LFO starter");
    std::string error;
    Owner engine(wirescape::document::load_runtime_patch(patch.dump(), catalog, cfg, error), app_engine_destroy);
    check(bool(engine), "existing saved LFO patch loads without migration");
    // Frozen free-run renderer from Lfo::process at pre-change main 7c7d713.
    // Use a same-build reference because libm sin bits may differ across platforms.
    const auto &params = patch.at("modules").at(4).at("parameters");
    check(patch.at("modules").at(4).at("module") == "essentials.lfo" &&
          patch.at("modules").at(4).at("id") == 5 && params.empty(), "saved LFO identity/defaults");
    const float rate = params.value("rate", 1.f), depth = params.value("depth", 1.f);
    const float offset = params.value("offset", 0.f);
    constexpr double tau = 6.283185307179586476925286766559;
    double phase = 0;
    float audio[128];
    auto &native = app_engine_native(engine.get());
    check(native.meter().feedback_edges == 0, "saved patch has no feedback chunking");
    for (uint32_t block = 0; block < 750; ++block) {
        check(app_engine_render(engine.get(), audio, 128) == WS2_OK, "render saved LFO patch");
        for (uint32_t i = 0; i < 128; ++i) {
            const float expected = static_cast<float>(std::sin(phase) * depth + offset);
            const float actual = native.output_sample(5, 0, 0, i);
            uint32_t before = 0, after = 0;
            std::memcpy(&before, &expected, sizeof(before));
            std::memcpy(&after, &actual, sizeof(after));
            check(before == after, "saved LFO control bit-identical to pre-phase renderer");
            phase += tau * rate / cfg.sample_rate;
            if (phase >= tau) phase = std::fmod(phase, tau);
        }
    }
    std::cout << "saved qt-lfo-filter loads unchanged; 96000 control samples bit-identical to pre-phase renderer\\n";
}

// OB-a3 pin 7: native document execution of a legacy v1 file is read-only.
// This tests the common loader used by CLI/soak/golden, not their separate CLI paths.
static void legacy_runtime_load_is_read_only(const std::filesystem::path &filename,
                                            AppEngine *catalog,
                                            const wirescape::engine2::Config &cfg) {
    std::ifstream before_file(filename, std::ios::binary);
    check(bool(before_file), "OB-a3 read legacy fixture");
    const std::string before((std::istreambuf_iterator<char>(before_file)), {});
    check(Json::parse(before).at("version") == 1, "OB-a3 fixture is v1");
    const auto stamp = std::filesystem::last_write_time(filename);
    std::string error;
    Owner engine(wirescape::document::load_runtime_patch(before, catalog, cfg, error), app_engine_destroy);
    check(bool(engine), "OB-a3 native loader still accepts v1");
    float samples[128]{};
    check(app_engine_render(engine.get(), samples, 128) == WS2_OK,
          "OB-a3 v1 graph remains executable");
    std::ifstream after_file(filename, std::ios::binary);
    check(bool(after_file), "OB-a3 fixture still exists");
    const std::string after((std::istreambuf_iterator<char>(after_file)), {});
    check(after == before && std::filesystem::last_write_time(filename) == stamp,
          "OB-a3 native v1 load must not rewrite original file");
    check(!std::filesystem::exists(filename.string() + ".bak-v1"),
          "OB-a3 execution-only loader cannot create a desktop backup");
}

static void stored_modulation_duplicates() {
    Json first = {{"kind", "modulation"}, {"amount", .8}, {"opaque", "first"},
                  {"from", {{"module", 10}, {"port", "control"}}},
                  {"to", {{"module", 9}, {"port", "frequency"}}}};
    Json later = first;
    later["amount"] = .7;
    later["opaque"] = "later";
    Json signal = {{"kind", "signal"}};
    Json cables = Json::array({first, signal, later});
    auto warnings = wirescape::document::normalize_stored_modulation(cables, 2);
    first["amount"] = 1.;
    check(cables == Json::array({first, signal}), "retain first metadata and position, clamp merged amount");
    check(warnings.size() == 1 && warnings[0].find("10:control -> 9:frequency") != std::string::npos,
          "warn once and identify the merged cable");
    first["amount"] = .8;
    Json last = later;
    last["amount"] = -.9;
    cables = Json::array({first, later, last});
    warnings = wirescape::document::normalize_stored_modulation(cables, 2);
    check(warnings.size() == 1 && std::abs(cables[0]["amount"].get<double>() - .6) < 1e-12,
          "sum all amounts before clamping");
}

static void osc_in_label_execution_metadata() {
    using namespace wirescape::document;
    const auto legacy = Json::parse(R"({"id":1,"module":"osc.in","config":{"rows":[{"pattern":"/filter","kind":"gate"}]}})");
    auto baseline = legacy;
    migrate_io_module(baseline);
    auto authored = baseline;
    authored["data"]["routes"]["rows"][0]["label"] = "Filter";
    const auto original = authored.dump();
    auto execution = authored;
    std::vector<std::string> warnings;
    migrate_io_module(execution, &warnings);
    check(warnings.empty(), "SC1 canonical row label has no load warning");
    check(execution == baseline, "SC1 canonical row label excluded from execution copy");
    check(authored.dump() == original, "SC1 authored label bytes preserved");
    // Both paths must give the same complete descriptor fields, including fallback rows.
    auto labelled_legacy = legacy;
    labelled_legacy["config"]["rows"][0]["label"] = "Filter";
    auto legacy_execution = labelled_legacy;
    const auto legacy_original = labelled_legacy.dump();
    migrate_io_module(legacy_execution, &warnings);
    check(warnings.empty() && legacy_execution == baseline, "SC1 legacy row label excluded without warning");
    check(labelled_legacy.dump() == legacy_original, "SC1 legacy authored bytes preserved");
}

// #663: missing feedback settings must work at Daisy-sized blocks, without
// weakening the validation of explicitly authored feedback delays.
static void small_block_feedback_default() {
    Json patch = Json::parse(R"({"format":"wirescape.native.patch","version":2,"settings":{},
      "modules":[{"id":1,"module":"essentials.vca","version":2}],
      "connections":[],"outputs":[{"module":1,"port":"audio","bus_channel":0}]})");
    for (uint32_t block : {16u, 17u, 32u, 64u}) {
        wirescape::engine2::Config cfg{};
        cfg.max_block = block;
        std::string error;
        auto load = [&] {
            return Owner(wirescape::document::load_runtime_patch(patch.dump(), nullptr, cfg, error),
                         app_engine_destroy);
        };
        auto plain = load();
        check(bool(plain), "#663 omitted feedback_block prepares at small block");
        float samples[64]{};
        check(app_engine_render(plain.get(), samples, block) == WS2_OK, "#663 render small block");

        patch["connections"] = Json::array({{{"kind","signal"},
            {"from",{{"module",1},{"port","audio"}}},
            {"to",{{"module",1},{"port","audio"}}}}});
        auto loop = load();
        check(bool(loop), "#663 feedback loop prepares with omitted setting");
        auto loops = app_engine_native(loop.get()).feedback_loops();
        check(loops.size() == 1 && loops[0].delay_frames == (block < 32 ? block : 32),
              "#663 default delay is min(32, max_block)");

        patch["settings"]["feedback_block"] = 1;
        auto explicit_loop = load();
        check(bool(explicit_loop), "#663 explicit valid feedback delay prepares");
        loops = app_engine_native(explicit_loop.get()).feedback_loops();
        check(loops.size() == 1 && loops[0].delay_frames == 1, "#663 explicit delay preserved");
        patch["settings"]["feedback_block"] = block + 1;
        check(!load() && error == "Invalid feedback block", "#663 explicit oversized delay refused");
        patch["settings"].erase("feedback_block");
        patch["connections"] = Json::array();
    }
}

int main(int argc,char**argv){try{
 osc_in_label_execution_metadata();
 stored_modulation_duplicates();
 small_block_feedback_default();
 check(argc==2,"demo argument");std::ifstream input(argv[1]);std::string bytes((std::istreambuf_iterator<char>(input)),{});check(!bytes.empty(),"read demo");
 wirescape::engine2::Config cfg{};
    cfg.sample_rate = 48000;
    cfg.max_block = 128;
    cfg.max_nodes = 64;
    cfg.event_budget = 2048;Owner catalog(app_engine_create(&cfg),app_engine_destroy);std::string error;
 saved_lfo_patch(argv[1], catalog.get(), cfg);
 legacy_runtime_load_is_read_only(argv[1], catalog.get(), cfg);
 // Qt's inspection-only legacy formats must never become executable native graphs.
 const auto fixtures = std::filesystem::path(argv[1]).parent_path().parent_path().parent_path() / "tests/native/compat/fixtures/legacy_documents";
 for (const char *name : {"patch_v1.json", "patch_v2.json", "patch_v3_unknown.json", "visual_study_v4.json",
                          "future_patch_v99.json", "malformed_patch.json"}) {
     std::ifstream fixture(fixtures / name, std::ios::binary);
     check(bool(fixture), "read original legacy fixture");
     const std::string original((std::istreambuf_iterator<char>(fixture)), {});
     const auto retained = original;
     const auto count = app_engine_module_count(catalog.get());
     Owner rejected(wirescape::document::load_runtime_patch(original, catalog.get(), cfg, error), app_engine_destroy);
     check(!rejected && !error.empty(), "legacy/visual/future/malformed fixture refuses execution with diagnostic");
     check(original == retained && app_engine_module_count(catalog.get()) == count,
           "refusal leaves source bytes and live catalogue unchanged");
 }

 auto load=[&](const std::string&source){return Owner(wirescape::document::load_runtime_patch(source,catalog.get(),cfg,error),app_engine_destroy);};
 auto v1=load(bytes);check(bool(v1),"v1 loader");auto source=Json::parse(bytes),patch=source;patch["version"]=2;patch["settings"]={{"max_channels",16},{"feedback_block",1},{"seed",1u}};patch["outputs"]=Json::array({{{"module",source["outputNode"]},{"port","audio"},{"bus_channel",0}}});
 for(auto&m:patch["modules"]){auto type=m["type"].get<std::string>();m["module"]=type;m["version"]=1;m["config"]=Json::object();m["parameters"]=Json::object();for(auto it=m["values"].begin();it!=m["values"].end();++it)m["parameters"][app_engine_parameter_id(catalog.get(),type.c_str(),uint32_t(std::stoul(it.key())))]=it.value();m.erase("type");m.erase("values");}
 for(auto&c:patch["connections"]){c["from"]={{"module",c["fromNode"]},{"port",c["fromPort"]}};c["to"]={{"module",c["toNode"]},{"port",c["toPort"]}};c["kind"]="signal";for(auto key:{"fromNode","fromPort","toNode","toPort"})c.erase(key);}
 auto v2=load(patch.dump());check(bool(v2),"v2 loader");float a[128],b[128];
 for(int block=0;block<100;++block){int ra,rb;size_t count;{allocation_watch::Scope watch;ra=app_engine_render(v1.get(),a,128);rb=app_engine_render(v2.get(),b,128);count=watch.allocations();}check(ra==WS2_OK&&rb==WS2_OK&&count==0,"loader callback allocation-free");for(int i=0;i<128;++i)check(a[i]==b[i]&&std::isfinite(a[i]),"v1/v2 graph equivalence");}
 check(!load("{\"format\":\"wirescape.native.patch\",\"format\":\"wirescape.native.patch\"}"),"duplicate keys rejected");
 for (const auto &raw : {std::string("{\"format\":1,\"\\u0066ormat\":2}"), std::string("{\"x\":[{\"a\":1,\"a\":2}]}")})
     check(!load(raw) && !error.empty(), "escaped and nested duplicate keys refused");
 auto duplicate = patch;
 duplicate["modules"].push_back(duplicate["modules"][0]);
 check(!load(duplicate.dump()), "duplicate module IDs refused");
 auto dangling = patch;
 dangling["connections"][0]["to"]["module"] = 99;
 check(!load(dangling.dump()), "dangling destination refused");
 dangling = patch;
 dangling["outputs"][0]["module"] = 99;
 check(!load(dangling.dump()), "dangling output refused");
 auto bad=patch;bad["version"]=99;check(!load(bad.dump()),"future version refused");bad=patch;bad["modules"][0]["parameters"]={{"unknown",1}};check(!load(bad.dump()),"unknown parameter refused");
 bad=patch;bad["modules"][0]["inactive"]=true;check(!load(bad.dump()),"inactive module refused");bad=patch;bad["modules"][0]["id"]=1.5;check(!load(bad.dump()),"fractional ID refused");
 bad=patch;bad["settings"]["max_channels"]=17;check(!load(bad.dump()),"channel limit");bad=patch;bad["modules"][0]["config"]={{"unknown",1}};check(!load(bad.dump()),"unsupported nonempty config fails closed");
 bad=patch;bad["settings"]["sample_rate"]="48000";check(!load(bad.dump()),"sample rate type");
 // E3a-2: data has its own typed envelope, independent of config.
 bad=patch;bad["modules"][0]["data"]=Json::array();
 check(!load(bad.dump()) && error.find("data") != std::string::npos,
       "malformed data envelope refused with field diagnostic");
 bad=patch;bad["modules"][0]["data"]=Json::object();
 check(bool(load(bad.dump())), "empty data object on legacy module remains loadable");

 auto ccpatch = Json::parse(R"({"format":"wirescape.native.patch","version":2,"settings":{},
  "modules":[{"id":200,"module":"midi.cc_to_cv","version":1,
    "config":{"rows":[{"channel":1,"controller":21,"bipolar":true,"min":3.5,"max":-2.25}]}},
    {"id":201,"module":"essentials.output","version":1}],
  "connections":[],"outputs":[{"module":201,"port":"audio","bus_channel":0}],
  "ui":{"opaque":{"keep":"lossless"}}})");
 auto ccfirst = load(ccpatch.dump());
 check(bool(ccfirst), "CC native range patch load");
 const auto saved = ccpatch.dump();
 auto reloaded = Json::parse(saved);
 check(reloaded["modules"][0]["config"]["rows"][0]["min"] == 3.5 &&
           reloaded["modules"][0]["config"]["rows"][0]["max"] == -2.25 &&
           reloaded["modules"][0]["config"]["rows"][0]["bipolar"] == true &&
           reloaded["ui"]["opaque"]["keep"] == "lossless",
       "CC JSON round-trip preserves rows/unknown UI");
 auto ccsecond = load(reloaded.dump());
 check(bool(ccsecond), "CC native range patch reload");
 bad = reloaded;
 bad["modules"][0]["config"]["rows"][0]["min"] = "3.5";
 check(!load(bad.dump()), "CC nonnumber minimum refused");
 bad = reloaded;
 bad["modules"][0]["config"]["rows"][0]["max"] = "not finite";
 check(!load(bad.dump()), "CC nonnumber maximum refused");
 float stable[128]{};
 {
     allocation_watch::Scope scope;
     check(app_engine_render(ccfirst.get(), stable, 128) == WS2_OK &&
               app_engine_render(ccsecond.get(), stable, 128) == WS2_OK && scope.allocations() == 0,
           "refusal leaves previously loaded graphs usable");
 }

 check(!load(std::string(wirescape::document::RuntimePatchLimit+1,' ')),"document size limit");check(!load("[]"),"root type");
 std::cout<<"runtime loader v1/v2, validation, noalloc pass\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
