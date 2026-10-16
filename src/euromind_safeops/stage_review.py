"""Bounded, read-only original-context review; never application or approval."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import unicodedata

from . import __version__
from .core import MAX_FILE_BYTES, MAX_FILES, SKIP_DIRS, SafeOpsError, decode_json_object, sha256
from .execution import execution_contract_digest, validate_config
from .scope import validate_scope_paths
from .stage_inspection import MAX_DEPTH, MAX_ENTRIES, _directory, _evidence, _proposal, inspect_stage
from .staging import MAX_COPY_BYTES
from .target_runner import validate_targets

_ERROR = "Stage review failed: invalid, unsafe, changing or oversized local evidence"
_NOTICE = ("Point-in-time local unkeyed evidence only; no approval renewal, application, "
           "checks, provider request or filesystem isolation")
_PLAN_FIELDS = {"schema", "id", "created_at", "task", "paths", "risk", "specialist",
                "provider", "advice", "workspace_digest", "execution", "fingerprint"}


def _ancestors(root: Path, path: Path) -> None:
    _directory(root)
    for parent in reversed(path.relative_to(root).parents):
        _directory(root / parent)


def _read(root: Path, path: Path, limit: int) -> bytes:
    _ancestors(root, path)
    raw = _evidence(path, limit=limit)
    _ancestors(root, path)
    return raw


def _source_snapshot(root: Path) -> tuple[dict, str]:
    """Match tree_digest ordering/exclusions, with strict reads and total bounds.

    Environment files and ordinary files named like generated directories remain
    in the original snapshot. Only actual generated directories are omitted.
    """
    observed, folded, total, entries = {}, set(), 0, 0
    digest = hashlib.sha256()

    def visit(directory: Path, depth: int) -> None:
        nonlocal total, entries
        if depth > MAX_DEPTH:
            raise ValueError("Directory budget exceeded")
        identity = _directory(directory)
        children = []
        with os.scandir(directory) as listing:
            for child in listing:
                entries += 1
                if entries > MAX_ENTRIES:
                    raise ValueError("Entry budget exceeded")
                children.append(child.name)
        directories = []
        for name in sorted(children):
            path = directory / name
            info = path.lstat()
            if (stat.S_ISLNK(info.st_mode) or
                    getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise ValueError("Unsafe source link")
            if stat.S_ISDIR(info.st_mode) and name in SKIP_DIRS:
                continue
            # Names are never echoed in errors; require unambiguous UTF-8 paths.
            name.encode("utf-8")
            if (unicodedata.normalize("NFC", name) != name or
                    any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in name)):
                raise ValueError("Ambiguous source name")
            if stat.S_ISDIR(info.st_mode):
                directories.append(path)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Nonregular source file")
            relative = path.relative_to(root).as_posix()
            if relative.casefold() in folded or len(observed) >= MAX_FILES:
                raise ValueError("Ambiguous or excessive source files")
            folded.add(relative.casefold())
            raw = _read(root, path, MAX_FILE_BYTES)
            total += len(raw)
            if total > MAX_COPY_BYTES:
                raise ValueError("Source byte budget exceeded")
            observed[relative] = hashlib.sha256(raw).hexdigest()
            digest.update(relative.encode("utf-8") + b"\0" + raw + b"\0")
        for child in directories:
            visit(child, depth + 1)
        if _directory(directory) != identity:
            raise ValueError("Source directory changed")

    visit(root, 0)
    return observed, digest.hexdigest()


def _targets(root: Path, config: dict) -> str | None:
    manifest = _target_manifest(root, config)
    return None if manifest is None else sha256(manifest)


def _target_manifest(root: Path, config: dict) -> list | None:
    if config["schema"] == 1:
        return None

    def select() -> set[Path]:
        selected = set()
        for check in config["checks"]:
            selected.update(validate_targets(root, check, config["targets"][check], all_files=True))
        if len(selected) > MAX_FILES:
            raise ValueError("Selected-file budget exceeded")
        return selected

    selected, manifest, total = select(), [], 0
    for path in sorted(selected):
        raw = _read(root, path, MAX_FILE_BYTES)
        total += len(raw)
        if total > MAX_COPY_BYTES:
            raise ValueError("Selected-byte budget exceeded")
        manifest.append([path.relative_to(root).as_posix(), hashlib.sha256(raw).hexdigest()])
    if select() != selected:
        raise ValueError("Selected paths changed")
    return manifest


def _observe(root: Path, stage_id: str, inspection: dict) -> dict:
    state = root / ".safeops"
    parents = (state, state / "plans", state / "proposals", state / "stages",
               state / "stages" / stage_id)
    identities = [_directory(path) for path in parents]
    intent_path = parents[-1] / "intent.json"
    intent_raw = _read(root, intent_path, 4096)
    intent = decode_json_object(intent_raw)
    proposal = _proposal(root, intent)
    if proposal["fingerprint"] != inspection["proposal_fingerprint"]:
        raise ValueError("Proposal changed")
    bindings = proposal["bindings"]
    plan_path = state / "plans" / (bindings["plan_id"] + ".json")
    plan_raw = _read(root, plan_path, 256_000)
    plan = decode_json_object(plan_raw)
    if (set(plan) != _PLAN_FIELDS or type(plan["schema"]) is not int or plan["schema"] != 1 or
            plan["id"] != bindings["plan_id"] or plan["risk"] not in ("low", "medium", "high") or
            sha256({k: v for k, v in plan.items() if k != "fingerprint"}) != plan["fingerprint"] or
            validate_scope_paths(root, plan["paths"]) != plan["paths"] or not plan["paths"]):
        raise ValueError("Invalid bound plan")
    config_path = state / "config.json"
    config_raw = _read(root, config_path, 256_000)
    config = validate_config(root, decode_json_object(config_raw))
    selected_digest = _targets(root, config)
    files, source_digest = _source_snapshot(root)
    candidate = proposal["candidate"]["files"]  # Strictly checked by inspect-stage.
    checks = {
        "plan": (plan["fingerprint"] == bindings["plan_fingerprint"] and
                 plan["workspace_digest"] == bindings["workspace_digest"] and
                 sorted(plan["paths"]) == sorted(item["path"] for item in candidate)),
        "source": source_digest == bindings["workspace_digest"],
        "candidate_bases": all(files.get(item["path"]) == item["base_sha256"] for item in candidate),
        "configuration": sha256(config) == bindings["config_digest"],
        "selected_targets": selected_digest == bindings["targets_digest"],
        "version": proposal["safeops_version"] == __version__,
        "execution_contract": execution_contract_digest() == bindings["execution_contract"],
    }
    if ([_directory(path) for path in parents] != identities or
            _read(root, intent_path, 4096) != intent_raw or
            _read(root, plan_path, 256_000) != plan_raw or
            _read(root, config_path, 256_000) != config_raw or _proposal(root, intent) != proposal):
        raise ValueError("Control state changed")
    return {"checks": checks, "source_workspace_digest": source_digest,
            "config_digest": sha256(config), "targets_digest": selected_digest,
            "execution_contract": execution_contract_digest(),
            "control_digests": [hashlib.sha256(raw).hexdigest() for raw in
                                (intent_raw, plan_raw, config_raw)]}


def review_stage(root: Path, stage_id: str) -> dict:
    """Require matching stage and two stable original-context observations."""
    try:
        root = root.resolve(strict=True)
        inspection = inspect_stage(root, stage_id)
        result = {"schema": 1, "stage_id": stage_id, "proposal_id": inspection["proposal_id"],
                  "proposal_fingerprint": inspection["proposal_fingerprint"],
                  "stage_status": inspection["status"], "notice": _NOTICE}
        if inspection["status"] != "matching":
            return {**result, "status": "incompatible", "source_context": "not-reviewed",
                    "reasons": ["stage-not-matching"]}
        observed = _observe(root, stage_id, inspection)
        if (_observe(root, stage_id, inspection) != observed or
                inspect_stage(root, stage_id) != inspection):
            raise ValueError("Context changed during review")
        checks = observed["checks"]
        return {**result, "status": "current" if all(checks.values()) else "stale",
                "source_context": "revalidated", "checks": checks,
                "reasons": [key.replace("_", "-") + "-changed" for key, value in checks.items() if not value],
                "recorded_safeops_version": inspection["recorded_safeops_version"],
                "version_matches": checks["version"], "receipt_fingerprint": inspection["receipt_fingerprint"],
                "observed_source_workspace_digest": observed["source_workspace_digest"],
                "recorded_source_workspace_digest": inspection["source_workspace_digest"]}
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError) as exc:
        raise SafeOpsError(_ERROR) from exc
