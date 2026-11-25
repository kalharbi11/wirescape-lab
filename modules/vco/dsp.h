// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../port_state.h"
namespace ws2ports {
struct Vco {
    static constexpr ws::Info info{"essentials.vco","VCO",2};
    static constexpr std::array inputs{
        ws::port("pitch","Pitch",WS2_PITCH),ws::port("fm","FM Hz",WS2_AUDIO),
        ws::port("notes","Notes",WS2_EV_NOTES,WS2_POLY,0,nullptr,WS2_EVENT)};
    static constexpr std::array outputs{ws::port("audio","Audio",WS2_AUDIO)};
    static constexpr std::array params{ws::param("frequency","Frequency",.01f,20000,220,"Hz",WS2_MODULATABLE|WS2_PER_VOICE|WS2_AUDIO_RATE_OK|WS2_AUTOMATABLE)};
    // Double phase preserves accumulated precision and ABI1 reference math.
    std::array<double,16>phase{};std::array<float,16>note_frequency{};std::array<bool,16>note_active{};
    double state_rate=48000.;
    void prepare(const ws::Setup&s){state_rate=s.sample_rate();}void reset(){phase.fill(0);note_frequency.fill(0);note_active.fill(false);}
    int save_state(ws::Writer out)const{
        if(!out.u32(1)||!write_double(out,state_rate))return WS2_CAPACITY;
        for(size_t c=0;c<phase.size();++c)
            if(!write_double(out,phase[c])||!out.f32(note_frequency[c])||
               !out.u32(note_active[c]?1u:0u))return WS2_CAPACITY;
        return WS2_OK;
    }
    int load_state(ws::Reader in){
        uint32_t version;
        double saved_rate;
        if(!in.u32(version))return WS2_INVALID;
        if(version!=1)return WS2_UNSUPPORTED;
        if(!read_double(in,saved_rate)||saved_rate!=state_rate)return WS2_INVALID;
        decltype(phase) p{};decltype(note_frequency) f{};decltype(note_active) a{};
        constexpr double tau=6.283185307179586476925286766559;
        for(size_t c=0;c<p.size();++c){
            uint32_t active;
            if(!read_double(in,p[c])||p[c]<0.||p[c]>=tau||
               !in.f32(f[c])||!std::isfinite(f[c])||f[c]<0.f||
               !in.u32(active)||active>1)return WS2_INVALID;
            a[c]=active!=0;
        }
        phase=p;note_frequency=f;note_active=a;
        return WS2_OK;
    }
    void process(ws::Block&b){
        constexpr double tau=6.283185307179586476925286766559;
        b.out(0).set_channels(b.channels());b.out(0).mark_constant(false);
        b.split([&](uint32_t first,uint32_t end){
            for(uint32_t group=0;group<b.channels();group+=4)for(uint32_t c=group;c<std::min(group+4,b.channels());++c){
                auto pitch=b.in(0).ch(c),fm=b.in(1).ch(c),frequency=b.param(0).ch(c);auto*out=b.out(0).ch(c);
                for(uint32_t i=first;i<end;++i){
                    out[i]=static_cast<float>(std::sin(phase[c]));
                    double hz=b.in(0).connected()?261.6255653005986*std::pow(2.,pitch[i])*(frequency[i]/220.):note_active[c]?note_frequency[c]:frequency[i];
                    hz=std::clamp(hz+fm[i],0.,b.sample_rate()*.49);
                    phase[c]+=tau*hz/b.sample_rate();if(phase[c]>=tau)phase[c]-=tau;
                }
            }
        },[&](const ws2_event&e){uint32_t c=e.channel<0?0:static_cast<uint32_t>(e.channel);if(c>=b.channels())return;
            if(e.type==WS2_NOTE_ON){note_frequency[c]=static_cast<float>(440*std::pow(2.,(e.key-69.)/12.));note_active[c]=true;}
            // Clear the event pitch immediately, but keep the free-running phase continuous.
            else if(e.type==WS2_NOTE_CHOKE){note_active[c]=false;}
        });
    }
};
}
