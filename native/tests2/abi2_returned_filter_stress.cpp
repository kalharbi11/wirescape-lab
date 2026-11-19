// SPDX-License-Identifier: GPL-3.0-only
// Execute the original stress functions unchanged against the ABI2 ladder.
#include "returned_filter_cases.h"
#include "module_loader.h"
#include "wirescape_sdk.h"
#include "frozen_reference.h"
std::array<uint32_t, 3> Processor::frozen_parameter_ids{};
int main(int argc,char**argv){try{require(argc==2,"expected module directory");ModuleLoader loader(argv[1]);stress_descriptor=loader.abi2("ladder");const auto frozen=abi1_frozen_descriptor("ladder");
 require(frozen.id==stress_descriptor->id,"frozen ladder module ID differs from ABI2");
 require(frozen.input_count==1&&frozen.output_count==1&&frozen.parameter_count==3,
         "frozen ABI1 ladder descriptor shape differs");
 require(stress_descriptor->input_count == frozen.input_count &&
         stress_descriptor->output_count == frozen.output_count &&
         stress_descriptor->param_count == frozen.parameter_count,
         "native ladder descriptor shape differs from frozen ABI1");
 for(uint32_t i=0;i<3;++i) {
  Processor::frozen_parameter_ids[i] = frozen.parameters[i].legacy_index;
  require(stress_descriptor->params[i].id != nullptr,
          "native ladder parameter ID missing");
 }
 for(double rate:{44100.,48000.,96000.}){impulse_cases(stress_descriptor,false,rate);modulation_case(stress_descriptor,false,rate);}
 std::puts("PASS unchanged returned_filter_stress cases against ABI2 ladder");return 0;}catch(const std::exception&e){std::fprintf(stderr,"FAIL ABI2 returned filter stress: %s\n",e.what());return 1;}}
