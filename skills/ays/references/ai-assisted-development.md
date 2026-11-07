# AI-assisted development

How Claude approaches larger changes and generated output. Load for any change
bigger than a one-line fix, any refactor or migration, and any session that
commits, deletes, or runs commands. SKILL.md's working method is built from
these rules. Each rule's "Why" is the reason to follow it; use it to judge cases
the rule does not spell out.

## Scope and planning

- `AID-009` DO, for non-trivial features, define the scope, functional boundaries, edge cases, and acceptance criteria in a short spec or plan before writing code; ask the user to clarify anything under-specified instead of guessing, and when the project keeps a plan document (e.g., PRD.md), wait for the user's approval of the plan before implementing
  - Why: Agreeing on scope and "done" first prevents building the wrong thing; a guess at an unclear requirement can waste the whole implementation.
- `AID-010` DO leave decisions about architecture, security protocols, compliance, and UX to the user: present the options with their trade-offs (using the ask-user-question tool where available) instead of choosing silently
  - Why: These choices carry long-term costs only the owner can weigh, and a silent choice hides trade-offs they might have decided differently.
- `AID-007` DO break large documentation or analysis tasks on big codebases into modules, starting with core dependencies before minor utilities, so each piece fits in context and stays accurate
  - Why: Too much at once overflows the context and accuracy drops; core modules first give every later piece the right foundation.

## Changing existing code

- `AID-001` DON'T rewrite working legacy code to adopt new frameworks, compilers, or paradigms unless asked, and verify that dependencies are compatible before proposing any migration
  - Why: Working code holds years of fixes and edge cases that a rewrite loses, and an unchecked migration breaks things that worked.
- `AID-002` DON'T try to refactor a whole multi-file repository in one pass; work in small, verified increments (one module or concern at a time), run the tests and linter after each change, and commit each step
  - Why: Small steps keep every change reviewable, and when something breaks, the cause is the one step just taken.
- `AID-003` DO understand the code and have passing tests in place (write characterization tests if none exist) before making structural changes, re-run them after every step to confirm business logic is unchanged, and don't start a large legacy migration without a verified test suite
  - Why: Tests pin down what the code does today, so they show immediately when a structural change altered it.
- `AID-019` DO, when asked to migrate legacy code to another language or architecture, translate its behavior into idiomatic structures of the target, guided by tests that pin down the existing behavior, rather than a literal line-by-line transliteration
  - Why: A literal translation carries the old language's habits into one where they are wrong; tests prove the behavior survived the move.

## Verifying work

- `AID-004` DON'T treat a clean static review (linters, type checks, or AI review comments) as proof that code works; run the tests and exercise the runtime behavior before approving, merging, or declaring work done
  - Why: Linters and reviews check form, not behavior; only running the code proves it works.
- `AID-005` DO review and test AI-generated front-end code, including your own, before shipping: check CSS scoping and global overrides, responsive behavior across viewports, semantic HTML and ARIA, and WCAG 2.2 AA accessibility
  - Why: Generated front-end code often leaks global CSS, breaks on mobile and skips accessibility, and only checking reveals it.
- `AID-006` DON'T present generated documentation of complex proprietary business logic, specialized algorithms, or safety-critical boundaries as verified; flag it for review by an engineer who knows the domain, and check that generated comments explain why the code is written that way, not just what it does (see WEB-275)
  - Why: Generated explanations of complex logic can be confidently wrong, and labeled as verified they mislead whoever relies on them.
- `AID-008` DON'T accept generated code on intuition alone ("vibe coding"): read and understand it, run it and its tests, commit regularly so any step can be rolled back, and never deploy it to production without passing the automated CI security gates (see OPS-008)
  - Why: Code nobody understands cannot be maintained or trusted, frequent commits make every step reversible, and CI gates catch the security flaws a quick read misses.
- `AID-020` DO attach an AI diligence statement, signed by the responsible person, to production code, financial audits and regulatory submissions produced with AI agents, stating which tools were used, for what, and how the output was verified
  - Why: An agent cannot take responsibility for its output, so a named person must state how it was checked, which gives reviewers and auditors a record to rely on.
- `AID-011` DO include unit tests and the necessary documentation with new production code, and run them
  - Why: Untested code has no proof it works and no guard against later regressions, and undocumented code is hard for anyone else to use.

## Safety and permissions

- `AID-012` DO ask for approval before destructive or hard-to-reverse actions (deleting files, rm -rf, dropping databases, force pushes), unfamiliar network calls, and committing or pushing unless the user has authorized them; never run elevated (sudo/administrator) commands without explicit approval, and use the agent's permission settings (allow and deny rules) to enforce these boundaries
  - Why: These actions cannot be undone, so asking first keeps the user in control of anything that could destroy work.
- `AID-013` DO match command syntax to the user's shell and OS (bash/zsh, PowerShell, CMD); for example, && chaining works in bash, CMD, and PowerShell 7+ but not in Windows PowerShell 5.1, and irm and other aliases exist only in PowerShell
  - Why: A command in the wrong shell's syntax fails, or worse, does something different from what was intended.
- `AID-014` DON'T send secrets, credentials, or proprietary source code to third-party services, including other AI APIs and consumer AI chat apps, unless the project's data-privacy terms allow it; use enterprise plans or APIs whose terms isolate your data, and scrub secrets first
  - Why: Anything sent to a third party leaves your control and may be logged, kept or used for training, and consumer chat apps usually give the weakest guarantees.
- `AID-021` DON'T give agentic desktop tools (e.g., Claude Code, Claude Cowork) access beyond the folders a task needs; scope them to specific project directories and enforce it with their permission settings (see AID-012)
  - Why: An agent can read or change anything it can reach, so a mistake or an injected instruction is limited only by the folders it was given.
- `AID-022` DON'T run AI tools or extensions that hold company access on unmanaged devices; require SSO, role-based access limits, and routing through the company's API gateway
  - Why: An unmanaged device is outside the company's security controls, so access held there can be stolen or misused without anyone seeing it.
- `AID-017` DON'T run autonomous or looping agent workflows without a passing-test exit condition, a maximum iteration count, and a token or time budget
  - Why: Without a clear stop condition and limits, a looping agent can run indefinitely and spend without bound.

## Project context

- `AID-015` DO keep the project's instruction file current (CLAUDE.md at the repo root or .claude/CLAUDE.md; .github/copilot-instructions.md for Copilot) with the build, test, lint, and type-check commands and the project's conventions, and never put secrets in it
  - Why: Every session starts with no memory of the project; the instruction file gives it the right commands and conventions instead of guesses.
- `AID-016` DO keep sessions focused: start a fresh session or compact the context between unrelated tasks, and keep durable project knowledge in the instruction file instead of the conversation, because answer quality can degrade as the context window fills
  - Why: A crowded context mixes unrelated details into answers, while knowledge kept in a file survives every session.
- `AID-018` DO define project-specific MCP servers in the project-scoped .mcp.json at the repo root (not in user-level configuration), so they are shared through version control, and reference credentials through environment variables instead of writing them into the file
  - Why: The project file travels with the repository, so every collaborator gets the same servers, and no credentials get committed.
