#!/usr/bin/env python3
"""Enforce the PII policy on anything about to be persisted (memory delta, merged
report, generated docs). Standard library only — installs nothing, no network.

Policy lives in `data/pii-policy.csv`, typed, with one of four actions:
  BLOCK  - must never be persisted (live credentials, national IDs, card numbers)
  REDACT - replace the value; the finding survives, the personal data does not
  HASH   - replace with a stable short hash so it stays correlatable across runs
           without publishing internal topology
  PASS   - explicitly allowed (public contacts, repo paths, public URLs)

Honest limits, stated up front: only the pattern-detectable types are caught
automatically. Types marked `judgment` in the policy (a home address in free
prose, a customer's name, health data) CANNOT be reliably regex-matched — this
tool lists them so the agent checks them deliberately. It reduces the blast
radius of a mistake; it is not a substitute for the agent applying the policy.

Black-box helper: run with --help, then invoke.

USAGE
    python redact.py --in delta.md --out delta.clean.md
    cat report.md | python redact.py > report.clean.md
    python redact.py --in memory-delta.md --strict     # exit 1 if a BLOCK type is present
    python redact.py --explain                         # print the policy table
"""
from __future__ import annotations
import argparse, csv, hashlib, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

POLICY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "pii-policy.csv")

# Pattern-detectable types only; anything requiring judgment is deliberately absent.
# ORDER MATTERS: most specific first. The phone pattern is the loosest, so it runs
# last - otherwise it swallows private IPs and long digit runs before their own
# (more accurate) rule ever sees them.
PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("secret-api-key", re.compile(
        r"\b(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_\-]{20,}|"
        r"gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|re_[A-Za-z0-9]{16,})\b")),
    ("credential-in-url", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@]+:[^\s/@]+@[^\s]+")),
    ("session-token", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    ("national-id", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("internal-host-ip", re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")),
    ("email-personal", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("payment-card", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("phone-number", re.compile(r"(?<![\w.])\+?\d[\d\s().-]{7,17}\d(?![\w.])")),
]

_DOTTED_QUAD = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")


def luhn_ok(digits):
    ds = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(ds) <= 19:
        return False
    total, parity = 0, len(ds) % 2
    for i, d in enumerate(ds):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def load_policy():
    with open(POLICY, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def short_hash(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:10]


def apply_policy(text, policy):
    findings, out = [], text
    for pid, rx in PATTERNS:
        rule = policy.get(pid)
        if not rule or rule["action"] == "PASS":
            continue
        action, repl = rule["action"], rule["replacement"]

        def sub(m, pid=pid, action=action, repl=repl):
            val = m.group(0)
            # A PAN only counts if it actually checksums - otherwise it is just digits.
            if pid == "payment-card" and not luhn_ok(val):
                return val
            # Never let the loose phone pattern claim a dotted quad or a bare
            # digit run; a real phone carries a '+' or separators.
            if pid == "phone-number":
                if _DOTTED_QUAD.fullmatch(val.strip()):
                    return val
                if not val.lstrip().startswith("+") and not re.search(r"[ ()\-]", val):
                    return val
            findings.append((pid, action, val[:6] + "..." if len(val) > 8 else val))
            if action == "HASH":
                return repl.replace("<hash>", short_hash(val))
            return repl

        out = rx.sub(sub, out)
    return out, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Apply the PII policy before persisting text.")
    ap.add_argument("--in", dest="inp", help="input file (default: stdin)")
    ap.add_argument("--out", dest="out", help="output file (default: stdout)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any BLOCK-class value was found")
    ap.add_argument("--explain", action="store_true", help="print the policy table and exit")
    a = ap.parse_args(argv)

    policy = load_policy()
    if a.explain:
        print(f"{'TYPE':<28} {'ACTION':<7} {'DETECT':<9} REPLACEMENT")
        for r in policy.values():
            print(f"{r['type']:<28} {r['action']:<7} {r['detect']:<9} {r['replacement']}")
        judgment = [r["type"] for r in policy.values() if r["detect"] == "judgment" and r["action"] != "PASS"]
        print("\nJudgment-only (NOT auto-detected — the agent must check these):")
        for t in judgment:
            print("  - " + t)
        return 0

    text = open(a.inp, encoding="utf-8", errors="replace").read() if a.inp else sys.stdin.read()
    cleaned, findings = apply_policy(text, policy)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(cleaned)
    else:
        sys.stdout.write(cleaned)

    blocked = [f for f in findings if f[1] == "BLOCK"]
    if findings:
        print(f"\n[redact] {len(findings)} value(s) handled:", file=sys.stderr)
        for pid, action, sample in findings:
            print(f"  {action:<7} {pid:<20} {sample}", file=sys.stderr)
    judgment = [r["type"] for r in policy.values() if r["detect"] == "judgment" and r["action"] != "PASS"]
    print("[redact] NOT auto-detectable — verify by hand before persisting: "
          + ", ".join(judgment), file=sys.stderr)

    if a.strict and blocked:
        print(f"[redact] STRICT: {len(blocked)} BLOCK-class value(s) present; refusing.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
