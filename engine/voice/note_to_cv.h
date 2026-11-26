// SPDX-License-Identifier: MIT
#pragma once
#include "allocator.h"
#include "wirescape/module2.h"
#include <array>
#include <cmath>
#include <type_traits>
namespace wirescape::voice {
// Single render owner. Source/channel pairs get bounded internal identities so
// the allocator's source-scoped sustain remains independent per MIDI channel.
class NoteToCv {
    struct Source {
        bool used = false;
        uint32_t id = 0;
        int16_t channel = 0;
    };
    std::array<Source, kMaxHeldNotes> sources_{};
    Allocator allocator_;
    struct Anonymous {
        bool used = false;
        uint32_t source = 0;
        int channel = 0, key = 0;
        int32_t id = 0;
        uint64_t order = 0;
        bool retired = false;
    };
    std::array<Anonymous, kMaxHeldNotes> anonymous_{};
    uint32_t serial_ = 0;
    uint64_t activation_ = 0;
    int32_t next_id() noexcept {
        // At most 128 anonymous notes and 16 voices can reserve IDs.
        for (int attempt = 0; attempt < kMaxHeldNotes + kMaxVoices + 1; ++attempt) {
            serial_ = (serial_ + 1) & 0x7fffffffu;
            int32_t id = static_cast<int32_t>(serial_);
            bool used = false;
            for (const auto &a : anonymous_)
                if (a.used && a.id == id) used = true;
            for (int c = 0; c < allocator_.voice_count(); ++c)
                if (allocator_.voice(c).gate && allocator_.voice(c).note_id == id) used = true;
            if (!used) return id;
        }
        return -1;
    }
    int token(uint32_t source, int channel, bool create) noexcept {
        int empty = -1;
        for (int i = 0; i < kMaxHeldNotes; ++i) {
            const auto &s = sources_[i];
            if (s.used && s.id == source && s.channel == channel) return i;
            if (!s.used && empty < 0) empty = i;
        }
        if (!create) return -1;
        if (empty < 0) {
            // Reclaim only between events, after synchronous release emission.
            // Host output queues hold original source IDs, not these tokens.
            std::array<bool, kMaxHeldNotes> reserved{};
            allocator_.visit_sources_in_use([&](uint32_t source) {
                if (source < reserved.size()) reserved[source] = true;
            });
            for (const auto &a : anonymous_)
                if (a.used) reserved[a.source] = true;
            for (int i = 0; i < kMaxHeldNotes; ++i)
                if (!reserved[i]) {
                    empty = i;
                    break;
                }
        }
        if (empty < 0) return -1;
        sources_[empty] = {true, source, static_cast<int16_t>(channel)};
        return empty;
    }
    template <class Emit>
    void changes(const std::array<Voice, kMaxVoices> &before, const ws2_event &cause, Emit emit_event, bool choke) {
        // Releases precede replacement attacks at the same offset.
        for (int c = 0; c < allocator_.voice_count(); ++c) {
            const auto &a = before[c];
            const auto &b = allocator_.voice(c);
            if (a.gate && (!b.gate || a.start_order != b.start_order)) {
                auto out = cause;
                out.type = choke || b.gate ? WS2_NOTE_CHOKE : WS2_NOTE_OFF;
                out.channel = c;
                out.key = a.key;
                out.note_id = a.note_id;
                out.source_id = sources_[a.source_id].id;
                out.value = 0;
                emit_event(out);
            }
        }
        for (int c = 0; c < allocator_.voice_count(); ++c) {
            const auto &a = before[c];
            const auto &b = allocator_.voice(c);
            if (b.gate && (!a.gate || a.start_order != b.start_order)) {
                auto out = cause;
                out.type = WS2_NOTE_ON;
                out.channel = c;
                out.key = b.key;
                out.note_id = b.note_id;
                out.source_id = sources_[b.source_id].id;
                out.value = b.velocity;
                emit_event(out);
            }
        }
    }
    std::array<Voice, kMaxVoices> snapshot() const noexcept {
        std::array<Voice, kMaxVoices> r{};
        for (int c = 0; c < allocator_.voice_count(); ++c) r[c] = allocator_.voice(c);
        return r;
    }

