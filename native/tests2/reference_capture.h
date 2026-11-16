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

template<class LegacyDescriptor>
inline void abi1_reference_capture_descriptor(const std::string& name,
                                              const LegacyDescriptor* desc) {
    const char* root = std::getenv("ABI1_REF_CAPTURE_DIR");
    if (!root || !*root) return;
    VERIFY(desc && name.find('/') == std::string::npos &&
           name.find('\\') == std::string::npos);
    const auto path = (std::filesystem::path(root) / (name + ".desc")).string();
    std::FILE* output = std::fopen(path.c_str(), "wb");
    VERIFY(output);
    std::fprintf(output, "id\\t%s\\n", desc->id);
    std::fprintf(output, "counts\\t%u\\t%u\\t%u\\n",
                 desc->input_count, desc->output_count, desc->parameter_count);
    for (uint32_t p = 0; p < desc->input_count; ++p)
        std::fprintf(output, "input\\t%u\\t%s\\n", p, desc->inputs[p].id);
    for (uint32_t p = 0; p < desc->output_count; ++p)
        std::fprintf(output, "output\\t%u\\t%s\\n", p, desc->outputs[p].id);
    for (uint32_t p = 0; p < desc->parameter_count; ++p) {
        uint32_t low, high, initial;
        std::memcpy(&low, &desc->parameters[p].minimum, 4);
        std::memcpy(&high, &desc->parameters[p].maximum, 4);
        std::memcpy(&initial, &desc->parameters[p].initial, 4);
        std::fprintf(output, "param\\t%u\\t%u\\t%08x\\t%08x\\t%08x\\n",
                     p, desc->parameters[p].id, low, high, initial);
    }
    VERIFY(std::fclose(output) == 0);
}
