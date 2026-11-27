// SPDX-License-Identifier: GPL-3.0-only
#include "../../tests/native/abi2/allocation_watch.h"
#include "app_engine.h"
#include "module_registry.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
static void check(bool ok,const char*message){if(!ok)throw std::runtime_error(message);}
using App=std::unique_ptr<AppEngine,decltype(&app_engine_destroy)>;
static App make(){wirescape::engine2::Config c{};
        c.sample_rate = 48000;
        c.max_block = 128;
        c.max_nodes = 32;
        c.event_budget = 2048;App e(app_engine_create(&c),app_engine_destroy);check(bool(e),"create app engine");return e;}
static void native_catalogue_and_replan(){
    auto source = make();
    // Known IDs may only grow (#687): every one must be present, none twice.
    std::set<std::string> ids;
    for (uint32_t i = 0; i < app_engine_module_count(source.get()); ++i)
        check(ids.insert(app_engine_module(source.get(), i)->id).second, "duplicate catalogue module ID");
    std::ifstream known(WS_KNOWN_MODULE_IDS);
    check(bool(known), "known module ID list readable");
    size_t known_count = 0;
    for (std::string line; std::getline(known, line);) {
        line.erase(line.find_last_not_of(" \t\r") + 1);
        if (line.empty() || line[0] == '#') continue;
        ++known_count;
        if (!ids.count(line)) throw std::runtime_error("known module ID missing from catalogue: " + line);
    }
    check(known_count >= 33, "known module ID list holds the 1.0 catalogue");
    bool quad_seen = false;
    for (auto *native : wirescape::app::builtin_modules()) {
        const ws2_descriptor *metadata = nullptr;
        for (uint32_t i = 0; i < app_engine_module_count(source.get()); ++i) {
            auto *d = app_engine_module(source.get(), i);
            if (!std::strcmp(d->id, native->id)) metadata = d;
        }
        check(app_engine_native_descriptor(source.get(), native->id) == native,
              "catalogue entry always has a native descriptor");
        check(metadata == native && metadata->input_count == native->input_count &&
                  metadata->output_count == native->output_count,
              "catalogue port counts");
        if (!std::strcmp(native->id, "essentials.quad_vca")) {
            check(metadata->input_count == 8 && metadata->output_count == 5,
                  "Quad VCA must expose eight inputs and five outputs");
            quad_seen = true;
        }
        for (uint32_t i = 0; i < native->input_count; ++i)
            check(metadata->inputs[i].kind == native->inputs[i].kind &&
                      metadata->inputs[i].hint == native->inputs[i].hint,
                  "catalogue input kind and hint preserved");
        for (uint32_t i = 0; i < native->output_count; ++i)
            check(metadata->outputs[i].kind == native->outputs[i].kind &&
                      metadata->outputs[i].hint == native->outputs[i].hint,
                  "catalogue output kind and hint preserved");
    }
    check(quad_seen, "Quad VCA is present in the native catalogue");
    // S2: two independently built facades have the same native-only catalogue.
    auto e = make();
    check(app_engine_module_count(e.get()) == app_engine_module_count(source.get()),
          "native catalogue stable across instances");
    for (uint32_t i = 0; i < app_engine_module_count(e.get()); ++i)
        check(app_engine_native_descriptor(e.get(), app_engine_module(e.get(), i)->id),
              "replacement catalogue has no metadata-only entry");
    source.reset();

    // Keep the facade's live-replan, state/generation and callback allocation
    // coverage; only the deleted ABI1 fixture/legacy-ID branches are removed.
    check(app_engine_add_node(e.get(), 9, "essentials.vca") == WS2_OK &&
          app_engine_prepare(e.get(), 9, 0) == WS2_OK, "native live graph");
    float samples[128]{};
    check(app_engine_render(e.get(), samples, 128) == WS2_OK &&
          std::all_of(samples, samples + 128, [](float v) { return v == 0.f; }),
          "native silent input renders zero");
    auto candidate = make();
    check(app_engine_add_node(candidate.get(), 9, "essentials.vca") == WS2_OK &&
          app_engine_add_node(candidate.get(), 10, "essentials.noise") == WS2_OK &&
          app_engine_prepare(candidate.get(), 9, 0) == WS2_OK,
          "native candidate stages unrelated node addition");
    std::atomic<bool> running{true}, failed{false};
    std::atomic<unsigned> blocks{0};
    std::atomic<float> last{0};
    std::atomic<size_t> live_allocations{0};
    std::thread render([&] {
        float out[128];
        while (running.load()) {
            int status;
            {
                allocation_watch::ThreadScope watch;
                status = app_engine_render(e.get(), out, 128);
                live_allocations += watch.allocations();
            }
            if (status != WS2_OK) failed = true;
            last.store(out[127]);
            ++blocks;
            std::this_thread::yield();
        }
    });
    struct Join {
        std::atomic<bool> &run;
        std::thread &thread;
        ~Join() {
            run = false;
            if (thread.joinable()) thread.join();
        }
    } join{running, render};
    auto wait = [&](unsigned count) {
        auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        while (blocks.load() < count && std::chrono::steady_clock::now() < deadline)
            std::this_thread::yield();
        check(blocks.load() >= count, "native live render progresses");
    };
    wait(2);
    const auto generation = app_engine_generation(e.get());
    check(app_engine_replan(e.get(), candidate.get(), 8000000) == WS2_OK,
          app_engine_error(e.get()));
    candidate.reset(); // Static native descriptors must outlive staged graph.
    wait(blocks.load() + 5);
    check(!failed.load() && last.load() == 0.f,
          "native output survives candidate retirement");
    check(app_engine_generation(e.get()) == generation && live_allocations.load() == 0,
          "facade preserves generation and allocation-free live replan");
    running = false;
    render.join();
    check(app_engine_native(e.get()).descriptor(10) != nullptr,
          "staged native node remains after candidate retirement");
}
static void host_notes(){
 auto e=make();check(app_engine_build_essentials(e.get(),"")==WS2_OK,"build app graph");
 auto& engine=app_engine_native(e.get());
 for(uint32_t node=1;node<=4;++node)check(engine.descriptor(node)&&engine.descriptor(node)->abi_version==2,"native ABI2 Essentials");
 for(auto node:{1u,2u}){ws2_event on{};on.struct_size=sizeof(on);on.type=WS2_NOTE_ON;on.value=69;on.source_id=1;on.note_id=71;check(app_engine_enqueue(e.get(),node,on,0,app_engine_generation(e.get()))==WS2_OK,"host note on");}
 for(auto node:{1u,2u}){ws2_event off{};off.struct_size=sizeof(off);off.type=WS2_NOTE_OFF;off.value=69;off.source_id=1;off.note_id=71;check(app_engine_enqueue(e.get(),node,off,4800,app_engine_generation(e.get()))==WS2_OK,"host note off");}
 float out[128],previous=0;double peak=0,tail=0;size_t allocations=0;unsigned crossings=0;
 for(uint32_t frame=0;frame<48000;frame+=128){uint32_t count=std::min(128u,48000-frame);int result;
  {allocation_watch::Scope watch;result=app_engine_render(e.get(),out,count);allocations+=watch.allocations();}
  check(result==WS2_OK,"render host-note graph");
  for(uint32_t i=0;i<count;++i){check(std::isfinite(out[i]),"finite callback output");peak=std::max(peak,double(std::abs(out[i])));if(frame+i>=24000)tail=std::max(tail,double(std::abs(out[i])));
   float oscillator=engine.output_sample(1,0,0,i);if(frame+i<4800&&previous<0&&oscillator>=0)++crossings;previous=oscillator;
  }
 }
 check(peak>0&&tail==0,"ADSR host note reaches envelope and releases");
 check(crossings>=42&&crossings<=45,"host A4 note reaches VCO");
 check(allocations==0,"host callback no allocation");
}
int main(int argc,char**){try{check(argc==1,"no fixture argument");check(app_engine_create(nullptr)==nullptr,"null configuration refused");native_catalogue_and_replan();host_notes();std::cout<<"PASS app native catalogue, host notes, live replan and allocation-free callbacks\n";return 0;}
catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
