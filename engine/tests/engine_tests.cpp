// SPDX-License-Identifier: GPL-3.0-only
#include "../../modules/lfo/dsp.h"
#include "../../modules/vco/dsp.h"
#include "../../tests/native/abi2/allocation_watch.h"
#include "../../tests/native/abi2/test_modules.h"
#include "engine2.h"
#include "types.h"
#include "layout.h"
#include "publication.h"
#include <type_traits>
#include "wirescape_sdk.h"
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>
#if defined(_MSC_VER)&&defined(_DEBUG)
#include <crtdbg.h>
#endif
using namespace wirescape::engine2;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"engine2 check line %d: %s\n",__LINE__,#x);std::abort();}}while(0)
struct Source {
 static constexpr ws::Info info{"test.source","Source",1};
 static constexpr std::array<ws2_port,0>inputs{};
 static constexpr std::array outputs{ws::port("out","Out",WS2_CV_BI)};
 static constexpr std::array params{ws::param("value","Value",-1,1,1)};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(b.channels());b.out(0).mark_constant(b.param(0).constant());for(uint32_t c=0;c<b.channels();++c)for(uint32_t i=0;i<(b.param(0).constant()?1u:b.frames());++i)b.out(0).ch(c)[i]=b.param(0).value(c,i)+.1f*c;}
};
template<int Policy>struct Pass {
 static constexpr ws::Info info{"test.pass","Pass",1};
 static constexpr std::array inputs{ws::port("in","In",WS2_AUDIO,Policy,.25f)};
 static constexpr std::array outputs{ws::port("out","Out",WS2_AUDIO)};
 static constexpr std::array params{ws::param("gain","Gain",0,1,1)};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(b.channels());bool constant=b.in(0).constant()&&b.param(0).constant();b.out(0).mark_constant(constant);for(uint32_t c=0;c<b.channels();++c)for(uint32_t i=0;i<(constant?1u:b.frames());++i)b.out(0).ch(c)[i]=b.in(0).value(c,i)*b.param(0).value(c,i);}
};
struct NonfiniteSource:Source {
 void process(ws::Block&b){Source::process(b);b.out(0).ch(0)[0]=std::nanf("");}
};
static void producer_validation(){
 Engine e;CHECK(e.add_node(1,ws::Module<NonfiniteSource>::descriptor()));CHECK(e.add_node(2,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(e.connect(1,0,2,0));CHECK(e.prepare());
 float out[256]{};float*outputs[]={out};CHECK(e.render(outputs,1,256)==WS2_OK);CHECK(e.meter().faults==1);CHECK(e.output_constant(1,0));CHECK(e.output_sample(1,0,0,0)==0);CHECK(e.output_sample(2,0,0,0)==0);
 float finite[]={0.f,-0.f,1.f,-2.f,3.e38f};CHECK(ws::finite_samples(finite,5));
 finite[4]=std::nanf("");CHECK(!ws::finite_samples(finite,5));finite[4]=INFINITY;CHECK(!ws::finite_samples(finite,5));
 // 1 and 2 are finite although their exponent bits OR to the Inf/NaN pattern.
 CHECK(ws::finite_samples(nullptr,0));
 std::array<float,258>samples{};
 for(uint32_t shift:{0u,1u})for(uint32_t count:{1u,2u,3u,4u,7u,17u,256u,257u}){
  for(uint32_t i=0;i<count;++i)samples[shift+i]=(i&1)?2.f:1.f;
  CHECK(ws::finite_samples(samples.data()+shift,count));
  for(float invalid:{std::nanf(""),INFINITY,-INFINITY})for(uint32_t index:{0u,count/2,count-1}){
   const float saved=samples[shift+index];samples[shift+index]=invalid;
   CHECK(!ws::finite_samples(samples.data()+shift,count));samples[shift+index]=saved;
  }
 }

}
struct AddressSource:Source {
 static inline const float*written=nullptr;
 void process(ws::Block&b){written=b.out(0).ch(0);Source::process(b);}
};
template<int Policy>struct AddressPass:Pass<Policy> {
 static inline const float*read=nullptr;
 void process(ws::Block&b){read=b.in(0).ch(0).p;Pass<Policy>::process(b);}
};
static void zero_copy(){
 for(uint32_t channels:{1u,4u}){
  Engine e;CHECK(e.add_node(1,ws::Module<AddressSource>::descriptor()));CHECK(e.add_node(2,ws::Module<AddressPass<WS2_POLY>>::descriptor()));CHECK(e.add_node(3,ws::Module<AddressPass<WS2_SUM>>::descriptor()));CHECK(e.set_channels(1,channels));CHECK(e.connect(1,0,2,0));CHECK(e.connect(1,0,3,0));CHECK(e.prepare());
  float out[17]{};float*outputs[]={out};CHECK(e.render(outputs,1,17)==WS2_OK);
  CHECK(AddressSource::written==AddressPass<WS2_POLY>::read);
  CHECK((AddressSource::written==AddressPass<WS2_SUM>::read)==(channels==1));
  CHECK(e.output_sample(2,0,channels-1,0)==1.f+.1f*(channels-1));
 }
}
struct Feedback {
 static constexpr ws::Info info{"test.feedback","Feedback",1};
 static constexpr std::array inputs{ws::port("in","In")};
 static constexpr std::array outputs{ws::port("out","Out")};
 static constexpr std::array<ws2_param,0>params{};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(1);b.out(0).mark_constant(false);for(uint32_t i=0;i<b.frames();++i)b.out(0).ch(0)[i]=.5f*b.in(0).value(0,i)+(b.frame_position()+i==0?1.f:0.f);}
};
struct Reporter {
 static constexpr ws::Info info{"test.reporter","Reporter",1};
 static constexpr std::array inputs{ws::port("in","In")};
 static constexpr std::array outputs{ws::port("out","Out")};
 static constexpr std::array<ws2_param,0>params{};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(1);b.out(0).mark_constant();b.out(0).ch(0)[0]=static_cast<float>(b.frames());}
};
struct Receiver {
 static constexpr ws::Info info{"test.receiver","Receiver",1};
 static constexpr std::array inputs{ws::port("events","Events",WS2_EV_NOTES,WS2_POLY,0,nullptr,WS2_EVENT)};
 static constexpr std::array outputs{ws::port("out","Out")};
 static constexpr std::array params{ws::param("gain","Gain",0,1,1)};
 float held=0;
 void prepare(const ws::Setup&){}void reset(){held=0;}
 void process(ws::Block&b){b.out(0).set_channels(1);b.out(0).mark_constant(false);b.split([&](uint32_t a,uint32_t z){for(uint32_t i=a;i<z;++i)b.out(0).ch(0)[i]=held*b.param(0).value(0,i);},[&](const ws2_event&e){if(e.type==WS2_NOTE_ON)held=e.value;else if(e.type==WS2_NOTE_OFF||e.type==WS2_NOTE_CHOKE)held=0;});}
};
struct Echo {
 static constexpr ws::Info info{"test.echo","Echo",1};
 static constexpr std::array inputs{ws::port("events","Events",WS2_EV_MESSAGE,WS2_POLY,0,nullptr,WS2_EVENT)};
 static constexpr std::array outputs{ws::port("events","Events",WS2_EV_MESSAGE,WS2_POLY,0,nullptr,WS2_EVENT)};
 static constexpr std::array<ws2_param,0>params{};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(0);for(auto&e:b.events())b.emit(0,e);}
};
struct BadEmitter:Echo {
 void process(ws::Block&b){b.out(0).set_channels(0);auto e=ws2_event{};e.struct_size=sizeof(e);e.type=WS2_NOTE_ON;e.value2=std::nanf("");CHECK(!b.emit(0,e));e.value2=0;e.ump_words=5;CHECK(!b.emit(0,e));}
};
static void invalid_events(){
 Engine e;CHECK(e.add_node(1,ws::Module<BadEmitter>::descriptor()));CHECK(e.register_producer()==0);CHECK(e.prepare());
 auto bad=ws2_event{};bad.struct_size=sizeof(bad);bad.type=WS2_NOTE_ON;bad.value2=std::nanf("");CHECK(e.enqueue(0,1,0,bad,0)==WS2_INVALID);bad.value2=0;bad.ump_words=5;CHECK(e.enqueue(0,1,0,bad,0)==WS2_INVALID);
 float out[17]{};float*outputs[]={out};CHECK(e.render(outputs,1,17)==WS2_OK);Outgoing outgoing;CHECK(!e.pop_egress(outgoing));CHECK(e.meter().events==0);
}
struct ParamProbe {
 static constexpr ws::Info info{"test.param","Parameter",1};
 static constexpr std::array<ws2_port,0>inputs{};
 static constexpr std::array outputs{ws::port("out","Out")};
 static constexpr std::array params{ws::param("value","Value",1,100,10,"",WS2_MODULATABLE|WS2_PER_VOICE,WS2_LOG)};
 void prepare(const ws::Setup&){}void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(b.channels());b.out(0).mark_constant(b.param(0).constant());for(uint32_t c=0;c<b.channels();++c)for(uint32_t i=0;i<(b.param(0).constant()?1u:b.frames());++i)b.out(0).ch(c)[i]=b.param(0).value(c,i);}
};
template<uint32_t Taper>struct CachedTaperProbe:ParamProbe {
 static constexpr std::array params{ws::param("value","Value",1,100,10,"",WS2_MODULATABLE,Taper)};
};
template<uint32_t Taper>static void cached_taper(){
 Engine e;CHECK(e.add_node(1,ws::Module<Source>::descriptor()));CHECK(e.add_node(2,ws::Module<CachedTaperProbe<Taper>>::descriptor()));CHECK(e.modulate(1,0,2,0,.125f));CHECK(e.prepare());
 float out[256]{};float*outputs[]={out};CHECK(e.render(outputs,1,256)==WS2_OK);
 const auto&p=CachedTaperProbe<Taper>::params[0];float expected=static_cast<float>(ws::to_plain(p,ws::to_normal(p,p.initial)+.125f));
 CHECK(e.output_sample(2,0,0,0)==expected);
}
struct LatencyProbe:Pass<WS2_POLY>{uint32_t latency_frames()const{return 7;}};
static ws2_event event(uint32_t type,float value=1,uint32_t index=0){ws2_event e{};e.struct_size=sizeof(e);e.type=type;e.value=value;e.index=index;e.note_id=1;e.channel=0;e.key=60;e.source_id=1;return e;}
static void render(Engine&e,uint32_t frames=256){std::array<float,4096>a{},b{};float*out[]={a.data(),b.data()};CHECK(e.render(out,2,frames)==WS2_OK);}
static void replan_test(Engine &live, Engine &candidate, uint64_t timeout_ns = 16000000) {
    std::atomic<bool> done{false};
    bool accepted = false;
    std::thread control([&] {
        accepted = live.replan(candidate, timeout_ns);
        done.store(true, std::memory_order_release);
    });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
    do { render(live, 16); std::this_thread::yield(); }
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline);
    control.join();
    CHECK(accepted);
}
static Config cfg(){Config c;c.ring_capacity=256;c.future_capacity=1024;return c;}
static void signals(){
 Engine e(cfg());CHECK(e.add_node(1,ws::Module<Source>::descriptor()));CHECK(e.add_node(2,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(e.add_node(3,ws::Module<Pass<WS2_SUM>>::descriptor()));CHECK(e.add_node(4,ws::Module<Pass<WS2_FIRST>>::descriptor()));
 CHECK(e.connect(1,0,2,0));CHECK(e.connect(1,0,3,0));CHECK(e.connect(1,0,4,0));CHECK(e.set_channels(1,4));CHECK(e.output(2,0,0));CHECK(e.output(2,0,1));CHECK(e.prepare());render(e);
 CHECK(e.output_channels(2,0)==4);CHECK(e.output_channels(3,0)==1);CHECK(std::abs(e.output_sample(3,0,0,0)-4.6f)<1e-6);CHECK(e.output_sample(4,0,0,0)==1);CHECK(e.output_constant(2,0));
 {allocation_watch::Scope watch;for(uint32_t n:{1u,16u,3u}){CHECK(e.set_channels(1,n));render(e,17);CHECK(e.output_channels(2,0)==n);}e.reset();CHECK(watch.allocations()==0);}
 CHECK(e.set_channels(1,0));render(e,1);CHECK(e.output_sample(2,0,0,0)==.25f);
}
static std::vector<float>loop(uint32_t delay,bool reverse){Config c=cfg();c.max_block=128;c.feedback_block=delay;Engine e(c);
 if(reverse){CHECK(e.add_node(2,ws::Module<Reporter>::descriptor()));CHECK(e.add_node(1,ws::Module<Feedback>::descriptor()));}
 else{CHECK(e.add_node(1,ws::Module<Feedback>::descriptor()));CHECK(e.add_node(2,ws::Module<Reporter>::descriptor()));}
 CHECK(e.connect(1,0,1,0));CHECK(e.connect(1,0,2,0));CHECK(e.output(1,0,0));CHECK(e.prepare());CHECK(e.feedback_edges()==1);
 std::vector<float>result(256);std::array<float,128>right{};
 for(uint32_t off=0;off<256;off+=128){float*out[]={result.data()+off,right.data()};CHECK(e.render(out,2,128)==WS2_OK);CHECK(e.output_sample(2,0,0,0)==128);}
 for(uint32_t i=0;i<256;++i){float expected=i%delay?0.f:std::ldexp(1.f,-static_cast<int>(i/delay));if(std::fpclassify(expected)==FP_SUBNORMAL)expected=0;CHECK(result[i]==expected);}return result;}
static void events(){
 Engine e(cfg());for(uint32_t i=1;i<=3;++i)CHECK(e.add_node(i,ws::Module<Echo>::descriptor()));CHECK(e.add_node(4,ws::Module<Receiver>::descriptor()));
 for(uint32_t i=1;i<=3;++i)CHECK(e.connect(i,0,4,0));for(int i=0;i<3;++i)CHECK(e.register_producer()==i);CHECK(e.prepare());
 for(uint32_t p=0;p<3;++p){auto n=event(WS2_NOTE_ON,.1f*(p+1));CHECK(e.enqueue(p,p+1,0,n,5)==WS2_OK);}
 render(e,17);CHECK(e.output_sample(4,0,0,4)==0);CHECK(std::abs(e.output_sample(4,0,0,5)-.3f)<1e-6);
 Outgoing out;uint32_t count=0;while(e.pop_egress(out)){CHECK(out.frame==5);++count;}CHECK(count==3);
 auto gen=e.meter().generation;e.panic();CHECK(e.meter().applied_generation==gen);CHECK(e.enqueue(0,1,0,event(WS2_NOTE_ON),20)==WS2_STATE);render(e,17);CHECK(e.meter().generation==e.meter().applied_generation);CHECK(e.output_sample(4,0,0,0)==0);
 CHECK(e.enqueue(0,1,0,event(WS2_NOTE_ON),40,Timing::Frames,gen)==WS2_STATE);
}
static void timing(){
 Config c=cfg();c.max_block=16;c.feedback_block=16;c.epoch_ns=1000000000;
 Engine e(c);CHECK(e.add_node(1,ws::Module<Receiver>::descriptor()));CHECK(e.register_producer()==0);CHECK(e.prepare());
 CHECK(e.publish_clock(0,c.epoch_ns));CHECK(!e.publish_clock(0,c.epoch_ns-1));
 CHECK(e.enqueue(0,1,0,event(WS2_NOTE_ON,.4f),1001000000,Timing::Timestamped)==WS2_OK);
 for(int i=0;i<4;++i){render(e,16);CHECK(e.output_sample(1,0,0,0)==0);}render(e,16);CHECK(e.output_sample(1,0,0,0)==.4f);
 CHECK(e.enqueue(0,1,0,event(WS2_NOTE_OFF),0,Timing::Immediate)==WS2_OK);render(e,16);CHECK(e.output_sample(1,0,0,0)==0);
}
static void overflow(){
 Config c=cfg();c.event_budget=8;c.release_reserve=2;c.ring_capacity=32;c.future_capacity=128;Engine e(c);
 CHECK(e.add_node(1,ws::Module<Receiver>::descriptor()));CHECK(e.register_producer()==0);CHECK(e.prepare());CHECK(e.enqueue(0,1,0,event(WS2_NOTE_ON),0)==WS2_OK);render(e,17);
 for(int i=0;i<20;++i)CHECK(e.enqueue(0,1,WS2_DIRECT_PORT,event(WS2_PARAM,float(i)/20),17)==WS2_OK);
 CHECK(e.enqueue(0,1,0,event(WS2_NOTE_OFF),17)==WS2_OK);render(e,17);CHECK(e.output_sample(1,0,0,0)==0);CHECK(e.meter().coalesced>0);CHECK(e.meter().release_emergencies==0);
 for(int i=0;i<12;++i)CHECK(e.enqueue(0,1,0,event(WS2_NOTE_OFF),34)==WS2_OK);render(e,17);CHECK(e.meter().release_emergencies==1);CHECK(e.meter().generation==e.meter().applied_generation);
 Config small=cfg();small.message_arena_bytes=8;Engine arena(small);CHECK(arena.add_node(1,ws::Module<Echo>::descriptor()));CHECK(arena.register_producer()==0);CHECK(arena.prepare());
 uint8_t bytes[16]{};auto message=event(WS2_MESSAGE);message.bytes=16;message.data=bytes;CHECK(arena.enqueue(0,1,0,message,0)==WS2_OK);render(arena);CHECK(arena.meter().arena_full==1);
}
static void rows(){
 Engine e(cfg());CHECK(e.add_node(1,ws::Module<ws2test::Rows>::descriptor(),{3}));CHECK(e.add_node(2,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(e.add_node(3,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(e.connect(1,0,2,0));CHECK(e.connect(1,2,3,0));CHECK(e.prepare());
 auto saved=e.save_state(1);CHECK(saved.size()==20);CHECK(e.load_state(1,saved)==WS2_OK);CHECK(e.save_state(1)==saved);
 auto future=saved;future[0]=9;CHECK(e.load_state(1,future)==WS2_UNSUPPORTED);CHECK(e.preserved_state(1)==future);CHECK(e.save_state(1)==future);CHECK(e.load_state(1,saved)==WS2_OK);
 Engine candidate(cfg());CHECK(candidate.add_node(1,ws::Module<ws2test::Rows>::descriptor(),{2}));CHECK(candidate.add_node(2,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(candidate.add_node(3,ws::Module<Pass<WS2_POLY>>::descriptor()));CHECK(candidate.connect(1,0,2,0));CHECK(!candidate.connect(1,2,3,0));CHECK(candidate.prepare());
 replan_test(e,candidate);for(int i=0;i<5;++i)render(e,256);render(e,17);CHECK(std::abs(e.output_sample(2,0,0,0)-.1f)<1e-6);CHECK(e.output_sample(3,0,0,0)==.25f);
}
static void producer_stress(){
 Config c=cfg();c.max_block=48;c.feedback_block=32;c.ring_capacity=1024;Engine e(c);CHECK(e.add_node(1,ws::Module<Receiver>::descriptor()));for(int i=0;i<3;++i)e.register_producer();CHECK(e.prepare());
 {allocation_watch::Scope watch;for(uint64_t block=0;block<10000;++block){for(uint32_t i=0;i<10;++i)CHECK(e.enqueue(i%3,1,WS2_DIRECT_PORT,event(WS2_PARAM,float(i)/10),block*48+i*4)==WS2_OK);render(e,48);}CHECK(watch.allocations()==0);}
 CHECK(e.meter().events==100000);CHECK(e.meter().faults==0);
 // Actual producer threads are joined before final drain/render/destruction.
 std::array<std::thread,3>threads;for(uint32_t p=0;p<3;++p)threads[p]=std::thread([&,p](){for(int i=0;i<100;++i)CHECK(e.enqueue(p,1,WS2_DIRECT_PORT,event(WS2_PARAM,.5f),0,Timing::Immediate)==WS2_OK);});
 for(auto&t:threads)t.join();render(e,48);CHECK(e.meter().faults==0);
 // Concurrent producer/render ownership, bounded batches avoid overload.
 std::atomic<int>done{0};for(uint32_t p=0;p<3;++p)threads[p]=std::thread([&,p](){for(int i=0;i<100;++i)CHECK(e.enqueue(p,1,WS2_DIRECT_PORT,event(WS2_PARAM,.5f),0,Timing::Immediate)==WS2_OK);++done;});
 while(done.load()!=3){render(e,48);std::this_thread::yield();}for(auto&t:threads)t.join();render(e,48);CHECK(e.meter().faults==0);
}
struct GlobalParamProbe:ParamProbe {
 static constexpr std::array params{ws::param("value","Value",1,100,10,"",WS2_MODULATABLE,WS2_LOG)};
 void process(ws::Block&b){CHECK(b.param(0).channels()==1);ParamProbe::process(b);}
};
static void parameter_channels(){
 Engine e;CHECK(e.add_node(1,ws::Module<ws2ports::Lfo>::descriptor()));CHECK(e.add_node(2,ws::Module<GlobalParamProbe>::descriptor()));CHECK(e.add_node(3,ws::Module<ParamProbe>::descriptor()));CHECK(e.set_channels(1,4));CHECK(e.modulate(1,0,2,0,.25f));CHECK(e.modulate(1,0,3,0,.25f));CHECK(e.register_producer()==0);CHECK(e.prepare());
 auto offset=event(WS2_PARAM_MOD,.2f);offset.channel=1;CHECK(e.enqueue(0,1,WS2_DIRECT_PORT,offset,0)==WS2_OK);render(e);
 CHECK(e.output_channels(2,0)==1);CHECK(e.output_channels(3,0)==4);CHECK(e.output_sample(3,0,0,17)!=e.output_sample(3,0,1,17));
 for(uint32_t i=0;i<256;++i){float expected=static_cast<float>(ws::to_plain(GlobalParamProbe::params[0],.5+double(.25f*e.output_sample(1,0,0,i))));CHECK(e.output_sample(2,0,0,i)==expected);}
}
static void modulation_spans(){
 Engine e;CHECK(e.add_node(1,ws::Module<ws2ports::Lfo>::descriptor()));CHECK(e.add_node(2,ws::Module<Source>::descriptor()));CHECK(e.add_node(3,ws::Module<ParamProbe>::descriptor()));CHECK(e.modulate(1,0,3,0,.2f));CHECK(e.modulate(2,0,3,0,.125f));CHECK(e.prepare());
 for(uint32_t frames:{1u,17u,256u}){render(e,frames);for(uint32_t i=0;i<frames;++i){
  double sum=double(.2f*e.output_sample(1,0,0,i))+double(.125f*e.output_sample(2,0,0,i));
  float expected=static_cast<float>(ws::to_plain(ParamProbe::params[0],.5+sum));CHECK(e.output_sample(3,0,0,i)==expected);
 }}
}
static void telemetry(){
  const Tap param{Tap::Param,2,0}, output_max{Tap::Output,1,0}, output_first{Tap::Output,1,0,Tap::First};
  const Tap events_out{Tap::EventOut,3,0};
  Config c=cfg();c.max_taps=4;
  Engine e(c);
  CHECK(e.add_node(1,ws::Module<Source>::descriptor()));
  CHECK(e.add_node(2,ws::Module<ParamProbe>::descriptor()));
  CHECK(e.add_node(3,ws::Module<Echo>::descriptor()));
  CHECK(e.set_channels(1,4));CHECK(e.set_parameter(1,0,.2f));
  CHECK(e.modulate(1,0,2,0,.25f));
  CHECK(!e.set_telemetry_taps({Tap{Tap::Param,99,0}}));
  CHECK(!e.set_telemetry_taps({Tap{Tap::Param,2,1}}));
  CHECK(!e.set_telemetry_taps({Tap{Tap::EventOut,1,0}}));
  CHECK(!e.set_telemetry_taps({Tap{Tap::Output,3,0}}));
  CHECK(!e.set_telemetry_taps({Tap{static_cast<Tap::Kind>(99),2,0}}));
  CHECK(!e.set_telemetry_taps({param,param}));
  CHECK(!e.set_telemetry_taps({param,output_max,output_first,events_out,events_out}));
  CHECK(e.set_telemetry_taps({param,output_max,events_out}));
  CHECK(e.register_producer()==0);CHECK(e.prepare());
  CHECK(!e.set_telemetry_taps({}));
  float values[4]{};uint32_t counts[4]{};uint64_t frame=999;
  CHECK(e.read_telemetry(values,counts,2,frame)==0&&frame==0);
  {allocation_watch::Scope watch;render(e,17);CHECK(watch.allocations()==0);}
  CHECK(e.read_telemetry(values,counts,4,frame)==3&&frame==17);
  CHECK(values[0]==e.output_sample(2,0,0,16));
  CHECK(values[0]>10.f); // A modulated plain-unit value, not normalized/base.
  CHECK(values[1]==e.output_sample(1,0,3,16)); // Loudest of four source channels.
  CHECK(counts[2]==0);
  for(uint32_t i=0;i<5;++i)CHECK(e.enqueue(0,3,0,event(WS2_NOTE_ON),17+i)==WS2_OK);
  render(e,17);
  CHECK(e.read_telemetry(values,counts,4,frame)==3&&frame==34&&counts[2]==5);
  render(e,17);
  CHECK(e.read_telemetry(values,counts,4,frame)==3&&counts[2]==5);
  Engine first(c);CHECK(first.add_node(1,ws::Module<Source>::descriptor()));CHECK(first.set_channels(1,4));
  CHECK(first.set_parameter(1,0,.2f));CHECK(first.set_telemetry_taps({output_first}));
  CHECK(first.prepare());render(first,1);
  CHECK(first.read_telemetry(values,counts,4,frame)==1&&values[0]==first.output_sample(1,0,0,0));

  Engine zero(c);CHECK(zero.add_node(1,ws::Module<Source>::descriptor()));
  CHECK(zero.add_node(2,ws::Module<ParamProbe>::descriptor()));
  CHECK(zero.modulate(1,0,2,0,0.f));CHECK(zero.set_telemetry_taps({param}));
  CHECK(zero.prepare());render(zero,17);
  CHECK(zero.read_telemetry(values,counts,4,frame)==1&&values[0]==10.f);
  Engine empty(c);CHECK(empty.add_node(1,ws::Module<Source>::descriptor()));
  CHECK(empty.set_telemetry_taps({}));CHECK(empty.prepare());
  {allocation_watch::Scope watch;render(empty,17);CHECK(watch.allocations()==0);}
  CHECK(empty.read_telemetry(values,counts,4,frame)==0&&frame==0);

  Config feedback=c;feedback.feedback_block=32;
  Engine loop(feedback);CHECK(loop.add_node(2,ws::Module<ParamProbe>::descriptor()));
  CHECK(loop.modulate(2,0,2,0,.02f));CHECK(loop.set_telemetry_taps({param}));CHECK(loop.prepare());
  render(loop,70);CHECK(loop.read_telemetry(values,counts,4,frame)==1&&frame==70);
  CHECK(values[0]==loop.output_sample(2,0,0,69)); // Final short feedback chunk.
}
// The host observation cannot perturb oscillator audio or note handling.
static void oscillator_pitch() {
    const Tap pitch{Tap::OscPitch, 1, 0};
    Engine plain, observed;
    for (auto *engine : {&plain, &observed}) {
        CHECK(engine->add_node(1, ws::Module<ws2ports::Vco>::descriptor()));
        CHECK(engine->output(1, 0, 0));
        CHECK(engine->set_parameter(1, 0, 440));
        CHECK(engine->register_producer() == 0);
    }
    CHECK(!plain.set_telemetry_taps({Tap{Tap::OscPitch, 1, 1}}));
    CHECK(!plain.set_telemetry_taps({Tap{Tap::OscPitch, 99, 0}}));
    for (const char *id : {"essentials.vco", "ports.macro_oscillator"}) {
        auto desc = *ws::Module<Source>::descriptor();
        desc.id = id;
        Engine incomplete;
        CHECK(incomplete.add_node(1, &desc) && !incomplete.set_telemetry_taps({pitch}));
    }
    CHECK(plain.set_telemetry_taps({}));
    CHECK(observed.set_telemetry_taps({pitch}));
    CHECK(plain.prepare() && observed.prepare());

    float a[17]{}, b[17]{};
    float *plain_outputs[] = {a};
    float *observed_outputs[] = {b};
    float values[1]{};
    uint32_t counts[1]{};
    uint64_t frame = 0;
    auto block = [&]() {
        allocation_watch::Scope watch;
        CHECK(plain.render(plain_outputs, 1, 17) == WS2_OK);
        CHECK(observed.render(observed_outputs, 1, 17) == WS2_OK);
        CHECK(watch.allocations() == 0);
        for (size_t i = 0; i < 17; ++i) {
            uint32_t left = 0, right = 0;
            std::memcpy(&left, &a[i], sizeof(left));
            std::memcpy(&right, &b[i], sizeof(right));
            CHECK(left == right); // Bit-identical floating-point samples.
        }
        CHECK(observed.read_telemetry(values, counts, 1, frame) == 1 && frame == observed.meter().frame);
    };

    block();
    CHECK(std::abs(values[0] - 440.f) < .01f);
    auto on = event(WS2_NOTE_ON);
    on.key = 72;
    CHECK(plain.enqueue(0, 1, 2, on, 17) == WS2_OK);
    CHECK(observed.enqueue(0, 1, 2, on, 17) == WS2_OK);
    block();
    CHECK(std::abs(values[0] - 523.2511f) < .01f);
    auto off = event(WS2_NOTE_OFF);
    off.key = 72;
    CHECK(plain.enqueue(0, 1, 2, off, 34) == WS2_OK);
    CHECK(observed.enqueue(0, 1, 2, off, 34) == WS2_OK);
    block();
    CHECK(std::abs(values[0] - 523.2511f) < .01f); // NOTE_OFF does not silence this VCO.
    auto choke = event(WS2_NOTE_CHOKE);
    choke.key = 72;
    CHECK(plain.enqueue(0, 1, 2, choke, 51) == WS2_OK);
    CHECK(observed.enqueue(0, 1, 2, choke, 51) == WS2_OK);
    block();
    CHECK(std::abs(values[0] - 440.f) < .01f);

    Engine cv;
    CHECK(cv.add_node(1, ws::Module<ws2ports::Vco>::descriptor()));
    CHECK(cv.add_node(2, ws::Module<Source>::descriptor()));
    CHECK(cv.set_parameter(2, 0, .75f));
    CHECK(cv.connect(2, 0, 1, 0));
    CHECK(cv.set_telemetry_taps({pitch}));
    CHECK(cv.prepare());
    {
        allocation_watch::Scope watch;
        render(cv, 17);
        CHECK(watch.allocations() == 0);
    }
    CHECK(cv.read_telemetry(values, counts, 1, frame) == 1);
    const float expected = 261.6255653f * std::pow(2.f, .75f);
    CHECK(std::abs(values[0] - expected) < .01f); // CV plus ratio, no FM applied.
}
static void modulation(){
 for(float amount:{-.5f,.5f,1.f}){
  Engine e(cfg());CHECK(e.add_node(1,ws::Module<Source>::descriptor()));CHECK(e.add_node(2,ws::Module<Source>::descriptor()));CHECK(e.add_node(3,ws::Module<ParamProbe>::descriptor()));CHECK(e.set_channels(1,4));CHECK(e.set_parameter(1,0,.2f));CHECK(e.set_parameter(2,0,.4f));CHECK(e.modulate(1,0,3,0,amount));CHECK(e.modulate(2,0,3,0,.25f));CHECK(e.prepare());render(e,17);CHECK(e.output_channels(3,0)==4);CHECK(e.output_constant(3,0));
  for(uint32_t c=0;c<4;++c){double n=.5+amount*(.2f+.1f*c)+.25*.4f;float expected=static_cast<float>(std::pow(100.,std::clamp(n,0.,1.)));CHECK(std::abs(e.output_sample(3,0,c,0)-expected)<2e-5);}
 }
 Engine e(cfg());CHECK(e.add_node(1,ws::Module<ParamProbe>::descriptor()));CHECK(e.register_producer()==0);CHECK(e.prepare());render(e,17);CHECK(e.enqueue(0,1,WS2_DIRECT_PORT,event(WS2_PARAM,100),17)==WS2_OK);render(e,17);CHECK(!e.output_constant(1,0));CHECK(std::abs(e.output_sample(1,0,0,0)-std::pow(100.,.5+.5/240))<1e-5);
 Engine latency(cfg());CHECK(latency.add_node(1,ws::Module<LatencyProbe>::descriptor()));CHECK(latency.add_node(2,ws::Module<LatencyProbe>::descriptor()));CHECK(latency.connect(1,0,2,0));CHECK(latency.output(2,0,0));CHECK(latency.prepare());CHECK(latency.meter().latency_frames==14);
}
static void live_modulation_amount() {
    Config config;
    config.ring_capacity = 2;
    Engine engine(config);
    CHECK(engine.add_node(1, ws::Module<Source>::descriptor()));
    CHECK(engine.add_node(2, ws::Module<ParamProbe>::descriptor()));
    CHECK(engine.set_channels(1, 2));
    CHECK(engine.set_parameter(1, 0, .5f));
    CHECK(engine.modulate(1, 0, 2, 0, 0));
    CHECK(!engine.modulate(1, 0, 2, 0, .1f));
    CHECK(engine.register_producer() == 0);
    CHECK(engine.prepare());
    render(engine, 16);
    CHECK(engine.output_constant(2, 0));
    CHECK(engine.set_mod_amount(9, 0, 2, 0, .5f) == WS2_INVALID);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, .25f) == WS2_OK);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, .5f) == WS2_OK);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, -.5f) == WS2_CAPACITY);
    engine.panic();
    {
        allocation_watch::Scope watch;
        render(engine, 128);
        CHECK(watch.allocations() == 0);
    }
    CHECK(!engine.output_constant(2, 0));
    for (uint32_t channel = 0; channel < 2; ++channel) {
        const auto cv = .5f + .1f * channel;
        for (uint32_t frame : {0u, 127u}) {
            const auto expected = std::pow(100., .5 + cv * .5 * (frame + 1) / 240);
            CHECK(std::abs(engine.output_sample(2, 0, channel, frame) - expected) < 2e-5);
        }
    }
    render(engine, 112);
    const auto steady = engine.output_sample(2, 0, 0, 111);
    render(engine, 8);
    CHECK(engine.output_constant(2, 0));
    CHECK(engine.output_sample(2, 0, 0, 0) == steady);

    CHECK(engine.set_mod_amount(1, 0, 2, 0, 0.f) == WS2_OK);
    engine.reset(); // Pending host packets are discarded by a quiescent reset.
    render(engine, 16);
    CHECK(engine.output_sample(2, 0, 0, 0) == steady);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, 0.f) == WS2_OK); // Resend document state.
    render(engine, 240);
    CHECK(engine.output_sample(2, 0, 0, 239) == 10.f);
}

