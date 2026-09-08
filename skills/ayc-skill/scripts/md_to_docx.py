#!/usr/bin/env python3
"""Render Markdown to a real Microsoft Word (.docx) file. Standard library only —
installs nothing. If `pandoc` is on PATH it's used (best fidelity); otherwise a
built-in stdlib writer produces a valid .docx covering the subset the docs agent
emits: headings, paragraphs, **bold**/*italic*/`code`, bullet + numbered lists,
pipe tables, blockquotes, `---` rules, and fenced code blocks.

Black-box helper: run with --help, then invoke. Don't read this source unless a
customized conversion is truly needed. It exists so the fleet can ship Word
documents (not .md) with zero dependencies, consistently, without hand-rolling
OOXML each time.

USAGE
    python md_to_docx.py --in FILE.md --out FILE.docx
    python md_to_docx.py --in-dir docs_src --out-dir .ayc-skill/docs   # batch: every *.md -> *.docx
    python md_to_docx.py --in FILE.md --out FILE.docx --no-pandoc          # force the built-in writer

Exit 0 on success; prints one line per file written.
"""
from __future__ import annotations
import argparse, html, os, re, shutil, subprocess, sys, zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Windows consoles default to cp1252 and would mangle the em dashes and arrows
    # this prints. Matches the guard the other helpers already carry.
except Exception:
    pass

# ---------------------------------------------------------------- inline runs
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
_ITAL = re.compile(r"\*([^*]+)\*|_([^_]+)_")


def _runs(text: str):
    """Yield (text, bold, italic, code) runs from one line of inline markdown."""
    # Tokenize by protecting code spans first, then bold, then italic.
    tokens = []  # (text, bold, italic, code)

    def emit_plain(s, bold, ital):
        pos = 0
        for m in _ITAL.finditer(s) if not (bold and ital) else []:
            if m.start() > pos:
                tokens.append((s[pos:m.start()], bold, ital, False))
            tokens.append((m.group(1) or m.group(2), bold, True, False))
            pos = m.end()
        if pos < len(s):
            tokens.append((s[pos:], bold, ital, False))

    def emit_bold(s):
        pos = 0
        for m in _BOLD.finditer(s):
            if m.start() > pos:
                emit_plain(s[pos:m.start()], False, False)
            emit_plain(m.group(1) or m.group(2), True, False)
            pos = m.end()
        if pos < len(s):
            emit_plain(s[pos:], False, False)

    pos = 0
    for m in _CODE.finditer(text):
        if m.start() > pos:
            emit_bold(text[pos:m.start()])
        tokens.append((m.group(1), False, False, True))
        pos = m.end()
    if pos < len(text):
        emit_bold(text[pos:])
    return [t for t in tokens if t[0]]


def _run_xml(text, bold, ital, code):
    props = []
    if bold:
        props.append("<w:b/>")
    if ital:
        props.append("<w:i/>")
    if code:
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    esc = html.escape(text).replace("\t", "    ")
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc}</w:t></w:r>'


