# VPS operations — the `devops` agent on a live server

`deploy.md` covers shipping code. This covers **owning the machine**: auditing it,
hardening it, operating it, and responding when it breaks — at the level a
principal SRE would.

This is the most dangerous capability in the fleet. Everything else reviews text;
this runs commands as root on a production box, where a wrong keystroke is not
revertible by editing a file. The discipline below is not ceremony — it is what
makes the authority safe enough to grant.

## The prime directive: audit read-only, change deliberately

**Every session on a server starts read-only.** Run
`python {skill_dir}/scripts/server_audit.py --script` and execute that; it emits *only*
inspection commands and is the safe way to learn the machine's real state. Form a
picture, report it, and only then propose changes.

Never explore by mutating. `systemctl restart` is not a diagnostic.

## Consent and access (first run)

Server ownership is opt-in and asked **once**. If memory has no server and no
`devops-consent` decision recorded in *Project preferences*:

- **Ask the user** whether they want the fleet to own DevOps/server operations. If
  **no**, record that and don't dispatch `devops` for server work again (in-repo
  pipeline/IaC review still happens). If **yes**, continue.
- **Access is by SSH key, never a password.** Ask for the host, the user, and the
  **path to an SSH key**, then connect verbosely (`ssh -v user@host`) to confirm
  reachability and record what worked. If the user only has a password, walk them
  through installing a key (`ssh-copy-id`) — do **not** accept or store a password.
  A stored root password would violate the fleet's own `secrets-in-env` standard
  and is exactly what the privacy gate BLOCKs.
- **Persist pointers, not secrets.** Into memory's *Infra & deploy*: host, user,
  and the key's *path on this machine*. Never the key material, never a password.

## Access and evidence

- **Credentials come from the environment, never from you.** SSH key path, host
  and user come from memory's *Infra & deploy* section or the user. You never
  generate, copy, print, or persist a key. Secrets go through the privacy gate
  (`redact.py`) before any of this reaches memory or a report — record *where* a
  credential lives, never its value.
- **Capture evidence.** Save raw command output to
  `.ayc-skill/log/<run-id>/server/`. A server claim with no captured output is
  an assertion, and rule 1 forbids those.
- **State the host and environment out loud** before acting. "Running on
  prod-web-01 as root" — the failure mode where someone operates on the wrong box
  is common and expensive.

## The audit surface

What a principal actually checks. `server_audit.py` covers each read-only.

**Identity & access**
SSH config (`PermitRootLogin`, `PasswordAuthentication`, key algorithms, port),
authorized_keys per user (whose keys are these, and should they still be there?),
sudoers and NOPASSWD grants, accounts with shells and their last login, stale
accounts from departed people.

**Network exposure**
Listening sockets vs what *should* be listening — a database bound to `0.0.0.0`
is the single most common serious finding. Firewall state and rules (ufw /
nftables / iptables / cloud security group), fail2ban or equivalent, and whether
the firewall actually survives reboot.

**Patch & vulnerability posture**
Available security updates, unattended-upgrades enabled and *working*, kernel
version vs installed (a patched kernel not rebooted into is not patched),
`/var/run/reboot-required`, EOL distro or runtime versions.

**TLS & edge**
Certificate expiry and renewal automation *proven* (not just installed), protocol
and cipher configuration, HSTS, OCSP stapling, HTTP/3 availability.

**Resources & capacity**
Disk and **inode** usage per filesystem (inode exhaustion presents as a baffling
"no space" with free space), memory and swap pressure, load vs core count, the
largest directories, and growth trend — a disk at 78% is only interesting
alongside how fast it got there.

