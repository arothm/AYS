#!/usr/bin/env python3
"""Test suite for the bundled helper scripts. Standard library only (unittest) —
installs nothing, needs no network.

    python -m unittest discover -s tests -v
    python tests/test_scripts.py

These tests exist because the skill's own Tester agent would fail this project
otherwise: the helpers make load-bearing claims ("contrast is measured", "the audit
is read-only", "--strict refuses a secret") and an untested claim is exactly what
shared-rules rule 1 forbids. Each test below pins one of those claims.
"""
from __future__ import annotations
import io
import json
import re
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout, redirect_stderr

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "skills", "ayc-skill")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import design_system  # noqa: E402
import md_to_docx  # noqa: E402
import recall  # noqa: E402
import redact  # noqa: E402
import run_scanners  # noqa: E402
import server_audit  # noqa: E402
import standards  # noqa: E402
import to_sarif  # noqa: E402
import with_server  # noqa: E402


def run(main, argv):
    """Invoke a script's main() capturing stdout/stderr and the exit code."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as e:  # argparse
            code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue(), err.getvalue()


# --------------------------------------------------------------- design_system
class TestContrast(unittest.TestCase):
    def test_known_wcag_ratios(self):
        # Black on white is the defined maximum, 21:1.
        self.assertAlmostEqual(design_system.contrast("#000000", "#ffffff"), 21.0, places=1)
        # A colour against itself has no contrast.
        self.assertAlmostEqual(design_system.contrast("#4a90d9", "#4a90d9"), 1.0, places=2)

    def test_contrast_is_symmetric(self):
        a = design_system.contrast("#1a1a1a", "#f5f5f5")
        b = design_system.contrast("#f5f5f5", "#1a1a1a")
        self.assertEqual(a, b)

    def test_shorthand_hex_expands(self):
        self.assertEqual(design_system.contrast("#000", "#fff"),
                         design_system.contrast("#000000", "#ffffff"))

    def test_verdict_thresholds(self):
        self.assertEqual(design_system.verdict(21.0), "AAA")
        self.assertEqual(design_system.verdict(4.5), "AA")
        self.assertEqual(design_system.verdict(4.49), "FAIL")
        # 3.0 fails for normal text but passes for large text.
        self.assertEqual(design_system.verdict(3.0), "FAIL")
        self.assertEqual(design_system.verdict(3.0, large=True), "AA")

    def test_dataset_validates(self):
        code, out, _ = run(design_system.main, ["--validate"])
        self.assertEqual(code, 0, out)
        self.assertIn("All checks passed", out)

    def test_compose_reports_no_match_honestly(self):
        code, out, _ = run(design_system.main, ["zzzz nonsense brief qqqq", "--format", "json"])
        self.assertEqual(code, 0)
        spec = json.loads(out)
        self.assertIn("no keyword match", spec["match_confidence"])

    def test_persist_writes_master(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(design_system.main,
                               ["premium minimal SaaS landing page", "--persist", "-o", d])
            self.assertEqual(code, 0, out)
            master = os.path.join(d, "design-system", "MASTER.md")
            self.assertTrue(os.path.isfile(master))
            with open(master, encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("MASTER Design System", body)
            # The contrast table must carry measured ratios, not assertions.
            self.assertIn(":1", body)


# ---------------------------------------------------------------------- redact
class TestRedact(unittest.TestCase):
    def setUp(self):
        self.policy = redact.load_policy()

    def test_blocks_private_key(self):
        text = "key:\n-----BEGIN RSA PRIVATE KEY-----\nMIIEow==\n"
        clean, findings = redact.apply_policy(text, self.policy)
        self.assertIn("[PRIVATE-KEY-BLOCKED]", clean)
        self.assertTrue(any(f[1] == "BLOCK" for f in findings))

    def test_blocks_aws_key(self):
        clean, findings = redact.apply_policy("id AKIAIOSFODNN7EXAMPLE here", self.policy)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", clean)
        self.assertTrue(any(f[0] == "secret-api-key" for f in findings))

    def test_strict_exits_nonzero_on_block(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "delta.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("token: sk-abcdefghijklmnopqrstuvwxyz012345\n")
            code, _, err = run(redact.main, ["--in", src, "--out", os.path.join(d, "o.md"),
                                             "--strict"])
        self.assertEqual(code, 1)
        self.assertIn("STRICT", err)

    def test_strict_passes_clean_text(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "clean.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("- [blocking] src/app.ts:42 - unchecked parse. Fix: guard NaN.\n")
            code, _, _ = run(redact.main, ["--in", src, "--out", os.path.join(d, "o.md"),
                                           "--strict"])
        self.assertEqual(code, 0)

    def test_file_line_paths_survive(self):
        """PASS-classed data must not be redacted, or findings stop being reproducible."""
        text = "- [warning] src/components/Cart.tsx:88 - no error state."
        clean, _ = redact.apply_policy(text, self.policy)
        self.assertIn("src/components/Cart.tsx:88", clean)

    def test_internal_ip_is_hashed_not_removed(self):
        clean, findings = redact.apply_policy("host 10.0.14.22 refused", self.policy)
        self.assertNotIn("10.0.14.22", clean)
        self.assertIn("[HOST-", clean)
        self.assertTrue(any(f[1] == "HASH" for f in findings))

    def test_hash_is_stable_across_calls(self):
        a, _ = redact.apply_policy("10.0.14.22", self.policy)
        b, _ = redact.apply_policy("10.0.14.22", self.policy)
        self.assertEqual(a, b)

    def test_luhn_gate_on_card_numbers(self):
        self.assertTrue(redact.luhn_ok("4111111111111111"))
        self.assertFalse(redact.luhn_ok("4111111111111112"))

    def test_non_luhn_digit_run_is_left_alone(self):
        """A long digit run that isn't a valid PAN must not be mangled."""
        text = "build 1234567890123456789"
        clean, _ = redact.apply_policy(text, self.policy)
        self.assertIn("1234567890123456789", clean)

    def test_dotted_quad_not_claimed_by_phone_pattern(self):
        clean, _ = redact.apply_policy("public 8.8.8.8 resolver", self.policy)
        self.assertIn("8.8.8.8", clean)

    def test_judgment_categories_are_always_announced(self):
        """The tool must state its own blind spots on every run."""
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "x.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("nothing sensitive\n")
            _, _, err = run(redact.main, ["--in", src, "--out", os.path.join(d, "o.md")])
        self.assertIn("NOT auto-detectable", err)


