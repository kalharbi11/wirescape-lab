# SPDX-License-Identifier: GPL-3.0-only
"""Archive a completed run for owner upload to a GitHub release."""
import argparse
import json
from pathlib import Path
import zipfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path,help="results/<machine>/<date>-<sha7> folder")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    root=args.run.resolve(strict=True)
    if not root.is_dir() or not (root/"manifest.json").is_file() or not (root/"report.md").is_file():
        p.error("run requires manifest.json and report.md")
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("completed"):
        p.error("incomplete run; resolve failures before packing")
    output=(args.out or root.parent/(root.name+".zip")).resolve()
    if output.is_relative_to(root):
        p.error("archive must be outside the run directory")
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=5,allowZip64=True) as archive:
        for file in sorted(root.rglob("*")):
            if file.is_symlink():
                p.error("refusing symlink in run: "+str(file))
            if file.is_file():
                archive.write(file,arcname=file.relative_to(root))
    print(output)


if __name__=="__main__":
    main()
