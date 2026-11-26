// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Host-only A77 validator; not part of the audio module's include graph.
#include "dsp.h"
#include <cstdio>
namespace wirescape::osc {
inline bool validate_osc_in_rows(const OscInRows &data, char (&error)[128]) {
    error[0] = '\0';
    for (uint32_t i = 0; i < 8; ++i) {
        const auto &row = data.rows[i];
        if (!(row.input_max > row.input_min)) {
            std::snprintf(error, sizeof(error), "routes.rows[%u].input_max: must exceed input_min", i);
            return false;
        }
        const auto *end = static_cast<const char *>(std::memchr(row.pattern, 0, sizeof(row.pattern)));
        Pattern pattern;
        if (!end || row.pattern[0] != '/' ||
            !pattern.compile(std::string_view(row.pattern, size_t(end - row.pattern)))) {
            std::snprintf(error, sizeof(error), "routes.rows[%u].pattern: invalid OSC pattern", i);
            return false;
        }
    }
    return true;
}
// Off-RT conversion of already validated legacy config, including all eight
// row-specific defaults. Host-owned pointers are deliberately excluded.
inline bool materialize_osc_in_rows(const Configuration &legacy, OscInRows &out, char (&error)[128]) {
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
