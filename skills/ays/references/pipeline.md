# The pipeline — Steps 0 through 6

The operating manual for a **review-driven run** — the fleet finds the work. When
the *user* brings the work list instead ("fix these, add those"), follow
`references/build-mode.md` and come back here for Step 6 when it's time to ship.
`SKILL.md` indexes both; this file is what you actually follow for a review run. Every `{skill_dir}` below is the resolved absolute path to the
skill directory (see `SKILL.md` §Resolve the skill directory first) — substitute the
real value before you run a command or send a dispatch.

---

## Step 0 — Memory

Check for `.ays/memory.md`. If it exists, read it — it is the project
briefing every agent inherits. If not, create `.ays/` (git-ignored — add it to `.gitignore` if
absent) and seed `memory.md` after Step 1's detection pass.

If a pre-rename `.ayc-skill/`, `.ac-code-skill/` or `.fleet/` directory exists, migrate it into
`.ays/` and remove the old one before anything else reads memory — two
workspaces side by side drift apart and an agent will read the stale one.

`references/memory.md` has the layout, the single-writer rule, the *Agent
learnings* store, the privacy gate, the migration rule, and the template.

---

## Step 1 — Detect stack and scope (or enter greenfield)

**First check whether there is anything to review.** No source beyond a
README/LICENSE, or the user says they want to start from scratch → **greenfield**
(below), not detection.

