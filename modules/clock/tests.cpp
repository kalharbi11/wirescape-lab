// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include <cstring>
#include "../../tests/native/abi2/utility_port_tests.h"
static void rounded_ticks_run_reset(){auto f=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor());std::fill_n(f->input[0][0],256,0);f->parameter[1][0][0]=1.6f;int high=0;for(int block=0;block<30;++block){f->run();for(int i=0;i<256;++i)high+=f->output[0][0][i]==1;}VERIFY(high==6000);f->parameter[3][0][0]=.49f;f->run(17);for(int i=0;i<17;++i)VERIFY(f->output[0][0][i]==0);f->parameter[3][0][0]=.5f;std::fill_n(f->input[0][0],256,.5f);f->run(1);VERIFY(f->output[0][0][0]==1);bool low=false;for(int block=0;block<30;++block){f->run();for(int i=0;i<256;++i)low|=f->output[0][0][i]==0;}VERIFY(low);f->input[0][0][0]=0;f->run(1);f->input[0][0][0]=1;f->run(1);VERIFY(f->output[0][0][0]==1);}
// M3 TR2 (0008 decision 7): sync=0 is the unchanged free-running clock; sync=1 follows the host beat.
static void sync_default_ignores_host(){auto a=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor()),b=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor());VERIFY(a->parameter[4][0][0]==0);ws2_transport t{sizeof(t),WS2_PLAYING,73,.37,0,4,4,0,0};b->process.transport=&t;for(auto*f:{a.get(),b.get()})std::fill_n(f->input[0][0],256,0);for(int block=0;block<200;++block){a->run();b->run();t.beat+=1.3;t.flags=block%3?WS2_PLAYING:0;for(int i=0;i<256;++i)VERIFY(std::memcmp(&a->output[0][0][i],&b->output[0][0][i],sizeof(float))==0);}}
static int count_rises(const float*x,int n,float&prev){int r=0;for(int i=0;i<n;++i){if(x[i]==1&&prev==0)++r;prev=x[i];}return r;}
static void sync_follows_host_beat(){
 for(float bpm_param:{20.f,300.f}){auto f=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor());std::fill_n(f->input[0][0],256,0);std::fill_n(f->parameter[4][0],256,1.f);std::fill_n(f->parameter[0][0],256,bpm_param);std::fill_n(f->parameter[1][0],256,4.f);
  ws2_transport t{sizeof(t),WS2_PLAYING,90,0,0,4,4,0,0};f->process.transport=&t;const double per_block=256*90./(60.*48000);float prev=0;int rises=0,high=0;
  // 90 BPM at 48 kHz: one beat is 32000 samples, so 500 blocks of 256 are exactly 4 beats.
  for(int block=0;block<500;++block){f->run();rises+=count_rises(f->output[0][0],256,prev);for(int i=0;i<256;++i)high+=f->output[0][0][i]==1;t.beat+=per_block;}
  VERIFY(rises==16);VERIFY(std::abs(high-64000)<=16);} // bpm parameter ignored; 4 ticks per beat at duty .5.
 {auto f=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor());std::fill_n(f->input[0][0],256,1.f);std::fill_n(f->parameter[4][0],256,1.f);
  ws2_transport t{sizeof(t),0,120,.25,0,4,4,0,0};f->process.transport=&t;f->run();for(int i=0;i<256;++i)VERIFY(f->output[0][0][i]==0); // host stopped: nothing
  t.flags=WS2_PLAYING;t.beat=.25;f->run(1);VERIFY(f->output[0][0][0]==1);t.beat=.5;f->run(1);VERIFY(f->output[0][0][0]==0); // locate; reset input does not move a derived phase
  t.beat=1.;f->run(1);VERIFY(f->output[0][0][0]==1);std::fill_n(f->parameter[3][0],256,0.f);f->run(1);VERIFY(f->output[0][0][0]==0);
  f->process.transport=nullptr;std::fill_n(f->parameter[3][0],256,1.f);f->run();for(int i=0;i<256;++i)VERIFY(f->output[0][0][i]==0);}
 {auto a=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor()),b=std::make_unique<DspFixture>(ws::Module<ws2ports::Clock>::descriptor()); // two followers agree after a locate
  ws2_transport t{sizeof(t),WS2_PLAYING,133,7.125,0,4,4,0,0};for(auto*f:{a.get(),b.get()}){std::fill_n(f->input[0][0],256,0);std::fill_n(f->parameter[4][0],256,1.f);f->process.transport=&t;}a->run();a->run();b->run();for(int i=0;i<256;++i)VERIFY(a->output[0][0][i]==b->output[0][0][i]);}
}
int main(int argc,char**argv){rounded_ticks_run_reset();sync_default_ignores_host();sync_follows_host_beat();return utility_port_tests("clock",argc,argv,1);}
