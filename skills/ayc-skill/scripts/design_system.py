#!/usr/bin/env python3
"""Compose a verified design system from a plain-language brief. Standard library
only — installs nothing, no network.

Given "premium minimal SaaS landing page" it matches a product rule, selects a
style / palette / font pairing, and emits a concrete spec: layout pattern +
section order, design tokens as CSS variables, typography with the CORRECT
provider import, key effects, anti-patterns to avoid, and a pre-delivery
checklist.

What makes this different from a lookup table: **it verifies what it emits.**
Every colour pair it prints carries a measured WCAG contrast ratio and a pass/fail
verdict, and `--validate` gates the whole dataset (contrast, font provider vs
import-URL coherence, referential integrity) with a non-zero exit on failure. A
generator that confidently emits an unreadable palette or a font-family it never
imported is worse than no generator.

Black-box helper: run with --help, then invoke.

USAGE
    python design_system.py "premium minimal SaaS landing page"
    python design_system.py "developer tool docs" --format json
    python design_system.py "analytics dashboard" --persist --output-dir .ayc-skill
    python design_system.py "checkout flow" --persist --page checkout -o .ayc-skill
    python design_system.py --validate          # dataset integrity gate (CI-friendly, offline)
    python design_system.py --validate --check-fonts   # + confirm providers really serve the families
    python design_system.py --check-fonts       # font probe only (needs network)
"""
from __future__ import annotations
import argparse, csv, json, math, os, re, sys, urllib.error, urllib.request

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
AA_NORMAL, AA_LARGE, AAA_NORMAL = 4.5, 3.0, 7.0

# Windows consoles default to cp1252 and would crash on the arrows/em-dashes below.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - non-reconfigurable stream
    pass


# ------------------------------------------------------------------ data load
def load(name):
    path = os.path.join(DATA, f"{name}.csv")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def by_id(rows):
    return {r["id"]: r for r in rows}


# ------------------------------------------------------------------- contrast
def _srgb(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def contrast(fg, bg):
    l1, l2 = luminance(fg), luminance(bg)
    lo, hi = sorted((l1, l2))
    return round((hi + 0.05) / (lo + 0.05), 2)


def verdict(ratio, large=False):
    need = AA_LARGE if large else AA_NORMAL
    if ratio >= AAA_NORMAL:
        return "AAA"
    return "AA" if ratio >= need else "FAIL"


# --------------------------------------------------------------------- search
_WORD = re.compile(r"[a-z0-9]+")


def toks(text):
    return _WORD.findall((text or "").lower())


def bm25(query, docs, k1=1.5, b=0.75):
    """docs: list[(key, text)] -> {key: score}"""
    corpus = {k: toks(t) for k, t in docs}
    n = len(corpus) or 1
    avg = sum(len(v) for v in corpus.values()) / n
    df = {}
    for words in corpus.values():
        for w in set(words):
            df[w] = df.get(w, 0) + 1
    scores = {}
    q = toks(query)
    for key, words in corpus.items():
        score, dl = 0.0, len(words) or 1
        for term in q:
            if term not in df:
                continue
            tf = words.count(term)
            if not tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg))
        scores[key] = score
    return scores


def pick(query, priority_ids, table, extra_field="keywords"):
    """Choose from a product rule's priority list, letting the brief re-rank it."""
    ids = [i.strip() for i in (priority_ids or "").split(",") if i.strip() and i.strip() in table]
    if not ids:
        return None
    docs = [(i, f"{table[i].get('id','')} {table[i].get(extra_field,'')} "
                f"{table[i].get('mood','')} {table[i].get('best_for','')} {table[i].get('style','')}")
            for i in ids]
    scores = bm25(query, docs)
    best = max(ids, key=lambda i: (scores.get(i, 0.0), -ids.index(i)))
    # ties / no signal -> keep the curated first choice
    return table[best] if scores.get(best, 0) > 0 else table[ids[0]]


