<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Local Codex lead: startup and continuity

Updated 2026-11-16 (New York). This is operational context, not a milestone contract or expanded authority.
The owner asked for autonomous delivery, existing ChatGPT builder dispatch, focused subagents,
cloud build support and scheduled reviews, with verification that dispatched work actually starts.

## Owner priority now

CI/CLI test turnaround is first. CI1 r1 is accepted on live main; CI1.1 issue #95 is assigned to
builder3 after #91 Result entered review. It exclusively owns ci.yml. Read its K1–K5 invariants;
no feature dispatch ahead of this packet, no test removal, retries, gate weakening or cache work.
The approximate five-minute target is an estimate. Result-or-blocked checkpoint: 07:00 ET.

## Start here
1. Read live main AGENTS.md, docs/context/CODEX_LEAD.md, CURRENT.md, QUESTIONS.md and the accepted
   contracts named by CURRENT. The local device-results checkout may be stale: do not change its
   branch or touch untracked recordings/captures. Use isolated branches/worktrees or GitHub tools.
2. Verify actual tool availability and GitHub access. Working repository is **kalharbi11/wirescape-lab**.
   kalharbi11/wirescape is read-only reference. Never infer permission from an old chat title.
3. Inspect batch #82 and latest PR result comments/heads/CI. Snapshots below must be checked live.
4. Inspect the existing automation before creating anything. Exactly one lead owns dispatch.

## Messaging route verified in the local lead
Discover tools by name in ALL_TOOLS and invoke through functions.exec:
- mcp__codex_app__list_threads: find existing conversations/status.
- mcp__codex_app__read_thread: read actual recent assistant results.
- mcp__codex_app__send_message_to_thread: send authorized prompts.
For ChatGPT destinations omit hostId/model/thinking. For cloud Codex use returned hostId=durable.
Never invent a CLI/database workaround if a host lacks the messaging tool.
Read summaries are sometimes delayed; tool success and an appended user message are not startup proof.

| Existing conversation | Thread ID | Host |
| --- | --- | --- |
| WLAB &#124; B1 &#124; #67 ABI1 references | 6af9f4cc-666c-83ea-b313-c88bae30030d | ChatGPT |
| WLAB &#124; B2 &#124; #52 instruction gate | 6af9f4ea-01f8-83ea-b4b4-1cb7911b99db | ChatGPT |
| WLAB &#124; B3 &#124; #66 golden coverage | 6af9f4fb-1a94-83e9-a01e-f29873521c61 | ChatGPT |
| WLAB &#124; B4 &#124; #61 UI profiling | 6afa2bbc-169c-83ea-af54-c20821d3eee6 | ChatGPT |
| WLAB &#124; WORKER 2 &#124; Cloud | 6afad0f1-55a8-8191-975f-f008479ba02f | durable |

Names can lag task changes. B3/B4 titles do not define their current assignments.

## Dispatch and review loop
One task/branch/PR per builder; no independent queue pickup. Up to four builders, fewer on shared files.
Use a concise N:run packet with issue, accepted contract revision, allowed paths and exact criteria.
After sending, inspect status/results shortly afterward and again about 30–60 seconds later.
Require an active assistant run, tool-backed acknowledgement or substantive result. If idle with only
the prompt, retry once concisely and verify again. Never flood or duplicate an active remote run.
The owner manually started builders when delivery alone failed; ask for manual activation only when
the supported route remains demonstrably blocked. No automation of the ChatGPT desktop UI.
Review actual code/evidence, not merely green workflow summaries. Pin expected head on merges.
Two correction rounds maximum, then QUESTIONS; keep unaffected work moving. Builders never merge.
Follow each accepted task's lead/contract-review/Fable merge authority, not its historical A/B/C alone.

## Delivery snapshot (verify live)

Accepted M0 r2, M1 r2, M2 r2, CI1 r1. Q1–Q6 answered on main. Live CURRENT, PR results and
exact current-head runs supersede snapshots.
- CI1/#95: builder3 first priority, baseline counts and pre-edit K4 search returned.
- B1 now #51/PR60 R2; #70 corrected2c464fb, 983 frozen cases including18 Windows cases,
  signed Result awaiting current-head native/Golden/dependency evidence with lead.
