// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "guttur/parameters.h"
#include <cstddef>
#include <cstdint>
#include <string_view>
namespace guttur {
struct Telemetry {
    uint32_t active_throats=0, active_notes=0;
    double f0_hz=0, rd=0, jitter_percent=0, shimmer_percent=0;
    double low_mid_ratio_db=0, low_mid_cut_db=0, limiter_reduction_db=0, peak=0, rms=0;
};
// Opaque 64-bit IDs are caller-owned. A note-on returns true on acceptance.
class Engine final {
public:
    using Allocator = void*(*)(void* user, size_t bytes, size_t alignment);
    Engine() noexcept = default;
    ~Engine();
    Engine(const Engine&)=delete;
    Engine& operator=(const Engine&)=delete;
    // May allocate and perform heavy table generation. Never call on audio thread.
    bool prepare(double rate, uint32_t max_block, uint64_t seed=17, Allocator alloc=nullptr, void* user=nullptr) noexcept;
    void reset() noexcept; // zeroes notes and buffers; retains parameter targets
    bool setParam(Param, double) noexcept; // atomic target; sampled on 128-frame control boundaries
    bool setParam(std::string_view, double) noexcept;
    double getParam(Param) const noexcept;
    bool loadPreset(std::string_view id) noexcept;
    bool noteOn(int64_t note_id, int midi, double velocity=1) noexcept;
    void noteOff(int64_t note_id) noexcept;
    void allOff() noexcept;
    void process(float* left, float* right, uint32_t frames) noexcept;
    uint32_t latencyFrames() const noexcept;
    double sampleRate() const noexcept;
    uint64_t samplePosition() const noexcept;
    Telemetry telemetry() const noexcept;
    bool ready() const noexcept {return p_!=nullptr;}
    // Control-plane versioned patch state: seed and parameter targets (not delay lines).
    size_t saveState(uint8_t* dst,size_t capacity) const noexcept;
    bool loadState(const uint8_t* src,size_t bytes) noexcept;
    static constexpr size_t stateBytes() noexcept {return 24+8*kParamDefs.size();}
private:
    friend size_t requiredMemoryBytes() noexcept;
    friend size_t requiredMemoryAlignment() noexcept;
    struct State;
    State* p_=nullptr;
    bool owned_=false;
};
// Exact allocation size/alignment of the prepared core, usable by ABI2 memory requirements.
size_t requiredMemoryBytes() noexcept;
size_t requiredMemoryAlignment() noexcept;
}
