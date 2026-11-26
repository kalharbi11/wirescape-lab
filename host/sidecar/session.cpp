// SPDX-License-Identifier: GPL-3.0-only
#include "session.h"
#include "../document/runtime_module_config.h"
#include "../../engine/data_pack.h"
#include "d5_gap_deadline.h"
#include "null_sink_wait.h"
#include "runtime_patch.h"
#include "runtime_patch_normalize.h"
#include "wirescape_sidecar_categories.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>

// The multimedia timer declarations require Windows' base types first.
#include <timeapi.h>
#if defined(_MSC_VER)
#pragma comment(lib, "winmm.lib")
#endif
#endif
#if defined(__has_feature)
#if __has_feature(address_sanitizer) || __has_feature(thread_sanitizer)
#define WIRESCAPE_SIDECAR_SANITIZED 1
#endif
#endif
#if defined(__SANITIZE_ADDRESS__) || defined(__SANITIZE_THREAD__)
#define WIRESCAPE_SIDECAR_SANITIZED 1
#endif
namespace wirescape::sidecar {
namespace {
// Every bus channel an output route may name (routes validate bus_channel 0..15).
constexpr uint32_t kCaptureChannels = 16;
// D5 budgets: 100 ms mute, 150 ms gap (stretched only when one block period is longer).
// Sanitizer builds run several times slower, so they get a liveness allowance instead;
// release builds (Linux, Pi, Windows) keep the D5 budget as a hard refusal.
#ifdef WIRESCAPE_SIDECAR_SANITIZED
constexpr std::chrono::milliseconds kMuteBudget{1000}, kGapBudget{1000};
#else
constexpr std::chrono::milliseconds kMuteBudget{100}, kGapBudget{150};
#endif
#ifdef _WIN32
// Set up before the first render, release only after the sink stops. Loading
// avrt dynamically keeps MMCSS optional on Windows installations without it.
class SinkScheduling {
    using Register = HANDLE(WINAPI *)(LPCWSTR, LPDWORD);
    using Revert = BOOL(WINAPI *)(HANDLE);
    HMODULE avrt_ = LoadLibraryW(L"avrt.dll");
    HANDLE task_ = nullptr;
    Revert revert_ = nullptr;
    bool timer_ = timeBeginPeriod(1) == TIMERR_NOERROR;
    int previous_priority_ = GetThreadPriority(GetCurrentThread());
    bool fallback_ = false;
    HANDLE waitable_ = nullptr;

  public:
    SinkScheduling() noexcept {
        // The 5.33 ms / 48 kHz block period is shorter than Windows' typical
        // condition-variable wake granularity. Request the high-resolution
        // kernel timer, falling back to the ordinary waitable timer on older OSes.
        constexpr DWORD kHighResolution = 0x00000002; // Windows 10 1803+
        waitable_ = CreateWaitableTimerExW(nullptr, nullptr, kHighResolution, TIMER_ALL_ACCESS);
        if (!waitable_) waitable_ = CreateWaitableTimerW(nullptr, FALSE, nullptr);
        if (avrt_) {
            const auto register_task =
                reinterpret_cast<Register>(GetProcAddress(avrt_, "AvSetMmThreadCharacteristicsW"));
            revert_ = reinterpret_cast<Revert>(GetProcAddress(avrt_, "AvRevertMmThreadCharacteristics"));
            DWORD index = 0;
            if (register_task && revert_) task_ = register_task(L"Pro Audio", &index);
        }
        if (!task_) fallback_ = SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL) != 0;
    }
    ~SinkScheduling() {
        if (waitable_) CloseHandle(waitable_);
        if (task_) revert_(task_);
        if (fallback_ && previous_priority_ != THREAD_PRIORITY_ERROR_RETURN)
            SetThreadPriority(GetCurrentThread(), previous_priority_);
        if (timer_) timeEndPeriod(1);
        if (avrt_) FreeLibrary(avrt_);
    }
    SinkScheduling(const SinkScheduling &) = delete;
    SinkScheduling &operator=(const SinkScheduling &) = delete;