  public:
    Status configure(Config config) noexcept {
        anonymous_ = {};
        serial_ = 0;
        activation_ = 0;
        sources_ = {};
        return allocator_.configure(config);
    }
    template <class Emit>
    Status resize(int max_voices, const ws2_event &cause, Emit emit_event) {
        const int previous = allocator_.voice_count();
        // Grow, mono and no-op do not need a voice snapshot or event emission.
        if (max_voices < 1 || max_voices > kMaxVoices ||
            max_voices >= previous || allocator_.config().mode == Mode::Mono)
            return allocator_.resize(max_voices);
        const auto before = snapshot();
        const auto status = allocator_.resize(max_voices);
        if (status != Status::Ok) return status;
        for (int c = max_voices; c < previous; ++c) {
            const auto &a = before[c];
            if (!a.gate) continue;
            // Keep FIFO tombstones for anonymous activations until their offs,
            // including when the same pitch is played after regrowth.
            for (auto &anon : anonymous_)
                if (anon.used && anon.source == a.source_id && anon.id == a.note_id)
                    anon.retired = true;
            auto out = cause;
            // A source-scoped choke could release retained downstream voices.
            // Emit an individual ordinary release with its old identity.
            out.type = WS2_NOTE_OFF;
            out.channel = c;
            out.key = a.key;
            out.note_id = a.note_id;
            out.source_id = sources_[a.source_id].id;
            out.value = 0;
            emit_event(out);
        }
        return status;
    }
    void reset() noexcept {
        allocator_.reset();
        sources_ = {};
        anonymous_ = {};
        serial_ = 0;
        activation_ = 0;
    }

