#!/usr/bin/env python3
"""Build ayc-skill.skill deterministically and correctly.

The .skill file is a zip of skills/ayc-skill/. Building it by hand (or with
PowerShell Compress-Archive on Windows) produced two validator failures: Windows
BACKSLASH path separators in the archive, and shipped __pycache__/*.pyc. This
builds it right — forward-slash arcnames, junk excluded — so desktop/Cowork
uploads validate without repackaging.

Deliberately bundles ONLY skills/ayc-skill/. The plugin's `agents/` and
`hooks/` directories are Claude Code plugin components with no meaning in a
.skill upload, and `tests/` is developer-only.

--check also enforces the Agent Skills frontmatter contract, because that is the
rule the desktop/Cowork upload path actually validates against: outside Claude
Code only `name`, `description`, `allowed-tools`, `license`, `metadata` and
`compatibility` are permitted, and any other key is a hard upload error rather
than an ignored field.

    python build.py            # writes ayc-skill.skill
    python build.py --check    # verify an existing bundle, don't rebuild
"""
from __future__ import annotations
import os, sys, zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Windows consoles default to cp1252 and would mangle the em dashes and arrows
    # this prints. Matches the guard the other helpers already carry.
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "skills", "ayc-skill")
OUT = os.path.join(ROOT, "ayc-skill.skill")
EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", "node_modules"}
EXCLUDE_EXT = {".pyc", ".pyo", ".pyd"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}


def wanted(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    name = parts[-1]
    if name in EXCLUDE_NAMES or os.path.splitext(name)[1] in EXCLUDE_EXT:
        return False
    return True


def files():
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            full = os.path.join(dirpath, f)
            if wanted(full):
                yield full


def build():
    if os.path.exists(OUT):
        os.remove(OUT)
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for full in sorted(files()):
            # arcname: forward slashes, rooted at the skill folder name
            rel = os.path.relpath(full, os.path.join(ROOT, "skills")).replace(os.sep, "/")
            z.write(full, rel)
            n += 1
    print(f"wrote {os.path.relpath(OUT, ROOT)} — {n} files, {os.path.getsize(OUT):,} bytes")
    return 0


# The Agent Skills spec allows only these keys. Claude Code accepts more, but a
# .skill carrying an extra key fails desktop/Cowork upload with a hard error.
SPEC_KEYS = {"name", "description", "allowed-tools", "license", "metadata", "compatibility"}
DESC_LIMIT = 1024


def check_frontmatter(text):
    """Validate SKILL.md frontmatter against the Agent Skills spec. Returns problems."""
    problems = []
    if not text.startswith("---"):
        return ["SKILL.md has no YAML frontmatter"]
    fm = text.split("---", 2)[1]
    keys, desc_lines, current = [], [], None
    for line in fm.splitlines():
        if line[:1] not in (" ", "\t", "") and ":" in line:
            current = line.split(":", 1)[0].strip()
            keys.append(current)
            if current == "description":
                rest = line.split(":", 1)[1].strip()
                desc_lines = [] if rest in (">-", ">", "|", "|-", "") else [rest]
        elif current == "description" and line.strip():
            desc_lines.append(line.strip())
    for k in keys:
        if k not in SPEC_KEYS:
            problems.append(f"frontmatter key {k!r} is not in the Agent Skills spec "
                            f"(allowed: {', '.join(sorted(SPEC_KEYS))}) — .skill upload would fail")
    if "description" not in keys:
        problems.append("frontmatter has no description")
    else:
        n = len(" ".join(desc_lines))
        if n > DESC_LIMIT:
            problems.append(f"description is {n} chars, over the {DESC_LIMIT} limit")
    return problems


def check(path=OUT):
    if not os.path.exists(path):
        print(f"no bundle at {path}")
        return 1
    problems = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        for name in names:
            if "\\" in name:
                problems.append(f"backslash path: {name}")
            if "__pycache__" in name or name.endswith((".pyc", ".pyo")):
                problems.append(f"python bytecode shipped: {name}")
            if name.rsplit("/", 1)[-1] in EXCLUDE_NAMES:
                problems.append(f"OS cruft shipped: {name}")
        skill_md = [n for n in names if n.endswith("/SKILL.md")]
        if not skill_md:
            problems.append("no SKILL.md in the bundle")
        else:
            problems += check_frontmatter(z.read(skill_md[0]).decode("utf-8"))
        count = len(names)
    if problems:
        print(f"{path}: {len(problems)} PROBLEM(S)")
        for p in problems:
            print("  " + p)
        return 1
    print(f"{path}: OK — {count} entries, forward-slash paths, no bytecode/cruft, "
          f"spec-legal frontmatter")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv[1:] else (build() or check()))
