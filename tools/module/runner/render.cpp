// SPDX-License-Identifier: GPL-3.0-only
#include "dispatch.h"
#include <iostream>
int module_render_main(int, const char* const*) {
    std::cerr << "render not implemented in MT1; MT3 owns this file\n";
    return 4;
}
