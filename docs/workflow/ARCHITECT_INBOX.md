<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

A planned review condition uses `review-required`. Open an Architect-only review row when its
pinned request is ready. Apply `needs/architect` and give the owner the ready queue and
`architect:run` trigger. The Architect clears ready Open rows at the owner's manual start.
Keep review material and its head pinned on the PR. Regular independent reviews use a pinned
request naming the eligible reviewer and the owner's manual start.

Builders update this inbox when required review is ready, a ruling is needed, or a question
requires the Architect. Use a docs PR and keep one current row per item. For a ready independent
review, name the eligible reviewer and mark the row as a handoff for the lead; Architect review
authority comes from the contract or the owner. The owner and delivery lead own the two trigger
labels, `architect-ready` and `review-ready`.

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
| A65 | 2026-11-24 | gpt-lead | contract-review | soon | [S7.9 manual review](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7148992053), base `cb0004b0ba56cfffd280567a29daf4151f830013`, head `c86810e2ac2d6d982df40ac1fdba29137bed0986`. D5 published, review M7 K1–K8, A63 and bounded r1.6 disposition. | S7.9 #444 |
| A66 | 2026-11-24 | gpt-lead | ruling | soon | [#467 Windows facts failure](https://github.com/kalharbi11/wirescape-lab/pull/467#issuecomment-7149127541), exact `6cbaf956f00c00351f6a0924d316a5dbe7e8aee2`. Required Windows Lab and the dedicated CHOKE capture passed. Separate Generate device-off facts failed compiling fetched libremidi before collectors. Confirm whether that exact advisory workflow can be handled separately for this evidence-only two-file PR. | #467 tooling merge |
| A67 | 2026-11-24 | gpt-lead | ruling | soon | [#463 hosted Windows mixed/still](https://github.com/kalharbi11/wirescape-lab/actions/runs/45522699609/artifacts/14981696094), head `5f91f9dd3c868357e181188a57af5b21bd5e4229`: route 17 and listener 9000 each report budget 0, enqueue 2; legacy route drops 0→2. Route the separate cause-specific fix under A61/A58, with B2 proposed, same load/limits and fail-first witness. | OSC product fix only |
| A64 follow-up | 2026-11-24 | gpt-builder1 / gpt-builder4 | ruling | soon | [#314 clocked-division target control](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7149509418), diagnostic base `6321dfeebdaab2bd39dd5e31446cc3ec17e628b5`, subject `e7726284a0116ba50f44946f48a4bf9720f36f6e`. Target peak frame48343 may contain startup history; switched is −2.271 dB vs old floor even if target is excluded. What validity check or original-floor disposition is required under A64(6)? Keep all fixed windows, fade, gain and bound. | S7.6 #449 division acceptance only |
| A62 CN follow-up | 2026-11-24 | gpt-builder1 | ruling | soon | [#472 measured rule-2 buffer discontinuities](https://github.com/kalharbi11/wirescape-lab/issues/472#issuecomment-7150508623), engine `e7d6bcd`, harness `873dc88`: 256→128 all 15 identical; 256→512 14 fresh IDs, held-note/tail silent, Clock −1 sample, carried Slew resumes exact after 479 samples but dip −24.636 dB/jump 194656.716. Disposition against M4 acceptance 2, or release separate correction; facts only, no gate change. | Final M4 CN acceptance (not E7 merge) |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A64 | 2026-11-24 | S7.6 #314/#449 `e772628`: A27 floor for mode/tone/division whose target state alone exceeds the old-value floor ([ask](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7148652913)) | **Ruled** ([M7 r1.8](milestones/M7.md), [Q28](QUESTIONS.md#q28--s76-endpoint-floor-a64), [comment](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7149046840)): floor = max(old-value, target-from-start) over the r1.4 windows; met at ≤ +0.1 dB over that floor (below meets). mode met (+0.030); tone +0.307 not met, real defect, fix in the DSP; division needs its target control. B4 #456 supplies the controls. |
| E7 | 2026-11-24 | #442 `2959f7e` Claude contract-review (lead pin 7148957226) | **Approved and merged** `94d1b0b` ([review](https://github.com/kalharbi11/wirescape-lab/pull/442#issuecomment-7149034643)); L1 MIDI note-off during the gap goes to the owner Pi checks. |
