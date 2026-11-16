#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Package actual ABI1 test-capture words as portable, hashed fixture candidates.

The input files are produced by unmodified ABI1 DSP/engine calls in passing
comparison tests, not generated from ABI2 results. This does not run a device.
"""
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import zlib
from zoneinfo import ZoneInfo

MODULES = ("vco", "lfo", "vcf", "adsr", "vca", "clock",
           "function_envelope", "ladder", "mixer", "noise",
           "output", "scale_offset", "slew")
UTILITIES = ("clock", "function_envelope", "ladder", "mixer",
             "noise", "output", "scale_offset", "slew")
RATES = (44100, 48000, 96000)
BLOCKS = (1, 17, 256)
CHANNELS = (1, 4, 16)
PATTERNS = tuple(range(4))


def file_kind(name):
    if name in ("shim_steady", "shim_scripted"):
        return ("shim", "shim")
    module = re.fullmatch(r"module_(.+)_(44100|48000|96000)_(1|17|256)", name)
    if module and module.group(1) in MODULES:
        return ("module", module.group(1))
    utility = re.fullmatch(
        r"utility_(.+)_(44100|48000|96000)_(1|4|16)_(1|17|256)_([0-3])", name)
    if utility and utility.group(1) in UTILITIES:
        return ("utility", utility.group(1) + "_" + utility.group(2))
    raise ValueError("unknown fixture tag: " + name)


def verify_inventory(names):
    expected = {"shim_steady", "shim_scripted"}
    expected.update("module_%s_%d_%d" % (mod, rate, block)
                    for mod in MODULES for rate in RATES for block in BLOCKS)
    expected.update("utility_%s_%d_%d_%d_%d" % (mod, rate, chans, block, pattern)
                    for mod in UTILITIES for rate in RATES for chans in CHANNELS
                    for block in BLOCKS for pattern in PATTERNS)
    missing, unexpected = expected - names, names - expected
    if missing or unexpected:
        raise ValueError("capture inventory mismatch: %d missing; %d unexpected; first=%s" %
                         (len(missing), len(unexpected),
                          sorted(missing | unexpected)[:8]))
    return len(expected)


def capture_metadata(repo_root, machine, compiler_id, compiler_version, build_config):
    commit = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid source commit")
    return {
        "source_commit": commit,
        "reference_origin": "passing live ABI1 calls; not ABI2-generated samples",
        "capture_date_et": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": machine,
        "platform": platform.platform(),
        "cpu": platform.processor() or platform.machine(),
        "compiler_id": compiler_id,
        "compiler_version": compiler_version,
        "build_config": build_config,
        "channels": "per-case (1/4/16 for utility; mono engine shim)",
        "format": "binary32 little-endian raw words, zlib level 9 + base64 in JSON",
        "byte_order": "little",
        "source_test_files": [
            "native/tests2/integration_tests.cpp",
            "native/tests2/module_tests.cpp",
            "native/tests2/utility_port_tests.h",
        ],
        "reference_math": "ABI1 engine and legacy module DSP; original comparison asserts pass before packaging",
        "seed": "DspFixture ws2_config seed=42; legacy cases as source tests",
        "rates_hz": list(RATES),
        "blocks_frames": list(BLOCKS),
        "utility_channels": list(CHANNELS),
        "utility_patterns": [
            "sine", "single impulse", "quadratic-phase sweep", "unconnected"
        ],
        "utility_resets": 2,
        "integration_frames": 16384,
        "integration_rate_hz": 48000,
        "integration_block_frames": 256
    }


def package(capture_dir, artifact_dir, metadata, emit_chunks=False):
    raw = {}
    for path in sorted(capture_dir.glob("*.f32le")):
        if path.name != path.stem + ".f32le":
            raise ValueError("unexpected extension")
        name = path.stem
        kind, group = file_kind(name)
        body = path.read_bytes()
        if not body or len(body) % 4:
            raise ValueError("invalid binary32 byte count in " + name)
        if kind == "shim" and len(body) != 16384 * 4:
            raise ValueError("incorrect integration frame count " + name)
        if kind == "module" and len(body) % (2048 * 4):
            raise ValueError("incomplete module reference " + name)
        if kind == "utility" and len(body) % (2 * 1024 * 4):
            raise ValueError("incomplete utility reference " + name)
        raw[name] = (kind, group, body)
    verify_inventory(set(raw))
    groups = {}
    for name, (kind, group, body) in raw.items():
        key = (kind, group)
        groups.setdefault(key, {})[name] = {
            "samples": len(body) // 4,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "codec": "zlib9+b64",
            "compressed_b64": base64.b64encode(zlib.compress(body, 9)).decode("ascii")
        }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for (kind, group), samples in sorted(groups.items()):
        filename = "abi1_%s_%s_%s.json" % (metadata["machine"], kind, group)
        doc = {
            "SPDX-License-Identifier": "GPL-3.0-only",
            "schema": "abi1-reference-candidate-v1",
            "metadata": metadata,
            "suite": kind,
            "group": group,
            "case_count": len(samples),
            "cases": samples,
        }
        content = json.dumps(doc, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(content.encode()).hexdigest()
        (artifact_dir / filename).write_text(content + "\n", encoding="utf-8")
        results.append((filename, digest, len(content), len(samples)))
        if emit_chunks:
            print("ABI1_FREEZE_BEGIN", filename, len(content), digest, flush=True)
            for offset in range(0, len(content), 1200):
                print("ABI1_FREEZE_CHUNK", filename, offset // 1200,
                      content[offset:offset + 1200], flush=True)
            print("ABI1_FREEZE_END", filename, flush=True)
    return results


def machine_name():
    os_name = (os.environ.get("RUNNER_OS") or platform.system()).lower()
    arch = (os.environ.get("RUNNER_ARCH") or platform.machine()).lower()
    if "windows" in os_name:
        if arch not in ("x64", "x86_64", "amd64"):
            raise ValueError("unsupported Windows architecture: " + arch)
        return "windows-x64"
    if "linux" in os_name:
        if arch in ("x64", "x86_64", "amd64"):
            return "linux-x64"
        if arch in ("arm64", "aarch64"):
            return "linux-arm64"
    raise ValueError("unsupported source machine: %s %s" % (os_name, arch))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--compiler-id", required=True)
    parser.add_argument("--compiler-version", required=True)
    parser.add_argument("--build-config", default="Release")
    parser.add_argument("--emit-chunks", action="store_true")
    args = parser.parse_args(argv)
    metadata = capture_metadata(args.repo_root, machine_name(),
                                args.compiler_id, args.compiler_version,
                                args.build_config)
    files = package(args.capture_dir, args.artifact_dir, metadata, args.emit_chunks)
    print("ABI1_FREEZE_SUMMARY", json.dumps(
        {"source_commit": metadata["source_commit"], "machine": metadata["machine"],
         "files": len(files), "cases": sum(row[3] for row in files),
         "total_json_bytes": sum(row[2] for row in files),
         "manifest_sha256": hashlib.sha256(json.dumps(files).encode()).hexdigest()},
        sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
