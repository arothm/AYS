#!/usr/bin/env python3
"""Look up, export and validate the AYS rules in references/*.md.

    rules.py show WEB-024 [GIT-009 ...]   print rules by ID, with their file and Why
    rules.py search <words>               rules whose text or Why contains every word
    rules.py export [-o FILE]             the whole list as one Markdown document
    rules.py validate                     exit 1 on any problem below

validate checks that every rule ID is well formed and unique, that every rule
has exactly one "Why" line under it, that every cross-reference ("see WEB-024")
points at a rule that exists, that each "Merged rules" entry names a retired ID
and a live one, and that SKILL.md links every reference file and no file it
doesn't have.

Standard library only. Paths resolve from this file, never the working
directory, because the skill runs inside someone else's repository.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    # Windows consoles default to cp1252 and would mangle the rule text.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULE = re.compile(r"^- `([^`]+)` (.*)$")
WHY = re.compile(r"^  - Why: (.*)$")
ID = re.compile(r"^[A-Z]{3}-\d{3}$")
REF = re.compile(r"\b[A-Z]{3}-\d{3}\b")
# Rule areas. Only these prefixes count as rule citations in text.
AREAS = {"WEB", "OPS", "GIT", "PKG", "BUN", "TWD", "RCT", "AID", "AIF", "MCP", "SKL"}
MERGE = re.compile(r"((?:[A-Z]{3}-\d{3}(?: and )?)+) → ([A-Z]{3}-\d{3})")
LINK = re.compile(r"`references/([^`]+\.md)`")


def load(skill_dir: str):
    """Return (rules, merges, problems). rules maps ID -> (file, text, why)."""
    rules: dict[str, tuple[str, str, str]] = {}
    merges: list[tuple[str, str, str]] = []
    problems: list[str] = []
    ref_dir = os.path.join(skill_dir, "references")
    for name in sorted(os.listdir(ref_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(ref_dir, name), encoding="utf-8") as f:
            text = f.read()
        body, _, merged = text.partition("## Merged rules")
        last = None  # the rule a following Why line belongs to
        for line in body.splitlines():
            m = RULE.match(line)
            if m:
                rid, rule = m.groups()
                last = None
                if not ID.match(rid):
                    problems.append(f"{name}: malformed rule ID {rid!r}")
                elif rid in rules:
                    problems.append(f"{name}: {rid} duplicates the rule in {rules[rid][0]}")
                else:
                    rules[rid] = (name, rule, "")
                    last = rid
                continue
            w = WHY.match(line)
            if w and last:
                f_, r_, why = rules[last]
                if why:
                    problems.append(f"{name}: {last} has more than one Why line")
                else:
                    rules[last] = (f_, r_, w.group(1))
        for old, new in MERGE.findall(merged):
            for rid in REF.findall(old):
                merges.append((name, rid, new))
    return rules, merges, problems


def validate(skill_dir: str) -> list[str]:
    rules, merges, problems = load(skill_dir)
    retired = {old for _, old, _ in merges}
    for name, old, new in merges:
        if old in rules:
            problems.append(f"{name}: {old} is listed as merged but is still a rule")
        if new not in rules:
            problems.append(f"{name}: {old} is merged into {new}, which does not exist")
    def cites(text):
        # Terms that merely look like IDs, such as AES-256, are not citations.
        return [ref for ref in REF.findall(text) if ref[:3] in AREAS]

    for rid, (name, rule, why) in rules.items():
        if rid[:3] not in AREAS:
            problems.append(f"{name}: {rid} has an unknown area prefix; add it to AREAS in rules.py")
        if not why:
            problems.append(f"{name}: {rid} has no 'Why' line under it")
        for ref in cites(rule + " " + why):
            if ref in retired:
                problems.append(f"{name}: {rid} cites {ref}, which was merged; cite its replacement")
            elif ref not in rules:
                problems.append(f"{name}: {rid} cites {ref}, which does not exist")
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
        skill = f.read()
    for ref in sorted(set(cites(skill)) - set(rules)):
        problems.append(f"SKILL.md cites {ref}, which does not exist")
    linked = set(LINK.findall(skill))
    present = {n for n in os.listdir(os.path.join(skill_dir, "references")) if n.endswith(".md")}
    for n in sorted(present - linked):
        problems.append(f"references/{n} is not linked from SKILL.md, so it will never load")
    for n in sorted(linked - present):
        problems.append(f"SKILL.md links references/{n}, which does not exist")
    return problems


def export(skill_dir: str) -> str:
    """The whole rule set as one Markdown document, in SKILL.md's routing order."""
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
        order = list(dict.fromkeys(LINK.findall(f.read())))
    rules, merges, _ = load(skill_dir)
    out = ["# AYS — Abdullrahman Yasser Skill: the rules", "",
           f"{len(rules)} rules. Each has an ID, the rule, and why to follow it.", ""]
    for name in order:
        with open(os.path.join(skill_dir, "references", name), encoding="utf-8") as f:
            text = f.read().partition("## Merged rules")[0]
        for line in text.splitlines():
            if line.startswith("# "):
                out += ["", "## " + line[2:], ""]
            elif line.startswith("## "):
                out += ["", "### " + line[3:], ""]
            elif RULE.match(line):
                rid, rule = RULE.match(line).groups()
                out += [f"**{rid}** {rule}", "", f"*Why:* {rules[rid][2]}", ""]
    if merges:
        out += ["", "## Merged numbers", "",
                " · ".join(f"{old} → {new}" for _, old, new in merges), ""]
    return "\n".join(out).replace("\n\n\n", "\n\n").strip() + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Look up, export and validate the AYS rules.")
    ap.add_argument("--skill-dir", default=SKILL_DIR, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="print rules by ID").add_argument("ids", nargs="+")
    sub.add_parser("search", help="rules containing every word").add_argument("words", nargs="+")
    sub.add_parser("export", help="the whole list as Markdown").add_argument("-o", "--out")
    sub.add_parser("validate", help="check IDs, Whys, cross-references and SKILL.md links")
    args = ap.parse_args(argv)

    if args.cmd == "validate":
        problems = validate(args.skill_dir)
        for p in problems:
            print("FAIL " + p)
        rules, merges, _ = load(args.skill_dir)
        if problems:
            print(f"{len(problems)} problem(s).")
            return 1
        print(f"OK: {len(rules)} rules, each with a Why; {len(merges)} merged IDs; "
              "all cross-references resolve.")
        return 0

    if args.cmd == "export":
        doc = export(args.skill_dir)
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as f:
                f.write(doc)
            print(f"wrote {args.out}")
        else:
            sys.stdout.write(doc)
        return 0

    rules, merges, _ = load(args.skill_dir)
    if args.cmd == "show":
        merged_into = {old: new for _, old, new in merges}
        status = 0
        for rid in (i.upper() for i in args.ids):
            target = merged_into.get(rid, rid)
            if target not in rules:
                print(f"{rid}: no such rule")
                status = 1
                continue
            name, rule, why = rules[target]
            head = f"{rid} was merged into {target}" if target != rid else rid
            print(f"{head} ({name}): {rule}\n  Why: {why}")
        return status

    words = [w.lower() for w in args.words]
    hits = [(rid, f, r, y) for rid, (f, r, y) in sorted(rules.items())
            if all(w in (r + " " + y).lower() for w in words)]
    for rid, f, r, y in hits:
        print(f"{rid} ({f}): {r}\n  Why: {y}")
    print(f"{len(hits)} rule(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
