"""Deterministic, advisory-only task planning and integrity checks."""

from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Any

from .core import SafeOpsError, file_in_workspace, read_json, sha256, tree_digest, utc_now, atomic_json_write

CRITICAL = (r"\bproduction\b", r"\bdeploy\b", r"\bpublish\b", r"\bdelete\b", r"\bdestroy\b", r"\bcredential", r"\bsecret", r"\bpassword", r"\bprivate.key", r"\.env\b", r"\bpayment", r"\btoken\b")
HIGH = (r"\bauth", r"\bcrypt", r"\bsecurity\b", r"\bmigrat", r"\bpermissions?\b", r"\brelease\b", r"\bfirewall\b")
MEDIUM = (r"\brefactor", r"\bdependenc", r"\bapi\b", r"\bdocker\b", r"\bupgrade\b", r"\bbackend\b")
SENSITIVE_TEXT = (r"sk-[A-Za-z0-9_-]{16,}", r"ghp_[A-Za-z0-9]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def risk_for(task: str, files: list[str]) -> str:
    content = " ".join([task, *files]).lower()
    for severity, patterns in (("critical", CRITICAL), ("high", HIGH), ("medium", MEDIUM)):
        if any(re.search(pattern, content) for pattern in patterns):
            return severity
    return "low"


def specialization(task: str) -> str:
    s = task.lower()
    for role, matches in (("security", ("security", "crypto", "auth", "threat")), ("infra-devops", ("docker", "devops", "deploy", "ci", "infrastructure")), ("mobile-app", ("flutter", "android", "ios")), ("backend", ("api", "rust", "python", "database")), ("documentation", ("readme", "documentation", "docs"))):
        if any(word in s for word in matches):
            return role
    return "general-engineering"


def validate_task(task: str) -> str:
    """Reject missing, oversized or obviously sensitive task text before remote calls."""
    task = task.strip()
    if not task or len(task) > 2000:
        raise SafeOpsError("Task must contain 1–2000 characters")
    if any(re.search(p, task) for p in SENSITIVE_TEXT):
        raise SafeOpsError("Task appears to contain a secret; do not save or transmit credentials")
    return task


def create_plan(root: Path, task: str, files: list[str], advice: str, provider: str) -> dict[str, Any]:
    task = validate_task(task)
    if len(files) > 20:
        raise SafeOpsError("At most 20 scope paths")
    for name in files:
        path = Path(name)
        if not name or path.is_absolute() or ".." in path.parts or path.as_posix().startswith(".safeops"):
            raise SafeOpsError(f"Invalid or internal scope path: {name}")
    plan = {
        "schema": 1,
        "id": secrets.token_hex(6),
        "created_at": utc_now(),
        "task": task,
        "paths": files,
        "risk": risk_for(task, files),
        "specialist": specialization(task),
        "provider": provider,
        "advice": advice[:6000],
        "workspace_digest": tree_digest(root),
        "execution": "approved checks only (task text and AI advice are never commands)",
    }
    plan["fingerprint"] = sha256(plan)
    atomic_json_write(file_in_workspace(root, "plans", plan["id"]), plan)
    return plan


def load_plan(root: Path, plan_id: str) -> dict[str, Any]:
    plan = read_json(file_in_workspace(root, "plans", plan_id))
    fingerprint = plan.pop("fingerprint", None)
    if (not isinstance(fingerprint, str) or sha256(plan) != fingerprint or
            plan.get("schema") != 1 or plan.get("id") != plan_id or
            plan.get("risk") not in ("low", "medium", "high", "critical")):
        raise SafeOpsError("Plan integrity verification failed")
    plan["fingerprint"] = fingerprint
    return plan
