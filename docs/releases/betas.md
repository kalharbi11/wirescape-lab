<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Betas

One row per owner test build, oldest first (naming: [README.md](README.md)). Build each beta in its
own folder named after it: `~/wirescape/beta_NN` on the Pi, `C:\wirescape\beta_NN` on Windows
([../INSTALL.md](../INSTALL.md)). A beta becomes **v1.0** only when the owner accepts it as V1.

| Beta | Commit | Date (ET) | Built on | Owner result |
|---|---|---|---|---|
| beta_01 | `8fce43d` | 2026-11-28 | Pi 5 (folder `~/wirescape/wirescape-8fce43d`) | Build and app smoke passed; 137/138 headless tests. `runtime_module_config_tests` failed on config padding (fix: #768) |
| beta_02 | main after #768 merges | | Pi 5, Windows | pending |
