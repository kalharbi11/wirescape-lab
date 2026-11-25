<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue: five GPT chat lanes

Refreshed by gpt-lead, 2026-11-24 18:57 EST, after Architect run 31. Every builder is a
**ChatGPT chat session** with the GitHub connector. Its PR is its build and test environment: push to
run Lab CI, comment `/dev-run …` for targeted runs ([DEV_RUN](DEV_RUN.md)). No Codex sandbox is needed.
Codex is the **lead** only.

**Owner-started lanes.** The owner starts or resumes the existing builder chats with
`1:run` through `5:run`. Read the live lane row and linked packets on entry. Standing releases
and draft-ahead permissions apply in an active session. The manager/coordinator trial ended.

**How a lane works**
- **Long-running sessions.** A lane is a queue, not a single task. Keep working through it: implement,
  push, read CI, correct, post the Result, then start or draft the next task. Do not end the session
  while your lane has work ([continuation rules](README.md#builder-continuation-after-ci)).
- **Standing release.** A task is released when its predecessor in the same lane merges on `main`.
  Start it without asking, on its own `task/<issue#>-<slug>` branch and PR.
- **Draft-ahead.** While a PR waits on review or merge, you may open the next task in your lane as a
  draft PR. It rebases after its predecessor merges, and only merges after that.
- **Writers.** Stay inside your lane's paths. Shared files (catalogues, `CMakeLists.txt`, workflows)
  follow the merge order named in the row. A file in another lane needs that lane's PR merged first.
- **Auto-merge (owner, 2026-11-24).** For a task whose contract says `merge: lead` and has no review
  condition, the lead turns on auto-merge at release. It merges itself when the Result is posted and
  exact-head required checks are green. A reviewed task waits for its reviewer, then the lead or the Architect merges it.
- **Fewer stops ([SR20](STANDING.md)).** Start the next queue task yourself when its predecessor merges (open the issue if missing). Low findings never block. `merge: lead` tasks merge on exact-head green plus your Result. Ask for a Claude review once, at the merge-ready head.
- **Questions never stop a lane.** Add an [inbox](ARCHITECT_INBOX.md) row plus `needs/architect`, then
  work on the next independent item in your lane.

| Lane | Owns (paths) | Now | Then, in order (standing release) |
|---|---|---|---|
| **B5** `gpt-builder5` · **Engine** | `engine/` and tests, except E5v `engine/voice/` and B4 A63 `vco()` | **E5** [#429](https://github.com/kalharbi11/wirescape-lab/issues/429)/[#436](https://github.com/kalharbi11/wirescape-lab/pull/436) at `33c7d81`: A55/A59 incremental implementation; [Lab 45511697941](https://github.com/kalharbi11/wirescape-lab/actions/runs/45511697941) and targeted engine test fail line 615, `live.output_sample(1, 1, 0, 15) == 1.f`. Diagnose replacement/ring-out and correct the proven cause. Finish ER4, adopt/ring-out, bounded replay after collect, fade and ABI size guard, then gather exact-head evidence and one Claude review. | E3a after E5 (OB1.1). E5 first if E7 shares sidecar `commit`. |
| **B2** `gpt-builder2` · **I/O + sidecar** | `host/`, `modules/osc_in/`, `engine/control/` handlers | **E7** [#431](https://github.com/kalharbi11/wirescape-lab/issues/431)/[#442](https://github.com/kalharbi11/wirescape-lab/pull/442) at `1bce2f6`: Spectral C2 refusal passed targeted and [Lab 45511645596](https://github.com/kalharbi11/wirescape-lab/actions/runs/45511645596) green. Apply [A62](milestones/M4.md) to `freshModules`: host-uncarried instances only, OK hooks count as carried. Add SR17 schema/regen and protocol reply paragraph, and enumerate version-only resets in the Result. Keep E5/E7 writes disjoint. Older #444 MIDI snapshot hypothesis is unproven; latest #444 draft sanitizer passed. Bring a reproducible failure before a fix. | Ready-head evidence and one pinned Claude review. B3 owns hosted OSC exposure after E7; B1 owns subsequent CN rows. |
| **B4** `gpt-builder4` · **Sound** | Modules, sound facts, module tests; A63 `vco()`; separate #451 evidence files | **S7.9** [#440](https://github.com/kalharbi11/wirescape-lab/issues/440)/[#444](https://github.com/kalharbi11/wirescape-lab/pull/444) at `c86810e`: A63 oracle passed targeted port/ADSR and [Lab 45511569027](https://github.com/kalharbi11/wirescape-lab/actions/runs/45511569027). Non-draft for full evidence. Keep exact equality and verify M7 evidence before review. **Independent** [#451](https://github.com/kalharbi11/wirescape-lab/issues/451)/[#456](https://github.com/kalharbi11/wirescape-lab/pull/456) at `3913265`: A27 captures completed on both architectures. Record provisional numbers for B1 and repin only at its final base/head. | S7.9 then OB-d bundled-patch list. CHAOS provenance Low is separate. Keep catalogue/S0 writers serialized. |
| **B1** `gpt-builder1` · **Studio / OB-c / facts, sound overflow** | Studio/OB-c tests, `facts/dsp/edit_continuity.md`; module-local M7 paths | **S7.5** [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) at `c1601bc`: D5 published, uploaded digests verified. Owner starts the [pinned K1–K8 request](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7147921470). Lead merges after eligible approval. **S7.6 draft-ahead** [#314](https://github.com/kalharbi11/wirescape-lab/issues/314)/[#449](https://github.com/kalharbi11/wirescape-lab/pull/449) at `e772628`: endpoint-oracle correction passed [Lab 45511541508](https://github.com/kalharbi11/wirescape-lab/actions/runs/45511541508). [A27 provisional capture 45511845773](https://github.com/kalharbi11/wirescape-lab/actions/runs/45511845773) shows mode/tone remain +3.614/+2.658 dB above floor; locate raw peaks and correct the scoped DSP. Clocked division is ~2.271 dB below floor, unclocked `no_effect`; carry evidence and leave the literal floor interpretation to the Architect if needed. | After #291, sync Delay, give B4 final A27 pins and collect final M7 evidence. Then CN refresh after E5v/E5/E7, including A62 buffer rows and larger nontrivial-state witness, followed by A2 rewrite and OB-f1. |
| **B3** `gpt-builder3` · **Floater** | Assigned paths only | **E5v** [#439](https://github.com/kalharbi11/wirescape-lab/issues/439)/[#441](https://github.com/kalharbi11/wirescape-lab/pull/441) at `27f9881`: Lab/Golden green; strict x64 keyboard voices1/8 +1.148096/+1.126998%. SR6 round 2; [#459](https://github.com/kalharbi11/wirescape-lab/issues/459) supports scoped base/head function attribution before a correction. **A61** accepted [#433](https://github.com/kalharbi11/wirescape-lab/pull/433) native diagnostics at `8cb9d2e`; lead opened ready-head checks. [#457](https://github.com/kalharbi11/wirescape-lab/issues/457) additive OSC status fields can draft now, ready after #442. Wait for a real split before proposing a product fix. | After E5v paired G8 green, [#452](https://github.com/kalharbi11/wirescape-lab/issues/452) source-pinned CN voice-count capture must show 0 ms held-note silence. Then E5v lead merge, then optional Note Trigger #322. |

**Parked until after OB1** (branches kept): Gate Delay #333, CAT-1 #358 (+MB1), MT2 #176. Note Trigger #322 and M7 batch 2 were unparked in run 29.
**Postponed to the OB1 candidate:** Pi work (PI-1 #369, OB-g4, A31) and acceptance item 7.

**Manual starts:** `1:run` to `5:run` in the existing builder chats. Start `review` separately for the pinned S7.5 request.

## How the lead maintains this table
- Each lead run checks every lane: PR heads, exact-head CI, latest Result, labels. Refresh the
  "Now" cell and move finished tasks out. Keep evidence on GitHub.
- When a lane runs dry, add its next task from the roadmap. If none fits, lend the builder to the
  floater pool.
- The Architect refreshes this table on every Architect run as well. On a conflict, the lead's
  dispatch wins.

Signed: codex-lead, 2026-11-24, 18:57 EST
