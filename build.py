#!/usr/bin/env python3
"""Build ays.skill, the zip that Claude Desktop and Cowork accept as an upload.

    python build.py            write ays.skill from skills/ays/
    python build.py --check    verify ays.skill matches skills/ays/ and is uploadable

The bundle is deterministic: sorted entries, a fixed timestamp, forward-slash
paths and LF line endings, so the same source gives the same bytes on Windows
and Linux. Hand-made zips have failed the upload validator before (backslash
paths, shipped __pycache__), which is why this script exists.

--check enforces the Agent Skills frontmatter contract the upload path applies:
only the keys in ALLOWED_KEYS, a lowercase-hyphenated name equal to the folder
name, and a description of at most 1024 characters. Any other key is a hard
upload error, not an ignored field.
"""
from __future__ import annotations

import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "skills", "ays")
OUT = os.path.join(ROOT, "ays.skill")
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_EXT = {".pyc", ".pyo"}
TEXT_EXT = {".md", ".py", ".json", ".csv", ".txt"}
EPOCH = (1980, 1, 1, 0, 0, 0)


def sources(src: str) -> dict[str, bytes]:
    """Map archive path -> bytes for every file that belongs in the bundle."""
    top = os.path.basename(src)
    files: dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if os.path.splitext(name)[1] in SKIP_EXT:
                continue
            path = os.path.join(dirpath, name)
            with open(path, "rb") as f:
                data = f.read()
            if os.path.splitext(name)[1] in TEXT_EXT:
                data = data.replace(b"\r\n", b"\n")
            rel = os.path.relpath(path, os.path.dirname(src)).replace(os.sep, "/")
            files[rel if rel.startswith(top + "/") else top + "/" + rel] = data
    return files


def frontmatter_problems(skill_md: str, folder: str) -> list[str]:
    m = re.match(r"---\n(.*?)\n---\n", skill_md, re.S)
    if not m:
        return ["SKILL.md has no frontmatter block"]
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        km = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if km:
            fields[km.group(1)] = km.group(2).strip()
    problems = [f"frontmatter key {k!r} is not allowed outside Claude Code"
                for k in sorted(set(fields) - ALLOWED_KEYS)]
    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        problems.append(f"name {name!r} must be lowercase letters, digits and hyphens")
    elif name != folder:
        problems.append(f"name {name!r} must equal the folder name {folder!r}")
    desc = fields.get("description", "")
    if not desc:
        problems.append("description is missing")
    elif len(desc) > 1024:
        problems.append(f"description is {len(desc)} characters; the limit is 1024")
    return problems


def build(src: str = SRC, out: str = OUT) -> int:
    files = sources(src)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files):
            info = zipfile.ZipInfo(rel, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[rel])
    return len(files)


def check(src: str = SRC, out: str = OUT) -> list[str]:
    if not os.path.exists(out):
        return [f"{os.path.basename(out)} does not exist; run python build.py"]
    with zipfile.ZipFile(out) as z:
        bundled = {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}
    problems = [f"bad entry {n!r}" for n in bundled
                if "\\" in n or "__pycache__" in n or os.path.splitext(n)[1] in SKIP_EXT]
    expected = sources(src)
    if bundled != expected:
        changed = sorted(set(bundled) ^ set(expected)) or sorted(
            n for n in expected if bundled.get(n) != expected[n])
        problems.append("bundle is stale; run python build.py (differs: "
                        + ", ".join(changed[:5]) + ")")
    top = os.path.basename(src)
    skill_md = expected.get(top + "/SKILL.md")
    if skill_md is None:
        problems.append("SKILL.md is missing")
    else:
        problems += frontmatter_problems(skill_md.decode("utf-8"), top)
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--check"]:
        problems = check()
        for p in problems:
            print("FAIL " + p)
        if problems:
            return 1
        print(f"OK: {os.path.basename(OUT)} matches skills/ays and is uploadable")
        return 0
    if argv:
        print(__doc__)
        return 2
    n = build()
    print(f"wrote {os.path.basename(OUT)}: {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
