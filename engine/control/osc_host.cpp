// SPDX-License-Identifier: GPL-3.0-only
#include "osc_host.h"
#include "../../host/osc/codec.h"
#include "../../host/document/io_data_migration.h"
#include <nlohmann/json.hpp>
#include <cstring>
#include <stdexcept>
namespace wirescape::osc {
int Host::deliver(void *context, uint32_t node, const ws2_event &event, uint64_t timestamp) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (!self.engine_) return WS2_INVALID;
    auto &graph = app_engine_native(self.engine_);
    const int result = graph.enqueue(2, node, WS2_DIRECT_PORT, event, timestamp, engine2::Timing::Timestamped,
                                     app_engine_generation(self.engine_));
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
    const auto &match = self.classify(port, address);
    return !match.known || (match.enabled_mask & (uint32_t{1} << current)) != 0;
}
const Host::AddressMatch &Host::classify(uint16_t port, std::string_view address) noexcept {
    auto &self = *this;
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
        found->row_masks.fill(0);
        // Service bounds routes to 32. Include fully disabled filters so their
        // addresses cannot be reintroduced through another route's discovery.
        for (size_t i = 0; i < self.filters_.size(); ++i) {
            const auto &filter = *self.filters_[i];
            if (filter.port != port) continue;
            for (uint32_t row = 0; row < filter.patterns.size(); ++row) {
                if (!filter.patterns[row].match(address)) continue;
                found->known = true;
                if (filter.enabled[row]) {
                    found->enabled_mask |= uint32_t{1} << i;
                    found->row_masks[i] |= uint8_t(1u << row);
                }
            }
        }
        found->valid = true;
    }
    return *found;
}
void Host::match_rows(void *context, uint16_t port, std::string_view address,
                      uint64_t timestamp_ns) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (address.size() > 255) return;
    const auto &match = self.classify(port, address);
    for (size_t i = 0; i < self.filters_.size(); ++i) {
        const auto mask = match.row_masks[i];
        if (!mask) continue;
        for (size_t row = 0; row < 8; ++row) {
            if (!(mask & (1u << row))) continue;
            auto &activity = self.activity_[i][row];
            activity.sequence.fetch_add(1);
            activity.timestamp_ns.store(timestamp_ns);
            activity.sequence.fetch_add(1);
        }
    }
}
void Host::reset_activity() noexcept {
    // Called only with the service stopped and joined.
    for (auto &filter : activity_) for (auto &row : filter) {
        row.sequence.store(0, std::memory_order_relaxed);
        row.timestamp_ns.store(0, std::memory_order_relaxed);
        row.snapshot = {};
    }
}
bool Host::observing(void *context) noexcept {
    const auto &observer = static_cast<Host *>(context)->controller_;
    return observer.message && observer.enabled && observer.enabled(observer.context);
}
void Host::observe_message(void *context, uint16_t port, const Message &message) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (!observing(context) || message.address.size() > 255) return;
    const auto &match = self.classify(port, message.address);
    const bool matched = match.enabled_mask != 0;
    const bool disabled_only = match.known && !matched;
    const auto &observer = self.controller_;
    observer.message(observer.context, port, message, matched, disabled_only, observer.generation);
}
void Host::observe_control_message(void *context, uint16_t port, const Message &message) noexcept {
    auto &self = *static_cast<Host *>(context);
    if (!observing(context) || message.address.size() > 255) return;
    const auto &match = self.classify(port, message.address);
    const auto &observer = self.controller_;
    if (observer.control_message)
        observer.control_message(observer.context, port, message, match.enabled_mask != 0, observer.generation);
}
void Host::prepare(AppEngine *engine, const std::string &document,
                   std::optional<uint64_t> activity_generation) {
    stop();
    if (!activity_generation || activity_generation != activity_generation_) reset_activity();
    activity_generation_ = activity_generation;
    auto patch = nlohmann::json::parse(document);
    std::vector<Route> routes;
    for (auto &module : patch.at("modules")) {
        if (module.value("module", std::string{}) != "osc.in") continue;
        document::migrate_io_module(module);
        const auto data = document::read_io_slot<OscInRows, OscIn, validate_osc_in_rows>(module);
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
        // Pattern routing applies to every module, including disabled rows.
        // Use the same validated, migrated rows as the DSP slot.
        for (uint32_t i = 0; i < 8; ++i) {
            const auto &row = data.rows[i];
            filter->enabled[i] = row.enabled != 0;
            if (!row.enabled) ++disabled;
            if (!filter->patterns[i].compile(row.pattern))
                throw std::runtime_error("Invalid OSC row pattern");
        }
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
    if (control_port_) routes.push_back({0, control_port_, control_lan_, true});
    if (routes.size() + disabled_.size() > 32) throw std::runtime_error("Too many OSC routes");
    if (routes.empty()) return;
    service_ = std::make_unique<Service>(Sink{this, deliver, accept, observing, observe_message, observe_control_message, match_rows}, authorized_);
    for (const auto &route : routes)
        if (!service_->add(route)) throw std::runtime_error("Cannot stage OSC route");
    engine_ = engine;
    // No socket opens during staging; activation is an accepted-only step.
}
void Host::activate() noexcept {
    if (!service_) return;
    try {
        // Busy ports report unavailable status; they never refuse the patch.
        (void)service_->start();
    } catch (...) {
        service_->stop();
    }
}
void Host::start(AppEngine *engine, const std::string &document) {
    prepare(engine, document);
    activate();
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
}
std::vector<RouteState> Host::states() const {
    auto out = service_ ? service_->states() : std::vector<RouteState>{};
    out.insert(out.end(), disabled_.begin(), disabled_.end());
    for (auto &route : out) {
        if (route.control) continue;
        for (size_t i = 0; i < filters_.size(); ++i) {
            if (filters_[i]->node != route.node) continue;
            for (size_t row = 0; row < route.rows.size(); ++row) {
                const auto &activity = activity_[i][row];
                // Bounded status-side retries; no torn count/time pairs and no
                // blocking the worker or adding work to render/audio.
                for (unsigned attempt = 0; attempt < 4; ++attempt) {
                    const auto before = activity.sequence.load();
                    if (before & 1) continue;
                    const auto timestamp = activity.timestamp_ns.load();
                    if (before == activity.sequence.load()) {
                        activity.snapshot = {before / 2, timestamp};
                        break;
                    }
                }
                route.rows[row] = activity.snapshot;
            }
            break;
        }
    }
    return out;
}
} // namespace wirescape::osc
