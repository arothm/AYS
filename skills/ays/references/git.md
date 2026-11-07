# Git

Load for any repository work: committing, branching, merging, undoing, pushing,
or setting up a new project. Each rule's "Why" is the reason to follow it; use it
to judge cases the rule does not spell out.

## Repository basics

- `GIT-001` DO push every project to a remote host (e.g., GitHub, GitLab, Bitbucket) from the very start, so there is always an off-machine copy of the code; the remote is a safeguard but not a full backup (issues, wikis, and large files may not be included)
  - Why: A laptop can fail, be stolen or be wiped; with a remote copy the code survives.
- `GIT-002` DO keep all software code, infrastructure-as-code manifests, and documentation under version control, for solo projects as much as for teams
  - Why: Version control makes every change reviewable and reversible, which a solo developer needs as much as a team does.
- `GIT-003` DON'T use manual directory copies, duplicate folders, or ZIP archives as a versioning or backup strategy
  - Why: Copies have no history, no diff and no merge, and soon nobody knows which one is current.
- `GIT-016` DO include a structured, informative README.md in Markdown at the root of every project repository
  - Why: The README is the first thing anyone opens, future you included; it says what the project is and how to run it.

## Committing

- `GIT-004` DO run git status (and git diff) routinely before and after staging to verify what is in the working tree, the index, and HEAD, and always before resolving merge conflicts to identify the conflicting file paths
  - Why: Checking first catches stray files and unintended changes before they enter history, and shows exactly which files conflict.
- `GIT-005` DO write descriptive commit messages in the imperative mood (e.g., "Add login rate limiting") that explain what changed and why
  - Why: The message is how history explains itself; the reason behind a change cannot be recovered from the diff later.
- `GIT-006` DON'T commit generated runtime logs, build output, system binaries, temporary editor files, or dependency folders (e.g., node_modules); list them in .gitignore, and do commit lockfiles (see WEB-024)
  - Why: Generated files bloat the repository, cause merge conflicts and can leak paths or secrets; lockfiles belong in it because they pin exact versions.
- `GIT-007` DON'T combine unrelated changes into one large commit; stage changes deliberately (e.g., git add -p) and commit atomically so each commit can be reviewed and rolled back on its own
  - Why: Small focused commits can each be reviewed, bisected and reverted; one big commit forces all or nothing.
- `GIT-008` DO sign commits with GPG or SSH keys when the repository or team requires it, using the user's own configured keys
  - Why: A signature proves the commit came from you, not from someone who typed your name into their git config.
- `GIT-019` DON'T commit commented-out code, temporary bypasses, or debug override flags (e.g., !important hacks); Git history preserves old code, and an unavoidable workaround should carry a TODO that references a tracking issue
  - Why: Dead code confuses readers and goes stale, bypasses ship by accident, and history already keeps the old version.

## Secrets

- `GIT-009` DON'T store or commit plain-text secrets (API keys, personal access tokens, service credentials, private SSH keys, production certificates, .env files) in any repository, public or private, in workspace configuration files, or in AI prompts, repository instruction files (e.g., CLAUDE.md, copilot-instructions.md), and skill files; use environment variables or a secrets manager, and if a secret is ever committed, revoke and rotate it, because deleting it from history does not undo the exposure
  - Why: Repositories get cloned, forked and leaked, and bots scan public ones within minutes; only revoking the secret removes the risk.

## Safety and recovery

- `GIT-010` DON'T edit or delete files inside the .git folder by hand, and don't run low-level plumbing commands (e.g., update-ref, hash-object) unless you understand their effect on the repository database
  - Why: Hand edits there can corrupt the object database and lose history for good.
- `GIT-011` DON'T treat uncommitted work as safe: untracked and unstaged changes are not stored in Git's object database and cannot be recovered if overwritten, so commit or stash before risky operations (git reset --hard, git clean, rebase) and before switching branches with git switch or git checkout
  - Why: Uncommitted changes exist only as files on disk; once a reset or checkout overwrites them, Git has no copy to restore.
- `GIT-012` DO use git reflog to find and restore commits or branch pointers lost to a bad reset, rebase, or deleted branch; it is local to your machine and its entries expire, so recover promptly, and it is not a substitute for a remote copy
  - Why: The reflog remembers where HEAD and branches pointed, so commits that look lost can come back, but only on this machine and only for a while.
- `GIT-013` DO prefer git revert over git reset when undoing changes that were already published to a shared remote
  - Why: Revert adds a new commit that undoes the change, so everyone else's history stays valid; reset rewrites history they already have.
- `GIT-014` DON'T rebase or otherwise rewrite history (amend, or reset followed by a force push) on public, shared branches that collaborators are building on; rebasing your own unpublished or personal feature branches is fine
  - Why: Rewritten shared history forces everyone to reconcile their copies and can silently drop their work.
- `GIT-017` DON'T force push (git push --force) to shared or protected branches; on your own feature branches use --force-with-lease instead of plain --force, and use git revert to undo changes on shared branches
  - Why: A plain force push overwrites whatever is on the remote, including commits others pushed; --force-with-lease refuses when the remote has moved.

## Branching and collaboration

- `GIT-015` DO fetch the latest remote changes before starting new work (git fetch, then merge or fast-forward deliberately; git pull --ff-only is a safe default) so your local context includes the latest team commits
  - Why: Starting from stale code leads to conflicts and duplicated work, and --ff-only refuses to create surprise merge commits.
- `GIT-018` DO isolate experimental code, bug fixes, and feature work in dedicated branches, rather than working directly on main or master during multi-day features, and keep the main branch in a releasable state
  - Why: Branches keep unfinished work away from main, so main can always be released and a failed experiment costs nothing.
- `GIT-020` DO run parallel agent or multi-session work in separate Git worktrees (git worktree add), never in one shared working directory, so sessions cannot overwrite each other's changes
  - Why: Each worktree has its own files, so parallel sessions cannot overwrite each other's edits.