static void modulation_edge_birth() {
    auto build = [](Engine &engine, uint8_t source_rows, uint8_t other_rows, float amount) {
        CHECK(engine.add_node(1, ws::Module<ws2test::Rows>::descriptor(), {source_rows}));
        CHECK(engine.add_node(2, ws::Module<ParamProbe>::descriptor()));
        CHECK(engine.add_node(3, ws::Module<ws2test::Rows>::descriptor(), {other_rows}));
        CHECK(engine.modulate(1, 0, 2, 0, amount));
        CHECK(engine.register_producer() == 0);
        CHECK(engine.prepare());
    };
    Engine engine, other, replaced;
    build(engine, 1, 1, 0);
    build(other, 1, 2, .25f);
    build(replaced, 2, 2, .75f);
    render(engine, 16);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, .25f) == WS2_OK);
    const auto stale = engine.meter().stale;
    replan_test(engine, other);
    render(engine, 240);
    CHECK(engine.meter().stale == stale);
    CHECK(std::abs(engine.output_sample(2, 0, 0, 239) - std::pow(100., .525)) < 2e-5);

    // Live replacement can consume a pre-adoption update on the old edge;
    // unlike quiescent reconfigure, an exact stale increment isn't invariant.
    // Verify the new edge takes its own later authored update after the fade.
    CHECK(engine.set_mod_amount(1, 0, 2, 0, .75f) == WS2_OK);
    replan_test(engine, replaced);
    CHECK(engine.set_mod_amount(1, 0, 2, 0, .5f) == WS2_OK);
    for (int i=0;i<5;++i) render(engine, 256);
    CHECK(std::abs(engine.output_sample(2, 0, 0, 255) - std::pow(100., .55)) < 2e-5);
}

