// SPDX-License-Identifier: GPL-3.0-only
#include "guttur/engine.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
namespace {
void u16(std::ofstream&f,uint16_t n){for(int i=0;i<2;i++)f.put(char(n>>(8*i)));}
void u32(std::ofstream&f,uint32_t n){for(int i=0;i<4;i++)f.put(char(n>>(8*i)));}
void wav(const std::filesystem::path&file,const std::vector<float>&L,const std::vector<float>&R,int rate){
 std::ofstream f(file,std::ios::binary);const uint32_t size=uint32_t(L.size()*4);
 f.write("RIFF",4);u32(f,36+size);f.write("WAVEfmt ",8);u32(f,16);u16(f,1);u16(f,2);u32(f,rate);u32(f,rate*4);u16(f,4);u16(f,16);
 f.write("data",4);u32(f,size);
 for(size_t i=0;i<L.size();i++)for(float x:{L[i],R[i]}){
  const double z=std::clamp(double(x),-1.,1.);
  const int16_t s=int16_t(std::lround(z*32767));u16(f,uint16_t(s));
 }
}
struct Case {const char*id; const char*preset;int throat_count;int notes;bool plain;};
constexpr Case cases[]={
 {"plain","clean",1,1,true},{"clean","clean",3,1,false},{"weathered","weathered",3,1,false},
 {"raspy","raspy",3,1,false},{"chant_voice","chant",3,1,false},{"growl","growl",3,1,false},
 {"fry","fry",3,1,false},{"ayn","ayn",3,1,false},{"ring","ring",3,1,false},
 {"whisper","whisper",3,1,false},{"small","small",3,1,false},{"kargyraa","kargyraa",3,1,false},
 {"ensemble16","clean",8,2,false}};
}
int main(int argc,char**argv){
 std::filesystem::path out="renders_cpp";std::string selected="";int rate=48000;
 for(int i=1;i<argc;i++){
  const std::string a=argv[i];if(a=="--output-dir"&&i+1<argc)out=argv[++i];
  else if(a=="--case"&&i+1<argc)selected=argv[++i];
  else if(a=="--rate"&&i+1<argc)rate=std::stoi(argv[++i]);
  else{std::cerr<<"usage: guttur_offline [--output-dir dir] [--case plain|clean|...|all] [--rate 48000]\n";return 2;}
 }
 std::filesystem::create_directories(out);
 for(const auto&c:cases){if(!selected.empty()&&selected!="all"&&selected!=c.id)continue;
  guttur::Engine e;if(!e.prepare(rate,512,17)){std::cerr<<"prepare failed\n";return 3;}
  if(!e.loadPreset(c.preset)){std::cerr<<"preset failed\n";return 4;}
  e.setParam(guttur::Param::throats,c.throat_count);
  if(c.plain){
   for(auto p:{guttur::Param::breath,guttur::Param::whisper,guttur::Param::jitter,guttur::Param::shimmer,guttur::Param::tremor,
      guttur::Param::wander,guttur::Param::growl,guttur::Param::creak,guttur::Param::tailFry,guttur::Param::flutter,
      guttur::Param::rasp,guttur::Param::breaks,guttur::Param::vibrato,guttur::Param::drive,guttur::Param::spread})e.setParam(p,0);
   e.setParam(guttur::Param::wet,0);e.setParam(guttur::Param::sizeSpread,0);e.setParam(guttur::Param::looseness,0);
  }
  const uint32_t frames=uint32_t(rate*2),noteEnd=uint32_t(rate*.8);
  std::vector<float>L(frames),R(frames);
  e.noteOn(1,48,1.);if(c.notes==2)e.noteOn(2,55,.8);
  uint32_t pos=0;while(pos<frames){if(pos==noteEnd){e.noteOff(1);if(c.notes==2)e.noteOff(2);}
   const uint32_t n=std::min<uint32_t>(128,std::min<uint32_t>(frames-pos,pos<noteEnd?noteEnd-pos:frames-pos));
   e.process(L.data()+pos,R.data()+pos,n);pos+=n;
  }
  wav(out/(std::string(c.id)+".wav"),L,R,rate);
  double sum=0,peak=0;for(uint32_t i=0;i<frames;i++){sum+=L[i]*L[i]+R[i]*R[i];peak=std::max({peak,double(std::abs(L[i])),double(std::abs(R[i]))});}
  std::cout<<c.id<<": RMS="<<std::sqrt(sum/(2*frames))<<" peak="<<peak<<" latency="<<e.latencyFrames()<<" frames\n";
 }
 return 0;
}