# -------------------------------------------------------------------- compose
def pick_motion(style, motions, stack=None, forced=None):
    """Choose an animation library from the style's preference order, filtered by stack.

    Motion choice is a real performance decision, so the generator makes it
    explicitly rather than leaving the agent to guess a dependency's cost.
    """
    mtab = by_id(motions)
    if forced and forced in mtab:
        return mtab[forced]
    ids = [i.strip() for i in ((style or {}).get("motion_priority") or "").split(",")
           if i.strip() and i.strip() in mtab]
    if not ids:
        return None
    if stack:
        s = stack.lower().strip()
        fits = [i for i in ids
                if s in normalise(mtab[i]["stacks"]).split() or mtab[i]["stacks"].strip() == "all"]
        if fits:
            return mtab[fits[0]]
    return mtab[ids[0]]


def compose(query, products, styles, palettes, fonts, overrides=None, motions=None, stack=None):
    overrides = overrides or {}
    pdocs = [(r["id"], f"{r['product']} {r['keywords']} {r['pattern']}") for r in products]
    pscore = bm25(query, pdocs)
    ptab = by_id(products)
    best_pid = max(ptab, key=lambda i: pscore.get(i, 0.0))
    matched = pscore.get(best_pid, 0.0) > 0
    rule = ptab[best_pid]

    stab, ctab, ftab = by_id(styles), by_id(palettes), by_id(fonts)
    style = stab.get(overrides.get("style")) or pick(query, rule["style_priority"], stab)
    palette = ctab.get(overrides.get("palette")) or pick(query, rule["palette_priority"], ctab, "mood")
    font = ftab.get(overrides.get("font")) or pick(query, rule["font_priority"], ftab, "mood")

    return {
        "brief": query,
        "matched_product": rule["product"],
        "match_confidence": "matched" if matched else "no keyword match - fell back to first rule",
        "pattern": rule["pattern"],
        "section_order": [s.strip() for s in rule["section_order"].split(",")],
        "style": style,
        "palette": palette,
        "font": font,
        "key_effects": rule["key_effects"],
        "anti_patterns": [a.strip() for a in rule["anti_patterns"].split(",")],
        "severity": rule["severity"],
        "motion_lib": pick_motion(style, motions or [], stack, overrides.get("motion")),
        "stack": stack,
    }


PAIRS = [("foreground", "background", "body text"),
         ("on_primary", "primary", "text on primary"),
         ("on_accent", "accent", "text on accent"),
         ("card_foreground", "card", "text on card"),
         ("muted_foreground", "muted", "muted text"),
         ("on_destructive", "destructive", "text on destructive")]

TOKENS = ["primary", "on_primary", "accent", "on_accent", "background", "foreground",
          "card", "card_foreground", "muted", "muted_foreground", "border", "destructive"]


def checklist(spec):
    base = ["Every colour pair below meets WCAG AA (verified by this tool - re-verify after any overlay/gradient)",
            "Focus states visible on every interactive element",
            "`prefers-reduced-motion` path implemented for all motion",
            "Tap targets >= 44px on touch",
            "Responsive at 375 / 768 / 1024 / 1440",
            "Icons are SVG (never emoji) with accessible labels",
            "Type scale and spacing come from tokens, not magic numbers"]
    if spec["style"] and "HIGH RISK" in (spec["style"].get("a11y_notes") or ""):
        base.insert(1, f"STYLE RISK - {spec['style']['a11y_notes']}")
    return base


