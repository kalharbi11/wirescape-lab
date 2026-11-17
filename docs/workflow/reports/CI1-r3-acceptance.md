<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1 r3 evidence — CI1 r4 contract (GAP ONLY)

Prepared 2026-11-16 America/New_York against main 1e072cf239b804eb2a8fa3cbb7ee692546a374b6. Run timestamps use UTC. This is a notes-only evidence record under issue #141, **not** a CI1 acceptance, K8 keep/revert verdict, or product authorization. Governing contract: [CI1 r4](../milestones/CI1.md), [Fable Q17](../QUESTIONS.md).

## Completed predecessor stages — repository-linked evidence

| Stage | Implementation PR | Full implementation head | Merged main commit | Pinned exact-head Lab evidence | Observed facts / remaining citation needs |
|---|---|---|---|---|---|
| CI1.1 / #95 | #96 | `a56af2956a2ab6dc9e0be6d8c89e810201f41350` | `150321cb47e3eed94f6a5f0cd30ad97dc16e3228` | 43859112354 | Lead/builder report 11 successful jobs including literal `studio`; 3 shard inventory 128+103+113=344, native parity 114 per platform, sanitizer 78 at historical head, Desktop 24 listed. At first evidence run 43847804664, 4 native/sanitizer runner cores; 7.30-minute longest job, 29.12 runner-minutes vs old 9.48-minute/37.21 baseline. Measured test counts and timing are pinned in the CI1.1 own-PR facts and signed PR #96 Result. |
| CI1.2 / #108 | #110 | `aa5a3dc210706d21d1d7751d8ce8a82951909029` | `371c1778f2b4f028817c06a695cd488f718fcefe` | 43919414792 | Lead checked all three native matrix builds, all seven literal required names and foundation unit negative cases. Lead post-merge review of PR #97 confirms all seven required check names; notes-only code gates skipped. |
| CI1.4 / #122 | #123 | `c812590717db538df82022e14777eb3e5935ef6d` | `49747bdfbe5ff6d30f3924ade31335c6993bd21e` | 43943966878 | Lead checked 14/14 jobs green; four authenticated aggregates scoped to job-level `actions:read`, 239 foundation tests and 0 token-like log hits; Q12/K9. CI1.4 lead inspected authenticated aggregate logs; external M2 follow-up is not represented as a CI1 pass. |

## CI1 acceptance 1–5 / invariants K1–K6 and K9

