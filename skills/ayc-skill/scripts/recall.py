#!/usr/bin/env python3
"""Retrieve the RELEVANT parts of shared memory and docs instead of loading all of
them. Standard library only — installs nothing, no network.

Why this exists: memory and generated docs grow monotonically. Left unchecked,
every agent re-reads every byte on every run — on a mature repo that is hundreds
of KB per agent per run, which is exactly the waste principle 2 forbids. This
ranks memory sections and doc chunks against the agent's actual task and returns
only what matters, plus a small always-included core.

It never silently truncates: the output ends with an inventory of what was left
out, so an agent that needs more knows it exists and can ask for it by name.

Reads `.md` and the generated `.docx` (text is extracted from the OOXML, stdlib
only), so Word docs stay searchable.

USAGE
    python recall.py "budget race condition" --root .ayc-skill
    python recall.py "responsive breakpoints" --role frontend --top 6
    python recall.py "deploy rollback" --root .ayc-skill --format json
    python recall.py --list --root .ayc-skill        # section inventory only
"""
from __future__ import annotations
import argparse, json, math, os, re, sys, xml.etree.ElementTree as ET, zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Sections every agent needs regardless of the query — cheap and load-bearing.
PINNED = ["project overview", "stack & commands", "stack and commands",
          "testing harness", "dependencies", "open questions"]
_WORD = re.compile(r"[a-z0-9]+")
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def toks(t):
    return _WORD.findall((t or "").lower())


def docx_text(path):
    """Extract paragraph text from a .docx without any dependency."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except Exception:
        return ""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return ""
    out = []
    for para in root.iter(f"{_W_NS}p"):
        runs = [n.text or "" for n in para.iter(f"{_W_NS}t")]
        line = "".join(runs).strip()
        if line:
            out.append(line)
    return "\n".join(out)


def split_sections(text, source):
    """Split markdown-ish text into (heading, body, source) on ## / # headings."""
    sections, head, buf = [], "(preamble)", []
    for line in (text or "").splitlines():
        m = re.match(r"^#{1,3}\s+(.*)$", line)
        if m:
            if buf and "".join(buf).strip():
                sections.append((head, "\n".join(buf).strip(), source))
            head, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        sections.append((head, "\n".join(buf).strip(), source))
    return sections


def collect(root):
    sections = []
    mem = os.path.join(root, "memory.md")
    if os.path.isfile(mem):
        with open(mem, encoding="utf-8", errors="replace") as f:
            sections += split_sections(f.read(), "memory.md")
    docs = os.path.join(root, "docs")
    if os.path.isdir(docs):
        for dirpath, _dirs, files in os.walk(docs):
            for name in sorted(files):
                p = os.path.join(dirpath, name)
                rel = os.path.relpath(p, root)
                if name.lower().endswith(".docx") and not name.startswith("~$"):
                    sections += split_sections(docx_text(p), rel)
                elif name.lower().endswith((".md", ".txt")):
                    with open(p, encoding="utf-8", errors="replace") as f:
                        sections += split_sections(f.read(), rel)
    return sections


def bm25(query, docs, k1=1.5, b=0.75):
    corpus = {k: toks(t) for k, t in docs}
    n = len(corpus) or 1
    avg = sum(len(v) for v in corpus.values()) / n or 1
    df = {}
    for words in corpus.values():
        for w in set(words):
            df[w] = df.get(w, 0) + 1
    out = {}
    for key, words in corpus.items():
        s, dl = 0.0, len(words) or 1
        for term in toks(query):
            if term not in df:
                continue
            tf = words.count(term)
            if not tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg))
        out[key] = s
    return out


def is_pinned(heading, role=None):
    h = heading.lower()
    if any(p in h for p in PINNED):
        return True
    # a role gets its own accumulated learnings pinned
    return bool(role) and "agent learnings" in h


def recall(root, query, top=6, role=None):
    sections = collect(root)
    if not sections:
        return [], [], 0
    keyed = {i: s for i, s in enumerate(sections)}
    scores = bm25(query, [(i, f"{s[0]} {s[1]}") for i, s in keyed.items()])
    pinned = [i for i, s in keyed.items() if is_pinned(s[0], role)]
    ranked = [i for i in sorted(scores, key=lambda i: -scores[i])
              if scores[i] > 0 and i not in pinned][:top]
    chosen = pinned + ranked
    omitted = [i for i in keyed if i not in chosen]
    total = sum(len(s[1]) for s in sections)
    return [keyed[i] for i in chosen], [keyed[i] for i in omitted], total


def render(chosen, omitted, total, query, role):
    kept = sum(len(b) for _h, b, _s in chosen)
    out = [f"# Recalled context — query: {query!r}" + (f" · role: {role}" if role else ""), "",
           f"_Returned {len(chosen)} of {len(chosen) + len(omitted)} sections "
           f"(~{kept:,} of ~{total:,} chars). Pinned sections are always included._", ""]
    for h, body, src in chosen:
        out += [f"## {h}  _[{src}]_", body, ""]
    if omitted:
        out += ["---", "### Not included (available on request — nothing was silently dropped)"]
        out += [f"- {h}  _[{src}]_" for h, _b, src in omitted]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Retrieve relevant memory/doc sections instead of loading everything.")
    ap.add_argument("query", nargs="?", help="what this agent is about to work on")
    ap.add_argument("--root", default=".ayc-skill", help="the .ayc-skill directory (default: .ayc-skill)")
    ap.add_argument("--top", type=int, default=6, help="max non-pinned sections to return (default: 6)")
    ap.add_argument("--role", help="agent role; pins that role's Agent learnings")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--list", action="store_true", help="list every section without ranking")
    a = ap.parse_args(argv)

    if not os.path.isdir(a.root):
        print(f"No memory at {a.root!r} — first run, nothing to recall.", file=sys.stderr)
        return 0
    if a.list:
        for h, body, src in collect(a.root):
            print(f"{len(body):>7,}  {src:<28} {h}")
        return 0
    if not a.query:
        ap.error("give a query, or use --list")

    chosen, omitted, total = recall(a.root, a.query, a.top, a.role)
    if not chosen and not omitted:
        print(f"No memory at {a.root!r} — nothing to recall.")
        return 0
    if a.format == "json":
        print(json.dumps({"query": a.query, "role": a.role,
                          "returned": [{"heading": h, "source": s, "body": b} for h, b, s in chosen],
                          "omitted": [{"heading": h, "source": s} for h, _b, s in omitted],
                          "chars_total": total,
                          "chars_returned": sum(len(b) for _h, b, _s in chosen)}, indent=2))
    else:
        print(render(chosen, omitted, total, a.query, a.role))
    return 0


if __name__ == "__main__":
    sys.exit(main())
