// SPDX-License-Identifier: MIT
#include "wirescape_sdk.h"
#include "wirescape/beat_clock.h"
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <limits>
#include <vector>
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"SDK check line %d: %s\n",__LINE__,#x);std::abort();}}while(0)
struct Mini {
 static constexpr ws::Info info{"test.sdk","SDK test",1};
 static constexpr std::array inputs{ws::port("in","In")};
 static constexpr std::array outputs{ws::port("out","Out")};
 static constexpr std::array params{ws::param("gain","Gain",0,2,1)};
 void prepare(const ws::Setup&){} void reset(){}
 void process(ws::Block&b){b.out(0).set_channels(b.channels());b.out(0).mark_constant(b.in(0).constant()&&b.param(0).constant());for(uint32_t c=0;c<b.channels();++c)for(uint32_t i=0;i<(b.in(0).constant()&&b.param(0).constant()?1u:b.frames());++i)b.out(0).ch(c)[i]=b.in(0).ch(c)[i]*b.param(0).ch(c)[i];}
};
#define SDK_DATA_FIELDS(X, S) \
 X(S, value, float, WS2_F_F32, "Value", ws::data_range(0,1,.25)) \
 X(S, length, uint32_t, WS2_F_U32, "Length", ws::data_range(0,4,0)) \
 X(S, values, uint8_t[4], WS2_F_U8, "Values", ws::data_range(0,255,0,1)) \
 X(S, name, char[8], WS2_F_TEXT, "Name", ws::DataFieldRules{})
WS_DEFINE_DATA_STRUCT(SdkData, SDK_DATA_FIELDS)
static_assert(SdkData_fields.size() == 4);
static_assert(SdkData_fields[2].offset == offsetof(SdkData, values) && SdkData_fields[2].count == 4);
static_assert(SdkData_fields[2].length_field == 1 && SdkData_fields[3].count == 8);
struct MiniData : Mini {
 static constexpr std::array data_slots{ws::data_slot<SdkData>("settings","Settings",SdkData_fields)};
 void process(ws::Block&b) {
  uint32_t serial=0;const auto *v=b.data<SdkData>(0,serial);CHECK(v&&serial==7);
  b.out(0).set_channels(1);b.out(0).mark_constant();b.out(0).ch(0)[0]=v->value;
 }
};
// A116: the codegen pin must preserve exact finite-sample semantics.
static void finite_samples_tests(){
 const float inf=std::numeric_limits<float>::infinity();
 const float nan=std::numeric_limits<float>::quiet_NaN();
 // 0.5f and 2.0f have exponent bits 126 and 128 (OR == 255),
 // yet both are finite. This exercises the exact fallback scan.
 alignas(16) float data[35];
 for(uint32_t offset:{0u,1u})for(uint32_t count=0;count<=33;++count){
  float* row=data+offset;
  for(uint32_t i=0;i<count;++i)row[i]=(i%2)?2.f:.5f;
  CHECK(ws::finite_samples(row,count));
  for(uint32_t i=0;i<count;++i){
   float saved=row[i];
   for(float bad:{nan,inf,-inf}){
    row[i]=bad;CHECK(!ws::finite_samples(row,count));
   }
   row[i]=saved;
  }
  for(uint32_t i=0;i<count;++i)row[i]=(i%2)?-0.f:std::numeric_limits<float>::denorm_min();
  CHECK(ws::finite_samples(row,count));
 }
 const float limits[]={0.f,-0.f,std::numeric_limits<float>::max(),
                       -std::numeric_limits<float>::max(),std::numeric_limits<float>::min()};
 CHECK(ws::finite_samples(limits,5));
 CHECK(ws::finite_samples(nullptr,0));
 CHECK(ws::finite_samples(&nan,0));
 CHECK(!ws::finite_samples(&nan,1));
}
 // SDK-1: independent beat-clock oracles, not a second implementation.
