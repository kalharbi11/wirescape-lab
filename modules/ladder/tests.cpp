// SPDX-License-Identifier: GPL-3.0-only
#include "dsp.h"
#include "../../tests/native/abi2/utility_port_tests.h"
#include <complex>

namespace {
constexpr double pi = 3.14159265358979323846;
void run_checked(DspFixture& f) {
    allocation_watch::Scope watch;
    f.run(256);
    VERIFY(watch.allocations() == 0);
}

// Measure actual descriptor output, with parameters settled before a true
// single-sample impulse. Drive zero is the linear resonance criterion.
std::vector<float> impulse(const ws2_descriptor* d, double rate, float fc, float r) {
    auto f = std::make_unique<DspFixture>(d, rate, 1);
    f->parameter[0][0][0] = fc;
    f->parameter[1][0][0] = r;
    f->parameter[2][0][0] = 0;
    std::fill_n(f->input[0][0], 256, 0.f);
    for (int b = 0; b < 128; ++b) run_checked(*f);
    std::vector<float> samples;
    samples.reserve(8192);
    for (int b = 0; b < 32; ++b) {
        f->input[0][0][0] = b == 0 ? 1.f : 0.f;
        run_checked(*f);
        for (float x : f->output[0][0]) {
            VERIFY(std::isfinite(x));
            samples.push_back(x);
        }
    }
    return samples;
}

double magnitude(const std::vector<float>& samples, double rate, double hz) {
    const double angle = -2*pi*hz/rate;
    const std::complex<double> rotation(std::cos(angle), std::sin(angle));
    std::complex<double> phase(1, 0), sum(0, 0);
    for (float x : samples) {
        sum += double(x)*phase;
        phase *= rotation;
    }
    return std::abs(sum);
}

// Frozen pre-S7.8 linear transfer: four bilinear one-poles with a
// one-sample-delayed feedback path, k=.85*r, and DC makeup 1+k.
double legacy_magnitude(double rate, double fc, double r, double hz) {
    const double g = std::tan(pi*fc/rate);
    const double a = g/(1+g), k = .85*r;
    const auto z1 = std::polar(1., -2*pi*hz/rate);
    const auto h = a*(1.+z1)/(1.-(1.-2*a)*z1);
    const auto h4 = h*h*h*h;
    return std::abs((1.+k)*h4/(1.+k*z1*h4));
}

void resonance_matrix(const ws2_descriptor* d) {
    bool pass = true;
    for (double rate : {44100.,48000.,96000.})
        for (float fc : {1000.f,5000.f})
            for (float r : {.5f,.9f}) {
                const auto samples = impulse(d, rate, fc, r);
                double peak = 0, peak_hz = 0;
                auto examine = [&](double hz) {
                    const double m = magnitude(samples, rate, hz);
                    VERIFY(std::isfinite(m));
                    if (m > peak) { peak = m; peak_hz = hz; }
                };
                // Resolve the neighborhood of the target at 0.5% of fc;
                // include DC and the rest of the spectrum to reject a remote peak.
                for (int i = 0; i <= 400; ++i) examine(fc*i/200.);
                for (int i = 1; i <= 100; ++i)
                    examine(2*fc+(rate/2-2*fc)*i/100.);
                double mean_db = 0;
                for (int i = 0; i < 5; ++i) {
                    const double hz = 20+(fc/4.-20)*i/4.;
                    const double before = legacy_magnitude(rate, fc, r, hz);
                    const double after = magnitude(samples, rate, hz);
                    VERIFY(before > 0 && after > 0);
                    mean_db += 20*std::log10(after/before)/5.;
                }
                std::printf("Ladder S7.8 rate=%g fc=%g r=%g peak_hz=%.3f ratio=%.5f peak=%.6f passband_delta_db=%.6f\n",
                            rate, double(fc), double(r), peak_hz, peak_hz/fc, peak, mean_db);
                pass = pass && peak_hz >= .95*fc && peak_hz <= 1.05*fc
                            && std::abs(mean_db) <= 1.;
            }
    std::fflush(stdout);
    VERIFY(pass);
}

void bounded_step(const ws2_descriptor* d) {
    for (double rate : {44100.,48000.,96000.})
        for (float fc : {20.f,1000.f,5000.f,20000.f})
            for (float drive : {0.f,.5f,2.f}) {
                auto f = std::make_unique<DspFixture>(d, rate, 1);
                f->parameter[0][0][0] = fc;
                f->parameter[1][0][0] = 1.f;
                f->parameter[2][0][0] = drive;
                std::fill_n(f->input[0][0], 256, 0.f);
                for (int b = 0; b < 128; ++b) run_checked(*f);
                double peak = 0;
                for (int b = 0; b < 3*int(rate/256+1); ++b) {
                    const int span = int(rate/256+1);
                    std::fill_n(f->input[0][0], 256, b < span ? 1.f : b < 2*span ? -1.f : 0.f);
                    run_checked(*f);
                    for (float x : f->output[0][0]) {
                        VERIFY(std::isfinite(x));
                        peak = std::max(peak, std::abs(double(x)));
                    }
                }
                std::printf("Ladder max-resonance step rate=%g fc=%g drive=%g peak=%.6f\n",
                            rate, double(fc), double(drive), peak);
                // Explicit conservative headroom guard, not a clipping stage.
                VERIFY(peak <= 4.);
            }
}
} // namespace

int main(int argc,char**argv) {
    const int result = utility_port_tests("ladder",argc,argv);
    if (result != 0) return result;
    ModuleLoader loader(argv[1]);
    auto* d = loader.abi2("ladder");
    bounded_step(d);
    resonance_matrix(d);
    return 0;
}
