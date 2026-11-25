// SPDX-License-Identifier: GPL-3.0-only
#include "wirescape_sdk.h"
#include "../../tools/module/runner/abi_ws2.h"
#include <cstdio>
#include <cstdlib>
struct LegacyModule {
    static constexpr ws::Info info{"test.legacy_runner","Legacy runner",1};
    static constexpr std::array<ws2_port,0> inputs{};
    static constexpr std::array outputs{ws::port("out","Out")};
    static constexpr std::array<ws2_param,0> params{};
    void prepare(const ws::Setup &) {}
    void reset() {}
    void process(ws::Block &b) {
        b.out(0).set_channels(1);
        b.out(0).mark_constant();
        b.out(0).ch(0)[0] = 1;
    }
};
static ws2_descriptor descriptor = *ws::Module<LegacyModule>::descriptor();
extern "C" WS2_EXPORT uint32_t WS2_CALL ws_module2_abi_version(void) { return WS_ABI2_VERSION; }
extern "C" WS2_EXPORT const ws2_descriptor *WS2_CALL ws_module2_entry(void) { return &descriptor; }
int main() {
    descriptor.struct_size = offsetof(ws2_descriptor, data_slot_count);
    descriptor.data_slot_count = 1; // Absent bytes must not affect description.
    HostModule legacy;
    const auto described = legacy.describe();
    if (!described.errors.empty() || described.id != "test.legacy_runner" ||
        described.abi_version != WS_ABI2_VERSION || described.outputs.size() != 1) return 1;
    --descriptor.struct_size;
    HostModule truncated;
    if (truncated.describe().errors.empty()) return 2;
    std::puts("PASS legacy descriptor describe and truncated descriptor refusal");
}
