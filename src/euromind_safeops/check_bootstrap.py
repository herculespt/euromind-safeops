"""Private gated launcher for existing fixed checks; not an approval command."""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading


def _fixed(command: list[str]) -> None:
    from .execution import CHECKS
    from .target_runner import TARGET_COMMAND
    if not command or command[0] != sys.executable:
        raise ValueError("Invalid interpreter")
    args = command[1:]
    if args in CHECKS.values():
        return
    if (args[:len(TARGET_COMMAND)] == TARGET_COMMAND and len(args) > len(TARGET_COMMAND) + 1 and
            args[len(TARGET_COMMAND)] in CHECKS):
        return  # target_runner repeats full directory validation before importing code.
    raise ValueError("Unsupported fixed check")


def main(argv: list[str] | None = None) -> int:
    values = sys.argv[1:] if argv is None else argv
    if len(values) < 5:
        return 2
    destination, token, parent_group, *command = values
    try:
        _fixed(command)
        if len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
            return 2
        parent_group = int(parent_group)
        if os.name == "posix" and (os.getpgrp() != os.getpid() or parent_group <= 0):
            return 2
        # EOF here cannot launch a worker. Only the owning parent supplies G.
        if sys.stdin.buffer.read(1) != b"G":
            return 2
        released = threading.Event()

        def control():
            try:
                command = sys.stdin.buffer.read(1)
            except (OSError, ValueError):
                command = b""
            if command == b"X":
                released.set()
                return
            if os.name == "posix":
                try:
                    os.killpg(os.getpid(), signal.SIGKILL)
                except OSError:
                    pass
            os._exit(2)

        threading.Thread(target=control, daemon=True).start()
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, close_fds=True)
        code = child.wait()
        if os.name == "posix":
            # Keep this PID allocated, but leave the owned group observable as empty.
            os.setpgid(0, parent_group)
        raw = json.dumps({"schema": 1, "pid": os.getpid(), "token": token, "exit_code": code}).encode() + b"\n"
        prepared = Path(destination + ".tmp")
        fd = os.open(prepared, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
        os.replace(prepared, destination)
        released.wait()
        return 0
    except (OSError, ValueError, TypeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
