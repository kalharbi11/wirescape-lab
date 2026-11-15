// SPDX-License-Identifier: GPL-3.0-only
#include "benchmark_graph.h"
#include "../../tests2/dsp_fixture.h"
#include "../../tests2/module_loader.h"
#include "wirescape/engine.h"
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <vector>
using namespace wirescape::engine2;
struct Measurement {double mean=0,worst=0,p99=0;std::array<double,5>means{};std::vector<double>times;};
template<class F>void measure(Measurement&row,uint32_t repetition,F call){
 double sum=0;
 for(int i=0;i<800;++i){auto start=std::chrono::steady_clock::now();VERIFY(call()==0);double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();row.times.push_back(ns);sum+=ns;}
 row.means[repetition]=sum/800;
}
int main(int argc,char**argv){
 VERIFY(argc==3||argc==5);
 uint32_t block=256;
 if(argc==5){
  VERIFY(std::strcmp(argv[3],"--block")==0);
  char*end=nullptr;const auto size=std::strtoul(argv[4],&end,10);
  VERIFY(end!=argv[4]&&*end=='\0'&&(size==64||size==128||size==256));
  block=static_cast<uint32_t>(size);
 }
 ModuleLoader loader(argv[1]);ws_engine_config c{sizeof(c),48000,block,32,1024};std::unique_ptr<ws_engine,decltype(&ws_engine_destroy)>old(ws_engine_create(&c),ws_engine_destroy);VERIFY(old);
 const char*names[]={"vco","vcf","vca"};for(uint32_t i=0;i<3;++i){auto*d=loader.abi1(names[i]);VERIFY(ws_engine_register_module(old.get(),d)==0);VERIFY(ws_engine_add_node(old.get(),i+1,d->id)==0);}VERIFY(ws_engine_connect(old.get(),1,0,2,0)==0);VERIFY(ws_engine_connect(old.get(),2,1,3,0)==0);VERIFY(ws_engine_prepare(old.get(),3,0)==0);
 auto mono=make(1,false),poly=make(8,false),modulated=make(1,true);std::vector<std::unique_ptr<Engine>>eight;for(int i=0;i<8;++i)eight.push_back(make(1,false));
 auto fixed=std::make_unique<DspFixture>(ws::Module<ws2ports::Vcf>::descriptor()),varying=std::make_unique<DspFixture>(ws::Module<ws2ports::Vcf>::descriptor());varying->pars[0].flags=0;for(uint32_t i=0;i<block;++i)varying->parameter[0][0][i]=1000+500*std::sin(.03f*i);
 float buffer[256]{};float*out[]={buffer};Measurement rows[7];
 auto call=[&](int which){switch(which){
 case 0:return ws_engine_render(old.get(),buffer,block);
 case 1:return mono->render(out,1,block);
 case 2:return poly->render(out,1,block);
 case 3:for(auto&e:eight)if(e->render(out,1,block))return 1;return 0;
 case 4:return modulated->render(out,1,block);
 case 5:fixed->run(block);return 0;
 default:varying->run(block);return 0;}};
 for(int c=0;c<7;++c){rows[c].times.reserve(4000);for(int i=0;i<256;++i)VERIFY(call(c)==0);}
 for(uint32_t repetition=0;repetition<5;++repetition)for(int c=0;c<7;++c)measure(rows[c],repetition,[&](){return call(c);});
 for(auto&row:rows){auto means=row.means;std::sort(means.begin(),means.end());row.mean=means[2];std::sort(row.times.begin(),row.times.end());row.worst=row.times.back();row.p99=row.times[3960];}
 FILE*f=std::fopen(argv[2],"w");VERIFY(f);const char*labels[]={"abi1_mono","abi2_mono","abi2_poly8","abi2_eight_mono","abi2_modulated","vcf_constant","vcf_audio_rate_cutoff"};std::fprintf(f,"{\"sample_rate\":48000,\"frames\":%u,\"warmup_blocks\":256,\"measured_blocks\":4000,\"repetitions\":5,\"blocks_per_repetition\":800,\"rows\":[",block);
 for(int i=0;i<7;++i)std::fprintf(f,"%s{\"name\":\"%s\",\"mean_ns\":%.3f,\"worst_ns\":%.3f,\"p99_ns\":%.3f,\"repetition_means_ns\":[%.3f,%.3f,%.3f,%.3f,%.3f]}",i?",":"",labels[i],rows[i].mean,rows[i].worst,rows[i].p99,rows[i].means[0],rows[i].means[1],rows[i].means[2],rows[i].means[3],rows[i].means[4]);
 std::fprintf(f,"],\"mono_ratio\":%.9g,\"poly8_vs_eight_mono_ratio\":%.9g,\"modulated_ratio\":%.9g}\n",rows[1].mean/rows[0].mean,rows[2].mean/rows[3].mean,rows[4].mean/rows[1].mean);std::fclose(f);
 std::printf("ABI2/ABI1 mono %.3fx; poly8/eight-mono %.3fx; modulated/unmodulated %.3fx\n",rows[1].mean/rows[0].mean,rows[2].mean/rows[3].mean,rows[4].mean/rows[1].mean);
}
