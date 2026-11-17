// SPDX-License-Identifier: GPL-3.0-only
#include "abi_ws2.h"
#include "dispatch.h"
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc < 2) { std::cerr << "expected describe, matrix or render\n"; return 2; }
    const std::string command(argv[1]);
    if (command == "describe") {
        HostModule module;
        const auto description = module.describe();
        std::cout << module.describe_json() << '\n';
        return description.errors.empty() ? 0 : 1;
    }
    if (command == "matrix") return module_matrix_main(argc - 1, const_cast<const char* const*>(argv + 1));
    if (command == "render") return module_render_main(argc - 1, const_cast<const char* const*>(argv + 1));
    std::cerr << "unknown runner command\n";
    return 2;
}