static void beat_clock_tests() {
    using wsbeat::BeatClock;
    using wsbeat::division_beats;
    using wsbeat::division_index;
    const double expected[]{16,8,4,3,2,1.5,4./3,1,.75,2./3,.5,.375,1./3,.25,.1875,1./6,.125,1./12};
    for (int i=0; i<18; ++i) {
        CHECK(division_beats(float(i)) == expected[i]);
        CHECK(division_index(3*expected[i], expected[i]) == 3);
        CHECK(division_index(3*expected[i]-1e-5, expected[i]) == 2);
    }
    CHECK(division_beats(-100) == 16);
    CHECK(division_beats(100) == 1./12);
    CHECK(division_beats(7.5f) == .75);
    CHECK(division_beats(std::nanf("")) == 1);
    CHECK(division_index(-.25,.25) == -1);
    const auto near = [](double a, double b) { return std::abs(a-b)<1e-12; };
    for (double rate : {44100.,48000.,96000.}) {
        BeatClock c;
        ws2_transport t{};
        t.struct_size=sizeof(t); t.flags=WS2_PLAYING; t.bpm=120; t.beat=12;
        for (uint32_t frame=0; frame<32; ++frame)
            CHECK(near(c.step(false,0,false,1,&t,frame,rate),12+frame*2/rate));
        CHECK(near(c.samples_per_beat(),rate/2));
        CHECK(near(c.step(false,0,true,1,&t,32,rate),0));
        CHECK(near(c.step(false,0,false,1,&t,33,rate),2/rate));
        // Stopped transport advances from the last beat, not t.beat.
        t.flags=0; t.bpm=90; t.beat=99;
        const double last=c.beat();
        for (uint32_t frame=0; frame<32; ++frame)
            CHECK(near(c.step(false,0,false,1,&t,frame,rate),last+(frame+1)*1.5/rate));
        CHECK(near(c.samples_per_beat(),rate/1.5));
        CHECK(c.step(false,0,true,1,&t,32,rate)==0);
        CHECK(near(c.step(false,0,false,1,nullptr,0,rate),2/rate));
        c.reset();
        CHECK(c.beat()==0 && !c.held());
        CHECK(near(c.step(false,0,false,1,nullptr,0,rate),2/rate));

        // Clock at 4 PPQ: an edge is 1/4 beat, period 8 samples.
        c.reset();
        CHECK(c.step(true,1,true,4,nullptr,0,rate)==0);
        for (uint32_t f=1; f<8; ++f)
            CHECK(c.step(true,0,false,4,nullptr,f,rate)==0);
        CHECK(c.step(true,1,false,4,nullptr,8,rate)==.25);
        CHECK(c.samples_per_beat()==32);
        CHECK(c.step(true,.375f,false,4,nullptr,9,rate)==.28125);
        CHECK(c.step(true,0,true,4,nullptr,10,rate)==0);
        for (uint32_t f=11; f<16; ++f)
            CHECK(near(c.step(true,0,false,4,nullptr,f,rate),double(f-10)/32));
        CHECK(c.step(true,1,false,4,nullptr,16,rate)==.1875);
        for (uint32_t f=17; f<32; ++f)
            CHECK(c.step(true,0,false,4,nullptr,f,rate)<.4375);
        CHECK(c.step(true,0,false,4,nullptr,32,rate)<.4375 && c.held());
        const double held=c.beat();
        CHECK(c.step(true,0,false,4,nullptr,33,rate)==held);
        CHECK(c.step(true,1,false,4,nullptr,34,rate)==.4375 && !c.held());

        // State round-trip while a gate is latched in the hysteresis band.
        BeatClock restored;
        const auto state=c.save();
        CHECK(restored.restore(state));
        CHECK(restored.save().flags==state.flags);
        auto bad=state; bad.flags=16;
        CHECK(!restored.restore(bad));
        bad=state; bad.samples_per_beat=0;
        CHECK(!restored.restore(bad));
        CHECK(restored.beat()==c.beat() && restored.save().flags==state.flags);
        for (uint32_t f=35; f<80; ++f) {
            const float clock=f<38?.375f:(f%8==0?1.f:0.f);
            CHECK(restored.step(true,clock,false,4,nullptr,f,rate)==
                  c.step(true,clock,false,4,nullptr,f,rate));
            CHECK(restored.held()==c.held());
        }
    }
}

