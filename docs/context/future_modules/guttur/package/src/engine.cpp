// SPDX-License-Identifier: GPL-3.0-only
#include "guttur/engine.h"
#include "guttur/presets.h"
#include "internal.h"
#include <atomic>
#include <cstdlib>
#if defined(_MSC_VER)
#include <malloc.h>
#endif
#include <new>
#include <utility>
namespace guttur {
using namespace detail;
namespace {
using Params=std::array<double,kParamDefs.size()>;
inline double get(const Params&p,Param x)noexcept{return p[static_cast<unsigned>(x)];}
inline double hz(int midi)noexcept{return 440.*std::pow(2.,(midi-69.)/12.);}
struct Loose {double lag,slip,scoop,settle,detune,skip,coupling,vowel,level;};
Loose looseTable(double L) noexcept{return {lerp(6,116,L),lerp(2,47,L),lerp(6,76,L),lerp(.06,.28,L),lerp(2,22,L),lerp(0,.12,L),lerp(.5,0,L),lerp(.02,.12,L),lerp(.5,3.5,L)};}
double expectedPower(const Pulse&pt,const Tube&grid,double sr,double f0,double L,double rd)noexcept{
 double F[NRES]{},A[NRES]{},B[NRES]{};
 const double minA=grid.lookup(.5,0,.5,.3,F,A),sc=L_REF/L;
 const double rf=clamp((rd-RD_MIN)/RD_STEP,0,NR-1.001);const int r0=int(rf);const double rw=rf-r0;
 for(int k=0;k<NRES;k++){F[k]*=sc;B[k]=bandwidth(F[k],k,rd,minA);}
 double P=0;
 for(int h=1;h<=NH;h++){
  const double f=h*f0;if(f>7000||f>.45*sr)break;
  const double c=(1-rw)*pt.harm[r0*NH+h-1]+rw*pt.harm[(r0+1)*NH+h-1];
  double hr=0,hi=0;
  for(int k=0;k<NRES;k++){
   const double wk=F[k],q=B[k],dr=wk*wk-f*f,di=f*q,den=dr*dr+di*di,g=A[k]*wk*wk/den;
   hr+=g*dr;hi-=g*di;
  }
  const double f2=f*f,kw=(1+1.5119*f2/(f2+2.25e6))*(f2*f2/(f2*f2+2.1e6));
  P+=c*c*(hr*hr+hi*hi)*kw;
 }
 return P;
}
inline double antiderivative(double x)noexcept{const double a=std::abs(x);return a+std::log1p(std::exp(-2*a))-LN2;}
// C++17 aligned_alloc is not implemented by MSVC. Both paths run only on the
// non-realtime owner during prepare/destroy; Wirescape supplies its own arena.
void* platformAlignedAlloc(size_t bytes,size_t alignment) noexcept {
#if defined(_MSC_VER)
 return _aligned_malloc(bytes,alignment);
#else
 return std::aligned_alloc(alignment,bytes);
#endif
}
void platformAlignedFree(void* p) noexcept {
#if defined(_MSC_VER)
 _aligned_free(p);
#else
 std::free(p);
#endif
}
}
void Singer::reset(int singerSlot)noexcept{
 *this=Singer{};slot=singerSlot;rng=hash(slot,991,7,3)|1u;noiseRng=rng;
}
void Singer::assign(int64_t id,int singerIndex,int groupSize,int note,double velocity,uint32_t seedIn,const Params&P,double /*time*/)noexcept{
 ownerId=id;index=singerIndex;group=groupSize;midi=note;seq=seedIn;
 L=get(P,Param::size);az=get(P,Param::azimuth);dist=get(P,Param::distance);
 baseHz=hz(note);fCur=fNow=baseHz;fLow=92*std::pow(L_REF/L,1.6);
 // Per-singer hashes deliberately reproduce GUTTUR play-mode placement.
 const auto lt=looseTable(get(P,Param::looseness));const int32_t sid=int32_t(seedIn);
 L=clamp(get(P,Param::size)+(index==0?0:h11(sid,11,0,0)*1.6*get(P,Param::sizeSpread)),13,20.5);
 fLow=92*std::pow(L_REF/L,1.6);
 detune=index==0?0:h11(sid,12,0,0)*lt.detune;
 levelDb=index==0?0:-h01(sid,13,0,0)*lt.level;
 vowelOff=index==0?0:h11(sid,14,0,0)*lt.vowel;
 const double spreadDeg=get(P,Param::spread)*70;
 az=clamp(get(P,Param::azimuth)+(group>1?(double(index)/(group-1)-.5)*2*spreadDeg:0)+h11(sid,15,0,0)*6*get(P,Param::spread),-180,180);
 dist=clamp(get(P,Param::distance)+h01(sid,16,0,0)*.12*get(P,Param::spread),0,1);
 lagMs=index==0?0:lt.lag*(.35+.65*h01(sid,17,0,0));
 carrier=index<3||group<=3;lod=(dist>.55&&index>0)?6:NRES;
 coupling=lt.coupling;looseWander=lt.detune*.3;
 for(int i=0;i<3;i++)trem[i]=h01(sid,i+1,0,0)*TAU;
 tremR[0]=4.1+h01(sid,4,0,0)*.8;tremR[1]=5+h01(sid,5,0,0)*.7;tremR[2]=5.9+h01(sid,6,0,0)*.9;
 vibPh=h01(sid,7,0,0)*TAU;
 gainExtra=1;style=get(P,Param::style);active=true;gate=false;voicing=false;p=0;pT=0;
 pendingLevel=velocity;
}
void Singer::start(double level,double scoop_,double settle)noexcept{
 gate=true;pT=level;pendingLevel=level;
 scoop=-scoop_;scoopTau=std::max(.02,settle/2.3);
 if(!voicing)fCur=baseHz*std::pow(2,(detune-scoop_)/1200.);
 first=voicing?0:2;active=true;silentBlocks=0;
}
void Singer::closure(double sr,double sharedJit,bool gritAfter,const Params&P,const Calibration&cal,const Pulse&pt)noexcept{
 const double f=std::max(1.,fCur),regNew=clamp(std::log2(f/fLow)/2.5,0,1);reg=regNew;parity^=1;
 const double grit=gritAfter?0:1;
 const double growl=get(P,Param::growl)*grit,lowG=1-smooth(.2,.48,reg),dbl=growl*lowG,gHi=growl*(1-lowG);
 const double releaseFry=(1-V)*(gate?.15:1)*get(P,Param::tailFry);
 const double creak=clamp(get(P,Param::creak)+releaseFry,0,1)*grit;
 const double lowC=1-smooth(.1,.38,reg),cr=creak*lowC,crackP=creak*(1-lowC)*.05;
 const double c=coupling,sj=get(P,Param::jitter)*grit*.01*cal.jitter;
 double jit=sj*(c*sharedJit+std::sqrt(std::max(0.,1-c*c))*gauss(rng));
 jit+=gHi*.012*gauss(rng);
 double per=sr/f*(1+clamp(jit,-.25,.25));
 const double ss=get(P,Param::shimmer)*grit*.01*cal.shimmer+gHi*.06;
 double a=1+ss*gauss(rng);
 if(dbl>0){if(parity){a*=1-.62*dbl;per*=1+.09*dbl;}else per*=1-.09*dbl;}
 double pulse=per,gapVal=0;
 if(cr>0){pulse=per/(1+1.3*cr);gapVal=per-pulse;
  if(parity){gapVal+=.9*cr*per*(.45+.55*rnd(rng));a*=1-.55*cr*(.4+.6*rnd(rng));}
  if(rnd(rng)<.08*cr)a*=.08;
 }
 if(crackP>0&&rnd(rng)<crackP){if(rnd(rng)<.5)gapVal+=per*(.3+.6*rnd(rng));else a*=.3;jit+=.02*gauss(rng);}
 if(breakN>0){--breakN;pulse/=breakR;gapVal/=breakR;a*=.55;}
 else if(get(P,Param::breaks)>0 && grit){const double near=.25+std::exp(-std::pow((reg-.55)/.12,2));
  if(rnd(rng)<get(P,Param::breaks)*.004*near){breakN=2+int(rnd(rng)*6);breakR=rnd(rng)<.6?1.5:2;}
 }
 const double voiced=V*(1-get(P,Param::whisper));
 double boost=1;if(first>0){boost=1+.5*smooth(.6,1,style);first--;}
 ampT=std::max(0.,a)*voiced*pLevel*boost*norm*(1+cr);
 double rd=lerp(2.3,.62,get(P,Param::pressure))+get(P,Param::breath)*.7-cr*.55-dbl*.25-(boost-1)*.8;
 if(breakN>0)rd+=.6;
 rd=clamp(rd+.05*std::min(1.,ss*12)*gauss(rng),RD_MIN,RD_MAX-1e-6);
 const double rf=(rd-RD_MIN)/RD_STEP;rdA=int(rf);rdW=rf-rdA;tabRd=rdW<.5?rdA:rdA+1;rdNow=rd;
 const double fp=sr/std::max(pulse,1.),lim=.475*sr/fp;
 lev=0;while(lev<NLEV-1&&pt.hmax[lev]>lim)lev++;
 inc=1/std::max(pulse,1.);gap=int(std::floor(gapVal+.5));
 raspC=(get(P,Param::rasp)*grit+gHi*.5+dbl*.25)*(.5+rnd(rng));
 const int k=int(cycN%64)*3;cycle[k]=(pulse+gapVal)/sr*1000;cycle[k+1]=ampT;cycle[k+2]=cr>.3?2:dbl>.3?1:(gapVal>0?3:0);cycN++;
 if(voiced<=.002&&!gate)voicing=false;
}
struct Engine::State {
 double sr=48000;uint32_t max_block=512,ctlLeft=0;uint64_t frame=0,seed=17;
 Pulse pulses{};Tube grid{};Room room{};
 std::array<std::atomic<double>,kParamDefs.size()>targets{};
 std::atomic<double>presetTrimTarget{0};
 Params P{}; Calibration cal{};
 // These buffers are only used during prepare, allowing zero temporary heap allocations.
 std::array<double,M> re{},im{};
 std::array<double,16384> xr{},xi{};
 std::array<Singer,kMaxThroats> singers{};
 struct Note {int64_t id=0;int midi=0;uint64_t seq=0;int size=0;bool released=false;};
 std::array<Note,kMaxNotes>notes{};
 uint64_t noteSeq=0;double time=0,sjT=0,sjA=0,sjB=0,sharedJit=0,lnRef=0,presetTrim=0;
 uint32_t sjN=1,activeCount=0;int focus=-1;
 std::array<Biquad,2>lowSh{},highSh{},lmEq{};Biquad scLM{},scPR{};
 double eLM=1e-9,ePR=1e-9,lmCut=0,lmC=0,lmCStep=0,lmRatio=0,dc[4]{},limG=1,limGR=0;
 std::array<double,1024>limBL{},limBR{},limQv{};
 std::array<int64_t,1024>limQ{};
 uint32_t limW=0;int64_t limIdx=0,limQh=0,limQt=0;
 uint32_t limLook=120;bool gritAfter=false;
 double peak=0,rms=0,rmsAccum=0,peakAccum=0;
 // Hot-path coefficients: derived from sample rate in prepare, not per rendered sample.
 double ampSmooth=0,lowMidEnvelopeCoeff=0,limiterReleaseCoeff=0,limiterAttackCoeff=0;
 // Master and reverb-send output mix are smoothed at the 128-frame control clock.
 double masterGain=1,masterStep=0,wetGain=.392,wetStep=0;
 double gritPre=1,gritTrim=1;
 uint32_t metricFrames=0;double roomSize=-1,roomDecay=-1,body=999,air=999;
 void setTone()noexcept{
  const double b=get(P,Param::body),a=get(P,Param::air);
  if(b!=body||a!=air){for(int i=0;i<2;i++){lowSh[i].set(Biquad::LowShelf,240,.7,b,sr);highSh[i].set(Biquad::HighShelf,2400,.7,a,sr);}body=b;air=a;}
  const double rs=get(P,Param::room),rd=get(P,Param::decay);
  if(rs!=roomSize||rd!=roomDecay){room.set(rs,rd);roomSize=rs;roomDecay=rd;}
  gritAfter=get(P,Param::gritAfter)>.5;
 }
 void reset()noexcept{
  for(int i=0;i<kMaxThroats;i++)singers[i].reset(i);
  notes={};noteSeq=0;focus=-1;activeCount=0;
  room.reset();for(int i=0;i<2;i++){lowSh[i].reset();highSh[i].reset();lmEq[i].reset();}
  scLM.reset();scPR.reset();
  eLM=ePR=1e-9;lmCut=lmC=lmCStep=lmRatio=0;std::fill_n(dc,4,0);
  limBL.fill(0);limBR.fill(0);limQ.fill(0);limQv.fill(0);limW=0;limIdx=limQh=limQt=0;limG=1;limGR=0;
  frame=0;time=0;ctlLeft=0;sjT=sjA=sjB=sharedJit=0;sjN=1;peak=rms=peakAccum=rmsAccum=0;metricFrames=0;
  masterGain=db(get(P,Param::level));masterStep=0;
  wetGain=get(P,Param::wet)*1.4;wetStep=0;
 }
 bool hasNote(int64_t id)const noexcept{for(const auto& n:notes)if(n.id==id)return true;return false;}
 void releaseNote(int64_t id)noexcept{
  for(auto&n:notes)if(n.id==id&&!n.released){
   n.released=true;
   for(auto&s:singers)if(s.ownerId==id){const double lag=s.index==0?0:s.lagMs*.6/1000;
    if(s.pendingAt>=0)s.pendingStop=time+lag+.03;else s.pendingStop=time+lag;
   }
  }
 }
 // Internal note group allocation; bounded to 16 slots and 16 total generators.
 bool addNote(int64_t id,int midi,double vel)noexcept{
  if(hasNote(id))return false;
  Note*target=nullptr;for(auto&n:notes)if(!n.id){target=&n;break;}
  if(!target){for(auto&n:notes)if(n.released){target=&n;break;}}
  if(!target)return false;
  if(target->id){const int64_t old=target->id;for(auto&s:singers)if(s.ownerId==old){s.killFade=1;s.ownerId=0;}*target={};}
  Params desired{};for(unsigned k=0;k<desired.size();k++)desired[k]=targets[k].load(std::memory_order_relaxed);
  const int G=std::clamp(int(std::lround(get(desired,Param::throats))),1,kMaxThroatsPerNote);
  target->id=id;target->midi=midi;target->seq=++noteSeq;target->size=G;target->released=false;
  const auto lt=looseTable(get(desired,Param::looseness));
  const double trimNow=presetTrimTarget.load(std::memory_order_relaxed);
  std::array<bool,kMaxThroats> chosen{};
  for(int i=0;i<G;i++){
   Singer*s=nullptr;
   for(auto&x:singers)if(!chosen[x.slot] && !x.active && x.ownerId==0 && !x.killFade){s=&x;break;}
   if(!s){uint64_t oldest=UINT64_MAX;
    for(auto&x:singers)if(!chosen[x.slot] && x.ownerId){const auto*own=static_cast<const Note*>(nullptr);for(const auto&n:notes)if(n.id==x.ownerId){own=&n;break;}
      const uint64_t priority=(own&&own->released?0ull:1ull)<<62 | (own?own->seq:0);
      if(priority<oldest){oldest=priority;s=&x;}
    }
   }
   if(!s)break;
   chosen[s->slot]=true;
   if(s->ownerId){s->killFade=1;s->pendingStop=-1;} // One 128-sample fade before replacing the voice.
   const int slot=s->slot;const uint32_t oldrng=s->rng;
   if(!s->killFade){s->reset(slot);s->rng=oldrng;}
   // This slot is now owned by the new note. Its assignment keeps old sound during fade if stolen.
   s->ownerId=id;
   if(s->killFade){s->pendingAt=-2; s->seq=target->seq; s->midi=midi;s->index=i;s->group=G;s->pendingLevel=vel;}
   else{
    const uint32_t placeSeed=uint32_t(seed*131+i*7);
    s->assign(id,i,G,midi,vel,placeSeed,desired,time);
    s->gainExtra=std::pow(G,-(.44+.08*(1-get(desired,Param::looseness))))*db(trimNow);
    const double slip=i==0?0:h11(int32_t(target->seq),i,21,0)*lt.slip;
    s->pendingAt=time+std::max(0.,(s->lagMs+slip)/1000.);
    s->pendingScoop=i==0?lt.scoop*.3:lt.scoop*(.4+.6*h01(int32_t(target->seq),i,22,0));
    s->pendingSettle=lt.settle;
   }
   if(i==0)focus=slot;
  }
  return true;
 }
 void finishSteal(Singer&s)noexcept{
  const int slot=s.slot,index=s.index,midi=s.midi,group=s.group;const uint64_t sq=s.seq;
  const int64_t id=s.ownerId;const double vel=s.pendingLevel;
  s.reset(slot);
  if(!hasNote(id))return;
  const auto lt=looseTable(get(P,Param::looseness));
  const uint32_t placeSeed=uint32_t(seed*131+index*7);
  s.assign(id,index,group,midi,vel,placeSeed,P,time);
  s.gainExtra=std::pow(group,-(.44+.08*(1-get(P,Param::looseness))))*db(presetTrim);
  const double slip=index==0?0:h11(int32_t(sq),index,21,0)*lt.slip;
  s.pendingAt=time+std::max(0.,(s.lagMs+slip)/1000.);
  s.pendingScoop=lt.scoop*.5;s.pendingSettle=lt.settle;
  for(const auto&n:notes)if(n.id==id && n.released){s.pendingStop=s.pendingAt+.05;break;}
 }
 void control()noexcept{
  constexpr int n=128;
  time=double(frame)/sr;
  bool changed=false;
  for(unsigned i=0;i<P.size();i++){const double v=targets[i].load(std::memory_order_relaxed);if(P[i]!=v){P[i]=v;changed=true;}}
  const double trim=presetTrimTarget.load(std::memory_order_relaxed);
  if(trim!=presetTrim){presetTrim=trim;changed=true;}
  if(changed){setTone();const double L=get(P,Param::looseness);for(auto&s:singers)if(s.active&&s.ownerId){
   const auto lt=looseTable(L);const int i=s.index,G=s.group,seedIn=int32_t(seed*131+i*7);
   s.L=clamp(get(P,Param::size)+(i==0?0:h11(seedIn,11,0,0)*1.6*get(P,Param::sizeSpread)),13,20.5);
   s.fLow=92*std::pow(L_REF/s.L,1.6);s.detune=i==0?0:h11(seedIn,12,0,0)*lt.detune;
   s.levelDb=i==0?0:-h01(seedIn,13,0,0)*lt.level;
   s.vowelOff=i==0?0:h11(seedIn,14,0,0)*lt.vowel;
   const double spreadDeg=get(P,Param::spread)*70;
   s.az=clamp(get(P,Param::azimuth)+(G>1?(double(i)/(G-1)-.5)*2*spreadDeg:0)+h11(seedIn,15,0,0)*6*get(P,Param::spread),-180,180);
   s.dist=clamp(get(P,Param::distance)+h01(seedIn,16,0,0)*.12*get(P,Param::spread),0,1);
   s.lagMs=i==0?0:lt.lag*(.35+.65*h01(seedIn,17,0,0));s.carrier=i<3||G<=3;
   s.lod=s.dist>.55&&i>0?6:NRES;
   s.gainExtra=std::pow(G,-(.44+.08*(1-L)))*db(presetTrim);
   s.coupling=lt.coupling;s.looseWander=lt.detune*.3;
  }}
  const double dt=n/sr;
  sjT+=dt;
  if(sjT>.008){sjT=0;sjA=sjB;sjN=hash(int32_t(sjN),5,9,1);
   sjB=(h01(int32_t(sjN),1,0,0)+h01(int32_t(sjN),2,0,0)+h01(int32_t(sjN),3,0,0)+h01(int32_t(sjN),4,0,0)-2)*1.732;}
  sharedJit=lerp(sjA,sjB,sjT/.008);
  activeCount=0;
  for(auto&s:singers){
   if(s.killFade && s.pendingAt==-2){s.gainT=0;s.gainStep=(s.gainT-s.gainCur)/n;continue;}
   if(s.pendingAt>=0 && time>=s.pendingAt){s.pendingAt=-1;s.start(s.pendingLevel,s.pendingScoop,s.pendingSettle);}
   if(s.pendingStop>=0 && time>=s.pendingStop){s.pendingStop=-1;s.stop();}
   if(!s.active)continue;
   ++activeCount;
   s.style=get(P,Param::style);const double st=s.style,att=std::max(st>.85?.004:.012,get(P,Param::attack)/1000.*(1.2-st));
   const double rel=get(P,Param::release)/1000.;
   const double tc=s.pT>s.p?att:rel;
   s.p+=(s.pT-s.p)*(1-std::exp(-dt/tc));
   if(s.p<1e-5&&s.pT==0)s.p=0;
   const double th=st<.33?lerp(.12,.5,st/.33):st<.67?lerp(.5,.08,(st-.33)/.34):lerp(.08,0,(st-.67)/.33);
   const double lead=st<.33?lerp(.25,.9,st/.33):st<.67?lerp(.9,.1,(st-.33)/.34):lerp(.1,0,(st-.67)/.33);
   s.V=smooth(th,th+.22,s.p);s.pLevel=std::pow(s.p,.7);
   if(!s.voicing&&s.V>.002){s.voicing=true;s.ph=0;s.gap=0;s.parity=0;s.closureFirst=true;}
   const double asp=get(P,Param::breath)*.55*(1+.5*s.reg);
   const double pre=lead*s.p*(1-s.V)*.9;
   s.noiseAT=(asp*s.V+pre+get(P,Param::whisper)*s.p*.95)*(gritAfter?.6:1);
   s.breathFloor=.12+.5*get(P,Param::breath);
   s.scoop*=std::exp(-dt/s.scoopTau);
   const double tremAmp=get(P,Param::tremor)*(.55+.45*std::sin(time*.37+s.trem[0]));
   const double trem=tremAmp*(.5*std::sin(TAU*s.tremR[0]*time+s.trem[0])+.3*std::sin(TAU*s.tremR[1]*time+s.trem[1])+.2*std::sin(TAU*s.tremR[2]*time+s.trem[2]));
   s.wanderV+=(gauss(s.rng)*.9-s.wanderV)*(1-std::exp(-dt/.6));
   s.wanderS+=(s.wanderV-s.wanderS)*(1-std::exp(-dt/1.4));
   const double wand=(get(P,Param::wander)+(s.index>0?s.looseWander:0))*s.wanderS*1.6;
   s.vibPh+=TAU*5.4*dt;
   const double vib=get(P,Param::vibrato)*std::sin(s.vibPh)*smooth(.25,.9,s.p);
   const double cents=s.detune+s.scoop+trem+wand+vib;
   const double target=s.baseHz*std::pow(2,cents/1200);
   const double gl=std::max(.002,get(P,Param::glide)/1000.);
   s.fCur+=(target-s.fCur)*(1-std::exp(-dt/gl));
   const double vowel=s.vowelNow=get(P,Param::vowel)+s.vowelOff,mouth=s.mouthNow=get(P,Param::mouth);
   const double minA=grid.lookup(vowel,get(P,Param::pharynx),mouth,get(P,Param::ring),s.Fbuf,s.Abuf);
   const double scale=L_REF/s.L,rd=s.rdNow>0?s.rdNow:lerp(2.3,.62,get(P,Param::pressure));
   for(int k=0;k<s.lod;k++){
    double F=std::min(s.Fbuf[k]*scale,.42*sr);
    const double B=bandwidth(F,k,rd,minA),g=std::tan(PI*F/sr),kk=std::min(1.9,B/F);
    const double a1=1/(1+g*(g+kk)),a2=g*a1,a3=g*a2;
    s.F[k]=F;s.B[k]=B;
    if(!s.coefInit){s.ca1[k]=a1;s.ca2[k]=a2;s.ca3[k]=a3;s.ca[k]=s.Abuf[k];}
    s.ta[k]=s.Abuf[k];s.ta1[k]=a1;s.ta2[k]=a2;s.ta3[k]=a3;
    s.cStep1[k]=(a1-s.ca1[k])/n;s.cStep2[k]=(a2-s.ca2[k])/n;s.cStep3[k]=(a3-s.ca3[k])/n;s.aStep[k]=(s.ta[k]-s.ca[k])/n;
   }
   s.coefInit=true;
   const double fLowest=s.fCur*(get(P,Param::growl)>.1?.5:1)*(1-.5*clamp(get(P,Param::creak),0,1));
   double hpf=.6*fLowest;if(!s.carrier)hpf=std::max(hpf,.9*s.fCur);
   hpf=clamp(hpf*(1+1.2*s.dist),25,900);
   {const double g=std::tan(PI*hpf/sr),k=1.41421356,a1=1/(1+g*(g+k));
    s.hpT1=a1;s.hpT2=g*a1;s.hpT3=g*g*a1;
    if(!s.hpInit){s.hp_1=s.hpT1;s.hp_2=s.hpT2;s.hp_3=s.hpT3;s.hpInit=true;}
    s.hpS1=(s.hpT1-s.hp_1)/n;s.hpS2=(s.hpT2-s.hp_2)/n;s.hpS3=(s.hpT3-s.hp_3)/n;
   }
   const double ffc=clamp(30+.3*s.fCur,30,150),fq=1.6;
   s.flg=std::tan(PI*ffc/sr);s.flk=1/fq;
   s.flNorm=1/std::sqrt((1./3)*PI*(ffc/fq)/sr)*.5;
   s.flDepth=(gritAfter?0:get(P,Param::flutter))*.32*(.75+.5*(1-s.reg));
   s.driveT=get(P,Param::drive);
   if(s.lnF==0 || std::abs(s.fCur/s.lnF-1)>=.02||std::abs(rd-s.lnRd)>=.06||s.lnL!=s.L){
    s.lnF=s.fCur;s.lnRd=rd;s.lnL=s.L;
    const double power=expectedPower(pulses,grid,sr,clamp(s.fCur,30,1500),s.L,rd);
    const double corr=std::pow(10.,-3.6*std::max(0.,1.5-rd)*std::max(0.,std::log2(std::max(1.,s.fCur)/110))/20);
    s.normT=clamp(std::sqrt(lnRef/(power+1e-12))*corr,.08,12);
    if(s.lnF==s.fCur && s.norm==1 && s.cycN==0)s.norm=s.normT;
   }
   s.norm+=(s.normT-s.norm)*(1-std::exp(-dt/.12));
   s.noiseAT*=std::pow(std::max(0.,s.norm),.6*(1-get(P,Param::whisper)));
   s.noiseStep=(s.noiseAT-s.noiseA)/n;
   s.gainT=s.killFade?0:db(s.levelDb)*s.gainExtra*cal.voice/cal.preDrive;
   s.gainStep=(s.gainT-s.gainCur)/n;
   const double d=s.dist,dirG=1/(1+4.5*d*d+1.5*d),azr=s.az*PI/180,lat=std::sin(azr),back=smooth(95,160,std::abs(s.az));
   const double pan=(lat+1)*PI/4;
   s.gLT=std::cos(pan)*dirG*(1-.18*back);s.gRT=std::sin(pan)*dirG*(1-.18*back);
   s.sendT=(.32+.5*d)*(.85+.3*back);
   const double lpf=clamp(17000*std::exp(-1.9*d)*(1-.45*back),1800,18000);
   s.dlpC=1-std::exp(-TAU*lpf/sr);
   s.itdT=std::min(60.,std::abs(lat)*.00062*sr);s.farR=lat<0;
   s.shadowC=1-std::exp(-TAU*clamp(18000-13500*std::abs(lat),2500,18000)/sr);
   if(!s.spaceInit){s.gL=s.gLT;s.gR=s.gRT;s.spaceInit=true;}
   s.gLStep=(s.gLT-s.gL)/n;s.gRStep=(s.gRT-s.gR)/n;s.sendStep=(s.sendT-s.revS)/n;s.itdStep=(s.itdT-s.pdel)/n;
   s.noiseRng=s.rng;
   s.energy=0;
  }
  const double lmcT=1-std::pow(10.,-lmCut/20);lmCStep=(lmcT-lmC)/n;
  // Initial preset configuration is immediate. Later automation ramps over 128
  // samples, avoiding full-scale steps from abrupt master/wet control changes.
  const double targetMaster=db(get(P,Param::level));
  const double targetWet=get(P,Param::wet)*1.4;
  if(frame==0){masterGain=targetMaster;wetGain=targetWet;}
  masterStep=(targetMaster-masterGain)/n;
  wetStep=(targetWet-wetGain)/n;
  gritPre=(2.2+6*(get(P,Param::growl)+get(P,Param::rasp)+get(P,Param::shimmer)/12+
                    get(P,Param::jitter)/3+get(P,Param::creak))/3);
  gritTrim=db(cal.afterTrim)/std::sqrt(gritPre);
  room.control(n);
 }
 void singerSample(Singer&s,double&outL,double&outR,double&send)noexcept{
  // JS Singer.render: one sample at a time, retaining the absolute control tick.
  if(s.closureFirst){s.closureFirst=false;s.closure(sr,sharedJit,gritAfter,P,cal,pulses);s.noiseRng=s.rng;}
  uint32_t&x=s.noiseRng;
  const double w1=xorshift(x)/2147483648.-1,w2=xorshift(x)/2147483648.-1;
  const double fa1=1/(1+s.flg*(s.flg+s.flk)),fa2=s.flg*fa1,fa3=s.flg*fa2;
  const double fv3=w2-s.fl2,fv1=fa1*s.fl1+fa2*fv3,fv2=s.fl2+fa2*s.fl1+fa3*fv3;
  s.fl1=2*fv1-s.fl1;s.fl2=2*fv2-s.fl2;
  const double fm=1+s.flDepth*s.flNorm*fv1*s.flk;
  double source=0,gateFlow=0;
  if(s.voicing){
   if(s.gap>0)--s.gap;
   else{
    s.ph+=s.inc;
    if(s.ph>=1){s.ph-=1;s.closure(sr,sharedJit,gritAfter,P,cal,pulses);if(s.gap>0){s.ph=0;--s.gap;}}
    if(s.voicing&&s.gap==0){
     const int lev=s.lev,S=pulses.sizes[lev],o=pulses.base[lev];
     const double fi=s.ph*S;const int i0=std::clamp(int(fi),0,S-1);const double fr=fi-i0;
     const int oa=o+s.rdA*(S+1)+i0,ob=oa+(S+1);
     const double va=pulses.data[oa]+fr*(pulses.data[oa+1]-pulses.data[oa]);
     const double vb=s.rdA+1<NR?pulses.data[ob]+fr*(pulses.data[ob+1]-pulses.data[ob]):va;
     source=lerp(va,vb,s.rdW);
     gateFlow=pulses.flow[s.tabRd*(FLOW+1)+std::clamp(int(s.ph*FLOW),0,FLOW)];
    }
   }
   s.amp+=(s.ampT-s.amp)*ampSmooth;
   source*=s.amp*fm;
  }
  s.noiseA+=s.noiseStep;
  const double aspC=.974,hp=w1-s.asp1;
  s.asp1=w1*(1-aspC)+s.asp1*aspC;
  const double g=s.voicing?(s.breathFloor+(1-s.breathFloor)*gateFlow):1;
  const double noise=hp*s.noiseA*g*.35+w2*s.raspC*gateFlow*gateFlow*s.amp*.28;
  const double input=source+noise;
  // The ten parallel zero-delay SVFs, with tube-M22 residue amplitudes.
  double filtered=0;
  for(int k=0;k<s.lod;k++){
   s.ca1[k]+=s.cStep1[k];s.ca2[k]+=s.cStep2[k];s.ca3[k]+=s.cStep3[k];s.ca[k]+=s.aStep[k];
   const double v3=input-s.ic2[k],v1=s.ca1[k]*s.ic1[k]+s.ca2[k]*v3,v2=s.ic2[k]+s.ca2[k]*s.ic1[k]+s.ca3[k]*v3;
   s.ic1[k]=2*v1-s.ic1[k]+1e-25;s.ic2[k]=2*v2-s.ic2[k];
   filtered+=s.ca[k]*v2;
  }
  // Ramped pitch-following SVF high-pass.
  s.hp_1+=s.hpS1;s.hp_2+=s.hpS2;s.hp_3+=s.hpS3;
  const double v0=filtered+1e-18,v3=v0-s.hp2,v1=s.hp_1*s.hp1+s.hp_2*v3,v2=s.hp2+s.hp_2*s.hp1+s.hp_3*v3;
  s.hp1=2*v1-s.hp1;s.hp2=2*v2-s.hp2;
  filtered=v0-1.41421356*v1-v2;
  filtered*=cal.preDrive;
  // Antiderivative antialiasing, not a normal tanh waveshaper.
  if(s.driveT>.002||s.driveOn){
   const double pre=1+14*s.driveT*s.driveT,post=1/std::sqrt(pre);
   const double xi=filtered*pre,d=xi-s.xPrev,lx=antiderivative(xi),lp=antiderivative(s.xPrev);
   const double y=std::abs(d)<1e-6?std::tanh(.5*(xi+s.xPrev)):(lx-lp)/d;
   s.xPrev=xi;
   if(!s.driveOn && s.driveFadeLeft==0)s.driveFadeLeft=128;
   const double faded=s.driveFadeLeft?lerp(filtered,y*post,double(128-s.driveFadeLeft)/128):y*post;
   filtered=faded;
   if(s.driveFadeLeft) --s.driveFadeLeft;
   s.driveOn=s.driveT>.002;
  }
  // Gain and stereo distance, angle, ITD and head shadow.
  s.gainCur+=s.gainStep;s.gL+=s.gLStep;s.gR+=s.gRStep;s.revS+=s.sendStep;s.pdel+=s.itdStep;
  const double v=filtered*s.gainCur;
  s.energy+=v*v;
  s.dlp+=(v+1e-18-s.dlp)*s.dlpC;
  const int w=int(s.itdW),mask=127;
  s.itd[w]=float(s.dlp);
  const double rp=w-s.pdel,ri=std::floor(rp),rf=rp-ri;
  const double dv=s.itd[int(ri)&mask]*(1-rf)+s.itd[(int(ri)+1)&mask]*rf;
  s.itdW=(s.itdW+1)&mask;
  s.flp+=(dv-s.flp)*s.shadowC;
  if(s.farR){outL+=s.dlp*s.gL;outR+=s.flp*s.gR;}
  else {outL+=s.flp*s.gL;outR+=s.dlp*s.gR;}
  send+=v*s.revS;
 }
 void sample(float&left,float&right)noexcept{
  double dryL=0,dryR=0,send=0;
  for(auto&s:singers)if(s.active){singerSample(s,dryL,dryR,send);}
  double wetL=0,wetR=0;
  wetGain+=wetStep;
  room.sample(send,wetL,wetR,wetGain);
  double l=dryL+wetL,r=dryR+wetR;
  if(gritAfter){
   l=std::tanh(l*gritPre)*gritTrim;r=std::tanh(r*gritPre)*gritTrim;
  }
  l=highSh[0].tick(lowSh[0].tick(l));r=highSh[1].tick(lowSh[1].tick(r));
  const double m=.5*(l+r),a=scLM.tick(m),b=scPR.tick(m);
  eLM+=(a*a-eLM)*lowMidEnvelopeCoeff;ePR+=(b*b-ePR)*lowMidEnvelopeCoeff;
  lmC+=lmCStep;l-=lmC*lmEq[0].tick(l);r-=lmC*lmEq[1].tick(r);
  const double dl=l-dc[0]+.9995*dc[1];dc[0]=l;dc[1]=dl;
  const double dr=r-dc[2]+.9995*dc[3];dc[2]=r;dc[3]=dr;
  masterGain+=masterStep;l=dl*masterGain;r=dr*masterGain;
  // Bounded monotone minimum-gain queue (2.5ms look-ahead).
  constexpr double ceiling=.891;
  const double need=std::min(1.,ceiling/(std::max(std::abs(l),std::abs(r))+1e-12));
  const int64_t idx=limIdx++;
  while(limQt>limQh && limQv[(limQt-1)&1023]>=need)--limQt;
  limQ[limQt&1023]=idx;limQv[limQt&1023]=need;limQt++;
  while(limQt>limQh && limQ[limQh&1023]<=idx-int64_t(limLook))limQh++;
  const double target=limQv[limQh&1023];
  limG+=(target-limG)*(target<limG?limiterAttackCoeff:limiterReleaseCoeff);
  const auto w=limW,rd=(w-limLook+1024)&1023;
  limBL[w]=l;limBR[w]=r;limW=(w+1)&1023;
  const double ol=clamp(limBL[rd]*limG,-ceiling,ceiling),orr=clamp(limBR[rd]*limG,-ceiling,ceiling);
  left=std::isfinite(ol)?float(ol):0;right=std::isfinite(orr)?float(orr):0;
  peakAccum=std::max(peakAccum,std::max(std::abs(double(left)),std::abs(double(right))));
  rmsAccum+=double(left)*left+double(right)*right;metricFrames++;
  limGR=std::min(limGR,20*std::log10(std::max(1e-8,limG)));
 }
 void finishBlock()noexcept{
  // Finalise RNG and voice lifecycle only after exactly 128 rendered samples.
  for(auto&s:singers)if(s.active){
   s.rng=s.noiseRng;
   s.outLev=std::sqrt(s.energy/128.);
   if(s.pendingAt<0 && !s.voicing&&s.p<1e-4&&s.noiseA<1e-5&&!s.gate){
    if(s.outLev<1e-5)s.silentBlocks++;else s.silentBlocks=0;
    if(s.silentBlocks>6){const int slot=s.slot;s.reset(slot);}
   }else s.silentBlocks=0;
  }
  for(auto&s:singers)if(s.killFade)finishSteal(s);
  // Release empty note records without blocking allocation of new notes.
  for(auto&n:notes)if(n.id){bool found=false;for(const auto&s:singers)if(s.ownerId==n.id){found=true;break;}if(!found)n={};}
  const double dt=128./sr;
  lmRatio=10*std::log10((eLM+1e-12)/(ePR+1e-12));
  const double over=lmRatio-cal.lowMidTarget,cutT=over>0&&eLM>1e-8?std::min(6.,over*.6):0;
  lmCut+=(cutT-lmCut)*(1-std::exp(-dt/.4));
  if(cutT==0&&lmCut<.02)lmCut=0;
  peak=std::max(peak*.9,peakAccum);rms=metricFrames?std::sqrt(rmsAccum/(2*metricFrames)):0;
  peakAccum=rmsAccum=0;metricFrames=0;
  // Noise amplitude targets and sample ramps always finish on this boundary.
  // End-of-control-block snapping keeps successive control ramps drift-free.
  masterGain=db(get(P,Param::level));wetGain=get(P,Param::wet)*1.4;
  for(auto&s:singers)if(s.active){s.noiseA=s.noiseAT;s.gainCur=s.gainT;s.gL=s.gLT;s.gR=s.gRT;s.revS=s.sendT;s.pdel=s.itdT;
   for(int k=0;k<s.lod;k++){s.ca1[k]=s.ta1[k];s.ca2[k]=s.ta2[k];s.ca3[k]=s.ta3[k];s.ca[k]=s.ta[k];}
   s.hp_1=s.hpT1;s.hp_2=s.hpT2;s.hp_3=s.hpT3;
  }
 }
};
Engine::~Engine(){if(p_){p_->~State();if(owned_)platformAlignedFree(p_);}}
size_t requiredMemoryBytes()noexcept{return sizeof(Engine::State);}
size_t requiredMemoryAlignment()noexcept{return alignof(Engine::State);}
bool Engine::prepare(double rate,uint32_t max_block,uint64_t seed,Allocator allocator,void*ctx)noexcept{
 if(!std::isfinite(rate)||rate<44100||rate>96000||max_block==0||max_block>65536)return false;
 if(p_){p_->~State();if(owned_)platformAlignedFree(p_);p_=nullptr;}
 const size_t alignment=std::max<size_t>(alignof(State),32),size=(sizeof(State)+alignment-1)/alignment*alignment;
 void*mem=allocator?allocator(ctx,size,alignment):platformAlignedAlloc(size,alignment);
 if(!mem)return false;
 if(reinterpret_cast<uintptr_t>(mem)%alignment!=0){if(!allocator)platformAlignedFree(mem);return false;}
 owned_=allocator==nullptr;
 p_=new(mem)State{};p_->sr=rate;p_->max_block=max_block;p_->seed=seed;
 for(unsigned i=0;i<kParamDefs.size();i++){p_->P[i]=kParamDefs[i].initial;p_->targets[i].store(p_->P[i],std::memory_order_relaxed);}
 p_->pulses.build(p_->re.data(),p_->im.data(),p_->xr.data(),p_->xi.data());
 p_->grid.build();
 p_->lnRef=expectedPower(p_->pulses,p_->grid,rate,160,L_REF,1.2);
 p_->room.prepare(rate);
 p_->scLM.set(Biquad::BandPass,280,.6,0,rate);p_->scPR.set(Biquad::BandPass,2000,.55,0,rate);
 for(int i=0;i<2;i++)p_->lmEq[i].set(Biquad::BandPass,310,.8,0,rate);
 p_->limLook=uint32_t(std::floor(.0025*rate+.5));
 p_->ampSmooth=1-std::exp(-1/(.0015*rate));
 p_->lowMidEnvelopeCoeff=1-std::exp(-1/(.35*rate));
 p_->limiterReleaseCoeff=1-std::exp(-1/(.08*rate));
 p_->limiterAttackCoeff=1-std::exp(-1/(p_->limLook*.25));
 p_->setTone();p_->reset();
 return true;
}
void Engine::reset()noexcept{if(p_)p_->reset();}
bool Engine::setParam(Param p,double value)noexcept{
 const unsigned i=static_cast<unsigned>(p);
 if(!p_||i>=kParamDefs.size()||!std::isfinite(value))return false;
 const auto&d=kParamDefs[i];p_->targets[i].store(clamp(value,d.minimum,d.maximum),std::memory_order_relaxed);return true;
}
bool Engine::setParam(std::string_view name,double value)noexcept{
 for(unsigned i=0;i<kParamDefs.size();i++){if(name==kParamDefs[i].id)return setParam(static_cast<Param>(i),value);}
 return false;
}
double Engine::getParam(Param p)const noexcept{
 const unsigned i=static_cast<unsigned>(p);return p_ && i<kParamDefs.size()?p_->targets[i].load(std::memory_order_relaxed):0;
}
bool Engine::loadPreset(std::string_view id)noexcept{
 if(!p_)return false;
 for(const auto&preset:kPresets)if(id==preset.id){
  for(unsigned i=0;i<kParamDefs.size();i++)p_->targets[i].store(preset.values[i],std::memory_order_relaxed);
  p_->presetTrimTarget.store(preset.trim,std::memory_order_relaxed);return true;
 }
 return false;
}
bool Engine::noteOn(int64_t id,int midi,double velocity)noexcept{
 if(!p_||id==0||midi<0||midi>127||!std::isfinite(velocity))return false;
 return p_->addNote(id,midi,clamp(velocity,0,1));
}
void Engine::noteOff(int64_t id)noexcept{if(p_)p_->releaseNote(id);}
void Engine::allOff()noexcept{if(p_)for(auto&n:p_->notes)if(n.id)p_->releaseNote(n.id);}
void Engine::process(float*left,float*right,uint32_t frames)noexcept{
 if(!left||!right)return;
 if(!p_){std::fill_n(left,frames,0);std::fill_n(right,frames,0);return;}
 auto&s=*p_;
 for(uint32_t i=0;i<frames;i++){
  if(s.ctlLeft==0){s.control();s.ctlLeft=128;s.limGR=0;}
  s.sample(left[i],right[i]);s.frame++;--s.ctlLeft;
  if(s.ctlLeft==0)s.finishBlock();
 }
}
uint32_t Engine::latencyFrames()const noexcept{return p_?p_->limLook:0;}
double Engine::sampleRate()const noexcept{return p_?p_->sr:0;}
uint64_t Engine::samplePosition()const noexcept{return p_?p_->frame:0;}
Telemetry Engine::telemetry()const noexcept{
 Telemetry t{};if(!p_)return t;
 const auto&s=*p_;
 t.active_throats=s.activeCount;
 for(const auto&n:s.notes)if(n.id&&!n.released)t.active_notes++;
 const Singer*fs=nullptr;
 if(s.focus>=0&&s.focus<kMaxThroats&&s.singers[s.focus].active)fs=&s.singers[s.focus];
 if(!fs)for(const auto&v:s.singers)if(v.active){fs=&v;break;}
 if(fs){t.f0_hz=fs->fCur;t.rd=fs->rdNow;const int N=std::min(uint32_t(64),fs->cycN);
  double jsum=0,ssum=0,tsum=0,asum=0;int cnt=0;
  for(int j=1;j<N;j++){
   const int k0=int((fs->cycN-j)%64)*3,k1=int((fs->cycN-j-1)%64)*3;
   if(fs->cycle[k0+1]<=0||fs->cycle[k1+1]<=0)continue;
   jsum+=std::abs(fs->cycle[k0]-fs->cycle[k1]);tsum+=fs->cycle[k0];
   ssum+=std::abs(fs->cycle[k0+1]-fs->cycle[k1+1]);asum+=fs->cycle[k0+1];cnt++;
  }
  if(cnt&&tsum>0)t.jitter_percent=jsum/tsum*100;
  if(cnt&&asum>0)t.shimmer_percent=ssum/asum*100;
 }
 t.low_mid_ratio_db=s.lmRatio;t.low_mid_cut_db=s.lmCut;t.limiter_reduction_db=s.limGR;t.peak=s.peak;t.rms=s.rms;
 return t;
}
namespace {
void store32(uint8_t*&p,uint32_t v){for(int i=0;i<4;i++)*p++=uint8_t(v>>(i*8));}
uint32_t load32(const uint8_t*&p){uint32_t v=0;for(int i=0;i<4;i++)v|=uint32_t(*p++)<<(i*8);return v;}
void store64(uint8_t*&p,uint64_t v){store32(p,uint32_t(v));store32(p,uint32_t(v>>32));}
uint64_t load64(const uint8_t*&p){const uint64_t lo=load32(p);return lo|(uint64_t(load32(p))<<32);}
}
size_t Engine::saveState(uint8_t*dst,size_t capacity)const noexcept{
 if(!p_||!dst||capacity<stateBytes())return 0;
 uint8_t*p=dst;store32(p,0x47555452u);store32(p,2);store64(p,p_->seed);
 uint64_t trimBits;const double trim=p_->presetTrimTarget.load(std::memory_order_relaxed);std::memcpy(&trimBits,&trim,8);store64(p,trimBits);
 for(unsigned i=0;i<kParamDefs.size();i++){
  const double v=getParam(static_cast<Param>(i));uint64_t bits;std::memcpy(&bits,&v,8);store64(p,bits);
 }
 return size_t(p-dst);
}
bool Engine::loadState(const uint8_t*src,size_t bytes)noexcept{
 if(!p_||!src||bytes!=stateBytes())return false;
 const uint8_t*q=src;if(load32(q)!=0x47555452u||load32(q)!=2)return false;
 const auto seed=load64(q);uint64_t trimBits=load64(q);double trim;std::memcpy(&trim,&trimBits,8);
 if(!std::isfinite(trim)||trim<-24||trim>24)return false;
 Params staged{};
 for(unsigned i=0;i<kParamDefs.size();i++){
  uint64_t bits=load64(q);std::memcpy(&staged[i],&bits,8);const auto&d=kParamDefs[i];
  if(!std::isfinite(staged[i])||staged[i]<d.minimum||staged[i]>d.maximum)return false;
 }
 p_->seed=seed;p_->presetTrimTarget.store(trim,std::memory_order_relaxed);
 for(unsigned i=0;i<kParamDefs.size();i++)p_->targets[i].store(staged[i],std::memory_order_relaxed);
 p_->reset();return true;
}
}
