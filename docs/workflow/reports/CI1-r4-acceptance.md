<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1 r4 acceptance request — 2026-11-17

Design authority acceptance is requested after this report and its K8 fact file merge.
This report does not itself accept the milestone. The earlier
[CI1 r3 filename / r4 GAP-ONLY report](CI1-r3-acceptance.md) remains a dated historical record;
its missing K8 disposition is supplied by the evidence below.

| CI1 r4 criterion | Evidence | Delivery disposition |
|---|---|---|
| 1: CI1.1 K1 test identity and K4 grep | PR96 heada56af2956a2ab6dc9e0be6d8c89e810201f41350, merge150321cb47e3eed94f6a5f0cd30ad97dc16e3228, Lab43859112354; detailed counts/table in historical report | merged |
| 2: changed-scope positive/negative cases in foundation | PR96/CI1.1 evidence, later PR110/123 foundation coverage and source references in historical report | merged |
| 3: own PR timing/core count fact | facts/tests/ci_durations_2026-11-16_ci1.md, own full PR Lab43847804664; historical report distinguishes later aggregate-only correction head | merged |
| 4: longest job and runner-minutes against estimate | 7.30min /29.12runner-min vs9.48min /37.21; sanitizer-cache question resolved through Q9/Q17 and CI1.3 | measured, scope unchanged |
| 5: CI1.2 literal required names/negative unit cases and PR97 notes revalidation | PR110 headaa5a3dc210706d21d1d7751d8ce8a82951909029, merge371c1778f2b4f028817c06a695cd488f718fcefe, Lab43919414792 and PR97 signed post-merge review | merged |
| 6: CI1.3 K7 cold/save/restore, before-after/queue tables, K8 on main | PR129/merge879a26cc4a6261cf49ab46afb63e1ee6a993612f, historical cold/queue tables; new [literal first qualifying K8 fact](../../../facts/tests/ci_durations_2026-11-17_ci1_k8.md) | lead KEEP under Q17; fact lands with this report |

CI1.4/K9 supplemental evidence: PR123 headc812590717db538df82022e14777eb3e5935ef6d,
merge49747bdfbe5ff6d30f3924ade31335c6993bd21e, Lab43943966878 (14/14),239foundation tests;
authenticated aggregate scope and token-log audit are recorded in the historical report.

**K8 decision:** literal first eligible PR Lab44028971243/head309bf8851008976070b899768db35eb1e500a6b1,
created2026-11-17T06:08:10Z after all six prior post-save PR Labs skipped sanitizers.
Job133856058680 restored a main-saved key and completed297s by API timestamps (threshold318s),
221/271hits,83/83sanitizer tests. **KEEP** the CI1.3 sanitizer cache, as Q17 fixes.
No second observation, threshold change, CI change or revert is part of this report.
The complete chronology, key origin, ccache output and separately named log interval are in the fact file.

Limits: historical K1/K4/K9 assertions are pinned to their stage heads and cited signed evidence,
not represented as new whole-tree audits. PR timing is hosted timing, not a device fact.
Only the design authority records milestone acceptance; other tasks continue on their own dependencies.

Signed: gpt-lead, 2026-11-17
