// SPDX-License-Identifier: GPL-3.0-only
#include "internal.h"
namespace guttur::detail {
void Biquad::set(Type type,double f,double q,double gain,double sr)noexcept{
 const double A=std::pow(10.,gain/40),w=TAU*f/sr,cs=std::cos(w),sn=std::sin(w),al=sn/(2*q);
 double bb0=0,bb1=0,bb2=0,aa0=1,aa1=0,aa2=0;
 if(type==LowShelf||type==HighShelf){
  const double s=2*std::sqrt(A)*al,sg=type==LowShelf?1:-1;
  bb0=A*((A+1)-sg*(A-1)*cs+s);bb1=sg*2*A*((A-1)-sg*(A+1)*cs);bb2=A*((A+1)-sg*(A-1)*cs-s);
  aa0=(A+1)+sg*(A-1)*cs+s;aa1=-sg*2*((A-1)+sg*(A+1)*cs);aa2=(A+1)+sg*(A-1)*cs-s;
 }else if(type==Peak){bb0=1+al*A;bb1=-2*cs;bb2=1-al*A;aa0=1+al/A;aa1=-2*cs;aa2=1-al/A;}
 else if(type==BandPass){bb0=al;bb1=0;bb2=-al;aa0=1+al;aa1=-2*cs;aa2=1-al;}
 else if(type==HighPass){bb0=(1+cs)/2;bb1=-(1+cs);bb2=(1+cs)/2;aa0=1+al;aa1=-2*cs;aa2=1-al;}
 else {bb0=(1-cs)/2;bb1=1-cs;bb2=(1-cs)/2;aa0=1+al;aa1=-2*cs;aa2=1-al;}
 b0=bb0/aa0;b1=bb1/aa0;b2=bb2/aa0;a1=aa1/aa0;a2=aa2/aa0;
}
void Room::prepare(double rate)noexcept{
 sr=rate;constexpr double bases[8]={1153,1327,1559,1801,2063,2297,2539,2861};
 for(int i=0;i<8;i++){base[i]=bases[i]*rate/48000.;mph[i]=i*.77;}
 set(.5,1.8);reset();
}
void Room::set(double room,double decay)noexcept{
 size=.55+1.05*room;rt=decay;
 for(int i=0;i<8;i++){
  const double D=d[i]=std::min(8000.,base[i]*size);
  gL[i]=std::pow(10.,-3*D/(sr*rt*.45));gM[i]=std::pow(10.,-3*D/(sr*rt));gH[i]=std::pow(10.,-3*D/(sr*rt*.32));
 }
 cLo=1-std::exp(-TAU*320/sr);cHi=1-std::exp(-TAU*3800/sr);
 hpIn.set(Biquad::HighPass,240,.7,0,sr);hpIn2.set(Biquad::HighPass,240,.7,0,sr);
 constexpr double ts[6][3]={{.011,.5,-.2},{.019,-.25,.45},{.027,.32,.22},{.034,-.18,-.3},{.043,.2,-.16},{.052,-.14,.18}};
 for(int i=0;i<6;i++){tapsD[i]=int(std::floor(ts[i][0]*sr*size+.5));tapsL[i]=ts[i][1];tapsR[i]=ts[i][2];}
 preD=int(std::floor(.012*sr+.5));
}
void Room::reset()noexcept{
 for(auto&l:lines)l.fill(0);
 pre.fill(0);lo.fill(0);hi.fill(0);
 for(int i=0;i<8;i++)mph[i]=i*.77;
 w=pw=0;idle=0;control_rem=0;hpIn.reset();hpIn2.reset();
}
void Room::control(uint32_t n)noexcept{
 for(int k=0;k<8;k++){
  const double a=d[k]+5*std::sin(mph[k]);mph[k]+=(.11+.05*k)*TAU*n/sr;
  const double b=d[k]+5*std::sin(mph[k]);dStart[k]=a;dInc[k]=(b-a)/n;
 }
 control_rem=0;
}
void Room::sample(double input,double&outL,double&outR,double wet)noexcept{
 const double x=hpIn2.tick(hpIn.tick(input));pre[pw]=float(x);
 double eL=0,eR=0;
 for(int j=0;j<6;j++){const float tap=pre[(pw-tapsD[j])&8191];eL+=tap*tapsL[j];eR+=tap*tapsR[j];}
 const double xin=pre[(pw-preD)&8191];pw=(pw+1)&8191;
 for(int k=0;k<8;k++){
  const double rp=w-(dStart[k]+dInc[k]*control_rem),ri=std::floor(rp),fr=rp-ri;
  const int index=int(ri)&8191;
  const double a=lines[k][index],y=a+(lines[k][(index+1)&8191]-a)*fr;
  const double l=lo[k]+(y-lo[k])*cLo;lo[k]=l;
  const double rest=y-l,h=hi[k]+(rest-hi[k])*cHi;hi[k]=h;
  v[k]=l*gL[k]+h*gM[k]+(rest-h)*gH[k];
 }
 const double a0=v[0]+v[1],a1=v[0]-v[1],a2=v[2]+v[3],a3=v[2]-v[3],a4=v[4]+v[5],a5=v[4]-v[5],a6=v[6]+v[7],a7=v[6]-v[7];
 const double b0=a0+a2,b2=a0-a2,b1=a1+a3,b3=a1-a3,b4=a4+a6,b6=a4-a6,b5=a5+a7,b7=a5-a7;
 constexpr double c=.35355339059327373;
 const double y0=(b0+b4)*c,y4=(b0-b4)*c,y1=(b1+b5)*c,y5=(b1-b5)*c,y2=(b2+b6)*c,y6=(b2-b6)*c,y3=(b3+b7)*c,y7=(b3-b7)*c;
 const float xi=float(xin*.35);
 lines[0][w]=float(y0+xi);lines[1][w]=float(y1+xi);lines[2][w]=float(y2+xi);lines[3][w]=float(y3+xi);
 lines[4][w]=float(y4+xi);lines[5][w]=float(y5+xi);lines[6][w]=float(y6+xi);lines[7][w]=float(y7+xi);
 w=(w+1)&8191;control_rem++;
 outL+=((y0+y2+y4+y6)*.5+eL*.6)*wet;
 outR+=((y1+y3+y5+y7)*.5+eR*.6)*wet;
}
}
