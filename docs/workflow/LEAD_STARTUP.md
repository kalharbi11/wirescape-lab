<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Local Codex lead: startup and continuity

Updated 2026-11-16 (New York). This is operational context, not a milestone contract or expanded authority.
The owner asked for autonomous delivery, existing ChatGPT builder dispatch, focused subagents,
cloud build support and scheduled reviews, with verification that dispatched work actually starts.

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
- Accepted contracts: M0 r2, M1 r2, M2 r2. PR87 scope/naming changes are now merged.
- Completed: PR63=2a02874, PR83=389ed265, PR69=cacf9ea, PR88=e0a1185d.
- B1: #67/70 frozen ABI1 data conversion. 983 cases staged; 18 Windows-specific module cases
  must stay distinct. Completion still needs committed reader data, ABI1 link removal and exact-head evidence.
- B2: #52/58 correction round1 at 9b8574854d6c90313b4036a8801862ed57d5dd08. Validate probe JSON
  faults/missing/malformed evidence despite exit0. Mocked tests pass; actual new profiling evidence pending.
  Runs 43835691748 instruction and 43835691687 Lab. Preserve 97 rows, 2 accepted Chord exceptions,
  original baselines/provenance, advisory gate and +3% threshold.
- B3: P2/#79 edit paths active. P1/#89 reviewed; source389ed265, 1317 expanded anchors/1245 excerpts
  checked by cloud. Lead added six anchors as f94b324e9b546037094ab9097133c824aa3ace86: fresh CI required.
- B4: #59 latency correction round1 active; S0/#84 assigned but paused until corrected59 returns review.
  Centered-envelope plus extra half-window offset advanced clean onset 41/44/90 samples at44.1/48/96k.
  Require independent known-start, phase/noise and timing-interval tests. No physical tests.
- Device73 metadata corrected to fa7c297b961fd78fa74060c5a5c318ec034c0003: 7 report headers,
  28 adjacent license sidecars, README table placement. Root checked zero raw artifacts changed.
  Await fresh CI then merge73 before fixing75 (5 headers/25 sidecars/table integration, raw bytes preserved).
- Queued: inventories80/81; S0/#84 paused; E0/#85 and PV1/#86 queued. Reconcile with M2r2 ordering:
  E0 and sidecar-related work merge before M1S5a or wait until S5b. No task dispatched merely by filing it.
- T0.5/#51/60 remains queued for R2 work. T0.13a/b still need explicit implementation packets.

## Cloud support
Fresh isolated baseline cacf9ea Release build passed 468 steps and 114/114 devices-off CTests.
Five fresh codeload dependency archives matched pinned SHA256. Toolchain: GCC14.2, Python3.12,
CMake4.2.3, Ninja1.13.0. This proves this Codex cloud environment, not Fable's separate Claude environment.
The cloud worker retains its isolated baseline checkout/build cache and support logs. Ask it for exact
current paths; do not commit machine-specific paths or copy builds from the older reference checkout.
Supported commands used: git_deps.py, headless CMake UI/Osc-fuzz OFF, tools/dev.py build --headless/test
with parallelism2 and existing toolchain PATH. No package install/settings changes were made.
Cloud finished citation validation and is collecting bounded null-sink S0 protocol transcripts under
build/support. It is support, not a fifth product writer; no tracked edits unless explicitly reassigned.

## Timers, usage, and replacement-lead handoff
Automation ID: wlab-lead-review. Existing target thread: 01a1e370-1e2a-79c0-a439-f0ac099e433a.
Normal cadence after reset: **45 minutes** (owner steering, 2026-11-16). At09:12UTC five-hour usage reached90%; next check temporarily scheduled
04:57 New York (09:57UTC), after reported09:55:41UTC reset. Recheck actual usage then use 45-minute intervals.
Do not redeem reset credits or buy credits automatically. Weekly quota is shared too.
Use brief changed-state checks; no CI/model waiting loops or duplicate expensive reruns.
When a new lead takes over: finish this chat's active turn, inspect automation and builders, then use
automation_update to retarget this existing heartbeat to the new local thread (or stop old before creating
one replacement). Preserve prompt/cadence/status intentionally. Do not leave two lead schedules active.
A new chat must verify its own messaging tools; access does not follow from its name.
Keep the computer on and desktop app running for local scheduled work.

## Fable timing
QUESTIONS has Q4 (protocol refusal/convergence behavior) and Q5 (owner bundled patch/preset reset
decision and protected constraints). Run **fable: run questions** at the next available Fable session:
those decisions matter for future contracts, not a reason to stop unaffected current work.
Use explicit Fable design work on the next needed contract while Codex builds. Do not schedule
milestone acceptance just because time elapsed: run **fable: run accept M0** after the lead publishes
the complete criterion-to-evidence acceptance report. Required Claude contract reviews are separate
base/head/invariant-pinned requests; queue them when those PRs are ready.

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
