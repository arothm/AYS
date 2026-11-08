---
name: ays
description: Abdullrahman Yasser's engineering rules and working method (AYS = Abdullrahman Yasser Skill), so work is done the way he would do it himself. Covers web (HTML, CSS, JavaScript, HTTP delivery, performance, SEO), DevOps, linting and formatting (ESLint, Prettier), Git, npm/pnpm, Bun, Tailwind, React, AI-assisted development, LLM-powered features, MCP servers and Agent Skills. Use for any coding, review, refactor, build, test, deploy or repository task in these areas, and whenever the user says "use ays", "run ays" or asks to work the way Abdullrahman would.
license: MIT
---

# AYS — Abdullrahman Yasser Skill

This skill carries Abdullrahman's own engineering knowledge: 439 rules, each with
a stable ID (`WEB-024`, `GIT-009`, ...) and a "Why" line giving his reason. Do the
work the way he would: follow the working method below, load the rule files the
task needs, and apply them. Where a rule doesn't spell a case out, decide by its
Why.

## Load only what the task needs

Read the matching files in `references/` before writing or reviewing code. Load
every row that applies; skip the rest.

| Task touches | Load |
|---|---|
| HTML markup, templates, JSX structure | `references/web-html.md` |
| Stylesheets, component styling | `references/web-css.md` |
| JavaScript or TypeScript | `references/web-javascript.md` |
| Serving, performance, protocols, browser testing, dependency updates | `references/web-delivery.md` |
| Public pages meant to rank or be cited | `references/web-seo.md` |
| Hosting, VPS, CI/CD, environments | `references/devops.md` |
| Linters, formatters, static analysis, Git hooks, editor settings (ESLint, Prettier) | `references/linting-formatting.md` |
| Any commit, branch, merge, undo or push | `references/git.md` |
| package.json / npm / pnpm, or installing any package | `references/package-management.md` |
| Bun projects | `references/bun.md` |
| Tailwind projects | `references/tailwind.md` |
| React projects | `references/react.md` |
| Any change larger than a one-line fix | `references/ai-assisted-development.md` |
| Features that call LLMs or ML models, or choosing an AI model or provider | `references/ai-features.md` |
| MCP servers or clients | `references/mcp-servers.md` |
| Writing or changing a skill, including this one | `references/agent-skills.md` |

Detect the stack from the repository (package.json, lockfiles, bunfig.toml,
Tailwind and React imports) instead of asking. Files marked "load only when"
apply only to projects that use that tool.

To read a rule cited by ID, or find rules on a topic, run the bundled script by
its absolute path (this skill's directory, not the user's project):

```
python <skill-dir>/scripts/rules.py show WEB-024
python <skill-dir>/scripts/rules.py search "lazy"
```

## Checking a project

When asked to check, audit or review a project against AYS (or before declaring
web work done), run the checker on the project root:

```
python <skill-dir>/scripts/check.py <project-dir>
python <skill-dir>/scripts/check.py --rules      # which rules it covers
```

It reports `file:line  RULE-ID  severity  message`. An `error` breaks the rule as
written. A `review` is probably a breach but needs judgment: read the code before
reporting it (an `outline: none` may have a focus style elsewhere). The script
only covers rules detectable from source text, so after it, read the code against
the loaded reference files for the rest, and report both together with each
rule's ID and Why. Fix nothing until the user approves (AID-012).

## Working method

Each step is Abdullrahman's own rule, cited by ID.

1. **Orient.** Read the project's instruction file (AID-015) and check `git status`
   and the remote before starting (GIT-004, GIT-015).
2. **Plan before non-trivial work.** Write the scope, boundaries, edge cases and
   acceptance criteria first, and ask about anything under-specified instead of
   guessing (AID-009). Architecture, security, compliance and UX decisions are
   the user's: present the options with trade-offs (AID-010).
3. **Change in small, verified steps.** One module or concern at a time (AID-002),
   with passing tests in place before structural changes (AID-003), on a branch
   for multi-day work (GIT-018). Keep the project's existing libraries and working
   code unless asked (AID-001, RCT-007). New code ships with tests and docs
   (AID-011).
4. **Prove it works.** A clean lint or review is not proof; run the tests and the
   real behavior (AID-004). For web work, test as a real user in a real browser,
   watch the network log and fix every 4xx/5xx (WEB-023, WEB-005), test with the
   keyboard only (WEB-152), check contrast (WEB-224) and validate markup and CSS
   (WEB-020, WEB-208). Run `check.py` on what you changed. Review generated
   front-end code like anyone else's (AID-005).
5. **Stay safe.** Ask before destructive or hard-to-reverse actions, unfamiliar
   network calls, and commits or pushes not yet authorized (AID-012). Match the
   user's shell (AID-013). Never commit or send secrets (GIT-009, AID-014). Verify
   every package before installing it (PKG-009).
6. **Commit cleanly.** Atomic commits with imperative messages that say what and
   why (GIT-005, GIT-007); never commented-out code or debug bypasses (GIT-019).
7. **Report.** Cite the rule ID behind every finding, fix and decision, and say
   plainly what was verified and what was not.

## When rules and the situation disagree

- The user's explicit instruction in the session wins over a rule. If it breaks
  one, name the rule once, then do what they asked.
- A project's established conventions win over a style rule (see AID-001,
  RCT-007, BUN-005). Point out the difference; don't silently rewrite either side.
- If the task falls outside these rules (backend frameworks, databases, server
  security, TypeScript configuration, and so on), say that AYS has no rule for
  it, then use standard good practice and label it as not from AYS.
