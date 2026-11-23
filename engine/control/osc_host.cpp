// SPDX-License-Identifier: GPL-3.0-only
#include "osc_host.h"
#include <nlohmann/json.hpp>
#include <cstring>
#include <stdexcept>
namespace wirescape::osc {
int Host::deliver(void *context, uint32_t node, const ws2_event &event, uint64_t timestamp) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (!self.engine_) return WS2_INVALID;
    auto &graph = app_engine_native(self.engine_);
    const int result = graph.enqueue(2, node, WS2_DIRECT_PORT, event, timestamp, engine2::Timing::Timestamped,
                                     self.engine_generation_);
    if (result == WS2_OK && self.monitor_) self.monitor_->osc(node, event, timestamp);
    return result;
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
    engine_generation_ = app_engine_native(engine_).meter().generation;
    // Busy ports report unavailable status; they never refuse the patch.
    (void)service_->start();
}
void Host::stop() noexcept {
    if (service_) {
        service_->stop();
        service_.reset();
    }
    disabled_.clear();
    filters_.clear();
    for (auto &entry : cached_matches_) entry.valid = false;
    engine_ = nullptr;
    engine_generation_ = 0;
}
std::vector<RouteState> Host::states() const {
    auto out = service_ ? service_->states() : std::vector<RouteState>{};
    out.insert(out.end(), disabled_.begin(), disabled_.end());
    return out;
}
} // namespace wirescape::osc