# ------------------------------------------------------------------- renderers
def render_markdown(spec):
    s, p, f = spec["style"], spec["palette"], spec["font"]
    out = [f"# Design System — {spec['brief']}", ""]
    out += [f"**Matched product:** {spec['matched_product']}  ",
            f"**Match:** {spec['match_confidence']}  ",
            f"**Priority:** {spec['severity']}", ""]
    out += ["## Layout pattern", f"**{spec['pattern']}**", "",
            "Section order: " + " → ".join(spec["section_order"]), ""]
    if s:
        out += ["## Style", f"**{s['style']}** — {s['keywords']}", "",
                f"- **Best for:** {s['best_for']}",
                f"- **Do not use for:** {s['avoid_for']}",
                f"- **Effects:** {s['effects']}",
                f"- **Motion:** {s['motion']}",
                f"- **Performance:** {s['perf']}",
                f"- **Accessibility:** {s['a11y_notes']}",
                f"- **Signature moment:** {s['signature_moment']}", ""]
    if p:
        out += ["## Colour tokens", "", f"_Palette: {p['name']} — {p['mood']} ({p['mode']} mode)_", "",
                "| Token | Hex | CSS variable |", "|---|---|---|"]
        for t in TOKENS:
            out.append(f"| {t} | `{p[t]}` | `--color-{t.replace('_','-')}` |")
        out += ["", "### Verified contrast", "", "| Pair | Ratio | WCAG |", "|---|---|---|"]
        for fg, bg, label in PAIRS:
            r = contrast(p[fg], p[bg])
            out.append(f"| {label} (`{p[fg]}` on `{p[bg]}`) | {r}:1 | {verdict(r)} |")
        out += ["", f"_Notes: {p['notes']}_", ""]
    if f:
        out += ["## Typography", f"- **Provider:** {f['provider']}",
                f"- **Heading:** {f['heading']}", f"- **Body:** {f['body']}"]
        if f.get("mono"):
            out.append(f"- **Mono:** {f['mono']}")
        out.append(f"- **Mood:** {f['mood']}")
        urls = import_urls(f)
        if urls:
            out += ["", "```css"] + [f"@import url('{u}');" for u in urls] + [
                f"/* stack */ font-family: {f['css_stack']};", "```", ""]
        else:
            out += ["", "```css", f"/* no import needed */ font-family: {f['css_stack']};", "```", ""]
    m = spec.get("motion_lib")
    if m:
        out += ["## Motion", ""]
        if s:
            out.append(f"**Character:** {s['motion']}")
        out += ["", f"**Recommended library:** {m['name']}"
                + (f" — `{m['package']}`" if m["package"] not in ("none", "") else " (no dependency)"),
                "",
                f"- **Weight:** {m['weight_tier']} — {m['weight_note']}",
                f"- **Stacks:** {m['stacks']}" + (f"  _(selected for: {spec['stack']})_" if spec.get("stack") else ""),
                f"- **Strengths:** {m['strengths']}",
                f"- **Best for:** {m['best_for']}",
                f"- **Do NOT reach for it when:** {m['avoid_when']}",
                f"- **Reduced motion:** {m['reduced_motion']}",
                f"- **SSR:** {m['ssr_notes']}",
                f"- **Licence:** {m['license']}",
                "",
                "_Cheaper option first: if a CSS transition expresses the idea, use it — "
                "an animation dependency must earn its bytes against the performance budget._",
                ""]
    out += ["## Key effects", spec["key_effects"], ""]
    out += ["## Anti-patterns — do NOT do these"] + [f"- {a}" for a in spec["anti_patterns"]] + [""]
    out += ["## Pre-delivery checklist"] + [f"- [ ] {c}" for c in checklist(spec)] + [""]
    out += ["---", "_Generated by ayc-skill design_system.py. Contrast ratios are measured, "
            "not asserted. Re-verify contrast against the rendered result after any gradient, "
            "image, or translucency overlay._"]
    return "\n".join(out)


def render_json(spec):
    p = spec["palette"]
    payload = dict(spec)
    if p:
        payload["contrast"] = {label: {"fg": p[fg], "bg": p[bg], "ratio": contrast(p[fg], p[bg]),
                                       "wcag": verdict(contrast(p[fg], p[bg]))}
                               for fg, bg, label in PAIRS}
    payload["checklist"] = checklist(spec)
    return json.dumps(payload, indent=2)


