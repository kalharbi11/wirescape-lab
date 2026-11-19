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
import lzma
from pathlib import Path
import re
import sys
import zlib

from freeze import file_kind, verify_inventory

MAX_CASE_BYTES = 1024 * 1024
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024


# Exact Architect A7 S4 reference from the immutable hosted ABI1 capture.
S4_CASE = "qt_free_saved_v2_abi1_48000_128_96000"
S4_SHA256 = "485456df74522320047a4ae9361e5de52042c15079ccb4549982fbe41d887419"
S4_BLOB_SHA1 = "4dc06c72035a30979ea84beacc7664999bce77b6"

def decode_case(name, entry):
    if name != S4_CASE:
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


def load_s4_qt_free_fixture(path, expected):
    """Decode only the architect-authorized saved-v2 comparison reference."""
    if not isinstance(expected, dict) or path.name != expected.get("document"):
        raise ValueError("missing S4 fixture manifest entry")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError("oversized S4 fixture document")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "abi1-s4-qt-free-frozen-v1":
        raise ValueError("unknown S4 fixture schema")
    source = document.get("source", {})
    if (source.get("workflow_run") != expected.get("workflow_run")
            or source.get("artifact_id") != expected.get("artifact_id")
            or source.get("capture_commit") != expected.get("source_commit")
            or source.get("decoded_git_blob_sha1") != expected.get("git_blob_sha1")):
        raise ValueError("S4 capture provenance mismatch")
    cases = document.get("cases")
    if not isinstance(cases, dict) or set(cases) != {S4_CASE}:
        raise ValueError("S4 frozen case inventory mismatch")
    entry = cases[S4_CASE]
    if (expected.get("id") != S4_CASE or expected.get("samples") != 96000
            or expected.get("bytes") != 384000 or expected.get("sha256") != S4_SHA256
            or expected.get("git_blob_sha1") != S4_BLOB_SHA1
            or entry.get("samples") != expected["samples"]
            or entry.get("bytes") != expected["bytes"]
            or entry.get("sha256") != expected["sha256"]):
        raise ValueError("S4 frozen length or digest manifest mismatch")
    raw = decode_case(S4_CASE, entry)
    blob_header = ("blob " + str(len(raw)) + "\0").encode("ascii")
    if hashlib.sha1(blob_header + raw).hexdigest() != S4_BLOB_SHA1:
        raise ValueError("S4 decoded Git blob digest mismatch")
    return raw


