# DevOps

Load when choosing hosting, deploying, running servers or VPS instances, setting
up CI/CD, or handling environments and configuration. Each rule's "Why" is the
reason to follow it; use it to judge cases the rule does not spell out.

- `OPS-001` DO implement isolated staging environments to validate runtime version upgrades, security patches, and database migrations before pushing to production
  - Why: An upgrade or migration that fails in staging costs nothing; the same failure in production means downtime or lost data.
- `OPS-002` DON'T apply manual configuration updates directly to unmanaged production VPS instances without automated backup snapshots and infrastructure-as-code tracking
  - Why: Manual changes cannot be reproduced or reviewed, and without a snapshot there is no way back when one breaks the server.
- `OPS-003` DON'T set excessively long Time-To-Live (TTL) durations on dynamic cloud service endpoints subject to automated blue-green deployments or disaster recovery failover pipelines
  - Why: Clients cache DNS for the whole TTL, so after a switch or failover they keep hitting the old target until it expires.
- `OPS-004` DO select containerized managed hosts or dedicated VPS instances for transactional production applications to isolate system performance from adjacent tenant workloads
  - Why: Dedicated resources keep response times predictable, because another tenant's load cannot slow your transactions.
- `OPS-005` DON'T host mission-critical applications on oversold shared hosting environments exposed to resource exhaustion from noisy neighbors
  - Why: Oversold hosts share CPU, memory and disk, so a neighbor's spike can take your application down.
- `OPS-006` DO evaluate server runtime memory use before choosing a stack or VPS size, stream large files and payloads instead of buffering them in memory, and consider embedded databases (e.g., SQLite) where a separate database server is not needed
  - Why: Memory is usually the first limit on a small server; streaming keeps memory flat whatever the file size, and SQLite removes a whole server to run.
- `OPS-007` DO build and publish documentation and release notes from the CI pipeline on merge (for example with a docs platform such as Mintlify or GitBook, or a static docs generator), so they update together with code instead of drifting from the API
  - Why: Docs built from the same commit as the code cannot fall out of date with it.
- `OPS-008` DO run automated checks (linting, formatting checks such as prettier --check, type checks, tests, static analysis, security scans) in CI on every push or pull request, make them required gates for merging (including code written by AI), and reserve human review for architecture, trade-offs, security compliance, regulatory auditing, UX design, and product intent; code style is left to the formatter and linter, never debated in review
  - Why: Automated gates catch regressions on every change whoever wrote it, which leaves people free to judge what tools cannot; style settled by a tool costs no review time and no arguments.
- `OPS-009` DON'T let CI/CD agents or automation commit directly to protected production branches; require a human-approved pull request, and enforce it with branch protection rules
  - Why: Human review on protected branches is the last check before production; automation that bypasses it can ship anything.
- `OPS-010` DO account for API rate limits in background scripts and CI pipelines, especially on free tiers: cap concurrency, retry with exponential backoff, and respect Retry-After headers
  - Why: Hitting a rate limit fails jobs and can get you temporarily banned; backoff and Retry-After let the pipeline recover on its own.
- `OPS-011` DO validate required environment variables (e.g., API tokens and keys) at application startup and fail fast with a clear error message before serving requests or starting any execution loop
  - Why: A missing variable caught at startup is one clear error; caught mid-request, it becomes a confusing failure in production.
