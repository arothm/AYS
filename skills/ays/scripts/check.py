#!/usr/bin/env python3
"""Scan a project for breaches of the AYS rules a script can detect.

    check.py <project-dir>              report findings, exit 1 if any is an error
    check.py <project-dir> --strict     also exit 1 on findings marked "review"
    check.py <project-dir> --json       machine-readable findings
    check.py --rules                    list the rule IDs this script checks

Each finding names the rule ID, file and line. "error" means the rule is broken
as written; "review" means it is probably broken but a person must judge it
(an outline: none may have a replacement focus style elsewhere). The checker
covers only rules that can be detected from source text; the rest still need
reading the code against references/.

HTML is parsed with the standard library's html.parser; CSS and JavaScript are
scanned line by line after comments and string literals are blanked, so the
checks are deliberately conservative. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit",
             "coverage", "vendor", "__pycache__", ".venv", "venv", ".cache", ".turbo", ".vercel"}
HTML_EXT = {".html", ".htm"}
CSS_EXT = {".css"}
JS_EXT = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"}
JSX_EXT = {".jsx", ".tsx"}

# Every rule this script can report, with what it looks for. Tests assert each
# ID exists in references/, so a renumbered rule cannot silently orphan a check.
CHECKS = {
    "WEB-008": "uppercase HTML tag names",
    "WEB-012": "more than one <body>",
    "WEB-013": "more than one visible <main>",
    "WEB-016": "absolute link written without a protocol (href=\"www...\")",
    "WEB-018": "<img> without alt, or filler alt text",
    "WEB-020": "markup the parser could not read",
    "WEB-025": "single-quoted attribute values",
    "WEB-027": "<html> without lang",
    "WEB-040": "<a> used as a button (onclick with no real href)",
    "WEB-044": "consecutive <br> tags used for spacing",
    "WEB-048": "ID selectors in CSS",
    "WEB-051": "obsolete align attribute",
    "WEB-053": "<div> inside <p>",
    "WEB-054": "duplicate id values",
    "WEB-068": "<li> outside <ul>, <ol> or <menu>",
    "WEB-070": "type attribute on <ul> or <li>",
    "WEB-074": "obsolete compact attribute",
    "WEB-081": "obsolete table summary attribute",
    "WEB-090": "<source> without a type attribute",
    "WEB-092": "autoplay on audio or video",
    "WEB-093": "loading=\"lazy\" on audio or video",
    "WEB-096": "more than one <figcaption> in a <figure>",
    "WEB-097": "<iframe> without title",
    "WEB-099": "obsolete frameborder or scrolling on <iframe>",
    "WEB-103": "<form> nested in another <form>",
    "WEB-175": "blocking <script src> in <head> without defer, async or type=module",
    "WEB-182": "<meta charset> missing or not first in <head>",
    "WEB-183": "viewport meta missing, or zoom disabled",
    "WEB-185": "meta keywords tag",
    "WEB-186": "skipped heading level",
    "WEB-189": "more than one <h1>",
    "WEB-198": "<img> without width and height",
    "WEB-204": "form control without a name inside a <form>",
    "WEB-205": "password field in a GET form",
    "WEB-207": "more than one autofocus",
    "WEB-209": "British spelling in CSS (colour, centre, behaviour)",
    "WEB-210": "type=\"text/css\" on <link> or <style>",
    "WEB-212": ":hover rule with no matching :focus or :focus-visible rule",
    "WEB-213": "line-height with a unit",
    "WEB-215": "outline: none / outline: 0",
    "WEB-216": "unquoted font-family name containing a space",
    "WEB-218": "font-size in px",
    "WEB-219": "full-height container using 100vh without a dvh value",
    "WEB-221": "width: 100vw",
    "WEB-226": "hsla() instead of hsl() with alpha",
    "WEB-227": "!important",
    "WEB-230": "loose equality (== or !=)",
    "WEB-233": "var declarations",
    "WEB-236": "assignment to a native prototype",
    "WEB-239": "background image without a background-color in the same rule",
    "WEB-246": "scroll-behavior: smooth outside a reduced-motion media query",
    "WEB-258": "secret-looking value in client code",
    "WEB-268": "auth token written to localStorage",
    "WEB-276": "fetch() without a signal or timeout",
    "RCT-005": "create-react-app (react-scripts) dependency",
    "RCT-018": "array index used as a React key",
    "RCT-019": "direct DOM queries in a React component",
    "RCT-021": "state setter called directly in an event attribute",
    "PKG-001": "package.json is not valid JSON",
    "PKG-002": "build tooling listed under dependencies",
    "PKG-005": "more than one package manager lockfile",
    "WEB-024": "package.json without a lockfile",
    "BUN-001": "ts-node or babel-node in a Bun project",
    "BUN-012": "dotenv in a Bun project",
    "GIT-006": "node_modules or log files tracked in git",
    "GIT-009": "secret file (.env, private key) tracked in git",
    "GIT-016": "no README.md at the project root",
}

FILLER_ALT = {"image", "picture", "photo", "img", "pic", "graphic", "icon", "logo.png"}
DEV_TOOLS = {"vite", "webpack", "webpack-cli", "rollup", "esbuild", "parcel", "typescript",
             "eslint", "prettier", "jest", "vitest", "mocha", "nodemon", "ts-node",
             "@babel/core", "babel-loader", "postcss", "autoprefixer", "stylelint",
             "@vitejs/plugin-react", "husky", "lint-staged"}
LOCKFILES = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"]
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_live_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}"
    r"|github_pat_[A-Za-z0-9_]{40,}|xox[bpa]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}"
    r"|-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    r"|(?:NEXT_PUBLIC_|VITE_|REACT_APP_)\w*(?:SECRET|PRIVATE|PASSWORD|SERVICE_ROLE)\w*)")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
# Elements whose end tag may be omitted; a new start tag of a listed sibling closes them.
IMPLIED = {"li": {"li"}, "p": {"p", "div", "ul", "ol", "table", "section", "article",
                               "header", "footer", "nav", "aside", "h1", "h2", "h3",
                               "h4", "h5", "h6", "form", "main", "figure", "blockquote"},
           "dt": {"dt", "dd"}, "dd": {"dt", "dd"}, "option": {"option"},
           "tr": {"tr"}, "td": {"td", "th", "tr"}, "th": {"td", "th", "tr"}}


class Report:
    def __init__(self, root: str):
        self.root = root
        self.findings: list[dict] = []

    def add(self, path: str, line: int, rule: str, severity: str, message: str):
        rel = os.path.relpath(path, self.root).replace(os.sep, "/") if path else "."
        self.findings.append({"file": rel, "line": line, "rule": rule,
                              "severity": severity, "message": message})


# ---------------------------------------------------------------- HTML

class HtmlChecker(HTMLParser):
    def __init__(self, path: str, report: Report):
        super().__init__(convert_charrefs=True)
        self.path, self.r = path, report
        self.stack: list[str] = []
        self.ids: dict[str, int] = {}
        self.counts = {"body": 0, "main": 0, "h1": 0, "autofocus": 0}
        self.last_heading = 0
        self.head_first: str | None = None
        self.in_head = False
        self.saw_charset = self.saw_viewport = self.full_doc = False
        self.forms: list[dict] = []
        self.figures: list[int] = []
        self.prev_br_line = None
        self.text_since_br = ""

    def add(self, rule, severity, message):
        self.r.add(self.path, self.getpos()[0], rule, severity, message)

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        raw = self.get_starttag_text() or ""
        line = self.getpos()[0]
        m = re.match(r"<\s*([A-Za-z][\w-]*)", raw)
        if m and m.group(1) != m.group(1).lower() and "-" not in m.group(1):
            self.add("WEB-008", "error", f"tag <{m.group(1)}> should be lowercase")
        if re.search(r"=\s*'", raw):
            self.add("WEB-025", "review", f"<{tag}> uses single-quoted attribute values")

        # Before implied closing, which would end the <p> the div sits in.
        if tag == "div" and "p" in self.stack:
            self.add("WEB-053", "error", "<div> inside <p>")
        for implied_by, closers in IMPLIED.items():
            if self.stack and self.stack[-1] == implied_by and tag in closers:
                self.stack.pop()

        if tag == "br":
            if self.prev_br_line is not None and not self.text_since_br.strip():
                self.add("WEB-044", "error", "consecutive <br> tags; use <p> and CSS margin")
            self.prev_br_line, self.text_since_br = line, ""
        else:
            self.prev_br_line = None

        if "align" in a:
            self.add("WEB-051", "error", f"obsolete align attribute on <{tag}>")
        if "compact" in a:
            self.add("WEB-074", "error", f"obsolete compact attribute on <{tag}>")
        if "id" in a and a["id"]:
            if a["id"] in self.ids:
                self.add("WEB-054", "error", f"id \"{a['id']}\" already used on line {self.ids[a['id']]}")
            else:
                self.ids[a["id"]] = line
        if "autofocus" in a:
            self.counts["autofocus"] += 1
            if self.counts["autofocus"] == 2:
                self.add("WEB-207", "error", "more than one element has autofocus")

        if tag == "html":
            self.full_doc = True
            if not a.get("lang"):
                self.add("WEB-027", "error", "<html> has no lang attribute")
        elif tag == "head":
            self.full_doc, self.in_head = True, True
        elif tag == "body":
            self.in_head = False
            self.counts["body"] += 1
            if self.counts["body"] == 2:
                self.add("WEB-012", "error", "more than one <body>")
        elif tag == "meta":
            if "charset" in a:
                self.saw_charset = True
            name = a.get("name", "").lower()
            if name == "viewport":
                self.saw_viewport = True
                content = a.get("content", "").replace(" ", "").lower()
                if "user-scalable=no" in content or "user-scalable=0" in content \
                        or re.search(r"maximum-scale=1(\.0)?(,|$)", content):
                    self.add("WEB-183", "error", "viewport disables zoom")
            if name == "keywords":
                self.add("WEB-185", "error", "meta keywords tag; search engines ignore it")
        elif tag == "main":
            if "hidden" not in a:
                self.counts["main"] += 1
                if self.counts["main"] == 2:
                    self.add("WEB-013", "error", "more than one visible <main>")
            bad = [t for t in self.stack if t in {"header", "nav", "footer", "article", "aside"}]
            if bad:
                self.add("WEB-013", "error", f"<main> is nested inside <{bad[-1]}>")
        elif re.fullmatch(r"h[1-6]", tag):
            level = int(tag[1])
            if level == 1:
                self.counts["h1"] += 1
                if self.counts["h1"] == 2:
                    self.add("WEB-189", "error", "more than one <h1>")
            if self.last_heading and level > self.last_heading + 1:
                self.add("WEB-186", "error", f"<{tag}> follows <h{self.last_heading}>; a level was skipped")
            self.last_heading = level
        elif tag == "img":
            if "alt" not in a:
                self.add("WEB-018", "error", f"<img src=\"{a.get('src', '')}\"> has no alt attribute")
            elif a["alt"].strip().lower() in FILLER_ALT:
                self.add("WEB-018", "error", f"alt=\"{a['alt']}\" describes nothing")
            if "width" not in a or "height" not in a:
                self.add("WEB-198", "review", f"<img src=\"{a.get('src', '')}\"> has no width/height")
        elif tag == "a":
            href = a.get("href", None)
            if href and href.lower().startswith("www."):
                self.add("WEB-016", "error", f"href=\"{href}\" has no protocol")
            if "onclick" in a and (href is None or href in {"", "#"} or href.lower().startswith("javascript:")):
                self.add("WEB-040", "error", "<a> used as a button; use <button>")
        elif tag in {"ul", "li"} and "type" in a:
            self.add("WEB-070", "error", f"type attribute on <{tag}>; use CSS list-style-type")
        elif tag == "table" and "summary" in a:
            self.add("WEB-081", "error", "obsolete summary attribute; use <caption>")
        elif tag in {"audio", "video"}:
            if "autoplay" in a:
                self.add("WEB-092", "review", f"<{tag}> autoplays without a user opt-in")
            if a.get("loading", "").lower() == "lazy":
                self.add("WEB-093", "error", f"loading=\"lazy\" does nothing on <{tag}>; use preload")
        elif tag == "source":
            if "type" not in a and any(t in self.stack for t in ("picture", "video", "audio")):
                self.add("WEB-090", "review", "<source> has no type attribute")
        elif tag == "iframe":
            if not a.get("title"):
                self.add("WEB-097", "error", "<iframe> has no title")
            for old in ("frameborder", "scrolling"):
                if old in a:
                    self.add("WEB-099", "error", f"obsolete {old} on <iframe>; use CSS")
        elif tag == "form":
            if self.forms:
                self.add("WEB-103", "error", "<form> nested inside another <form>")
            self.forms.append({"method": a.get("method", "get").lower(), "line": line})
        elif tag == "figure":
            self.figures.append(0)
        elif tag == "figcaption" and self.figures:
            self.figures[-1] += 1
            if self.figures[-1] == 2:
                self.add("WEB-096", "error", "more than one <figcaption> in this <figure>")
        elif tag == "script" and self.in_head and "src" in a:
            if not ({"defer", "async"} & set(a)) and a.get("type", "").lower() != "module":
                self.add("WEB-175", "error", f"<script src=\"{a['src']}\"> in <head> blocks parsing; add defer")
        elif tag in {"link", "style"} and a.get("type", "").lower() == "text/css":
            self.add("WEB-210", "error", f"type=\"text/css\" on <{tag}> is unnecessary")

        if tag in {"input", "select", "textarea"} and self.forms:
            itype = a.get("type", "text").lower()
            if itype not in {"submit", "button", "reset", "image"} and not a.get("name"):
                self.add("WEB-204", "error", f"<{tag}> inside a form has no name, so its value is not submitted")
            if itype == "password" and self.forms[-1]["method"] == "get":
                self.add("WEB-205", "error", "password field in a GET form; use method=\"post\"")
        if tag == "li" and not any(t in self.stack for t in ("ul", "ol", "menu")):
            self.add("WEB-068", "error", "<li> outside <ul>, <ol> or <menu>")

        if self.in_head and tag != "head" and self.head_first is None:
            self.head_first = "charset" if (tag == "meta" and "charset" in a) else "other"
            if self.head_first != "charset":
                self.add("WEB-182", "error", "first element in <head> is not <meta charset>")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        if tag == "form" and self.forms:
            self.forms.pop()
        if tag == "figure" and self.figures:
            self.figures.pop()
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        self.text_since_br += data

    def finish(self):
        if self.full_doc:
            if not self.saw_charset:
                self.r.add(self.path, 1, "WEB-182", "error", "no <meta charset> in the document")
            if not self.saw_viewport:
                self.r.add(self.path, 1, "WEB-183", "error", "no viewport meta tag")


def check_html(path: str, text: str, report: Report):
    p = HtmlChecker(path, report)
    try:
        p.feed(text)
        p.close()
    except Exception as e:  # html.parser is lenient; a crash here is a real parse problem
        report.add(path, p.getpos()[0], "WEB-020", "error", f"markup could not be parsed: {e}")
        return
    p.finish()


# ---------------------------------------------------------------- source scrubbing

def blank_js(text: str) -> str:
    """Replace comments and string/template literals with spaces, keeping newlines,
    so line numbers stay right and code inside strings cannot match a check."""
    out, i, n = [], 0, len(text)
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j])); i = j
        elif c in "'\"`":
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 2
                    continue
                if c != "`" and text[j] == "\n":
                    break  # unterminated (often an apostrophe in JSX text); stop at the line end
                j += 1
            inner = re.sub(r"[^\n]", " ", text[i + 1:min(j, n)])
            if j < n and text[j] == c:
                out.append(c + inner + c); i = j + 1
            else:
                out.append(c + inner); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def blank_css(text: str) -> str:
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ---------------------------------------------------------------- CSS

def css_blocks(text: str):
    """Yield (selector_or_at_rule_chain, body, start_offset) for each declaration block."""
    stack, start, header_start = [], 0, 0
    for i, c in enumerate(text):
        if c == "{":
            stack.append((text[header_start:i].strip(), i + 1))
            header_start = i + 1
        elif c == "}":
            if stack:
                header, body_start = stack.pop()
                body = text[body_start:i]
                if "{" not in body:
                    chain = [h for h, _ in stack] + [header]
                    yield chain, body, body_start
            header_start = i + 1
        elif c == ";" and not stack:
            header_start = i + 1


def check_css(path: str, text: str, report: Report):
    clean = blank_css(text)
    selectors_seen = set()
    hover_rules = []
    for chain, body, at in css_blocks(clean):
        header = chain[-1]
        if header.startswith("@"):
            continue
        for sel in (s.strip() for s in header.split(",")):
            selectors_seen.add(re.sub(r"\s+", " ", sel))
            if re.search(r"#[A-Za-z_-][\w-]*", sel):
                report.add(path, line_of(clean, at), "WEB-048", "review", f"ID selector \"{sel}\"; use a class")
            if ":hover" in sel:
                hover_rules.append((sel, line_of(clean, at)))
        decls = body
        has_image = re.search(r"background(-image)?\s*:[^;]*url\(", decls)
        has_color = re.search(r"background-color\s*:", decls) or re.search(
            r"background\s*:[^;]*(#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\()", decls)
        if has_image and not has_color:
            report.add(path, line_of(clean, at), "WEB-239", "review", "background image without a fallback background-color")
        if re.search(r"(min-)?height\s*:\s*100vh", decls) and "dvh" not in decls:
            report.add(path, line_of(clean, at), "WEB-219", "review", "100vh without a 100dvh value; mobile toolbars cut it off")
        if re.search(r"scroll-behavior\s*:\s*smooth", decls):
            if not any("prefers-reduced-motion" in h and "no-preference" in h for h in chain):
                report.add(path, line_of(clean, at), "WEB-246", "error",
                           "scroll-behavior: smooth outside @media (prefers-reduced-motion: no-preference)")

    for sel, line in hover_rules:
        base = re.sub(r"\s+", " ", sel.replace(":hover", ""))
        if not any(s.replace(":focus-visible", "").replace(":focus-within", "").replace(":focus", "") == base
                   and ":focus" in s for s in selectors_seen):
            report.add(path, line, "WEB-212", "review", f"\"{sel}\" has no matching :focus/:focus-visible style")

    for m in re.finditer(r"!important", clean):
        report.add(path, line_of(clean, m.start()), "WEB-227", "review", "!important; prefer @layer or lower specificity")
    for m in re.finditer(r"outline\s*:\s*(none|0)\b", clean):
        report.add(path, line_of(clean, m.start()), "WEB-215", "review",
                   "outline removed; make sure a visible focus style replaces it")
    for m in re.finditer(r"(?<![-\w])width\s*:\s*100vw", clean):
        report.add(path, line_of(clean, m.start()), "WEB-221", "error", "width: 100vw overflows by the scrollbar width")
    for m in re.finditer(r"line-height\s*:\s*[\d.]+(px|em|rem|%)", clean):
        report.add(path, line_of(clean, m.start()), "WEB-213", "error", "line-height with a unit; use a unitless number")
    for m in re.finditer(r"font-size\s*:\s*[\d.]+px", clean):
        report.add(path, line_of(clean, m.start()), "WEB-218", "review", "font-size in px; use rem")
    for m in re.finditer(r"\bhsla\(", clean):
        report.add(path, line_of(clean, m.start()), "WEB-226", "error", "hsla() is a legacy alias; use hsl() with alpha")
    for m in re.finditer(r"\b(colour|centre|behaviour|capitalise)\b", clean):
        report.add(path, line_of(clean, m.start()), "WEB-209", "error", f"British spelling \"{m.group(1)}\" is invalid CSS")
    for m in re.finditer(r"font-family\s*:\s*([^;}]+)", clean):
        for fam in (f.strip() for f in m.group(1).split(",")):
            if " " in fam and not fam.startswith(("'", '"')) and "var(" not in fam and "!important" not in fam:
                report.add(path, line_of(clean, m.start()), "WEB-216", "error", f"font family {fam} must be quoted")


# ---------------------------------------------------------------- JavaScript / React

def check_js(path: str, text: str, report: Report, is_react: bool):
    clean = blank_js(text)
    ext = os.path.splitext(path)[1]

    def each(pattern, rule, severity, message, src=clean, flags=0):
        for m in re.finditer(pattern, src, flags):
            report.add(path, line_of(src, m.start()), rule, severity, message)

    each(r"\bvar\s+[A-Za-z_$]", "WEB-233", "error", "var declaration; use const or let")
    each(r"(?<![=!<>])==(?!=)|!=(?!=)", "WEB-230", "error", "loose equality; use === or !==")
    each(r"\b(Array|Object|String|Number|Function|Promise|Element|HTMLElement)\.prototype\.\w+\s*=(?!=)",
         "WEB-236", "error", "assignment to a native prototype")
    for m in re.finditer(r"localStorage\s*(\.setItem\s*\(|\[)\s*['\"`][^'\"`]*(token|jwt|auth|session|password|secret)",
                         text, re.I):
        report.add(path, line_of(text, m.start()), "WEB-268", "error",
                   "auth data in localStorage; use an HttpOnly cookie")
    for m in SECRET.finditer(text):
        report.add(path, line_of(text, m.start()), "WEB-258", "error",
                   f"secret-looking value \"{m.group(0)[:12]}...\" in client code")
    for m in re.finditer(r"\bfetch\s*\(", clean):
        depth, j = 0, m.end() - 1
        while j < len(clean):
            if clean[j] == "(":
                depth += 1
            elif clean[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if not re.search(r"\bsignal\b|\btimeout\b", text[m.start():j]):
            report.add(path, line_of(clean, m.start()), "WEB-276", "review",
                       "fetch() without a signal; add AbortSignal.timeout() or a controller")

    if is_react and (ext in JSX_EXT or ext == ".js"):
        each(r"\bon[A-Z]\w*\s*=\s*\{\s*set[A-Z]\w*\s*\(", "RCT-021", "error",
             "setter called during render; wrap it: onClick={() => setX(...)}")
        each(r"\bkey\s*=\s*\{\s*(index|idx|i)\s*\}", "RCT-018", "review",
             "array index as key; use a stable id if the list can change")
        if ext in JSX_EXT:
            each(r"\bdocument\.(getElementById|querySelector(All)?|getElementsBy\w+)\s*\(", "RCT-019", "review",
                 "direct DOM query in a component; use state or a ref")


# ---------------------------------------------------------------- project files

def check_project(root: str, report: Report, tracked: list[str] | None):
    if not any(os.path.exists(os.path.join(root, n)) for n in ("README.md", "readme.md", "Readme.md")):
        report.add("", 0, "GIT-016", "error", "no README.md at the project root")

    pkg_path = os.path.join(root, "package.json")
    deps, dev = {}, {}
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, encoding="utf-8") as f:
                pkg = json.load(f)
            deps, dev = pkg.get("dependencies", {}) or {}, pkg.get("devDependencies", {}) or {}
        except ValueError as e:
            report.add(pkg_path, getattr(e, "lineno", 1), "PKG-001", "error", f"package.json is not valid JSON: {e}")
        locks = [n for n in LOCKFILES if os.path.exists(os.path.join(root, n))]
        if not locks:
            report.add(pkg_path, 1, "WEB-024", "error", "no lockfile; versions are not pinned")
        if len({n.split(".")[0].replace("-lock", "") for n in locks}) > 1:
            report.add(pkg_path, 1, "PKG-005", "error", "lockfiles from several package managers: " + ", ".join(locks))
        for name in sorted(set(deps) & DEV_TOOLS):
            report.add(pkg_path, 1, "PKG-002", "review", f"{name} is build tooling; move it to devDependencies")
        if "react-scripts" in deps or "react-scripts" in dev:
            report.add(pkg_path, 1, "RCT-005", "error", "create-react-app is deprecated; use Vite")
        if any(n.startswith("bun.lock") for n in locks):
            for name in ("dotenv",):
                if name in deps or name in dev:
                    report.add(pkg_path, 1, "BUN-012", "error", "dotenv is redundant; Bun loads .env itself")
            for name in ("ts-node", "babel-node", "@babel/node"):
                if name in deps or name in dev:
                    report.add(pkg_path, 1, "BUN-001", "error", f"{name} is redundant; Bun runs TypeScript directly")

    for rel in tracked or []:
        low = rel.lower()
        if low.startswith("node_modules/") or "/node_modules/" in low:
            report.add(os.path.join(root, rel), 0, "GIT-006", "error", "node_modules is tracked in git")
            break
    for rel in tracked or []:
        base = os.path.basename(rel).lower()
        if base.endswith(".log"):
            report.add(os.path.join(root, rel), 0, "GIT-006", "error", "log file tracked in git")
        if (base == ".env" or (base.startswith(".env.") and not base.endswith((".example", ".sample", ".template")))) \
                or base in {"id_rsa", "id_ed25519"} or base.endswith((".pem", ".key")):
            report.add(os.path.join(root, rel), 0, "GIT-009", "error", "secret file is tracked in git; remove it and rotate its secrets")
    return {**deps, **dev}


def git_tracked(root: str):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.splitlines() if out.returncode == 0 else None


def scan(root: str) -> Report:
    report = Report(root)
    tracked = git_tracked(root)
    packages = check_project(root, report, tracked)
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ".min." not in name and ext in HTML_EXT | CSS_EXT | JS_EXT:
                files.append((os.path.join(dirpath, name), ext))
    is_react = "react" in packages or any(ext in JSX_EXT for _, ext in files)
    for path, ext in files:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        if ext in HTML_EXT:
            check_html(path, text, report)
        elif ext in CSS_EXT:
            check_css(path, text, report)
        else:
            check_js(path, text, report, is_react)
    report.findings.sort(key=lambda f: (f["file"], f["line"], f["rule"]))
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Scan a project for detectable AYS rule breaches.")
    ap.add_argument("root", nargs="?", help="project directory to scan")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    ap.add_argument("--strict", action="store_true", help="exit 1 on review findings too")
    ap.add_argument("--rules", action="store_true", help="list the rules this script checks")
    args = ap.parse_args(argv)

    if args.rules:
        for rid, what in sorted(CHECKS.items()):
            print(f"{rid}  {what}")
        print(f"{len(CHECKS)} rules are checked automatically; the rest need reading the code.")
        return 0
    if not args.root or not os.path.isdir(args.root):
        ap.error("give the project directory to scan")

    report = scan(os.path.abspath(args.root))
    found = report.findings
    if args.json:
        print(json.dumps(found, indent=2))
    else:
        for f in found:
            where = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            print(f"{where}  {f['rule']}  {f['severity']:<6}  {f['message']}")
        errors = sum(f["severity"] == "error" for f in found)
        print(f"\n{len(found)} finding(s): {errors} error(s), {len(found) - errors} to review. "
              f"Checked {len(CHECKS)} of the AYS rules; see rules.py show <ID> for each one's Why.")
    failing = [f for f in found if f["severity"] == "error" or args.strict]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
