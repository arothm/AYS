#!/usr/bin/env python3
"""Query the fleet's non-negotiable standards, and route a need to the agent that
owns it. Standard library only — installs nothing, no network.

Two jobs:

1. **Standards.** `data/standards.csv` holds the rules every run must respect,
   each owned by exactly one agent, with a severity and — crucially — a `verify`
   column saying how to *prove* compliance rather than assert it. An agent pulls
   only its own standards at dispatch, so briefs stay small — `--compact` trims
   that to one line per rule, with `--why <id>` for the rationale of the ones it
   actually reports against.

2. **Routing.** `--who "<need>"` answers "which agent covers this?" by matching
   the need against agent ownership and the standards they own. Useful when the
   coordinator is selecting agents and when a user asks who handles X.

USAGE
    python standards.py --agent frontend            # that agent's standards
    python standards.py --agent frontend --compact  # one line per rule (dispatch form)
    python standards.py --why rate-limiting         # why + how to verify one rule
    python standards.py --agent devops --checklist  # as a report checklist
    python standards.py --context commercial,ai     # standards gated on context
    python standards.py --severity blocking
    python standards.py --who "who handles rate limiting and auth?"
    python standards.py --validate                  # dataset integrity gate
"""
from __future__ import annotations
import argparse, csv, math, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
AGENTS = {
    "frontend": "UI architecture, performance budgets, accessibility, design tokens, dead FE code",
    "backend": "distributed correctness, data architecture, query plans, API governance, migrations",
    "security": "logic flaws, crypto, secrets, supply chain, authz, PII and privacy compliance",
    "tester": "all testing, suite strategy, flakiness, contract/perf/chaos, coverage, test authoring",
    "devops": "delivery pipeline, infrastructure, TLS/edge, observability, deploys and rollback, dependency upgrades",
    "ai-engineer": "prompts, agent/RAG architecture, evals, model choice, token cost and guardrails",
}
SEVERITIES = {"blocking", "warning", "nit"}
_WORD = re.compile(r"[a-z0-9+]+")


def toks(t):
    return _WORD.findall((t or "").lower())


def load(name):
    with open(os.path.join(DATA, f"{name}.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bm25(query, docs, k1=1.5, b=0.75):
    corpus = {k: toks(t) for k, t in docs}
    n = len(corpus) or 1
    avg = sum(len(v) for v in corpus.values()) / n or 1
    df = {}
    for w in corpus.values():
        for t in set(w):
            df[t] = df.get(t, 0) + 1
    out = {}
    for key, words in corpus.items():
        s, dl = 0.0, len(words) or 1
        for term in toks(query):
            tf = words.count(term)
            if not tf or term not in df:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg))
        out[key] = s
    return out


def applicable(row, contexts):
    a = (row["applies_to"] or "any").strip()
    return a == "any" or not contexts or a in contexts


def show(rows, checklist=False, compact=False):
    if not rows:
        print("(no standards match)")
        return
    if compact:
        # One line per rule: enough to check against, ~a third of the tokens of
        # the full form. The WHY and VERIFY columns are a `--why <id>` away, so
        # an agent pays for them only on the rules it actually reports against.
        width = max(len(r["id"]) for r in rows)
        for r in rows:
            print(f"{r['severity'][0].upper()} {r['id']:<{width}}  {r['rule']}")
        print(f"\n{len(rows)} rules (B=blocking W=warning N=nit). "
              f"Why/how-to-verify for one: --why <id>")
        return
    if checklist:
        for r in rows:
            print(f"- [ ] **{r['severity'].upper()}** ({r['owner']}) {r['rule']}")
            print(f"      _verify:_ {r['verify']}")
        return
    for r in rows:
        print(f"\n[{r['severity'].upper():<8}] {r['id']}  ({r['category']} · owner: {r['owner']} · applies: {r['applies_to']})")
        print(f"  RULE   {r['rule']}")
        print(f"  WHY    {r['why']}")
        print(f"  VERIFY {r['verify'].strip()}")


