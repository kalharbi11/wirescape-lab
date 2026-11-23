#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""OB-b: read-only post-S6 Pi source-layout check (no install or launch)."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Source files only: generated binaries, node_modules and Pi hardware are not
# prerequisites for this path-only dry run. Native/CMakeLists.txt was retained
# by S6 and is still the CMake -S source used by tools/dev.py.
REQUIRED = {
    "retained CMake source root": "native/CMakeLists.txt",
    "engine core": "engine/engine2.h",
    "sidecar main": "host/sidecar/main.cpp",
    "sidecar session": "host/sidecar/session.cpp",
    "native CLI play": "host/cli/play.cpp",
    "OSC ingress service": "host/net/osc_service.cpp",
    "OSC output bus": "host/osc/out_bus.h",
    "OSC In module": "modules/osc_in/dsp.h",
    "OSC Out module": "modules/osc_out/dsp.h",
    "desktop entry source": "apps/desktop/main.ts",
    "desktop npm manifest": "apps/desktop/package.json",
    "studio npm manifest": "apps/studio/package.json",
    "Pi preflight": "tools/pi/preflight.py",
    "Pi source updater": "tools/pi/update-and-build.sh",
    "Pi device-off smoke": "tools/pi/app_smoke.py",
    "build and launch driver": "tools/dev.py",
    "source install guide": "docs/INSTALL.md",
}

# Guard against accidentally treating an unmigrated pre-S6 tree as Pi-ready.
MOVED_FROM = (
    "native/engine2/engine2.h",
    "native/sidecar/session.cpp",
    "native/io/net/osc_service.cpp",
    "native/modules2/osc_in/dsp.h",
)


def inspect(root: Path) -> list[tuple[str, bool, str]]:
    results = []
    for label, relative in REQUIRED.items():
        results.append((label, (root / relative).is_file(), relative))
    for relative in MOVED_FROM:
        results.append(("obsolete pre-S6 source absent", not (root / relative).exists(), relative))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="inspect source paths only, without git, builds, devices or writes")
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="source checkout to inspect (default: script's checkout)")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("specify --dry-run; this script never installs or launches Wirescape")
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("--root must name an existing checkout directory")
    checks = inspect(root)
    for label, ok, relative in checks:
        print(f"{'PASS' if ok else 'FAIL'} {label}: {relative}")
    failures = sum(not ok for _, ok, _ in checks)
    print(f"OB-b source paths: {len(checks) - failures}/{len(checks)} passed; "
          "source-only, no build, install, hardware or filesystem changes")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
