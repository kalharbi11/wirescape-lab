// SPDX-License-Identifier: GPL-3.0-only
#include "dsp_fixture.h"
#include <memory>
#include <cstring>
#include <limits>
#include <cmath>
#ifndef WS2_PORTABLE_TEST
#include "allocation_watch.h"
#include "frozen_reference.h"
#endif
static const ws2_descriptor*descriptors[]={ws::Module<ws2ports::Vco>::descriptor(),ws::Module<ws2ports::Lfo>::descriptor(),ws::Module<ws2ports::Vcf>::descriptor(),ws::Module<ws2ports::Adsr>::descriptor(),ws::Module<ws2ports::Vca>::descriptor(),ws::Module<ws2ports::Clock>::descriptor(),ws::Module<ws2ports::FunctionEnvelope>::descriptor(),ws::Module<ws2ports::Ladder>::descriptor(),ws::Module<ws2ports::Mixer>::descriptor(),ws::Module<ws2ports::Noise>::descriptor(),ws::Module<ws2ports::Output>::descriptor(),ws::Module<ws2ports::ScaleOffset>::descriptor(),ws::Module<ws2ports::Slew>::descriptor()};
static const char*names[]={"vco","lfo","vcf","adsr","vca","clock","function_envelope","ladder","mixer","noise","output","scale_offset","slew"};
static void matrix(){
 for(auto*d:descriptors)for(double rate:{44100.,48000.,96000.})for(uint32_t count:{1u,4u,16u})for(uint32_t block:{1u,17u,256u}){
  auto a=std::make_unique<DspFixture>(d,rate,count),b=std::make_unique<DspFixture>(d,rate,count);
  uint64_t reference=0;for(int pass=0;pass<2;++pass){uint64_t hash=UINT64_C(14695981039346656037);
   for(int n=0;n<3;++n){a->run(block);b->run(block);for(uint32_t p=0;p<d->output_count;++p)for(uint32_t c=0;c<count;++c)for(uint32_t i=0;i<block;++i){VERIFY(std::isfinite(a->output[p][c][i]));VERIFY(a->output[p][c][i]==b->output[p][c][i]);uint32_t bits;std::memcpy(&bits,&a->output[p][c][i],4);hash=(hash^bits)*UINT64_C(1099511628211);}}
   if(pass==0)reference=hash;else VERIFY(reference==hash);
   a->reset();b->reset();
  }
 }
 // Scalar reference is the same multiply order as f4, including tail lanes.
 auto a=std::make_unique<DspFixture>(descriptors[4],48000,16);a->run();
 for(uint32_t c=0;c<16;++c)for(uint32_t i=0;i<256;++i)VERIFY(std::abs(a->output[0][c][i]-a->input[0][c][i]*a->input[1][c][i])<=1e-6f);
 // Direct DSP counter proves constant-cutoff caching, independent of the wrapper.
 ws2ports::Vcf v;v.reset();auto f=std::make_unique<DspFixture>(descriptors[2],48000,4);ws::Block block(f->process);v.process(block);VERIFY(v.coefficient_recomputes==4);v.process(block);VERIFY(v.coefficient_recomputes==4);
 f->parameter[0][0][0]=2000;v.process(block);VERIFY(v.coefficient_recomputes==8);
 // Nullable transport, play/stop and locate behavior for synced LFO.
 auto l=std::make_unique<DspFixture>(descriptors[1]);l->parameter[3][0][0]=1;l->run(17);VERIFY(l->output[0][0][1]!=0);
 ws2_transport t{sizeof(t),0,120,.25,0,4,4,0,0};l->process.transport=&t;l->run(17);for(int i=0;i<17;++i)VERIFY(std::abs(l->output[0][0][i]-1)<1e-6);
 t.beat=.5;l->run(17);VERIFY(std::abs(l->output[0][0][0])<1e-6);t.flags=WS2_PLAYING;l->run(17);VERIFY(l->output[0][0][1]<0);
 auto guard=std::make_unique<DspFixture>(descriptors[4]);guard->process.output_count=0;VERIFY(guard->d->process(guard->state,&guard->process)==WS2_INVALID);guard->process.output_count=1;
 guard->input[0][0][0]=std::numeric_limits<float>::quiet_NaN();VERIFY(guard->d->process(guard->state,&guard->process)==WS2_INVALID);VERIFY(guard->outs[0].flags&WS2_CONSTANT);VERIFY(guard->output[0][0][0]==0);
 std::printf("PASS %zu DSP matrix cases, reset/determinism, scalar VCA, VCF counter, nullable/stop/locate transport\n",std::size(descriptors)*27);
}

