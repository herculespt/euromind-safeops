"""Bounded historical stage inspection; no writes or execution authority."""

from __future__ import annotations

from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata

from . import __version__
from .core import MAX_FILE_BYTES, MAX_FILES, SKIP_DIRS, SafeOpsError, decode_json_object, sha256
from .preview import MAX_BYTES, _read_regular, _text
from .proposals import _load
from .scope import validate_scope_paths
from .staging import MAX_COPY_BYTES, MAX_RECEIPT_BYTES, _environment_path

MAX_ENTRIES = 10_000
MAX_DEPTH = 64
_INTENT = {"schema", "stage_id", "created_at", "safeops_version", "proposal_id",
           "proposal_fingerprint", "candidate_sha256", "source_workspace_digest"}
_RECEIPT = _INTENT | {"status", "files", "copied_bytes", "staged_workspace_digest", "fingerprint"}
_ENTRY = {"path", "source_sha256", "staged_sha256", "bytes", "replaced"}
_BINDINGS = {"plan_id", "plan_fingerprint", "workspace_digest", "config_digest",
             "targets_digest", "execution_contract"}
_NOTICE = "Historical local copy inspection only; no source revalidation, approval, writes or checks"
_ERROR = "Stage inspection failed: invalid, unsafe, changing or oversized local evidence"


def _hex(value: object, length: int = 64) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{" + str(length) + "}", value) is not None


def _directory(path: Path) -> tuple[int, int]:
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or
            getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise ValueError("Unsafe directory")
    return info.st_dev, info.st_ino


def _evidence(path: Path, *, limit: int) -> bytes:
    if path.lstat().st_nlink != 1:
        raise ValueError("Multiply linked evidence")
    return _read_regular(path, limit=limit)


def _intent(value: dict, stage_id: str) -> None:
    if (set(value) != _INTENT or type(value["schema"]) is not int or value["schema"] != 1 or
            value["stage_id"] != stage_id or not _hex(value["proposal_id"], 12) or
            any(not _hex(value[name]) for name in
                ("proposal_fingerprint", "candidate_sha256", "source_workspace_digest")) or
            not isinstance(value["safeops_version"], str) or
            not re.fullmatch(r"\d{1,6}\.\d{1,6}\.\d{1,6}(?:a\d{1,6})?", value["safeops_version"]) or
            not isinstance(value["created_at"], str) or
            not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", value["created_at"])):
        raise ValueError("Invalid intent")
    datetime.fromisoformat(value["created_at"])


def _path(root: Path, value: object) -> str:
    if (not isinstance(value, str) or any(part in {"", ".", ".."} for part in value.split("/")) or
            PurePosixPath(value).as_posix() != value or
            unicodedata.normalize("NFC", value) != value or
            any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value) or
            _environment_path(value)):
        raise ValueError("Invalid manifest path")
    validate_scope_paths(root, [value])
    return value


def _proposal(root: Path, intent: dict) -> dict:
    # Load historical integrity only. Current-source review would reject useful
    # retained stages after edits/upgrades and must not be confused with this check.
    directory = root / ".safeops" / "proposals"
    _directory(directory)
    if (directory / (intent["proposal_id"] + ".json")).lstat().st_nlink != 1:
        raise ValueError("Multiply linked proposal")
    record = _load(root, intent["proposal_id"])
    bindings = record["bindings"]
    if (record["fingerprint"] != intent["proposal_fingerprint"] or
            record["candidate_sha256"] != intent["candidate_sha256"] or
            record["safeops_version"] != intent["safeops_version"] or
            set(bindings) != _BINDINGS or not _hex(bindings["plan_id"], 12) or
            any(not _hex(bindings[name]) for name in _BINDINGS - {"plan_id", "targets_digest"}) or
            (bindings["targets_digest"] is not None and not _hex(bindings["targets_digest"])) or
            bindings["workspace_digest"] != intent["source_workspace_digest"]):
        raise ValueError("Broken proposal linkage")
    return record


