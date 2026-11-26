// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include "../../tests/native/abi2/utility_port_tests.h"
static void missing_and_nonfinite(){auto f=std::make_unique<DspFixture>(ws::Module<ws2ports::Slew>::descriptor());std::fill_n(f->input[0][0],256,1);f->run();float held=f->output[0][0][255];VERIFY(held>0);f->ins[0].channels=0;f->ins[0].flags=WS2_CONSTANT;f->run(1);VERIFY(f->output[0][0][0]>0&&f->output[0][0][0]<held);f->ins[0].channels=1;f->ins[0].flags=WS2_CONNECTED;f->parameter[0][0][0]=0;f->run(1);VERIFY(f->output[0][0][0]==1);for(float value:{NAN,INFINITY}){f->input[0][0][0]=value;f->run(1);VERIFY(f->output[0][0][0]==1);}f->reset();}
static void e7c_state_roundtrip(){
 const auto*d=ws::Module<ws2ports::Slew>::descriptor();
 auto a=std::make_unique<DspFixture>(d,48000.,1), b=std::make_unique<DspFixture>(d,48000.,1);
 auto rate=std::make_unique<DspFixture>(d,44100.,1);
 for(auto*f:{a.get(),b.get(),rate.get()}){
  f->parameter[0][0][0]=.031f; f->parameter[1][0][0]=.071f;
  std::fill_n(f->input[0][0],256,1.f);
 }
 a->run(173); a->run(71); const auto saved=port_save(*a);
 VERIFY(port_load(*b,saved)==WS2_OK);
 for(int n=0;n<10;++n){
  for(auto*f:{a.get(),b.get()})std::fill_n(f->input[0][0],256,n<4?1.f:-.5f);
  a->run(127);b->run(127);
  VERIFY(std::memcmp(a->output[0][0],b->output[0][0],127*sizeof(float))==0);
 }
 const auto current=port_save(*b);auto bad=saved;bad[0]=99;
 VERIFY(port_load(*b,bad)==WS2_UNSUPPORTED&&port_save(*b)==current);
 bad=saved;bad.pop_back();
 VERIFY(port_load(*b,bad)==WS2_INVALID&&port_save(*b)==current);
 // Slew state is expressed in level and seconds/unit; C2 permits adaptation.
 // Test rate mismatch explicitly, with a rate-matched level and physical slope oracle.
 VERIFY(port_load(*rate,saved)==WS2_OK);
 const float held=a->output[0][0][0]; (void)held;
 auto at_saved=std::make_unique<DspFixture>(d,48000.,1);
 VERIFY(port_load(*at_saved,saved)==WS2_OK);
 for(auto*f:{rate.get(),at_saved.get()})std::fill_n(f->input[0][0],256,1.f);
 at_saved->parameter[0][0][0]=.031f; at_saved->parameter[1][0][0]=.071f;
 rate->run(147);at_saved->run(160); // equal elapsed seconds
 VERIFY(std::abs(rate->output[0][0][146]-at_saved->output[0][0][159])<1e-6f);
}
int main(int argc,char**argv){e7c_state_roundtrip();missing_and_nonfinite();return utility_port_tests("slew",argc,argv);}
