"""Bounded unkeyed execution evidence; not approval or authenticated provenance."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import secrets

from . import __version__
from .core import SafeOpsError, decode_json_object, json_bytes, sha256, utc_now
from .execution import execution_contract_digest, validate_config
from .locking import _open_file
from .scope import validate_scope_paths
from .stage_inspection import _directory, _hex
from .stage_review import _ancestors, _read, _source_snapshot, _targets

MAX_RECEIPT_BYTES = 16_000
_CONTEXT = {"plan_fingerprint", "plan_digest", "approval_digest", "workspace_digest",
            "config_digest", "targets_digest", "execution_contract"}
_INTENT = {"schema", "run_id", "started_at", "safeops_version", "plan_id", "bindings",
           "checks", "timeout", "fingerprint"}
_RECEIPT = {"schema", "run_id", "intent_fingerprint", "finished_at", "status",
            "end_context", "checks", "reasons", "fingerprint"}
_ERROR = "Run receipt inspection failed: invalid, unsafe, changing or oversized local evidence"
_NOTICE = "Historical local unkeyed evidence only; no current-source revalidation, approval or application authority"


def read_plan(root: Path, plan_id: str) -> dict:
    if not _hex(plan_id, 12):
        raise SafeOpsError("Invalid plan ID")
    try:
        plan = decode_json_object(_read(root, root / ".safeops/plans" / (plan_id + ".json"), 256_000))
        if (type(plan.get("schema")) is not int or plan["schema"] != 1 or
                plan.get("id") != plan_id or plan.get("risk") not in ("low", "medium", "high", "critical") or
                not _hex(plan.get("workspace_digest")) or
                sha256({k: v for k, v in plan.items() if k != "fingerprint"}) != plan.get("fingerprint")):
            raise ValueError("Invalid plan")
        return plan
    except (SafeOpsError, OSError, ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError("Cannot safely read the run plan") from exc


def capture_context(root: Path, plan_id: str) -> tuple[dict, dict, dict, dict]:
    """Read bounded control/source/selected inputs; import no project code."""
    try:
        state = root / ".safeops"
        parents = (state, state / "plans", state / "approvals")
        identities = [_directory(p) for p in parents]
        paths = (state / "plans" / (plan_id + ".json"),
                 state / "approvals" / (plan_id + ".json"), state / "config.json")
        raw = [_read(root, p, 256_000) for p in paths]
        plan = read_plan(root, plan_id)
        validate_scope_paths(root, plan.get("paths"))
        approved = decode_json_object(raw[1])
        config = validate_config(root, decode_json_object(raw[2]))
        if decode_json_object(raw[0]) != plan:
            raise ValueError("Plan changed")
        selected = _targets(root, config)
        _, source = _source_snapshot(root)
        context = {"plan_fingerprint": plan["fingerprint"], "plan_digest": sha256(plan),
                   "approval_digest": sha256(approved), "workspace_digest": source,
                   "config_digest": sha256(config), "targets_digest": selected,
                   "execution_contract": execution_contract_digest()}
        if ([_read(root, p, 256_000) for p in paths] != raw or
                [_directory(p) for p in parents] != identities):
            raise ValueError("Control state changed")
        return context, plan, approved, config
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError) as exc:
        raise SafeOpsError("Cannot safely observe approved run inputs") from exc


def stable_context(root: Path, plan_id: str) -> tuple[dict, dict, dict, dict]:
    before = capture_context(root, plan_id)
    if capture_context(root, plan_id) != before:
        raise SafeOpsError("Approved run inputs changed during observation")
    return before


def _context(value: object) -> None:
    if (not isinstance(value, dict) or set(value) != _CONTEXT or
            any(not _hex(value[k]) for k in _CONTEXT - {"targets_digest"}) or
            value["targets_digest"] is not None and not _hex(value["targets_digest"])):
        raise ValueError("Invalid context")


def _time(value: object) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", value):
        raise ValueError("Invalid timestamp")
    datetime.fromisoformat(value)


def _fingerprint(value: dict, fields: set) -> None:
    if (set(value) != fields or type(value["schema"]) is not int or value["schema"] != 1 or
            not _hex(value["fingerprint"]) or
            sha256({k: v for k, v in value.items() if k != "fingerprint"}) != value["fingerprint"]):
        raise ValueError("Invalid fingerprint or schema")


def _intent(value: dict, run_id: str) -> None:
    _fingerprint(value, _INTENT)
    if (value["run_id"] != run_id or not _hex(value["plan_id"], 12) or
            not isinstance(value["safeops_version"], str) or
            not re.fullmatch(r"\d{1,6}\.\d{1,6}\.\d{1,6}(?:a\d{1,6})?", value["safeops_version"]) or
            type(value["timeout"]) is not int or not 1 <= value["timeout"] <= 300 or
            not isinstance(value["checks"], list) or not 1 <= len(value["checks"]) <= 2 or
            any(not isinstance(c, str) or c not in {"compile", "unit-tests"} for c in value["checks"]) or
            len(set(value["checks"])) != len(value["checks"])):
        raise ValueError("Invalid intent")
    _context(value["bindings"])
    _time(value["started_at"])


def changed_inputs(before: dict, after: dict) -> list[str]:
    groups = {"plan": ("plan_fingerprint", "plan_digest"), "approval": ("approval_digest",),
              "source": ("workspace_digest",), "configuration": ("config_digest",),
              "selected-targets": ("targets_digest",), "execution-contract": ("execution_contract",)}
    return [name + "-changed" for name, keys in groups.items() if any(before[k] != after[k] for k in keys)]


def result_status(intent: dict, checks: list[dict], after: dict | None) -> tuple[str, list[str]]:
    if not checks:
        raise ValueError("No observed checks")
    if after is None:
        return "incomplete", ["postcheck-context-unavailable"]
    reasons = changed_inputs(intent["bindings"], after)
    if reasons:
        return "changed-inputs", reasons
    if checks[-1]["status"] == "timed-out":
        return "timed-out", []
    passed = len(checks) == len(intent["checks"]) and all(c["status"] == "passed" for c in checks)
    return ("passed" if passed else "failed"), []


def _receipt(value: dict, intent: dict) -> None:
    _fingerprint(value, _RECEIPT)
    _time(value["finished_at"])
    if value["run_id"] != intent["run_id"] or value["intent_fingerprint"] != intent["fingerprint"]:
        raise ValueError("Receipt differs from intent")
    checks = value["checks"]
    if not isinstance(checks, list) or not 1 <= len(checks) <= len(intent["checks"]):
        raise ValueError("Invalid check count")
    for index, check in enumerate(checks):
        if (not isinstance(check, dict) or set(check) != {"check", "status", "exit_code"} or
                check["check"] != intent["checks"][index] or
                check["status"] not in ("passed", "failed", "timed-out") or
                type(check["exit_code"]) is not int or not -(2**31) <= check["exit_code"] < 2**32 or
                (check["status"] == "passed") != (check["exit_code"] == 0) or
                (check["status"] == "timed-out" and check["exit_code"] != -1) or
                index < len(checks) - 1 and check["status"] != "passed"):
            raise ValueError("Invalid check outcome")
    after = value["end_context"]
    if after is not None:
        _context(after)
    status, reasons = result_status(intent, checks, after)
    if (value["status"] != status or value["reasons"] != reasons or
            status == "failed" and checks[-1]["status"] != "failed"):
        raise ValueError("Inconsistent result")


def _write_new(root: Path, path: Path, value: dict) -> None:
    raw = json_bytes(value) + b"\n"
    if len(raw) > MAX_RECEIPT_BYTES:
        raise SafeOpsError("Run evidence exceeds the receipt budget")
    _ancestors(root, path)
    with os.fdopen(_open_file(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL), "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    if _read(root, path, MAX_RECEIPT_BYTES) != raw:
        raise SafeOpsError("Run evidence changed while writing")


def begin_run(root: Path, plan_id: str, bindings: dict, checks: list[str], timeout: int) -> dict:
    """Allocate exclusive evidence only after approval and initial revalidation."""
    run_id = secrets.token_hex(6)
    try:
        state = root / ".safeops"
        _directory(state)
        history = state / "runs"
        history.mkdir(mode=0o700, exist_ok=True)
        _directory(history)
        owned = history / run_id
        owned.mkdir(mode=0o700)
        parents = (state, history, owned)
        identities = [_directory(p) for p in parents]
        intent = {"schema": 1, "run_id": run_id, "started_at": utc_now(),
                  "safeops_version": __version__, "plan_id": plan_id, "bindings": bindings,
                  "checks": checks, "timeout": timeout}
        intent["fingerprint"] = sha256(intent)
        _intent(intent, run_id)
        _write_new(root, owned / "intent.json", intent)
        return {"intent": intent, "identities": identities}
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError(f"Cannot initialize run {run_id}; inspect retained evidence before retrying") from exc


def finish_run(root: Path, owner: dict, checks: list[dict], after: dict | None) -> dict:
    intent = owner["intent"]
    run_id = intent["run_id"]
    try:
        state = root / ".safeops"
        owned = state / "runs" / run_id
        parents = (state, state / "runs", owned)
        if ([_directory(p) for p in parents] != owner["identities"] or
                _read(root, owned / "intent.json", MAX_RECEIPT_BYTES) != json_bytes(intent) + b"\n"):
            raise ValueError("Run owner changed")
        status, reasons = result_status(intent, checks, after)
        receipt = {"schema": 1, "run_id": run_id, "intent_fingerprint": intent["fingerprint"],
                   "finished_at": utc_now(), "status": status, "end_context": after,
                   "checks": checks, "reasons": reasons}
        receipt["fingerprint"] = sha256(receipt)
        _receipt(receipt, intent)
        _write_new(root, owned / "receipt.json", receipt)
        return receipt
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError(f"Cannot complete run {run_id}; inspect retained evidence before retrying") from exc


def inspect_run(root: Path, run_id: str) -> dict:
    """Inspect historical evidence independently of current project/approval files."""
    try:
        if not _hex(run_id, 12):
            raise ValueError("Invalid run ID")
        root = root.resolve(strict=True)
        state = root / ".safeops"
        owned = state / "runs" / run_id
        parents = (state, state / "runs", owned)
        identities = [_directory(p) for p in parents]
        intent_raw = _read(root, owned / "intent.json", MAX_RECEIPT_BYTES)
        intent = decode_json_object(intent_raw)
        _intent(intent, run_id)
        result = {"schema": 1, "run_id": run_id, "plan_id": intent["plan_id"],
                  "intent_fingerprint": intent["fingerprint"], "started_at": intent["started_at"],
                  "recorded_safeops_version": intent["safeops_version"],
                  "version_matches": intent["safeops_version"] == __version__,
                  "bindings": intent["bindings"], "expected_checks": intent["checks"],
                  "source_context": "historical-binding-only", "notice": _NOTICE}
        path = owned / "receipt.json"
        try:
            path.lstat()
        except FileNotFoundError:
            receipt_raw = None
            result.update(status="incomplete", reasons=["completion-receipt-absent"])
        else:
            receipt_raw = _read(root, path, MAX_RECEIPT_BYTES)
            receipt = decode_json_object(receipt_raw)
            _receipt(receipt, intent)
            result.update({k: receipt[k] for k in ("finished_at", "status", "end_context", "checks", "reasons")})
            result["receipt_fingerprint"] = receipt["fingerprint"]
        if ([_directory(p) for p in parents] != identities or
                _read(root, owned / "intent.json", MAX_RECEIPT_BYTES) != intent_raw):
            raise ValueError("Run evidence changed")
        if receipt_raw is None:
            try:
                path.lstat()
            except FileNotFoundError:
                pass
            else:
                raise ValueError("Receipt appeared")
        elif _read(root, path, MAX_RECEIPT_BYTES) != receipt_raw:
            raise ValueError("Receipt changed")
        return result
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError) as exc:
        raise SafeOpsError(_ERROR) from exc
