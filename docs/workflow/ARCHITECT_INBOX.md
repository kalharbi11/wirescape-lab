<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

The Claude Architect performs all independent and Claude contract reviews under the owner's
2026-11-24 direction. Give each ready review an Open inbox row and `needs/architect`. Keep
`review-required` while it gates a merge. Pin full tested base/head SHAs, invariants and evidence
on the PR. Architect independence and all contract gates still apply. The owner or lead may
apply `architect-ready` once on one linked ready issue at the end of a verified batch. That
wake serves the whole inbox. The owner may also run `architect:run` manually.

Builders add or update one inbox row for a merge-ready review, ruling or Architect question.
Use a docs PR, identify the exact head and the task that waits, and preserve the pinned Result.
Only the owner or delivery lead applies an Architect trigger label.

## How to add a row
- Append to **Open**, newest last. One row per ask. Keep the cell short; the link holds detail.
- `Urg`: **now** = blocks a critical-path task (OB0, or the OB1 serial chain) ·
  **soon** = needed within ~2 days · **later** = parked or P3 work.
- `Waits` names the single task that stops (SR19: everything else keeps running).
- Long questions still go in [QUESTIONS.md](QUESTIONS.md); the row links to them.

## How the Architect clears rows
The Architect answers (in QUESTIONS, the PR, or a contract), moves the row to **Cleared** with
the answer's link and date, removes the `needs/architect` label, and updates CURRENT.
Cleared rows older than one run are deleted (git history keeps them).

## Open
| ID | Date ET | From | Kind | Urg | Ask (link) | Waits |
|---|---|---|---|---|---|---|
| A31 | 2026-11-23 | owner | blocker (Pi) | **postponed to OB1 candidate** (OB r2.6) | wirescape-pi hosted jobs cannot run until the private repo's Actions minutes return (2026-11-30), the runner is re-registered, and PI-1 [#369](https://github.com/kalharbi11/wirescape-lab/issues/369) (lab-side dispatch/publish, owner token `PI_BRIDGE_TOKEN`) lands. **Interim (run 44):** Pi evidence comes from owner-run `tools/owner_record.py` zips uploaded to [#590](https://github.com/kalharbi11/wirescape-lab/issues/590), plus hosted Linux arm64 CI. Keep this row Open until a `/pi-run` round-trip works. | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | MT2 T11 option-metadata grant. MT2 is parked in the lab (0023 §7.1; module tooling grows in `wirescape-test`); PR #176 was closed in the run-44 cleanup (branch kept). Re-rule when it is reopened. | MT2 only |
| B5-OBh3-gate | 2026-11-26 | gpt-builder5 | ruling (gate routing) | now | #610 exact ready head `b7eda294907e42cf2eb6ec02373394b53dcee4d0`: sole Lab red is `abi2_midi_egress_gate_tests`, `unexpected_gate_edge: 1`, outside test-only OB-h3 delta; #600 reports same symptom, cause unproven. Assign fix owner / disposition; no waiver or rerun. [Evidence and ask](https://github.com/kalharbi11/wirescape-lab/pull/610#issuecomment-7201317132) | #610 (P0a final release follows) |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B4-CMP1-retention | 2026-11-26 | Retain #592's 33 raw JSON artifacts | **Done** at `b77b6e7` after the owner allowed the artifact host: archive and all 33 member digests match the manifest; B4 re-verified and fixed one report line at `4026404`. [evidence](https://github.com/kalharbi11/wirescape-lab/pull/592#issuecomment-7200996322) |
| B2-E3c-runner | 2026-11-26 | #540 strict paired: six CC/OSC rows unavailable | **Fixed** `65a3eb8`: `engine/tests/module_cpu_probe.cpp` now packs default data slots (`initialize_data_slots`). Paired 45878542261 is 100/102 on both arches, equal to base. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7200833554) |
| B1-RS-modal | 2026-11-26 | #621 `App.ts` recovery modal blocks the non-modal crash loop | **Granted:** one `App.ts` guard that skips `offerRecovery('engine')` when the desktop restart bridge is present; added on #624 after #540 merges (B5 #545 does not touch `App.ts`). [ruling](https://github.com/kalharbi11/wirescape-lab/issues/621#issuecomment-7201215791) (supersedes PR #626) |
| B3-OBh6-timing | 2026-11-26 | #604 needs per-block timing from `wirescape_render` | **Granted:** opt-in timing flag in `tools/render/main.cpp` + tests; default output byte-identical; diagnostic labelling. After #600 facts. [ruling](https://github.com/kalharbi11/wirescape-lab/issues/604#issuecomment-7201217274) (supersedes PR #625) |
| Lane holds | 2026-11-26 | #609 after #592; #610 after #545 | **Lifted:** queue order only. #609 waits only on #540 (shared `module_catalog.h`); #610 has no shared path, ready with auto-merge. ([#609](https://github.com/kalharbi11/wirescape-lab/pull/609#issuecomment-7200953454), [#610](https://github.com/kalharbi11/wirescape-lab/pull/610#issuecomment-7200951975)) |
| B3-OBh1-dispatch | 2026-11-26 | Dispatch `ob-g7-hosted-soak.yml` at `48479fc` for #600 | **Dispatched** run [45877224981](https://github.com/kalharbi11/wirescape-lab/actions/runs/45877224981) (workflow from `main` `337d8e8`, `ref=48479fc38d5d1d74eefd0851ff893988d9398220`) ([#600 comment](https://github.com/kalharbi11/wirescape-lab/issues/600#issuecomment-7200746558)), run 47. B3 audits. |
| Planner run 1 | 2026-11-26 | Verify 0023, file its tasks, end wrap-up (§8) | **Transcribed** in run 47: M3 r2, M7 r1.7, OB r2.13 (+Gate P0 rows), STANDING SR22–SR25, CI-S1–S3 applied, issues #363/#358 reopened, #619–#622 filed, BUILDERS refreshed. One cite error (R2.5 `RealEngine.ts:300-304` → `:393-436`); rulings unaffected. |
