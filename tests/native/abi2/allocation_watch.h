// SPDX-License-Identifier: MIT
#pragma once
#include <atomic>
#include <cstdint>
namespace allocation_watch {
extern std::atomic<bool> enabled;
extern std::atomic<uint64_t> count;
// Define TLS in every test TU that uses ThreadScope/record() via C++17 inline
// variables; an extern-only TLS wrapper reached a null pointer under UBSan.
inline thread_local bool thread_enabled = false;
inline thread_local uint64_t thread_count = 0;
struct Scope {
    Scope(){count=0;enabled=true;}
    ~Scope(){enabled=false;}
    uint64_t allocations()const{return count.load();}
};
// For a render thread running concurrently with legal control-thread allocations.
struct ThreadScope {
    ThreadScope() {
        thread_count = 0;
        thread_enabled = true;
    }
    ~ThreadScope() { thread_enabled = false; }
    uint64_t allocations() const { return thread_count; }
};
}
