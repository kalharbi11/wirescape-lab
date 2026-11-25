// SPDX-License-Identifier: GPL-3.0-only
#include "osc_host.h"
#include <nlohmann/json.hpp>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
namespace wirescape::osc {
int Host::deliver(void *context, uint32_t node, const ws2_event &event, uint64_t timestamp) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (!self.engine_) return WS2_INVALID;
    auto &graph = app_engine_native(self.engine_);
    const int result = graph.enqueue(2, node, WS2_DIRECT_PORT, event, timestamp, engine2::Timing::Timestamped,
                                     app_engine_generation(self.engine_));
    if (self.trace_enabled_)
        self.trace_delivery(node, timestamp, result, graph.meter());
    if (result == WS2_OK && self.monitor_) self.monitor_->osc(node, event, timestamp);
    return result;
}
// A74: diagnostic-only observation, on the existing sole producer worker.
void Host::trace_delivery(uint32_t node, uint64_t timestamp, int result,
                          const engine2::Meter &meter) noexcept {
    const TraceSample sample{++attempts_, timestamp, meter.frame, meter.ring_full,
                             meter.generation, node};
    if (result == WS2_CAPACITY) {
        ++capacity_;
        if (refusal_count_ < trace_limit) refusals_[refusal_count_++] = sample;
    } else {
        if (result == WS2_OK) ++queued_;
        else if (result == WS2_INVALID) ++invalid_;
        else if (result == WS2_STATE) ++state_;
        else ++other_;
        // Only the last 256 attempts before the first refusal are retained.
        if (!capacity_) prior_[prior_count_++ % trace_limit] = sample;
    }
}
void Host::report_trace() const noexcept {
    if (!trace_enabled_ || !engine_) return;
    const auto end = app_engine_get_meter(engine_);
    const uint64_t prior_size = capacity_ ? (prior_count_ < trace_limit ? prior_count_ : trace_limit) : 0;
    const auto u = [](uint64_t value) { return static_cast<unsigned long long>(value); };
    // Meter.events is engine-wide processed-event count, not OSC ring drains.
    std::fprintf(stderr,
        "osc_capacity_epoch queued=%llu invalid=%llu capacity=%llu state=%llu other=%llu "
        "events_start=%llu events_end=%llu trace_count=%llu omitted=%llu\n",
        u(queued_), u(invalid_), u(capacity_), u(state_), u(other_), u(events_start_),
        u(end.events), u(prior_size + refusal_count_), u(capacity_ - refusal_count_));
    auto print = [&](const char *kind, const TraceSample &v) {
        std::fprintf(stderr,
            "osc_capacity_sample kind=%s ordinal=%llu module=%u arrival_ns=%llu frame=%llu "
            "ring_full=%llu generation=%llu\n",
            kind, u(v.ordinal), unsigned(v.module), u(v.arrival_ns), u(v.frame),
            u(v.ring_full), u(v.generation));
    };
    for (uint64_t i = prior_count_ - prior_size; i < prior_count_; ++i)
        print("prior", prior_[i % trace_limit]);
    for (uint64_t i = 0; i < refusal_count_; ++i) print("refusal", refusals_[i]);
}
// At 64 x 200 Hz, sending each recognized message to all nine OSC In
// modules exhausts the bounded engine ingress ring. Match known addresses
// *once* against all routes on the incoming port, then deliver only to matching
// enabled modules. Unmatched addresses retain the existing `messages`
// discovery path; disabled rows never opt a route into accepted delivery.
// Service calls accept serially on its sole worker, so no locking or allocation
// is needed on this ingress hot path. Each cache entry is bounded to 255 bytes.
bool Host::accept(void *context, uint32_t node, std::string_view address) noexcept {
    auto &self = *static_cast<Host *>(context);
    size_t current = self.filters_.size();
    uint16_t port = 0;
    for (size_t i = 0; i < self.filters_.size(); ++i)
        if (self.filters_[i]->node == node) {
            current = i;
            port = self.filters_[i]->port;
            break;
        }
    if (current == self.filters_.size()) return true; // unregistered route: prior discovery behavior
    if (address.size() > 255) return false; // OSC decoder's existing upper bound

    uint32_t hash = 2166136261u;
    for (unsigned char byte : address) {
        hash ^= byte;
        hash *= 16777619u;
    }
    hash = (hash ^ port) * 16777619u;
    constexpr uint32_t slots = 128;
    const uint32_t first = hash % slots;
    AddressMatch *found = nullptr;
    for (uint32_t offset = 0; offset < 4; ++offset) {
        auto &candidate = self.cached_matches_[(first + offset) % slots];
        if (!candidate.valid ||
            (candidate.port == port && candidate.length == address.size() &&
             std::memcmp(candidate.address.data(), address.data(), address.size()) == 0)) {
            found = &candidate;
            break;
        }
    }
    // Bounded four-probe cache: collisions cause only recomputation, not loss.
    if (!found) found = &self.cached_matches_[first];
    if (!found->valid || found->port != port || found->length != address.size() ||
        std::memcmp(found->address.data(), address.data(), address.size()) != 0) {
        found->port = port;
        found->length = uint16_t(address.size());
        if (!address.empty()) std::memcpy(found->address.data(), address.data(), address.size());
        found->known = false;
        found->enabled_mask = 0;
        // Service bounds routes to 32. Include fully disabled filters so their
        // addresses cannot be reintroduced through another route's discovery.
        for (size_t i = 0; i < self.filters_.size(); ++i) {
            const auto &filter = *self.filters_[i];
            if (filter.port != port) continue;
            for (uint32_t row = 0; row < filter.patterns.size(); ++row) {
                if (!filter.patterns[row].match(address)) continue;
                found->known = true;
                if (filter.enabled[row]) found->enabled_mask |= uint32_t{1} << i;
            }
        }
        found->valid = true;
    }
    return !found->known || (found->enabled_mask & (uint32_t{1} << current)) != 0;
}
void Host::start(AppEngine *engine, const std::string &document) {
    stop();
    auto patch = nlohmann::json::parse(document);
    std::vector<Route> routes;
    for (const auto &module : patch.at("modules")) {
        if (module.value("module", std::string{}) != "osc.in") continue;
        const auto config = module.value("config", nlohmann::json::object());
        const uint32_t port = config.value("port", 9000u);
        if (port < 1 || port > 65535) throw std::runtime_error("OSC port outside 1..65535");
        const uint32_t node = module.at("id").get<uint32_t>();
        const bool lan = config.value("lan", false);
        // Absent `enabled` means enabled; only a module whose eight rows are all
        // explicitly disabled ("Clear") is left unbound and reported as disabled.
        uint32_t disabled = 0;
        auto filter = std::make_unique<Filter>();
        filter->node = node;
        filter->port = uint16_t(port);
        filter->enabled.fill(true);
        std::array<std::string, 8> patterns;
        for (uint32_t i = 0; i < 8; ++i) patterns[i] = "/pico1/knob/" + std::to_string(i + 1);
        if (config.contains("rows") && config.at("rows").is_array())
            for (size_t i = 0; i < config.at("rows").size() && i < 8; ++i) {
                const auto &row = config.at("rows").at(i);
                if (!row.is_object()) continue;
                if (row.contains("pattern") && row.at("pattern").is_string())
                    patterns[i] = row.at("pattern").get<std::string>();
                if (row.contains("enabled") && row.at("enabled") == false) {
                    filter->enabled[i] = false;
                    ++disabled;
                }
            }
        // Pattern routing applies to every module, not only partial Clears.
        // A fully disabled route is still recognized but never bound.
        for (uint32_t i = 0; i < 8; ++i)
            if (!filter->patterns[i].compile(patterns[i])) throw std::runtime_error("Invalid OSC row pattern");
        filters_.push_back(std::move(filter));
        if (disabled >= 8) {
            RouteState state;
            state.node = node;
            state.port = uint16_t(port);
            state.lan_requested = lan;
            state.state = "disabled";
            disabled_.push_back(state);
        } else routes.push_back({node, uint16_t(port), lan});
    }
    if (routes.size() + disabled_.size() > 32) throw std::runtime_error("Too many OSC routes");
    if (routes.empty()) return;
    service_ = std::make_unique<Service>(Sink{this, deliver, accept}, authorized_);
    for (const auto &route : routes)
        if (!service_->add(route)) throw std::runtime_error("Cannot stage OSC route");
    engine_ = engine;
    const char *diagnostic = std::getenv("WIRESCAPE_OSC_CAPACITY_DIAGNOSTIC");
    trace_enabled_ = diagnostic && std::strcmp(diagnostic, "1") == 0 && engine_;
    attempts_ = queued_ = invalid_ = capacity_ = state_ = other_ = 0;
    prior_count_ = refusal_count_ = 0;
    events_start_ = trace_enabled_ ? app_engine_get_meter(engine_).events : 0;
    // Busy ports report unavailable status; they never refuse the patch.
    (void)service_->start();
}
void Host::stop() noexcept {
    if (service_) {
        service_->stop();
        report_trace(); // after join, before engine retirement
        service_.reset();
    }
    trace_enabled_ = false;
    disabled_.clear();
    filters_.clear();
    for (auto &entry : cached_matches_) entry.valid = false;
    engine_ = nullptr;
}
std::vector<RouteState> Host::states() const {
    auto out = service_ ? service_->states() : std::vector<RouteState>{};
    out.insert(out.end(), disabled_.begin(), disabled_.end());
    return out;
}
} // namespace wirescape::osc
