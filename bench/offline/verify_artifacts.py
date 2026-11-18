# SPDX-License-Identifier: GPL-3.0-only
"""Validate mandatory measurements from a real Release offline-facts run."""
import argparse
import json
from pathlib import Path


def validate(folder):
    perf = Path(folder) / "perf"
    results = {}
    for section in ("module_cpu", "engine_cpu", "soak_failures",
                    "probe_failures", "denormal_spikes"):
        data = perf / (section + ".json")
        markdown = perf / (section + ".md")
        if not data.is_file() or not markdown.is_file():
            raise ValueError("missing artifacts for " + section)
        document = json.loads(data.read_text(encoding="utf-8"))
        if not document.get("provenance", {}).get("commit"):
            raise ValueError("missing commit provenance: " + section)
        results[section] = document["rows"]
    blocks = {64, 128, 256}
    engine = results["engine_cpu"]
    expected_engine = {"abi2_mono", "abi2_poly8", "abi2_eight_mono",
                       "abi2_modulated", "vcf_constant", "vcf_audio_rate_cutoff"}
    for block in blocks:
        rows = [r for r in engine if r.get("block_frames") == block]
        if (len(rows) != 6 or any(r.get("status") != "measured" for r in rows)
                or {r.get("name") for r in rows} != expected_engine):
            raise ValueError("exact six genuinely measured engine cases required for block " + str(block))
    denormal = results["denormal_spikes"]
    for block in blocks:
        if not any(r.get("block_frames") == block and r.get("status") == "measured"
                   and r.get("p99_ratio") is not None for r in denormal):
            raise ValueError("no measured 1e-30 input CPU ratio for block " + str(block))
    failures = results["soak_failures"]
    for row in failures:
        if not row.get("error_text"):
            raise ValueError("soak failure lacks exact diagnostic: " + str(row.get("patch")))
        if row.get("sidecar_result") not in ("ack", "refuse"):
            raise ValueError("soak failure lacks sidecar reply: " + str(row.get("patch")))
        if row["sidecar_result"] == "refuse" and not row.get("sidecar_message"):
            raise ValueError("sidecar refusal lacks message: " + str(row.get("patch")))
    for row in results["probe_failures"]:
        for key in ("module", "block_frames", "channels", "sample_rate_hz",
                    "instances", "input_mode", "stderr"):
            if key not in row:
                raise ValueError("probe failure missing " + key)
    return {"soak_failures": len(failures),
            "probe_failures": len(results["probe_failures"]),
            "measured_denormal": sum(r.get("status") == "measured" for r in denormal),
            "measured_engine_benchmarks": sum(r.get("status") == "measured" for r in engine)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.out_dir), sort_keys=True))


if __name__ == "__main__":
    main()