Otherwise detect the stack language-agnostically from what is actually in the repo.
`references/stack-detection.md` covers signal files, frontend vs. backend, pulling
the *real* test/lint/build/e2e commands out of config, the dependency inventory
(manifests, lockfiles, the ecosystem's update/audit tooling), and scope selection
(working diff vs. whole tree — default to the diff for pre-commit/pre-merge asks).
It also flags **AI/LLM signals**, which decides whether `ai-engineer` runs.

Record verified stack + commands + dependency inventory + whether the repo has AI
features into memory, so no later agent re-derives them.

**On the first run, ask the two pre-review preferences — don't guess them**
(`stack-detection.md` §0b), batched into one short prompt:

- **private/internal or commercial/public** — drives the noindex vs. privacy-policy
  standards, and is passed to every agent as `standards.py --context <value>`.
- **should the fleet own DevOps** — only if a server may be in scope; SSH-key only,
  see the `devops` brief.

Record both in *Project preferences* and honour them thereafter without re-asking.

---

## Step 2 — Select the agents and confirm

Match agents to the repo and the request. Launching all six when three are
relevant burns tokens for no gain (rule 2). State your selection in a line or two
and let the user add or drop before you launch. A one-prompt full run auto-selects
every agent the stack supports.

---

## Step 3 — Review phase (parallel, read-only)

**Snapshot the tree first.** Run `git status --porcelain` and keep the output.
The review agents hold `Write`/`Edit` for the fix phase, so read-only here is
enforced by *verification*, not by an empty tool list: diff the snapshot against
`git status --porcelain` when the phase ends. Any file changed during review is a
hard failure — name the agent, report it, and re-run that agent's review against
the restored state before trusting its findings. Outside a git repo, say that the
check is unavailable and treat the phase as unverified.

Launch every selected review agent **in a single turn** so they run concurrently —
this is the point of the fleet. Prefer the shipped agent definitions
(`ays-frontend`, `ays-backend`, `ays-security`, `ays-tester`, `ays-ai-engineer`); fall
back to a general-purpose subagent with the phase rules stated in the prompt.

**Each agent reviews only the surface it owns.** Overlapping territory is what
makes a fleet cost more than one agent and find less.

### Assembling a dispatch — send what varies, nothing else

**The shipped agent definitions already carry the five rules, the principal-caliber
lens, the role brief, the phase discipline and the output caps.** Re-sending them
is the most expensive mistake available here: identical text, authored into your
context, then copied into six dispatches, paid for twice over. Don't.

A dispatch is five short things:

1. **the task** — what this agent is reviewing or building, in a sentence or two
2. the detected **`{scope}`** and **`{commands}`** (real ones, from Step 1)
3. the resolved **`{skill_dir}`** — substituted, never the literal placeholder
4. the opening instruction:
   `python "{skill_dir}/scripts/recall.py" "<the agent's task>" --root .ays --role <role>`
5. the **context** for its standards (`private|commercial`, `web,api,ai`) — the
   agent runs `standards.py --agent <role> --compact --context <ctx>` itself

Anything deeper — the long-form rules, the report template, the testing-harness
protocol, the rationale behind a standard — the agent **reads for itself** from
`{skill_dir}/references/`, which costs one agent's context instead of yours plus
theirs. Point at the file; never paste it.

**On a host without the shipped agent definitions** (a plain general-purpose
subagent), the brief isn't preloaded, so fall back to the old assembly:
`shared-rules.md` + the role's block from `agent-roles.md` + `report-format.md`'s
output caps + the phase rules, followed by the five items above.

### `tester` runs the product, not just its suite

On any repo with a runnable UI, `tester` brings the app up
(`python "{skill_dir}/scripts/with_server.py" --help`) and drives it through the
**isolated in-app browser** — the `mcp__Claude_Browser__*` tools, which `ays-tester`
and `ays-frontend` carry in their tool lists. *Never* the user's real or paired
Chrome (`mcp__claude-in-chrome__*`). Per primary screen:

- **Both viewports** — render and screenshot at **desktop 1440×900** and **mobile
  375×812**; judge the rendering, not just the DOM.
- **Every clickable element** — enumerate the interactive controls and click them.
  Report dead, misrouted, silently-failing, and keyboard-unreachable ones.
  Destructive controls only against disposable data.
- **Console + network on every action, including page load** — errors and warnings,
  4xx/5xx and never-resolving requests, and the **response bodies** (a `200`
  carrying `{"error": …}` is the failure a status check misses).
- **Evidence or it didn't happen** — screenshots, console dumps and the
  request/response log to `.ays/log/<run-id>/screens/`; every claim cites
  its artefact.

No browser tools available in this host → say so, fall back to the project's own e2e
suite, and label everything visual or flow-based **"unverified (no browser)"**. The
missing browser is itself a finding. Full protocol: `testing-harness.md` §Policy 3b.

### The sweeps that run here

`security` reports outdated/EOL/advisory dependencies alongside its audit;
`frontend`/`backend` report unused/stale dependencies plus dead code, dead files and
dead folders for their side of the tree. *Applying* dependency upgrades is `devops`,
approval-gated.

### Merging — don't staple

Format in `references/report-format.md`. Lead with a verdict and severity counts,
group by severity (not by agent), deduplicate shared root causes, keep `file:line`
and a concrete fix on every line.

- **Before promoting anything to `blocking`, a second agent already in the run must
  independently re-derive it from source.** Unreproduced findings ship as warnings
  labelled "single-agent, unconfirmed" — a blocking finding stops merges and
  deploys, so it carries the highest cost of being wrong.
- **Run variant analysis on every confirmed finding before you write the report.**
  A bug is rarely alone; see `report-format.md` §Variant analysis.
- Run the merged report through
  `python "{skill_dir}/scripts/redact.py" --in report.md --strict` and save it to
  `.ays/log/<run-id>/report.md`; Step 4 delivers it to the user.
- Optionally emit machine-readable findings for CI:
  `python "{skill_dir}/scripts/to_sarif.py" --in report.md --out findings.sarif`.
- Consolidate Memory deltas into `memory.md` through the same privacy gate, and file
  *Improvements* under *Agent learnings*.

### Enhancements

Each agent returns up to **3** forward-looking enhancements (not defects). On a full
run, compile them into the report's *Recommendations & enhancements* section, ranked
by impact ÷ effort, deduped against the memory *Enhancement backlog*, and kept out
of the defect counts. On a **quick diff-check**, tell agents to skip enhancements and
omit the section — there the user wants defects only, not a roadmap.

---

## Step 4 — Deliver the report

**Both places, in full.** Saved at `.ays/log/<run-id>/report.md` **and**
rendered whole into the chat — not a summary behind a file link. For a large
report, lead the chat copy with the verdict and severity counts so the top stays
skimmable, then the full grouped findings below.

Close with the **fix batches** the user can approve (see Step 5), and the result of
the review-phase write check from Step 3 — "no files changed during review" is a
line worth printing, because its absence is a failure.

---

## Step 5 — Fix phase (approval-gated), then re-review

Report first, then fix. Every fix traces to a finding in the merged report.

Offer fixes in **approve-able batches** ("all auto-formatting", "the 3 null-check
bugs", "the 2 security fixes", "remove the 4 confirmed-dead files/deps") rather than
one yes/no. Safe mechanical fixes first; behavioural changes (logic, test
expectations, security semantics, dependency removals/upgrades) need explicit
per-item confirmation.

**Each agent fixes its own findings.** Re-dispatch the owning agent with the exact
list of findings the user approved for it — `frontend` fixes the frontend
findings, `backend` the backend ones, `tester` authors the missing tests,
`ai-engineer` the AI/LLM changes, `security` its own (per-item confirmed, never
batched blind). The agent that raised the finding already holds the file, the
repro and the reasoning, so its fix is better and cheaper than a generic applier
re-deriving all three.

**One agent at a time.** This phase is sequential — never the parallel fan-out
Step 3 uses. Two agents editing a shared tree corrupt it, and no ordering
guarantee survives concurrency. Within an agent, one finding at a time, smallest
change that resolves it, nothing unapproved however obvious. Coverage gaps and
AI/LLM fixes are write actions too, and are gated the same way.

**The verdict is yours, not theirs.** After each agent finishes, *you* re-run the
relevant test, lint or scanner command and report that output. An agent grading
its own fix is the blind spot this design introduces; objective command output is
what closes it.

### Then every owning agent re-reviews its own fixes

Re-dispatch the agents whose findings were fixed — **read-only, in parallel**, scoped
to the fix diff, each carrying the findings it raised. Each returns a verdict per
finding:

- **fixed** — re-derived from current source, confirmed resolved
- **not fixed** — still reproduces (say how)
- **regressed** — the fix introduced a new problem (report at its own severity)

A verdict is a *re-derivation from the current source*, not a re-reading of the
diff. "The patch looks right" is not a verdict.

`tester` re-runs the suites **and** re-exercises the affected screens in the browser
— a UI fix confirmed only by a green unit test is not confirmed. Anything `not
fixed` or `regressed` goes to a second, smaller fix round. **Do not advance to
deploy with a failed verdict outstanding.**

Report the verdict table (`report-format.md` §fix-verification), then consolidate it
into memory — a finding confirmed `fixed` is no longer "present", so reconcile its
status everywhere it appears.

---

## Step 6 — Deploy (approved, with rollback), then verify by re-running

**Server ownership is consent-gated.** Check *Project preferences* →
`devops-consent`. `no` → no server work (in-repo pipeline/IaC review still happens).
`unasked` and a server may be in scope → ask once. On **yes**, take access **by SSH
key, never a password** (host + user + key *path*, verified with `ssh -v`, recorded
as pointers only). See `references/vps-operations.md`.

**Server operations.** `devops` audits **read-only first**
(`python "{skill_dir}/scripts/server_audit.py" --script`, run over SSH, output
captured and triaged with `--parse`) across access, network exposure, patching, TLS,
resources, services, containers, logging and backups — then proposes changes and
performs routine maintenance. Reversible routine operations proceed; anything
destructive, irreversible, or capable of severing access stops and asks. It never
weakens a security control to make something work.

**Deploy.** Per `references/deploy.md`: verify every precondition (security gate,
migration gate, rollback path), deploy via the project's own mechanism, health-check
the running version, and **roll back automatically** if it doesn't come up healthy.
This phase changes state, so it runs alone — never concurrent with the read-only
agents. Consolidate the *Infra & deploy* delta into memory afterwards.

### Post-deploy verification — one re-run to approve the shipped state

A green health check proves the app came up, not that the fixes work in production.
Once the deploy is healthy, run **Steps 1–3 again** against the deployed tree:
re-detect (the deploy may have changed versions or config), re-select the same
agents, re-review — with `tester` exercising the live flows against the **deployed
URL**, not localhost.

Produce `log/<run-id>/post-deploy-report.md` plus a chat copy, with one verdict:
**approved**, **approved with findings** (new non-blocking issues, listed), or **not
approved** (a blocking finding on the deployed build — say plainly whether a
rollback is warranted and let the user decide).

Three guards, because a pipeline that re-runs itself must terminate:

1. **Exactly once per deploy.** Its own output never triggers another pass.
2. **Read-only.** No fixes, no second deploy. New findings are
   reported; fixing them means the user starting a fresh cycle.
3. **Skipped when there is nothing to verify against** — no reachable deployed
   environment, or a deploy that rolled back (report the rollback instead).

---

## Greenfield bootstrap

Empty/near-empty repo + intent to start a project → **interview first, then
scaffold.**

Pool the intake questions from every role (end of `references/agent-roles.md`) and
ask them in **batched, prioritized rounds** so you learn as much as possible up
front and get the first build right: what and for whom, scope vs. non-goals,
frontend/backend shape, data model, auth & compliance, testing bar, deploy target.
Record the answers in memory's *Requirements & product*. Then:

1. Propose a concrete stack + scaffold plan and confirm it. On an **aesthetic**
   brief ("premium minimal", "editorial", "make it feel expensive"), `frontend` runs
   `python "{skill_dir}/scripts/design_system.py" "<brief>" --persist -o .ays`
   to compose a verified design system — pattern, style, colour tokens with
   **measured** WCAG ratios, typography with the correct import, anti-patterns,
   checklist — into `.ays/design-system/MASTER.md`, with `--page <name>`
   overrides inheriting from it. Then apply `references/design-inspiration.md` for
   taste calibration, implemented originally in the project's own tokens and stack
   (learn principles, never clone). Record the direction in memory.
2. On approval, scaffold the project (structure, tooling, CI, a running skeleton)
   and seed `memory.md` with the chosen stack and commands.

From there the normal pipeline applies as the code grows.
