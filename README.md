<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Wirescape lab

A working copy of the Wirescape product (modular synth: C++17 realtime engine
`wirescape-engine`, Electron app, TypeScript Studio UI) for a review,
measurement and restructuring pass. The product tree came from
`kalharbi11/wirescape` at the SHA in [`docs/context/SNAPSHOT.md`](docs/context/SNAPSHOT.md),
without that repo's planning and agent process.

- New lead session: read the [delivery-lead brief](docs/context/CODEX_LEAD.md), then send `lead:run`.
- Project status: [builder queue](docs/workflow/BUILDERS.md), [milestone roadmap](docs/workflow/ROADMAP.md), [Architect handoff](docs/workflow/CURRENT.md), and [workflow and labels](docs/workflow/README.md).
- What the product is and how to build it: [`docs/PRODUCT_README.md`](docs/PRODUCT_README.md), [`docs/INSTALL.md`](docs/INSTALL.md)
- How it works today: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/specs/`](docs/specs/)
- Why it looks like this, and what is left over: [`docs/context/`](docs/context/)
- Measurements and neutral data: [`facts/`](facts/README.md), produced by [`bench/`](bench/README.md)
- Proposals (the only place for opinions): [`proposals/`](proposals/)

Nothing in `facts/` or `docs/context/` is a plan. Licences: GPL-3.0 overall; the
SDK, ABI 2 header and voice library are MIT (`LICENSES/`). Wirescape is a
trademark ([TRADEMARKS.md](TRADEMARKS.md)).
