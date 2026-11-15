// SPDX-License-Identifier: GPL-3.0-only
#include "internal.h"
#include <algorithm>
namespace guttur::detail {
namespace {
void fft(double*re,double*im,int n,bool inverse) noexcept {
 for(int i=1,j=0;i<n;++i){int bit=n>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j){std::swap(re[i],re[j]);std::swap(im[i],im[j]);}}
 for(int len=2;len<=n;len<<=1){const double a=(inverse?TAU:-TAU)/len,wr=std::cos(a),wi=std::sin(a);
  for(int i=0;i<n;i+=len){double cr=1,ci=0;for(int k=0;k<len/2;k++){
   const int p=i+k,q=p+len/2;const double tr=re[q]*cr-im[q]*ci,ti=re[q]*ci+im[q]*cr;
   re[q]=re[p]-tr;im[q]=im[p]-ti;re[p]+=tr;im[p]+=ti;
   const double nr=cr*wr-ci*wi;ci=cr*wi+ci*wr;cr=nr;
  }}
 }
 if(inverse)for(int i=0;i<n;i++){re[i]/=n;im[i]/=n;}
}
struct LF {double Tp,Te,Ta,eps,shift,Delta,omega,alpha,E0;};
LF lfParams(double Rd)noexcept{
 const double Ra=-.01+.048*Rd,Rk=.224+.118*Rd;
 const double Rg=(Rk/4)*(.5+1.2*Rk)/(.11*Rd-Ra*(.5+1.2*Rk));
 const double Ta=Ra,Tp=1/(2*Rg),Te=Tp+Tp*Rk,eps=1/Ta,shift=std::exp(-eps*(1-Te)),Delta=1-shift;
 double rhs=(1/eps)*(shift-1)+(1-Te)*shift;rhs/=Delta;
 const double lower=-(Te-Tp)/2+rhs, upper=-lower, omega=PI/Tp,si=std::sin(omega*Te);
 const double y=-PI*si*upper/(Tp*2),z=std::log(y),alpha=z/(Tp/2-Te),E0=-1/(si*std::exp(alpha*Te));
 return {Tp,Te,Ta,eps,shift,Delta,omega,alpha,E0};
}
double lfSample(const LF&p,double t) noexcept {
 if(t>p.Te)return (-std::exp(-p.eps*(t-p.Te))+p.shift)/p.Delta;
 return p.E0*std::exp(p.alpha*t)*std::sin(p.omega*t);
}
}
void Pulse::build(double*re,double*im,double*xr,double*xi) noexcept {
 int total=0;
 for(int l=0;l<NLEV;++l){hmax[l]=std::max(2,512>>l);sizes[l]=l==0?16384:std::min(16384,64*hmax[l]);base[l]=total;total+=(sizes[l]+1)*NR;}
 for(int r=0;r<NR;++r){
  const auto p=lfParams(RD_MIN+r*RD_STEP);te[r]=float(p.Te);
  double mean=0;
  for(int i=0;i<M;i++){re[i]=lfSample(p,double(i)/M);im[i]=0;mean+=re[i];}
  mean/=M;
  double acc=0,fmin=std::numeric_limits<double>::infinity(),fmax=1e-9;
  // temporarily re-use the input's imaginary vector as integrated flow
  for(int i=0;i<M;i++){acc+=re[i]-mean;im[i]=acc;fmin=std::min(fmin,acc);}
  for(int i=0;i<M;i++)fmax=std::max(fmax,im[i]-fmin);
  for(int k=0;k<=FLOW;k++){const int idx=std::min(M-1,int(std::floor(double(k)*(M-1)/FLOW+.5)));flow[r*(FLOW+1)+k]=float((im[idx]-fmin)/fmax);}
  std::fill_n(im,M,0.);
  fft(re,im,M,false);
  for(int h=1;h<=NH;h++)harm[r*NH+h-1]=float(std::hypot(re[h],im[h])/M*2);
  for(int l=0;l<NLEV;l++){
   const int S=sizes[l],H=hmax[l];std::fill_n(xr,S,0.);std::fill_n(xi,S,0.);
   for(int h=1;h<=H && h<S/2;h++){
    const double x=double(h)/H,tap=x<.7?1.:.5*(1+std::cos(PI*(x-.7)/.3)),g=tap*S/double(M);
    xr[h]=re[h]*g;xi[h]=im[h]*g;xr[S-h]=re[h]*g;xi[S-h]=-im[h]*g;
   }
   fft(xr,xi,S,true);
   const int o=base[l]+r*(S+1);
   for(int i=0;i<S;i++)data[o+i]=float(xr[i]);
   data[o+S]=float(xr[0]);
  }
 }
}
}