static void lfo_phase() {
    const auto *d = descriptors[1];
    VERIFY(d->output_count == 2);
    VERIFY(!std::strcmp(d->outputs[0].id, "control") && !std::strcmp(d->outputs[1].id, "phase"));
    VERIFY(d->outputs[1].kind == WS2_SIGNAL && d->outputs[1].hint == WS2_CV_UNI);
    VERIFY(d->param_count == 5);
    const char *ids[] = {"rate", "depth", "offset", "sync", "beats"};
    for (uint32_t i = 0; i < 5; ++i) {
        VERIFY(!std::strcmp(d->params[i].id, ids[i]));
        VERIFY(d->params[i].legacy_index == i);
    }

    auto f = std::make_unique<DspFixture>(d, 48000, 4);
    f->pars[0].channels = 4;
    constexpr double tau = 6.283185307179586476925286766559;
    const float rates[4] = {5.f, 10.f, 15.f, 20.f};
    double reference[4]{};
    float previous[4]{};
    uint32_t wraps[4]{};
    for (uint32_t c = 0; c < 4; ++c) f->parameter[0][c][0] = rates[c];

    // Verify every sample against the pre-existing control formula, including its update order.
    for (uint32_t block = 0; block < 21; ++block) {
        f->run(256);
        for (uint32_t c = 0; c < 4; ++c) {
            VERIFY(f->outs[0].channels == 4 && f->outs[1].channels == 4);
            for (uint32_t i = 0; i < 256; ++i) {
                const float actual = f->output[1][c][i];
                VERIFY(actual >= 0.f && actual < 1.f);
                if ((block || i) && actual < previous[c]) ++wraps[c];
                const float control = static_cast<float>(std::sin(reference[c]) * 1.f + 0.f);
                uint32_t expected_bits = 0;
                uint32_t actual_bits = 0;
                std::memcpy(&expected_bits, &control, sizeof(control));
                std::memcpy(&actual_bits, &f->output[0][c][i], sizeof(control));
                VERIFY(expected_bits == actual_bits);
                VERIFY(std::abs(actual - static_cast<float>(reference[c] / tau)) < 1e-6f);
                reference[c] += tau * rates[c] / 48000.;
                if (reference[c] >= tau) reference[c] = std::fmod(reference[c], tau);
                previous[c] = actual;
            }
        }
    }
    VERIFY(wraps[0] == 0 && wraps[1] == 1 && wraps[2] == 1 && wraps[3] == 2);

    // Depth and offset affect only control; phase must continue running.
    f->reset();
    f->parameter[1][0][0] = 0;
    f->parameter[2][0][0] = .25f;
    f->run(256);
    for (uint32_t c = 0; c < 4; ++c) {
        for (uint32_t i = 0; i < 256; ++i) VERIFY(f->output[0][c][i] == .25f);
        VERIFY(f->output[1][c][255] > f->output[1][c][0]);
    }

    // Each voice's beats/cycle parameter controls its transport-synced phase.
    ws2_transport t{sizeof(t), WS2_PLAYING, 120, .25, 0, 4, 4, 0, 0};
    f->process.transport = &t;
    f->parameter[3][0][0] = 1;
    f->pars[4].channels = 4;
    const float beats[4] = {1.f, 2.f, 4.f, 8.f};
    for (uint32_t c = 0; c < 4; ++c) f->parameter[4][c][0] = beats[c];
    f->run(17);
    for (uint32_t c = 0; c < 4; ++c) {
        for (uint32_t i = 0; i < 17; ++i) {
            const double position = .25 + double(i) * 120. / (60. * 48000.);
            const double cycles = position / beats[c];
            VERIFY(std::abs(f->output[1][c][i] - float(cycles - std::floor(cycles))) < 1e-6f);
        }
    }

    // A stopped transport holds the located phase, including negative beat positions.
    t.flags = 0;
    t.beat = -.25;
    f->run(17);
    for (uint32_t c = 0; c < 4; ++c) {
        for (uint32_t i = 0; i < 17; ++i) {
            const double cycles = -.25 / double(beats[c]);
            VERIFY(std::abs(f->output[1][c][i] - float(cycles - std::floor(cycles))) < 1e-6f);
        }
    }
    std::puts("PASS LFO phase: IDs, per-voice ramp/wrap, bit-exact control, depth zero, sync/locate/stop");
}
struct VcoTrackingInput {
    bool cable;
    float pitch;
    int midi = -1;
};
static double measured_vco_hz(VcoTrackingInput input) {
    auto f = std::make_unique<DspFixture>(descriptors[0]);
    f->ins[0].flags = input.cable ? WS2_CONNECTED : 0;
    f->ins[1].flags = 0; // No FM; frequency remains the unchanged 220 Hz default.
    std::fill_n(f->input[0][0], 256, input.pitch);
    ws2_event on{};
    if (input.midi >= 0) {
        on.struct_size = sizeof(on);
        on.type = WS2_NOTE_ON;
        on.key = input.midi;
        on.channel = 0;
        on.value = 1;
        f->process.events = {sizeof(ws2_event_list), 1, &on};
    }
    float previous = 0;
    uint32_t rising = 0;
    for (uint32_t first = 0; first < 48000; first += 256) {
        const uint32_t count = std::min(256u, 48000 - first);
        f->run(count);
        f->process.events.count = 0;
        for (uint32_t i = 0; i < count; ++i) {
            const float sample = f->output[0][0][i];
            if (previous <= 0 && sample > 0) ++rising;
            previous = sample;
        }
    }
    return rising; // Cycles over exactly 1 second, +/- 1 Hz resolution.
}
static void vco_keyboard_tracking() {
    const double c4 = measured_vco_hz({true, 0.f});
    const double a4 = measured_vco_hz({true, .75f});
    const double octave = measured_vco_hz({true, 1.f});
    VERIFY(std::abs(c4 - 261.6255653) < 2);
    VERIFY(std::abs(a4 - 440) < 2);
    VERIFY(std::abs(octave / c4 - 2) < .02);
    VERIFY(std::abs(measured_vco_hz({false, 0.f, 60}) - 261.6255653) < 2);
    VERIFY(std::abs(measured_vco_hz({false, 0.f, 69}) - 440) < 2);
    VERIFY(std::abs(measured_vco_hz({false, 0.f, 127}) - 12543.853951) < 2);
    std::puts("PASS VCO pitch CV (0=C4, 0.75=A4, 1=octave) and MIDI 60/69/127 tracking");
}
static void vca_broadcast(){
 for(uint32_t frames:{1u,4u,17u,256u}){
  auto f=std::make_unique<DspFixture>(descriptors[4],48000,4);
  f->ins[1].flags=WS2_CONNECTED|WS2_CONSTANT;f->pars[0].flags=WS2_CONSTANT;f->pars[0].channels=4;
  for(uint32_t c=0;c<4;++c){
   std::fill_n(f->input[1][c],256,std::numeric_limits<float>::quiet_NaN());
   std::fill_n(f->parameter[0][c],256,std::numeric_limits<float>::quiet_NaN());
   f->input[1][c][0]=-.75f+.1f*c;f->parameter[0][c][0]=.25f+.125f*c;
   for(uint32_t i=0;i<frames;++i)f->input[0][c][i]=(i&1)?-0.f:.125f*(i%5);
  }
  f->run(frames);
  for(uint32_t c=0;c<4;++c)for(uint32_t i=0;i<frames;++i){
   const float expected=(f->input[0][c][i]*f->input[1][c][0])*f->parameter[0][c][0];
   VERIFY(!std::memcmp(&expected,&f->output[0][c][i],sizeof(float)));
  }
 }
 std::puts("PASS VCA constant broadcast ignores undefined tails and preserves signed-zero bits");
}
static void vca_exact(){
 for(double rate:{44100.,48000.,96000.})for(uint32_t channels:{1u,4u,16u})for(uint32_t frames:{1u,17u,256u})for(uint32_t mask=0;mask<8;++mask){
  auto f=std::make_unique<DspFixture>(descriptors[4],rate,channels);f->ins[0].flags=WS2_CONNECTED|((mask&1)?WS2_CONSTANT:0);f->ins[1].flags=WS2_CONNECTED|((mask&2)?WS2_CONSTANT:0);f->pars[0].flags=(mask&4)?WS2_CONSTANT:0;
  for(uint32_t c=0;c<channels;++c)for(uint32_t i=0;i<frames;++i)f->parameter[0][c][i]=.25f+.001f*i;
  f->run(frames);for(uint32_t c=0;c<channels;++c)for(uint32_t i=0;i<((f->outs[0].flags&WS2_CONSTANT)?1:frames);++i){
   float expected=f->input[0][c][(mask&1)?0:i]*f->input[1][c][(mask&2)?0:i]*f->parameter[0][0][(mask&4)?0:i];VERIFY(f->output[0][c][i]==expected);
  }
 }
 std::puts("PASS exact VCA scalar equality across rate/channel/frame/constant matrix");
}

