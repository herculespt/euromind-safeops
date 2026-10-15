"""Maintainer CI adapter: trusted unittest execution and numeric job summaries."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .check_runner import run_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", default="tests", help="Trusted unittest discovery root")
    parser.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"),
                        help="Append numeric Markdown summary (default: GITHUB_STEP_SUMMARY)")
    args = parser.parse_args(argv)
    if not args.summary:
        parser.error("--summary or GITHUB_STEP_SUMMARY is required")
    code, stats = run_suite(args.tests)
    status = "passed" if code == 0 else "failed"
    lines = [f"### SafeOps {__version__} — tests {status}", "", "| Result | Count |", "|---|---:|"]
    for label, key in (("Discovered", "discovered"), ("Run (including skipped)", "run"),
                       ("Failures", "failures"), ("Errors", "errors"), ("Skipped", "skipped"),
                       ("Expected failures", "expected_failures"), ("Unexpected successes", "unexpected_successes")):
        lines.append(f"| {label} | {stats[key]} |")
    lines.extend(["", f"Phase: {stats['phase']}. Check exit code: {code}.", "",
                  "Counts describe trusted unittest results; they do not prove coverage or isolation.", ""])
    try:
        with Path(args.summary).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n" + "\n".join(lines))
    except OSError:
        print("SafeOps: cannot write CI summary", file=sys.stderr)
        return 2
    print("SafeOps: aggregate CI summary appended")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
