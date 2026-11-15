// SPDX-License-Identifier: GPL-3.0-only
#include "guttur/engine.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <iostream>
#include <vector>
int main(int argc,char**argv){
 const int blocks=argc>1?std::max(100,std::atoi(argv[1])):3000;
 for(int nvoices:{1,16}){
  guttur::Engine e;if(!e.prepare(48000,128)){std::cerr<<"prepare fail\n";return 1;}
  e.loadPreset("growl");e.setParam(guttur::Param::throats,1);e.setParam(guttur::Param::rasp,1);
  e.setParam(guttur::Param::creak,1);e.setParam(guttur::Param::growl,1);
  for(int n=0;n<nvoices;n++)e.noteOn(n+1,32+(n%16),1);
  std::array<float,128>L{},R{};for(int i=0;i<256;i++)e.process(L.data(),R.data(),128);
  std::vector<double>us(blocks);
  for(auto&t:us){auto t0=std::chrono::steady_clock::now();e.process(L.data(),R.data(),128);
   t=std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-t0).count();}
  std::sort(us.begin(),us.end());std::cout<<"{\"throats\":"<<nvoices<<",\"blocks\":"<<blocks
    <<",\"p50_us\":"<<us[blocks/2]<<",\"p95_us\":"<<us[size_t(blocks*.95)]
    <<",\"worst_us\":"<<us.back()<<",\"period_us\":2666.667}\n";
 }
}
