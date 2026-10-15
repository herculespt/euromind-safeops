"""Cooperative local native locks and explicit archival recovery, not isolation."""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
import uuid
from contextlib import contextmanager
from pathlib import Path

from .core import SafeOpsError, atomic_json_write, audit, decode_json_object, json_bytes, utc_now, workspace

LOCK_PROTOCOL_VERSION = 1
MAX_MARKER_BYTES = 4096


class GuardBusy(SafeOpsError):
    """A native guard could not be acquired without waiting."""


def _linked(info: os.stat_result) -> bool:
    return bool(stat.S_ISLNK(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _directory(path: Path) -> None:
    info = path.lstat()
    if _linked(info) or not stat.S_ISDIR(info.st_mode):
        raise SafeOpsError("Lock state requires a regular directory without links/reparse points")


def _state(root: Path) -> Path:
    directory = workspace(root)
    _directory(directory)
    return directory


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _regular(info: os.stat_result) -> None:
    if _linked(info) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SafeOpsError("Lock files must be regular, without links, reparse points or hard-link aliases")


def _open_file(path: Path, flags: int) -> int:
    try:
        before = path.lstat()
        _regular(before)
    except FileNotFoundError:
        before = None
    fd = os.open(path, flags | getattr(os, "O_NOFOLLOW", 0) |
                 getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0), 0o600)
    try:
        os.set_inheritable(fd, False)
        opened = os.fstat(fd)
        _regular(opened)
        current = path.lstat()
        _regular(current)
        if (_identity(opened) != _identity(current) or
                before is not None and _identity(before) != _identity(opened)):
            raise SafeOpsError("Lock file changed while opening")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _native_lock(fd: int, *, release: bool = False) -> None:
    try:
        if os.name == "posix":
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            # Windows permits byte-region locks beyond EOF; the guard stays empty.
            msvcrt.locking(fd, msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
        else:
            raise SafeOpsError("Native run locking is unsupported on this platform")
    except ImportError as exc:
        raise SafeOpsError("Native run locking is unavailable") from exc
    except OSError as exc:
        if not release and exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
            raise GuardBusy("Run guard is busy; another operation may be active") from exc
        raise SafeOpsError("Native run guard operation failed") from exc


@contextmanager
def _guard(directory: Path):
    fd = _open_file(directory / "run.guard", os.O_RDWR | os.O_CREAT)
    acquired = False
    try:
        _native_lock(fd)
        acquired = True
        yield
    finally:
        try:
            if acquired:
                _native_lock(fd, release=True)
        finally:
            os.close(fd)
    # Never unlink the guard: another process can already have its descriptor.


def _marker(directory: Path) -> dict | None:
    try:
        fd = _open_file(directory / "run.lock", os.O_RDONLY)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        raw = handle.read(MAX_MARKER_BYTES + 1)
    if len(raw) > MAX_MARKER_BYTES:
        raise SafeOpsError("Run marker exceeds the 4096-byte inspection limit")
    result = {"raw": raw, "identity": _identity(info),
              "fingerprint": hashlib.sha256(raw).hexdigest(), "format": "unrecognized",
              "owner_pid": None, "plan_id": None}
    stripped = raw.strip()
    if re.fullmatch(rb"[0-9]{1,20}", stripped) and int(stripped) > 0:
        result.update(format="legacy-pid", owner_pid=int(stripped))
        return result
    try:
        record = decode_json_object(raw)
    except (ValueError, UnicodeError, RecursionError):
        return result
    if (set(record) == {"schema", "pid", "plan_id", "token", "created_at"} and
            type(record.get("schema")) is int and record["schema"] == 1 and
            type(record.get("pid")) is int and record["pid"] > 0 and
            isinstance(record.get("plan_id"), str) and re.fullmatch(r"[a-f0-9]{12}", record["plan_id"]) and
            isinstance(record.get("token"), str) and re.fullmatch(r"[a-f0-9]{32}", record["token"]) and
            isinstance(record.get("created_at"), str) and len(record["created_at"]) <= 64):
        result.update(format="record-v1", owner_pid=record["pid"], plan_id=record["plan_id"])
    return result


def lock_status(root: Path) -> dict:
    """Point-in-time metadata and nonblocking probe; create or remove no files."""
    directory = _state(root)
    marker = _marker(directory)
    try:
        fd = _open_file(directory / "run.guard", os.O_RDWR)
    except FileNotFoundError:
        guard = "absent"
    else:
        try:
            try:
                _native_lock(fd)
            except GuardBusy:
                guard = "busy"
            else:
                _native_lock(fd, release=True)
                guard = "free"
        finally:
            os.close(fd)
    return {"guard": guard, "marker_present": marker is not None,
            "marker_fingerprint": marker["fingerprint"] if marker else None,
            "marker_format": marker["format"] if marker else None,
            "owner_pid": marker["owner_pid"] if marker else None,
            "plan_id": marker["plan_id"] if marker else None,
            "notice": "Point-in-time status; no PID or free guard proves that child checks stopped"}


@contextmanager
def execution_lock(root: Path, plan_id: str):
    directory = _state(root)
    with _guard(directory):
        raw = json_bytes({"schema": 1, "pid": os.getpid(), "plan_id": plan_id,
                          "token": uuid.uuid4().hex, "created_at": utc_now()}) + b"\n"
        try:
            fd = _open_file(directory / "run.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise SafeOpsError("Run marker exists; inspect doctor and verify checks before explicit recovery") from exc
        with os.fdopen(fd, "wb") as handle:
            identity = _identity(os.fstat(handle.fileno()))
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        # Initialization failure intentionally leaves the marker for inspection.
        try:
            yield
        finally:
            current = _marker(directory)
            if current is None or current["identity"] != identity or current["raw"] != raw:
                raise SafeOpsError("Run marker missing or changed; automatic cleanup refused")
            (directory / "run.lock").unlink()


def recover_lock(root: Path, confirmation: str, reason: str, acknowledged: bool) -> dict:
    if not isinstance(confirmation, str) or not re.fullmatch(r"[a-f0-9]{64}", confirmation):
        raise SafeOpsError("Recovery requires --confirm matching the doctor marker fingerprint")
    if acknowledged is not True:
        raise SafeOpsError("Recovery requires --confirm-no-running-checks after independent verification")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise SafeOpsError("Recovery reason must contain 1–500 characters")
    try:
        reason.encode("utf-8")
    except UnicodeError as exc:
        raise SafeOpsError("Recovery reason must be valid UTF-8") from exc
    root = root.resolve(strict=True)
    directory = _state(root)
    with _guard(directory):
        marker = _marker(directory)
        if marker is None or marker["fingerprint"] != confirmation:
            raise SafeOpsError("Run marker absent or changed; inspect doctor again")
        history = directory / "recovered-locks"
        if history.exists():
            _directory(history)
        history.mkdir(mode=0o700, exist_ok=True)
        _directory(history)
        recovery_id = uuid.uuid4().hex
        destination = history / recovery_id
        destination.mkdir(mode=0o700)
        receipt = {"schema": 1, "action": "archive-run-marker", "marker_fingerprint": confirmation,
                   "marker_format": marker["format"], "reason": reason.strip(),
                   "no_running_checks_confirmed": True, "requested_at": utc_now()}
        atomic_json_write(destination / "receipt.json", receipt)
        current = _marker(directory)
        if current is None or current["identity"] != marker["identity"] or current["raw"] != marker["raw"]:
            raise SafeOpsError("Run marker changed during recovery; original path retained")
        archive = destination / "run.lock"
        if archive.exists():
            raise SafeOpsError("Recovery archive already exists")
        (directory / "run.lock").rename(archive)
        audit(root, "recover-lock", marker["plan_id"] or "", recovery_id)
    return {"status": "recovered", "marker_fingerprint": confirmation,
            "archive": archive.relative_to(root).as_posix(),
            "receipt": (destination / "receipt.json").relative_to(root).as_posix(),
            "notice": "Recovery grants no execution approval; review interrupted checks and workspace state"}
