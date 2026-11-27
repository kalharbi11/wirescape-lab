// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../port_state.h"
namespace ws2ports {
struct Output {
 static constexpr ws::Info info{"essentials.output","Output",2};
 static constexpr std::array inputs{ws::port("audio", "Audio", WS2_AUDIO, WS2_SUM)};
 static constexpr std::array outputs{ws::port("audio", "Audio", WS2_AUDIO)};
 static constexpr std::array<ws2_param,0>params{};
 void prepare(const ws::Setup&){}void reset(){}
 // A119: hoist loop-invariant handles; same values, same order.
 void process(ws::Block&b){const auto in=b.in(0);auto out=b.out(0);const uint32_t channels=b.channels();out.set_channels(channels);const bool constant=in.constant();out.mark_constant(constant);const uint32_t n=constant?1u:b.frames();for(uint32_t c=0;c<channels;++c){const ws::Channel src=in.ch(c);float*dst=out.ch(c);for(uint32_t i=0;i<n;++i)dst[i]=src[i];}}
 int save_state(ws::Writer w){return w.u32(1)?WS2_OK:WS2_CAPACITY;}
 int load_state(ws::Reader r){uint32_t version;if(!r.u32(version))return WS2_INVALID;return version==1?WS2_OK:WS2_UNSUPPORTED;}
};
}
