// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only A77 validator; not part of the audio module's include graph.
#include "dsp.h"
#include <string>
namespace wirescape::osc {
inline bool validate_osc_in_rows(const OscInRows &data, std::string &error) {
    error.clear();
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &row = data.rows[i];
        const auto prefix = "routes.rows[" + std::to_string(i) + "].";
        if (!(row.input_max > row.input_min)) {
            error = prefix + "input_max: must exceed input_min";
            return false;
        }
        const auto *end = static_cast<const char *>(std::memchr(row.pattern, 0, sizeof(row.pattern)));
        Pattern pattern;
        if (!end || row.pattern[0] != '/' ||
            !pattern.compile(std::string_view(row.pattern, size_t(end - row.pattern)))) {
            error = prefix + "pattern: invalid OSC pattern";
            return false;
        }
    }
    return true;
}
// Off-RT conversion of already validated legacy config, including all eight
// row-specific defaults. Host-owned pointers are deliberately excluded.
inline bool materialize_osc_in_rows(const Configuration &legacy, OscInRows &out, std::string &error) {
    OscInRows candidate{};
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &src = legacy.rows[i];
        auto &dst = candidate.rows[i];
        std::memcpy(dst.pattern, src.pattern, sizeof(dst.pattern));
        dst.argument = src.argument; dst.kind = src.kind;
        dst.input_min = src.input_min; dst.input_max = src.input_max;
        dst.output_min = src.output_min; dst.output_max = src.output_max;
        dst.smoothing_ms = src.smoothing_ms; dst.timeout_ms = src.timeout_ms;
        dst.stale = src.stale; dst.enabled = uint8_t(src.enabled);
    }
    if (!validate_osc_in_rows(candidate, error)) return false;
    out = candidate;
    return true;
}
} // namespace wirescape::osc
