"""Bounded fixed-check lifecycle with owned native groups/jobs and output tails."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time

from .core import SafeOpsError, decode_json_object
from .locking import RetainRunMarker
from .windows_job import Job

TAIL_BYTES = 65_536
CLEANUP_SECONDS = 3.0
TERM_GRACE = 0.2
POLL_SECONDS = 0.02
SUPERVISION_CONTRACT = {"schema": 1, "launcher": ["-I", "-m", "euromind_safeops.check_bootstrap"],
                        "posix": "gated-group-anchor", "windows": "gated-kill-on-close-job",
                        "tail_bytes": TAIL_BYTES, "returned_characters": 12_000,
                        "cleanup_seconds": CLEANUP_SECONDS, "term_grace": TERM_GRACE,
                        "stdin": "devnull", "unconfirmed_cleanup": "retain-marker-no-receipt"}


class _Tail:
    def __init__(self, stream):
        self.stream, self.data = stream, bytearray()
        self.eof, self.failed = threading.Event(), False
        self.thread = threading.Thread(target=self._read, daemon=True)

    def _read(self):
        try:
            while raw := self.stream.read(8192):
                self.data.extend(raw)
                if len(self.data) > TAIL_BYTES:
                    del self.data[:-TAIL_BYTES]
        except (OSError, ValueError):
            self.failed = True
        finally:
            try:
                self.stream.close()
            except (OSError, ValueError):
                self.failed = True
            self.eof.set()

    def text(self) -> str:
        return self.data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")[-12_000:]


def _group_empty(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return True
    return False


def _completion(path: Path, process, token: str) -> int | None:
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1024 or
            getattr(before, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise ValueError("Unsafe launcher completion")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read(1025)
    if len(raw) > 1024 or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        raise ValueError("Launcher completion changed")
    value = decode_json_object(raw)
    if (set(value) != {"schema", "pid", "token", "exit_code"} or type(value["schema"]) is not int or
            value["schema"] != 1 or type(value["pid"]) is not int or value["pid"] != process.pid or
            value["token"] != token or type(value["exit_code"]) is not int or
            not -(2**31) <= value["exit_code"] < 2**32):
        raise ValueError("Invalid launcher completion")
    return value["exit_code"]


def _preflight() -> int:
    if os.name == "nt":
        return 0
    if (os.name != "posix" or not all(hasattr(os, n) for n in ("setpgid", "getpgid", "getpgrp", "killpg")) or
            signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL):
        raise SafeOpsError("Native check supervision unavailable or incompatible process ownership")
    return os.getpgrp()


def _signal_group(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


@dataclass(frozen=True)
class _Cleanup:
    confirmed: bool
    reason: str

    def __bool__(self):
        return self.confirmed


def _stop(process, job: Job | None, tails: list[_Tail], *, assigned: bool, released: bool) -> _Cleanup:
    """Never reap the POSIX anchor until every group signal has been sent."""
    deadline, confirmed = time.monotonic() + CLEANUP_SECONDS, True
    phase, reason = "native-termination", "confirmed"
    try:
        if job is not None and assigned:
            job.terminate()
        elif os.name == "posix" and not released:
            phase = "group-term"
            _signal_group(process.pid, signal.SIGTERM)
            time.sleep(TERM_GRACE)
            phase = "group-kill"
            _signal_group(process.pid, signal.SIGKILL)
        # Gated/unassigned child, or POSIX anchor already outside the owned group.
        phase = "launcher-kill"
        process.kill()
        phase = "launcher-wait"
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        phase = "native-empty-observation"
        while not (job.active() == 0 if job is not None and assigned else _group_empty(process.pid) if os.name == "posix" else True):
            if time.monotonic() >= deadline:
                return _Cleanup(False, "owned-group-or-job-still-present")
            time.sleep(POLL_SECONDS)
    except BaseException as exc:
        confirmed = False
        reason = phase + (f"-errno-{exc.errno}" if isinstance(exc, OSError) else "-interrupted-or-failed")
    try:
        for tail in tails:
            if tail.thread.ident is None:
                tail.stream.close()
            else:
                tail.thread.join(max(0, deadline - time.monotonic()))
                confirmed = confirmed and tail.eof.is_set() and not tail.failed
                if not confirmed and reason == "confirmed":
                    reason = "output-reader-incomplete"
    except BaseException:
        confirmed = False
        reason = "output-reader-cleanup-failed"
    return _Cleanup(confirmed, reason)


def run_check(command: list[str], *, cwd: Path, timeout: int, env: dict) -> subprocess.CompletedProcess:
    parent_group = _preflight()
    job, process, tails, assigned, clean, released = None, None, [], False, False, False
    try:
        if os.name == "nt":
            job = Job()
        with tempfile.TemporaryDirectory(prefix="safeops-check-") as temporary:
            destination = Path(temporary) / "completion.json"
            token = secrets.token_hex(16)
            flags = {"process_group": 0} if os.name == "posix" else {}
            process = subprocess.Popen([sys.executable, *SUPERVISION_CONTRACT["launcher"], str(destination), token,
                                        str(parent_group), *command], cwd=cwd, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, close_fds=True, **flags)
            deadline = time.monotonic() + timeout
            if job is not None:
                job.assign(process)
                assigned = True
            elif os.getpgid(process.pid) != process.pid:
                raise OSError("Launcher group not owned")
            tails = [_Tail(process.stdout), _Tail(process.stderr)]
            for tail in tails:
                tail.thread.start()
            process.stdin.write(b"G")
            while True:
                code = _completion(destination, process, token)
                if code is not None and (job.active() == 1 if job is not None else _group_empty(process.pid)):
                    break
                if code is None and all(t.eof.is_set() for t in tails):
                    raise ValueError("Launcher stopped without completion")
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(POLL_SECONDS)
            released = True  # No further POSIX group signals: the group was observed absent.
            process.stdin.write(b"X")
            process.stdin.close()
            cleanup_deadline = time.monotonic() + CLEANUP_SECONDS
            if process.wait(timeout=CLEANUP_SECONDS) != 0:
                raise ValueError("Launcher did not complete")
            if job is not None and job.active() != 0:
                raise ValueError("Job still active")
            for tail in tails:
                tail.thread.join(max(0, cleanup_deadline - time.monotonic()))
            if any(not t.eof.is_set() or t.failed for t in tails):
                raise RetainRunMarker("Check supervision incomplete: output streams did not close")
            clean = True
            return subprocess.CompletedProcess(command, code, tails[0].text(), tails[1].text())
    except BaseException as exc:
        if process is not None and not clean:
            if isinstance(exc, RetainRunMarker):
                raise
            cleanup = _stop(process, job, tails, assigned=assigned, released=released)
            if not cleanup:
                reason = getattr(cleanup, "reason", "unconfirmed")
                raise RetainRunMarker(f"Check supervision incomplete ({reason}); retained run marker requires independent process verification") from exc
        if isinstance(exc, (KeyboardInterrupt, SystemExit, subprocess.TimeoutExpired)):
            raise
        raise SafeOpsError("Cannot supervise the fixed check safely") from exc
    finally:
        if process is not None and process.stdin is not None and not process.stdin.closed:
            try:
                process.stdin.close()
            except BaseException as exc:
                raise RetainRunMarker("Cannot confirm control-pipe release; run marker retained") from exc
        if process is not None:
            for stream in (process.stdout, process.stderr):
                if not any(t.stream is stream and t.thread.ident is not None for t in tails):
                    try:
                        stream.close()
                    except BaseException as exc:
                        raise RetainRunMarker("Cannot confirm stream release; run marker retained") from exc
        if job is not None:
            try:
                job.close()
            except BaseException as exc:
                raise RetainRunMarker("Cannot confirm native job release; run marker retained") from exc
