// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
namespace ws2ports {
struct Adsr {
    static constexpr ws::Info info{"essentials.adsr","ADSR",2};
    static constexpr std::array inputs{ws::port("gate","Gate",WS2_GATE),ws::port("notes","Notes",WS2_EV_NOTES,WS2_POLY,0,nullptr,WS2_EVENT)};
    static constexpr std::array outputs{ws::port("envelope","Envelope",WS2_CV_UNI)};
    static constexpr uint32_t flags=WS2_MODULATABLE|WS2_PER_VOICE|WS2_AUTOMATABLE;
    static constexpr std::array params{ws::param("attack","Attack",.0001f,30,.01f,"s",flags,WS2_LINEAR,0),ws::param("decay","Decay",.0001f,30,.1f,"s",flags,WS2_LINEAR,1),ws::param("sustain","Sustain",0,1,.7f,"",flags|WS2_AUDIO_RATE_OK,WS2_LINEAR,2),ws::param("release","Release",.0001f,30,.2f,"s",flags,WS2_LINEAR,3),
        ws::param("mode","Mode (Gate/Trigger)",0,1,0,"",WS2_STEPPED|WS2_AUTOMATABLE,WS2_LINEAR,4,4,1),
        ws::param("hold","Hold",0,30,0,"s",flags,WS2_LINEAR,5)};
    struct Voice {float level=0,start=0;uint64_t elapsed=0,duration=1,hold_left=0;int stage=0;bool gated=false,triggered=false;uint32_t source=0;int32_t note=0;ws::Schmitt edge;};
    std::array<Voice,16>voices{};
    bool trigger_mode_seen=false; // only the default Gate path uses original fast-loop
    void prepare(const ws::Setup&){}void reset(){for(auto&v:voices)v=Voice{};trigger_mode_seen=false;}
    void start(Voice&v,int stage,float seconds,double rate){v.stage=stage;v.start=v.level;v.elapsed=0;v.duration=std::max<uint64_t>(1,static_cast<uint64_t>(std::llround(seconds*rate)));}
    // CHOKE still invalidates the old note immediately; decay its residual
    // level over a fixed 5 ms instead of making a discontinuous CV step.
    // Reuse the normal Release stage, leaving the per-sample loop untouched.
    void choke(Voice&v,double rate){
        const float level=v.level;
        v=Voice{};
        if(level>0.f){v.level=level;start(v,4,.005f,rate);}
    }
    void process_default_gate(ws::Block&b){
        b.out(0).set_channels(b.channels());b.out(0).mark_constant(false);
        b.split([&](uint32_t first,uint32_t end){
            for(uint32_t group=0;group<b.channels();group+=4)for(uint32_t c=group;c<std::min(group+4,b.channels());++c){auto&v=voices[c];auto*out=b.out(0).ch(c);
                for(uint32_t i=first;i<end;++i){
                    if(b.in(0).connected()){
                        bool high=v.edge.process(b.in(0).value(c,i));
                        if(high&&!v.gated){v.gated=true;start(v,1,b.param(0).value(c,i),b.sample_rate());}
                        else if(!high&&v.gated){v.gated=false;start(v,4,b.param(3).value(c,i),b.sample_rate());}
                    }
                    float sustain=b.param(2).value(c,i);
                    if(v.stage==1){v.level=v.start+(1-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=1;start(v,2,b.param(1).value(c,i),b.sample_rate());}}
                    else if(v.stage==2){v.level=v.start+(sustain-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=sustain;v.stage=3;}}
                    else if(v.stage==3)v.level=sustain;
                    else if(v.stage==4){v.level=v.start*(1-static_cast<float>(++v.elapsed)/static_cast<float>(v.duration));if(v.elapsed>=v.duration){v.level=0;v.stage=0;}}
                    out[i]=v.level;
                }
            }
        },[&](const ws2_event&e){
            uint32_t c=e.channel<0?0:static_cast<uint32_t>(e.channel);if(c>=b.channels()||b.in(0).connected())return;
            auto&v=voices[c];uint32_t at=std::min(e.offset,b.frames()-1);
            if(e.type==WS2_NOTE_ON){v.source=e.source_id;v.note=e.note_id;v.gated=true;start(v,1,b.param(0).value(c,at),b.sample_rate());}
            else if((e.type==WS2_NOTE_OFF||e.type==WS2_NOTE_CHOKE)&&v.source==e.source_id&&v.note==e.note_id){if(e.type==WS2_NOTE_CHOKE)choke(v,b.sample_rate());else if(v.gated){v.gated=false;start(v,4,b.param(3).value(c,at),b.sample_rate());}}
        });
    }
    void process(ws::Block&b){
        // For the default constant mode, run exactly the pre-OB Gate engine.
        // There is no extra branch in its per-voice hot loop.
        if(!trigger_mode_seen && b.param(4).constant() && b.param(4).channels()==1 &&
           b.param(4).value(0,0)<=.5f){process_default_gate(b);return;}
        b.out(0).set_channels(b.channels());b.out(0).mark_constant(false);
        b.split([&](uint32_t first,uint32_t end){
            for(uint32_t group=0;group<b.channels();group+=4)for(uint32_t c=group;c<std::min(group+4,b.channels());++c){auto&v=voices[c];auto*out=b.out(0).ch(c);
                // Use the exact pre-OB Gate loop for the default constant mode.
                // Its hot path keeps the M1 instruction footprint and float order;
                // Trigger/retrigger and automated mode changes take the general path.
                const bool original_gate = !v.triggered && b.param(4).constant() &&
                                           b.param(4).value(c,first) <= .5f;
                if (original_gate) {
                for(uint32_t i=first;i<end;++i){
                    if(b.in(0).connected()){
                        bool high=v.edge.process(b.in(0).value(c,i));
                        if(high&&!v.gated){v.gated=true;start(v,1,b.param(0).value(c,i),b.sample_rate());}
                        else if(!high&&v.gated){v.gated=false;start(v,4,b.param(3).value(c,i),b.sample_rate());}
                    }
                    float sustain=b.param(2).value(c,i);
                    if(v.stage==1){v.level=v.start+(1-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=1;start(v,2,b.param(1).value(c,i),b.sample_rate());}}
                    else if(v.stage==2){v.level=v.start+(sustain-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=sustain;v.stage=3;}}
                    else if(v.stage==3)v.level=sustain;
                    else if(v.stage==4){v.level=v.start*(1-static_cast<float>(++v.elapsed)/static_cast<float>(v.duration));if(v.elapsed>=v.duration){v.level=0;v.stage=0;}}
                    out[i]=v.level;
                }
                } else {
                for(uint32_t i=first;i<end;++i){
                    if(b.in(0).connected()){
                        bool high=v.edge.process(b.in(0).value(c,i));
                        if(high&&!v.gated){v.gated=true;v.triggered=b.param(4).value(c,i)>.5f;trigger_mode_seen |= v.triggered;start(v,1,b.param(0).value(c,i),b.sample_rate());}
                        else if(!high&&v.gated){v.gated=false;if(!v.triggered)start(v,4,b.param(3).value(c,i),b.sample_rate());}
                    }
                    float sustain=b.param(2).value(c,i);
                    if(v.stage==1){v.level=v.start+(1-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=1;start(v,2,b.param(1).value(c,i),b.sample_rate());}}
                    else if(v.stage==2){v.level=v.start+(sustain-v.start)*static_cast<float>(++v.elapsed)/static_cast<float>(v.duration);if(v.elapsed>=v.duration){v.level=sustain;if(v.triggered){
                            v.hold_left=static_cast<uint64_t>(std::llround(std::clamp(b.param(5).value(c,i),0.f,30.f)*b.sample_rate()));
                            if(v.hold_left==0)start(v,4,b.param(3).value(c,i),b.sample_rate());
                            else v.stage=3;
                        }else v.stage=3;}}
                    else if(v.stage==3){v.level=sustain;if(v.triggered&&v.hold_left&&--v.hold_left==0)
                        start(v,4,b.param(3).value(c,i),b.sample_rate());}
                    else if(v.stage==4){v.level=v.start*(1-static_cast<float>(++v.elapsed)/static_cast<float>(v.duration));if(v.elapsed>=v.duration){v.level=0;v.stage=0;}}
                    out[i]=v.level;
                }
                }
            }
        },[&](const ws2_event&e){
            uint32_t c=e.channel<0?0:static_cast<uint32_t>(e.channel);if(c>=b.channels()||b.in(0).connected())return;
            auto&v=voices[c];uint32_t at=std::min(e.offset,b.frames()-1);
            if(e.type==WS2_NOTE_ON){v.source=e.source_id;v.note=e.note_id;v.gated=true;v.triggered=b.param(4).value(c,at)>.5f;trigger_mode_seen |= v.triggered;start(v,1,b.param(0).value(c,at),b.sample_rate());}
            else if((e.type==WS2_NOTE_OFF||e.type==WS2_NOTE_CHOKE)&&v.source==e.source_id&&v.note==e.note_id){if(e.type==WS2_NOTE_CHOKE)choke(v,b.sample_rate());else if(v.gated){v.gated=false;if(!v.triggered)start(v,4,b.param(3).value(c,at),b.sample_rate());}}
        });
    }
};
}