def _manifest(receipt: dict, intent: dict, proposal: dict, root: Path) -> dict:
    if (set(receipt) != _RECEIPT or type(receipt["schema"]) is not int or
            any(receipt[key] != value for key, value in intent.items()) or
            receipt["status"] != "staged" or not _hex(receipt["fingerprint"]) or
            sha256({k: v for k, v in receipt.items() if k != "fingerprint"}) != receipt["fingerprint"] or
            not _hex(receipt["staged_workspace_digest"]) or type(receipt["copied_bytes"]) is not int or
            not 0 <= receipt["copied_bytes"] <= MAX_COPY_BYTES or
            not isinstance(receipt["files"], list) or not 1 <= len(receipt["files"]) <= MAX_FILES):
        raise ValueError("Invalid receipt")
    expected, folded, total = {}, set(), 0
    for item in receipt["files"]:
        if (not isinstance(item, dict) or set(item) != _ENTRY or
                not _hex(item["source_sha256"]) or not _hex(item["staged_sha256"]) or
                type(item["bytes"]) is not int or not 0 <= item["bytes"] <= MAX_FILE_BYTES or
                type(item["replaced"]) is not bool or
                (not item["replaced"] and item["source_sha256"] != item["staged_sha256"]) or
                (item["replaced"] and item["source_sha256"] == item["staged_sha256"])):
            raise ValueError("Invalid file entry")
        path = _path(root, item["path"])
        if path.casefold() in folded:
            raise ValueError("Duplicate or case-colliding path")
        folded.add(path.casefold())
        expected[path] = item
        total += item["bytes"]
    if total != receipt["copied_bytes"]:
        raise ValueError("Invalid byte count")
    candidate = proposal["candidate"]
    if (set(candidate) != {"schema", "files"} or type(candidate["schema"]) is not int or
            candidate["schema"] != 1 or not isinstance(candidate["files"], list) or
            not 1 <= len(candidate["files"]) <= 20):
        raise ValueError("Invalid candidate")
    replaced = set()
    for item in candidate["files"]:
        if not isinstance(item, dict) or set(item) != {"path", "base_sha256", "content"}:
            raise ValueError("Invalid replacement")
        path = _path(root, item["path"])
        if path in replaced or path not in expected or not isinstance(item["content"], str):
            raise ValueError("Invalid replacement linkage")
        raw = item["content"].encode("utf-8")
        _text(raw)
        entry = expected[path]
        if (len(raw) > MAX_BYTES or not entry["replaced"] or
                item["base_sha256"] != entry["source_sha256"] or len(raw) != entry["bytes"] or
                hashlib.sha256(raw).hexdigest() != entry["staged_sha256"]):
            raise ValueError("Replacement differs from proposal")
        replaced.add(path)
    if replaced != {path for path, item in expected.items() if item["replaced"]}:
        raise ValueError("Invalid replacement set")
    return expected


