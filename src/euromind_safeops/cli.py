"""EuroMind SafeOps command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import SafeOpsError, atomic_json_write, audit, read_json, secure_dir, tree_digest, workspace
from .execution import approve, get_config, run
from .planning import create_plan, load_plan, specialization
from .providers import offline_advice, remote_advice
from .scanning import scan


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safeops", description="Safety-focused engineering orchestration (v0.1.0 alpha)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project directory (default: current directory)")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize local, git-ignored SafeOps workspace")
    commands.add_parser("doctor", help="Check local installation and workspace")
    p = commands.add_parser("plan", help="Create a hashed, advisory-only task plan")
    p.add_argument("task", help="Short task description; never paste secrets")
    p.add_argument("--path", action="append", default=[], help="Relative scope path (repeatable)")
    p.add_argument("--provider", choices=["offline", "openai-compatible"], default="offline")
    p.add_argument("--endpoint", default="")
    p.add_argument("--model", default="")
    p.add_argument("--allow-remote", action="store_true", help="Consent to send task text to endpoint")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise SafeOpsError("--root must be an existing directory")
        if args.command == "init":
            directory = secure_dir(root)
            if directory.exists():
                raise SafeOpsError("Already initialized (.safeops exists)")
            directory.mkdir(mode=0o700)
            atomic_json_write(directory / "config.json", {"schema": 1, "checks": ["compile", "unit-tests"]})
            (directory / "plans").mkdir()
            (directory / "approvals").mkdir()
            print(f"Initialized: {directory}")
            print("Local state is excluded from Git by the recommended .gitignore")
            return 0
        if args.command == "doctor":
            cfg = get_config(root)
            print(json.dumps({"version": __version__, "root": str(root), "checks": cfg["checks"],
                              "source_files_digest": tree_digest(root), "test_files": len(list((root / "tests").glob("test*.py")))}, indent=2))
            return 0
        if args.command == "scan":
            findings = scan(root)
            print(json.dumps({"findings": findings, "count": len(findings),
                              "note": "Pattern checks are not a full security audit"}, indent=2))
            return 1 if findings else 0
        workspace(root)
        if args.command == "plan":
            if args.provider == "openai-compatible":
                if not args.endpoint or not args.model:
                    raise SafeOpsError("Remote provider needs --endpoint and --model")
                advice = remote_advice(args.task, endpoint=args.endpoint, model=args.model, allow_remote=args.allow_remote)
            else:
                if args.allow_remote or args.endpoint or args.model:
                    raise SafeOpsError("Remote flags only apply to --provider openai-compatible")
                advice = offline_advice(args.task, specialization(args.task))
            plan = create_plan(root, args.task, args.path, advice, args.provider)
            audit(root, "plan", plan["id"], plan["risk"])
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            if plan["risk"] == "critical":
                print("CRITICAL: execution is blocked by policy", file=sys.stderr)
            return 0
        if args.command == "review":
            print(json.dumps(load_plan(root, args.plan_id), indent=2, ensure_ascii=False))
            return 0
        if args.command == "approve":
            record = approve(root, args.plan_id, args.reason, args.confirm)
            print(json.dumps(record, indent=2, ensure_ascii=False))
            return 0
        if args.command == "run":
            result = run(root, args.plan_id, timeout=args.timeout)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["status"] == "passed" else 1
        raise SafeOpsError("Unsupported command")
    except (SafeOpsError, FileNotFoundError) as exc:
        print(f"safeops: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
