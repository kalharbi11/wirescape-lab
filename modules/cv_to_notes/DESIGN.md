<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CV to Notes design / provenance

Original GPL-3.0-only ABI2 C++ module developed for Wirescape Lab issue #327,
following `proposals/0020-note-tools-and-gate-delay.md` §2 (2026-11-22).
No third-party DSP, protocol revision, SDK ABI change or external dependency.
The descriptor, registration and event emission follow the existing
`notes_to_cv` and `chord` module conventions. Fixed 16-lane state keeps all
audio-thread processing allocation-free. The module is experimental.