# ------------------------------------------------------------------- standards
class TestStandards(unittest.TestCase):
    def test_dataset_validates(self):
        code, out, _ = run(standards.main, ["--validate"])
        self.assertEqual(code, 0, out)
        self.assertIn("All checks passed", out)

    def test_every_standard_has_an_owner_and_verify(self):
        for row in standards.load("standards"):
            self.assertIn(row["owner"], set(standards.AGENTS) | {"all"}, row["id"])
            self.assertTrue(row["verify"].strip(), "%s has no verify method" % row["id"])
            self.assertIn(row["severity"], standards.SEVERITIES, row["id"])

    def test_standard_ids_are_unique(self):
        ids = [r["id"] for r in standards.load("standards")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_agent_filter_returns_only_that_agent(self):
        code, out, _ = run(standards.main, ["--agent", "devops"])
        self.assertEqual(code, 0)
        self.assertIn("devops", out)
        # frontend-owned rules must not leak into a devops brief
        self.assertNotIn("skeleton-loaders", out)

    def test_compact_is_one_line_per_rule_and_much_smaller(self):
        code, full, _ = run(standards.main, ["--agent", "backend"])
        code2, small, _ = run(standards.main, ["--agent", "backend", "--compact"])
        self.assertEqual((code, code2), (0, 0))
        rules = [r for r in standards.load("standards")
                 if r["owner"] in ("backend", "all")]
        body = [l for l in small.splitlines() if l.strip() and not l.startswith(("B=", str(len(rules))))]
        # every rule present, one line each, and the verbose columns dropped
        for r in rules:
            self.assertIn(r["id"], small, r["id"])
        self.assertNotIn("VERIFY", small)
        self.assertLess(len(small.split()), len(full.split()) / 2)

    def test_why_returns_one_rule_in_full_and_rejects_unknown_ids(self):
        code, out, _ = run(standards.main, ["--why", "rate-limiting"])
        self.assertEqual(code, 0)
        self.assertIn("VERIFY", out)
        self.assertNotIn("no-n-plus-1", out)  # exactly one rule, not the agent's set
        code, out, _ = run(standards.main, ["--why", "not-a-real-rule"])
        self.assertEqual(code, 1)  # non-zero so a typo in a dispatch is caught

    def test_routing_names_a_plausible_owner(self):
        code, out, _ = run(standards.main, ["--who", "TLS certificates and HTTP/3 at the edge"])
        self.assertEqual(code, 0)
        self.assertIn("devops", out)

    def test_component_libraries_all_record_a_licence(self):
        for lib in standards.load("component-libraries"):
            self.assertTrue(lib["licence"].strip(), "%s has no licence" % lib["id"])


# ---------------------------------------------------------------------- recall
class TestRecall(unittest.TestCase):
    def _workspace(self, d):
        os.makedirs(os.path.join(d, "docs"), exist_ok=True)
        with open(os.path.join(d, "memory.md"), "w", encoding="utf-8") as f:
            f.write("# Memory\n\n## Project overview\nA cart service.\n\n"
                    "## Stack & commands\ntest: pytest\n\n"
                    "## Deploy rollback\nBlue-green with a previous image tag.\n\n"
                    "## Unrelated trivia\nThe office cat is called Pixel.\n")
        return d

    def test_pinned_sections_always_returned(self):
        with tempfile.TemporaryDirectory() as d:
            self._workspace(d)
            chosen, _omitted, _total = recall.recall(d, "something totally unrelated", top=1)
            heads = [h.lower() for h, _b, _s in chosen]
            self.assertTrue(any("project overview" in h for h in heads))
            self.assertTrue(any("stack" in h for h in heads))

    def test_query_surfaces_the_matching_section(self):
        with tempfile.TemporaryDirectory() as d:
            self._workspace(d)
            chosen, _o, _t = recall.recall(d, "rollback", top=3)
            heads = [h.lower() for h, _b, _s in chosen]
            self.assertTrue(any("rollback" in h for h in heads))

    def test_nothing_is_silently_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            self._workspace(d)
            chosen, omitted, _t = recall.recall(d, "rollback", top=1)
            rendered = recall.render(chosen, omitted, 100, "rollback", None)
            if omitted:
                self.assertIn("Not included", rendered)
                for h, _b, _s in omitted:
                    self.assertIn(h, rendered)

    def test_missing_workspace_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, _ = run(recall.main, ["anything", "--root", os.path.join(d, "nope")])
        self.assertEqual(code, 0)

    def test_reads_docx_sections(self):
        with tempfile.TemporaryDirectory() as d:
            self._workspace(d)
            src = os.path.join(d, "TDD.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# Technical Design\n\n## Sharding strategy\nHash on tenant id.\n")
            out = os.path.join(d, "docs", "TDD.docx")
            md_to_docx.convert(src, out, use_pandoc=False)
            chosen, _o, _t = recall.recall(d, "sharding tenant", top=4)
            blob = " ".join(b for _h, b, _s in chosen)
            self.assertIn("Hash on tenant id", blob)


# ------------------------------------------------------------------ md_to_docx
class TestMdToDocx(unittest.TestCase):
    def test_produces_a_valid_docx(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# Title\n\nA paragraph with **bold** and `code`.\n\n"
                        "- one\n- two\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
            out = os.path.join(d, "doc.docx")
            md_to_docx.convert(src, out, use_pandoc=False)
            self.assertTrue(os.path.isfile(out))
            with zipfile.ZipFile(out) as z:
                names = z.namelist()
                self.assertIn("word/document.xml", names)
                self.assertIn("[Content_Types].xml", names)
                self.assertEqual(z.testzip(), None)
                body = z.read("word/document.xml").decode("utf-8")
            self.assertIn("Title", body)
            self.assertIn("bold", body)

    def test_escapes_xml_metacharacters(self):
        """A doc containing < & > must not produce corrupt OOXML."""
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# A & B\n\nUse <script> & \"quotes\" carefully.\n")
            out = os.path.join(d, "doc.docx")
            md_to_docx.convert(src, out, use_pandoc=False)
            with zipfile.ZipFile(out) as z:
                body = z.read("word/document.xml").decode("utf-8")
            self.assertNotIn("<script>", body)
            self.assertIn("&lt;script&gt;", body)


# ----------------------------------------------------------------- server_audit
class TestServerAudit(unittest.TestCase):
    # Precise tokens only. A crude substring list produces false alarms - `getent
    # passwd` is a read, and flagging it would train someone to loosen this test,
    # which is the one test that guarantees the script cannot break a server.
    MUTATING = ("systemctl restart", "systemctl stop", "systemctl start",
                "systemctl enable", "systemctl disable", "systemctl reload",
                "apt-get install", "apt install", "apt-get upgrade", "apt upgrade",
                "dnf install", "dnf upgrade", "yum install", "pip install",
                "rm -", "mv ", "chmod ", "chown ", "mkdir ", "touch ",
                "ufw allow", "ufw deny", "ufw enable", "ufw disable", "ufw delete",
                "iptables -a", "iptables -d", "iptables -i", "iptables -f", "nft add",
                "nft delete", "nft flush",
                "docker run", "docker rm", "docker stop", "docker start",
                "docker restart", "docker exec", "docker pull", "docker prune",
                "docker system prune",
                "reboot", "shutdown", "halt", "truncate ", "| tee", "sed -i",
                "useradd", "usermod", "userdel", "groupadd", "passwd ",
                "ssh-keygen -f", "certbot renew", "kill ", "pkill ")

    @staticmethod
    def segments(cmd):
        """Split a shell line into the commands it actually invokes.

        Matching mutating verbs anywhere in the string gives false alarms - `getent
        passwd` is a read whose text contains `passwd`. What matters is whether a
        verb appears in *command position*, so split on the separators that start a
        new command and test each segment's first word.
        """
        parts = re.split(r"\|\||&&|[;|\n]|\$\(|`|\bthen\b|\bdo\b", cmd.lower())
        return [p.strip().lstrip("{( ") for p in parts if p.strip()]

    def test_every_emitted_command_is_read_only(self):
        """The script's core safety claim: it cannot break a server."""
        for category, checks in server_audit.AUDIT.items():
            for title, cmd in checks:
                for seg in self.segments(cmd):
                    for bad in self.MUTATING:
                        self.assertFalse(
                            seg.startswith(bad),
                            "%s/%s invokes a mutating command %r in: %s"
                            % (category, title, bad, cmd))

    def test_no_output_redirection_into_files(self):
        for category, checks in server_audit.AUDIT.items():
            for title, cmd in checks:
                self.assertNotIn(" > ", cmd, "%s/%s redirects to a file" % (category, title))
                self.assertNotIn(" >> ", cmd, "%s/%s appends to a file" % (category, title))

    def test_script_generation_covers_all_categories(self):
        script = server_audit.build_script(list(server_audit.AUDIT))
        self.assertTrue(script.startswith("#!/usr/bin/env bash"))
        for category in server_audit.AUDIT:
            self.assertIn(category, script)

    def test_parse_flags_password_auth(self):
        captured = ("%s identity :: sshd\npermitrootlogin yes\npasswordauthentication yes\n"
                    "%s done\n" % (server_audit.MARK, server_audit.MARK))
        _blocks, findings, _empty = server_audit.parse(captured)
        meanings = " ".join(f[2] for f in findings)
        self.assertIn("root login", meanings)
        self.assertIn("password authentication", meanings)
        self.assertTrue(all(f[0] in ("blocking", "warning", "nit", "info") for f in findings))

    def test_empty_section_is_reported_as_unknown_not_clean(self):
        captured = "%s network :: firewall\n\n%s done\n" % (server_audit.MARK, server_audit.MARK)
        _blocks, _findings, empty = server_audit.parse(captured)
        self.assertIn("network :: firewall", empty)

    def test_script_never_connects(self):
        """server_audit must not import any network module."""
        with open(os.path.join(SKILL, "scripts", "server_audit.py"), encoding="utf-8") as fh:
            src = fh.read()
        for mod in ("import socket", "import subprocess", "urllib", "paramiko", "requests"):
            self.assertNotIn(mod, src)


# --------------------------------------------------------------- run_scanners
class TestRunScanners(unittest.TestCase):
    def test_plan_is_empty_without_manifests(self):
        with tempfile.TemporaryDirectory() as d:
            jobs = run_scanners.plan(d)
            # Only globally-installed scanners (semgrep/gitleaks/trufflehog/osv) may appear;
            # none of the manifest-gated ones should.
            names = {t for _c, t, _cmd in jobs}
            self.assertNotIn("npm-audit", names)
            self.assertNotIn("pip-audit", names)
            self.assertNotIn("cargo-audit", names)

    def test_npm_audit_gated_on_package_json(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "package.json"), "w").write("{}")
            names = {t for _c, t, _cmd in run_scanners.plan(d)}
            if run_scanners.has("npm"):
                self.assertIn("npm-audit", names)


# -------------------------------------------------------------------- to_sarif
REPORT = """# AYC Skill - Review Report

**Verdict:** NEEDS WORK

## Blocking
- [blocking] src/cart/total.ts:42 - unchecked NaN from user input. Fix: guard with Number.isNaN.

## Warnings
- [warning] api/order.py:88 - broad except swallows the error. Fix: catch ValueError only.
- [warning] path/or/area - a template placeholder that is not a real path.

## Nits
- [nit] web/Button.tsx:12 - inconsistent naming. Fix: rename to isDisabled.
"""


class TestToSarif(unittest.TestCase):
    def test_parses_findings_and_skips_prose(self):
        findings = to_sarif.parse(REPORT)
        self.assertEqual(len(findings), 3)
        paths = [f["path"] for f in findings]
        self.assertIn("src/cart/total.ts", paths)
        self.assertNotIn("path/or/area", paths)

    def test_line_numbers_and_severity(self):
        f = to_sarif.parse(REPORT)[0]
        self.assertEqual(f["line"], 42)
        self.assertEqual(f["severity"], "blocking")
        self.assertIn("Number.isNaN", f["fix"])

    def test_sarif_shape_is_valid(self):
        doc = to_sarif.to_sarif(to_sarif.parse(REPORT))
        self.assertEqual(doc["version"], "2.1.0")
        run_ = doc["runs"][0]
        self.assertEqual(run_["tool"]["driver"]["name"], "ayc-skill")
        self.assertEqual(len(run_["results"]), 3)
        levels = sorted(r["level"] for r in run_["results"])
        self.assertEqual(levels, ["error", "note", "warning"])
        loc = run_["results"][0]["locations"][0]["physicalLocation"]
        self.assertEqual(loc["artifactLocation"]["uri"], "src/cart/total.ts")
        self.assertEqual(loc["region"]["startLine"], 42)

    def test_every_result_references_a_declared_rule(self):
        doc = to_sarif.to_sarif(to_sarif.parse(REPORT))
        run_ = doc["runs"][0]
        declared = {r["id"] for r in run_["tool"]["driver"]["rules"]}
        for res in run_["results"]:
            self.assertIn(res["ruleId"], declared)

    def test_fail_on_blocking_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "report.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write(REPORT)
            code, _, _ = run(to_sarif.main,
                             ["--in", src, "--out", os.path.join(d, "o.sarif"),
                              "--fail-on", "blocking"])
        self.assertEqual(code, 1)

    def test_clean_report_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "report.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# Report\n\n**Verdict:** PASS\n\nNo findings.\n")
            out = os.path.join(d, "o.sarif")
            code, _, _ = run(to_sarif.main, ["--in", src, "--out", out, "--fail-on", "blocking"])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as fh:
                doc = json.load(fh)
            self.assertEqual(doc["runs"][0]["results"], [])

    def test_em_dash_separator_is_accepted(self):
        findings = to_sarif.parse("- [blocking] a/b.ts:9 — boom. Fix: don't.")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 9)

    def test_line_number_survives_every_separator(self):
        """Regression: the colon before a line number must never be mistaken for the
        problem separator, which silently reported every finding at line 1."""
        for sep in ("—", "–", "-", "--"):
            with self.subTest(sep=sep):
                findings = to_sarif.parse("- [blocking] src/a.ts:42 %s boom. Fix: guard." % sep)
                self.assertEqual(len(findings), 1, sep)
                self.assertEqual(findings[0]["path"], "src/a.ts")
                self.assertEqual(findings[0]["line"], 42, "line lost with %r" % sep)

    def test_colon_separator_without_line_number(self):
        findings = to_sarif.parse("- [warning] src/a.ts: no error state. Fix: add one.")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["path"], "src/a.ts")
        self.assertEqual(findings[0]["line"], 1)

    def test_mojibake_separator_does_not_fake_line_one(self):
        """If the dash is unreadable the finding may be dropped, but it must never be
        emitted pointing at the wrong line."""
        for f in to_sarif.parse("- [blocking] src/a.ts:42 �� boom. Fix: guard."):
            self.assertNotEqual((f["path"], f["line"]), ("src/a.ts", 1))


