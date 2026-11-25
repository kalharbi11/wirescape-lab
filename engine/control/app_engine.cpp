// SPDX-License-Identifier: GPL-3.0-only
#include <array>
#include "app_engine.h"
#include "module_catalog.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <deque>
#include <functional>
#include <map>
#include <string>
#include <vector>
struct AppEngine {
 struct Entry { const ws2_descriptor* native=nullptr; std::map<std::string,uint32_t,std::less<>> by_id; };
 std::deque<Entry> entries;std::map<uint32_t,const Entry*> nodes;
 // Destroy the scheduler before the metadata and libraries its nodes borrow.
 wirescape::engine2::Engine engine;
 std::atomic<float> peak{0};std::atomic<uint64_t> blocks{0};
 // Per bus-channel block peaks for Output meters (stereo patches use one Output per side).
 static constexpr uint32_t meter_channels = 16;
 std::array<std::atomic<float>, meter_channels> channel_peaks{};
 // Single atomic command/ack; the render callback exclusively owns master_gain.
 // 0 unity, 1 fade-out, 2 full silent block completed, 3 fade-in requested, 4 begun.
 std::atomic<uint32_t> master_fade{0};
 // Steady-clock timestamp of first fade-out render callback; 0 until observed.
 std::atomic<uint64_t> master_fade_out_started_ns{0};
 // Control-owned request time; published before the callback may observe phase 1.
 std::atomic<uint64_t> master_fade_out_requested_ns{0};
 float master_gain = 1.0f, master_step = 1.0f;
 std::string error;
 explicit AppEngine(const wirescape::engine2::Config& c,const wirescape::engine2::Config* override=nullptr):engine(override?*override:c){
     // A linear 1.0 -> 0.0 edge completes in no more than 10 ms of samples.
     master_step = 1.0f / float(std::max(1.0, std::floor(c.sample_rate * 0.01)));
     engine.register_producer();
     engine.register_producer(); // producer 0 host keys, 1 MIDI service
     engine.register_producer(); // producer 2 OSC worker; idle without osc.in
     for (auto *d : wirescape::app::builtin_modules()) {
         entries.emplace_back();
         entries.back().native = d;
         for (uint32_t i=0; i<d->param_count; ++i) entries.back().by_id.emplace(d->params[i].id,i);
     }
 }
 const Entry* find(const char* id)const{for(auto& e:entries)if(std::strcmp(e.native->id,id)==0)return &e;return nullptr;}
};
AppEngine* app_engine_create(const wirescape::engine2::Config*c){
 if(!c)return nullptr;
 try{return new AppEngine(*c);}catch(...){return nullptr;}
}
AppEngine* app_engine_create_config(const wirescape::engine2::Config*c,const wirescape::engine2::Config*n){
 if(!c)return nullptr;
 try{return new AppEngine(*c,n);}catch(...){return nullptr;}
}
void app_engine_destroy(AppEngine*e){delete e;}
uint32_t app_engine_abi_version(){return 2;}
const char* app_engine_error(const AppEngine*e){return e->error.empty()?e->engine.error().c_str():e->error.c_str();}
wirescape::engine2::Engine& app_engine_native(AppEngine*e){return e->engine;}
uint32_t app_engine_module_count(const AppEngine*e){return static_cast<uint32_t>(e->entries.size());}
const ws2_descriptor* app_engine_module(const AppEngine*e,uint32_t i){return i<e->entries.size()?e->entries[i].native:nullptr;}
const ws2_descriptor *app_engine_native_descriptor(const AppEngine *e, const char *module) {
    if (!e || !module) return nullptr;
    const auto *entry = e->find(module);
    return entry ? entry->native : nullptr;
}
AppDataValidator app_engine_data_validator(const AppEngine *e, const ws2_descriptor *d) {
    if (!e || !d) return nullptr;
    for (const auto &entry : e->entries)
        if (entry.native == d) return wirescape::app::builtin_data_validator(d);
    return nullptr;
}
int app_engine_add_node(AppEngine*e,uint32_t id,const char*type){return app_engine_add_node_config(e,id,type,{});}
int app_engine_add_node_config(AppEngine*e,uint32_t id,const char*type,const std::vector<uint8_t>&config){auto*d=e->find(type);if(!d)return WS2_UNSUPPORTED;bool ok=d->native&&e->engine.add_node(id,d->native,config);if(ok)e->nodes[id]=d;return ok?WS2_OK:WS2_STATE;}
int app_engine_connect(AppEngine*e,uint32_t a,uint32_t ap,uint32_t b,uint32_t bp){return e->engine.connect(a,ap,b,bp)?WS2_OK:WS2_STATE;}
int app_engine_prepare(AppEngine*e,uint32_t n,uint32_t p){return e->engine.output(n,p,0)&&e->engine.prepare()?WS2_OK:WS2_STATE;}
int app_engine_replan(AppEngine *live, AppEngine *candidate, uint64_t timeout_ns) {
    if (!live || !candidate || live == candidate) return WS2_INVALID;
    try {
        std::map<uint32_t, const AppEngine::Entry *> nodes;
        for (auto &item : candidate->nodes) {
            const auto *entry = live->find(item.second->native->id);
            if (!entry || entry->native != item.second->native) {
                live->error = "Module catalogue differs from live graph";
                return WS2_STATE;
            }
            nodes.emplace(item.first, entry);
        }
        if (!live->engine.replan(candidate->engine, timeout_ns)) {
            live->error = live->engine.error();
            return live->error == "Replacement busy: predecessor still fading" ? WS2_CAPACITY : WS2_STATE;
        }
        live->nodes.swap(nodes);
        live->error.clear();
        return WS2_OK;
    } catch (const std::exception &e) {
        live->error = e.what();
        return WS2_STATE;
    }
}
int app_engine_initialize_parameter(AppEngine*e,uint32_t node,const char*id,float value) {
 if(!e||!id)return WS2_INVALID;
 const auto it=e->nodes.find(node);
 if(it==e->nodes.end())return WS2_UNSUPPORTED;
 const auto slot=it->second->by_id.find(id);
 if(slot==it->second->by_id.end())return WS2_INVALID;
 return e->engine.set_parameter(node,slot->second,value)?WS2_OK:WS2_INVALID;
}
int app_engine_enqueue(AppEngine*e,uint32_t node,const ws2_event&event,uint64_t frame,
                       uint64_t generation,const char*parameter_id) {
 if(!e)return WS2_INVALID;
 if(event.type!=WS2_NOTE_ON&&event.type!=WS2_NOTE_OFF&&event.type!=WS2_PARAM)return WS2_INVALID;
 ws2_event native{};
 native.struct_size=sizeof(native);
 native.source_id=event.source_id;
 native.note_id=event.note_id;
 native.channel=0;
 native.key=static_cast<int32_t>(event.value);
 native.value=1;
 if(event.type==WS2_PARAM) {
  if(!parameter_id)return WS2_INVALID;
  const auto node_it=e->nodes.find(node);
  if(node_it==e->nodes.end())return WS2_UNSUPPORTED;
  const auto slot=node_it->second->by_id.find(parameter_id);
  if(slot==node_it->second->by_id.end())return WS2_INVALID;
  native.type=WS2_PARAM; native.index=slot->second; native.value=event.value;
 } else native.type=event.type;
 const int result=e->engine.enqueue(0,node,WS2_DIRECT_PORT,native,frame,
                                    wirescape::engine2::Timing::Frames,generation);
 return result==WS2_OK?WS2_OK:result==WS2_CAPACITY?WS2_CAPACITY:WS2_INVALID;
}
static bool routes_gate_to_envelope(const ws2_descriptor *native) {
 return native && (!std::strcmp(native->id,"essentials.adsr") ||
                   !std::strcmp(native->id,"host.keyboard"));
}
int app_engine_enqueue_gate(AppEngine*e,uint32_t node,float value,uint64_t frame,
                            uint64_t generation,uint32_t source_id) {
 if(!e)return WS2_INVALID;
 const auto it=e->nodes.find(node);
 if(it==e->nodes.end())return WS2_UNSUPPORTED;
 if(!routes_gate_to_envelope(it->second->native))return WS2_OK;
 ws2_event native{};
 native.struct_size=sizeof(native);native.type=value>0?WS2_NOTE_ON:WS2_NOTE_OFF;
 native.source_id=source_id;native.note_id=0;native.channel=0;native.key=60;native.value=1;
 const int result=e->engine.enqueue(0,node,WS2_DIRECT_PORT,native,frame,
                                    wirescape::engine2::Timing::Frames,generation);
 return result==WS2_OK?WS2_OK:result==WS2_CAPACITY?WS2_CAPACITY:WS2_INVALID;
}
int app_engine_render_live(AppEngine *e, float *const *out, uint32_t channels, uint32_t n, uint64_t callback_time_ns) {
    int r = e->engine.render(out, channels, n, callback_time_ns);
    if (r != WS2_OK) return WS2_CAPACITY;
    float p = 0;
    const auto fade = e->master_fade.load(std::memory_order_acquire);
    if (fade == 1 && callback_time_ns != 0 && callback_time_ns != UINT64_MAX) {
        // The request precedes phase 1 (release/acquire), and gain changes after this load.
        // max(entry, request) is a lower bound on actual fade start, so its gap
        // measurement is conservative even when the request overlaps engine.render.
        const auto requested_ns = e->master_fade_out_requested_ns.load(std::memory_order_acquire);
        const auto first_fade_ns = std::max(callback_time_ns, requested_ns);
        uint64_t unset = 0;
        e->master_fade_out_started_ns.compare_exchange_strong(unset, first_fade_ns, std::memory_order_release,
                                                              std::memory_order_relaxed);
    }
    if (fade == 0) {
        // Unmodified unity path preserves the existing offline/sample results.
        for (uint32_t c = 0; c < channels; ++c) {
            float channel = 0;
            for (uint32_t i = 0; i < n; ++i) channel = std::max(channel, std::abs(out[c][i]));
            if (c < AppEngine::meter_channels) e->channel_peaks[c].store(channel, std::memory_order_relaxed);
            p = std::max(p, channel);
        }
    } else {
        const float initial_gain = e->master_gain;
        float gain = initial_gain;
        const float delta = fade == 1 ? -e->master_step : (fade == 3 || fade == 4 ? e->master_step : 0.0f);
        for (uint32_t i = 0; i < n; ++i) {
            gain = std::clamp(gain + delta, 0.0f, 1.0f);
            for (uint32_t c = 0; c < channels; ++c) {
                out[c][i] *= gain;
                p = std::max(p, std::abs(out[c][i]));
            }
        }
        e->master_gain = gain;
        for (uint32_t c = 0; c < channels && c < AppEngine::meter_channels; ++c) {
            float channel = 0;
            for (uint32_t i = 0; i < n; ++i) channel = std::max(channel, std::abs(out[c][i]));
            e->channel_peaks[c].store(channel, std::memory_order_relaxed);
        }
        uint32_t expected = fade;
        if (fade == 1 && initial_gain == 0.0f) {
            // At least one *entire* rendered block was hard zero.
            e->master_fade.compare_exchange_strong(expected, 2, std::memory_order_release);
        } else if ((fade == 3 || fade == 4) && gain >= 1.0f) {
            e->master_fade.compare_exchange_strong(expected, 0, std::memory_order_release);
        } else if (fade == 3) {
            e->master_fade.compare_exchange_strong(expected, 4, std::memory_order_release);
        }
    }
    e->peak.store(p);
    e->blocks.fetch_add(1);
    return WS2_OK;
}
void app_engine_begin_master_fade_out(AppEngine *e) noexcept {
    e->master_fade_out_started_ns.store(0, std::memory_order_relaxed);
    e->master_fade_out_requested_ns.store(app_engine_clock_ns(), std::memory_order_relaxed);
    e->master_fade.store(1, std::memory_order_release);
}
uint64_t app_engine_master_fade_out_started_ns(const AppEngine *e) noexcept {
    return e->master_fade_out_started_ns.load(std::memory_order_acquire);
}
uint64_t app_engine_master_fade_out_requested_ns(const AppEngine *e) noexcept {
    return e->master_fade_out_requested_ns.load(std::memory_order_acquire);
}
bool app_engine_master_fade_silent(const AppEngine *e) noexcept {
    return e->master_fade.load(std::memory_order_acquire) == 2;
}
void app_engine_prepare_master_fade_in(AppEngine *e) noexcept {
    // The candidate must not be rendered until after this setup.
    e->master_gain = 0.0f;
    e->master_fade.store(3, std::memory_order_release);
}
void app_engine_resume_master_fade(AppEngine *e) noexcept {
    // Cancel an interrupted fade without writing the callback-owned gain.
    e->master_fade.store(3, std::memory_order_release);
}
bool app_engine_master_fade_in_started(const AppEngine *e) noexcept {
    const auto phase = e->master_fade.load(std::memory_order_acquire);
    return phase == 4 || phase == 0;
}
uint64_t app_engine_clock_ns() {
    return uint64_t(
        std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch())
            .count());
}
int app_engine_render_channels(AppEngine *e, float *const *out, uint32_t channels, uint32_t n) {
    return app_engine_render_live(e, out, channels, n, UINT64_MAX);
}
int app_engine_render(AppEngine*e,float*out,uint32_t n){float* rows[]={out};return app_engine_render_channels(e,rows,1,n);}
int app_engine_reset(AppEngine*e){e->engine.reset();e->peak.store(0);for(auto&c:e->channel_peaks)c.store(0);e->blocks.store(0);return WS2_OK;}
float app_engine_channel_peak(const AppEngine*e,uint32_t channel){return e&&channel<AppEngine::meter_channels?e->channel_peaks[channel].load(std::memory_order_relaxed):0.f;}
int app_engine_activate(AppEngine*){return WS2_OK;}
int app_engine_deactivate(AppEngine*){return WS2_OK;}
int app_engine_panic(AppEngine*e){e->engine.panic();return WS2_OK;}
uint64_t app_engine_generation(const AppEngine*e){return e->engine.meter().generation;}
wirescape::engine2::Meter app_engine_get_meter(const AppEngine*e){return e->engine.meter();}
int app_engine_build_essentials(AppEngine*e,const char*){return app_engine_add_node(e,1,"essentials.vco")||app_engine_add_node(e,2,"essentials.adsr")||app_engine_add_node(e,3,"essentials.vca")||app_engine_add_node(e,4,"essentials.output")||app_engine_connect(e,1,0,3,0)||app_engine_connect(e,2,0,3,1)||app_engine_connect(e,3,0,4,0)||app_engine_prepare(e,4,0)?WS2_STATE:WS2_OK;}

const char* app_engine_parameter_id(const AppEngine*e,const char*type,uint32_t index){for(auto*d:wirescape::app::builtin_modules())if(!std::strcmp(d->id,type))return index<d->param_count?d->params[index].id:"";auto*d=e->find(type);return d&&index<d->native->param_count?d->native->params[index].id:"";}
