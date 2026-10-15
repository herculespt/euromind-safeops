"""Exercise the packaged CI adapter against real isolated unittest fixtures."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from euromind_safeops import __version__
from euromind_safeops.junit import write_report


class CIReportingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "tests").mkdir()
        self.source = self.root / "tests" / "test_fixture.py"
        self.summary = self.root / "summary.md"
        self.junit = self.root / "report.xml"

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

    def junit_fixture(self, source, **kwargs):
        return self.run_fixture(source, arguments=["--summary", str(self.summary),
                                                   "--junit", str(self.junit)], **kwargs)

    def read_report(self):
        root = ET.parse(self.junit).getroot()
        self.assertEqual(root.tag, "testsuites")
        suite = root.find("testsuite")
        cases = suite.findall("testcase")
        self.assertEqual(int(root.get("tests")), len(cases))
        self.assertEqual({key: suite.get(key) for key in root.attrib}, root.attrib)
        for tag, key in (("failure", "failures"), ("error", "errors"), ("skipped", "skipped")):
            self.assertEqual(int(root.get(key)), len(suite.findall(f"testcase/{tag}")))
        for number, case in enumerate(cases, 1):
            self.assertEqual(case.attrib, {"classname": "safeops.unittest", "name": f"case-{number}"})
        properties = {item.get("name"): item.get("value") for item in suite.find("properties")}
        self.assertEqual(properties["safeops_version"], __version__)
        self.assertEqual(properties["report_schema"], "1")
        return root, cases, properties

    def test_junit_pass_skip_expected_failure_and_private_xml_characters(self):
        completed = self.junit_fixture(
            "import unittest\nclass PrivateTestName(unittest.TestCase):\n"
            " def test_private_pass(self): print('private output')\n"
            " @unittest.skip('private <é>& reason\\x00')\n def test_private_skip(self): pass\n"
            " @unittest.expectedFailure\n def test_private_expected(self): self.fail('private message')\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        root, cases, properties = self.read_report()
        self.assertEqual(root.get("tests"), "3")
        self.assertEqual(root.get("skipped"), "2")
        self.assertEqual({c[0].get("type") for c in cases if len(c)}, {"skipped", "expected-failure"})
        self.assertEqual(properties["check_exit_code"], "0")
        self.assertNotIn("private", self.junit.read_text().lower())
        self.assertNotIn("system-out", self.junit.read_text())

    def test_junit_failure_error_unexpected_success(self):
        completed = self.junit_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_failure(self): self.fail('private assertion')\n"
            " def test_error(self): raise RuntimeError('private exception')\n"
            " @unittest.expectedFailure\n def test_unexpected(self): pass\n")
        self.assertEqual(completed.returncode, 1)
        root, cases, properties = self.read_report()
        self.assertEqual(root.get("failures"), "2")
        self.assertEqual(root.get("errors"), "1")
        self.assertEqual(properties["check_exit_code"], "1")
        self.assertEqual({c[0].get("type") for c in cases}, {"failure", "error", "unexpected-success"})
        self.assertNotIn("private", self.junit.read_text())

    def test_junit_subtest_outcomes_do_not_serialize_parameters(self):
        completed = self.junit_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_subtests(self):\n"
            "  for i in range(3):\n"
            "   with self.subTest(private_parameter='private value', i=i):\n"
            "    if i == 1: self.fail('private assertion')\n"
            "    if i == 2: raise ValueError('private error')\n"
            " def test_successful_subtests(self):\n"
            "  with self.subTest(private_parameter='private'): pass\n")
        self.assertEqual(completed.returncode, 1)
        root, _, _ = self.read_report()
        self.assertEqual(root.get("tests"), "3")  # two failed subtests + successful parent
        self.assertEqual(root.get("failures"), "1")
        self.assertEqual(root.get("errors"), "1")
        self.assertIn("| Run (including skipped) | 2 |", self.summary.read_text())
        self.assertNotIn("private", self.junit.read_text())

    def test_junit_class_fixture_error_is_not_lost_when_no_case_runs(self):
        completed = self.junit_fixture(
            "import unittest\nclass T(unittest.TestCase):\n"
            " @classmethod\n def setUpClass(cls): raise RuntimeError('private fixture')\n"
            " def test_unused(self): pass\n")
        self.assertEqual(completed.returncode, 1)
        root, _, _ = self.read_report()
        self.assertEqual(root.get("tests"), "1")
        self.assertEqual(root.get("errors"), "1")
        self.assertIn("| Run (including skipped) | 0 |", self.summary.read_text())

    def test_junit_module_fixture_skip_adds_runner_error(self):
        completed = self.junit_fixture(
            "import unittest\ndef setUpModule(): raise unittest.SkipTest('private')\n"
            "class T(unittest.TestCase):\n def test_unused(self): pass\n")
        self.assertEqual(completed.returncode, 2)
        root, _, properties = self.read_report()
        self.assertEqual(root.get("skipped"), "1")
        self.assertEqual(root.get("errors"), "1")
        self.assertEqual(properties["check_exit_code"], "2")

    def test_junit_empty_suite_is_visible_error(self):
        completed = self.junit_fixture("value = 1\n")
        self.assertEqual(completed.returncode, 2)
        root, cases, properties = self.read_report()
        self.assertEqual(root.get("errors"), "1")
        self.assertEqual(cases[0][0].get("type"), "runner-error")
        self.assertEqual(properties["phase"], "discovery")

    def test_junit_all_skipped_suite_is_visible_error(self):
        completed = self.junit_fixture(
            "import unittest\n@unittest.skip('private')\nclass T(unittest.TestCase):\n def test_it(self): pass\n")
        self.assertEqual(completed.returncode, 2)
        root, _, _ = self.read_report()
        self.assertEqual(root.get("tests"), "2")
        self.assertEqual(root.get("skipped"), "1")
        self.assertEqual(root.get("errors"), "1")

    def test_junit_discovery_hook_exit_is_visible_error(self):
        completed = self.junit_fixture("def load_tests(loader, tests, pattern): raise SystemExit(0)\n")
        self.assertEqual(completed.returncode, 2)
        _, _, properties = self.read_report()
        self.assertEqual(properties["phase"], "discovery")

    def test_junit_import_error_is_visible_error(self):
        completed = self.junit_fixture("raise RuntimeError('private import error')\n")
        self.assertEqual(completed.returncode, 1)
        root, _, _ = self.read_report()
        self.assertEqual(root.get("errors"), "1")

    def test_junit_interrupted_execution_keeps_observed_outcomes_and_runner_error(self):
        completed = self.junit_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n"
            "class BrokenSuite(unittest.TestSuite):\n"
            " def run(self, result, debug=False):\n"
            "  super().run(result, debug)\n  raise SystemExit(0)\n"
            "def load_tests(loader, tests, pattern): return BrokenSuite([T('test_it')])\n")
        self.assertEqual(completed.returncode, 2)
        root, _, properties = self.read_report()
        self.assertEqual(root.get("tests"), "2")
        self.assertEqual(root.get("errors"), "1")
        self.assertEqual(properties["phase"], "execution")

    def test_junit_is_optional(self):
        completed = self.run_fixture("import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n")
        self.assertEqual(completed.returncode, 0)
        self.assertFalse(self.junit.exists())

    def test_junit_write_failure_keeps_summary_and_fails_adapter(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            arguments=["--summary", str(self.summary), "--junit", str(self.root / 'missing' / 'report.xml')])
        self.assertEqual(completed.returncode, 2)
        self.assertIn("cannot write JUnit report", completed.stderr)
        self.assertIn("JUnit report write failed. Adapter exit code: 2.", self.summary.read_text())
        self.assertFalse((self.root / "missing").exists())
        self.assertNotIn("Traceback", completed.stderr)

    def test_junit_directory_destination_fails_without_temporary_file(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            arguments=["--summary", str(self.summary), "--junit", str(self.root)])
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(list(self.root.glob(".safeops-junit-*")), [])

    def test_junit_and_summary_same_destination_rejected_before_import(self):
        completed = self.run_fixture("raise RuntimeError('must not import')\n",
            arguments=["--summary", str(self.summary), "--junit", str(self.summary)])
        self.assertEqual(completed.returncode, 2)
        self.assertIn("destinations must differ", completed.stderr)
        self.assertNotIn("must not import", completed.stderr)
        self.assertFalse(self.summary.exists())

    def test_junit_and_summary_hardlink_alias_rejected(self):
        self.summary.write_text("prior summary")
        try:
            os.link(self.summary, self.junit)
        except OSError:
            self.skipTest("Hard links unavailable")
        completed = self.junit_fixture("raise RuntimeError('must not import')\n")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("destinations must differ", completed.stderr)
        self.assertEqual(self.summary.read_text(), "prior summary")

    def test_junit_summary_failure_does_not_discard_test_report(self):
        completed = self.run_fixture(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            arguments=["--summary", str(self.root), "--junit", str(self.junit)])
        self.assertEqual(completed.returncode, 2)
        _, _, properties = self.read_report()
        self.assertEqual(properties["check_exit_code"], "0")  # test status, not adapter status

    def test_junit_atomic_replace_failure_preserves_previous_report(self):
        self.junit.write_text("previous report")
        with patch("euromind_safeops.junit.os.replace", side_effect=OSError("private OS error")):
            with self.assertRaises(OSError):
                write_report(self.junit, ["passed"], 0, "completed")
        self.assertEqual(self.junit.read_text(), "previous report")
        self.assertEqual(list(self.root.glob(".safeops-junit-*")), [])

    def test_junit_overwrites_instead_of_appending(self):
        self.junit.write_text("obsolete private report")
        completed = self.junit_fixture("import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n")
        self.assertEqual(completed.returncode, 0)
        self.read_report()
        self.assertNotIn("obsolete", self.junit.read_text())
