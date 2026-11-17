// SPDX-License-Identifier: GPL-3.0-only
// MT2 offline matrix: all module interaction goes through the neutral HostModule.
#include "abi_ws2.h"
#include "dispatch.h"
#include <algorithm>
#include <cmath>
#include <cfenv>
#if defined(__SSE__)
#include <xmmintrin.h>
#endif
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <locale>
#include <sstream>
#include <string>
#include <vector>

#if defined(__linux__)
extern "C" {
void* __real_malloc(size_t);
void* __real_calloc(size_t, size_t);
void* __real_realloc(void*, size_t);
void* __real_aligned_alloc(size_t, size_t);
void* __wrap_malloc(size_t n) {
    if (allocation_watch::thread_enabled) ++allocation_watch::thread_count;
    return __real_malloc(n);
}
void* __wrap_calloc(size_t n, size_t m) {
    if (allocation_watch::thread_enabled) ++allocation_watch::thread_count;
    return __real_calloc(n, m);
}
void* __wrap_realloc(void* p, size_t n) {
    if (allocation_watch::thread_enabled) ++allocation_watch::thread_count;
    return __real_realloc(p, n);
}
void* __wrap_aligned_alloc(size_t a, size_t n) {
    if (allocation_watch::thread_enabled) ++allocation_watch::thread_count;
    return __real_aligned_alloc(a, n);
}
}
#endif

