<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1.3 — PR Lab CI job-level queue and sanitizer-cache facts

- **Date (America/New_York):** 2026-11-16
- **Inspection:** fixed 20 most-recent Lab CI `pull_request` runs at November 16, 2026 metadata snapshot; see run IDs below
- **Repository:** `kalharbi11/wirescape-lab`
- **Preparation source code pin:** `main` `042454de51a739ed4cf39324baa07028c42acc9f` (`ci.yml` blob `b85b08283d0cdf8ff4ed4f71f304577ad4e07647`). This is not a benchmark run head.
- **Source endpoints:** `GET /repos/kalharbi11/wirescape-lab/actions/runs?event=pull_request&per_page=100` filtered to workflow name `Lab CI`, and `GET /repos/kalharbi11/wirescape-lab/actions/runs/{run_id}/jobs?per_page=100` for the selected runs; second attempt checked using `GET /repos/kalharbi11/wirescape-lab/actions/runs/43914680092/attempts/2/jobs?per_page=100`.
- **Fields:** run `id`, `head_sha`, `created_at`, `run_started_at`, `status`, `conclusion`; job `id`, `name`, `created_at`, `started_at`, `completed_at`, `status`, `conclusion`.
- **Calculation:** valid non-skipped job queue seconds = `job.started_at` minus `job.created_at`; job duration = `job.completed_at` minus `job.started_at`; negative queue and skipped jobs yield null (not zero). Run creation is never substituted for job creation.

## Fixed run list

| Run ID | Head SHA | Run created UTC | Run start UTC | Status observed initially / conclusion | Job count |
|---|---|---|---|---|---:|
| 43916678348 | `e00062fffefbc72d37533f12e960a0b39897bae9` | 2026-11-16T17:16:43Z | 2026-11-16T17:16:43Z | completed / success | 7 |
| 43916214352 | `aeeecb0e9419ee1a05cd296fd29617d748def586` | 2026-11-16T17:14:09Z | 2026-11-16T17:14:09Z | completed / success | 11 |
| 43914680092 | `9bc7eebc87ce473782ac2a17ded200eddb374583` | 2026-11-16T17:05:44Z | 2026-11-16T17:22:47Z | in_progress / null | 11 |
| 43912720275 | `6e7376e62dbd75007fc93a8989ce48571f20fe4d` | 2026-11-16T16:54:59Z | 2026-11-16T16:54:59Z | completed / success | 11 |
| 43909707167 | `2918781feedda70f6f3294d023412a05bad90d88` | 2026-11-16T16:38:20Z | 2026-11-16T16:38:20Z | completed / success | 11 |
| 43904392596 | `e66d1ffdb1a6cc42bea7a074ca240f218377838e` | 2026-11-16T16:09:41Z | 2026-11-16T16:09:41Z | completed / success | 11 |
| 43904305918 | `b35e5ee571a33178e5083d8bc3ecad6bfe298ac0` | 2026-11-16T16:09:13Z | 2026-11-16T16:09:13Z | completed / cancelled | 0 |
| 43903784936 | `8cb7d0de1c625ea1f4cc26dff230dbe358e11283` | 2026-11-16T16:06:27Z | 2026-11-16T16:06:27Z | completed / cancelled | 0 |
| 43903466106 | `5edb49a7bcb479d94da1ba94c1594e049591c23f` | 2026-11-16T16:04:46Z | 2026-11-16T16:04:46Z | completed / cancelled | 0 |
| 43903218805 | `bc8b1171097950b5b0183ac42233f850b928292e` | 2026-11-16T16:03:27Z | 2026-11-16T16:03:27Z | completed / cancelled | 0 |
| 43903102039 | `0b5ea4798fd8571acf229fe81fbf6212732e69a1` | 2026-11-16T16:02:49Z | 2026-11-16T16:02:49Z | completed / cancelled | 0 |
| 43902997597 | `0b483a4ce011a0b9a047fa0c58be4e6132460288` | 2026-11-16T16:02:15Z | 2026-11-16T16:02:15Z | completed / cancelled | 11 |
| 43902918613 | `becf69c12f43774e69723cb0caeee1714d3aa1fb` | 2026-11-16T16:01:49Z | 2026-11-16T16:01:49Z | completed / cancelled | 0 |
| 43902625213 | `0dbb55d78f0d320e82579fa3926323ba95787fc7` | 2026-11-16T16:00:18Z | 2026-11-16T16:00:18Z | completed / cancelled | 0 |
| 43902528552 | `d44307780caccb8d286796703d4bc508543dbd95` | 2026-11-16T15:59:48Z | 2026-11-16T15:59:48Z | completed / cancelled | 0 |
| 43902258379 | `2ed0c808033acfb8bad2042ba5590b81de560a34` | 2026-11-16T15:58:18Z | 2026-11-16T15:58:18Z | completed / cancelled | 0 |
| 43902194620 | `deed1b49092ce5b9a208cd540bed5e3671323e04` | 2026-11-16T15:57:56Z | 2026-11-16T15:57:56Z | completed / cancelled | 0 |
| 43901974127 | `f638ee059ab879a693c37fae929336d317888586` | 2026-11-16T15:56:44Z | 2026-11-16T15:56:44Z | completed / cancelled | 0 |
| 43901817351 | `311c5f2b4423784ac3c7c8fff54d0fd37509aeb9` | 2026-11-16T15:55:55Z | 2026-11-16T15:55:55Z | completed / cancelled | 11 |
| 43901746509 | `806663999c305f1e484b5885f63d8fee249a922c` | 2026-11-16T15:55:33Z | 2026-11-16T15:55:33Z | completed / success | 7 |

