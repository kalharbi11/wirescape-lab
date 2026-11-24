<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner Build releases

## OB-0 candidate

Status: **OB0 accepted, 2026-11-20 (claude-architect), on the OB contract's acceptance item 1.** Tag `owner-build-0` → `a440d7175659402474290e34a1d63b4404dcaa72` (annotated, immutable). The owner directed tagging before the Pi smoke. The Pi 5 source-install and smoke check is an owner-only follow-up on #198: recorded, not waived. A Pi failure gets a fix on `main` and a note here; the tag never moves.

- Integrated source candidate: `a440d7175659402474290e34a1d63b4404dcaa72`. M2 E1b-r, M7 baseline/S7.1/S7.2/S7.4 and OB-a1 are merged. [Delivery tracker](https://github.com/kalharbi11/wirescape-lab/issues/198)
- Reverb S7.2 keeps Mix continuous through zero and measured a maximum full-mode output of 0.9806554914 FS against a 1.00 FS limit. Lab, three-platform Golden and instruction checks passed on the reviewed PR head. [Independent review and measured evidence](https://github.com/kalharbi11/wirescape-lab/pull/255#issuecomment-7030178826)
- Existing personal patches are optional inputs to the folder runner. The owner intends to start a fresh patch collection. The shipped comparison fixtures are part of CI.

Use a separate, clean Pi 5 checkout of `kalharbi11/wirescape-lab` and the full candidate SHA above. Run the read-only preflight, exact-SHA Release source build, native tests, and device-off Electron smoke. The signed checklist gives the commands, expected reports and rollback checks. Keep the existing install and profile available. Once the release is accepted, resolve `owner-build-0` to a commit before using it as an install ref. [Pi 5 install and rollback checklist](https://github.com/kalharbi11/wirescape-lab/issues/198#issuecomment-7020888787)

Signed: codex-lead, 2026-11-20, 01:17 EST
