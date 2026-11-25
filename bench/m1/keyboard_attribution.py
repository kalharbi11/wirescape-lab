# SPDX-License-Identifier: GPL-3.0-only
"""Exclusive Ir attribution for uncompressed single-event Callgrind profiles."""
import argparse
from collections import Counter
import json
import posixpath
import re
from pathlib import Path


def exclusive(path, root):
    counts = Counter()
    obj = file = name = None
    call = False
    positions = None
    summary = None
    events = None
    parts = 0

    def normalize(value):
        const = str(root.resolve()) + "/"
        relative = root.name + "/"
        if value.startswith(const):
            return "<source>/" + posixpath.normpath(value[len(const):])
        if value.startswith(relative):
            return "<source>/" + posixpath.normpath(value[len(relative):])
        return value

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("part:"):
            parts += 1
        elif line.startswith("positions:"):
            positions = line.split()[1:]
        elif line.startswith("events:"):
            events = line.split()[1:]
        elif line.startswith("summary:"):
            summary = int(line.split()[1])
        elif line.startswith("ob="):
            obj = normalize(line[3:])
        elif line.startswith(("fl=", "fi=", "fe=")):
            file = normalize(line[3:])
        elif line.startswith("fn="):
            name = line[3:]
            if re.match(r"^\(\d+\)(?:\s|$)", name):
                raise ValueError("compressed function identity")
        elif line.startswith("calls="):
            if call:
                raise ValueError("missing call cost")
            call = True
        elif line[0] in "0123456789+-*":
            if positions != ["line"] or events != ["Ir"]:
                raise ValueError("expected line positions and Ir only")
            fields = line.split()
            if len(fields) != 2:
                raise ValueError("unexpected cost shape")
            cost = int(fields[1])
            if cost < 0 or name is None:
                raise ValueError("invalid cost")
            if call:
                call = False
            else:
                counts[(obj or "???", file or "???", name)] += cost
    if call or parts != 1 or summary is None or sum(counts.values()) != summary:
        raise ValueError("profile incomplete or exclusive counts do not match summary")
    return counts


def compare(base12, base24, head12, head24):
    rows = []
    for key in set(base12) | set(base24) | set(head12) | set(head24):
        b = base24[key] - base12[key]
        h = head24[key] - head12[key]
        if b or h:
            rows.append(dict(object=key[0], file=key[1], function=key[2],
                             base_ir_per_block=b / 12, head_ir_per_block=h / 12,
                             delta_ir_per_block=(h - b) / 12))
    return sorted(rows, key=lambda row: (-abs(row["delta_ir_per_block"]),
                                        row["object"], row["file"], row["function"]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-root", type=Path, required=True)
    p.add_argument("--head-root", type=Path, required=True)
    p.add_argument("--profiles", type=Path, required=True)
    p.add_argument("--voices", type=int, choices=(1, 8), required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    data = [exclusive(a.profiles / f"{side}-{a.voices}-{n}.callgrind", root)
            for side, root in (("base", a.base_root), ("head", a.head_root))
            for n in (12, 24)]
    rows = compare(*data)
    totals = [sum(c.values()) for c in data]
    b, h = (totals[1] - totals[0]) / 12, (totals[3] - totals[2]) / 12
    report = dict(voices=a.voices, totals=totals, base_ir_per_block=b,
                  head_ir_per_block=h, delta_ir_per_block=h-b, rows=rows)
    a.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"voices={a.voices} base={b:.6f} head={h:.6f} delta={h-b:.6f}")
    for row in rows[:30]:
        print(f'{row["delta_ir_per_block"]:+.6f} | {row["base_ir_per_block"]:.6f} | '
              f'{row["head_ir_per_block"]:.6f} | {row["file"]} | {row["function"]}')


if __name__ == "__main__":
    main()
