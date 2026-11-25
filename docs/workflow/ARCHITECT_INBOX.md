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
| A31 | 2026-11-23 | owner | blocker (Pi) | **postponed to OB1 candidate** (OB r2.6, owner 2026-11-23) | wirescape-pi hosted jobs cannot run: (1) Actions minutes are used up until 2026-11-30; (2) the `WIRESCAPE_LAB_TOKEN` secret returns 401 and the owner replaces it; (3) the Pi runner may need re-registering. Keep this row Open until a `/pi-run` round-trip works. **Run 19b: [PI-1 #369](https://github.com/kalharbi11/wirescape-lab/issues/369) removes (1) and (2): dispatch and publish move to the lab, and the private repo needs no hosted minutes. It waits for the owner's token setup.** **Interim, allowed (owner question, 2026-11-23):** an agent running on the Pi as `wsci` may run `ci/sandbox.py` (CURRENT run 10c command), which keeps lab code inside podman. It posts `result.json` as a lab comment through its own app connection, with the SHA, Pi and date. The agent never runs lab code outside the sandbox and never gets the Pi user's own credentials. **2026-11-24:** owner is re-registering the runner and creating the PI-1 token (`PI_BRIDGE_TOKEN` in lab Environment `pi-bridge`, main only). | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |
| B4-A70 hooks | 2026-11-24 | gpt-builder4 | ruling | now | [#503 exact test-only scope/semantics](https://github.com/kalharbi11/wirescape-lab/issues/503#issuecomment-7152068965): one allocator friend declaration for fieldwise state, preserve held-note delivery bookkeeping without re-emit, C2 stateless/Slew adaptation. | E7c Keyboard hook and C2 tests |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A68 overturn | 2026-11-24 | #486 1024 prep +10.4 MB > 8 MiB | **M4 A70**: state hooks. E7c [#503](https://github.com/kalharbi11/wirescape-lab/issues/503) (B4), #486 witness only (B2) ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/486#issuecomment-7151878428)). |
| A69 follow-up | 2026-11-24 | #480 cost subject | **M4 A69a**: Black Ice Choir single-instance, plus clocked-groove dual and adoption blocks ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/480#issuecomment-7151868497)). |
| A69 adopt finding | 2026-11-24 | #436 held-bus dip after adopt | **M4 A71**, an erratum to 0005 §7: no release-all to `O` after a successful adopt. A High finding for E5 to fix before its Result ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7151866942)). |
| A64 mode follow-up | 2026-11-24 | #314 mode validity | **M7 r1.9a**: the check is one-sided; mode is met at +0.030 dB ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7151869667)). |
| B3-A60-scope | 2026-11-24 | #322 arm64 Function Envelope rows | **M7 r1.6b**: the r1.6a(b) exception applies ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/322#issuecomment-7151870666)). |
| A67 visibility | 2026-11-24 | #494 opt-in hosted reason summary (#500) | **Granted as asked** ([comment](https://github.com/kalharbi11/wirescape-lab/issues/494#issuecomment-7151889088)); #500 superseded and closed. |