int main(){
 beat_clock_tests();
 finite_samples_tests();
 for(double sr:{44100.,48000.,96000.}){ws::LinearRamp r(0);r.prepare(sr);CHECK(r.next()==0);r.set(1);uint32_t n=static_cast<uint32_t>(sr*.005);for(uint32_t i=1;i<=n;++i)CHECK(std::abs(r.next()-double(i)/n)<1e-12);CHECK(r.constant());r.set(.2);r.reset();CHECK(r.next()==.2);}
 ws::Schmitt gate;CHECK(!gate.process(.5f));CHECK(gate.process(.51f));CHECK(gate.process(.25f));CHECK(!gate.process(.24f));
 ws::Trigger trig;trig.prepare(44100);trig.fire();int high=0;for(int i=0;i<100;++i)high+=trig.next()>0;CHECK(high==45);
 ws::Random a,b,c;a.seed(123,0);b.seed(123,0);c.seed(123,1);bool different=false;for(int i=0;i<500;++i){auto x=a.next();CHECK(x==b.next());different|=x!=c.next();}CHECK(different);
 alignas(16) float x[]={1,2,3,4},y[]={4,3,2,1},z[4];(ws::simd::f4::load(x)*ws::simd::f4::load(y)+ws::simd::f4(2)).store(z);for(int i=0;i<4;++i)CHECK(z[i]==x[i]*y[i]+2);
 double maximum=0;for(int i=-10000;i<=10000;++i){float t=float(i)/40000;maximum=std::max(maximum,std::abs(double(ws::fastmath::tan_small(t))-std::tan(double(t))));}CHECK(maximum<6e-8);
 auto log=ws::param("f","F",20,20000,1000,"Hz",0,WS2_LOG);CHECK(std::abs(ws::to_plain(log,.5)-std::sqrt(20.*20000))<1e-8);CHECK(std::abs(ws::to_normal(log,1000)-ws::to_normal(log,ws::to_plain(log,ws::to_normal(log,1000))))<1e-12);
 struct Pool {alignas(64) unsigned char arena[4096];size_t used=0;} pool;
 ws2_host host{sizeof(host),&pool,[](void*p,size_t n,size_t align,uint32_t)->void*{auto&v=*static_cast<Pool*>(p);v.used=(v.used+align-1)&~(align-1);if(v.used+n>4096)return nullptr;void*r=v.arena+v.used;v.used+=n;return r;}};
 auto*d=ws::Module<Mini>::descriptor();void*instance=d->create(&host);CHECK(instance);
 ws2_config cfg{sizeof(cfg),48000,32,16,123,nullptr,0};CHECK(d->prepare(instance,&cfg,&host)==WS2_OK);
 alignas(32) float storage[16][32]{};float*outputs[16];for(int j=0;j<16;++j)outputs[j]=storage[j];
 alignas(32) float input[32]={.25f},gain[32]={2};const float*ip[]={input};const float*gp[]={gain};
 ws2_signal in{sizeof(in),ip,1,WS2_CONSTANT|WS2_CONNECTED},parameter{sizeof(parameter),gp,1,WS2_CONSTANT};
 ws2_signal_out out{sizeof(out),outputs,1,0,16};ws2_process ctx{};ctx.struct_size=sizeof(ctx);ctx.frames=17;ctx.sample_rate=48000;ctx.channels=4;ctx.input_count=1;ctx.output_count=1;ctx.param_count=1;ctx.inputs=&in;ctx.params=&parameter;ctx.outputs=&out;
 // G5: even poisoned appended fields are absent at the pre-E5 process size.
 auto legacy=ctx;legacy.struct_size=offsetof(ws2_process,data_count);
 legacy.data_count=UINT32_MAX;legacy.data=nullptr;
 CHECK(d->process(instance,&legacy)==WS2_OK);
 auto allocated=pool.used;CHECK(d->process(instance,&ctx)==WS2_OK);CHECK(pool.used==allocated);CHECK(out.channels==4&&(out.flags&WS2_CONSTANT));for(int j=0;j<4;++j)CHECK(storage[j][0]==.5f);
 float scratch[17]{};ws::Signal signal(&in);CHECK(signal.row(3,scratch,17)==scratch);for(float v:scratch)CHECK(v==.25f);
 in.flags=WS2_CONNECTED;CHECK(signal.row(0,scratch,17)==input);in.flags|=WS2_CONSTANT;
 ws::Signal missing(nullptr);CHECK(missing.row(0,scratch,17)==scratch);for(float v:scratch)CHECK(v==0);
 input[0]=std::nanf("");CHECK(d->process(instance,&ctx)==WS2_INVALID);CHECK(storage[0][0]==0);input[0]=.25f;
 ctx.frames=33;CHECK(d->process(instance,&ctx)==WS2_INVALID);ctx.frames=17;ctx.struct_size=0;CHECK(d->process(instance,&ctx)==WS2_INVALID);ctx.struct_size=sizeof(ctx);
 storage[0][0]=99;CHECK(d->process(nullptr,&ctx)==WS2_INVALID);CHECK(storage[0][0]==0);
 for(int failure=0;failure<4;++failure){auto invalid=ctx;storage[0][0]=99;
  if(failure==0)invalid.frames=33;
  if(failure==1)invalid.sample_rate=44100;
  if(failure==2)invalid.param_count=0;
  if(failure==3){invalid.events.struct_size=sizeof(ws2_event_list);invalid.events.count=1;invalid.events.items=nullptr;}
  CHECK(d->process(instance,&invalid)==WS2_INVALID);CHECK(storage[0][0]==0);CHECK(out.flags&WS2_CONSTANT);
 }
 for(int failure=0;failure<6;++failure){ws2_event e{};e.struct_size=sizeof(e);e.type=WS2_NOTE_ON;
  if(failure==0)e.value2=std::nanf("");if(failure==1)e.ump_words=5;if(failure==2)e.type=0;
  if(failure==3)e.bytes=WS2_MAX_PAYLOAD+1;if(failure==4)e.bytes=1;if(failure==5)e.struct_size=0;
  auto invalid=ctx;invalid.events={sizeof(ws2_event_list),1,&e};storage[0][0]=99;
  CHECK(d->process(instance,&invalid)==WS2_INVALID);CHECK(storage[0][0]==0);
 }
 d->reset(instance);d->destroy(instance);CHECK(pool.used==allocated);
 auto *dd=ws::Module<MiniData>::descriptor();
 CHECK(dd->data_slot_count==1&&dd->data_slots[0].field_count==4&&dd->data_slots[0].bytes==sizeof(SdkData));
 void *di=dd->create(&host);CHECK(di&&dd->prepare(di,&cfg,&host)==WS2_OK);
 alignas(16) SdkData data{};data.value=.625f;
 ws2_data view{sizeof(view),&data,sizeof(data),7};
 ctx.data_count=1;ctx.data=&view;
 CHECK(dd->process(di,&ctx)==WS2_OK&&storage[0][0]==.625f);
 ctx.struct_size=offsetof(ws2_process,data_count);CHECK(dd->process(di,&ctx)==WS2_INVALID);
 ctx.struct_size=sizeof(ctx);ctx.data=nullptr;CHECK(dd->process(di,&ctx)==WS2_INVALID);
 dd->destroy(di);
 std::puts("PASS SDK ramp/gate/trigger/PRNG/SIMD/taper/fastmath");
}
