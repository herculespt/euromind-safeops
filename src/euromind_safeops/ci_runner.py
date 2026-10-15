"""Maintainer CI adapter: trusted unittest execution, summaries and optional JUnit."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .check_runner import run_suite
from .junit import OutcomeResult, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", default="tests", help="Trusted unittest discovery root")
    parser.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"),
                        help="Append numeric Markdown summary (default: GITHUB_STEP_SUMMARY)")
    parser.add_argument("--junit", help="Replace a local JUnit XML report (existing parent required)")
    args = parser.parse_args(argv)
    if not args.summary:
        parser.error("--summary or GITHUB_STEP_SUMMARY is required")
    if args.junit:
        try:
            summary, junit = Path(args.summary), Path(args.junit)
            same = (junit.resolve() == summary.resolve()
                    or (junit.exists() and summary.exists() and junit.samefile(summary)))
        except (OSError, ValueError):
            parser.error("invalid report destination")
        if same:
            parser.error("summary and JUnit destinations must differ")
    outcomes: list[str] = []

    def resultclass(*values, **kwargs):
        return OutcomeResult(*values, outcomes=outcomes, **kwargs)

    code, stats = run_suite(args.tests, resultclass=resultclass if args.junit else None)
    reporting_failed = False
    if args.junit:
        try:
            write_report(Path(args.junit), outcomes, code, stats["phase"])
            print("SafeOps: JUnit report written")
        except (OSError, ValueError):
            print("SafeOps: cannot write JUnit report", file=sys.stderr)
            reporting_failed = True
    status = "passed" if code == 0 else "failed"
    lines = [f"### SafeOps {__version__} — tests {status}", "", "| Result | Count |", "|---|---:|"]
    for label, key in (("Discovered", "discovered"), ("Run (including skipped)", "run"),
                       ("Failures", "failures"), ("Errors", "errors"), ("Skipped", "skipped"),
                       ("Expected failures", "expected_failures"), ("Unexpected successes", "unexpected_successes")):
        lines.append(f"| {label} | {stats[key]} |")
    lines.extend(["", f"Phase: {stats['phase']}. Check exit code: {code}.", "",
                  "Counts describe trusted unittest results; they do not prove coverage or isolation.", ""])
    if reporting_failed:
        lines.extend(["JUnit report write failed. Adapter exit code: 2.", ""])
    try:
        with Path(args.summary).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n" + "\n".join(lines))
    except (OSError, ValueError):
        print("SafeOps: cannot write CI summary", file=sys.stderr)
        return 2
    print("SafeOps: aggregate CI summary appended")
    return 2 if reporting_failed else code


if __name__ == "__main__":
    raise SystemExit(main())
