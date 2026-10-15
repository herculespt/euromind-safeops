"""Portable advisory path preflight. This does not enforce filesystem isolation."""

from __future__ import annotations

import stat
from pathlib import Path, PurePosixPath, PureWindowsPath

from .core import SKIP_DIRS, SafeOpsError


_INTERNAL_PARTS = frozenset(name.casefold() for name in SKIP_DIRS)
_DEVICE_NAMES = frozenset({"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    prefix + digit for prefix in ("COM", "LPT") for digit in "123456789¹²³"
})


def validate_scope_paths(root: Path, paths: list[str]) -> list[str]:
    """Validate declared paths without reading their contents or importing tests.

    Future files are allowed. Existing components must be regular files or
    directories, with no links/reparse points. A later filesystem race is still
    possible; callers revalidate at the relevant lifecycle boundaries.
    """
    if not isinstance(paths, list) or len(paths) > 20:
        raise SafeOpsError("Scope paths must be a list of at most 20 entries")
    try:
        root = root.resolve(strict=True)
        if not root.is_dir():
            raise SafeOpsError("Scope root must be a directory")
        result = []
        for value in paths:
            if (not isinstance(value, str) or not value or
                    any(ord(c) < 32 or ord(c) == 127 or c in '\\:<>"|?*' for c in value)):
                raise SafeOpsError("Scope paths must use nonempty portable relative names")
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise SafeOpsError("Scope paths must be valid UTF-8 text") from exc
            path = PurePosixPath(value)
            if path.is_absolute() or PureWindowsPath(value).drive or ".." in value.split("/"):
                raise SafeOpsError("Scope paths must stay relative to the workspace")
            if any(part.casefold() in _INTERNAL_PARTS for part in path.parts):
                raise SafeOpsError("Scope paths cannot name internal or generated components")
            if any(part.endswith((".", " ")) or part.split(".", 1)[0].upper() in _DEVICE_NAMES
                   for part in path.parts):
                raise SafeOpsError("Scope paths cannot use reserved or ambiguous names")
            canonical = path.as_posix()
            if canonical in result:
                raise SafeOpsError("Scope paths must be unique after normalization")
            candidate = root
            for index, part in enumerate(path.parts):
                candidate = candidate / part
                try:
                    info = candidate.lstat()
                except FileNotFoundError:
                    break
                if (stat.S_ISLNK(info.st_mode) or
                        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise SafeOpsError("Scope paths cannot traverse links or reparse points")
                if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                    raise SafeOpsError("Scope paths require regular files or directories")
                if index < len(path.parts) - 1 and not stat.S_ISDIR(info.st_mode):
                    raise SafeOpsError("Scope path ancestors must be directories")
            if not (root / canonical).resolve(strict=False).is_relative_to(root):
                raise SafeOpsError("Scope paths must stay inside the workspace")
            result.append(canonical)
        return result
    except (OSError, RuntimeError) as exc:
        raise SafeOpsError("Cannot inspect scope paths") from exc
