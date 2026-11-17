<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M2 #139 applyGraph continuity: pending actual null-sink measurement

**Evidence status: BLOCKED on native execution and retained raw/marks artifacts.**
This is a capture inventory, not a numeric measurement or M2 acceptance.
Source inspection and new synthetic harness authoring occurred in regular
Chat through the connected repository API only; no native executable,
PCM file, .marks file or worker artifact was downloaded or run here.

**Current source baseline:** main
4161b90fcc2fff48058ca50f44eafb15fe0ff764 (2026-11-16 ET);
the exact M2 #139 PR build head must be taken from the new PR's signed
Result and verified by the actual sidecar hello SHA. M0 original before
numbers are in facts/BASELINE.md and facts/dsp/edit_continuity.{json,md}
at lab commit 4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad, cloud Linux x86_64
Xeon 2.10 GHz, UTC 2026-11-16T19:00Z. Historical three-repeat
worst values include loadGraph identical tone silence 6.04 ms and
held-note silence about 1.02e3 ms; those are NOT applyGraph readings.
Existing 119 historical witness rows and eight prior unsupported labels
retain their date/source and original meanings until new evidence lands.

**Contract:** M2 r3 acceptance point 3; proposals/0005 section 4; M0 r3
R7. Existing marks-based time window and metrics are unchanged. Expected
and acceptable design language about an applyGraph witness dip with no
restart is not a fabricated pass/fail measurement, and no numeric
threshold or physical-audio equivalence is inferred.

| New edit family to measure | Required witnesses | 3 repeats | Marked reply path, replaced, unapplied | Recorded numeric values |
|---|---|---|---|---|
| applyGraph identical | tone, slip tone, tail, held note, clock, subject | pending | pending | unverified |
| applyGraph Groove steps | tone, slip tone, tail, held note, clock, subject | pending | pending | unverified |
| applyGraph Groove length | tone, slip tone, tail, held note, clock, subject | pending | pending | unverified |
| applyGraph voice count | tone, slip tone, tail, held note, clock, subject | pending | pending | unverified |
| applyGraph OSC In row | tone, slip tone, tail, held note, clock | pending | pending | unverified |
| applyGraph one parameter | tone, slip tone, tail, held note, clock, subject | pending | pending | unverified |
| applyGraph deleted module | tone, slip tone, tail, held note, clock | pending | pending | unverified |
| applyGraph restored module | tone, slip tone, tail, held note, clock | pending | pending | unverified |

A complete execution creates 45 new witness rows, 24 edited
captures and 3 no-edit reference captures, each with a marks file.
Every row needs three actual replies, b0/b1/gen and alignments,
per-repeat metrics and worst values, machine/toolchain/source/build
provenance and raw/marks checksums. Counts are planned, not observed.

**Reviewable capture package:** bench/continuity/CAPTURE.md provides
the exact command template, source/build pin check, case list, raw file
inventory and publication limits. Owner's Worker2 must publish a
reviewable package from a pinned built sidecar and recompute hashes.
The original JSON/Markdown must then be augmented without relabeling
any M0 rows. No raw captures, ZIPs over 1 MB, usernames, hostnames,
absolute machine paths, real audio/MIDI or LAN measurements are
authorized in this fact.

**Limitations:** No raw/marks artifacts currently exist in this Chat;
no phase, dip, restarted, time-slip, silence or acoustic comparison can
be asserted for the new cases. ringmod2 has no measurement in the
existing baseline; no sound-parity claim is made.
