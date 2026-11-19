// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Causal polyphase windowed-sinc conversion from the pinned 48 kHz Plaits core.
// There are no runtime coefficient calculations or allocations.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace macro_oscillator {
struct RateConverter {
    static constexpr uint32_t kTaps = 96;
    static constexpr uint32_t kPhases = 128;
    static constexpr uint32_t kRing = 128; // power of two, larger than kTaps
    static constexpr uint32_t kCenter = (kTaps - 1) / 2;
    static constexpr size_t kTableBytes = size_t(kPhases + 1) * kTaps * sizeof(float);
    struct Frame { float main = 0.f, aux = 0.f; };
    struct State {
        Frame *history = nullptr; // host-owned WS2_LARGE, allocated in prepare
        uint64_t produced = 0;
        double source_time = 0;
    };
    float *table = nullptr; // host-owned WS2_LARGE, allocated in prepare
    double increment = 1.;
    uint32_t latency = 12;
    bool enabled() const { return table != nullptr; }
    void prepare(float *coefficients, double output_rate) {
        table = coefficients;
        increment = 48000. / output_rate;
        latency = static_cast<uint32_t>(std::ceil((12. + (kTaps - 1) * .5) * output_rate / 48000.));
        // The 44.1-kHz Nyquist edge must be suppressed, and the 96-kHz
        // interpolation images begin at 24 kHz. 16 kHz stays in the passband.
        const double cutoff = std::max(1000., std::min(20000., output_rate * .5 - 3500.)) / 48000.;
        constexpr double pi = 3.1415926535897932384626433832795;
        for (uint32_t phase = 0; phase <= kPhases; ++phase) {
            const double fraction = double(phase) / kPhases;
            double sum = 0.;
            for (uint32_t tap = 0; tap < kTaps; ++tap) {
                const double position = double(tap) + fraction - (kTaps - 1) * .5;
                const double angle = pi * position;
                const double sinc = std::abs(position) < 1e-12
                    ? 2. * cutoff : std::sin(2. * cutoff * angle) / angle;
                const double window_phase = 2. * pi * tap / (kTaps - 1);
                const double window = .35875 - .48829 * std::cos(window_phase)
                    + .14128 * std::cos(2. * window_phase)
                    - .01168 * std::cos(3. * window_phase);
                const double coefficient = sinc * window;
                table[size_t(phase) * kTaps + tap] = static_cast<float>(coefficient);
                sum += coefficient;
            }
            for (uint32_t tap = 0; tap < kTaps; ++tap)
                table[size_t(phase) * kTaps + tap] =
                    static_cast<float>(table[size_t(phase) * kTaps + tap] / sum);
        }
    }
    static void reset(State &state) {
        state.produced = 0;
        state.source_time = 0.;
        if (state.history) std::fill_n(state.history, kRing, Frame{});
    }
    // next() is the existing 12-frame Plaits FIFO, running at 48 kHz.
    // A call consumes at most ceil(48000/host_rate) core frames; the FIR
    // sees past samples only. The fixed group delay is reported above.
    template <typename Next>
    Frame output(State &state, Next &&next) const {
        const double source_time = state.source_time + 1e-9;
        const uint64_t latest = static_cast<uint64_t>(source_time);
        while (state.produced <= latest) {
            state.history[state.produced & (kRing - 1)] = next();
            ++state.produced;
        }
        const double phase = std::min(double(kPhases), (source_time - double(latest)) * kPhases);
        const uint32_t row = std::min(uint32_t(phase), kPhases - 1);
        const float blend = static_cast<float>(phase - row);
        const float *first = table + size_t(row) * kTaps;
        const float *second = first + kTaps;
        Frame result{};
        for (uint32_t tap = 0; tap < kTaps && uint64_t(tap) <= latest; ++tap) {
            const auto &sample = state.history[(latest - tap) & (kRing - 1)];
            const float weight = first[tap] + blend * (second[tap] - first[tap]);
            result.main += sample.main * weight;
            result.aux += sample.aux * weight;
        }
        state.source_time += increment;
        return result;
    }
};
} // namespace macro_oscillator
