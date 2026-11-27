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



## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B2-P1e-ingress, B2-P1e-admission (#703) | 2026-11-26 | [#672](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7209167061) OSC ingress paths, [#620](https://github.com/kalharbi11/wirescape-lab/issues/620#issuecomment-7209344389) admission predicate, pending OSC across a commit | **A110** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7209512268): `osc_service`/`osc_host` granted for one bounded ingress hook and classification only. A read-only atomic `accepting` accessor is granted. Pending OSC events from an older route generation are dropped at flush and counted in `dropped.latest`; no reclassification. |
| B2-P1e-review (#702) | 2026-11-27 | owner `architect:run`: review and merge | **Approved and merged** [#702](https://github.com/kalharbi11/wirescape-lab/pull/702#issuecomment-7210957641) at `992d599` (head `593264f`; no High/Medium; Low: document the 64-child stream cap with P1-e2). #698/#706 closed as superseded by #660's merge. Headless H-G #30 merged; headless H-14 #26 unblocked. P1-e2 stays open in #672. |
| B2-P1e2-review (#713) | 2026-11-27 | [#708 contract review](https://github.com/kalharbi11/wirescape-lab/pull/708#issuecomment-7212151691) | [Approved](https://github.com/kalharbi11/wirescape-lab/pull/708#issuecomment-7212205643) at integrated head `68907e2` and merged as `bd6ac9d`. The oversized port argument diagnostic is a nonblocking follow-up. |
| B2-P1e2-scope (#708) | 2026-11-27 | [#672](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7211025024) control-port paths, shared-port semantics | **A111** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7211059942): `osc_service`/`osc_host` granted for one control-only listener, route identity, counters and stream-only observation; capability fixtures/schema granted. Shared port: observe once; `matched:true` if an enabled patch row matched, else `matched:false` always reported (not gated by `oscUnmatched`). B5 #699 overlap: second to merge merges `main`. |
| B2-P1e2-followup (#709) | 2026-11-27 | [#672](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7211087130) `controller_stream.h` grant | **A112** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7211469629): one internal control-port flag bypasses `oscUnmatched` at ingress and drain; all else unchanged. `controllerStream.controlPort` is advertised whenever the build supports it; open state comes from `status.osc.routes`. |
| H-14-macro (#711) | 2026-11-27 | gpt-lead: Macro witness at the P1-e pin | **A113** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/711#issuecomment-7211469849): mapped-param witness accepted for H-14 and the smoke; Macro row deferred to the MOD-5 pin (not waived); H-f1 stays unmeasured, with a workload task in bundle I. |
| B2-672-ahead | 2026-11-26 | owner: start P1-e #672 during #660 testing | **A109** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/672#issuecomment-7209249864): a draft-ahead branch from #660's head, test first, no edits to #660's recovery code. After #660 merges: merge `main`, rerun §3.5 and #660's witnesses on the combined head, then the Claude contract review. #660 `7f1f2e3` green so far (Windows pending). |
| B2-A104b-close | 2026-11-26 | [#620](https://github.com/kalharbi11/wirescape-lab/issues/620#issuecomment-7208836573) failed MIDI close lifetime | **A104b** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/620#issuecomment-7209025375): `host/sidecar/devices.{h,cpp}` ObservedMidi teardown granted. A callback target is never freed while the backend may call it. A failed close keeps the slot (`worker-failed`, no new enum). A permanent failure retains quiesced storage. Destructors never throw. `backend_` is destroyed before `slots_`. |
| H-11-controls | 2026-11-26 | [headless #11](https://github.com/kalharbi11/wirescape-headless/issues/11#issuecomment-7208948479) non-numeric script controls | **A108** [ruling](https://github.com/kalharbi11/wirescape-headless/issues/11#issuecomment-7209029932): v1 stays numeric. `button` is an additive momentary press (H-11a #25). text, notes, label and unbounded number are not Player controls in v1 (a check warning). A 0025 §9 row was added. #11 is closed. |
| Owner-headless-hw | 2026-11-26 | owner: open the tasks for an early headless hardware test | Owner hold amended for this path only: B2 #660 → **P1-e #672** released; **P1-f/g #699** filed and released to B5. Headless bundle H (#24–#26) filed, and soak moved to bundle I ([headless #27](https://github.com/kalharbi11/wirescape-headless/pull/27)). |
| Planner-limits | 2026-11-26 | Baseline reds found by A107 | For the planner: arm64 ASan A78 mute refusal at gen=10 (reproduced on base, #692) and baseline Windows "rendering output takes the live replan" failure (run 45928800288). Not waived; no task filed under the owner hold. |

