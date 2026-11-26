// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include <atomic>
#include <cstdint>

namespace wirescape::engine2 {
// A51: a timeout may refuse only an unclaimed publication. The injected
// monotonic clock and yield make both sides of the cancellation race testable.
template<class Layout, class Deadline, class Now, class Yield>
bool publish_and_wait(std::atomic<Layout *> &pending, std::atomic<uint64_t> &adopted,
                      Layout *next, uint64_t revision, Deadline deadline, Now now, Yield yield) noexcept {
    pending.store(next, std::memory_order_release);
    bool claimed = false;
    while (adopted.load(std::memory_order_acquire) < revision) {
        if (!claimed && now() >= deadline) {
            auto *expected = next;
            if (pending.compare_exchange_strong(expected, nullptr, std::memory_order_acq_rel)) return false;
            claimed = true;
        }
        yield();
    }
    return true;
}
} // namespace wirescape::engine2