- B2 now P3/#80; #58 merged64c1c6b after root code review and independent downloaded-artifact
  audit:95numeric+2Chord each architecture, hashes/provenance/arithmetic, zero>+3percent.
- B3 P1/#89 merged3ae712b after semantic/citation review and exact-head43837338789.
  P2/#91 independently audited184citations/231ranges/25files/19commands; root added refused-draft
  qualification and editorial fix as38057f3, fresh CI needed. Builder3 stays exclusively onCI1.
- B4 #59 round2 returned3e485dff to refuse callback-status capture damage (five new mocks);
  fresh Lab43847088024/Device43847088206 and Worker2 delta review pending. Earlier onsetfix
  passed independent720pulse oracle. Two rounds used; #84paused, no physical latency claimed.
- #73 merged e559634 after recorded independent factual/privacy/raw-blob review and exactheadCI.
  #75 corrected09a7cf3: main integration,5 reportheaders,25 license sidecars,18-row table;
  all25rawblobSHAs unchanged. Lab43846491720/Device43846491709 pending. #50 review remains.
- Earlier completed63=2a02874,83=389ed265,69=cacf9ea,88=e0a1185d.
- Queued81,84paused,85E0/86PV1, explicitT0.13a/b packets. CI1 first. E0/sidecar work before
  M1S5a or afterS5b. No arbitrary queue pickup. Facts/source pins remain historical evidence.

## Cloud support

The current support destination is Worker2 (ID in routing table), hostdurable, Codex backing.
Actual inventory: clean reference checkout at44da1e4, no lab checkout; GCC14.2/Python3.12.14 and
CMake4.2.3/Ninja1.13 in an existing tool venv. Its reference build cache is not lab evidence.
It has GitHub reads but cannot message back; local lead reads its result. Do not assume shared
artifacts/cache with the old worker. PR59 read-only delta support is pinned to3e485dff; no tracked edits,
native builds, package installs, settings changes, devices or LAN are authorized by that package.

Old worker history/cache are retained but receive no new tasks. Recorded old-worker baseline
cacf9ea build:468 steps,114/114 devices-off tests,5 pinned dependency hashes verified. This proves
that old Codex environment, not Worker2 or Fable's Claude environment. Its S0 capture task finished;
the catalogue hash matched two processes, status/ACK random tokens and telemetry times differed.
Those are support observations, not implemented S0 tests or normalized snapshots.

## Timers, usage, and replacement-lead handoff

Exactly one lead owns dispatch. Current local lead: **WLAB | LEAD | delivery 2**, thread
`01a1e3ca-c0d2-7d80-b1bc-6bcb93692b9a`, hostlocal, verified by actual app tools.
The existing automation **wlab-lead-review** was read back ACTIVE, targeting this thread every
**45 minutes**. Previous lead01a1e370-1e2a-79c0-a439-f0ac099e433a stopped dispatch.
Do not create a duplicate schedule. Local scheduled work requires the computer/app running.

At takeover usage was five-hour4percent/weekly84percent used; later checkpoint31percent/88percent.
These are snapshots, not current availability. These shared
account windows do not reset when chats rotate. Check actual usage before substantial work;
no reset-credit redemption or credit purchase. Missing context percentage is unavailable, not zero.
Keep changed-state checks brief, no model waiting loops or duplicate expensive CI runs.
Optional15-minute CI-only timers need a verified supported watcher, one owner and stop condition.
At any future handoff, save checkpoint/heads/results, verify new host/tools and retarget this
same existing heartbeat; old lead stops. Never claim successful scheduling from an unconfirmed call.

## Fable timing

Q1–Q6 have been answered. Q4 busy retry/convergence and Q5 bundled reset decisions are in
QUESTIONS; Q6 is accepted CI1. No new question is implied by old startup snapshots.
Keep M0/M1/M2 and golden24-identical criteria unchanged. The owner's own patches still need
the owner's disposition, as CURRENT records. CI1 implementation is the current first priority.
Run fable:run questions only for newly unresolved questions. Milestone acceptance follows a complete
criterion-to-evidence report, not elapsed time. Required Claude contract reviews remain separate
base/head/invariant-pinned requests; never merge merge:fable work by assumption.

