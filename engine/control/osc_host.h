// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../../host/net/osc_service.h"
#include "../../host/osc/pattern.h"
#include "app_engine.h"
#include "monitor_capture.h"
#include <array>
#include <memory>
#include <string>
#include <vector>
namespace wirescape::osc {
// Control-owner host; the worker reads the current graph generation on delivery.
class Host {
    std::unique_ptr<Service> service_;
    std::vector<RouteState> disabled_; // modules with every row disabled: no socket (#612)
    // Every configured OSC In route has compiled patterns, including all-enabled
    // routes. Service owns one worker, so its read-only route configuration and
    // bounded address cache have exactly one ingress-thread writer.
    struct Filter {
        uint32_t node = 0;
        uint16_t port = 0;
        std::array<Pattern, 8> patterns{};
        std::array<bool, 8> enabled{};
    };
    std::vector<std::unique_ptr<Filter>> filters_;
    struct AddressMatch {
        std::array<char, 256> address{};
        uint16_t port = 0, length = 0;
        uint32_t enabled_mask = 0; // one bit per configured OSC In filter (maximum 32)
        bool valid = false, known = false;
    };
    std::array<AddressMatch, 128> cached_matches_{};
    static bool accept(void *, uint32_t, std::string_view) noexcept;
    // A74 temporary diagnostic: sole worker writes, control reads only after
    // Service::stop joins. Fixed-size history before first refusal, plus a
    // bounded prefix of capacity refusals; no render-thread instrumentation.
    struct TraceSample {
        uint64_t ordinal = 0, arrival_ns = 0, frame = 0, ring_full = 0, generation = 0;
        uint32_t module = 0;
    };
    static constexpr size_t trace_limit = 256;
    bool trace_enabled_ = false;
    uint64_t attempts_ = 0, queued_ = 0, invalid_ = 0, capacity_ = 0, state_ = 0, other_ = 0;
    uint64_t events_start_ = 0, prior_count_ = 0, refusal_count_ = 0;
    std::array<TraceSample, trace_limit> prior_{}, refusals_{};
    void trace_delivery(uint32_t, uint64_t, int, const engine2::Meter &) noexcept;
    void report_trace() const noexcept;
    AppEngine *engine_ = nullptr;
    bool authorized_ = false;
    monitor::Capture *monitor_ = nullptr;
    static int deliver(void *, uint32_t, const ws2_event &, uint64_t) noexcept;

  public:
    explicit Host(bool confirmed_lan = false) : authorized_(confirmed_lan) {}
    ~Host() { stop(); }
    void observe(monitor::Capture *capture) noexcept { monitor_ = capture; }
    Host(const Host &) = delete;
    Host &operator=(const Host &) = delete;
    void start(AppEngine *, const std::string &document);
    void stop() noexcept;
    std::vector<RouteState> states() const;
};
} // namespace wirescape::osc