    void wait_until(std::chrono::steady_clock::time_point deadline, HANDLE stop_event, std::mutex &mutex,
                    std::condition_variable &wake, const std::atomic<bool> &stop) {
        if (waitable_ && stop_event) {
            const auto result = sink_wait_until(
                deadline, [] { return std::chrono::steady_clock::now(); },
                [&](int64_t due) {
                    LARGE_INTEGER relative{};
                    relative.QuadPart = due;
                    if (!SetWaitableTimer(waitable_, &relative, 0, nullptr, nullptr, FALSE))
                        return SinkWaitResult::unavailable;
                    const HANDLE handles[] = {stop_event, waitable_};
                    const DWORD signal = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
                    if (signal == WAIT_OBJECT_0) return SinkWaitResult::stopped;
                    if (signal == WAIT_OBJECT_0 + 1) return SinkWaitResult::deadline;
                    return SinkWaitResult::unavailable;
                });
            if (result != SinkWaitResult::unavailable) return;
        }
        // Resource/API failure: preserve the original interruptible CV path.
        std::unique_lock<std::mutex> lock(mutex);
        wake.wait_until(lock, deadline, [&] { return stop.load(); });
    }
};
#endif
struct Refusal : std::runtime_error {
    std::string code, defer_id;
    Refusal(std::string c, const char *m, std::string deferred = {})
        : std::runtime_error(m), code(std::move(c)), defer_id(std::move(deferred)) {}
};
void need(bool condition, const char *code = "invalid", const char *message = "Invalid command") {
    if (!condition) throw Refusal(code, message);
}
uint32_t integer(const Json &v, uint32_t low = 1, uint32_t high = UINT32_MAX) {
    need(v.is_number_integer());
    auto n = v.get<int64_t>();
    need(n >= low && uint64_t(n) <= high);
    return uint32_t(n);
}
double number(const Json &v, double low, double high) {
    need(v.is_number());
    double n = v.get<double>();
    need(std::isfinite(n) && n >= low && n <= high);
    return n;
}
Json identity(const Json &c) {
    return {{"kind", c.at("kind")},
            {"from", {{"module", c.at("from").at("module")}, {"port", c.at("from").at("port")}}},
            {"to", {{"module", c.at("to").at("module")}, {"port", c.at("to").at("port")}}}};
}
Json &node(Json &patch, uint32_t id) {
    for (auto &m : patch.at("modules"))
        if (m.at("id") == id) return m;
    throw Refusal("not-found", "No such module");
}
const ws2_param *parameter(const ws2_descriptor *d, const std::string &id) {
    for (uint32_t i = 0; i < d->param_count; ++i)
        if (id == d->params[i].id) return &d->params[i];
    throw Refusal("not-found", "No such parameter");
}
const ws2_port *port(const ws2_descriptor *d, const std::string &id, bool output) {
    auto *p = output ? d->outputs : d->inputs;
    auto n = output ? d->output_count : d->input_count;
    for (uint32_t i = 0; i < n; ++i)
        if (id == p[i].id) return &p[i];
    throw Refusal("not-found", "No such port");
}
Json catalogue(AppEngine *engine) {
    auto result = Json::array();
    const char *hints[] = {"any",  "audio",   "pitch",    "cv_bi",   "cv_uni",
                           "gate", "trigger", "ev_notes", "ev_midi", "ev_message"};
    for (uint32_t i = 0; i < app_engine_module_count(engine); ++i) {
        const auto *d = app_engine_module(engine, i);
        if (!d) continue;
        Json ports = Json::array(), params = Json::array();
        for (bool output : {false, true}) {
            auto *p = output ? d->outputs : d->inputs;
            auto n = output ? d->output_count : d->input_count;
            for (uint32_t j = 0; j < n; ++j)
                ports.push_back({{"id", p[j].id},
                                 {"name", p[j].name},
                                 {"direction", output ? "output" : "input"},
                                 {"kind", p[j].kind == WS2_EVENT ? "event" : "signal"},
                                 {"hint", hints[std::min(p[j].hint, 9u)]},
                                 {"poly", p[j].poly == WS2_SUM     ? "sum"
                                          : p[j].poly == WS2_FIRST ? "first"
                                                                   : "poly"},
                                 {"stereo_pair", p[j].stereo_pair ? Json(p[j].stereo_pair) : Json(nullptr)}});
        }
        for (uint32_t j = 0; j < d->param_count; ++j) {
            auto &p = d->params[j];
            Json value = {{"id", p.id},
                          {"name", p.name},
                          {"minimum", p.minimum},
                          {"maximum", p.maximum},
                          {"default", p.initial},
                          {"unit", p.unit ? p.unit : ""},
                          {"taper", p.taper == WS2_LOG   ? "log"
                                    : p.taper == WS2_EXP ? "exp"
                                                         : "linear"},
                          {"step", p.step},
                          {"decimals", p.decimals},
                          {"modulatable", bool(p.flags & WS2_MODULATABLE)}};
            if (p.option_count) {
                value["choices"] = Json::array();
                for (uint32_t k = 0; k < p.option_count; ++k) value["choices"].push_back(p.options[k]);
            }
            params.push_back(value);
        }
        result.push_back(
            {{"id", d->id}, {"name", d->name}, {"category", wirescape_sidecar_category(d->id)}, {"ports", ports}, {"parameters", params}});
    }
    return {{"modules", result}};
}
} // namespace
Options parse_options(int argc, char **argv) {
    Options o;
    o.directory = std::filesystem::absolute(argv[0]).parent_path().string();
    bool cli_rate = false, cli_block = false, cli_settings = false;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--confirm-audio") o.audio = true;
        else if (arg == "--confirm-midi") o.midi = true;
        else if (arg == "--confirm-lan") o.lan = true;
        else if (arg == "--null-audio") o.null_audio = true;
        else if (arg == "--scripted-midi") o.scripted_midi = true;
        else if (arg == "--bench-summary") o.bench_summary = true;
        else if (arg == "--capture-null-sink") {
            need(++i < argc);
            o.capture_null_sink = argv[i];
            need(!o.capture_null_sink.empty());
        } else if (arg == "--device" || arg == "--settings" || arg == "--rate" || arg == "--block") {
            need(++i < argc);
            std::string v = argv[i];
            need(!v.empty());
            if (arg == "--device") o.device = v;
            else if (arg == "--settings") { o.settings = v; cli_settings = true; }
            else {
                need(v.find_first_not_of("0123456789") == std::string::npos);
                auto n = std::stoull(v);
                need(n > 0 && n <= (arg == "--block" ? 4096 : UINT32_MAX));
                if (arg == "--block") {
                    o.block = uint32_t(n);
                    cli_block = true;
                } else {
                    o.rate = uint32_t(n);
                    cli_rate = true;
                }
            }
        } else throw Refusal("invalid", "Unknown startup flag");
    }
    // Explicit CLI rate/block always win for this invocation; persisted choices
    // apply only when their corresponding command-line option is absent.
    if (!cli_rate || !cli_block) {
        try {
            std::ifstream in(o.settings, std::ios::binary);
            if (in) {
                std::string bytes(LineLimit + 1, '\0');
                in.read(bytes.data(), std::streamsize(bytes.size()));
                bytes.resize(size_t(in.gcount()));
                const auto settings = strict_json(bytes);
                if (settings.contains("audio") && settings["audio"].is_object()) {
                    const auto &audio = settings["audio"];
                    if (!cli_rate && audio.contains("sampleRate") && audio["sampleRate"].is_number_integer()) {
                        const auto value = audio["sampleRate"].get<int64_t>();
                        if (value == 44100 || value == 48000 || value == 96000) o.rate = uint32_t(value);
                    }
                    if (!cli_block && audio.contains("bufferFrames") && audio["bufferFrames"].is_number_integer()) {
                        const auto value = audio["bufferFrames"].get<int64_t>();
                        if (value == 64 || value == 128 || value == 256 || value == 512 || value == 1024)
                            o.block = uint32_t(value);
                    }
                }
            }
        } catch (...) {
            std::cerr << "Invalid audio preferences; retaining startup settings\n";
        }
    }
    need(!o.bench_summary || o.null_audio, "invalid", "--bench-summary requires --null-audio");
    need(!o.scripted_midi || (o.null_audio && cli_settings), "invalid",
         "--scripted-midi requires --null-audio and an explicit --settings path");
    need(o.capture_null_sink.empty() || o.null_audio, "invalid", "--capture-null-sink requires --null-audio");
    if (o.null_audio) o.audio = o.midi = false;
    return o;
}
Session::Session(Options options)
    : options_(std::move(options)),
      config_([](const Options &options) {
          engine2::Config native{};
          native.sample_rate = double(options.rate);
          native.max_block = options.block;
          native.max_nodes = 64;
          native.event_budget = 2048;
          return native;
      }(options_)),
      catalogue_(app_engine_create(&config_), app_engine_destroy), engine_(nullptr, app_engine_destroy) {
    need(bool(catalogue_), "unavailable", "Cannot create catalogue");
    std::random_device random;
    token_ = std::to_string(random()) + "-" + std::to_string(app_engine_clock_ns());
    try {
        std::ifstream in(options_.settings, std::ios::binary);
        if (in) {
            std::string bytes(LineLimit + 1, '\0');
            in.read(bytes.data(), std::streamsize(bytes.size()));
            bytes.resize(size_t(in.gcount()));
            preferences_ = strict_json(bytes);
        }
    } catch (...) {
        preferences_ = Json::object();
    }
    std::unique_ptr<midi::Backend> scripted_source;
    if (options_.scripted_midi) {
        auto scripted = std::make_unique<midi::ScriptedBackend>();
        scripted_midi_ = scripted.get();
        scripted_source = std::move(scripted);
    }
    auto observed = std::make_unique<ObservedMidi>(options_.null_audio && !options_.scripted_midi,
                                                    options_.midi, std::move(scripted_source),
                                                    options_.scripted_midi);
    observer_ = observed.get();
    observer_->endpoints();
    monitor_ = std::make_unique<monitor::Capture>();
    midi_ = std::make_unique<midi::Host>(options_.midi || options_.null_audio, std::move(observed));
    midi_->observe(monitor_.get());
    // The device-off null sink must not bind LAN, even when its stub launcher
    // exercises --confirm-lan forwarding. Real consent still needs both flags.
    osc_ = std::make_unique<osc::Host>(options_.lan && !options_.null_audio);
    osc_->observe(monitor_.get());
    if ((options_.midi || options_.null_audio) && preferences_.contains("devices")) midi_->restore(preferences_.dump());
    // The synthetic endpoint has its own identity and is selected only on an
    // explicit null-audio invocation. Never consult the physical MIDI observer.
    if (scripted_midi_) midi_->select(scripted_midi_->identity(), true);
    patch_ = {{"format", "wirescape.native.patch"},
              {"version", 2},
              {"modules", Json::array({{{"id", 1}, {"module", "essentials.output"}}})},
              {"connections", Json::array()}};
    patch_ = execution(patch_);
    monitor_->configure(patch_);
    osc_out_ = std::make_unique<osc::OutHost>(patch_.dump());
    document::ScopedOutBuses staged_out(osc_out_->buses());
    std::string error;
    engine_.reset(document::load_runtime_patch(patch_.dump(), catalogue_.get(), config_, error));
    need(bool(engine_), "unavailable", "Cannot create startup graph");
    active_ = engine_.get();
    refresh_devices();
    device_ = options_.device.empty() ? preferences_.value("audioDeviceId", std::string{}) : options_.device;
    if (options_.audio) audio_state_ = "starting";
    if (!options_.capture_null_sink.empty()) {
        need(capture_.open(options_.capture_null_sink), "unavailable", "Cannot open --capture-null-sink file");
        need(marks_.open(options_.capture_null_sink + ".marks"), "unavailable", "Cannot open capture marks file");
    }
}
void Session::start(std::chrono::steady_clock::time_point now) {
    try {
        start_audio(now);
        start_midi();
        start_osc();
        if (scripted_midi_) {
            scripted_started_ = std::chrono::steady_clock::now();
            need(scripted_midi_->set_origin_ns(app_engine_clock_ns()), "invalid",
                 "Scripted MIDI source started before its origin was set");
            scripted_started_enabled_ = true;
        }
        if (stream_) persist();
    } catch (...) {
        osc_out_->stop();
        osc_->stop();
        midi_->stop();
        stop_audio();
        throw;
    }
}
Session::~Session() {
    try {
        shutdown();
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
    }
}
void Session::shutdown() {
    osc_out_->stop();
    osc_->stop(); // stop/join packet acquisition before audio or engine teardown
    midi_->stop();
    stop_audio();
    if (capture_.enabled() && !capture_reported_) {
        capture_reported_ = true;
        capture_.close(); // the sink thread has joined
        marks_.close();
        std::cerr << "capture segments=" << capture_.segments() << " blocks=" << capture_.blocks()
                  << " failed=" << (capture_.failed() || marks_.failed() ? 1 : 0) << '\n';
    }
    if (options_.bench_summary && !bench_reported_) {
        bench_reported_ = true;
        std::cerr << "bench blocks=" << bench_.blocks << " p50=" << bench_.percentile(50)
                  << " p99=" << bench_.percentile(99) << " max=" << bench_.max_percent
                  << " overruns=" << bench_.overruns << " faults=" << bench_.faults
                  << " overrun_render_count=" << bench_.overrun_render_count
                  << " overrun_render_max_us=" << bench_.overrun_render_max_us
                  << " overrun_wake_count=" << bench_.overrun_wake_count
                  << " overrun_wake_max_us=" << bench_.overrun_wake_max_us << '\n';
    }
}
void Session::start_audio(std::chrono::steady_clock::time_point now, StoppedGraph *rollback, Json *fresh) {
    stop_sink_.store(false);
    audio_reason_.clear();
    if (options_.audio) {
        try {
            // Resolve the default only before any identity has been selected.
            // A remembered/missing output must never be replaced by the default.
            if (device_.empty() || device_.find('|') == std::string::npos) {
                const auto list = audio::devices(options_.directory, {false, {}, {}});
                if (!device_.empty()) {
                    // Pre-identity settings stored a bare name. Upgrade a unique name to its id;
                    // a name Windows repeats across host APIs can never open, so use the default.
                    const auto named = std::count_if(list.begin(), list.end(),
                                                     [&](const audio::Device &d) { return d.name == device_; });
                    const int found = audio::resolve_device(list, device_);
                    if (found >= 0) device_ = list[size_t(found)].id;
                    else if (named > 1) device_.clear();
                }
                if (device_.empty())
                    for (const auto &d : list)
                        if (d.is_default) device_ = d.id;
            }
            need(!device_.empty(), "unavailable", "No selected audio output");
            try {
                stream_ = std::make_unique<audio::Stream>(engine_, audio::StreamSelection{options_.directory, device_},
                                                          options_.rate, options_.block, [this] { midi_->stop(); });
            } catch (const audio::PreferredBufferSize &driver) {
                open_at_driver_block(driver.frames(), rollback, fresh); // exactly one retry; throws on refusal
            }
            audio_state_ = "running";
            audio_error_.clear(); // an actual successful reopen clears the last error
            audio_backoff_ = std::chrono::milliseconds(100);
        } catch (const audio::RateUnsupported &) {
            audio_state_ = "no-device";
            audio_reason_ = "rate-unsupported"; // invalid rates are refusals, never retry loops
        } catch (const audio::ShutdownFailure &) {
            throw;
        } catch (const std::exception &e) {
            audio_error_ = audio::bounded_audio_error(e.what());
            audio_state_ = device_.empty() ? "no-device" : "reconnecting";
            audio_retry_ = now + audio_backoff_;
            audio_backoff_ = std::min(audio_backoff_ * 2, std::chrono::milliseconds(5000));
            if (!engine_) throw;
        }
    } else {
        active_ = engine_.get();
#ifdef _WIN32
        // The control thread owns this event until after join; the kernel wait
        // can be interrupted immediately even for the 512 ms long-block case.
        sink_stop_event_ = CreateEventW(nullptr, TRUE, FALSE, nullptr);
#endif
        try {
            // Without capture the sink renders the stereo pair exactly as before. With
            // --capture-null-sink it renders every bus channel a route may name (0..15);
            // rows 0 and 1 are produced identically either way.
            const uint32_t channels = capture_.enabled() ? kCaptureChannels : 2;
            sink_ = std::thread([this, live = active_, channels,
                                 storage = std::vector<float>(size_t(options_.block) * channels),
                                 scratch = std::vector<float>(capture_.enabled() ? size_t(options_.block) * channels : 0),
                                 rows = std::vector<float *>(channels)]() mutable {
                for (uint32_t c = 0; c < channels; ++c) rows[c] = storage.data() + size_t(c) * options_.block;
#ifdef _WIN32
                SinkScheduling scheduling;
#endif
                capture_.begin(options_.rate, channels, options_.block); // no-op without the flag
                auto next = std::chrono::steady_clock::now();
                sink_rendering_.store(true, std::memory_order_release);
                while (!stop_sink_.load()) {
                    live = sink_slot_.adopt(live); // same block-boundary handoff as the PortAudio callback
                    auto before = std::chrono::steady_clock::now();
                    const int render =
                        app_engine_render_live(live, rows.data(), channels, options_.block, app_engine_clock_ns());
                    if (options_.bench_summary) {
                        bench_.observe_faults(app_engine_native(live).meter().faults);
                        if (render != WS2_OK) ++bench_.faults;
                    }
                    if (render != WS2_OK) break;
                    auto after = std::chrono::steady_clock::now();
                    // Null-sink thread only (not Engine::render, not a device callback).
                    capture_.append(rows.data(), channels, options_.block, scratch.data());
                    double percent =
                        std::chrono::duration<double>(after - before).count() * options_.rate / options_.block * 100;
                    cpu_.store(percent);
                    const auto scheduled_start = next;
                    next += std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                        std::chrono::duration<double>(double(options_.block) / options_.rate));
                    if (options_.bench_summary) bench_.record_timing(percent, before, after, scheduled_start, next);
#ifdef _WIN32
                    scheduling.wait_until(next, static_cast<HANDLE>(sink_stop_event_), sink_mutex_, sink_wake_,
                                          stop_sink_);
#else
                    std::unique_lock<std::mutex> lock(sink_mutex_);
                    sink_wake_.wait_until(lock, next, [this] { return stop_sink_.load(); });
#endif
                }
                capture_.end();
                sink_rendering_.store(false, std::memory_order_release);
            });
        } catch (...) {
#ifdef _WIN32
            if (sink_stop_event_) CloseHandle(static_cast<HANDLE>(sink_stop_event_));
            sink_stop_event_ = nullptr;
#endif
            throw;
        }
    }
}
// Control thread, no stream running (the failed open returned engine_). Keel's
// #627 ruling: same quiescent path as setBufferFrames, one open, no persistence.
Session::StoppedGraph Session::prepare_stopped_graph(const engine2::Config &next_config, Json *fresh) {
    // E7: both instances are quiescent. The same committed document supplies
    // IDs, types and configs to both graphs; never replay a stored document
    // snapshot as if it were current runtime state. In particular, an earlier
    // unsupported blob retained by Engine::load_state is not a live snapshot.
    struct Snapshot {
        uint32_t id;
        std::string type;
        const ws2_descriptor *descriptor;
        std::vector<uint8_t> bytes;
    };
    std::vector<Snapshot> snapshots;
    auto runtime = patch_;
    auto &old = app_engine_native(engine_.get());
    for (auto &m : runtime["modules"]) {
        const auto id = m["id"].get<uint32_t>();
        const auto type = m["module"].get<std::string>();
        const auto *d = old.descriptor(id);
        Snapshot snapshot{id, type, d, {}};
        if (d && type == d->id && old.preserved_state(id).empty())
            snapshot.bytes = old.save_state(id);
        snapshots.push_back(std::move(snapshot));
        // The normal patch loader remains strict; only this rebuild copy omits
        // authored state so a rate-dependent live state refusal is nonfatal.
        m.erase("state");
    }
    StoppedGraph next;
    next.telemetry = document::telemetry::Sampler(
        document::telemetry::plan(patch_, catalogue_.get(), /*phase_enabled=*/true, /*groove_enabled=*/true));
    next.out = std::make_unique<osc::OutHost>(patch_.dump());
    document::ScopedOutBuses staged_out(next.out->buses());
    std::string error;
    next.engine.reset(document::load_runtime_patch(runtime.dump(), catalogue_.get(), next_config, error,
                                                  &next.telemetry.taps()));
    if (!next.engine) return next;
    auto &candidate = app_engine_native(next.engine.get());
    for (const auto &snapshot : snapshots) {
        // Current built-in state writers with a successful hook write at least
        // a version word. Engine::save_state returns empty for unsupported/error.
        // Match the actual descriptor as well as the unchanged document config.
        const bool restored = snapshot.descriptor && candidate.descriptor(snapshot.id) == snapshot.descriptor &&
                              !snapshot.bytes.empty() &&
                              candidate.load_state(snapshot.id, snapshot.bytes) == WS2_OK;
        if (!restored && fresh) {
            Json entry = {{"moduleId", snapshot.id}, {"module", snapshot.type}};
            if (std::find(fresh->begin(), fresh->end(), entry) == fresh->end())
                fresh->push_back(std::move(entry));
        }
    }
    app_engine_prepare_master_fade_in(next.engine.get());
    return next;
}