def unpack_frozen(manifest_path, corpus_dir, destination, machine, s4_fixture=None):
    """Unpack exact recorded ABI1 words (no ABI1 code or devices involved).

    Every byte is checked against the original source-machine capture digest.
    Only 18 Windows module block=256 cases override the common Linux corpus.
    """
    if machine not in ("linux-x64", "linux-arm64", "windows-x64"):
        raise ValueError("unsupported fixture machine")
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    if doc.get("schema") != "abi1-reference-word-hash-manifest-v1":
        raise ValueError("unsupported frozen-reference schema")
    captures = doc.get("capture_sources", {})
    if set(captures) != {"linux-x64", "linux-arm64", "windows-x64"}:
        raise ValueError("missing platform capture provenance")
    source = doc.get("capture_source_commit")
    if not isinstance(source, str) or not re.fullmatch("[0-9a-f]{40}", source):
        raise ValueError("invalid source commit")
    expected = doc.get("linux_common_and_windows_unchanged")
    if not isinstance(expected, dict):
        raise ValueError("missing expected case map")
    verify_inventory(set(expected))
    meta = doc.get("corpus", {})
    def unseal(info, max_bytes):
        chunks = info.get("chunk_filenames")
        if not isinstance(chunks, list) or not chunks:
            raise ValueError("missing frozen corpus chunks")
        packed = ""
        for name in chunks:
            if not isinstance(name, str) or not re.fullmatch("abi1_(?:common|windows)_[0-9]{3}\\.b64", name):
                raise ValueError("invalid frozen chunk filename")
            lines = (corpus_dir / name).read_text(encoding="ascii").splitlines()
            if len(lines) != 2 or lines[0] != "# SPDX-License-Identifier: GPL-3.0-only":
                raise ValueError("invalid frozen-reference SPDX/payload lines: " + name)
            if not re.fullmatch("[A-Za-z0-9+/=]+", lines[1]):
                raise ValueError("invalid base64 payload: " + name)
            packed += lines[1]
        compressed = base64.b64decode(packed, validate=True)
        if len(compressed) != info.get("lzma_bytes"):
            raise ValueError("compressed corpus length mismatch")
        if hashlib.sha256(compressed).hexdigest() != info.get("lzma_sha256"):
            raise ValueError("compressed corpus digest mismatch")
        if info.get("uncompressed_bytes", 0) > max_bytes:
            raise ValueError("oversized frozen corpus")
        # Stream-decompress with a bounded output allocation.
        dec = lzma.LZMADecompressor()
        raw = dec.decompress(compressed, max_length=max_bytes+1)
        if not dec.eof or dec.unused_data or len(raw) != info.get("uncompressed_bytes"):
            raise ValueError("frozen corpus truncation or length mismatch")
        if hashlib.sha256(raw).hexdigest() != info.get("uncompressed_sha256"):
            raise ValueError("uncompressed corpus digest mismatch")
        return raw
    raw = unseal(meta, 64 * 1024 * 1024)
    raw_by_case = {}
    pos = 0
    for name in sorted(expected):
        entry = expected[name]
        n = entry.get("bytes")
        if not isinstance(n, int) or not 0 < n <= 1024 * 1024 or n % 4:
            raise ValueError("invalid captured float count: " + name)
        data = raw[pos:pos+n]
        if len(data) != n or hashlib.sha256(data).hexdigest() != entry.get("sha256"):
            raise ValueError("ABI1 source case digest mismatch: " + name)
        raw_by_case[name] = data
        pos += n
    if pos != len(raw):
        raise ValueError("extra sample bytes in frozen corpus")
    windows = doc.get("windows_overrides", {})
    delta = meta.get("windows_override", {})
    if set(delta.get("case_names", [])) != set(windows):
        raise ValueError("Windows override inventory mismatch")
    if machine == "windows-x64":
        data = unseal(delta, 1024 * 1024)
        pos = 0
        for name in sorted(windows):
            n = windows[name].get("bytes")
            if not isinstance(n, int) or n % 4:
                raise ValueError("invalid Windows byte count: " + name)
            block = data[pos:pos+n]
            if len(block) != n or hashlib.sha256(block).hexdigest() != windows[name].get("sha256"):
                raise ValueError("Windows source case digest mismatch: " + name)
            raw_by_case[name] = block
            pos += n
        if pos != len(data):
            raise ValueError("extra Windows sample bytes")
    descriptors = doc.get("legacy_descriptors")
    if not isinstance(descriptors, dict) or len(descriptors) != 8:
        raise ValueError("missing captured descriptor metadata")
    for name, entry in descriptors.items():
        value = entry.get("utf8")
        if not isinstance(value, str) or not value.startswith("id\t"):
            raise ValueError("invalid ABI1 descriptor: " + name)
        if hashlib.sha256(value.encode("utf-8")).hexdigest() != entry.get("sha256"):
            raise ValueError("ABI1 descriptor digest mismatch: " + name)
    s4_raw = load_s4_qt_free_fixture(s4_fixture, doc.get("s4_qt_free")) if s4_fixture else None
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(raw_by_case.items()):
        (destination / (name + ".f32le")).write_bytes(data)
    for name, entry in sorted(descriptors.items()):
        (destination / (name + ".desc")).write_bytes(entry["utf8"].encode("utf-8"))
    if s4_raw is not None:
        (destination / (S4_CASE + ".f32le")).write_bytes(s4_raw)
    result = {"machine": machine, "source_commit": source, "cases":len(raw_by_case),
              "bytes":sum(len(x) for x in raw_by_case.values()),
              "source_artifact_id":captures[machine]["artifact_id"]}
    (destination / "capture_source.json").write_text(json.dumps(result,sort_keys=True)+"\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--s4-fixture", type=Path)
    parser.add_argument("--verify-s4", type=Path)
    parser.add_argument("--corpus-dir", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--machine", required=True,
                        choices=("linux-x64", "linux-arm64", "windows-x64"))
    args = parser.parse_args(argv)
    if args.verify_s4:
        raw = args.verify_s4.read_bytes()
        if len(raw) != 384000 or hashlib.sha256(raw).hexdigest() != S4_SHA256:
            raise ValueError("unpacked S4 ABI1 reference hash mismatch")
        print("ABI1_S4_FROZEN_HASH_OK", S4_SHA256)
    elif args.manifest and args.corpus_dir:
        result = unpack_frozen(args.manifest, args.corpus_dir,
                               args.destination, args.machine, args.s4_fixture)
        print("ABI1_FROZEN_UNPACKED", result)
    elif args.fixtures:
        files = sorted(args.fixtures.glob("abi1_" + args.machine + "_*.json"))
        if not files:
            parser.error("no source ABI1 reference files for machine " + args.machine)
        result = unpack(files, args.destination, args.machine)
        print("ABI1_REFERENCE_UNPACKED", result["machine"],
              result["source_commit"], result["case_count"])
    else:
        parser.error("expected --manifest and --corpus-dir or --fixtures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
