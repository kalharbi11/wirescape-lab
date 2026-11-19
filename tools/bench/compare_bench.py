# SPDX-License-Identifier: GPL-3.0-only
"""Compare ABI2 benchmark medians; optional unchanged M1-R gates."""
import argparse
import json
import math
import statistics
from pathlib import Path

RATIOS = ("poly8_vs_eight_mono_ratio", "modulated_ratio")
ENGINE_MODES = {"abi2_mono", "abi2_poly8", "abi2_eight_mono",
                "abi2_modulated", "vcf_constant", "vcf_audio_rate_cutoff"}


def load(path, historical=False):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    values = {}
    for row in data["rows"]:
        name = row["name"]
        if name in values or "|" in name or "\n" in name:
            raise ValueError("invalid or duplicate row name")
        repetitions = row.get("repetition_means_ns")
        if not repetitions or len(repetitions) < 5:
            raise ValueError("five repetition means required; legacy means are not medians")
        if any(not math.isfinite(x) or x <= 0 for x in repetitions):
            raise ValueError("repetition means must be positive and finite")
        values[name] = statistics.median(repetitions)
    # Historic pre-S4 base alone may include the retired ABI1 mono row.
    if historical:
        values.pop("abi1_mono", None)
    if set(values) != ENGINE_MODES:
        raise ValueError("exact six surviving benchmark cases required")
    for ratio, numerator, denominator in (
        (RATIOS[0], "abi2_poly8", "abi2_eight_mono"),
        (RATIOS[1], "abi2_modulated", "abi2_mono"),
    ):
        values[ratio] = values[numerator] / values[denominator]
    return values


def table(head, base=None):
    lines = ["| Metric | Head |" + (" Base | Head/base delta |" if base else ""),
             "|---|---:|" + ("---:|---:|" if base else "")]
    if base is not None and head.keys() != base.keys():
        raise ValueError("benchmark row sets differ")
    for name, value in head.items():
        unit = " ratio" if name in RATIOS else " median ns"
        label = name.replace("_", "\\_") + unit
        line = f"| {label} | {value:.6f} |"
        if base is not None:
            line += f" {base[name]:.6f} | {(value / base[name] - 1) * 100:+.2f}% |"
        lines.append(line)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args(argv)
    try:
        head = load(args.head)
        print(table(head, load(args.base, historical=True) if args.base else None))
    except (OSError, ValueError, KeyError, TypeError, statistics.StatisticsError) as exc:
        parser.error(str(exc))
    return int(args.gate and head[RATIOS[0]] > 1.00)


if __name__ == "__main__":
    raise SystemExit(main())
