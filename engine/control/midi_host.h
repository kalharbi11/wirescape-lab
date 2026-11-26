// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "app_engine.h"
#include "midi_service.h"
#include <atomic>
#include <memory>
#include <string>
#include <vector>
namespace wirescape::monitor {
class Capture;
}
namespace wirescape::midi {
// Control owner only. Stop joins ingress before its borrowed engine is replaced.
class Host {
    bool injected_backend_ = false;
    std::unique_ptr<Backend> backend_;
    std::unique_ptr<Service> service_;
    AppEngine *engine_ = nullptr;
    bool authorized_ = false;
    std::string last_statistics_;
    Counters completed_{}; // Final totals from stopped services, control owner only.
    std::atomic<uint64_t> release_panics_{0}; // failed release enqueue -> global engine panic
    std::vector<Endpoint> enabled_;
    monitor::Capture *monitor_ = nullptr;
    static int deliver(void *, uint32_t, const ws2_event &, uint64_t) noexcept;

  public:
    explicit Host(bool authorized = false, std::unique_ptr<Backend> fake = {});
    ~Host();
    void observe(monitor::Capture *capture) noexcept { monitor_ = capture; }
    bool authorized() const noexcept { return authorized_; }
    void authorize(bool);
    std::vector<Endpoint> endpoints();
    const std::vector<Endpoint> &enabled() const { return enabled_; }
    void select(Endpoint, bool);
    void restore(const std::string &document);
    bool start(AppEngine *, const std::string &document, std::string &error);
    // Control-thread admission check: online means the backend opened this identity.
    bool online(const Endpoint &) const;
    // Atomically accept a prepared graph and its subscriptions on the control thread.
    // Refusal (including a busy MIDI worker) preserves graph and routes for retry.
    bool replan(AppEngine *candidate, const std::string &document, uint64_t timeout_ns, std::string &error,
                engine2::Engine::BeforePublish before_publish = nullptr, void *context = nullptr);
    void stop();
    Counters counters() const noexcept;
    std::string diagnostics() const;
};
}
