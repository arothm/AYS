#!/usr/bin/env python3
"""Emit a strictly READ-ONLY server audit, and triage the captured output.
Standard library only — installs nothing.

**This script never connects to anything and never runs a remote command.** It
generates an inspection script for a human or the `devops` agent to run over SSH,
then parses what came back. That is deliberate: a tool that cannot reach a server
cannot break one, and every command it emits is inspection-only — no restarts, no
edits, no package operations. Mutating a box is the agent's job, under the
approval discipline in `references/vps-operations.md`, never this script's.

USAGE
    python server_audit.py --script > audit.sh        # generate the read-only audit
    ssh host 'bash -s' < audit.sh > captured.txt      # you run it; this tool does not
    python server_audit.py --parse captured.txt       # triage what came back

    python server_audit.py --plan                     # human-readable command plan
    python server_audit.py --script --only security,network
    python server_audit.py --list                     # audit categories
"""
from __future__ import annotations
import argparse, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MARK = "===AYC-AUDIT==="

# Every command here MUST be read-only. Anything that changes state is a bug.
AUDIT = {
    "identity": [
        ("sshd effective config", "sshd -T 2>/dev/null | grep -Ei 'permitrootlogin|passwordauthentication|pubkeyauthentication|port|permitemptypasswords|x11forwarding' || grep -Ev '^\\s*#|^\\s*$' /etc/ssh/sshd_config"),
        ("accounts with a login shell", "getent passwd | awk -F: '$7 !~ /(nologin|false)$/ {print $1\":\"$3\":\"$7}'"),
        ("sudoers and NOPASSWD grants", "grep -rEh '^[^#].*ALL' /etc/sudoers /etc/sudoers.d/ 2>/dev/null"),
        ("authorized_keys per user", "for h in /root /home/*; do [ -f \"$h/.ssh/authorized_keys\" ] && echo \"-- $h\" && ssh-keygen -lf \"$h/.ssh/authorized_keys\" 2>/dev/null; done"),
        ("last logins", "last -n 15 2>/dev/null | head -20"),
    ],
    "network": [
        ("listening sockets", "ss -tulpn 2>/dev/null || netstat -tulpn 2>/dev/null"),
        ("ufw status", "ufw status verbose 2>/dev/null"),
        ("nftables/iptables rules", "nft list ruleset 2>/dev/null | head -60 || iptables -S 2>/dev/null | head -60"),
        ("fail2ban", "fail2ban-client status 2>/dev/null"),
    ],
    "patching": [
        ("os release", "cat /etc/os-release 2>/dev/null | head -4"),
        ("pending updates", "(apt list --upgradable 2>/dev/null | tail -n +2 | head -40) || (dnf check-update 2>/dev/null | head -40)"),
        ("unattended-upgrades", "systemctl is-enabled unattended-upgrades 2>/dev/null; cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null"),
        ("running vs installed kernel", "echo \"running: $(uname -r)\"; ls -1t /boot/vmlinuz-* 2>/dev/null | head -3"),
        ("reboot required", "test -f /var/run/reboot-required && cat /var/run/reboot-required*"),
    ],
    "tls": [
        ("certificate expiry", "for c in /etc/letsencrypt/live/*/fullchain.pem; do [ -f \"$c\" ] && echo \"-- $c\" && openssl x509 -enddate -noout -in \"$c\"; done 2>/dev/null"),
        ("renewal automation", "systemctl list-timers 2>/dev/null | grep -Ei 'certbot|acme|renew'"),
    ],
    "resources": [
        ("disk usage", "df -hP | grep -v tmpfs"),
        ("inode usage", "df -iP | grep -v tmpfs"),
        ("memory and swap", "free -h"),
        ("load vs cores", "uptime; nproc"),
        ("largest directories", "du -xh --max-depth=2 / 2>/dev/null | sort -rh | head -15"),
    ],
    "services": [
        ("failed units", "systemctl --failed --no-legend 2>/dev/null"),
        ("enabled at boot", "systemctl list-unit-files --state=enabled --no-legend 2>/dev/null | head -40"),
        ("restart loops", "systemctl list-units --type=service --no-legend 2>/dev/null | head -40"),
        ("cron and timers", "systemctl list-timers --no-legend 2>/dev/null | head -20; ls -1 /etc/cron.d/ 2>/dev/null; crontab -l 2>/dev/null"),
        ("time sync", "timedatectl 2>/dev/null | head -8"),
    ],
    "containers": [
        ("running containers", "docker ps --format '{{.Names}}\\t{{.Status}}\\t{{.Image}}\\t{{.Ports}}' 2>/dev/null"),
        ("restart counts", "docker ps -a --format '{{.Names}}' 2>/dev/null | while read c; do echo \"$c $(docker inspect -f '{{.RestartCount}} {{.State.Status}}' \"$c\" 2>/dev/null)\"; done"),
        ("containers running as root", "docker ps -q 2>/dev/null | while read i; do echo \"$(docker inspect -f '{{.Name}} user=[{{.Config.User}}]' \"$i\" 2>/dev/null)\"; done"),
        ("reclaimable space", "docker system df 2>/dev/null"),
        ("image ages", "docker images --format '{{.Repository}}:{{.Tag}}\\t{{.CreatedSince}}' 2>/dev/null | head -20"),
    ],
    "logging": [
        ("logrotate config present", "ls -1 /etc/logrotate.d/ 2>/dev/null | head -20"),
        ("largest log files", "find /var/log -type f -size +50M -exec ls -lh {} + 2>/dev/null | head -15"),
        ("journald limits", "grep -Ev '^\\s*#|^\\s*$' /etc/systemd/journald.conf 2>/dev/null; journalctl --disk-usage 2>/dev/null"),
        ("recent errors", "journalctl -p err -n 30 --no-pager 2>/dev/null"),
    ],
    "backups": [
        ("backup jobs", "systemctl list-timers --no-legend 2>/dev/null | grep -Ei 'backup|dump|snapshot'; grep -rils 'backup' /etc/cron* 2>/dev/null | head"),
        ("recent backup artefacts", "find / -xdev -type f \\( -name '*.dump' -o -name '*backup*.tar.gz' -o -name '*.sql.gz' \\) -mtime -14 -printf '%TY-%Tm-%Td %s %p\\n' 2>/dev/null | sort -r | head -15"),
    ],
}