namespace {
constexpr double pi = 3.14159265358979323846;
struct GradualUnderflow {
#if defined(__SSE__)
    unsigned previous = _mm_getcsr();
    GradualUnderflow() { _mm_setcsr(previous & ~(1u << 15 | 1u << 6)); }
    ~GradualUnderflow() { _mm_setcsr(previous); }
#elif defined(__aarch64__) && !defined(_WIN32)
    uint64_t previous = 0;
    GradualUnderflow() {
        asm volatile("mrs %0, fpcr" : "=r"(previous));
        const uint64_t gradual = previous & ~(uint64_t(1) << 24 | uint64_t(1) << 19);
        asm volatile("msr fpcr, %0" :: "r"(gradual));
    }
    ~GradualUnderflow() { asm volatile("msr fpcr, %0" :: "r"(previous)); }
#else
    GradualUnderflow() { std::fesetenv(FE_DFL_ENV); }
#endif
};
struct Result {
    std::string test, status = "pass", detail = "completed";
    int rate = 48000, block = 17, voices = 1, frame = 0, channel = 0;
    std::string port = "", param = "";
    double metric = 0;
};
std::string quote(const std::string& s) {
    std::ostringstream o;
    o << '"';
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') o << '\\' << c;
        else if (c == '\n') o << "\\n";
        else if (c == '\r') o << "\\r";
        else if (c == '\t') o << "\\t";
        else if (c < 32) {
            const char* digits = "0123456789abcdef";
            o << "\\u00" << digits[c >> 4] << digits[c & 15];
        } else o << char(c);
    }
    return o.str() + '"';
}
void emit(const Result& r) {
    std::ostringstream o;
    o.imbue(std::locale::classic());
    o << "{\"test\":" << quote(r.test) << ",\"status\":" << quote(r.status)
      << ",\"detail\":" << quote(r.detail) << ",\"where\":{\"rate\":" << r.rate
      << ",\"block\":" << r.block << ",\"voices\":" << r.voices
      << ",\"channel\":" << r.channel << ",\"frame\":" << r.frame
      << ",\"port\":" << quote(r.port) << ",\"param\":" << quote(r.param)
      << "},\"metrics\":{\"value\":" << (std::isfinite(r.metric) ? r.metric : 0) << "}}";
    std::cout << o.str() << '\n';
}
Result row(const std::string& test, int rate, int block, int voices) {
    Result r; r.test = test; r.rate = rate; r.block = block; r.voices = voices; return r;
}
bool equal(float a, float b) { return std::memcmp(&a, &b, sizeof(float)) == 0; }
float stimulus(uint64_t frame, unsigned port, unsigned channel, int rate) {
    // Stateless seed-42 noise, so block segmentation cannot change the input.
    uint32_t x = 42u ^ (uint32_t(frame) * 747796405u) ^ (port * 2891336453u)
                 ^ (channel * 277803737u);
    x ^= x >> 16; x *= 2246822519u; x ^= x >> 13;
    const float noise = float(int(x & 65535u) - 32768) / 32768.f;
    return .12f * float(std::sin(2 * pi * (220 + 37 * port) * double(frame) / rate))
           + .002f * noise;
}
HostBlock make_block(const HostDescription& d, int rate, unsigned frames,
                     unsigned voices, uint64_t offset = 0,
                     int special = 0, int changed_param = -1,
                     float value = 0, bool sweep = false,
                     int nonfinite_input = -1, int nonfinite_param = -1) {
    HostBlock b;
    b.frames = frames; b.channels = voices; b.sample_rate = rate;
    for (unsigned j = 0; j < d.inputs.size(); ++j) {
        HostSignal s; s.channels = voices;
        for (unsigned c = 0; c < voices; ++c) {
            std::vector<float> samples(frames);
            for (unsigned i = 0; i < frames; ++i)
                samples[i] = stimulus(offset + i, j, c, rate);
            if (special && int(j) == nonfinite_input && !samples.empty())
                samples[0] = special == 1 ? std::numeric_limits<float>::quiet_NaN()
                           : special == 2 ? std::numeric_limits<float>::infinity()
                                          : -std::numeric_limits<float>::infinity();
            s.samples.push_back(std::move(samples));
        }
        b.inputs.push_back(std::move(s));
    }
    for (unsigned j = 0; j < d.params.size(); ++j) {
        HostSignal s; s.channels = voices; s.constant = !sweep;
        for (unsigned c = 0; c < voices; ++c) {
            std::vector<float> samples(sweep ? frames : 1, d.params[j].initial);
            if (int(j) == changed_param) {
                for (unsigned i = 0; i < samples.size(); ++i)
                    samples[i] = sweep
                        ? d.params[j].minimum + (d.params[j].maximum - d.params[j].minimum) *
                              float((offset + i) % 64) / 63.f : value;
            }
            if (special && int(j) == nonfinite_param)
                samples[0] = special == 1 ? std::numeric_limits<float>::quiet_NaN()
                           : special == 2 ? std::numeric_limits<float>::infinity()
                                          : -std::numeric_limits<float>::infinity();
            s.samples.push_back(std::move(samples));
        }
        b.params.push_back(std::move(s));
    }
    // Event descriptors are neutral; note-on/off kind integers are part of the
    // existing runner protocol and do not reference or redefine ABI symbols.
    for (unsigned j = 0; j < d.inputs.size(); ++j) if (d.inputs[j].kind == 2u) {
        for (unsigned c = 0; c < voices; ++c) {
            HostEvent e; e.type = (offset / frames) % 2 == 0 ? 1u : 2u;
            e.offset = 0; e.port = j; e.channel = int(c); e.note_id = int(c);
            e.key = 60 + int(c); e.value = 1; b.events.push_back(e);
        }
    }
    return b;
}
struct Observed {
    int code = -1;
    uint64_t allocations = 0;
    bool finite = true, zero_constant = true;
    unsigned out_channels = 0;
    double peak = 0;
    std::vector<float> values;
};
Observed observe(HostModule& module, HostBlock& block, bool measure = false) {
    Observed o;
    o.code = module.process(block, measure ? &o.allocations : nullptr);
    for (const auto& p : block.outputs) {
        o.out_channels = std::max(o.out_channels, p.channels);
        for (unsigned c = 0; c < p.channels && c < p.samples.size(); ++c) {
            const auto& samples = p.samples[c];
            for (unsigned i = 0; i < (p.constant ? 1u : block.frames) && i < samples.size(); ++i) {
                const float v = samples[i];
                o.values.push_back(v);
                if (!std::isfinite(v)) o.finite = false;
                else o.peak = std::max(o.peak, double(std::fabs(v)));
                if (!p.constant || v != 0) o.zero_constant = false;
            }
        }
    }
    return o;
}
bool identical(const Observed& a, const Observed& b, unsigned& first) {
    if (a.code != b.code || a.values.size() != b.values.size()) return false;
    for (unsigned i = 0; i < a.values.size(); ++i)
        if (!equal(a.values[i], b.values[i])) { first = i; return false; }
    return true;
}
bool prepared(HostModule& m, int rate, int frames, int voices, const std::vector<uint8_t>& config) {
    return m.create(rate, frames, voices, config) == 0;
}
std::vector<float> stream(const HostDescription& d, int rate, unsigned chunk,
                          unsigned voices, const std::vector<uint8_t>& config,
                          int seconds = 1, bool decay = false, bool* good = nullptr) {
    HostModule m;
    std::vector<float> flattened;
    bool ok = prepared(m, rate, chunk, voices, config);
    const uint64_t length = uint64_t(rate) * seconds;
    for (uint64_t at = 0; ok && at < length; at += chunk) {
        auto b = make_block(d, rate, unsigned(std::min<uint64_t>(chunk, length - at)), voices, at);
        if (decay && at >= uint64_t(rate)) {
            for (auto& input : b.inputs)
                for (auto& channel : input.samples) std::fill(channel.begin(), channel.end(), 0.f);
        }
        auto o = observe(m, b);
        if (o.code != 0 || !o.finite) { ok = false; break; }
        flattened.insert(flattened.end(), o.values.begin(), o.values.end());
    }
    if (good) *good = ok;
    return flattened;
}
void result_after(bool ok, Result& r, const std::string& failure) {
    if (!ok) { r.status = "fail"; r.detail = failure; }
}
}

