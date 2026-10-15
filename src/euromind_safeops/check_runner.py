"""Fixed unittest adapter. Discovery runs only inside the approved child process.

This is not isolation: imported tests and load_tests hooks remain trusted code.
"""

from __future__ import annotations

import sys
import unittest


def main(start_directory: str = "tests") -> int:
    try:
        suite = unittest.TestLoader().discover(start_directory, pattern="test*.py")
        count = suite.countTestCases()
    except (Exception, SystemExit) as exc:
        print(f"SafeOps: test discovery failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    if count == 0:
        print("SafeOps: No tests discovered; refusing successful check", file=sys.stderr)
        return 2
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    except (Exception, SystemExit) as exc:
        print(f"SafeOps: test execution failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    if not result.wasSuccessful():
        return 1
    if result.testsRun <= len(result.skipped):
        print("SafeOps: No non-skipped tests executed; refusing successful check", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