# ------------------------------------------------------------------- validate
def normalise(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def import_urls(f):
    """Every stylesheet URL a pairing needs, in order.

    `import_url` may hold more than one whitespace-separated URL, because not every
    provider serves multiple families from one request. Fontshare's API answers a
    multi-family `f[]=a&f[]=b` query with only the FIRST family, silently, with a
    200 - so a pairing that needed two requests and made one shipped a body font
    the page never loaded.
    """
    return (f.get("import_url") or "").split()


_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def check_fonts_online(fonts, timeout=10):
    """Opt-in network probe: does each declared family actually exist at its provider?

    The offline validator proves internal consistency (the family is named in the
    import URL). Only the provider can confirm the family still EXISTS. Returns
    (failures, skipped, checked). A network problem is a `skipped`, never a
    failure - a CI gate must not go red because a runner had no egress.
    """
    failures, skipped, checked = [], [], 0
    for f in fonts:
        if f["provider"] == "system" or not f["import_url"]:
            continue
        fams = [f["heading"], f["body"]] + ([f["mono"]] if f.get("mono") else [])
        fams = list(dict.fromkeys(fams))
        bodies, http_error, net_error = [], None, None
        for url in import_urls(f):
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    bodies.append((r.status, r.read().decode("utf-8", "replace")))
            except urllib.error.HTTPError as e:
                http_error = e.code
                break
            except Exception as e:  # DNS, TLS, timeout, offline
                net_error = type(e).__name__
                break
        if http_error is not None:
            # 4xx from a font CDN means the family/slug is wrong - that IS a failure.
            failures.append(f"FONT-NET  {f['id']}: provider returned HTTP {http_error} for its import_url "
                            f"-> at least one family name/slug is wrong")
            checked += 1
            continue
        if net_error is not None:
            skipped.append(f"{f['id']} ({net_error})")
            continue
        checked += 1
        css = normalise("\n".join(b for _, b in bodies))
        bad_status = [st for st, _ in bodies if st != 200]
        if bad_status or not css.strip():
            failures.append(f"FONT-NET  {f['id']}: provider returned HTTP "
                            f"{bad_status[0] if bad_status else 200} / empty CSS")
            continue
        for fam in fams:
            if normalise(fam) not in css:
                failures.append(f"FONT-NET  {f['id']}: '{fam}' is not served by {f['provider']} "
                                f"at this URL -> it would silently fall back")
    return failures, skipped, checked


def validate(styles, palettes, fonts, products, motions=None, check_online=False):
    motions = motions or []
    failures, checks = [], 0

    mtab = by_id(motions)
    for s in styles:
        refs = [x.strip() for x in (s.get("motion_priority") or "").split(",") if x.strip()]
        if not refs:
            failures.append(f"REF       style {s['id']}: no motion_priority set")
        for ref in refs:
            checks += 1
            if ref not in mtab:
                failures.append(f"REF       style {s['id']}: motion library '{ref}' does not exist")

    for p in palettes:
        for fg, bg, label in PAIRS:
            checks += 1
            r = contrast(p[fg], p[bg])
            if r < AA_NORMAL:
                failures.append(f"CONTRAST  {p['id']}: {label} {p[fg]} on {p[bg]} = {r}:1 (< {AA_NORMAL})")

    for f in fonts:
        checks += 1
        fams = [f["heading"], f["body"]] + ([f["mono"]] if f.get("mono") else [])
        url = normalise(" ".join(import_urls(f)))
        if f["provider"] == "system":
            if f["import_url"]:
                failures.append(f"FONT      {f['id']}: provider=system but an import_url is set")
            continue
        if not f["import_url"]:
            failures.append(f"FONT      {f['id']}: provider={f['provider']} but import_url is empty")
            continue
        for fam in fams:
            if normalise(fam) not in url:
                failures.append(f"FONT      {f['id']}: declares '{fam}' but import_url never loads it "
                                f"-> font-family would silently fall back")

    stab, ctab, ftab = by_id(styles), by_id(palettes), by_id(fonts)
    for r in products:
        for field, table, kind in (("style_priority", stab, "style"),
                                   ("palette_priority", ctab, "palette"),
                                   ("font_priority", ftab, "font")):
            for ref in [x.strip() for x in r[field].split(",") if x.strip()]:
                checks += 1
                if ref not in table:
                    failures.append(f"REF       {r['id']}: {kind} '{ref}' does not exist")

    net_note = ""
    if check_online:
        nf, skipped, nchecked = check_fonts_online(fonts)
        failures += nf
        checks += nchecked
        net_note = f" Probed {nchecked} font import URL(s) online."
        if skipped:
            net_note += f" SKIPPED (unreachable, not a failure): {', '.join(skipped)}."

    print(f"Validated {checks} checks across {len(palettes)} palettes, {len(fonts)} font pairings, "
          f"{len(styles)} styles, {len(products)} product rules, {len(motions)} motion libraries.{net_note}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for x in failures:
            print("  " + x)
        return 1
    print("All checks passed.")
    return 0


# -------------------------------------------------------------------- persist
def persist(spec, out_dir, page=None):
    root = os.path.join(out_dir, "design-system")
    body = render_markdown(spec)
    if page:
        d = os.path.join(root, "pages")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{page}.md")
        body = body.replace("# Design System —", f"# Page Override: {page} —", 1)
        body += ("\n\n> **Override scope.** This page deviates from `../MASTER.md`. "
                 "Anything not restated here inherits from MASTER.\n")
    else:
        os.makedirs(root, exist_ok=True)
        path = os.path.join(root, "MASTER.md")
        body = body.replace("# Design System —", "# MASTER Design System —", 1)
        body += ("\n\n> **Master scope.** Global rules for the whole product. "
                 "Page-specific deviations live in `pages/<name>.md` and override this file.\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


# ------------------------------------------------------------------------ cli
def main(argv=None):
    ap = argparse.ArgumentParser(description="Compose a verified design system from a brief (stdlib only).")
    ap.add_argument("query", nargs="?", help="the design brief, e.g. 'premium minimal SaaS landing page'")
    ap.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    ap.add_argument("--style", help="force a style id")
    ap.add_argument("--palette", help="force a palette id")
    ap.add_argument("--font", help="force a font-pairing id")
    ap.add_argument("--motion", help="force a motion-library id")
    ap.add_argument("--stack", help="target stack (react, nextjs, vue, svelte, vanilla...) - "
                                    "filters the motion-library recommendation")
    ap.add_argument("--persist", action="store_true", help="write design-system/MASTER.md")
    ap.add_argument("--page", help="write a page override into design-system/pages/")
    ap.add_argument("--output-dir", "-o", default=".", help="where design-system/ is created")
    ap.add_argument("--validate", action="store_true", help="dataset integrity gate; non-zero exit on failure")
    ap.add_argument("--check-fonts", action="store_true",
                    help="ALSO probe each font import URL online to confirm the provider really serves "
                         "those families (opt-in; needs network; unreachable = skipped, not failed)")
    ap.add_argument("--list", choices=["styles", "palettes", "fonts", "products", "motion"],
                    help="list available ids")
    a = ap.parse_args(argv)

    styles, palettes, fonts, products = load("styles"), load("palettes"), load("font-pairings"), load("product-rules")
    motions = load("motion-libraries")

    if a.validate:
        return validate(styles, palettes, fonts, products, motions, check_online=a.check_fonts)
    if a.check_fonts:
        nf, skipped, nchecked = check_fonts_online(fonts)
        print(f"Probed {nchecked} font import URL(s).")
        if skipped:
            print(f"  SKIPPED (unreachable, not a failure): {', '.join(skipped)}")
        if nf:
            print(f"\n{len(nf)} FAILURE(S):")
            for x in nf:
                print("  " + x)
            return 1
        print("All probed families are served by their declared provider.")
        return 0
    if a.list:
        field = {"styles": "style", "palettes": "name", "fonts": "name",
                 "products": "product", "motion": "name"}[a.list]
        rows = {"styles": styles, "palettes": palettes, "fonts": fonts,
                "products": products, "motion": motions}[a.list]
        for r in rows:
            print(f"{r['id']:<24} {r[field]}")
        return 0
    if not a.query:
        ap.error("give a brief, or use --validate / --list")

    spec = compose(a.query, products, styles, palettes, fonts,
                   {"style": a.style, "palette": a.palette, "font": a.font, "motion": a.motion},
                   motions=motions, stack=a.stack)

    if a.persist or a.page:
        print("wrote " + persist(spec, a.output_dir, a.page))
        return 0
    print(render_json(spec) if a.format == "json" else render_markdown(spec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
