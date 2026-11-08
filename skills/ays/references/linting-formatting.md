# Linting and formatting

Load when setting up, configuring or running linters, formatters, type checkers
or static analysis (ESLint, Prettier, SAST tools), Git hooks, or editor settings.
The Prettier rules apply only to projects that use Prettier (see TWD-003). Each
rule's "Why" is the reason to follow it; use it to judge cases the rule does not
spell out.

## Setting up

- `LNT-001` DO set up static analysis (a linter and, where the language has one, a type checker) when a project starts, so quality checks exist before technical debt builds up; don't rely only on runtime tests to catch syntax errors or unhandled code paths, especially in interpreted languages. In an existing project without these tools, propose them instead of adding them unasked (see TWD-003)
  - Why: Static analysis catches whole classes of mistakes on every line without running anything, while tests only cover the paths they exercise; added later, it starts with a backlog of warnings nobody fixes.
- `LNT-002` DO install linters and formatters as local devDependencies of the project (see PKG-002), with Prettier pinned to an exact version (npm install --save-dev --save-exact prettier), and run them through the project's scripts; DON'T rely on a globally installed ESLint or the version bundled with an editor extension
  - Why: Everyone and CI then run the same version and get the same results; Prettier can change its output between releases, so an unpinned update reformats files nobody touched.
- `LNT-003` DO start ESLint from its recommended rule set (js.configs.recommended from @eslint/js in eslint.config.js; the "eslint:recommended" string belongs to the eslintrc format, which ESLint 10 removed) and add rules on top of it
  - Why: The recommended set catches real logic errors with no setup effort, and the old eslintrc syntax is simply not read by current ESLint.
- `LNT-004` DON'T switch on a large, strict style guide (e.g., the full Airbnb config) all at once in a legacy codebase; begin with the recommended logic checks, fix those, then tighten the rules in small steps (see AID-002)
  - Why: Thousands of style warnings at once bury the few real bugs and stall the adoption; small steps keep each change reviewable.
- `LNT-005` DO set an explicit complexity limit in the linter (e.g., ESLint's complexity rule, which counts the paths through a function) so functions stay small and fully unit-testable
  - Why: Every extra path through a function needs its own test, so a limit keeps functions small enough to test fully and understand.

## Suppressions and warnings

- `LNT-006` DO name the rule in every lint suppression comment and give the reason (e.g., // eslint-disable-next-line no-console -- CLI output), and DON'T use blanket suppressions such as a bare /* eslint-disable-next-line */ that silence every rule
  - Why: A blanket comment also hides unrelated real errors on that line, and the reason tells the next reader whether the suppression is still needed.
- `LNT-007` DON'T ignore warnings from static security analysis (SAST) tools: fix each one, or suppress it with a recorded reason after review, and treat any finding in code that handles personal data covered by regulations such as GDPR as blocking
  - Why: An ignored warning is a known vulnerability left in place, and a leak of regulated personal data brings fines on top of the breach.

## Hooks

- `LNT-008` DO run fast checks (formatting, linting, syntax) on staged files in a pre-commit Git hook (e.g., husky with lint-staged, or the pre-commit framework), and keep the same checks in CI, because hooks can be skipped with --no-verify (see OPS-008)
  - Why: The hook catches problems seconds after they are written, before they enter history; CI is still needed because a hook runs only where it is installed and can be skipped.

## ESLint with Prettier

- `LNT-009` DO, when ESLint and Prettier are used together, add eslint-config-prettier as the last entry of the ESLint config array (import eslint-config-prettier/flat in eslint.config.js) so no later config can re-enable rules that conflict with Prettier, and check for conflicts with its CLI helper (npx eslint-config-prettier eslint.config.js)
  - Why: Later entries override earlier ones, so anywhere but last a style guide can switch conflicting rules back on and the two tools fight over the same lines.
- `LNT-010` DON'T configure formatting rules (e.g., indent, max-len, quotes) in ESLint when Prettier formats the code; leave layout to Prettier and logic to ESLint
  - Why: Two tools formatting the same code produce conflicting errors and fix loops; ESLint has deprecated its own formatting rules anyway.

## Prettier and editors

- `LNT-011` DO commit a .prettierignore only for files Prettier would otherwise format but must not, such as vendored code or committed generated output; Prettier 3 already skips node_modules and follows .gitignore
  - Why: Reformatting generated or vendored files creates noisy diffs and changes that the next build or update overwrites (see WEB-272), while repeating the default ignores adds nothing.
- `LNT-012` DO commit shared editor settings that make the project's formatter the default per language (e.g., in VS Code's .vscode/settings.json, "[javascript]": { "editor.defaultFormatter": "esbenp.prettier-vscode" }), so everyone's editor formats the same way on save
  - Why: Without shared settings each editor formats with its own defaults, and every save produces unrelated formatting changes in the diff.
