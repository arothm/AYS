#!/usr/bin/env python3
"""Start one or more servers, wait until their ports are accepting connections,
run a target command, then shut the servers down. Standard library only — no
external dependencies.

This is a black-box helper: run it with --help, then invoke it. You should not
need to read this source. It exists so testing agents don't reinvent server
lifecycle management (and don't clutter their context window) every run.

USAGE
    python with_server.py --server "<cmd>" --port <N> [more --server/--port] \
        -- <command to run once servers are up>

    Each --server must be followed (in order) by its --port. The command after
    the `--` separator runs once every port is reachable; when it exits (or on
    Ctrl-C), every server is terminated.

EXAMPLES
    # Single dev server, then run an automation/test command
    python with_server.py --server "npm run dev" --port 5173 -- pytest e2e/

    # Backend + frontend together
    python with_server.py \
        --server "cd backend && python server.py" --port 3000 \
        --server "cd frontend && npm run dev" --port 5173 \
        -- python run_flows.py

    # Just wait for readiness then exit 0 (smoke check the port opens)
    python with_server.py --server "npm run preview" --port 4173 -- true

OPTIONS
    --server CMD     Shell command that starts a server (repeatable).
    --port N         Port to wait on for the preceding --server (repeatable).
    --host HOST      Host to probe (default 127.0.0.1).
    --timeout SEC    Max seconds to wait per port (default 60).
    --                Everything after this is the command to run.

EXIT CODES
    Propagates the target command's exit code. Returns 1 if a server fails to
    become ready within the timeout (and reports which one).
"""
import argparse
import os
import socket
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Windows consoles default to cp1252 and would mangle the em dashes and arrows
    # this prints. Matches the guard the other helpers already carry.
except Exception:
    pass

IS_WINDOWS = os.name == "nt"


def spawn(cmd):
    """Start a shell command in its own process group / session.

    `shell=True` puts a shell between us and the server, so the handle we hold is
    the shell's, not the server's. Killing only that handle leaves the server
    running and its port bound - and we would print "servers stopped" while it is
    still listening. Grouping the whole tree up front is what makes stop() able to
    take all of it down.
    """
    if IS_WINDOWS:
        return subprocess.Popen(
            cmd, shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return subprocess.Popen(cmd, shell=True, start_new_session=True)


def stop(proc, grace=5.0):
    """Terminate a server and every process it spawned. Best effort, never raises."""
    if proc.poll() is not None:
        return
    if IS_WINDOWS:
        # terminate() ends the cmd.exe wrapper only. taskkill /T walks the tree.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), 15)
        except Exception:
            proc.terminate()
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        if not IS_WINDOWS:
            try:
                os.killpg(os.getpgid(proc.pid), 9)
            except Exception:
                proc.kill()
        else:
            proc.kill()


def port_is_open(host, port):
    """True if something still accepts connections on (host, port)."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_port(host, port, timeout):
    """Return True once (host, port) accepts a TCP connection, else False."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def parse_args(argv):
    if "--" in argv:
        sep = argv.index("--")
        head, target = argv[:sep], argv[sep + 1:]
    else:
        head, target = argv, []

    p = argparse.ArgumentParser(add_help=True, description="Run servers around a command.")
    p.add_argument("--server", action="append", default=[], metavar="CMD")
    p.add_argument("--port", action="append", default=[], type=int, metavar="N")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args(head)
    return args, target


def main(argv):
    args, target = parse_args(argv)

    if len(args.server) != len(args.port):
        print("error: each --server needs exactly one matching --port", file=sys.stderr)
        return 2
    if not target:
        print("error: no target command given after `--`", file=sys.stderr)
        return 2

    procs = []
    try:
        # Launch every server.
        for cmd, port in zip(args.server, args.port):
            print(f"[with_server] starting: {cmd}  (port {port})", file=sys.stderr)
            procs.append(spawn(cmd))

        # Wait for each port to open.
        for cmd, port in zip(args.server, args.port):
            if not wait_for_port(args.host, port, args.timeout):
                print(f"[with_server] TIMEOUT: {args.host}:{port} not ready "
                      f"in {args.timeout}s (server: {cmd})", file=sys.stderr)
                return 1
            print(f"[with_server] ready: {args.host}:{port}", file=sys.stderr)

        # Run the target command with servers up.
        print(f"[with_server] running: {' '.join(target)}", file=sys.stderr)
        return subprocess.call(target)
    finally:
        for proc in procs:
            stop(proc)
        # Verify rather than assert. A port still bound after teardown is a leak
        # that would make the NEXT run fail to start its server, with an error
        # pointing at that run instead of at this one.
        leaked = [p for p in args.port if port_is_open(args.host, p)]
        if leaked:
            print("[with_server] WARNING: still listening after teardown: "
                  + ", ".join(f"{args.host}:{p}" for p in leaked)
                  + " - a leftover process is holding the port", file=sys.stderr)
        else:
            print("[with_server] servers stopped", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