    // A70a: stopped-owner state only. Every scalar is encoded explicitly;
    // slot positions are significant (FIFO, rotation and source reclamation).
    template<class Writer> int save(Writer w) const {
        const auto u=[&](uint32_t v){return w.u32(v);};
        const auto q=[&](uint64_t v){return u(uint32_t(v))&&u(uint32_t(v>>32));};
        const auto& a=allocator_;
        const auto cfg=a.config_;
        if(!u(1)||!u(cfg.max_voices)||!u(uint32_t(cfg.mode))||
           !u(uint32_t(cfg.mono_priority))||!u(cfg.legato)||
           !u(serial_)||!q(activation_)||!q(a.order_)||!u(a.cursor_))return WS2_CAPACITY;
        for(const auto& s:sources_)
            if(!u(s.used)||!u(s.id)||!u(uint32_t(s.channel)))return WS2_CAPACITY;
        for(const auto& n:anonymous_)
            if(!u(n.used)||!u(n.source)||!u(uint32_t(n.channel))||
               !u(uint32_t(n.key))||!u(uint32_t(n.id))||!q(n.order)||!u(n.retired))
                return WS2_CAPACITY;
        for(const auto& h:a.held_)
            if(!u(h.used)||!u(h.down)||!u(h.note.source_id)||!u(uint32_t(h.note.note_id))||
               !u(uint32_t(h.note.channel))||!u(uint32_t(h.note.key))||
               !w.f32(h.note.velocity)||!q(h.order)||!u(uint32_t(int(h.voice)+1)))
                return WS2_CAPACITY;
        for(const auto& v:a.voices_)
            if(!u(v.assigned)||!u(v.gate)||!u(v.trigger)||!u(v.retrigger)||
               !u(v.source_id)||!u(uint32_t(v.note_id))||!u(uint32_t(v.channel))||
               !u(uint32_t(v.key))||!w.f32(v.pitch)||!w.f32(v.velocity)||
               !w.f32(v.pressure)||!w.f32(v.timbre)||!q(v.start_order))
                return WS2_CAPACITY;
        for(int i=0;i<kMaxSustainSources;++i)
            if(!u(a.sustain_used_[i])||!u(a.sustain_sources_[i]))return WS2_CAPACITY;
        return WS2_OK;
    }
    template<class Reader> int load(Reader r) {
        const auto u=[&](uint32_t& v){return r.u32(v);};
        const auto q=[&](uint64_t& v){uint32_t lo,hi;
            if(!u(lo)||!u(hi))return false;
            v=uint64_t(lo)|(uint64_t(hi)<<32);return true;};
        const auto flag=[&](bool& v){uint32_t n;
            if(!u(n)||n>1)return false;
            v=n!=0;return true;};
        const auto bounded=[&](auto& v,uint32_t max){uint32_t n;
            if(!u(n)||n>max)return false;
            v=static_cast<std::decay_t<decltype(v)>>(n);return true;};
        const auto id=[&](int32_t& v){uint32_t n;
            if(!u(n)||(n>0x7fffffffu&&n!=UINT32_MAX))return false;
            v=n==UINT32_MAX?-1:static_cast<int32_t>(n);return true;};
        const auto unit=[&](float& v){return r.f32(v)&&std::isfinite(v)&&v>=0.f&&v<=1.f;};
        NoteToCv next;
        auto& a=next.allocator_;
        const auto cfg=allocator_.config_;
        uint32_t ver,count,mode,priority,legato;
        if(!u(ver))return WS2_INVALID;
        if(ver!=1)return WS2_UNSUPPORTED;
        if(!u(count)||count!=cfg.max_voices||!u(mode)||mode!=uint32_t(cfg.mode)||
           !u(priority)||priority!=uint32_t(cfg.mono_priority)||!u(legato)||legato!=uint32_t(cfg.legato))
            return WS2_INVALID;
        a.config_=cfg;
        const int voices=a.voice_count();
        if(!bounded(next.serial_,0x7fffffffu)||!q(next.activation_)||
           !q(a.order_)||!bounded(a.cursor_,uint32_t(voices-1)))return WS2_INVALID;
        for(auto& s:next.sources_){
            if(!flag(s.used)||!u(s.id)||!bounded(s.channel,15))return WS2_INVALID;
            if(!s.used&&(s.id||s.channel))return WS2_INVALID;
        }
        for(int i=0;i<kMaxHeldNotes;++i)if(next.sources_[i].used)
            for(int j=0;j<i;++j)if(next.sources_[j].used&&
                next.sources_[j].id==next.sources_[i].id&&
                next.sources_[j].channel==next.sources_[i].channel)return WS2_INVALID;
        const auto source=[&](uint32_t t,int c){return t<kMaxHeldNotes&&
            next.sources_[t].used&&next.sources_[t].channel==c;};
        for(auto& n:next.anonymous_){
            if(!flag(n.used)||!bounded(n.source,kMaxHeldNotes-1)||!bounded(n.channel,15)||
               !bounded(n.key,127)||!id(n.id)||!q(n.order)||!flag(n.retired))return WS2_INVALID;
            if(n.used&&(!source(n.source,n.channel)||n.id<0||!n.order||n.order>next.activation_))
                return WS2_INVALID;
            if(!n.used&&(n.source||n.channel||n.key||n.id||n.order||n.retired))return WS2_INVALID;
        }
        for(int i=0;i<kMaxHeldNotes;++i)if(next.anonymous_[i].used)
            for(int j=0;j<i;++j)if(next.anonymous_[j].used&&
                (next.anonymous_[j].id==next.anonymous_[i].id||
                 next.anonymous_[j].order==next.anonymous_[i].order))return WS2_INVALID;
        for(auto& h:a.held_){
            uint32_t index;
            if(!flag(h.used)||!flag(h.down)||!bounded(h.note.source_id,kMaxHeldNotes-1)||
               !id(h.note.note_id)||!bounded(h.note.channel,15)||!bounded(h.note.key,127)||
               !unit(h.note.velocity)||!q(h.order)||!u(index)||index>uint32_t(voices))return WS2_INVALID;
            h.voice=static_cast<int8_t>(int(index)-1);
            if(h.used&&(!source(h.note.source_id,h.note.channel)||h.note.note_id<0||
               !h.order||h.order>a.order_||(cfg.mode!=Mode::Mono&&h.voice<0)))return WS2_INVALID;
            if(!h.used&&(h.down||h.voice!=-1||h.order||h.note.source_id||
                h.note.note_id!=-1||h.note.channel||h.note.key!=60||h.note.velocity!=1.f))
                return WS2_INVALID;
        }
        for(int i=0;i<kMaxHeldNotes;++i)if(a.held_[i].used)
            for(int j=0;j<i;++j)if(a.held_[j].used&&
                (a.held_[j].order==a.held_[i].order||
                 (a.held_[j].note.source_id==a.held_[i].note.source_id&&
                  a.held_[j].note.note_id==a.held_[i].note.note_id)))return WS2_INVALID;
        for(int i=0;i<kMaxVoices;++i){
            auto& v=a.voices_[i];
            if(!flag(v.assigned)||!flag(v.gate)||!flag(v.trigger)||!flag(v.retrigger)||
               !bounded(v.source_id,kMaxHeldNotes-1)||!id(v.note_id)||!bounded(v.channel,15)||
               !bounded(v.key,127)||!r.f32(v.pitch)||!std::isfinite(v.pitch)||
               !unit(v.velocity)||!unit(v.pressure)||!unit(v.timbre)||!q(v.start_order))return WS2_INVALID;
            if((v.gate&&!v.assigned)||(v.trigger&&!v.gate)||(v.retrigger&&!v.trigger)||
               (i>=voices&&v.assigned)||
               (v.assigned&&(!v.start_order||v.start_order>a.order_||v.note_id<0||
                v.pitch!=(static_cast<float>(v.key)-60.f)/12.f)))return WS2_INVALID;
            if(!v.assigned&&(v.start_order||v.gate||v.source_id||v.note_id!=-1||
                v.channel||v.key!=60||v.pitch!=0.f||v.velocity!=0.f||
                v.pressure!=0.f||v.timbre!=0.f))return WS2_INVALID;
            int matches=0;
            for(const auto& h:a.held_)if(h.used&&h.voice==i){
                if(!v.gate||h.order!=v.start_order||h.note.source_id!=v.source_id||
                   h.note.note_id!=v.note_id||h.note.channel!=v.channel||h.note.key!=v.key||
                   h.note.velocity!=v.velocity)return WS2_INVALID;
                ++matches;
            }
            if(matches!=(v.gate?1:0)||(v.gate&&!source(v.source_id,v.channel)))return WS2_INVALID;
        }
        for(int i=0;i<kMaxSustainSources;++i){
            if(!flag(a.sustain_used_[i])||!bounded(a.sustain_sources_[i],kMaxHeldNotes-1))
                return WS2_INVALID;
            if(a.sustain_used_[i]){
                if(!next.sources_[a.sustain_sources_[i]].used)return WS2_INVALID;
                for(int j=0;j<i;++j)if(a.sustain_used_[j]&&
                    a.sustain_sources_[j]==a.sustain_sources_[i])return WS2_INVALID;
            }
        }
        for(const auto& h:a.held_)if(h.used&&!h.down&&!a.sustained(h.note.source_id))return WS2_INVALID;
        if(cfg.mode==Mode::Mono){
            const int selected=a.choose_mono();
            if((selected>=0)!=a.voices_[0].gate||
               (selected>=0&&a.held_[selected].voice!=0))return WS2_INVALID;
        }
        *this=next;
        return WS2_OK;
    }

