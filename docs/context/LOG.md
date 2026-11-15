<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Lab log (newest first)

## 2026-11-15 — device results filed (Keel)
Done: removed the two owner-uploaded zips from `tests/` (21 MB, duplicates of the draft release
`bench-2026-11-14`; still in history at `6edc84a`). Unpacked the small files of the cd9a6a5 device-off
archives and the new Windows validation zip (842d682) into `facts/device/results/`, now laid out as
`<machine>/<date>-<sha7>-<scope>/` with an index `README.md`.
State of main: Pi 15-minute quick run done (b1d92be, local MIDI patch); Windows has build, dry run and
a speaker check only.
Next: Windows 15-minute quick run; Pi 60-minute full run; reference-tool comparisons.
Open for the owner: attach `windows-validation-2026-11-15-842d682.zip` to the draft release
`bench-2026-11-14`; upload future run zips to the release, not the repo.
Signed: Keel, 2026-11-15

## 2026-11-14 — setup (Keel)
Imported the product tree at the SNAPSHOT SHA; wrote AGENTS/CLAUDE, context docs, facts/bench skeleton.
Queued the first GPT issues (CI, fact pack, device harness, research). Fable has not started.
Signed: Keel, 2026-11-14
