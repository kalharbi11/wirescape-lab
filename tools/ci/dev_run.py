# SPDX-License-Identifier: GPL-3.0-only
"""Dev-run: on-demand build/test diagnostics on hosted runners for a PR head.

Three subcommands, used by .github/workflows/dev-run.yml:
  parse    trusted job: parse a `/dev-run ...` request into a JSON spec
  execute  untrusted job: build the PR head and run the requested profile
  report   trusted job: turn the execute summaries (untrusted data) into a PR comment

The parse and report jobs only ever run this file from `main`. The execute job runs
the PR's code, so it has a read-only token and no secrets. Results are diagnostics,
never contract evidence (docs/workflow/DEV_RUN.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

PROFILES = ("test", "asan", "cmd", "studio")
PLATFORMS = ("linux-x64", "linux-arm64")
RUNNERS = {"linux-x64": "ubuntu-latest", "linux-arm64": "ubuntu-24.04-arm"}
CMD_PREFIXES = ("build/native/", "build/asan/", "python3 tools/", "valgrind ", "ctest ")
FILTER_RE = re.compile(r"^[A-Za-z0-9_.*+?|^$()\[\] -]{1,200}$")
KEYS = {"platform", "filter", "cmd", "build", "timeout", "repeat"}
TAIL_LINES = 150
MAX_COMMENT = 60000
ASAN_FLAGS = "-fsanitize=address,undefined -fno-sanitize-recover=undefined -fno-omit-frame-pointer"


class RequestError(ValueError):
    pass


def parse_request(text: str) -> dict:
    """Parse the first line of a request. Raises RequestError with a user-facing reason."""
    line = (text or "").strip().splitlines()[0].strip() if (text or "").strip() else ""
    if line.startswith("/dev-run"):
        line = line[len("/dev-run"):].strip()
    try:
        words = shlex.split(line)
    except ValueError as exc:
        raise RequestError(f"could not split the request: {exc}") from None
    if not words:
        raise RequestError("no profile given; use one of: " + ", ".join(PROFILES))
    profile, rest = words[0], words[1:]
    if profile not in PROFILES:
        raise RequestError(f"unknown profile `{profile}`; use one of: " + ", ".join(PROFILES))
    opts: dict[str, str] = {}
    for word in rest:
        key, sep, value = word.partition("=")
        if not sep or key not in KEYS:
            raise RequestError(f"unknown option `{word}`; allowed: " + ", ".join(sorted(KEYS)))
        if key in opts:
            raise RequestError(f"option `{key}` given twice")
        opts[key] = value
    spec: dict = {"profile": profile}

    platform = opts.get("platform", "linux-x64")
    if platform == "both":
        spec["platforms"] = list(PLATFORMS)
    elif platform in PLATFORMS:
        spec["platforms"] = [platform]
    else:
        raise RequestError("platform must be linux-x64, linux-arm64 or both")
    if profile == "studio" and spec["platforms"] != ["linux-x64"]:
        raise RequestError("studio runs on linux-x64 only")

    filt = opts.get("filter", "")
    if filt and not FILTER_RE.match(filt):
        raise RequestError("filter may use letters, digits and regex characters _.*+?|^$()[]- only")
    spec["filter"] = filt

    build = opts.get("build", "asan" if profile == "asan" else "release")
    if build not in ("release", "asan"):
        raise RequestError("build must be release or asan")
    if profile in ("test", "studio") and build != "release":
        raise RequestError("use the asan profile for a sanitizer test run")
    spec["build"] = build

    try:
        timeout = int(opts.get("timeout", "60"))
        repeat = int(opts.get("repeat", "1"))
    except ValueError:
        raise RequestError("timeout and repeat must be whole numbers") from None
    if not 1 <= timeout <= 1800:
        raise RequestError("timeout must be 1..1800 seconds")
    if not 1 <= repeat <= 20:
        raise RequestError("repeat must be 1..20")
    spec["timeout"] = timeout
    spec["repeat"] = repeat

    cmd = opts.get("cmd", "")
    if profile == "cmd":
        if not cmd:
            raise RequestError('the cmd profile needs cmd="..."')
        if not cmd.startswith(CMD_PREFIXES):
            raise RequestError("cmd must start with one of: " + ", ".join(p.strip() for p in CMD_PREFIXES))
        if any(c in cmd for c in "\n\r\0"):
            raise RequestError("cmd must be one line")
        argv = shlex.split(cmd)
        if any(".." in part.split("/") for part in argv):
            raise RequestError("cmd may not use `..` path parts")
        spec["cmd"] = argv
    elif cmd:
        raise RequestError("cmd= is only for the cmd profile")
    else:
        spec["cmd"] = []
    spec["request"] = ("/dev-run " + line).strip()
    return spec


# ---------------------------------------------------------------- execute (untrusted job)

class Runner:
    def __init__(self, out: Path):
        self.out = out
        self.log = (out / "log.txt").open("w", encoding="utf-8", errors="replace")
        self.steps: list[dict] = []

    def run(self, name: str, argv: list[str], timeout: int = 3600, env: dict | None = None,
            cwd: str | None = None) -> int:
        self.log.write(f"\n===== step: {name}\n$ {shlex.join(argv)}\n")
        self.log.flush()
        start = time.monotonic()
        try:
            proc = subprocess.run(argv, stdout=self.log, stderr=subprocess.STDOUT, timeout=timeout,
                                  cwd=cwd, env={**os.environ, **(env or {})})
            code = proc.returncode
        except subprocess.TimeoutExpired:
            self.log.write(f"\n!!!!! step timed out after {timeout} s\n")
            code = 124
        except OSError as exc:
            self.log.write(f"\n!!!!! could not start: {exc}\n")
            code = 127
        seconds = round(time.monotonic() - start, 1)
        self.log.write(f"===== exit {code} after {seconds} s\n")
        self.log.flush()
        self.steps.append({"name": name, "exit": code, "seconds": seconds})
        return code


def _ctest(build_dir: str, spec: dict) -> list[str]:
    argv = ["ctest", "--test-dir", build_dir, "-C", "Release", "--output-on-failure",
            "--timeout", str(spec["timeout"])]
    if spec["filter"]:
        argv += ["-R", spec["filter"]]
    if spec["repeat"] > 1:
        argv += ["--repeat", f"until-fail:{spec['repeat']}"]
    return argv


def execute(spec: dict, platform: str, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    r = Runner(out)
    profile = spec["profile"]
    ok = True
    if profile == "studio":
        # The workflow installs Node, npm packages and Chromium and sets WIRESCAPE_CHROMIUM.
        argv = ["npm", "test", "--"]
        if spec["filter"]:
            argv += ["-g", spec["filter"]]
        if spec["repeat"] > 1:
            argv += ["--repeat-each", str(spec["repeat"])]
        ok = r.run("studio playwright", argv, timeout=3600, cwd="apps/studio") == 0
    elif spec["build"] == "asan":
        env = {"ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1", "UBSAN_OPTIONS": "halt_on_error=1"}
        ok = r.run("configure asan", ["cmake", "-S", "native", "-B", "build/asan", "-G", "Ninja",
                                       "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                                       "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
                                       f"-DCMAKE_CXX_FLAGS={ASAN_FLAGS}", f"-DCMAKE_C_FLAGS={ASAN_FLAGS}"]) == 0
        ok = ok and r.run("build asan", ["cmake", "--build", "build/asan"]) == 0
        if ok and profile == "asan":
            ok = r.run("ctest asan", _ctest("build/asan", spec), timeout=7200, env=env) == 0
        elif ok:
            ok = r.run("cmd", spec["cmd"], timeout=spec["timeout"] * spec["repeat"] + 60, env=env) == 0
    else:
        ok = r.run("build headless", [sys.executable, "tools/dev.py", "build", "--headless"]) == 0
        if ok and profile == "test":
            ok = r.run("ctest", _ctest("build/native", spec), timeout=7200) == 0
        elif ok and profile == "cmd":
            for i in range(spec["repeat"]):
                ok = r.run(f"cmd #{i + 1}", spec["cmd"], timeout=spec["timeout"] + 60) == 0 and ok
    r.log.close()
    lines = (out / "log.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    failed = []
    if "The following tests FAILED:" in lines:
        idx = lines.index("The following tests FAILED:")
        failed = [ln.strip() for ln in lines[idx + 1:idx + 41] if ln.strip() and not ln.startswith("Errors while")]
    summary = {
        "platform": platform,
        "sha": os.environ.get("DEV_RUN_SHA", ""),
        "ok": ok,
        "steps": r.steps,
        "failed_tests": failed,
        "tail": lines[-TAIL_LINES:],
    }
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return 0 if ok else 1


# ---------------------------------------------------------------- report (trusted job)

def _clean(text: str, limit: int = 400) -> str:
    text = str(text)[:limit]
    text = text.replace("```", "ʼʼʼ").replace("@", "@​")
    return "".join(c for c in text if c == "\t" or c >= " ")


def build_report(spec: dict, sha: str, run_url: str, summaries: list[dict]) -> str:
    want = set(spec["platforms"])
    rows, details = [], []
    for s in summaries:
        if not isinstance(s, dict) or s.get("platform") not in want:
            continue
        plat = s["platform"]
        steps = s.get("steps") if isinstance(s.get("steps"), list) else []
        step_txt = ", ".join(
            f"{_clean(st.get('name', '?'), 40)} → {int(st.get('exit', -1))} ({float(st.get('seconds', 0)):.0f} s)"
            for st in steps[:30] if isinstance(st, dict))
        rows.append(f"| {plat} | {'✅ pass' if s.get('ok') is True else '❌ fail'} | {step_txt} |")
        want.discard(plat)
        tail = s.get("tail") if isinstance(s.get("tail"), list) else []
        failed = s.get("failed_tests") if isinstance(s.get("failed_tests"), list) else []
        body = ""
        if failed:
            body += "Failed tests:\n```text\n" + "\n".join(_clean(f, 200) for f in failed[:40]) + "\n```\n"
        body += f"Last {len(tail[-TAIL_LINES:])} log lines:\n```text\n" + \
            "\n".join(_clean(t, 400) for t in tail[-TAIL_LINES:]) + "\n```"
        details.append(f"<details{' open' if s.get('ok') is not True else ''}><summary>{plat} log</summary>\n\n{body}\n</details>")
    for plat in sorted(want):
        rows.append(f"| {plat} | ⚠️ no result (job cancelled or setup failed; see run) | |")
    head = (f"<!-- dev-run -->\n**dev-run** `{_clean(spec['request'], 300)}`\n\n"
            f"Head tested: `{sha}` · [run and full logs]({run_url})\n\n"
            "| platform | result | steps |\n|---|---|---|\n" + "\n".join(rows) + "\n\n")
    foot = ("\n\n_Diagnostic only: not contract evidence. Exact-head Lab CI and the contract's "
            "gates still decide. See `docs/workflow/DEV_RUN.md`._")
    text = head + "\n\n".join(details) + foot
    if len(text) > MAX_COMMENT:
        text = head + "(log tails omitted: too long; open the run)" + foot
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("--out", required=True)
    e = sub.add_parser("execute")
    e.add_argument("--spec", required=True)
    e.add_argument("--platform", required=True, choices=PLATFORMS)
    e.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--spec", required=True)
    rp.add_argument("--results", required=True)
    rp.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "parse":
        try:
            spec = parse_request(os.environ.get("DEV_RUN_REQUEST", ""))
            spec["matrix"] = {"include": [{"platform": p, "runner": RUNNERS[p]} for p in spec["platforms"]]}
            spec["error"] = ""
        except RequestError as exc:
            spec = {"error": str(exc), "request": _clean(os.environ.get("DEV_RUN_REQUEST", ""), 300)}
        Path(args.out).write_text(json.dumps(spec), encoding="utf-8")
        print(json.dumps(spec, indent=1))
        return 0
    if args.cmd == "execute":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        return execute(spec, args.platform, Path(args.out))
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    summaries = []
    for f in sorted(Path(args.results).rglob("summary.json")):
        try:
            summaries.append(json.loads(f.read_text(encoding="utf-8")[:2_000_000]))
        except (OSError, ValueError):
            continue
    text = build_report(spec, os.environ.get("DEV_RUN_SHA", ""), os.environ.get("DEV_RUN_URL", ""), summaries)
    Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
