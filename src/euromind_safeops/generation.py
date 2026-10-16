"""Exact-request source consent and unapproved AI proposals, never execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from . import __version__
from .candidate_transport import MAX_CANDIDATE_BYTES, prepare_request, send_request
from .core import SafeOpsError, decode_json_object, json_bytes, sha256
from .planning import SENSITIVE_TEXT, load_plan, validate_task
from .preview import _read_regular, _text
from .proposals import _context, _record_proposal, _validate_candidate
from .scanning import PATTERNS

MAX_FILES = 4
MAX_SOURCE_BYTES = 8192
MAX_SOURCE_TOTAL = 16384
MAX_REPLACEMENT_BYTES = 16384
MAX_REPLACEMENT_TOTAL = 32768
POLICY = {"schema": 1, "source_files": MAX_FILES, "source_bytes": MAX_SOURCE_BYTES,
          "source_total": MAX_SOURCE_TOTAL, "replacement_bytes": MAX_REPLACEMENT_BYTES,
          "replacement_total": MAX_REPLACEMENT_TOTAL, "candidate_bytes": MAX_CANDIDATE_BYTES,
          "proposal_schema": 2, "approval": "none"}


def _safe_text(text: str):
    if not isinstance(text, str):
        raise SafeOpsError("Generation request text must be a string")
    if (any(re.search(p, text) for p in SENSITIVE_TEXT) or
            any(p.search(text) for p in PATTERNS.values())):
        raise SafeOpsError("Selected request/candidate appears to contain credentials; generation refused")


def _source(root: Path, paths: list[str]) -> list[dict]:
    if not 1 <= len(paths) <= MAX_FILES:
        raise SafeOpsError("Generation requires one to four explicit file paths")
    files, total = [], 0
    for path in paths:
        selected = root / path
        try:
            if selected.lstat().st_nlink != 1:
                raise SafeOpsError("Generation refuses hardlinked source files")
            raw = _read_regular(selected, limit=MAX_SOURCE_BYTES)
            if selected.lstat().st_nlink != 1:
                raise SafeOpsError("Generation source changed during inspection")
        except OSError as exc:
            raise SafeOpsError("Cannot inspect a generation source") from exc
        text = _text(raw)
        _safe_text(path)
        _safe_text(text)
        total += len(raw)
        if total > MAX_SOURCE_TOTAL:
            raise SafeOpsError("Generation source total exceeds 16384 bytes")
        files.append({"path": path, "base_sha256": hashlib.sha256(raw).hexdigest(), "content": text})
    return files


def review_generation(root: Path, plan_id: str, *, provider: str, model: str,
                      endpoint: str = "", timeout: int = 30) -> dict:
    """Read-only, offline preview of the exact request, excluding auth headers."""
    bindings, paths = _context(root, plan_id)
    plan = load_plan(root, plan_id)
    task = validate_task(plan["task"])
    _safe_text(model)
    _safe_text(endpoint)
    files = _source(root, paths)
    request = prepare_request({"schema": 1, "task": task, "files": files}, provider=provider,
                              model=model, endpoint=endpoint, timeout=timeout)
    if _context(root, plan_id) != (bindings, paths) or _source(root, paths) != files:
        raise SafeOpsError("Generation context changed during request review")
    result = {"schema": 1, "status": "generation-review", "safeops_version": __version__,
              "plan_id": plan_id, "bindings": bindings, "policy": POLICY, "request": request,
              "notice": "Review exact source upload locally; no request sent, approval granted or proposal stored"}
    result["fingerprint"] = sha256(result)
    return result


def _candidate(root, text, paths):
    try:
        raw = text.encode("utf-8")
        if len(raw) > MAX_CANDIDATE_BYTES:
            raise ValueError("Oversize candidate")
        document = decode_json_object(raw)
    except (ValueError, UnicodeError, RecursionError, AttributeError) as exc:
        raise SafeOpsError("Generated candidate must be bounded unambiguous UTF-8 JSON") from exc
    entries = document.get("files")
    if (not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES or
            any(not isinstance(entry, dict) or entry.get("path") not in paths for entry in entries)):
        raise SafeOpsError("Generated candidate must replace only selected files within the file limit")
    _validate_candidate(root, document, paths)
    total = 0
    for entry in document["files"]:
        raw = entry["content"].encode("utf-8")
        total += len(raw)
        if len(raw) > MAX_REPLACEMENT_BYTES or total > MAX_REPLACEMENT_TOTAL:
            raise SafeOpsError("Generated replacements exceed byte limits")
        _safe_text(entry["content"])
    return document


def generate_proposal(root: Path, plan_id: str, confirm: str, *, allow_source_upload: bool,
                      provider: str, model: str, endpoint: str = "", timeout: int = 30) -> dict:
    if not allow_source_upload or not isinstance(confirm, str) or not re.fullmatch(r"[0-9a-f]{64}", confirm):
        raise SafeOpsError("Generation requires --allow-source-upload and exact reviewed --confirm fingerprint")
    options = {"provider": provider, "model": model, "endpoint": endpoint, "timeout": timeout}
    review = review_generation(root, plan_id, **options)
    if review["fingerprint"] != confirm:
        raise SafeOpsError("Generation confirmation is stale or does not match the exact reviewed request")
    if review_generation(root, plan_id, **options) != review:
        raise SafeOpsError("Generation context changed before upload")
    answer = send_request(review["request"])
    if review_generation(root, plan_id, **options) != review:
        raise SafeOpsError("Generation context changed after upload; no proposal stored")
    _, paths = _context(root, plan_id)
    document = _candidate(root, answer, paths)
    origin = {"kind": "ai", "provider": provider, "model": model, "request_sha256": confirm}
    return _record_proposal(root, plan_id, document, review["bindings"], paths, origin=origin)