## Queue by job group

| Job group | Valid n | Median queue (s) | Maximum queue (s) | Max run ID / job ID |
|---|---:|---:|---:|---|
| foundation | 8 | 3 | 56 | `43904392596 / 133431215271` |
| changed-scope | 8 | 2 | 64 | `43904392596 / 133431215886` |
| desktop | 7 | 3 | 108 | `43902997597 / 133424665469` |
| sanitizers | 6 | 2.5 | 138 | `43902997597 / 133424665528` |
| linux-x64 | 6 | 3 | 387 | `43902997597 / 133424665513` |
| linux-arm64 | 6 | 5 | 36 | `43904392596 / 133432002149` |
| windows-x64 | 6 | 2.5 | 61 | `43902997597 / 133424665448` |
| studio shard 1/3 | 6 | 3 | 305 | `43902997597 / 133424665512` |
| studio shard 2/3 | 6 | 3 | 245 | `43902997597 / 133424665535` |
| studio shard 3/3 | 6 | 3 | 86 | `43902997597 / 133424665467` |
| studio | 6 | 3 | 94 | `43901817351 / 133423273047` |

- **Valid observations:** 71; overall median 3 seconds.
- **Skipped records:** 10; no measured queue.
- **Negative created/start intervals:** 10 on attempt-2 run `43914680092`, treated as null. Its one valid `desktop` queue is 2 seconds. Per-attempt endpoint reproduced the ten anomalies, not resolved them.
- **Runs cancelled without a job record:** 11. They stay in the 20-run denominator and do not become zero-second job queues.
- **Largest queue:** 387 seconds, `linux-x64` job `133424665513` in run `43902997597` (run ultimately cancelled).
- **Inference:** group medians are 2–5 seconds, below the 7.30-minute longest-job reference, but cancellation selection and attempt timestamps limit generalizability.

## Machine-readable per-job evidence

The complete 91-row per-job source-field table appears below; the separate staging CSV is not part of this PR. `null` is an explicit missing/skipped/invalid queue, never zero. Timestamp strings are UTC and taken from GitHub jobs metadata.


### Complete per-job timestamp and queue records (UTC)

