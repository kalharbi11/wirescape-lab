// SPDX-License-Identifier: GPL-3.0-only
#include "midi_host.h"
#include "midi_release.h"
#include "midi_service.h"
#include "monitor_capture.h"
#include <algorithm>
#include <nlohmann/json.hpp>
#include <stdexcept>
namespace wirescape::midi {
namespace {
// Service-owned counters only; release_panics_ already spans the Host lifetime.
void add_service_counters(Counters &total, const Counters &live) noexcept {
    total.received += live.received;
    total.dropped += live.dropped;
    total.malformed += live.malformed;
    total.oversize += live.oversize;
    total.ring_full += live.ring_full;
    total.disconnects += live.disconnects;
    total.send_fail += live.send_fail;
    total.ignored_rpn += live.ignored_rpn;
}
std::vector<Route> subscriptions(const std::string &document) {
    const auto j = nlohmann::json::parse(document);
    std::vector<Route> routes;
    for (auto &m : j.at("modules")) {
        const auto type = m.value("module", m.value("type", std::string{}));
        if (type == "host.keyboard") {
            const auto node = m.at("id").get<uint32_t>();
            routes.push_back({node, {}, true, true});
            continue;
        }
        if (type != "midi.in") continue;
        auto c = m.value("config", nlohmann::json::object());
        auto name = c.value("endpoint", std::string("all_enabled"));
        Route r;
        r.node = m.at("id").get<uint32_t>();
        r.all_enabled = name == "all_enabled";
        r.endpoint = {name, c.value("system_name", std::string{})};
        routes.push_back(std::move(r));
    }
    if (routes.size() > 64) throw std::runtime_error("Too many MIDI routes");
    return routes;
}
} // namespace
Host::Host(bool authorized, std::unique_ptr<Backend> fake)
    : injected_backend_(bool(fake)), backend_(std::move(fake)), authorized_(authorized) {
    if (!backend_ && authorized_) backend_ = real_backend(true);
}
Host::~Host(){stop();}
void Host::authorize(bool enabled) {
    if (service_) throw std::runtime_error("Stop playback before changing MIDI authorization");
    if (enabled && !backend_) backend_ = real_backend(true);
    if (!enabled && !injected_backend_) backend_.reset();
    authorized_ = enabled;
}
std::vector<Endpoint> Host::endpoints() {
    if (service_) throw std::runtime_error("Stop playback before refreshing MIDI endpoints");
    return authorized_ && backend_ ? backend_->endpoints() : std::vector<Endpoint>{};
}
void Host::select(Endpoint selection,bool enable){if(service_)throw std::runtime_error("Stop playback before changing MIDI endpoints");auto match=[&](const Endpoint&s){return s.name==selection.name&&s.system_name==selection.system_name;};enabled_.erase(std::remove_if(enabled_.begin(),enabled_.end(),match),enabled_.end());if(enable)enabled_.push_back(std::move(selection));}
void Host::restore(const std::string&document){
 if(service_)throw std::runtime_error("Stop playback before restoring MIDI endpoints");
 auto j=nlohmann::json::parse(document);std::vector<Endpoint> staged;
 if(j.contains("devices")){
  if(!j.at("devices").is_array())throw std::runtime_error("Invalid devices array");
  for(auto&d:j.at("devices")){
   if(!d.is_object()||!d.contains("kind")||!d["kind"].is_string()||d["kind"]!="midi")continue;
   if(d.contains("enabled")&&!d["enabled"].is_boolean())throw std::runtime_error("Invalid MIDI enabled flag");
   if(!d.value("enabled",false))continue;
   if(!d.contains("name")||!d["name"].is_string()||d["name"].get<std::string>().empty()||(d.contains("system_name")&&!d["system_name"].is_string()))throw std::runtime_error("Invalid MIDI endpoint identity");
   Endpoint e{d.at("name").get<std::string>(),d.value("system_name",std::string{})};
   if(std::none_of(staged.begin(),staged.end(),[&](const Endpoint&s){return s.name==e.name&&s.system_name==e.system_name;}))staged.push_back(std::move(e));
   if(staged.size()>16)throw std::runtime_error("At most 16 MIDI endpoints may be enabled");
  }
 }enabled_=std::move(staged);
}

int Host::deliver(void *opaque, uint32_t node, const ws2_event &e, uint64_t ns) noexcept {
    auto &h = *static_cast<Host *>(opaque);
    auto &engine = app_engine_native(h.engine_);
    int result = engine.enqueue(1, node, WS2_DIRECT_PORT, e, ns, wirescape::engine2::Timing::Timestamped,
                                engine.meter().generation);
    if (result != WS2_OK && (e.type == WS2_NOTE_OFF || e.type == WS2_NOTE_CHOKE || wirescape::engine2::midi_release(e))) {
        h.release_panics_.fetch_add(1, std::memory_order_relaxed);
        engine.panic();
    }
    if (result == WS2_OK && h.monitor_) h.monitor_->midi(node, e, ns);
    return result;
}
bool Host::start(AppEngine*engine,const std::string&document,std::string&error){stop();try{
        engine_ = engine;
        if (enabled_.empty()) {
            error.clear();
            return true;
        }
        if (!authorized_ || !backend_) throw std::runtime_error("Enable MIDI before opening selected endpoints");
        if (!engine) throw std::runtime_error("No MIDI render engine");
        auto routes = subscriptions(document);
        engine_ = engine;
        service_ = std::make_unique<Service>(*backend_, Sink{this, deliver});
        for (auto &s : enabled_)
            if (!service_->enable({s.name, s.system_name})) throw std::runtime_error("Too many enabled MIDI endpoints");
        if (!service_->replace_routes(std::move(routes))) throw std::runtime_error("Invalid MIDI routes");
        // Resolve/open once on the control thread before reporting an explicit
        // enable result. Saved disconnected endpoints remain offline but are
        // tolerated at startup; Session checks the requested identity on toggle.
        service_->poll();
        if (!service_->start()) throw std::runtime_error("MIDI service did not start");
        error.clear();
        return true;
 }catch(const std::exception&e){error=e.what();stop();return false;}}
bool Host::replan(AppEngine *candidate, const std::string &document, uint64_t timeout_ns, std::string &error,
                  engine2::Engine::BeforePublish before_publish, void *context) {
    try {
        auto routes = subscriptions(document); // Parse/allocate before attempting any live change.
        if (std::any_of(routes.begin(), routes.end(), [](const Route &r) { return !r.node; }))
            throw std::runtime_error("Invalid MIDI route");
        // replace_routes calls commit only after acquiring its try-lock. A valid
        // route table with no commit invocation therefore means MIDI contention.
        bool commit_entered = false;
        int result = WS2_STATE;
        auto commit = [&] {
            commit_entered = true;
            if (engine_) result = app_engine_replan(engine_, candidate, timeout_ns, before_publish, context);
            return result == WS2_OK;
        };
        if (!(service_ ? service_->replace_routes(std::move(routes), commit) : commit())) {
            error = service_ && !commit_entered ? "MIDI worker busy" :
                result == WS2_CAPACITY ? app_engine_error(engine_) : "Live graph refused";
            return false;
        }
        error.clear();
        return true;
    } catch (const std::exception &e) {
        error = e.what();
        return false;
    }
}
bool Host::online(const Endpoint &endpoint) const {
    if (!service_) return false;
    const auto states = service_->endpoint_states();
    return std::any_of(states.begin(), states.end(), [&](const auto &s) {
        return s.saved.name == endpoint.name && s.saved.system_name == endpoint.system_name && s.online;
    });
}
void Host::stop() {
    if (service_) {
        service_->stop();
        last_statistics_ = diagnostics(); // Snapshot cumulative totals and stopped ports.
        add_service_counters(completed_, service_->counters());
        service_.reset();
    }
    engine_ = nullptr;
}
std::string Host::diagnostics() const {
    if (!service_ && !last_statistics_.empty()) return last_statistics_;
    auto c = counters();
    auto ports = nlohmann::json::array();
    if (service_)
        for (const auto &s : service_->endpoint_states())
            ports.push_back({{"name", s.saved.name},
                             {"system_name", s.saved.system_name},
                             {"received", s.received},
                             {"online", s.online}});
    return nlohmann::json{{"received", c.received},   {"dropped", c.dropped},
                          {"malformed", c.malformed}, {"oversize", c.oversize},
                          {"ring_full", c.ring_full}, {"disconnects", c.disconnects},
                          {"send_fail", c.send_fail}, {"ignored_rpn", c.ignored_rpn},
                          {"release_panics", c.release_panics}, {"ports", ports}}
        .dump();
}
Counters Host::counters()const noexcept{
    auto c = completed_;
    if (service_) add_service_counters(c, service_->counters());
    c.release_panics = release_panics_.load(std::memory_order_relaxed);
    return c;
}
}
