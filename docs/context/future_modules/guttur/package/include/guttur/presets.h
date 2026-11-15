// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "guttur/parameters.h"
#include <array>
namespace guttur {
struct Preset {const char* id; const char* name; std::array<double,kParamDefs.size()> values; double trim;};
extern const std::array<Preset,11> kPresets;
}
