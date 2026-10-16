"""Explicit approval and fixed-command check execution. Not a sandbox."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core import SafeOpsError, atomic_json_write, audit, file_in_workspace, read_json, sha256, tree_digest, utc_now, workspace
from .locking import LOCK_PROTOCOL_VERSION, execution_lock
from .planning import load_plan
from .scope import validate_scope_paths
from .target_runner import TARGET_COMMAND, validate_targets

CHECKS = {
    "compile": ["-m", "compileall", "-q", "src", "tests"],
    "unit-tests": ["-m", "euromind_safeops.check_runner"],
}
CONFIG_SCHEMA_VERSION = 1
APPROVAL_SCHEMA_VERSION = 2
RUNNER_PROTOCOL_VERSION = 4


def execution_contract_digest() -> str:
    """Invalidate approvals when the installed version or fixed runner contract changes."""
    return sha256({"safeops_version": __version__, "runner_protocol": RUNNER_PROTOCOL_VERSION,
                   "checks": CHECKS, "target_command": TARGET_COMMAND,
                   "lock_protocol": LOCK_PROTOCOL_VERSION, "python_io_encoding": "utf-8",
                   "python_dont_write_bytecode": True, "run_receipt_schema": 1})


def get_config(root: Path) -> dict:
    return validate_config(root, read_json(workspace(root) / "config.json"))


def validate_config(root: Path, config: dict) -> dict:
    """Validate decoded policy without reopening its backing file."""
    check_names = config.get("checks")
    schema = config.get("schema")
    if (type(schema) is not int or schema not in (1, 2) or
            set(config) != ({"schema", "checks"} if schema == 1 else {"schema", "checks", "targets"})):
        raise SafeOpsError("Invalid config: expected schema 1/checks or schema 2/checks/targets")
    if (not isinstance(check_names, list) or not check_names or
            any(not isinstance(x, str) or x not in CHECKS for x in check_names) or
            len(set(check_names)) != len(check_names)):
        raise SafeOpsError("Invalid config: checks must be a nonempty list of unique supported names")
    if schema == 2:
        targets = config["targets"]
        if not isinstance(targets, dict) or set(targets) != set(check_names):
            raise SafeOpsError("Invalid config: targets must name exactly the enabled checks")
        for check in check_names:
            validate_targets(root, check, targets[check])
    return config


def targets_digest(root: Path, config: dict) -> str | None:
    """Bind every selected regular file, including normal snapshot exclusions."""
    if config["schema"] == 1:
        return None
    selected = set()
    for check in config["checks"]:
        selected.update(validate_targets(root, check, config["targets"][check], all_files=True))
    manifest = []
    try:
        for path in sorted(selected):
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as handle:
                while block := handle.read(65536):
                    size += len(block)
                    if size > 12_000_000:
                        raise SafeOpsError("Selected file exceeds 12000000 bytes")
                    digest.update(block)
            manifest.append([path.relative_to(root.resolve()).as_posix(), digest.hexdigest()])
    except OSError as exc:
        raise SafeOpsError("Cannot fingerprint selected targets") from exc
    return sha256(manifest)


def approve(root: Path, plan_id: str, reason: str, confirmation: str) -> dict:
    if confirmation != plan_id:
        raise SafeOpsError("Approval requires --confirm matching the plan ID")
    if not reason.strip() or len(reason) > 500:
        raise SafeOpsError("Approval reason must contain 1–500 characters")
    plan = load_plan(root, plan_id)
    if plan["risk"] == "critical":
        raise SafeOpsError("Critical-risk plans cannot be approved under the current policy")
    validate_scope_paths(root, plan.get("paths"))
    if tree_digest(root) != plan["workspace_digest"]:
        raise SafeOpsError("Workspace changed since planning; create a new plan")
    cfg = get_config(root)
    record = {"schema": APPROVAL_SCHEMA_VERSION, "plan_id": plan_id, "fingerprint": plan["fingerprint"],
              "workspace_digest": plan["workspace_digest"], "config_digest": sha256(cfg),
              "execution_contract": execution_contract_digest(),
              "reason": reason.strip(), "approved_at": utc_now()}
    if cfg["schema"] == 2:
        record["targets_digest"] = targets_digest(root, cfg)
    atomic_json_write(file_in_workspace(root, "approvals", plan_id), record)
    audit(root, "approve", plan_id, "approved")
    return record


def run(root: Path, plan_id: str, *, timeout: int = 60) -> dict:
    # Local import keeps receipt inspection independent of execution-module load order.
    from .run_receipts import begin_run, changed_inputs, finish_run, read_plan, result_status, stable_context

    if type(timeout) is not int or timeout < 1 or timeout > 300:
        raise SafeOpsError("--timeout must be between 1 and 300 seconds")
    root = root.resolve(strict=True)
    plan = read_plan(root, plan_id)
    if plan["risk"] == "critical":
        raise SafeOpsError("Critical-risk plans are blocked")
    validate_scope_paths(root, plan.get("paths"))
    owner = None
    try:
        with execution_lock(root, plan_id):
            before, current_plan, approved, cfg = stable_context(root, plan_id)
            if (type(approved.get("schema")) is not int or approved.get("schema") != APPROVAL_SCHEMA_VERSION or
                    approved.get("execution_contract") != execution_contract_digest() or
                    approved.get("plan_id") != plan_id or
                    approved.get("fingerprint") != plan["fingerprint"] or
                    approved.get("workspace_digest") != plan["workspace_digest"] or
                    approved.get("config_digest") != before["config_digest"] or current_plan != plan):
                raise SafeOpsError("Missing or stale approval; create a new plan and approve it under this version")
            if before["workspace_digest"] != plan["workspace_digest"]:
                raise SafeOpsError("Workspace changed since planning; approval is stale")
            if cfg["schema"] == 2 and approved.get("targets_digest") != before["targets_digest"]:
                raise SafeOpsError("Selected targets changed; approval is stale")
            owner = begin_run(root, plan_id, before, cfg["checks"], timeout)
            results = []
            outcomes = []
            # Keep Python check streams and their decoding independent of the OS locale.
            check_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
            for check in cfg["checks"]:
                if cfg["schema"] == 2:
                    paths = cfg["targets"][check]
                    validate_targets(root, check, paths)
                    command = [sys.executable, *TARGET_COMMAND, check, *paths]
                elif check == "compile" and not ((root / "src").is_dir() and (root / "tests").is_dir()):
                    raise SafeOpsError("compile requires src/ and tests/ directories")
                else:
                    command = [sys.executable, *CHECKS[check]]
                try:
                    completed = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                               timeout=timeout, check=False, encoding="utf-8",
                                               errors="replace", env=check_env)
                    result = {"check": check, "exit_code": completed.returncode,
                              "stdout": completed.stdout[-12000:], "stderr": completed.stderr[-12000:]}
                    outcome = "passed" if completed.returncode == 0 else "failed"
                except subprocess.TimeoutExpired:
                    result = {"check": check, "exit_code": -1, "stdout": "", "stderr": "Timed out"}
                    outcome = "timed-out"
                except OSError as exc:
                    raise SafeOpsError("cannot start the fixed check") from exc
                results.append(result)
                outcomes.append({"check": check, "exit_code": result["exit_code"], "status": outcome})
                try:
                    after = stable_context(root, plan_id)[0]
                except SafeOpsError:
                    after = None
                if outcome != "passed" or after is None or changed_inputs(before, after):
                    break
            status, _ = result_status(owner["intent"], outcomes, after)
    except (SafeOpsError, OSError) as exc:
        if owner is None:
            raise
        message = str(exc) if isinstance(exc, SafeOpsError) else "cannot execute approved checks"
        raise SafeOpsError(f"Run {owner['intent']['run_id']} incomplete: {message}") from exc
    # A terminal receipt is created only after successful guard/marker cleanup and
    # audit append. Failures leave the unique intent for historical inspection.
    run_id = owner["intent"]["run_id"]
    try:
        audit(root, "run", plan_id, status)
    except (SafeOpsError, OSError) as exc:
        raise SafeOpsError(f"Run {run_id} incomplete: cannot append the run audit event") from exc
    receipt = finish_run(root, owner, outcomes, after)
    return {"plan_id": plan_id, "run_id": run_id, "status": status, "checks": results,
            "receipt_fingerprint": receipt["fingerprint"], "reasons": receipt["reasons"]}
