#!/usr/bin/env python3
"""Detect which security scanners are installed and run the ones that apply to
this repo, printing a normalized summary. Standard library only — installs
nothing. If a scanner isn't present it's skipped and noted (never guessed at).

Black-box helper: run with --help, then invoke. Don't read this source unless a
customized run is truly needed. It exists so the security agent runs
whatever the environment already has, consistently, without hand-rolling each
invocation or bloating context.

USAGE
    python run_scanners.py [--path DIR] [--json]

    --path DIR   Repo/subdir to scan (default: current directory).
    --json       Emit machine-readable JSON instead of the text summary.

WHAT IT RUNS (only if the tool is on PATH and the repo matches)
    Dependency audit : npm audit --json (if package.json),
                       pip-audit (if requirements*.txt/pyproject.toml),
                       cargo audit (if Cargo.toml),
                       osv-scanner (any, if installed)
    SAST             : semgrep --config auto,
                       bandit -r (Python)
    Secret scan      : gitleaks detect, trufflehog filesystem

Findings are for TRIAGE. Per the fleet's "never assume" rule, the agent must
still confirm each reported issue against the real code before reporting it as
fact — scanners produce false positives.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Windows consoles default to cp1252 and would mangle the em dashes and arrows
    # this prints. Matches the guard the other helpers already carry.
except Exception:
    pass


def has(tool):
    return shutil.which(tool) is not None


def exists(path, *names):
    return any(os.path.exists(os.path.join(path, n)) for n in names)


def run(cmd, cwd):
    """Run a command, capturing output; never raise on non-zero exit."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                              text=True, timeout=600)
        return {"cmd": cmd, "exit": proc.returncode,
                "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "exit": None, "stdout": "", "stderr": "timeout"}


def plan(path):
    """Decide which scanners to run given what's installed and present."""
    jobs = []  # (category, tool, command)
    # Dependency audits
    if exists(path, "package.json") and has("npm"):
        jobs.append(("deps", "npm-audit", "npm audit --json"))
    if exists(path, "requirements.txt", "pyproject.toml") and has("pip-audit"):
        jobs.append(("deps", "pip-audit", "pip-audit"))
    if exists(path, "Cargo.toml") and has("cargo") and has("cargo-audit"):
        jobs.append(("deps", "cargo-audit", "cargo audit"))
    if has("osv-scanner"):
        jobs.append(("deps", "osv-scanner", "osv-scanner -r ."))
    # SAST
    if has("semgrep"):
        jobs.append(("sast", "semgrep", "semgrep --config auto --error --quiet"))
    if has("bandit") and exists(path, "pyproject.toml", "setup.py", "requirements.txt"):
        jobs.append(("sast", "bandit", "bandit -r . -q"))
    # Secret scanning
    if has("gitleaks"):
        jobs.append(("secrets", "gitleaks", "gitleaks detect --no-banner"))
    if has("trufflehog"):
        jobs.append(("secrets", "trufflehog", "trufflehog filesystem . --no-update"))
    return jobs


def main(argv):
    p = argparse.ArgumentParser(add_help=True, description=__doc__)
    p.add_argument("--path", default=".")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    path = os.path.abspath(args.path)

    jobs = plan(path)
    results = [dict(category=c, tool=t, **run(cmd, path)) for c, t, cmd in jobs]

    if args.json:
        print(json.dumps({"path": path, "ran": results}, indent=2))
        return 0

    if not jobs:
        print("No security scanners found on PATH. Install e.g. semgrep, "
              "pip-audit, gitleaks — or the agent should fall back to manual "
              "review and say so (do not fabricate scanner results).")
        return 0

    print(f"# Security scan summary — {path}\n")
    for r in results:
        status = "ok" if r["exit"] == 0 else f"flagged/exit={r['exit']}"
        print(f"## [{r['category']}] {r['tool']} — {status}")
        out = (r["stdout"] or r["stderr"]).strip()
        print(out[:2000] if out else "(no output)")
        print()
    print("NOTE: triage only — confirm each finding against the real code "
          "before reporting it (scanners have false positives).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