def _scan(root: Path) -> tuple[dict, str]:
    observed, folded, total, entries = {}, set(), 0, 0
    digest = hashlib.sha256()

    def visit(directory: Path, depth: int) -> None:
        nonlocal total, entries
        if depth > MAX_DEPTH:
            raise ValueError("Too many directory levels")
        identity = _directory(directory)
        children = []
        with os.scandir(directory) as listing:
            for child in listing:
                entries += 1
                if entries > MAX_ENTRIES:
                    raise ValueError("Too many entries")
                # Omit conventional generated/state/environment components without
                # traversing them, including excluded links. Included links fail.
                if child.name in SKIP_DIRS or _environment_path(child.name):
                    continue
                children.append(child.name)
        directories = []
        for name in sorted(children):
            path = directory / name
            info = path.lstat()
            if (stat.S_ISLNK(info.st_mode) or
                    getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise ValueError("Included link")
            if stat.S_ISDIR(info.st_mode):
                directories.append(path)
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Nonregular or multiply linked file")
            relative = _path(root, path.relative_to(root).as_posix())
            if relative.casefold() in folded or len(observed) >= MAX_FILES:
                raise ValueError("Ambiguous or excessive files")
            folded.add(relative.casefold())
            raw = _read_regular(path, limit=MAX_FILE_BYTES)
            total += len(raw)
            if total > MAX_COPY_BYTES:
                raise ValueError("Copy exceeds budget")
            observed[relative] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            digest.update(relative.encode("utf-8") + b"\0" + raw + b"\0")
            validate_scope_paths(root, [relative])
        for child in directories:
            visit(child, depth + 1)
        if _directory(directory) != identity:
            raise ValueError("Directory changed")

    visit(root, 0)
    return observed, digest.hexdigest()


def inspect_stage(root: Path, stage_id: str) -> dict:
    """Compare a retained schema-1 receipt with two bounded read-only scans."""
    try:
        if not _hex(stage_id, 12):
            raise ValueError("Invalid stage ID")
        state = root / ".safeops"
        owned = state / "stages" / stage_id
        parents = (state, state / "stages", owned)
        identities = [_directory(path) for path in parents]
        intent_path, receipt_path = owned / "intent.json", owned / "receipt.json"
        intent_raw = _evidence(intent_path, limit=4096)
        intent = decode_json_object(intent_raw)
        _intent(intent, stage_id)
        proposal = _proposal(root, intent)
        result = {"schema": 1, "stage_id": stage_id, "proposal_id": intent["proposal_id"],
                  "proposal_fingerprint": intent["proposal_fingerprint"],
                  "recorded_safeops_version": intent["safeops_version"],
                  "version_matches": intent["safeops_version"] == __version__,
                  "source_context": "historical-binding-only",
                  "source_workspace_digest": intent["source_workspace_digest"],
                  "workspace": str(owned / "workspace"), "notice": _NOTICE}
        try:
            receipt_path.lstat()
        except FileNotFoundError:
            # Do not inspect or repair a partial workspace, and detect a receipt
            # appearing while inspecting the intent/proposal evidence.
            status = "incomplete"
            receipt_raw = None
        else:
            receipt_raw = _evidence(receipt_path, limit=MAX_RECEIPT_BYTES)
            receipt = decode_json_object(receipt_raw)
            destination = owned / "workspace"
            _directory(destination)
            expected = _manifest(receipt, intent, proposal, destination)
            observed, digest = _scan(destination)
            if _scan(destination) != (observed, digest):
                raise ValueError("Workspace changed during inspection")
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            changed = sorted(path for path in set(expected) & set(observed)
                             if observed[path] != {"sha256": expected[path]["staged_sha256"],
                                                   "bytes": expected[path]["bytes"]})
            status = "changed" if missing or extra or changed else "matching"
            if status == "matching" and digest != receipt["staged_workspace_digest"]:
                raise ValueError("Receipt digest inconsistent with manifest")
            result.update(receipt_fingerprint=receipt["fingerprint"], missing=missing,
                          extra=extra, changed=changed, recorded_files=len(expected),
                          observed_files=len(observed), recorded_bytes=receipt["copied_bytes"],
                          observed_bytes=sum(item["bytes"] for item in observed.values()),
                          recorded_workspace_digest=receipt["staged_workspace_digest"],
                          observed_workspace_digest=digest)
        if (_evidence(intent_path, limit=4096) != intent_raw or
                _proposal(root, intent) != proposal or
                [_directory(path) for path in parents] != identities):
            raise ValueError("Control state changed")
        if receipt_raw is None:
            try:
                receipt_path.lstat()
            except FileNotFoundError:
                pass
            else:
                raise ValueError("Receipt appeared")
        elif _evidence(receipt_path, limit=MAX_RECEIPT_BYTES) != receipt_raw:
            raise ValueError("Receipt changed")
        return {**result, "status": status}
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError) as exc:
        raise SafeOpsError(_ERROR) from exc
