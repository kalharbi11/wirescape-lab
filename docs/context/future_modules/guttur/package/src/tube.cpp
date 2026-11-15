// SPDX-License-Identifier: GPL-3.0-only
#include "internal.h"
#include "reference_constants.h"
namespace guttur::detail {
namespace {
double profileAt(int v,double x)noexcept{
 const auto&cp=kAnchors[v];
 for(int i=1;i<kAnchorsCount[v];i++)if(x<=cp[i].x){const double t=(x-cp[i-1].x)/(cp[i].x-cp[i-1].x);const double d=(1-t)*std::sqrt(cp[i-1].area)+t*std::sqrt(cp[i].area);return d*d;}
 return cp[kAnchorsCount[v]-1].area;
}
void areaFunction(double vowel,double pharynx,double mouth,double ring,double*out)noexcept{
 const double pos=clamp(vowel,0,1)*4;const int i0=std::min(3,int(std::floor(pos)));const double t=pos-i0;
 const double mk=std::pow(2,(clamp(mouth,0,1)-.5)*4.4);
 for(int i=0;i<NS;i++){
  const double x=(i+.5)/NS,d=(1-t)*std::sqrt(profileAt(i0,x))+t*std::sqrt(profileAt(i0+1,x));
  double A=d*d;
  const double wp=std::exp(-std::pow((x-.27)/.09,2))*clamp(pharynx,0,1);
  A=std::pow(A,1-wp)*std::pow(.3,wp);
  const double wr=(1-smooth(.08,.16,x))*clamp(ring,0,1)*.85;
  A=std::pow(A,1-wr)*std::pow(.22,wr);
  A*=std::pow(mk,smooth(.76,.92,x));
  out[i]=std::max(.05,A);
 }
}
double tubeM22(const double*A,double L,double f) noexcept {
 const double l=L/NS,k=TAU*f*l/SOUND,cs=std::cos(k),sn=std::sin(k);
 double a=1,b=0,c=0,d=1;
 for(int i=0;i<NS;i++){
  const double Z=1/A[i],b2=Z*sn,c2=sn/Z;
  const double na=a*cs-b*c2,nb=a*b2+b*cs,nc=c*cs+d*c2,nd=-c*b2+d*cs;
  a=na;b=nb;c=nc;d=nd;
 }
 const double r=std::sqrt(A[NS-1]/PI),ke=TAU*f*.8*r/SOUND,ce=std::cos(ke),se=std::sin(ke);
 const double Z=1/A[NS-1];
 return -c*Z*se+d*ce;
}
void tubeResonances(const double*A,double L,double*out,double*amp)noexcept{
 int found=0;const double df=25,f0=40;double v0=tubeM22(A,L,f0);
 for(double f=f0+df;f<16000 && found<NRES;f+=df){
  const double v=tubeM22(A,L,f);
  if(v0*v<0){double lo=f-df,hi=f,vl=v0;
   for(int it=0;it<22;it++){const double m=.5*(lo+hi),vm=tubeM22(A,L,m);if(vl*vm<=0)hi=m;else{lo=m;vl=vm;}}
   const double fk=.5*(lo+hi),dl=.25,dd=(tubeM22(A,L,fk+dl)-tubeM22(A,L,fk-dl))/(2*dl);
   amp[found]=-2/(fk*dd);out[found++]=fk;
  }
  v0=v;
 }
 for(;found<NRES;found++){out[found]=found?out[found-1]*1.15:500;amp[found]=0;}
}
}
void Tube::build()noexcept{
 double A[NS]{},R[NRES]{},RA[NRES]{};int idx=0;
 for(int iv=0;iv<9;iv++)for(int ip=0;ip<5;ip++)for(int im=0;im<5;im++)for(int ir=0;ir<4;ir++){
  areaFunction(double(iv)/8,double(ip)/4,double(im)/4,double(ir)/3,A);
  tubeResonances(A,L_REF,R,RA);
  double mn=99;for(double a:A)mn=std::min(mn,a);
  for(int k=0;k<NRES;k++){F[idx*NRES+k]=float(R[k]);Am[idx*NRES+k]=float(RA[k]);}
  minA[idx++]=float(mn);
 }
}
double Tube::lookup(double vowel,double pharynx,double mouth,double ring,double*outF,double*outA)const noexcept{
 const double fv=clamp(vowel,0,1)*8,fp=clamp(pharynx,0,1)*4,fm=clamp(mouth,0,1)*4,fr=clamp(ring,0,1)*3;
 const int iv=std::min(7,int(fv)),ip=std::min(3,int(fp)),im=std::min(3,int(fm)),ir=std::min(2,int(fr));
 const double tv=fv-iv,tp=fp-ip,tm=fm-im,tr=fr-ir;
 std::fill_n(outF,NRES,0.);if(outA)std::fill_n(outA,NRES,0.);
 double mA=0;
 for(int c=0;c<16;c++){
  const int dv=c&1,dp=(c>>1)&1,dm=(c>>2)&1,dr=(c>>3)&1;
  const double w=(dv?tv:1-tv)*(dp?tp:1-tp)*(dm?tm:1-tm)*(dr?tr:1-tr);
  if(w==0)continue;
  const int idx=(((iv+dv)*5+(ip+dp))*5+(im+dm))*4+(ir+dr),o=idx*NRES;
  for(int k=0;k<NRES;k++){outF[k]+=w*F[o+k];if(outA)outA[k]+=w*Am[o+k];}
  mA+=w*minA[idx];
 }
 return mA;
}
double bandwidth(double F,int n,double rd,double minA)noexcept{
 double B;
 if(F<500)B=165.327516+F*(-.673636734+F*(1.80874446e-3+F*(-4.52201682e-6+F*(7.495140e-9-F*4.70219241e-12))));
 else if(F<5000)B=15.8146139+F*(8.10159009e-2+F*(-9.79728215e-5+F*(5.28725064e-8+F*(-1.07099364e-11+F*7.91528509e-16))));
 else B=360*std::pow(F/5000,1.6);
 B=std::max(B,40.);
 if(n==0)B+=28*rd;else if(n==1)B+=14*rd;else if(n==2)B+=6*rd;
 const double narrow=clamp((.9-minA)/.75,0,1);
 if(n<3)B*=1+narrow*(n==0?.9:n==1?.6:.3);
 if(F>3000)B=std::max(B,.075*F);
 return B;
}
}
