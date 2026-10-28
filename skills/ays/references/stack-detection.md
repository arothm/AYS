# Stack detection

Goal: figure out what languages/frameworks are present, which parts are
frontend vs backend, and — most importantly — the *actual* commands the project
uses to test, lint, type-check, and build. Never hardcode a command; read it
from the project's own config so the agents run what CI runs.

## 0. Empty repo → greenfield, not detection

Before detecting anything, check whether there's anything to detect. If the repo
has no source beyond a README/LICENSE/`.gitignore` (no signal files below, no
`src`), or the user says they want to start from scratch, **stop detection and
hand back to the coordinator's greenfield bootstrap** (SKILL.md) — the fleet
interviews the user and scaffolds instead of reviewing an empty tree. Everything
below assumes there's existing code.

## 0b. Project context — ask, don't guess

Several standards are context-gated: a **private/internal/personal** project must
ship `noindex`, and a **commercial/public** one must ship a privacy policy. Getting
this wrong is costly in both directions (a private tool indexed by Google, or a
commercial site with no privacy policy), so **ask the user once rather than
inferring it**: *"Is this project private/internal, or commercial/public?"*

Record the answer in memory's *Project preferences* (`context: private|commercial`)
and pass it to every agent as `standards.py --context <value>`. Once recorded, it
drives the gated standards on this and every later run without asking again — the
user can change it. While you're asking, capture the other **pre-review** preference
too: whether the fleet should own DevOps (see the `devops` brief).

## 1. Find the subprojects

Start by listing the repo root and looking one or two levels deep for the signal
files below. In a monorepo you'll often find several (e.g. `apps/web/package.json`
and `services/api/pyproject.toml`). Each cluster of signal files is a subproject
that may deserve its own agent.

| Signal file | Ecosystem | Usual role |
|---|---|---|
| `package.json` | Node / JS / TS | frontend or backend (check deps) |
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python | usually backend |
| `go.mod` | Go | backend |
| `Cargo.toml` | Rust | backend / CLI |
| `pom.xml`, `build.gradle` | Java / Kotlin | backend |
| `Gemfile` | Ruby | backend / Rails |
| `composer.json` | PHP | backend |
| `*.csproj`, `*.sln` | .NET | backend |
| `Dockerfile`, `docker-compose.yml` | any | hints at services |

## 2. Frontend vs backend

For a `package.json`, read `dependencies`/`devDependencies`:

- **Frontend** signals: `react`, `vue`, `svelte`, `@angular/core`, `next`,
  `nuxt`, `vite`, `webpack`, `tailwindcss`, presence of `public/index.html`,
  `src/components`, `.jsx`/`.tsx`/`.vue` files.
- **Backend** signals: `express`, `fastify`, `koa`, `@nestjs/core`, `prisma`,
  `typeorm`, database drivers (`pg`, `mysql2`, `mongoose`), no DOM/bundler deps.

Python/Go/Rust/Java/Ruby/PHP subprojects are backend by default. A repo can be
frontend-only, backend-only, or both — plan agents accordingly.

**AI/LLM signals** (decides whether to include the `ai-engineer` agent): SDKs
like `anthropic`, `openai`, `@anthropic-ai/sdk`, `google-generativeai`,
`cohere`, `mistralai`; orchestration like `langchain`, `llamaindex`,
`semantic-kernel`; local models via `transformers`/`ollama`; a vector DB
(`pinecone`, `weaviate`, `qdrant`, `pgvector`, `chromadb`); or prompt/agent
files (`*.prompt`, a `prompts/` dir, tool/function-calling schemas). If any are
present, record "AI features: yes" in memory and include `ai-engineer`.

## 3. Extract the real commands

Prefer commands the project already defines over generic ones.

**Node (`package.json` → `scripts`)** — look for keys like `test`, `test:unit`,
`test:e2e`, `lint`, `typecheck`/`type-check`, `build`. Run via the project's
package manager: detect the lockfile (`package-lock.json`→npm,
`yarn.lock`→yarn, `pnpm-lock.yaml`→pnpm, `bun.lockb`→bun) and use
`npm run <script>` / `yarn <script>` / `pnpm <script>` / `bun run <script>`.

**Python (`pyproject.toml`)** — test runner is usually `pytest`; linters/format
under `[tool.ruff]`, `[tool.flake8]`, `[tool.black]`, `[tool.mypy]`. Common
commands: `pytest`, `ruff check .`, `mypy .`, `black --check .`.

**Go** — `go test ./...`, `go vet ./...`, `gofmt -l .`, and `golangci-lint run`
if configured.

**Rust** — `cargo test`, `cargo clippy`, `cargo fmt --check`.

**Java/Kotlin** — `mvn test` / `./gradlew test`, plus `checkstyle`/`spotbugs`/
`ktlint` if present.

**Ruby** — `bundle exec rspec`, `bundle exec rubocop`.

**Fallbacks** — also check a `Makefile` (targets like `test`, `lint`), CI config
(`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`) which reveals the
exact commands the team trusts, and `pre-commit-config.yaml` for the lint/format
tools they've standardized on.

## 4. Inventory dependencies (feeds the dependency checks)

While you have the manifests open, record what the dependency sweeps will need
so they don't re-derive it:

- **Manifests & lockfiles** — where they are, per subproject.
- **The ecosystem's update/audit tooling** so `security` and the `frontend`/
  `backend` agents use the real thing: `npm outdated` / `npm audit`, `pip list --outdated`
  / `pip-audit`, `go list -m -u all` / `govulncheck`, `cargo outdated` /
  `cargo audit`, `bundle outdated` / `bundler-audit`, etc.
- **Unused-dependency detectors** if present: `depcheck`, `knip`, `ts-prune`
  (JS/TS), `deptry`, `pip-autoremove` (Python), `cargo-udeps` (Rust),
  `go mod tidy` (Go). If none is installed, agents fall back to grepping each
  declared dependency name across the source.

Write this into memory's *Dependencies* section. It's what lets `security`
flag outdated/EOL/advisory packages and the `frontend`/`backend` agents flag
declared-but-never-imported dependencies, without every run rediscovering the
toolchain.

## 5. Determine review scope

- **Diff scope** (default for pre-commit/pre-merge): `git status --porcelain`
  for uncommitted work, or `git diff --name-only <base>...HEAD` (base is usually
  `main`/`master`/`develop`) for a branch. Hand agents the changed file list.
- **Full scope**: the whole subproject tree, for a full audit or a small repo.

If `git` isn't available or the repo isn't a git repo, fall back to full scope
and note it.