| Criterion | Verified source and result | Qualification |
|---|---|---|
| K1, acceptance 1 | [CI1.1 implementation Lab 43847804664](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664) documented 114 identical native CTest names per Linux x64, ARM64 and Windows; 78 historical ABI2 sanitizer names, all unchanged; Studio lists 128+103+113 = 344 (343 passed/one existing skip); Desktop 24 (22 passed/two existing skips). [Final correction head Lab 43859112354](https://github.com/kalharbi11/wirescape-lab/actions/runs/43859112354) had 11/11 green including literal studio aggregate. | Baseline 78 was historical, not a fixed count for future merged tests. |
| K2, K3, K5 | [PR #96](https://github.com/kalharbi11/wirescape-lab/pull/96) preserved sanitizer flags, timeout/retries/skips, Playwright single worker and Desktop job; source scope fail-closes on unknown/mixed paths, pushes/main/manual run full code jobs. | This report did not host-run all conditional paths. |
| K4, acceptance 2 | CI1.1 pre-implementation grep across native/apps/tools and CMake readers, plus foundation source-scope tests for notes-only, mixed, docs/specs, facts/dsp, .github, empty and unknown inputs. Foundation always executes. | Source-read audit is pinned to CI1.1, not a new current-tree audit. |
| K6, acceptance 5 | [CI1.2 Lab 43919414792](https://github.com/kalharbi11/wirescape-lab/actions/runs/43919414792) succeeded on all 7 literal required names (foundation, linux-x64, linux-arm64, windows-x64, sanitizers, studio, desktop) and all 3 actual native matrix legs. Unit tests cover missing/duplicate/failing/cancelled/skipped/wrong-attempt/API failure. [#97 post-merge](https://github.com/kalharbi11/wirescape-lab/pull/97#issuecomment-6924496171) again showed seven names with notes-only code jobs correctly skipped. | No unconditional success or policy/required-check bypass was authorized. |
| K9 | [CI1.4 Lab 43943966878](https://github.com/kalharbi11/wirescape-lab/actions/runs/43943966878) 14/14 jobs green, 239 foundation tests. Job-scoped actions:read on only 3 native and 1 Studio aggregates; bearer token only in verifier step, fixed api.github.com, redirects denied; retries/fallback denied. [Lead review](https://github.com/kalharbi11/wirescape-lab/pull/123#issuecomment-6929573080) found zero token-like patterns in 4 aggregate logs. | Log-pattern audit is not a universal guarantee of no secret leakage. |
| Acceptance 3–4 | [CI1.1 facts](../../../facts/tests/ci_durations_2026-11-16_ci1.md) measure baseline vs own completed PR; see table below. | Own timing PR head predates the later aggregate-only correction head. |
| Acceptance 6 | **OPEN:** merged CI1.3 K7, but Q17's single qualifying K8 keep/revert decision and neutral facts-on-main are not documented as complete. | **Milestone acceptance is NOT established.** |

## Historical duration and queue measurements

| Metric | Original Lab push [43837588432](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432) | CI1.1 implementation PR [43847804664](https://github.com/kalharbi11/wirescape-lab/actions/runs/43847804664) |
|---|---:|---:|
| Longest job, sanitizers | 9.48 min | **7.30 min** (2.18 min lower) |
| Total job runner-minutes | 37.21 | **29.12** (8.09 fewer) |
| Printed runner core count on three native platforms and sanitizer | original configured 2 | **4** each |
| Full PR wall time including queue | not comparable push population | **20.55 min**, not longest-job duration |

The approximately 5-minute longest-job goal was an estimate, not an acceptance gate. The fixed CI1 K8 reference is **7.30 min = 438 seconds**; a genuinely restored warm sanitizer job must finish **≤318 seconds**.

**Historical queue sample, not live/current:** [CI1.3 facts](../../../facts/tests/ci_durations_2026-11-16_ci1_3.md) pins 20 PR-run IDs and 91 job source rows, 71 valid job-created-to-started intervals; overall median **3 s**, maximum **387 s**. Ten skipped rows and ten anomalous negative created/start intervals are null, not zero. Eleven cancelled runs yielded no job rows. This is not current queue telemetry or workflow wall time; the median did not exceed the prior longest-job reference.

## CI1.3 K7/K8 after Fable Q17: observed run chronology

PR [#129](https://github.com/kalharbi11/wirescape-lab/pull/129) merged the reviewed head **0f3b447c158f86f1c2b24e0f0065081e9a348ec3** into main at **879a26cc4a6261cf49ab46afb63e1ee6a993612f**. K7 retains C/C++ compiler launchers, compiler-content check, 500 MB cache limit, toolchain/OS/architecture/sanitizer-flags key and post-build statistics, **PR restore only** and **main/manual cold save only**. ABI2 ctest-name identity was proven **82 ordered tests on both the then-current base and PR head**, no additions/removals; later S3 logs 83 after unrelated test additions. [K7 source facts](../../../facts/tests/ci_durations_2026-11-16_ci1_3.md) contain the 82-row identity table.

| Run / job, head provenance | Exact cache/time facts | K8 relevance |
|---|---|---|
| Manual [43966200132](https://github.com/kalharbi11/wirescape-lab/actions/runs/43966200132), sanitizer 133646255526, head 21bc87c | Successful **cold** feature-branch cache save **2026-11-16 22:10:10.992 UTC**; entry 10628646155, ref refs/heads/task/109-sanitizer-ccache, 102097945 bytes, version b97fbe098767aae2aa5efb5d4f8da4e488678a6aaf72931965bfb19f3ef9e00a, key ending 43966200132-1 | Manual save; not a warm PR |
| Prior [43964380415](https://github.com/kalharbi11/wirescape-lab/actions/runs/43964380415) attempt 2, sanitizer 133653972206 | **COLD MISS, 428 s, 49/274 ccache hits**. Original run created 2026-11-16 21:52:04Z before manual save; second attempt began 22:16:23Z afterward. | Neither K8 pass nor genuine warm K8 failure |
| Fresh pre-merge PR [43984524907](https://github.com/kalharbi11/wirescape-lab/actions/runs/43984524907), sanitizer 133709192008, head 0f3b447 | **COLD MISS, 326 s, 49/274 hits**, all 14 Lab jobs green, 82/82 sanitizer CTests | Not K8 warm evidence |
| Post-merge main push [43990935312](https://github.com/kalharbi11/wirescape-lab/actions/runs/43990935312), sanitizer 133731284556, main head 879a26c | Run created **2026-11-17 00:50:58Z**, deliberately cold/no restore; ccache **49/271 hits**, 222 misses; **83** ABI2 tests; successfully **SAVED 00:59:31.7337289Z** with key ci1-sanitizers-v1-Linux-X64-0471e1e6607848e88fd22945e0ac38d7ec63d5edd8e82904d3a268599e7d7be9-43990935312-1 | Valid main cold cache seed for Q17 |
| S3 PR [43991231173](https://github.com/kalharbi11/wirescape-lab/actions/runs/43991231173), sanitizer 133734959398, head b438613f | **Run created 00:53:11Z BEFORE save**; sanitizer began **01:02:25.942Z** AFTER save; **RESTORED exact main key 01:03:14.614Z**; ccache **221/271 hits (81.55%)**, 50 misses; succeeded **01:07:27.962Z**, **302.020 s** logged job first-to-last, 83 CTest names | **Real warm restoration, but provisional**: not established as Q17's first qualifying PR workflow *run created after* main save |

Warm evidence source: [#141 reviewer chronology](https://github.com/kalharbi11/wirescape-lab/issues/141#issuecomment-6934886853), actual [main cold](https://github.com/kalharbi11/wirescape-lab/actions/runs/43990935312) and [S3 PR](https://github.com/kalharbi11/wirescape-lab/actions/runs/43991231173) job logs. A job that started after save does **not** establish that its **workflow run was created after save**. The **302.020 s restored result is not silently substituted as the literal Q17 qualifying measurement**.

### Scope/version findings and limits

[Official cache-access docs](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache) explain event/ref scoping. The earlier feature-branch seed and PR misses shared the key prefix; a pinned actions/cache version computation of literal input **~/.cache/ccache|zstd-without-long|1.0** matched saved entry version **b97fbe...**. That computation did **not** expose PR restore backend effective scope/version; the earlier miss's particular backend cause was not observed. **Q17's approved bootstrap-order remedy** put a cold-save on main; the successful restored key in the later S3 job proves a main-seeded cache was accessible, not which internal request condition caused the old misses.

## Open gates — gap-only disposition

1. **Q17 first eligible workflow-run identification:** source-link the first pull_request **run created after** 2026-11-17 **00:59:31.7337289Z** in which sanitizers actually ran; show run creation, head, job/attempt, start/complete, matched key or MISS, ccache -s and duration. The reviewer sample created at 00:53:11Z is **not automatically eligible**, despite its successful warm job.
2. **Single-shot K8 decision remains with lead/design authority:** if that literal first eligible PR run restores and the job is **≤318 s**, keep the merged sanitizer cache; if restored and >318 s or MISS, the lead files one revert PR. **No second measurement/retry or threshold adjustment.** Record the actual qualifying numbers in a neutral facts/tests/ci_durations_* file on **main**, kept or reverted.
3. **Acceptance 6 and CI1 milestone sign-off remain open** until the Q17 decision and on-main fact are recorded. Neither #129 merged status nor 14 green jobs grants acceptance.
4. **Fresh #141 notes-only Lab CI must be observed separately** on this report's exact head; the notes-only classifier permits code checks to skip, not a claim of a new K8 measurement.
5. **Isolation:** #141 writes only docs/workflow/reports/CI1-r3-acceptance.md. #153 source is frozen pending the lead SR6 ruling. No changes to workflows, native, tests, facts, settings or product are part of this report.

**Final report status: GAP-ONLY / BLOCKED ON Q17 AND NEUTRAL FACTS-ON-MAIN.** This is **not** CI1 milestone acceptance.

Signed: gpt-builder2, 2026-11-16