int module_matrix_main(int argc, const char* const* argv) {
    bool full = false;
    std::vector<uint8_t> config;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--full") full = true;
        else if (arg == "--config" && i + 1 < argc) {
            std::istringstream bytes(argv[++i]);
            std::string part;
            while (std::getline(bytes, part, ',')) {
                try {
                    const unsigned v = unsigned(std::stoul(part));
                    if (v > 255 || config.size() >= 4096) return 2;
                    config.push_back(uint8_t(v));
                } catch (...) { return 2; }
            }
        } else return 2;
    }
    HostModule meta;
    const auto d = meta.describe();
    Result t1 = row("T1", 48000, 17, 1);
    if (!d.errors.empty()) { t1.status = "fail"; t1.detail = d.errors.front(); }
    else t1.detail = "descriptor valid";
    emit(t1);
    if (!d.errors.empty()) return 0;

    const std::vector<int> rates = full ? std::vector<int>{44100, 48000, 96000}
                                        : std::vector<int>{48000};
    const std::vector<int> blocks = full ? std::vector<int>{1, 17, 64, 256}
                                         : std::vector<int>{17, 256};
    const std::vector<int> voice_counts = full ? std::vector<int>{1, 4, 16}
                                               : std::vector<int>{1, 4};
    for (int rate : rates) {
        HostModule m;
        Result t2 = row("T2", rate, blocks.back(), 1);
        int status = m.create(rate, blocks.back(), 1, config);
        if (status != 0) {
            t2.status = rate == 48000 ? "fail" : "warn";
            t2.detail = "prepare refuses " + std::to_string(rate) + " Hz, code " + std::to_string(status);
        } else t2.detail = "rate supported";
        emit(t2);
        if (status != 0) continue;
        for (int frames : blocks) for (int voices : voice_counts) {
            HostModule unit;
            Result t3 = row("T3", rate, frames, voices);
            if (!prepared(unit, rate, frames, voices, config)) {
                t3.status = "fail"; t3.detail = "prepare failed for block or voices";
            } else {
                auto b = make_block(d, rate, frames, voices);
                const auto result = observe(unit, b);
                if (result.code != 0 || result.out_channels > unsigned(voices)) {
                    t3.status = "fail";
                    t3.detail = "process returned " + std::to_string(result.code) +
                                " for " + std::to_string(frames) + " frames";
                }
            }
            emit(t3);
        }
    }
    const int rate = 48000, frames = 17, voices = full ? 16 : 4;
    {
        Result t4 = row("T4", rate, frames, voices);
        HostModule together;
        if (!prepared(together, rate, frames, voices, config)) {
            t4.status = "skip"; t4.detail = "prepare unavailable";
        } else {
            auto b = make_block(d, rate, frames, voices);
            auto multi = observe(together, b);
            if (multi.code) {
                t4.status = "fail"; t4.detail = "poly processing returned nonzero";
            } else for (unsigned c = 0; c < unsigned(voices) && t4.status == "pass"; ++c) {
                HostModule alone;
                if (!prepared(alone, rate, frames, 1, config)) {
                    t4.status = "fail"; t4.detail = "isolated voice preparation failed"; break;
                }
                auto single = make_block(d, rate, frames, 1);
                for (size_t j = 0; j < single.inputs.size(); ++j)
                    single.inputs[j].samples[0] = b.inputs[j].samples[c];
                for (size_t j = 0; j < single.params.size(); ++j)
                    single.params[j].samples[0] = b.params[j].samples[c];
                const auto solo = observe(alone, single);
                if (solo.code) { t4.status = "fail"; t4.detail = "isolated voice processing failed"; break; }
                for (unsigned p = 0; p < d.outputs.size() && t4.status == "pass"; ++p) {
                    if (d.outputs[p].poly != 0 || p >= b.outputs.size() ||
                        p >= single.outputs.size() || c >= b.outputs[p].channels) continue;
                    const auto& a = b.outputs[p].samples[c];
                    const auto& z = single.outputs[p].samples[0];
                    const unsigned limit = unsigned(frames);
                    for (unsigned f = 0; f < limit; ++f) {
                        const float av = a[b.outputs[p].constant ? 0 : f];
                        const float zv = z[single.outputs[p].constant ? 0 : f];
                        if (!equal(av, zv)) {
                            t4.status = "fail"; t4.detail = "voice leaks into isolated voice";
                            t4.channel = c; t4.frame = f; t4.port = d.outputs[p].id; break;
                        }
                    }
                }
            }
        }
        emit(t4);
    }
    {
        Result t5 = row("T5", rate, frames, 1);
        HostModule a, b;
        if (!prepared(a, rate, frames, 1, config) || !prepared(b, rate, frames, 1, config)) {
            t5.status = "skip"; t5.detail = "prepare unavailable";
        } else {
            auto ba = make_block(d, rate, frames, 1), bb = make_block(d, rate, frames, 1);
            unsigned first = 0;
            result_after(identical(observe(a, ba), observe(b, bb), first),
                         t5, "two fresh instances differ");
            t5.frame = int(first);
        }
        emit(t5);
    }
    {
        Result t6 = row("T6", rate, frames, 1);
        HostModule used, fresh;
        if (!prepared(used, rate, frames, 1, config) || !prepared(fresh, rate, frames, 1, config)) {
            t6.status = "skip"; t6.detail = "prepare unavailable";
        } else {
            for (unsigned i = 0; i < 3; ++i) {
                auto b = make_block(d, rate, frames, 1, i * frames);
                observe(used, b);
            }
            used.reset();
            auto a = make_block(d, rate, frames, 1);
            auto b = make_block(d, rate, frames, 1);
            unsigned first = 0;
            result_after(identical(observe(used, a), observe(fresh, b), first),
                         t6, "after reset output differs");
            t6.frame = int(first);
        }
        emit(t6);
    }
    {
        Result t7 = row("T7", rate, frames, 1);
        HostModule a, b;
        if (!prepared(a, rate, frames, 1, config) || !prepared(b, rate, frames, 1, config)) {
            t7.status = "skip"; t7.detail = "prepare unavailable";
        } else {
            for (unsigned i = 0; i < 3; ++i) {
                auto block = make_block(d, rate, frames, 1, i * frames);
                observe(a, block);
            }
            std::vector<uint8_t> bytes;
            const int saved = a.save(bytes);
            if (saved == 3) { t7.status = "skip"; t7.detail = "state unsupported"; }
            else if (saved != 0) { t7.status = "fail"; t7.detail = "save failed"; }
            else if (b.load(bytes) != 0) { t7.status = "fail"; t7.detail = "load failed"; }
            else {
                auto x = make_block(d, rate, frames, 1, 3 * frames);
                auto y = make_block(d, rate, frames, 1, 3 * frames);
                unsigned first = 0;
                result_after(identical(observe(a, x), observe(b, y), first),
                             t7, "loaded copy diverges");
                t7.frame = int(first);
                if (!bytes.empty()) {
                    bytes.pop_back();
                    HostModule truncated;
                    if (prepared(truncated, rate, frames, 1, config) && truncated.load(bytes) == 0) {
                        t7.status = "fail"; t7.detail = "truncated state accepted";
                    }
                }
            }
        }
        emit(t7);
    }
    {
        Result t8 = row("T8", rate, frames, 1);
        HostModule m;
        if (!prepared(m, rate, frames, 1, config)) {
            t8.status = "skip"; t8.detail = "prepare unavailable";
        } else {
            auto block = make_block(d, rate, frames, 1);
            const auto o = observe(m, block, true);
            uint64_t reset_allocs = 0;
            m.reset(&reset_allocs);
            t8.metric = double(o.allocations + reset_allocs);
            if (o.allocations || reset_allocs) {
                t8.status = "fail";
                t8.detail = std::to_string(o.allocations) + " process / " +
                            std::to_string(reset_allocs) + " reset allocations";
            } else t8.detail = "no measured callback allocation";
        }
        emit(t8);
    }
    {
        Result t9 = row("T9", rate, frames, 1);
        HostModule m;
        if (!prepared(m, rate, frames, 1, config)) {
            t9.status = "skip"; t9.detail = "prepare unavailable";
        } else {
            for (int k = 1; k <= 3 && t9.status == "pass"; ++k) {
                for (size_t j = 0; j < d.inputs.size() + d.params.size(); ++j) {
                    const bool is_input = j < d.inputs.size();
                    auto block = make_block(d, rate, frames, 1, 0, k, -1, 0, false,
                                            is_input ? int(j) : -1,
                                            is_input ? -1 : int(j - d.inputs.size()));
                    const auto o = observe(m, block);
                    if (!((o.code == 1 && o.zero_constant) ||
                          (o.code == 0 && o.finite))) {
                        t9.status = "fail";
                        t9.detail = "nonfinite input not safely handled";
                        if (is_input) t9.port = d.inputs[j].id;
                        else t9.param = d.params[j - d.inputs.size()].id;
                        t9.frame = 0; break;
                    }
                    m.reset();
                }
            }
        }
        emit(t9);
    }
    for (unsigned j = 0; j < d.params.size(); ++j) {
        const auto& param = d.params[j];
        std::vector<float> cases{param.minimum, param.maximum};
        // Full mode also probes every representable step. The neutral HostParam
        // carries step, but not discrete option_count/options (recorded gap).
        bool step_limit = false;
        if (full && std::isfinite(param.step) && param.step > 0 &&
            std::isfinite(param.maximum - param.minimum)) {
            const double steps = std::floor(double(param.maximum - param.minimum) / param.step);
            if (steps > 1024) step_limit = true;
            else for (unsigned k = 1; k < unsigned(steps); ++k)
                cases.push_back(float(double(param.minimum) + k * double(param.step)));
        }
        for (unsigned index = 0; index < cases.size(); ++index) {
            for (int buffer = 0; buffer < (full ? 2 : 1); ++buffer) {
                Result t11 = row("T11", rate, frames, 1);
                t11.param = param.id;
                const float value = cases[index];
                HostModule m;
                if (!prepared(m, rate, frames, 1, config)) {
                    t11.status = "skip"; t11.detail = "prepare unavailable";
                } else {
                    auto b = make_block(d, rate, frames, 1, 0, 0, int(j), value);
                    if (buffer) {
                        b.params[j].constant = false;
                        for (auto& channel : b.params[j].samples)
                            channel.assign(frames, value);
                    }
                    const auto o = observe(m, b);
                    t11.metric = o.peak;
                    t11.detail = (buffer ? "per-sample " : "constant ") +
                                 std::string(index == 0 ? "minimum" :
                                             index == 1 ? "maximum" : "step") +
                                 " value=" + std::to_string(value);
                    if (o.code || !o.finite) {
                        t11.status = "fail";
                        t11.detail += " nonfinite or process error " + std::to_string(o.code);
                    } else if (o.peak > 4.0) {
                        t11.status = "warn";
                        t11.detail += " peak exceeds 4 FS";
                    }
                }
                emit(t11);
            }
        }
        if (step_limit) {
            Result t11 = row("T11", rate, frames, 1);
            t11.param = param.id;
            t11.status = "warn";
            t11.detail = "step grid exceeds 1024 probes; enumeration incomplete";
            emit(t11);
        }
    }
    if (full) {
        Result t10 = row("T10", rate, 256, 1);
        bool ok = false;
        std::vector<float> tail;
        {
            GradualUnderflow gradual; // FTZ/DAZ off for stimulus and decay.
            tail = stream(d, rate, 256, 1, config, 2, true, &ok);
        }
        uint64_t subnormal = 0;
        size_t last_nontrivial = 0, last_nonzero = 0;
        double peak = 0;
        for (size_t i = 0; i < tail.size(); ++i)
            if (i < size_t(rate)) peak = std::max(peak, std::fabs(double(tail[i])));
        const double threshold = peak * .001;
        for (size_t i = size_t(rate); i < tail.size(); ++i) {
            const float value = tail[i];
            if (std::fpclassify(value) == FP_SUBNORMAL) ++subnormal;
            if (std::fabs(double(value)) > threshold) last_nontrivial = i;
            if (value != 0) last_nonzero = i;
        }
        t10.metric = double(subnormal);
        t10.status = "warn"; // report-only, never exit failure
        t10.detail = ok
            ? "subnormal samples " + std::to_string(subnormal) +
              ", -60 dB at " + std::to_string(double(last_nontrivial) / rate) +
              " s, exact silence at " + std::to_string(double(last_nonzero) / rate) + " s"
            : "denormal decay probe unavailable";
        emit(t10);
        for (unsigned j = 0; j < d.params.size(); ++j) {
            Result t12 = row("T12", rate, 64, 1);
            t12.param = d.params[j].id;
            if (!(d.params[j].flags & 1u)) {
                t12.status = "skip"; t12.detail = "parameter not modulatable";
            } else {
                HostModule m;
                if (!prepared(m, rate, 64, 1, config)) {
                    t12.status = "skip"; t12.detail = "prepare unavailable";
                } else {
                    auto b = make_block(d, rate, 64, 1, 0, 0, int(j), 0, true);
                    const auto o = observe(m, b);
                    if (o.code || !o.finite) {
                        t12.status = "fail"; t12.detail = "fast sweep nonfinite or failed";
                    } else {
                        unsigned clicks = 0;
                        for (size_t i = 1; i < o.values.size(); ++i)
                            if (std::fabs(o.values[i] - o.values[i-1]) > .25f) ++clicks;
                        t12.metric = clicks;
                        if (clicks) { t12.status = "warn"; t12.detail = "fast sweep click count"; }
                    }
                }
            }
            emit(t12);
        }
        Result t13 = row("T13", rate, 256, 1);
        bool reference_ok = false;
        const auto reference = stream(d, rate, 256, 1, config, 1, false, &reference_ok);
        double diff = 0;
        bool valid = reference_ok;
        for (unsigned chunk : {1u, 17u, 64u}) {
            bool other_ok = false;
            const auto other = stream(d, rate, chunk, 1, config, 1, false, &other_ok);
            if (!other_ok || other.size() != reference.size()) { valid = false; continue; }
            for (size_t i = 0; i < other.size(); ++i)
                diff = std::max(diff, std::fabs(double(other[i]) - reference[i]));
        }
        t13.metric = diff;
        if (!valid) { t13.status = "warn"; t13.detail = "block independence comparison unavailable"; }
        else if (diff > 1e-5) { t13.status = "warn"; t13.detail = "output depends on block size"; }
        else t13.detail = diff == 0 ? "bitwise equal across blocks" : "difference within tolerance";
        emit(t13);
    }
    return 0;
}
