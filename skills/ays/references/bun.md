# Bun

Load only when the project uses Bun (bun.lock or bun.lockb, bunfig.toml, or Bun
APIs in the code). Each rule's "Why" is the reason to follow it; use it to judge
cases the rule does not spell out.

- `BUN-001` DO run .ts and .tsx files directly with Bun, and do not add ts-node, babel-node, or other transpilation layers just to execute TypeScript
  - Why: Bun runs TypeScript natively, so an extra layer only adds dependencies and startup time.
- `BUN-002` DO use bun --hot during server development to reload code without restarting the process; global state on globalThis persists across reloads, so keep sockets and connection pools there (e.g., globalThis.pool ??= createPool()) instead of creating new ones on every reload
  - Why: --hot swaps code without a restart, but a pool created on every reload leaks connections until the database refuses more.
- `BUN-003` DO audit dependencies for native add-ons before migrating production workloads to Bun; add-ons that use V8-specific APIs will not work because Bun runs on JavaScriptCore, while Node-API add-ons usually do
  - Why: Finding the incompatible add-ons first avoids a migration that fails in production.
- `BUN-004` DON'T assume synthetic I/O benchmarks replace load-testing; load-test your own application code
  - Why: Benchmarks measure the runtime, not your queries, I/O and dependencies; only a load test shows your real capacity.
- `BUN-005` DO use bun test with the built-in bun:test expect() matchers instead of external test runners and assertion libraries in Bun projects, without replacing an existing runner unless asked
  - Why: The built-in runner is fast and needs no extra dependencies, while replacing a runner that works creates churn nobody asked for.
- `BUN-006` DO name test files with .test.ts or .spec.ts so bun test discovers them automatically
  - Why: bun test finds files by these names, and any other name is silently skipped.
- `BUN-007` DO compile standalone single-file executables with bun build --compile for CLI tools, so the target machine needs no runtime or setup
  - Why: One self-contained file runs on machines that do not have Bun installed.
- `BUN-008` DO prefer native Bun.serve() and Bun.sql over external HTTP frameworks and database wrappers when they meet the project's needs (check that Bun.sql supports your database)
  - Why: The built-in APIs are fast and add no dependency to install, update or audit.
- `BUN-009` DON'T add third-party shell execution libraries when Bun.$ is available
  - Why: Bun.$ already runs shell commands across platforms with safe escaping, so a library adds nothing but a dependency.
- `BUN-010` DON'T write custom HTML-escaping code when Bun.escapeHTML() is available
  - Why: Hand-written escaping tends to miss a character and opens an XSS hole; the built-in is complete and fast.
- `BUN-011` DO use the standard Request and Response objects in Bun.serve() fetch handlers
  - Why: Standard web APIs keep handlers portable to other runtimes and familiar to anyone who knows fetch.
- `BUN-012` DON'T hardcode port numbers or secret keys; read them from environment variables (Bun loads .env files automatically into process.env and Bun.env, so do not install dotenv in Bun-only projects), and never commit .env files (see GIT-009)
  - Why: Hardcoded values differ per environment and secrets in code leak; dotenv is redundant because Bun already loads .env.
