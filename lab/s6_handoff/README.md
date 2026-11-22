<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S6 cloud takeover

The owner authorized any B4 cloud agent to take over issue #294 and draft PR #295. The takeover supersedes earlier agent instructions that limited the writer to this local chat or told a previous cloud B4 writer to stand down. Claim the sole writer slot on the PR before editing and use the existing task/294-m1-s6 branch. The owner did not waive the contract, evidence gates, device-off rules, independent Claude review, or lead-only merge.

## Evidence and replay

- Work started against frozen baseline `23443691b4950b4747ade943d7d8602d281938fc`. The verified rehearsal uses `a72f50d84b1051401c65e9babf74bf2ff6b49778`. Recheck current main and the draft branch before claiming the slot. Preserve history and use fast-forward publication only.
- The guard classified the 76 reported entries and found 30 additional path consumers. The replay covers 444 moves and 103 modified files. It preserves 108 configured CTest names, public module header bytes, committed fixture and provenance bytes. C99 header and banned-includes CTests passed locally, and generated protocol matched.
- Baseline and scratch replay both fail device-off S0 snapshot at byte 213 in s0_status.ndjson (469 expected bytes, 997 produced). Await lead/Architect disposition of that baseline failure. Keep the snapshot and assertions intact in S6.
- The checked-in plan remains partial. Do not treat this tree as the PR source, review-ready, or acceptance evidence 1–6. Do not publish the scratch commit. Continue exact path review and preserve assertions, targets, artifacts and triggers.

Use a separate clean clone pinned to a72f50d as SOURCE and the #295 clone as HANDOFF. Run from HANDOFF. Paths below are shell variables set to those clone roots.

```sh
python3 lab/m1_s6_preview.py --root "$SOURCE" > /tmp/s6-preview.json
python3 lab/s6_handoff/s6_reference_audit.py "$SOURCE" /tmp/s6-preview.json > /tmp/s6-reference-audit.json
python3 lab/s6_handoff/s6_replay_moves.py "$SOURCE" /tmp/s6-reference-audit.json --entry-plan lab/s6_handoff/s6-native-wiring-plan.json
```

Expected partial tree: `3a23a1cd0832f1e5d98c9ac94df05779a57e713d`. The replay writes scratch Git objects and an isolated index. It checks source Git-blob SHA-256 and exact line anchors regardless of checkout line endings, then verifies the generated tree and leaves the checkout clean. Use the four plan scripts to reconstruct the reviewed subsets from the same preview; the combined JSON is the exact replay input.

## Next

1. Resolve the baseline S0 disposition with the lead. Complete the remaining active tooling and workflow reference review against live main, including split-root scans and historical baseline consumers.
2. Convert the partial exact edits into the complete deterministic migration script and manifest. Verify final tree deltas, permissions and frozen bytes on an isolated checkout.
3. Obtain all current 0006 evidence and post a signed Result on #295. Keep it draft until evidence and independent replay requirements are met. Lead owns dispatch and merge.

Signed: gpt-builder4, 2026-11-21 EST
