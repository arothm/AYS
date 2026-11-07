# Agent Skills

Load only when authoring, reviewing or installing Agent Skills — including
changes to AYS itself. Each rule's "Why" is the reason to follow it; use it to
judge cases the rule does not spell out.

- `SKL-001` DO keep always-loaded context (system prompts, CLAUDE.md) lean, and move specialized procedures, operational scripts, API schemas, and long documents into skills or reference files that load on demand
  - Why: Always-loaded text costs tokens on every request, while on-demand files leave the context free for the task at hand.
- `SKL-002` DO write precise, high-signal skill descriptions (what the skill does and when to use it), because the description is what the agent uses to decide whether to load the skill
  - Why: The agent decides from the description alone, so a vague one loads the skill at the wrong time or never.
- `SKL-003` DON'T duplicate the same procedural instructions across several skills, which creates context collisions and ambiguous skill selection
  - Why: Duplicates leave the agent unsure which skill applies, and the copies drift apart when only one is updated.
- `SKL-004` DON'T mix project-specific repository guidelines (CLAUDE.md) with portable, cross-project domain knowledge (skills); keep each in its own place
  - Why: Project rules only fit one repository, while a skill must work in any repository.
- `SKL-005` DO resolve file paths inside skill scripts reliably, relative to the script's own location (e.g., __file__ in Python or import.meta.dirname in Node) or through documented variables, never relative to the current working directory, and avoid hardcoding machine-specific absolute paths
  - Why: While a skill runs, the working directory is the user's project, so paths relative to it point at the wrong place.
- `SKL-006` DO keep the root SKILL.md concise and move detailed schemas, API documentation, and long guidelines into separate files in a references/ directory
  - Why: A short SKILL.md loads fast, and the details load only when a task needs them.
- `SKL-007` DO put deterministic, repeatable logic in standalone scripts in a scripts/ directory that the skill runs, and keep SKILL.md for instructions
  - Why: A script gives the same exact result every time and costs far fewer tokens than having the model work it out.
- `SKL-008` DO test a new skill by confirming that the host discovers it and loads it on demand for the intended requests (e.g., with your IDE's chat debug view or the agent's logs), not up front or never
  - Why: A skill that never loads is worthless, and one that always loads wastes context on every request.
- `SKL-009` DO run skills that execute scripts inside an isolated sandbox (container or virtual machine) and review the code of any third-party skill before installing it, because a skill can run arbitrary code
  - Why: A skill's scripts run with your permissions, so reviewing and sandboxing them limits what a malicious or buggy one can do.