static double vcf_tone_gain(float cutoff,float resonance,double frequency,uint32_t tap) {
 auto f=std::make_unique<DspFixture>(descriptors[2],48000.,1);
 f->parameter[0][0][0]=cutoff;f->parameter[1][0][0]=resonance;
 constexpr double pi=3.14159265358979323846;
 double dry_energy=0,wet_energy=0;
 // More than 0.5 s of warmup and 0.5 s of measurement at 48 kHz.
 for(uint32_t block=0;block<200;++block){
  for(uint32_t i=0;i<256;++i){
   const double t=double(block*256+i)/48000.;
   f->input[0][0][i]=static_cast<float>(std::sin(2*pi*frequency*t));
  }
  f->run(256);
  if(block>=96)for(uint32_t i=0;i<256;++i){
   const double dry=f->input[0][0][i],wet=f->output[tap][0][i];
   dry_energy+=dry*dry;wet_energy+=wet*wet;
  }
 }
 VERIFY(dry_energy>0&&std::isfinite(wet_energy));
 return std::sqrt(wet_energy/dry_energy);
}
static void vcf_passband() {
 for(float cutoff:{100.f,1000.f,5000.f})for(float resonance:{.25f,.5f,.75f,.9f})
  for(uint32_t tap=0;tap<2;++tap){
   double mean_db=0;
   for(uint32_t bin=0;bin<5;++bin){
    const double frequency=20.+(cutoff/4.-20.)*bin/4.;
    const double baseline=vcf_tone_gain(cutoff,0.f,frequency,tap);
    const double measured=vcf_tone_gain(cutoff,resonance,frequency,tap);
    VERIFY(baseline>0&&measured>0);
    mean_db+=20*std::log10(measured/baseline)/5.;
   }
   std::printf("VCF S7.7 passband fc=%g resonance=%g tap=%s mean_relative_db=%.4f\n",
               double(cutoff),double(resonance),tap?"low24":"low12",mean_db);
   VERIFY(std::abs(mean_db)<=1.0);
  }
 std::puts("PASS VCF passband +/-1 dB, 20 Hz through fc/4, both taps");
}
// The M7 VCF change is output-only. Re-run the pre-S7.7 recursion as an
// independent test reference, including a single-sample excitation followed
// by silence at high resonance: no pole, state, or self-oscillation change.
static void vcf_state_and_peak_invariants() {
 constexpr double pi=3.14159265358979323846;
 for(float cutoff:{100.f,1000.f,5000.f})for(float resonance:{.5f,.9f,.95f}){
  auto f=std::make_unique<DspFixture>(descriptors[2],48000.,1);
  f->parameter[0][0][0]=cutoff;f->parameter[1][0][0]=resonance;
  ws2ports::Vcf actual;actual.reset();
  std::array<double,4> old_state{};
  const double g=std::tan(pi*cutoff/48000.),a=g/(1+g);
  const double k=(3.2/.95)*resonance;
  const double makeup=1.+.9*k;
  for(uint32_t n=0;n<400;++n){
   float reference12[256]{},reference24[256]{};
   for(uint32_t i=0;i<256;++i){
    const double x=(n==0&&i==0)?1.:0.;
    f->input[0][0][i]=static_cast<float>(x);
    double zero=0;
    for(auto state:old_state)zero=a*zero+(1-a)*state;
    const double a2=a*a,a4=a2*a2;
    const double feedback=(a4*x+zero)/(1+k*a4);
    double stage=x-k*feedback;
    for(int j=0;j<4;++j){
     const double v=(stage-old_state[j])*a;
     stage=old_state[j]+v;
     old_state[j]=stage+v;
     if(std::abs(old_state[j])<1.e-20)old_state[j]=0;
     if(j==1)reference12[i]=static_cast<float>(stage*makeup);
    }
    reference24[i]=static_cast<float>(stage*makeup);
   }
   ws::Block block(f->process);actual.process(block);
   for(uint32_t i=0;i<256;++i){
    VERIFY(std::abs(f->output[0][0][i]-reference12[i])<1.e-6f);
    VERIFY(std::abs(f->output[1][0][i]-reference24[i])<1.e-6f);
   }
   for(uint32_t j=0;j<4;++j)VERIFY(actual.z[0][j]==old_state[j]);
  }
  // Constant positive makeup preserves the frequency of every spectral peak;
  // at resonance 0.9 it can only raise (never lower) the peak height.
  if(resonance==.9f)VERIFY(makeup>=1.);
 }
 std::puts("PASS VCF pre-S7.7 state and single-impulse tail exactly unchanged; fixed-gain peak invariant");
}

