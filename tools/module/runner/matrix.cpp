// SPDX-License-Identifier: GPL-3.0-only
#include "dispatch.h"
#include <iostream>
int module_matrix_main(int, const char* const*) {
    std::cerr << "matrix not implemented in MT1; MT2 owns this file\n";
    return 4;
}
