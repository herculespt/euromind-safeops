"""Local plan-bound candidate records. No application or execution authority."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import secrets
import stat

from . import __version__
from .core import (SafeOpsError, atomic_json_write, audit, decode_json_object,
                   file_in_workspace, json_bytes, sha256, tree_digest, utc_now, workspace)
from .execution import execution_contract_digest, get_config, targets_digest
from .planning import load_plan
from .preview import MAX_BYTES, _read_regular, preview_document, read_candidate
from .scope import validate_scope_paths

MAX_RECORD_BYTES = MAX_BYTES + 4096
_FIELDS = {"schema", "id", "created_at", "safeops_version", "bindings", "candidate",
           "candidate_sha256", "fingerprint"}
_NOTICE = "Local proposal only: no source writes, approval grant, provider request or checks"


def _location(root: Path, proposal_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{12}", proposal_id):
        raise SafeOpsError("Invalid proposal ID")
    directory = workspace(root)
    for parent in (directory, directory / "proposals"):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if (not stat.S_ISDIR(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise SafeOpsError("Proposal storage must be directories without links or reparse points")
    return file_in_workspace(root, "proposals", proposal_id)


def _context(root: Path, plan_id: str) -> tuple[dict, list[str]]:
    plan = load_plan(root, plan_id)
    if plan["risk"] == "critical":
        raise SafeOpsError("Critical-risk plans cannot receive proposals")
    paths = validate_scope_paths(root, plan.get("paths"))
    if not paths:
        raise SafeOpsError("Proposals require explicit plan --path entries for each file")
    current = tree_digest(root)
    if current != plan.get("workspace_digest"):
        raise SafeOpsError("Workspace changed since planning; create a new plan and candidate")
    config = get_config(root)
    return {"plan_id": plan_id, "plan_fingerprint": plan["fingerprint"],
            "workspace_digest": current, "config_digest": sha256(config),
            "targets_digest": targets_digest(root, config),
            "execution_contract": execution_contract_digest()}, paths


def _validate_candidate(root: Path, document: dict, paths: list[str]) -> dict:
    result = preview_document(root, document)
    if not {item["path"] for item in result["files"]}.issubset(paths):
        raise SafeOpsError("Each proposed file must exactly match an explicit plan --path entry")
    if len(json_bytes(document)) > MAX_BYTES:
        raise SafeOpsError("Canonical candidate exceeds 256000 bytes")
    return result


def create_proposal(root: Path, plan_id: str, candidate: Path) -> dict:
    bindings, paths = _context(root, plan_id)
    document = read_candidate(candidate)
    preview = _validate_candidate(root, document, paths)
    if _context(root, plan_id) != (bindings, paths):
        raise SafeOpsError("Proposal context changed during validation")
    proposal_id = secrets.token_hex(6)
    record = {"schema": 1, "id": proposal_id, "created_at": utc_now(),
              "safeops_version": __version__, "bindings": bindings, "candidate": document,
              "candidate_sha256": preview["candidate_sha256"]}
    record["fingerprint"] = sha256(record)
    location = _location(root, proposal_id)
    location.parent.mkdir(mode=0o700, exist_ok=True)
    atomic_json_write(location, record)
    audit(root, "propose", plan_id, "recorded")
    return {"schema": 1, "status": "proposal-recorded", "proposal_id": proposal_id,
            "plan_id": plan_id, "candidate_sha256": record["candidate_sha256"],
            "fingerprint": record["fingerprint"], "notice": _NOTICE}


def _load(root: Path, proposal_id: str) -> dict:
    try:
        record = decode_json_object(_read_regular(_location(root, proposal_id), limit=MAX_RECORD_BYTES))
        if (set(record) != _FIELDS or type(record["schema"]) is not int or record["schema"] != 1 or
                record["id"] != proposal_id or not isinstance(record["bindings"], dict) or
                not isinstance(record["candidate"], dict) or
                not isinstance(record["created_at"], str) or
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", record["created_at"])):
            raise ValueError("Invalid record")
        datetime.fromisoformat(record["created_at"])
        fingerprint = record.pop("fingerprint")
        if (not isinstance(fingerprint, str) or sha256(record) != fingerprint or
                record["candidate_sha256"] != sha256(record["candidate"])):
            raise ValueError("Invalid fingerprint")
        record["fingerprint"] = fingerprint
        return record
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError("Proposal integrity verification failed") from exc


def review_proposal(root: Path, proposal_id: str) -> dict:
    record = _load(root, proposal_id)
    plan_id = record["bindings"].get("plan_id")
    if not isinstance(plan_id, str) or not re.fullmatch(r"[a-f0-9]{12}", plan_id):
        raise SafeOpsError("Proposal plan binding is invalid")
    bindings, paths = _context(root, plan_id)
    if record["safeops_version"] != __version__ or record["bindings"] != bindings:
        raise SafeOpsError("Proposal bindings are stale; create a new reviewed plan and proposal")
    preview = _validate_candidate(root, record["candidate"], paths)
    if _context(root, plan_id) != (bindings, paths):
        raise SafeOpsError("Proposal context changed during review")
    return {"schema": 1, "status": "proposal-reviewed", "proposal_id": proposal_id,
            "plan_id": plan_id, "fingerprint": record["fingerprint"],
            "candidate_sha256": preview["candidate_sha256"], "files": preview["files"],
            "notice": _NOTICE}
