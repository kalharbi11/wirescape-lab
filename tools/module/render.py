# SPDX-License-Identifier: GPL-3.0-only
"""MT3 owns rendering implementation; this stub reserves a stable dispatch path."""

def run(root, folder, layout, messages, args, report):
    entry = messages["STAGE"]
    report["results"].append({"test": "STAGE", "status": "skip",
                              "what": entry["what"], "where": {"command": "render"},
                              "fix": entry["fix"], "metrics": {}})
    return 4