## Minimal owner prompt for a replacement local chat
> lead: run. Read docs/workflow/LEAD_STARTUP.md and live CURRENT/contracts. You are the replacement
> local gpt-lead. I authorize messaging the listed WLAB builders/cloud worker and continued
> contract-delegated delivery/reviews/merges. Take over the existing heartbeat without duplicate
> dispatch; verify actual tool access and builder execution. Continue autonomously within the contracts.

Signed: gpt-lead, 2026-11-16


## Owner-requested local replacement and worker rotation

At the post-reset 04:57 New York check, once this handoff is reviewable and CI permits, the current
lead is authorized to create the replacement local lead automatically with the minimal owner prompt
above. Use the verified local lab project ID `f6ca202f-4314-44be-99fc-1fef2e97dc67`, after checking
list_projects still identifies it as local. create_thread target must be project/environment local;
verify returned hostId is local. Never choose a cloud or projectless fallback. Preserve local checkout
and captures. Transfer the existing heartbeat to the ready replacement thread and set a 45-minute
cadence; old lead stops dispatching after transfer. Resolve setup completion before using thread IDs.

Give builders longer cohesive issue-scoped tasks. The accepted one-active-task rule still applies;
the lead may assign a separate nonoverlapping task after the prior result enters review. Optional
15-minute CI follow-up is useful only through a verified supported scheduler/event watcher, with a
stop condition and one owner. Do not assume ChatGPT workers have timer capabilities or create
parallel model polling loops.

Retain old builder chats until their open PR ownership and correction handoffs are reconciled.
Snapshot: B1 #70 (and queued #60), B2 #58, B3 #89/#91, B4 #59 (and paused #84); root owns device
publication maintenance #73/#75 and existing #50 review. A fresh builder must reuse the same branch
and PR, read the signed result and latest lead findings, and prove actual startup before the old chat
is retired. Record each replacement thread ID here. Do not reset all chats mid-task.


## Explicit owner instruction: agent manages all chat rotation

Owner confirmation (2026-11-16): the lead, not the owner, creates the new local lead and takes care
of replacing ChatGPT builder chats after they close their PRs. No further routine confirmation is
needed for these named WLAB replacements and their task prompts.

The replacement lead must preserve the single existing heartbeat at a 45-minute cadence after
reset. It owns future timer updates, builder dispatch, delayed startup verification, result review,
correction routing and dependency-ready work. Timer creation/update must succeed before claiming it
is scheduled. Local scheduled work requires the machine and app running.

For each builder, first verify all PRs that old chat owns are merged or otherwise closed with an
explicit signed handoff/disposition; finish active correction rounds and account for queued tasks.
Do not close a PR merely to rotate its chat. Then create a fresh ChatGPT chat in the existing WLAB
ChatGPT project using supported app tools, read back its actual ID/project, update this routing table
and CURRENT, and dispatch the next contracted task with scope, branch/PR, evidence requirements and
result template. Verify an actual active/tool-backed run shortly afterward and again after 30–60
seconds; send success alone is insufficient. Mark the old chat superseded after the new route works;
preserve its history and never delete chats. If supported tools cannot create a ChatGPT replacement,
report the exact capability gap and keep unaffected work moving instead of substituting a cloud
Codex task or claiming creation succeeded. The local Codex lead must remain local.

The owner does not need to manually create chats or add takeover timers. Maintain one lead and one
lead heartbeat, with no duplicate writers or simultaneous old/new dispatch.


## Worker 2 and regular ChatGPT Chat mode (owner steering)

The active cloud support destination is **WLAB | WORKER 2 | Cloud**, thread
`6afad0f1-55a8-8191-975f-f008479ba02f`, host `durable`, backing kind Codex. The old cloud
worker `6afa6fc7-50e8-8191-a754-714000ff902e` is superseded for new tasks; retain its history and
artifacts, not further assignments. Its S0 capture task finished. Do not assume Worker 2 shares that
worker's checkout/cache: inspect its environment and retrieve needed artifacts before relying on them.
Old worker S0 evidence: clean baseline cacf9ea; catalogue56001bytes hash
`e409cfd907dd5e6ff7c480060da47f32ce41eac373afb4df79d9f9e591012b56` matched two processes;
status/ACK differed in random session tokens, telemetry in time. No normalization. Exact envelope
snapshot needs test-only deterministic session control; existing CLI has no control; parameter ACK
has no value echo. This is support evidence, not implemented S0 tests.

