// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../port_state.h"
namespace ws2ports {
struct Ladder {
 static constexpr ws::Info info{"essentials.ladder","Ladder Filter",2};
 static constexpr std::array inputs{ws::port("audio","Audio",WS2_AUDIO)};static constexpr std::array outputs{ws::port("audio","Audio",WS2_AUDIO)};
 static constexpr std::array params{ws::param("cutoff","Cutoff",20,20000,1000,"Hz",port_flags,WS2_LINEAR,0),ws::param("resonance","Resonance",0,1,0,"",port_flags,WS2_LINEAR,1),ws::param("drive","Drive",0,2,0,"",port_flags,WS2_LINEAR,2)};
 struct Voice{PortRamp cutoff{1000},resonance{0},drive{0};std::array<double,4>z{};double previous=0;};std::array<Voice,16>voices{};double rate=48000;
 void prepare(const ws::Setup&s){rate=s.sample_rate();for(auto&v:voices){v.cutoff.prepare(rate);v.resonance.prepare(rate);v.drive.prepare(rate);}reset();}
 void reset(){for(auto&v:voices){v.z.fill(0);v.previous=0;v.cutoff.reset();v.resonance.reset();v.drive.reset();}}
 void process(ws::Block&b){
  b.out(0).set_channels(b.channels());b.out(0).mark_constant(false);
  for(uint32_t c=0;c<b.channels();++c){
   auto&v=voices[c];
   for(uint32_t i=0;i<b.frames();++i){
    v.cutoff.update(b.param(0).value(c,i));v.resonance.update(b.param(1).value(c,i));v.drive.update(b.param(2).value(c,i));
    float input=b.in(0).value(c,i);
    double x=std::max(-1.e6,std::min(1.e6,std::isfinite(input)?double(input):0.));
    double cutoff=std::min(v.cutoff.next(),.45*rate),g=std::tan(3.14159265358979323846*cutoff/rate);
    const double r=v.resonance.next(),d=v.drive.next();
    if(r!=0.)g*=1.+1.45*r*(1.-r);
    const double a=g/(1.+g);
    double stage;
    if(r==0.){
     // Preserve the original non-resonant operation order, including signed zero.
     const double k=.85*r;
     stage=(1.+k)*x-k*v.previous;
    }else{
     // Four TPT poles have H=(1+j*t)^-1. In the zero-delay loop the
     // squared denominator is |(1+j*t)^4+k|^2; its stationary point
     // satisfies (1+t^2)^3=k*(3-t^2). A quadratic prewarp approximates
     // the inverse peak ratio at the specified resonance settings.
     const double k=3.*r,a2=a*a,a4=a2*a2;
     double zero=0.;
     for(double z:v.z)zero=a*zero+(1.-a)*z;
     // Solve the current-sample linear feedback loop, not the delayed
     // previous output. k<=3 keeps the linear poles below oscillation.
     stage=((1.+k)*x-k*zero)/(1.+k*a4);
    }
    // Apply the existing drive curve to the solved input; for nonzero
    // drive this is a bounded nonlinearity, not an implicit tanh solve.
    const double drive=3.*d;
    if(d!=0.)stage=std::tanh(drive*stage)/drive;
    for(auto&z:v.z){
     double value=(stage-z)*a;double y=z+value;z=y+value;
     if(std::abs(z)<1.e-20)z=0;
     stage=y;
    }
    // Keep the v1 saved-state layout; this field no longer feeds back.
    v.previous=stage;b.out(0).ch(c)[i]=static_cast<float>(stage);
   }
  }
 }
 int save_state(ws::Writer w){if(!w.u32(1))return WS2_CAPACITY;for(auto&v:voices){for(double z:v.z)if(!write_double(w,z))return WS2_CAPACITY;if(!write_double(w,v.previous)||!v.cutoff.write(w)||!v.resonance.write(w)||!v.drive.write(w))return WS2_CAPACITY;}return WS2_OK;}
 int load_state(ws::Reader r){uint32_t version;if(!r.u32(version))return WS2_INVALID;if(version!=1)return WS2_UNSUPPORTED;auto staged=voices;for(auto&v:staged){for(auto&z:v.z)if(!read_double(r,z))return WS2_INVALID;if(!read_double(r,v.previous)||!v.cutoff.read(r,20,20000)||!v.resonance.read(r,0,1)||!v.drive.read(r,0,2))return WS2_INVALID;}voices=staged;return WS2_OK;}
};
}
