"""Exercise the packaged CI adapter against real isolated unittest fixtures."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CIReportingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "tests").mkdir()
        self.source = self.root / "tests" / "test_fixture.py"
        self.summary = self.root / "summary.md"

    def run_fixture(self, source, *, arguments=None, environment=None):
        self.source.write_text(source, encoding="utf-8")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        env.pop("GITHUB_STEP_SUMMARY", None)
        env.update(environment or {})
        return subprocess.run([sys.executable, "-m", "euromind_safeops.ci_runner",
                               *(arguments if arguments is not None else ["--summary", str(self.summary)])],
                              cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8")

    def test_successful_mixed_suite_has_numeric_counts_and_no_test_text(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_pass(self): print('private fixture text')\n"
            " @unittest.skip('private skip reason')\n def test_skip(self): pass\n"
            " @unittest.expectedFailure\n def test_expected(self): self.fail('private failure')\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = self.summary.read_text(encoding="utf-8")
        for row in ("| Discovered | 3 |", "| Run (including skipped) | 3 |", "| Skipped | 1 |",
                    "| Expected failures | 1 |", "tests passed", "Phase: completed. Check exit code: 0."):
            self.assertIn(row, summary)
        self.assertNotIn("private", summary)
        self.assertNotIn("test_pass", summary)
        self.assertIn("private fixture text", completed.stdout)

    def test_failures_and_errors_still_write_summary(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_failure(self): self.fail('fixture')\n"
            " def test_error(self): raise RuntimeError('fixture')\n")
        self.assertEqual(completed.returncode, 1)
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("tests failed", summary)
        self.assertIn("| Failures | 1 |", summary)
        self.assertIn("| Errors | 1 |", summary)

    def test_unexpected_success_is_failure(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " @unittest.expectedFailure\n def test_unexpected(self): pass\n")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("| Unexpected successes | 1 |", self.summary.read_text(encoding="utf-8"))

    def test_empty_discovery_is_reported_as_unusable(self):
        completed = self.run_fixture("value = 1\n")
        self.assertEqual(completed.returncode, 2)
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("| Discovered | 0 |", summary)
        self.assertIn("Phase: discovery. Check exit code: 2.", summary)

    def test_all_skipped_is_not_success(self):
        completed = self.run_fixture(
            "import unittest\n@unittest.skip('fixture')\nclass T(unittest.TestCase):\n def test_it(self): pass\n")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("| Skipped | 1 |", self.summary.read_text(encoding="utf-8"))

    def test_zero_exit_during_discovery_is_reported_as_failure(self):
        completed = self.run_fixture("raise SystemExit(0)\n")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("tests failed", self.summary.read_text(encoding="utf-8"))

    def test_zero_exit_from_discovery_hook_is_reported_as_unusable(self):
        completed = self.run_fixture("def load_tests(loader, tests, pattern): raise SystemExit(0)\n")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Phase: discovery", self.summary.read_text(encoding="utf-8"))

    def test_unusable_test_root_still_reports(self):
        completed = self.run_fixture("", arguments=["--tests", "missing", "--summary", str(self.summary)])
        self.assertEqual(completed.returncode, 2)
        self.assertIn("tests failed", self.summary.read_text(encoding="utf-8"))

    def test_summary_environment_and_utf8_append(self):
        self.summary.write_text("Resumo prévio", encoding="utf-8")
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            arguments=[], environment={"GITHUB_STEP_SUMMARY": str(self.summary)})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = self.summary.read_text(encoding="utf-8")
        self.assertTrue(summary.startswith("Resumo prévio\n### SafeOps"))

    def test_missing_summary_destination_is_usage_error(self):
        completed = self.run_fixture("raise RuntimeError('must not import')\n", arguments=[])
        self.assertEqual(completed.returncode, 2)
        self.assertIn("GITHUB_STEP_SUMMARY is required", completed.stderr)
        self.assertNotIn("must not import", completed.stderr)
        self.assertFalse(self.summary.exists())

    def test_summary_write_failure_is_not_a_pass(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            arguments=["--summary", str(self.root)])
        self.assertEqual(completed.returncode, 2)
        self.assertIn("cannot write CI summary", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