    uint32_t original_source(uint32_t token) const noexcept {
        return token < sources_.size() ? sources_[token].id : UINT32_MAX;
    }
    Allocator &allocator() noexcept { return allocator_; }
    const Allocator &allocator() const noexcept { return allocator_; }
    template <class Emit> void sustain(uint32_t source, int channel, bool down, const ws2_event &e, Emit emit_event) {
        int t = token(source, channel, down);
        if (t < 0) return;
        auto before = snapshot();
        allocator_.sustain(static_cast<uint32_t>(t), down);
        changes(before, e, emit_event, false);
    }
    template <class Emit> void release_channel(uint32_t source, int channel, const ws2_event &e, Emit emit_event) {
        int t = token(source, channel, false);
        if (t < 0) return;
        auto before = snapshot();
        allocator_.release_all_from_source(static_cast<uint32_t>(t));
        changes(before, e, emit_event, true);
        for (auto &a : anonymous_)
            if (a.used && a.source == static_cast<uint32_t>(t)) a = {};
    }
    template <class Emit> void release_all(uint32_t source, const ws2_event &e, Emit emit_event) {
        auto before = snapshot();
        if (source == UINT32_MAX) allocator_.reset();
        else
            for (int t = 0; t < kMaxHeldNotes; ++t)
                if (sources_[t].used && sources_[t].id == source) allocator_.release_all_from_source(t);
        changes(before, e, emit_event, true);
        for (auto &a : anonymous_)
            if (a.used && (source == UINT32_MAX || sources_[a.source].id == source)) a = {};
    }
    template <class Emit> void event(const ws2_event &e, Emit emit_event) {
        if (e.type == WS2_NOTE_CHOKE) {
            release_all(e.source_id, e, emit_event);
            return;
        }
        int channel = e.channel < 0 ? 0 : e.channel;
        if (channel > 15) return;
        int t = token(e.source_id, channel, e.type == WS2_NOTE_ON);
        if (t < 0) return;
        Note n{static_cast<uint32_t>(t), e.note_id, static_cast<int16_t>(channel), static_cast<int16_t>(e.key),
               e.value};
        auto before = snapshot();
        if (e.type == WS2_NOTE_ON) {
            int slot = -1;
            if (n.note_id < 0) {
                for (int i = 0; i < kMaxHeldNotes; ++i)
                    if (!anonymous_[i].used) {
                        slot = i;
                        break;
                    }
                if (slot < 0) return;
                n.note_id = next_id();
                if (n.note_id < 0) return;
            }
            auto result = allocator_.note_on(n);
            if (result.status == Status::Ok && slot >= 0)
                anonymous_[slot] = {true, n.source_id, channel, n.key, n.note_id, ++activation_};
            if (result.status == Status::Ok && slot < 0)
                for (auto &a : anonymous_)
                    if (a.used && a.source == n.source_id && a.id == n.note_id) a.retired = true;
        } else if (e.type == WS2_NOTE_OFF) {
            int slot = -1;
            if (n.note_id < 0) {
                for (int i = 0; i < kMaxHeldNotes; ++i) {
                    const auto &a = anonymous_[i];
                    if (a.used && a.source == n.source_id && a.channel == channel && a.key == n.key &&
                        (slot < 0 || a.order < anonymous_[slot].order))
                        slot = i;
                }
                if (slot < 0) return;
                n.note_id = anonymous_[slot].id;
                bool retired = anonymous_[slot].retired;
                anonymous_[slot] = {};
                if (retired) return;
            }
            // A stolen activation remains in our FIFO until its own Note Off.
            // Its allocator record may be gone; that off must not close its replacement.
            allocator_.note_off(n);
        } else if (e.type == WS2_NOTE_EXPRESSION) {
            for (int c = 0; c < allocator_.voice_count(); ++c) {
                const auto &v = allocator_.voice(c);
                if (v.source_id == n.source_id &&
                    ((n.note_id >= 0 && n.note_id == v.note_id) || (n.note_id < 0 && n.key == v.key))) {
                    Note addressed = n;
                    addressed.note_id = v.note_id;
                    allocator_.expression(addressed, e.expression == WS2_EX_PRESSURE ? e.value : v.pressure,
                                          e.expression == WS2_EX_TIMBRE ? e.value : v.timbre);
                    auto out = e;
                    out.channel = c;
                    out.note_id = v.note_id;
                    emit_event(out);
                    if (n.note_id >= 0) break;
                }
            }
        }
        changes(before, e, emit_event, false);
    }
};
} // namespace wirescape::voice