**Every ChatGPT builder/reviewer replacement must use regular Chat mode.** Not ChatGPT Work mode,
Codex, or Codex Cloud. The Codex local lead and Codex cloud support are separate explicit exceptions.
This is the owner's intended subscription allocation, not a verified guarantee of unlimited usage.
Verify backing kind and actual mode in supported tools/UI; project membership alone does not prove
Chat mode. Current create_thread ChatGPT target exposes Work Cloud, so do not misuse it as a Chat
replacement. If no supported regular-Chat creation route exists, report that specific capability gap
and keep existing regular Chat builders working; do not silently substitute a metered Codex task.

## Criteria for rotating long chats

Codex lead/cloud chats have priority for rotation to limit repeated context and usage. At every
batch/task boundary, prefer a fresh Codex chat when any of these is true:
- Context usage is reported at70percent or more, or repeated compaction has occurred.
- The thread spans two completed delivery batches or about four hours of active coordination.
- It repeatedly rereads old results, loses current ownership/state, confuses source/head evidence,
  or spends more context recovering history than executing the current packet.
These are operational heuristics, not claims that a fresh chat resets account quotas or always costs
less. If context metrics are unavailable, use elapsed batches and observed recovery friction; don't
fabricate a percentage. An owner request to rotate takes precedence.

Before rotation, commit/push a safe checkpoint, record exact heads/CI/results/remaining work and
capabilities in repository handoffs, then verify the replacement's actual host and tools. Transfer
one heartbeat and one task owner; no duplicate writers. A long active task may move only after an
explicit signed handoff and old writer stops. Never abandon uncommitted work for a fresh context.
For regular ChatGPT builders, rotate after the current round and all owned PRs close, unless the
owner explicitly authorizes a controlled mid-task transfer. Keep old histories. Update routing IDs.
Codex capacity resets remain shared across chats; preserve reported reset timing and weekly budget.


## Completed local lead transition

Created **WLAB | LEAD | delivery 2**, ready thread `01a1e3ca-c0d2-7d80-b1bc-6bcb93692b9a`,
verified returned host `local`, using the saved local lab project. The existing `wlab-lead-review`
heartbeat was retargeted to that thread with a45-minute interval. The previous local lead
`01a1e370-1e2a-79c0-a439-f0ac099e433a` stops dispatch after this transfer. Do not create another
lead heartbeat. Worker2 was sent its cloud-support role/introduction; actual startup/capabilities
must still be verified separately. Latest guide edits require current-headCI before PR92merge.


## Replacement lead verification checkpoint

The replacement read live main policies/contracts/questions, verified the transferred heartbeat and
local host/tools, and retained the local device checkout/captures. Regular Chat creation/mode
verification is unavailable in the current supported thread schema: create_thread offers WorkCloud
only for ChatGPT and list/read return backing kind but no Chat/Work mode field. Do not automate the
ChatGPT desktop UI or substitute Work/Codex. Existing builders remain in place while this gap and
open ownership persist. Record any later supported regular-Chat route before rotation.

Signed: gpt-lead, 2026-11-16

## Active takeover superseding historical snapshots — 2026-11-16

Sole local lead: WLAB | LEAD | 4, thread01a1e5ad-ea43-7b12-bc15-85ff572f1843.
Existing wlab-lead-review ACTIVE every45minutes on that thread; previous leads idle.
Read CURRENT and LOCAL_LEAD_HANDOFF for current routes/heads, not older tables above.
CI1r3 Q12 accepted PR119/fbbf771; CI1.4/#122 GPT-B4 before cache109/GPT-B2.
GPT regular Chat routes: B1 6afadca6-071c-83ea-a029-b22c1560a794;
B2 6afadc8d-5138-83ea-bb36-88048b6bf54d; B3 6afadc7c-9b44-83ea-be32-dbd465646ce0;
B4 6afadc5f-8478-83ea-89a0-6b2bedf3b2a9. Worker2 unchanged, hostdurable.
Owner now says Claude builders finish current tasks/corrections then stop; no new Claude work.
No automatic S3/E1b dispatch. Review116 is done, correct its current branch. Preserve local captures.
