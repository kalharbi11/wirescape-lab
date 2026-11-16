#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate and unpack committed ABI1 reference candidates into build-only files.

No engine or device is invoked. The cases are frozen actual legacy outputs,
never synthesized by this program from an ABI2 result.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import zlib

from freeze import file_kind, verify_inventory

MAX_CASE_BYTES = 1024 * 1024
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024


def decode_case(name, entry):
    file_kind(name)
    if entry.get("codec") != "zlib9+b64":
        raise ValueError("unsupported fixture codec: " + name)
    samples = entry.get("samples")
    byte_count = entry.get("bytes")
    if (not isinstance(samples, int) or samples < 1
            or not isinstance(byte_count, int) or byte_count != samples * 4
            or byte_count > MAX_CASE_BYTES):
        raise ValueError("incorrect binary32 length: " + name)
    encoded = entry.get("compressed_b64")
    if not isinstance(encoded, str):
        raise ValueError("missing compressed bytes: " + name)
    packed = base64.b64decode(encoded, validate=True)
    inflater = zlib.decompressobj()
    body = inflater.decompress(packed, byte_count + 1)
    if len(body) != byte_count or not inflater.eof or inflater.unused_data:
        raise ValueError("malformed or unbounded compressed fixture: " + name)
    expected = entry.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError("missing SHA-256 digest: " + name)
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError("ABI1 fixture digest mismatch: " + name)
    return body


def unpack(files, destination, machine):
    references = {}
    descriptors = {}
    metadata = None
    for path in sorted(files):
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise ValueError("oversized fixture document: " + path.name)
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("schema") != "abi1-reference-candidate-v1":
            raise ValueError("unknown fixture schema")
        meta = document.get("metadata", {})
        if meta.get("machine") != machine:
            raise ValueError("wrong-platform fixture: " + path.name)
        if not re.fullmatch(r"[0-9a-f]{40}", str(meta.get("source_commit", ""))):
            raise ValueError("invalid source commit")
        if metadata is None:
            metadata = meta
        elif meta != metadata:
            raise ValueError("mixed ABI1 source or capture settings")
        cases = document.get("cases")
        if not isinstance(cases, dict) or len(cases) != document.get("case_count"):
            raise ValueError("invalid case inventory length")
        if document.get("suite") == "utility":
            desc = document.get("descriptor")
            key = "utility_" + str(document.get("group", "")).rsplit("_", 1)[0]
            if not isinstance(desc, dict) or desc.get("name") != key:
                raise ValueError("missing ABI1 utility descriptor " + key)
            value = desc.get("utf8")
            digest = desc.get("sha256")
            if not isinstance(value, str) or not value.startswith("id\t"):
                raise ValueError("invalid legacy descriptor content " + key)
            if hashlib.sha256(value.encode("utf-8")).hexdigest() != digest:
                raise ValueError("legacy descriptor SHA-256 mismatch " + key)
            if key in descriptors and descriptors[key] != value:
                raise ValueError("conflicting legacy descriptor " + key)
            descriptors[key] = value
        for name, entry in cases.items():
            if name in references:
                raise ValueError("duplicate frozen reference " + name)
            references[name] = decode_case(name, entry)
    verify_inventory(set(references))
    if set(descriptors) != {
        "utility_" + module for module in
        ("clock", "function_envelope", "ladder", "mixer",
         "noise", "output", "scale_offset", "slew")
    }:
        raise ValueError("incomplete frozen utility descriptor inventory")
    destination.mkdir(parents=True, exist_ok=True)
    for name, body in sorted(references.items()):
        (destination / (name + ".f32le")).write_bytes(body)
    for name, data in sorted(descriptors.items()):
        (destination / (name + ".desc")).write_text(data, encoding="utf-8")
    manifest = {
        "SPDX-License-Identifier": "GPL-3.0-only",
        "source_commit": metadata["source_commit"],
        "machine": machine,
        "case_count": len(references),
        "sha256": {name: hashlib.sha256(body).hexdigest()
                   for name, body in sorted(references.items())}
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--machine", required=True,
                        choices=("linux-x64", "linux-arm64", "windows-x64"))
    args = parser.parse_args(argv)
    files = sorted(args.fixtures.glob("abi1_" + args.machine + "_*.json"))
    if not files:
        parser.error("no source ABI1 reference files for machine " + args.machine)
    result = unpack(files, args.destination, args.machine)
    print("ABI1_REFERENCE_UNPACKED", result["machine"],
          result["source_commit"], result["case_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
