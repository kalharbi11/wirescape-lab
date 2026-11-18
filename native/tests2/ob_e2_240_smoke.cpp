// SPDX-License-Identifier: GPL-3.0-only
// #240 OB-e2: production engine, live catalogue, real two-second device-off smoke.
// No native module, sidecar, shared harness or build-system source modification.
#include "module_catalog.h"
#include "engine2.h"
#include "wirescape_sdk.h"
#include "allocation_watch.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using wirescape::engine2::Engine;
using wirescape::engine2::Config;
using wirescape::engine2::Timing;
using wirescape::engine2::Tap;
namespace {
constexpr uint32_t kNode=2;
constexpr uint32_t kSource=1;
constexpr double kPi=3.14159265358979323846;

void require(bool condition,const std::string &explanation) {
    if (!condition) throw std::runtime_error(explanation);
}
std::string quote(const std::string &s) {
    std::string out="\"";
    for(unsigned char c:s) {
        if(c=='\\'||c=='"') {out+='\\';out+=char(c);}
        else if(c=='\n')out+="\\n";
        else if(c=='\r')out+="\\r";
        else if(c=='\t')out+="\\t";
        else if(c<32)out+='?';
        else out+=char(c);
    }
    return out+"\"";
}
struct Stimulus {
    static constexpr ws::Info info{"test.ob_e2_240.stimulus","OB-e2 240 synthetic source",1};
    static constexpr std::array<ws2_port,0> inputs{};
    static constexpr std::array outputs{
        ws::port("audio","Audio",WS2_AUDIO),
        ws::port("pitch","Pitch",WS2_PITCH),
        ws::port("cv","CV",WS2_CV_BI),
        ws::port("unipolar","Unipolar",WS2_CV_UNI),
        ws::port("gate","Gate",WS2_GATE),
        ws::port("trigger","Trigger",WS2_TRIGGER)};
    static constexpr std::array<ws2_param,0> params{};
    double rate=48000;
    void prepare(const ws::Setup &s) {rate=s.sample_rate();}
    void reset() {}
    void process(ws::Block &b) {
        for(uint32_t o=0;o<outputs.size();++o) {
            b.out(o).set_channels(1);
            b.out(o).mark_constant(false);
        }
        const uint64_t period=std::max<uint64_t>(1,uint64_t(rate/4));
        for(uint32_t i=0;i<b.frames();++i) {
            uint64_t frame=b.frame_position()+i;
            double t=double(frame)/rate;
            b.out(0).ch(0)[i]=float(.25*std::sin(2*kPi*220*t));
            b.out(1).ch(0)[i]=.18f;
            b.out(2).ch(0)[i]=.26f;
            b.out(3).ch(0)[i]=.82f;
            b.out(4).ch(0)[i]=frame<uint64_t(rate*1.5)?1.f:0.f;
            b.out(5).ch(0)[i]=frame%period==0?1.f:0.f;
        }
    }
};
uint32_t source_port(uint32_t hint) {
    switch(hint){
    case WS2_AUDIO:return 0;
    case WS2_PITCH:return 1;
    case WS2_CV_BI:return 2;
    case WS2_CV_UNI:return 3;
    case WS2_GATE:return 4;
    case WS2_TRIGGER:return 5;
    default:return 0;
    }
}
ws2_event event(uint32_t type) {
    ws2_event e{};
    e.struct_size=sizeof(e);
    e.type=type;
    e.source_id=9;
    e.note_id=44;
    e.key=60;
    e.channel=0;
    e.value=.8f;
    return e;
}
std::vector<uint8_t> osc_packet() {
    std::vector<uint8_t> data;
    auto padded=[&](const char *s) {
        for(const char *p=s;*p;++p)data.push_back(uint8_t(*p));
        data.push_back(0);
        while(data.size()%4)data.push_back(0);
    };
    padded("/pico1/knob/1");
    padded(",f");
    for(uint32_t byte:{0x3fu,0x40u,0x00u,0x00u})data.push_back(uint8_t(byte));
    return data;
}
struct HostServices {
    wirescape::monitor::Tap monitor;
    wirescape::osc::OutBus osc_out;
    wirescape::monitor::Configuration monitor_cfg{};
    wirescape::osc::OutConfiguration osc_cfg{};
    HostServices() {
        monitor_cfg.tap=&monitor;
        osc_cfg.bus=&osc_out;
    }
    std::vector<uint8_t> config_for(const std::string &id) {
        const void *ptr=nullptr;
        size_t bytes=0;
        if(id=="monitor"){ptr=&monitor_cfg;bytes=sizeof(monitor_cfg);}
        if(id=="osc.out"){ptr=&osc_cfg;bytes=sizeof(osc_cfg);}
        if(!ptr)return {};
        const auto *p=static_cast<const uint8_t*>(ptr);
        return {p,p+bytes};
    }
};
struct Outcome {
    std::string id,status="fail",reason,event_check="none";
    uint32_t rate=0,block=0,params=0,signal_outputs=0,event_outputs=0;
    uint64_t frames=0,allocations=0,egress=0,telemetry=0,faults=0,changed_params=0;
    double peak=0,peak_audio=0;
};
void output_record(const Outcome &r) {
    std::cout<<"OBE2_ROW {\"id\":"<<quote(r.id)
             <<",\"rate_hz\":"<<r.rate
             <<",\"block\":"<<r.block
             <<",\"status\":"<<quote(r.status)
             <<",\"reason\":"<<quote(r.reason)
             <<",\"frames\":"<<r.frames
             <<",\"params\":"<<r.params
             <<",\"swept_params\":"<<r.changed_params
             <<",\"signal_outputs\":"<<r.signal_outputs
             <<",\"event_outputs\":"<<r.event_outputs
             <<",\"peak\":"<<r.peak
             <<",\"audio_peak\":"<<r.peak_audio
             <<",\"render_allocations\":"<<r.allocations
             <<",\"engine_faults\":"<<r.faults
             <<",\"egress_events\":"<<r.egress
             <<",\"event_tap_count\":"<<r.telemetry
             <<",\"named_check\":"<<quote(r.event_check)
             <<"}\n";
}
uint32_t first_signal(const ws2_descriptor *d) {
    for(uint32_t p=0;p<d->output_count;++p)
        if(d->outputs[p].kind==WS2_SIGNAL)return p;
    return UINT32_MAX;
}
bool is_named_event_case(const std::string &id) {
    return id=="midi.in"||id=="midi.cc_to_cv"||id=="midi.to_cv"||
           id=="essentials.chord"||id=="essentials.notes_to_cv"||
           id=="host.keyboard"||id=="monitor"||id=="osc.in"||id=="osc.out";
}
Outcome smoke(const std::string &id,const ws2_descriptor *d,uint32_t rate,uint32_t block) {
    Outcome result;
    result.id=id;result.rate=rate;result.block=block;
    if(!d){result.reason="missing actual production catalogue descriptor";return result;}
    result.params=d->param_count;
    for(uint32_t i=0;i<d->output_count;++i)
        (d->outputs[i].kind==WS2_SIGNAL?result.signal_outputs:result.event_outputs)++;
    try {
        HostServices host;
        Config cfg;
        cfg.sample_rate=rate;cfg.max_block=block;cfg.max_channels=16;
        cfg.seed=37;cfg.event_budget=4096;cfg.release_reserve=256;cfg.ring_capacity=1024;cfg.max_nodes=8;
        Engine engine(cfg);
        require(engine.add_node(kSource,ws::Module<Stimulus>::descriptor()),
                "failed to add deterministic production-engine stimulus: "+engine.error());
        require(engine.add_node(kNode,d,host.config_for(id)),
                "failed to add actual production module: "+engine.error());
        for(uint32_t p=0;p<d->input_count;++p)
            if(d->inputs[p].kind==WS2_SIGNAL)
                require(engine.connect(kSource,source_port(d->inputs[p].hint),kNode,p),
                        "failed to patch real module signal input "+std::string(d->inputs[p].id)+": "+engine.error());
        const uint32_t tap_output=first_signal(d);
        if(tap_output!=UINT32_MAX)
            require(engine.output(kNode,tap_output,0),"failed to tap target signal output");
        else
            require(engine.output(kSource,0,0),"event-only module has no signal bus for engine");
        std::vector<Tap> event_taps;
        for(uint32_t p=0;p<d->output_count;++p)
            if(d->outputs[p].kind==WS2_EVENT){
                Tap tap{};
                tap.kind=Tap::EventOut;tap.node=kNode;tap.index=p;
                event_taps.push_back(tap);
            }
        if(!event_taps.empty())
            require(engine.set_telemetry_taps(event_taps),"event output telemetry setup failed");
        const int producer=engine.register_producer();
        require(producer==0,"no real engine event producer");
        require(engine.prepare(),"actual production engine prepare failed: "+engine.error());
        // Defaults are observed over the first 0.5s. Sweep every actual
        // descriptor parameter through 0/25/50/75/100% of its PLAIN min-max
        // range at 0.5/0.75/1/1.25/1.5s, with no excluded parameters.
        for(uint32_t p=0;p<d->param_count;++p) {
            const auto &param=d->params[p];
            require(std::isfinite(param.minimum)&&std::isfinite(param.maximum)&&
                    param.minimum<=param.initial&&param.initial<=param.maximum,
                    "invalid live descriptor parameter bounds");
            for(uint32_t step=0;step<=4;++step) {
                ws2_event value=event(WS2_PARAM);
                value.index=p;
                value.value=std::clamp(float(double(param.minimum)+
                    (double(param.maximum)-double(param.minimum))*double(step)/4.0),
                    param.minimum,param.maximum);
                const uint64_t at=uint64_t(rate/2)+uint64_t(rate)*step/4u;
                require(engine.enqueue(uint32_t(producer),kNode,WS2_DIRECT_PORT,
                                       value,at,Timing::Frames)==WS2_OK,
                        "5-step min-max parameter sweep enqueue failed: "+
                        std::string(param.id));
            }
            ++result.changed_params;
        }
        // All device inputs are synthesized through the in-process engine.
        // Physical MIDI/OSC services, audio devices, sockets and LAN stay off.
        bool events_scheduled=false;
        for(uint32_t p=0;p<d->input_count;++p)if(d->inputs[p].kind==WS2_EVENT) {
            uint32_t hint=d->inputs[p].hint;
            ws2_event on=event(hint==WS2_EV_MIDI?WS2_MIDI:
                               hint==WS2_EV_MESSAGE?WS2_MESSAGE:WS2_NOTE_ON);
            if(on.type==WS2_MIDI){on.ump_words=1;on.ump[0]=id=="midi.cc_to_cv"?0x20b0017fu:0x20903c64u;}
            if(on.type==WS2_MESSAGE)continue; // device-free OSC direct ingress below
            require(engine.enqueue(uint32_t(producer),kNode,p,on,0,Timing::Frames)==WS2_OK,
                    "event input note/MIDI ingress failed");
            events_scheduled=true;
            ws2_event off=on;
            off.type=hint==WS2_EV_MIDI?WS2_MIDI:WS2_NOTE_OFF;
            if(off.type==WS2_MIDI)off.ump[0]=0x20803c00u;
            off.value=0;
            require(engine.enqueue(uint32_t(producer),kNode,p,off,rate+rate/2,Timing::Frames)==WS2_OK,
                    "event input release ingress failed");
        }
        if(id=="host.keyboard"||id=="midi.in"||id=="osc.in"||id=="monitor"){
            ws2_event on=event(id=="midi.in"?WS2_MIDI:id=="osc.in"?WS2_MESSAGE:WS2_NOTE_ON);
            std::vector<uint8_t> payload;
            if(on.type==WS2_MIDI){on.ump_words=1;on.ump[0]=0x20903c64u;}
            if(on.type==WS2_MESSAGE){payload=osc_packet();on.message_kind=WS2_MSG_OSC;
                on.data=payload.data();on.bytes=uint32_t(payload.size());}
            require(engine.enqueue(uint32_t(producer),kNode,WS2_DIRECT_PORT,on,0,Timing::Frames)==WS2_OK,
                    "synthetic direct host-event ingress failed");
            events_scheduled=true;
        }
        const uint64_t total=uint64_t(rate)*2;
        std::array<float,256> out{};
        float *bus[]={out.data()};
        uint64_t egress_note=0,egress_midi=0;
        double gate_peak=0,cc_peak=0,osc_peak=0;
        for(uint64_t position=0;position<total;) {
            const auto n=uint32_t(std::min<uint64_t>(block,total-position));
            uint64_t allocations=0;
            int code=WS2_OK;
            {
                allocation_watch::ThreadScope watch;
                code=engine.render(bus,1,n);
                allocations=watch.allocations();
            }
            result.allocations+=allocations;
            require(code==WS2_OK,"Engine::render returned failure");
            require(allocations==0,"process allocated heap memory during real Engine::render");
            require(engine.meter().faults==0,"Engine reported a module/finite output fault");
            for(uint32_t i=0;i<n;++i) {
                require(std::isfinite(out[i]),"nonfinite actual production bus sample");
                result.peak=std::max(result.peak,double(std::abs(out[i])));
            }
            for(uint32_t port=0;port<d->output_count;++port) {
                if(d->outputs[port].kind!=WS2_SIGNAL)continue;
                const uint32_t voices=engine.output_channels(kNode,port);
                require(voices<=16,"invalid real signal output channel count");
                for(uint32_t v=0;v<voices;++v)for(uint32_t i=0;i<n;++i) {
                    const float sample=engine.output_sample(kNode,port,v,i);
                    require(std::isfinite(sample),"nonfinite actual module signal output");
                    if(d->outputs[port].hint==WS2_AUDIO)
                        result.peak_audio=std::max(result.peak_audio,double(std::abs(sample)));
                    if(id=="midi.cc_to_cv")cc_peak=std::max(cc_peak,double(std::abs(sample)));
                    if(id=="midi.to_cv"||id=="essentials.notes_to_cv"||id=="host.keyboard")
                        if(std::strcmp(d->outputs[port].id,"gate")==0)
                            gate_peak=std::max(gate_peak,double(std::abs(sample)));
                    if(id=="osc.in")osc_peak=std::max(osc_peak,double(std::abs(sample)));
                }
            }
            wirescape::engine2::Outgoing outgoing{};
            while(engine.pop_egress(outgoing)){
                ++result.egress;
                if(outgoing.event.type==WS2_NOTE_ON)++egress_note;
                if(outgoing.event.type==WS2_MIDI)++egress_midi;
            }
            position+=n;
            result.frames+=n;
        }
        if(!event_taps.empty()) {
            std::vector<float> values(event_taps.size(),0.f);
            std::vector<uint32_t> counts(event_taps.size(),0);
            uint64_t frame=0;
            require(engine.read_telemetry(values.data(),counts.data(),uint32_t(counts.size()),frame)
                    ==counts.size()&&frame==total,"incomplete named event-output telemetry");
            for(auto count:counts)result.telemetry+=count;
        }
        bool audio=false;
        for(uint32_t p=0;p<d->output_count;++p)
            audio=audio||(d->outputs[p].kind==WS2_SIGNAL&&d->outputs[p].hint==WS2_AUDIO);
        if(audio)require(result.peak_audio>1e-6,
                         "audio-producing module remained silent with named patched signal/gate stimulus");
        if(id=="midi.in"){require(egress_midi>=1,"midi.in did not emit device-off MIDI passthrough");
            result.event_check="MIDI UMP event egress";}
        if(id=="essentials.chord"){require(egress_note>=1,"Chord notes did not emit");
            result.event_check="Chord note-on egress";}
        if(id=="monitor"){require(host.monitor.received.load()>0&&host.monitor.write.load()>0,
                                 "monitor synthetic event/row telemetry absent");
            result.event_check="monitor Tap received/write counters";}
        if(id=="osc.out"){require(host.osc_out.rows[0].blocks.load()>0,
                                 "OSC Out local bus rows were not processed");
            result.event_check="OSC Out in-memory OutBus rows only (no network)";}
        if(id=="osc.in"){require(osc_peak>1e-6,"OSC In direct encoded message did not reach CV row");
            result.event_check="OSC In direct synthetic OSC message/CV row (no socket)";}
        if(id=="midi.cc_to_cv"){require(cc_peak>1e-6,"CC-to-CV direct MIDI CC response absent");
            result.event_check="MIDI CC UMP-to-CV response";}
        if(id=="midi.to_cv"||id=="essentials.notes_to_cv"||id=="host.keyboard"){
            require(gate_peak>1e-6,"note ingress did not assert gate");
            result.event_check="note/MIDI ingress to gate output";}
        if(id=="sequencing.groove")result.event_check="internal clock/gate source and signal outputs";
        if(is_named_event_case(id)&&result.event_check=="none")
            throw std::runtime_error("named event-case lacks its explicit assertion");
        require(result.frames==total,"did not render exactly 2.000 s");
        require(result.changed_params==d->param_count,"did not sweep all descriptor parameters");
        result.faults=engine.meter().faults;
        result.status="pass";
        result.reason=audio?"finite non-silent real audio; no allocations; min/max sweep":
                          "finite real signal/event path; non-silence only applies to audio-output modules";
        (void)events_scheduled;
    } catch(const std::exception &e){
        result.status="fail";
        result.reason=e.what();
    }
    return result;
}
} // namespace
int main(int argc,char**argv) {
    std::setvbuf(stdout,nullptr,_IONBF,0);
    if(argc!=2){std::fprintf(stderr,"usage: ob_e2_240_smoke PALETTE_IDS.txt\n");return 2;}
    std::ifstream input(argv[1]);
    if(!input){std::fprintf(stderr,"cannot read current Studio palette ID manifest\n");return 2;}
    std::vector<std::string> palette;
    std::set<std::string> seen;
    std::string line;
    while(std::getline(input,line))if(!line.empty()){
        if(!seen.insert(line).second){std::fprintf(stderr,"duplicate palette ID: %s\n",line.c_str());return 2;}
        palette.push_back(line);
    }
    const auto &native=wirescape::app::builtin_modules();
    std::map<std::string,const ws2_descriptor*> by_id;
    for(const auto *d:native){
        if(!d||!d->id||!by_id.emplace(d->id,d).second){
            std::fprintf(stderr,"duplicate/null native production descriptor\n");
            return 2;
        }
    }
    std::fprintf(stderr,"OB-e2 live catalogue: palette=%zu, native=%zu, expected_snapshot=34\n",
                 palette.size(),by_id.size());
    // Do not silently accept changed palette membership or stale generated
    // catalogue; every missing case is emitted as a FAILED matrix row below.
    bool catalogue_ok=palette.size()==34&&by_id.size()==34;
    for(const auto&entry:by_id)
        if(!seen.count(entry.first)){
            catalogue_ok=false;
            std::fprintf(stderr,"OBE2_CATALOGUE_EXTRA %s\n",entry.first.c_str());
        }
    uint32_t passes=0,failures=0;
    for(const auto&id:palette) {
        const auto it=by_id.find(id);
        if(it==by_id.end())catalogue_ok=false;
        for(uint32_t rate:{44100u,48000u})for(uint32_t block:{64u,256u}) {
            const auto outcome=smoke(id,it==by_id.end()?nullptr:it->second,rate,block);
            output_record(outcome);
            if(outcome.status=="pass")++passes;else ++failures;
        }
    }
    std::cout<<"OBE2_TOTAL {\"palette_ids\":"<<palette.size()<<",\"native_ids\":"
             <<by_id.size()<<",\"expected_cases\":136,\"pass\":"<<passes
             <<",\"fail\":"<<failures
             <<",\"catalogue_match\":"<<(catalogue_ok?"true":"false")<<"}\n";
    return catalogue_ok&&failures==0&&passes==136?0:1;
}