**Services & processes**
systemd units: failed, enabled-but-dead, and enabled-at-boot vs currently running
(a service that works now but won't survive reboot is a latent outage). Restart
loops. Resource-hungry processes. Cron and timers — including jobs that fail
silently because nobody reads the mail.

**Containers (where used)**
Container health and restart counts, image ages and provenance, dangling
images/volumes eating disk, containers running as root, published ports vs
intended, and whether compose files on the box match the repo.

**Logging & observability**
Log rotation configured and effective (unrotated logs are a classic disk-filler),
journald limits, whether errors reach anywhere a human looks, time sync (NTP —
skewed clocks corrupt correlation and break TLS/tokens).

**Backups — the one people fake**
Do backups exist, are they *current*, are they **off-box**, and has a restore
been *tested*? An untested backup is a hypothesis. Report an untested backup as a
finding regardless of how healthy the backup job looks.

## Routine maintenance

Owning the machine means keeping it healthy over time, not only auditing it once.
As approved ongoing operations (each still under the change discipline below):

- **Patch and update.** Apply routine low-risk OS and security updates and tool
  upgrades. A kernel upgrade, or anything that needs a reboot, is **surfaced and
  scheduled with the user — never auto-applied**; a patched-but-not-rebooted
  kernel is not patched.
- **Tune for performance from the resource picture.** Turn what the audit found
  into concrete recommendations: a service to right-size, a connection pool to
  bound, swap to add, a hot process to move or cap, a filesystem whose *growth
  rate* (not just current %) will exhaust it. Name the expected effect and the
  cost, ADR-style — don't tune blind.
- **Keep the hygiene jobs working.** Confirm log rotation, cert renewal,
  unattended-upgrades and backups are still *running and effective*, not merely
  installed. The most common outage is a boring job that silently stopped.

## Change discipline

Once the audit is reported and changes are approved:

1. **Know the undo before the do.** Capture current state (config file copy,
   package version, image tag, firewall rules) and state the exact rollback
   command *before* running the change. If you cannot articulate the undo, the
   change is not ready.
2. **One change at a time, verified.** Apply, verify the intended effect, verify
   nothing else broke (health check + the service's own logs), then move on.
   Batched changes make attribution impossible when something breaks.
3. **Prefer durable over ad-hoc.** Edit the config file and reload; don't set a
   runtime value that evaporates on reboot. If the project has config management,
   change it there — a server that drifts from its declared state is a future
   outage.
4. **Never lock yourself out.** Firewall and SSH changes are the classic
   self-inflicted outage: keep the current session open, apply, verify from a
   *second* connection, and only then trust it. Prefer timed auto-revert
   (`ufw` rules with a scheduled rollback, or `sshd -T` validation) for anything
   touching remote access.
5. **Never weaken a control to make something work.** Disabling SELinux/AppArmor,
   opening a firewall to `0.0.0.0/0`, turning on `PasswordAuthentication`, or
   `chmod 777` to fix a permission error are not fixes; they are new findings.
   If that's the only way forward, stop and report.

## What always stops and asks

Full authority for reversible routine operations. These require explicit human
approval every time, regardless:

- Anything that **destroys or overwrites data** — dropping databases, `rm -rf` on
  data paths, restoring over live data, formatting or resizing volumes.
- **Rebooting or stopping** a live service, including kernel upgrades that require
  one.
- **User, key, or permission changes** that could remove someone's access.
- **Firewall or SSH changes** that could sever remote access.
- **Anything irreversible without a proven rollback**, including migrations run
  outside the deploy pipeline.
- **Rotating credentials** — coordinate, because everything holding the old one
  breaks at once.

## Incidents

When the server is actively broken, the order is: **stabilise, then diagnose,
then fix.**

- Capture evidence *before* restarting anything — logs, `dmesg`, resource state,
  the failing unit's status. A restart destroys the evidence and you get one shot
  at it.
- Prefer the smallest action that restores service, and say plainly that it is
  mitigation, not a fix.
- Timeline everything: what you saw, what you ran, what changed. That timeline is
  the postmortem.
- Afterwards, write the root cause and the systemic fix into memory's *Infra &
  deploy* section — an incident that isn't recorded gets repeated.

## Back to memory

Every server session ends with a Memory delta for *Infra & deploy*: verified host
facts, what was audited and found, what changed and its rollback, and any pending
maintenance (patches, cert expiry, reboot-required). Locations and methods only —
**never secret values**. This is what lets the next run skip rediscovery and
resume operating the machine instead of relearning it.