# ------------------------------------------------------------------ with_server
class TestWithServer(unittest.TestCase):
    """Regression: teardown killed the shell, not the server.

    `shell=True` puts a shell between the runner and the server, so the handle it
    held was the shell's. terminate() ended that and left the server listening,
    while the runner printed "servers stopped" - a false claim AND a bound port
    that made the next run's server fail to start.
    """

    def test_spawn_isolates_the_process_tree(self):
        import inspect
        src = inspect.getsource(with_server.spawn)
        if with_server.IS_WINDOWS:
            self.assertIn("CREATE_NEW_PROCESS_GROUP", src)
        else:
            self.assertIn("start_new_session", src)

    def test_stop_kills_the_whole_tree_not_just_the_shell(self):
        import inspect
        src = inspect.getsource(with_server.stop)
        self.assertTrue("taskkill" in src and "/T" in src,
                        "Windows teardown must walk the process tree")
        self.assertIn("killpg", src, "POSIX teardown must signal the process group")

    def test_teardown_is_verified_not_asserted(self):
        """The runner must probe the port after teardown, not just claim success."""
        import inspect
        src = inspect.getsource(with_server.main)
        self.assertIn("port_is_open", src)
        self.assertIn("still listening after teardown", src)

    def test_port_is_open_reports_a_closed_port_as_closed(self):
        # A port nothing is bound to must read as closed, or the leak check is noise.
        self.assertFalse(with_server.port_is_open("127.0.0.1", 9))

    def test_mismatched_server_and_port_counts_are_rejected(self):
        code, out, err = run(with_server.main,
                             ["--server", "sleep 1", "--", "true"])
        self.assertEqual(code, 2)
        self.assertIn("matching --port", err)


