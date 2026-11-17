<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M2 #139: pinned applyGraph continuity capture package (Worker2)

## Scope and source pin

Historical T0.13b before-values live in facts/dsp/edit_continuity.{json,md}
and facts/BASELINE.md. Their 119 witness rows were measured at commit
4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad, Linux x86_64 cloud
container, 2026-11-16T19:00Z, with three repeats. Retain that pin and its
numbers. M2 extension source base is main
4161b90fcc2fff48058ca50f44eafb15fe0ff764; do not label old data as
measurements at the new commit.

For this task, use the exact 40-character PR #139 branch HEAD reported in
its signed Result, after the ONE cohesive implementation push. The build
must use that checkout, not a detached older main or a binary from a cache.
The runner's --built-head must equal git rev-parse HEAD and is checked
against the actual sidecar hello.engine.sha (12-character compiled pin).
The sidecar executable is also SHA-256 hashed. The authored PR/result
must state both full source SHA and binary SHA-256.

## Reproduction (Linux x64 cloud worker with supported native build)

Commands are relative to the repo root; no physical audio/MIDI devices or
LAN flags are authorized. The engine harness always sets --null-audio,
isolated --settings, 48000 Hz, 256 frames, --capture-null-sink. Its OSC In
probe uses loopback only, never LAN. Never record usernames, hostnames,
absolute worker paths or real device names in published facts.

1. Check out the exact full PR #139 HEAD and verify it matches the Result.
2. Build the same pinned native target used by the existing PV1 drift CI:
   cmake -S native -B build/continuity -G Ninja -DCMAKE_BUILD_TYPE=Release
   cmake --build build/continuity --target wirescape_engine_sidecar --parallel 4
   If the hosted dependency proxy refuses tar archives, use the CURRENT.md
   byte-identical pinned git-archive seeding recipe, verifying URL_HASH
   before configuring; never skip integrity checks or change native code.
3. Run the unchanged synthetic workflow command:
   python -m unittest discover -s bench/continuity/tests -v
4. On that exact clean checkout, run the following one measurement packet
   (the shell lines marked backslash are continuation lines):

       HEAD="$(git rev-parse HEAD)"
       python bench/continuity/run.py \
         --engine build/continuity/wirescape-engine \
         --built-head "$HEAD" --repeats 3 \
         --only "applyGraph identical" "applyGraph Groove steps" \
           "applyGraph Groove length" "applyGraph voice count" \
           "applyGraph OSC In row" "applyGraph one parameter" \
           "applyGraph deleted module" "applyGraph restored module" \
         --keep /ARTIFACT_AREA/applygraph-raw \
         --out /ARTIFACT_AREA/applygraph-measured

   /ARTIFACT_AREA is an owner-approved worker artifact directory OUTSIDE
   the repository and is not a literal host path to publish. Use an
   approved artifact store/link for review; do not commit raw captures
   or ZIPs over 1 MB. No fresh values are claimed before this executes.

## Exact required return package

- A full source commit SHA, CMake/C++/Python versions, machine class
  (OS/arch/CPU model, not hostname), UTC date, and binary SHA-256. Report
  the native configure/build command, exit codes and any seeding hashes.
- The generated applygraph-measured.json and .md, including all eight edit
  cases, three repeats and every continuing-witness/subject row: silence,
  dip, phase/time-slip, jump, disturbed span, restarted where observable,
  and each worst-of-three; unsupported observations get explicit reasons
  and nulls, never manufactured zeros.
- Three no-edit reference runs (one per repeat) plus eight edit captures
  per repeat = 27 raw float32 captures and 27 corresponding .marks files.
  The JSON records per-file relative name, SHA-256, byte count and repeat;
  independently recompute hashes before fact merge. The sidecar's marks
  retain re/type/ok/gen/b0/b1 for load, note and edit. Each row retains
  gen-before/gen-after, reply.ok/code, applyGraph path/replaced/unapplied,
  the actual b0/b1 bracket width, full marks, reference alignment
  interval/uncertainty and residual; no timestamp-only edit location.
- The original 119-row facts JSON and Markdown are NOT overwritten by
  the measurement command. After Worker2/root verifies actual raw bytes,
  append the M2 rows in a separately pinned section and remove only the
  eight formerly unsupported M2 labels. Keep every old row's numbers,
  original commit/date/machine, metric definition and original R7 marks.
  No pass/fail column or device-audio/sound-parity claim.

If build, execution, capture upload or artifact retrieval is unavailable,
send a BLOCKED Result with the exact failed step, source pin, absent
artifacts and evidence gap. A green CI synthetic job alone cannot supply
the missing 24 three-repeat measurements or real marks. Root independently
reviews and controls acceptance; do not self-merge.
