"""Bounded application journals and point-in-time recovery observations."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat

from . import __version__
from .core import SafeOpsError, decode_json_object, json_bytes, sha256
from .locking import _open_file
from .preview import MAX_BYTES, MAX_TOTAL_BYTES, _text
from .run_receipts import _fingerprint, _time
from .stage_inspection import _directory, _hex, _path
from .stage_review import _ancestors, _read

MAX_JOURNAL_BYTES = 64_000
MAX_ARTIFACTS = 85
_INFO = {"sha256", "bytes", "identity", "mode", "uid", "gid", "stamp"}
_MANIFEST = {"schema", "id", "created_at", "safeops_version", "stage_id", "run_id", "plan_id", "proposal_id",
             "review_fingerprint", "proposal_fingerprint", "stage_receipt_fingerprint",
             "run_receipt_fingerprint", "files", "fingerprint"}
_TERMINAL = {"schema", "id", "intent_fingerprint", "finished_at", "status", "files", "fingerprint"}
_RESTORE = {"schema", "id", "intent_fingerprint", "index", "prepared", "fingerprint"}
_ERROR = "Application inspection failed: invalid, unsafe, changing or oversized local evidence"


def observe_file(root: Path, path: Path) -> tuple[dict, bytes]:
    before = path.lstat()
    raw = _read(root, path, MAX_BYTES)
    after = path.lstat()
    def info(value):
        return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": value.st_size,
                "identity": [value.st_dev, value.st_ino], "mode": stat.S_IMODE(value.st_mode),
                "uid": value.st_uid, "gid": value.st_gid,
                "stamp": [value.st_mtime_ns, value.st_ctime_ns]}
    if info(before) != info(after) or len(raw) != after.st_size:
        raise ValueError("File changed while reading")
    return info(after), raw


def same_file(observed: dict, expected: dict, *, stamps: bool = False) -> bool:
    keys = _INFO if stamps else _INFO - {"stamp"}
    return all(observed[k] == expected[k] for k in keys)


def _info(value: object) -> None:
    if (not isinstance(value, dict) or set(value) != _INFO or not _hex(value["sha256"]) or
            type(value["bytes"]) is not int or not 0 <= value["bytes"] <= MAX_BYTES or
            any(type(value[k]) is not int or not 0 <= value[k] < 2**128 for k in ("mode", "uid", "gid")) or
            value["mode"] > 0o777 or not value["mode"] & 0o200 or
            any(not isinstance(value[k], list) or len(value[k]) != 2 or
                any(type(v) is not int or abs(v) >= 2**128 for v in value[k])
                for k in ("identity", "stamp")) or any(v < 0 for v in value["identity"])):
        raise ValueError("Invalid file metadata")


def marker_bytes(manifest: dict) -> bytes:
    return json_bytes({"schema": 1, "id": manifest["id"],
                       "intent_fingerprint": manifest["fingerprint"]}) + b"\n"


def write_bytes(root: Path, path: Path, raw: bytes, *, metadata: dict | None = None) -> dict:
    """Exclusive/fsynced private artifact; no cleanup of partial evidence."""
    if len(raw) > max(MAX_BYTES, MAX_JOURNAL_BYTES):
        raise ValueError("Artifact byte budget exceeded")
    _ancestors(root, path)
    with os.fdopen(_open_file(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL), "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
        if metadata is not None:
            opened = os.fstat(handle.fileno())
            if (opened.st_uid, opened.st_gid) != (metadata["uid"], metadata["gid"]):
                os.chown(path, metadata["uid"], metadata["gid"])
            os.chmod(path, metadata["mode"])
            os.fsync(handle.fileno())
    observed, actual = observe_file(root, path)
    if actual != raw:
        raise ValueError("Written artifact changed")
    return observed


def write_record(root: Path, path: Path, value: dict) -> dict:
    value = dict(value)
    value["fingerprint"] = sha256(value)
    raw = json_bytes(value) + b"\n"
    if len(raw) > MAX_JOURNAL_BYTES:
        raise ValueError("Journal record too large")
    write_bytes(root, path, raw)
    return value


def _manifest(root: Path, value: dict, application_id: str) -> None:
    _fingerprint(value, _MANIFEST)
    _time(value["created_at"])
    if (value["id"] != application_id or any(not _hex(value[k], 12) for k in
                                           ("stage_id", "run_id", "plan_id", "proposal_id")) or
            any(not _hex(value[k]) for k in ("review_fingerprint", "proposal_fingerprint",
                                            "stage_receipt_fingerprint", "run_receipt_fingerprint")) or
            not isinstance(value["safeops_version"], str) or
            re.fullmatch(r"[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}(?:a[0-9]{1,5})?", value["safeops_version"]) is None or
            not isinstance(value["files"], list) or not 1 <= len(value["files"]) <= 20):
        raise ValueError("Invalid application intent")
    seen, total = set(), 0
    for entry in value["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "before", "after"}:
            raise ValueError("Invalid application file")
        path = _path(root, entry["path"])
        if path.casefold() in seen:
            raise ValueError("Duplicate application path")
        seen.add(path.casefold())
        for name in ("before", "after"):
            _info(entry[name])
            total += entry[name]["bytes"]
        before, after = entry["before"], entry["after"]
        if (before["sha256"] == after["sha256"] or before["identity"] == after["identity"] or
                any(before[k] != after[k] for k in ("mode", "uid", "gid"))):
            raise ValueError("Invalid replacement metadata")
    if total > MAX_TOTAL_BYTES:
        raise ValueError("Application byte budget exceeded")


def _optional(root: Path, path: Path) -> tuple[bytes, dict] | None:
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    raw = _read(root, path, MAX_JOURNAL_BYTES)
    return raw, decode_json_object(raw)


def read_journal(root: Path, application_id: str) -> tuple[dict, dict, dict]:
    """Strict immutable journal, original backups and current candidate files."""
    if not _hex(application_id, 12):
        raise ValueError("Invalid application ID")
    state = root / ".safeops"
    owned = state / "applications" / application_id
    parents = (state, state / "applications", owned)
    identities = [_directory(p) for p in parents]
    raw = _read(root, owned / "intent.json", MAX_JOURNAL_BYTES)
    manifest = decode_json_object(raw)
    _manifest(root, manifest, application_id)
    allowed = {"intent.json", "applied.json", "rolled-back.json"}
    for i in range(len(manifest["files"])):
        allowed.update(f"{prefix}-{i:03d}.{suffix}" for prefix, suffix in
                       (("backup", "bin"), ("new", "bin"), ("restore", "bin"), ("restore", "json")))
    names = []
    with os.scandir(owned) as entries:
        for entry in entries:
            names.append(entry.name)
            if len(names) > MAX_ARTIFACTS or entry.name not in allowed:
                raise ValueError("Unknown or excessive journal artifacts")
    artifacts = {}
    for name in sorted(names):
        artifacts[name] = observe_file(root, owned / name)[0]
    restores, backups, current = {}, [], []
    for i, entry in enumerate(manifest["files"]):
        backup_info, backup = observe_file(root, owned / f"backup-{i:03d}.bin")
        _text(backup)
        if (backup_info["sha256"], backup_info["bytes"]) != (entry["before"]["sha256"], entry["before"]["bytes"]):
            raise ValueError("Backup differs from original")
        backups.append(backup)
        restore = _optional(root, owned / f"restore-{i:03d}.json")
        if restore:
            value = restore[1]
            _fingerprint(value, _RESTORE)
            _info(value["prepared"])
            if (value["id"] != application_id or value["intent_fingerprint"] != manifest["fingerprint"] or
                    type(value["index"]) is not int or value["index"] != i or
                    any(value["prepared"][k] != entry["before"][k] for k in ("sha256", "bytes", "mode", "uid", "gid"))):
                raise ValueError("Invalid restore intent")
            restores[i] = value["prepared"]
        for prefix, expected in (("new", entry["after"]), ("restore", restores.get(i))):
            name = f"{prefix}-{i:03d}.bin"
            if name in artifacts and (expected is None or not same_file(artifacts[name], expected, stamps=True)):
                raise ValueError("Unbound or changed prepared file")
        current.append(observe_file(root, root / entry["path"])[0])
    terminals = {}
    for status in ("applied", "rolled-back"):
        record = _optional(root, owned / (status + ".json"))
        if not record:
            continue
        value = record[1]
        _fingerprint(value, _TERMINAL)
        _time(value["finished_at"])
        if (value["id"] != application_id or value["intent_fingerprint"] != manifest["fingerprint"] or
                value["status"] != status or not isinstance(value["files"], list) or
                len(value["files"]) != len(manifest["files"])):
            raise ValueError("Invalid completion record")
        for i, info in enumerate(value["files"]):
            _info(info)
            expected = [manifest["files"][i]["after"]] if status == "applied" else [manifest["files"][i]["before"], restores.get(i)]
            if not any(e is not None and same_file(info, e) for e in expected):
                raise ValueError("Completion file linkage differs")
        terminals[status] = value
    pending = _optional(root, state / "application.pending")
    if pending:
        p = pending[1]
        if (set(p) != {"schema", "id", "intent_fingerprint"} or type(p["schema"]) is not int or
                p["schema"] != 1 or not _hex(p["id"], 12) or not _hex(p["intent_fingerprint"])):
            raise ValueError("Invalid pending marker")
        pending_owner = "self" if pending[0] == marker_bytes(manifest) else "other"
        pending_info = observe_file(root, state / "application.pending")[0]
    else:
        pending_owner, pending_info = "absent", None
    files = []
    for i, (entry, observed) in enumerate(zip(manifest["files"], current)):
        applied = terminals.get("applied", {}).get("files", [])[i] if "applied" in terminals else entry["after"]
        restored = terminals.get("rolled-back", {}).get("files", [])[i] if "rolled-back" in terminals else restores.get(i)
        if same_file(observed, entry["before"], stamps=True):
            status = "original"
        elif same_file(observed, applied, stamps="applied" in terminals):
            status = "applied"
        elif restored is not None and same_file(observed, restored, stamps="rolled-back" in terminals):
            status = "restored"
        else:
            status = "conflict"
        files.append({"path": entry["path"], "state": status, "observed": observed})
    conflict = any(f["state"] == "conflict" for f in files)
    completion = "rolled-back" if "rolled-back" in terminals else "applied" if "applied" in terminals else None
    status = "conflicted" if conflict else "pending"
    if not conflict and pending_owner != "self":
        if completion == "rolled-back" and all(f["state"] in {"original", "restored"} for f in files):
            status = "rolled-back"
        elif completion == "applied" and all(f["state"] == "applied" for f in files):
            status = "applied"
    result = {"schema": 1, "application_id": application_id, "journal_fingerprint": manifest["fingerprint"],
              "recorded_safeops_version": manifest["safeops_version"],
              "version_matches": manifest["safeops_version"] == __version__, "status": status,
              "completion": completion, "pending_owner": pending_owner, "files": files,
              "rollback_candidate": not conflict and pending_owner != "other",
              "evidence_digest": sha256({"artifacts": artifacts, "pending": pending_info, "parents": identities})}
    result["rollback_fingerprint"] = sha256(result)
    if ([_directory(p) for p in parents] != identities or
            _read(root, owned / "intent.json", MAX_JOURNAL_BYTES) != raw):
        raise ValueError("Journal changed")
    return result, manifest, {"backups": backups, "restores": restores, "identities": identities}


def inspect_application(root: Path, application_id: str) -> dict:
    try:
        root = root.resolve(strict=True)
        result = read_journal(root, application_id)[0]
        if read_journal(root, application_id)[0] != result:
            raise ValueError("Application changed during inspection")
        return {**result, "notice": "Point-in-time local unkeyed journal; no isolation, current-project approval or forced recovery"}
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError, IndexError) as exc:
        raise SafeOpsError(_ERROR) from exc
