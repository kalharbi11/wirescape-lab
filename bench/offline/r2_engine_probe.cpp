// SPDX-License-Identifier: GPL-3.0-only
// T0.5 R2: device-free engine-process probe. No production code modified.
// Compiled from bench/offline/ against the existing Release engine2 static lib.
#include "../../native/engine2/engine2.h"
#include "../../native/sdk/wirescape_sdk.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

using wirescape::engine2::Config;
using wirescape::engine2::Engine;
namespace {
constexpr double pi = 3.14159265358979323846;
uint32_t source_rate = 48000;
bool source_tail = false;
std::vector<float> source_tone; // Filled quiescently before any render.

uint64_t emitted_pre_silence=0;
uint64_t emitted_impulse=0;
uint64_t emitted_active=0;
uint64_t emitted_tail_zero=0;
uint64_t emitted_bad_tail=0;
void reset_source_counters() {
    emitted_pre_silence=0;emitted_impulse=0;emitted_active=0;
    emitted_tail_zero=0;emitted_bad_tail=0;
}

// Fully deterministic source for the engine graph, never a direct descriptor
// process() call. Engine::render installs the production FTZ/DAZ/FZ guard.
struct SignalSource {
    static constexpr ws::Info info{"bench.r2.excitation","R2 test source",1};
    static constexpr std::array<ws2_port,0> inputs{};
    static constexpr std::array outputs{ws::port("audio","Audio",WS2_AUDIO)};
    static constexpr std::array<ws2_param,0> params{};
    void reset(){}
    void process(ws::Block& b) {
        auto output = b.out(0);
        output.set_channels(1);
        output.mark_constant(false);
        auto* samples = output.ch(0);
        for(uint32_t i=0; i<b.frames(); ++i) {
            const uint64_t frame = b.frame_position()+i;
            if(source_tail) {
                if(frame < source_rate) {
                    // No trigonometry, allocations or logging in timed DSP.
                    samples[i]=source_tone[static_cast<size_t>(frame)];
                    ++emitted_active;
                } else {
                    samples[i]=0.f;
                    uint32_t bits=0;
                    std::memcpy(&bits,&samples[i],4);
                    if(bits==0)++emitted_tail_zero;
                    else ++emitted_bad_tail;
                }
            } else {
                samples[i] = frame == source_rate ? 1.f : 0.f;
                if(frame<source_rate)++emitted_pre_silence;
                if(samples[i]!=0.f)++emitted_impulse;
            }
        }
    }
};
std::string escaped(const std::string& s) {
    std::string v;
    for(char c:s) {
        if(c=='"' || c=='\\')v.push_back('\\');
        if(static_cast<unsigned char>(c)>=32)v.push_back(c);
    }
    return v;
}
struct Library {
    void* handle;
    explicit Library(const std::string& filename) {
        handle=dlopen(filename.c_str(), RTLD_NOW|RTLD_LOCAL);
        if(!handle) throw std::runtime_error(std::string("module dlopen: ")+dlerror());
    }
    ~Library(){dlclose(handle);}
    const ws2_descriptor* descriptor() const {
        auto entry=reinterpret_cast<ws2_entry_fn>(dlsym(handle,"ws_module2_entry"));
        auto abi=reinterpret_cast<uint32_t(*)()>(dlsym(handle,"ws_module2_abi_version"));
        if(!entry||!abi||abi()!=2)throw std::runtime_error("missing ABI2 entry/version");
        auto* d=entry();
        if(!d)throw std::runtime_error("null ABI2 descriptor");
        return d;
    }
};
struct Case {
    const ws2_descriptor* desc;
    int audio_input=-1, audio_output=-1;
    explicit Case(const ws2_descriptor* d):desc(d) {
        for(uint32_t i=0;i<d->input_count;++i)
            if(d->inputs[i].kind==WS2_SIGNAL&&d->inputs[i].hint==WS2_AUDIO)
                audio_input=static_cast<int>(i);
        for(uint32_t i=0;i<d->output_count;++i)
            if(d->outputs[i].kind==WS2_SIGNAL&&d->outputs[i].hint==WS2_AUDIO) {
                audio_output=static_cast<int>(i);
                break;
            }
    }
};
void need(bool good,const std::string& what) {
    if(!good)throw std::runtime_error(what);
}
std::unique_ptr<Engine> new_engine(const Case& c,uint32_t rate,uint32_t block,
                                   bool set_resonance) {
    Config cfg;
    cfg.sample_rate=rate;cfg.max_block=block;cfg.max_channels=1;
    cfg.seed=42;
    auto engine=std::make_unique<Engine>(cfg);
    need(engine->add_node(1,ws::Module<SignalSource>::descriptor()),
         "cannot insert deterministic signal source: "+engine->error());
    need(engine->add_node(2,c.desc),"cannot insert target module: "+engine->error());
    for(uint32_t i=0;i<c.desc->input_count;++i) {
        const auto& port=c.desc->inputs[i];
        if(port.kind==WS2_SIGNAL && port.hint==WS2_AUDIO)
            need(engine->connect(1,0,2,i),"cannot connect source to audio input: "+engine->error());
    }
    need(engine->output(2,c.audio_output,0),"cannot tap module output: "+engine->error());
    need(engine->prepare(),"cannot prepare module: "+engine->error());
    if(set_resonance)
        for(uint32_t i=0;i<c.desc->param_count;++i)
            if(std::strcmp(c.desc->params[i].id,"resonance")==0)
                need(engine->set_parameter(2,i,c.desc->params[i].maximum),
                     "cannot set max resonance: "+engine->error());
    engine->reset(); // Start one full second of silence before the single impulse.
    return engine;
}
double median(std::vector<double>& numbers) {
    need(!numbers.empty(),"no full-size blocks for timing median");
    std::sort(numbers.begin(),numbers.end());
    size_t half=numbers.size()/2;
    return numbers.size()%2 ? numbers[half] : (numbers[half-1]+numbers[half])/2.;
}
bool is_subnormal(float f) {
    uint32_t bits;std::memcpy(&bits,&f,4);
    return (bits&0x7f800000u)==0 && (bits&0x007fffffu)!=0;
}
bool nonfinite(float f) {
    uint32_t bits;std::memcpy(&bits,&f,4);
    return (bits&0x7f800000u)==0x7f800000u;
}
std::string mode_name() {
#if defined(__SSE2__) || defined(_M_X64)
    return "engine_render_mxcsr_ftz_daz";
#elif defined(__aarch64__) && !defined(_MSC_VER)
    return "engine_render_fpcr_fz";
#else
    return "engine_render_guard_unverified";
#endif
}
void impulse(const Case& c,const std::string& name,uint32_t rate,
             uint32_t block,const std::string& filename) {
    source_rate=rate;source_tail=false;reset_source_counters();
    auto engine=new_engine(c,rate,block,true);
    std::vector<float> capture;
    capture.reserve(2ull*rate);
    std::array<float,256> output{};
    float* bus[]={output.data()};
    const uint64_t total=3ull*rate;
    uint32_t nonzero_input=0;
    for(uint64_t frame=0;frame<total;) {
        const uint32_t frames=static_cast<uint32_t>(std::min<uint64_t>(block,total-frame));
        need(engine->render(bus,1,frames)==WS2_OK,"engine impulse render failed");
        for(uint32_t i=0;i<frames;++i) {
            nonzero_input+=((frame+i)==rate);
            if(frame+i>=rate)capture.push_back(output[i]);
        }
        frame+=frames;
    }
    need(nonzero_input==1 && emitted_impulse==1 &&
         emitted_pre_silence==rate && capture.size()==2ull*rate,
         "invalid emitted source sample or impulse frame accounting");
    std::ofstream out(filename,std::ios::binary|std::ios::trunc);
    need(static_cast<bool>(out),"cannot write impulse capture");
    out.write(reinterpret_cast<const char*>(capture.data()),
              static_cast<std::streamsize>(capture.size()*sizeof(float)));
    need(static_cast<bool>(out),"cannot complete impulse capture");
    std::printf("{\"status\":\"measured\",\"module\":\"%s\",\"mode\":\"impulse\","
      "\"rate_hz\":%u,\"block_frames\":%u,\"one_second_pre_silence_frames\":%u,"
      "\"impulse_amplitude\":1.0,\"input_nonzero_frames\":%u,"
      "\"capture_frames\":%zu,\"output_port\":%d,\"faults\":%llu,"
      "\"source\":\"engine2_render_native_test_signal\"}\n",
      escaped(name).c_str(),rate,block,rate,nonzero_input,capture.size(),
      c.audio_output,static_cast<unsigned long long>(engine->meter().faults));
}
void tail(const Case& c,const std::string& name,uint32_t rate,uint32_t block) {
    source_rate=rate;source_tail=true;
    source_tone.resize(rate);
    for(uint32_t frame=0;frame<rate;++frame)
        source_tone[frame]=static_cast<float>(
            .5*std::sin((2.*pi*440.*frame)/rate));
    std::printf("{\"status\":\"measured\",\"module\":\"%s\",\"mode\":\"tail\","
      "\"rate_hz\":%u,\"block_frames\":%u,\"active_frames\":%u,"
      "\"zero_frames\":%llu,\"zero_input_verified\":true,"
      "\"production_ftz_mode\":\"%s\",\"timing\":\"wall_ns_around_engine_render\","
      "\"repeats\":[",
      escaped(name).c_str(),rate,block,rate,
      static_cast<unsigned long long>(5ull*rate),mode_name().c_str());
    for(int repeat=0;repeat<5;++repeat) {
        reset_source_counters();
        auto engine=new_engine(c,rate,block,false);
        std::array<float,256> samples{};
        float* bus[]={samples.data()};
        std::vector<double> active,silent;
        uint64_t subnormals=0,nonfinites=0,zero_input_count=0,source_count=0;
        const uint64_t total=6ull*rate;
        for(uint64_t frame=0;frame<total;) {
            const uint64_t until=frame<rate ? rate-frame : total-frame;
            uint32_t frames=static_cast<uint32_t>(std::min<uint64_t>(block,until));
            const auto t0=std::chrono::steady_clock::now();
            const int rc=engine->render(bus,1,frames);
            const auto t1=std::chrono::steady_clock::now();
            need(rc==WS2_OK,"engine tail render failed");
            if(frames==block) {
                const double ns=std::chrono::duration<double,std::nano>(t1-t0).count();
                (frame<rate ? active : silent).push_back(ns);
            }
            for(uint32_t i=0;i<frames;++i) {
                if(frame+i>=rate) {
                    ++zero_input_count; // The source above emits literal +0.0f.
                    subnormals+=is_subnormal(samples[i]);
                } else ++source_count;
                nonfinites+=nonfinite(samples[i]);
            }
            frame+=frames;
        }
        need(source_count==rate && zero_input_count==5ull*rate &&
             emitted_active==rate && emitted_tail_zero==5ull*rate &&
             emitted_bad_tail==0,
             "tail source emitted nonzero data during required exact silence");
        const double active_ns=median(active),silent_ns=median(silent);
        need(active_ns>0 && std::isfinite(silent_ns),"invalid block duration");
        std::printf("%s{\"repeat\":%d,\"active_median_ns\":%.9g,"
          "\"silent_median_ns\":%.9g,\"silent_over_active\":%.9g,"
          "\"active_full_blocks\":%zu,\"silent_full_blocks\":%zu,"
          "\"subnormal_output_samples\":%llu,\"nonfinite_output_samples\":%llu,"
          "\"faults\":%llu}",repeat?",":"",repeat,
          active_ns,silent_ns,silent_ns/active_ns,active.size(),silent.size(),
          static_cast<unsigned long long>(subnormals),
          static_cast<unsigned long long>(nonfinites),
          static_cast<unsigned long long>(engine->meter().faults));
    }
    std::puts("]}");
}
}
int main(int argc,char**argv) {
    try {
        need(argc==7,"usage: r2_engine_probe MODE MODULE LIBRARY RATE BLOCK CAPTURE_OUT");
        const std::string mode=argv[1],module=argv[2],library=argv[3],out=argv[6];
        const uint32_t rate=static_cast<uint32_t>(std::stoul(argv[4]));
        const uint32_t block=static_cast<uint32_t>(std::stoul(argv[5]));
        need((rate==44100||rate==48000||rate==96000)&&block==128,
             "unsupported rate/block request");
        Library owner(library);
        Case c(owner.descriptor());
        if(c.audio_input<0 || c.audio_output<0) {
            std::printf("{\"status\":\"not_applicable\",\"module\":\"%s\","
               "\"mode\":\"%s\",\"rate_hz\":%u,\"reason\":\"%s\"}\n",
               escaped(module).c_str(),escaped(mode).c_str(),rate,
               c.audio_input<0?"no_audio_input":"no_audio_output");
            return 0;
        }
        if(mode=="impulse")impulse(c,module,rate,block,out);
        else if(mode=="tail")tail(c,module,rate,block);
        else throw std::runtime_error("unknown probe mode");
        return 0;
    }catch(const std::exception& e) {
        std::fprintf(stderr,"R2 probe failure: %s\n",e.what());
        return 2;
    }
}