def route(need, standards):
    """Which agent owns this need? Score agents by their remit + the standards they own."""
    owned = {}
    for a, remit in AGENTS.items():
        mine = [s for s in standards if s["owner"] in (a, "all")]
        blob = remit + " " + " ".join(f"{s['id']} {s['category']} {s['rule']}" for s in mine)
        owned[a] = blob
    scores = bm25(need, list(owned.items()))
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top = ranked[0][1] if ranked else 0.0
    # Only surface agents that are genuinely in contention. Everything owns the
    # shared 'code-comments' rule, so an unfiltered list names every agent and is
    # useless as routing.
    cutoff = max(top * 0.25, 0.5)
    print(f"Need: {need!r}\n")
    hit = False
    for agent, score in ranked:
        if score < cutoff:
            continue
        hit = True
        rel = [s for s in standards if s["owner"] in (agent, "all")
               and bm25(need, [(s["id"], f"{s['id']} {s['category']} {s['rule']}")]).get(s["id"], 0) > 0]
        print(f"  → {agent:<12} (score {score:.1f}) — {AGENTS[agent]}")
        for s in rel[:4]:
            print(f"       · {s['id']} [{s['severity']}]")
    if not hit:
        print("  No confident owner. Default to the coordinator's judgement and say so —\n"
              "  an unowned need is a gap worth reporting, not a silent skip.")


def validate(standards, libs):
    failures, checks = [], 0
    seen = set()
    for r in standards:
        checks += 3
        if r["owner"] not in AGENTS and r["owner"] != "all":
            failures.append(f"OWNER    {r['id']}: '{r['owner']}' is not a fleet agent (or 'all')")
        if r["severity"] not in SEVERITIES:
            failures.append(f"SEVERITY {r['id']}: '{r['severity']}' not in {sorted(SEVERITIES)}")
        if not r["verify"].strip():
            failures.append(f"VERIFY   {r['id']}: no verification method — a rule you cannot check is a wish")
        if r["id"] in seen:
            failures.append(f"DUP      {r['id']}: duplicate id")
        seen.add(r["id"])
    for l in libs:
        checks += 1
        if not l["licence"].strip():
            failures.append(f"LICENCE  {l['id']}: no licence recorded — never adopt code with unknown terms")
    print(f"Validated {checks} checks across {len(standards)} standards and {len(libs)} component libraries.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print("  " + f)
        return 1
    print("All checks passed.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Query fleet standards and route a need to its owning agent.")
    ap.add_argument("--agent", choices=sorted(AGENTS) + ["all"], help="standards owned by this agent")
    ap.add_argument("--category", help="filter by category (ux, a11y, security, performance, ...)")
    ap.add_argument("--severity", choices=sorted(SEVERITIES), help="filter by severity")
    ap.add_argument("--context", help="comma list: web,api,ai,commercial,private — gates context-specific rules")
    ap.add_argument("--checklist", action="store_true", help="emit as a markdown checklist")
    ap.add_argument("--compact", action="store_true", help="one line per rule (the dispatch form — ~3x cheaper)")
    ap.add_argument("--why", metavar="ID", help="full rationale + verification for one rule id")
    ap.add_argument("--who", help="which agent covers this need?")
    ap.add_argument("--libraries", action="store_true", help="list the vetted component libraries")
    ap.add_argument("--validate", action="store_true", help="dataset integrity gate")
    a = ap.parse_args(argv)

    standards, libs = load("standards"), load("component-libraries")

    if a.validate:
        return validate(standards, libs)
    if a.libraries:
        for l in libs:
            print(f"\n{l['name']}  ({l['kind']}, {l['stacks']})\n  {l['url']}\n"
                  f"  delivery: {l['delivery']}\n  licence:  {l['licence']}\n"
                  f"  best for: {l['best_for']}\n  caveats:  {l['caveats']}")
        return 0
    if a.who:
        route(a.who, standards)
        return 0
    if a.why:
        hit = [r for r in standards if r["id"] == a.why]
        if not hit:
            print(f"no standard with id {a.why!r}. Known ids: "
                  + ", ".join(sorted(r["id"] for r in standards)))
            return 1
        show(hit)
        return 0

    contexts = [c.strip() for c in (a.context or "").split(",") if c.strip()]
    rows = [r for r in standards
            if (not a.agent or a.agent == "all" or r["owner"] in (a.agent, "all"))
            and (not a.category or a.category.lower() in r["category"].lower())
            and (not a.severity or r["severity"] == a.severity)
            and applicable(r, contexts)]
    rows.sort(key=lambda r: (["blocking", "warning", "nit"].index(r["severity"]), r["id"]))
    show(rows, a.checklist, a.compact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
