<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1.1 Lab CI durations — 2026-11-16

- **Date (America/New_York):** 2026-11-16.
- **Examined implementation base:** `55b7a1c0d2072b4ef00c393e5e13bd05ade3ef80` (live `main` when issue #95 was claimed).
- **Completed baseline:** [Lab CI push run 43837588432](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432) at commit `320576c322c81b8feae76f18ff0cb58ba1f6feb9`; method and step timing source: [`ci_durations_2026-11-16.md`](ci_durations_2026-11-16.md). The one intervening commit to branch base did not modify native CMake test definitions, Playwright configs or test files (compare `320576c...55b7a1c`).
- **Own PR full-run source:** [Lab CI PR run 43847804664](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664), event `pull_request`, attempt 1, completed `success`, exact implementation head `aa016e81bf421cd7b1b6f1093eddfe8bebe19d8b`, branch `task/95-ci1-feedback`, issue #95 / PR #96. Run started `2026-11-16T10:19:29Z`, updated `2026-11-16T10:40:02Z` (UTC). This is the first complete code-head PR run, not a baseline push run.
- **Measurement method for own PR:** GitHub Actions run and jobs REST `started_at` / `completed_at` timestamps at [run 43847804664 jobs](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664); each job/step duration is completed minus started; summed exact job seconds, then rounded to two decimal minutes, gives runner-minutes. Run wall time uses `updated_at - run_started_at` (includes hosted queue delay). Values are observed, not a five-minute estimate; table build/prep/test are explicitly named step durations, with remainder in other. Core counts are literal `Runner cores: 4` lines in each corresponding current-head native/sanitizer job log. Same time method as baseline.

## Baseline hosted durations — completed push run (not own PR)

| Job | Runner | Job min | Build step min | Test step min | Other step min |
| --- | --- | ---: | ---: | ---: | ---: |
| sanitizers | `ubuntu-latest` | 9.48 | 8.27 | 1.07 | 0.14 |
| studio (Playwright + linked desktop) | `ubuntu-latest` | 9.42 | 0.58 | 8.68 | 0.16 |
| windows-x64 | `windows-latest` | 7.00 | 4.60 (+0.45 pinned PortAudio) | 1.42 | 0.53 |
| linux-arm64 | `ubuntu-24.04-arm` | 4.68 | 3.57 | 0.93 | 0.18 |
| linux-x64 | `ubuntu-latest` | 3.88 | 2.88 | 0.88 | 0.12 |
| desktop | `ubuntu-latest` | 2.02 | 0.25 | 1.60 | 0.17 |
| foundation | `ubuntu-latest` | 0.73 | — | 0.43 | 0.30 |
| **Sum** | | **37.21** | | | |

## K1 baseline test counts and exact CTest names

| Suite | Base discovered | Base completion | Own PR exact-head discovery/completion |
| --- | ---: | --- | --- |
| native linux-x64 | 114 | 114 passed | 114/114 passed; `ctest -N` exact 114-name/order match |
| native linux-arm64 | 114 | 114 passed | 114/114 passed; `ctest -N` exact 114-name/order match |
| native windows-x64 | 114 | 114 passed | 114/114 passed; `ctest -N` exact 114-name/order match |
| sanitizers `-R abi2` | 78 | 78 passed | 78/78 passed; `ctest -N -R abi2` exact 78-name/order match |
| Studio Playwright | 344 | 343 passed; one existing skipped test | shard lists 128 + 103 + 113 = **344**, results 127 passed/1 skipped + 103 passed + 113 passed = **343 passed/1 existing skipped** |
| Desktop Playwright | 24 | 22 passed; two existing skipped tests | **24 discovered, 22 passed/2 existing skipped**, unchanged desktop job |

**K1 evidence:** [native Linux x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639415), [ARM64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639488), [Windows](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639494), [sanitizers](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639324), [Studio shard 1](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639522), [shard 2](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639475), [shard 3](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639453), and [desktop](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639371). Each CTest inventory was parsed against the fully named base list printed below: all four comparisons are position-by-position identical. Studio `playwright test --list --shard=N/3` totals and test completion from the three job logs. Foundation ran 222 Python unit tests with four pre-existing skips (success).

**Exact native CTest names** as emitted by [Linux x64 baseline job](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432/job/133197976662), representative of the same 114-name baseline on all three native runners:

```text
native_engine_tests
native_module_tests
native_scale_offset_tests
native_provider_bridge_tests
native_lfo_tests
essentials_noise_tests
essentials_slew_tests
essentials_function_envelope_tests
essentials_clock_tests
essentials_vcf_tests
essentials_ladder_tests
returned_filter_stress
abi2_osc_host_service_tests
abi2_osc_graph_ingress_tests
abi2_sidecar_protocol_tests
sidecar_golden
abi2_sidecar_unit_tests
abi2_sidecar_audio_recovery_tests
groove_observation_tests
groove_runtime_tests
abi2_runtime_patch_tests
qt_free_patch_coverage_tests
abi2_builtin_source_tests
ui_patch_conformance
ui_catalogue_sync
abi2_offline_play
class_demo_patches
class_demo_cc_depth
runtime_module_config_tests
golden_render_hashes
golden_event_stream
golden_serialization
abi2_header_c99
abi2_sdk_tests
abi2_sdk_scalar_tests
abi2_voice_tests
abi2_note_identity_tests
abi2_template_tests
abi2_engine_tests
abi2_module_tests
abi2_scalar_ports
abi2_portable_ports
abi2_benchmark
abi2_benchmark_64
abi2_benchmark_128
abi2_benchmark_256
abi2_integration_tests
abi2_guide_tests
abi2_example_random_source_tests
abi2_example_step_sequencer_tests
abi2_osc_codec_tests
abi2_osc_in_tests
abi2_osc_out_tests
abi2_monitor_tests
abi2_panic_stress
abi2_feedback_tests
abi2_banned_includes
abi2_soak_smoke
abi2_soak_stats_tests
abi2_soak_cli
abi2_port_behavior_tests
abi2_staged_tests
abi2_live_replan_tests
abi2_clock_tests
abi2_function_envelope_tests
abi2_ladder_tests
abi2_mixer_tests
abi2_noise_tests
abi2_output_tests
abi2_scale_offset_tests
abi2_slew_tests
abi2_returned_filter_stress
abi2_module_cpu_probe_output_tests
abi2_module_cpu_probe_smoke
abi2_module_cpu_probe_tiny_64
abi2_module_cpu_probe_tiny_128
abi2_module_cpu_probe_tiny_256
abi2_module_cpu_probe_stress_smoke
abi2_module_cpu_probe_poly_smoke
abi2_module_cpu_probe_spectral_smoke
abi2_module_cpu_probe_unit
abi2_host_keyboard_tests
qt_free_stream_lifecycle_tests
abi2_audio_callback_live_midi_tests
abi2_midi_release_tests
midi_host_tests
abi2_midi_live_host_tests
app_engine_tests
app_document_soak
abi2_midi_backend_gate_tests
abi2_midi_service_tests
abi2_midi_in_tests
abi2_midi_to_cv_tests
abi2_midi_cc_to_cv_tests
abi2_macro_oscillator_tests
abi2_macro_reference_guards
abi2_macro_reference
abi2_chaos_lite_tests
abi2_blend_tests
abi2_resonator_tests
abi2_spectral_tests
abi2_delay_tests
abi2_reverb_tests
abi2_quantizer_tests
abi2_quad_vca_tests
abi2_notes_to_cv_tests
abi2_chord_tests
render_evidence_adsr_notes
render_evidence_frequency_step
render_evidence_blend_selection
render_evidence_library_smoke
render_evidence_late_negative
render_evidence_negative
capture_offline_selftests
```

**Exact sanitizer ABI2 CTest names** as emitted by [baseline sanitizer job](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432/job/133197976726):

```text
abi2_osc_host_service_tests
abi2_osc_graph_ingress_tests
abi2_sidecar_protocol_tests
abi2_sidecar_unit_tests
abi2_sidecar_audio_recovery_tests
abi2_runtime_patch_tests
abi2_builtin_source_tests
abi2_offline_play
abi2_header_c99
abi2_sdk_tests
abi2_sdk_scalar_tests
abi2_voice_tests
abi2_note_identity_tests
abi2_template_tests
abi2_engine_tests
abi2_module_tests
abi2_scalar_ports
abi2_portable_ports
abi2_benchmark
abi2_benchmark_64
abi2_benchmark_128
abi2_benchmark_256
abi2_integration_tests
abi2_guide_tests
abi2_example_random_source_tests
abi2_example_step_sequencer_tests
abi2_osc_codec_tests
abi2_osc_in_tests
abi2_osc_out_tests
abi2_monitor_tests
abi2_panic_stress
abi2_feedback_tests
abi2_banned_includes
abi2_soak_smoke
abi2_soak_stats_tests
abi2_soak_cli
abi2_port_behavior_tests
abi2_staged_tests
abi2_live_replan_tests
abi2_clock_tests
abi2_function_envelope_tests
abi2_ladder_tests
abi2_mixer_tests
abi2_noise_tests
abi2_output_tests
abi2_scale_offset_tests
abi2_slew_tests
abi2_returned_filter_stress
abi2_module_cpu_probe_output_tests
abi2_module_cpu_probe_smoke
abi2_module_cpu_probe_tiny_64
abi2_module_cpu_probe_tiny_128
abi2_module_cpu_probe_tiny_256
abi2_module_cpu_probe_stress_smoke
abi2_module_cpu_probe_poly_smoke
abi2_module_cpu_probe_spectral_smoke
abi2_module_cpu_probe_unit
abi2_host_keyboard_tests
abi2_audio_callback_live_midi_tests
abi2_midi_release_tests
abi2_midi_live_host_tests
abi2_midi_backend_gate_tests
abi2_midi_service_tests
abi2_midi_in_tests
abi2_midi_to_cv_tests
abi2_midi_cc_to_cv_tests
abi2_macro_oscillator_tests
abi2_macro_reference_guards
abi2_chaos_lite_tests
abi2_blend_tests
abi2_resonator_tests
abi2_spectral_tests
abi2_delay_tests
abi2_reverb_tests
abi2_quantizer_tests
abi2_quad_vca_tests
abi2_notes_to_cv_tests
abi2_chord_tests
```

## Own PR full-run durations — completed exact implementation head

- **Run:** [Lab CI #43847804664](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664), `pull_request`, attempt 1, implementation HEAD `aa016e81bf421cd7b1b6f1093eddfe8bebe19d8b`, conclusion **success**, 10/10 jobs successful (including all three Studio shards).
- **Job and step timing:** GitHub Actions REST UTC timestamp differences; rounded minutes; build/prep means the separately identified principal build or install step. For Windows, pinned PortAudio duration is shown in parentheses alongside the native build; `other` is the remainder of job time (not a measured extra build stage).

| Job | Printed runner cores | Job min | Build/prep step min | Test step min | Other step min |
| --- | ---: | ---: | ---: | ---: | ---: |
| [changed-scope](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133235861409) | n/a | 0.08 | — | — | 0.08 |
| [foundation](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133235861173) | n/a | 0.47 | — | 0.35 | 0.12 |
| [linux-x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639415) | 4 | 3.32 | 2.27 | 0.88 | 0.17 |
| [linux-arm64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639488) | 4 | 2.98 | 1.87 | 0.93 | 0.18 |
| [windows-x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639494) | 4 | 4.57 | 2.77 (+0.35 pinned PortAudio) | 1.00 | 0.45 |
| [sanitizers](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639324) | 4 | 7.30 | 6.17 | 1.00 | 0.13 |
| [studio shard 1/3](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639522) | n/a | 2.20 | 0.30 | 1.70 | 0.20 |
| [studio shard 2/3](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639475) | n/a | 2.82 | 0.48 | 2.07 | 0.27 |
| [studio shard 3/3](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639453) | n/a | 3.63 | 0.35 | 3.10 | 0.18 |
| [desktop](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664/job/133236639371) | n/a | 1.75 | 0.08 | 1.48 | 0.18 |
| **Sum runner-minutes** | | **29.12** | | | |

- **Own PR longest job:** `sanitizers`, **7.30 min** (baseline longest `sanitizers` 9.48 min; decrease **2.18 min**).
- **Own PR runner-minutes:** **29.12**, compared with prior push baseline **37.21** (difference **-8.09** runner-minutes; distinct push/PR provenance).
- **Own PR elapsed including scheduling delay:** **20.55 min**, `2026-11-16T10:19:29Z` to `2026-11-16T10:40:02Z` UTC; separate from longest job duration. The wall time is not the longest-job speed metric.
- **Printed runner cores:** native Linux x64 **4**, Linux ARM64 **4**, Windows x64 **4**, sanitizers Ubuntu **4**; each confirmed in the corresponding job logs. No two-core Linux runner condition triggered.
- **K2/K5:** original scope-limited implementation did not alter pre-existing test definitions/configs, sanitizer flags, retries, timeouts, or worker count. This fact-only evidence update modifies no executable code.
- **K3/K4:** source/workflow conditions cover full push-to-main/manual execution and fail-closed PR scope, while foundation remains always-running. These other event types were **not hosted-tested on this PR**. The pre-classifier K4 search results and directory reads are preserved in PR #96; no new scan or change to scope rules was made in this evidence-only update.
- **CI1 r1 estimate:** about 5 minutes for longest job, expressly **not** an acceptance threshold; observed longest job is 7.30 min. Sanitizers remain the longest; compiler-cache question belongs to the delivery lead, not this task.
- **Exact-head note:** this completed run proves the implementation state at `aa016e81bf421cd7b1b6f1093eddfe8bebe19d8b`. Updating this facts file creates a newer branch SHA; the new exact-head automatic CI must be checked by the lead at the next event/heartbeat. Do not report the earlier run as a pass on the new SHA.
