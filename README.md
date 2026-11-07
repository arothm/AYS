# AYS — Abdullrahman Yasser Skill

An Agent Skill that carries Abdullrahman Yasser's engineering knowledge, so that
when Claude works on a task it does it the way he would himself.

It holds **410 rules** across web (HTML, CSS, JavaScript, delivery, SEO), DevOps,
Git, npm/pnpm, Bun, Tailwind, React, AI-assisted development, LLM-powered
features, MCP servers and Agent Skills. Every rule carries a one-line **Why**, so
Claude can judge cases the rule doesn't spell out. On top sits a working method
assembled from those rules: plan first, change in small verified steps, prove it
in a real browser, ask before anything destructive, and cite the rule behind
every decision. A checker scans a project for the 67 rules a script can detect.

## Install

**Claude Code (plugin):**

```
/plugin marketplace add arothm/AYS
/plugin install ays@ccskill
```

**Claude Desktop / Cowork:** upload [`ays.skill`](ays.skill) as a custom skill
in the app's skill settings.

**Manual:** copy `skills/ays` into `~/.claude/skills/`.

## Use

It loads by itself when a task matches its description: any coding, review,
refactor, build, test, deploy or repository work in the areas above. To force it,
say "use ays". Claude then loads only the rule files the task needs (a CSS fix
loads `web-css.md`, not the SEO rules) and cites rule IDs such as `WEB-224` in
what it reports.

To check a project, say "use ays to check this project". Claude runs the checker,
then reads the code against the rules a script can't judge, and reports each
finding with its rule ID and Why. You can run the checker yourself:

```
python skills/ays/scripts/check.py path/to/project
python skills/ays/scripts/check.py --rules
```

It prints `file:line  RULE-ID  severity  message`. `error` means the rule is broken
as written; `review` means a person should look (an `outline: none` may have a
focus style elsewhere). It exits 1 when there is an error (`--strict`: any
finding), so it can gate CI. `--json` gives machine-readable output.

Look up rules, or export the whole list with every Why as one Markdown document:

```
python skills/ays/scripts/rules.py show WEB-024
python skills/ays/scripts/rules.py search contrast
python skills/ays/scripts/rules.py export -o ays-rules.md
```

## Layout

```
skills/ays/
  SKILL.md                     working method + which file to load when
  references/                  the rules and their Whys, one file per area
  scripts/rules.py             show / search / export / validate the rules
  scripts/check.py             scan a project for detectable rule breaches
docs/rule-revisions.md         every change made to the original list, and why
build.py                       builds ays.skill deterministically, --check verifies it
tests/test_ays.py              unit tests for rules.py, check.py and build.py
.claude-plugin/marketplace.json
```

## Changing the rules

1. Edit the rule in `skills/ays/references/`. Keep its ID; new rules take the
   next free number in their area, and need a `  - Why:` line directly under
   them. When merging two rules, list the retired ID under the file's
   `## Merged rules` heading. If `check.py` checks the rule, keep its ID in sync
   there (a test fails if a checked ID stops existing).
2. Check and rebuild:

   ```
   python skills/ays/scripts/rules.py validate
   python -m unittest discover -s tests
   python build.py
   python build.py --check
   ```

`ays.skill` is committed and nothing rebuilds it automatically, so skipping
`python build.py` leaves a stale upload. `build.py --check` catches that.

Everything is Python standard library: no install step, no dependencies.

## Limits

- **The checker covers 67 of 410 rules.** The rest need judgment and are applied
  by Claude reading the code. The checker reads source text, not a rendered page:
  it parses HTML with the standard library and scans CSS and JavaScript line by
  line with comments and strings blanked out, so it misses breaches that only
  appear at runtime and can flag a `review` item that is actually fine. It does
  not check inline `<style>`/`<script>` blocks or template languages yet.
- **Coverage has gaps.** There are no rules yet for backend frameworks,
  databases, server-side security, TypeScript configuration or DevOps
  operations; see `docs/rule-revisions.md`. In those areas Claude says the rule
  is not from AYS.
- **Not yet tested in a live session.** The files validate and the bundle
  builds, but confirming that Claude loads the skill for the right requests
  (SKL-008) still has to be done after installing it.

## License

MIT
