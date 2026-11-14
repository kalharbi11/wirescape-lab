# SPDX-License-Identifier: GPL-3.0-only
"""Device-free protocol probes for Wirescape graph capacity refusal.

Run only with a built engine executable. The subprocess receives --null-audio,
a fresh settings path, and no audio/MIDI/LAN consent flags.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "bench" / "compare"))
from generate_scaling import scaling_patch


def probe(executable, folder):
    folder.mkdir(parents=True, exist_ok=True)
    engine = [str(executable.resolve()), "--null-audio",
              "--settings", str((folder / "settings.json").resolve()),
              "--rate", "48000", "--block", "256"]
    commands = []
    replies = []
    stderr_path = folder / "engine-stderr.log"
    with stderr_path.open("wb") as stderr:
        process = subprocess.Popen(engine, cwd=ROOT, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=stderr, bufsize=0)
        try:
            line = process.stdout.readline()
            if not line:
                raise RuntimeError("sidecar exited without a hello")
            hello = json.loads(line)
            if hello.get("type") != "hello" or hello.get("v") != 0:
                raise RuntimeError("expected protocol v0 hello")

            n16 = scaling_patch(16, enforce_graph_limit=False)
            assert len(n16["modules"]) == 96
            n1 = scaling_patch(1)
            n1["connections"] = [n1["connections"][0]] * 129
            for id_, label, patch in (("limit-n16", "scaling-n16-96-nodes", n16),
                                       ("limit-edges", "129-connections", n1)):
                request = {"v": 0, "id": id_, "type": "loadGraph", "patch": patch}
                commands.append({"label": label, "type": request["type"],
                                 "modules": len(patch["modules"]),
                                 "connections": len(patch["connections"]),
                                 "id": id_})
                process.stdin.write(json.dumps(request, separators=(",", ":"),
                                                allow_nan=False).encode("utf-8") + b"\n")
                process.stdin.flush()
                for _ in range(500):
                    response_line = process.stdout.readline()
                    if not response_line:
                        raise RuntimeError("engine closed before refusal reply")
                    response = json.loads(response_line)
                    if response.get("re") == id_:
                        break
                else:
                    raise RuntimeError("no matched engine reply after 500 protocol lines")
                replies.append({"label": label, "response": response})
                if response.get("ok") is not False or response.get("code") != "limit" or response.get("message") != "Graph capacity exceeded":
                    raise RuntimeError("unexpected graph-capacity reply: " + json.dumps(response))
            return {"engine": "real_null_sink", "commands": commands, "replies": replies,
                    "hello": {"protocol": hello.get("protocol"), "module_type_count":
                              len(hello.get("catalogue", {}).get("modules", []))}}
        finally:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if process.returncode != 0 and sys.exc_info()[0] is None:
                raise RuntimeError(f"null sink sidecar exited {process.returncode}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--results", type=Path, default=HERE / "results" / "limits")
    args = parser.parse_args()
    if not args.engine.is_file():
        parser.error("--engine is not a built executable")
    dest = args.results / dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    i = 0
    folder = dest
    while folder.exists():
        i += 1
        folder = Path(str(dest) + "-" + str(i))
    evidence = probe(args.engine, folder)
    (folder / "analysis.json").write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n",
                                           encoding="utf-8")
    lines = ["# Null-sink graph-limit protocol evidence", "",
             "Backend: actual wirescape-engine with --null-audio, no devices", "",
             "| Probe | Modules | Connections | Reply code | Exact message |",
             "|---|---:|---:|---|---|"]
    for command, reply in zip(evidence["commands"], evidence["replies"]):
        ans = reply["response"]
        lines.append(f"| {command['label']} | {command['modules']} | {command['connections']} | "
                     f"{ans.get('code')} | {ans.get('message')} |")
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(folder / "report.md")


if __name__ == "__main__":
    main()