# ------------------------------------------------------------------ font imports
class TestFontImports(unittest.TestCase):
    """Regression: a pairing needing two provider requests only made one.

    Fontshare answers a multi-family `f[]=a&f[]=b` query with the FIRST family
    only, with a 200 and no error - so the body font silently fell back to
    system sans on every page the generator specced.
    """

    def test_every_declared_family_appears_in_some_import_url(self):
        fonts = design_system.load("font-pairings")
        for f in fonts:
            if f["provider"] == "system":
                continue
            urls = " ".join(design_system.import_urls(f)).lower()
            for fam in (f["heading"], f["body"], f.get("mono") or ""):
                if not fam:
                    continue
                self.assertIn(design_system.normalise(fam), design_system.normalise(urls),
                              "%s: '%s' is never loaded by any import URL" % (f["id"], fam))

    def test_fontshare_requests_one_family_per_url(self):
        """Fontshare drops every family after the first, so never batch them."""
        for f in design_system.load("font-pairings"):
            if f["provider"] != "fontshare":
                continue
            for url in design_system.import_urls(f):
                self.assertEqual(url.count("f[]="), 1,
                                 "%s batches families into one fontshare request; "
                                 "only the first would load" % f["id"])

    def test_emitted_css_imports_every_url(self):
        spec = design_system.compose(
            "bold creative agency launch",
            design_system.load("product-rules"), design_system.load("styles"),
            design_system.load("palettes"), design_system.load("font-pairings"),
            overrides={"font": "clash-switzer"},
            motions=design_system.load("motion-libraries"))
        md = design_system.render_markdown(spec)
        for url in design_system.import_urls(spec["font"]):
            self.assertIn(url, md, "emitted CSS omits an import the pairing needs")


# ------------------------------------------------------------------ data files
class TestDataIntegrity(unittest.TestCase):
    def test_pii_policy_actions_are_known(self):
        policy = redact.load_policy()
        for pid, row in policy.items():
            self.assertIn(row["action"], {"BLOCK", "REDACT", "HASH", "PASS"}, pid)
            self.assertIn(row["detect"], {"pattern", "judgment"}, pid)

    def test_every_pattern_has_a_policy_row(self):
        policy = redact.load_policy()
        for pid, _rx in redact.PATTERNS:
            self.assertIn(pid, policy, "pattern %s has no policy row" % pid)

    def test_file_paths_are_pass_classed(self):
        policy = redact.load_policy()
        self.assertEqual(policy["file-path-in-repo"]["action"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
