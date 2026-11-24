# SPDX-License-Identifier: GPL-3.0-only
"""Summarize completed PR checks. Never fetch or execute PR source."""
import json
import os
import re
import urllib.request
import urllib.error
from urllib.parse import urlsplit

MARKER = "<!-- wirescape-ci-digest-v1 -->"
NAMES = ("Lab CI", "Golden patch renders (same-runner base/head gate)",
         "M1 paired stage evidence (nonrequired)", "Instruction count gate (advisory)")
MATCH = re.compile(r"error|FAILED|Assertion|mismatch", re.I)
IR = re.compile(r"(?:\bIr\b|instruction|\bM1\b).*?\+(\d+(?:\.\d+)?)%", re.I)
PAIRED_IR = re.compile(
    r"^FAIL: module/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+:"
    r"\s*\+(\d+(?:\.\d+)?)% exceeds strict \+1%\s*$"
)
ACTION_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z[ \t]+")
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX = 2000000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_log(api_url, token, opener=None):
    """Never forward Authorization on a GitHub log redirect."""
    if urlsplit(api_url).scheme != "https" or urlsplit(api_url).hostname != "api.github.com":
        raise ValueError("log API must use api.github.com HTTPS")
    opener = opener or urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(api_url, headers={"Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json"})
    try:
        with opener.open(req, timeout=30) as response:
            return bounded(response)
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        target = exc.headers.get("Location", "")
    dest = urlsplit(target)
    if dest.scheme != "https" or not dest.hostname or dest.username or dest.password or dest.port not in (None, 443):
        raise ValueError("unsafe log redirect")
    # Explicitly no Authorization header on redirected object-storage request.
    # Reject any further redirect: only the first GitHub-issued HTTPS URL is trusted.
    with opener.open(urllib.request.Request(target), timeout=30) as response:
        return bounded(response)


def bounded(response):
    body = response.read(MAX + 1)
    if len(body) > MAX:
        raise ValueError("log exceeds limit")
    return body.decode("utf-8", "replace")


def safe(value, limit=220):
    value = str(value).replace("\r", " ").replace("\n", " ")
    value = "".join(c if 32 <= ord(c) < 127 else " " for c in value)
    value = value.replace("`", "'").replace("@", "@ ").replace("[", "(").replace("]", ")")
    return value.replace("<!--", "< !--").replace("-->", "-- >")[:limit]


def parse(log):
    lines = [safe(ACTION_TIMESTAMP.sub("", x, count=1)) for x in log[:MAX].splitlines()]
    return {
        "errors": [x for x in lines if MATCH.search(x)][:15],
        "tests": list(dict.fromkeys(x for x in lines if re.search(r"FAILED|FAIL:|test_\w+", x)))[:8],
        "golden": list(dict.fromkeys(x for x in lines if re.search(r"golden|\.wav", x, re.I) and MATCH.search(x)))[:8],
        "ir": list(dict.fromkeys(x for x in lines if (m := (PAIRED_IR.fullmatch(x) or IR.search(x))) and float(m.group(1)) > 1))[:8],
    }


def render(head, runs, failures):
    lines = [MARKER, "### CI digest", "Head: `" + head + "`"]
    for name in NAMES:
        r = runs.get(name)
        if r:
            url = r.get("html_url", "")
            if not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/actions/runs/\d+", url):
                url = ""
            lines.append("- " + name + ": " + safe(r.get("conclusion") or "pending") + " " + url)
        else:
            lines.append("- " + name + ": not reported on this head")
    for job, step, evidence in failures:
        lines.append("**" + safe(job, 80) + "** failed step: " + safe(step, 100))
        for category in ("errors", "tests", "golden", "ir"):
            for value in evidence[category]:
                lines.append("- " + category + ": " + safe(value))
    return "\n".join(lines[:59] + (["- Truncated at 60 lines."] if len(lines) > 60 else lines[59:]))


class API:
    def __init__(self, repo, token):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            raise ValueError("invalid repository")
        self.root = "https://api.github.com/repos/" + repo
        self.token = token

    def get(self, path, method="GET", data=None, raw=False):
        req = urllib.request.Request(self.root + path,
            data=None if data is None else json.dumps(data).encode(),
            method=method, headers={"Authorization": "Bearer " + self.token,
              "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
              "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(MAX + 1)
            if len(body) > MAX:
                raise ValueError("response too large")
            return body.decode("utf-8", "replace") if raw else json.loads(body)

    def pages(self, path, key=None):
        items = []
        for page in range(1, 11):
            sep = "&" if "?" in path else "?"
            result = self.get(path + sep + "per_page=100&page=" + str(page))
            chunk = result[key] if key else result
            items.extend(chunk)
            if len(chunk) < 100:
                break
        return items


def run(api, event, repo):
    wr = event["workflow_run"]
    sha = wr.get("head_sha", "")
    if (wr.get("event") != "pull_request" or wr.get("name") not in NAMES or
        wr.get("repository", {}).get("full_name") != repo or not SHA.fullmatch(sha)):
        return "ignored unrelated run"
    for ref in wr.get("pull_requests", []):
        number = ref.get("number")
        if type(number) is not int or number <= 0:
            continue
        pr = api.get("/pulls/" + str(number))
        if (pr.get("state") != "open" or pr["head"]["sha"] != sha or
            pr["base"]["repo"]["full_name"] != repo):
            continue
        all_runs = api.pages("/actions/runs?head_sha=" + sha, "workflow_runs")
        eligible = [r for r in all_runs if r.get("name") in NAMES and
            r.get("event") == "pull_request" and r.get("head_sha") == sha and
            any(p.get("number") == number for p in r.get("pull_requests", []))]
        if not any(r.get("id") == wr.get("id") for r in eligible):
            continue
        latest = {}
        for r in sorted(eligible, key=lambda x: x["id"], reverse=True):
            latest.setdefault(r["name"], r)
        failures = []
        for r in latest.values():
            if r.get("conclusion") not in ("failure", "timed_out"):
                continue
            for job in api.pages("/actions/runs/" + str(r["id"]) + "/jobs", "jobs"):
                if job.get("conclusion") != "failure":
                    continue
                step = next((s.get("name", "?") for s in job.get("steps", [])
                             if s.get("conclusion") == "failure"), "?")
                try:
                    log = download_log(api.root + "/actions/jobs/" + str(job["id"]) + "/logs", api.token)
                except (OSError, ValueError):
                    log = "error: log unavailable"
                failures.append((job.get("name", "?"), step, parse(log)))
        body = render(sha, latest, failures)
        # Final current-head guard: never publish a stale digest after slow log reads.
        current = api.get("/pulls/" + str(number))
        if current.get("state") != "open" or current["head"]["sha"] != sha:
            return "stale event: head changed before comment write"
        comments = api.pages("/issues/" + str(number) + "/comments")
        own = [c for c in comments if MARKER in c.get("body", "") and
               c.get("user", {}).get("login") == "github-actions[bot]"]
        # Repeat immediately before the mutating call, after comment enumeration.
        current = api.get("/pulls/" + str(number))
        if current.get("state") != "open" or current["head"]["sha"] != sha:
            return "stale event: head changed before comment write"
        if own:
            api.get("/issues/comments/" + str(own[0]["id"]), "PATCH", {"body": body})
        else:
            api.get("/issues/" + str(number) + "/comments", "POST", {"body": body})
        return "updated #" + str(number)
    return "no validated current-head PR"


if __name__ == "__main__":
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event = json.load(handle)
    print(run(API(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]),
              event, os.environ["GITHUB_REPOSITORY"]))
