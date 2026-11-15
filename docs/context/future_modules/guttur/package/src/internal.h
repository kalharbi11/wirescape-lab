// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "guttur/parameters.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
namespace guttur::detail {
constexpr double PI=3.141592653589793238462643383279502884, TAU=2*PI, LN2=.6931471805599453094;
constexpr int NR=17, NLEV=8, NH=160, NRES=10, NS=34, M=32768, FLOW=256, GRID=9*5*5*4;
constexpr int TABLE_TOTAL=831368;
constexpr double RD_MIN=.3,RD_MAX=2.7,RD_STEP=(RD_MAX-RD_MIN)/16., L_REF=17.5, SOUND=35000.;
inline double clamp(double x,double a,double b){return x<a?a:x>b?b:x;}
inline double lerp(double a,double b,double t){return a+(b-a)*t;}
inline double smooth(double a,double b,double x){const double t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);}
inline double db(double x){return std::pow(10.,x/20.);}
inline uint32_t hash(int32_t a,int32_t b,int32_t c,int32_t d){
 uint32_t h=2166136261u^uint32_t(a);h=(h^uint32_t(b))*16777619u;h=(h^uint32_t(c))*2246822519u;h=(h^uint32_t(d))*3266489917u;
 h^=h>>15;h*=2246822519u;h^=h>>13;h*=3266489917u;h^=h>>16;return h;
}
inline double h01(int32_t a,int32_t b,int32_t c,int32_t d){return hash(a,b,c,d)/4294967296.;}
inline double h11(int32_t a,int32_t b,int32_t c,int32_t d){return h01(a,b,c,d)*2-1;}
inline uint32_t xorshift(uint32_t& s){s^=s<<13;s^=s>>17;s^=s<<5;return s;}
inline double rnd(uint32_t& s){return xorshift(s)/4294967296.;}
inline double gauss(uint32_t& s){return (rnd(s)+rnd(s)+rnd(s)+rnd(s)-2)*1.7320508;}
struct Pulse {
 std::array<float,TABLE_TOTAL> data{};
 std::array<float,NR*(FLOW+1)> flow{};
 std::array<float,NR*NH> harm{};
 std::array<float,NR> te{};
 std::array<int,NLEV> sizes{},hmax{},base{};
 void build(double*re,double*im,double*xr,double*xi) noexcept;
};
struct Tube {
 std::array<float,GRID*NRES> F{},Am{};
 std::array<float,GRID> minA{};
 void build() noexcept;
 double lookup(double vowel,double pharynx,double mouth,double ring,double*outF,double*outA)const noexcept;
};
double bandwidth(double F,int n,double rd,double minA) noexcept;
struct Biquad {
 double b0=1,b1=0,b2=0,a1=0,a2=0,z1=0,z2=0;
 enum Type {LowShelf,HighShelf,Peak,BandPass,HighPass,LowPass};
 void set(Type,double f,double q,double dB,double sr)noexcept;
 double tick(double x)noexcept {const double y=b0*x+z1;z1=b1*x-a1*y+z2;z2=b2*x-a2*y;return y;}
 void reset()noexcept{z1=z2=0;}
};
struct Room {
 double sr=48000,size=1.075,rt=1.8,cLo=0,cHi=0;
 std::array<std::array<float,8192>,8> lines{};
 std::array<float,8192> pre{};
 std::array<double,8> base{},d{},gL{},gM{},gH{},lo{},hi{},mph{},dStart{},dInc{},v{};
 std::array<int,6> tapsD{};
 std::array<double,6> tapsL{},tapsR{};
 Biquad hpIn{},hpIn2{};
 uint32_t w=0,pw=0;int preD=0,idle=0;uint32_t control_rem=0;
 void prepare(double rate)noexcept;
 void set(double room,double decay)noexcept;
 void reset()noexcept;
 void control(uint32_t n=128)noexcept;
 void sample(double input,double&left,double&right,double wet)noexcept;
};
struct Calibration {
 double jitter=.87,shimmer=.95,voice=.1743,lowMidTarget=14,afterTrim=-6.5,preDrive=.25;
};
struct Singer {
 bool active=false,voicing=false,gate=false,unvoiced=false,closureFirst=false,coefInit=false,hpInit=false,driveOn=false,carrier=true,farR=false;
 int slot=0,index=0,midi=60,role=0,group=1,lod=NRES,first=0,breakN=0,parity=0,gap=0,lev=0,rdA=0,tabRd=0;double breakR=1;
 int64_t ownerId=0;uint64_t seq=0;
 uint32_t rng=1,noiseRng=1,cycN=0,itdW=0,silentBlocks=0,killFade=0,driveFadeLeft=0;
 double pendingAt=-1,pendingStop=-1, pendingScoop=0,pendingSettle=.1,pendingLevel=1;
 double L=17.5,az=0,dist=.15,lagMs=0,detune=0,levelDb=0,vowelOff=0,coupling=.5,looseWander=0;
 double baseHz=261.6256,fLow=92,fCur=110,fNow=110,scoop=0,scoopTau=.1,style=.45,pT=0,p=0,V=0,pLevel=0;
 double trem[3]{},tremR[3]{},vibPh=0,wanderS=0,wanderV=0;
 double ph=0,inc=0,amp=0,ampT=0,rdW=0,rdNow=1.2,raspC=0,reg=0;
 double noiseA=0,noiseAT=0,noiseStep=0,breathFloor=.12,asp1=0,fl1=0,fl2=0,flg=0,flk=0,flNorm=0,flDepth=0;
 double norm=1,normT=1,lnF=0,lnRd=0,lnL=0;
 double ic1[NRES]{},ic2[NRES]{},ca1[NRES]{},ca2[NRES]{},ca3[NRES]{},ta1[NRES]{},ta2[NRES]{},ta3[NRES]{},ca[NRES]{},ta[NRES]{},F[NRES]{},B[NRES]{},Fbuf[NRES]{},Abuf[NRES]{};
 double cStep1[NRES]{},cStep2[NRES]{},cStep3[NRES]{},aStep[NRES]{};
 double hp1=0,hp2=0,hp_1=0,hp_2=0,hp_3=0,hpT1=0,hpT2=0,hpT3=0,hpS1=0,hpS2=0,hpS3=0;
 double driveT=0,xPrev=0,gainT=0,gainCur=0,gainStep=0,gainExtra=1;
 double gLT=0,gRT=0,gL=0,gR=0,gLStep=0,gRStep=0,sendT=0,revS=0,sendStep=0;bool spaceInit=false;
 double dlp=0,flp=0,dlpC=0,shadowC=0,itdT=0,pdel=0,itdStep=0;
 std::array<float,128> itd{};
 double outLev=0,energy=0,vowelNow=.5,mouthNow=.5,Pe_pressure=0,Pe_growl=0;
 double cycle[64*3]{};
 // temporary rows are scalars while rendering; the JS also keeps a 512 frame array.
 void reset(int singerSlot)noexcept;
 void assign(int64_t note_id,int index_,int group_,int note,double velocity,uint32_t seed,const std::array<double,kParamDefs.size()>&P,double time)noexcept;
 void start(double level,double scoop_,double settle)noexcept;
 void stop()noexcept{gate=false;pT=0;}
 void closure(double sr,double sharedJit,bool grit,const std::array<double,kParamDefs.size()>&P,const Calibration&cal,const Pulse&tables)noexcept;
};
}
