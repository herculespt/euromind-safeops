"""Read-only, exact-base previews of local text replacement candidates."""

from __future__ import annotations

import difflib
import hashlib
import os
import re
import stat
import unicodedata
from pathlib import Path

from .core import SafeOpsError, decode_json_object, sha256
from .scope import validate_scope_paths


MAX_BYTES = 256_000
MAX_TOTAL_BYTES = 1_000_000


def _read_regular(path: Path) -> bytes:
    """Bound reads and reject nonregular descriptors; no write or blocking FIFO."""
    try:
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise SafeOpsError("Preview inputs must be existing regular files without links")
        flags = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) |
                 getattr(os, "O_BINARY", 0))
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (not stat.S_ISREG(opened.st_mode) or
                    (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)):
                raise SafeOpsError("Preview input changed during inspection")
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise SafeOpsError("Preview input exceeds 256000 bytes")
        return raw
    except OSError as exc:
        raise SafeOpsError("Cannot read a preview input") from exc


def _text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise SafeOpsError("Preview supports UTF-8 text only") from exc
    if len(text.splitlines()) > 5000:
        raise SafeOpsError("Preview text exceeds 5000 lines per file")
    if (text.startswith("\ufeff") or (text and not text.endswith("\n")) or
            any((ord(c) < 32 and c not in "\n\t") or 127 <= ord(c) <= 159 for c in text)):
        raise SafeOpsError("Preview requires BOM-free LF text with a final newline and no control characters")
    return text


def preview_candidate(root: Path, candidate: Path) -> dict:
    """Validate every entry before returning diffs; never persist or authorize it.

    Paths are checked again before a final byte comparison. This detects common
    concurrent edits, not all filesystem races, and is not an isolation boundary.
    """
    try:
        document = decode_json_object(_read_regular(candidate))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError("Candidate must be an unambiguous UTF-8 JSON object") from exc
    if (set(document) != {"schema", "files"} or type(document["schema"]) is not int or
            document["schema"] != 1 or not isinstance(document["files"], list) or
            not 1 <= len(document["files"]) <= 20):
        raise SafeOpsError("Candidate requires schema 1 and one to twenty file replacements")
    paths = []
    for item in document["files"]:
        if (not isinstance(item, dict) or set(item) != {"path", "base_sha256", "content"} or
                not isinstance(item["path"], str) or not isinstance(item["base_sha256"], str) or
                not re.fullmatch(r"[a-f0-9]{64}", item["base_sha256"]) or
                not isinstance(item["content"], str)):
            raise SafeOpsError("Candidate file fields must be path, lowercase base_sha256 and text content")
        path = item["path"]
        if (any(part in {"", "."} for part in path.split("/")) or
                unicodedata.normalize("NFC", path) != path or
                any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in path) or
                path.casefold() in {p.casefold() for p in paths}):
            raise SafeOpsError("Candidate paths must be canonical and unique without case collisions")
        paths.append(path)
    validate_scope_paths(root, paths)
    results, originals, total = [], [], 0
    for item in document["files"]:
        before = _read_regular(root / item["path"])
        if hashlib.sha256(before).hexdigest() != item["base_sha256"]:
            raise SafeOpsError("Candidate base hash does not match the current file")
        try:
            after = item["content"].encode("utf-8")
        except UnicodeError as exc:
            raise SafeOpsError("Candidate content must be UTF-8 text") from exc
        total += len(before) + len(after)
        if len(after) > MAX_BYTES or total > MAX_TOTAL_BYTES:
            raise SafeOpsError("Candidate replacement content exceeds preview byte limits")
        old_text, new_text = _text(before), _text(after)
        if before == after:
            raise SafeOpsError("Candidate replacements must change file content")
        diff = "".join(difflib.unified_diff(old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True), fromfile="a/" + item["path"], tofile="b/" + item["path"]))
        results.append({"path": item["path"], "before_sha256": item["base_sha256"],
                        "after_sha256": hashlib.sha256(after).hexdigest(), "diff": diff})
        originals.append(before)
    validate_scope_paths(root, paths)
    for path, original in zip(paths, originals):
        if _read_regular(root / path) != original:
            raise SafeOpsError("Source changed during preview; regenerate and review the candidate")
    return {"schema": 1, "status": "preview-only", "candidate_sha256": sha256(document),
            "files": results, "notice": "Preview only: no files written; no approval granted; no checks executed"}