def _para(text, style=None, runs=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    body = "".join(_run_xml(*r) for r in (runs if runs is not None else _runs(text)))
    return f"<w:p>{ppr}{body}</w:p>"


def _table(rows):
    # rows: list[list[str]] ; first row = header
    out = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
           '<w:tblW w:w="0" w:type="auto"/></w:tblPr>']
    for i, row in enumerate(rows):
        out.append("<w:tr>")
        for cell in row:
            runs = [(t, b or i == 0, it, c) for (t, b, it, c) in _runs(cell)]
            out.append(f"<w:tc><w:tcPr><w:tcW w:w=\"0\" w:type=\"auto\"/></w:tcPr>{_para('', runs=runs)}</w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    # a trailing empty paragraph keeps Word happy after a table
    return "".join(out) + "<w:p/>"


# ---------------------------------------------------------------- block parse
def md_to_body(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    body, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # fenced code block
        if stripped.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            for cl in code:
                body.append(_para("", style="Code", runs=[(cl or " ", False, False, True)]))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            body.append(_para(m.group(2).strip(), style=f"Heading{len(m.group(1))}"))
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*([-*_])\1\1+\s*$", line):
            body.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" '
                        'w:space="1" w:color="auto"/></w:pBdr></w:pPr></w:p>')
            i += 1
            continue

        # table (pipe) — a header row followed by a |---|--- separator
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            def cells(row):
                row = row.strip().strip("|")
                return [c.strip() for c in row.split("|")]
            rows = [cells(line)]
            i += 2
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]))
                i += 1
            body.append(_table(rows))
            continue

        # blockquote
        if stripped.startswith(">"):
            body.append(_para(stripped.lstrip("> ").strip(), style="Quote"))
            i += 1
            continue

        # bullet list (literal marker — avoids needing a numbering.xml part)
        if re.match(r"^\s*[-*+]\s+", line):
            body.append(_para("•  " + re.sub(r"^\s*[-*+]\s+", "", line), style="ListBullet"))
            i += 1
            continue

        # numbered list (keep the original number as a literal marker)
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if m:
            body.append(_para(f"{m.group(1)}.  {m.group(2)}", style="ListNumber"))
            i += 1
            continue

        # blank line
        if not stripped:
            i += 1
            continue

        # plain paragraph
        body.append(_para(stripped))
        i += 1
    return "".join(body)


# ---------------------------------------------------------------- docx package
_CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>')

_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>')

_DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>')


def _styles_xml():
    heads = "".join(
        f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/>'
        f'<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="{240 - i*20}" w:after="60"/>'
        f'<w:outlineLvl w:val="{i-1}"/></w:pPr>'
        f'<w:rPr><w:b/><w:sz w:val="{36 - (i-1)*4}"/><w:color w:val="1F2933"/></w:rPr></w:style>'
        for i in range(1, 7))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:style>'
        + heads +
        '<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="40"/><w:ind w:left="720" w:hanging="360"/></w:pPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="ListNumber"><w:name w:val="List Number"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="40"/><w:ind w:left="720" w:hanging="360"/></w:pPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:ind w:left="480"/></w:pPr><w:rPr><w:i/><w:color w:val="52606D"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="0"/><w:shd w:val="clear" w:fill="F5F7FA"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="20"/></w:rPr></w:style>'
        '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
        '<w:tblPr><w:tblBorders>'
        + "".join(f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="C9CED6"/>'
                  for e in ("top", "left", "bottom", "right", "insideH", "insideV")) +
        '</w:tblBorders></w:tblPr></w:style>'
        '</w:styles>')


def write_docx(md: str, out_path: str):
    body = md_to_body(md)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{body}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>')
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _styles_xml())
        z.writestr("word/document.xml", document)


def convert(in_path: str, out_path: str, use_pandoc: bool = True) -> str:
    if use_pandoc and shutil.which("pandoc"):
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        r = subprocess.run(["pandoc", "-f", "gfm", "-t", "docx", "-o", out_path, in_path],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return f"wrote {out_path} (pandoc)"
        # fall through to builtin on pandoc failure
    with open(in_path, encoding="utf-8") as f:
        write_docx(f.read(), out_path)
    return f"wrote {out_path} (builtin)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render Markdown to Microsoft Word (.docx). Stdlib only; uses pandoc if present.")
    ap.add_argument("--in", dest="inp", help="input .md file")
    ap.add_argument("--out", dest="out", help="output .docx file")
    ap.add_argument("--in-dir", help="convert every *.md in this dir")
    ap.add_argument("--out-dir", help="write *.docx here (with --in-dir)")
    ap.add_argument("--no-pandoc", action="store_true", help="force the built-in writer")
    a = ap.parse_args(argv)
    use_pandoc = not a.no_pandoc

    if a.in_dir:
        out_dir = a.out_dir or a.in_dir
        for name in sorted(os.listdir(a.in_dir)):
            if name.lower().endswith(".md"):
                src = os.path.join(a.in_dir, name)
                dst = os.path.join(out_dir, name[:-3] + ".docx")
                print(convert(src, dst, use_pandoc))
        return 0
    if a.inp and a.out:
        print(convert(a.inp, a.out, use_pandoc))
        return 0
    ap.error("give --in/--out or --in-dir[/--out-dir]")


if __name__ == "__main__":
    sys.exit(main())