| Run ID | Job ID | Job name | Created (`created_at`) | Started (`started_at`) | Queue s | Conclusion | Duration s | Queue exclusion |
|---|---|---|---|---|---:|---|---:|---|
| 43916678348 | 133472578351 | foundation | 17:16:44 | 17:16:46 | 2 | success | 30 | valid |
| 43916678348 | 133472578771 | changed-scope | 17:16:44 | 17:16:46 | 2 | success | 7 | valid |
| 43916678348 | 133472683349 | studio shard ${{ matrix.shard }}/3 | 17:16:54 | 17:16:54 | null | skipped | null | skipped_no_runner |
| 43916678348 | 133472683516 | matrix.name | 17:16:54 | 17:16:54 | null | skipped | null | skipped_no_runner |
| 43916678348 | 133472683970 | desktop | 17:16:54 | 17:16:54 | null | skipped | null | skipped_no_runner |
| 43916678348 | 133472684063 | studio | 17:16:54 | 17:16:54 | null | skipped | null | skipped_no_runner |
| 43916678348 | 133472684118 | sanitizers | 17:16:54 | 17:16:54 | null | skipped | null | skipped_no_runner |
| 43916214352 | 133470951634 | changed-scope | 17:14:10 | 17:14:13 | 3 | success | 20 | valid |
| 43916214352 | 133470951980 | foundation | 17:14:10 | 17:14:13 | 3 | success | 27 | valid |
| 43916214352 | 133471183245 | windows-x64 | 17:14:33 | 17:14:35 | 2 | success | 330 | valid |
| 43916214352 | 133471183280 | sanitizers | 17:14:33 | 17:14:35 | 2 | success | 513 | valid |
| 43916214352 | 133471183343 | studio shard 2/3 | 17:14:33 | 17:14:36 | 3 | success | 173 | valid |
| 43916214352 | 133471183354 | desktop | 17:14:33 | 17:14:36 | 3 | success | 128 | valid |
| 43916214352 | 133471183367 | linux-x64 | 17:14:33 | 17:14:36 | 3 | success | 189 | valid |
| 43916214352 | 133471183414 | linux-arm64 | 17:14:33 | 17:14:37 | 4 | success | 139 | valid |
| 43916214352 | 133471183427 | studio shard 1/3 | 17:14:33 | 17:14:36 | 3 | success | 173 | valid |
| 43916214352 | 133471183445 | studio shard 3/3 | 17:14:33 | 17:14:36 | 3 | success | 227 | valid |
| 43916214352 | 133473622986 | studio | 17:18:24 | 17:18:27 | 3 | success | 4 | valid |
| 43914680092 | 133476394524 | desktop | 17:22:50 | 17:22:52 | 2 | success | 109 | valid |
| 43914680092 | 133476396271 | studio shard 1/3 | 17:22:50 | 17:05:58 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476397011 | studio shard 3/3 | 17:22:50 | 17:05:57 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476397490 | windows-x64 | 17:22:50 | 17:05:59 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476398294 | studio | 17:22:50 | 17:10:20 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476458368 | sanitizers | 17:22:56 | 17:05:58 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476466144 | linux-x64 | 17:22:57 | 17:05:58 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476480602 | linux-arm64 | 17:22:58 | 17:06:00 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476480865 | foundation | 17:22:58 | 17:05:48 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476481669 | changed-scope | 17:22:58 | 17:05:48 | null | success | null | negative_interval_second_attempt |
| 43914680092 | 133476491822 | studio shard 2/3 | 17:22:59 | 17:05:58 | null | success | null | negative_interval_second_attempt |
| 43912720275 | 133458635962 | foundation | 16:55:00 | 16:55:02 | 2 | success | 25 | valid |
| 43912720275 | 133458636319 | changed-scope | 16:55:00 | 16:55:02 | 2 | success | 7 | valid |
| 43912720275 | 133458743255 | sanitizers | 16:55:10 | 16:55:12 | 2 | success | 388 | valid |
| 43912720275 | 133458743361 | linux-arm64 | 16:55:10 | 16:55:15 | 5 | success | 189 | valid |
| 43912720275 | 133458743407 | studio shard 3/3 | 16:55:10 | 16:55:12 | 2 | success | 232 | valid |
| 43912720275 | 133458743428 | studio shard 1/3 | 16:55:10 | 16:55:12 | 2 | success | 160 | valid |
| 43912720275 | 133458743440 | linux-x64 | 16:55:10 | 16:55:12 | 2 | success | 197 | valid |
| 43912720275 | 133458743445 | windows-x64 | 16:55:10 | 16:55:12 | 2 | success | 424 | valid |
| 43912720275 | 133458743457 | desktop | 16:55:10 | 16:55:12 | 2 | success | 127 | valid |
| 43912720275 | 133458743724 | studio shard 2/3 | 16:55:10 | 16:55:12 | 2 | success | 140 | valid |
| 43912720275 | 133461222115 | studio | 16:59:05 | 16:59:07 | 2 | success | 2 | valid |
| 43909707167 | 133447952320 | changed-scope | 16:38:21 | 16:38:23 | 2 | success | 6 | valid |
| 43909707167 | 133447952876 | foundation | 16:38:21 | 16:38:24 | 3 | success | 28 | valid |
| 43909707167 | 133448037080 | desktop | 16:38:29 | 16:38:32 | 3 | success | 138 | valid |
| 43909707167 | 133448037094 | studio shard 1/3 | 16:38:29 | 16:38:31 | 2 | success | 153 | valid |
| 43909707167 | 133448037115 | windows-x64 | 16:38:29 | 16:38:32 | 3 | success | 382 | valid |
| 43909707167 | 133448037122 | sanitizers | 16:38:29 | 16:38:32 | 3 | success | 389 | valid |
| 43909707167 | 133448037175 | studio shard 3/3 | 16:38:29 | 16:38:32 | 3 | success | 221 | valid |
| 43909707167 | 133448037194 | linux-arm64 | 16:38:29 | 16:38:33 | 4 | success | 185 | valid |
| 43909707167 | 133448037244 | studio shard 2/3 | 16:38:29 | 16:38:31 | 2 | success | 135 | valid |
| 43909707167 | 133448037325 | linux-x64 | 16:38:29 | 16:38:31 | 2 | success | 202 | valid |
| 43909707167 | 133450462049 | studio | 16:42:13 | 16:42:16 | 3 | success | 2 | valid |
| 43904392596 | 133431215271 | foundation | 16:12:45 | 16:13:41 | 56 | success | 27 | valid |
| 43904392596 | 133431215886 | changed-scope | 16:12:45 | 16:13:49 | 64 | success | 8 | valid |
| 43904392596 | 133432001906 | desktop | 16:13:58 | 16:14:00 | 2 | success | 118 | valid |
| 43904392596 | 133432002096 | studio shard 3/3 | 16:13:58 | 16:14:01 | 3 | success | 251 | valid |
| 43904392596 | 133432002113 | studio shard 1/3 | 16:13:58 | 16:14:24 | 26 | success | 179 | valid |
| 43904392596 | 133432002134 | linux-x64 | 16:13:58 | 16:14:44 | 46 | success | 191 | valid |
| 43904392596 | 133432002149 | linux-arm64 | 16:13:58 | 16:14:34 | 36 | success | 188 | valid |
| 43904392596 | 133432002182 | studio shard 2/3 | 16:13:58 | 16:14:29 | 31 | success | 146 | valid |
| 43904392596 | 133432002276 | windows-x64 | 16:13:58 | 16:14:11 | 13 | success | 435 | valid |
| 43904392596 | 133432002454 | sanitizers | 16:13:58 | 16:14:36 | 38 | success | 414 | valid |
| 43904392596 | 133434787715 | studio | 16:18:12 | 16:18:15 | 3 | success | 4 | valid |
| 43902997597 | 133424642965 | foundation | 16:02:48 | 16:02:48 | 0 | cancelled | 2 | valid |
| 43902997597 | 133424643490 | changed-scope | 16:02:48 | 16:02:48 | 0 | cancelled | 2 | valid |
| 43902997597 | 133424665394 | linux-arm64 | 16:02:50 | 16:03:11 | 21 | success | 187 | valid |
| 43902997597 | 133424665448 | windows-x64 | 16:02:50 | 16:03:51 | 61 | success | 433 | valid |
| 43902997597 | 133424665467 | studio shard 3/3 | 16:02:50 | 16:04:16 | 86 | success | 222 | valid |
| 43902997597 | 133424665469 | desktop | 16:02:50 | 16:04:38 | 108 | success | 135 | valid |
| 43902997597 | 133424665512 | studio shard 1/3 | 16:02:50 | 16:07:55 | 305 | success | 158 | valid |
| 43902997597 | 133424665513 | linux-x64 | 16:02:50 | 16:09:17 | 387 | success | 208 | valid |
| 43902997597 | 133424665528 | sanitizers | 16:02:50 | 16:05:08 | 138 | success | 398 | valid |
| 43902997597 | 133424665535 | studio shard 2/3 | 16:02:50 | 16:06:55 | 245 | success | 128 | valid |
| 43902997597 | 133429768198 | studio | 16:10:33 | 16:11:11 | 38 | success | 3 | valid |
| 43901817351 | 133420122709 | foundation | 15:55:56 | 15:55:59 | 3 | success | 25 | valid |
| 43901817351 | 133420123204 | changed-scope | 15:55:56 | 15:55:59 | 3 | success | 7 | valid |
| 43901817351 | 133420233307 | sanitizers | 15:56:06 | 15:56:08 | 2 | success | 298 | valid |
| 43901817351 | 133420233364 | studio shard 1/3 | 15:56:06 | 15:56:09 | 3 | success | 188 | valid |
| 43901817351 | 133420233456 | linux-arm64 | 15:56:06 | 15:56:11 | 5 | success | 186 | valid |
| 43901817351 | 133420233468 | studio shard 2/3 | 15:56:06 | 15:56:09 | 3 | success | 163 | valid |
| 43901817351 | 133420233483 | studio shard 3/3 | 15:56:06 | 15:56:09 | 3 | success | 273 | valid |
| 43901817351 | 133420233507 | desktop | 15:56:06 | 15:56:09 | 3 | success | 93 | valid |
| 43901817351 | 133420233531 | windows-x64 | 15:56:06 | 15:56:08 | 2 | success | 399 | valid |
| 43901817351 | 133420233556 | linux-x64 | 15:56:06 | 15:56:09 | 3 | success | 243 | valid |
| 43901817351 | 133423273047 | studio | 16:00:43 | 16:02:17 | 94 | success | 4 | valid |
| 43901746509 | 133419872325 | changed-scope | 15:55:34 | 15:55:36 | 2 | success | 6 | valid |
| 43901746509 | 133419873018 | foundation | 15:55:34 | 15:55:37 | 3 | success | 54 | valid |
| 43901746509 | 133419965844 | desktop | 15:55:42 | 15:55:42 | null | skipped | null | skipped_no_runner |
| 43901746509 | 133419965921 | sanitizers | 15:55:42 | 15:55:42 | null | skipped | null | skipped_no_runner |
| 43901746509 | 133419966754 | studio shard ${{ matrix.shard }}/3 | 15:55:43 | 15:55:43 | null | skipped | null | skipped_no_runner |
| 43901746509 | 133419966825 | matrix.name | 15:55:43 | 15:55:43 | null | skipped | null | skipped_no_runner |
| 43901746509 | 133419967006 | studio | 15:55:43 | 15:55:43 | null | skipped | null | skipped_no_runner |

