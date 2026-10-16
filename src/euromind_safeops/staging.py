"""Materialize reviewed replacements in a separate local copy, never the source."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import secrets
import stat

from . import __version__
from .core import (MAX_FILE_BYTES, SKIP_DIRS, SafeOpsError, atomic_json_write, audit,
                   json_bytes, sha256, source_files, tree_digest, utc_now, workspace)
from .preview import _read_regular
from .proposals import _load, review_proposal
from .scope import validate_scope_paths

MAX_COPY_BYTES = 64_000_000
MAX_RECEIPT_BYTES = 1_000_000


def _directory(path: Path) -> None:
    """Create only missing directories; refuse links/reparse points at use."""
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or
            getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise SafeOpsError("Staging requires directories without links or reparse points")


def _write_new(root: Path, relative: str, raw: bytes) -> None:
    current = root
    _directory(current)
    for part in Path(relative).parts[:-1]:
        current /= part
        _directory(current)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(root / relative, flags, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _environment_path(relative: str) -> bool:
    return any(part == ".env" or part.startswith(".env.") for part in Path(relative).parts)


def stage_proposal(root: Path, proposal_id: str, confirmation: str) -> dict:
    reviewed = review_proposal(root, proposal_id)
    if confirmation != reviewed["fingerprint"]:
        raise SafeOpsError("Staging requires --confirm matching the exact reviewed proposal fingerprint")
    record = _load(root, proposal_id)
    if record["fingerprint"] != reviewed["fingerprint"]:
        raise SafeOpsError("Proposal changed since review")
    replacements = {item["path"]: item for item in record["candidate"]["files"]}
    if any(_environment_path(path) for path in replacements):
        raise SafeOpsError("Environment files cannot be staged")
    state = workspace(root)
    _directory(state)
    _directory(state / "stages")
    stage_id = secrets.token_hex(6)
    owned = state / "stages" / stage_id
    owned.mkdir(mode=0o700)  # exclusive: never reuse or replace an existing stage
    intent = {"schema": 1, "stage_id": stage_id, "created_at": utc_now(),
              "safeops_version": __version__, "proposal_id": proposal_id,
              "proposal_fingerprint": reviewed["fingerprint"],
              "candidate_sha256": reviewed["candidate_sha256"],
              "source_workspace_digest": record["bindings"]["workspace_digest"]}
    try:
        atomic_json_write(owned / "intent.json", intent)
        destination = owned / "workspace"
        _directory(destination)
        manifest, total, replaced = [], 0, set()
        for path in source_files(root):
            relative = path.relative_to(root).as_posix()
            if _environment_path(relative) or any(part in SKIP_DIRS for part in Path(relative).parts):
                continue
            validate_scope_paths(root, [relative])
            before = _read_regular(path, limit=MAX_FILE_BYTES)
            before_hash = hashlib.sha256(before).hexdigest()
            item = replacements.get(relative)
            if item and before_hash != item["base_sha256"]:
                raise SafeOpsError("Candidate base changed during staging")
            after = item["content"].encode("utf-8") if item else before
            total += len(after)
            if total > MAX_COPY_BYTES:
                raise SafeOpsError("Staging copy exceeds 64000000 bytes")
            _write_new(destination, relative, after)
            manifest.append({"path": relative, "source_sha256": before_hash,
                             "staged_sha256": hashlib.sha256(after).hexdigest(),
                             "bytes": len(after), "replaced": item is not None})
            if item:
                replaced.add(relative)
        if replaced != set(replacements):
            raise SafeOpsError("A proposed file was omitted from the staging copy")
        expected = {item["path"]: item["staged_sha256"] for item in manifest}
        actual = {}
        for path in source_files(destination):
            relative = path.relative_to(destination).as_posix()
            validate_scope_paths(destination, [relative])
            actual[relative] = hashlib.sha256(_read_regular(path, limit=MAX_FILE_BYTES)).hexdigest()
        if actual != expected:
            raise SafeOpsError("Staging copy changed during validation")
        final = review_proposal(root, proposal_id)
        if final["fingerprint"] != reviewed["fingerprint"]:
            raise SafeOpsError("Proposal changed during staging")
        receipt = {**intent, "status": "staged", "files": manifest, "copied_bytes": total,
                   "staged_workspace_digest": tree_digest(destination)}
        receipt["fingerprint"] = sha256(receipt)
        if len(json_bytes(receipt)) + 1 > MAX_RECEIPT_BYTES:
            raise SafeOpsError("Staging receipt exceeds 1000000 bytes")
        atomic_json_write(owned / "receipt.json", receipt)
        audit(root, "stage-proposal", reviewed["plan_id"], "staged")
    except (SafeOpsError, OSError, UnicodeError) as exc:
        raise SafeOpsError(f"Staging did not complete; inspect retained local stage {stage_id}") from exc
    return {"schema": 1, "status": "staged", "stage_id": stage_id,
            "proposal_id": proposal_id, "proposal_fingerprint": reviewed["fingerprint"],
            "workspace": str(destination), "receipt_fingerprint": receipt["fingerprint"],
            "files": len(manifest), "copied_bytes": total,
            "notice": "Separate local copy only; no execution approval, checks or OS isolation"}
