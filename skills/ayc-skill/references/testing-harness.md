# Testing harness — shared playbook for all test agents

The harness-using agents follow this playbook so they verify with real evidence
instead of reasoning about the code, stay zero-dependency, and don't reinvent the
same plumbing each run: `tester` (all functional testing — unit/integration/e2e,
build, type-check) uses it in full; `frontend` uses the browser/viewport part for
responsive & color checks; `security` uses the scanner part; `ai-engineer` uses
it to run evals. It adapts the patterns proven by Anthropic's `webapp-testing`
skill to the fleet's principles.

## Policy 1 — Prefer the project's own runner; generate ad-hoc only as fallback

The project's maintained test suite is repeatable and trusted; generated
automation is not. So:

1. **Run what the project already has first** — the test/e2e commands detected
   in Step 1 (Jest/Vitest/Playwright/Cypress/pytest/etc.). This is the primary
   signal.
2. **Generate ad-hoc automation only when there is no suite** for what you need
   to verify, or to reproduce a specific bug. Label generated-automation results
   as such so they aren't mistaken for the project's own guarantees.

This directly answers the QA caveat: skills are good at ad-hoc generated
checks, but repeatable suites are better when they exist — so use them when they
exist.

## Policy 2 — Zero-dependency; browser automation via MCP (opt-in)

The skill installs nothing. Two consequences:

- **Server lifecycle** uses the bundled `{skill_dir}/scripts/with_server.py` (Python
  standard library only). It starts one or more servers, waits for their ports,
  runs your command, and tears them down. Run it with `--help`, then invoke it
  as a **black box** — do not read its source into your context (that wastes
  tokens; the script exists precisely so you don't have to).
- **Browser control** (rendering, clicking, screenshots, console logs) is done
  through a **Playwright/browser MCP if one is connected** — not a bundled
  Playwright install. Check for an available browser/Playwright MCP first.
  - **`ayc-tester` and `ayc-frontend` ship with the in-app browser tools
    (`mcp__Claude_Browser__*`) in their own tool lists** — that is the isolated
    browser, already available, and no MCP setup is needed to use it.
  - **Browser preference (important — respect the user's isolation choice).**
    When more than one browser MCP is available, ALWAYS prefer an isolated,
    sandboxed browser over the user's real logged-in browser. This is a category
    rule, not a fixed tool list — judge by *isolated vs. the user's real browser*.
    Order:
    1. An in-app / sandboxed browser MCP (e.g. `mcp__Claude_Browser__*`) —
       isolated, no personal logins, no history. **Use this by default.**
    2. A Playwright MCP (e.g. `mcp__playwright__*`) — its own throwaway
       Chromium, also isolated.
    **NEVER** use the user's real or paired Chrome (e.g.
    `mcp__claude-in-chrome__*`, or a Playwright launched with `--channel chrome`)
    for skill testing unless the user explicitly asks for it in this run — it
    carries their live logins, cookies, and history, and driving it is a privacy
    and safety hazard.
  - If present: drive the browser through the MCP tools (following the preference
    order above).
  - If absent: do **not** fabricate rendered results. Run the project's own
    headed/e2e suite if it has one, otherwise fall back to static code analysis
    and clearly mark those findings **"unverified (no browser available)"** so
    the coordinator and user know they weren't confirmed live. Note the missing
    MCP as a finding — knowing you couldn't render is useful information.

### Connecting a browser MCP (one-time, unlocks a lot)

A connected browser MCP is what lets the fleet **eyeball the UI**, **drive real
end-to-end flows and read the console**, and **browse the component catalogues**
(`design-inspiration.md`). It's the single highest-leverage thing to enable. In
Claude Code, add a Playwright MCP server — for example:

```
claude mcp add playwright -- npx @playwright/mcp@latest
```

Then restart/reload so it registers. Once present, the `frontend`, `tester`, and
`ai-engineer` agents detect it and use it automatically; nothing else changes.
Verify with `/mcp` (it should list the server). Without it, everything still
works — the fleet just labels visual/flow findings "unverified (no browser)"
rather than pretending it rendered them.

## Policy 3 — Reconnaissance-then-action (for anything browser-driven)

The most common browser-automation bug is acting before the page is ready. So:

1. **Navigate**, then **wait for the network to go idle** (equivalent of
   Playwright's `networkidle`) before you inspect anything on a dynamic app.
2. **Inspect the rendered state** — screenshot and/or read the DOM — to discover
   the real selectors.
3. **Act** using the discovered selectors, with explicit waits.

Decision tree for locating selectors:

```
Is the target static HTML?
  ├─ Yes → read the HTML file directly to get selectors
  │         └─ if that's incomplete, treat it as dynamic (below)
  └─ No (dynamic) → is the server already running?
       ├─ No  → use {skill_dir}/scripts/with_server.py to start it, then reconnoiter
       └─ Yes → navigate → wait for network idle → screenshot/inspect → act
```

## Policy 3b — Exercise the running product (mandatory for `tester` on any runnable UI)

The suite proves the code the team thought to test. Running the app proves the
product. **`tester` does both**, and this sweep is not optional when there is a UI
and an isolated browser MCP to drive it with.

Bring the app up with `{skill_dir}/scripts/with_server.py`, then work through this list per
primary screen. Screens come from memory's *Testing harness* section if recorded,
otherwise from the router/route table (read it — don't guess the URLs).

**1. Both viewports, eyeballed.**
Render each screen at **desktop 1440×900** and **mobile 375×812**, screenshot both,
and actually look: overflow and horizontal scroll, overlapping or clipped text,
off-screen or unreachable controls, collapsed layouts, images that don't scale, tap
targets under 44px, and anything that reads as broken to a human. The DOM being
correct and the page looking right are different claims — this one is visual.

**2. Every clickable element, actually clicked.**
Enumerate the interactive controls on the screen (buttons, links, nav and menu
items, tabs, accordions, form submits, modal open/close, pagination, icon-only
controls) and exercise each one. Report anything that is:
- **dead** — click produces no state change, no navigation, no request;
- **misrouted** — goes somewhere other than its label promises, or 404s;
- **silently failing** — the UI reports success while the network says otherwise;
- **keyboard-unreachable** — no focus, or no activation via Enter/Space (this is a
  `frontend` a11y finding too — report it, and let the merge dedupe).
Destructive controls (delete, pay, send, deactivate) are exercised **only** against
disposable local/staging data — never against production or real user records. If
you can't reach the flow safely, say so instead of clicking it.

**3. Console and network on every action.**
Around each interaction, capture:
- **console** — errors *and* warnings, including React/Vue key and hydration
  warnings, CSP violations, and uncaught promise rejections;
- **network** — failed requests, 4xx/5xx, requests that never resolve, duplicated or
  waterfalled calls on a single action;
- **response bodies** — read them. A `200` carrying `{"error": …}`, an empty payload
  where the UI expects a list, or a stack trace in the body is a finding the status
  code hides. This is the check most automation skips.
Page load counts as an action: capture the console and network of the initial load
for every screen too.

**4. Report per screen, with artefacts.**
One block per screen: viewport screenshots, the control inventory with pass/fail per
control, the console and network findings, and the artefact paths. A flow claimed
without an artefact is "likely", not verified (Policy 4).

**Fix-phase re-exercise.** When Step 5 fixes touch the UI or a flow, `tester`
re-runs this sweep **scoped to the affected screens** before the fix is marked
verified. A UI fix confirmed only by a green unit test has not been confirmed.

**No browser MCP?** Say so, run the project's own e2e suite instead, and label
everything visual or flow-based **"unverified (no browser)"**. Never describe a
screen you did not render or a click you did not perform.

## Policy 4 — Capture evidence to `.ayc-skill/log/<run-id>/`

"Never assume" means your claims should be backed by artifacts the user can
open. For each run, save into `.ayc-skill/log/<run-id>/` (git-ignored):

- **Screenshots** at the relevant states (and, for the designer, one per
  breakpoint).
- **Console logs** and any Playwright/e2e **traces** the runner produces.
- **Scanner output** (from `{skill_dir}/scripts/run_scanners.py`) for the security agent.

Reference the artifact path in the finding, e.g. `Fix: … (see
.ayc-skill/log/<run-id>/checkout-500.png)`. A finding with an artifact is verified;
one without is, at best, "likely."

## Policy 5 — Cache harness facts in memory

Discovering how to start the app, which selectors matter, where the e2e runner
lives, and whether a browser MCP is available costs tokens. Record these as a
**Memory delta** so the next run inherits them instead of rediscovering:

- server start command(s) + ports and readiness URL
- e2e/test runner location and invocation
- stable selectors for critical flows
- browser MCP availability
- design tokens / breakpoints (for the designer)

Verify a cached fact still holds if the relevant files changed since it was
recorded (check the diff, not a hunch) — stale harness facts are worse than
none.

## Security-specific: the scanner runner

`security` uses `{skill_dir}/scripts/run_scanners.py` (stdlib only, installs nothing).
It detects which scanners are already on PATH (`npm audit`, `pip-audit`,
`cargo audit`, `osv-scanner`, `semgrep`, `bandit`, `gitleaks`, `trufflehog`),
runs the ones that fit the repo, and prints a normalized summary to triage.
Run it with `--help` first, invoke as a black box, save output to the run log —
then **confirm each reported issue against the real code** before reporting it,
because scanners produce false positives (never-assume). If no scanner is
installed, it says so; fall back to manual review and state that, don't
fabricate results.