# Pattern -> (severity, what it means). Triage only; the agent confirms.
RED_FLAGS = [
    (r"(?im)^permitrootlogin\s+yes", "blocking", "SSH permits direct root login"),
    (r"(?im)^passwordauthentication\s+yes", "blocking", "SSH permits password authentication (brute-forceable)"),
    (r"(?im)^permitemptypasswords\s+yes", "blocking", "SSH permits empty passwords"),
    (r"(?im)NOPASSWD:\s*ALL", "warning", "passwordless sudo to ALL commands"),
    (r"(?im)Status:\s*inactive", "blocking", "firewall (ufw) is inactive"),
    (r"(?im)\b0\.0\.0\.0:(?:3306|5432|6379|27017|9200|11211|5672)\b", "blocking",
     "a database/cache port is bound to all interfaces"),
    (r"(?im)^\s*\*\s+soft", "nit", "check ulimits"),
    (r"(?im)reboot[- ]required", "warning", "a reboot is pending (kernel/library patches are not live until then)"),
    (r"(?im)\b(9[0-9]|100)%\s", "blocking", "a filesystem is at/over 90% (disk or inode)"),
    (r"(?im)\b(8[5-9])%\s", "warning", "a filesystem is over 85%"),
    (r"(?im)\bfailed\b.*\bunits?\b|●.*failed", "warning", "one or more systemd units are failed"),
    (r"(?im)restartcount[^0-9]*[1-9]|\s[1-9][0-9]*\srunning\b", "warning", "a container has restarted repeatedly"),
    (r"(?im)user=\[\]", "warning", "a container declares no user (likely running as root)"),
    (r"(?im)NTP service:\s*inactive|System clock synchronized:\s*no", "warning", "time is not synchronised"),
    (r"(?im)notAfter=.*(19|20)[0-9]{2}", "info", "certificate expiry present — check the date"),
]


