// SPDX-License-Identifier: GPL-3.0-only
// Compiled separately per catalogue module; no product modifications.
#include "wirescape_sdk.h"
#ifdef WS_S2_ARM
#undef WS_REGISTER_MODULE
#define WS_REGISTER_MODULE(T) extern "C" { unsigned char ws_s2_dsp_size[sizeof(T)] = {}; }
#else
#include <cstdio>
#include <cstdlib>
#include <vector>

struct Arena {
    std::vector<void*> blocks;
    ~Arena() { for (auto p : blocks) std::free(p); }
    static void* WS2_CALL alloc(void* ctx, size_t bytes, size_t alignment, uint32_t) {
        void* p = nullptr;
        if (posix_memalign(&p, std::max(alignment, sizeof(void*)), bytes)) return nullptr;
        static_cast<Arena*>(ctx)->blocks.push_back(p);
        return p;
    }
};
struct Count {
    uint64_t bytes = 0;
    static int WS2_CALL write(void* ctx, const void*, uint32_t n) {
        auto& c = *static_cast<Count*>(ctx);
        if (c.bytes + n > 1048576u) return WS2_CAPACITY;
        c.bytes += n;
        return WS2_OK;
    }
};
template<class T> int measure() {
    std::printf("DSP %zu\n", sizeof(T));
    for (unsigned rate : {48000u, 96000u}) {
        for (unsigned channels : {1u, 8u}) {
            ws2_config config{};
            config.struct_size = sizeof(config);
            config.sample_rate = rate;
            config.max_block_frames = 256;
            config.max_channels = channels;
            config.seed = 1;
            ws2_memory mem{};
            mem.alignment = 32; // SDK default when no extra memory hook exists.
            if constexpr (ws::HasMemory<T>::value) mem = T::memory_requirements(config);
            int status = WS2_UNSUPPORTED, prepared = WS2_UNSUPPORTED;
            uint64_t bytes = 0;
            if constexpr (ws::HasState<T>::value) {
                Arena arena;
                ws2_host host{sizeof(ws2_host), &arena, Arena::alloc};
                T dsp{};
                ws::Setup setup{config, host};
                bool ok = true;
                if constexpr (std::is_same_v<decltype(dsp.prepare(setup)), bool>)
                    ok = dsp.prepare(setup);
                else dsp.prepare(setup);
                prepared = ok ? WS2_OK : WS2_INVALID;
                if (ok) {
                    dsp.reset();
                    Count count;
                    ws2_writer writer{sizeof(ws2_writer), &count, Count::write};
                    status = dsp.save_state(ws::Writer(&writer));
                    bytes = count.bytes;
                }
            }
            // Delay refuses before the writer receives anything at 96 kHz.
            // Report actual written bytes and status, never label a refusal as 0-byte state.
            std::printf("MEM %u %u %zu %zu %d %d %llu\n", rate, channels,
                        mem.large_bytes, mem.alignment, prepared, status,
                        static_cast<unsigned long long>(bytes));
        }
    }
    return 0;
}
#undef WS_REGISTER_MODULE
#define WS_REGISTER_MODULE(T) int main() { return measure<T>(); }
#endif
#include WS_S2_MODULE