## K7 exact ABI2 name equality from hosted CTest inventories

- **Main base:** `042454de51a739ed4cf39324baa07028c42acc9f`, [Lab CI run 43961005460](https://github.com/kalharbi11/wirescape-lab/actions/runs/43961005460), sanitizer job `133628142310`, `ctest --test-dir build/asan -N -R abi2` log.
- **PR head before compiler-content-check correction:** `a8b88b3f3d5d54cad421ddeb587ade627e60d759`, [Lab CI run 43961945146](https://github.com/kalharbi11/wirescape-lab/actions/runs/43961945146), sanitizer job `133631415374`, same `ctest -N -R abi2` command and log.
- **Observed lists:** each 82 distinct names, same order, 0 added and 0 removed. The historic 78-name reference is not the active merged baseline. The correction-head exact inventory remains unverified until its run.

| Index | Base test name | PR head test name |
|---:|---|---|
| 1 | `abi2_osc_host_service_tests` | `abi2_osc_host_service_tests` |
| 2 | `abi2_osc_graph_ingress_tests` | `abi2_osc_graph_ingress_tests` |
| 3 | `abi2_sidecar_protocol_tests` | `abi2_sidecar_protocol_tests` |
| 4 | `abi2_sidecar_apply_graph_tests` | `abi2_sidecar_apply_graph_tests` |
| 5 | `abi2_sidecar_capture_tests` | `abi2_sidecar_capture_tests` |
| 6 | `abi2_sidecar_unit_tests` | `abi2_sidecar_unit_tests` |
| 7 | `abi2_sidecar_audio_recovery_tests` | `abi2_sidecar_audio_recovery_tests` |
| 8 | `abi2_sidecar_snapshot_tests` | `abi2_sidecar_snapshot_tests` |
| 9 | `abi2_runtime_patch_tests` | `abi2_runtime_patch_tests` |
| 10 | `abi2_builtin_source_tests` | `abi2_builtin_source_tests` |
| 11 | `abi2_offline_play` | `abi2_offline_play` |
| 12 | `abi2_header_c99` | `abi2_header_c99` |
| 13 | `abi2_sdk_tests` | `abi2_sdk_tests` |
| 14 | `abi2_sdk_scalar_tests` | `abi2_sdk_scalar_tests` |
| 15 | `abi2_voice_tests` | `abi2_voice_tests` |
| 16 | `abi2_note_identity_tests` | `abi2_note_identity_tests` |
| 17 | `abi2_template_tests` | `abi2_template_tests` |
| 18 | `abi2_engine_tests` | `abi2_engine_tests` |
| 19 | `abi2_module_tests` | `abi2_module_tests` |
| 20 | `abi2_scalar_ports` | `abi2_scalar_ports` |
| 21 | `abi2_portable_ports` | `abi2_portable_ports` |
| 22 | `abi2_benchmark` | `abi2_benchmark` |
| 23 | `abi2_benchmark_64` | `abi2_benchmark_64` |
| 24 | `abi2_benchmark_128` | `abi2_benchmark_128` |
| 25 | `abi2_benchmark_256` | `abi2_benchmark_256` |
| 26 | `abi2_integration_tests` | `abi2_integration_tests` |
| 27 | `abi2_guide_tests` | `abi2_guide_tests` |
| 28 | `abi2_example_random_source_tests` | `abi2_example_random_source_tests` |
| 29 | `abi2_example_step_sequencer_tests` | `abi2_example_step_sequencer_tests` |
| 30 | `abi2_osc_codec_tests` | `abi2_osc_codec_tests` |
| 31 | `abi2_osc_in_tests` | `abi2_osc_in_tests` |
| 32 | `abi2_osc_out_tests` | `abi2_osc_out_tests` |
| 33 | `abi2_monitor_tests` | `abi2_monitor_tests` |
| 34 | `abi2_panic_stress` | `abi2_panic_stress` |
| 35 | `abi2_feedback_tests` | `abi2_feedback_tests` |
| 36 | `abi2_banned_includes` | `abi2_banned_includes` |
| 37 | `abi2_soak_smoke` | `abi2_soak_smoke` |
| 38 | `abi2_soak_stats_tests` | `abi2_soak_stats_tests` |
| 39 | `abi2_soak_cli` | `abi2_soak_cli` |
| 40 | `abi2_port_behavior_tests` | `abi2_port_behavior_tests` |
| 41 | `abi2_staged_tests` | `abi2_staged_tests` |
| 42 | `abi2_live_replan_tests` | `abi2_live_replan_tests` |
| 43 | `abi2_clock_tests` | `abi2_clock_tests` |
| 44 | `abi2_function_envelope_tests` | `abi2_function_envelope_tests` |
| 45 | `abi2_ladder_tests` | `abi2_ladder_tests` |
| 46 | `abi2_mixer_tests` | `abi2_mixer_tests` |
| 47 | `abi2_noise_tests` | `abi2_noise_tests` |
| 48 | `abi2_output_tests` | `abi2_output_tests` |
| 49 | `abi2_scale_offset_tests` | `abi2_scale_offset_tests` |
| 50 | `abi2_slew_tests` | `abi2_slew_tests` |
| 51 | `abi2_reference_freezer_tests` | `abi2_reference_freezer_tests` |
| 52 | `abi2_returned_filter_stress` | `abi2_returned_filter_stress` |
| 53 | `abi2_module_cpu_probe_output_tests` | `abi2_module_cpu_probe_output_tests` |
| 54 | `abi2_module_cpu_probe_smoke` | `abi2_module_cpu_probe_smoke` |
| 55 | `abi2_module_cpu_probe_tiny_64` | `abi2_module_cpu_probe_tiny_64` |
| 56 | `abi2_module_cpu_probe_tiny_128` | `abi2_module_cpu_probe_tiny_128` |
| 57 | `abi2_module_cpu_probe_tiny_256` | `abi2_module_cpu_probe_tiny_256` |
| 58 | `abi2_module_cpu_probe_stress_smoke` | `abi2_module_cpu_probe_stress_smoke` |
| 59 | `abi2_module_cpu_probe_poly_smoke` | `abi2_module_cpu_probe_poly_smoke` |
| 60 | `abi2_module_cpu_probe_spectral_smoke` | `abi2_module_cpu_probe_spectral_smoke` |
| 61 | `abi2_module_cpu_probe_unit` | `abi2_module_cpu_probe_unit` |
| 62 | `abi2_host_keyboard_tests` | `abi2_host_keyboard_tests` |
| 63 | `abi2_audio_callback_live_midi_tests` | `abi2_audio_callback_live_midi_tests` |
| 64 | `abi2_midi_release_tests` | `abi2_midi_release_tests` |
| 65 | `abi2_midi_live_host_tests` | `abi2_midi_live_host_tests` |
| 66 | `abi2_midi_backend_gate_tests` | `abi2_midi_backend_gate_tests` |
| 67 | `abi2_midi_service_tests` | `abi2_midi_service_tests` |
| 68 | `abi2_midi_in_tests` | `abi2_midi_in_tests` |
| 69 | `abi2_midi_to_cv_tests` | `abi2_midi_to_cv_tests` |
| 70 | `abi2_midi_cc_to_cv_tests` | `abi2_midi_cc_to_cv_tests` |
| 71 | `abi2_macro_oscillator_tests` | `abi2_macro_oscillator_tests` |
| 72 | `abi2_macro_reference_guards` | `abi2_macro_reference_guards` |
| 73 | `abi2_chaos_lite_tests` | `abi2_chaos_lite_tests` |
| 74 | `abi2_blend_tests` | `abi2_blend_tests` |
| 75 | `abi2_resonator_tests` | `abi2_resonator_tests` |
| 76 | `abi2_spectral_tests` | `abi2_spectral_tests` |
| 77 | `abi2_delay_tests` | `abi2_delay_tests` |
| 78 | `abi2_reverb_tests` | `abi2_reverb_tests` |
| 79 | `abi2_quantizer_tests` | `abi2_quantizer_tests` |
| 80 | `abi2_quad_vca_tests` | `abi2_quad_vca_tests` |
| 81 | `abi2_notes_to_cv_tests` | `abi2_notes_to_cv_tests` |
| 82 | `abi2_chord_tests` | `abi2_chord_tests` |

## K7 and K8 cache provenance, acceptance pending

| Field | Evidence |
|---|---|
| CI1.3 sanitizer job | PR head `a8b88b3f3d5d54cad421ddeb587ade627e60d759`, Lab CI run `43961945146`, sanitizer job `133631415374` completed `success`, started `2026-11-16T21:37:31Z`, completed `2026-11-16T21:43:17Z`, **346 seconds = 5.77 min**. |
| Cache restoration | `actions/cache/restore@v4` logged **Cache not found**. The job printed `PR: no matching cache; cold build (not warm evidence)`. Thus no matched warm restore. |
| ccache statistics | `ccache -s` after the build: **49/274 hits (17.88%)**, **225/274 misses (82.12%)**. These hits do **not** demonstrate restoration of a warm cache. |
| Compiler fingerprint | SHA-256 `0471e1e6607848e88fd22945e0ac38d7ec63d5edd8e82904d3a268599e7d7be9` printed at this PR head; compiler paths, compiler-version text, build settings, and sanitizer flags feed the key. Correction adds `CCACHE_COMPILERCHECK=content`; no measured corrected-head result yet. |
| Cold main/manual save | **Not demonstrated** with CI1.3 workflow. Main baseline run predates CI1.3; branch-dispatch caches need not be visible to pull-request runs. No invented main save provenance. |
| Warm PR run | **Not demonstrated**. A successful cold PR run is not a warm PR run even with 49 ccache hits. |
| K8 reference | Fable's 7.30-minute longest-job baseline = 438 seconds. Required warm sanitizer runtime **≤318 seconds (5.30 minutes)**. |
| K8 result | **Blocked / untested**: a genuine matched warm PR cache hit and its runtime are required before merging. Do not claim success or change the threshold. |

This is a fixed historical queue sample plus identified hosted test/cache observations, not a fresh queue sample for the new PR date. No pipeline rerun or warm-cache benefit is asserted for the correction head.
