#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run the actual pinned headless Player validator on the SC4 fixture."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", required=True, help="full headless commit SHA")
    parser.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.headless):
        parser.error("--headless must be a full lowercase 40-character SHA")
    bundle = args.bundle.resolve(strict=True)
    if not (bundle / "player.json").is_file():
        parser.error("bundle must contain player.json")
    build = Path(__file__).resolve().parents[2] / "build"
    build.mkdir(exist_ok=True)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    with tempfile.TemporaryDirectory(prefix="sc4-headless-", dir=build) as work:
        checkout = Path(work) / "headless"
        try:
            subprocess.run(["git", "init", "--quiet", str(checkout)], check=True, env=env, timeout=60)
            subprocess.run(["git", "-C", str(checkout), "remote", "add", "origin",
                            "https://github.com/kalharbi11/wirescape-headless.git"],
                           check=True, env=env, timeout=60)
            subprocess.run(["git", "-C", str(checkout), "fetch", "--depth=1", "origin", args.headless],
                           check=True, env=env, timeout=180)
            subprocess.run(["git", "-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"],
                           check=True, env=env, timeout=60)
            actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                             text=True, env=env, timeout=60).strip()
            if actual != args.headless:
                raise RuntimeError(f"Headless SHA mismatch: expected {args.headless}, got {actual}")
            print(f"SC4 headless validator: {actual}", flush=True)
            # No --scripts: validation must never execute copied scripts or start a device.
            return subprocess.run([sys.executable, "-m", "player", "check", str(bundle)],
                                  cwd=checkout, env=env, timeout=120).returncode
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            print(f"SC4 validator failed: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
