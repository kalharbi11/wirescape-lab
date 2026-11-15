// SPDX-License-Identifier: GPL-3.0-only
// Wirescape ABI2 adapter. Does not contain or rewrite any GUTTUR DSP.
#pragma once
#include "wirescape_sdk.h"
#include "guttur/engine.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
namespace guttur::abi2 {
struct Module {
    static constexpr ws::Info info{"essentials.guttur", "GUTTUR", 1};
    static constexpr std::array inputs{ws::port("notes", "Notes", WS2_EV_NOTES, WS2_POLY, 0, nullptr, WS2_EVENT)};
    static constexpr std::array outputs{
       ws::port("left", "Left", WS2_AUDIO, WS2_POLY, 0, "stereo"),
       ws::port("right", "Right", WS2_AUDIO, WS2_POLY, 0, "stereo")};
    static constexpr std::array params{
      ws::param("pressure", "pressure", 0.0f, 1.0f, 0.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("breath", "breath", 0.0f, 1.0f, 0.12f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("whisper", "whisper", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("jitter", "jitter", 0.0f, 5.0f, 0.3f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("shimmer", "shimmer", 0.0f, 20.0f, 2.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("tremor", "tremor", 0.0f, 60.0f, 6.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("wander", "wander", 0.0f, 40.0f, 4.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("vibrato", "vibrato", 0.0f, 80.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("growl", "growl", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("creak", "creak", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("tail_fry", "tailFry", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("flutter", "flutter", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("rasp", "rasp", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("breaks", "breaks", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("size", "size", 13.0f, 20.5f, 17.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("pharynx", "pharynx", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("mouth", "mouth", 0.0f, 1.0f, 0.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("ring", "ring", 0.0f, 1.0f, 0.3f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("vowel", "vowel", 0.0f, 1.0f, 0.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("style", "style", 0.0f, 1.0f, 0.45f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("attack", "attack", 3.0f, 1200.0f, 60.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("release", "release", 20.0f, 2500.0f, 220.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("glide", "glide", 0.0f, 600.0f, 60.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("throats", "throats", 1.0f, 8.0f, 3.0f, "", WS2_STEPPED|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 1.0f),
      ws::param("looseness", "looseness", 0.0f, 1.0f, 0.35f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("spread", "spread", 0.0f, 1.0f, 0.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("size_spread", "sizeSpread", 0.0f, 1.0f, 0.4f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("distance", "distance", 0.0f, 1.0f, 0.15f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("azimuth", "azimuth", -180.0f, 180.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("room", "room", 0.0f, 1.0f, 0.5f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("decay", "decay", 0.3f, 7.0f, 1.8f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("wet", "wet", 0.0f, 1.0f, 0.28f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("drive", "drive", 0.0f, 1.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("body", "body", -12.0f, 6.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("air", "air", -6.0f, 9.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("level", "level", -24.0f, 6.0f, 0.0f, "", WS2_MODULATABLE|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 0.0f),
      ws::param("grit_after", "gritAfter", 0.0f, 1.0f, 0.0f, "", WS2_STEPPED|WS2_AUTOMATABLE, WS2_LINEAR, 0, 4, 1.0f),
    };
    guttur::Engine engine;
    struct Slot {uint32_t source=0;int32_t note_id=-1, channel=-1, key=0;int64_t handle=0;};
    std::array<Slot,guttur::kMaxNotes> identity{};
    uint64_t next=1;
    uint32_t max_block=0;
    static ws2_memory memory_requirements(const ws2_config& c){
      ws2_memory m{};m.struct_size=sizeof(m);m.alignment=32;
      // Prepared core includes LF tables, 4D tube grid, scratch, room and all 16 singers.
      m.large_bytes=guttur::requiredMemoryBytes()+64;
      (void)c;return m;
    }
    static void* allocate(void* ctx,size_t bytes,size_t align){
      const auto* setup=static_cast<const ws::Setup*>(ctx);
      return setup->alloc(bytes,align,WS2_LARGE);
    }
    bool prepare(const ws::Setup& s){
      max_block=s.max_block();
      return engine.prepare(s.sample_rate(),s.max_block(),s.config.seed,&Module::allocate,const_cast<ws::Setup*>(&s));
    }
    void reset(){engine.reset();identity={};next=1;}
    void update_params(ws::Block& b,uint32_t frame){
      // Host values are already clamped/tapered/modulated. Sample at the core's
      // absolute 128-frame control ticks, regardless of process callback size.
      for(uint32_t i=0;i<params.size();++i)engine.setParam(static_cast<guttur::Param>(i),b.param(i).value(0,frame));
    }
    void note_on(const ws2_event& e){
      Slot* free=nullptr;
      for(auto& s:identity)if(s.handle && s.source==e.source_id && s.note_id==e.note_id &&
           s.channel==e.channel && s.key==e.key){engine.noteOff(s.handle);s={};break;}
      for(auto& s:identity)if(!s.handle){free=&s;break;}
      if(!free)return; // Never overwrite identity without a matching release.
      const int64_t handle=static_cast<int64_t>(next++);
      if(engine.noteOn(handle,e.key,std::clamp(static_cast<double>(e.value),0.,1.)))
        *free={e.source_id,e.note_id,e.channel,e.key,handle};
    }
    void note_off(const ws2_event& e){
      for(auto& s:identity)if(s.handle && s.source==e.source_id && s.channel==e.channel && s.key==e.key &&
          (e.note_id<0 || s.note_id==e.note_id)){
        engine.noteOff(s.handle);s={};
        if(e.note_id<0)break; // anonymous ID: oldest matching slot
      }
    }
    void process(ws::Block& b){
      b.out(0).set_channels(1);b.out(1).set_channels(1);
      b.out(0).mark_constant(false);b.out(1).mark_constant(false);
      auto run=[&](uint32_t first,uint32_t end){
        while(first<end){
          const uint32_t tick=uint32_t(engine.samplePosition()%128);
          if(tick==0)update_params(b,first);
          const uint32_t n=std::min(end-first,128u-tick);
          engine.process(b.out(0).ch(0)+first,b.out(1).ch(0)+first,n);
          first+=n;
        }
      };
      b.split(run,[&](const ws2_event&e){
        if(engine.samplePosition()%128==0)update_params(b,e.offset);
        if(e.type==WS2_NOTE_ON)note_on(e);
        else if(e.type==WS2_NOTE_OFF||e.type==WS2_NOTE_CHOKE)note_off(e);
      });
    }
    uint32_t latency_frames()const{return engine.latencyFrames();}
    int save_state(ws::Writer w){
      std::array<uint8_t,guttur::Engine::stateBytes()>bytes{};
      if(engine.saveState(bytes.data(),bytes.size())!=bytes.size())return WS2_INVALID;
      return w.bytes(bytes.data(),static_cast<uint32_t>(bytes.size()))?WS2_OK:WS2_CAPACITY;
    }
    int load_state(ws::Reader r){
      std::array<uint8_t,guttur::Engine::stateBytes()>bytes{};
      if(!r.bytes(bytes.data(),static_cast<uint32_t>(bytes.size())))return WS2_INVALID;
      return engine.loadState(bytes.data(),bytes.size())?WS2_OK:WS2_UNSUPPORTED;
    }
};
}
