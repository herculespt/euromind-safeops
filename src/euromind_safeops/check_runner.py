"""Fixed unittest adapter. Discovery runs only inside the approved child process.

This is not isolation: imported tests and load_tests hooks remain trusted code.
"""

from __future__ import annotations

import sys
import unittest
from collections.abc import Callable


def run_suite(start_directory: str = "tests", *,
              resultclass: Callable[..., unittest.TextTestResult] | None = None) -> tuple[int, dict]:
    stats = {"discovered": 0, "run": 0, "failures": 0, "errors": 0, "skipped": 0,
             "expected_failures": 0, "unexpected_successes": 0, "phase": "discovery"}
    try:
        suite = unittest.TestLoader().discover(start_directory, pattern="test*.py")
        count = suite.countTestCases()
        stats["discovered"] = count
    except (Exception, SystemExit) as exc:
        print(f"SafeOps: test discovery failed ({type(exc).__name__})", file=sys.stderr)
        return 2, stats
    if count == 0:
        print("SafeOps: No tests discovered; refusing successful check", file=sys.stderr)
        return 2, stats
    stats["phase"] = "execution"
    try:
        result = unittest.TextTestRunner(verbosity=2, resultclass=resultclass).run(suite)
    except (Exception, SystemExit) as exc:
        print(f"SafeOps: test execution failed ({type(exc).__name__})", file=sys.stderr)
        return 2, stats
    stats.update(run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                 skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                 unexpected_successes=len(result.unexpectedSuccesses), phase="completed")
    if not result.wasSuccessful():
        return 1, stats
    if result.testsRun <= len(result.skipped):
        print("SafeOps: No non-skipped tests executed; refusing successful check", file=sys.stderr)
        return 2, stats
    return 0, stats


def main(start_directory: str = "tests") -> int:
    return run_suite(start_directory)[0]


if __name__ == "__main__":
    raise SystemExit(main())
