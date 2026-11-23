// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "../../modules/adsr/dsp.h"
#include "../../modules/blend/dsp.h"
#include "../../modules/chaos_lite/dsp.h"
#include "../../modules/chord/dsp.h"
#include "../../modules/clock/dsp.h"
#include "../../modules/delay/dsp.h"
#include "../../modules/function_envelope/dsp.h"
#include "../../modules/groove/dsp.h"
#include "../../modules/host_keyboard/dsp.h"
#include "../../modules/ladder/dsp.h"
#include "../../modules/lfo/dsp.h"
#include "../../modules/macro_oscillator/dsp.h"
#include "../../modules/midi_cc_to_cv/dsp.h"
#include "../../modules/midi_in/dsp.h"
#include "../../modules/midi_to_cv/dsp.h"
#include "../../modules/mixer/dsp.h"
#include "../../modules/monitor/dsp.h"
#include "../../modules/noise/dsp.h"
#include "../../modules/notes_to_cv/dsp.h"
#include "../../modules/cv_to_notes/dsp.h"
#include "../../modules/osc_in/dsp.h"
#include "../../modules/osc_out/dsp.h"
#include "../../modules/output/dsp.h"
#include "../../modules/quad_vca/dsp.h"
#include "../../modules/quantizer/dsp.h"
#include "../../modules/resonator/dsp.h"
#include "../../modules/reverb/dsp.h"
#include "../../modules/scale_offset/dsp.h"
#include "../../modules/slew/dsp.h"
#include "../../modules/spectral/dsp.h"
#include "../../modules/vca/dsp.h"
#include "../../modules/vcf/dsp.h"
#include "../../modules/vco/dsp.h"
#include "../../sdk/examples/random_source/dsp.h"
#include "../../sdk/examples/step_sequencer/dsp.h"
#include <vector>
namespace wirescape::app {
inline const std::vector<const ws2_descriptor *> &builtin_modules() {
    static const std::vector<const ws2_descriptor *> modules{
#define WS_APP_MODULE(Class) ws::Module<Class>::descriptor(),
#include "module_catalog.inc"
#undef WS_APP_MODULE
    };
    return modules;
}
} // namespace wirescape::app
