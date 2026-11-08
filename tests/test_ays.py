"""Tests for rules.py, check.py and build.py. Standard library only:

    python -m unittest discover -s tests
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "ays")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, ROOT)

import build  # noqa: E402
import check  # noqa: E402
import rules  # noqa: E402


def rmtree(path):
    # git marks its object files read-only, which Windows refuses to delete.
    def force(func, p, _exc):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onerror=force)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def make_skill(tmp, skill_md, refs, add_why=True):
    """Write a throwaway skill. Unless add_why is False, every rule line gets a
    Why line, so each test only exercises the problem it is about."""
    os.makedirs(os.path.join(tmp, "references"))
    with open(os.path.join(tmp, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)
    for name, text in refs.items():
        if add_why:
            text = re.sub(r"(?m)^(- `[^`]+` .*)$", r"\1\n  - Why: w", text)
        with open(os.path.join(tmp, "references", name), "w", encoding="utf-8") as f:
            f.write(text)
    return tmp


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


SKILL_MD = "---\nname: x\ndescription: d\n---\nLoad `references/a.md`.\n"


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, self.tmp)

    def problems(self, refs, skill_md=SKILL_MD, add_why=True):
        return rules.validate(make_skill(self.tmp, skill_md, refs, add_why))

    def test_real_skill_is_valid(self):
        self.assertEqual(rules.validate(SKILL), [])

    def test_real_skill_keeps_every_original_number(self):
        # 423 rules were handed over (13 duplicates merged, none dropped), then
        # batch 2 (2026-11-07) added 17 new IDs and batch 3 (2026-11-08) 12.
        found, merges, _ = rules.load(SKILL)
        self.assertEqual(len(found) + len(merges), 423 + 17 + 12)

    def test_real_skill_has_a_why_for_every_rule(self):
        found, _, _ = rules.load(SKILL)
        self.assertEqual([rid for rid, (_, _, why) in found.items() if not why], [])

    def test_clean_file_passes(self):
        self.assertEqual(self.problems({"a.md": "- `WEB-001` one\n- `WEB-002` see WEB-001\n"}), [])

    def test_missing_why(self):
        p = self.problems({"a.md": "- `WEB-001` one\n  - Why: w\n- `WEB-002` two\n"}, add_why=False)
        self.assertEqual(p, ["a.md: WEB-002 has no 'Why' line under it"])

    def test_two_whys(self):
        p = self.problems({"a.md": "- `WEB-001` one\n  - Why: a\n  - Why: b\n"}, add_why=False)
        self.assertTrue(any("more than one Why" in x for x in p), p)

    def test_why_cross_reference_is_checked(self):
        p = self.problems({"a.md": "- `WEB-001` one\n  - Why: see WEB-404\n"}, add_why=False)
        self.assertTrue(any("WEB-404" in x for x in p), p)

    def test_duplicate_id(self):
        p = self.problems({"a.md": "- `WEB-001` one\n- `WEB-001` two\n"})
        self.assertTrue(any("duplicates" in x for x in p), p)

    def test_malformed_id(self):
        p = self.problems({"a.md": "- `WEB-1` one\n"})
        self.assertTrue(any("malformed" in x for x in p), p)

    def test_dangling_cross_reference(self):
        p = self.problems({"a.md": "- `WEB-001` see WEB-999\n"})
        self.assertTrue(any("WEB-999, which does not exist" in x for x in p), p)

    def test_id_like_terms_are_not_citations(self):
        p = self.problems({"a.md": "- `WEB-001` encrypt with AES-256 and SHA-256\n"})
        self.assertEqual(p, [])

    def test_unknown_area_prefix(self):
        p = self.problems({"a.md": "- `XYZ-001` one\n"})
        self.assertTrue(any("unknown area prefix" in x for x in p), p)

    def test_reference_to_merged_rule(self):
        p = self.problems({"a.md": "- `WEB-001` one\n- `WEB-003` see WEB-002\n\n"
                                   "## Merged rules\n\nWEB-002 → WEB-001\n"})
        self.assertTrue(any("was merged" in x for x in p), p)

    def test_merged_id_still_present(self):
        p = self.problems({"a.md": "- `WEB-001` one\n- `WEB-002` two\n\n"
                                   "## Merged rules\n\nWEB-002 → WEB-001\n"})
        self.assertTrue(any("still a rule" in x for x in p), p)

    def test_merge_into_missing_rule(self):
        p = self.problems({"a.md": "- `WEB-001` one\n\n## Merged rules\n\nWEB-002 and WEB-003 → WEB-009\n"})
        self.assertEqual(sum("does not exist" in x for x in p), 2, p)

    def test_unlinked_reference_file(self):
        p = self.problems({"a.md": "- `WEB-001` one\n", "b.md": "- `GIT-001` two\n"})
        self.assertTrue(any("b.md is not linked" in x for x in p), p)

    def test_link_to_missing_file(self):
        p = self.problems({"a.md": "- `WEB-001` one\n"}, SKILL_MD + "Also `references/c.md`.\n")
        self.assertTrue(any("c.md, which does not exist" in x for x in p), p)

    def test_skill_md_cites_missing_rule(self):
        p = self.problems({"a.md": "- `WEB-001` one\n"}, SKILL_MD + "Follow GIT-404.\n")
        self.assertTrue(any("GIT-404" in x for x in p), p)

    def test_show_follows_merge(self):
        make_skill(self.tmp, SKILL_MD, {"a.md": "- `WEB-001` one\n\n## Merged rules\n\nWEB-002 → WEB-001\n"})
        self.assertEqual(rules.main(["--skill-dir", self.tmp, "show", "web-002"]), 0)
        self.assertEqual(rules.main(["--skill-dir", self.tmp, "show", "WEB-777"]), 1)

    def test_export_lists_every_rule_with_its_why(self):
        doc = rules.export(SKILL)
        found, _, _ = rules.load(SKILL)
        self.assertEqual(len(re.findall(r"(?m)^\*\*[A-Z]{3}-\d{3}\*\* ", doc)), len(found))
        self.assertEqual(doc.count("*Why:* "), len(found))
        self.assertIn("**GIT-009**", doc)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, self.tmp)
        write(self.tmp, "README.md", "# p\n")

    def rules_found(self):
        return {f["rule"] for f in check.scan(self.tmp).findings}

    def test_every_check_names_a_real_rule(self):
        found, _, _ = rules.load(SKILL)
        self.assertEqual(sorted(set(check.CHECKS) - set(found)), [])

    def test_clean_page_has_no_findings(self):
        write(self.tmp, "index.html",
              '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
              '<title>T</title>\n<script src="a.js" defer></script>\n</head>\n'
              '<body><header><nav aria-label="Main"><ul><li><a href="/a.html">About us</a></li>'
              '</ul></nav></header><main><h1>T</h1><h2>S</h2><p>x</p>'
              '<img src="d.webp" alt="Diagram" width="1" height="1"></main></body></html>\n')
        write(self.tmp, "a.js", "const a = 1;\nif (a === 1) {}\n")
        write(self.tmp, "s.css", ".b:hover, .b:focus-visible { line-height: 1.5; font-size: 1rem; }\n")
        self.assertEqual(check.scan(self.tmp).findings, [])

    def test_html_breaches(self):
        write(self.tmp, "p.html",
              "<!doctype html><html><head><title>t</title><script src='a.js'></script></head><body>"
              "<h1>a</h1><h3>b</h3><h1>c</h1><img src=x.jpg><p>t<div>d</div></p>"
              "<iframe src=x></iframe><div id=i></div><div id=i></div></body></html>")
        got = self.rules_found()
        for rid in ("WEB-027", "WEB-182", "WEB-183", "WEB-175", "WEB-186", "WEB-189",
                    "WEB-018", "WEB-198", "WEB-053", "WEB-097", "WEB-054", "WEB-025"):
            self.assertIn(rid, got)

    def test_css_ignores_comments_and_respects_media_query(self):
        write(self.tmp, "s.css", "/* outline: none; !important */\n"
              "@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }\n")
        self.assertEqual(check.scan(self.tmp).findings, [])
        write(self.tmp, "s.css", "html { scroll-behavior: smooth; }\n.a:focus { outline: none; }\n")
        self.assertEqual(self.rules_found(), {"WEB-246", "WEB-215"})

    def test_js_ignores_strings_and_comments(self):
        write(self.tmp, "a.js", '// var a == b\nconst s = "var x = y == z";\nconst t = `a != b`;\n')
        self.assertEqual(check.scan(self.tmp).findings, [])
        write(self.tmp, "a.js", "var a = 1;\nif (a == 1) {}\n")
        found = check.scan(self.tmp).findings
        self.assertEqual([(f["rule"], f["line"]) for f in found], [("WEB-233", 1), ("WEB-230", 2)])

    def test_unterminated_quote_keeps_line_numbers(self):
        write(self.tmp, "a.jsx", "const A = () => <p>don't</p>;\nvar b = 1;\n")
        self.assertIn(("WEB-233", 2), [(f["rule"], f["line"]) for f in check.scan(self.tmp).findings])

    def test_react_and_package_breaches(self):
        write(self.tmp, "package.json", json.dumps(
            {"dependencies": {"react": "19", "vite": "7", "react-scripts": "5"}}))
        write(self.tmp, "src/App.jsx", "export default function A({items}) {\n"
              "  return items.map((x, index) => <b key={index} onClick={setX(1)}>{x}</b>);\n}\n")
        got = self.rules_found()
        for rid in ("WEB-024", "PKG-002", "RCT-005", "RCT-018", "RCT-021"):
            self.assertIn(rid, got)

    def test_bun_and_lockfile_breaches(self):
        write(self.tmp, "package.json", json.dumps({"dependencies": {"dotenv": "1"}}))
        write(self.tmp, "bun.lock", "")
        write(self.tmp, "package-lock.json", "{}")
        self.assertTrue({"BUN-012", "PKG-005"} <= self.rules_found())

    def test_skips_dependency_and_build_folders(self):
        write(self.tmp, "node_modules/x/a.js", "var a = 1;\n")
        write(self.tmp, "dist/a.js", "var a = 1;\n")
        write(self.tmp, "lib.min.js", "var a = 1;\n")
        self.assertEqual(check.scan(self.tmp).findings, [])

    def test_missing_readme(self):
        os.remove(os.path.join(self.tmp, "README.md"))
        self.assertEqual(self.rules_found(), {"GIT-016"})

    def test_tracked_secret_file(self):
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        write(self.tmp, ".env", "KEY=1\n")
        git = ["git", "-C", self.tmp, "-c", "user.email=a@b", "-c", "user.name=t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        self.assertIn("GIT-009", self.rules_found())

    def test_exit_codes(self):
        self.assertEqual(check.main([self.tmp]), 0)
        write(self.tmp, "s.css", ".a { color: red !important; }\n")
        self.assertEqual(check.main([self.tmp]), 0)          # review only
        self.assertEqual(check.main([self.tmp, "--strict"]), 1)
        write(self.tmp, "a.js", "var a;\n")
        self.assertEqual(check.main([self.tmp]), 1)          # an error


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, self.tmp)
        self.src = os.path.join(self.tmp, "ays")
        shutil.copytree(SKILL, self.src, ignore=shutil.ignore_patterns("__pycache__"))
        self.out = os.path.join(self.tmp, "ays.skill")

    def test_build_then_check_passes(self):
        build.build(self.src, self.out)
        self.assertEqual(build.check(self.src, self.out), [])

    def test_bundle_is_deterministic_and_lf(self):
        build.build(self.src, self.out)
        first = read_bytes(self.out)
        path = os.path.join(self.src, "SKILL.md")
        data = read_bytes(path).replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        with open(path, "wb") as f:
            f.write(data)  # same content, CRLF endings
        build.build(self.src, self.out)
        self.assertEqual(read_bytes(self.out), first)

    def test_no_bytecode_and_forward_slashes(self):
        os.makedirs(os.path.join(self.src, "scripts", "__pycache__"), exist_ok=True)
        with open(os.path.join(self.src, "scripts", "__pycache__", "x.pyc"), "wb") as f:
            f.write(b"\0")
        build.build(self.src, self.out)
        with zipfile.ZipFile(self.out) as z:
            names = z.namelist()
        self.assertFalse(any("pycache" in n or "\\" in n for n in names), names)
        self.assertIn("ays/SKILL.md", names)
        self.assertIn("ays/scripts/check.py", names)

    def test_stale_bundle_fails(self):
        build.build(self.src, self.out)
        with open(os.path.join(self.src, "references", "git.md"), "a", encoding="utf-8") as f:
            f.write("\n")
        self.assertTrue(any("stale" in p for p in build.check(self.src, self.out)))

    def test_frontmatter_contract(self):
        ok = "---\nname: ays\ndescription: d\nlicense: MIT\n---\n"
        self.assertEqual(build.frontmatter_problems(ok, "ays"), [])
        self.assertTrue(build.frontmatter_problems(ok.replace("license", "version"), "ays"))
        self.assertTrue(build.frontmatter_problems(ok.replace("name: ays", "name: AYS"), "ays"))
        self.assertTrue(build.frontmatter_problems(ok, "other"))
        long = ok.replace("description: d", "description: " + "x" * 1025)
        self.assertTrue(build.frontmatter_problems(long, "ays"))


if __name__ == "__main__":
    unittest.main()
