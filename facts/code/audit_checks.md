<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Source checks made during the audit

Direct reads of the source at lab commit `7b334e5` (product tree = snapshot `44da1e4`), 2026-11-15 (ET),
Linux x86_64 cloud container, nothing executed.

| # | Question | Result | Where |
|---|---|---|---|
| 1 | FACT_PACK X5 / C2-Q5: does the SDK wrapper call the module's `reset()` after `prepare()`? | Yes. `Module<T>::prepare` calls `x.dsp.prepare(...)` and then `x.dsp.reset()` before returning `WS2_OK`. | `native/sdk/wirescape_sdk.h:203-205` |
| 2 | How many modules are in the compiled-in catalogue? | 34 `WS_APP_MODULE(...)` lines. | `native/control/module_catalog.inc:2-35` |
| 3 | How many lines of `engine2.cpp` mention `legacy`? | 37 (`grep -c legacy`). | `native/engine2/engine2.cpp` |
| 4 | Is the whole-document path separate from live replan in the sidecar? | `Session::commit(Json patch, bool new_namespace)`; live replan is attempted only under `if (!new_namespace && rendering)`. | `native/sidecar/session.cpp:673,704` |
| 5 | Had the Pi 60-minute, Windows 15-minute or cross-tool results been filed? | No. `facts/device/results/` holds `pi5/2026-11-14-b1d92be-quick`, `pi5/2026-11-14-cd9a6a5-device-off`, `windows-laptop/2026-11-14-cd9a6a5-device-off`, `windows-laptop/2026-11-15-842d682-validation`; `facts/compare/measured/` holds `wirescape_limits.md` only. | `origin/main` at `7b334e5` |
