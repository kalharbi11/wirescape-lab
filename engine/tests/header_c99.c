/* SPDX-License-Identifier: MIT */
#include "wirescape/module2.h"
#include <stddef.h>
typedef char signal_header_at_zero[(offsetof(ws2_signal,struct_size)==0)?1:-1];
typedef char event_header_at_zero[(offsetof(ws2_event,struct_size)==0)?1:-1];
#define AFTER(T, A, B) typedef char T##_##B##_after_##A[(offsetof(T,B)>=offsetof(T,A)+sizeof(((T*)0)->A))?1:-1]
AFTER(ws2_process,transport,data_count);
AFTER(ws2_process,data_count,data);
AFTER(ws2_descriptor,latency_frames,data_slot_count);
AFTER(ws2_descriptor,data_slot_count,data_slots);
AFTER(ws2_descriptor,data_slots,adopt);
AFTER(ws2_descriptor,adopt,replace_fade_ms);
int main(void) {
    ws2_signal s={0}; ws2_event e={0}; ws2_process p={0}; ws2_descriptor d={0};
    s.struct_size=sizeof(s); e.struct_size=sizeof(e);
    p.struct_size=offsetof(ws2_process,data_count);
    d.struct_size=offsetof(ws2_descriptor,data_slot_count);
    return WS_ABI2_VERSION==2 && s.struct_size>0 && e.struct_size>0 &&
           p.struct_size<sizeof(p) && d.struct_size<sizeof(d) &&
           p.data_count==0 && p.data==NULL && d.data_slot_count==0 &&
           d.data_slots==NULL && d.adopt==NULL && d.replace_fade_ms==0 ? 0 : 1;
}
