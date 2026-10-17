"""EuroMind SafeOps command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import SafeOpsError, atomic_json_write, audit, secure_dir, tree_digest, workspace
from .execution import APPROVAL_SCHEMA_VERSION, CONFIG_SCHEMA_VERSION, approve, execution_contract_digest, get_config, run
from .locking import lock_status, recover_lock
from .planning import create_plan, load_plan, specialization, validate_task
from .preview import preview_candidate
from .proposals import create_proposal, review_proposal
from .generation import generate_proposal, review_generation
from .providers import offline_advice, remote_advice, provider_status
from .scope import validate_scope_paths
from .scanning import scan
from .staging import stage_proposal
from .git_staging import review_git_stage, stage_git_proposal
from .stage_inspection import inspect_stage
from .stage_review import review_stage
from .run_receipts import inspect_run
from .application import apply_stage, review_application, rollback_application
from .application_journal import inspect_application


class ArgumentUsageError(Exception):
    def __init__(self, message: str, usage: str, prog: str):
        super().__init__(message)
        self.usage = usage
        self.prog = prog


class SafeOpsParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ArgumentUsageError(message, self.format_usage(), self.prog)


def make_parser() -> argparse.ArgumentParser:
    parser = SafeOpsParser(prog="safeops", description=f"Safety-focused engineering orchestration (v{__version__}, alpha)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project directory (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit a schema-1 JSON envelope (before command)")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize local, git-ignored SafeOps workspace")
    commands.add_parser("doctor", help="Check local installation and workspace")
    commands.add_parser("providers", help="List advisory backends and credential availability")
    p = commands.add_parser("plan", help="Create a hashed, advisory-only task plan")
    p.add_argument("task", help="Short task description; never paste secrets")
    p.add_argument("--path", action="append", default=[], help="Portable relative advisory path; not a check restriction (repeatable)")
    p.add_argument("--provider", choices=["offline", "openai", "anthropic", "openai-compatible"], default="offline")
    p.add_argument("--endpoint", default="")
    p.add_argument("--model", default="")
    p.add_argument("--allow-remote", action="store_true", help="Consent to send task text to provider")
    p.add_argument("--provider-timeout", type=int, default=15, help="Network timeout, 1-60 seconds")
    r = commands.add_parser("review", help="Show and integrity-check a stored plan")
    r.add_argument("plan_id")
    a = commands.add_parser("approve", help="Record human approval tied to fingerprint")
    a.add_argument("plan_id")
    a.add_argument("--reason", required=True)
    a.add_argument("--confirm", required=True, help="Repeat exact plan ID")
    run_parser = commands.add_parser("run", help="Run only fixed, approved check commands")
    run_parser.add_argument("plan_id")
    run_parser.add_argument("--timeout", type=int, default=60)
    commands.add_parser("scan", help="Best-effort secret pattern scan, file/line only")
    preview = commands.add_parser("preview", help="Validate local candidate replacements and show read-only diffs")
    preview.add_argument("candidate", type=Path, help="Local schema-1 candidate JSON file; never sent to providers")
    proposal = commands.add_parser("propose", help="Record a local candidate bound to an unchanged plan")
    proposal.add_argument("plan_id")
    proposal.add_argument("candidate", type=Path, help="Local candidate JSON; exact explicit plan paths required")
    proposal_review = commands.add_parser("review-proposal", help="Revalidate a stored proposal and show diffs")
    proposal_review.add_argument("proposal_id")
    git_review = commands.add_parser("review-git-stage", help="Review exact local detached Git staging without mutation")
    git_review.add_argument("proposal_id")
    git_stage = commands.add_parser("stage-git-proposal", help="Create an explicitly reviewed detached linked Git stage")
    git_stage.add_argument("proposal_id")
    git_stage.add_argument("--confirm", required=True, help="Exact fingerprint from review-git-stage")
    for command, help_text in (("review-generation", "Review exact source upload without contacting a provider"),
                               ("generate-proposal", "Send exact reviewed source and store an unapproved AI proposal")):
        generation = commands.add_parser(command, help=help_text)
        generation.add_argument("plan_id")
        generation.add_argument("--provider", required=True, choices=["openai", "anthropic", "openai-compatible"])
        generation.add_argument("--model", required=True)
        generation.add_argument("--endpoint", default="")
        generation.add_argument("--provider-timeout", type=int, default=30)
        if command == "generate-proposal":
            generation.add_argument("--confirm", required=True, help="Exact fingerprint from review-generation")
            generation.add_argument("--allow-source-upload", action="store_true", help="Consent to this exact task/source upload")
    staging = commands.add_parser("stage-proposal", help="Materialize a reviewed proposal in a separate local copy")
    staging.add_argument("proposal_id")
    staging.add_argument("--confirm", required=True, help="Repeat the exact fingerprint from review-proposal")
    inspection = commands.add_parser("inspect-stage", help="Read-only comparison of a retained stage receipt and copy")
    inspection.add_argument("stage_id", help="Exact stage ID under the original project's .safeops/stages")
    compatibility = commands.add_parser("review-stage", help="Read-only staged-copy and current original-context review")
    compatibility.add_argument("stage_id", help="Exact stage ID under the original project's .safeops/stages")
    receipt = commands.add_parser("inspect-run", help="Read-only historical inspection of approved-check receipts")
    receipt.add_argument("run_id", help="Exact run ID under the project's .safeops/runs")
    application_review = commands.add_parser("review-application", help="Review exact original replacements and current passed staged checks")
    application_review.add_argument("stage_id")
    application_review.add_argument("--run", required=True, dest="run_id", help="Passed run ID within the staged workspace")
    application = commands.add_parser("apply-stage", help="Apply reviewed existing text replacements with a recoverable journal")
    application.add_argument("stage_id")
    application.add_argument("--run", required=True, dest="run_id")
    application.add_argument("--confirm", required=True, help="Repeat exact fingerprint from review-application")
    application_inspection = commands.add_parser("inspect-application", help="Read-only journal and candidate-file recovery observations")
    application_inspection.add_argument("application_id")
    rollback = commands.add_parser("rollback-application", help="Explicitly restore only known journal-owned candidate files")
    rollback.add_argument("application_id")
    rollback.add_argument("--confirm", required=True, help="Repeat fresh rollback fingerprint from inspect-application")
    recovery = commands.add_parser("recover-lock", help="Archive a retained marker after verifying no checks are running")
    recovery.add_argument("--confirm", required=True, help="Repeat the exact doctor marker fingerprint")
    recovery.add_argument("--reason", required=True)
    recovery.add_argument("--confirm-no-running-checks", action="store_true",
                          help="Acknowledge independently verifying parent/child checks have stopped")
    return parser


def _json_requested(arguments: list[str]) -> bool:
    """Recognize the documented global flag without treating task/root text as flags."""
    skip_root = False
    for value in arguments:
        if skip_root and not value.startswith("-"):
            skip_root = False
            continue
        skip_root = False
        if value == "--root":
            skip_root = True
        elif value == "--json":
            return True
        elif value == "--" or not value.startswith("-"):
            break
    return False


def _execute(args: argparse.Namespace) -> tuple[dict, int, list[str]]:
    root = args.root.resolve(strict=True)
    if not root.is_dir():
        raise SafeOpsError("--root must be an existing directory")
    if args.command == "init":
        directory = secure_dir(root)
        if directory.exists():
            raise SafeOpsError("Already initialized (.safeops exists)")
        directory.mkdir(mode=0o700)
        config = {"schema": CONFIG_SCHEMA_VERSION, "checks": ["compile", "unit-tests"]}
        atomic_json_write(directory / "config.json", config)
        (directory / "plans").mkdir()
        (directory / "approvals").mkdir()
        return {"workspace": str(directory), "config": config}, 0, []
    if args.command == "providers":
        return {"providers": provider_status(), "notice": "API keys are never displayed"}, 0, []
    if args.command == "doctor":
        cfg = get_config(root)
        targets = cfg.get("targets", {"compile": ["src", "tests"], "unit-tests": ["tests"]})
        targets = {name: targets[name] for name in cfg["checks"]}
        test_root = root / targets["unit-tests"][0] if "unit-tests" in targets else None
        return {"version": __version__, "root": str(root), "checks": cfg["checks"],
                "config_schema": cfg["schema"], "targets": targets,
                "source_files_digest": tree_digest(root),
                "test_files": len(list(test_root.rglob("test*.py"))) if test_root else 0,
                "approval_schema": APPROVAL_SCHEMA_VERSION,
                "execution_contract": execution_contract_digest(),
                "run_lock": lock_status(root)}, 0, []
    if args.command == "scan":
        findings = scan(root)
        return {"findings": findings, "count": len(findings),
                "note": "Pattern checks are not a full security audit"}, 1 if findings else 0, []
    if args.command == "preview":
        return preview_candidate(root, args.candidate), 0, []
    if args.command == "review-git-stage":
        return review_git_stage(root, args.proposal_id), 0, []
    if args.command == "stage-git-proposal":
        return stage_git_proposal(root, args.proposal_id, args.confirm), 0, []
    if args.command == "review-application":
        return review_application(root, args.stage_id, args.run_id), 0, []
    if args.command == "apply-stage":
        return apply_stage(root, args.stage_id, args.run_id, args.confirm), 0, []
    if args.command == "inspect-application":
        result = inspect_application(root, args.application_id)
        return result, 0 if result["status"] in {"applied", "rolled-back"} else 1, []
    if args.command == "rollback-application":
        return rollback_application(root, args.application_id, args.confirm), 0, []
    if args.command == "inspect-run":
        result = inspect_run(root, args.run_id)
        return result, 0 if result["status"] == "passed" else 1, []
    if args.command == "review-stage":
        result = review_stage(root, args.stage_id)
        return result, 0 if result["status"] == "current" else 1, []
    workspace(root)
    if args.command in ("review-generation", "generate-proposal"):
        options = {"provider": args.provider, "model": args.model, "endpoint": args.endpoint,
                   "timeout": args.provider_timeout}
        if args.command == "review-generation":
            return review_generation(root, args.plan_id, **options), 0, []
        return generate_proposal(root, args.plan_id, args.confirm,
                                 allow_source_upload=args.allow_source_upload, **options), 0, []
    if args.command == "propose":
        return create_proposal(root, args.plan_id, args.candidate), 0, []
    if args.command == "review-proposal":
        return review_proposal(root, args.proposal_id), 0, []
    if args.command == "stage-proposal":
        return stage_proposal(root, args.proposal_id, args.confirm), 0, []
    if args.command == "inspect-stage":
        result = inspect_stage(root, args.stage_id)
        return result, 0 if result["status"] == "matching" else 1, []
    if args.command == "recover-lock":
        return recover_lock(root, args.confirm, args.reason, args.confirm_no_running_checks), 0, []
    if args.command == "plan":
        validate_task(args.task)
        scope_paths = validate_scope_paths(root, args.path)
        if args.provider != "offline":
            if args.provider == "openai-compatible" and not args.endpoint:
                raise SafeOpsError("Custom provider needs --endpoint")
            advice = remote_advice(args.task, provider=args.provider, endpoint=args.endpoint,
                                   model=args.model, allow_remote=args.allow_remote,
                                   timeout=args.provider_timeout)
        else:
            if args.allow_remote or args.endpoint or args.model or args.provider_timeout != 15:
                raise SafeOpsError("Remote flags only apply to remote providers")
            advice = offline_advice(args.task, specialization(args.task))
        plan = create_plan(root, args.task, scope_paths, advice, args.provider)
        audit(root, "plan", plan["id"], plan["risk"])
        warnings = ["CRITICAL: execution is blocked by policy"] if plan["risk"] == "critical" else []
        return plan, 0, warnings
    if args.command == "review":
        return load_plan(root, args.plan_id), 0, []
    if args.command == "approve":
        return approve(root, args.plan_id, args.reason, args.confirm), 0, []
    if args.command == "run":
        result = run(root, args.plan_id, timeout=args.timeout)
        return result, 0 if result["status"] == "passed" else 1, []
    raise SafeOpsError("Unsupported command")


def _envelope(command: str | None, code: int, *, data: dict | None = None,
              error: dict | None = None, warnings: list[str] | None = None) -> None:
    print(json.dumps({"schema": 1, "safeops_version": __version__, "command": command,
                      "ok": code == 0, "exit_code": code, "data": data,
                      "error": error, "warnings": warnings or []}, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_mode = _json_requested(arguments)
    if json_mode and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = make_parser()
    try:
        args = parser.parse_args(arguments)
    except ArgumentUsageError as exc:
        if json_mode:
            # Do not echo argument values: they may include accidental credentials.
            _envelope(None, 2, error={"code": "invalid_arguments", "message": "Invalid command arguments; see --help"})
        else:
            print(exc.usage, end="", file=sys.stderr)
            print(f"{exc.prog}: error: {exc}", file=sys.stderr)
        return 2
    if args.json and not json_mode and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    json_mode = args.json
    try:
        data, code, warnings = _execute(args)
    except (SafeOpsError, OSError) as exc:
        if json_mode:
            error = {"code": "policy_error", "message": str(exc)} if isinstance(exc, SafeOpsError) else {
                "code": "filesystem_error", "message": "Cannot access the workspace or a required file"}
            _envelope(args.command, 2, error=error)
        else:
            print(f"safeops: {exc}", file=sys.stderr)
        return 2
    if json_mode:
        _envelope(args.command, code, data=data, warnings=warnings)
    else:
        if args.command == "init":
            print(f"Initialized: {data['workspace']}")
            print("Local state is excluded from Git by the recommended .gitignore")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=args.command in {"doctor", "providers", "scan"}))
        for warning in warnings:
            print(warning, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
