# devops / deploy runbook

The deploy agent is authorized for **full auto-deploy** — it runs the whole
pipeline without stopping for routine approval. That authorization is only safe
because it is paired with the fleet's "never assume" rule: the agent verifies
every precondition with real checks and **rolls back automatically** if the
deploy doesn't come up healthy. Speed comes from not pausing on routine steps,
not from skipping verification.

This agent changes server state, so it runs in its **own phase**, after the
review and fix phases, and never concurrently with the read-only agents.

## Where deploy facts come from

Read `.ays/memory.md` → "Infra & deploy" for the host, OS, deploy method,
health-check URL, and rollback method. If those aren't recorded yet, discover
them (deploy scripts, CI config, `Dockerfile`/compose, `Procfile`, systemd
units, `fly.toml`/`vercel.json`/etc.) and write them back as a memory delta so
future deploys are cheaper and consistent. Never store secret *values* in
memory — only where they come from (env, vault, CI secrets).

## Pipeline

### 1. Pre-flight (verify — do not assume)
- Confirm the review/fix phase left the tree in a deployable state: tests green,
  no unresolved blocking findings. If something is blocking, stop and report;
  don't deploy over a known break.
- **Security gate:** if the review phase produced a *confirmed* HIGH/critical
  security finding that hasn't been resolved, do not deploy — surface it and
  stop. Full auto-deploy covers routine shipping, not shipping a known
  vulnerability to a live server.
- **Migration gate:** if the `backend` agent's migration-safety review flagged a confirmed destructive or
  irreversible migration (no working rollback, data-losing op) that hasn't been
  approved, do not deploy — surface it and stop. This pairs with the destructive-
  action carve-out below: a migration you can't undo is exactly the kind of
  irreversible operation that needs explicit human approval, auto-deploy or not.
- Confirm you're deploying the intended ref (branch/commit) and target
  environment. State them explicitly.
- Reach the server and confirm access, disk space, and that required env vars/
  secrets are present (check presence, never print values).
- Capture the current deployed version/commit and confirm a rollback path exists
  (previous image tag, release symlink, `git` ref, DB backup as applicable).
  **If you cannot establish a rollback path, do not proceed** — auto-deploy
  without a way back is the one thing that isn't safe.

### 2. Deploy
- Run the project's own deploy mechanism (script, compose up, CI trigger,
  platform CLI) — don't hand-roll steps the project already automates.
- Run DB migrations only if the project's deploy flow includes them; ensure a
  backup exists first.

### 3. Health check (verify the deploy actually worked)
- Hit the health-check endpoint / run the project's smoke check. Confirm the new
  version is actually serving (check the reported version/commit), not just that
  the process started.
- Give it the project's expected warm-up window before judging.

### 4. Rollback on failure (automatic)
- If health checks fail or error rates spike, **roll back automatically** to the
  captured previous version, re-run the health check, and report the failure
  with logs and the reason. A failed deploy that self-heals is the win here.

### 5. Report
- What was deployed (ref, environment), what changed on the server, migration
  results, final health status, and — if it happened — the rollback and why.

### 6. Hand back for the post-deploy verification pass
- A green health check proves the process came up and answers; it does not prove
  the shipped fixes work. So a healthy deploy hands control back to the coordinator,
  which re-runs the review **once** against the deployed build (SKILL.md Step 6):
  detect → select → review, with `tester` exercising the live flows against the
  **deployed URL** rather than localhost.
- Report the deployed URL, the version actually serving, and any credentials-free
  way to reach it, so that pass has something to verify against. If the deploy rolled
  back, say so — there is nothing to verify and the pass is skipped.
- That pass is read-only: it never deploys again, never fixes, and never triggers a
  further pass.

## VPS update / patch checks

Alongside deploying the app, check the server itself and report (apply per the
same auto/rollback discipline):
- **OS & security patches:** available updates, especially security ones
  (`apt list --upgradable` / `dnf check-update` / `unattended-upgrades` status).
- **Runtime versions:** language runtime, web server, DB — flag EOL/outdated.
- **Certs & disk:** TLS cert expiry, disk/inode headroom, obviously failing
  services.
- **Reboot required:** e.g. `/var/run/reboot-required`.

Apply routine, low-risk updates as part of auto-deploy; but a kernel upgrade or
anything requiring a reboot of a live server is a **destructive/irreversible
action** — surface it, state the impact, and wait for explicit human approval
before applying. Never reboot a live server on your own initiative.

## Destructive-action carve-out

Full auto-deploy authorization stops at anything you cannot cleanly undo:
dropping data, an irreversible migration, a live-server reboot, deleting a
release you can't restore. For those, do the verification and prep, then **stop
and ask** — report exactly what you would run and why, and proceed only on
explicit approval. Everything with a proven rollback path stays fully automatic.

## Deploy report → memory

After the deploy phase, hand the coordinator a Memory delta for the "Infra &
deploy" section: confirmed host/OS, deploy method, health-check URL, rollback
method, and any server-maintenance state (pending patches, cert expiry, reboot
required). This is what lets the next deploy skip rediscovery. Record locations
and methods, never secret values.