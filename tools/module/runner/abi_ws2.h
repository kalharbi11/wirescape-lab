// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Sole ABI-dependent translation boundary. MT2/MT3 use only neutral Host* types.
#include "wirescape/module2.h"
#include "allocation_watch.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <limits>
#include <locale>
#include <sstream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>
#ifdef _WIN32
#include <malloc.h>
#endif

struct HostEvent {
    unsigned type = 0, offset = 0, port = 0, flags = 0;
    int channel = 0, note_id = -1, key = 0;
    unsigned source_id = 0, index = 0;
    float value = 0, value2 = 0;
};
struct HostSignal {
    bool constant = false, connected = true;
    unsigned channels = 0;
    std::vector<std::vector<float>> samples;
};
struct HostPort {
    std::string id, name;
    unsigned kind = 0, hint = 0, poly = 0;
};
struct HostParam {
    std::string id, name, unit;
    float minimum = 0, maximum = 0, initial = 0, step = 0;
    unsigned flags = 0;
};
struct HostDescription {
    std::string id, name;
    unsigned version = 0, abi_version = 0;
    std::vector<HostPort> inputs, outputs;
    std::vector<HostParam> params;
    std::vector<std::string> errors;
};
struct HostBlock {
    unsigned frames = 0, channels = 1;
    double sample_rate = 48000.;
    std::vector<HostSignal> inputs, params, outputs;
    std::vector<HostEvent> events, emitted;
};

class HostModule {
    const ws2_descriptor* descriptor_ = nullptr;
    void* instance_ = nullptr;
    std::vector<void*> allocations_;
    ws2_host host_{};
    ws2_config config_{};
    std::vector<uint8_t> config_data_;
    bool measuring_ = false;
    uint64_t process_host_allocations_ = 0;