#ifndef WS2_PORTABLE_TEST
static void equivalence(const char*report){
 FILE*file=std::fopen(report,"w");VERIFY(file);std::fprintf(file,"{\"modules\":[");
 for(uint32_t m=0;m<std::size(descriptors);++m){double worst=0;
  // Only VCF's nine ABI1 PCM cases are retired for the intended M7 sound change.
  // The source-verified frozen data remain intact and every other module stays strict.
  if(m==2){std::puts("retired: intended sound change S7.7 — VCF nine frozen ABI1 cases");continue;}
  for(double rate:{44100.,48000.,96000.})for(uint32_t block:{1u,17u,256u}){
   auto f=std::make_unique<DspFixture>(descriptors[m],rate,1);
   char reference_name[128];
   std::snprintf(reference_name,sizeof(reference_name),"module_%s_%u_%u",
                 names[m],static_cast<unsigned>(rate),block);
   const auto frozen=abi1_frozen_samples(reference_name);
   // The legacy capture emitted exactly 2048 samples per ABI1 output port.
   // ABI2 may expose additional ports (e.g. LFO phase); never invent ABI1 data.
   const size_t frozen_output_count=frozen.size()/2048;
   VERIFY(frozen.size()%2048==0 && frozen_output_count>0 &&
          frozen_output_count<=descriptors[m]->output_count);
   size_t reference_pos=0;
   // ABI1 VCO had no pitch/FM inputs: preserve the original input conditions.
   if(m==0){f->ins[0].flags=WS2_CONSTANT;f->ins[1].flags=WS2_CONSTANT;f->input[0][0][0]=f->input[1][0][0]=0;}
   ws2_event on{};on.struct_size=sizeof(on);on.type=WS2_NOTE_ON;on.key=60;on.note_id=1;on.source_id=1;on.channel=0;on.value=1;
   if(m==3){f->ins[0].flags=WS2_CONSTANT;f->input[0][0][0]=0;f->process.events={sizeof(ws2_event_list),1,&on};}
   for(uint32_t pos=0;pos<2048;){
    uint32_t n=std::min(block,2048-pos);
    f->run(n);
    for(uint32_t p=0;p<frozen_output_count;++p)
     for(uint32_t i=0;i<n;++i){
      VERIFY(reference_pos<frozen.size());
      worst=std::max(worst,double(std::abs(frozen[reference_pos++]-f->output[p][0][(f->outs[p].flags&WS2_CONSTANT)?0:i])));
     }
    f->process.events.count=0;pos+=n;
   }
   VERIFY(reference_pos==frozen.size());
  }
  std::printf("equivalence %s max_abs_error %.9g\n",names[m],worst);
  std::fprintf(file,"%s{\"name\":\"%s\",\"max_abs_error\":%.12g,\"passed\":%s}",
               m?",":"",names[m],worst,worst<=1e-6?"true":"false");
  VERIFY(m<5?worst<=1e-6:worst==0);
 }
 std::fputs("]}\n",file);std::fclose(file);
}

static void noalloc(){for(auto*d:descriptors){auto f=std::make_unique<DspFixture>(d,48000,16);allocation_watch::Scope watch;for(int i=0;i<16;++i){f->run(17);f->reset();}VERIFY(watch.allocations()==0);}std::puts("PASS zero new/new[]/aligned-new in static SDK/DSP process/reset");}
#endif
int main(int argc, char **argv) {
#if defined(__cpp_exceptions) || defined(_CPPUNWIND)
    try {
#endif
        matrix();
        vco_keyboard_tracking();
        vca_exact();
        vca_broadcast();
        lfo_phase();
        vcf_passband();
        vcf_state_and_peak_invariants();
#ifndef WS2_PORTABLE_TEST
        noalloc();
        VERIFY(argc==2);
        equivalence(argv[1]);
#else
    (void)argc;
    (void)argv;
#endif
#if defined(__cpp_exceptions) || defined(_CPPUNWIND)
    } catch (...) {
        std::fputs("Unexpected exception in module tests\n", stderr);
        return 1;
    }
#endif
    return 0;
}
