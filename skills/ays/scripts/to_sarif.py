#!/usr/bin/env python3
"""Convert the merged review report's findings into SARIF 2.1.0. Standard library
only — installs nothing, no network.

Why this exists: the markdown report is for a human, and a human is not a CI gate.
SARIF is the format GitHub code scanning, Azure DevOps, and most security dashboards
already ingest, so emitting it turns a run's findings into something that can block a
pull request instead of something someone has to read and remember.

It parses the finding shape `references/report-format.md` specifies:

    - [blocking] path/to/file.ts:42 — <problem>. Fix: <suggestion>.
    - [warning]  path/to/other.py:88 - <problem>. Fix: <suggestion>.

Severity maps blocking→error, warning→warning, nit→note. Lines that don't match are
ignored, so pointing it at a whole report (headings, tables, prose) is fine.

Black-box helper: run with --help, then invoke.

USAGE
    python to_sarif.py --in report.md --out findings.sarif
    python to_sarif.py --in report.md --out findings.sarif --fail-on blocking
    cat report.md | python to_sarif.py > findings.sarif
"""
from __future__ import annotations
import argparse, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Reports are UTF-8 and full of em dashes. Without this, a piped report on a
    # cp1252 console decodes into mojibake and the separator stops matching.
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOL = "ays"
INFO_URI = "https://github.com/arothm/AYS"

LEVEL = {"blocking": "error", "warning": "warning", "nit": "note"}
RANK = {"blocking": 3, "warning": 2, "nit": 1}

# - [blocking] path/to/file.ts:42 — problem. Fix: suggestion.
# The separator may be an em dash, en dash, hyphen, or a colon followed by space.
#
# The location is captured as ONE token and split in code rather than with an
# optional `(?::(\d+))?` group. With the group, a report whose em dash failed to
# decode let the regex backtrack, skip the line capture, and use the `:` before the
# line number as the separator instead - silently reporting every finding at line 1.
# A wrong line number is worse than no line number: it sends a reviewer to the wrong
# place with full confidence.
FINDING = re.compile(
    r"^\s*[-*]\s*"
    r"[\[\(](?P<sev>blocking|warning|nit)[\]\)]\s*"
    r"(?P<loc>\S+?)"
    r"\s*(?:[—–-]+|:\s)\s*"
    r"(?P<rest>.+?)\s*$",
    re.IGNORECASE)

LOC = re.compile(r"^(?P<path>.+?)(?::(?P<line>\d+))?$")

FIX = re.compile(r"\bFix:\s*(?P<fix>.+?)\s*$", re.IGNORECASE)
# A path we'll accept as a real artifact location rather than prose. Requiring a
# file extension keeps template placeholders ("path/or/area", "path/to/file") and
# prose out of the SARIF, since a bogus artifactLocation is worse than a dropped
# finding - it sends a reviewer to a file that doesn't exist. An extensionless path
# still qualifies when the finding carries a line number, which prose never does.
HAS_EXT = re.compile(r"^[\w.@/\\-]+\.[A-Za-z0-9_]{1,12}$")
PATHISH = re.compile(r"^[\w.@/\\-]+$")


def rule_id(sev, message):
    """Stable-ish rule id from the leading words of the message."""
    words = re.findall(r"[a-z0-9]+", message.lower())[:4]
    return "ays-%s-%s" % (sev.lower(), "-".join(words) or "finding")


def parse(text):
    findings = []
    for raw in (text or "").splitlines():
        m = FINDING.match(raw)
        if not m:
            continue
        loc = LOC.match(m.group("loc").strip("`*_ "))
        if not loc:
            continue
        path, line = loc.group("path"), loc.group("line")
        # A finding line whose "path" is prose or a template placeholder is not a
        # locatable result - skip it rather than emit a bogus artifact location.
        if not PATHISH.match(path) or not (HAS_EXT.match(path) or line):
            continue
        rest = m.group("rest").strip()
        fixm = FIX.search(rest)
        fix = fixm.group("fix") if fixm else ""
        problem = rest[:fixm.start()].strip(" .") if fixm else rest.strip(" .")
        findings.append({
            "severity": m.group("sev").lower(),
            "path": path.replace("\\", "/"),
            "line": int(line) if line else 1,
            "problem": problem or rest,
            "fix": fix,
        })
    return findings


def to_sarif(findings):
    rules, seen = [], {}
    results = []
    for f in findings:
        rid = rule_id(f["severity"], f["problem"])
        if rid not in seen:
            seen[rid] = True
            rules.append({
                "id": rid,
                "shortDescription": {"text": f["problem"][:120]},
                "defaultConfiguration": {"level": LEVEL[f["severity"]]},
                "properties": {"severity": f["severity"]},
            })
        message = f["problem"] + (("  Fix: " + f["fix"]) if f["fix"] else "")
        results.append({
            "ruleId": rid,
            "level": LEVEL[f["severity"]],
            "message": {"text": message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f["path"]},
                    "region": {"startLine": max(1, f["line"])},
                }
            }],
        })
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": TOOL,
                "informationUri": INFO_URI,
                "rules": rules,
            }},
            "results": results,
        }],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert an ays report to SARIF 2.1.0.")
    ap.add_argument("--in", dest="inp", help="the merged report markdown (default: stdin)")
    ap.add_argument("--out", dest="out", help="output .sarif file (default: stdout)")
    ap.add_argument("--fail-on", choices=["blocking", "warning", "nit"],
                    help="exit 1 if any finding is at or above this severity")
    a = ap.parse_args(argv)

    if a.inp:
        if not os.path.isfile(a.inp):
            print("no such report: %s" % a.inp, file=sys.stderr)
            return 2
        with open(a.inp, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    findings = parse(text)
    doc = json.dumps(to_sarif(findings), indent=2)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(doc + "\n")
        counts = {}
        for f_ in findings:
            counts[f_["severity"]] = counts.get(f_["severity"], 0) + 1
        summary = ", ".join("%d %s" % (n, s) for s, n in sorted(counts.items())) or "no findings"
        print("wrote %s - %s" % (a.out, summary))
    else:
        sys.stdout.write(doc + "\n")

    if a.fail_on:
        threshold = RANK[a.fail_on]
        hits = [f for f in findings if RANK[f["severity"]] >= threshold]
        if hits:
            print("[to_sarif] %d finding(s) at or above '%s'" % (len(hits), a.fail_on),
                  file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