    static bool id_ok(const char* id) {
        if (!id || !*id) return false;
        for (const char* c = id; *c; ++c) {
            if (!(*c >= 'a' && *c <= 'z') && !(*c >= '0' && *c <= '9') &&
                *c != '_' && *c != '.') return false;
        }
        return true;
    }
    static std::string safe(const char* p) { return p ? std::string(p) : std::string(); }
    static void* WS2_CALL allocate(void* ctx, size_t size, size_t alignment, uint32_t) {
        auto* self = static_cast<HostModule*>(ctx);
        if (!self || alignment > 4096) return nullptr;
        alignment = std::max(alignment, sizeof(void*));
        if (alignment & (alignment - 1)) return nullptr;
        void* out = nullptr;
#ifdef _WIN32
        out = _aligned_malloc(size ? size : 1, alignment);
#else
        if (posix_memalign(&out, alignment, size ? size : 1)) out = nullptr;
#endif
        if (out) {
            if (self->measuring_) ++self->process_host_allocations_;
            self->allocations_.push_back(out);
        }
        return out;
    }
    static void free_aligned(void* p) {
#ifdef _WIN32
        _aligned_free(p);
#else
        std::free(p);
#endif
    }
    static ws2_event as_native(const HostEvent& e) {
        ws2_event n{};
        n.struct_size = sizeof(n); n.type = e.type; n.offset = e.offset;
        n.port = e.port; n.flags = e.flags; n.channel = e.channel;
        n.note_id = e.note_id; n.key = e.key; n.source_id = e.source_id;
        n.index = e.index; n.value = e.value; n.value2 = e.value2;
        return n;
    }
    static HostEvent as_host(const ws2_event& e) {
        return {e.type, e.offset, e.port, e.flags, e.channel, e.note_id,
                e.key, e.source_id, e.index, e.value, e.value2};
    }
    static int WS2_CALL push_event(void* ctx, uint32_t port, const ws2_event* e) {
        if (!ctx || !e) return WS2_INVALID;
        auto* block = static_cast<HostBlock*>(ctx);
        auto event = as_host(*e);
        event.port = port;
        block->emitted.push_back(event);
        return WS2_OK;
    }
    static int WS2_CALL write_state(void* ctx, const void* data, uint32_t count) {
        if (!ctx || (!data && count)) return WS2_INVALID;
        auto* bytes = static_cast<std::vector<uint8_t>*>(ctx);
        if (count > 1024 * 1024 || bytes->size() + count > 1024 * 1024) return WS2_CAPACITY;
        const auto* p = static_cast<const uint8_t*>(data);
        bytes->insert(bytes->end(), p, p + count);
        return WS2_OK;
    }
    struct Reader { const uint8_t* data; size_t count, offset = 0; };
    static int WS2_CALL read_state(void* ctx, void* dest, uint32_t count) {
        auto* reader = static_cast<Reader*>(ctx);
        if (!reader || (!dest && count) || count > reader->count - reader->offset) return WS2_INVALID;
        if (count) std::memcpy(dest, reader->data + reader->offset, count);
        reader->offset += count;
        return WS2_OK;
    }
    static std::string quote(const std::string& input) {
        std::ostringstream out;
        out << '"';
        for (unsigned char c : input) {
            switch (c) {
                case '"': out << "\\\""; break;
                case '\\': out << "\\\\"; break;
                case '\n': out << "\\n"; break;
                case '\r': out << "\\r"; break;
                case '\t': out << "\\t"; break;
                default:
                    if (c < 32) {
                        out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec;
                    } else out << char(c);
            }
        }
        return out.str() + '"';
    }
    static void number(std::ostringstream& out, float v) {
        if (std::isfinite(v)) out << std::setprecision(std::numeric_limits<float>::max_digits10) << v;
        else out << "null";
    }

public:
    HostModule() : descriptor_(ws_module2_entry()) {
        host_ = {sizeof(host_), this, &HostModule::allocate};
    }
    HostModule(const HostModule&) = delete;
    HostModule& operator=(const HostModule&) = delete;
    ~HostModule() { destroy(); }
    HostDescription describe() const {
        HostDescription o;
        const auto* d = descriptor_;
        if (!d) { o.errors.push_back("entry returned no descriptor"); return o; }
        if (d->struct_size < sizeof(ws2_descriptor)) {
            o.errors.push_back("descriptor struct_size is too small"); return o;
        }
        o.id = safe(d->id); o.name = safe(d->name);
        o.version = d->version; o.abi_version = d->abi_version;
        if (d->abi_version != WS_ABI2_VERSION || ws_module2_abi_version() != WS_ABI2_VERSION)
            o.errors.push_back("ABI version mismatch");
        if (!id_ok(d->id)) o.errors.push_back("module id is malformed");
        if (o.name.empty()) o.errors.push_back("module name is empty");
        if (!d->create || !d->destroy || !d->prepare || !d->process)
            o.errors.push_back("required callback missing");
        if (d->input_count > WS2_MAX_PORTS || d->output_count > WS2_MAX_PORTS ||
            d->param_count > WS2_MAX_PARAMS) {
            o.errors.push_back("descriptor count exceeds ABI limit"); return o;
        }
        if ((d->input_count && !d->inputs) || (d->output_count && !d->outputs) ||
            (d->param_count && !d->params)) {
            o.errors.push_back("descriptor array pointer is null"); return o;
        }
        auto inspect_ports = [&o](const ws2_port* src, unsigned count, std::vector<HostPort>& dst, const char* label) {
            std::unordered_set<std::string> ids;
            for (unsigned i = 0; i < count; ++i) {
                const auto& p = src[i];
                if (p.struct_size < sizeof(ws2_port)) o.errors.push_back(std::string(label) + " struct_size too small");
                if (!id_ok(p.id)) o.errors.push_back(std::string(label) + " id malformed");
                auto name = safe(p.id);
                if (!ids.insert(name).second) o.errors.push_back(std::string(label) + " duplicate id: " + name);
                if (p.kind != WS2_SIGNAL && p.kind != WS2_EVENT) o.errors.push_back(std::string(label) + " invalid kind: " + name);
                dst.push_back({name, safe(p.name), p.kind, p.hint, p.poly});
            }
        };
        inspect_ports(d->inputs, d->input_count, o.inputs, "input");
        inspect_ports(d->outputs, d->output_count, o.outputs, "output");
        std::unordered_set<std::string> ids;
        for (unsigned i = 0; i < d->param_count; ++i) {
            const auto& p = d->params[i];
            if (p.struct_size < sizeof(ws2_param)) o.errors.push_back("param struct_size too small");
            if (!id_ok(p.id)) o.errors.push_back("param id malformed");
            auto id = safe(p.id);
            if (!ids.insert(id).second) o.errors.push_back("param duplicate id: " + id);
            if (!std::isfinite(p.minimum) || !std::isfinite(p.maximum) || !std::isfinite(p.initial) ||
                !(p.minimum < p.maximum) || p.initial < p.minimum || p.initial > p.maximum)
                o.errors.push_back("param range/initial invalid: " + id);
            o.params.push_back({id, safe(p.name), safe(p.unit), p.minimum, p.maximum,
                                p.initial, p.step, p.flags});
        }
        return o;
    }
    std::string describe_json() const {
        const auto d = describe();
        std::ostringstream out;
        out.imbue(std::locale::classic());
        out << "{\"id\":" << quote(d.id) << ",\"name\":" << quote(d.name)
            << ",\"version\":" << d.version << ",\"abi_version\":" << d.abi_version;
        auto ports = [&out](const char* name, const std::vector<HostPort>& items) {
            out << ",\"" << name << "\":[";
            for (size_t i = 0; i < items.size(); ++i) {
                const auto& p = items[i];
                if (i) out << ',';
                out << "{\"id\":" << quote(p.id) << ",\"name\":" << quote(p.name)
                    << ",\"kind\":" << p.kind << ",\"hint\":" << p.hint
                    << ",\"poly\":" << p.poly << '}';
            }
            out << ']';
        };
        ports("inputs", d.inputs); ports("outputs", d.outputs);
        out << ",\"params\":[";
        for (size_t i = 0; i < d.params.size(); ++i) {
            const auto& p = d.params[i];
            if (i) out << ',';
            out << "{\"id\":" << quote(p.id) << ",\"name\":" << quote(p.name)
                << ",\"unit\":" << quote(p.unit) << ",\"minimum\":";
            number(out, p.minimum); out << ",\"maximum\":"; number(out, p.maximum);
            out << ",\"initial\":"; number(out, p.initial);
            out << ",\"step\":"; number(out, p.step);
            out << ",\"flags\":" << p.flags << '}';
        }
        out << "],\"errors\":[";
        for (size_t i = 0; i < d.errors.size(); ++i) {
            if (i) out << ',';
            out << quote(d.errors[i]);
        }
        out << "]}";
        return out.str();
    }
    int create(double rate, unsigned block, unsigned voices, const std::vector<uint8_t>& config = {}) {
        if (!descriptor_ || instance_) return WS2_INVALID;
        config_data_ = config;
        config_ = {sizeof(config_), rate, block, voices, 42,
                   config_data_.empty() ? nullptr : config_data_.data(),
                   static_cast<uint32_t>(config_data_.size())};
        instance_ = descriptor_->create(&host_);
        if (!instance_) return WS2_CAPACITY;
        return descriptor_->prepare(instance_, &config_, &host_);
    }
    // Optional allocation count spans only the module callback (not host-side
    // buffer/pointer setup). MT2 must not count the runner's own vector growth.
    int process(HostBlock& block, uint64_t* allocation_count = nullptr) {
        if (!descriptor_ || !instance_) return WS2_INVALID;
        const unsigned ni = descriptor_->input_count, no = descriptor_->output_count,
                       np = descriptor_->param_count;
        std::vector<ws2_signal> inputs(ni), params(np);
        std::vector<ws2_signal_out> outputs(no);
        std::vector<std::vector<const float*>> in_ptrs(ni), param_ptrs(np);
        std::vector<std::vector<float*>> out_ptrs(no);
        auto fill_in = [&](const std::vector<HostSignal>& src, std::vector<ws2_signal>& dest,
                           std::vector<std::vector<const float*>>& pointers) {
            for (size_t i = 0; i < dest.size(); ++i) {
                if (i < src.size()) {
                    for (const auto& ch : src[i].samples) pointers[i].push_back(ch.data());
                    dest[i] = {sizeof(ws2_signal), pointers[i].empty() ? nullptr : pointers[i].data(),
                               static_cast<uint32_t>(pointers[i].size()),
                               static_cast<uint32_t>((src[i].constant ? WS2_CONSTANT : 0u) |
                                                     (src[i].connected ? WS2_CONNECTED : 0u))};
                } else dest[i] = {sizeof(ws2_signal), nullptr, 0, WS2_CONSTANT};
            }
        };
        fill_in(block.inputs, inputs, in_ptrs);
        fill_in(block.params, params, param_ptrs);
        block.outputs.resize(no);
        for (unsigned i = 0; i < no; ++i) {
            auto& b = block.outputs[i]; b.channels = block.channels;
            b.samples.assign(block.channels, std::vector<float>(block.frames, 0.));
            for (auto& ch : b.samples) out_ptrs[i].push_back(ch.data());
            outputs[i] = {sizeof(ws2_signal_out), out_ptrs[i].data(), block.channels, 0, block.channels};
        }
        std::vector<ws2_event> events;
        for (const auto& e : block.events) events.push_back(as_native(e));
        ws2_event_list evt{sizeof(evt), static_cast<uint32_t>(events.size()),
                           events.empty() ? nullptr : events.data()};
        std::vector<ws2_event_list> event_in(ni, {sizeof(ws2_event_list), 0, nullptr});
        std::vector<ws2_event_out> event_out(no);
        for (unsigned i = 0; i < no; ++i)
            event_out[i] = {sizeof(ws2_event_out), &block, i, &HostModule::push_event};
        ws2_process ctx{};
        ctx.struct_size = sizeof(ctx); ctx.frames = block.frames;
        ctx.sample_rate = block.sample_rate; ctx.channels = block.channels;
        ctx.input_count = ni; ctx.output_count = no; ctx.param_count = np;
        ctx.inputs = inputs.data(); ctx.outputs = outputs.data(); ctx.params = params.data();
        ctx.event_inputs = event_in.data(); ctx.event_outputs = event_out.data();
        ctx.events = evt;
        int status;
        if (allocation_count) {
            // Event delivery is a host callback and must not consume measured
            // heap operations for the module. Reserve before entering the scope.
            block.emitted.reserve(block.emitted.size() + 1024);
            process_host_allocations_ = 0;
            measuring_ = true;
            {
                allocation_watch::ThreadScope counter;
                status = descriptor_->process(instance_, &ctx);
                *allocation_count = counter.allocations();
            }
            measuring_ = false;
            *allocation_count += process_host_allocations_;
        } else {
            status = descriptor_->process(instance_, &ctx);
        }
        for (unsigned i = 0; i < no; ++i) {
            block.outputs[i].channels = outputs[i].channels;
            block.outputs[i].constant = (outputs[i].flags & WS2_CONSTANT) != 0;
        }
        return status;
    }
    void reset(uint64_t* allocation_count = nullptr) {
        if (allocation_count) *allocation_count = 0;
        if (!descriptor_ || !instance_ || !descriptor_->reset) return;
        if (allocation_count) {
            process_host_allocations_ = 0;
            measuring_ = true;
            {
                allocation_watch::ThreadScope counter;
                descriptor_->reset(instance_);
                *allocation_count = counter.allocations();
            }
            measuring_ = false;
            *allocation_count += process_host_allocations_;
        } else descriptor_->reset(instance_);
    }
    int save(std::vector<uint8_t>& data) {
        if (!descriptor_ || !instance_ || !descriptor_->save_state) return WS2_UNSUPPORTED;
        data.clear(); ws2_writer writer{sizeof(writer), &data, &HostModule::write_state};
        return descriptor_->save_state(instance_, &writer);
    }
    int load(const std::vector<uint8_t>& data) {
        if (!descriptor_ || !instance_ || !descriptor_->load_state) return WS2_UNSUPPORTED;
        Reader state{data.data(), data.size(), 0};
        ws2_reader reader{sizeof(reader), &state, &HostModule::read_state,
                          static_cast<uint32_t>(data.size())};
        return descriptor_->load_state(instance_, &reader);
    }
    void destroy() {
        if (instance_ && descriptor_ && descriptor_->destroy) descriptor_->destroy(instance_);
        instance_ = nullptr;
        for (void* p : allocations_) free_aligned(p);
        allocations_.clear();
    }
};
