"""Integrity, workspace and persistence primitives (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SafeOpsError(Exception):
    """Controlled error suitable for the CLI without a traceback."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(obj: Any) -> str:
    return hashlib.sha256(json_bytes(obj)).hexdigest()


def secure_dir(root: Path) -> Path:
    root = root.resolve(strict=True)
    directory = root / ".safeops"
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise SafeOpsError("Unsafe .safeops location (symlink or non-directory)")
    return directory


def workspace(root: Path) -> Path:
    directory = secure_dir(root)
    if not (directory / "config.json").is_file():
        raise SafeOpsError("Workspace is not initialized; run 'safeops init' first")
    return directory


def file_in_workspace(root: Path, group: str, name: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{12}", name):
        raise SafeOpsError("Invalid plan ID")
    parent = workspace(root) / group
    if parent.is_symlink():
        raise SafeOpsError("Workspace storage must not be a symlink")
    location = parent / f"{name}.json"
    if location.is_symlink():
        raise SafeOpsError("Workspace file must not be a symlink")
    return location


def atomic_json_write(path: Path, data: Any, *, replace: bool = False) -> None:
    """Write via temp+rename; avoid following destination symlinks."""
    if path.is_symlink():
        raise SafeOpsError("Refusing to overwrite symlink")
    if path.exists() and not replace:
        raise SafeOpsError(f"Already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".safeops-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(json_bytes(data) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink() or (path.exists() and not replace):
            raise SafeOpsError("Concurrent update or symlink detected")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise SafeOpsError(f"Refusing symlink: {path}")
    try:
        with path.open("rb") as handle:
            raw = handle.read(256_001)
        if len(raw) > 256_000:
            raise SafeOpsError("JSON file exceeds limit")
        def unique_object(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError("Duplicate JSON object key")
                result[key] = item
            return result

        def reject_constant(_value):
            raise ValueError("Non-standard JSON numeric constant")

        def finite_float(text):
            number = float(text)
            if not math.isfinite(number):
                raise ValueError("Non-finite JSON numeric value")
            return number

        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object,
                           parse_constant=reject_constant, parse_float=finite_float)
        if not isinstance(value, dict):
            raise ValueError("Expected an object")
        return value
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError(f"Cannot read {path.name}: {exc}") from exc


SKIP_DIRS = frozenset({".git", ".safeops", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", "node_modules", "dist", "build"})
MAX_FILES = 5000
MAX_FILE_BYTES = 12_000_000


def source_files(root: Path):
    """Yield regular files without traversing symlinks; reject unscannable trees."""
    count = 0
    for base, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(d for d in directories if d not in SKIP_DIRS and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            count += 1
            if count > MAX_FILES:
                raise SafeOpsError(f"Too many files (> {MAX_FILES}); scope the workspace")
            if path.stat().st_size > MAX_FILE_BYTES:
                raise SafeOpsError(f"File too large to fingerprint: {path.relative_to(root)}")
            yield path


def tree_digest(root: Path) -> str:
    """Hash file content and relative names, excluding generated runtime data."""
    h = hashlib.sha256()
    for path in source_files(root):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8") + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(128 * 1024), b""):
                h.update(chunk)
        h.update(b"\0")
    return h.hexdigest()


def audit(root: Path, action: str, plan_id: str, status: str) -> None:
    import json
    path = workspace(root) / "audit.jsonl"
    if path.is_symlink():
        raise SafeOpsError("Refusing symlink audit log")
    record = {"timestamp": utc_now(), "action": action, "plan_id": plan_id, "status": status}
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
