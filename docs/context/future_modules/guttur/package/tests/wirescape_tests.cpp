// SPDX-License-Identifier: GPL-3.0-only
// ABI2 callback-level integration test (compiled inside a Wirescape checkout).
#include "../dsp.h"
#if __has_include("../../tests2/allocation_watch.h")
#include "../../tests2/allocation_watch.h"
#define GUTTUR_HAS_ALLOCATION_WATCH 1
#endif
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
#define REQUIRE(x) do{if(!(x)){std::fprintf(stderr,"FAIL %s:%d %s\n",__FILE__,__LINE__,#x);std::abort();}}while(0)
struct Arena {
 std::vector<uint8_t>data;
 size_t used=0;
 explicit Arena(size_t cap):data(cap){}
 static void* WS2_CALL allocate(void*ctx,size_t bytes,size_t align,uint32_t){
  auto&a=*static_cast<Arena*>(ctx);
  const uintptr_t base=reinterpret_cast<uintptr_t>(a.data.data());
  const uintptr_t next=(base+a.used+align-1)&~(uintptr_t(align)-1);
  const size_t end=next-base+bytes;
  if(end>a.data.size())return nullptr;
  a.used=end;return reinterpret_cast<void*>(next);
 }
};
int main(){
 using M=guttur::abi2::Module;
 auto*d=ws::Module<M>::descriptor();
 REQUIRE(d && d->abi_version==WS_ABI2_VERSION && d->param_count==37);
 REQUIRE(d->input_count==1 && d->output_count==2);
 ws2_config c{};c.struct_size=sizeof(c);c.sample_rate=48000;c.max_block_frames=256;c.max_channels=16;c.seed=17;
 ws2_memory mem{};mem.struct_size=sizeof(mem);
 REQUIRE(d->memory_requirements(&c,&mem)==WS2_OK);
 Arena arena(mem.fast_bytes+mem.large_bytes+1024*1024);
 ws2_host host{sizeof(host),&arena,&Arena::allocate};
 void*inst=d->create(&host);REQUIRE(inst);
 REQUIRE(d->prepare(inst,&c,&host)==WS2_OK);
 std::array<float,256>L{},R{};
 float* lrows[16]{};float* rrows[16]{};
 for(int k=0;k<16;k++){lrows[k]=L.data();rrows[k]=R.data();}
 ws2_signal_out out[2]{{sizeof(ws2_signal_out),lrows,1,0,16},{sizeof(ws2_signal_out),rrows,1,0,16}};
 std::array<float,37>values{};std::array<const float*,37>ptrs{};
 std::array<ws2_signal,37>params{};
 for(uint32_t i=0;i<37;i++){
  values[i]=M::params[i].initial;ptrs[i]=&values[i];
  params[i]={sizeof(ws2_signal),&ptrs[i],1,WS2_CONSTANT};
 }
 ws2_signal inputs[]{ {sizeof(ws2_signal),nullptr,0,WS2_CONSTANT} };
 ws2_event on{};on.struct_size=sizeof(on);on.type=WS2_NOTE_ON;on.offset=0;on.port=0;
 on.source_id=42;on.note_id=7;on.channel=0;on.key=48;on.value=1;
 ws2_event_list events{sizeof(ws2_event_list),1,&on};
 ws2_process ctx{};ctx.struct_size=sizeof(ctx);ctx.frames=128;ctx.sample_rate=48000;
 ctx.channels=1;ctx.inputs=inputs;ctx.input_count=1;ctx.outputs=out;ctx.output_count=2;
 ctx.param_count=37;ctx.params=params.data();ctx.events=events;
 double peak=0;
 for(int i=0;i<30;i++){
  if(i==1)events.count=0;
#ifdef GUTTUR_HAS_ALLOCATION_WATCH
  {
    allocation_watch::Scope watch;
    REQUIRE(d->process(inst,&ctx)==WS2_OK);
    REQUIRE(watch.allocations()==0);
  }
#else
  REQUIRE(d->process(inst,&ctx)==WS2_OK);
#endif
  REQUIRE(out[0].channels==1 && out[1].channels==1);
  REQUIRE(!(out[0].flags&WS2_CONSTANT));
  for(int j=0;j<128;j++){
   REQUIRE(std::isfinite(L[j]) && std::isfinite(R[j]));
   peak=std::max({peak,double(std::abs(L[j])),double(std::abs(R[j]))});
  }
  ctx.frame_position+=128;
 }
 REQUIRE(peak>1e-7 && peak<=.891001);
 REQUIRE(d->latency_frames(inst)==120);
 auto off=on;off.type=WS2_NOTE_OFF;events.items=&off;events.count=1;
 REQUIRE(d->process(inst,&ctx)==WS2_OK);
 d->reset(inst);d->destroy(inst);
 std::printf("PASS abi2_guttur: peak=%g latency=120 memory=%zu\n",peak,mem.large_bytes);
}