struct TransportProbe {
    static constexpr ws::Info info{"test.transport", "Transport", 1};
    static constexpr std::array<ws2_port, 0> inputs{};
    static constexpr std::array outputs{ws::port("bpm", "BPM"), ws::port("beat", "Beat"),
                                        ws::port("playing", "Playing")};
    static constexpr std::array<ws2_param, 0> params{};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &block) {
        const auto &transport = *block.transport();
        const float values[]{float(transport.bpm), float(transport.beat),
                             transport.flags & WS2_PLAYING ? 1.f : 0.f};
        for (uint32_t port = 0; port < 3; ++port) {
            block.out(port).set_channels(1);
            block.out(port).mark_constant();
            block.out(port).ch(0)[0] = values[port];
        }
    }
};

static void check_transport(Engine &engine, float bpm, float beat, bool playing) {
    CHECK(engine.output_sample(1, 0, 0, 0) == bpm);
    CHECK(std::abs(engine.output_sample(1, 1, 0, 0) - beat) < 1.e-5f);
    CHECK(engine.output_sample(1, 2, 0, 0) == float(playing));
}

static void transport_ring() {
    Config config;
    config.ring_capacity = 2;
    config.future_capacity = 1;
    config.event_budget = 2;
    config.release_reserve = 1;
    Engine engine(config);
    CHECK(engine.transport(85, true, 2.) == WS2_OK);
    CHECK(engine.transport(90, false) == WS2_OK);
    CHECK(engine.transport(301, true) == WS2_INVALID);
    CHECK(engine.transport(90, true, -1.) == WS2_INVALID);
    CHECK(engine.add_node(1, ws::Module<TransportProbe>::descriptor()));
    CHECK(engine.add_node(2, ws::Module<Receiver>::descriptor()));
    CHECK(engine.register_producer() == 0);
    CHECK(engine.prepare());
    render(engine, 16);
    check_transport(engine, 90, 2, false);

    // Neither ordinary future storage nor a node's event budget may limit transport.
    CHECK(engine.enqueue(0, 2, 0, event(WS2_NOTE_ON, .5f), 160) == WS2_OK);
    CHECK(engine.enqueue(0, 2, 0, event(WS2_TRANSPORT_EVENT), 0) == WS2_INVALID);
    render(engine, 16); // Future is now full.
    {
        allocation_watch::Scope watch;
        CHECK(engine.transport(110, true, 4.) == WS2_OK);
        CHECK(engine.transport(100, false) == WS2_OK);
        CHECK(engine.transport(200, true, 9.) == WS2_CAPACITY);
        check_transport(engine, 90, 2, false); // Neither send changed the previous block.
        render(engine, 16);
        CHECK(watch.allocations() == 0);
    }
    check_transport(engine, 100, 4, false); // Both ring entries ran, in send order.
    CHECK(engine.meter().ring_full == 1 && engine.meter().events == 0 && engine.meter().dropped == 0);
    while (engine.meter().frame <= 160) render(engine, 16);
    check_transport(engine, 100, 4, false);
    CHECK(engine.output_sample(2, 0, 0, 0) == .5f); // Stop freezes beat but DSP and notes keep running.

    CHECK(engine.transport(120, true) == WS2_OK);
    engine.panic();
    CHECK(engine.transport(150, false, 6.) == WS2_OK);
    render(engine, 16);
    check_transport(engine, 150, 6, false);
    CHECK(engine.output_sample(2, 0, 0, 0) == 0);
    // A pre-panic packet must apply even if no later packet could mask its loss.
    CHECK(engine.transport(180, true, 7.) == WS2_OK);
    engine.panic();
    render(engine, 16);
    check_transport(engine, 180, 7, true);
    CHECK(engine.transport(60, false) == WS2_OK);
    render(engine, 16);
    check_transport(engine, 60, 7.001f, false);

    CHECK(engine.transport(300, true, 20.) == WS2_OK);
    engine.reset(); // Drops pending host ingress and resets the beat at the next render.
    render(engine, 16);
    check_transport(engine, 60, 0, false);
    CHECK(engine.transport(300, true, 20.) == WS2_OK); // Control owner resends document state.
    render(engine, 16);
    check_transport(engine, 300, 20, true);
}

