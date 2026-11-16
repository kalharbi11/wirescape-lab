<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1.1 Lab CI durations — 2026-11-16

- **Date (America/New_York):** 2026-11-16.
- **Examined implementation base:** `55b7a1c0d2072b4ef00c393e5e13bd05ade3ef80` (live `main` when issue #95 was claimed).
- **Completed baseline:** [Lab CI push run 43837588432](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432) at commit `320576c322c81b8feae76f18ff0cb58ba1f6feb9`; method and step timing source: [`ci_durations_2026-11-16.md`](ci_durations_2026-11-16.md). The one intervening commit to branch base did not modify native CMake test definitions, Playwright configs or test files (compare `320576c...55b7a1c`).
- **Own PR full-run source:** pending PR creation and hosted CI on `task/95-ci1-feedback`. All PR duration/core-count cells marked `pending` are **unobserved**, not estimates.
- **Measurement method for own PR when complete:** each job and named step uses `completed_at - started_at`; sum of job durations is runner-minutes; run time uses `updated_at - run_started_at` including runner wait; minutes to two decimals. This matches the baseline method.

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

| Suite | Base discovered | Base completion | Own PR discovery/completion |
| --- | ---: | --- | --- |
| native linux-x64 | 114 | 114 passed | pending |
| native linux-arm64 | 114 | 114 passed | pending |
| native windows-x64 | 114 | 114 passed | pending |
| sanitizers `-R abi2` | 78 | 78 passed | pending |
| Studio Playwright | 344 | 343 passed; one existing skipped test | pending sum of shards 1–3 |
| Desktop Playwright | 24 | 22 passed; two existing skipped tests | pending, unchanged desktop CI job |

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

## Own PR full-run durations (unverified until an actual hosted run completes)

| Job | Printed runner cores | Job min | Build step min | Test step min | Other step min |
| --- | ---: | ---: | ---: | ---: | ---: |
| changed-scope | n/a | pending | pending | pending | pending |
| foundation | n/a | pending | pending | pending | pending |
| native linux-x64 | pending | pending | pending | pending | pending |
| native linux-arm64 | pending | pending | pending | pending | pending |
| native windows-x64 | pending | pending | pending | pending | pending |
| sanitizers | pending | pending | pending | pending | pending |
| studio shard 1/3 | n/a | pending | pending | pending | pending |
| studio shard 2/3 | n/a | pending | pending | pending | pending |
| studio shard 3/3 | n/a | pending | pending | pending | pending |
| desktop | n/a | pending | pending | pending | pending |
| **Sum runner-minutes** | | **pending** | | | |

- **Own PR full-run URL:** pending PR run.
- **Own PR longest job:** pending.
- **Own PR elapsed time including runner wait:** pending.
- **CI1 r1 estimate (not a pass threshold):** longest job approximately 5 minutes. No PR speedup or speed regression is asserted before hosted evidence.
- **Baseline notes:** the original 9.42-minute Studio job includes the linked 24-test desktop suite, which the separate 2.02-minute desktop job also ran. The PR configuration removes that duplicate link while preserving the desktop job.