void Session::swap_stopped_graph(StoppedGraph &other) noexcept {
    engine_.swap(other.engine);
    telemetry_.swap(other.telemetry);
    osc_out_.swap(other.out);
    active_ = engine_.get();
}

void Session::open_at_driver_block(int64_t frames, StoppedGraph *rollback, Json *fresh) {
    if (frames < 1 || frames > 4096)
        throw std::runtime_error("ASIO driver requires " + std::to_string(frames) + " frames (supported 1-4096)");
    const auto block = uint32_t(frames);
    // A driver-selected block within the prepared capacity needs no graph change.
    if (block <= config_.max_block) {
        stream_ = std::make_unique<audio::Stream>(
            engine_, audio::StreamSelection{options_.directory, device_}, options_.rate, block,
            [this] { midi_->stop(); }, /*allow_preferred_retry=*/false);
        if (!requested_block_) requested_block_ = options_.block;
        options_.block = block;
        return;
    }
    engine2::Config next_config = config_;
    next_config.max_block = block;
    // Preferred-buffer retries may run after a failed startup or hot-unplug:
    // OSC/MIDI workers can still hold the old graph while stream_ is null.
    const bool had_osc = !osc_->states().empty() || !osc_out_->states().empty();
    osc_out_->stop();
    osc_->stop();
    auto resume_osc = [this, had_osc](void *) noexcept {
        if (!had_osc) return;
        try {
            start_osc();
        } catch (...) {
            osc_out_->stop();
            osc_->stop();
        }
    };
    std::unique_ptr<void, decltype(resume_osc)> osc_restart(this, resume_osc);
    midi_->stop();
    bool restore_midi_on_failure = true;
    auto resume_midi = [this, &restore_midi_on_failure](void *) noexcept {
        if (!restore_midi_on_failure) return;
        try {
            start_midi();
        } catch (...) {
            midi_->stop();
        }
    };
    std::unique_ptr<void, decltype(resume_midi)> midi_restart(this, resume_midi);
    auto previous = prepare_stopped_graph(next_config, fresh);
    if (!previous.engine)
        throw std::runtime_error("Graph cannot prepare at the ASIO driver's " + std::to_string(block) + " frames");
    swap_stopped_graph(previous);
    try {
        stream_ = std::make_unique<audio::Stream>(
            engine_, audio::StreamSelection{options_.directory, device_}, options_.rate, block,
            [this] { midi_->stop(); }, /*allow_preferred_retry=*/false);
    } catch (...) {
        swap_stopped_graph(previous);
        throw;
    }
    restore_midi_on_failure = false; // caller start()/poll_audio()/apply() resumes MIDI
    // A command may still fail after opening the stream (e.g. persistence).
    // Keep its original engine AND buses until the whole command commits.
    if (rollback && !rollback->engine) *rollback = std::move(previous);
    if (!requested_block_) requested_block_ = options_.block;
    config_ = next_config;
    options_.block = block;
}

