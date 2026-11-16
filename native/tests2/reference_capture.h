// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Test-only collection of actual ABI1 IEEE-754 binary32 output words.
// Disabled unless the runner explicitly sets ABI1_REF_CAPTURE_DIR.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>

inline void abi1_reference_capture(const std::string& name,
                                   const std::vector<float>& samples) {
    const char* root = std::getenv("ABI1_REF_CAPTURE_DIR");
    if (!root || !*root) return;
    static_assert(sizeof(float) == 4, "ABI1 fixtures require IEEE binary32");
    VERIFY(name.find('/') == std::string::npos && name.find('\\') == std::string::npos);
    std::filesystem::create_directories(root);
    const auto path = (std::filesystem::path(root) / (name + ".f32le")).string();
    std::FILE* output = std::fopen(path.c_str(), "wb");
    VERIFY(output);
    for (float sample : samples) {
        uint32_t word;
        std::memcpy(&word, &sample, sizeof word);
        const unsigned char bytes[] = {
            static_cast<unsigned char>(word),
            static_cast<unsigned char>(word >> 8),
            static_cast<unsigned char>(word >> 16),
            static_cast<unsigned char>(word >> 24)
        };
        VERIFY(std::fwrite(bytes, 1, sizeof bytes, output) == sizeof bytes);
    }
    VERIFY(std::fclose(output) == 0);
}
