// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include <cstdint>
#include "engine2.h"
// Internal native-only facade; events and statuses use native ABI2 types.
struct AppEngine;
AppEngine* app_engine_create(const wirescape::engine2::Config*);
AppEngine* app_engine_create_config(const wirescape::engine2::Config*,const wirescape::engine2::Config*);
void app_engine_destroy(AppEngine*);
const char* app_engine_error(const AppEngine*);
uint32_t app_engine_abi_version();
uint32_t app_engine_module_count(const AppEngine*);
const ws2_descriptor* app_engine_module(const AppEngine*,uint32_t);
// Borrowed metadata; valid while the internal catalogue owner lives.
const ws2_descriptor *app_engine_native_descriptor(const AppEngine *, const char *module);
// Optional host-only callback, keyed by catalogue descriptor identity; no ABI change.
using AppDataValidator = bool (*)(const ws2_data_slot &, const std::vector<uint8_t> &, std::string &);
AppDataValidator app_engine_data_validator(const AppEngine *, const ws2_descriptor *);
int app_engine_add_node(AppEngine*,uint32_t,const char*);
int app_engine_add_node_config(AppEngine*,uint32_t,const char*,const std::vector<uint8_t>&);
int app_engine_connect(AppEngine*,uint32_t,uint32_t,uint32_t,uint32_t);
int app_engine_prepare(AppEngine*,uint32_t,uint32_t);
// Control thread only; candidate is prepared, live rendering stays on its owner.
int app_engine_replan(AppEngine *live, AppEngine *candidate, uint64_t timeout_ns,
                      wirescape::engine2::Engine::BeforePublish before_publish = nullptr,
                      void *context = nullptr);
// Resolve string parameter IDs on the control side, never in the render callback.
int app_engine_initialize_parameter(AppEngine*,uint32_t,const char*,float);
int app_engine_enqueue(AppEngine*,uint32_t,const ws2_event&,uint64_t frame,uint64_t generation,
                       const char *parameter_id=nullptr);
// Preserve the gate -> envelope/keyboard rule, never oscillator pitch.
int app_engine_enqueue_gate(AppEngine*,uint32_t,float,uint64_t frame,uint64_t generation,uint32_t source_id=0);
int app_engine_render(AppEngine*,float*,uint32_t);
int app_engine_render_channels(AppEngine*,float*const*,uint32_t,uint32_t);
// Live audio callbacks: publish the callback's steady-clock time as the D13 anchor so
// Timestamped ingress (MIDI SystemMonotonic, service chokes) maps onto the timeline.
uint64_t app_engine_clock_ns();
int app_engine_render_live(AppEngine *, float *const *, uint32_t, uint32_t, uint64_t callback_time_ns);
// Internal D5 mute-gap controls; only the callback owns the current gain.
void app_engine_begin_master_fade_out(AppEngine *) noexcept;
// First fade-out render callback in steady-clock ns; 0 until a callback observes it.
uint64_t app_engine_master_fade_out_started_ns(const AppEngine *) noexcept;
// Test/diagnostic-only off-RT accessor for the clock-origin overlap contract.
uint64_t app_engine_master_fade_out_requested_ns(const AppEngine *) noexcept;
bool app_engine_master_fade_silent(const AppEngine *) noexcept;
void app_engine_prepare_master_fade_in(AppEngine *) noexcept; // only on a quiescent engine
void app_engine_resume_master_fade(AppEngine *) noexcept;
bool app_engine_master_fade_in_started(const AppEngine *) noexcept;
int app_engine_reset(AppEngine*);
int app_engine_activate(AppEngine*);
int app_engine_deactivate(AppEngine*);
int app_engine_panic(AppEngine*);
uint64_t app_engine_generation(const AppEngine*);
wirescape::engine2::Meter app_engine_get_meter(const AppEngine*);
/** Last rendered block's peak on one bus channel (0 for channels >= 16 or before rendering). */
float app_engine_channel_peak(const AppEngine*,uint32_t channel);
int app_engine_build_essentials(AppEngine*,const char*);
wirescape::engine2::Engine& app_engine_native(AppEngine*);

const char* app_engine_parameter_id(const AppEngine*,const char*module,uint32_t index);
