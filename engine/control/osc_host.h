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
// A110: sidecar-owned storage, host borrows a quiescent-installed observer.
// The generation is fixed for the lifetime of this filter/worker instance.
struct ControllerObserver {
    void *context = nullptr;
    bool (*enabled)(void *) noexcept = nullptr;
    void (*message)(void *, uint16_t, const Message &, bool matched, bool disabled_only,
                    uint64_t route_generation) noexcept = nullptr;
    uint64_t generation = 0;
};
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
    const AddressMatch &classify(uint16_t port, std::string_view address) noexcept;
    static bool accept(void *, uint32_t, std::string_view) noexcept;
    static bool observing(void *) noexcept;
    static void observe_message(void *, uint16_t, const Message &) noexcept;
    ControllerObserver controller_{};
    AppEngine *engine_ = nullptr;
    bool authorized_ = false;
    monitor::Capture *monitor_ = nullptr;
    static int deliver(void *, uint32_t, const ws2_event &, uint64_t) noexcept;

  public:
    explicit Host(bool confirmed_lan = false) : authorized_(confirmed_lan) {}
    ~Host() { stop(); }
    void observe(monitor::Capture *capture) noexcept { monitor_ = capture; }
    // Control owner only, with the worker stopped (or not yet activated).
    void observe_controller(ControllerObserver observer) noexcept { controller_ = observer; }
    Host(const Host &) = delete;
    Host &operator=(const Host &) = delete;
    // Stage filters and socket declarations without opening sockets. Activate
    // only after the engine accepts the corresponding document/slot write.
    void prepare(AppEngine *, const std::string &document);
    void activate() noexcept;
    void start(AppEngine *, const std::string &document);
    void stop() noexcept;
    std::vector<RouteState> states() const;
};
} // namespace wirescape::osc
