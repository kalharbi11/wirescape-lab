<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1 r4 / Q17 first qualifying pull-request sanitizer measurement

Date: 2026-11-17 America/New_York. Repository: kalharbi11/wirescape-lab.
Measured lab commit: `309bf8851008976070b899768db35eb1e500a6b1` (PR #159).
Machine class: hosted Linux x64, Ubuntu 26.04.1, runner image ubuntu-26.04 / 20261111.196.1.
Sources: [Q17](../../docs/workflow/QUESTIONS.md), [CI1 r4](../../docs/workflow/milestones/CI1.md),
[run 44028971243](https://github.com/kalharbi11/wirescape-lab/actions/runs/44028971243),
[sanitizer job 133856058680](https://github.com/kalharbi11/wirescape-lab/actions/runs/44028971243/job/133856058680).

## Chronology and selection

First post-merge main cold cache save: run43990935312, sanitizer133731284556,
2026-11-17T00:59:31.7337289Z. Prior S3 run43991231173 was created00:53:11Z before this save;
its 302.020s restored job is outside this selection.
The Actions run-list query `created=>2026-11-17T00:59:31Z&per_page=100` returned52/52 runs at
review (2026-11-17); filtering event=pull_request and path=.github/workflows/ci.yml yields this
complete ordered prefix through the first executing sanitizer:

| Workflow created UTC | PR Lab run | Sanitizers |
|---|---:|---|
| 01:20:08 | 43994774030 | skipped |
| 01:20:47 | 43994861777 | skipped |
| 01:32:28 | 43996356462 | skipped |
| 02:19:15 | 44002094930 | skipped |
| 02:31:22 | 44003605247 | skipped |
| 04:44:38 | 44019266806 | skipped |
| 06:08:10 | 44028971243 | success, executed |

All dates in this table are2026-11-17. No later successful attempt replaces the selected run.
Run44028971243 event=pull_request, associated PR159, attempt1, exact head above.

## Cache and duration observations

| Field | Observed value |
|---|---|
| Workflow/job outcome | success / success |
| Cache restore step | actions/cache/restore@v4; restored successfully |
| Matched key | ci1-sanitizers-v1-Linux-X64-0471e1e6607848e88fd22945e0ac38d7ec63d5edd8e82904d3a268599e7d7be9-44019382004-1 |
| Origin of matched key | main push44019382004, sanitizer133825010131, saved2026-11-17T04:51:11.9111053Z |
| Job API started / completed UTC | 06:08:21 / 06:13:18 |
| Job API duration | 297s |
| Complete log first / last UTC | 06:08:22.7895625 / 06:13:15.9947894 |
| Complete log interval | 293.205227s (different endpoints from job API) |
| K8 threshold | 318s |
| API duration minus threshold | -21s |
| Cacheable calls | 271/271 |
| Hits / misses | 221/271 (81.55%) / 50/271 (18.45%) |
| Direct / preprocessed hits | 218/221 / 3/221 |
| Sanitizer CTests | 83/83 passed; test interval64.25s |

Matched-cache source: [main run44019382004](https://github.com/kalharbi11/wirescape-lab/actions/runs/44019382004).
It is later than the original main seed; the selected PR run is after both main saves.
The primary interval uses GitHub job API timestamps. The full log interval is separately named;
both are below318s. The original CI1 before value is438s (7.30min), so the API interval differs
by141s (2.35min). This is one selected Q17 observation, not a repeated sample.

`ccache -s` excerpt:
```text
Cacheable calls:   271 / 271 (100.0%)
  Hits:            221 / 271 (81.55%)
    Direct:        218 / 221 (98.64%)
    Preprocessed:    3 / 221 ( 1.36%)
  Misses:           50 / 271 (18.45%)
```

Limits: hosted timing is environment-dependent; this file records the fixed Q17 observation.
No device measurements, settings changes, gate changes, retries or additional K8 samples were
performed for this disposition. The historical before/after and queue tables remain in
[CI1 gap evidence](../../docs/workflow/reports/CI1-r3-acceptance.md) and the cited earlier facts.

Signed: gpt-lead, 2026-11-17
