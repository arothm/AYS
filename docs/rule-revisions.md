# Rule revisions

Every change made to Abdullrahman's original list (423 rules, received
2026-10-29) when it was encoded into AYS. Anything not listed here was kept word
for word. Original numbers are kept as IDs: Web #24 is `WEB-024`, Git #9 is
`GIT-009`. Prefixes: WEB, OPS (DevOps), GIT, PKG (package management), BUN, TWD
(Tailwind), RCT (React), AID (AI-assisted development), AIF (AI-powered
features), MCP, SKL (Agent Skills).

Result: 410 rules. 13 duplicates were merged into another rule; no rule was
dropped. `python skills/ays/scripts/rules.py show WEB-049` shows where a merged
number went.

## Corrected

| Rule | Was | Now | Why |
|---|---|---|---|
| WEB-004 | HTML has no functionality without JavaScript | Native HTML behavior (links, forms, `<details>`, `<dialog>`, popover) first; add JS only for what it cannot do | Overstated, and contradicted WEB-144 and WEB-259 |
| WEB-013 | `<main>` must be a direct child of `<body>` | One visible `<main>`; direct child on plain pages, may sit inside the app root in framework apps; never inside header/nav/footer/article/aside | Impossible in React/Vite apps (`<div id="root">`), and not what the spec requires |
| TWD-003 | Let prettier-plugin-tailwindcss sort classes | Same, but only when the project already uses Prettier; don't add it unasked | Contradicted the "don't add libraries unasked" rules |

## Context added

These rules read as if part of their context was missing, so the agent would have
applied them literally. Each gained one clause.

| Rule | Added |
|---|---|
| WEB-026 | Applies when markup is parsed as XML (XHTML, SVG, XML documents) |
| WEB-028 | "Shorthand" means boolean-attribute shorthand (bare `checked`) |
| WEB-030 | Also `children` and `nextElementSibling` for element traversal |
| WEB-032 | Why: whitespace between inline-block elements renders as gaps; use Flexbox or Grid |
| WEB-033 | Why: `firstChild` is often a whitespace text node |
| WEB-034 | Fix the layout with Flexbox/Grid and let the minifier handle whitespace |
| WEB-172 | HTTP/3 uses RESET_STREAM/STOP_SENDING where HTTP/2 uses RST_STREAM |

## Updated with checked facts

| Rule | Change | Source checked 2026-10-29 |
|---|---|---|
| PKG-006 | npm `min-release-age` is off by default; pnpm 11 turns `minimumReleaseAge` on by default | npm 11.10.0 notes; pnpm 11 coverage |
| WEB-169 | Exact date: Google stopped FAQ rich results on May 7, 2026 | Search industry coverage of the change |

## Merged duplicates

| Retired | Merged into | Shared point |
|---|---|---|
| WEB-049, WEB-101 | WEB-009 | Elements need both opening and closing tags |
| WEB-050, WEB-197 | WEB-014 | Div-itis; no `<span>` where a block container is needed |
| WEB-056 | WEB-054 | Unique ids |
| WEB-058 | WEB-048 | Classes for styles and shared behavior |
| WEB-126, WEB-127 | WEB-001 | Separation of HTML, CSS and JavaScript |
| WEB-132 | WEB-129 | Inline styles are a last resort |
| WEB-166 | WEB-169 | Structured data |
| WEB-167 | WEB-018 | Meaningful alt text |
| WEB-168 | WEB-017 | Descriptive media filenames |
| WEB-194 | WEB-013 | One `<main>` per document |

Cross-references were rewritten to IDs ("see #144" became "see WEB-144").

## Why lines added

Every rule gained a one-line "Why" under it, drafted by Claude for Abdullrahman's
review: the consequence of following or breaking the rule. They are new text, not
part of the original list, so review them like any other change. `rules.py
validate` fails a rule that has none.

## Kept as written, flagged

- **WEB-037** (open external links in a new tab). Much accessibility and UX
  guidance prefers leaving that choice to the user. Kept because it is a
  deliberate preference; WEB-039 already requires announcing the new window.

## Reorganized

The Web section (276 rules) was split by topic so a task loads only what it
needs: `web-html.md`, `web-css.md`, `web-javascript.md`, `web-delivery.md`
(HTTP, performance, testing, compatibility) and `web-seo.md`. Inside every file,
rules are grouped under headings; their IDs did not change.

## Not covered yet

AYS has no rules for these, and SKILL.md tells the agent to say so rather than
present general practice as Abdullrahman's:

- Backend frameworks, API design and databases (queries, migrations, indexing)
- Server-side security: XSS-safe DOM writes, CSP, CSRF, parameterized SQL,
  password hashing, CORS, server-side rate limiting
- TypeScript configuration and typing conventions
- Testing strategy beyond E2E (WEB-023) and "ship tests with code" (AID-011)
- DevOps operations: backups with restore tests, monitoring and alerting,
  rollback, Docker, SSH and firewall hardening
