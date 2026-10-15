"""Explicit approval and fixed-command check execution. Not a sandbox."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core import SafeOpsError, atomic_json_write, audit, file_in_workspace, read_json, sha256, tree_digest, utc_now, workspace
from .planning import load_plan

CHECKS = {
    "compile": ["-m", "compileall", "-q", "src", "tests"],
    "unit-tests": ["-m", "euromind_safeops.check_runner"],
}
CONFIG_SCHEMA_VERSION = 1
APPROVAL_SCHEMA_VERSION = 2
RUNNER_PROTOCOL_VERSION = 1


def execution_contract_digest() -> str:
    """Invalidate approvals when the installed version or fixed runner contract changes."""
    return sha256({"safeops_version": __version__, "runner_protocol": RUNNER_PROTOCOL_VERSION,
                   "checks": CHECKS, "python_io_encoding": "utf-8"})


def get_config(root: Path) -> dict:
    config = read_json(workspace(root) / "config.json")
    check_names = config.get("checks")
    if (set(config) != {"schema", "checks"} or type(config.get("schema")) is not int or
            config["schema"] != CONFIG_SCHEMA_VERSION):
        raise SafeOpsError("Invalid config: expected exactly schema (integer 1) and checks")
    if (not isinstance(check_names, list) or not check_names or
            any(not isinstance(x, str) or x not in CHECKS for x in check_names) or
            len(set(check_names)) != len(check_names)):
        raise SafeOpsError("Invalid config: checks must be a nonempty list of unique supported names")
    return config


def approve(root: Path, plan_id: str, reason: str, confirmation: str) -> dict:
    if confirmation != plan_id:
        raise SafeOpsError("Approval requires --confirm matching the plan ID")
    if not reason.strip() or len(reason) > 500:
        raise SafeOpsError("Approval reason must contain 1–500 characters")
    plan = load_plan(root, plan_id)
    if plan["risk"] == "critical":
        raise SafeOpsError("Critical-risk plans cannot be approved under the current policy")
    if tree_digest(root) != plan["workspace_digest"]:
        raise SafeOpsError("Workspace changed since planning; create a new plan")
    cfg = get_config(root)
    record = {"schema": APPROVAL_SCHEMA_VERSION, "plan_id": plan_id, "fingerprint": plan["fingerprint"],
              "workspace_digest": plan["workspace_digest"], "config_digest": sha256(cfg),
              "execution_contract": execution_contract_digest(),
              "reason": reason.strip(), "approved_at": utc_now()}
    atomic_json_write(file_in_workspace(root, "approvals", plan_id), record)
    audit(root, "approve", plan_id, "approved")
    return record


def run(root: Path, plan_id: str, *, timeout: int = 60) -> dict:
    if timeout < 1 or timeout > 300:
        raise SafeOpsError("--timeout must be between 1 and 300 seconds")
    plan = load_plan(root, plan_id)
    if plan["risk"] == "critical":
        raise SafeOpsError("Critical-risk plans are blocked")
    approved = read_json(file_in_workspace(root, "approvals", plan_id))
    cfg = get_config(root)
    if (approved.get("schema") != APPROVAL_SCHEMA_VERSION or
            approved.get("execution_contract") != execution_contract_digest() or
            approved.get("plan_id") != plan_id or
            approved.get("fingerprint") != plan["fingerprint"] or
            approved.get("workspace_digest") != plan["workspace_digest"] or
            approved.get("config_digest") != sha256(cfg)):
        raise SafeOpsError("Missing or stale approval; create a new plan and approve it under this version")
    if tree_digest(root) != plan["workspace_digest"]:
        raise SafeOpsError("Workspace changed since planning; approval is stale")
    lock = workspace(root) / "run.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise SafeOpsError("Another run may be active; inspect .safeops/run.lock") from exc
    results = []
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        # Keep Python check streams and their decoding independent of the OS locale.
        check_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        for check in cfg["checks"]:
            if check == "compile" and not ((root / "src").is_dir() and (root / "tests").is_dir()):
                raise SafeOpsError("compile requires src/ and tests/ directories")
            command = [sys.executable, *CHECKS[check]]
            try:
                completed = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                           timeout=timeout, check=False, encoding="utf-8",
                                           errors="replace", env=check_env)
                result = {"check": check, "exit_code": completed.returncode,
                          "stdout": completed.stdout[-12000:], "stderr": completed.stderr[-12000:]}
            except subprocess.TimeoutExpired:
                result = {"check": check, "exit_code": -1, "stdout": "", "stderr": "Timed out"}
            results.append(result)
            if result["exit_code"] != 0:
                break
        status = "passed" if len(results) == len(cfg["checks"]) and all(r["exit_code"] == 0 for r in results) else "failed"
        audit(root, "run", plan_id, status)
        return {"plan_id": plan_id, "status": status, "checks": results}
    finally:
        lock.unlink(missing_ok=True)
