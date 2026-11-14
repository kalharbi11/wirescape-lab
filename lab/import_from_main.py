#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Copy the product tree of kalharbi11/wirescape at one SHA into this lab repo.

Usage: python lab/import_from_main.py /path/to/wirescape <sha>

Rules (see lab/MANIFEST.md): every tracked file is copied unless EXCLUDE matches it.
Workflows go to ci/from-main/ (inactive). The SHA is recorded in docs/context/SNAPSHOT.md.
Re-run it only while the product tree is untouched in the lab; it refuses otherwise.
"""
import pathlib, subprocess, sys, tarfile, io

EXCLUDE_PREFIXES = (
    # agent process and planning
    "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", ".claude/", ".readme",
    "apps/studio/AGENTS.md", "apps/studio/CLAUDE.md", "apps/studio/IMPORT.md",
    "apps/studio/archive/", "apps/studio/reference/",
    "apps/studio/docs/PLAN.md", "apps/studio/docs/DECISIONS.md",
    "apps/studio/docs/PHASE7_HANDOFF.md", "apps/studio/docs/PHASE8_HANDOFF.md",
    "apps/studio/docs/PRE_PI_READINESS_REVIEW.md", "apps/studio/docs/PI_UI_TEST_PLAN.md",
    "apps/studio/docs/PI_UI_RUNNER.md", "apps/studio/docs/ARCHIVE.md",
    "docs/PLAN.md", "docs/PLANNER_HANDOFF.md", "docs/WORKFLOW.md", "docs/STATUS.md",
    "docs/DEMO_CLASS.md", "docs/PI_RUNNER.md", "docs/WINDOWS_DEMO_UPDATE.md",
    "docs/tasks/", "docs/planner/", "docs/reviews/", "docs/sequencer/AGENT_PROMPT.md",
    "docs/design/BETA08", "docs/design/M3_", "docs/design/STUDIO_REFINEMENT_BRIEF.md",
    # process tooling
    "tools/board.py", "tools/merge_gate.py", "tools/review_pack.py", "tools/ci_logs.py",
    "tools/runner_health.py", "tools/docs_fresh.py", "tools/test_dev_accept.py",
    "tools/ci/guard.py", "tools/ci/test_guard.py",
    "tools/foundation/tests/test_board.py", "tools/foundation/tests/test_merge_gate.py",
    "tools/foundation/tests/test_review_pack.py", "tools/foundation/tests/test_runner_health.py",
    "tools/foundation/tests/test_docs_fresh.py",
    ".github/CODEOWNERS", ".github/copilot-instructions.md", ".github/dependabot.yml", ".github/pull_request_template.md", ".github/ISSUE_TEMPLATE/",
)
INACTIVE_WORKFLOWS = {"board.yml", "guard.yml", "merge_gate.yml", "main_verify.yml", "post_merge.yml"}
PRODUCT_ROOTS = ("native/", "apps/", "tools/", "docs/specs/", "controllers/", "tests/")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, sha = pathlib.Path(sys.argv[1]), sys.argv[2]
    lab = pathlib.Path(__file__).resolve().parents[1]
    full = subprocess.check_output(["git", "-C", str(src), "rev-parse", sha], text=True).strip()
    snap = lab / "docs/context/SNAPSHOT.md"
    if snap.exists():
        changed = subprocess.run(["git", "-C", str(lab), "log", "--format=%h %s", "--", *PRODUCT_ROOTS],
                                 capture_output=True, text=True).stdout.splitlines()
        foreign = [c for c in changed if "import from main" not in c]
        if foreign:
            sys.exit("Refusing: the lab already changed the product tree:\n" + "\n".join(foreign))
    blob = subprocess.check_output(["git", "-C", str(src), "archive", "--format=tar", full])
    copied, skipped = 0, []
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            name = m.name
            if name.startswith(".github/workflows/"):
                base = name.rsplit("/", 1)[-1]
                if base in INACTIVE_WORKFLOWS:
                    skipped.append(name)
                    continue
                name = "ci/from-main/" + base
            elif name.startswith(EXCLUDE_PREFIXES):
                skipped.append(name)
                continue
            out = lab / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(tar.extractfile(m).read())
            out.chmod(m.mode & 0o777 or 0o644)
            copied += 1
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(
        "<!-- SPDX-License-Identifier: GPL-3.0-only -->\n# Snapshot\n\n"
        f"Product tree imported from `kalharbi11/wirescape` at `{full}`.\n"
        f"{copied} files copied, {len(skipped)} process files left out (rules: `lab/MANIFEST.md`).\n"
        "Every fact in `facts/` names the lab commit it was measured on.\n")
    print(f"copied {copied}, skipped {len(skipped)}")


if __name__ == "__main__":
    main()
