// SPDX-License-Identifier: GPL-3.0-only
#include "guttur/engine.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <vector>
static std::atomic<int> allocations{0};static std::atomic<bool> watch{false};
void*operator new(std::size_t n){if(watch.load())allocations++;if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void*operator new[](std::size_t n){if(watch.load())allocations++;if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void operator delete(void*p)noexcept{std::free(p);}void operator delete[](void*p)noexcept{std::free(p);}
void operator delete(void*p,std::size_t)noexcept{std::free(p);}void operator delete[](void*p,std::size_t)noexcept{std::free(p);}
#define REQUIRE(x) do{if(!(x)){std::fprintf(stderr,"FAIL: %s:%d %s\n",__FILE__,__LINE__,#x);std::exit(1);}}while(0)
static std::vector<float>render(uint32_t block,double rate=48000){
 guttur::Engine e;REQUIRE(e.prepare(rate,std::max(block,512u),17));
 REQUIRE(e.loadPreset("clean"));REQUIRE(e.setParam(guttur::Param::throats,1));
 const uint32_t N=8192;std::vector<float>L(N),R(N);
 REQUIRE(e.noteOn(4,48,1.));
 uint32_t pos=0;watch=true;
 while(pos<N){const uint32_t n=std::min(block,N-pos);e.process(L.data()+pos,R.data()+pos,n);pos+=n;}
 watch=false;REQUIRE(allocations.load()==0);
 for(uint32_t i=0;i<N;i++){REQUIRE(std::isfinite(L[i]));REQUIRE(std::isfinite(R[i]));REQUIRE(std::abs(L[i])<=.891001f);REQUIRE(std::abs(R[i])<=.891001f);}
 return L;
}

// Parameter targets and sample-offset note events must follow absolute frame time,
// never the host's callback boundaries. This also exercises a live wet/master sweep.
static std::vector<float>render_automation(uint32_t block){
 guttur::Engine e;REQUIRE(e.prepare(48000,4096,123));
 REQUIRE(e.loadPreset("growl"));REQUIRE(e.setParam(guttur::Param::throats,2));
 constexpr uint32_t total=8192;std::vector<float>L(total),R(total);
 uint32_t pos=0;
 while(pos<total){
  if(pos==0)REQUIRE(e.noteOn(501,55,.8));
  if(pos==1337){REQUIRE(e.setParam(guttur::Param::wet,.95));REQUIRE(e.setParam(guttur::Param::level,-8));}
  if(pos==2763)REQUIRE(e.noteOn(502,48,1));
  if(pos==4211)e.noteOff(501);
  if(pos==5777)e.noteOff(502);
  uint32_t n=std::min(block,total-pos);
  for(auto next:{1337u,2763u,4211u,5777u})if(pos<next)n=std::min(n,next-pos);
  watch=true;e.process(L.data()+pos,R.data()+pos,n);watch=false;
  pos+=n;
 }
 REQUIRE(allocations.load()==0);
 for(auto x:L)REQUIRE(std::isfinite(x)&&std::abs(x)<=.891001f);
 return L;
}
static void test_ensemble_and_release(){
 guttur::Engine e;REQUIRE(e.prepare(48000,256,17));
 e.loadPreset("clean");REQUIRE(e.setParam(guttur::Param::throats,1));
 for(int i=0;i<16;i++)REQUIRE(e.noteOn(100+i,40+i,.8));
 REQUIRE(!e.noteOn(1000,60,.8));
 std::array<float,256>L{},R{};
 for(int k=0;k<16;k++)e.process(L.data(),R.data(),256);
 auto t=e.telemetry();REQUIRE(t.active_notes==16&&t.active_throats<=16);
 e.allOff();
 for(int k=0;k<1000;k++)e.process(L.data(),R.data(),256);
 t=e.telemetry();REQUIRE(t.active_notes==0);
 REQUIRE(e.noteOn(2000,64));
}

int main(){
 for(auto k:guttur::kParamDefs)REQUIRE(k.minimum<=k.initial&&k.initial<=k.maximum);
 const auto a=render(128),b=render(1),c=render(17),d=render(512),f=render(4096);
 REQUIRE(a==b);REQUIRE(a==c);REQUIRE(a==d);REQUIRE(a==f);
 const auto mod_a=render_automation(1),mod_b=render_automation(17),mod_c=render_automation(128),mod_d=render_automation(4096);
 REQUIRE(mod_a==mod_b&&mod_a==mod_c&&mod_a==mod_d);
 test_ensemble_and_release();
 bool voiced=false;for(float x:a)if(std::abs(x)>1e-8)voiced=true;REQUIRE(voiced);
 {guttur::Engine e;REQUIRE(e.prepare(48000,512));REQUIRE(e.latencyFrames()==120);
  REQUIRE(e.noteOn(10,50));REQUIRE(!e.noteOn(10,50));
  e.noteOff(555); // Stale identity is ignored.
  REQUIRE(e.noteOn(11,55));e.noteOff(10);e.allOff();
  REQUIRE(!e.setParam(guttur::Param::pressure,std::nan("")));
  REQUIRE(e.setParam(guttur::Param::throats,16));REQUIRE(e.getParam(guttur::Param::throats)==8);
  std::vector<uint8_t>bytes(e.stateBytes());REQUIRE(e.saveState(bytes.data(),bytes.size())==bytes.size());
  bytes[0]^=1;REQUIRE(!e.loadState(bytes.data(),bytes.size()));bytes[0]^=1;REQUIRE(e.loadState(bytes.data(),bytes.size()));
  std::vector<float> x(2048),y(2048);e.process(x.data(),y.data(),2048);
  for(int i=0;i<16;i++)REQUIRE(e.noteOn(100+i,42+i,1));
  REQUIRE(!e.noteOn(999,60));e.allOff();
 }
 REQUIRE(render(128,44100).size()==8192);
 REQUIRE(render(128,96000).size()==8192);
 {guttur::Engine e;REQUIRE(e.prepare(48000,128));REQUIRE(e.noteOn(1,48));
  std::vector<float>a(1024),b(1024),aa(1024),bb(1024);e.process(a.data(),b.data(),1024);
  e.reset();REQUIRE(e.noteOn(1,48));e.process(aa.data(),bb.data(),1024);
  REQUIRE(a==aa&&b==bb);
 }
 std::puts("PASS: parameter ranges, block/automation/event matrix, no allocation, reset, IDs, 16-throat release, state, rates, finite output");
}
