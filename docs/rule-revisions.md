# Rule revisions

Every change made to Abdullrahman's original list (423 rules, received
2026-10-29) when it was encoded into AYS. Anything not listed here was kept word
for word. Original numbers are kept as IDs: Web #24 is `WEB-024`, Git #9 is
`GIT-009`. Prefixes: WEB, OPS (DevOps), GIT, PKG (package management), BUN, TWD
(Tailwind), RCT (React), AID (AI-assisted development), AIF (AI-powered
features), MCP, SKL (Agent Skills), LNT (linting and formatting, added in batch 3).

Result: 410 rules. 13 duplicates were merged into another rule; no rule was
dropped. `python skills/ays/scripts/rules.py show WEB-049` shows where a merged
number went. Later batches are recorded at the end of this file; the current
total is 439.

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

## Batch 2: enterprise AI (2026-11-07)

37 rules received in sections 1.3, 2.4, 3.3, 4.3, 5.3 and 6.4, vetted against
the existing set and approved by Abdullrahman as proposed. Result: 17 new rules,
7 existing rules extended, 1 duplicate left unchanged, 4 dropped. Facts checked
2026-11-07: Opus 4.8 effort levels and adaptive thinking (Anthropic docs),
prompt-cache pricing (cached reads cost 0.1x input), Claude Mythos 5 access
through Project Glasswing, Anthropic's AI diligence statement tutorial.

### Extended

| Rule | Batch rules | Added |
|---|---|---|
| AID-014 | 1.3-5 | Consumer AI chat apps; use enterprise plans or APIs that isolate data |
| AIF-005 | 2.4-1, 2.4-4, 4.3-3, 4.3-4 | Classification and data conversion on small models; route by complexity at volume; Sonnet 5.5 as the default, not a mandate, dated |
| AIF-010 | 1.3-6 | Inline citations and automatic support checks on critical paths (not RAG everywhere, which contradicted AIF-023) |
| AIF-018 | 5.3-3 | Turn caching on; "up to 90%" corrected to cached input costing about a tenth |
| AIF-020 | 3.3-4 | Toxic or unauthorized output; never blocklists or regex alone |
| AIF-025 | 4.3-1 | Small model under a stronger orchestrator, model names dated |
| AID-008 | 5.3-5 | No production deploy without CI security gates (OPS-008) |

### Added

| Rule | Batch rules | Change from the original wording |
|---|---|---|
| AIF-029 | 1.3-1, 2.4-5, 6.4-4 | Merged; HIPAA only for health data; check which features the agreement covers |
| AIF-030 | 1.3-2, 2.4-5 | AES-256 at rest, TLS in transit; residency includes logs and backups |
| AIF-031 | 1.3-3 | Dedicated capacity only when volume or an SLA justifies it |
| AIF-032 | 1.3-4 | Redact secrets and personal data from logs |
| AIF-033 | 1.3-7, 2.4-2 | Merged; evaluate fallback models before they serve traffic |
| AIF-034 | 2.4-3 | Cost caveat: OCR or transcription when text is enough |
| AIF-035 | 2.4-6, 6.4-1 | Merged; leaderboards allowed for shortlisting |
| AIF-036 | 3.3-1 | Hard constraints enforced in code too (prompts aren't deterministic, AIF-003) |
| AIF-037 | 3.3-5 | RLHF/RLAIF are training methods; became LLM-as-judge plus human sampling |
| AIF-038 | 4.3-2, 4.3-5 | Merged; total caps kept (AIF-008), only thinking budgets left to the model |
| AIF-039 | 4.3-6 | Named Claude Mythos 5 and Project Glasswing |
| AIF-040 | 6.4-5 | Rewritten as a DO |
| AIF-041 | 6.4-6 | Fine-tuning last, after evaluation and retrieval (AIF-023) |
| AIF-042 | 3.3-6 | Interpreted as checking each region's AI and data rules |
| AID-020 | 5.3-1 | Signed by a named person; states tools, use and verification |
| AID-021 | 5.3-4 | Enforced with permission settings (AID-012) |
| AID-022 | 5.3-6 | Wording simplified |

### Not added

| Batch rule | Outcome | Why |
|---|---|---|
| 5.3-2 (adopt MCP) | Duplicate of MCP-001 | MCP-002 already limits it |
| 3.3-2 (mechanistic interpretability audits) | Dropped | A research technique users of hosted models cannot run; AIF-001 covers explainability |
| 3.3-3 (ASL thresholds) | Dropped | Anthropic's own policy for training models; AIF-008, AIF-019 and AIF-026 cover agent limits |
| 6.4-2 (embed engineering partners) | Dropped | Hiring advice, not an engineering rule |
| 6.4-3 (AQe Digital's AI solutions) | Dropped | A vendor advertisement |

## Batch 3: static analysis, ESLint and Prettier (2026-11-08)

24 rules received in four groups (labelled here S1-S6 static analysis, E1-E6
ESLint, P1-P6 Prettier, C1-C6 ESLint with Prettier, DOs before DON'Ts), vetted
and approved by Abdullrahman as proposed. Result: a new area, LNT (linting and
formatting, `references/linting-formatting.md`), with 12 rules, and OPS-008
extended; nothing dropped. Facts checked 2026-11-08: ESLint 10 removed the
eslintrc format and ESLint 9 reached end of life on 2026-08-06 (eslint.org);
eslint-config-prettier's `/flat` entry and CLI helper (its README); Prettier 3
skips node_modules and follows .gitignore by default (prettier.io); ESLint's
formatting rules are deprecated (eslint.org).

The Prettier rules are scoped to projects that use Prettier, so they agree with
TWD-003 (don't add Prettier unasked).

### Extended

| Rule | Batch rules | Added |
|---|---|---|
| OPS-008 | S4, P5, P6, C6 | Formatting checks such as `prettier --check` in the CI gates; code style left to tools, never debated in review |

### Added

| Rule | Batch rules | Change from the original wording |
|---|---|---|
| LNT-001 | S1, S6 | Merged; propose the tools in existing projects instead of adding them unasked |
| LNT-002 | E1, E4, P1, P4 | Merged into one "local, pinned tools" rule |
| LNT-003 | E2 | `eslint:recommended` updated to `js.configs.recommended` (eslintrc removed in ESLint 10) |
| LNT-004 | E6 | Tighten in small steps (AID-002) |
| LNT-005 | S3 | Named ESLint's `complexity` rule |
| LNT-006 | E3, E5 | Merged; a reason after `--` added |
| LNT-007 | S5 | "Don't ignore" became fix, or suppress with a recorded reason |
| LNT-008 | S2 | Same checks kept in CI, since hooks can be skipped |
| LNT-009 | C1, C2, C3, C5 | Merged; `"prettier"` extends entry updated to `eslint-config-prettier/flat` |
| LNT-010 | C4 | Unchanged in substance |
| LNT-011 | P2 | Narrowed: Prettier 3 already skips node_modules; reason changed from performance to generated files |
| LNT-012 | P3 | VS Code example added |