static void transport_serial() {
    Config config;
    uint64_t serial = 0;
    double beat = 0;
    TransportUpdate{120, 8, false, true}.apply(10, serial, config, beat);
    TransportUpdate{200, 1, true, true}.apply(9, serial, config, beat);
    TransportUpdate{200, 2, true, true}.apply(10, serial, config, beat);
    CHECK(serial == 10 && config.bpm == 120 && !config.playing && beat == 8);
    TransportUpdate{140, 0, true, false}.apply(11, serial, config, beat);
    CHECK(serial == 11 && config.bpm == 140 && config.playing && beat == 8);
}

static void transport_replan() {
    Config config;
    config.max_block = 4096; // Ample wall-clock window for the control/render handshake.
    Engine live(config), candidate(config);
    auto replaced = *ws::Module<Receiver>::descriptor();
    CHECK(candidate.transport(250, true, 99.) == WS2_OK);
    for (auto *engine : {&live, &candidate}) {
        CHECK(engine->add_node(1, ws::Module<TransportProbe>::descriptor()));
        CHECK(engine->add_node(2, engine == &live ? ws::Module<Receiver>::descriptor() : &replaced));
        CHECK(engine->add_node(4, ws::Module<ws2test::Rows>::descriptor(), {1}));
        CHECK(engine->register_producer() == 0);
        CHECK(engine->prepare());
    }
    CHECK(live.transport(130, false, 12.) == WS2_OK);
    CHECK(live.enqueue(0, 2, 0, event(WS2_NOTE_ON, 1.f), 100000) == WS2_OK);
    CHECK(live.enqueue(0, 3, 0, event(WS2_NOTE_ON, 1.f), 100000) == WS2_OK);
    render(live, 16);
    check_transport(live, 130, 12, false);
    const auto stale = live.meter().stale;
    CHECK(stale == 1); // Missing node is counted immediately.

    std::atomic<bool> complete{false};
    bool replanned = false;
    std::thread control([&] {
        replanned = live.replan(candidate, 200000000);
        complete.store(true, std::memory_order_release);
    });
    while (!complete.load(std::memory_order_acquire)) {
        render(live, 16);
        std::this_thread::yield();
    }
    control.join();
    CHECK(replanned);
    render(live, 16);
    check_transport(live, 130, 12, false);
    CHECK(live.meter().stale == stale + 1); // Queued event predates replacement node's birth.
    CHECK(live.output_sample(2, 0, 0, 0) == 0);
    CHECK(live.transport(135, false, 13.) == WS2_OK);
    render(live, 16);
    check_transport(live, 135, 13, false);

    // Live config replacement carries the current serial and queued host updates.
    Engine config_replacement(config);
    CHECK(config_replacement.add_node(1, ws::Module<TransportProbe>::descriptor()));
    CHECK(config_replacement.add_node(2, &replaced));
    CHECK(config_replacement.add_node(4, ws::Module<ws2test::Rows>::descriptor(), {2}));
    CHECK(config_replacement.register_producer() == 0);
    CHECK(config_replacement.prepare());
    CHECK(live.transport(170, false, 21.) == WS2_OK);
    replan_test(live, config_replacement, 200000000);
    render(live, 16);
    check_transport(live, 170, 21, false);
    CHECK(live.transport(165, false) == WS2_OK);
    render(live, 16);
    check_transport(live, 165, 21, false);
}
// ER4: a config-shaped synthetic voice owner has the same descriptor and ID
// on either side of an edit. The replacement must replay the existing held
// note without a new attack from the test. A pre-adoption note-off must reach it.
// Conversely, removing the ID and introducing it in a separate edit
// invalidates the old packet; it must not release the newly held note.
static void append_only_descriptor_registration() {
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    // Deliberately poison bytes beyond the advertised size: they are absent.
    d.struct_size = offsetof(ws2_descriptor, data_slot_count);
    d.data_slot_count = 1;
    Engine legacy;
    CHECK(legacy.add_node(1, &d));
    CHECK(legacy.output(1, 0, 0));
    CHECK(legacy.prepare());
    render(legacy, 16);
    CHECK(legacy.output_sample(1, 0, 0, 15) == 1.f);
    ws2_descriptor unsupported = d;
    unsupported.struct_size = sizeof(unsupported);
    Engine not_yet;
    CHECK(!not_yet.add_node(1, &unsupported));
}
// E3a: a valid declared slot has its packed defaults before the first process.
static int WS2_CALL data_slot_probe_process(void *self, ws2_process *p) {
    CHECK(p->struct_size >= offsetof(ws2_process, data) + sizeof(p->data));
    CHECK(p->data_count == 1 && p->data);
    const auto &slot = p->data[0];
    CHECK(slot.struct_size >= sizeof(ws2_data));
    CHECK(slot.data && slot.bytes == sizeof(float) && slot.serial == 1);
    CHECK(reinterpret_cast<uintptr_t>(slot.data) % 16 == 0);
    float value = 0;
    std::memcpy(&value, slot.data, sizeof(value));
    CHECK(value == .375f);
    return ws::Module<Source>::descriptor()->process(self, p);
}
static void data_slot_defaults() {
    const ws2_field field{sizeof(ws2_field), "value", "Value", WS2_F_F32,
        0, 1, 0, WS2_NO_FIELD, 0, nullptr, 0., 1., .375, 0, nullptr};
    const ws2_data_slot slot{sizeof(ws2_data_slot), "settings", "Settings",
        sizeof(float), 1, &field, 0};
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.data_slot_count = 1;
    d.data_slots = &slot;
    d.process = data_slot_probe_process;
    Engine e;
    CHECK(e.add_node(1, &d));
    CHECK(e.output(1, 0, 0));
    CHECK(e.prepare());
    { allocation_watch::Scope watch; render(e, 16); render(e, 17);
      CHECK(watch.allocations() == 0); }
    CHECK(e.output_sample(1, 0, 0, 15) == 1.f);
}
static uint32_t data_probe_serial = 0;
static bool data_probe_compare = false;
static uint32_t data_probe_calls = 0;
static const void *data_probe_pointer = nullptr;
static uint32_t data_probe_shared_serial = 0;
static int WS2_CALL data_delivery_probe(void *self, ws2_process *p) {
    CHECK(p->data_count == 1 && p->data && p->data[0].data);
    CHECK(p->data[0].bytes == sizeof(float));
    CHECK(reinterpret_cast<uintptr_t>(p->data[0].data) % 16 == 0);
    float v = 0;
    std::memcpy(&v, p->data[0].data, sizeof(v));
    data_probe_serial = p->data[0].serial;
    if (data_probe_compare) {
        if (!data_probe_calls) {
            data_probe_pointer = p->data[0].data;
            data_probe_shared_serial = data_probe_serial;
        } else {
            CHECK(p->data[0].data == data_probe_pointer);
            CHECK(data_probe_serial == data_probe_shared_serial);
        }
        ++data_probe_calls;
    }
    const int result = ws::Module<Source>::descriptor()->process(self, p);
    for (uint32_t c = 0; c < p->outputs[0].channels; ++c)
        p->outputs[0].data[c][0] = v;
    return result;
}
static void live_data_delivery() {
    const ws2_field field{sizeof(ws2_field), "value", "Value", WS2_F_F32,
        0, 1, 0, WS2_NO_FIELD, 0, nullptr, 0., 1., .375, 0, nullptr};
    const ws2_data_slot slot{sizeof(ws2_data_slot), "settings", "Settings",
        sizeof(float), 1, &field, 0};
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.data_slot_count = 1;
    d.data_slots = &slot;
    d.process = data_delivery_probe;
    auto packed = [](float v) {
        std::vector<uint8_t> bytes(sizeof(v));
        std::memcpy(bytes.data(), &v, sizeof(v));
        return bytes;
    };
    Config c = cfg();
    c.ring_capacity = 2;
    Engine e(c);
    CHECK(e.add_node(1, &d));
    CHECK(e.set_data_packed(1, 0, packed(.25f)) == WS2_OK);
    CHECK(e.output(1, 0, 0));
    CHECK(e.register_producer() == 0);
    CHECK(e.prepare());
    auto verify = [&](float value, uint32_t serial) {
        allocation_watch::Scope watch;
        render(e, 16);
        CHECK(watch.allocations() == 0);
        CHECK(e.output_sample(1, 0, 0, 15) == value);
        CHECK(data_probe_serial == serial);
    };
    verify(.25f, 1);
    CHECK(e.set_data_packed(1, 1, packed(.5f)) == WS2_INVALID);
    CHECK(e.set_data_packed(1, 0, {}) == WS2_INVALID);
    CHECK(e.set_data_packed(1, 0, packed(.5f)) == WS2_OK);
    CHECK(e.set_data_packed(1, 0, packed(.75f)) == WS2_OK);
    CHECK(e.set_data_packed(1, 0, packed(1.f)) == WS2_CAPACITY);
    e.panic(); // Host writes bypass generation and event budgets.
    verify(.75f, 3);
    CHECK(e.set_data_packed(1, 0, packed(.125f)) == WS2_OK);
    e.reset(); // Discards pending packet; caller re-sends document data.
    verify(.75f, 3);
    CHECK(e.set_data_packed(1, 0, packed(.125f)) == WS2_OK);
    verify(.125f, 5);
    // A queued write survives a same-descriptor replacement and both
    // instances see the current immutable block from the adoption boundary.
    CHECK(e.set_data_packed(1, 0, packed(.625f)) == WS2_OK);
    Engine candidate(c);
    CHECK(candidate.add_node(1, &d, {1}));
    CHECK(candidate.output(1, 0, 0));
    CHECK(candidate.prepare());
    replan_test(e, candidate);
    verify(.625f, 6);
    CHECK(e.set_data_packed(1, 0, packed(.875f)) == WS2_OK);
    verify(.875f, 7);
}
static void data_history_reclaim() {
    DataSlotStorage owner(4);
    for (uint32_t serial = 1; serial <= 6; ++serial)
        owner.versions.push_back({serial, allocate_data_block(4)});
    // Active and fading instances still reference different versions.
    // After reset the other versions have no ring reader.
    owner.canceled_through = 6;
    owner.reclaim(1, [](uint32_t serial) { return serial == 1 || serial == 2; });
    CHECK(owner.versions.size() == 3);
    CHECK(owner.versions[0].serial == 1 && owner.versions[1].serial == 2 &&
          owner.versions[2].serial == 6 && owner.canceled_through == 0);
    owner.reclaim(6, [](uint32_t) { return false; });
    CHECK(owner.versions.size() == 1 && owner.versions.front().serial == 6);
}
static int WS2_CALL data_serial_probe(void *self, ws2_process *p) {
    const int result = data_delivery_probe(self, p);
    CHECK(p->outputs[0].data[0][0] == float(p->data[0].serial % 256) / 256.f);
    return result;
}
static void data_lifetime_stress() {
    const ws2_field field{sizeof(ws2_field), "value", "Value", WS2_F_F32,
        0, 1, 0, WS2_NO_FIELD, 0, nullptr, 0., 1., 1./256., 0, nullptr};
    const ws2_data_slot slot{sizeof(ws2_data_slot), "settings", "Settings",
        sizeof(float), 1, &field, 0};
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.data_slot_count = 1;
    d.data_slots = &slot;
    d.process = data_serial_probe;
    Config c = cfg();
    c.ring_capacity = 16;
    Engine e(c);
    CHECK(e.add_node(1, &d) && e.output(1, 0, 0));
    CHECK(e.register_producer() == 0 && e.prepare());
    std::atomic<bool> done{false};
    constexpr uint32_t writes = 10000;
    std::thread consumer([&] {
        allocation_watch::ThreadScope watch;
        while (!done.load(std::memory_order_acquire)) {
            render(e, 16);
            std::this_thread::yield();
        }
        render(e, 16);
        CHECK(data_probe_serial == writes + 1);
        CHECK(watch.allocations() == 0);
    });
    std::vector<uint8_t> bytes(sizeof(float));
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
    for (uint32_t serial = 2; serial <= writes + 1; ++serial) {
        const float value = float(serial % 256) / 256.f;
        std::memcpy(bytes.data(), &value, sizeof(value));
        int result;
        while ((result = e.set_data_packed(1, 0, bytes)) == WS2_CAPACITY) {
            CHECK(std::chrono::steady_clock::now() < deadline);
            std::this_thread::yield();
        }
        CHECK(result == WS2_OK);
    }
    done.store(true, std::memory_order_release);
    consumer.join();
    CHECK(e.meter().faults == 0);
}
// E3a-2: a prepared document candidate explicitly supplies data for
// both retained and replaced instances, rather than inheriting stale bytes.
static void candidate_document_data() {
    const ws2_field field{sizeof(ws2_field), "value", "Value", WS2_F_F32,
        0, 1, 0, WS2_NO_FIELD, 0, nullptr, 0., 1., .375, 0, nullptr};
    const ws2_data_slot slot{sizeof(ws2_data_slot), "settings", "Settings",
        sizeof(float), 1, &field, 0};
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.data_slot_count = 1;
    d.data_slots = &slot;
    d.process = data_delivery_probe;
    Config c = cfg(); c.max_block = 4096;
    auto make = [&](uint8_t shape, float value) {
        auto e = std::make_unique<Engine>(c);
        std::vector<uint8_t> packed(sizeof(value));
        std::memcpy(packed.data(), &value, sizeof(value));
        CHECK(e->add_node(1, &d, {shape}) && e->output(1, 0, 0));
        CHECK(e->set_data_packed(1, 0, packed) == WS2_OK);
        CHECK(e->register_producer() == 0 && e->prepare());
        return e;
    };
    auto live = make(1, .25f);
    render(*live, 16);
    auto retained = make(1, .5f);
    replan_test(*live, *retained, 200000000);
    render(*live, 16);
    CHECK(live->output_sample(1, 0, 0, 15) == .5f && data_probe_serial == 2);
    auto replaced = make(2, .75f);
    replan_test(*live, *replaced, 200000000);
    render(*live, 16);
    CHECK(live->output_sample(1, 0, 0, 15) == .75f && data_probe_serial == 3);
}
static void data_replacement_lifetime() {
    const ws2_field field{sizeof(ws2_field), "value", "Value", WS2_F_F32,
        0, 1, 0, WS2_NO_FIELD, 0, nullptr, 0., 1., .375, 0, nullptr};
    const ws2_data_slot slot{sizeof(ws2_data_slot), "settings", "Settings",
        sizeof(float), 1, &field, 0};
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.data_slot_count = 1;
    d.data_slots = &slot;
    d.process = data_delivery_probe;
    d.replace_fade_ms = 500;
    Config c = cfg(); c.max_block = 4096;
    Engine live(c);
    CHECK(live.add_node(1, &d, {1}) && live.output(1, 0, 0));
    CHECK(live.register_producer() == 0 && live.prepare());
    auto packed = [](float value) {
        std::vector<uint8_t> bytes(sizeof(value));
        std::memcpy(bytes.data(), &value, sizeof(value));
        return bytes;
    };
    auto candidate = [&](uint8_t shape) {
        auto next = std::make_unique<Engine>(c);
        if (shape) {
            CHECK(next->add_node(1, &d, {shape}) && next->output(1, 0, 0));
        } else {
            CHECK(next->add_node(9, ws::Module<Source>::descriptor()));
        }
        CHECK(next->prepare());
        return next;
    };
    auto publish = [&](Engine &next) {
        std::atomic<bool> finished{false};
        bool accepted = false;
        std::thread control([&] {
            accepted = live.replan(next, 200000000);
            finished.store(true, std::memory_order_release);
        });
        do {
            render(live, 1);
            std::this_thread::sleep_for(std::chrono::microseconds(100));
        } while (!finished.load(std::memory_order_acquire));
        control.join();
        CHECK(accepted);
    };
    auto shared = [&](uint32_t serial, float value) {
        data_probe_calls = 0;
        data_probe_compare = true;
        { allocation_watch::Scope watch; render(live, 1); CHECK(watch.allocations() == 0); }
        data_probe_compare = false;
        CHECK(data_probe_calls == 2 && data_probe_shared_serial == serial);
        CHECK(live.output_sample(1, 0, 0, 0) == value);
        data_probe_pointer = nullptr;
    };
    auto first = candidate(2);
    CHECK(live.set_data_packed(1, 0, packed(.5f)) == WS2_OK);
    publish(*first);
    shared(2, .5f);
    auto second = candidate(3);
    CHECK(live.set_data_packed(1, 0, packed(.75f)) == WS2_OK);
    // A75: refusal is synchronous, leaves the candidate reusable, and
    // does not consume an ingress packet or change the current transition.
    const auto before = live.meter();
    CHECK(!live.replan(*second, 200000000));
    CHECK(live.error() == "Replacement busy: predecessor still fading");
    CHECK(live.replacement_blocked_ids() == std::vector<uint32_t>{1});
    CHECK(live.replacement_tail_pending(1));
    CHECK(!live.replacement_tail_pending(9));
    CHECK(live.meter().frame == before.frame && live.meter().generation == before.generation);
    shared(3, .75f);
    CHECK(live.set_data_packed(1, 0, packed(.875f)) == WS2_OK);
    shared(4, .875f);
    for (int i = 0; i < 7; ++i) render(live, 4096); // more than 500 ms
    CHECK(!live.replacement_tail_pending(1));
    publish(*second);
    CHECK(live.replacement_blocked_ids().empty());
    shared(4, .875f);
    for (int i = 0; i < 7; ++i) render(live, 4096);
    // Remove then re-add the ID: a fresh binding has default serial/value,
    // even if old fading instances and queued packets still exist.
    CHECK(live.set_data_packed(1, 0, packed(.125f)) == WS2_OK);
    auto removed = candidate(0); publish(*removed);
    auto reborn = candidate(1); publish(*reborn);
    render(live, 1);
    CHECK(live.output_sample(1, 0, 0, 0) == .375f);
    CHECK(live.set_data_packed(1, 0, packed(.25f)) == WS2_OK);
    render(live, 1);
    CHECK(live.output_sample(1, 0, 0, 0) == .25f);
}
// A75 applies to legacy slot-free descriptors as well. Compare the
// complete fade against an identical engine that never receives the refused
// edit, then compare the accepted retry against its first normal edit.
static void legacy_replacement_busy() {
    ws2_descriptor d = *ws::Module<Source>::descriptor();
    d.replace_fade_ms = 500;
    Config c = cfg(); c.max_block = 4096;
    auto make = [&](uint8_t shape, float value) {
        auto e = std::make_unique<Engine>(c);
        CHECK(e->add_node(1, &d, {shape}) && e->output(1, 0, 0));
        CHECK(e->set_parameter(1, 0, value));
        CHECK(e->register_producer() == 0 && e->prepare());
        return e;
    };
    auto live = make(1, 1.f), witness = make(1, 1.f);
    auto first = make(2, .5f), first_witness = make(2, .5f);
    auto second = make(3, .25f), second_witness = make(3, .25f);
    auto sample = [](Engine &e) {
        float value = 0; float *out[]{&value};
        allocation_watch::ThreadScope watch;
        CHECK(e.render(out, 1, 1) == WS2_OK);
        CHECK(watch.allocations() == 0);
        return value;
    };
    auto begin = [&](Engine &e, Engine &candidate, float initial) {
        std::atomic<bool> done{false}; bool accepted = false;
        std::thread control([&] {
            accepted = e.replan(candidate, 200000000);
            done.store(true, std::memory_order_release);
        });
        std::vector<float> trace;
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        do {
            float v = sample(e);
            if (v != initial || !trace.empty()) trace.push_back(v);
            std::this_thread::sleep_for(std::chrono::microseconds(100));
            CHECK(std::chrono::steady_clock::now() < deadline);
        } while (!done.load(std::memory_order_acquire));
        control.join();
        CHECK(accepted && !trace.empty());
        return trace;
    };
    auto compare = [&](std::vector<float> a, std::vector<float> b) {
        // Remove scheduler-dependent pre-adoption constant samples only.
        // Compare every actual transition sample, including the settled end.
        const auto count = std::max(a.size(), b.size());
        while (a.size() < count) a.push_back(sample(*live));
        while (b.size() < count) b.push_back(sample(*witness));
        CHECK(std::memcmp(a.data(), b.data(), a.size()*sizeof(float)) == 0);
        for (uint32_t i = 0; i < 24001; ++i) {
            float x = sample(*live), y = sample(*witness);
            CHECK(std::memcmp(&x, &y, sizeof(float)) == 0);
        }
    };
    CHECK(sample(*live) == 1.f && sample(*witness) == 1.f);
    auto a = begin(*live, *first, 1.f);
    auto b = begin(*witness, *first_witness, 1.f);
    const auto meter = live->meter();
    CHECK(!live->replan(*second, 200000000));
    CHECK(live->error() == "Replacement busy: predecessor still fading");
    CHECK(live->meter().frame == meter.frame && live->meter().generation == meter.generation);
    compare(std::move(a), std::move(b));
    CHECK(sample(*live) == .5f && sample(*witness) == .5f);
    a = begin(*live, *second, .5f);
    b = begin(*witness, *second_witness, .5f);
    compare(std::move(a), std::move(b));
    CHECK(sample(*live) == .25f && sample(*witness) == .25f);
}
// E5 L2: direct-port CHOKE is source-wide in the combined-events voice
// consumer. The host fallback ledger must agree, including routed input
// notes of the same source; unrelated sources survive a targeted choke.
static void direct_choke_replacement_ledger() {
    Config config = cfg(); config.max_block = 4096;
    auto make = [&](uint8_t voices) {
        auto e = std::make_unique<Engine>(config);
        CHECK(e->add_node(1, ws::Module<ws2test::NotesToCv>::descriptor(), {voices}));
        CHECK(e->output(1, 1, 0) && e->register_producer() == 0 && e->prepare());
        return e;
    };
    auto gates = [](Engine &e) {
        uint32_t active = 0;
        for (uint32_t ch = 0; ch < e.output_channels(1, 1); ++ch)
            if (e.output_sample(1, 1, ch, 15) == 1.f) ++active;
        return active;
    };
    for (const bool all_sources : {false, true}) {
        auto live = make(4), candidate = make(5);
        auto n = event(WS2_NOTE_ON, .75f);
        CHECK(live->enqueue(0, 1, WS2_DIRECT_PORT, n, 0, Timing::Immediate) == WS2_OK);
        n.note_id = 2; n.key = 62;
        CHECK(live->enqueue(0, 1, 0, n, 0, Timing::Immediate) == WS2_OK);
        n.note_id = 3; n.key = 64; n.source_id = 2;
        CHECK(live->enqueue(0, 1, 0, n, 0, Timing::Immediate) == WS2_OK);
        render(*live, 16);
        CHECK(gates(*live) == 3);
        auto choke = event(WS2_NOTE_CHOKE);
        choke.source_id = all_sources ? UINT32_MAX : 1;
        choke.note_id = choke.channel = -1;
        CHECK(live->enqueue(0, 1, WS2_DIRECT_PORT, choke, 0, Timing::Immediate) == WS2_OK);
        render(*live, 16);
        CHECK(gates(*live) == (all_sources ? 0u : 1u));
        replan_test(*live, *candidate, 200000000);
        render(*live, 16);
        CHECK(gates(*live) == (all_sources ? 0u : 1u));
        CHECK(live->meter().faults == 0);
    }
}
static void replacement_packet_birth() {
    Config config;
    config.max_block = 4096;
    auto make = [&](uint8_t voices) {
        auto e = std::make_unique<Engine>(config);
        CHECK(e->add_node(9, ws::Module<Source>::descriptor()));
        if (voices) {
            CHECK(e->add_node(1, ws::Module<ws2test::NotesToCv>::descriptor(), {voices}));
            CHECK(e->output(1, 1, 0));
        }
        CHECK(e->register_producer() == 0);
        CHECK(e->prepare());
        return e;
    };
    auto replan = [&](Engine &live, Engine &candidate) {
        std::atomic<bool> done{false};
        bool ok = false;
        std::thread control([&] {
            ok = live.replan(candidate, 200000000);
            done.store(true, std::memory_order_release);
        });
        while (!done.load(std::memory_order_acquire)) {
            render(live, 16);
            std::this_thread::sleep_for(std::chrono::microseconds(100));
        }
        control.join();
        CHECK(ok);
    };
    auto held = [&](Engine &live) {
        CHECK(live.enqueue(0, 1, 0, event(WS2_NOTE_ON, .75f), 0, Timing::Immediate) == WS2_OK);
        render(live, 16);
        CHECK(live.output_sample(1, 1, 0, 15) == 1.f);
    };
    for (bool replace : {false, true}) {
        auto live = make(1);
        held(*live);
        const auto stale = live->meter().stale;
        const uint64_t due = live->meter().frame + 65536;
        CHECK(live->enqueue(0, 1, 0, event(WS2_NOTE_OFF, 0), due) == WS2_OK);
        render(*live, 16); // Packet now lives in the future queue.
        auto successor = make(2);
        if (!replace) {
            auto absent = make(0);
            replan(*live, *absent);
            CHECK(live->meter().stale == stale + 1);
        }
        replan(*live, *successor);
        CHECK(live->meter().frame < due);
        if (!replace) held(*live); // A newly born ID needs its own attack.
        else {
            render(*live, 16);
            CHECK(live->output_sample(1, 1, 0, 15) == 1.f);
        }
        CHECK(live->meter().stale == stale + (replace ? 0 : 1));
        while (live->meter().frame <= due) render(*live, 4096);
        render(*live, 16);
        CHECK(live->output_sample(1, 1, 0, 15) == (replace ? 0.f : 1.f));
        CHECK(live->meter().stale == stale + (replace ? 0 : 1));
    }
}
// E4a: topology entries must not embed DSP instances. Two layouts must
// be able to refer to the same instance without moving its address.
static void layout_instance_separation(){
 CHECK(std::is_reference_v<decltype(Node::instance)>);
 Instance instance;
 instance.id = 7;
 Layout first, second;
 first.nodes.push_back(std::make_unique<Node>(instance));
 second.nodes.push_back(std::make_unique<Node>(instance));
 first.nodes[0]->slot.index = 1;
 second.nodes[0]->slot.index = 2;
 CHECK(&first.nodes[0]->instance == &second.nodes[0]->instance);
 CHECK(first.nodes[0]->slot.index != second.nodes[0]->slot.index);
 first.nodes.clear();
 CHECK(second.nodes[0]->instance.id == 7);
}
static void removed_mod_edge_lookup(){
 Layout layout;
 layout.edges.push_back({1, 0, 2, 0, 2, .1f});
 layout.edges.push_back({2, 0, 3, 0, 2, .2f});
 layout.edges.push_back({2, 0, 3, 0, 2, .3f});
 layout.edges.push_back({3, 0, 4, 0, 2, .4f});
 layout.edges[1].removed = true;
 CHECK(layout.find_mod_edge(2, 0, 3, 0) == &layout.edges[2]);
 layout.edges[2].removed = true;
 CHECK(layout.find_mod_edge(2, 0, 3, 0) == nullptr);
 CHECK(layout.find_mod_edge(1, 0, 2, 0) == &layout.edges[0]);
 CHECK(layout.find_mod_edge(3, 0, 4, 0) == &layout.edges[3]);
 CHECK(layout.find_mod_edge(2, 0, 4, 0) == nullptr);
}
static void edge_envelope_and_publication(){
 EdgeGain gain;
 gain.jump(0);
 gain.set(1, 240);
 CHECK(gain.at(0) == float(1. / 240));
 CHECK(gain.at(59) == .25f);
 CHECK(!gain.advance(60));
 CHECK(gain.current() == .25f);
 gain.set(1, 240); // Same target must not restart an in-flight ramp.
 CHECK(gain.at(0) == float(61. / 240));
 gain.set(0, 240);
 CHECK(gain.at(0) == float(.25 * (239. / 240)));
 CHECK(gain.advance(240) && gain.silent());
 gain.set(1, 0);
 CHECK(gain.current() == 1);

 int next = 7;
 std::atomic<int *> pending{nullptr};
 std::atomic<uint64_t> adopted{0};
 unsigned tick = 0;
 CHECK(!publish_and_wait(pending, adopted, &next, 1, 3u,
     [&]{return tick;}, [&]{++tick;}));
 CHECK(!pending.load() && adopted.load() == 0);
 tick = 0;
 CHECK(publish_and_wait(pending, adopted, &next, 1, 3u,
     [&]{return tick;}, [&]{
         ++tick;
         if (tick == 1) CHECK(pending.exchange(nullptr) == &next);
         // Claim before deadline, acknowledge after it: timeout CAS loses.
         if (tick == 5) adopted.store(1);
     }));
 CHECK(!pending.load() && adopted.load() == 1 && tick == 5);

 Ring ring(3);
 Packet a{}, b{}, c{}, out{};
 a.revision = 1; a.order = 1;
 b.revision = 2; b.order = 2;
 c.revision = 1; c.order = 3;
 CHECK(ring.push(a) && ring.push(b) && ring.push(c));
 uint64_t blocked = 0;
 CHECK(ring.pop_adopted(out, 1, blocked) && out.order == 1);
 CHECK(!ring.pop_adopted(out, 1, blocked) && blocked == 2);
 CHECK(!ring.pop_adopted(out, 1, blocked) && blocked == 2);
 CHECK(ring.pop_adopted(out, 2, blocked) && out.order == 2);
 CHECK(ring.pop_adopted(out, 2, blocked) && out.order == 3);
 CHECK(!ring.pop_adopted(out, 2, blocked));
}
int main(){
 edge_envelope_and_publication();
 layout_instance_separation();
 removed_mod_edge_lookup();
#ifdef _MSC_VER
 _set_abort_behavior(0,_WRITE_ABORT_MSG|_CALL_REPORTFAULT);
#endif
#if defined(_MSC_VER)&&defined(_DEBUG)
 // Warm thread runtime bookkeeping before comparing normal CRT heap blocks.
 {std::thread warm([](){});warm.join();}
 _CrtMemState before{},after{},difference{};_CrtMemCheckpoint(&before);
#endif
 invalid_events();
 live_modulation_amount();
 modulation_edge_birth();
 transport_ring();
 transport_serial();
 transport_replan();
 append_only_descriptor_registration();
 data_slot_defaults();
 live_data_delivery();
 data_history_reclaim();
 data_lifetime_stress();
 data_replacement_lifetime();
 candidate_document_data();
 legacy_replacement_busy();
 direct_choke_replacement_ledger();
 replacement_packet_birth();
 parameter_channels();
 modulation_spans();
 telemetry();
 oscillator_pitch();
 producer_validation();
 zero_copy();
 cached_taper<WS2_LINEAR>();
 cached_taper<WS2_LOG>();
 cached_taper<WS2_EXP>();
 signals();
 CHECK(loop(32, false) == loop(32, true));
 CHECK(loop(1, false) == loop(1, true));
 events();
 timing();
 overflow();
 rows();
 producer_stress();
 modulation();
#if defined(_MSC_VER)&&defined(_DEBUG)
 CHECK(_CrtCheckMemory());_CrtMemCheckpoint(&after);if(_CrtMemDifference(&difference,&before,&after)){
  std::fprintf(stderr,"Debug CRT normal blocks %zu -> %zu, bytes %zu -> %zu; client blocks %zu -> %zu\n",before.lCounts[_NORMAL_BLOCK],after.lCounts[_NORMAL_BLOCK],before.lSizes[_NORMAL_BLOCK],after.lSizes[_NORMAL_BLOCK],before.lCounts[_CLIENT_BLOCK],after.lCounts[_CLIENT_BLOCK]);return 1;
 }std::puts("PASS Debug CRT shutdown heap balance");
#endif
 std::puts("PASS engine2 channels/modulation/events/feedback/arena/state/generation/fake clocks/concurrent stress");}