void Session::stop_audio() {
    stop_sink_.store(true);
#ifdef _WIN32
    if (sink_stop_event_) SetEvent(static_cast<HANDLE>(sink_stop_event_));
#endif
    sink_wake_.notify_all();
    if (sink_.joinable()) sink_.join();
#ifdef _WIN32
    if (sink_stop_event_) CloseHandle(static_cast<HANDLE>(sink_stop_event_));
    sink_stop_event_ = nullptr;
#endif
    sink_rendering_.store(false, std::memory_order_release);
    if (stream_) {
        engine_ = stream_->stop();
        dropouts_.fetch_add(stream_->dropouts()); // include the final callback after stop joins
        stream_.reset();
    }
    cpu_.store(0);
}
void Session::start_midi() {
    std::string error;
    need(midi_->start(active_, patch_.dump(), error), "unavailable", "Cannot start MIDI subscriptions");
}
void Session::start_osc() {
    osc_->start(active_, patch_.dump());
    osc_out_->start(); // control-owned loopback sender; never touches the render thread
}
bool Session::refresh_devices(bool audio, bool probe_rates, const std::string &target) {
    bool enumerated = audio;
    if (audio) try {
            const bool playing = stream_ && stream_->running();
            auto next = audio_devices(options_.directory, options_.null_audio,
                                      {probe_rates, target, playing ? device_ : std::string{}});
            for (auto &entry : next) {
                const auto id = entry.at("id").get<std::string>();
                const bool active = playing && id == device_;
                if (!probe_rates || active || (!target.empty() && target != id)) {
                    const auto old = std::find_if(audio_devices_.begin(), audio_devices_.end(),
                                                  [&](const Json &d) { return d.at("id") == id; });
                    if (old != audio_devices_.end() &&
                        old->value("outputChannels", 2) == entry.value("outputChannels", 2))
                        for (const auto *key : {"sampleRates", "supported", "unsupportedReason"}) {
                            entry.erase(key);
                            if (old->contains(key)) entry[key] = (*old)[key];
                        }
                }
                if (active && entry.value("outputChannels", 2) >= 2) {
                    entry["supported"] = true;
                    entry.erase("unsupportedReason");
                    // A cached known set includes the rate proven by the running stream.
                    // Unknown remains omitted; a singleton would falsely exclude other rates.
                    if (entry.contains("sampleRates") &&
                        std::find(entry["sampleRates"].begin(), entry["sampleRates"].end(), Json(options_.rate)) ==
                            entry["sampleRates"].end())
                        entry["sampleRates"].push_back(options_.rate);
                }
            }
            // Registry discovery is read-only and never initializes an audio driver.
            // The fake-backend test supplies the registry list through this seam.
            std::vector<audio::RawDevice> visible;
            for (const auto &entry : next)
                if (entry.value("hostApi", std::string{}) == "ASIO")
                    visible.push_back({entry.at("name").get<std::string>(), "ASIO"});
            Json unavailable = Json::array();
            for (const auto &name : audio::unavailable_asio_drivers(audio::installed_asio_drivers(), visible))
                unavailable.push_back({{"hostApi", "ASIO"}, {"name", name}, {"reason", "driver-init-failed"}});
            audio_devices_ = std::move(next);
            unavailable_audio_drivers_ = std::move(unavailable);
        } catch (...) {
            enumerated = false; // Keep the last successful list; failure is not disappearance.
        }
    midi_devices_ = midi_devices({observer_->observed(), midi_->enabled()}, options_.midi || options_.null_audio);
    return enumerated;
}
void Session::persist() {
    auto preferences = preferences_;
    preferences["audioDeviceId"] = device_;
    preferences["devices"] = Json::array();
    for (const auto &e : midi_->enabled())
        preferences["devices"].push_back(
            {{"kind", "midi"}, {"name", e.name}, {"system_name", e.system_name}, {"enabled", true}});
    auto path = std::filesystem::path(options_.settings), temp = path;
    temp += ".tmp";
    if (!path.parent_path().empty()) std::filesystem::create_directories(path.parent_path());
    {
        std::ofstream out(temp, std::ios::binary | std::ios::trunc);
        out << preferences.dump();
        out.close();
        need(bool(out), "unavailable", "Cannot save device preferences");
    }
#ifdef _WIN32
    need(
        MoveFileExW(temp.wstring().c_str(), path.wstring().c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH),
        "unavailable", "Cannot save device preferences");
#else
    std::filesystem::rename(temp, path);
#endif
    preferences_ = std::move(preferences);
}
Json Session::execution(Json patch) {
    need(patch.is_object() && patch.at("format") == "wirescape.native.patch" &&
         patch.at("version").is_number_integer() && patch.at("version") == 2);
    need(patch.at("modules").is_array() && patch.at("connections").is_array());
    need(patch["modules"].size() <= 64 && patch["connections"].size() <= 128, "limit", "Graph capacity exceeded");
    if (!patch.contains("settings")) patch["settings"] = Json::object();
    std::set<uint32_t> ids;
    auto descriptor = [&](uint32_t id) {
        auto &m = node(patch, id);
        auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());
        need(d, "unknown-module", "Module not installed");
        return d;
    };
    uint32_t output = UINT32_MAX, osc_routes = 0;
    for (auto &m : patch["modules"]) {
        auto id = integer(m.at("id"));
        need(ids.insert(id).second, "duplicate", "Duplicate module ID");
        auto *d = descriptor(id);
        need(!m.value("inactive", false), "unavailable", "Module is inactive");
        if (std::string(d->id) == "osc.in") need(++osc_routes <= 32, "limit", "At most 32 OSC input routes");
        if (!m.contains("version")) m["version"] = d->version;
        if (std::string(d->id) == "essentials.output") output = std::min(output, id);
        auto values = m.value("parameters", Json::object());
        need(values.is_object());
        for (auto it = values.begin(); it != values.end(); ++it) {
            auto *p = parameter(d, it.key());
            need(it.value().is_number());
            double value = it.value().get<double>();
            need(std::isfinite(value) && value >= p->minimum && value <= p->maximum, "refused",
                 "Parameter outside range");
        }
    }
    std::set<std::string> edges;
    for (const auto &c : patch["connections"]) {
        need(c.is_object());
        auto from = integer(c.at("from").at("module")), to = integer(c.at("to").at("module"));
        auto *fd = descriptor(from);
        auto *td = descriptor(to);
        auto *f = port(fd, c.at("from").at("port").get<std::string>(), true);
        auto kind = c.at("kind").get<std::string>();
        need(edges.insert(identity(c).dump()).second, "duplicate", "Duplicate connection");
        if (kind == "modulation") {
            auto *p = parameter(td, c.at("to").at("port").get<std::string>());
            need(f->kind == WS2_SIGNAL, "kind-mismatch", "Modulation requires a signal source");
            need(p->flags & WS2_MODULATABLE, "refused", "Parameter cannot be modulated");
            number(c.at("amount"), -1, 1);
        } else {
            need(kind == "event" || kind == "signal");
            auto *t = port(td, c.at("to").at("port").get<std::string>(), false);
            auto expected = kind == "event" ? WS2_EVENT : WS2_SIGNAL;
            need(f->kind == expected && t->kind == expected, "kind-mismatch", "Cable requires matching port kinds");
        }
    }
    if (!patch.contains("outputs")) {
        need(output != UINT32_MAX, "refused", "Patch needs an Output module");
        patch["outputs"] = Json::array({{{"module", output}, {"port", "audio"}, {"bus_channel", 0}},
                                        {{"module", output}, {"port", "audio"}, {"bus_channel", 1}}});
    }
    need(patch["outputs"].is_array() && !patch["outputs"].empty(), "refused", "Invalid output routes");
    for (const auto &o : patch["outputs"]) {
        auto *d = descriptor(integer(o.at("module")));
        auto *p = port(d, o.at("port").get<std::string>(), true);
        need(p->kind == WS2_SIGNAL, "kind-mismatch", "Output requires a signal port");
        integer(o.at("bus_channel"), 0, 15);
    }
    need(patch.dump().size() <= LineLimit, "limit", "Patch exceeds byte limit");
    return patch;
}
Json Session::config_event(uint32_t id, const PendingConfig &pending,
                           const char *outcome, uint64_t generation) const {
    return deferred_config_event(token_, id, pending, outcome, generation);
}
Json Session::take_config_events() {
    Json events = Json::array();
    events.swap(config_events_);
    return events;
}
bool Session::commit(Json patch, bool new_namespace, std::optional<uint32_t> retry_id, bool explicit_graph) {
    patch = execution(std::move(patch));
    // A80: an opted-in full snapshot can carry still-pending authored
    // configs alongside unrelated edits. Execute those nodes at their
    // committed config until their correlated deferral completes.
    std::set<uint32_t> snapshot_supersedes;
    if (explicit_graph) {
        for (auto &m : patch["modules"]) {
            const auto id = integer(m.at("id"));
            const auto pending = pending_configs_.find(id);
            if (pending == pending_configs_.end()) continue;
            if (m.at("module") != pending->second.module ||
                m.value("config", Json::object()) != pending->second.config) {
                snapshot_supersedes.insert(id);
                continue;
            }
            const auto &old = node(patch_, id);
            if (old.contains("config")) m["config"] = old.at("config");
            else m.erase("config");
        }
    }
    // loadGraph is a stored document; a changed live slot is an edit.
    // Unchanged forward-compatible stored fields remain opaque.
    if (!new_namespace) for (const auto &m : patch["modules"]) {
        const auto data = m.value("data", Json::object());
        need(data.is_object(), "invalid", "data: expected object");
        auto old = std::find_if(patch_["modules"].begin(), patch_["modules"].end(),
            [&](const Json &n) { return n.at("id") == m.at("id") && n.at("module") == m.at("module"); });
        const auto prior = old == patch_["modules"].end() ? Json::object() : old->value("data", Json::object());
        const auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());
        need(d, "unknown-module", "Module not installed");
        const auto count = d->struct_size >= offsetof(ws2_descriptor, data_slots) + sizeof(d->data_slots)
            ? d->data_slot_count : 0;
        for (auto it = data.begin(); it != data.end(); ++it) {
            if (prior.contains(it.key()) && prior.at(it.key()) == it.value()) continue;
            uint32_t slot = 0;
            while (slot < count && it.key() != d->data_slots[slot].id) ++slot;
            need(slot < count, "invalid", ("data." + it.key() + ": unknown slot").c_str());
            std::vector<uint8_t> packed;
            std::string diagnostic;
            if (!ws::data_layout::pack_data_slot(d->data_slots[slot], it.value(),
                    ws::data_layout::DataLoad::Edit, packed, diagnostic, nullptr,
                    app_engine_data_validator(catalogue_.get(), d)))
                throw Refusal("invalid", diagnostic.c_str());
        }
        // Removing a declared slot is a live reset to its packed defaults.
        // Validate that edit with the same descriptor callback and field path.
        for (uint32_t slot = 0; slot < count; ++slot) {
            const auto &declared = d->data_slots[slot];
            if (!prior.contains(declared.id) || data.contains(declared.id)) continue;
            std::vector<uint8_t> packed;
            std::string diagnostic;
            if (!ws::data_layout::pack_data_slot(declared, Json::object(),
                    ws::data_layout::DataLoad::Edit, packed, diagnostic, nullptr,
                    app_engine_data_validator(catalogue_.get(), d)))
                throw Refusal("invalid", diagnostic.c_str());
        }
    }
    std::string error;
    const auto patch_bytes = patch.dump();
    // Stage metadata and cursor storage before any live graph swap.
    document::telemetry::Sampler next_telemetry(
        document::telemetry::plan(patch, catalogue_.get(), /*phase_enabled=*/true, /*groove_enabled=*/true));
    auto next_out = std::make_unique<osc::OutHost>(patch_bytes);
    document::ScopedOutBuses staged_out(next_out->buses());
    audio::EngineOwner candidate(
        document::load_runtime_patch(patch_bytes, catalogue_.get(), config_, error, &next_telemetry.taps()),
        app_engine_destroy);
    need(bool(candidate), "refused", "Graph configuration or state refused");
    // Stage all potentially throwing document/ID work before accepting a live graph.
    std::set<uint32_t> ids = new_namespace ? std::set<uint32_t>{} : used_ids_;
    for (const auto &m : patch["modules"]) ids.insert(integer(m["id"]));
    // Stage queue and terminal events before accepting the graph. A
    // refused ordinary transaction never publishes these changes.
    auto next_pending = pending_configs_;
    auto next_events = config_events_;
    std::set<uint32_t> changed_data;
    for (auto it = next_pending.begin(); it != next_pending.end();) {
        const auto id = it->first;
        auto next = std::find_if(patch["modules"].begin(), patch["modules"].end(),
            [&](const Json &m) { return m.at("id") == id; });
        auto old = std::find_if(patch_["modules"].begin(), patch_["modules"].end(),
            [&](const Json &m) { return m.at("id") == id; });
        const bool applied = retry_id && *retry_id == id;
        const bool data_changed = next != patch["modules"].end() && old != patch_["modules"].end() &&
            next->value("data", Json::object()) != old->value("data", Json::object());
        if (data_changed) changed_data.insert(id);
        if (applied || new_namespace || snapshot_supersedes.count(id) ||
            next == patch["modules"].end() || old == patch_["modules"].end() ||
            next->at("module") != it->second.module ||
            next->value("config", Json::object()) != old->value("config", Json::object())) {
            next_events.push_back(config_event(id, it->second, applied ? "applied" : "superseded", generation_ + 1));
            it = next_pending.erase(it);
        } else ++it;
    }
    // Live data delivery normally retains the instance. OSC Out is the
    // existing exception: its freshly staged bus is construction config.
    for (auto id : changed_data)
        stage_data_supersession(next_pending, next_events, token_, id, true,
                               node(patch, id).at("module") == "osc.out", generation_ + 1);
    // Determine eligibility by reverting ONLY changed config fields in an
    // execution copy and comparing the entire transaction to committed state.
    // Mixed data/topology/parameter/metadata changes can never be deferred.
    Json config_only = patch;
    std::vector<uint32_t> changed_configs;
    if (!new_namespace && !retry_id) {
        for (auto &m : config_only["modules"]) {
            const auto id = integer(m.at("id"));
            auto old = std::find_if(patch_["modules"].begin(), patch_["modules"].end(),
                [&](const Json &n) { return n.at("id") == id; });
            if (old == patch_["modules"].end() || old->at("module") != m.at("module")) continue;
            if (old->value("config", Json::object()) == m.value("config", Json::object())) continue;
            changed_configs.push_back(id);
            if (old->contains("config")) m["config"] = old->at("config");
            else m.erase("config");
        }
    }
    // A pending-config revert in a mixed refused snapshot must not be
    // silently dropped. Only newly changed config IDs are admitted here.
    const bool eligible_shape = !changed_configs.empty() && config_only == patch_ &&
        std::all_of(snapshot_supersedes.begin(), snapshot_supersedes.end(), [&](uint32_t id) {
            return std::find(changed_configs.begin(), changed_configs.end(), id) != changed_configs.end();
        });
    // A75/MIDI-busy refusals must leave live routes, counters and caches
    // untouched. Quiesce OSC only after the engine's staging preflight and
    // before publication, or immediately before the D5 swap.
    bool osc_paused = false;
    auto pause_osc = [&]() noexcept {
        if (osc_paused) return;
        osc_out_->stop();
        osc_->stop();
        osc_paused = true;
    };
    auto resume_osc = [this, &osc_paused](void *) noexcept {
        if (!osc_paused) return;
        try {
            start_osc();
        } catch (...) {
            osc_out_->stop();
            osc_->stop();
        }
    };
    std::unique_ptr<void, decltype(resume_osc)> osc_restart(this, resume_osc);
    const bool rendering = (stream_ && stream_->running()) || sink_rendering_.load(std::memory_order_acquire);
    if (!new_namespace && rendering) {
        const uint64_t timeout_ns = 3ULL * options_.block * 1000000000ULL / options_.rate;
        // A busy MIDI dispatch is transient; a graph refusal is not. Never stop for busy.
        for (unsigned attempt = 0; attempt < 4; ++attempt) {
            if (midi_->replan(candidate.get(), patch_bytes, timeout_ns, error,
                    [](void *ctx) noexcept { (*static_cast<decltype(pause_osc) *>(ctx))(); }, &pause_osc)) {
                osc_out_.swap(next_out); // rendered graph now owns the new bus
                patch_.swap(patch);
                used_ids_.swap(ids);
                pending_configs_.swap(next_pending);
                config_events_.swap(next_events);
                // Rebuild direct-only routing and clear old ring on commit.
                monitor_->configure(patch_);
                telemetry_.swap(next_telemetry); // Engine2 counts restart at every replan.
                ++generation_;
                std::cerr << "commit path=live gen=" << generation_ << '\n';
                return true;
            }
            // A75 is not an ordinary replan refusal: D5 would cut the
            // predecessor tail. Preserve the live graph and report busy.
            if (error == "Replacement busy: predecessor still fading") {
                const auto &blocked = app_engine_native(active_).replacement_blocked_ids();
                if (client_deferred_ && !retry_id && eligible_shape &&
                    std::all_of(changed_configs.begin(), changed_configs.end(), [&](uint32_t id) {
                        return std::find(blocked.begin(), blocked.end(), id) != blocked.end();
                    })) {
                    auto deferred = pending_configs_;
                    auto events = config_events_;
                    const auto defer_id = std::to_string(++next_defer_id_);
                    const auto now = std::chrono::steady_clock::now();
                    for (auto id : changed_configs) {
                        const auto &m = node(patch, id);
                        const auto *d = app_engine_native(active_).descriptor(id);
                        uint32_t ms = WS2_REPLACE_FADE_DEFAULT_MS;
                        if (d && d->struct_size >= offsetof(ws2_descriptor, replace_fade_ms) + sizeof(d->replace_fade_ms) &&
                            d->replace_fade_ms)
                            ms = std::min(d->replace_fade_ms, WS2_REPLACE_FADE_MAX_MS);
                        const auto previous = deferred.find(id);
                        if (previous != deferred.end())
                            events.push_back(config_event(id, previous->second, "superseded", generation_));
                        deferred.insert_or_assign(id, PendingConfig{m.at("module").get<std::string>(),
                            defer_id, m.value("config", Json::object()),
                            now + std::chrono::milliseconds(2 * ms + 1000)});
                    }
                    Refusal refusal("busy", error.c_str(), defer_id);
                    pending_configs_.swap(deferred);
                    config_events_.swap(events);
                    throw refusal;
                }
                throw Refusal("busy", error.c_str());
            }
            if (error != "MIDI worker busy") break;
            if (retry_id || attempt == 3) throw Refusal("busy", "MIDI worker busy; graph unchanged");
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
    }
    // Deferred A75 retries must never fall through to D5, even on another error.
    if (retry_id) throw Refusal("unavailable", "Deferred live config retry unavailable");
    // D5 replaces every instance, so a changed data slot now supersedes
    // that ID's pending config. Keep unrelated pending IDs (A80).
    // Stage before the swap; an unsuccessful D5 publishes no events.
    for (auto id : changed_data)
        stage_data_supersession(next_pending, next_events, token_, id, true, true, generation_ + 1);
    // D5 directly for loadGraph, stopped/lost streams and non-busy replan refusal.
    // The candidate was fully prepared above, so validation refusal is untouched.
    pause_osc();
    const auto begun = std::chrono::steady_clock::now();
    // D5 budgets (see kMuteBudget/kGapBudget); they stretch only when a block period is longer.
    const auto period = std::chrono::microseconds(int64_t(1e6 * double(options_.block) / double(options_.rate)));
    const auto gap_budget = std::max<std::chrono::microseconds>(kGapBudget, 3 * period);
    // The request/mute watchdog is separate from the actual audio interruption.
    auto gap_deadline = begun + gap_budget;
    auto output_live = [&] {
        return (stream_ && stream_->running()) || sink_rendering_.load(std::memory_order_acquire);
    };
    // Hands an engine to the running render thread at a block boundary. On success `e`
    // owns the retired engine, which the render thread no longer touches.
    auto exchange = [&](audio::EngineOwner &e, std::chrono::steady_clock::time_point deadline) {
        if (stream_) return stream_->exchange(e, deadline);
        if (!sink_slot_.offer(e.get(), deadline)) return false;
        std::swap(engine_, e);
        return true;
    };
    if (output_live()) {
        app_engine_begin_master_fade_out(active_);
        // Acknowledging a mute needs the in-flight block to finish, one fade block and one
        // entirely silent block: two periods is the bare minimum with no scheduling margin,
        // which a block-paced sink (Windows timer granularity) can miss. Stretch to three
        // periods, matching the gap budget below; kMuteBudget is unchanged at normal blocks.
        const auto deadline = begun + std::max<std::chrono::microseconds>(kMuteBudget, 3 * period);
        while (!app_engine_master_fade_silent(active_)) {
            // D6 may lose the stream during a refused replan or the D5 fade.
            // A callback that no longer renders cannot acknowledge a mute.
            if (!output_live()) break;
            if (std::chrono::steady_clock::now() >= deadline) {
                app_engine_resume_master_fade(active_);
                throw Refusal("unavailable", "Audio mute did not complete");
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        if (app_engine_master_fade_silent(active_)) {
            const auto first_fade_ns = app_engine_master_fade_out_started_ns(active_);
            if (first_fade_ns == 0) {
                app_engine_resume_master_fade(active_);
                throw Refusal("unavailable", "Audio fade callback unavailable");
            }
            gap_deadline = d5_gap_deadline(first_fade_ns, gap_budget);
        }
    }
    app_engine_prepare_master_fade_in(candidate.get());
    try {
        midi_->stop();
        app_engine_panic(active_);
    } catch (...) {
        app_engine_resume_master_fade(active_);
        throw;
    }
    auto old_patch = patch_;
    if (output_live()) {
        // In place: the device stays open and the render thread adopts the faded-in
        // candidate, so the gap is a few block periods. Reopening a Windows device
        // cannot fit the gap budget, so the stream is never restarted here.
        AppEngine *const previous = active_, *const next = candidate.get();
        if (!exchange(candidate, gap_deadline)) {
            app_engine_resume_master_fade(active_);
            start_midi();
            throw Refusal("unavailable", "Audio swap exceeded gap budget");
        }
        active_ = next; // `candidate` now owns the retired graph; it is destroyed below.
        patch_.swap(patch);
        try {
            start_midi();
            while (!app_engine_master_fade_in_started(active_)) {
                if (std::chrono::steady_clock::now() >= gap_deadline)
                    throw Refusal("unavailable", "Audio swap exceeded gap budget");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        } catch (...) {
            midi_->stop();
            patch_ = old_patch;
            app_engine_prepare_master_fade_in(previous);
            if (exchange(candidate, std::chrono::steady_clock::now() + gap_budget)) {
                active_ = previous;
            } else { // The render thread stalled: restore the previous graph the slow way.
                stop_audio();
                engine_ = std::move(candidate);
                active_ = engine_.get();
                start_audio();
            }
            start_midi();
            throw;
        }
    } else {
        stop_audio();
        auto previous = std::move(engine_);
        engine_ = std::move(candidate);
        active_ = engine_.get();
        patch_.swap(patch); // No allocation after the quiescent graph replacement.
        try {
            start_audio();
            start_midi();
            if (stream_ || sink_.joinable()) {
                while (!app_engine_master_fade_in_started(active_)) {
                    if (std::chrono::steady_clock::now() >= gap_deadline)
                        throw Refusal("unavailable", "Audio swap exceeded gap budget");
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                }
            }
        } catch (...) {
            midi_->stop();
            stop_audio();
            engine_ = std::move(previous);
            active_ = engine_.get();
            patch_ = old_patch;
            app_engine_prepare_master_fade_in(active_);
            start_audio();
            start_midi();
            throw;
        }
    }
    osc_out_.swap(next_out); // only after a successful D5 commit; rollback retains the old bus
    ++generation_;
    keyboard_.fill(false);
    used_ids_.swap(ids);
    pending_configs_.swap(next_pending);
    config_events_.swap(next_events);
    // No old-generation messages survive a successful graph commit.
    monitor_->configure(patch_);
    telemetry_.swap(next_telemetry); // D5 also resets all last-seen event counts.
    std::cerr << "commit path=d5 gen=" << generation_ << '\n';
    return false;
}
// applyGraph (0005 section 3, M2 E1a). Runs after a successful commit, so it never throws:
// the graph and gen have already advanced and the reply must be ok.
Json Session::reconcile_graph(const Json &before, bool live) {
    Json replaced = Json::array(), unapplied = Json::array();
    std::map<uint32_t, const Json *> prior;
    for (const auto &m : before["modules"]) prior.emplace(m["id"].get<uint32_t>(), &m);
    // The engine keeps an instance only when ID, descriptor and config bytes are unchanged
    // (engine2.cpp replan). Compare the same canonical bytes (E0). An OSC Out instance gets a
    // freshly staged bus pointer in its config on every commit, so it is never kept.
    auto same_instance = [](const Json &a, const Json &b) {
        const auto type = a["module"].get<std::string>();
        if (type != b["module"].get<std::string>() || type == "osc.out") return false;
        try {
            const auto id = a["id"].get<uint32_t>();
            return document::runtime_module_config(type, a.value("config", Json::object()), id) ==
                   document::runtime_module_config(type, b.value("config", Json::object()), id);
        } catch (...) {
            return false; // unreachable for committed documents; report as replaced
        }
    };
    struct Change {
        uint32_t id;
        const ws2_param *param;
        uint32_t index;
        float value;
        Json previous; // the committed value, or null when it was the module's initial value
    };
    std::vector<Change> changes;
    for (const auto &m : patch_["modules"]) {
        const auto id = m["id"].get<uint32_t>();
        const auto found = prior.find(id);
        if (found == prior.end()) continue; // created (rule 4)
        const Json &old = *found->second;
        if (!same_instance(old, m)) {
            replaced.push_back(id); // rule 3
            continue;
        }
        if (!live) continue; // D5 rebuilt every instance from the document (rule 6)
        auto *d = app_engine_native_descriptor(catalogue_.get(), m["module"].get<std::string>().c_str());
        if (!d) continue;
        const auto old_values = old.value("parameters", Json::object());
        const auto new_values = m.value("parameters", Json::object());
        for (uint32_t i = 0; i < d->param_count; ++i) {
            const auto &p = d->params[i];
            auto value_of = [&](const Json &values) {
                const auto it = values.find(p.id);
                return it != values.end() && it->is_number() ? it->get<float>() : p.initial;
            };
            const float from = value_of(old_values), to = value_of(new_values);
            if (from == to) continue;
            const auto it = old_values.find(p.id);
            changes.push_back({id, &p, i, to, it != old_values.end() ? *it : Json(nullptr)});
        }
    }
    // Rule 5: live parameter events after the swap, in document order. A queue that stays full
    // for three block periods without draining returns that parameter and every later one in
    // `unapplied`; the document keeps their old value.
    const auto period = std::chrono::microseconds(int64_t(1e6 * double(options_.block) / double(options_.rate)));
    std::chrono::steady_clock::time_point deadline{};
    bool full = false, exhausted = false;
    for (const auto &c : changes) {
        bool sent = false;
        while (!exhausted) {
            ws2_event native{};
            native.struct_size = sizeof(native);
            native.type = WS2_PARAM;
            native.index = c.index;
            native.value = c.value;
            if (app_engine_native(active_).enqueue(0, c.id, WS2_DIRECT_PORT, native, 0, engine2::Timing::Immediate) ==
                WS2_OK) {
                sent = true;
                full = false; // the queue drained: the next stall gets its own three periods
                break;
            }
            const auto now = std::chrono::steady_clock::now();
            if (!full) {
                full = true;
                deadline = now + 3 * period;
            }
            if (now >= deadline) exhausted = true;
            else std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        if (sent) continue;
        unapplied.push_back({{"moduleId", c.id}, {"paramId", c.param->id}});
        auto &parameters = node(patch_, c.id)["parameters"];
        if (c.previous.is_null()) parameters.erase(c.param->id);
        else parameters[c.param->id] = c.previous;
    }
    return {{"path", live ? "live" : "restart"}, {"replaced", std::move(replaced)}, {"unapplied", std::move(unapplied)}};
}
Json Session::apply(const Json &command) {
    auto refuse_rate = [&]() {
        audio_reason_ = "rate-unsupported";
        throw Refusal("refused", "rate-unsupported");
    };
    auto type = command.at("type").get<std::string>();
    if (type == "hello") {
        need(!client_hello_seen_, "duplicate", "Client hello already received");
        const auto &capabilities = command.at("capabilities");
        need(capabilities.is_array() && capabilities.size() <= 256, "invalid", "Invalid capabilities");
        bool supports_deferred = false;
        for (const auto &capability : capabilities) {
            need(capability.is_string() && capability.get_ref<const std::string &>().size() <= 128,
                 "invalid", "Invalid capability");
            supports_deferred |= capability == "configDeferred";
        }
        client_deferred_ = supports_deferred;
        client_hello_seen_ = true;
        return nullptr;
    }
    if (type == "listAudioDevices") {
        refresh_devices();
        Json result = {{"devices", audio_devices_}};
        if (!unavailable_audio_drivers_.empty()) result["audio"] = {{"unavailableDrivers", unavailable_audio_drivers_}};
        return result;
    }
    if (type == "listMidiDevices") return {{"devices", midi_devices_}};
    if (type == "midiLearn") {
        need(command.at("armed").is_boolean());
        const bool armed = command.at("armed").get<bool>();
        observer_->arm_learning(armed);
        return {{"armed", armed}};
    }
    if (type == "setOsc") throw Refusal("unavailable", "Capability not available");
    if (type == "setSampleRate" || type == "setBufferFrames") {
        const bool rate_change = type == "setSampleRate";
        const auto value = integer(command.at(rate_change ? "hz" : "frames"));
        const std::array<uint32_t, 3> rates{44100, 48000, 96000};
        const std::array<uint32_t, 5> blocks{64, 128, 256, 512, 1024};
        need(rate_change ? std::find(rates.begin(), rates.end(), value) != rates.end()
                         : std::find(blocks.begin(), blocks.end(), value) != blocks.end(),
             "invalid", "Rate or buffer size is outside the supported set");
        need(options_.audio || options_.null_audio, "unavailable", "Audio access not authorized");
        const uint32_t next_rate = rate_change ? value : options_.rate;
        const uint32_t next_block = rate_change ? options_.block : value;
        if (options_.audio) {
            refresh_devices(true, true, device_);
            need((stream_ && stream_->running()) || audio_reason_ == "rate-unsupported", "unavailable",
                 "No active audio stream");
            const auto count = std::count_if(audio_devices_.begin(), audio_devices_.end(),
                                             [&](const Json &d) { return d.at("id") == device_; });
            need(count == 1, "unavailable", "Selected audio output is missing or ambiguous");
            const auto entry = std::find_if(audio_devices_.begin(), audio_devices_.end(),
                                            [&](const Json &d) { return d.at("id") == device_; });
            need(entry->value("supported", true), "unavailable", "Audio output is unsupported");
            if (entry->contains("sampleRates") &&
                std::find((*entry)["sampleRates"].begin(), (*entry)["sampleRates"].end(), Json(next_rate)) ==
                    (*entry)["sampleRates"].end())
                refuse_rate();
        } else {
            need(sink_.joinable(), "unavailable", "No active null-audio stream");
        }
        if (next_rate == options_.rate && next_block == options_.block) return nullptr;

        // Control thread only. Keep the prepared graph when only the stream's
        // block size changes within its capacity; never panic or reset it.
        const auto old_config = config_;
        const auto old_rate = options_.rate, old_block = options_.block, old_requested = requested_block_;
        const auto old_preferences = preferences_;
        const bool rebuild = next_rate != old_rate || next_block > config_.max_block;
        osc_out_->stop();
        osc_->stop();
        auto resume_osc = [this](void *) noexcept {
            try {
                start_osc();
            } catch (...) {
                osc_out_->stop();
                osc_->stop();
            }
        };
        std::unique_ptr<void, decltype(resume_osc)> osc_restart(this, resume_osc);
        midi_->stop();
        stop_audio();
        StoppedGraph previous;
        Json fresh = Json::array();
        try {
            if (rebuild) {
                engine2::Config next_config = config_;
                next_config.sample_rate = next_rate;
                next_config.max_block = next_block;
                previous = prepare_stopped_graph(next_config, &fresh);
                need(bool(previous.engine), "unavailable", "Graph cannot prepare at requested stream configuration");
                swap_stopped_graph(previous);
                config_ = next_config;
            }
            options_.rate = next_rate;
            options_.block = next_block;
            requested_block_ = 0;
            start_audio(std::chrono::steady_clock::now(), &previous, &fresh);
            need(!options_.audio || (stream_ && stream_->running()), "unavailable",
                 "Audio device refused the new stream");
            start_midi();
            preferences_["audio"]["sampleRate"] = next_rate;
            preferences_["audio"]["bufferFrames"] = next_block;
            Json result = previous.engine ? Json{{"freshModules", std::move(fresh)}} : Json(nullptr);
            persist(); // only after the replacement stream is running
            ++generation_;
            if (previous.engine) keyboard_.fill(false);
            return result;
        } catch (...) {
            const bool rate_refused = audio_reason_ == "rate-unsupported";
            midi_->stop();
            stop_audio();
            if (previous.engine) swap_stopped_graph(previous);
            config_ = old_config;
            options_.rate = old_rate;
            options_.block = old_block;
            requested_block_ = old_requested;
            preferences_ = old_preferences;
            start_audio();
            start_midi();
            if (rate_refused) refuse_rate();
            throw Refusal("unavailable", "Stream change refused; previous configuration restored");
        }
    }

    if (type == "selectAudioDevice") {
        need(command.at("deviceId").is_string());
        auto id = command.at("deviceId").get<std::string>();
        refresh_devices(true, true, id);
        auto count = std::count_if(audio_devices_.begin(), audio_devices_.end(),
                                   [&](const Json &d) { return d.at("id") == id; });
        need(count > 0, "not-found", "No such audio output");
        need(count == 1, "duplicate", "Ambiguous audio output name");
        auto found =
            std::find_if(audio_devices_.begin(), audio_devices_.end(), [&](const Json &d) { return d.at("id") == id; });
        if (!found->value("supported", true)) {
            if (found->value("unsupportedReason", std::string{}) == "rate-unsupported") refuse_rate();
            throw Refusal("refused", found->value("unsupportedReason", std::string("unsupported")).c_str());
        }
        if (found->contains("sampleRates") && std::find((*found)["sampleRates"].begin(), (*found)["sampleRates"].end(),
                                                        Json(options_.rate)) == (*found)["sampleRates"].end())
            refuse_rate();
        need(options_.audio || options_.null_audio, "unavailable", "Audio device access is not authorized");
        auto old_device = device_;
        const auto old_config = config_;
        const auto old_block = options_.block, old_requested = requested_block_;
        StoppedGraph previous;
        Json fresh = Json::array(), result;
        // A device switch also tears down an audio worker. Join the packet
        // producer first, and resume against the same committed graph on
        // both success and restored-device failure paths.
        osc_out_->stop();
        osc_->stop();
        auto resume_osc = [this](void *) noexcept {
            try {
                start_osc();
            } catch (...) {
                osc_out_->stop();
                osc_->stop();
            }
        };
        std::unique_ptr<void, decltype(resume_osc)> osc_restart(this, resume_osc);
        midi_->stop();
        stop_audio();
        device_ = id;
        try {
            start_audio(std::chrono::steady_clock::now(), &previous, &fresh);
            need(!options_.audio || bool(stream_), "unavailable", "Cannot open audio output");
            start_midi();
            if (previous.engine) result = Json{{"freshModules", std::move(fresh)}};
            persist();
            if (previous.engine) keyboard_.fill(false);
        } catch (...) {
            const bool rate_refused = audio_reason_ == "rate-unsupported";
            // Preserve the attempted PortAudio/ASIO failure before a successful
            // rollback reopens the old stream and clears audio.error.
            const std::string failed_open = audio_error_;
            midi_->stop();
            stop_audio();
            if (previous.engine) swap_stopped_graph(previous);
            config_ = old_config;
            options_.block = old_block;
            requested_block_ = old_requested;
            device_ = old_device;
            start_audio();
            start_midi();
            if (rate_refused) refuse_rate();
            if (!failed_open.empty()) throw Refusal("unavailable", failed_open.c_str());
            throw;
        }
        refresh_devices(true, false);
        return result;
    }
    if (type == "setMidiEnabled") {
        need(command.at("deviceId").is_string() && command.at("on").is_boolean());
        auto id = command.at("deviceId").get<std::string>();
        auto found =
            std::find_if(midi_devices_.begin(), midi_devices_.end(), [&](const Json &d) { return d.at("id") == id; });
        need(found != midi_devices_.end(), "not-found", "No such MIDI input");
        need(options_.midi || options_.null_audio, "unavailable", "MIDI device access is not authorized");
        const midi::Endpoint selection{found->at("name").get<std::string>(),
                                       found->at("system_name").get<std::string>()};
        const bool enable = command.at("on").get<bool>();
        auto old = midi_->enabled();
        midi_->stop();
        midi_->select(selection, enable);
        try {
            need(midi_->enabled().size() <= 16, "limit", "Too many MIDI inputs");
            start_midi();
            // An ACK for a newly enabled input must mean its backend opened.
            // Startup restore still tolerates saved disconnected endpoints.
            if (enable) need(midi_->online(selection), "unavailable", "MIDI input could not be opened");
            persist();
        } catch (...) {
            midi_->stop();
            auto selected = midi_->enabled();
            for (auto &e : selected) midi_->select(e, false);
            for (auto &e : old) midi_->select(e, true);
            start_midi();
            throw;
        }
        refresh_devices(false);
        return nullptr;
    }
    if (type == "panic") {
        app_engine_panic(active_);
        keyboard_.fill(false);
        observer_->clear_notes();
        return nullptr;
    }
    if (type == "noteOn" || type == "noteOff") {
        auto key = integer(command.at("note"), 0, 127);
        float velocity = type == "noteOn" ? float(number(command.at("velocity"), 0, 1)) : 0;
        ws2_event event{};
        event.struct_size = sizeof(event);
        event.type = type == "noteOn" ? WS2_NOTE_ON : WS2_NOTE_OFF;
        event.note_id = -1;
        event.key = int32_t(key);
        event.value = velocity;
        for (const auto &m : patch_["modules"])
            if (m.at("module") == "host.keyboard") {
                auto result = app_engine_native(active_).enqueue(0, integer(m.at("id")), WS2_DIRECT_PORT, event, 0,
                                                                 engine2::Timing::Immediate);
                if (result != WS2_OK) {
                    if (type == "noteOff") app_engine_panic(active_);
                    throw Refusal("busy", "Event queue full");
                }
            }
        keyboard_[key] = type == "noteOn";
        return nullptr;
    }
    if (type == "setParam") {
        auto id = integer(command.at("moduleId"));
        auto &m = node(patch_, id);
        auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());
        auto param = command.at("paramId").get<std::string>();
        auto *p = parameter(d, param);
        need(command.at("value").is_number());
        double plain = command.at("value").get<double>();
        need(std::isfinite(plain));
        need(plain >= p->minimum && plain <= p->maximum, "refused", "Parameter outside range");
        float value = float(plain);
        ws2_event native{};
        native.struct_size = sizeof(native);
        native.type = WS2_PARAM;
        native.index = uint32_t(p - d->params);
        native.value = value;
        auto result = app_engine_native(active_).enqueue(0, id, WS2_DIRECT_PORT, native, 0, engine2::Timing::Immediate);
        need(result == WS2_OK, "busy", "Event queue full");
        m["parameters"][param] = value;
        return nullptr;
    }
    if (type == "setData") {
        const auto id = integer(command.at("moduleId"));
        auto &m = node(patch_, id);
        const auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());
        need(d, "unknown-module", "Module not installed");
        need(command.at("slot").is_string(), "invalid", "data.slot: expected string");
        const auto slot_id = command.at("slot").get<std::string>();
        const auto count = d->struct_size >= offsetof(ws2_descriptor, data_slots) + sizeof(d->data_slots)
            ? d->data_slot_count : 0;
        uint32_t slot = 0;
        while (slot < count && slot_id != d->data_slots[slot].id) ++slot;
        need(slot < count, "invalid", ("data." + slot_id + ": unknown slot").c_str());
        const auto &value = command.at("value");
        std::vector<uint8_t> packed;
        std::string error;
        if (!ws::data_layout::pack_data_slot(d->data_slots[slot], value,
                ws::data_layout::DataLoad::Edit, packed, error, nullptr,
                app_engine_data_validator(catalogue_.get(), d)))
            throw Refusal("invalid", error.c_str());
        // All JSON work and validation must precede the ring insertion. On
        // capacity/invalid/state refusal the execution document is unchanged.
        auto updated = m;
        if (!updated.contains("data")) updated["data"] = Json::object();
        updated["data"][slot_id] = value;
        const auto result = app_engine_native(active_).set_data_packed(id, slot, packed);
        need(result != WS2_CAPACITY, "busy", "Data queue full");
        need(result != WS2_INVALID, "invalid", "Invalid data slot");
        need(result == WS2_OK, "unavailable", "Data slot unavailable");
        m.swap(updated);
        return nullptr;
    }
    if (type == "loadGraph") {
        auto loaded = command.at("patch");
        auto &connections = loaded.at("connections");
        need(connections.is_array());
        need(connections.size() <= 128, "limit", "Graph capacity exceeded");
        std::vector<std::string> warnings;
        try {
            warnings = document::normalize_stored_modulation(connections, 2);
        } catch (const std::invalid_argument &e) {
            throw Refusal("invalid", e.what());
        }
        commit(std::move(loaded), true);
        if (!warnings.empty()) return Json{{"warnings", std::move(warnings)}};
        return nullptr;
    }
    if (type == "setModAmount") {
        const auto key = identity(command.at("connection"));
        auto &cables = patch_.at("connections");
        auto found = std::find_if(cables.begin(), cables.end(),
                                  [&](const Json &cable) { return identity(cable) == key; });
        need(found != cables.end(), "not-found", "No such connection");
        need(found->at("kind") == "modulation");
        const auto from = integer(key.at("from").at("module"));
        const auto to = integer(key.at("to").at("module"));
        const auto amount = number(command.at("amount"), -1, 1);
        auto &engine = app_engine_native(active_);
        auto *source = engine.descriptor(from);
        auto *destination = engine.descriptor(to);
        need(source && destination, "not-found", "No such module");
        auto *out = port(source, key.at("from").at("port").get<std::string>(), true);
        auto *param = parameter(destination, key.at("to").at("port").get<std::string>());
        const auto result = engine.set_mod_amount(from, uint32_t(out - source->outputs), to,
                                                  uint32_t(param - destination->params), float(amount));
        need(result != WS2_CAPACITY, "busy", "Event queue full");
        need(result == WS2_OK, "unavailable", "Modulation edge unavailable");
        (*found)["amount"] = amount;
        return nullptr;
    }
    Json candidate = patch_;
    if (type == "applyGraph") {
        // Same validation and execution copy as loadGraph, but in the current ID namespace and
        // through the live replan: unchanged modules keep their instances (0005 section 3).
        const Json before = patch_;
        const bool live = commit(command.at("patch"), false, std::nullopt, true);
        return reconcile_graph(before, live);
    }
    if (type == "addModule") {
        auto id = integer(command.at("moduleId"));
        need(!used_ids_.count(id), "duplicate", "Module ID was already used");
        Json module = {{"id", id}, {"module", command.at("moduleType")}};
        if (command.contains("params")) module["parameters"] = command.at("params");
        candidate["modules"].push_back(module);
    } else if (type == "removeModule") {
        auto id = integer(command.at("moduleId"));
        node(candidate, id);
        auto &modules = candidate["modules"];
        modules.erase(std::remove_if(modules.begin(), modules.end(), [&](const Json &m) { return m["id"] == id; }),
                      modules.end());
        auto &cables = candidate["connections"];
        cables.erase(
            std::remove_if(cables.begin(), cables.end(),
                           [&](const Json &c) { return c["from"]["module"] == id || c["to"]["module"] == id; }),
            cables.end());
        auto &outputs = candidate["outputs"];
        outputs.erase(std::remove_if(outputs.begin(), outputs.end(), [&](const Json &o) { return o["module"] == id; }),
                      outputs.end());
    } else if (type == "connect" || type == "disconnect") {
        auto connection = command.at("connection");
        need(connection.is_object());
        auto &cables = candidate["connections"];
        auto found = std::find_if(cables.begin(), cables.end(),
                                  [&](const Json &c) { return identity(c) == identity(connection); });
        if (type == "connect") {
            need(found == cables.end(), "duplicate", "Connection exists");
            cables.push_back(connection);
        } else {
            need(found != cables.end(), "not-found", "No such connection");
            cables.erase(found);
        }
    } else if (type == "ccMap.set") {
        auto &m = node(candidate, integer(command.at("moduleId")));
        need(m.at("module") == "midi.cc_to_cv", "not-found", "No such CC mapping module");
        auto row = integer(command.at("row"), 0, UINT32_MAX);
        need(row < 8, "limit", "CC row capacity exceeded");
        auto &cfg = m["config"];
        if (cfg.is_null()) cfg = Json::object();
        auto &rows = cfg["rows"];
        if (rows.is_null()) rows = Json::array();
        need(rows.is_array() && row <= rows.size(), "limit", "CC rows cannot have holes");
        auto mapping = command.at("mapping");
        need(mapping.is_object());
        integer(mapping.at("channel"), 0, 16);
        integer(mapping.at("controller"), 0, 127);
        for (const char *key : {"fourteen_bit", "bipolar"})
            if (mapping.contains(key)) need(mapping[key].is_boolean());
        if (mapping.contains("smoothing_ms")) number(mapping["smoothing_ms"], 0, 2000);
        if (row == rows.size()) rows.push_back(mapping);
        else rows[row] = mapping;
    } else throw Refusal("invalid", "Unknown command type");
    commit(std::move(candidate), false);
    return nullptr;
}
Json Session::base() const { return {{"v", 0}, {"session", token_}, {"gen", std::to_string(generation_)}}; }
Json Session::reply(const Request &request) {
    // Marks bracket (R7): blocks appended before the command is applied.
    const uint64_t b0 = marks_.enabled() ? capture_.appended() : 0;
    auto result = base();
    result["re"] = nullptr;
    result["ok"] = false;
    try {
        if (!request.value.is_null() && request.value.contains("id") && request.value["id"].is_string()) {
            auto id = request.value["id"].get<std::string>();
            bool valid = !id.empty() && id.size() <= 64 &&
                         std::all_of(id.begin(), id.end(), [](unsigned char c) { return c >= 32 && c <= 126; });
            if (valid) result["re"] = id;
        }
        if (!request.error.empty()) throw Refusal(request.error, "Input refused");
        need(!result["re"].is_null());
        need(request.value.at("v").is_number_integer() && request.value.at("v") == 0 &&
             request.value.at("type").is_string());
        auto data = apply(request.value);
        result["ok"] = true;
        if (!data.is_null()) result["result"] = std::move(data);
    } catch (const audio::ShutdownFailure &e) {
        std::cerr << e.what() << '\n';
        std::cerr.flush();
        std::_Exit(2);
    } catch (const Refusal &e) {
        result["code"] = e.code;
        result["message"] = e.what();
        if (!e.defer_id.empty()) {
            result["deferred"] = true;
            result["deferId"] = e.defer_id;
        }
    } catch (const Json::exception &) {
        result["code"] = "invalid";
        result["message"] = "Invalid command field";
    } catch (const std::exception &) {
        result["code"] = "unavailable";
        result["message"] = "Engine operation unavailable";
    }
    result["gen"] = std::to_string(generation_);
    if (marks_.enabled()) {
        // ...and after the reply is built. The reply itself is unchanged by marking.
        const uint64_t b1 = capture_.appended();
        Json mark = {{"re", result["re"]}, {"type", nullptr}, {"ok", result["ok"]},
                     {"gen", result["gen"]}, {"b0", b0}, {"b1", b1}};
        if (request.value.is_object() && request.value.contains("type") && request.value["type"].is_string())
            mark["type"] = request.value["type"];
        marks_.write(mark.dump());
    }
    return result;
}
Json Session::audio_status() const {
    auto selected = stream_ && stream_->running();
    const double cpu = selected ? stream_->cpu_percent() : 0;
    // An opened stream has no measured load until its first callback completes.
    // A zero-frame callback also leaves load unavailable, so it stays starting.
    const bool measured = std::isfinite(cpu) && cpu >= 0;
    auto state = audio_state_;
    if (options_.audio && stream_ && !selected) state = "device-lost";
    else if (selected && !measured) state = "starting";
    Json result = {{"state", state},
                   {"deviceId", selected ? Json(device_) : Json(nullptr)},
                   {"deviceName", selected ? Json(device_) : Json(nullptr)},
                   {"sampleRate", options_.rate},
                   {"bufferFrames", options_.block},
                   {"latencyMs", 2. * options_.block / options_.rate * 1000},
                   {"cpuPercent", measured ? cpu : 0},
                   {"dropouts", dropouts_.load() + (stream_ ? stream_->dropouts() : 0)}};
    if (!audio_reason_.empty()) result["reason"] = audio_reason_;
    if (!audio_error_.empty()) result["error"] = audio_error_;
    // The ASIO driver forced bufferFrames; the user's saved size is unchanged.
    if (requested_block_ && requested_block_ != options_.block) result["requestedBufferFrames"] = requested_block_;
    if (!unavailable_audio_drivers_.empty()) result["unavailableDrivers"] = unavailable_audio_drivers_;
    return result;
}
Json Session::midi_status() const {
    // Preserve the v0 default hello/status wire shape, including the pinned
    // S0 byte snapshot. Opt-in scripted MIDI is the only counter transport.
    Json result = {{"devices", midi_devices_}, {"activity", observer_->activity()}};
    if (options_.scripted_midi)
        result["counters"] = Json::parse(midi_->diagnostics()); // real Host/Service counters
    auto learn = observer_->learning();
    if (!learn.is_null()) result["learn"] = std::move(learn);
    return result;
}
Json Session::hello() const {
    Json capabilities = Json::array(
        {"midiLearn", "telemetry.playhead", "telemetry.monitor", "setSampleRate", "setBufferFrames", "osc", "osc.out",
         "applyGraph", "configDeferred"});
    return {{"v", 0},
            {"session", token_},
            {"type", "hello"},
            {"protocol", 0},
            {"engine", {{"version", "1.0.0"}, {"sha", WIRESCAPE_ENGINE_SHA}}},
            {"capabilities", std::move(capabilities)},
            {"catalogue", catalogue(catalogue_.get())},
            {"audioDevices", audio_devices_},
            {"audio", audio_status()},
            {"midi", midi_status()}};
}
Json Session::status() const {
    // The caller is the existing 100ms control-thread status tick, never render.
    if (active_) app_engine_native(active_).refresh_latency();
    auto value = base();
    value["type"] = "status";
    value["status"] = {{"audio", audio_status()}, {"midi", midi_status()}};
    // Snapshot only on the control thread. Summary fields are aggregate actual
    // bind state; multi-port details stay in the bounded per-route list.
    Json osc_status = {{"enabled", false}, {"bind", "127.0.0.1"}, {"port", 0}, {"lan", false}};
    Json osc_routes = Json::array();
    bool any_bound = false, any_lan = false, port_busy = false;
    for (const auto &route : osc_->states()) {
        if (osc_routes.empty()) osc_status["port"] = route.port;
        const std::string state = route.state;
        const bool listening = state == "listening" || state == "lan-not-confirmed";
        any_bound |= listening;
        any_lan |= listening && route.lan_bound;
        port_busy |= state == "port-busy"; // a disabled route (#612) is not an error
        Json entry = Json::object();
        entry["module"] = std::to_string(route.node);
        entry["port"] = route.port;
        entry["bind"] = route.lan_bound ? "0.0.0.0" : "127.0.0.1";
        entry["state"] = route.state;
        entry["received"] = route.received;
        entry["dropped"] = route.dropped;
        entry["budget_dropped"] = route.budget_dropped;
        entry["enqueue_dropped"] = route.enqueue_dropped;
        entry["listener_budget_dropped"] = route.listener_budget_dropped;
        entry["listener_enqueue_dropped"] = route.listener_enqueue_dropped;
        osc_routes.push_back(std::move(entry));
    }
    osc_status["enabled"] = any_bound;
    osc_status["lan"] = any_lan;
    osc_status["bind"] = any_lan ? "0.0.0.0" : "127.0.0.1";
    if (port_busy) osc_status["last_error"] = "port-busy";
    osc_status["routes"] = std::move(osc_routes);
    Json out_routes = Json::array();
    for (const auto &route : osc_out_->states()) {
        Json entry = {{"module", std::to_string(route.node)},
                      {"port", route.port},
                      {"state", route.state},
                      {"sent", route.sent},
                      {"dropped", route.dropped}};
        if (route.last_error) entry["last_error"] = route.last_error;
        out_routes.push_back(std::move(entry));
    }
    osc_status["out"] = std::move(out_routes);
    value["status"]["osc"] = std::move(osc_status);
    return value;
}
Json Session::telemetry() {
    auto held = observer_->held();
    for (size_t key = 0; key < 128; ++key)
        if (keyboard_[key] && std::find(held.begin(), held.end(), Json(key)) == held.end()) held.push_back(key);
    auto meters = Json::object();
    // Every observed essentials.output reports its own bus channel(s): one Output
    // feeding both sides gives [L,R]; a per-side Output (stereo patches) gives
    // [peak,peak] of its channel. Owner v1: stereo Output meters never moved.
    const auto meter = app_engine_get_meter(active_);
    if (meter.frame != 0) {
        std::map<int64_t, std::array<float, 2>> levels;
        std::map<int64_t, std::array<bool, 2>> seen;
        for (const auto &route : patch_["outputs"]) {
            if (route.value("port", "") != "audio" || !route.contains("module") || !route.contains("bus_channel"))
                continue;
            const auto id = integer(route["module"]);
            if (node(patch_, id).value("module", "") != "essentials.output") continue;
            const auto channel = integer(route["bus_channel"], 0, 15);
            const float level = app_engine_channel_peak(active_, static_cast<uint32_t>(channel));
            auto &l = levels[id];
            auto &s = seen[id];
            if (channel == 1) { l[1] = level; s[1] = true; }
            else if (channel == 0) { l[0] = level; s[0] = true; }
            else { l[0] = std::max(l[0], level); s[0] = true; }
        }
        for (const auto &[id, l] : levels) {
            const auto &s = seen[id];
            const float left = s[0] ? l[0] : l[1], right = s[1] ? l[1] : l[0];
            meters[std::to_string(id)] = Json::array({left, right});
        }
    }
    Json telemetry = {{"tick", ++tick_},
                      {"time", std::chrono::duration<double>(std::chrono::steady_clock::now() - started_).count()},
                      {"meters", meters},
                      {"heldNotes", held}};
    telemetry["scope"] = Json::object();
    auto snapshot = telemetry_.sample(active_);
    telemetry.update(snapshot);
    auto monitors = monitor_->snapshot(); // ingress-owned rings; never read in the render callback
    if (!monitors.empty()) telemetry["monitor"] = std::move(monitors);
    auto value = base();
    value["type"] = "telemetry";
    value["telemetry"] = telemetry;
    return value;
}
Json Session::devices() {
    auto value = base();
    value["type"] = "devices";
    value["audioDevices"] = audio_devices_;
    value["midiDevices"] = midi_devices_;
    if (!unavailable_audio_drivers_.empty()) value["audio"] = {{"unavailableDrivers", unavailable_audio_drivers_}};
    return value;
}
bool Session::poll_audio(std::chrono::steady_clock::time_point now, bool enumerated) {
    if (!options_.audio) return false;
    auto previous = audio_state_;
    const auto matches = std::count_if(audio_devices_.begin(), audio_devices_.end(),
                                       [&](const Json &d) { return d.at("id") == device_; });
    if (stream_ && (!stream_->running() || (enumerated && matches == 0))) {
        // A hot-unplug retires an audio callback while preserving the graph.
        // Quiesce OSC ingress until the owned audio stream is joined.
        osc_out_->stop();
        osc_->stop();
        auto resume_osc = [this](void *) noexcept {
            try {
                start_osc();
            } catch (...) {
                osc_out_->stop();
                osc_->stop();
            }
        };
        std::unique_ptr<void, decltype(resume_osc)> osc_restart(this, resume_osc);
        midi_->stop();
        stop_audio();
        audio_reason_.clear(); // genuine device loss supersedes a prior refused setting
        audio_state_ = "device-lost";
        audio_backoff_ = std::chrono::milliseconds(100);
        audio_retry_ = now + audio_backoff_;
    } else if (!stream_) {
        if (audio_reason_ == "rate-unsupported") return false;
        if (audio_state_ == "device-lost") audio_state_ = "reconnecting";
        if (now < audio_retry_) return previous != audio_state_;
        start_audio(now);
        if (stream_) start_midi();
    }
    return previous != audio_state_;
}
// OB-g9 #348: the control owner is the single egress consumer (ABI2_SPEC D13). Render copies
// every routed module event to the egress rings; COMMUNICATION_MODULES_PLAN's I/O dispatcher
// will send them. No endpoint sink exists yet, so drained events are discarded. Undrained, a
// full critical ring turns each further release (e.g. MIDI note-off into midi.to_cv) into an
// engine emergency: the generation moves, all DSP resets and OSC In can no longer enqueue.
// Control thread only, like every other active_ swap, so this never races a graph change.
void Session::drain_egress() noexcept {
    if (!active_) return;
    auto &live = app_engine_native(active_);
    engine2::Outgoing discarded;
    for (uint32_t i = 0; i < kEgressDrainPerPoll && live.pop_egress(discarded); ++i) {
    }
}
bool Session::retry_config(std::chrono::steady_clock::time_point now) {
    // Deadlines expire even when rendering has stopped. Inspect retirement
    // before building a candidate or pausing host workers; one attempt only.
    for (auto it = pending_configs_.begin(); it != pending_configs_.end();) {
        if (now >= it->second.deadline) {
            config_events_.push_back(config_event(it->first, it->second, "failed", generation_));
            it = pending_configs_.erase(it);
        } else ++it;
    }
    if (pending_configs_.empty() ||
        !((stream_ && stream_->running()) || sink_rendering_.load(std::memory_order_acquire))) return false;
    auto &graph = app_engine_native(active_);
    for (auto it = pending_configs_.begin(); it != pending_configs_.end(); ++it) {
        const auto id = it->first;
        if (graph.replacement_tail_pending(id)) continue;
        try {
            Json candidate = patch_; // rebase only config on the newest committed document
            auto &m = node(candidate, id);
            if (m.at("module") != it->second.module ||
                m.value("config", Json::object()) == it->second.config) {
                config_events_.push_back(config_event(id, it->second, "superseded", generation_));
                pending_configs_.erase(id);
                return false;
            }
            m["config"] = it->second.config;
            commit(std::move(candidate), false, id);
            return true;
        } catch (const std::exception &e) {
            std::cerr << "deferred config refused: " << e.what() << '\n';
            // A retirement permits exactly one attempt. Never retry a refusal
            // every poll or fall back to D5.
            const auto pending = pending_configs_.find(id);
            if (pending != pending_configs_.end()) {
                config_events_.push_back(config_event(id, pending->second, "failed", generation_));
                pending_configs_.erase(pending);
            }
            return false;
        }
    }
    return false;
}
bool Session::poll(std::chrono::steady_clock::time_point now) {
    if (scripted_midi_ && scripted_started_enabled_ && now >= scripted_started_) {
        const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(now - scripted_started_).count();
        scripted_midi_->advance_to(uint64_t(elapsed), 4096); // bounded; no OS device, no callback allocation
    }
    drain_egress();
    observer_->expire_learning(now);
    auto old_audio = audio_devices_, old_midi = midi_devices_;
    const auto old_unavailable = unavailable_audio_drivers_;
    if (midi_->enabled().empty()) observer_->endpoints();
    // Warm polling refreshes identities only: ALSA format probes can open a busy PCM.
    // Without a stream every call is a cold init, so space those out.
    constexpr std::chrono::seconds kColdEnumeration{2};
    const bool warm = stream_ != nullptr || !options_.audio;
    const bool cold_due = !cold_enumeration_ || now - *cold_enumeration_ >= kColdEnumeration;
    if (!warm && cold_due) cold_enumeration_ = now;
    const auto enumerated = refresh_devices(warm || cold_due, !warm);
    auto changed = poll_audio(now, enumerated);
    changed = retry_config(now) || changed;
    return changed || old_audio != audio_devices_ || old_midi != midi_devices_ ||
           old_unavailable != unavailable_audio_drivers_;
}
} // namespace wirescape::sidecar