def build_script(cats):
    lines = ["#!/usr/bin/env bash",
             "# READ-ONLY audit generated by ayc-skill server_audit.py.",
             "# It inspects only: no restarts, no edits, no package changes.",
             "set -u", ""]
    for cat in cats:
        for title, cmd in AUDIT[cat]:
            lines.append(f'echo "{MARK} {cat} :: {title}"')
            lines.append(f"{{ {cmd} ; }} 2>&1 | head -80")
            lines.append("")
    lines.append(f'echo "{MARK} done"')
    return "\n".join(lines)


def parse(text):
    blocks, cur, buf = [], None, []
    for line in text.splitlines():
        if line.startswith(MARK):
            if cur:
                blocks.append((cur, "\n".join(buf)))
            label = line[len(MARK):].strip()
            cur, buf = (None if label == "done" else label), []
        else:
            buf.append(line)
    if cur:
        blocks.append((cur, "\n".join(buf)))

    findings, empty = [], []
    for label, body in blocks:
        if not body.strip():
            empty.append(label)
            continue
        for rx, sev, meaning in RED_FLAGS:
            m = re.search(rx, body)
            if m:
                sample = m.group(0).strip()[:70]
                findings.append((sev, label, meaning, sample))

    order = {"blocking": 0, "warning": 1, "nit": 2, "info": 3}
    findings.sort(key=lambda f: order.get(f[0], 9))
    return blocks, findings, empty


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a read-only server audit and triage its output. Never connects anywhere.")
    ap.add_argument("--script", action="store_true", help="emit the read-only bash audit")
    ap.add_argument("--plan", action="store_true", help="human-readable command plan")
    ap.add_argument("--parse", help="triage a captured output file")
    ap.add_argument("--only", help="comma list of categories")
    ap.add_argument("--list", action="store_true", help="list categories")
    a = ap.parse_args(argv)

    cats = [c.strip() for c in a.only.split(",")] if a.only else list(AUDIT)
    bad = [c for c in cats if c not in AUDIT]
    if bad:
        ap.error(f"unknown categories: {', '.join(bad)}. Available: {', '.join(AUDIT)}")

    if a.list:
        for c in AUDIT:
            print(f"{c:<12} {len(AUDIT[c])} checks")
        return 0
    if a.plan:
        for c in cats:
            print(f"\n## {c}")
            for title, cmd in AUDIT[c]:
                print(f"  - {title}\n      {cmd}")
        return 0
    if a.script:
        print(build_script(cats))
        return 0
    if a.parse:
        with open(a.parse, encoding="utf-8", errors="replace") as f:
            blocks, findings, empty = parse(f.read())
        print(f"Parsed {len(blocks)} audit section(s).\n")
        if findings:
            print("TRIAGE (pattern-matched — the agent must confirm each against the raw output):")
            for sev, label, meaning, sample in findings:
                print(f"  [{sev.upper():<8}] {label}\n             {meaning}\n             matched: {sample}")
        else:
            print("No red-flag patterns matched.")
        if empty:
            print(f"\nNo output (tool absent, or nothing to report) — NOT the same as 'passed':")
            for e in empty:
                print("  - " + e)
        print("\nTriage is a starting point, not a verdict. Confirm every item against the raw\n"
              "capture before reporting it, and treat an empty section as unknown, not clean.")
        return 0

    ap.error("choose --script, --plan, --parse or --list")


if __name__ == "__main__":
    sys.exit(main())
