# SPDX-License-Identifier: GPL-3.0-only
"""Strict per-render Callgrind Ir decoder; no elapsed-time or whole-run estimate."""
import re

FRAME_BLOCK = 256
ADOPT_SYMBOL = "wirescape::engine2::Engine::Impl::adopt_layout("


def parse_dump(text):
    """One labelled client-request dump, with one Ir event and exact totals."""
    fields = {}
    functions = {}
    current_callee = None
    adopt_calls = 0
    # A symbol may be referenced before its definition elsewhere in the dump.
    for line in text.splitlines():
        m = re.fullmatch(r"(?:c?fn)=\((\d+)\) (.+)", line)
        if m:
            ident, name = m.groups()
            if ident in functions and functions[ident] != name:
                raise ValueError("conflicting function compression IDs")
            functions[ident] = name
    for line in text.splitlines():
        if line.startswith(("desc: Trigger: ", "events: ", "summary: ", "totals: ")):
            key, _, value = line.partition(": ")
            if key == "desc":
                key = "trigger"
                value = value.removeprefix("Trigger: ")
            if key in fields:
                raise ValueError("duplicate profile metadata")
            fields[key] = value.strip()
        if line.startswith("cfn="):
            name = line[4:]
            m = re.fullmatch(r"\((\d+)\)(?: (.+))?", name)
            if m:
                name = m[2] or functions.get(m[1])
                if name is None:
                    raise ValueError("unknown callee compression ID")
            current_callee = name
        elif line.startswith("fn="):
            current_callee = None
        elif line.startswith("calls="):
            if current_callee is None:
                raise ValueError("call count without callee")
            m = re.match(r"calls=(\d+)(?:\s|$)", line)
            if not m:
                raise ValueError("invalid call count")
            if ADOPT_SYMBOL in current_callee:
                adopt_calls += int(m[1])
    label = re.fullmatch(r"Client Request: block-(\d+)", fields.get("trigger", ""))
    if not label or fields.get("events") != "Ir":
        raise ValueError("expected labelled render block with only Ir")
    if not all(re.fullmatch(r"\d+", fields.get(k, "")) for k in ("summary", "totals")):
        raise ValueError("invalid or missing Ir total")
    ir = int(fields["summary"])
    if ir <= 0 or ir != int(fields["totals"]):
        raise ValueError("nonpositive or inconsistent Ir total")
    return {"block": int(label[1]), "ir": ir, "adopt_calls": adopt_calls}


def summarize(rows, kind, fade_frames, request_block=None):
    """Require an observed publication; do not infer from wall-clock scheduling."""
    rows = sorted(rows, key=lambda r: r["block"])
    if (not rows or any(type(r[k]) is not int or r[k] < 0
                        for r in rows for k in ("block", "ir", "adopt_calls"))
            or any(r["ir"] == 0 or r["adopt_calls"] > 1 for r in rows)
            or [r["block"] for r in rows] != list(range(rows[0]["block"], rows[-1]["block"]+1))):
        raise ValueError("invalid, duplicate or missing render blocks")
    publications = [i for i, r in enumerate(rows) if r["adopt_calls"]]
    if kind == "single":
        if fade_frames != 0 or publications or request_block is not None:
            raise ValueError("single-instance measurement contains publication")
        return {"kind": kind, "max_block_ir": max(r["ir"] for r in rows), "window": rows}
    if kind != "dual" or type(fade_frames) is not int or fade_frames <= 0:
        raise ValueError("unknown measurement kind or invalid fade")
    if len(publications) != 2:
        raise ValueError("require actual edit and housekeeping publications")
    first, settled = publications
    if type(request_block) is not int or request_block not in [r["block"] for r in rows]:
        raise ValueError("missing actual request boundary")
    request = request_block - rows[0]["block"]
    end_fade = first + (fade_frames + FRAME_BLOCK - 1) // FRAME_BLOCK
    if request < 2 or request > first or end_fade + 2 > len(rows) or settled < end_fade or settled + 3 > len(rows):
        raise ValueError("incomplete transition window or premature housekeeping")
    # The old instance can remain in the transition layout until housekeeping.
    # Include every actual dual-instance block, not just the audible fade.
    return {"kind": kind,
            "request_block": request_block,
            "adoption_block": rows[first]["block"], "adoption_block_ir": rows[first]["ir"],
            "max_dual_instance_block_ir": max(r["ir"] for r in rows[first:settled]),
            "last_fade_block": rows[end_fade-1]["block"],
            "housekeeping_block": rows[settled]["block"],
            "max_audible_fade_block_ir": max(r["ir"] for r in rows[first:end_fade]),
            "housekeeping_block_ir": rows[settled]["ir"],
            "window": rows[request-2:settled+3]}
